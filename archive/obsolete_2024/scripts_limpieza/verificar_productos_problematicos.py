#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificación Específica de Productos Problemáticos
Busca productos reacondicionados, accesorios y precios bajos que pasaron el filtro
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import psycopg2
from psycopg2 import extras
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def verificar_problematicos():
    print("VERIFICACION DE PRODUCTOS PROBLEMATICOS")
    print("=" * 60)
    
    try:
        # Configuración de BD
        DB_CONFIG = {
            'host': os.getenv('DB_HOST', '34.176.197.136'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'postgres'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD')
        }
        
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
        
        print("1. BUSQUEDA DE PRODUCTOS REACONDICIONADOS")
        print("-" * 40)
        
        cursor.execute("""
            SELECT pm.product_id, pm.name, 
                   COALESCE(pa.precio_tarjeta, pa.precio_normal, pa.precio_oferta, 0) as precio
            FROM productos_maestros pm
            LEFT JOIN precios_actuales pa ON pm.product_id = pa.product_id
            WHERE pm.active = true AND (
                LOWER(pm.name) LIKE '%reacondicionado%' OR
                LOWER(pm.name) LIKE '%usado%' OR 
                LOWER(pm.name) LIKE '%refurbished%' OR
                LOWER(pm.name) LIKE '%recondicionado%'
            )
            ORDER BY pm.name
        """)
        
        reacondicionados = cursor.fetchall()
        print(f"Productos reacondicionados encontrados: {len(reacondicionados)}")
        
        if reacondicionados:
            for i, producto in enumerate(reacondicionados, 1):
                precio = producto['precio'] or 0
                print(f"   {i:2d}. {producto['name'][:60]}... - ${precio:,}")
        
        print("\n2. BUSQUEDA DE ACCESORIOS")
        print("-" * 40)
        
        cursor.execute("""
            SELECT pm.product_id, pm.name, 
                   COALESCE(pa.precio_tarjeta, pa.precio_normal, pa.precio_oferta, 0) as precio
            FROM productos_maestros pm
            LEFT JOIN precios_actuales pa ON pm.product_id = pa.product_id
            WHERE pm.active = true AND (
                LOWER(pm.name) LIKE '%control remoto%' OR
                LOWER(pm.name) LIKE '%cable%' OR
                LOWER(pm.name) LIKE '%funda%' OR
                LOWER(pm.name) LIKE '%cargador%' OR
                LOWER(pm.name) LIKE '%protector%' OR
                LOWER(pm.name) LIKE '%soporte%' OR
                LOWER(pm.name) LIKE '%bateria externa%' OR
                LOWER(pm.name) LIKE '%power bank%'
            )
            ORDER BY pm.name
        """)
        
        accesorios = cursor.fetchall()
        print(f"Accesorios encontrados: {len(accesorios)}")
        
        if accesorios:
            for i, producto in enumerate(accesorios, 1):
                precio = producto['precio'] or 0
                print(f"   {i:2d}. {producto['name'][:60]}... - ${precio:,}")
        
        print("\n3. BUSQUEDA DE PRECIOS BAJOS (<$50,000)")
        print("-" * 40)
        
        cursor.execute("""
            SELECT pm.product_id, pm.name, 
                   COALESCE(pa.precio_tarjeta, pa.precio_normal, pa.precio_oferta, 0) as precio
            FROM productos_maestros pm
            LEFT JOIN precios_actuales pa ON pm.product_id = pa.product_id
            WHERE pm.active = true 
            AND COALESCE(pa.precio_tarjeta, pa.precio_normal, pa.precio_oferta, 0) > 0
            AND COALESCE(pa.precio_tarjeta, pa.precio_normal, pa.precio_oferta, 0) < 50000
            ORDER BY precio ASC
        """)
        
        precios_bajos = cursor.fetchall()
        print(f"Productos con precios bajos encontrados: {len(precios_bajos)}")
        
        if precios_bajos:
            for i, producto in enumerate(precios_bajos, 1):
                precio = producto['precio'] or 0
                print(f"   {i:2d}. {producto['name'][:60]}... - ${precio:,}")
        
        print("\n4. RESUMEN")
        print("-" * 40)
        
        total_problematicos = len(reacondicionados) + len(accesorios) + len(precios_bajos)
        
        print(f"Total productos problemáticos: {total_problematicos}")
        print(f"   - Reacondicionados: {len(reacondicionados)}")
        print(f"   - Accesorios: {len(accesorios)}")  
        print(f"   - Precios bajos: {len(precios_bajos)}")
        
        if total_problematicos > 0:
            print(f"\nACCION REQUERIDA: Ejecutar script de eliminación para {total_problematicos} productos")
            print("Comando sugerido: python eliminar_directo.py")
        else:
            print("\nEXCELENTE: No se encontraron productos problemáticos")
            print("El filtro está funcionando correctamente")
        
        cursor.close()
        conn.close()
        
        return total_problematicos
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return -1

if __name__ == "__main__":
    verificar_problematicos()