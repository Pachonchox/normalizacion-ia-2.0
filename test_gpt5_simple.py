#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del Sistema GPT-5 Simple
"""

import sys
import os
import asyncio
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Configurar variables de entorno para testing
os.environ['REDIS_MOCK'] = 'true'
os.environ['OPENAI_API_KEY'] = 'test-key'

async def test_gpt5():
    """Test basico del sistema GPT-5"""
    print("=== TEST SISTEMA GPT-5 ===")
    
    try:
        # 1. Test Router
        print("\n1. Test Router...")
        from gpt5.router import GPT5Router, ModelType
        
        router = GPT5Router()
        
        producto = {
            "name": "iPhone 15 Pro Max 256GB Titanium",
            "category": "smartphones",
            "price": 1299990
        }
        
        model, complexity = router.route_single(producto)
        print(f"   Producto: {producto['name'][:40]}...")
        print(f"   Modelo asignado: {model.value}")
        print(f"   Complejidad: {complexity:.3f}")
        
        # 2. Test Prompts
        print("\n2. Test Prompts...")
        from gpt5.prompts import PromptManager, PromptMode
        
        pm = PromptManager()
        prompt = pm.get_prompt("gpt-5-mini", "smartphones", PromptMode.STANDARD, producto)
        print(f"   Prompt generado: {len(prompt)} caracteres")
        print(f"   Snippet: {prompt[:100]}...")
        
        # 3. Test Validator
        print("\n3. Test Validator...")
        from gpt5.validator import StrictValidator
        
        validator = StrictValidator()
        
        # Test taxonomia
        valid, final_cat, msg = validator.validate_taxonomy("celulares", "general")
        print(f"   Taxonomia 'celulares' -> '{final_cat}' (valido: {valid})")
        
        # 4. Test Cache L1
        print("\n4. Test Cache L1...")
        from gpt5.cache_l1 import L1RedisCache
        
        cache = L1RedisCache(use_mock=True)
        
        test_data = {
            "brand": "APPLE",
            "model": "iPhone 15 Pro Max"
        }
        
        # Test set/get
        cache.set("test_key", test_data, "smartphones")
        retrieved = cache.get("test_key")
        print(f"   Cache funciona: {retrieved is not None}")
        print(f"   Stats: {cache.get_stats()}")
        
        # 5. Test Rate Limiter
        print("\n5. Test Rate Limiter...")
        from gpt5.throttling import RateLimiter
        
        limiter = RateLimiter()
        acquired = await limiter.acquire("gpt-5-mini", 100)
        print(f"   Token adquirido: {acquired}")
        
        status = limiter.get_status("gpt-5-mini")
        print(f"   Requests disponibles: {status['requests_available']:.1f}")
        
        # 6. Test Batch Routing
        print("\n6. Test Batch Routing...")
        productos = [
            {"name": "Coca Cola 500ml", "category": "beverages", "price": 1500},
            {"name": "iPhone 15 Pro", "category": "smartphones", "price": 1200000},
            {"name": "MacBook Pro", "category": "notebooks", "price": 2500000}
        ]
        
        batches = router.route_batch(productos)
        
        for model_type, products in batches.items():
            if products:
                print(f"   {model_type.value}: {len(products)} productos")
        
        # 7. Test Costos
        print("\n7. Test Estimacion Costos...")
        savings = router.estimate_savings(productos * 10)
        print(f"   Productos: {savings['total_products']}")
        print(f"   Ahorro estimado: {savings['savings_percent']:.1f}%")
        
        print("\n=== TODOS LOS TESTS EXITOSOS ===")
        return True
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_gpt5())
    print(f"\nResultado: {'EXITO' if success else 'FALLO'}")
    sys.exit(0 if success else 1)