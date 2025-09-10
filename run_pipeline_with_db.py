#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline de Normalización con Base de Datos
Versión completa con persistencia en PostgreSQL
"""

import os
import sys
import json
import psycopg2
from datetime import datetime
from typing import Dict, Any, List

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['DB_ENABLED'] = 'true'

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

def guardar_en_bd(productos: List[Dict[str, Any]]):
    """Guardar productos normalizados en la base de datos"""
    
    print("\n[BD] Guardando productos en base de datos...")
    
    # Configuración de BD
    db_config = {
        'host': os.getenv('DB_HOST'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }
    
    try:
        # Conectar a BD
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        guardados = 0
        actualizados = 0
        errores = 0
        
        for producto in productos:
            try:
                # 1. Verificar si existe el retailer
                retailer = producto.get('retailer', 'Unknown')
                cursor.execute(
                    "SELECT id FROM retailers WHERE name = %s",
                    (retailer,)
                )
                retailer_result = cursor.fetchone()
                
                if not retailer_result:
                    # Crear retailer si no existe
                    cursor.execute(
                        "INSERT INTO retailers (name, active) VALUES (%s, true) RETURNING id",
                        (retailer,)
                    )
                    retailer_id = cursor.fetchone()[0]
                else:
                    retailer_id = retailer_result[0]
                
                # 2. Insertar/actualizar producto maestro
                cursor.execute("""
                    INSERT INTO productos_maestros (
                        fingerprint, product_id, name, brand, model, 
                        category, attributes, ai_enhanced, ai_confidence,
                        processing_version, active
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, true)
                    ON CONFLICT (fingerprint) DO UPDATE SET
                        name = EXCLUDED.name,
                        brand = EXCLUDED.brand,
                        model = EXCLUDED.model,
                        category = EXCLUDED.category,
                        attributes = EXCLUDED.attributes,
                        ai_enhanced = EXCLUDED.ai_enhanced,
                        ai_confidence = EXCLUDED.ai_confidence,
                        processing_version = EXCLUDED.processing_version,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id, (xmax = 0) as inserted
                """, (
                    producto['fingerprint'],
                    producto['product_id'],
                    producto['name'],
                    producto['brand'],
                    producto.get('model'),
                    producto['category'],
                    json.dumps(producto.get('attributes', {})),
                    producto.get('ai_enhanced', False),
                    producto.get('category_confidence', 0.0),
                    producto.get('processing_version', 'v2.0')
                ))
                
                result = cursor.fetchone()
                producto_maestro_id = result[0]
                fue_insertado = result[1]
                
                if fue_insertado:
                    guardados += 1
                else:
                    actualizados += 1
                
                # 3. Actualizar precios actuales
                precio_actual = producto.get('price_current')
                precio_original = producto.get('price_original')
                
                if precio_actual:
                    cursor.execute("""
                        INSERT INTO precios_actuales (
                            fingerprint, retailer_id, product_id,
                            precio_normal, precio_tarjeta, precio_oferta,
                            currency, stock_status, url
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (fingerprint, retailer_id) DO UPDATE SET
                            precio_normal = EXCLUDED.precio_normal,
                            precio_tarjeta = EXCLUDED.precio_tarjeta,
                            precio_oferta = EXCLUDED.precio_oferta,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        producto['fingerprint'],
                        retailer_id,
                        producto['product_id'],
                        precio_original or precio_actual,
                        precio_actual if precio_original else None,
                        None,  # precio_oferta
                        'CLP',
                        'available',
                        producto.get('url')
                    ))
                
            except Exception as e:
                print(f"   [ERROR] Producto {producto.get('product_id')}: {e}")
                errores += 1
                conn.rollback()
                continue
        
        # Confirmar cambios
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"\n[BD] Resultados:")
        print(f"   - Nuevos: {guardados}")
        print(f"   - Actualizados: {actualizados}")
        print(f"   - Errores: {errores}")
        print(f"   [OK] Total procesados: {guardados + actualizados}/{len(productos)}")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] No se pudo conectar a BD: {e}")
        return False

def main():
    """Función principal con BD"""
    
    print("="*60)
    print("PIPELINE DE NORMALIZACION CON BASE DE DATOS")
    print("="*60)
    
    # Importar pipeline
    from run_pipeline import PipelineNormalizacion
    
    # Crear pipeline (sin BD interna para manejarlo aquí)
    pipeline = PipelineNormalizacion(use_llm=False, use_db=False)
    
    # Productos de ejemplo más completos
    productos_ejemplo = [
        {
            "product_id": "SMRT-001",
            "name": "Samsung Galaxy S24 Ultra 512GB 5G Titanium Black",
            "brand": "Samsung",
            "retailer": "Falabella",
            "normal_price": 1299990,
            "card_price": 1099990,
            "product_link": "https://falabella.com/samsung-s24"
        },
        {
            "product_id": "NOTE-001",
            "name": "Notebook Dell XPS 13 Intel Core i7 16GB RAM 512GB SSD",
            "retailer": "Paris",
            "normal_price": 999990,
            "product_link": "https://paris.cl/dell-xps13"
        },
        {
            "product_id": "PERF-001",
            "name": "Perfume Carolina Herrera Good Girl 80ml EDP Mujer",
            "retailer": "Ripley",
            "normal_price_text": "$94.990",
            "card_price_text": "$84.990"
        },
        {
            "product_id": "TV-001",
            "name": "Smart TV LG 55 pulgadas 4K OLED",
            "retailer": "Falabella",
            "normal_price": 899990,
            "offer_price": 799990
        },
        {
            "product_code": "TAB-001",
            "name": "iPad Pro 11 256GB WiFi Space Gray",
            "brand": "Apple",
            "retailer": "Paris",
            "precio_normal": 949990
        },
        {
            "product_id": "AUDIO-001",
            "name": "AirPods Pro 2da generación",
            "brand": "Apple",
            "retailer": "Falabella",
            "normal_price": 249990
        },
        {
            "product_id": "LAV-001",
            "name": "Lavadora Samsung 15kg Inverter",
            "retailer": "Ripley",
            "normal_price": 449990,
            "card_price": 399990
        },
        {
            "product_id": "REF-001",
            "name": "Refrigerador LG Side by Side 601L",
            "retailer": "Paris",
            "normal_price": 1299990
        }
    ]
    
    print(f"\nProcesando {len(productos_ejemplo)} productos...")
    print("-"*60)
    
    # Procesar lote
    resultados = pipeline.procesar_lote(productos_ejemplo)
    
    if resultados:
        # Guardar en archivo JSON
        archivo = f"productos_normalizados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        pipeline.guardar_resultados(resultados, archivo)
        
        # Guardar en base de datos
        guardar_en_bd(resultados)
    
    # Mostrar estadísticas
    pipeline.mostrar_estadisticas()
    
    print("\n[EXITO] Pipeline con BD completado")
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR FATAL] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)