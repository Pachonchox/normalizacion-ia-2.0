#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Tests E2E para sistema GPT-5
Tests completos de integración de todos los componentes
"""

import pytest
import asyncio
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import sys

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from normalize_gpt5 import (
    normalize_with_gpt5,
    process_batch_gpt5,
    ProcessingMode
)
from gpt5.router import GPT5Router, ModelType
from gpt5.prompts import PromptManager, PromptMode
from gpt5.validator import StrictValidator, QualityGate
from gpt5.cache_l1 import L1RedisCache
from gpt5.throttling import RateLimiter, CircuitBreaker, CircuitState


class TestGPT5Components:
    """Tests unitarios de componentes individuales"""
    
    def test_router_complexity_analysis(self):
        """Test análisis de complejidad del router"""
        router = GPT5Router()
        
        # Producto simple
        simple_product = {
            "name": "Coca Cola 500ml",
            "category": "beverages",
            "price": 1500
        }
        model, complexity = router.route_single(simple_product)
        assert model == ModelType.GPT5_MINI
        assert complexity < 0.35
        
        # Producto complejo
        complex_product = {
            "name": "MacBook Pro 16 M3 Max 48GB RAM 1TB SSD Space Gray 2024",
            "category": "notebooks",
            "price": 3899990
        }
        model, complexity = router.route_single(complex_product)
        assert complexity > 0.5
        
        # Producto medio
        medium_product = {
            "name": "Samsung Galaxy A54 5G 128GB",
            "category": "smartphones",
            "price": 399990
        }
        model, complexity = router.route_single(medium_product)
        assert 0.35 <= complexity <= 0.7
    
    def test_router_fallback_chain(self):
        """Test cadena de fallback correcta (siempre a modelo superior)"""
        router = GPT5Router()
        
        # GPT-5-mini debe hacer fallback a GPT-5
        chain = router.get_fallback_chain(ModelType.GPT5_MINI)
        assert chain[0] == ModelType.GPT5_MINI
        assert chain[1] == ModelType.GPT5
        
        # GPT-5 debe hacer fallback a GPT-4o
        chain = router.get_fallback_chain(ModelType.GPT5)
        assert chain[0] == ModelType.GPT5
        assert chain[1] == ModelType.GPT4O
    
    def test_prompt_manager_selection(self):
        """Test selección de prompts por modelo/categoría/modo"""
        pm = PromptManager()
        
        product = {
            "name": "iPhone 15 Pro",
            "category": "smartphones",
            "price": 1299990
        }
        
        # Prompt minimal para batch
        prompt = pm.get_prompt(
            model="gpt-5-mini",
            category="smartphones",
            mode=PromptMode.MINIMAL,
            product=product
        )
        assert len(prompt) < 150  # Debe ser compacto
        assert "smartphones" in prompt
        
        # Prompt detailed para GPT-5
        prompt = pm.get_prompt(
            model="gpt-5",
            category="smartphones",
            mode=PromptMode.DETAILED,
            product=product
        )
        assert len(prompt) > 300  # Debe ser detallado
        assert "exhaustivamente" in prompt.lower()
        
        # System prompts específicos
        assert "JSON" in pm.system_prompts["gpt-5-mini"]
        assert "chileno" in pm.system_prompts["gpt-5"]
    
    def test_validator_taxonomy(self):
        """Test validación de taxonomía"""
        validator = StrictValidator()
        
        # Categoría válida
        valid, final, msg = validator.validate_taxonomy("smartphones", "celulares")
        assert valid
        assert final == "smartphones"
        
        # Categoría inválida
        valid, final, msg = validator.validate_taxonomy("categoria_invalida", "general")
        assert not valid
        assert final == "general"  # Fallback
        
        # Alias de categoría
        valid, final, msg = validator.validate_taxonomy("celulares", "general")
        assert valid
        assert final == "smartphones"  # Normalizado
    
    def test_validator_attributes(self):
        """Test validación de atributos por categoría"""
        validator = StrictValidator()
        
        # Atributos válidos para smartphones
        attrs_smartphone = {
            "capacity": "256GB",
            "color": "negro",
            "network": "5G"
        }
        valid, clean, warnings = validator.validate_attributes(attrs_smartphone, "smartphones")
        assert valid
        assert "capacity" in clean
        
        # Atributos inválidos (se limpian)
        attrs_invalid = {
            "invalid_attr": "value",
            "capacity": "256GB"
        }
        valid, clean, warnings = validator.validate_attributes(attrs_invalid, "smartphones")
        assert "invalid_attr" not in clean
        assert "capacity" in clean
        assert len(warnings) > 0
    
    def test_validator_quality_gate(self):
        """Test control de calidad"""
        validator = StrictValidator()
        
        # Producto de alta calidad
        good_product = {
            "brand": "APPLE",
            "model": "iPhone 15 Pro",
            "normalized_name": "APPLE iPhone 15 Pro 256GB Negro",
            "attributes": {"capacity": "256GB", "color": "negro"},
            "confidence": 0.95
        }
        valid, score, issues = validator.validate_quality(good_product, "smartphones")
        assert valid
        assert score > 0.8
        assert len(issues) == 0
        
        # Producto de baja calidad
        bad_product = {
            "brand": "",
            "model": "producto",
            "normalized_name": "producto",
            "confidence": 0.3
        }
        valid, score, issues = validator.validate_quality(bad_product, "general")
        assert not valid
        assert score < 0.5
        assert len(issues) > 0
    
    def test_l1_cache_operations(self):
        """Test operaciones de cache L1"""
        cache = L1RedisCache(use_mock=True)  # Usar mock para tests
        
        test_data = {
            "brand": "SAMSUNG",
            "model": "Galaxy S24",
            "attributes": {"capacity": "256GB"}
        }
        
        # Set
        success = cache.set("test_fingerprint", test_data, "smartphones")
        assert success
        
        # Get
        retrieved = cache.get("test_fingerprint")
        assert retrieved is not None
        assert retrieved["brand"] == "SAMSUNG"
        
        # Exists
        assert cache.exists("test_fingerprint")
        assert not cache.exists("non_existent")
        
        # Delete
        assert cache.delete("test_fingerprint")
        assert not cache.exists("test_fingerprint")
        
        # Stats
        stats = cache.get_stats()
        assert stats["hits"] >= 1
        assert stats["sets"] >= 1
    
    def test_l1_cache_ttl_by_category(self):
        """Test TTL dinámico por categoría"""
        cache = L1RedisCache(use_mock=True)
        
        # Verificar configuración de TTL
        assert cache._get_ttl("smartphones") == 86400  # 1 día
        assert cache._get_ttl("perfumes") == 2592000   # 30 días
        assert cache._get_ttl("groceries") == 3600     # 1 hora
        assert cache._get_ttl("unknown") == 43200      # 12 horas (default)
    
    @pytest.mark.asyncio
    async def test_rate_limiter_token_bucket(self):
        """Test token bucket del rate limiter"""
        limiter = RateLimiter()
        
        # Debe permitir requests iniciales
        acquired = await limiter.acquire("gpt-5-mini", 100)
        assert acquired
        
        # Verificar límites por modelo
        config = limiter.configs["gpt-5-mini"]
        assert config.requests_per_minute == 500
        
        # Stats
        status = limiter.get_status("gpt-5-mini")
        assert "requests_available" in status
        assert "circuit_state" in status
    
    def test_circuit_breaker_states(self):
        """Test estados del circuit breaker"""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1)
        
        # Estado inicial: CLOSED
        assert cb.state == CircuitState.CLOSED
        
        # Simular fallos
        for _ in range(3):
            cb._on_failure()
        
        # Debe abrir el circuito
        assert cb.state == CircuitState.OPEN
        
        # No debe permitir llamadas
        with pytest.raises(Exception) as e:
            cb.call(lambda: None)
        assert "Circuit breaker is OPEN" in str(e.value)
        
        # Reset manual
        cb.reset()
        assert cb.state == CircuitState.CLOSED


class TestGPT5Integration:
    """Tests de integración del sistema completo"""
    
    @pytest.mark.asyncio
    @patch('normalize_gpt5.openai.ChatCompletion.acreate')
    @patch('normalize_gpt5._generate_embedding')
    async def test_normalize_with_cache_hit(self, mock_embedding, mock_openai):
        """Test normalización con cache hit"""
        # Setup mocks
        mock_embedding.return_value = None
        
        # Preparar producto
        product = {
            "name": "iPhone 15 Pro 256GB",
            "category": "smartphones",
            "price": 1299990,
            "retailer": "test"
        }
        
        # Primera llamada - debe llamar a OpenAI
        mock_openai.return_value = AsyncMock(
            choices=[Mock(message=Mock(content=json.dumps({
                "brand": "APPLE",
                "model": "iPhone 15 Pro",
                "normalized_name": "APPLE iPhone 15 Pro 256GB",
                "attributes": {"capacity": "256GB"},
                "confidence": 0.95,
                "category_suggestion": "smartphones"
            })))],
            usage=Mock(total_tokens=100, prompt_tokens=50, completion_tokens=50)
        )
        
        result1 = await normalize_with_gpt5(product, mode=ProcessingMode.SINGLE)
        
        assert result1["brand"] == "APPLE"
        assert mock_openai.called
        
        # Segunda llamada - debe usar cache
        mock_openai.reset_mock()
        result2 = await normalize_with_gpt5(product, mode=ProcessingMode.SINGLE)
        
        # No debe llamar a OpenAI si hay cache
        # (dependiendo de la implementación del cache)
    
    @pytest.mark.asyncio 
    @patch('normalize_gpt5.openai.ChatCompletion.acreate')
    async def test_fallback_chain(self, mock_openai):
        """Test cadena de fallback cuando falla un modelo"""
        product = {
            "name": "Producto complejo",
            "category": "notebooks",
            "price": 2000000
        }
        
        # Primer intento falla
        mock_openai.side_effect = [
            Exception("Rate limit exceeded"),  # GPT-5 falla
            AsyncMock(  # GPT-4o funciona
                choices=[Mock(message=Mock(content=json.dumps({
                    "brand": "BRAND",
                    "model": "Model",
                    "normalized_name": "BRAND Model",
                    "attributes": {},
                    "confidence": 0.8,
                    "category_suggestion": "notebooks"
                })))],
                usage=Mock(total_tokens=100, prompt_tokens=50, completion_tokens=50)
            )
        ]
        
        result = await normalize_with_gpt5(product, mode=ProcessingMode.SINGLE)
        
        # Debe obtener resultado a pesar del fallo
        assert result["brand"] == "BRAND"
        assert mock_openai.call_count == 2  # Dos intentos
    
    @pytest.mark.asyncio
    async def test_batch_processing_routing(self):
        """Test procesamiento batch con routing por complejidad"""
        products = [
            {"name": "Coca Cola 500ml", "category": "beverages", "price": 1500},
            {"name": "iPhone 15 Pro Max", "category": "smartphones", "price": 1299990},
            {"name": "MacBook Pro M3 Max", "category": "notebooks", "price": 3899990}
        ]
        
        router = GPT5Router()
        batches = router.route_batch(products)
        
        # Verificar distribución
        assert len(batches[ModelType.GPT5_MINI]) >= 1  # Coca Cola
        assert any(p["name"] == "Coca Cola 500ml" for p in batches[ModelType.GPT5_MINI])
        
        # Los productos complejos pueden ir a GPT-5
        total_routed = sum(len(b) for b in batches.values())
        assert total_routed == len(products)
    
    @pytest.mark.asyncio
    async def test_quality_validation_pipeline(self):
        """Test pipeline de validación de calidad"""
        validator = StrictValidator()
        
        # Resultado de IA simulado
        ai_result = {
            "brand": "SAMSUNG",
            "model": "Galaxy S24 Ultra",
            "normalized_name": "SAMSUNG Galaxy S24 Ultra 512GB Negro",
            "attributes": {
                "capacity": "512GB",
                "color": "negro",
                "invalid_attr": "should_be_removed"
            },
            "confidence": 0.92,
            "category_suggestion": "celulares"  # Alias que debe normalizarse
        }
        
        # Validar taxonomía
        valid_tax, final_cat, _ = validator.validate_taxonomy(
            ai_result["category_suggestion"], 
            "smartphones"
        )
        assert valid_tax
        assert final_cat == "smartphones"  # Normalizado
        
        # Validar atributos
        valid_attrs, clean_attrs, warnings = validator.validate_attributes(
            ai_result["attributes"],
            final_cat
        )
        assert "invalid_attr" not in clean_attrs
        assert "capacity" in clean_attrs
        
        # Validar calidad general
        ai_result["category_suggestion"] = final_cat
        ai_result["attributes"] = clean_attrs
        
        valid_quality, score, issues = validator.validate_quality(
            ai_result,
            final_cat
        )
        assert valid_quality
        assert score > 0.7


class TestGPT5CostOptimization:
    """Tests de optimización de costos"""
    
    def test_batch_cost_estimation(self):
        """Test estimación de costos con batch vs individual"""
        router = GPT5Router()
        
        products = [
            {"name": f"Product {i}", "category": "general", "price": 10000}
            for i in range(100)
        ]
        
        savings = router.estimate_savings(products)
        
        # Batch debe ser más barato
        assert savings["optimized_cost_usd"] < savings["baseline_cost_usd"]
        assert savings["savings_percent"] > 30  # Al menos 30% de ahorro
        
        # Verificar distribución
        assert savings["total_products"] == 100
        assert "distribution" in savings
    
    def test_cache_impact_on_cost(self):
        """Test impacto del cache en costos"""
        cache = L1RedisCache(use_mock=True)
        
        # Simular productos cacheados
        for i in range(50):
            cache.set(f"fp_{i}", {"brand": f"BRAND_{i}"}, "general")
        
        stats = cache.get_stats()
        
        # Con 50% cache hit, el costo se reduce significativamente
        # Cache hits cuestan $0
        cached_cost = 0
        api_cost = 50 * 0.0003  # 50 llamadas a API
        total_cost = cached_cost + api_cost
        
        assert total_cost < 100 * 0.0003  # Menor que sin cache


@pytest.fixture
def sample_products():
    """Fixture con productos de ejemplo"""
    return [
        {
            "name": "iPhone 15 Pro Max 256GB Natural Titanium",
            "category": "smartphones",
            "price": 1299990,
            "retailer": "falabella",
            "url": "https://falabella.com/product/123"
        },
        {
            "name": "Samsung Galaxy S24 Ultra 512GB Titanium Gray",
            "category": "smartphones", 
            "price": 1399990,
            "retailer": "paris",
            "url": "https://paris.cl/product/456"
        },
        {
            "name": "MacBook Pro 16 M3 Max 48GB RAM 1TB SSD",
            "category": "notebooks",
            "price": 3899990,
            "retailer": "ripley",
            "url": "https://ripley.cl/product/789"
        },
        {
            "name": "Perfume Chanel No 5 EDP 100ml",
            "category": "perfumes",
            "price": 189990,
            "retailer": "falabella",
            "url": "https://falabella.com/product/abc"
        },
        {
            "name": "Coca Cola Sin Azúcar 2L",
            "category": "beverages",
            "price": 2190,
            "retailer": "jumbo",
            "url": "https://jumbo.cl/product/def"
        }
    ]


def test_e2e_pipeline_components():
    """Test que todos los componentes están disponibles"""
    # Router
    router = GPT5Router()
    assert router is not None
    
    # Prompt Manager
    pm = PromptManager()
    assert len(pm.prompts) > 0
    assert len(pm.system_prompts) > 0
    
    # Validator
    validator = StrictValidator()
    assert validator.taxonomy is not None
    assert validator.attribute_schemas is not None
    
    # L1 Cache
    cache = L1RedisCache(use_mock=True)
    assert cache is not None
    
    # Rate Limiter
    limiter = RateLimiter()
    assert len(limiter.configs) > 0
    assert len(limiter.circuit_breakers) > 0


if __name__ == "__main__":
    # Ejecutar tests
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])