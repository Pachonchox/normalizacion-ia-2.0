#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚦 Sistema de Throttling y Circuit Breakers
Control de rate limits, backpressure y resiliencia
"""

import time
import asyncio
from typing import Dict, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from collections import deque
from datetime import datetime, timedelta
import logging
import random

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Estados del circuit breaker"""
    CLOSED = "closed"      # Normal, permitir requests
    OPEN = "open"          # Falla detectada, bloquear requests
    HALF_OPEN = "half_open"  # Probando recuperación

@dataclass
class RateLimitConfig:
    """Configuración de rate limits por modelo"""
    model: str
    requests_per_minute: int
    requests_per_second: Optional[int] = None
    tokens_per_minute: Optional[int] = None
    concurrent_limit: int = 10

class TokenBucket:
    """Implementación de Token Bucket para rate limiting"""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Args:
            capacity: Capacidad máxima del bucket
            refill_rate: Tokens por segundo a agregar
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> bool:
        """
        Intentar adquirir tokens
        
        Returns:
            True si se pudo adquirir, False si no hay suficientes
        """
        async with self._lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    async def acquire_with_wait(self, tokens: int = 1, max_wait: float = 60) -> bool:
        """Adquirir tokens esperando si es necesario"""
        start = time.time()
        
        while time.time() - start < max_wait:
            if await self.acquire(tokens):
                return True
            
            # Calcular tiempo de espera
            wait_time = min(
                (tokens - self.tokens) / self.refill_rate,
                max_wait - (time.time() - start)
            )
            
            if wait_time > 0:
                await asyncio.sleep(min(wait_time, 1))
        
        return False
    
    def _refill(self):
        """Rellenar bucket basado en tiempo transcurrido"""
        now = time.time()
        elapsed = now - self.last_refill
        
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    @property
    def available(self) -> float:
        """Tokens disponibles actualmente"""
        self._refill()
        return self.tokens

class CircuitBreaker:
    """Circuit breaker para manejar fallos"""
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 success_threshold: int = 2):
        """
        Args:
            failure_threshold: Fallos antes de abrir circuito
            recovery_timeout: Segundos antes de intentar recuperación
            success_threshold: Éxitos necesarios para cerrar circuito
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_state_change = datetime.now()
        
        # Estadísticas
        self.stats = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'rejected_calls': 0
        }
    
    def call(self, func: Callable, *args, **kwargs):
        """
        Ejecutar función a través del circuit breaker
        
        Raises:
            Exception: Si el circuito está abierto o la función falla
        """
        self.stats['total_calls'] += 1
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"🔄 Circuit breaker entering HALF_OPEN state")
            else:
                self.stats['rejected_calls'] += 1
                raise Exception(f"Circuit breaker is OPEN (failures: {self.failure_count})")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    async def call_async(self, func: Callable, *args, **kwargs):
        """Versión asíncrona del circuit breaker"""
        self.stats['total_calls'] += 1
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"🔄 Circuit breaker entering HALF_OPEN state")
            else:
                self.stats['rejected_calls'] += 1
                raise Exception(f"Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Manejar llamada exitosa"""
        self.stats['successful_calls'] += 1
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.success_count = 0
                logger.info(f"✅ Circuit breaker CLOSED (recovered)")
    
    def _on_failure(self):
        """Manejar fallo"""
        self.stats['failed_calls'] += 1
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logger.warning(f"⚠️ Circuit breaker OPEN (failed during recovery)")
        elif self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"🔴 Circuit breaker OPEN (threshold reached: {self.failure_count})")
    
    def _should_attempt_reset(self) -> bool:
        """Verificar si deberíamos intentar recuperación"""
        return (
            self.last_failure_time and
            datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)
        )
    
    def reset(self):
        """Reset manual del circuit breaker"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        logger.info("🔄 Circuit breaker manually reset")
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas"""
        return {
            'state': self.state.value,
            'failure_count': self.failure_count,
            **self.stats
        }

class RateLimiter:
    """Sistema completo de rate limiting para múltiples modelos"""
    
    def __init__(self):
        # Configuración por modelo
        self.configs = {
            'gpt-5-mini': RateLimitConfig(
                model='gpt-5-mini',
                requests_per_minute=500,
                requests_per_second=10,
                tokens_per_minute=150000
            ),
            'gpt-5': RateLimitConfig(
                model='gpt-5',
                requests_per_minute=100,
                requests_per_second=2,
                tokens_per_minute=50000
            ),
            'gpt-4o-mini': RateLimitConfig(
                model='gpt-4o-mini',
                requests_per_minute=200,
                requests_per_second=5,
                tokens_per_minute=100000
            ),
            'gpt-4o': RateLimitConfig(
                model='gpt-4o',
                requests_per_minute=50,
                requests_per_second=1,
                tokens_per_minute=30000
            )
        }
        
        # Token buckets por modelo
        self.request_buckets = {}
        self.token_buckets = {}
        
        for model, config in self.configs.items():
            # Bucket para requests por minuto
            self.request_buckets[model] = TokenBucket(
                capacity=config.requests_per_minute,
                refill_rate=config.requests_per_minute / 60
            )
            
            # Bucket para tokens si está configurado
            if config.tokens_per_minute:
                self.token_buckets[model] = TokenBucket(
                    capacity=config.tokens_per_minute,
                    refill_rate=config.tokens_per_minute / 60
                )
        
        # Circuit breakers por modelo
        self.circuit_breakers = {
            model: CircuitBreaker(failure_threshold=5, recovery_timeout=60)
            for model in self.configs.keys()
        }
        
        # Estadísticas
        self.stats = {
            'requests_accepted': 0,
            'requests_throttled': 0,
            'requests_rejected': 0
        }
    
    async def acquire(self, model: str, estimated_tokens: int = 250) -> bool:
        """
        Intentar adquirir permiso para hacer request
        
        Args:
            model: Modelo a usar
            estimated_tokens: Tokens estimados del request
        
        Returns:
            True si se puede proceder, False si está throttled
        """
        if model not in self.configs:
            logger.warning(f"Unknown model for rate limiting: {model}")
            return True
        
        # Verificar circuit breaker
        if self.circuit_breakers[model].state == CircuitState.OPEN:
            self.stats['requests_rejected'] += 1
            return False
        
        # Verificar rate limit de requests
        request_bucket = self.request_buckets[model]
        if not await request_bucket.acquire():
            self.stats['requests_throttled'] += 1
            return False
        
        # Verificar rate limit de tokens
        if model in self.token_buckets:
            token_bucket = self.token_buckets[model]
            if not await token_bucket.acquire(estimated_tokens):
                self.stats['requests_throttled'] += 1
                return False
        
        self.stats['requests_accepted'] += 1
        return True
    
    async def acquire_with_backoff(self, model: str, estimated_tokens: int = 250,
                                  max_retries: int = 3) -> bool:
        """Adquirir con retry y exponential backoff"""
        
        for attempt in range(max_retries):
            if await self.acquire(model, estimated_tokens):
                return True
            
            # Exponential backoff con jitter
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            logger.info(f"⏳ Rate limited, waiting {wait_time:.1f}s (attempt {attempt + 1}/{max_retries})")
            await asyncio.sleep(wait_time)
        
        return False
    
    def report_success(self, model: str):
        """Reportar éxito al circuit breaker"""
        if model in self.circuit_breakers:
            self.circuit_breakers[model]._on_success()
    
    def report_failure(self, model: str, error: Exception = None):
        """Reportar fallo al circuit breaker"""
        if model in self.circuit_breakers:
            self.circuit_breakers[model]._on_failure()
            
            # Analizar tipo de error para ajustar comportamiento
            if error:
                error_str = str(error).lower()
                if '429' in error_str or 'rate limit' in error_str:
                    # Rate limit error - esperar más
                    logger.warning(f"⚠️ Rate limit error for {model}")
                elif '503' in error_str or 'unavailable' in error_str:
                    # Servicio no disponible
                    logger.error(f"🔴 Service unavailable for {model}")
    
    def get_status(self, model: str = None) -> Dict[str, Any]:
        """Obtener estado del rate limiter"""
        if model:
            return {
                'model': model,
                'requests_available': self.request_buckets[model].available,
                'tokens_available': self.token_buckets.get(model, TokenBucket(0, 0)).available,
                'circuit_state': self.circuit_breakers[model].state.value,
                'circuit_stats': self.circuit_breakers[model].get_stats()
            }
        
        # Estado global
        return {
            'stats': self.stats,
            'models': {
                m: {
                    'requests_available': self.request_buckets[m].available,
                    'circuit_state': self.circuit_breakers[m].state.value
                }
                for m in self.configs.keys()
            }
        }
    
    def reset_circuit(self, model: str):
        """Reset manual del circuit breaker de un modelo"""
        if model in self.circuit_breakers:
            self.circuit_breakers[model].reset()

class AdaptiveThrottler:
    """Throttler adaptativo que ajusta límites según performance"""
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
        self.performance_window = deque(maxlen=100)  # Últimas 100 requests
        self.adjustment_interval = 60  # Segundos entre ajustes
        self.last_adjustment = time.time()
    
    def record_latency(self, model: str, latency_ms: int, success: bool):
        """Registrar latencia de request"""
        self.performance_window.append({
            'model': model,
            'latency_ms': latency_ms,
            'success': success,
            'timestamp': time.time()
        })
        
        # Ajustar si es necesario
        if time.time() - self.last_adjustment > self.adjustment_interval:
            self._adjust_limits()
    
    def _adjust_limits(self):
        """Ajustar límites basado en performance"""
        if len(self.performance_window) < 10:
            return
        
        # Calcular métricas
        avg_latency = sum(r['latency_ms'] for r in self.performance_window) / len(self.performance_window)
        success_rate = sum(1 for r in self.performance_window if r['success']) / len(self.performance_window)
        
        # Ajustar según performance
        for model in self.rate_limiter.configs.keys():
            model_requests = [r for r in self.performance_window if r['model'] == model]
            
            if not model_requests:
                continue
            
            model_success_rate = sum(1 for r in model_requests if r['success']) / len(model_requests)
            
            # Si hay muchos errores, reducir límites
            if model_success_rate < 0.8:
                old_limit = self.rate_limiter.configs[model].requests_per_minute
                new_limit = int(old_limit * 0.8)
                self.rate_limiter.configs[model].requests_per_minute = new_limit
                logger.warning(f"📉 Reducing rate limit for {model}: {old_limit} → {new_limit} RPM")
            
            # Si todo va bien y latencia es baja, aumentar límites
            elif model_success_rate > 0.95 and avg_latency < 1000:
                old_limit = self.rate_limiter.configs[model].requests_per_minute
                new_limit = int(old_limit * 1.1)
                self.rate_limiter.configs[model].requests_per_minute = new_limit
                logger.info(f"📈 Increasing rate limit for {model}: {old_limit} → {new_limit} RPM")
        
        self.last_adjustment = time.time()

# Singleton
_rate_limiter = None

def get_rate_limiter() -> RateLimiter:
    """Obtener instancia singleton del rate limiter"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter

if __name__ == "__main__":
    import asyncio
    
    async def test():
        limiter = get_rate_limiter()
        
        print("=== RATE LIMITER TEST ===")
        
        # Test adquisición normal
        for i in range(5):
            acquired = await limiter.acquire('gpt-5-mini', 100)
            print(f"Request {i+1}: {'✅ Allowed' if acquired else '❌ Throttled'}")
        
        # Test circuit breaker
        print("\n=== CIRCUIT BREAKER TEST ===")
        
        # Simular fallos
        for i in range(6):
            limiter.report_failure('gpt-5', Exception("Test error"))
        
        status = limiter.get_status('gpt-5')
        print(f"GPT-5 Circuit State: {status['circuit_state']}")
        
        # Intentar request con circuito abierto
        acquired = await limiter.acquire('gpt-5')
        print(f"Request with open circuit: {'✅ Allowed' if acquired else '❌ Blocked'}")
        
        print(f"\nGlobal Status: {limiter.get_status()}")
    
    asyncio.run(test())