#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 L1 Cache Redis - Cache caliente para respuestas ultrarrápidas
Cache de primer nivel con TTL dinámico por categoría
"""

import json
import redis
import hashlib
import logging
from typing import Dict, Any, Optional, List
from datetime import timedelta
import pickle

logger = logging.getLogger(__name__)

class L1RedisCache:
    """Cache L1 con Redis para hits <200ms"""
    
    def __init__(self, 
                 host: str = "localhost",
                 port: int = 6379,
                 db: int = 0,
                 password: str = None,
                 use_mock: bool = False):
        """
        Inicializar cache L1
        
        Args:
            use_mock: Si True, usa diccionario en memoria (para desarrollo sin Redis)
        """
        self.use_mock = use_mock
        self.namespace = "norm:v2"
        self.version = "2.0"
        
        if use_mock:
            # Mock para desarrollo/testing
            self.mock_cache = {}
            self.mock_ttls = {}
            logger.warning("🟡 Using MOCK Redis (in-memory). Install Redis for production.")
        else:
            try:
                self.redis_client = redis.Redis(
                    host=host,
                    port=port,
                    db=db,
                    password=password,
                    decode_responses=False,  # Usaremos pickle para objetos complejos
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test conexión
                self.redis_client.ping()
                logger.info(f"✅ Redis L1 Cache connected: {host}:{port}")
            except Exception as e:
                logger.warning(f"⚠️ Redis not available, using mock: {e}")
                self.use_mock = True
                self.mock_cache = {}
                self.mock_ttls = {}
        
        # TTLs por categoría (segundos)
        self.ttl_config = {
            # Productos tecnológicos (cambian frecuentemente)
            'smartphones': 86400,      # 1 día
            'notebooks': 86400,        # 1 día
            'tablets': 86400,          # 1 día
            'smart_tv': 172800,        # 2 días
            'smartwatches': 86400,     # 1 día
            
            # Productos estables
            'perfumes': 2592000,       # 30 días
            'beauty': 1209600,         # 14 días
            'clothing': 604800,        # 7 días
            'shoes': 604800,           # 7 días
            
            # Productos muy volátiles
            'groceries': 3600,         # 1 hora
            'beverages': 7200,         # 2 horas
            'fresh_food': 1800,        # 30 minutos
            
            # Default
            'default': 43200           # 12 horas
        }
        
        # Estadísticas
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'errors': 0
        }
    
    def _get_key(self, fingerprint: str) -> str:
        """Generar clave con namespace y versión"""
        return f"{self.namespace}:{self.version}:{fingerprint}"
    
    def _get_ttl(self, category: str) -> int:
        """Obtener TTL para categoría"""
        return self.ttl_config.get(category, self.ttl_config['default'])
    
    def get(self, fingerprint: str) -> Optional[Dict[str, Any]]:
        """
        Obtener del cache L1
        
        Returns:
            Datos normalizados o None si no existe
        """
        key = self._get_key(fingerprint)
        
        try:
            if self.use_mock:
                # Mock implementation
                if key in self.mock_cache:
                    self.stats['hits'] += 1
                    logger.debug(f"✨ L1 Cache HIT (mock): {fingerprint[:8]}...")
                    return self.mock_cache[key]
                else:
                    self.stats['misses'] += 1
                    return None
            else:
                # Redis real
                data = self.redis_client.get(key)
                
                if data:
                    self.stats['hits'] += 1
                    
                    # Incrementar contador de hits
                    self.redis_client.hincrby(f"{key}:meta", "hits", 1)
                    
                    # Deserializar
                    result = pickle.loads(data)
                    logger.debug(f"✨ L1 Cache HIT: {fingerprint[:8]}... (TTL: {self.redis_client.ttl(key)}s)")
                    return result
                else:
                    self.stats['misses'] += 1
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting from L1 cache: {e}")
            self.stats['errors'] += 1
            return None
    
    def set(self, fingerprint: str, data: Dict[str, Any], 
            category: str = None, ttl_override: int = None) -> bool:
        """
        Guardar en cache L1
        
        Args:
            fingerprint: Identificador único
            data: Datos a cachear
            category: Categoría para TTL
            ttl_override: TTL específico (override config)
        
        Returns:
            True si se guardó correctamente
        """
        key = self._get_key(fingerprint)
        ttl = ttl_override or self._get_ttl(category)
        
        try:
            if self.use_mock:
                # Mock implementation
                self.mock_cache[key] = data
                self.mock_ttls[key] = ttl
                self.stats['sets'] += 1
                logger.debug(f"💾 L1 Cache SET (mock): {fingerprint[:8]}... (TTL: {ttl}s)")
                return True
            else:
                # Redis real
                # Serializar con pickle para mantener tipos complejos
                serialized = pickle.dumps(data)
                
                # Guardar con TTL
                self.redis_client.setex(key, ttl, serialized)
                
                # Guardar metadata
                meta_key = f"{key}:meta"
                self.redis_client.hset(meta_key, mapping={
                    "category": category or "unknown",
                    "hits": 0,
                    "ttl_original": ttl
                })
                self.redis_client.expire(meta_key, ttl)
                
                self.stats['sets'] += 1
                logger.debug(f"💾 L1 Cache SET: {fingerprint[:8]}... (TTL: {ttl}s)")
                return True
                
        except Exception as e:
            logger.error(f"Error setting L1 cache: {e}")
            self.stats['errors'] += 1
            return False
    
    def delete(self, fingerprint: str) -> bool:
        """Eliminar del cache"""
        key = self._get_key(fingerprint)
        
        try:
            if self.use_mock:
                if key in self.mock_cache:
                    del self.mock_cache[key]
                    if key in self.mock_ttls:
                        del self.mock_ttls[key]
                    return True
                return False
            else:
                result = self.redis_client.delete(key, f"{key}:meta")
                return result > 0
                
        except Exception as e:
            logger.error(f"Error deleting from L1 cache: {e}")
            return False
    
    def exists(self, fingerprint: str) -> bool:
        """Verificar si existe en cache"""
        key = self._get_key(fingerprint)
        
        try:
            if self.use_mock:
                return key in self.mock_cache
            else:
                return self.redis_client.exists(key) > 0
        except:
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cache"""
        hit_rate = 0
        total = self.stats['hits'] + self.stats['misses']
        if total > 0:
            hit_rate = self.stats['hits'] / total
        
        stats = {
            **self.stats,
            'hit_rate': f"{hit_rate:.1%}",
            'total_requests': total
        }
        
        if not self.use_mock:
            try:
                # Info adicional de Redis
                info = self.redis_client.info('memory')
                stats['redis_memory'] = info.get('used_memory_human', 'N/A')
                stats['redis_keys'] = self.redis_client.dbsize()
            except:
                pass
        
        return stats
    
    def clear_stats(self):
        """Limpiar estadísticas"""
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'errors': 0
        }
    
    def flush_pattern(self, pattern: str = None):
        """Limpiar cache por patrón"""
        if self.use_mock:
            if pattern:
                keys_to_delete = [k for k in self.mock_cache.keys() if pattern in k]
                for k in keys_to_delete:
                    del self.mock_cache[k]
            else:
                self.mock_cache.clear()
                self.mock_ttls.clear()
        else:
            try:
                pattern = pattern or f"{self.namespace}:*"
                cursor = 0
                while True:
                    cursor, keys = self.redis_client.scan(cursor, match=pattern, count=100)
                    if keys:
                        self.redis_client.delete(*keys)
                    if cursor == 0:
                        break
            except Exception as e:
                logger.error(f"Error flushing cache: {e}")
    
    def warmup(self, products: List[Dict[str, Any]], category: str = None):
        """
        Pre-calentar cache con productos
        Útil después de limpiar o al iniciar
        """
        warmed = 0
        for product in products:
            if 'fingerprint' in product and 'normalized_data' in product:
                if self.set(product['fingerprint'], product['normalized_data'], category):
                    warmed += 1
        
        logger.info(f"🔥 Cache warmed up with {warmed} products")
        return warmed
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Obtener uso de memoria"""
        if self.use_mock:
            import sys
            size = sum(sys.getsizeof(v) for v in self.mock_cache.values())
            return {
                'type': 'mock',
                'entries': len(self.mock_cache),
                'size_bytes': size,
                'size_human': f"{size/1024:.1f}KB"
            }
        else:
            try:
                info = self.redis_client.info('memory')
                return {
                    'type': 'redis',
                    'used_memory': info.get('used_memory_human'),
                    'peak_memory': info.get('used_memory_peak_human'),
                    'keys': self.redis_client.dbsize()
                }
            except:
                return {'error': 'Could not get memory info'}
    
    def adjust_ttl(self, category: str, new_ttl: int):
        """Ajustar TTL para una categoría dinámicamente"""
        old_ttl = self.ttl_config.get(category, self.ttl_config['default'])
        self.ttl_config[category] = new_ttl
        logger.info(f"⚙️ TTL adjusted for {category}: {old_ttl}s → {new_ttl}s")

# ============================================================================
# Cache Manager con fallback automático
# ============================================================================

class CacheManager:
    """Gestor de cache con fallback L1 → L2 → L3"""
    
    def __init__(self, l1_cache: L1RedisCache = None, 
                 l2_cache: Any = None, 
                 l3_cache: Any = None):
        self.l1 = l1_cache or L1RedisCache(use_mock=True)
        self.l2 = l2_cache  # Semantic cache (pgvector)
        self.l3 = l3_cache  # PostgreSQL persistent
    
    async def get(self, fingerprint: str) -> Optional[Dict[str, Any]]:
        """Buscar en cache con fallback L1 → L2 → L3"""
        
        # L1: Redis (más rápido)
        result = self.l1.get(fingerprint)
        if result:
            return result
        
        # L2: Semantic cache
        if self.l2:
            result = await self.l2.find_similar(fingerprint)
            if result:
                # Promover a L1
                self.l1.set(fingerprint, result, result.get('category'))
                return result
        
        # L3: PostgreSQL
        if self.l3:
            result = self.l3.get(fingerprint)
            if result:
                # Promover a L1
                self.l1.set(fingerprint, result, result.get('category'))
                return result
        
        return None
    
    async def set(self, fingerprint: str, data: Dict[str, Any], category: str = None):
        """Guardar en todos los niveles de cache"""
        
        # L1: Siempre
        self.l1.set(fingerprint, data, category)
        
        # L2: Si tiene embedding
        if self.l2 and 'embedding' in data:
            await self.l2.store(fingerprint, data['embedding'], data)
        
        # L3: Siempre (persistente)
        if self.l3:
            self.l3.set(fingerprint, data)

# Singleton
_l1_cache = None

def get_l1_cache() -> L1RedisCache:
    """Obtener instancia singleton del cache L1"""
    global _l1_cache
    if _l1_cache is None:
        # Intentar conectar a Redis, fallback a mock
        try:
            _l1_cache = L1RedisCache(
                host="localhost",
                port=6379,
                use_mock=False
            )
        except:
            logger.warning("Redis not available, using mock cache")
            _l1_cache = L1RedisCache(use_mock=True)
    return _l1_cache

if __name__ == "__main__":
    # Testing
    cache = get_l1_cache()
    
    # Test set/get
    test_data = {
        "brand": "APPLE",
        "model": "iPhone 15 Pro Max",
        "normalized_name": "APPLE iPhone 15 Pro Max 256GB Negro",
        "attributes": {
            "capacity": "256GB",
            "color": "negro"
        },
        "confidence": 0.92
    }
    
    fingerprint = "test_" + hashlib.sha1("test_product".encode()).hexdigest()[:8]
    
    print("=== L1 CACHE TEST ===")
    print(f"Setting cache for: {fingerprint}")
    cache.set(fingerprint, test_data, "smartphones")
    
    print("Getting from cache...")
    result = cache.get(fingerprint)
    print(f"Result: {result is not None}")
    
    print(f"\nStats: {cache.get_stats()}")
    print(f"Memory: {cache.get_memory_usage()}")