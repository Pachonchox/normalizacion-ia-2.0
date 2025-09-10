#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 GPT-5 Metrics Collector
Sistema de monitoreo y métricas para tracking de costos, performance y calidad
"""

from __future__ import annotations
import time
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RequestMetric:
    """Métrica individual de request"""
    timestamp: float
    model: str
    latency_ms: float
    tokens_used: int
    cost_usd: float
    cache_hit: bool
    batch_mode: bool
    complexity_score: float
    success: bool
    error: Optional[str] = None


@dataclass
class BatchMetric:
    """Métrica de procesamiento batch"""
    batch_id: str
    timestamp: float
    model: str
    product_count: int
    total_tokens: int
    total_cost_usd: float
    processing_time_seconds: float
    success_rate: float


class MetricsCollector:
    """
    Colector centralizado de métricas para GPT-5
    """
    
    def __init__(self, persist_path: str = "out/metrics"):
        self.metrics = {
            'requests': [],
            'batches': [],
            'models': defaultdict(lambda: {
                'total_requests': 0,
                'total_tokens': 0,
                'total_cost': 0.0,
                'avg_latency': 0.0,
                'success_rate': 0.0
            }),
            'cache': {
                'hits': 0,
                'misses': 0,
                'semantic_hits': 0
            },
            'costs': {
                'hourly': defaultdict(float),
                'daily': defaultdict(float),
                'total': 0.0
            }
        }
        
        self.persist_path = Path(persist_path)
        self.persist_path.mkdir(parents=True, exist_ok=True)
        
        # Cargar métricas históricas si existen
        self._load_historical_metrics()
    
    def track_request(self, model: str, latency_ms: float, tokens: int,
                     cost: float, cache_hit: bool = False, batch: bool = False,
                     complexity: float = 0.5, success: bool = True, 
                     error: str = None):
        """Registra métrica de request individual"""
        
        metric = RequestMetric(
            timestamp=time.time(),
            model=model,
            latency_ms=latency_ms,
            tokens_used=tokens,
            cost_usd=cost,
            cache_hit=cache_hit,
            batch_mode=batch,
            complexity_score=complexity,
            success=success,
            error=error
        )
        
        self.metrics['requests'].append(metric)
        
        # Actualizar agregados por modelo
        model_stats = self.metrics['models'][model]
        model_stats['total_requests'] += 1
        model_stats['total_tokens'] += tokens
        model_stats['total_cost'] += cost
        
        # Actualizar latencia promedio
        n = model_stats['total_requests']
        model_stats['avg_latency'] = (
            (model_stats['avg_latency'] * (n - 1) + latency_ms) / n
        )
        
        # Actualizar success rate
        if success:
            success_count = model_stats.get('success_count', 0) + 1
            model_stats['success_count'] = success_count
            model_stats['success_rate'] = success_count / n
        
        # Actualizar cache stats
        if cache_hit:
            self.metrics['cache']['hits'] += 1
        else:
            self.metrics['cache']['misses'] += 1
        
        # Actualizar costos
        self._update_costs(cost)
        
        # Log si es significativo
        if cost > 0.1:  # Más de 10 centavos
            logger.info(f"💰 High cost request: ${cost:.3f} using {model}")
    
    def track_batch(self, batch_id: str, model: str, product_count: int,
                   tokens: int, cost: float, processing_time: float,
                   success_rate: float):
        """Registra métrica de batch processing"""
        
        metric = BatchMetric(
            batch_id=batch_id,
            timestamp=time.time(),
            model=model,
            product_count=product_count,
            total_tokens=tokens,
            total_cost_usd=cost,
            processing_time_seconds=processing_time,
            success_rate=success_rate
        )
        
        self.metrics['batches'].append(metric)
        
        # Log batch completion
        logger.info(f"📦 Batch completed: {product_count} products, ${cost:.2f}, {success_rate:.1%} success")
    
    def _update_costs(self, cost: float):
        """Actualiza tracking de costos"""
        now = datetime.now()
        
        # Costo por hora
        hour_key = now.strftime("%Y-%m-%d_%H")
        self.metrics['costs']['hourly'][hour_key] += cost
        
        # Costo por día
        day_key = now.strftime("%Y-%m-%d")
        self.metrics['costs']['daily'][day_key] += cost
        
        # Costo total
        self.metrics['costs']['total'] += cost
    
    def get_current_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas actuales"""
        
        total_requests = len(self.metrics['requests'])
        if total_requests == 0:
            return {'message': 'No metrics collected yet'}
        
        # Calcular estadísticas agregadas
        recent_requests = [r for r in self.metrics['requests'][-100:]]  # Últimas 100
        
        avg_latency = sum(r.latency_ms for r in recent_requests) / len(recent_requests)
        cache_hit_rate = self.metrics['cache']['hits'] / max(
            self.metrics['cache']['hits'] + self.metrics['cache']['misses'], 1
        )
        
        # Distribución por modelo
        model_distribution = {}
        for model, stats in self.metrics['models'].items():
            if stats['total_requests'] > 0:
                model_distribution[model] = {
                    'requests': stats['total_requests'],
                    'percentage': stats['total_requests'] / total_requests * 100,
                    'avg_latency_ms': stats['avg_latency'],
                    'total_cost': stats['total_cost'],
                    'success_rate': stats['success_rate']
                }
        
        # Costos
        now = datetime.now()
        today_cost = self.metrics['costs']['daily'].get(now.strftime("%Y-%m-%d"), 0.0)
        hour_cost = self.metrics['costs']['hourly'].get(now.strftime("%Y-%m-%d_%H"), 0.0)
        
        return {
            'total_requests': total_requests,
            'total_batches': len(self.metrics['batches']),
            'avg_latency_ms': round(avg_latency, 2),
            'cache_hit_rate': round(cache_hit_rate, 3),
            'model_distribution': model_distribution,
            'costs': {
                'last_hour': round(hour_cost, 2),
                'today': round(today_cost, 2),
                'total': round(self.metrics['costs']['total'], 2)
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def get_cost_breakdown(self, period: str = "daily") -> Dict[str, float]:
        """
        Obtiene desglose de costos por período
        period: 'hourly', 'daily'
        """
        if period == "hourly":
            costs = dict(self.metrics['costs']['hourly'])
        else:
            costs = dict(self.metrics['costs']['daily'])
        
        # Ordenar por fecha
        return dict(sorted(costs.items()))
    
    def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Obtiene tendencias de performance"""
        
        cutoff = time.time() - (hours * 3600)
        recent = [r for r in self.metrics['requests'] if r.timestamp > cutoff]
        
        if not recent:
            return {'message': f'No data in last {hours} hours'}
        
        # Agrupar por hora
        hourly_stats = defaultdict(lambda: {
            'requests': 0,
            'avg_latency': 0.0,
            'cache_hits': 0,
            'errors': 0
        })
        
        for req in recent:
            hour = datetime.fromtimestamp(req.timestamp).strftime("%Y-%m-%d_%H")
            stats = hourly_stats[hour]
            stats['requests'] += 1
            stats['avg_latency'] = (
                (stats['avg_latency'] * (stats['requests'] - 1) + req.latency_ms) 
                / stats['requests']
            )
            if req.cache_hit:
                stats['cache_hits'] += 1
            if not req.success:
                stats['errors'] += 1
        
        return dict(hourly_stats)
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """Verifica condiciones de alerta"""
        
        alerts = []
        
        # Alerta de costo alto
        hour_cost = self.metrics['costs']['hourly'].get(
            datetime.now().strftime("%Y-%m-%d_%H"), 0.0
        )
        if hour_cost > 10.0:  # Más de $10 USD/hora
            alerts.append({
                'level': 'warning',
                'type': 'high_cost',
                'message': f'High hourly cost: ${hour_cost:.2f}',
                'timestamp': datetime.now().isoformat()
            })
        
        # Alerta de latencia alta
        recent = [r for r in self.metrics['requests'][-20:]]
        if recent:
            avg_latency = sum(r.latency_ms for r in recent) / len(recent)
            if avg_latency > 5000:  # Más de 5 segundos
                alerts.append({
                    'level': 'warning',
                    'type': 'high_latency',
                    'message': f'High average latency: {avg_latency:.0f}ms',
                    'timestamp': datetime.now().isoformat()
                })
        
        # Alerta de errores
        recent_errors = sum(1 for r in recent if not r.success)
        if recent_errors > 5:
            alerts.append({
                'level': 'error',
                'type': 'high_error_rate',
                'message': f'{recent_errors} errors in last 20 requests',
                'timestamp': datetime.now().isoformat()
            })
        
        return alerts
    
    def save_metrics(self):
        """Persiste métricas a disco"""
        
        # Convertir dataclasses a dict para serialización
        data = {
            'requests': [asdict(r) for r in self.metrics['requests'][-1000:]],  # Últimas 1000
            'batches': [asdict(b) for b in self.metrics['batches'][-100:]],  # Últimos 100
            'models': dict(self.metrics['models']),
            'cache': self.metrics['cache'],
            'costs': {
                'hourly': dict(self.metrics['costs']['hourly']),
                'daily': dict(self.metrics['costs']['daily']),
                'total': self.metrics['costs']['total']
            },
            'saved_at': datetime.now().isoformat()
        }
        
        file_path = self.persist_path / f"metrics_{datetime.now().strftime('%Y%m%d')}.json"
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"💾 Metrics saved to {file_path}")
    
    def _load_historical_metrics(self):
        """Carga métricas históricas si existen"""
        
        today_file = self.persist_path / f"metrics_{datetime.now().strftime('%Y%m%d')}.json"
        
        if today_file.exists():
            try:
                with open(today_file, 'r') as f:
                    data = json.load(f)
                
                # Restaurar costos históricos
                self.metrics['costs']['daily'] = defaultdict(float, data.get('costs', {}).get('daily', {}))
                self.metrics['costs']['total'] = data.get('costs', {}).get('total', 0.0)
                
                logger.info(f"📈 Loaded historical metrics from {today_file}")
                
            except Exception as e:
                logger.error(f"Failed to load metrics: {e}")
    
    def generate_report(self) -> str:
        """Genera reporte formateado de métricas"""
        
        stats = self.get_current_stats()
        
        report = f"""
📊 GPT-5 METRICS REPORT
{'=' * 50}

📈 GENERAL STATS
- Total Requests: {stats.get('total_requests', 0):,}
- Total Batches: {stats.get('total_batches', 0):,}
- Avg Latency: {stats.get('avg_latency_ms', 0):.2f}ms
- Cache Hit Rate: {stats.get('cache_hit_rate', 0):.1%}

💰 COSTS
- Last Hour: ${stats.get('costs', {}).get('last_hour', 0):.2f}
- Today: ${stats.get('costs', {}).get('today', 0):.2f}
- Total: ${stats.get('costs', {}).get('total', 0):.2f}

🎯 MODEL DISTRIBUTION
"""
        
        for model, data in stats.get('model_distribution', {}).items():
            report += f"- {model}: {data['requests']:,} requests ({data['percentage']:.1f}%), ${data['total_cost']:.2f}\n"
        
        report += f"\n📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return report


if __name__ == "__main__":
    # Test del colector de métricas
    collector = MetricsCollector()
    
    # Simular algunas métricas
    import random
    
    models = ["gpt-5-mini", "gpt-5", "gpt-4o-mini"]
    
    for i in range(50):
        model = random.choice(models)
        latency = random.uniform(500, 3000)
        tokens = random.randint(100, 500)
        cost = tokens / 1000 * (0.0003 if "mini" in model else 0.001)
        cache_hit = random.random() > 0.7
        
        collector.track_request(
            model=model,
            latency_ms=latency,
            tokens=tokens,
            cost=cost,
            cache_hit=cache_hit,
            complexity=random.random(),
            success=random.random() > 0.05
        )
    
    # Simular batch
    collector.track_batch(
        batch_id="test_batch_001",
        model="gpt-5-mini",
        product_count=1000,
        tokens=100000,
        cost=15.0,
        processing_time=120.5,
        success_rate=0.98
    )
    
    # Mostrar reporte
    print(collector.generate_report())
    
    # Verificar alertas
    alerts = collector.check_alerts()
    if alerts:
        print("\n⚠️ ALERTS:")
        for alert in alerts:
            print(f"  - [{alert['level']}] {alert['message']}")
    
    # Guardar métricas
    collector.save_metrics()