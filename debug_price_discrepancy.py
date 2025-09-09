#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 Debug Discrepancia Productos vs Precios
Investigar por qué hay más productos (47) que precios (37)
"""

import psycopg2
from datetime import datetime, timedelta

def main():
    print("INVESTIGANDO DISCREPANCIA PRODUCTOS vs PRECIOS")
    print("=" * 60)
    
    # Conectar a BD (usando credenciales del check_real_schema.py)
    conn = psycopg2.connect(
        host='34.176.197.136',
        port=5432,
        database='postgres',
        user='postgres',
        password='Osmar2503!',
        connect_timeout=15
    )
    
    cursor = conn.cursor()
    
    try:
        # 1. Contar productos maestros
        cursor.execute("SELECT COUNT(*) FROM productos_maestros WHERE active = true")
        productos_count = cursor.fetchone()[0]
        print(f"Productos maestros activos: {productos_count}")
        
        # 2. Contar precios actuales
        cursor.execute("SELECT COUNT(*) FROM precios_actuales")
        precios_count = cursor.fetchone()[0]
        print(f"Precios actuales: {precios_count}")
        
        print(f"\nDiscrepancia: {productos_count - precios_count} productos sin precio")
        
        # 3. Buscar productos sin precios
        cursor.execute("""
            SELECT pm.fingerprint, pm.name, pm.brand, pm.created_at
            FROM productos_maestros pm
            LEFT JOIN precios_actuales pa ON pm.fingerprint = pa.fingerprint
            WHERE pm.active = true AND pa.fingerprint IS NULL
            ORDER BY pm.created_at DESC
            LIMIT 15
        """)
        
        productos_sin_precio = cursor.fetchall()
        
        if productos_sin_precio:
            print(f"\nPRODUCTOS SIN PRECIOS ({len(productos_sin_precio)} encontrados):")
            print("=" * 60)
            for i, (fingerprint, name, brand, created_at) in enumerate(productos_sin_precio, 1):
                print(f"{i:2d}. {name[:40]:<40} | {brand or 'Sin marca':<15} | {created_at}")
        
        # 4. Verificar productos insertados recientemente (última hora)
        cursor.execute("""
            SELECT pm.fingerprint, pm.name, pm.brand, pm.created_at,
                   CASE WHEN pa.fingerprint IS NOT NULL THEN 'SI' ELSE 'NO' END as tiene_precio
            FROM productos_maestros pm
            LEFT JOIN precios_actuales pa ON pm.fingerprint = pa.fingerprint
            WHERE pm.created_at >= %s
            ORDER BY pm.created_at DESC
        """, (datetime.now() - timedelta(hours=2),))
        
        productos_recientes = cursor.fetchall()
        
        if productos_recientes:
            print(f"\nPRODUCTOS INSERTADOS ULTIMAS 2 HORAS ({len(productos_recientes)} encontrados):")
            print("=" * 80)
            for fingerprint, name, brand, created_at, tiene_precio in productos_recientes:
                status = "OK" if tiene_precio == 'SI' else "NO"
                print(f"[{status}] {name[:35]:<35} | {brand or 'Sin marca':<12} | {created_at} | Precio: {tiene_precio}")
        
        # 5. Verificar si hay problemas en el campo price de los productos originales
        cursor.execute("""
            SELECT pm.fingerprint, pm.name, pm.attributes
            FROM productos_maestros pm
            LEFT JOIN precios_actuales pa ON pm.fingerprint = pa.fingerprint
            WHERE pm.active = true AND pa.fingerprint IS NULL
            LIMIT 3
        """)
        
        productos_sample = cursor.fetchall()
        
        if productos_sample:
            print(f"\nMUESTRA DE PRODUCTOS SIN PRECIO (primeros 3):")
            print("=" * 60)
            for i, (fingerprint, name, attributes) in enumerate(productos_sample, 1):
                print(f"\n{i}. {name}")
                print(f"   Fingerprint: {fingerprint}")
                if attributes:
                    import json
                    attrs = json.loads(attributes) if isinstance(attributes, str) else attributes
                    # Buscar campos relacionados con precio
                    price_fields = [k for k in attrs.keys() if 'price' in k.lower() or 'precio' in k.lower()]
                    print(f"   Campos precio encontrados: {price_fields}")
                    for field in price_fields[:3]:  # Mostrar máximo 3 campos
                        print(f"     {field}: {attrs[field]}")
                else:
                    print("   Sin atributos")
        
        print(f"\nRESUMEN:")
        print(f"   - Total productos: {productos_count}")
        print(f"   - Total precios: {precios_count}")
        print(f"   - Productos sin precio: {productos_count - precios_count}")
        print(f"   - Productos recientes: {len(productos_recientes)}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()