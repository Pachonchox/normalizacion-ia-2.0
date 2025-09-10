#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUDIT: Auditor Completo de Base de Datos PostgreSQL
Sistema de auditoría para verificar integridad, consistencia y rendimiento
"""

import psycopg2
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from simple_db_connector import SimplePostgreSQLConnector

class DatabaseAuditor:
    """Auditor completo de base de datos"""
    
    def __init__(self):
        self.connector = SimplePostgreSQLConnector(
            host="34.176.197.136",
            port=5432,
            database="postgres",
            user="postgres",
            password="Osmar2503!",
            pool_size=3
        )
        self.audit_results = {}
    
    def audit_schema_integrity(self):
        """Auditar integridad del esquema"""
        print("=== AUDITORIA DE ESQUEMA ===")
        
        with self.connector.get_connection() as conn:
            with conn.cursor() as cursor:
                # Verificar todas las tablas esperadas
                expected_tables = [
                    'productos_maestros', 'precios_actuales', 'precios_historicos',
                    'ai_metadata_cache', 'categories', 'brands', 'retailers',
                    'attributes_schema', 'price_alerts', 'processing_logs', 'system_config'
                ]
                
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)
                
                existing_tables = [row[0] for row in cursor.fetchall()]
                
                print(f"Tablas esperadas: {len(expected_tables)}")
                print(f"Tablas encontradas: {len(existing_tables)}")
                
                missing_tables = set(expected_tables) - set(existing_tables)
                extra_tables = set(existing_tables) - set(expected_tables) - set([
                    t for t in existing_tables if t.startswith('precios_historicos_')
                ])
                
                if missing_tables:
                    print(f"WARNING: TABLAS FALTANTES: {missing_tables}")
                else:
                    print("OK: Todas las tablas principales estan presentes")
                
                if extra_tables:
                    print(f"INFO:  Tablas adicionales: {extra_tables}")
                
                # Verificar particiones de precios_historicos
                cursor.execute("""
                    SELECT schemaname, tablename FROM pg_tables 
                    WHERE tablename LIKE 'precios_historicos_%'
                    ORDER BY tablename
                """)
                
                partitions = cursor.fetchall()
                print(f"Particiones históricas: {len(partitions)}")
                for partition in partitions:
                    print(f"  - {partition[1]}")
                
                self.audit_results['schema'] = {
                    'missing_tables': list(missing_tables),
                    'extra_tables': list(extra_tables),
                    'partitions_count': len(partitions),
                    'status': 'OK' if not missing_tables else 'WARNING'
                }
    
    def audit_data_integrity(self):
        """Auditar integridad de datos"""
        print("\\n=== AUDITORIA DE INTEGRIDAD DE DATOS ===")
        
        with self.connector.get_connection() as conn:
            with conn.cursor() as cursor:
                issues = []
                
                # 1. Verificar orphaned records
                cursor.execute("""
                    SELECT COUNT(*) FROM precios_actuales pa
                    LEFT JOIN productos_maestros pm ON pa.fingerprint = pm.fingerprint
                    WHERE pm.fingerprint IS NULL
                """)
                orphaned_prices = cursor.fetchone()[0]
                
                if orphaned_prices > 0:
                    issues.append(f"Precios huérfanos (sin producto maestro): {orphaned_prices}")
                    print(f"WARNING:  Precios huérfanos: {orphaned_prices}")
                else:
                    print("OK: No hay precios huérfanos")
                
                # 2. Verificar productos sin precios
                cursor.execute("""
                    SELECT COUNT(*) FROM productos_maestros pm
                    LEFT JOIN precios_actuales pa ON pm.fingerprint = pa.fingerprint
                    WHERE pa.fingerprint IS NULL AND pm.active = true
                """)
                products_no_prices = cursor.fetchone()[0]
                
                if products_no_prices > 0:
                    issues.append(f"Productos activos sin precios: {products_no_prices}")
                    print(f"WARNING:  Productos sin precios: {products_no_prices}")
                else:
                    print("OK: Todos los productos activos tienen precios")
                
                # 3. Verificar retailers inválidos
                cursor.execute("""
                    SELECT COUNT(*) FROM precios_actuales pa
                    LEFT JOIN retailers r ON pa.retailer_id = r.id
                    WHERE r.id IS NULL
                """)
                invalid_retailers = cursor.fetchone()[0]
                
                if invalid_retailers > 0:
                    issues.append(f"Precios con retailer inválido: {invalid_retailers}")
                    print(f"WARNING:  Referencias retailer inválidas: {invalid_retailers}")
                else:
                    print("OK: Todas las referencias de retailer son válidas")
                
                # 4. Verificar categorías inválidas
                cursor.execute("""
                    SELECT COUNT(*) FROM productos_maestros pm
                    LEFT JOIN categories c ON pm.category = c.category_id
                    WHERE c.category_id IS NULL AND pm.active = true
                """)
                invalid_categories = cursor.fetchone()[0]
                
                if invalid_categories > 0:
                    issues.append(f"Productos con categoría inválida: {invalid_categories}")
                    print(f"WARNING:  Categorías inválidas: {invalid_categories}")
                else:
                    print("OK: Todas las categorías son válidas")
                
                # 5. Verificar duplicados por fingerprint
                cursor.execute("""
                    SELECT fingerprint, COUNT(*) 
                    FROM productos_maestros 
                    WHERE active = true
                    GROUP BY fingerprint 
                    HAVING COUNT(*) > 1
                """)
                duplicates = cursor.fetchall()
                
                if duplicates:
                    issues.append(f"Fingerprints duplicados: {len(duplicates)}")
                    print(f"WARNING:  Fingerprints duplicados: {len(duplicates)}")
                    for dup in duplicates[:5]:
                        print(f"    - {dup[0]}: {dup[1]} registros")
                else:
                    print("OK: No hay fingerprints duplicados")
                
                # 6. Verificar precios negativos o cero
                cursor.execute("""
                    SELECT COUNT(*) FROM precios_actuales 
                    WHERE precio_normal <= 0 OR precio_tarjeta <= 0
                """)
                invalid_prices = cursor.fetchone()[0]
                
                if invalid_prices > 0:
                    issues.append(f"Precios inválidos (<=0): {invalid_prices}")
                    print(f"WARNING:  Precios inválidos: {invalid_prices}")
                else:
                    print("OK: Todos los precios son válidos")
                
                self.audit_results['data_integrity'] = {
                    'issues': issues,
                    'status': 'OK' if not issues else 'WARNING'
                }
    
    def audit_performance(self):
        """Auditar rendimiento de la base de datos"""
        print("\\n=== AUDITORIA DE RENDIMIENTO ===")
        
        try:
            with self.connector.get_connection() as conn:
                with conn.cursor() as cursor:
                # 1. Tamaños de tablas
                cursor.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                    LIMIT 10
                """)
                
                table_sizes = cursor.fetchall()
                print("Top 10 tablas por tamaño:")
                for table in table_sizes:
                    print(f"  - {table[1]}: {table[2]}")
                
                # 2. Estadísticas de consultas (si pg_stat_statements está habilitado)
                print("\\nINFO: Saltando estadisticas de consultas (requiere configuracion especial)")
                
                # 3. Estadísticas de índices
                cursor.execute("""
                    SELECT 
                        indexname,
                        tablename,
                        idx_scan as index_scans,
                        idx_tup_read as tuples_read,
                        idx_tup_fetch as tuples_fetched
                    FROM pg_stat_user_indexes 
                    WHERE schemaname = 'public'
                    ORDER BY idx_scan DESC
                    LIMIT 10
                """)
                
                index_stats = cursor.fetchall()
                print("\\nÍndices más utilizados:")
                for idx in index_stats:
                    print(f"  - {idx[0]} ({idx[1]}): {idx[2]} scans")
                
                # 4. Conexiones activas
                cursor.execute("""
                    SELECT state, COUNT(*) 
                    FROM pg_stat_activity 
                    WHERE datname = current_database()
                    GROUP BY state
                """)
                
                connections = cursor.fetchall()
                print("\\nConexiones por estado:")
                for conn_stat in connections:
                    print(f"  - {conn_stat[0] or 'NULL'}: {conn_stat[1]}")
                
                    self.audit_results['performance'] = {
                        'largest_tables': [{'name': t[1], 'size': t[2]} for t in table_sizes[:5]],
                        'total_tables': len(table_sizes),
                        'status': 'OK'
                    }
        except Exception as e:
            print(f"ERROR: Error en auditoria de rendimiento: {e}")
            self.audit_results['performance'] = {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def audit_data_quality(self):
        """Auditar calidad de datos"""
        print("\\n=== AUDITORIA DE CALIDAD DE DATOS ===")
        
        with self.connector.get_connection() as conn:
            with conn.cursor() as cursor:
                quality_issues = []
                
                # 1. Productos con nombres vacíos o muy cortos
                cursor.execute("""
                    SELECT COUNT(*) FROM productos_maestros 
                    WHERE active = true AND (name IS NULL OR LENGTH(name) < 5)
                """)
                empty_names = cursor.fetchone()[0]
                
                if empty_names > 0:
                    quality_issues.append(f"Productos con nombres vacíos/cortos: {empty_names}")
                    print(f"WARNING:  Nombres vacíos/cortos: {empty_names}")
                else:
                    print("OK: Todos los productos tienen nombres válidos")
                
                # 2. Marcas desconocidas
                cursor.execute("""
                    SELECT COUNT(*) FROM productos_maestros 
                    WHERE active = true AND (brand IS NULL OR brand = 'DESCONOCIDA')
                """)
                unknown_brands = cursor.fetchone()[0]
                
                if unknown_brands > 0:
                    quality_issues.append(f"Productos con marca desconocida: {unknown_brands}")
                    print(f"WARNING:  Marcas desconocidas: {unknown_brands}")
                else:
                    print("OK: Todas las marcas están identificadas")
                
                # 3. Productos sin atributos
                cursor.execute("""
                    SELECT COUNT(*) FROM productos_maestros 
                    WHERE active = true AND (attributes IS NULL OR attributes = '{}')
                """)
                no_attributes = cursor.fetchone()[0]
                
                if no_attributes > 0:
                    quality_issues.append(f"Productos sin atributos: {no_attributes}")
                    print(f"WARNING:  Sin atributos: {no_attributes}")
                else:
                    print("OK: Todos los productos tienen atributos")
                
                # 4. Productos sin enriquecimiento IA
                cursor.execute("""
                    SELECT COUNT(*) FROM productos_maestros 
                    WHERE active = true AND ai_enhanced = false
                """)
                no_ai = cursor.fetchone()[0]
                
                if no_ai > 0:
                    quality_issues.append(f"Productos sin IA: {no_ai}")
                    print(f"WARNING:  Sin enriquecimiento IA: {no_ai}")
                else:
                    print("OK: Todos los productos tienen enriquecimiento IA")
                
                # 5. Confianza IA baja
                cursor.execute("""
                    SELECT COUNT(*) FROM productos_maestros 
                    WHERE active = true AND ai_confidence < 0.8
                """)
                low_confidence = cursor.fetchone()[0]
                
                if low_confidence > 0:
                    quality_issues.append(f"Productos con confianza IA baja: {low_confidence}")
                    print(f"WARNING:  Confianza IA baja (<0.8): {low_confidence}")
                else:
                    print("OK: Alta confianza en enriquecimiento IA")
                
                # 6. Distribución por categorías
                cursor.execute("""
                    SELECT category, COUNT(*) as count,
                           ROUND(COUNT(*)::numeric * 100 / SUM(COUNT(*)) OVER(), 2) as percentage
                    FROM productos_maestros 
                    WHERE active = true
                    GROUP BY category 
                    ORDER BY count DESC
                """)
                
                category_dist = cursor.fetchall()
                print("\\nDistribución por categorías:")
                for cat in category_dist:
                    print(f"  - {cat[0]}: {cat[1]} productos ({cat[2]}%)")
                
                # 7. Distribución por retailers
                cursor.execute("""
                    SELECT r.name, COUNT(*) as count,
                           ROUND(COUNT(*)::numeric * 100 / SUM(COUNT(*)) OVER(), 2) as percentage
                    FROM precios_actuales pa
                    JOIN retailers r ON pa.retailer_id = r.id
                    GROUP BY r.name 
                    ORDER BY count DESC
                """)
                
                retailer_dist = cursor.fetchall()
                print("\\nDistribución por retailers:")
                for ret in retailer_dist:
                    print(f"  - {ret[0]}: {ret[1]} productos ({ret[2]}%)")
                
                self.audit_results['data_quality'] = {
                    'issues': quality_issues,
                    'category_distribution': dict([(cat[0], cat[1]) for cat in category_dist]),
                    'retailer_distribution': dict([(ret[0], ret[1]) for ret in retailer_dist]),
                    'status': 'OK' if len(quality_issues) <= 2 else 'WARNING'
                }
    
    def audit_cache_effectiveness(self):
        """Auditar efectividad del cache IA"""
        print("\\n=== AUDITORIA DE CACHE IA ===")
        
        with self.connector.get_connection() as conn:
            with conn.cursor() as cursor:
                # 1. Estadísticas generales del cache
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_entries,
                        AVG(confidence) as avg_confidence,
                        AVG(hits) as avg_hits,
                        MAX(hits) as max_hits,
                        COUNT(*) FILTER (WHERE hits > 0) as used_entries
                    FROM ai_metadata_cache
                """)
                
                cache_stats = cursor.fetchone()
                print(f"Entradas totales en cache: {cache_stats[0]}")
                print(f"Confianza promedio: {cache_stats[1]:.3f}")
                print(f"Hits promedio: {cache_stats[2]:.1f}")
                print(f"Máximo hits: {cache_stats[3]}")
                print(f"Entradas utilizadas: {cache_stats[4]} ({cache_stats[4]/cache_stats[0]*100:.1f}%)")
                
                # 2. Cache más utilizado
                cursor.execute("""
                    SELECT fingerprint, brand, model, hits, confidence
                    FROM ai_metadata_cache 
                    ORDER BY hits DESC 
                    LIMIT 10
                """)
                
                top_cache = cursor.fetchall()
                print("\\nCache más utilizado:")
                for cache in top_cache:
                    print(f"  - {cache[1]} {cache[2]}: {cache[3]} hits (conf: {cache[4]:.2f})")
                
                # 3. Cache con baja confianza
                cursor.execute("""
                    SELECT COUNT(*) FROM ai_metadata_cache 
                    WHERE confidence < 0.8
                """)
                
                low_conf_cache = cursor.fetchone()[0]
                if low_conf_cache > 0:
                    print(f"WARNING:  Entradas cache con confianza baja: {low_conf_cache}")
                else:
                    print("OK: Todo el cache tiene alta confianza")
                
                # 4. Eficiencia del cache (productos con cache vs sin cache)
                cursor.execute("""
                    SELECT 
                        COUNT(*) FILTER (WHERE pm.fingerprint IS NOT NULL) as with_cache,
                        COUNT(*) FILTER (WHERE pm.fingerprint IS NULL) as without_cache
                    FROM productos_maestros pm
                    LEFT JOIN ai_metadata_cache aic ON pm.fingerprint = aic.fingerprint
                    WHERE pm.active = true
                """)
                
                cache_efficiency = cursor.fetchone()
                total_products = cache_efficiency[0] + cache_efficiency[1]
                efficiency_pct = (cache_efficiency[0] / total_products * 100) if total_products > 0 else 0
                
                print(f"\\nEficiencia del cache:")
                print(f"  - Con cache: {cache_efficiency[0]} productos")
                print(f"  - Sin cache: {cache_efficiency[1]} productos")
                print(f"  - Eficiencia: {efficiency_pct:.1f}%")
                
                self.audit_results['cache'] = {
                    'total_entries': cache_stats[0],
                    'avg_confidence': float(cache_stats[1]) if cache_stats[1] else 0,
                    'efficiency_pct': efficiency_pct,
                    'low_confidence_entries': low_conf_cache,
                    'status': 'OK' if efficiency_pct > 90 and low_conf_cache == 0 else 'WARNING'
                }
    
    def audit_recent_activity(self):
        """Auditar actividad reciente"""
        print("\\n=== AUDITORIA DE ACTIVIDAD RECIENTE ===")
        
        with self.connector.get_connection() as conn:
            with conn.cursor() as cursor:
                # 1. Actividad en últimas 24 horas
                cursor.execute("""
                    SELECT 
                        DATE_TRUNC('hour', created_at) as hour,
                        COUNT(*) as operations
                    FROM processing_logs 
                    WHERE created_at > NOW() - INTERVAL '24 hours'
                    GROUP BY DATE_TRUNC('hour', created_at)
                    ORDER BY hour DESC
                    LIMIT 24
                """)
                
                hourly_activity = cursor.fetchall()
                print("Actividad por hora (últimas 24h):")
                for hour, ops in hourly_activity:
                    print(f"  - {hour}: {ops} operaciones")
                
                # 2. Productos actualizados recientemente
                cursor.execute("""
                    SELECT name, brand, updated_at
                    FROM productos_maestros 
                    WHERE updated_at > NOW() - INTERVAL '24 hours'
                    ORDER BY updated_at DESC
                    LIMIT 10
                """)
                
                recent_updates = cursor.fetchall()
                print("\\nProductos actualizados (últimas 24h):")
                for prod in recent_updates:
                    print(f"  - {prod[1]} {prod[0][:30]}... ({prod[2]})")
                
                # 3. Errores recientes
                cursor.execute("""
                    SELECT operation, error_message, created_at
                    FROM processing_logs 
                    WHERE status = 'error' AND created_at > NOW() - INTERVAL '24 hours'
                    ORDER BY created_at DESC
                    LIMIT 5
                """)
                
                recent_errors = cursor.fetchall()
                if recent_errors:
                    print("\\nWARNING:  Errores recientes:")
                    for error in recent_errors:
                        print(f"  - {error[0]}: {error[1]} ({error[2]})")
                else:
                    print("\\nOK: No hay errores recientes")
                
                self.audit_results['recent_activity'] = {
                    'operations_24h': sum([op[1] for op in hourly_activity]),
                    'updates_24h': len(recent_updates),
                    'errors_24h': len(recent_errors),
                    'status': 'OK' if len(recent_errors) == 0 else 'WARNING'
                }
    
    def generate_audit_report(self):
        """Generar reporte final de auditoría"""
        print("\\n" + "="*60)
        print("AUDIT: REPORTE FINAL DE AUDITORIA")
        print("="*60)
        
        # Calcular score general
        total_checks = len(self.audit_results)
        ok_checks = sum(1 for r in self.audit_results.values() if r.get('status') == 'OK')
        warning_checks = total_checks - ok_checks
        
        overall_score = (ok_checks / total_checks * 100) if total_checks > 0 else 0
        
        print(f"\\nPUNTUACION GENERAL: {overall_score:.1f}%")
        print(f"Checks exitosos: {ok_checks}/{total_checks}")
        if warning_checks > 0:
            print(f"WARNING:  Warnings: {warning_checks}")
        
        print("\\nRESUMEN POR CATEGORIA:")
        for category, result in self.audit_results.items():
            status_emoji = "OK:" if result.get('status') == 'OK' else "WARNING: "
            print(f"  {status_emoji} {category.upper()}: {result.get('status', 'UNKNOWN')}")
        
        # Recomendaciones
        print("\\nRECOMENDACIONES:")
        recommendations = []
        
        if self.audit_results.get('data_integrity', {}).get('issues'):
            recommendations.append("- Resolver problemas de integridad de datos")
        
        if self.audit_results.get('data_quality', {}).get('issues'):
            recommendations.append("- Mejorar calidad de datos (nombres, marcas, atributos)")
        
        if self.audit_results.get('cache', {}).get('efficiency_pct', 100) < 90:
            recommendations.append("- Optimizar eficiencia del cache IA")
        
        if self.audit_results.get('recent_activity', {}).get('errors_24h', 0) > 0:
            recommendations.append("- Investigar y resolver errores recientes")
        
        if not recommendations:
            print("  OK: No hay recomendaciones específicas. Sistema en buen estado.")
        else:
            for rec in recommendations:
                print(f"  {rec}")
        
        # Guardar reporte
        report = {
            'audit_timestamp': datetime.now().isoformat(),
            'overall_score': overall_score,
            'results': self.audit_results,
            'recommendations': recommendations
        }
        
        with open('../out/audit_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\\nREPORT: Reporte guardado en: out/audit_report.json")
        return report
    
    def run_full_audit(self):
        """Ejecutar auditoría completa"""
        print("INICIANDO AUDITORIA COMPLETA DE BASE DE DATOS")
        print("=" * 60)
        
        try:
            self.audit_schema_integrity()
            self.audit_data_integrity()
            self.audit_performance()
            self.audit_data_quality()
            self.audit_cache_effectiveness()
            self.audit_recent_activity()
            
            return self.generate_audit_report()
            
        except Exception as e:
            print(f"ERROR: ERROR durante auditoría: {e}")
            import traceback
            traceback.print_exc()
            return None

def main():
    """Función principal de auditoría"""
    auditor = DatabaseAuditor()
    report = auditor.run_full_audit()
    
    if report:
        print("\\nSUCCESS: AUDITORIA COMPLETADA EXITOSAMENTE")
    else:
        print("\\nERROR: AUDITORIA FALLÓ")

if __name__ == "__main__":
    main()