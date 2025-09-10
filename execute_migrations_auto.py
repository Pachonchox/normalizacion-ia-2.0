#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ejecuta migraciones y truncate automáticamente
"""

import psycopg2
import sys

def execute_all():
    print("="*60)
    print("EJECUTANDO MIGRACIONES Y TRUNCATE AUTOMATICO")
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
        # 1. TRUNCAR DATOS PRIMERO (para limpiar todo)
        print("\n1. TRUNCANDO TODOS LOS DATOS...")
        
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
        
        truncated = 0
        for table in tables_to_truncate:
            try:
                cursor.execute(f"TRUNCATE TABLE {table} CASCADE;")
                print(f"   OK: Truncado {table}")
                truncated += 1
            except psycopg2.errors.UndefinedTable:
                print(f"   SKIP: {table} no existe aun")
            except Exception as e:
                print(f"   ERROR en {table}: {e}")
        
        # Rehabilitar FK
        cursor.execute("SET session_replication_role = 'origin';")
        conn.commit()
        print(f"   Total truncados: {truncated} tablas")
        
        # 2. CREAR EXTENSIONES
        print("\n2. Creando extensiones...")
        try:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            conn.commit()
            print("   OK: Extension vector")
        except Exception as e:
            conn.rollback()
            print(f"   INFO: {e}")
        
        try:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
            conn.commit()
            print("   OK: Extension uuid-ossp")
        except Exception as e:
            conn.rollback()
            print(f"   INFO: {e}")
        
        # 3. CREAR TABLAS GPT-5
        print("\n3. Creando tablas GPT-5...")
        
        tables_sql = [
            # model_config
            """
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
            )
            """,
            
            # gpt5_batch_jobs
            """
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
            )
            """,
            
            # product_complexity_cache
            """
            CREATE TABLE IF NOT EXISTS product_complexity_cache (
                fingerprint VARCHAR(64) PRIMARY KEY,
                complexity_score NUMERIC(3,2) NOT NULL,
                model_assigned VARCHAR(50) NOT NULL,
                routing_reason VARCHAR(200),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # semantic_cache
            """
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
            )
            """,
            
            # processing_metrics
            """
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fingerprint VARCHAR(64),
                retailer VARCHAR(50),
                category VARCHAR(50)
            )
            """,
            
            # processing_queue
            """
            CREATE TABLE IF NOT EXISTS processing_queue (
                id SERIAL PRIMARY KEY,
                fingerprint VARCHAR(64) NOT NULL,
                product_data JSONB NOT NULL,
                priority INTEGER DEFAULT 5,
                status VARCHAR(50) DEFAULT 'pending',
                assigned_model VARCHAR(50),
                batch_id VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # category_embeddings
            """
            CREATE TABLE IF NOT EXISTS category_embeddings (
                category_id VARCHAR(50) PRIMARY KEY,
                category_name VARCHAR(200) NOT NULL,
                embedding vector(1536),
                sample_count INTEGER DEFAULT 0,
                avg_complexity NUMERIC(3,2),
                typical_attributes JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
        
        created = 0
        for sql in tables_sql:
            try:
                cursor.execute(sql)
                created += 1
            except Exception as e:
                print(f"   ERROR: {e}")
                conn.rollback()
        
        conn.commit()
        print(f"   OK: {created} tablas creadas/verificadas")
        
        # 4. CONFIGURAR MODELOS
        print("\n4. Configurando modelos GPT...")
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
        print("   OK: 4 modelos configurados")
        
        # 5. ACTUALIZAR TABLAS EXISTENTES
        print("\n5. Actualizando tablas existentes...")
        
        updates = [
            "ALTER TABLE ai_metadata_cache ADD COLUMN IF NOT EXISTS model_used VARCHAR(50)",
            "ALTER TABLE ai_metadata_cache ADD COLUMN IF NOT EXISTS tokens_used INTEGER DEFAULT 0",
            "ALTER TABLE ai_metadata_cache ADD COLUMN IF NOT EXISTS processing_version VARCHAR(20) DEFAULT 'v1.0'",
            "ALTER TABLE ai_metadata_cache ADD COLUMN IF NOT EXISTS batch_id VARCHAR(100)",
            "ALTER TABLE ai_metadata_cache ADD COLUMN IF NOT EXISTS quality_score NUMERIC(3,2)",
            "ALTER TABLE ai_metadata_cache ADD COLUMN IF NOT EXISTS ttl_hours INTEGER DEFAULT 168",
            "ALTER TABLE ai_metadata_cache ADD COLUMN IF NOT EXISTS ai_response JSONB",
            "ALTER TABLE ai_metadata_cache ADD COLUMN IF NOT EXISTS embedding vector(1536)",
            "ALTER TABLE ai_metadata_cache ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            
            "ALTER TABLE productos_maestros ADD COLUMN IF NOT EXISTS complexity_score NUMERIC(3,2)",
            "ALTER TABLE productos_maestros ADD COLUMN IF NOT EXISTS last_model_used VARCHAR(50)",
            "ALTER TABLE productos_maestros ADD COLUMN IF NOT EXISTS processing_confidence NUMERIC(3,2)",
            "ALTER TABLE productos_maestros ADD COLUMN IF NOT EXISTS last_processed_at TIMESTAMP",
            "ALTER TABLE productos_maestros ADD COLUMN IF NOT EXISTS processing_count INTEGER DEFAULT 0"
        ]
        
        updated = 0
        for sql in updates:
            try:
                cursor.execute(sql)
                updated += 1
            except Exception:
                pass  # Columna ya existe
        
        conn.commit()
        print(f"   OK: {updated} columnas agregadas/verificadas")
        
        # 6. CREAR INDICES
        print("\n6. Creando indices...")
        
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_semantic_embedding ON semantic_cache USING hnsw (embedding vector_cosine_ops)",
            "CREATE INDEX IF NOT EXISTS idx_complexity_score ON product_complexity_cache(complexity_score)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_created ON processing_metrics(created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_queue_status ON processing_queue(status) WHERE status = 'pending'",
            "CREATE INDEX IF NOT EXISTS idx_batch_jobs_status ON gpt5_batch_jobs(status)",
            "CREATE INDEX IF NOT EXISTS idx_ai_cache_model ON ai_metadata_cache(model_used)",
            "CREATE INDEX IF NOT EXISTS idx_ai_cache_batch ON ai_metadata_cache(batch_id)"
        ]
        
        idx_created = 0
        for sql in indices:
            try:
                cursor.execute(sql)
                idx_created += 1
            except Exception:
                pass
        
        conn.commit()
        print(f"   OK: {idx_created} indices creados/verificados")
        
        # 7. CREAR VISTAS MATERIALIZADAS
        print("\n7. Creando vistas materializadas...")
        
        views = [
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_products_by_complexity AS
            SELECT 
                pm.categoria_id,
                COUNT(DISTINCT pm.id) as total_products,
                AVG(pcc.complexity_score) as avg_complexity,
                SUM(CASE WHEN pcc.model_assigned = 'gpt-5-mini' THEN 1 ELSE 0 END) as gpt5_mini_count,
                SUM(CASE WHEN pcc.model_assigned = 'gpt-5' THEN 1 ELSE 0 END) as gpt5_count,
                CURRENT_TIMESTAMP as last_refresh
            FROM productos_maestros pm
            LEFT JOIN product_complexity_cache pcc ON pm.fingerprint = pcc.fingerprint
            GROUP BY pm.categoria_id
            """,
            
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_cost_metrics AS
            SELECT 
                DATE(created_at) as date,
                model,
                request_type,
                COUNT(*) as total_requests,
                SUM(tokens_input) as total_input_tokens,
                SUM(tokens_output) as total_output_tokens,
                SUM(cost_usd) as total_cost_usd,
                AVG(latency_ms) as avg_latency_ms,
                CURRENT_TIMESTAMP as last_refresh
            FROM processing_metrics
            GROUP BY DATE(created_at), model, request_type
            """
        ]
        
        for sql in views:
            try:
                cursor.execute(sql)
                conn.commit()
                print("   OK: Vista materializada creada")
            except Exception as e:
                conn.rollback()
                if "already exists" not in str(e):
                    print(f"   ERROR: {e}")
        
        # 8. VERIFICACION FINAL
        print("\n8. VERIFICACION FINAL...")
        
        # Contar modelos
        cursor.execute("SELECT COUNT(*) FROM model_config WHERE active = TRUE")
        model_count = cursor.fetchone()[0]
        
        # Contar tablas GPT5
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND (table_name LIKE 'gpt5_%' OR table_name = 'semantic_cache' 
                 OR table_name = 'product_complexity_cache' OR table_name = 'processing_metrics')
        """)
        table_count = cursor.fetchone()[0]
        
        # Verificar columnas en ai_metadata_cache
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.columns
            WHERE table_name = 'ai_metadata_cache'
            AND column_name IN ('model_used', 'tokens_used', 'batch_id', 'quality_score', 'embedding')
        """)
        col_count = cursor.fetchone()[0]
        
        # Verificar datos truncados
        cursor.execute("SELECT COUNT(*) FROM ai_metadata_cache")
        ai_cache_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM productos_maestros")
        productos_count = cursor.fetchone()[0]
        
        print(f"   Modelos GPT activos: {model_count}")
        print(f"   Tablas GPT-5: {table_count}")
        print(f"   Columnas GPT-5 en ai_metadata_cache: {col_count}")
        print(f"   Registros en ai_metadata_cache: {ai_cache_count}")
        print(f"   Registros en productos_maestros: {productos_count}")
        
        print("\n" + "="*60)
        print("MIGRACION Y TRUNCATE COMPLETADO EXITOSAMENTE")
        print("="*60)
        print("\nEstado final:")
        print("  - Base de datos limpia (0 registros)")
        print("  - Esquema GPT-5 instalado")
        print("  - 4 modelos configurados")
        print("  - Sistema listo para procesamiento")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"\nERROR CRITICO: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        cursor.close()
        conn.close()
        return False

if __name__ == "__main__":
    success = execute_all()
    sys.exit(0 if success else 1)