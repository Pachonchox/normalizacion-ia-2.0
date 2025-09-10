#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ejecuta migraciones y truncate de forma simplificada
"""

import psycopg2
import sys
import time

def execute_migrations():
    print("="*60)
    print("EJECUTANDO MIGRACIONES Y TRUNCATE GPT-5")
    print("="*60)
    
    # Conectar
    try:
        conn = psycopg2.connect(
            host='34.176.197.136',
            port=5432,
            database='postgres',
            user='postgres',
            password='Osmar2503!'
        )
        conn.autocommit = False
        cursor = conn.cursor()
        print("OK: Conectado a la base de datos")
    except Exception as e:
        print(f"ERROR: No se pudo conectar: {e}")
        return False
    
    try:
        # 1. CREAR EXTENSIONES
        print("\n1. Creando extensiones...")
        try:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cursor.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
            conn.commit()
            print("   OK: Extensiones creadas")
        except Exception as e:
            print(f"   ADVERTENCIA: {e}")
            conn.rollback()
        
        # 2. CREAR TABLAS GPT-5
        print("\n2. Creando tablas nuevas GPT-5...")
        
        # model_config
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_config (
                model_name VARCHAR(50) PRIMARY KEY,
                family VARCHAR(50) NOT NULL,
                cost_per_1k_input NUMERIC(10,6) NOT NULL,
                cost_per_1k_output NUMERIC(10,6) NOT NULL,
                batch_discount NUMERIC(3,2) DEFAULT 0.50,
                max_tokens INTEGER NOT NULL,
                timeout_ms INTEGER DEFAULT 30000,
                fallback_model VARCHAR(50),
                complexity_threshold_min NUMERIC(3,2) DEFAULT 0.0,
                complexity_threshold_max NUMERIC(3,2) DEFAULT 1.0,
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # gpt5_batch_jobs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gpt5_batch_jobs (
                batch_id VARCHAR(100) PRIMARY KEY,
                model VARCHAR(50) NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                total_products INTEGER NOT NULL,
                processed_products INTEGER DEFAULT 0,
                estimated_cost NUMERIC(10,4),
                actual_cost NUMERIC(10,4),
                file_path VARCHAR(500),
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                metadata JSONB DEFAULT '{}'::jsonb
            );
        """)
        
        # product_complexity_cache
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product_complexity_cache (
                fingerprint VARCHAR(64) PRIMARY KEY,
                complexity_score NUMERIC(3,2) NOT NULL,
                model_assigned VARCHAR(50) NOT NULL,
                routing_reason VARCHAR(200),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # semantic_cache
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS semantic_cache (
                id SERIAL PRIMARY KEY,
                fingerprint VARCHAR(64) NOT NULL,
                embedding vector(1536),
                product_data JSONB NOT NULL,
                normalized_data JSONB NOT NULL,
                model_used VARCHAR(50),
                similarity_threshold NUMERIC(3,2) DEFAULT 0.85,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                ttl_hours INTEGER DEFAULT 168
            );
        """)
        
        # processing_metrics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_metrics (
                id SERIAL PRIMARY KEY,
                model VARCHAR(50) NOT NULL,
                request_type VARCHAR(50) NOT NULL,
                tokens_input INTEGER DEFAULT 0,
                tokens_output INTEGER DEFAULT 0,
                cost_usd NUMERIC(10,6) DEFAULT 0,
                latency_ms INTEGER,
                cache_hit BOOLEAN DEFAULT FALSE,
                complexity_score NUMERIC(3,2),
                success BOOLEAN DEFAULT TRUE,
                error_type VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # processing_queue
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_queue (
                id SERIAL PRIMARY KEY,
                fingerprint VARCHAR(64) NOT NULL,
                product_data JSONB NOT NULL,
                priority INTEGER DEFAULT 5,
                status VARCHAR(50) DEFAULT 'pending',
                assigned_model VARCHAR(50),
                batch_id VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        conn.commit()
        print("   OK: Tablas GPT-5 creadas")
        
        # 3. INSERTAR CONFIGURACION DE MODELOS
        print("\n3. Configurando modelos GPT...")
        cursor.execute("""
            INSERT INTO model_config 
            (model_name, family, cost_per_1k_input, cost_per_1k_output, batch_discount, 
             max_tokens, timeout_ms, fallback_model, complexity_threshold_min, complexity_threshold_max) 
            VALUES
            ('gpt-5-mini', 'gpt-5', 0.0003, 0.0012, 0.50, 16384, 30000, 'gpt-5', 0.0, 0.35),
            ('gpt-5', 'gpt-5', 0.0030, 0.0120, 0.50, 32768, 60000, 'gpt-4o-mini', 0.35, 0.75),
            ('gpt-4o-mini', 'gpt-4o', 0.00015, 0.0006, 0.50, 128000, 30000, null, 0.75, 1.0),
            ('gpt-4o', 'gpt-4o', 0.0025, 0.0100, 0.50, 128000, 60000, null, 0.0, 1.0)
            ON CONFLICT (model_name) DO UPDATE SET
                cost_per_1k_input = EXCLUDED.cost_per_1k_input,
                cost_per_1k_output = EXCLUDED.cost_per_1k_output,
                updated_at = CURRENT_TIMESTAMP;
        """)
        conn.commit()
        print("   OK: Modelos configurados")
        
        # 4. ACTUALIZAR TABLAS EXISTENTES
        print("\n4. Actualizando tablas existentes...")
        
        # Agregar columnas a ai_metadata_cache si no existen
        columns_to_add = [
            ("model_used", "VARCHAR(50)"),
            ("tokens_used", "INTEGER DEFAULT 0"),
            ("processing_version", "VARCHAR(20) DEFAULT 'v1.0'"),
            ("batch_id", "VARCHAR(100)"),
            ("quality_score", "NUMERIC(3,2)"),
            ("ttl_hours", "INTEGER DEFAULT 168"),
            ("ai_response", "JSONB"),
            ("embedding", "vector(1536)"),
            ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        ]
        
        for col_name, col_type in columns_to_add:
            try:
                cursor.execute(f"""
                    ALTER TABLE ai_metadata_cache 
                    ADD COLUMN IF NOT EXISTS {col_name} {col_type};
                """)
                conn.commit()
            except Exception as e:
                conn.rollback()
                # Ignorar si la columna ya existe
                pass
        
        print("   OK: Tablas existentes actualizadas")
        
        # 5. TRUNCAR DATOS
        print("\n5. TRUNCANDO DATOS...")
        print("   ADVERTENCIA: Se eliminaran TODOS los datos")
        
        # Confirmar
        response = input("   Escriba 'SI' para confirmar TRUNCATE: ")
        if response != 'SI':
            print("   CANCELADO: No se truncaron datos")
            return False
        
        # Deshabilitar FK temporalmente
        cursor.execute("SET session_replication_role = 'replica';")
        
        # Lista de tablas a truncar
        tables_to_truncate = [
            'processing_queue',
            'processing_metrics', 
            'semantic_cache',
            'product_complexity_cache',
            'gpt5_batch_jobs',
            'processing_logs',
            'price_alerts',
            'precios_historicos',
            'precios_actuales',
            'ai_metadata_cache',
            'productos_maestros'
        ]
        
        for table in tables_to_truncate:
            try:
                cursor.execute(f"TRUNCATE TABLE {table} CASCADE;")
                print(f"   OK: Truncado {table}")
            except psycopg2.errors.UndefinedTable:
                print(f"   SKIP: {table} no existe")
            except Exception as e:
                print(f"   ERROR en {table}: {e}")
        
        # Rehabilitar FK
        cursor.execute("SET session_replication_role = 'origin';")
        conn.commit()
        
        print("   OK: Datos truncados")
        
        # 6. VERIFICACION FINAL
        print("\n6. Verificacion final...")
        
        # Contar modelos
        cursor.execute("SELECT COUNT(*) FROM model_config WHERE active = TRUE")
        model_count = cursor.fetchone()[0]
        print(f"   Modelos activos: {model_count}")
        
        # Contar tablas GPT5
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND (table_name LIKE 'gpt5_%' OR table_name LIKE '%_cache')
        """)
        table_count = cursor.fetchone()[0]
        print(f"   Tablas GPT-5: {table_count}")
        
        # Verificar ai_metadata_cache tiene nuevas columnas
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.columns
            WHERE table_name = 'ai_metadata_cache'
            AND column_name IN ('model_used', 'tokens_used', 'batch_id')
        """)
        col_count = cursor.fetchone()[0]
        print(f"   Columnas GPT-5 en ai_metadata_cache: {col_count}")
        
        print("\n" + "="*60)
        print("MIGRACION COMPLETADA EXITOSAMENTE")
        print("="*60)
        print("\nLa base de datos esta lista para:")
        print("  1. Procesamiento con GPT-5")
        print("  2. Batch processing con 50% descuento")
        print("  3. Cache semantico con embeddings")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"\nERROR CRITICO: {e}")
        conn.rollback()
        cursor.close()
        conn.close()
        return False

if __name__ == "__main__":
    success = execute_migrations()
    sys.exit(0 if success else 1)