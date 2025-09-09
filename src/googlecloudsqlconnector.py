"""
Google Cloud SQL PostgreSQL Connector
Sistema de Análisis de Precios Retail Chile
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from contextlib import contextmanager
from dataclasses import dataclass, asdict
import time

import psycopg2
from psycopg2 import pool, extras
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
from google.cloud.sql.connector import Connector
import pg8000
import numpy as np

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CloudSQLConfig:
    """Configuración para Google Cloud SQL"""
    project_id: str
    region: str
    instance_name: str
    database_name: str = "retail_prices"
    user: str = "postgres"
    password: Optional[str] = None
    use_cloud_sql_proxy: bool = True
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    enable_iam_auth: bool = False
    
    @property
    def instance_connection_string(self) -> str:
        """Formato: project:region:instance"""
        return f"{self.project_id}:{self.region}:{self.instance_name}"


class CloudSQLConnector:
    """
    Conector principal para Google Cloud SQL PostgreSQL
    con soporte para Cloud SQL Proxy y connection pooling
    """
    
    def __init__(self, config: CloudSQLConfig):
        self.config = config
        self.connector = None
        self.engine = None
        self.connection_pool = None
        self._init_connector()
        
    def _init_connector(self):
        """Inicializar Cloud SQL Connector"""
        try:
            if self.config.use_cloud_sql_proxy:
                # Usar Cloud SQL Python Connector
                self.connector = Connector()
                
                # Crear función para obtener conexiones
                def getconn() -> pg8000.dbapi.Connection:
                    conn = self.connector.connect(
                        self.config.instance_connection_string,
                        "pg8000",
                        user=self.config.user,
                        password=self.config.password,
                        db=self.config.database_name,
                        enable_iam_auth=self.config.enable_iam_auth
                    )
                    return conn
                
                # Crear engine SQLAlchemy con pool
                self.engine = create_engine(
                    "postgresql+pg8000://",
                    creator=getconn,
                    pool_size=self.config.pool_size,
                    max_overflow=self.config.max_overflow,
                    pool_timeout=self.config.pool_timeout,
                    pool_recycle=3600,  # Reciclar conexiones cada hora
                    pool_pre_ping=True,  # Verificar conexiones antes de usar
                    echo=False
                )
                
            else:
                # Conexión directa sin Cloud SQL Proxy (para desarrollo)
                connection_string = (
                    f"postgresql://{self.config.user}:{self.config.password}@"
                    f"/{self.config.database_name}?"
                    f"host=/cloudsql/{self.config.instance_connection_string}"
                )
                self.engine = create_engine(
                    connection_string,
                    pool_size=self.config.pool_size,
                    max_overflow=self.config.max_overflow,
                    pool_timeout=self.config.pool_timeout,
                    pool_recycle=3600,
                    pool_pre_ping=True,
                    echo=False
                )
            
            # Crear pool de conexiones psycopg2 para operaciones masivas
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=2,
                maxconn=self.config.pool_size,
                host=f"/cloudsql/{self.config.instance_connection_string}",
                database=self.config.database_name,
                user=self.config.user,
                password=self.config.password
            ) if not self.config.use_cloud_sql_proxy else None
            
            logger.info(f"✅ Conectado a Cloud SQL: {self.config.instance_connection_string}")
            
        except Exception as e:
            logger.error(f"❌ Error conectando a Cloud SQL: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Context manager para obtener conexión del pool"""
        conn = None
        try:
            if self.connection_pool:
                conn = self.connection_pool.getconn()
            else:
                conn = self.engine.connect()
            yield conn
        finally:
            if conn:
                if self.connection_pool:
                    self.connection_pool.putconn(conn)
                else:
                    conn.close()
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Ejecutar query SELECT y retornar resultados como lista de diccionarios"""
        with self.engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            return [dict(row._mapping) for row in result]
    
    def execute_update(self, query: str, params: Optional[Dict] = None) -> int:
        """Ejecutar query UPDATE/DELETE y retornar filas afectadas"""
        with self.engine.begin() as conn:
            result = conn.execute(text(query), params or {})
            return result.rowcount
    
    def bulk_insert(self, table: str, data: List[Dict], on_conflict: Optional[str] = None) -> int:
        """
        Inserción masiva optimizada para Cloud SQL
        
        Args:
            table: Nombre de la tabla
            data: Lista de diccionarios con los datos
            on_conflict: Cláusula ON CONFLICT (ej: "ON CONFLICT (fingerprint) DO UPDATE SET ...")
        
        Returns:
            Número de filas insertadas
        """
        if not data:
            return 0
        
        try:
            # Obtener columnas del primer registro
            columns = list(data[0].keys())
            
            # Crear query de inserción
            placeholders = ', '.join([f":{col}" for col in columns])
            columns_str = ', '.join(columns)
            
            query = f"""
                INSERT INTO {table} ({columns_str})
                VALUES ({placeholders})
            """
            
            if on_conflict:
                query += f" {on_conflict}"
            
            # Ejecutar inserción masiva
            with self.engine.begin() as conn:
                result = conn.execute(text(query), data)
                return result.rowcount
                
        except Exception as e:
            logger.error(f"Error en bulk_insert: {e}")
            raise
    
    def upsert_price(self, price_data: Dict) -> bool:
        """
        Upsert inteligente de precios con detección de cambios
        Solo actualiza si hay cambios reales en los precios
        """
        query = """
            INSERT INTO precios_actuales (
                fingerprint, retailer_id, product_id,
                precio_normal, precio_tarjeta, precio_oferta,
                currency, stock_status, url, metadata
            ) VALUES (
                :fingerprint, :retailer_id, :product_id,
                :precio_normal, :precio_tarjeta, :precio_oferta,
                :currency, :stock_status, :url, :metadata
            )
            ON CONFLICT (fingerprint, retailer_id) DO UPDATE SET
                precio_normal = EXCLUDED.precio_normal,
                precio_tarjeta = EXCLUDED.precio_tarjeta,
                precio_oferta = EXCLUDED.precio_oferta,
                stock_status = EXCLUDED.stock_status,
                url = EXCLUDED.url,
                metadata = EXCLUDED.metadata,
                ultima_actualizacion = CURRENT_TIMESTAMP
            WHERE 
                precios_actuales.precio_normal IS DISTINCT FROM EXCLUDED.precio_normal OR
                precios_actuales.precio_tarjeta IS DISTINCT FROM EXCLUDED.precio_tarjeta OR
                precios_actuales.precio_oferta IS DISTINCT FROM EXCLUDED.precio_oferta
            RETURNING id
        """
        
        # Convertir metadata a JSON si es necesario
        if 'metadata' in price_data and not isinstance(price_data['metadata'], str):
            price_data['metadata'] = json.dumps(price_data['metadata'])
        
        with self.engine.begin() as conn:
            result = conn.execute(text(query), price_data)
            return result.rowcount > 0
    
    def get_ai_cache(self, fingerprint: str) -> Optional[Dict]:
        """
        Obtener metadata IA desde el cache en BD
        Reemplaza la lectura de archivo JSON
        """
        query = """
            SELECT * FROM update_ai_cache_hit(:fingerprint)
        """
        
        result = self.execute_query(query, {'fingerprint': fingerprint})
        
        if result:
            cache_data = result[0]
            # Convertir a formato esperado por el pipeline
            return {
                'brand': cache_data['brand'],
                'model': cache_data['model'],
                'refined_attributes': cache_data['refined_attributes'],
                'normalized_name': cache_data['normalized_name'],
                'confidence': float(cache_data['confidence']) if cache_data['confidence'] else 0.0,
                'category_suggestion': cache_data['category_suggestion']
            }
        return None
    
    def set_ai_cache(self, fingerprint: str, metadata: Dict) -> bool:
        """
        Guardar metadata IA en el cache de BD
        Reemplaza la escritura a archivo JSON
        """
        query = """
            INSERT INTO ai_metadata_cache (
                fingerprint, brand, model, refined_attributes,
                normalized_name, confidence, category_suggestion,
                ai_processing_time, metadata
            ) VALUES (
                :fingerprint, :brand, :model, :refined_attributes,
                :normalized_name, :confidence, :category_suggestion,
                :ai_processing_time, :metadata
            )
            ON CONFLICT (fingerprint) DO UPDATE SET
                brand = EXCLUDED.brand,
                model = EXCLUDED.model,
                refined_attributes = EXCLUDED.refined_attributes,
                normalized_name = EXCLUDED.normalized_name,
                confidence = EXCLUDED.confidence,
                category_suggestion = EXCLUDED.category_suggestion,
                ai_processing_time = EXCLUDED.ai_processing_time,
                metadata = EXCLUDED.metadata,
                updated_at = CURRENT_TIMESTAMP
        """
        
        # Preparar datos para inserción
        cache_data = {
            'fingerprint': fingerprint,
            'brand': metadata.get('brand'),
            'model': metadata.get('model'),
            'refined_attributes': json.dumps(metadata.get('refined_attributes', {})),
            'normalized_name': metadata.get('normalized_name'),
            'confidence': metadata.get('confidence', 0.0),
            'category_suggestion': metadata.get('category_suggestion'),
            'ai_processing_time': metadata.get('ai_processing_time', 0.0),
            'metadata': json.dumps(metadata.get('metadata', {}))
        }
        
        return self.execute_update(query, cache_data) > 0
    
    def get_categories(self) -> List[Dict]:
        """Obtener todas las categorías activas desde BD"""
        query = """
            SELECT 
                category_id, name, synonyms, 
                parent_category, attributes_schema, level
            FROM categories
            WHERE active = TRUE
            ORDER BY level, name
        """
        return self.execute_query(query)
    
    def get_brands(self) -> Dict[str, List[str]]:
        """Obtener marcas y sus aliases desde BD"""
        query = """
            SELECT brand_canonical, aliases
            FROM brands
            WHERE active = TRUE
        """
        
        results = self.execute_query(query)
        
        # Convertir a formato esperado por el pipeline
        brands_dict = {}
        for row in results:
            brands_dict[row['brand_canonical']] = row['aliases']
        
        return brands_dict
    
    def create_daily_snapshot(self) -> int:
        """Ejecutar snapshot diario de precios"""
        query = "SELECT create_daily_snapshot()"
        
        with self.engine.begin() as conn:
            result = conn.execute(text(query))
            
            # Obtener número de registros procesados
            count_query = """
                SELECT COUNT(*) as count 
                FROM precios_historicos 
                WHERE fecha_snapshot = CURRENT_DATE
            """
            count_result = conn.execute(text(count_query))
            count = count_result.fetchone()[0]
            
            logger.info(f"✅ Snapshot diario creado: {count} registros")
            return count
    
    def get_price_comparison(self, fingerprints: Optional[List[str]] = None) -> List[Dict]:
        """
        Obtener comparación de precios entre retailers
        Optimizado para consultas frecuentes
        """
        if fingerprints:
            query = """
                SELECT * FROM mv_comparacion_precios
                WHERE fingerprint = ANY(:fingerprints)
            """
            params = {'fingerprints': fingerprints}
        else:
            query = "SELECT * FROM mv_comparacion_precios LIMIT 100"
            params = {}
        
        return self.execute_query(query, params)
    
    def get_price_history(self, fingerprint: str, days: int = 30) -> List[Dict]:
        """
        Obtener historial de precios para un producto
        """
        query = """
            SELECT 
                ph.fecha_snapshot,
                r.name as retailer,
                ph.precio_normal,
                ph.precio_tarjeta,
                ph.precio_oferta,
                ph.stock_status
            FROM precios_historicos ph
            JOIN retailers r ON ph.retailer_id = r.id
            WHERE ph.fingerprint = :fingerprint
                AND ph.fecha_snapshot >= CURRENT_DATE - (:days || ' days')::interval
            ORDER BY ph.fecha_snapshot DESC, r.name
        """
        
        return self.execute_query(query, {
            'fingerprint': fingerprint,
            'days': days
        })
    
    def detect_price_changes(self, threshold_percentage: float = 10.0) -> List[Dict]:
        """
        Detectar cambios de precio significativos
        """
        query = """
            SELECT 
                pa.fingerprint,
                pm.name,
                pm.brand,
                r.name as retailer,
                pa.precio_normal,
                pa.precio_anterior_normal,
                pa.cambio_porcentaje_normal,
                pa.precio_tarjeta,
                pa.precio_anterior_tarjeta,
                pa.cambio_porcentaje_tarjeta,
                pa.ultimo_cambio,
                pa.cambios_hoy
            FROM precios_actuales pa
            JOIN productos_maestros pm ON pa.fingerprint = pm.fingerprint
            JOIN retailers r ON pa.retailer_id = r.id
            WHERE 
                ABS(COALESCE(pa.cambio_porcentaje_normal, 0)) >= :threshold OR
                ABS(COALESCE(pa.cambio_porcentaje_tarjeta, 0)) >= :threshold OR
                ABS(COALESCE(pa.cambio_porcentaje_oferta, 0)) >= :threshold
            ORDER BY pa.ultimo_cambio DESC
        """
        
        return self.execute_query(query, {'threshold': threshold_percentage})
    
    def get_cache_metrics(self) -> Dict:
        """
        Obtener métricas del cache IA
        """
        query = """
            SELECT 
                COUNT(*) as total_entries,
                AVG(confidence) as avg_confidence,
                SUM(hits) as total_hits,
                AVG(hits) as avg_hits_per_entry,
                MAX(hits) as max_hits,
                COUNT(CASE WHEN hits > 0 THEN 1 END) as entries_with_hits,
                AVG(ai_processing_time) as avg_processing_time_ms
            FROM ai_metadata_cache
        """
        
        result = self.execute_query(query)
        return result[0] if result else {}
    
    def log_processing(self, module: str, operation: str, status: str,
                      affected_records: int = 0, error: Optional[str] = None,
                      metadata: Optional[Dict] = None):
        """
        Registrar operación en log de procesamiento
        """
        query = """
            INSERT INTO processing_logs (
                module_name, operation, status,
                affected_records, error_message, metadata
            ) VALUES (
                :module, :operation, :status,
                :affected_records, :error, :metadata
            )
        """
        
        self.execute_update(query, {
            'module': module,
            'operation': operation,
            'status': status,
            'affected_records': affected_records,
            'error': error,
            'metadata': json.dumps(metadata or {})
        })
    
    def refresh_materialized_views(self):
        """Refrescar vistas materializadas para análisis"""
        views = ['mv_comparacion_precios', 'mv_cache_metrics']
        
        for view in views:
            try:
                with self.engine.begin() as conn:
                    conn.execute(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view}"))
                logger.info(f"✅ Vista materializada {view} actualizada")
            except Exception as e:
                logger.error(f"❌ Error actualizando vista {view}: {e}")
    
    def create_alert(self, alert_config: Dict) -> int:
        """
        Crear configuración de alerta
        """
        query = """
            INSERT INTO price_alerts (
                fingerprint, retailer_id, alert_type,
                threshold_value, threshold_percentage,
                category, brand, notification_channels, config
            ) VALUES (
                :fingerprint, :retailer_id, :alert_type,
                :threshold_value, :threshold_percentage,
                :category, :brand, :notification_channels, :config
            )
            RETURNING id
        """
        
        # Preparar datos
        alert_config['notification_channels'] = json.dumps(
            alert_config.get('notification_channels', ['email'])
        )
        alert_config['config'] = json.dumps(
            alert_config.get('config', {})
        )
        
        with self.engine.begin() as conn:
            result = conn.execute(text(query), alert_config)
            return result.fetchone()[0]
    
    def check_alerts(self) -> List[Dict]:
        """
        Verificar alertas activas que deben ser disparadas
        """
        query = """
            WITH price_changes AS (
                SELECT 
                    pa.fingerprint,
                    pa.retailer_id,
                    CASE 
                        WHEN pa.cambio_porcentaje_normal < 0 THEN 'price_drop'
                        WHEN pa.cambio_porcentaje_normal > 0 THEN 'price_increase'
                        ELSE NULL
                    END as change_type,
                    ABS(pa.cambio_porcentaje_normal) as change_percentage,
                    pa.precio_normal - pa.precio_anterior_normal as change_value
                FROM precios_actuales pa
                WHERE pa.ultimo_cambio >= NOW() - INTERVAL '1 hour'
                    AND pa.cambio_porcentaje_normal IS NOT NULL
            )
            SELECT 
                a.id as alert_id,
                a.fingerprint,
                a.retailer_id,
                a.alert_type,
                a.notification_channels,
                pc.change_percentage,
                pc.change_value,
                pm.name as product_name,
                pm.brand,
                r.name as retailer_name
            FROM price_alerts a
            JOIN price_changes pc ON 
                a.fingerprint = pc.fingerprint AND
                a.retailer_id = pc.retailer_id AND
                a.alert_type = pc.change_type
            JOIN productos_maestros pm ON a.fingerprint = pm.fingerprint
            JOIN retailers r ON a.retailer_id = r.id
            WHERE a.active = TRUE
                AND (
                    (a.threshold_percentage IS NOT NULL AND 
                     pc.change_percentage >= a.threshold_percentage) OR
                    (a.threshold_value IS NOT NULL AND 
                     ABS(pc.change_value) >= a.threshold_value)
                )
                AND (a.last_triggered IS NULL OR 
                     a.last_triggered < NOW() - INTERVAL '1 hour')
        """
        
        alerts = self.execute_query(query)
        
        # Actualizar last_triggered para evitar spam
        if alerts:
            alert_ids = [a['alert_id'] for a in alerts]
            update_query = """
                UPDATE price_alerts 
                SET last_triggered = CURRENT_TIMESTAMP,
                    trigger_count = trigger_count + 1
                WHERE id = ANY(:alert_ids)
            """
            self.execute_update(update_query, {'alert_ids': alert_ids})
        
        return alerts
    
    def get_system_config(self, key: Optional[str] = None) -> Any:
        """
        Obtener configuración del sistema
        """
        if key:
            query = """
                SELECT config_value 
                FROM system_config 
                WHERE config_key = :key AND active = TRUE
            """
            result = self.execute_query(query, {'key': key})
            return json.loads(result[0]['config_value']) if result else None
        else:
            query = """
                SELECT config_key, config_value, description
                FROM system_config
                WHERE active = TRUE
            """
            return self.execute_query(query)
    
    def close(self):
        """Cerrar conexiones y limpiar recursos"""
        try:
            if self.connector:
                self.connector.close()
            if self.engine:
                self.engine.dispose()
            if self.connection_pool:
                self.connection_pool.closeall()
            logger.info("✅ Conexiones cerradas correctamente")
        except Exception as e:
            logger.error(f"❌ Error cerrando conexiones: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Funciones helper para el pipeline
def create_connector_from_config(config_path: str = "config.local.toml") -> CloudSQLConnector:
    """
    Crear conector desde archivo de configuración TOML
    """
    import toml
    
    with open(config_path, 'r') as f:
        config = toml.load(f)
    
    db_config = config.get('database', {})
    
    cloud_config = CloudSQLConfig(
        project_id=db_config.get('project_id', os.environ.get('GCP_PROJECT')),
        region=db_config.get('region', 'us-central1'),
        instance_name=db_config.get('instance_name'),
        database_name=db_config.get('database_name', 'retail_prices'),
        user=db_config.get('user', 'postgres'),
        password=db_config.get('password', os.environ.get('DB_PASSWORD')),
        use_cloud_sql_proxy=db_config.get('use_cloud_sql_proxy', True)
    )
    
    return CloudSQLConnector(cloud_config)


# Clase para compatibilidad con el pipeline existente
class DatabaseCache:
    """
    Clase wrapper para reemplazar el cache de archivos JSON
    con cache en base de datos
    """
    
    def __init__(self, connector: CloudSQLConnector):
        self.connector = connector
        self.fallback_to_file = False
        self.cache_file = None
    
    def get(self, fingerprint: str) -> Optional[Dict]:
        """Obtener del cache (compatible con interfaz existente)"""
        try:
            return self.connector.get_ai_cache(fingerprint)
        except Exception as e:
            logger.error(f"Error obteniendo cache: {e}")
            if self.fallback_to_file and self.cache_file:
                # Fallback a archivo si está configurado
                return self._get_from_file(fingerprint)
            return None
    
    def set(self, fingerprint: str, metadata: Dict) -> bool:
        """Guardar en cache (compatible con interfaz existente)"""
        try:
            return self.connector.set_ai_cache(fingerprint, metadata)
        except Exception as e:
            logger.error(f"Error guardando cache: {e}")
            if self.fallback_to_file and self.cache_file:
                # Fallback a archivo si está configurado
                return self._save_to_file(fingerprint, metadata)
            return False
    
    def _get_from_file(self, fingerprint: str) -> Optional[Dict]:
        """Fallback: leer de archivo JSON"""
        if not os.path.exists(self.cache_file):
            return None
        
        with open(self.cache_file, 'r') as f:
            cache = json.load(f)
            return cache.get(fingerprint)
    
    def _save_to_file(self, fingerprint: str, metadata: Dict) -> bool:
        """Fallback: guardar en archivo JSON"""
        cache = {}
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
        
        cache[fingerprint] = metadata
        
        with open(self.cache_file, 'w') as f:
            json.dump(cache, f, indent=2)
        
        return True


if __name__ == "__main__":
    # Ejemplo de uso
    config = CloudSQLConfig(
        project_id="your-project-id",
        region="us-central1",
        instance_name="retail-prices-instance",
        database_name="retail_prices",
        user="postgres",
        password="your-password"
    )
    
    with CloudSQLConnector(config) as db:
        # Test de conexión
        result = db.execute_query("SELECT COUNT(*) as count FROM productos_maestros")
        print(f"Productos en BD: {result[0]['count']}")
        
        # Test de cache IA
        cache_data = db.get_ai_cache("test_fingerprint")
        if cache_data:
            print(f"Cache encontrado: {cache_data}")
        
        # Test de métricas
        metrics = db.get_cache_metrics()
        print(f"Métricas del cache: {metrics}")
        
        # Test de detección de cambios
        changes = db.detect_price_changes(threshold_percentage=5.0)
        print(f"Cambios detectados: {len(changes)}")