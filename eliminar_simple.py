#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Eliminar Productos Problemáticos - Enfoque Simple
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from unified_connector import get_unified_connector

def eliminar_simple():
    print("ELIMINACION SIMPLE DE PRODUCTOS PROBLEMATICOS")
    print("=" * 60)
    
    try:
        connector = get_unified_connector()
        
        print("1. Eliminando productos reacondicionados...")
        
        # Eliminar productos reacondicionados directamente
        result = connector.execute_update("""
            UPDATE productos_maestros 
            SET active = false, updated_at = NOW()
            WHERE active = true AND (
                LOWER(name) LIKE '%reacondicionado%' OR
                LOWER(name) LIKE '%usado%' OR 
                LOWER(name) LIKE '%refurbished%'
            )
        """, None)
        
        print(f"   {result} productos reacondicionados marcados como inactivos")
        
        print("2. Eliminando accesorios...")
        
        # Eliminar accesorios
        result = connector.execute_update("""
            UPDATE productos_maestros 
            SET active = false, updated_at = NOW()
            WHERE active = true AND (
                LOWER(name) LIKE '%control remoto%' OR
                LOWER(name) LIKE '%cable%' OR
                LOWER(name) LIKE '%funda%' OR
                LOWER(name) LIKE '%cargador%' OR
                LOWER(name) LIKE '%protector%' OR
                LOWER(name) LIKE '%soporte%' OR
                LOWER(name) LIKE '%bateria externa%' OR
                LOWER(name) LIKE '%power bank%'
            )
        """, None)
        
        print(f"   {result} accesorios marcados como inactivos")
        
        print("3. Eliminando precios asociados...")
        
        # Eliminar precios de productos inactivos
        result = connector.execute_update("""
            DELETE FROM precios_actuales 
            WHERE product_id IN (
                SELECT product_id FROM productos_maestros WHERE active = false
            )
        """, None)
        
        print(f"   {result} precios eliminados")
        
        print("4. Limpiando cache IA...")
        
        # Eliminar cache IA de productos inactivos
        result = connector.execute_update("""
            DELETE FROM ai_metadata_cache 
            WHERE fingerprint IN (
                SELECT fingerprint FROM productos_maestros WHERE active = false
            )
        """, None)
        
        print(f"   {result} registros de cache IA eliminados")
        
        print("5. Verificando estado final...")
        
        # Verificar resultado
        stats = connector.execute_query("""
            SELECT 
                (SELECT COUNT(*) FROM productos_maestros WHERE active = true) as activos,
                (SELECT COUNT(*) FROM productos_maestros WHERE active = false) as inactivos,
                (SELECT COUNT(*) FROM precios_actuales) as precios,
                (SELECT COUNT(*) FROM ai_metadata_cache) as cache
        """)[0]
        
        print(f"   Productos activos: {stats['activos']}")
        print(f"   Productos inactivos: {stats['inactivos']}")
        print(f"   Precios actuales: {stats['precios']}")
        print(f"   Cache IA: {stats['cache']}")
        
        # Verificar integridad
        if stats['activos'] == stats['precios']:
            print("   ✓ Integridad BD: OK")
        else:
            print(f"   ⚠ Integridad BD: {stats['activos']} productos vs {stats['precios']} precios")
        
        print(f"\n{'='*60}")
        print("ELIMINACION COMPLETADA")
        print(f"Productos activos restantes: {stats['activos']}")
        print(f"Productos eliminados (inactivos): {stats['inactivos']}")
        print("Base de datos limpia")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    eliminar_simple()