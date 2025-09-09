#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 Script Simple de Prueba de Conexión PostgreSQL
Prueba la conexión directa a PostgreSQL sin Cloud SQL
"""

import psycopg2
from psycopg2 import OperationalError

def main():
    """Prueba la conexión directa a PostgreSQL"""
    
    # Configuración de base de datos
    db_config = {
        "host": "34.176.197.136",
        "port": 5432,
        "database": "postgres", 
        "user": "postgres",
        "password": "Osmar2503!"
    }
    
    print(">> Iniciando prueba de conexion PostgreSQL directa...")
    
    try:
        # Conectar directamente con psycopg2
        print(f"-> Conectando a {db_config['host']}:{db_config['port']}...")
        
        connection = psycopg2.connect(
            host=db_config["host"],
            port=db_config["port"],
            database=db_config["database"],
            user=db_config["user"],
            password=db_config["password"]
        )
        
        print("OK: Conexion establecida exitosamente")
        
        # Crear cursor
        cursor = connection.cursor()
        
        # Verificar tablas existentes
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print(f"INFO: Tablas encontradas en la base de datos: {len(tables)}")
        
        for table in tables:
            print(f"  - {table[0]}")
        
        # Probar consulta simple
        cursor.execute("SELECT current_timestamp as now, version() as version;")
        result = cursor.fetchone()
        
        print(f"Timestamp actual: {result[0]}")
        print(f"Version PostgreSQL: {result[1][:50]}...")
        
        # Cerrar cursor y conexión
        cursor.close()
        connection.close()
        
    except OperationalError as e:
        print(f"ERROR: Error de conexion: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Error inesperado: {e}")
        return False
    
    print("SUCCESS: Prueba de conexion completada exitosamente!")
    return True

if __name__ == "__main__":
    main()