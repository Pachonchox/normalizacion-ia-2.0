#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUDITORIA SIMPLE DE BASE DE DATOS
Version simplificada y robusta para auditoría rápida
"""

import psycopg2
import json
from datetime import datetime

def audit_database():
    """Realizar auditoría completa de la base de datos"""
    
    print("=== AUDITORIA COMPLETA BASE DE DATOS ===")
    print("=" * 50)
    
    # Conectar
    conn = psycopg2.connect(
        host="34.176.197.136",
        port=5432,
        database="postgres",
        user="postgres",
        password="Osmar2503!"
    )
    
    audit_results = {}
    
    try:
        cursor = conn.cursor()
        
        # 1. ESQUEMA Y TABLAS
        print("\\n1. ESTRUCTURA DE ESQUEMA")
        cursor.execute("""
            SELECT table_name, 
                   pg_size_pretty(pg_total_relation_size('public.'||table_name)) as size
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY pg_total_relation_size('public.'||table_name) DESC
        """)
        
        tables = cursor.fetchall()
        print(f"Total tablas: {len(tables)}")
        print("Top 10 por tamaño:")
        for table in tables[:10]:
            print(f"  - {table[0]}: {table[1]}")
        
        # 2. DATOS PRINCIPALES
        print("\\n2. ESTADISTICAS DE DATOS")
        
        # Productos maestros
        cursor.execute("SELECT COUNT(*) FROM productos_maestros WHERE active = true")
        productos_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM precios_actuales")
        precios_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ai_metadata_cache")
        cache_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM retailers WHERE active = true")
        retailers_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM categories WHERE active = true")
        categories_count = cursor.fetchone()[0]
        
        print(f"Productos maestros: {productos_count}")
        print(f"Precios actuales: {precios_count}")
        print(f"Cache IA: {cache_count}")
        print(f"Retailers activos: {retailers_count}")
        print(f"Categorias activas: {categories_count}")
        
        # 3. CALIDAD DE DATOS
        print("\\n3. CALIDAD DE DATOS")
        
        # Productos con IA
        cursor.execute("SELECT COUNT(*) FROM productos_maestros WHERE ai_enhanced = true AND active = true")
        ai_enhanced = cursor.fetchone()[0]
        ai_percentage = (ai_enhanced / productos_count * 100) if productos_count > 0 else 0
        
        print(f"Productos con IA: {ai_enhanced}/{productos_count} ({ai_percentage:.1f}%)")
        
        # Confianza promedio IA
        cursor.execute("SELECT AVG(ai_confidence) FROM productos_maestros WHERE ai_enhanced = true AND active = true")
        avg_confidence = cursor.fetchone()[0]
        print(f"Confianza IA promedio: {avg_confidence:.3f}")
        
        # Marcas desconocidas
        cursor.execute("SELECT COUNT(*) FROM productos_maestros WHERE brand = 'DESCONOCIDA' AND active = true")
        unknown_brands = cursor.fetchone()[0]
        print(f"Marcas desconocidas: {unknown_brands}")
        
        # 4. DISTRIBUCION POR CATEGORIA
        print("\\n4. DISTRIBUCION POR CATEGORIA")
        cursor.execute("""
            SELECT category, COUNT(*) as count,
                   ROUND(COUNT(*)::numeric * 100 / SUM(COUNT(*)) OVER(), 1) as percentage
            FROM productos_maestros 
            WHERE active = true
            GROUP BY category 
            ORDER BY count DESC
        """)
        
        categories = cursor.fetchall()
        for cat in categories:
            print(f"  - {cat[0]}: {cat[1]} productos ({cat[2]}%)")
        
        # 5. TOP MARCAS
        print("\\n5. TOP 10 MARCAS")
        cursor.execute("""
            SELECT brand, COUNT(*) as count
            FROM productos_maestros 
            WHERE active = true
            GROUP BY brand 
            ORDER BY count DESC
            LIMIT 10
        """)
        
        brands = cursor.fetchall()
        for brand in brands:
            print(f"  - {brand[0]}: {brand[1]} productos")
        
        # 6. INTEGRIDAD DE DATOS
        print("\\n6. VERIFICACIONES DE INTEGRIDAD")
        issues = []
        
        # Precios huérfanos
        cursor.execute("""
            SELECT COUNT(*) FROM precios_actuales pa
            LEFT JOIN productos_maestros pm ON pa.fingerprint = pm.fingerprint
            WHERE pm.fingerprint IS NULL
        """)
        orphaned = cursor.fetchone()[0]
        if orphaned > 0:
            issues.append(f"Precios huerfanos: {orphaned}")
        
        # Productos sin precios
        cursor.execute("""
            SELECT COUNT(*) FROM productos_maestros pm
            LEFT JOIN precios_actuales pa ON pm.fingerprint = pa.fingerprint
            WHERE pa.fingerprint IS NULL AND pm.active = true
        """)
        no_prices = cursor.fetchone()[0]
        if no_prices > 0:
            issues.append(f"Productos sin precios: {no_prices}")
        
        # Duplicados
        cursor.execute("""
            SELECT COUNT(*) FROM (
                SELECT fingerprint FROM productos_maestros 
                WHERE active = true
                GROUP BY fingerprint 
                HAVING COUNT(*) > 1
            ) duplicates
        """)
        duplicates = cursor.fetchone()[0]
        if duplicates > 0:
            issues.append(f"Fingerprints duplicados: {duplicates}")
        
        if issues:
            print("PROBLEMAS ENCONTRADOS:")
            for issue in issues:
                print(f"  WARNING: {issue}")
        else:
            print("OK: No se encontraron problemas de integridad")
        
        # 7. ACTIVIDAD RECIENTE
        print("\\n7. ACTIVIDAD RECIENTE (24h)")
        cursor.execute("""
            SELECT COUNT(*) FROM processing_logs 
            WHERE created_at > NOW() - INTERVAL '24 hours'
        """)
        recent_logs = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM productos_maestros 
            WHERE updated_at > NOW() - INTERVAL '24 hours'
        """)
        recent_updates = cursor.fetchone()[0]
        
        print(f"Logs de procesamiento: {recent_logs}")
        print(f"Productos actualizados: {recent_updates}")
        
        # 8. CACHE IA EFECTIVIDAD
        print("\\n8. EFECTIVIDAD CACHE IA")
        cursor.execute("SELECT AVG(hits) FROM ai_metadata_cache WHERE hits > 0")
        avg_hits = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ai_metadata_cache WHERE hits = 0")
        unused_cache = cursor.fetchone()[0]
        
        print(f"Hits promedio: {avg_hits:.1f}" if avg_hits else "Hits promedio: 0")
        print(f"Entradas sin usar: {unused_cache}")
        
        # RESUMEN FINAL
        print("\\n" + "="*50)
        print("RESUMEN DE AUDITORIA")
        print("="*50)
        
        # Calcular score de salud
        health_score = 100
        if issues:
            health_score -= len(issues) * 10
        if ai_percentage < 90:
            health_score -= 10
        if avg_confidence and avg_confidence < 0.8:
            health_score -= 10
        
        print(f"PUNTUACION DE SALUD: {health_score}%")
        
        if health_score >= 90:
            print("ESTADO: EXCELENTE - Sistema funcionando óptimamente")
        elif health_score >= 80:
            print("ESTADO: BUENO - Funcionamiento normal con mejoras menores")
        elif health_score >= 70:
            print("ESTADO: ACEPTABLE - Requiere atención a algunos problemas")
        else:
            print("ESTADO: PROBLEMATICO - Requiere atención inmediata")
        
        # Datos para reporte
        report = {
            'timestamp': datetime.now().isoformat(),
            'health_score': health_score,
            'stats': {
                'productos_maestros': productos_count,
                'precios_actuales': precios_count,
                'cache_ia': cache_count,
                'retailers': retailers_count,
                'categorias': categories_count,
                'ai_enhanced_pct': ai_percentage,
                'avg_confidence': float(avg_confidence) if avg_confidence else 0
            },
            'issues': issues,
            'recent_activity': {
                'logs_24h': recent_logs,
                'updates_24h': recent_updates
            }
        }
        
        # Guardar reporte
        with open('../out/audit_simple_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\\nReporte guardado en: out/audit_simple_report.json")
        
    except Exception as e:
        print(f"ERROR: Error durante auditoria: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    audit_database()