#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🗑️ Borrar Productos Others
Eliminar productos categorizados como 'others' y su cache IA
"""

import sys
import os

# Agregar src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from unified_connector import get_unified_connector

def delete_others_products():
    print("BORRANDO PRODUCTOS CATEGORIA 'OTHERS'")
    print("=" * 50)
    
    try:
        connector = get_unified_connector()
        
        # 1. Obtener fingerprints de productos 'others'
        query_fingerprints = """
            SELECT fingerprint, name, brand
            FROM productos_maestros 
            WHERE category = 'others' AND active = true
        """
        
        others_products = connector.execute_query(query_fingerprints)
        
        if not others_products:
            print("No hay productos en categoria 'others' para borrar")
            return True
        
        print(f"Productos a borrar: {len(others_products)}")
        print("-" * 60)
        
        fingerprints = []
        for i, product in enumerate(others_products, 1):
            print(f"{i}. {product['name']} | {product['brand']}")
            fingerprints.append(product['fingerprint'])
        
        print("-" * 60)
        
        # 2. Borrar de precios_actuales
        delete_precios = """
            DELETE FROM precios_actuales 
            WHERE fingerprint = ANY(%(fingerprints)s)
        """
        
        result = connector.execute_update(delete_precios, {'fingerprints': fingerprints})
        print(f"Precios borrados: OK")
        
        # 3. Borrar de ai_metadata_cache  
        delete_cache = """
            DELETE FROM ai_metadata_cache 
            WHERE fingerprint = ANY(%(fingerprints)s)
        """
        
        result = connector.execute_update(delete_cache, {'fingerprints': fingerprints})
        print(f"Cache IA borrado: OK")
        
        # 4. Borrar de productos_maestros (marcar como inactivos)
        delete_productos = """
            UPDATE productos_maestros 
            SET active = false 
            WHERE fingerprint = ANY(%(fingerprints)s)
        """
        
        result = connector.execute_update(delete_productos, {'fingerprints': fingerprints})
        print(f"Productos marcados inactivos: OK")
        
        # 5. Verificar limpieza
        verify_query = """
            SELECT COUNT(*) as count
            FROM productos_maestros 
            WHERE category = 'others' AND active = true
        """
        
        remaining = connector.execute_query(verify_query)[0]['count']
        
        if remaining == 0:
            print(f"\nLIMPIEZA COMPLETADA EXITOSAMENTE")
            print(f"- {len(others_products)} productos 'others' eliminados")
            print(f"- Cache IA limpiado")
            print(f"- Precios eliminados") 
            print(f"- Productos marcados como inactivos")
        else:
            print(f"\nADVERTENCIA: Quedan {remaining} productos 'others' activos")
        
        # 6. Estadísticas finales
        stats_query = """
            SELECT 
                (SELECT COUNT(*) FROM productos_maestros WHERE active = true) as productos_activos,
                (SELECT COUNT(*) FROM precios_actuales) as precios_totales,
                (SELECT COUNT(*) FROM ai_metadata_cache) as cache_total
        """
        
        final_stats = connector.execute_query(stats_query)[0]
        
        print(f"\nESTADISTICAS FINALES:")
        print(f"- Productos activos: {final_stats['productos_activos']}")
        print(f"- Precios totales: {final_stats['precios_totales']}")
        print(f"- Cache IA total: {final_stats['cache_total']}")
        
        return True
        
    except Exception as e:
        print(f"ERROR borrando productos others: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    delete_others_products()