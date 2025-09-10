#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificar datos guardados en la base de datos
"""

import os
import psycopg2
import json
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def verificar_datos():
    """Verificar y mostrar datos guardados en BD"""
    
    print("="*60)
    print("VERIFICACION DE DATOS EN BASE DE DATOS")
    print("="*60)
    
    # Configuración
    db_config = {
        'host': os.getenv('DB_HOST'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }
    
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # 1. PRODUCTOS MAESTROS
        print("\n[1] PRODUCTOS MAESTROS")
        print("-"*40)
        
        cursor.execute("""
            SELECT fingerprint, product_id, name, brand, category, 
                   processing_version, created_at
            FROM productos_maestros
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        productos = cursor.fetchall()
        print(f"Total productos recientes: {len(productos)}\n")
        
        for p in productos[:5]:
            print(f"ID: {p[1]}")
            print(f"   Nombre: {p[2][:50]}...")
            print(f"   Marca: {p[3]}")
            print(f"   Categoria: {p[4]}")
            print(f"   Version: {p[5]}")
            print(f"   Creado: {p[6]}")
            print()
        
        # 2. PRECIOS ACTUALES
        print("[2] PRECIOS ACTUALES")
        print("-"*40)
        
        cursor.execute("""
            SELECT pa.product_id, r.name as retailer,
                   pa.precio_normal, pa.precio_tarjeta, pa.precio_oferta,
                   pa.updated_at
            FROM precios_actuales pa
            JOIN retailers r ON pa.retailer_id = r.id
            ORDER BY pa.updated_at DESC
            LIMIT 10
        """)
        
        precios = cursor.fetchall()
        print(f"Total precios recientes: {len(precios)}\n")
        
        for p in precios[:5]:
            print(f"Producto: {p[0]} @ {p[1]}")
            print(f"   Normal: ${p[2]:,}" if p[2] else "   Normal: -")
            if p[3]:
                print(f"   Tarjeta: ${p[3]:,}")
            if p[4]:
                print(f"   Oferta: ${p[4]:,}")
            print(f"   Actualizado: {p[5]}")
            print()
        
        # 3. ESTADISTICAS POR CATEGORIA
        print("[3] ESTADISTICAS POR CATEGORIA")
        print("-"*40)
        
        cursor.execute("""
            SELECT category, COUNT(*) as total
            FROM productos_maestros
            GROUP BY category
            ORDER BY total DESC
        """)
        
        categorias = cursor.fetchall()
        
        for cat, total in categorias:
            print(f"   {cat}: {total} productos")
        
        # 4. ESTADISTICAS POR RETAILER
        print("\n[4] ESTADISTICAS POR RETAILER")
        print("-"*40)
        
        cursor.execute("""
            SELECT r.name, COUNT(DISTINCT pa.product_id) as productos
            FROM precios_actuales pa
            JOIN retailers r ON pa.retailer_id = r.id
            GROUP BY r.name
            ORDER BY productos DESC
        """)
        
        retailers = cursor.fetchall()
        
        for retailer, total in retailers:
            print(f"   {retailer}: {total} productos")
        
        # 5. PRODUCTOS MAS RECIENTES
        print("\n[5] ULTIMOS PRODUCTOS AGREGADOS")
        print("-"*40)
        
        cursor.execute("""
            SELECT pm.name, pm.brand, pm.category, pm.created_at
            FROM productos_maestros pm
            WHERE pm.created_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour'
            ORDER BY pm.created_at DESC
            LIMIT 10
        """)
        
        recientes = cursor.fetchall()
        
        if recientes:
            print(f"Productos agregados en la ultima hora: {len(recientes)}\n")
            for r in recientes:
                tiempo = datetime.now() - r[3].replace(tzinfo=None)
                minutos = int(tiempo.total_seconds() / 60)
                print(f"   - {r[0][:40]}")
                print(f"     {r[1]} | {r[2]} | hace {minutos} minutos")
        else:
            print("No hay productos nuevos en la ultima hora")
        
        # RESUMEN
        cursor.execute("SELECT COUNT(*) FROM productos_maestros")
        total_productos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM precios_actuales")
        total_precios = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM retailers")
        total_retailers = cursor.fetchone()[0]
        
        print("\n" + "="*60)
        print("RESUMEN DE BASE DE DATOS")
        print("="*60)
        print(f"\n[OK] Total productos maestros: {total_productos}")
        print(f"[OK] Total registros de precios: {total_precios}")
        print(f"[OK] Total retailers: {total_retailers}")
        print(f"\n[EXITO] Base de datos operativa con datos normalizados")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        return False

if __name__ == "__main__":
    verificar_datos()