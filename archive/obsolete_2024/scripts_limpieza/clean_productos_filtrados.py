#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧹 Limpiar Productos Filtrados
Eliminar productos reacondicionados, accesorios y precios bajos de la BD
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'Scrappers'))

from unified_connector import get_unified_connector
from product_filter import ProductFilter

def clean_productos_filtrados():
    print("LIMPIEZA DE PRODUCTOS FILTRADOS")
    print("=" * 50)
    
    try:
        connector = get_unified_connector()
        
        # 1. OBTENER PRODUCTOS ACTUALES
        print("1. Obteniendo productos actuales de la BD...")
        productos = connector.execute_query("""
            SELECT 
                p.id,
                p.product_id,
                p.fingerprint, 
                p.name,
                COALESCE(pr.precio_tarjeta, pr.precio_normal, pr.precio_oferta, 0) as precio_actual,
                p.created_at
            FROM productos_maestros p
            LEFT JOIN precios_actuales pr ON p.product_id = pr.product_id
            WHERE p.active = true
            ORDER BY p.created_at DESC
        """)
        
        print(f"Productos en BD: {len(productos)}")
        
        # 2. APLICAR FILTRO PARA IDENTIFICAR PRODUCTOS PROBLEMÁTICOS
        print("2. Identificando productos que deben eliminarse...")
        
        filter_instance = ProductFilter()
        productos_to_delete = []
        
        for producto in productos:
            # Adaptar formato para el filtro
            product_data = {
                'name': producto['name'],
                'card_price': producto['precio_actual'] or 0
            }
            
            should_filter, reason = filter_instance.should_filter_out(product_data)
            
            if should_filter:
                productos_to_delete.append({
                    'id': producto['id'],
                    'product_id': producto['product_id'],
                    'fingerprint': producto['fingerprint'],
                    'name': producto['name'],
                    'price': producto['precio_actual'],
                    'reason': reason
                })
        
        print(f"Productos a eliminar: {len(productos_to_delete)}")
        
        # 3. MOSTRAR PRODUCTOS QUE SE VAN A ELIMINAR
        if productos_to_delete:
            print("3. Productos que se eliminarán:")
            
            stats = {'reacondicionado': 0, 'accesorio': 0, 'precio_bajo': 0}
            
            for i, product in enumerate(productos_to_delete[:20], 1):  # Mostrar solo primeros 20
                reason = product['reason']
                if 'reacondicionado' in reason:
                    stats['reacondicionado'] += 1
                if 'accesorio' in reason:
                    stats['accesorio'] += 1
                if 'precio_bajo' in reason:
                    stats['precio_bajo'] += 1
                    
                print(f"   {i:2d}. [{reason:15}] {product['name'][:60]} - ${product['price']:,}")
            
            if len(productos_to_delete) > 20:
                print(f"   ... y {len(productos_to_delete) - 20} productos más")
            
            print(f"\nResumen por razón:")
            print(f"   Reacondicionados: {stats['reacondicionado']}")
            print(f"   Accesorios: {stats['accesorio']}")
            print(f"   Precios bajos: {stats['precio_bajo']}")
            
            # 4. ELIMINAR PRODUCTOS
            print(f"\n4. Eliminando {len(productos_to_delete)} productos...")
            
            product_ids_to_delete = [p['product_id'] for p in productos_to_delete]
            fingerprints_to_delete = [p['fingerprint'] for p in productos_to_delete]
            
            # Convertir a listas de strings para la consulta
            product_ids_str = "', '".join(product_ids_to_delete)
            fingerprints_str = "', '".join(fingerprints_to_delete)
            
            # Ejecutar eliminaciones por lotes para evitar problemas
            deleted_precios = 0
            deleted_cache = 0
            updated_productos = 0
            
            # Procesar en lotes de 10 para evitar problemas con consultas muy largas
            batch_size = 10
            for i in range(0, len(product_ids_to_delete), batch_size):
                batch_product_ids = product_ids_to_delete[i:i+batch_size]
                batch_fingerprints = fingerprints_to_delete[i:i+batch_size]
                
                batch_ids_str = "', '".join(batch_product_ids)
                batch_fp_str = "', '".join(batch_fingerprints)
                
                # Eliminar de precios_actuales
                try:
                    connector.execute_query(f"""
                        DELETE FROM precios_actuales 
                        WHERE product_id IN ('{batch_ids_str}')
                    """)
                    deleted_precios += len(batch_product_ids)
                except Exception as e:
                    print(f"   Error eliminando precios lote {i//batch_size + 1}: {e}")
                
                # Eliminar de ai_metadata_cache
                try:
                    connector.execute_query(f"""
                        DELETE FROM ai_metadata_cache 
                        WHERE fingerprint IN ('{batch_fp_str}')
                    """)
                    deleted_cache += len(batch_fingerprints)
                except Exception as e:
                    print(f"   Error eliminando cache lote {i//batch_size + 1}: {e}")
                
                # Marcar como inactivos en productos_maestros
                try:
                    connector.execute_query(f"""
                        UPDATE productos_maestros 
                        SET active = false, updated_at = NOW()
                        WHERE product_id IN ('{batch_ids_str}')
                    """)
                    updated_productos += len(batch_product_ids)
                except Exception as e:
                    print(f"   Error actualizando productos lote {i//batch_size + 1}: {e}")
            
            print(f"   Precios eliminados: {deleted_precios}")
            print(f"   Cache eliminado: {deleted_cache}")
            print(f"   Productos marcados inactivos: {updated_productos}")
            
            print("   Eliminación completada")
            
        else:
            print("3. No hay productos que eliminar")
        
        # 5. VERIFICAR ESTADO FINAL
        print("5. Verificando estado final...")
        final_stats = connector.execute_query("""
            SELECT 
                (SELECT COUNT(*) FROM productos_maestros WHERE active = true) as productos_activos,
                (SELECT COUNT(*) FROM productos_maestros WHERE active = false) as productos_inactivos,
                (SELECT COUNT(*) FROM precios_actuales) as precios_actuales,
                (SELECT COUNT(*) FROM ai_metadata_cache) as cache_ia
        """)[0]
        
        print(f"   Productos activos: {final_stats['productos_activos']}")
        print(f"   Productos inactivos: {final_stats['productos_inactivos']}")
        print(f"   Precios actuales: {final_stats['precios_actuales']}")
        print(f"   Cache IA: {final_stats['cache_ia']}")
        
        # Verificar integridad
        if final_stats['productos_activos'] == final_stats['precios_actuales']:
            print("   ✓ Integridad BD: OK")
        else:
            print("   ⚠ Integridad BD: Discrepancia")
        
        print(f"\n{'='*50}")
        print(f"LIMPIEZA COMPLETADA")
        print(f"Productos eliminados: {len(productos_to_delete)}")
        print(f"Productos válidos restantes: {final_stats['productos_activos']}")
        
        return True
        
    except Exception as e:
        print(f"ERROR en limpieza: {e}")
        return False

if __name__ == "__main__":
    clean_productos_filtrados()