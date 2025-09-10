#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
from datetime import datetime

def analyze_cache_discrepancy():
    """Analizar discrepancia entre requests API y cache entries"""
    
    print("=== ANÁLISIS DISCREPANCIA CACHE IA ===")
    print("=" * 50)
    
    # Conectar a BD
    conn = psycopg2.connect(
        host="34.176.197.136",
        port=5432,
        database="postgres",
        user="postgres",
        password="Osmar2503!"
    )
    
    try:
        cursor = conn.cursor()
        
        # 1. Conteo total de cache entries
        print("\n1. RESUMEN CACHE IA:")
        cursor.execute("SELECT COUNT(*) FROM ai_metadata_cache")
        total_cache = cursor.fetchone()[0]
        print(f"   Total entradas cache: {total_cache}")
        
        # 2. Distribución por hits
        cursor.execute("""
            SELECT hits, COUNT(*) as count
            FROM ai_metadata_cache
            GROUP BY hits
            ORDER BY hits
        """)
        
        hits_distribution = cursor.fetchall()
        print(f"\n2. DISTRIBUCIÓN HITS:")
        fresh_requests = 0  # hits = 0 significa request fresco
        reused_cache = 0    # hits > 0 significa cache reutilizado
        
        for hits, count in hits_distribution:
            print(f"   {hits} hits: {count} entradas")
            if hits == 0:
                fresh_requests += count
            else:
                reused_cache += count
        
        print(f"\n   FRESH REQUESTS (hits=0): {fresh_requests}")
        print(f"   CACHE REUTILIZADO (hits>0): {reused_cache}")
        
        # 3. Timeline de creación de cache
        print(f"\n3. TIMELINE CREACIÓN CACHE:")
        cursor.execute("""
            SELECT DATE_TRUNC('minute', created_at) as minute, 
                   COUNT(*) as new_entries,
                   COUNT(CASE WHEN hits = 0 THEN 1 END) as fresh_at_creation
            FROM ai_metadata_cache
            GROUP BY DATE_TRUNC('minute', created_at)
            ORDER BY minute
        """)
        
        timeline = cursor.fetchall()
        total_fresh = 0
        for minute, new_entries, fresh_at_creation in timeline:
            total_fresh += fresh_at_creation
            print(f"   {minute}: {new_entries} nuevas ({fresh_at_creation} fresh) - Acum: {total_fresh}")
        
        # 4. Verificar productos vs cache
        print(f"\n4. PRODUCTOS vs CACHE:")
        cursor.execute("SELECT COUNT(*) FROM productos_maestros WHERE ai_enhanced = true")
        ai_products = cursor.fetchone()[0]
        print(f"   Productos AI enhanced: {ai_products}")
        
        # 5. Buscar posibles duplicados o reutilización
        print(f"\n5. ANÁLISIS FINGERPRINTS:")
        cursor.execute("""
            SELECT amc.fingerprint, amc.hits, COUNT(pm.fingerprint) as products_using_it
            FROM ai_metadata_cache amc
            LEFT JOIN productos_maestros pm ON amc.fingerprint = pm.fingerprint
            WHERE pm.ai_enhanced = true
            GROUP BY amc.fingerprint, amc.hits
            HAVING COUNT(pm.fingerprint) > 1
            ORDER BY COUNT(pm.fingerprint) DESC
            LIMIT 10
        """)
        
        shared_cache = cursor.fetchall()
        if shared_cache:
            print("   Cache compartido entre productos:")
            for fingerprint, hits, product_count in shared_cache:
                print(f"     {fingerprint[:12]}...: {product_count} productos, {hits} hits")
        else:
            print("   No hay cache compartido entre productos")
        
        # 6. CONCLUSIÓN
        print(f"\n" + "="*50)
        print("CONCLUSIÓN ANÁLISIS:")
        print("="*50)
        print(f"• Total cache entries: {total_cache}")
        print(f"• Requests frescos estimados: {fresh_requests}")
        print(f"• Cache reutilizado: {reused_cache}")
        print(f"• Productos AI enhanced: {ai_products}")
        
        if fresh_requests == 16:
            print(f"✅ COINCIDENCIA: {fresh_requests} fresh requests = 16 API requests")
            print(f"   Los otros {total_cache - fresh_requests} son cache hits (no consumen API)")
        else:
            print(f"⚠️  DISCREPANCIA: {fresh_requests} fresh requests vs 16 API requests")
            print(f"   Diferencia: {abs(fresh_requests - 16)}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    analyze_cache_discrepancy()