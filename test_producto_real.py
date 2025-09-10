#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de procesamiento de producto real con BD
"""

import sys
import os
import asyncio
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Configurar variables de entorno
os.environ['REDIS_MOCK'] = 'true'  # Usar mock para Redis

async def test_producto_real():
    """Test con producto real usando BD"""
    print("=== TEST PRODUCTO REAL CON BD ===")
    
    try:
        # Importar sistema
        from normalize_gpt5 import normalize_with_gpt5, ProcessingMode
        
        # Producto de ejemplo real
        producto = {
            'name': 'iPhone 15 Pro Max 256GB Natural Titanium Liberado',
            'category': 'smartphones',
            'price': 1299990,
            'retailer': 'falabella',
            'url': 'https://falabella.com/falabella-cl/product/123456',
            'brand': 'Apple',
            'metadata': {
                'scraped_at': '2024-12-09',
                'store_id': 'FAL001'
            }
        }
        
        print(f"Producto a procesar:")
        print(f"  Nombre: {producto['name']}")
        print(f"  Precio: ${producto['price']:,} CLP")
        print(f"  Retailer: {producto['retailer']}")
        
        # Procesar con sistema GPT-5 (modo SINGLE para test)
        print(f"\nProcesando con GPT-5...")
        
        resultado = await normalize_with_gpt5(
            producto, 
            mode=ProcessingMode.SINGLE
        )
        
        print(f"\n=== RESULTADO ===")
        print(f"Product ID: {resultado.get('product_id', 'N/A')}")
        print(f"Fingerprint: {resultado.get('fingerprint', 'N/A')[:16]}...")
        print(f"Marca: {resultado.get('brand', 'N/A')}")
        print(f"Modelo: {resultado.get('model', 'N/A')}")
        print(f"Nombre normalizado: {resultado.get('name', 'N/A')}")
        print(f"Categoria: {resultado.get('category', 'N/A')}")
        print(f"Precio actual: ${resultado.get('price_current', 0):,}")
        print(f"URL: {resultado.get('url', 'N/A')}")
        
        # Metadatos AI
        print(f"\n=== METADATOS AI ===")
        print(f"AI Enhanced: {resultado.get('ai_enhanced', False)}")
        print(f"AI Confidence: {resultado.get('ai_confidence', 0):.3f}")
        print(f"AI Model: {resultado.get('ai_model', 'N/A')}")
        print(f"Version: {resultado.get('processing_version', 'N/A')}")
        print(f"Pending Batch: {resultado.get('pending_batch', False)}")
        
        # Atributos
        attrs = resultado.get('attributes', {})
        if attrs:
            print(f"\n=== ATRIBUTOS ===")
            for key, value in attrs.items():
                print(f"  {key}: {value}")
        
        print(f"\n=== TEST COMPLETADO EXITOSAMENTE ===")
        return True
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_producto_real())
    print(f"\nResultado final: {'EXITO' if success else 'FALLO'}")
    sys.exit(0 if success else 1)