#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🗑️ Script de Truncate de Datos - Sistema GPT-5
Limpia todos los datos sin eliminar el esquema
"""

import psycopg2
import sys
import logging
from datetime import datetime
from typing import Dict, List
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataTruncator:
    """Ejecutor de truncate con confirmación y logging"""
    
    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
        
        # Tablas a truncar (orden importante por dependencias)
        self.tables_to_truncate = [
            # Tablas GPT-5 nuevas
            'processing_queue',
            'processing_metrics',
            'semantic_cache',
            'product_complexity_cache',
            'gpt5_batch_jobs',
            'category_embeddings',
            
            # Tablas del sistema actual
            'processing_logs',
            'price_alerts',
            'precios_historicos',
            'precios_actuales',
            'ai_metadata_cache',
            'productos_maestros'
        ]
        
        # Tablas a preservar (configuración)
        self.tables_to_preserve = [
            'model_config',      # Configuración de modelos GPT
            'categories',        # Taxonomía
            'brands',           # Marcas
            'retailers',        # Retailers
            'attributes_schema', # Esquemas
            'system_config',    # Configuración sistema
            'migration_history' # Historial migraciones
        ]
    
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
            logger.info(f"✅ Conectado a {self.host}:{self.port}/{self.database}")
            return True
        except Exception as e:
            logger.error(f"❌ Error conectando: {e}")
            return False
    
    def get_table_stats(self) -> Dict[str, int]:
        """Obtener estadísticas de tablas antes del truncate"""
        stats = {}
        
        try:
            with self.connection.cursor() as cursor:
                for table in self.tables_to_truncate:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        stats[table] = count
                    except psycopg2.errors.UndefinedTable:
                        stats[table] = -1  # Tabla no existe
                    except Exception:
                        stats[table] = 0
                
                # Tamaño total de BD
                cursor.execute("""
                    SELECT pg_size_pretty(pg_database_size(current_database()))
                """)
                stats['db_size'] = cursor.fetchone()[0]
                
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
        
        return stats
    
    def truncate_table(self, table_name: str) -> bool:
        """Truncar una tabla específica"""
        try:
            with self.connection.cursor() as cursor:
                # Verificar si existe
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    )
                """, (table_name,))
                
                if not cursor.fetchone()[0]:
                    logger.info(f"⏭️  Tabla no existe: {table_name}")
                    return True
                
                # Truncar con CASCADE
                cursor.execute(f"TRUNCATE TABLE {table_name} CASCADE")
                self.connection.commit()
                logger.info(f"✓ Truncado: {table_name}")
                return True
                
        except Exception as e:
            self.connection.rollback()
            logger.error(f"❌ Error truncando {table_name}: {e}")
            return False
    
    def reset_sequences(self):
        """Reiniciar todas las secuencias"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT sequence_name 
                    FROM information_schema.sequences 
                    WHERE sequence_schema = 'public'
                """)
                
                sequences = cursor.fetchall()
                
                for seq in sequences:
                    cursor.execute(f"ALTER SEQUENCE {seq[0]} RESTART WITH 1")
                
                self.connection.commit()
                logger.info(f"✓ {len(sequences)} secuencias reiniciadas")
                
        except Exception as e:
            logger.error(f"Error reiniciando secuencias: {e}")
    
    def vacuum_analyze(self):
        """Ejecutar VACUUM y ANALYZE"""
        try:
            # VACUUM requiere autocommit
            old_isolation = self.connection.isolation_level
            self.connection.set_isolation_level(0)
            
            with self.connection.cursor() as cursor:
                cursor.execute("VACUUM ANALYZE")
                logger.info("✓ VACUUM y ANALYZE completado")
            
            self.connection.set_isolation_level(old_isolation)
            
        except Exception as e:
            logger.error(f"Error en VACUUM: {e}")
    
    def refresh_materialized_views(self):
        """Refrescar vistas materializadas"""
        try:
            with self.connection.cursor() as cursor:
                views = [
                    'mv_products_by_complexity',
                    'mv_daily_cost_metrics'
                ]
                
                for view in views:
                    try:
                        cursor.execute(f"REFRESH MATERIALIZED VIEW {view}")
                        self.connection.commit()
                        logger.info(f"✓ Vista refrescada: {view}")
                    except psycopg2.errors.UndefinedObject:
                        logger.info(f"⏭️  Vista no existe: {view}")
                    except Exception as e:
                        logger.warning(f"No se pudo refrescar {view}: {e}")
                        
        except Exception as e:
            logger.error(f"Error refrescando vistas: {e}")
    
    def execute_truncate(self, confirm: bool = True) -> bool:
        """Ejecutar truncate completo"""
        
        if not self.connect():
            return False
        
        try:
            # Obtener estadísticas actuales
            stats_before = self.get_table_stats()
            
            print("\n" + "="*60)
            print("📊 ESTADÍSTICAS ACTUALES:")
            print("="*60)
            
            total_records = 0
            for table, count in stats_before.items():
                if table != 'db_size' and count > 0:
                    print(f"  • {table}: {count:,} registros")
                    total_records += count
            
            print(f"\n  Total: {total_records:,} registros")
            print(f"  Tamaño BD: {stats_before.get('db_size', 'N/A')}")
            
            # Confirmación
            if confirm:
                print("\n" + "⚠️ "*10)
                print("ADVERTENCIA: Se eliminarán TODOS los datos")
                print("⚠️ "*10)
                print(f"\nTablas a TRUNCAR ({len(self.tables_to_truncate)}):")
                for table in self.tables_to_truncate:
                    print(f"  🗑️ {table}")
                
                print(f"\nTablas a PRESERVAR ({len(self.tables_to_preserve)}):")
                for table in self.tables_to_preserve:
                    print(f"  ✅ {table}")
                
                response = input("\n¿Confirma el TRUNCATE de datos? (escriba 'SI' para confirmar): ")
                
                if response != 'SI':
                    print("❌ Operación cancelada")
                    return False
            
            print("\n🚀 Iniciando TRUNCATE...")
            print("-"*60)
            
            # Deshabilitar temporalmente foreign keys
            with self.connection.cursor() as cursor:
                cursor.execute("SET session_replication_role = 'replica'")
                self.connection.commit()
            
            # Truncar tablas en orden
            success_count = 0
            failed_tables = []
            
            for table in self.tables_to_truncate:
                if self.truncate_table(table):
                    success_count += 1
                else:
                    failed_tables.append(table)
            
            # Rehabilitar foreign keys
            with self.connection.cursor() as cursor:
                cursor.execute("SET session_replication_role = 'origin'")
                self.connection.commit()
            
            # Reset secuencias
            print("\n🔄 Reiniciando secuencias...")
            self.reset_sequences()
            
            # Refrescar vistas materializadas
            print("\n📊 Refrescando vistas materializadas...")
            self.refresh_materialized_views()
            
            # VACUUM y ANALYZE
            print("\n🧹 Ejecutando VACUUM y ANALYZE...")
            self.vacuum_analyze()
            
            # Estadísticas finales
            stats_after = self.get_table_stats()
            
            print("\n" + "="*60)
            print("✅ TRUNCATE COMPLETADO")
            print("="*60)
            print(f"  • Tablas truncadas: {success_count}/{len(self.tables_to_truncate)}")
            
            if failed_tables:
                print(f"  • Tablas con error: {', '.join(failed_tables)}")
            
            print(f"  • Tamaño BD después: {stats_after.get('db_size', 'N/A')}")
            
            # Log en BD
            try:
                with self.connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO processing_logs 
                        (process_type, status, message, details)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        'TRUNCATE_DATA',
                        'completed' if not failed_tables else 'partial',
                        f'Truncate de {success_count} tablas',
                        psycopg2.extras.Json({
                            'tables_truncated': success_count,
                            'failed_tables': failed_tables,
                            'timestamp': datetime.now().isoformat()
                        })
                    ))
                    self.connection.commit()
            except:
                pass  # Si processing_logs fue truncada, ignorar
            
            return len(failed_tables) == 0
            
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
    ║        🗑️ TRUNCATE DE DATOS - Sistema GPT-5            ║
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
    
    # Crear truncator
    truncator = DataTruncator(**DB_CONFIG)
    
    # Ejecutar con confirmación
    if truncator.execute_truncate(confirm=True):
        print("\n✅ Truncate completado exitosamente")
        print("\n📝 La base de datos está lista para:")
        print("  1. Recibir nuevos datos con el sistema GPT-5")
        print("  2. Comenzar procesamiento batch")
        print("  3. Poblar cache semántico")
        sys.exit(0)
    else:
        print("\n❌ Truncate falló o fue cancelado")
        sys.exit(1)

if __name__ == "__main__":
    main()