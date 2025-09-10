#!/usr/bin/env python3
"""
📸 Generador de snapshot completo de los 20 productos procesados
Incluye: BD, cache, métricas y estado final
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

def generate_snapshot():
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
        "categorias": [],
        "cache": {},
        "metrics": {},
        "summary": {}
    }
    
    try:
        # Conectar a BD
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Obtener productos maestros (últimos 20)
        print("📊 Obteniendo productos maestros de la BD...")
        cur.execute("""
            SELECT 
                pm.*,
                c.nombre as categoria_nombre,
                c.path as categoria_path
            FROM productos_maestros pm
            LEFT JOIN categorias c ON pm.categoria_id = c.id
            ORDER BY pm.created_at DESC
            LIMIT 20
        """)
        productos = cur.fetchall()
        snapshot["productos_maestros"] = [dict(p) for p in productos]
        
        # 2. Obtener precios actuales
        print("💰 Obteniendo precios actuales...")
        producto_ids = [p['id'] for p in productos]
        if producto_ids:
            cur.execute("""
                SELECT 
                    pa.*,
                    pm.nombre as producto_nombre,
                    pm.marca
                FROM precios_actuales pa
                JOIN productos_maestros pm ON pa.producto_id = pm.id
                WHERE pa.producto_id = ANY(%s)
                ORDER BY pa.fecha_actualizacion DESC
            """, (producto_ids,))
            precios = cur.fetchall()
            snapshot["precios_actuales"] = [dict(p) for p in precios]
        
        # 3. Obtener categorías usadas
        print("📁 Obteniendo categorías...")
        cur.execute("""
            SELECT DISTINCT
                c.*,
                COUNT(pm.id) as productos_count
            FROM categorias c
            LEFT JOIN productos_maestros pm ON c.id = pm.categoria_id
            WHERE pm.id = ANY(%s) OR c.nivel <= 2
            GROUP BY c.id, c.nombre, c.path, c.nivel, c.parent_id
            ORDER BY c.nivel, c.nombre
        """, (producto_ids if producto_ids else [0],))
        categorias = cur.fetchall()
        snapshot["categorias"] = [dict(c) for c in categorias]
        
        # 4. Estadísticas generales
        print("📈 Calculando estadísticas...")
        cur.execute("""
            SELECT 
                COUNT(DISTINCT id) as total_productos,
                COUNT(DISTINCT marca) as total_marcas,
                COUNT(DISTINCT categoria_id) as total_categorias,
                COUNT(DISTINCT CASE WHEN precio_min IS NOT NULL THEN id END) as productos_con_precio,
                AVG(precio_min) as precio_promedio,
                MIN(precio_min) as precio_minimo,
                MAX(precio_max) as precio_maximo,
                MIN(created_at) as primera_carga,
                MAX(created_at) as ultima_carga
            FROM productos_maestros
            WHERE created_at >= CURRENT_DATE
        """)
        stats = cur.fetchone()
        snapshot["summary"]["database_stats"] = dict(stats) if stats else {}
        
        # 5. Distribución por retailer
        cur.execute("""
            SELECT 
                retailer,
                COUNT(*) as cantidad
            FROM precios_actuales
            WHERE producto_id = ANY(%s)
            GROUP BY retailer
            ORDER BY cantidad DESC
        """, (producto_ids if producto_ids else [0],))
        retailers = cur.fetchall()
        snapshot["summary"]["retailers"] = {r['retailer']: r['cantidad'] for r in retailers}
        
        # 6. Leer cache si existe
        print("💾 Leyendo cache...")
        cache_file = "ai_cache_products.json"
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                # Tomar solo las últimas 20 entradas
                snapshot["cache"] = dict(list(cache_data.items())[-20:])
        
        # 7. Leer métricas si existen
        metrics_files = [
            "out/metrics.json",
            "out_test/metrics.json",
            "out_final_test/metrics.json"
        ]
        for mf in metrics_files:
            if os.path.exists(mf):
                with open(mf, 'r', encoding='utf-8') as f:
                    snapshot["metrics"][mf] = json.load(f)
        
        # 8. Resumen final
        snapshot["summary"]["totals"] = {
            "productos_en_snapshot": len(snapshot["productos_maestros"]),
            "precios_registrados": len(snapshot["precios_actuales"]),
            "categorias_usadas": len([c for c in snapshot["categorias"] if c.get('productos_count', 0) > 0]),
            "entradas_cache": len(snapshot["cache"]),
            "archivos_metricas": len(snapshot["metrics"])
        }
        
        # Cerrar conexión
        cur.close()
        conn.close()
        
        # Guardar snapshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"snapshot_20_productos_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n✅ Snapshot generado: {output_file}")
        print(f"📊 Resumen:")
        print(f"   - Productos maestros: {snapshot['summary']['totals']['productos_en_snapshot']}")
        print(f"   - Precios actuales: {snapshot['summary']['totals']['precios_registrados']}")
        print(f"   - Categorías: {snapshot['summary']['totals']['categorias_usadas']}")
        print(f"   - Cache entries: {snapshot['summary']['totals']['entradas_cache']}")
        
        if snapshot["summary"]["database_stats"]:
            stats = snapshot["summary"]["database_stats"]
            print(f"\n📈 Estadísticas BD (hoy):")
            print(f"   - Total productos: {stats.get('total_productos', 0)}")
            print(f"   - Total marcas: {stats.get('total_marcas', 0)}")
            print(f"   - Precio promedio: ${stats.get('precio_promedio', 0):,.0f}" if stats.get('precio_promedio') else "   - Precio promedio: N/A")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Error generando snapshot: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    archivo = generate_snapshot()
    if archivo:
        print(f"\n🎉 Snapshot completo disponible en: {archivo}")