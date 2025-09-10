#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Test de 10 perfumes de Falabella con Pipeline Integrado
Extrae 10 perfumes reales de Falabella y los procesa en el pipeline completo
"""

import os
import sys
import json
import io
from datetime import datetime
from pathlib import Path

# Configurar encoding UTF-8
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def extract_10_perfumes_falabella():
    """Extraer 10 perfumes de Falabella desde el archivo de datos local"""
    
    print("🧪 EXTRAYENDO 10 PERFUMES DE FALABELLA")
    print("=" * 50)
    
    # Buscar archivo de perfumes más reciente
    perfume_file = "datos/falabella/busqueda_perfume_ciclo001_2025-09-10_19-06-58.json"
    
    if not os.path.exists(perfume_file):
        print(f"❌ No se encontró el archivo: {perfume_file}")
        return None
    
    # Leer datos
    with open(perfume_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    productos = data.get('products', [])
    
    if len(productos) < 10:
        print(f"⚠️ Solo hay {len(productos)} productos disponibles")
        productos_test = productos
    else:
        productos_test = productos[:10]
    
    print(f"✅ Seleccionados {len(productos_test)} perfumes de Falabella")
    
    # Preparar datos para el pipeline
    productos_preparados = []
    
    for i, producto in enumerate(productos_test, 1):
        # Adaptar formato para el pipeline
        producto_prep = {
            "name": producto.get('name', ''),
            "product_link": producto.get('product_link', ''),
            "normal_price": producto.get('normal_price'),
            "normal_price_text": producto.get('normal_price_text', ''),
            "card_price": producto.get('card_price'),
            "card_price_text": producto.get('card_price_text', ''),
            "original_price": producto.get('original_price'),
            "original_price_text": producto.get('original_price_text', ''),
            "brand": producto.get('brand', ''),
            "product_code": producto.get('product_code', ''),
            "search_term": producto.get('search_term', 'perfume'),
            "retailer": "Falabella",
            "source": "datos_locales_falabella"
        }
        
        productos_preparados.append(producto_prep)
        
        print(f"  P{i:2d}: {producto_prep['name'][:50]}...")
        print(f"       💰 {producto_prep['normal_price_text']} | {producto_prep['brand']}")
        print(f"       🔗 {'✅' if producto_prep['product_link'] else '❌'} Link")
    
    print()
    return productos_preparados

def process_with_pipeline(productos):
    """Procesar productos con el pipeline integrado"""
    
    print("⚙️ PROCESANDO CON PIPELINE INTEGRADO")
    print("=" * 50)
    
    try:
        # Importar pipeline
        from normalize_integrated import normalize_batch_integrated
        
        # Preparar metadata
        metadata = {
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "search_term": "perfume",
            "search_name": "Perfumes Test",
            "base_url": "https://www.falabella.com/falabella-cl/search?Ntt=perfume",
            "scraper": "Test 10 Perfumes Falabella",
            "total_products": len(productos)
        }
        
        # Procesar productos
        print(f"🔄 Iniciando normalización de {len(productos)} productos...")
        
        # Crear estructura de datos para el pipeline
        productos_raw = []
        for producto in productos:
            item_data = {
                "item": producto,
                "metadata": metadata,
                "retailer": "Falabella",
                "source_path": "test_10_perfumes_falabella"
            }
            productos_raw.append(item_data)
        
        # Ejecutar pipeline
        resultados = normalize_batch_integrated(productos_raw, persist_db=True)
        
        print(f"✅ Pipeline completado!")
        print(f"   📊 Productos procesados: {len(resultados)}")
        
        # Guardar resultados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"productos_perfumes_falabella_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "total_products": len(resultados),
                    "source": "test_10_perfumes_falabella",
                    "pipeline": "normalize_integrated"
                },
                "products": resultados
            }, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Resultados guardados en: {output_file}")
        
        return resultados, output_file
        
    except Exception as e:
        print(f"❌ Error en pipeline: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def main():
    """Función principal"""
    
    print("🚀 TEST: 10 PERFUMES FALABELLA → PIPELINE INTEGRADO")
    print("🎯 Objetivo: Ingresar productos reales y crear snapshot de BD")
    print("="*60)
    
    # 1. Extraer productos
    productos = extract_10_perfumes_falabella()
    if not productos:
        print("❌ No se pudieron extraer productos")
        return
    
    print()
    
    # 2. Procesar con pipeline
    resultados, output_file = process_with_pipeline(productos)
    if not resultados:
        print("❌ No se pudo procesar con el pipeline")
        return
    
    print()
    print("✅ PROCESO COMPLETADO EXITOSAMENTE")
    print(f"📊 {len(resultados)} perfumes de Falabella procesados")
    print(f"💾 Archivo: {output_file}")
    print("🗄️  Datos guardados en BD PostgreSQL")
    print()
    print("📋 Siguiente paso: crear snapshot de la base de datos")

if __name__ == "__main__":
    main()