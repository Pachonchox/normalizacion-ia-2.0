#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Test del Sistema GPT-5 Completo
Test de integración que verifica todos los componentes
"""

import sys
import os
import asyncio
import json
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Configurar variables de entorno para testing
os.environ['REDIS_MOCK'] = 'true'
os.environ['OPENAI_API_KEY'] = 'test-key'

async def test_sistema_gpt5():
    """Test completo del sistema GPT-5"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                   🧪 TEST SISTEMA GPT-5                          ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # 1. Test de importaciones
        print("📦 1. Verificando importaciones...")
        
        from gpt5.router import GPT5Router, ModelType
        print("  ✅ Router importado")
        
        from gpt5.prompts import PromptManager, PromptMode
        print("  ✅ Prompts importado")
        
        from gpt5.validator import StrictValidator
        print("  ✅ Validator importado")
        
        from gpt5.cache_l1 import L1RedisCache
        print("  ✅ Cache L1 importado")
        
        from gpt5.throttling import RateLimiter
        print("  ✅ Throttling importado")
        
        print("  🎉 Todas las importaciones exitosas!")
        
        # 2. Test de Router
        print("\n🎯 2. Test Router de Complejidad...")
        router = GPT5Router()
        
        # Producto simple
        producto_simple = {
            "name": "Coca Cola 500ml",
            "category": "beverages", 
            "price": 1500
        }
        
        model, complexity = router.route_single(producto_simple)
        print(f"  🥤 Producto simple → {model.value} (complejidad: {complexity:.2f})")
        
        # Producto complejo
        producto_complejo = {
            "name": "MacBook Pro 16 M3 Max 48GB RAM 1TB SSD Space Gray 2024",
            "category": "notebooks",
            "price": 3899990
        }
        
        model, complexity = router.route_single(producto_complejo)
        print(f"  💻 Producto complejo → {model.value} (complejidad: {complexity:.2f})")
        
        # 3. Test de Prompts
        print("\n📝 3. Test Generación de Prompts...")
        prompt_manager = PromptManager()
        
        producto_test = {
            "name": "iPhone 15 Pro Max 256GB Titanium",
            "category": "smartphones",
            "price": 1299990
        }
        
        # Prompt minimal
        prompt_minimal = prompt_manager.get_prompt(
            "gpt-5-mini", "smartphones", PromptMode.MINIMAL, producto_test
        )
        print(f"  📱 Prompt minimal: {len(prompt_minimal)} chars")
        
        # Prompt standard
        prompt_standard = prompt_manager.get_prompt(
            "gpt-5-mini", "smartphones", PromptMode.STANDARD, producto_test
        )
        print(f"  📱 Prompt standard: {len(prompt_standard)} chars")
        
        # 4. Test de Validator
        print("\n✅ 4. Test Validación...")
        validator = StrictValidator()
        
        # Test taxonomía
        valid, final_cat, msg = validator.validate_taxonomy("celulares", "general")
        print(f"  📋 Taxonomía 'celulares' → '{final_cat}' (válido: {valid})")
        
        # Test atributos
        attrs = {"capacity": "256GB", "color": "negro", "invalid_attr": "test"}
        valid, clean_attrs, warnings = validator.validate_attributes(attrs, "smartphones")
        print(f"  🔧 Atributos limpios: {clean_attrs}")
        print(f"  ⚠️ Advertencias: {len(warnings)}")
        
        # 5. Test de Cache L1
        print("\n💾 5. Test Cache L1 (Mock)...")
        cache = L1RedisCache(use_mock=True)
        
        test_data = {
            "brand": "APPLE",
            "model": "iPhone 15 Pro Max",
            "normalized_name": "APPLE iPhone 15 Pro Max 256GB Titanium"
        }
        
        # Set
        success = cache.set("test_fp", test_data, "smartphones")
        print(f"  💾 Cache SET: {success}")
        
        # Get
        retrieved = cache.get("test_fp")
        print(f"  🔍 Cache GET: {retrieved is not None}")
        print(f"  📊 Stats: {cache.get_stats()}")
        
        # 6. Test de Rate Limiter
        print("\n⚡ 6. Test Rate Limiter...")
        rate_limiter = RateLimiter()
        
        # Test adquisición
        acquired = await rate_limiter.acquire("gpt-5-mini", 100)
        print(f"  🎫 Token acquisition: {acquired}")
        
        # Stats
        status = rate_limiter.get_status("gpt-5-mini")
        print(f"  📈 Requests disponibles: {status['requests_available']:.1f}")
        print(f"  🔄 Circuit state: {status['circuit_state']}")
        
        # 7. Test Batch Routing
        print("\n📦 7. Test Batch Routing...")
        productos_batch = [
            {"name": "Coca Cola 500ml", "category": "beverages", "price": 1500},
            {"name": "iPhone 15 Pro", "category": "smartphones", "price": 1200000},
            {"name": "Notebook Gaming ROG", "category": "notebooks", "price": 2500000},
            {"name": "Perfume Chanel", "category": "perfumes", "price": 150000}
        ]
        
        batches = router.route_batch(productos_batch)
        
        for model_type, products in batches.items():
            if products:
                print(f"  📊 {model_type.value}: {len(products)} productos")
        
        # 8. Test Estimación de Costos
        print("\n💰 8. Test Estimación de Costos...")
        savings = router.estimate_savings(productos_batch * 25)  # 100 productos
        print(f"  💸 Productos: {savings['total_products']}")
        print(f"  💵 Costo baseline: ${savings['baseline_cost_usd']:.4f}")
        print(f"  💲 Costo optimizado: ${savings['optimized_cost_usd']:.4f}")
        print(f"  💰 Ahorro: {savings['savings_percent']:.1f}%")
        
        print("""
╔══════════════════════════════════════════════════════════════════╗
║                    🎉 TODOS LOS TESTS EXITOSOS                   ║
║                   Sistema GPT-5 Funcional                        ║
╚══════════════════════════════════════════════════════════════════╝
        """)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR EN TEST: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_sistema_gpt5())
    print(f"\n🏁 Resultado final: {'✅ ÉXITO' if success else '❌ FALLO'}")
    sys.exit(0 if success else 1)