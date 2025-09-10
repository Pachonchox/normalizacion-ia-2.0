#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Tests de Validación para Migración GPT-5
Suite completa de tests para validar routing, batch processing y ahorros
"""

import pytest
import asyncio
import json
from typing import List, Dict, Any
from unittest.mock import Mock, patch, AsyncMock

# Agregar src al path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gpt5.router import GPT5Router, ModelType, ComplexityAnalyzer
from gpt5.batch.processor import BatchProcessor, BatchOrchestrator
from gpt5.cache.semantic_cache import SemanticCache
from gpt5.prompt_optimizer import PromptOptimizer, PromptStyle
from gpt5.monitoring.metrics_collector import MetricsCollector


class TestGPT5Router:
    """Tests para el router inteligente"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.router = GPT5Router()
        self.test_products = [
            {
                "name": "iPhone 15 Pro Max 256GB Negro",
                "category": "smartphones",
                "price": 1200000
            },
            {
                "name": "Coca Cola 500ml",
                "category": "beverages", 
                "price": 1500
            },
            {
                "name": "MacBook Pro M3 32GB RAM 1TB SSD",
                "category": "notebooks",
                "price": 3500000
            },
            {
                "name": "Perfume Chanel No 5 100ml",
                "category": "perfumes",
                "price": 150000
            }
        ]
    
    def test_complexity_calculation(self):
        """Test cálculo de complejidad"""
        analyzer = ComplexityAnalyzer()
        
        # Producto simple
        simple = {"name": "Agua mineral 500ml", "category": "beverages", "price": 1000}
        complexity = analyzer.calculate_complexity(simple)
        assert complexity < 0.35, f"Producto simple debería tener complejidad < 0.35, got {complexity}"
        
        # Producto complejo
        complex = {
            "name": "ASUS ROG Strix G16 RTX 4070 Ti 32GB DDR5 2TB NVMe",
            "category": "notebooks",
            "price": 2800000
        }
        complexity = analyzer.calculate_complexity(complex)
        assert complexity > 0.7, f"Producto complejo debería tener complejidad > 0.7, got {complexity}"
    
    def test_routing_distribution(self):
        """Test distribución de routing"""
        # Procesar productos de prueba
        batches = self.router.route_batch(self.test_products * 25)  # 100 productos
        
        # Verificar que hay distribución
        assert len(batches[ModelType.GPT5_MINI]) > 0, "Debería haber productos para GPT-5-mini"
        assert len(batches[ModelType.GPT5]) > 0, "Debería haber productos para GPT-5"
        
        # Verificar que GPT-5-mini tiene mayoría (productos simples)
        total = sum(len(b) for b in batches.values())
        mini_percentage = len(batches[ModelType.GPT5_MINI]) / total
        assert mini_percentage > 0.5, f"GPT-5-mini debería procesar >50%, got {mini_percentage:.1%}"
    
    def test_cost_savings_estimation(self):
        """Test estimación de ahorros"""
        products = self.test_products * 100  # 400 productos
        savings = self.router.estimate_savings(products)
        
        assert savings['total_products'] == 400
        assert savings['savings_percent'] > 30, "Debería ahorrar al menos 30%"
        assert savings['optimized_cost_usd'] < savings['baseline_cost_usd']
        
        print(f"\n💰 Savings Test Results:")
        print(f"  Baseline: ${savings['baseline_cost_usd']:.2f}")
        print(f"  Optimized: ${savings['optimized_cost_usd']:.2f}")
        print(f"  Savings: {savings['savings_percent']:.1f}%")
    
    def test_fallback_chain(self):
        """Test cadena de fallback"""
        chain = self.router.get_fallback_chain(ModelType.GPT5_MINI)
        assert chain[0] == ModelType.GPT5_MINI
        assert ModelType.GPT4O_MINI in chain, "Debería incluir GPT-4o-mini como fallback"


class TestBatchProcessor:
    """Tests para procesamiento batch"""
    
    @pytest.fixture
    def processor(self):
        """Fixture para batch processor"""
        return BatchProcessor(api_key="test_key")
    
    @pytest.mark.asyncio
    async def test_batch_file_creation(self, processor):
        """Test creación de archivo batch"""
        products = [
            {"name": f"Product {i}", "category": "test", "price": 1000 * i}
            for i in range(10)
        ]
        
        file_path, batch_id = await processor.create_batch_file(
            products,
            "gpt-5-mini",
            "Normalize: {name}"
        )
        
        # Verificar que se creó el archivo
        from pathlib import Path
        assert Path(file_path).exists()
        assert batch_id.startswith("batch_")
        
        # Verificar contenido JSONL
        with open(file_path, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 10, "Debería tener 10 líneas JSONL"
            
            # Verificar estructura de primera línea
            first = json.loads(lines[0])
            assert first['method'] == "POST"
            assert first['url'] == "/v1/chat/completions"
            assert 'body' in first
            assert first['body']['model'] == "gpt-5-mini"
    
    def test_cost_estimation_with_discount(self, processor):
        """Test estimación de costos con descuento batch"""
        products = [{"name": f"Product {i}"} for i in range(1000)]
        
        # Costo sin batch (normal)
        normal_cost = (1000 * 250 / 1000) * 0.0003  # 1000 productos * 250 tokens * precio
        
        # Costo con batch (50% descuento)
        batch_cost = processor._estimate_cost(products, "gpt-5-mini")
        
        assert batch_cost < normal_cost
        assert batch_cost == pytest.approx(normal_cost * 0.5, rel=0.1)
        
        print(f"\n💵 Cost Comparison:")
        print(f"  Normal: ${normal_cost:.2f}")
        print(f"  Batch: ${batch_cost:.2f}")
        print(f"  Savings: ${normal_cost - batch_cost:.2f} (50%)")


class TestSemanticCache:
    """Tests para cache semántico"""
    
    @pytest.mark.asyncio
    async def test_semantic_similarity(self):
        """Test búsqueda por similitud semántica"""
        cache = SemanticCache(backend="memory", similarity_threshold=0.85)
        
        # Mock del embedding generation
        async def mock_embedding(text):
            # Simular embeddings basados en hash del texto
            import hashlib
            import numpy as np
            seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
            np.random.seed(seed)
            return np.random.randn(1536)
        
        cache.generate_embedding = mock_embedding
        
        # Producto original
        product1 = {
            'name': 'iPhone 15 Pro Max 256GB Negro',
            'brand': 'APPLE',
            'category': 'smartphones'
        }
        normalized1 = {'brand': 'APPLE', 'model': 'iPhone 15 Pro Max'}
        
        await cache.store(product1, normalized1)
        
        # Producto similar (diferente color)
        product2 = {
            'name': 'iPhone 15 Pro Max 256GB Blanco',  # Solo cambia color
            'brand': 'APPLE',
            'category': 'smartphones'
        }
        
        # No debería encontrar match exacto pero sí semántico
        result = await cache.find_similar(product2)
        
        # Verificar estadísticas
        stats = cache.get_stats()
        assert stats['total_queries'] > 0
        
        print(f"\n🧠 Cache Stats:")
        print(f"  Queries: {stats['total_queries']}")
        print(f"  Hits: {stats.get('hits', 0)}")
        print(f"  Semantic Hits: {stats.get('semantic_hits', 0)}")


class TestPromptOptimizer:
    """Tests para optimización de prompts"""
    
    def setup_method(self):
        self.optimizer = PromptOptimizer()
    
    def test_prompt_styles(self):
        """Test diferentes estilos de prompt"""
        product = {
            "name": "Samsung Galaxy S24 Ultra 512GB",
            "category": "smartphones",
            "price": 1500000
        }
        
        # Minimal prompt
        minimal = self.optimizer.optimize_prompt(product, "gpt-5-mini", PromptStyle.MINIMAL)
        assert len(minimal) < 100, "Prompt minimal debería ser < 100 chars"
        
        # Detailed prompt
        detailed = self.optimizer.optimize_prompt(product, "gpt-5", PromptStyle.DETAILED)
        assert len(detailed) > 300, "Prompt detailed debería ser > 300 chars"
        
        # Batch prompt (ultra-optimizado)
        product['_batch_mode'] = True
        batch = self.optimizer.optimize_prompt(product, "gpt-5-mini")
        assert len(batch) < 80, "Batch prompt debería ser ultra-compacto"
        
        print(f"\n📝 Prompt Lengths:")
        print(f"  Minimal: {len(minimal)} chars")
        print(f"  Detailed: {len(detailed)} chars")
        print(f"  Batch: {len(batch)} chars")
    
    def test_token_estimation(self):
        """Test estimación de tokens"""
        prompt = "Este es un prompt de prueba para estimar tokens"
        
        estimates = {
            PromptStyle.MINIMAL: self.optimizer.estimate_tokens(prompt, PromptStyle.MINIMAL),
            PromptStyle.STANDARD: self.optimizer.estimate_tokens(prompt, PromptStyle.STANDARD),
            PromptStyle.DETAILED: self.optimizer.estimate_tokens(prompt, PromptStyle.DETAILED)
        }
        
        # Verificar que MINIMAL < STANDARD < DETAILED
        assert estimates[PromptStyle.MINIMAL] < estimates[PromptStyle.STANDARD]
        assert estimates[PromptStyle.STANDARD] < estimates[PromptStyle.DETAILED]


class TestMetricsCollector:
    """Tests para colector de métricas"""
    
    def test_cost_tracking(self):
        """Test tracking de costos"""
        collector = MetricsCollector()
        
        # Simular requests
        for i in range(10):
            collector.track_request(
                model="gpt-5-mini",
                latency_ms=1000 + i * 100,
                tokens=200,
                cost=0.06,  # 200 tokens * 0.0003
                cache_hit=i % 3 == 0,
                complexity=0.3
            )
        
        stats = collector.get_current_stats()
        
        assert stats['total_requests'] == 10
        assert stats['costs']['total'] == pytest.approx(0.6, rel=0.01)
        assert stats['cache_hit_rate'] > 0
        
        print(f"\n📊 Metrics Summary:")
        print(f"  Total Requests: {stats['total_requests']}")
        print(f"  Cache Hit Rate: {stats['cache_hit_rate']:.1%}")
        print(f"  Total Cost: ${stats['costs']['total']:.2f}")
    
    def test_alert_generation(self):
        """Test generación de alertas"""
        collector = MetricsCollector()
        
        # Simular alto costo
        for _ in range(100):
            collector.track_request(
                model="gpt-5",
                latency_ms=6000,  # Alta latencia
                tokens=500,
                cost=0.5,  # Alto costo
                success=False  # Error
            )
        
        alerts = collector.check_alerts()
        assert len(alerts) > 0, "Debería generar alertas"
        
        # Verificar tipos de alerta
        alert_types = {alert['type'] for alert in alerts}
        assert 'high_cost' in alert_types or 'high_latency' in alert_types


class TestIntegration:
    """Tests de integración end-to-end"""
    
    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        """Test pipeline completo con todos los componentes"""
        
        # Crear productos de prueba
        products = [
            {"name": f"iPhone 15 {variant}", "category": "smartphones", "price": 1000000}
            for variant in ["128GB", "256GB", "512GB", "1TB"]
        ] * 25  # 100 productos
        
        # 1. Router
        router = GPT5Router()
        batches = router.route_batch(products)
        optimized = router.optimize_batches(batches)
        
        assert len(optimized) > 0, "Debería crear batches optimizados"
        
        # 2. Prompt Optimizer
        optimizer = PromptOptimizer()
        for batch in optimized[:1]:  # Test primer batch
            prompts = optimizer.optimize_batch_prompts(
                batch['products'],
                batch['model']
            )
            assert len(prompts) == len(batch['products'])
        
        # 3. Estimación de costos
        savings = router.estimate_savings(products)
        assert savings['savings_percent'] > 40, "Debería ahorrar >40% con batch + routing"
        
        print(f"\n🎯 Integration Test Results:")
        print(f"  Products: {len(products)}")
        print(f"  Batches: {len(optimized)}")
        print(f"  Estimated Savings: {savings['savings_percent']:.1f}%")
        print(f"  Cost Reduction: ${savings['savings_usd']:.2f}")


if __name__ == "__main__":
    # Ejecutar tests
    pytest.main([__file__, "-v", "--tb=short"])
    
    # También ejecutar algunos tests manuales
    print("\n" + "="*60)
    print("MANUAL VALIDATION TESTS")
    print("="*60)
    
    # Test rápido del router
    router = GPT5Router()
    test_products = [
        {"name": "Coca Cola 2L", "category": "beverages", "price": 2500},
        {"name": "MacBook Pro M3 Max 64GB", "category": "notebooks", "price": 4500000}
    ]
    
    for product in test_products:
        model, complexity = router.route_single(product)
        print(f"\n{product['name']}")
        print(f"  Model: {model.value}")
        print(f"  Complexity: {complexity:.2f}")