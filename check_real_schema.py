#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificar esquema real de las tablas
"""

import psycopg2

def main():
    print("Verificando esquema real de las tablas...")
    
    conn = psycopg2.connect(
        host='34.176.197.136',
        port=5432,
        database='postgres',
        user='postgres',
        password='Osmar2503!',
        connect_timeout=15
    )
    
    cursor = conn.cursor()
    
    # Tablas a verificar
    tables = ['productos_maestros', 'precios_actuales', 'precios_historicos']
    
    for table in tables:
        print(f"\n=== TABLA: {table} ===")
        try:
            cursor.execute(f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = '{table}'
                AND table_schema = 'public'
                ORDER BY ordinal_position
            """)
            
            columns = cursor.fetchall()
            if columns:
                for col in columns:
                    print(f"  {col[0]:<25} | {col[1]:<15} | NULL: {col[2]:<3} | Default: {col[3]}")
            else:
                print(f"  Tabla {table} no encontrada")
                
        except Exception as e:
            print(f"  Error: {e}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()