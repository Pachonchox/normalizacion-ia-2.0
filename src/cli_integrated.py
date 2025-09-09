#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 CLI Integrado con Base de Datos
Sistema completo que usa BD para todo el pipeline E2E
"""

import argparse
import json
import os
import time
from typing import Dict, Any, List

try:
    from .ingest import load_items
    from .categorize_db import load_taxonomy
    from .normalize_integrated import normalize_one_integrated, normalize_batch_integrated
    from .persistence import write_jsonl
    from .metrics import Metrics
    from .match import load_normalized, do_match
    from .db_persistence import get_persistence_instance
except ImportError:
    from ingest import load_items
    from categorize_db import load_taxonomy
    from normalize_integrated import normalize_one_integrated, normalize_batch_integrated
    from persistence import write_jsonl
    from metrics import Metrics
    from match import load_normalized, do_match
    from db_persistence import get_persistence_instance

def cmd_normalize_integrated(args):
    """Normalización integrada con BD completa"""
    
    print(f"=== NORMALIZACION INTEGRADA E2E ===")
    print(f"Input: {args.input}")
    print(f"Output: {args.out}")
    print(f"Base de datos: ACTIVA")
    
    metrics = Metrics()
    start_time = time.time()
    
    # Cargar taxonomía (automáticamente desde BD)
    taxonomy = load_taxonomy(args.taxonomy)
    print(f"Taxonomía cargada desde: {taxonomy.get('source', 'unknown')}")
    
    # Cargar items crudos
    items = []
    for rec in load_items(args.input):
        items.append(rec)
        metrics.inc("loaded")
    
    print(f"Productos cargados: {len(items)}")
    
    if not items:
        print("WARNING: No se encontraron productos para procesar")
        return
    
    # Normalizar en lote usando BD
    print(f"\\nIniciando normalizacion con BD...")
    out_rows = normalize_batch_integrated(items)
    
    # Guardar JSONL para compatibilidad
    n = write_jsonl(out_rows, os.path.join(args.out, "normalized_products.jsonl"))
    metrics.dump(args.out)
    
    # Estadísticas de BD
    try:
        persistence = get_persistence_instance()
        stats = persistence.get_processing_stats()
        
        print(f"\\n=== ESTADÍSTICAS BASE DE DATOS ===")
        print(f"Productos en BD: {stats.get('productos_maestros', 0)}")
        print(f"Precios en BD: {stats.get('precios_actuales', 0)}")
        print(f"Productos IA: {stats.get('productos_ai_enhanced', 0)}")
        print(f"Retailers: {stats.get('retailers_activos', 0)}")
        
    except Exception as e:
        print(f"Error obteniendo estadísticas BD: {e}")
    
    elapsed = time.time() - start_time
    print(f"\\nCOMPLETADO")
    print(f"Productos procesados: {len(out_rows)}")
    print(f"Archivo JSONL: {os.path.join(args.out, 'normalized_products.jsonl')}")
    print(f"Tiempo total: {elapsed:.1f}s")

def cmd_stats_db(args):
    """Mostrar estadísticas de la base de datos"""
    
    print(f"=== ESTADÍSTICAS BASE DE DATOS ===")
    
    try:
        persistence = get_persistence_instance()
        stats = persistence.get_processing_stats()
        
        print(f"RESUMEN GENERAL:")
        print(f"  - Productos maestros: {stats.get('productos_maestros', 0)}")
        print(f"  - Precios actuales: {stats.get('precios_actuales', 0)}")
        print(f"  - Productos con IA: {stats.get('productos_ai_enhanced', 0)}")
        print(f"  - Retailers activos: {stats.get('retailers_activos', 0)}")
        print(f"  - Categorias: {stats.get('categorias', 0)}")
        print(f"  - Logs (24h): {stats.get('logs_24h', 0)}")
        
        # Detalles adicionales
        from simple_db_connector import SimplePostgreSQLConnector
        connector = SimplePostgreSQLConnector(
            host="34.176.197.136", port=5432, database="postgres",
            user="postgres", password="Osmar2503!", pool_size=3
        )
        
        with connector.get_connection() as conn:
            with conn.cursor() as cursor:
                # Top categorías
                cursor.execute("""
                    SELECT category, COUNT(*) as count 
                    FROM productos_maestros 
                    WHERE active = true 
                    GROUP BY category 
                    ORDER BY count DESC 
                    LIMIT 5
                """)
                top_categories = cursor.fetchall()
                
                print(f"\\nTOP CATEGORIAS:")
                for cat, count in top_categories:
                    print(f"  - {cat}: {count} productos")
                
                # Top marcas
                cursor.execute("""
                    SELECT brand, COUNT(*) as count 
                    FROM productos_maestros 
                    WHERE active = true 
                    GROUP BY brand 
                    ORDER BY count DESC 
                    LIMIT 5
                """)
                top_brands = cursor.fetchall()
                
                print(f"\\nTOP MARCAS:")
                for brand, count in top_brands:
                    print(f"  - {brand}: {count} productos")
                
                # Últimas actualizaciones
                cursor.execute("""
                    SELECT name, updated_at 
                    FROM productos_maestros 
                    WHERE active = true 
                    ORDER BY updated_at DESC 
                    LIMIT 3
                """)
                recent = cursor.fetchall()
                
                print(f"\\nULTIMAS ACTUALIZACIONES:")
                for name, updated in recent:
                    print(f"  - {name[:40]}... ({updated})")
                
    except Exception as e:
        print(f"ERROR obteniendo estadisticas: {e}")

def cmd_clean_test_data(args):
    """Limpiar datos de prueba de la BD"""
    
    print(f"=== LIMPIEZA DE DATOS DE PRUEBA ===")
    
    try:
        from simple_db_connector import SimplePostgreSQLConnector
        connector = SimplePostgreSQLConnector(
            host="34.176.197.136", port=5432, database="postgres",
            user="postgres", password="Osmar2503!", pool_size=3
        )
        
        with connector.get_connection() as conn:
            with conn.cursor() as cursor:
                # Eliminar productos de prueba
                cursor.execute("DELETE FROM precios_actuales WHERE fingerprint LIKE 'test_%'")
                deleted_prices = cursor.rowcount
                
                cursor.execute("DELETE FROM productos_maestros WHERE fingerprint LIKE 'test_%'")
                deleted_products = cursor.rowcount
                
                # Eliminar retailer de prueba
                cursor.execute("DELETE FROM retailers WHERE name = 'Test Store'")
                deleted_retailers = cursor.rowcount
                
                conn.commit()
                
                print(f"OK: Limpieza completada:")
                print(f"  - Productos eliminados: {deleted_products}")
                print(f"  - Precios eliminados: {deleted_prices}")
                print(f"  - Retailers eliminados: {deleted_retailers}")
                
    except Exception as e:
        print(f"ERROR en limpieza: {e}")

def main():
    ap = argparse.ArgumentParser(prog="retail-normalizer-integrated")
    sub = ap.add_subparsers(dest="cmd", required=True)

    # Comando normalize integrado
    ap_norm = sub.add_parser("normalize", help="Normalización integrada con BD")
    ap_norm.add_argument("--input", required=True, help="Directorio con .json crudos")
    ap_norm.add_argument("--out", required=True, help="Directorio de salida")
    ap_norm.add_argument("--taxonomy", default="../configs/taxonomy_v1.json")
    ap_norm.set_defaults(func=cmd_normalize_integrated)

    # Comando estadísticas BD
    ap_stats = sub.add_parser("stats", help="Estadísticas de base de datos")
    ap_stats.set_defaults(func=cmd_stats_db)

    # Comando limpieza
    ap_clean = sub.add_parser("clean", help="Limpiar datos de prueba")
    ap_clean.set_defaults(func=cmd_clean_test_data)

    # Mantener compatibilidad con comandos originales
    ap_match = sub.add_parser("match", help="Matching inter-retail")
    ap_match.add_argument("--normalized", required=True)
    ap_match.add_argument("--out", required=True)
    ap_match.add_argument("--sim", type=float, default=0.86)
    ap_match.add_argument("--max-cands", type=int, default=50)
    ap_match.set_defaults(func=cmd_match_original)

    args = ap.parse_args()
    args.func(args)

def cmd_match_original(args):
    """Matching original (para compatibilidad)"""
    from match import load_normalized, do_match
    from persistence import write_jsonl
    
    rows = load_normalized(args.normalized)
    pairs = do_match(rows, threshold=args.sim, max_cands=args.max_cands)
    outp = os.path.join(args.out, "matches.jsonl")
    write_jsonl(pairs, outp)
    print(f"[OK] Matches: {len(pairs)} -> {outp}")

if __name__ == "__main__":
    main()