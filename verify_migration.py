#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verificar migración de datos"""

import psycopg2

def main():
    conn = psycopg2.connect(
        host="34.176.197.136",
        port=5432,
        database="postgres",
        user="postgres",
        password="Osmar2503!"
    )
    
    cursor = conn.cursor()
    
    print("=== CATEGORIAS MIGRADAS ===")
    cursor.execute("SELECT category_id, name, synonyms FROM categories ORDER BY category_id")
    categories = cursor.fetchall()
    
    for cat in categories:
        synonyms = ', '.join(cat[2][:3]) + ('...' if len(cat[2]) > 3 else '')
        print(f"{cat[0]:<15} | {cat[1]:<25} | {synonyms}")
    
    print("\n=== MARCAS MIGRADAS (muestra) ===")
    cursor.execute("SELECT brand_canonical, array_length(aliases, 1) FROM brands ORDER BY brand_canonical LIMIT 10")
    brands = cursor.fetchall()
    
    for brand in brands:
        print(f"{brand[0]:<20} | {brand[1]} aliases")
    
    print("\n=== ESQUEMAS DE ATRIBUTOS ===")
    cursor.execute("SELECT category_id, COUNT(*) as attr_count FROM attributes_schema GROUP BY category_id ORDER BY category_id")
    attr_counts = cursor.fetchall()
    
    for attr in attr_counts:
        print(f"{attr[0]:<15} | {attr[1]} atributos definidos")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()