#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 Analizar Categoría Others
Ver qué productos están siendo categorizados como "others" y por qué
"""

import json
import sys
import os

# Agregar src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from unified_connector import get_unified_connector

def analizar_others():
    print("ANALISIS CATEGORIA 'OTHERS'")
    print("=" * 50)
    
    try:
        connector = get_unified_connector()
        
        # 1. Obtener todos los productos categorizados como 'others'
        query_others = """
            SELECT pm.name, pm.brand, pm.model, pm.attributes, pm.ai_enhanced, pm.ai_confidence,
                   pa.precio_normal, pa.precio_tarjeta, pm.created_at
            FROM productos_maestros pm
            LEFT JOIN precios_actuales pa ON pm.fingerprint = pa.fingerprint  
            WHERE pm.category = 'others' AND pm.active = true
            ORDER BY pm.created_at DESC
        """
        
        products_others = connector.execute_query(query_others)
        
        print(f"PRODUCTOS EN CATEGORIA 'OTHERS': {len(products_others)}")
        print("=" * 80)
        
        for i, product in enumerate(products_others, 1):
            print(f"\n{i}. {product['name']}")
            print(f"   Marca: {product['brand']}")
            print(f"   Modelo: {product['model'] or 'N/A'}")
            
            # Precio
            precio_normal = product['precio_normal'] or 0
            precio_tarjeta = product['precio_tarjeta'] or 0
            precio_mostrar = precio_tarjeta if precio_tarjeta else precio_normal
            print(f"   Precio: ${precio_mostrar:,} CLP")
            
            # IA info
            ai_status = "SI" if product['ai_enhanced'] else "NO"
            ai_conf = product['ai_confidence'] or 0
            print(f"   IA Enhanced: {ai_status} (conf: {ai_conf:.2f})")
            
            # Atributos
            attributes = product['attributes'] or {}
            if isinstance(attributes, str):
                try:
                    attributes = json.loads(attributes)
                except:
                    attributes = {}
            
            if attributes:
                print(f"   Atributos: {attributes}")
            else:
                print(f"   Atributos: (ninguno)")
            
            print(f"   Fecha: {product['created_at']}")
            print("-" * 60)
        
        # 2. Verificar en qué casos podría haber mejor categorización
        print(f"\nANALISIS DE CATEGORIZACION:")
        print("=" * 50)
        
        palabras_clave = {
            'smart_tv': ['smart tv', 'television', 'control remoto', 'tv'],
            'smartphones': ['smartphone', 'celular', 'phone', 'movil'],
            'perfumes': ['perfume', 'fragancia', 'colonia', 'edt', 'edp'],
            'notebooks': ['notebook', 'laptop', 'computador'],
            'appliances': ['refrigerador', 'lavadora', 'microondas', 'horno'],
            'home': ['cama', 'mesa', 'silla', 'mueble', 'hogar']
        }
        
        posibles_recategorizaciones = []
        
        for product in products_others:
            name_lower = product['name'].lower()
            
            for categoria, keywords in palabras_clave.items():
                for keyword in keywords:
                    if keyword in name_lower:
                        posibles_recategorizaciones.append({
                            'nombre': product['name'],
                            'categoria_sugerida': categoria,
                            'palabra_clave': keyword,
                            'confianza_actual': product['ai_confidence'] or 0
                        })
                        break
        
        if posibles_recategorizaciones:
            print(f"POSIBLES RE-CATEGORIZACIONES ({len(posibles_recategorizaciones)}):")
            for item in posibles_recategorizaciones:
                print(f"  - {item['nombre'][:50]}...")
                print(f"    Sugerencia: {item['categoria_sugerida']} (palabra: '{item['palabra_clave']}')")
                print(f"    Confianza IA actual: {item['confianza_actual']:.2f}")
                print()
        else:
            print("No se encontraron re-categorizaciones obvias.")
        
        # 3. Ver todas las categorías disponibles
        print(f"\nCATEGORIAS DISPONIBLES EN BD:")
        print("-" * 30)
        
        categorias_query = """
            SELECT name, active 
            FROM categories 
            ORDER BY name
        """
        
        categorias = connector.execute_query(categorias_query)
        
        for cat in categorias:
            status = "ACTIVA" if cat['active'] else "INACTIVA"
            print(f"  - {cat['name']} ({status})")
        
        return products_others
        
    except Exception as e:
        print(f"ERROR analizando others: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    analizar_others()