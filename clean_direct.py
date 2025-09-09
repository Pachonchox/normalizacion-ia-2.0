#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Limpieza Directa - Solo consultas de conteo y identificación
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from unified_connector import get_unified_connector

def clean_direct():
    print("LIMPIEZA DIRECTA - IDENTIFICAR PRODUCTOS FILTRADOS")
    print("=" * 60)
    
    try:
        connector = get_unified_connector()
        
        # 1. Estado actual
        print("1. Estado actual BD:")
        stats_inicial = connector.execute_query("""
            SELECT 
                COUNT(*) as total_productos,
                COUNT(CASE WHEN active = true THEN 1 END) as productos_activos,
                COUNT(CASE WHEN active = false THEN 1 END) as productos_inactivos
            FROM productos_maestros
        """)[0]
        
        precios_count = connector.execute_query("SELECT COUNT(*) as count FROM precios_actuales")[0]['count']
        cache_count = connector.execute_query("SELECT COUNT(*) as count FROM ai_metadata_cache")[0]['count']
        
        print(f"   Total productos: {stats_inicial['total_productos']}")
        print(f"   Productos activos: {stats_inicial['productos_activos']}")
        print(f"   Productos inactivos: {stats_inicial['productos_inactivos']}")
        print(f"   Precios actuales: {precios_count}")
        print(f"   Cache IA: {cache_count}")
        
        # 2. Identificar productos problemáticos
        print("\n2. Identificando productos problemáticos:")
        
        # Reacondicionados
        reacondicionados_result = connector.execute_query("""
            SELECT COUNT(*) as count FROM productos_maestros 
            WHERE active = true AND (
                LOWER(name) LIKE '%reacondicionado%' OR
                LOWER(name) LIKE '%usado%' OR
                LOWER(name) LIKE '%refurbished%'
            )
        """)
        reacondicionados = reacondicionados_result[0]['count'] if reacondicionados_result else 0
        
        # Accesorios
        accesorios_result = connector.execute_query("""
            SELECT COUNT(*) as count FROM productos_maestros 
            WHERE active = true AND (
                LOWER(name) LIKE '%control%' OR
                LOWER(name) LIKE '%cable%' OR
                LOWER(name) LIKE '%funda%' OR
                LOWER(name) LIKE '%cargador%' OR
                LOWER(name) LIKE '%protector%' OR
                LOWER(name) LIKE '%soporte%' OR
                LOWER(name) LIKE '%bateria externa%' OR
                LOWER(name) LIKE '%power bank%'
            )
        """)
        accesorios = accesorios_result[0]['count'] if accesorios_result else 0
        
        # Precios bajos
        precios_bajos_result = connector.execute_query("""
            SELECT COUNT(*) as count
            FROM productos_maestros p
            LEFT JOIN precios_actuales pr ON p.product_id = pr.product_id
            WHERE p.active = true 
            AND COALESCE(pr.precio_tarjeta, pr.precio_normal, pr.precio_oferta, 0) > 0
            AND COALESCE(pr.precio_tarjeta, pr.precio_normal, pr.precio_oferta, 0) < 50000
        """)
        precios_bajos = precios_bajos_result[0]['count'] if precios_bajos_result else 0
        
        print(f"   Reacondicionados: {reacondicionados}")
        print(f"   Accesorios: {accesorios}")
        print(f"   Precios bajos (<50K): {precios_bajos}")
        
        # 3. Muestra de productos problemáticos
        print("\n3. Muestra de productos reacondicionados:")
        muestra_reacondicionados = connector.execute_query("""
            SELECT name FROM productos_maestros 
            WHERE active = true AND (
                LOWER(name) LIKE '%reacondicionado%' OR
                LOWER(name) LIKE '%usado%' OR
                LOWER(name) LIKE '%refurbished%'
            )
            LIMIT 10
        """)
        
        for i, producto in enumerate(muestra_reacondicionados, 1):
            print(f"   {i:2d}. {producto['name'][:80]}")
        
        print("\n4. Muestra de accesorios:")
        muestra_accesorios = connector.execute_query("""
            SELECT name FROM productos_maestros 
            WHERE active = true AND (
                LOWER(name) LIKE '%control%' OR
                LOWER(name) LIKE '%cable%' OR
                LOWER(name) LIKE '%funda%' OR
                LOWER(name) LIKE '%cargador%' OR
                LOWER(name) LIKE '%protector%' OR
                LOWER(name) LIKE '%soporte%' OR
                LOWER(name) LIKE '%bateria externa%' OR
                LOWER(name) LIKE '%power bank%'
            )
            LIMIT 10
        """)
        
        for i, producto in enumerate(muestra_accesorios, 1):
            print(f"   {i:2d}. {producto['name'][:80]}")
        
        print("\n5. Muestra de precios bajos:")
        muestra_precios = connector.execute_query("""
            SELECT p.name, COALESCE(pr.precio_tarjeta, pr.precio_normal, pr.precio_oferta, 0) as precio
            FROM productos_maestros p
            LEFT JOIN precios_actuales pr ON p.product_id = pr.product_id
            WHERE p.active = true 
            AND COALESCE(pr.precio_tarjeta, pr.precio_normal, pr.precio_oferta, 0) > 0
            AND COALESCE(pr.precio_tarjeta, pr.precio_normal, pr.precio_oferta, 0) < 50000
            LIMIT 10
        """)
        
        for i, producto in enumerate(muestra_precios, 1):
            print(f"   {i:2d}. {producto['name'][:60]} - ${producto['precio']:,}")
        
        total_filtrar = reacondicionados + accesorios + precios_bajos
        productos_limpios_estimados = stats_inicial['productos_activos'] - total_filtrar
        
        print(f"\n{'='*60}")
        print(f"RESUMEN:")
        print(f"Productos actuales activos: {stats_inicial['productos_activos']}")
        print(f"Productos a filtrar (estimado): {total_filtrar}")
        print(f"  - Reacondicionados: {reacondicionados}")
        print(f"  - Accesorios: {accesorios}")  
        print(f"  - Precios bajos: {precios_bajos}")
        print(f"Productos limpios estimados: {productos_limpios_estimados}")
        
        # Verificar si el filtro integrado funcionará ahora
        print(f"\nEL FILTRO INTEGRADO AHORA DEBERÍA FUNCIONAR")
        print(f"Al hacer nueva inserción masiva, estos productos serán filtrados automáticamente")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    clean_direct()