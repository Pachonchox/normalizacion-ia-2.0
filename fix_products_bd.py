#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 Re-procesar productos con retailer fix
Re-insertar los 10 productos con el mapeo correcto de retailers
"""

import json
import sys
import os

# Agregar src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from normalize_integrated import normalize_batch_integrated

def fix_products():
    print("RE-PROCESANDO 10 PRODUCTOS CON RETAILER FIX")
    print("=" * 60)
    
    # Cargar los productos originales
    with open('test_productos_10/test_products_10_20250909_171225.json', 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    print(f"Cargados {len(products)} productos para re-procesar...")
    
    # Verificar retailers originales
    retailers = {}
    for product in products:
        retailer = product.get('_retailer', 'Unknown')
        retailers[retailer] = retailers.get(retailer, 0) + 1
    
    print("Retailers detectados:")
    for retailer, count in retailers.items():
        print(f"  - {retailer}: {count} productos")
    
    # Re-normalizar todos los productos (con retailer fix)
    print("\nRe-normalizando productos...")
    results = normalize_batch_integrated(products, retailer=None)
    
    print(f"\nRE-PROCESAMIENTO COMPLETADO:")
    print(f"Productos procesados: {len(results)}")
    
    # Verificar que ahora tengan retailers correctos
    retailer_counts = {}
    for result in results:
        retailer = result.get('retailer', 'Unknown')
        retailer_counts[retailer] = retailer_counts.get(retailer, 0) + 1
    
    print("\nRetailers en productos normalizados:")
    for retailer, count in retailer_counts.items():
        print(f"  - {retailer}: {count} productos")
    
    # Guardar resultados actualizados
    output_file = 'test_salida_bd/fixed_normalized_products.jsonl'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
    
    print(f"\nResultados guardados en: {output_file}")
    
    return results

if __name__ == "__main__":
    fix_products()