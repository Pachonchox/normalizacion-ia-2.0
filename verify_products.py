#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verificar productos guardados"""

import psycopg2
import json

def main():
    conn = psycopg2.connect(
        host="34.176.197.136",
        port=5432,
        database="postgres",
        user="postgres",
        password="Osmar2503!"
    )
    
    cursor = conn.cursor()
    
    print("=== PRODUCTOS MAESTROS ===")
    cursor.execute("SELECT fingerprint, name, brand, category, ai_enhanced, ai_confidence FROM productos_maestros ORDER BY created_at DESC LIMIT 5")
    products = cursor.fetchall()
    
    for prod in products:
        print(f"Fingerprint: {prod[0][:16]}...")
        print(f"Nombre: {prod[1]}")
        print(f"Marca: {prod[2]}")
        print(f"Categoria: {prod[3]}")
        print(f"AI Enhanced: {prod[4]} (conf: {prod[5]})")
        print("-" * 50)
    
    print("\n=== PRECIOS ACTUALES ===")
    cursor.execute("""
        SELECT pa.fingerprint, pa.precio_normal, pa.precio_tarjeta, 
               pa.currency, r.name as retailer
        FROM precios_actuales pa
        JOIN retailers r ON pa.retailer_id = r.id
        ORDER BY pa.ultima_actualizacion DESC
        LIMIT 5
    """)
    prices = cursor.fetchall()
    
    for price in prices:
        print(f"Fingerprint: {price[0][:16]}...")
        precio_normal = f"${price[1]:,} {price[3]}" if price[1] else "N/A"
        precio_tarjeta = f"${price[2]:,} {price[3]}" if price[2] else "N/A"
        print(f"Precio Normal: {precio_normal}")
        print(f"Precio Tarjeta: {precio_tarjeta}")
        print(f"Retailer: {price[4]}")
        print("-" * 30)
    
    print("\n=== ESTADISTICAS GENERALES ===")
    cursor.execute("SELECT COUNT(*) FROM productos_maestros WHERE active = true")
    total_products = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM precios_actuales")
    total_prices = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM retailers WHERE active = true")
    total_retailers = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM processing_logs WHERE created_at > NOW() - INTERVAL '1 hour'")
    recent_logs = cursor.fetchone()[0]
    
    print(f"Productos maestros: {total_products}")
    print(f"Precios actuales: {total_prices}")
    print(f"Retailers activos: {total_retailers}")
    print(f"Logs ultima hora: {recent_logs}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()