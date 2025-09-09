#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📦 Extractor de 10 Productos para Prueba
Selecciona 10 productos de diferentes retailers para test de inserción BD
"""

import json
import os
import random
from pathlib import Path
from datetime import datetime

def extract_products_from_json(json_file, max_products=4):
    """Extraer productos de un archivo JSON"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extraer lista de productos
        products = []
        if isinstance(data, list):
            products = data
        elif isinstance(data, dict):
            for key in ['products', 'productos', 'items', 'data', 'results']:
                if key in data and isinstance(data[key], list):
                    products = data[key]
                    break
        
        if not products:
            return []
        
        # Seleccionar productos al azar
        selected = random.sample(products, min(len(products), max_products))
        
        return selected
        
    except Exception as e:
        print(f"Error procesando {json_file}: {e}")
        return []

def main():
    """Función principal"""
    datos_dir = Path("datos")
    output_dir = Path("test_productos_10")
    
    if not datos_dir.exists():
        print(f"❌ Directorio datos no encontrado: {datos_dir}")
        return
    
    # Crear directorio de salida
    output_dir.mkdir(exist_ok=True)
    
    print("EXTRAYENDO 10 PRODUCTOS DE DIFERENTES RETAILERS")
    print("=" * 60)
    
    all_products = []
    retailers = ['falabella', 'ripley', 'paris']
    
    for retailer in retailers:
        retailer_dir = datos_dir / retailer
        if not retailer_dir.exists():
            print(f"{retailer}: carpeta no encontrada")
            continue
        
        print(f"Procesando {retailer}...")
        
        # Buscar archivos JSON (no logs)
        json_files = list(retailer_dir.glob('*.json'))
        if not json_files:
            print(f"  Sin archivos JSON en {retailer}")
            continue
        
        # Tomar el más reciente
        latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
        print(f"  Usando: {latest_file.name}")
        
        # Extraer productos
        products = extract_products_from_json(latest_file, max_products=4)
        
        if products:
            # Añadir metadata del retailer
            for product in products:
                product['_retailer'] = retailer
                product['_source_file'] = latest_file.name
                product['_extracted_at'] = datetime.now().isoformat()
            
            all_products.extend(products)
            print(f"  {len(products)} productos extraídos")
        else:
            print(f"  No se pudieron extraer productos")
    
    if not all_products:
        print("\nNo se encontraron productos para extraer")
        return
    
    # Limitar a 10 productos
    if len(all_products) > 10:
        selected_products = random.sample(all_products, 10)
    else:
        selected_products = all_products
    
    print(f"\nRESUMEN:")
    print(f"  Total productos encontrados: {len(all_products)}")
    print(f"  Productos seleccionados: {len(selected_products)}")
    
    # Guardar productos seleccionados
    output_file = output_dir / f"test_products_10_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(selected_products, f, ensure_ascii=False, indent=2)
    
    print(f"\nProductos guardados en: {output_file}")
    
    # Mostrar distribución por retailer
    retailer_count = {}
    for product in selected_products:
        retailer = product.get('_retailer', 'unknown')
        retailer_count[retailer] = retailer_count.get(retailer, 0) + 1
    
    print("\nDistribución por retailer:")
    for retailer, count in retailer_count.items():
        print(f"  {retailer}: {count} productos")
    
    # Mostrar algunos productos
    print(f"\nProductos seleccionados:")
    for i, product in enumerate(selected_products, 1):
        name = product.get('name', product.get('nombre', product.get('title', 'Sin nombre')))[:50]
        retailer = product.get('_retailer', 'unknown')
        print(f"  {i:2d}. [{retailer.upper()}] {name}")
    
    print(f"\nListo para probar inserción en BD con: {output_file}")

if __name__ == "__main__":
    main()