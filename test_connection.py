#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 Script de Prueba de Conexión PostgreSQL
Prueba la conexión a la base de datos y verifica las tablas
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from googlecloudsqlconnector import CloudSQLConnector

def main():
    """Prueba la conexión a PostgreSQL y verifica las tablas"""
    
    # Configuración de base de datos
    db_config = {
        "host": "34.176.197.136",
        "port": 5432,
        "database": "postgres", 
        "user": "postgres",
        "password": "Osmar2503!"
    }
    
    print("🚀 Iniciando prueba de conexión PostgreSQL...")
    
    try:
        # Crear conector
        connector = GoogleCloudSQLConnector(db_config)
        print("✅ Conector creado exitosamente")
        
        # Probar conexión
        with connector.get_connection() as conn:
            with conn.cursor() as cursor:
                print("✅ Conexión establecida exitosamente")
                
                # Verificar tablas existentes
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name;
                """)
                
                tables = cursor.fetchall()
                print(f"📊 Tablas encontradas en la base de datos: {len(tables)}")
                
                for table in tables:
                    print(f"  - {table[0]}")
                
                # Probar consulta simple
                cursor.execute("SELECT current_timestamp as now, version() as version;")
                result = cursor.fetchone()
                
                print(f"⏰ Timestamp actual: {result[0]}")
                print(f"🗂️ Versión PostgreSQL: {result[1][:50]}...")
                
    except Exception as e:
        print(f"❌ Error en la conexión: {e}")
        return False
    
    print("🎉 Prueba de conexión completada exitosamente!")
    return True

if __name__ == "__main__":
    main()