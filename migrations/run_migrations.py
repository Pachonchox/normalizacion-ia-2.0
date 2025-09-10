#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Script de Ejecución de Migraciones GPT-5
Ejecuta las migraciones de forma segura y ordenada
"""

import psycopg2
from psycopg2 import sql
import sys
import os
from pathlib import Path
import logging
from datetime import datetime
import json
import time
from typing import Dict, List, Tuple

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MigrationRunner:
    """Ejecutor de migraciones con validación y rollback"""
    
    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
        self.migrations_dir = Path(__file__).parent
        
    def connect(self) -> bool:
        """Conectar a la base de datos"""
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            self.connection.autocommit = False  # Control manual de transacciones
            logger.info(f"✅ Conectado a {self.host}:{self.port}/{self.database}")
            return True
        except Exception as e:
            logger.error(f"❌ Error conectando: {e}")
            return False
    
    def create_migration_table(self):
        """Crear tabla de control de migraciones si no existe"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS migration_history (
                        id SERIAL PRIMARY KEY,
                        migration_file VARCHAR(255) UNIQUE NOT NULL,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        execution_time_ms INTEGER,
                        status VARCHAR(50) DEFAULT 'completed',
                        error_message TEXT,
                        rollback_at TIMESTAMP
                    )
                """)
                self.connection.commit()
                logger.info("📋 Tabla migration_history verificada")
        except Exception as e:
            logger.error(f"Error creando tabla de migraciones: {e}")
            self.connection.rollback()
            raise
    
    def check_migration_applied(self, migration_file: str) -> bool:
        """Verificar si una migración ya fue aplicada"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM migration_history 
                    WHERE migration_file = %s AND status = 'completed'
                """, (migration_file,))
                count = cursor.fetchone()[0]
                return count > 0
        except:
            return False
    
    def backup_schema(self) -> str:
        """Crear backup del esquema actual"""
        backup_file = f"backup_schema_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        backup_path = self.migrations_dir / "backups" / backup_file
        backup_path.parent.mkdir(exist_ok=True)
        
        try:
            # Usar pg_dump para backup (requiere pg_dump instalado)
            import subprocess
            
            env = os.environ.copy()
            env['PGPASSWORD'] = self.password
            
            result = subprocess.run([
                'pg_dump',
                '-h', self.host,
                '-p', str(self.port),
                '-U', self.user,
                '-d', self.database,
                '--schema-only',
                '-f', str(backup_path)
            ], env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"💾 Backup creado: {backup_path}")
                return str(backup_path)
            else:
                logger.warning(f"⚠️ No se pudo crear backup con pg_dump: {result.stderr}")
                return None
        except Exception as e:
            logger.warning(f"⚠️ pg_dump no disponible: {e}")
            return None
    
    def validate_prerequisites(self) -> Tuple[bool, List[str]]:
        """Validar prerequisitos antes de migración"""
        issues = []
        
        try:
            with self.connection.cursor() as cursor:
                # Verificar versión PostgreSQL
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                logger.info(f"📌 PostgreSQL: {version}")
                
                # Verificar extensiones requeridas disponibles
                cursor.execute("""
                    SELECT name FROM pg_available_extensions 
                    WHERE name IN ('vector', 'uuid-ossp', 'pg_stat_statements')
                """)
                extensions = [row[0] for row in cursor.fetchall()]
                
                if 'vector' not in extensions:
                    issues.append("❌ Extensión 'vector' no disponible (requerida para embeddings)")
                if 'uuid-ossp' not in extensions:
                    issues.append("⚠️ Extensión 'uuid-ossp' no disponible (recomendada)")
                
                # Verificar tablas existentes
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('ai_metadata_cache', 'productos_maestros', 'categories')
                """)
                existing_tables = [row[0] for row in cursor.fetchall()]
                
                if 'ai_metadata_cache' not in existing_tables:
                    issues.append("⚠️ Tabla 'ai_metadata_cache' no existe")
                if 'productos_maestros' not in existing_tables:
                    issues.append("⚠️ Tabla 'productos_maestros' no existe")
                
                # Verificar espacio disponible
                cursor.execute("""
                    SELECT pg_database_size(current_database()) as size,
                           pg_size_pretty(pg_database_size(current_database())) as size_pretty
                """)
                db_size = cursor.fetchone()
                logger.info(f"💾 Tamaño BD actual: {db_size[1]}")
                
                return len(issues) == 0, issues
                
        except Exception as e:
            logger.error(f"Error validando prerequisitos: {e}")
            return False, [str(e)]
    
    def execute_migration(self, migration_file: str) -> bool:
        """Ejecutar un archivo de migración"""
        migration_path = self.migrations_dir / migration_file
        
        if not migration_path.exists():
            logger.error(f"❌ Archivo no encontrado: {migration_path}")
            return False
        
        # Verificar si ya fue aplicada
        if self.check_migration_applied(migration_file):
            logger.info(f"⏭️ Migración ya aplicada: {migration_file}")
            return True
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🚀 Ejecutando migración: {migration_file}")
        logger.info(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # Leer archivo SQL
            with open(migration_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Dividir por bloques DO $$ para ejecutar correctamente
            sql_blocks = []
            current_block = []
            in_do_block = False
            
            for line in sql_content.split('\n'):
                if 'DO $$' in line:
                    if current_block:
                        sql_blocks.append('\n'.join(current_block))
                        current_block = []
                    in_do_block = True
                
                current_block.append(line)
                
                if '$$;' in line and in_do_block:
                    sql_blocks.append('\n'.join(current_block))
                    current_block = []
                    in_do_block = False
            
            if current_block:
                sql_blocks.append('\n'.join(current_block))
            
            # Ejecutar bloques
            with self.connection.cursor() as cursor:
                for block_num, block in enumerate(sql_blocks, 1):
                    if block.strip():
                        try:
                            # Limpiar comentarios de una línea que pueden causar problemas
                            clean_block = '\n'.join(
                                line for line in block.split('\n')
                                if not line.strip().startswith('--')
                            )
                            
                            if clean_block.strip():
                                cursor.execute(clean_block)
                                logger.info(f"  ✓ Bloque {block_num}/{len(sql_blocks)} ejecutado")
                        except psycopg2.errors.DuplicateTable:
                            logger.info(f"  ⏭️ Tabla ya existe (bloque {block_num})")
                        except psycopg2.errors.DuplicateObject:
                            logger.info(f"  ⏭️ Objeto ya existe (bloque {block_num})")
                        except Exception as e:
                            if "already exists" in str(e).lower():
                                logger.info(f"  ⏭️ Objeto ya existe (bloque {block_num})")
                            else:
                                raise
                
                # Registrar migración exitosa
                execution_time = int((time.time() - start_time) * 1000)
                cursor.execute("""
                    INSERT INTO migration_history (migration_file, execution_time_ms, status)
                    VALUES (%s, %s, 'completed')
                """, (migration_file, execution_time))
                
                self.connection.commit()
                
                logger.info(f"✅ Migración completada en {execution_time}ms")
                return True
                
        except Exception as e:
            self.connection.rollback()
            logger.error(f"❌ Error en migración: {e}")
            
            # Registrar error
            try:
                with self.connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO migration_history (migration_file, status, error_message)
                        VALUES (%s, 'failed', %s)
                    """, (migration_file, str(e)))
                    self.connection.commit()
            except:
                pass
            
            return False
    
    def verify_migration(self, migration_name: str) -> Dict:
        """Verificar que la migración se aplicó correctamente"""
        results = {
            'tables_created': 0,
            'columns_added': 0,
            'indices_created': 0,
            'issues': []
        }
        
        try:
            with self.connection.cursor() as cursor:
                if '001' in migration_name:
                    # Verificar tablas nuevas de migración 001
                    expected_tables = [
                        'model_config', 'gpt5_batch_jobs', 'product_complexity_cache',
                        'semantic_cache', 'processing_metrics', 'processing_queue',
                        'category_embeddings'
                    ]
                    
                    for table in expected_tables:
                        cursor.execute("""
                            SELECT COUNT(*) FROM information_schema.tables 
                            WHERE table_schema = 'public' AND table_name = %s
                        """, (table,))
                        if cursor.fetchone()[0] > 0:
                            results['tables_created'] += 1
                            logger.info(f"  ✓ Tabla {table} creada")
                        else:
                            results['issues'].append(f"Tabla {table} no encontrada")
                    
                    # Verificar modelos configurados
                    cursor.execute("SELECT COUNT(*) FROM model_config WHERE active = TRUE")
                    model_count = cursor.fetchone()[0]
                    logger.info(f"  ✓ {model_count} modelos configurados")
                    
                elif '002' in migration_name:
                    # Verificar columnas agregadas en migración 002
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns
                        WHERE table_name = 'ai_metadata_cache'
                        AND column_name IN ('model_used', 'tokens_used', 'batch_id', 
                                           'quality_score', 'ttl_hours', 'embedding')
                    """)
                    columns_added = cursor.fetchall()
                    results['columns_added'] = len(columns_added)
                    logger.info(f"  ✓ {len(columns_added)} columnas agregadas a ai_metadata_cache")
                
                # Verificar índices
                cursor.execute("""
                    SELECT COUNT(*) FROM pg_indexes 
                    WHERE schemaname = 'public' 
                    AND indexname LIKE 'idx_%'
                    AND tablename IN ('ai_metadata_cache', 'semantic_cache', 
                                     'processing_metrics', 'gpt5_batch_jobs')
                """)
                results['indices_created'] = cursor.fetchone()[0]
                logger.info(f"  ✓ {results['indices_created']} índices creados")
                
        except Exception as e:
            results['issues'].append(str(e))
        
        return results
    
    def run_all_migrations(self) -> bool:
        """Ejecutar todas las migraciones pendientes"""
        if not self.connect():
            return False
        
        try:
            # Crear tabla de control
            self.create_migration_table()
            
            # Validar prerequisitos
            valid, issues = self.validate_prerequisites()
            if issues:
                logger.warning("⚠️ Advertencias encontradas:")
                for issue in issues:
                    logger.warning(f"  {issue}")
                
                if not valid and any('❌' in issue for issue in issues):
                    logger.error("❌ Prerequisitos críticos no cumplidos")
                    return False
            
            # Crear backup
            backup_path = self.backup_schema()
            if backup_path:
                logger.info(f"💾 Backup guardado en: {backup_path}")
            
            # Lista de migraciones en orden
            migrations = [
                '001_gpt5_initial_schema.sql',
                '002_update_existing_tables.sql'
            ]
            
            success_count = 0
            
            for migration in migrations:
                if self.execute_migration(migration):
                    # Verificar migración
                    verification = self.verify_migration(migration)
                    if verification['issues']:
                        logger.warning(f"⚠️ Problemas en verificación: {verification['issues']}")
                    else:
                        logger.info(f"✅ Migración verificada correctamente")
                    success_count += 1
                else:
                    logger.error(f"❌ Fallo en migración: {migration}")
                    break
            
            # Resumen final
            logger.info(f"\n{'='*60}")
            logger.info(f"📊 RESUMEN DE MIGRACIÓN")
            logger.info(f"{'='*60}")
            logger.info(f"✅ Migraciones exitosas: {success_count}/{len(migrations)}")
            
            if success_count == len(migrations):
                logger.info("🎉 ¡Todas las migraciones completadas exitosamente!")
                
                # Estadísticas finales
                with self.connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT 
                            (SELECT COUNT(*) FROM information_schema.tables 
                             WHERE table_schema = 'public') as total_tables,
                            (SELECT COUNT(*) FROM model_config WHERE active = TRUE) as active_models,
                            (SELECT pg_size_pretty(pg_database_size(current_database()))) as db_size
                    """)
                    stats = cursor.fetchone()
                    logger.info(f"\n📈 Estado final:")
                    logger.info(f"  - Tablas totales: {stats[0]}")
                    logger.info(f"  - Modelos activos: {stats[1]}")
                    logger.info(f"  - Tamaño BD: {stats[2]}")
                
                return True
            else:
                logger.error("❌ Algunas migraciones fallaron")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error general: {e}")
            return False
        finally:
            if self.connection:
                self.connection.close()
                logger.info("🔌 Conexión cerrada")

def main():
    """Función principal"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║        🚀 MIGRACIÓN GPT-5 - Normalización IA 2.0        ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Configuración de conexión
    DB_CONFIG = {
        'host': '34.176.197.136',
        'port': 5432,
        'database': 'postgres',
        'user': 'postgres',
        'password': 'Osmar2503!'
    }
    
    # Confirmar ejecución
    print(f"📍 Servidor: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"🗄️ Base de datos: {DB_CONFIG['database']}")
    print(f"👤 Usuario: {DB_CONFIG['user']}")
    print()
    
    response = input("⚠️ ¿Desea ejecutar las migraciones? (s/n): ").lower()
    
    if response != 's':
        print("❌ Migración cancelada")
        return
    
    # Ejecutar migraciones
    runner = MigrationRunner(**DB_CONFIG)
    
    if runner.run_all_migrations():
        print("\n✅ Migración completada exitosamente")
        print("\n📝 Próximos pasos:")
        print("  1. Verificar logs en migration_*.log")
        print("  2. Ejecutar tests de validación")
        print("  3. Actualizar normalize.py con nuevo conector")
        print("  4. Migrar datos existentes")
        sys.exit(0)
    else:
        print("\n❌ Migración falló - revisar logs")
        sys.exit(1)

if __name__ == "__main__":
    main()