#!/usr/bin/env python3
"""
📸 Generador de snapshot completo simplificado
Para los 20 productos procesados, sin tabla categorías
"""
import json
import os
import sys
import io
from datetime import datetime
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Configurar encoding UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Cargar variables de entorno
load_dotenv()

def get_db_connection():
    """Obtener conexión a la base de datos"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', 5432),
        database=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        cursor_factory=RealDictCursor
    )

def generate_complete_snapshot():
    """Generar snapshot completo del estado actual"""
    
    snapshot = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "environment": {
                "db_host": os.getenv('DB_HOST'),
                "db_name": os.getenv('DB_NAME'),
                "llm_enabled": os.getenv('LLM_ENABLED', 'true'),
                "openai_model": os.getenv('OPENAI_MODEL', 'gpt-5-mini')
            }
        },
        "productos_maestros": [],
        "precios_actuales": [],
        "cache": {},
        "archivos_procesados": {},
        "summary": {}
    }
    
    try:
        # Conectar a BD
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Obtener los últimos 20 productos maestros
        print("📊 Obteniendo productos maestros de la BD...")
        cur.execute("""
            SELECT 
                id,
                product_id,
                name,
                brand,
                model,
                category,
                attributes,
                ai_enhanced,
                ai_confidence,
                processing_version,
                fingerprint,
                active,
                created_at::text,
                updated_at::text
            FROM productos_maestros
            ORDER BY created_at DESC
            LIMIT 20
        """)
        productos = cur.fetchall()
        snapshot["productos_maestros"] = [dict(p) for p in productos]
        
        # 2. Obtener precios actuales para estos productos
        print("💰 Obteniendo precios actuales...")
        producto_ids = [p['product_id'] for p in productos]
        if producto_ids:
            cur.execute("""
                SELECT 
                    pa.product_id,
                    pa.retailer_id,
                    pa.precio_normal,
                    pa.precio_tarjeta,
                    pa.precio_oferta,
                    pa.currency,
                    pa.stock_status,
                    pa.url,
                    pa.ultima_actualizacion::text,
                    pm.name as producto_nombre,
                    pm.brand
                FROM precios_actuales pa
                JOIN productos_maestros pm ON pa.product_id = pm.product_id
                WHERE pa.product_id = ANY(%s)
                ORDER BY pa.ultima_actualizacion DESC
            """, (producto_ids,))
            precios = cur.fetchall()
            snapshot["precios_actuales"] = [dict(p) for p in precios]
        
        # 3. Estadísticas generales de hoy
        print("📈 Calculando estadísticas...")
        cur.execute("""
            SELECT 
                COUNT(DISTINCT id) as total_productos,
                COUNT(DISTINCT brand) as total_marcas,
                COUNT(DISTINCT category) as total_categorias,
                COUNT(DISTINCT CASE WHEN ai_enhanced = true THEN id END) as productos_con_ia,
                AVG(ai_confidence) as confianza_promedio,
                MIN(created_at) as primera_carga,
                MAX(updated_at) as ultima_actualizacion
            FROM productos_maestros
            WHERE DATE(created_at) = CURRENT_DATE
        """)
        stats = cur.fetchone()
        snapshot["summary"]["database_stats_today"] = dict(stats) if stats else {}
        
        # 4. Estadísticas totales
        cur.execute("""
            SELECT 
                COUNT(DISTINCT id) as total_productos,
                COUNT(DISTINCT brand) as total_marcas,
                COUNT(DISTINCT category) as total_categorias
            FROM productos_maestros
        """)
        stats_total = cur.fetchone()
        snapshot["summary"]["database_stats_total"] = dict(stats_total) if stats_total else {}
        
        # 5. Distribución por categoría
        cur.execute("""
            SELECT 
                category,
                COUNT(*) as cantidad
            FROM productos_maestros
            WHERE product_id = ANY(%s)
            GROUP BY category
            ORDER BY cantidad DESC
        """, (producto_ids if producto_ids else [''],))
        categorias = cur.fetchall()
        snapshot["summary"]["categorias"] = {c['category']: c['cantidad'] for c in categorias}
        
        # 6. Distribución por retailer
        cur.execute("""
            SELECT 
                retailer_id,
                COUNT(*) as cantidad,
                AVG(precio_normal) as precio_promedio
            FROM precios_actuales
            WHERE product_id = ANY(%s)
            GROUP BY retailer_id
            ORDER BY cantidad DESC
        """, (producto_ids if producto_ids else [''],))
        retailers = cur.fetchall()
        snapshot["summary"]["retailers"] = [dict(r) for r in retailers]
        
        # 7. Leer cache si existe
        print("💾 Leyendo cache...")
        cache_file = "ai_cache_products.json"
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                # Manejar si el cache es dict o list
                if isinstance(cache_data, dict):
                    snapshot["cache"]["total_entries"] = len(cache_data)
                    snapshot["cache"]["sample_entries"] = dict(list(cache_data.items())[-5:])
                elif isinstance(cache_data, list):
                    snapshot["cache"]["total_entries"] = len(cache_data)
                    snapshot["cache"]["sample_entries"] = cache_data[-5:] if len(cache_data) > 0 else []
        
        # 8. Leer archivos procesados
        archivos_json = [
            "test_20_productos_reales_20250910_175730.json",
            "productos_normalizados_20250910_175756.json"
        ]
        
        for archivo in archivos_json:
            try:
                if os.path.exists(archivo):
                    file_stats = os.stat(archivo)
                    snapshot["archivos_procesados"][archivo] = {
                        "size_bytes": file_stats.st_size,
                        "modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                    }
                    
                    # Leer contenido si es pequeño
                    if file_stats.st_size < 100000:  # < 100KB
                        with open(archivo, 'r', encoding='utf-8') as f:
                            try:
                                data = json.load(f)
                                if isinstance(data, list):
                                    snapshot["archivos_procesados"][archivo]["productos_count"] = len(data)
                                    snapshot["archivos_procesados"][archivo]["sample"] = data[:2] if len(data) > 0 else []
                            except:
                                pass
            except PermissionError:
                snapshot["archivos_procesados"][archivo] = {"error": "Permission denied"}
            except Exception as e:
                snapshot["archivos_procesados"][archivo] = {"error": str(e)}
        
        # 9. Resumen final
        snapshot["summary"]["totals"] = {
            "productos_en_snapshot": len(snapshot["productos_maestros"]),
            "precios_registrados": len(snapshot["precios_actuales"]),
            "categorias_distintas": len(snapshot["summary"].get("categorias", {})),
            "retailers_activos": len(snapshot["summary"].get("retailers", [])),
            "archivos_procesados": len(snapshot["archivos_procesados"]),
            "entradas_cache_total": snapshot["cache"].get("total_entries", 0)
        }
        
        # Cerrar conexión
        cur.close()
        conn.close()
        
        # Guardar snapshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"SNAPSHOT_COMPLETO_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n✅ Snapshot completo generado: {output_file}")
        print(f"\n📊 RESUMEN DEL SNAPSHOT:")
        print(f"   ══════════════════════════════════════")
        print(f"   📦 Productos en snapshot: {snapshot['summary']['totals']['productos_en_snapshot']}")
        print(f"   💰 Precios registrados: {snapshot['summary']['totals']['precios_registrados']}")
        print(f"   📁 Categorías distintas: {snapshot['summary']['totals']['categorias_distintas']}")
        print(f"   🏪 Retailers activos: {snapshot['summary']['totals']['retailers_activos']}")
        print(f"   📄 Archivos procesados: {snapshot['summary']['totals']['archivos_procesados']}")
        print(f"   💾 Cache entries totales: {snapshot['summary']['totals']['entradas_cache_total']}")
        
        if snapshot["summary"].get("database_stats_today"):
            stats = snapshot["summary"]["database_stats_today"]
            print(f"\n   📈 ESTADÍSTICAS DE HOY:")
            print(f"   ────────────────────────")
            print(f"   • Total productos: {stats.get('total_productos', 0)}")
            print(f"   • Total marcas: {stats.get('total_marcas', 0)}")
            print(f"   • Productos con IA: {stats.get('productos_con_ia', 0)}")
            print(f"   • Confianza promedio IA: {stats.get('confianza_promedio', 0):.2f}" if stats.get('confianza_promedio') else "   • Confianza promedio: N/A")
        
        if snapshot["summary"].get("categorias"):
            print(f"\n   📊 DISTRIBUCIÓN POR CATEGORÍA:")
            print(f"   ─────────────────────────────")
            for cat, count in snapshot["summary"]["categorias"].items():
                print(f"   • {cat}: {count} productos")
        
        if snapshot["summary"].get("retailers"):
            print(f"\n   🏪 DISTRIBUCIÓN POR RETAILER:")
            print(f"   ────────────────────────────")
            for r in snapshot["summary"]["retailers"]:
                precio_prom = f"${r['precio_promedio']:,.0f}" if r.get('precio_promedio') else "N/A"
                print(f"   • Retailer {r['retailer_id']}: {r['cantidad']} precios (prom: {precio_prom})")
        
        print(f"\n   ══════════════════════════════════════")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Error generando snapshot: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    archivo = generate_complete_snapshot()
    if archivo:
        print(f"\n🎉 SNAPSHOT COMPLETO DISPONIBLE EN: {archivo}")
        print(f"📂 Tamaño del archivo: {os.path.getsize(archivo):,} bytes")