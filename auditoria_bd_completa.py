#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 Auditoría Completa de Base de Datos
Análisis exhaustivo de la integridad, calidad y consistencia de los datos
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import psycopg2
from psycopg2 import extras
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def execute_query(query):
    """Ejecutar consulta con conexión directa"""
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', '34.176.197.136'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'postgres'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD')
    }
    
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    cursor.execute(query)
    results = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return results

def auditoria_completa():
    print("AUDITORIA COMPLETA DE BASE DE DATOS")
    print("=" * 80)
    
    try:
        
        # ESTADISTICAS GENERALES
        print("\n1. ESTADISTICAS GENERALES")
        print("-" * 50)
        
        stats = execute_query("""
            SELECT 
                (SELECT COUNT(*) FROM productos_maestros WHERE active = true) as productos_activos,
                (SELECT COUNT(*) FROM productos_maestros WHERE active = false) as productos_inactivos,
                (SELECT COUNT(*) FROM precios_actuales) as precios_totales,
                (SELECT COUNT(*) FROM ai_metadata_cache) as cache_ia_total,
                (SELECT COUNT(*) FROM retailers) as retailers_total,
                (SELECT COUNT(DISTINCT retailer_id) FROM precios_actuales) as retailers_activos,
                (SELECT COUNT(*) FROM processing_logs WHERE created_at >= NOW() - INTERVAL '24 hours') as logs_24h,
                (SELECT COUNT(*) FROM processing_logs WHERE created_at >= NOW() - INTERVAL '1 hour') as logs_1h
        """)[0]
        
        print(f"   Productos activos: {stats['productos_activos']:,}")
        print(f"   Productos inactivos: {stats['productos_inactivos']:,}")
        print(f"   Precios actuales: {stats['precios_totales']:,}")
        print(f"   Cache IA: {stats['cache_ia_total']:,}")
        print(f"   Retailers totales: {stats['retailers_total']}")
        print(f"   Retailers activos: {stats['retailers_activos']}")
        print(f"   Logs últimas 24h: {stats['logs_24h']}")
        print(f"   Logs última 1h: {stats['logs_1h']}")
        
        # INTEGRIDAD DE DATOS
        print("\n2. INTEGRIDAD DE DATOS")
        print("-" * 50)
        
        # Productos sin precios
        productos_sin_precios = execute_query("""
            SELECT COUNT(*) as count 
            FROM productos_maestros pm 
            WHERE pm.active = true 
            AND pm.product_id NOT IN (
                SELECT DISTINCT product_id FROM precios_actuales
            )
        """)[0]['count']
        
        # Precios sin productos
        precios_huerfanos = execute_query("""
            SELECT COUNT(*) as count 
            FROM precios_actuales pa 
            WHERE pa.product_id NOT IN (
                SELECT product_id FROM productos_maestros WHERE active = true
            )
        """)[0]['count']
        
        # Cache IA huerfano
        cache_huerfano = execute_query("""
            SELECT COUNT(*) as count 
            FROM ai_metadata_cache aic 
            WHERE aic.fingerprint NOT IN (
                SELECT fingerprint FROM productos_maestros WHERE active = true
            )
        """)[0]['count']
        
        print(f"   Integridad productos/precios: {stats['productos_activos'] == stats['precios_totales']}")
        if productos_sin_precios > 0:
            print(f"   Productos sin precios: {productos_sin_precios}")
        if precios_huerfanos > 0:
            print(f"   Precios huerfanos: {precios_huerfanos}")
        if cache_huerfano > 0:
            print(f"   Cache IA huerfano: {cache_huerfano}")
        
        # ANALISIS POR CATEGORIAS
        print("\n3. ANALISIS POR CATEGORIAS")
        print("-" * 50)
        
        categorias = execute_query("""
            SELECT 
                category,
                COUNT(*) as total_productos,
                AVG(COALESCE(pa.precio_tarjeta, pa.precio_normal, pa.precio_oferta, 0)) as precio_promedio,
                MIN(COALESCE(pa.precio_tarjeta, pa.precio_normal, pa.precio_oferta, 0)) as precio_min,
                MAX(COALESCE(pa.precio_tarjeta, pa.precio_normal, pa.precio_oferta, 0)) as precio_max,
                COUNT(CASE WHEN pm.ai_enhanced = true THEN 1 END) as con_ia
            FROM productos_maestros pm
            LEFT JOIN precios_actuales pa ON pm.product_id = pa.product_id
            WHERE pm.active = true
            GROUP BY category
            ORDER BY total_productos DESC
        """)
        
        for cat in categorias:
            precio_prom = cat['precio_promedio'] or 0
            precio_min = cat['precio_min'] or 0
            precio_max = cat['precio_max'] or 0
            pct_ia = (cat['con_ia'] / cat['total_productos'] * 100) if cat['total_productos'] > 0 else 0
            
            print(f"   {cat['category']:15} | {cat['total_productos']:4} productos | "
                  f"${precio_prom:,.0f} promedio | ${precio_min:,.0f}-${precio_max:,.0f} | "
                  f"{pct_ia:.1f}% IA")
        
        # ANALISIS POR RETAILER
        print("\n4. ANALISIS POR RETAILER")
        print("-" * 50)
        
        retailers = execute_query("""
            SELECT 
                r.name as retailer_name,
                COUNT(pa.product_id) as total_productos,
                AVG(COALESCE(pa.precio_tarjeta, pa.precio_normal, pa.precio_oferta, 0)) as precio_promedio,
                MIN(pa.updated_at) as primera_actualizacion,
                MAX(pa.updated_at) as ultima_actualizacion
            FROM retailers r
            LEFT JOIN precios_actuales pa ON r.id = pa.retailer_id
            LEFT JOIN productos_maestros pm ON pa.product_id = pm.product_id AND pm.active = true
            GROUP BY r.id, r.name
            ORDER BY total_productos DESC
        """)
        
        for ret in retailers:
            if ret['total_productos'] > 0:
                precio_prom = ret['precio_promedio'] or 0
                primera = ret['primera_actualizacion'] or "N/A"
                ultima = ret['ultima_actualizacion'] or "N/A"
                print(f"   {ret['retailer_name']:15} | {ret['total_productos']:4} productos | "
                      f"${precio_prom:,.0f} promedio | Última: {ultima}")
            else:
                print(f"   {ret['retailer_name']:15} | Sin productos")
        
        # ANALISIS DE IA Y CACHE
        print("\n5. ANALISIS DE IA Y CACHE")
        print("-" * 50)
        
        ia_stats = execute_query("""
            SELECT 
                COUNT(*) as total_productos,
                COUNT(CASE WHEN ai_enhanced = true THEN 1 END) as con_ia,
                AVG(ai_confidence) as confidence_promedio,
                MIN(ai_confidence) as confidence_min,
                MAX(ai_confidence) as confidence_max
            FROM productos_maestros 
            WHERE active = true
        """)[0]
        
        cache_stats = execute_query("""
            SELECT 
                COUNT(*) as total_cache,
                AVG(hits) as hits_promedio,
                MAX(hits) as hits_max,
                COUNT(CASE WHEN hits > 1 THEN 1 END) as reutilizados
            FROM ai_metadata_cache
        """)[0]
        
        pct_ia = (ia_stats['con_ia'] / ia_stats['total_productos'] * 100) if ia_stats['total_productos'] > 0 else 0
        pct_cache_reutilizado = (cache_stats['reutilizados'] / cache_stats['total_cache'] * 100) if cache_stats['total_cache'] > 0 else 0
        
        print(f"   Productos con IA: {ia_stats['con_ia']}/{ia_stats['total_productos']} ({pct_ia:.1f}%)")
        print(f"   Confianza IA promedio: {ia_stats['confidence_promedio']:.3f}")
        print(f"   Confianza IA rango: {ia_stats['confidence_min']:.3f} - {ia_stats['confidence_max']:.3f}")
        print(f"   Entradas cache total: {cache_stats['total_cache']}")
        print(f"   Cache reutilizado: {cache_stats['reutilizados']}/{cache_stats['total_cache']} ({pct_cache_reutilizado:.1f}%)")
        print(f"   Hits promedio: {cache_stats['hits_promedio']:.1f}")
        print(f"   Hits máximo: {cache_stats['hits_max']}")
        
        # ANALISIS DE PRECIOS
        print("\n6. ANALISIS DE PRECIOS")
        print("-" * 50)
        
        precio_stats = execute_query("""
            SELECT 
                COUNT(*) as total_precios,
                COUNT(CASE WHEN precio_normal IS NOT NULL THEN 1 END) as con_precio_normal,
                COUNT(CASE WHEN precio_tarjeta IS NOT NULL THEN 1 END) as con_precio_tarjeta,
                COUNT(CASE WHEN precio_oferta IS NOT NULL THEN 1 END) as con_precio_oferta,
                AVG(COALESCE(precio_tarjeta, precio_normal, precio_oferta, 0)) as precio_promedio_general,
                MIN(COALESCE(precio_tarjeta, precio_normal, precio_oferta, 999999999)) as precio_min_general,
                MAX(COALESCE(precio_tarjeta, precio_normal, precio_oferta, 0)) as precio_max_general,
                COUNT(CASE WHEN COALESCE(precio_tarjeta, precio_normal, precio_oferta, 0) < 50000 THEN 1 END) as precios_bajos,
                COUNT(CASE WHEN COALESCE(precio_tarjeta, precio_normal, precio_oferta, 0) > 1000000 THEN 1 END) as precios_altos
            FROM precios_actuales
        """)[0]
        
        print(f"   Total precios: {precio_stats['total_precios']:,}")
        print(f"   Con precio normal: {precio_stats['con_precio_normal']:,}")
        print(f"   Con precio tarjeta: {precio_stats['con_precio_tarjeta']:,}")
        print(f"   Con precio oferta: {precio_stats['con_precio_oferta']:,}")
        print(f"   Precio promedio: ${precio_stats['precio_promedio_general']:,.0f}")
        print(f"   Rango precios: ${precio_stats['precio_min_general']:,.0f} - ${precio_stats['precio_max_general']:,.0f}")
        print(f"   Precios < $50.000: {precio_stats['precios_bajos']:,}")
        print(f"   Precios > $1.000.000: {precio_stats['precios_altos']:,}")
        
        # DETECCION DE PRODUCTOS PROBLEMATICOS
        print("\n7. DETECCION DE PRODUCTOS PROBLEMATICOS")
        print("-" * 50)
        
        problematicos_query = """
            SELECT 
                pm.product_id,
                pm.name,
                COALESCE(pa.precio_tarjeta, pa.precio_normal, pa.precio_oferta, 0) as precio_actual,
                CASE 
                    WHEN (LOWER(pm.name) LIKE '%reacondicionado%' OR 
                          LOWER(pm.name) LIKE '%usado%' OR 
                          LOWER(pm.name) LIKE '%refurbished%') THEN 'reacondicionado'
                    WHEN (LOWER(pm.name) LIKE '%control%' OR 
                          LOWER(pm.name) LIKE '%cable%' OR 
                          LOWER(pm.name) LIKE '%funda%' OR 
                          LOWER(pm.name) LIKE '%cargador%' OR 
                          LOWER(pm.name) LIKE '%protector%' OR 
                          LOWER(pm.name) LIKE '%soporte%' OR 
                          LOWER(pm.name) LIKE '%bateria externa%' OR 
                          LOWER(pm.name) LIKE '%power bank%') THEN 'accesorio'
                    WHEN COALESCE(pa.precio_tarjeta, pa.precio_normal, pa.precio_oferta, 0) < 50000 
                         AND COALESCE(pa.precio_tarjeta, pa.precio_normal, pa.precio_oferta, 0) > 0 THEN 'precio_bajo'
                    ELSE NULL
                END as problema
            FROM productos_maestros pm
            LEFT JOIN precios_actuales pa ON pm.product_id = pa.product_id
            WHERE pm.active = true
            AND (
                -- Reacondicionados
                (LOWER(pm.name) LIKE '%reacondicionado%' OR 
                 LOWER(pm.name) LIKE '%usado%' OR 
                 LOWER(pm.name) LIKE '%refurbished%')
                OR
                -- Accesorios
                (LOWER(pm.name) LIKE '%control%' OR 
                 LOWER(pm.name) LIKE '%cable%' OR 
                 LOWER(pm.name) LIKE '%funda%' OR 
                 LOWER(pm.name) LIKE '%cargador%' OR 
                 LOWER(pm.name) LIKE '%protector%' OR 
                 LOWER(pm.name) LIKE '%soporte%' OR 
                 LOWER(pm.name) LIKE '%bateria externa%' OR 
                 LOWER(pm.name) LIKE '%power bank%')
                OR
                -- Precios bajos
                (COALESCE(pa.precio_tarjeta, pa.precio_normal, pa.precio_oferta, 0) < 50000 
                 AND COALESCE(pa.precio_tarjeta, pa.precio_normal, pa.precio_oferta, 0) > 0)
            )
            ORDER BY problema, pm.name
        """
        
        problematicos = execute_query(problematicos_query)
        
        if problematicos:
            stats_problematicos = {'reacondicionado': 0, 'accesorio': 0, 'precio_bajo': 0}
            
            print(f"   PRODUCTOS PROBLEMATICOS DETECTADOS: {len(problematicos)}")
            print("\n   Primeros 10 productos problemáticos:")
            
            for i, producto in enumerate(problematicos[:10], 1):
                problema = producto['problema']
                if problema:
                    stats_problematicos[problema] += 1
                precio = producto['precio_actual'] or 0
                print(f"      {i:2d}. [{problema:12}] {producto['name'][:50]}... - ${precio:,}")
            
            if len(problematicos) > 10:
                # Contar el resto
                for producto in problematicos[10:]:
                    problema = producto['problema']
                    if problema:
                        stats_problematicos[problema] += 1
                
                print(f"      ... y {len(problematicos) - 10} productos más")
            
            print(f"\n   Resumen productos problemáticos:")
            print(f"      Reacondicionados: {stats_problematicos['reacondicionado']}")
            print(f"      Accesorios: {stats_problematicos['accesorio']}")
            print(f"      Precios bajos: {stats_problematicos['precio_bajo']}")
            
            print(f"\n   ACCION REQUERIDA: Eliminar {len(problematicos)} productos problematicos")
        else:
            print("   No se detectaron productos problematicos")
        
        # ANALISIS DE ACTIVIDAD RECIENTE
        print("\n8. ANALISIS DE ACTIVIDAD RECIENTE")
        print("-" * 50)
        
        # Productos añadidos en las últimas 24h
        productos_recientes = execute_query("""
            SELECT COUNT(*) as count 
            FROM productos_maestros 
            WHERE created_at >= NOW() - INTERVAL '24 hours'
        """)[0]['count']
        
        # Precios actualizados en las últimas 24h
        precios_actualizados = execute_query("""
            SELECT COUNT(*) as count 
            FROM precios_actuales 
            WHERE updated_at >= NOW() - INTERVAL '24 hours'
        """)[0]['count']
        
        # Cache IA usado recientemente
        cache_reciente = execute_query("""
            SELECT COUNT(*) as count 
            FROM ai_metadata_cache 
            WHERE updated_at >= NOW() - INTERVAL '24 hours'
        """)[0]['count']
        
        print(f"   Productos añadidos últimas 24h: {productos_recientes}")
        print(f"   Precios actualizados últimas 24h: {precios_actualizados}")
        print(f"   Cache IA usado últimas 24h: {cache_reciente}")
        
        # RECOMENDACIONES DE MANTENIMIENTO
        print("\n9. RECOMENDACIONES DE MANTENIMIENTO")
        print("-" * 50)
        
        recomendaciones = []
        
        if productos_sin_precios > 0:
            recomendaciones.append(f"• Revisar {productos_sin_precios} productos sin precios")
        
        if precios_huerfanos > 0:
            recomendaciones.append(f"• Limpiar {precios_huerfanos} precios huérfanos")
        
        if cache_huerfano > 0:
            recomendaciones.append(f"• Limpiar {cache_huerfano} entradas de cache IA huérfanas")
        
        if problematicos:
            recomendaciones.append(f"• Eliminar {len(problematicos)} productos problemáticos")
        
        if pct_ia < 90:
            recomendaciones.append(f"• Mejorar cobertura IA ({pct_ia:.1f}% actual)")
        
        if precio_stats['precios_bajos'] > 0:
            recomendaciones.append(f"• Revisar {precio_stats['precios_bajos']} productos con precios < $50.000")
        
        if recomendaciones:
            for rec in recomendaciones:
                print(f"   {rec}")
        else:
            print("   No se detectaron problemas que requieran mantenimiento")
        
        # RESUMEN EJECUTIVO
        print("\n10. RESUMEN EJECUTIVO")
        print("=" * 50)
        
        print(f"   Database Health Score: ", end="")
        
        # Calcular score de salud
        score = 100
        if productos_sin_precios > 0:
            score -= 20
        if precios_huerfanos > 0:
            score -= 15
        if problematicos:
            score -= 30
        if pct_ia < 80:
            score -= 10
        if cache_huerfano > 0:
            score -= 5
        
        if score >= 90:
            print(f"[VERDE] {score}/100 - EXCELENTE")
        elif score >= 70:
            print(f"[AMARILLO] {score}/100 - BUENO")
        elif score >= 50:
            print(f"[NARANJA] {score}/100 - REGULAR")
        else:
            print(f"[ROJO] {score}/100 - CRITICO")
        
        print(f"\n   Estado general:")
        print(f"   • {stats['productos_activos']:,} productos activos con {stats['precios_totales']:,} precios")
        print(f"   • {pct_ia:.1f}% productos enriquecidos con IA")
        print(f"   • {len(categorias)} categorías activas")
        print(f"   • {stats['retailers_activos']} retailers con productos")
        print(f"   • Cache IA con {pct_cache_reutilizado:.1f}% reutilización")
        
        if problematicos:
            print(f"   • {len(problematicos)} productos problematicos requieren atencion")
        else:
            print(f"   • No hay productos problematicos")
        
        return True
        
    except Exception as e:
        print(f"ERROR en auditoría: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    auditoria_completa()