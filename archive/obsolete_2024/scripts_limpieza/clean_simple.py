#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Limpieza Simple - Eliminar productos reacondicionados y accesorios
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from unified_connector import get_unified_connector

def clean_simple():
    print("LIMPIEZA SIMPLE - PRODUCTOS FILTRADOS")
    print("=" * 50)
    
    try:
        connector = get_unified_connector()
        
        # Obtener conexion raw para ejecutar comandos directos
        conn = connector.get_connection()
        cursor = conn.cursor()
        
        # 1. Productos reacondicionados por nombre
        reacondicionados_query = """
            SELECT product_id, name FROM productos_maestros 
            WHERE active = true AND (
                LOWER(name) LIKE '%reacondicionado%' OR
                LOWER(name) LIKE '%usado%' OR
                LOWER(name) LIKE '%refurbished%'
            )
        """
        
        cursor.execute(reacondicionados_query)
        reacondicionados = cursor.fetchall()
        
        print(f"Productos reacondicionados encontrados: {len(reacondicionados)}")
        for product_id, name in reacondicionados[:5]:
            print(f"  - {name[:60]}...")
        
        # 2. Accesorios por nombre (controles, cables, etc)
        accesorios_query = """
            SELECT product_id, name FROM productos_maestros 
            WHERE active = true AND (
                LOWER(name) LIKE '%control%' OR
                LOWER(name) LIKE '%cable%' OR
                LOWER(name) LIKE '%funda%' OR
                LOWER(name) LIKE '%cargador%' OR
                LOWER(name) LIKE '%protector%' OR
                LOWER(name) LIKE '%soporte%' OR
                LOWER(name) LIKE '%audifonos%' OR
                LOWER(name) LIKE '%bateria%' OR
                LOWER(name) LIKE '%memoria%'
            )
        """
        
        cursor.execute(accesorios_query)
        accesorios = cursor.fetchall()
        
        print(f"Accesorios encontrados: {len(accesorios)}")
        for product_id, name in accesorios[:5]:
            print(f"  - {name[:60]}...")
        
        # 3. Productos precio bajo (usando JOIN con precios_actuales)
        precio_bajo_query = """
            SELECT p.product_id, p.name, COALESCE(pr.precio_tarjeta, pr.precio_normal, pr.precio_oferta, 0) as precio
            FROM productos_maestros p
            LEFT JOIN precios_actuales pr ON p.product_id = pr.product_id
            WHERE p.active = true 
            AND COALESCE(pr.precio_tarjeta, pr.precio_normal, pr.precio_oferta, 0) > 0
            AND COALESCE(pr.precio_tarjeta, pr.precio_normal, pr.precio_oferta, 0) < 50000
        """
        
        cursor.execute(precio_bajo_query)
        precios_bajos = cursor.fetchall()
        
        print(f"Productos precio bajo (<50K) encontrados: {len(precios_bajos)}")
        for product_id, name, precio in precios_bajos[:5]:
            print(f"  - {name[:50]}... ${precio:,}")
        
        # Combinar todos los product_ids a eliminar (evitar duplicados)
        all_product_ids = set()
        
        for product_id, _ in reacondicionados:
            all_product_ids.add(product_id)
        
        for product_id, _ in accesorios:
            all_product_ids.add(product_id)
            
        for product_id, _, _ in precios_bajos:
            all_product_ids.add(product_id)
        
        print(f"\nTotal productos únicos a eliminar: {len(all_product_ids)}")
        
        if len(all_product_ids) > 0:
            # 4. ELIMINAR EN BATCH
            print("4. Eliminando productos...")
            
            # Convertir a lista para procesar
            product_ids_list = list(all_product_ids)
            
            # Eliminar precios_actuales
            for product_id in product_ids_list:
                cursor.execute("DELETE FROM precios_actuales WHERE product_id = %s", (product_id,))
            
            # Eliminar ai_metadata_cache (por fingerprint - necesitamos obtenerlo)
            cursor.execute("""
                DELETE FROM ai_metadata_cache 
                WHERE fingerprint IN (
                    SELECT fingerprint FROM productos_maestros 
                    WHERE product_id = ANY(%s)
                )
            """, (product_ids_list,))
            
            # Marcar como inactivos productos_maestros
            cursor.execute("""
                UPDATE productos_maestros 
                SET active = false, updated_at = NOW()
                WHERE product_id = ANY(%s)
            """, (product_ids_list,))
            
            # Confirmar transacción
            conn.commit()
            
            print("   Eliminación completada")
        
        # 5. Verificar resultado
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM productos_maestros WHERE active = true) as activos,
                (SELECT COUNT(*) FROM productos_maestros WHERE active = false) as inactivos,
                (SELECT COUNT(*) FROM precios_actuales) as precios,
                (SELECT COUNT(*) FROM ai_metadata_cache) as cache
        """)
        
        stats = cursor.fetchone()
        activos, inactivos, precios, cache = stats
        
        print(f"\n5. Estado final:")
        print(f"   Productos activos: {activos}")
        print(f"   Productos inactivos: {inactivos}")
        print(f"   Precios actuales: {precios}")
        print(f"   Cache IA: {cache}")
        
        if activos == precios:
            print("   Integridad BD: OK")
        else:
            print(f"   Integridad BD: ADVERTENCIA ({activos} productos != {precios} precios)")
        
        cursor.close()
        conn.close()
        
        print(f"\n{'='*50}")
        print(f"LIMPIEZA COMPLETADA")
        print(f"Productos eliminados: {len(all_product_ids)}")
        print(f"Productos válidos restantes: {activos}")
        
        return True
        
    except Exception as e:
        print(f"ERROR en limpieza: {e}")
        return False

if __name__ == "__main__":
    clean_simple()