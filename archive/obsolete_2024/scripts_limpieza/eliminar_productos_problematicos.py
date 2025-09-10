#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🗑️ Eliminar Productos Problemáticos
Eliminar productos reacondicionados, accesorios y precios bajos de la BD
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from unified_connector import get_unified_connector

def eliminar_productos_problematicos():
    print("ELIMINACION DE PRODUCTOS PROBLEMATICOS")
    print("=" * 60)
    
    try:
        connector = get_unified_connector()
        
        # 1. IDENTIFICAR PRODUCTOS PROBLEMÁTICOS
        print("1. Identificando productos problemáticos...")
        
        # Consulta para identificar productos problemáticos
        productos_problematicos = connector.execute_query("""
            SELECT DISTINCT p.product_id, p.name,
                   COALESCE(pr.precio_tarjeta, pr.precio_normal, pr.precio_oferta, 0) as precio_actual,
                   CASE 
                       WHEN (LOWER(p.name) LIKE '%reacondicionado%' OR 
                             LOWER(p.name) LIKE '%usado%' OR 
                             LOWER(p.name) LIKE '%refurbished%') THEN 'reacondicionado'
                       WHEN (LOWER(p.name) LIKE '%control%' OR 
                             LOWER(p.name) LIKE '%cable%' OR 
                             LOWER(p.name) LIKE '%funda%' OR 
                             LOWER(p.name) LIKE '%cargador%' OR 
                             LOWER(p.name) LIKE '%protector%' OR 
                             LOWER(p.name) LIKE '%soporte%' OR 
                             LOWER(p.name) LIKE '%bateria externa%' OR 
                             LOWER(p.name) LIKE '%power bank%') THEN 'accesorio'
                       WHEN COALESCE(pr.precio_tarjeta, pr.precio_normal, pr.precio_oferta, 0) < 50000 
                            AND COALESCE(pr.precio_tarjeta, pr.precio_normal, pr.precio_oferta, 0) > 0 THEN 'precio_bajo'
                       ELSE 'otros'
                   END as razon
            FROM productos_maestros p
            LEFT JOIN precios_actuales pr ON p.product_id = pr.product_id
            WHERE p.active = true
            AND (
                -- Reacondicionados
                (LOWER(p.name) LIKE '%reacondicionado%' OR 
                 LOWER(p.name) LIKE '%usado%' OR 
                 LOWER(p.name) LIKE '%refurbished%')
                OR
                -- Accesorios
                (LOWER(p.name) LIKE '%control%' OR 
                 LOWER(p.name) LIKE '%cable%' OR 
                 LOWER(p.name) LIKE '%funda%' OR 
                 LOWER(p.name) LIKE '%cargador%' OR 
                 LOWER(p.name) LIKE '%protector%' OR 
                 LOWER(p.name) LIKE '%soporte%' OR 
                 LOWER(p.name) LIKE '%bateria externa%' OR 
                 LOWER(p.name) LIKE '%power bank%')
                OR
                -- Precios bajos
                (COALESCE(pr.precio_tarjeta, pr.precio_normal, pr.precio_oferta, 0) < 50000 
                 AND COALESCE(pr.precio_tarjeta, pr.precio_normal, pr.precio_oferta, 0) > 0)
            )
            ORDER BY razon, p.name
        """)
        
        print(f"Productos problemáticos encontrados: {len(productos_problematicos)}")
        
        if len(productos_problematicos) == 0:
            print("No hay productos problemáticos para eliminar")
            return True
        
        # Agrupar por razón
        stats = {'reacondicionado': 0, 'accesorio': 0, 'precio_bajo': 0}
        
        print("\n2. Productos que se eliminarán:")
        for i, producto in enumerate(productos_problematicos[:20], 1):  # Mostrar primeros 20
            razon = producto['razon']
            stats[razon] += 1
            precio = producto['precio_actual'] or 0
            print(f"   {i:2d}. [{razon:12}] {producto['name'][:60]} - ${precio:,}")
        
        if len(productos_problematicos) > 20:
            print(f"   ... y {len(productos_problematicos) - 20} productos más")
        
        print(f"\nResumen:")
        print(f"   Reacondicionados: {stats['reacondicionado']}")
        print(f"   Accesorios: {stats['accesorio']}")
        print(f"   Precios bajos: {stats['precio_bajo']}")
        print(f"   Total a eliminar: {len(productos_problematicos)}")
        
        # 3. ELIMINAR PRODUCTOS
        print(f"\n3. Eliminando {len(productos_problematicos)} productos...")
        
        product_ids_to_delete = [p['product_id'] for p in productos_problematicos]
        
        # Eliminar en lotes para evitar problemas
        batch_size = 50
        deleted_precios = 0
        deleted_cache = 0 
        updated_productos = 0
        
        for i in range(0, len(product_ids_to_delete), batch_size):
            batch = product_ids_to_delete[i:i+batch_size]
            
            print(f"   Procesando lote {i//batch_size + 1}/{(len(product_ids_to_delete)-1)//batch_size + 1}...")
            
            # Eliminar usando consultas simples con IN 
            batch_str = "', '".join(batch)
            
            try:
                # Eliminar precios_actuales
                connector.execute_query(f"""
                    DELETE FROM precios_actuales 
                    WHERE product_id IN ('{batch_str}')
                """)
                deleted_precios += len(batch)
            except Exception as e:
                print(f"     Error eliminando precios: {e}")
            
            try:
                # Eliminar cache IA
                connector.execute_query(f"""
                    DELETE FROM ai_metadata_cache 
                    WHERE fingerprint IN (
                        SELECT fingerprint FROM productos_maestros 
                        WHERE product_id IN ('{batch_str}')
                    )
                """)
                deleted_cache += len(batch)
            except Exception as e:
                print(f"     Error eliminando cache: {e}")
            
            try:
                # Marcar productos como inactivos
                connector.execute_query(f"""
                    UPDATE productos_maestros 
                    SET active = false, updated_at = NOW()
                    WHERE product_id IN ('{batch_str}')
                """)
                updated_productos += len(batch)
            except Exception as e:
                print(f"     Error actualizando productos: {e}")
        
        print(f"   Precios eliminados: {deleted_precios}")
        print(f"   Cache eliminado: {deleted_cache}")
        print(f"   Productos marcados inactivos: {updated_productos}")
        
        # 4. VERIFICAR RESULTADO FINAL
        print("\n4. Verificando estado final...")
        
        stats_final = connector.execute_query("""
            SELECT 
                (SELECT COUNT(*) FROM productos_maestros WHERE active = true) as activos,
                (SELECT COUNT(*) FROM productos_maestros WHERE active = false) as inactivos,
                (SELECT COUNT(*) FROM precios_actuales) as precios,
                (SELECT COUNT(*) FROM ai_metadata_cache) as cache
        """)[0]
        
        print(f"   Productos activos: {stats_final['activos']}")
        print(f"   Productos inactivos: {stats_final['inactivos']}")
        print(f"   Precios actuales: {stats_final['precios']}")
        print(f"   Cache IA: {stats_final['cache']}")
        
        # Verificar integridad
        if stats_final['activos'] == stats_final['precios']:
            print("   ✓ Integridad BD: OK (productos = precios)")
        else:
            print(f"   ⚠ Integridad BD: Discrepancia ({stats_final['activos']} productos vs {stats_final['precios']} precios)")
        
        print(f"\n{'='*60}")
        print(f"ELIMINACION COMPLETADA")
        print(f"Productos eliminados: {len(productos_problematicos)}")
        print(f"Productos válidos restantes: {stats_final['activos']}")
        print(f"Base de datos limpia y lista")
        
        return True
        
    except Exception as e:
        print(f"ERROR en eliminación: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    eliminar_productos_problematicos()