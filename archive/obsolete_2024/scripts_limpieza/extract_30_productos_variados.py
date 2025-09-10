#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛍️ Extraer 30 Productos Variados para Test Completo
Seleccionar productos de diferentes categorías, retailers y precios
"""

import json
import os
import random
from collections import defaultdict

def extract_varied_products():
    print("EXTRAYENDO 30 PRODUCTOS VARIADOS")
    print("=" * 50)
    
    # Buscar todos los archivos JSON en la carpeta datos
    datos_folders = {
        'falabella': 'datos/falabella',
        'ripley': 'datos/ripley', 
        'paris': 'datos/paris'
    }
    
    all_products = []
    products_by_retailer = defaultdict(list)
    
    # Cargar productos de cada retailer
    for retailer, folder_path in datos_folders.items():
        if os.path.exists(folder_path):
            json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
            print(f"Retailer {retailer}: {len(json_files)} archivos encontrados")
            
            for json_file in json_files[-3:]:  # Solo los 3 más recientes
                file_path = os.path.join(folder_path, json_file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Extraer productos según estructura del archivo
                    products_in_file = []
                    
                    if isinstance(data, list):
                        products_in_file = data
                    elif isinstance(data, dict):
                        # Estructura con metadata y products
                        if 'products' in data:
                            products_in_file = data['products']
                        elif 'items' in data:
                            products_in_file = data['items']
                        else:
                            # Si no hay estructura clara, intentar buscar listas
                            for key, value in data.items():
                                if isinstance(value, list) and len(value) > 0:
                                    if isinstance(value[0], dict) and 'name' in value[0]:
                                        products_in_file = value
                                        break
                    
                    for item in products_in_file:
                        if isinstance(item, dict) and item.get('name'):
                            # Agregar metadata del retailer
                            item['_retailer'] = retailer
                            item['_source_file'] = json_file
                            products_by_retailer[retailer].append(item)
                            all_products.append(item)
                            
                except Exception as e:
                    print(f"Error cargando {json_file}: {e}")
        else:
            print(f"Carpeta {folder_path} no existe")
    
    print(f"\nTotal productos cargados: {len(all_products)}")
    for retailer, products in products_by_retailer.items():
        print(f"  - {retailer}: {len(products)} productos")
    
    if len(all_products) < 30:
        print(f"ADVERTENCIA: Solo hay {len(all_products)} productos disponibles")
        return all_products[:len(all_products)]
    
    # Estrategia de selección balanceada
    selected_products = []
    
    # 1. Por retailer (10 de cada uno si es posible)
    products_per_retailer = 10
    for retailer, products in products_by_retailer.items():
        if products:
            sample_size = min(products_per_retailer, len(products))
            selected = random.sample(products, sample_size)
            selected_products.extend(selected)
            print(f"Seleccionados de {retailer}: {len(selected)} productos")
    
    # 2. Si faltan productos, completar aleatoriamente
    if len(selected_products) < 30:
        remaining_needed = 30 - len(selected_products)
        remaining_products = [p for p in all_products if p not in selected_products]
        
        if remaining_products:
            additional = random.sample(
                remaining_products, 
                min(remaining_needed, len(remaining_products))
            )
            selected_products.extend(additional)
    
    # Limitamos a exactamente 30
    final_products = selected_products[:30]
    
    # Analizar variedad de productos seleccionados
    print(f"\nPRODUCTOS SELECCIONADOS: {len(final_products)}")
    
    # Por retailer
    retailer_count = defaultdict(int)
    price_ranges = defaultdict(int)
    
    for product in final_products:
        retailer_count[product.get('_retailer', 'unknown')] += 1
        
        # Analizar precios
        price = product.get('card_price') or product.get('normal_price') or 0
        if price < 50000:
            price_ranges['Bajo (<50K)'] += 1
        elif price < 200000:
            price_ranges['Medio (50K-200K)'] += 1
        elif price < 500000:
            price_ranges['Alto (200K-500K)'] += 1
        else:
            price_ranges['Premium (>500K)'] += 1
    
    print("Distribución por retailer:")
    for retailer, count in retailer_count.items():
        print(f"  - {retailer}: {count}")
    
    print("Distribución por precio:")
    for range_name, count in price_ranges.items():
        print(f"  - {range_name}: {count}")
    
    # Guardar productos seleccionados
    output_file = 'test_productos_30/productos_variados_30.json'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_products, f, ensure_ascii=False, indent=2)
    
    print(f"\n30 productos guardados en: {output_file}")
    
    # Mostrar muestra de productos
    print(f"\nMUESTRA DE PRODUCTOS SELECCIONADOS:")
    print("-" * 80)
    for i, product in enumerate(final_products[:5], 1):
        name = product.get('name', 'Sin nombre')[:50]
        retailer = product.get('_retailer', 'unknown')
        price = product.get('card_price') or product.get('normal_price') or 0
        brand = product.get('brand', 'Sin marca')
        
        print(f"{i:2}. {name:50} | {retailer:8} | {brand:10} | ${price:,}")
    
    if len(final_products) > 5:
        print(f"    ... y {len(final_products) - 5} productos más")
    
    return final_products

if __name__ == "__main__":
    extract_varied_products()