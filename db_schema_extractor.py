#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🗄️ Extractor de Esquema de Base de Datos
Genera documentación completa del esquema actual
"""

import os
import json
from src.simple_db_connector import SimplePostgreSQLConnector

def extract_full_schema():
    """Extraer esquema completo de la base de datos"""
    
    # Credenciales desde .env
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = int(os.getenv('DB_PORT', '5432'))
    db_name = os.getenv('DB_NAME', 'postgres')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')

    print(f"Conectando a {db_user}@{db_host}:{db_port}/{db_name}")

    try:
        connector = SimplePostgreSQLConnector(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password,
            pool_size=1
        )
        
        schema = {}
        
        with connector.get_connection() as conn:
            with conn.cursor() as cursor:
                
                # 1. Obtener lista de tablas
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """)
                
                tables = [row[0] for row in cursor.fetchall()]
                print(f"\nTABLAS ENCONTRADAS ({len(tables)}):")
                for table in tables:
                    print(f"  - {table}")
                
                # 2. Para cada tabla, obtener columnas
                for table in tables:
                    cursor.execute("""
                        SELECT 
                            column_name,
                            data_type,
                            is_nullable,
                            column_default,
                            character_maximum_length,
                            numeric_precision,
                            numeric_scale
                        FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                        ORDER BY ordinal_position
                    """, (table,))
                    
                    columns = []
                    for col in cursor.fetchall():
                        columns.append({
                            'name': col[0],
                            'type': col[1],
                            'nullable': col[2] == 'YES',
                            'default': col[3],
                            'max_length': col[4],
                            'precision': col[5],
                            'scale': col[6]
                        })
                    
                    # 3. Obtener primary keys
                    cursor.execute("""
                        SELECT column_name
                        FROM information_schema.key_column_usage
                        WHERE table_schema = 'public'
                        AND table_name = %s
                        AND constraint_name IN (
                            SELECT constraint_name
                            FROM information_schema.table_constraints
                            WHERE table_schema = 'public'
                            AND table_name = %s
                            AND constraint_type = 'PRIMARY KEY'
                        )
                    """, (table, table))
                    
                    primary_keys = [row[0] for row in cursor.fetchall()]
                    
                    # 4. Obtener foreign keys
                    cursor.execute("""
                        SELECT 
                            kcu.column_name,
                            ccu.table_name AS foreign_table_name,
                            ccu.column_name AS foreign_column_name
                        FROM information_schema.key_column_usage AS kcu
                        JOIN information_schema.constraint_column_usage AS ccu
                            ON ccu.constraint_name = kcu.constraint_name
                        WHERE kcu.table_schema = 'public'
                        AND kcu.table_name = %s
                        AND kcu.constraint_name IN (
                            SELECT constraint_name
                            FROM information_schema.table_constraints
                            WHERE table_schema = 'public'
                            AND table_name = %s
                            AND constraint_type = 'FOREIGN KEY'
                        )
                    """, (table, table))
                    
                    foreign_keys = []
                    for fk in cursor.fetchall():
                        foreign_keys.append({
                            'column': fk[0],
                            'references_table': fk[1],
                            'references_column': fk[2]
                        })
                    
                    # 5. Obtener índices
                    cursor.execute("""
                        SELECT 
                            indexname,
                            indexdef
                        FROM pg_indexes
                        WHERE tablename = %s
                        AND schemaname = 'public'
                    """, (table,))
                    
                    indexes = []
                    for idx in cursor.fetchall():
                        indexes.append({
                            'name': idx[0],
                            'definition': idx[1]
                        })
                    
                    schema[table] = {
                        'columns': columns,
                        'primary_keys': primary_keys,
                        'foreign_keys': foreign_keys,
                        'indexes': indexes
                    }
        
        return schema
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    schema = extract_full_schema()
    
    if schema:
        # Guardar esquema como JSON
        with open('db_schema.json', 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
        
        print(f"\nEsquema guardado en db_schema.json")
        print(f"Total tablas procesadas: {len(schema)}")
    else:
        print("No se pudo extraer el esquema")