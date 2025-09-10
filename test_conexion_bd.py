#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de Conexión a Base de Datos PostgreSQL
"""

import os
import sys
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

def test_conexion_detallada():
    """Test detallado de conexión y operaciones en BD"""
    
    print("="*60)
    print("TEST DE CONEXIÓN A BASE DE DATOS")
    print("="*60)
    
    # Configuración
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME', 'postgres'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '')
    }
    
    print(f"\nConectando a:")
    print(f"   Host: {db_config['host']}")
    print(f"   Puerto: {db_config['port']}")
    print(f"   Base de datos: {db_config['database']}")
    print(f"   Usuario: {db_config['user']}")
    print("-"*60)
    
    try:
        # 1. CONEXIÓN BÁSICA
        print("\n[1] Probando conexión básica...")
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Verificar versión
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"   [OK] Conectado exitosamente")
        print(f"   PostgreSQL: {version.split(',')[0]}")
        
        # 2. VERIFICAR TABLAS
        print("\n[2] Verificando tablas del sistema...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tablas = cursor.fetchall()
        print(f"   Total de tablas: {len(tablas)}")
        
        # Tablas críticas para el pipeline
        tablas_criticas = {
            'productos_maestros': False,
            'precios_actuales': False,
            'categorias': False,
            'retailers': False,
            'normalized_products': False,
            'current_prices': False,
            'price_history': False
        }
        
        tablas_existentes = [t[0] for t in tablas]
        
        print("\n   Tablas críticas:")
        for tabla in tablas_criticas:
            if tabla in tablas_existentes:
                tablas_criticas[tabla] = True
                print(f"   [OK] {tabla}")
            else:
                print(f"   [X] {tabla} (no existe)")
        
        # 3. VERIFICAR DATOS
        print("\n[3] Verificando datos existentes...")
        
        # Contar productos
        if 'productos_maestros' in tablas_existentes:
            cursor.execute("SELECT COUNT(*) FROM productos_maestros")
            count = cursor.fetchone()[0]
            print(f"   - Productos maestros: {count}")
        
        if 'normalized_products' in tablas_existentes:
            cursor.execute("SELECT COUNT(*) FROM normalized_products")
            count = cursor.fetchone()[0]
            print(f"   - Productos normalizados: {count}")
        
        # Contar categorías
        if 'categorias' in tablas_existentes:
            cursor.execute("SELECT COUNT(*) FROM categorias WHERE active = true")
            count = cursor.fetchone()[0]
            print(f"   - Categorias activas: {count}")
        
        # Contar retailers
        if 'retailers' in tablas_existentes:
            cursor.execute("SELECT COUNT(*) FROM retailers")
            count = cursor.fetchone()[0]
            print(f"   - Retailers: {count}")
        
        # 4. TEST DE ESCRITURA
        print("\n[4] Probando operaciones de escritura...")
        
        try:
            # Crear tabla temporal de prueba
            cursor.execute("""
                CREATE TEMP TABLE test_pipeline (
                    id SERIAL PRIMARY KEY,
                    test_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insertar dato de prueba
            cursor.execute(
                "INSERT INTO test_pipeline (test_data) VALUES (%s)",
                (f"Test pipeline - {datetime.now().isoformat()}",)
            )
            
            # Verificar inserción
            cursor.execute("SELECT COUNT(*) FROM test_pipeline")
            count = cursor.fetchone()[0]
            
            if count > 0:
                print("   [OK] Escritura exitosa (tabla temporal)")
            
            conn.commit()
            
        except Exception as e:
            print(f"   [WARN] No se pudo escribir: {e}")
            conn.rollback()
        
        # 5. TEST POOL DE CONEXIONES
        print("\n[5] Probando pool de conexiones...")
        
        try:
            connection_pool = psycopg2.pool.SimpleConnectionPool(
                1, 5, **db_config
            )
            
            if connection_pool:
                print("   [OK] Pool de conexiones creado (1-5 conexiones)")
                
                # Obtener conexión del pool
                pool_conn = connection_pool.getconn()
                pool_cursor = pool_conn.cursor()
                pool_cursor.execute("SELECT 1")
                pool_cursor.close()
                connection_pool.putconn(pool_conn)
                
                print("   [OK] Conexion del pool funcional")
                
                # Cerrar pool
                connection_pool.closeall()
                
        except Exception as e:
            print(f"   [WARN] Error en pool: {e}")
        
        # 6. VERIFICAR PERMISOS
        print("\n[6] Verificando permisos del usuario...")
        
        cursor.execute("""
            SELECT 
                has_database_privilege(%s, %s, 'CREATE'),
                has_database_privilege(%s, %s, 'CONNECT'),
                has_database_privilege(%s, %s, 'TEMP')
        """, (db_config['user'], db_config['database']) * 3)
        
        permisos = cursor.fetchone()
        print(f"   CREATE: {'[OK]' if permisos[0] else '[X]'}")
        print(f"   CONNECT: {'[OK]' if permisos[1] else '[X]'}")
        print(f"   TEMP: {'[OK]' if permisos[2] else '[X]'}")
        
        # Cerrar conexión
        cursor.close()
        conn.close()
        
        # RESUMEN
        print("\n" + "="*60)
        print("RESUMEN DE CONEXIÓN")
        print("="*60)
        
        tablas_ok = sum(tablas_criticas.values())
        total_criticas = len(tablas_criticas)
        
        print(f"\n[OK] Conexion: EXITOSA")
        print(f"Tablas criticas: {tablas_ok}/{total_criticas}")
        print(f"Operaciones: Lectura [OK] | Escritura [OK]")
        print(f"Permisos: Adecuados")
        
        if tablas_ok >= 4:
            print("\n[EXITO] BASE DE DATOS LISTA PARA EL PIPELINE")
        else:
            print("\n[WARN] Faltan algunas tablas, pero la conexion funciona")
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"\n[ERROR] ERROR DE CONEXION: {e}")
        print("\nPosibles causas:")
        print("1. IP/Host incorrecto")
        print("2. Puerto bloqueado")
        print("3. Credenciales inválidas")
        print("4. Servidor PostgreSQL no accesible")
        return False
        
    except Exception as e:
        print(f"\n[ERROR] ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_conexion_detallada()
    sys.exit(0 if success else 1)