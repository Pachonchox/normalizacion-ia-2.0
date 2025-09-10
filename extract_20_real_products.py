#!/usr/bin/env python3
"""
🧪 Extractor de 20 productos reales de los archivos de datos existentes
"""
import json
import os
from datetime import datetime
from pathlib import Path
import sys
import io

# Configurar encoding UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def extract_real_products():
    """Extraer 20 productos reales variados de los archivos existentes"""
    
    productos_seleccionados = []
    
    # Archivos a leer con límite de productos por archivo
    archivos_fuente = [
        ("datos/falabella/busqueda_smartphone_ciclo003_2025-09-09_17-06-13.json", 5),  # Smartphones
        ("datos/falabella/busqueda_perfume_ciclo001_2025-09-09_17-04-19.json", 4),     # Perfumes  
        ("datos/falabella/busqueda_smartv_ciclo002_2025-09-09_17-05-16.json", 3),      # Smart TVs
        ("datos/paris/busqueda_notebook_ciclo002_2025-09-09_17-05-15.json", 3),        # Notebooks
        ("datos/paris/busqueda_smartphone_ciclo001_2025-09-09_17-03-52.json", 2),      # Más smartphones
        ("datos/ripley/rotation_perfume_c001_2025-09-09_17-01-55.json", 2),            # Más perfumes
        ("datos/ripley/rotation_smartv_c002_2025-09-09_17-03-33.json", 1),             # Más TVs
    ]
    
    contador_id = 1
    
    for archivo_path, limite in archivos_fuente:
        try:
            with open(archivo_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            productos = data.get('products', [])[:limite]
            
            # Determinar retailer desde el path
            if 'falabella' in archivo_path:
                retailer = 'Falabella'
            elif 'paris' in archivo_path:
                retailer = 'Paris'
            elif 'ripley' in archivo_path:
                retailer = 'Ripley'
            else:
                retailer = 'Unknown'
            
            # Procesar cada producto
            for prod in productos:
                # Construir producto normalizado
                producto_normalizado = {
                    "producto_id": f"real_{contador_id:03d}",
                    "nombre": prod.get('name', 'Sin nombre'),
                    "marca": prod.get('brand', 'Sin marca'),
                    "precio": prod.get('card_price') or prod.get('normal_price') or 0,
                    "precio_normal": prod.get('normal_price', 0),
                    "precio_original": prod.get('original_price'),
                    "retailer": retailer,
                    "url": prod.get('product_link', ''),
                    "categoria_scraping": prod.get('search_name', 'Sin categoría'),
                    "termino_busqueda": prod.get('search_term', ''),
                    "fecha_captura": prod.get('scraped_at', datetime.now().isoformat()),
                    "pagina_scrapeada": prod.get('page_scraped', 1)
                }
                
                # Agregar descripción basada en el nombre y categoría
                if 'smartphone' in archivo_path.lower() or 'smartphone' in prod.get('search_term', '').lower():
                    producto_normalizado['descripcion'] = f"Smartphone {prod.get('brand', '')} {prod.get('name', '')}"
                    producto_normalizado['categoria_inferida'] = 'Electrónica > Celulares'
                elif 'perfume' in archivo_path.lower():
                    producto_normalizado['descripcion'] = f"Perfume {prod.get('brand', '')} {prod.get('name', '')}"
                    producto_normalizado['categoria_inferida'] = 'Belleza > Perfumes'
                elif 'smartv' in archivo_path.lower() or 'tv' in prod.get('name', '').lower():
                    producto_normalizado['descripcion'] = f"Smart TV {prod.get('brand', '')} {prod.get('name', '')}"
                    producto_normalizado['categoria_inferida'] = 'Electrónica > Televisores'
                elif 'notebook' in archivo_path.lower():
                    producto_normalizado['descripcion'] = f"Notebook {prod.get('brand', '')} {prod.get('name', '')}"
                    producto_normalizado['categoria_inferida'] = 'Electrónica > Computadores'
                else:
                    producto_normalizado['descripcion'] = f"{prod.get('brand', '')} {prod.get('name', '')}"
                    producto_normalizado['categoria_inferida'] = 'General'
                
                productos_seleccionados.append(producto_normalizado)
                contador_id += 1
                
        except Exception as e:
            print(f"⚠️ Error procesando {archivo_path}: {e}")
    
    # Guardar productos seleccionados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"test_20_productos_reales_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(productos_seleccionados, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Archivo creado: {output_file}")
    print(f"📊 Total productos extraídos: {len(productos_seleccionados)}")
    
    # Mostrar resumen
    retailers = {}
    categorias = {}
    for p in productos_seleccionados:
        retailers[p['retailer']] = retailers.get(p['retailer'], 0) + 1
        categorias[p['categoria_scraping']] = categorias.get(p['categoria_scraping'], 0) + 1
    
    print(f"\n📈 Distribución por retailer:")
    for r, count in retailers.items():
        print(f"   - {r}: {count} productos")
    
    print(f"\n📁 Distribución por categoría:")
    for c, count in categorias.items():
        print(f"   - {c}: {count} productos")
    
    return output_file

if __name__ == "__main__":
    archivo = extract_real_products()
    print(f"\n🚀 Ahora ejecuta el pipeline con:")
    print(f"   python run_pipeline_with_db.py")
    print(f"   o")
    print(f"   python -m src.cli normalize --input {archivo}")