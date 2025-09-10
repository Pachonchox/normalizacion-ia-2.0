#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Conector PostgreSQL con Soporte GPT-5
Conector extendido con todas las funcionalidades para GPT-5:
- Batch processing
- Cache semántico con embeddings
- Métricas de costo
- Routing inteligente
"""

import psycopg2
from psycopg2 import pool, extras
import json
import logging
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager
from datetime import datetime, timedelta
import numpy as np
from enum import Enum

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """Modelos disponibles"""
    GPT5_MINI = "gpt-5-mini"
    GPT5 = "gpt-5"
    GPT4O_MINI = "gpt-4o-mini"
    GPT4O = "gpt-4o"

class BatchStatus(Enum):
    """Estados de batch"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class GPT5DatabaseConnector:
    """Conector completo para soporte GPT-5"""
    
    def __init__(self, host: str, port: int, database: str, user: str, password: str, pool_size: int = 10):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.pool_size = pool_size
        self.connection_pool = None
        self._init_pool()
    
    def _init_pool(self):
        """Inicializar pool de conexiones"""
        try:
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                1, self.pool_size,
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                cursor_factory=extras.RealDictCursor  # Retorna diccionarios
            )
            logger.info(f"✅ Pool GPT-5 inicializado: {self.host}:{self.port}/{self.database}")
        except Exception as e:
            logger.error(f"❌ Error inicializando pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Context manager para obtener conexión del pool"""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            yield conn
        finally:
            if conn:
                self.connection_pool.putconn(conn)
    
    # ============================================================================
    # 🤖 GESTIÓN DE MODELOS
    # ============================================================================
    
    def get_model_config(self, model_name: str = None) -> Optional[Dict]:
        """Obtener configuración de modelo(s)"""
        query = """
            SELECT model_name, family, cost_per_1k_input, cost_per_1k_output,
                   batch_discount, max_tokens, timeout_ms, fallback_model,
                   complexity_threshold_min, complexity_threshold_max
            FROM model_config 
            WHERE active = TRUE
        """
        params = []
        
        if model_name:
            query += " AND model_name = %s"
            params.append(model_name)
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    if model_name:
                        return cursor.fetchone()
                    return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error obteniendo config de modelo: {e}")
            return None
    
    def get_model_by_complexity(self, complexity_score: float) -> str:
        """Obtener modelo apropiado según complejidad"""
        query = """
            SELECT model_name
            FROM model_config
            WHERE active = TRUE
              AND %s >= complexity_threshold_min
              AND %s < complexity_threshold_max
            ORDER BY cost_per_1k_input ASC
            LIMIT 1
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (complexity_score, complexity_score))
                    result = cursor.fetchone()
                    return result['model_name'] if result else ModelType.GPT4O_MINI.value
        except Exception as e:
            logger.error(f"Error obteniendo modelo por complejidad: {e}")
            return ModelType.GPT4O_MINI.value
    
    # ============================================================================
    # 📊 BATCH PROCESSING
    # ============================================================================
    
    def create_batch_job(self, model: str, products: List[Dict], 
                         estimated_cost: float = None) -> str:
        """Crear nuevo trabajo batch"""
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(str(products).encode()).hexdigest()[:8]}"
        
        query = """
            INSERT INTO gpt5_batch_jobs 
            (batch_id, model, status, total_products, estimated_cost, metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING batch_id
        """
        
        metadata = {
            "product_count_by_category": {},
            "avg_name_length": np.mean([len(p.get('name', '')) for p in products]),
            "retailers": list(set(p.get('retailer', 'unknown') for p in products))
        }
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (
                        batch_id,
                        model,
                        BatchStatus.PENDING.value,
                        len(products),
                        estimated_cost,
                        json.dumps(metadata)
                    ))
                    conn.commit()
                    logger.info(f"✅ Batch job creado: {batch_id} ({len(products)} productos)")
                    return batch_id
        except Exception as e:
            logger.error(f"Error creando batch job: {e}")
            raise
    
    def update_batch_status(self, batch_id: str, status: BatchStatus, 
                           processed: int = None, error: str = None):
        """Actualizar estado de batch"""
        updates = ["status = %s"]
        params = [status.value]
        
        if processed is not None:
            updates.append("processed_products = %s")
            params.append(processed)
        
        if status == BatchStatus.PROCESSING and "started_at" not in updates:
            updates.append("started_at = CURRENT_TIMESTAMP")
        
        if status in [BatchStatus.COMPLETED, BatchStatus.FAILED]:
            updates.append("completed_at = CURRENT_TIMESTAMP")
        
        if error:
            updates.append("error_message = %s")
            params.append(error)
        
        params.append(batch_id)
        
        query = f"""
            UPDATE gpt5_batch_jobs 
            SET {', '.join(updates)}
            WHERE batch_id = %s
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    conn.commit()
                    logger.info(f"📊 Batch {batch_id} actualizado: {status.value}")
        except Exception as e:
            logger.error(f"Error actualizando batch: {e}")
    
    def get_pending_batches(self, limit: int = 10) -> List[Dict]:
        """Obtener batches pendientes"""
        query = """
            SELECT batch_id, model, total_products, created_at
            FROM gpt5_batch_jobs
            WHERE status = %s
            ORDER BY created_at ASC
            LIMIT %s
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (BatchStatus.PENDING.value, limit))
                    return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error obteniendo batches pendientes: {e}")
            return []
    
    # ============================================================================
    # 🧠 CACHE SEMÁNTICO
    # ============================================================================
    
    def store_semantic_cache(self, fingerprint: str, embedding: np.ndarray, 
                            product_data: Dict, normalized_data: Dict, 
                            model_used: str = None):
        """Guardar en cache semántico con embedding"""
        query = """
            INSERT INTO semantic_cache 
            (fingerprint, embedding, product_data, normalized_data, model_used)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (fingerprint) DO UPDATE SET
                embedding = EXCLUDED.embedding,
                normalized_data = EXCLUDED.normalized_data,
                model_used = EXCLUDED.model_used,
                last_accessed = CURRENT_TIMESTAMP,
                access_count = semantic_cache.access_count + 1
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Convertir numpy array a lista para PostgreSQL
                    embedding_list = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
                    
                    cursor.execute(query, (
                        fingerprint,
                        embedding_list,
                        json.dumps(product_data),
                        json.dumps(normalized_data),
                        model_used
                    ))
                    conn.commit()
                    logger.debug(f"🧠 Cache semántico guardado: {fingerprint[:8]}...")
        except Exception as e:
            logger.error(f"Error guardando cache semántico: {e}")
    
    def search_semantic_cache(self, embedding: np.ndarray, 
                             similarity_threshold: float = 0.85, 
                             limit: int = 5) -> List[Dict]:
        """Buscar en cache por similitud semántica"""
        query = """
            SELECT fingerprint, product_data, normalized_data, model_used,
                   1 - (embedding <=> %s::vector) as similarity
            FROM semantic_cache
            WHERE 1 - (embedding <=> %s::vector) >= %s
              AND created_at > CURRENT_TIMESTAMP - INTERVAL '%s hours' * ttl_hours
            ORDER BY similarity DESC
            LIMIT %s
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    embedding_list = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
                    
                    cursor.execute(query, (
                        embedding_list,
                        embedding_list,
                        similarity_threshold,
                        1,  # Factor para TTL
                        limit
                    ))
                    
                    results = cursor.fetchall()
                    
                    # Actualizar access count para los resultados
                    if results:
                        fingerprints = [r['fingerprint'] for r in results]
                        update_query = """
                            UPDATE semantic_cache 
                            SET last_accessed = CURRENT_TIMESTAMP,
                                access_count = access_count + 1
                            WHERE fingerprint = ANY(%s)
                        """
                        cursor.execute(update_query, (fingerprints,))
                        conn.commit()
                    
                    return results
        except Exception as e:
            logger.error(f"Error buscando en cache semántico: {e}")
            return []
    
    # ============================================================================
    # 📈 MÉTRICAS Y COSTOS
    # ============================================================================
    
    def log_processing_metric(self, model: str, request_type: str, 
                             tokens_input: int, tokens_output: int,
                             cost_usd: float, latency_ms: int = None,
                             cache_hit: bool = False, cache_type: str = None,
                             complexity_score: float = None, batch_id: str = None,
                             success: bool = True, error_type: str = None,
                             fingerprint: str = None, retailer: str = None,
                             category: str = None):
        """Registrar métrica de procesamiento"""
        query = """
            INSERT INTO processing_metrics (
                model, request_type, tokens_input, tokens_output, cost_usd,
                latency_ms, cache_hit, cache_type, complexity_score, batch_id,
                success, error_type, fingerprint, retailer, category
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (
                        model, request_type, tokens_input, tokens_output, cost_usd,
                        latency_ms, cache_hit, cache_type, complexity_score, batch_id,
                        success, error_type, fingerprint, retailer, category
                    ))
                    conn.commit()
                    
                    if not success:
                        logger.warning(f"⚠️ Métrica de error registrada: {error_type}")
        except Exception as e:
            logger.error(f"Error registrando métrica: {e}")
    
    def get_cost_summary(self, days: int = 7) -> Dict:
        """Obtener resumen de costos"""
        query = """
            SELECT 
                model,
                COUNT(*) as total_requests,
                SUM(tokens_input) as total_input_tokens,
                SUM(tokens_output) as total_output_tokens,
                SUM(cost_usd) as total_cost,
                AVG(cost_usd) as avg_cost_per_request,
                SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END)::FLOAT / COUNT(*) as cache_hit_rate,
                AVG(latency_ms) as avg_latency,
                SUM(CASE WHEN success THEN 1 ELSE 0 END)::FLOAT / COUNT(*) as success_rate
            FROM processing_metrics
            WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '%s days'
            GROUP BY model
            ORDER BY total_cost DESC
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (days,))
                    results = cursor.fetchall()
                    
                    summary = {
                        'period_days': days,
                        'models': results,
                        'total_cost': sum(r['total_cost'] or 0 for r in results),
                        'total_requests': sum(r['total_requests'] for r in results)
                    }
                    
                    # Calcular ahorros por cache
                    cache_hits = sum(r['total_requests'] * (r['cache_hit_rate'] or 0) for r in results)
                    estimated_savings = cache_hits * 0.0003  # Estimado promedio
                    summary['cache_savings_usd'] = estimated_savings
                    
                    return summary
        except Exception as e:
            logger.error(f"Error obteniendo resumen de costos: {e}")
            return {}
    
    # ============================================================================
    # 🔄 COMPLEJIDAD Y ROUTING
    # ============================================================================
    
    def save_complexity_analysis(self, fingerprint: str, complexity_score: float,
                                model_assigned: str, routing_reason: str = None,
                                weights: Dict[str, float] = None):
        """Guardar análisis de complejidad"""
        query = """
            INSERT INTO product_complexity_cache (
                fingerprint, complexity_score, model_assigned, routing_reason,
                category_weight, name_length_weight, price_weight, attributes_weight
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (fingerprint) DO UPDATE SET
                complexity_score = EXCLUDED.complexity_score,
                model_assigned = EXCLUDED.model_assigned,
                routing_reason = EXCLUDED.routing_reason,
                updated_at = CURRENT_TIMESTAMP
        """
        
        weights = weights or {}
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (
                        fingerprint,
                        complexity_score,
                        model_assigned,
                        routing_reason,
                        weights.get('category', 0),
                        weights.get('name_length', 0),
                        weights.get('price', 0),
                        weights.get('attributes', 0)
                    ))
                    conn.commit()
                    logger.debug(f"📊 Complejidad guardada: {fingerprint[:8]}... = {complexity_score:.2f}")
        except Exception as e:
            logger.error(f"Error guardando complejidad: {e}")
    
    def get_complexity_analysis(self, fingerprint: str) -> Optional[Dict]:
        """Obtener análisis de complejidad"""
        query = """
            SELECT complexity_score, model_assigned, routing_reason,
                   category_weight, name_length_weight, price_weight, 
                   attributes_weight, created_at
            FROM product_complexity_cache
            WHERE fingerprint = %s
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (fingerprint,))
                    return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error obteniendo complejidad: {e}")
            return None
    
    # ============================================================================
    # 🔧 UTILIDADES
    # ============================================================================
    
    def cleanup_old_cache(self, days: int = 30) -> int:
        """Limpiar cache antiguo"""
        queries = [
            # Limpiar semantic_cache
            """
            DELETE FROM semantic_cache
            WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
              AND access_count < 3
            """,
            # Limpiar processing_metrics antiguas
            """
            DELETE FROM processing_metrics
            WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
            """,
            # Limpiar batches fallidos antiguos
            """
            DELETE FROM gpt5_batch_jobs
            WHERE status = 'failed'
              AND created_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
            """
        ]
        
        total_deleted = 0
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    for query in queries:
                        cursor.execute(query, (days,))
                        total_deleted += cursor.rowcount
                    conn.commit()
                    logger.info(f"🧹 Limpieza completada: {total_deleted} registros eliminados")
                    return total_deleted
        except Exception as e:
            logger.error(f"Error en limpieza: {e}")
            return 0
    
    def refresh_materialized_views(self):
        """Refrescar vistas materializadas"""
        views = [
            "mv_products_by_complexity",
            "mv_daily_cost_metrics"
        ]
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    for view in views:
                        cursor.execute(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view}")
                    conn.commit()
                    logger.info(f"📊 Vistas materializadas actualizadas")
        except Exception as e:
            logger.error(f"Error refrescando vistas: {e}")
    
    def get_stats(self) -> Dict:
        """Obtener estadísticas generales del sistema"""
        stats_queries = {
            'total_products_cached': "SELECT COUNT(*) FROM ai_metadata_cache",
            'semantic_cache_size': "SELECT COUNT(*) FROM semantic_cache",
            'pending_batches': "SELECT COUNT(*) FROM gpt5_batch_jobs WHERE status = 'pending'",
            'models_active': "SELECT COUNT(*) FROM model_config WHERE active = TRUE",
            'avg_complexity': "SELECT AVG(complexity_score) FROM product_complexity_cache",
            'cache_hit_rate_7d': """
                SELECT AVG(CASE WHEN cache_hit THEN 1 ELSE 0 END) 
                FROM processing_metrics 
                WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '7 days'
            """
        }
        
        stats = {}
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    for key, query in stats_queries.items():
                        cursor.execute(query)
                        result = cursor.fetchone()
                        stats[key] = result[0] if result and result[0] else 0
                    
                    return stats
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    def close(self):
        """Cerrar pool de conexiones"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("🔌 Pool de conexiones cerrado")

# ============================================================================
# 🎯 CLASE EXTENDIDA PARA CACHE IA
# ============================================================================

class GPT5AICache:
    """Cache IA extendido con soporte GPT-5"""
    
    def __init__(self, connector: GPT5DatabaseConnector):
        self.connector = connector
    
    def get(self, fingerprint: str) -> Optional[Dict]:
        """Obtener del cache IA (compatible con sistema actual)"""
        query = """
            SELECT fingerprint, brand, model, refined_attributes,
                   normalized_name, confidence, category_suggestion,
                   model_used, tokens_used, quality_score, ai_response
            FROM ai_metadata_cache 
            WHERE fingerprint = %s
              AND (ttl_hours = 0 OR 
                   created_at > CURRENT_TIMESTAMP - INTERVAL '1 hour' * ttl_hours)
        """
        
        try:
            with self.connector.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (fingerprint,))
                    result = cursor.fetchone()
                    
                    if result:
                        # Actualizar hits
                        update_query = """
                            UPDATE ai_metadata_cache 
                            SET hits = COALESCE(hits, 0) + 1,
                                last_hit = CURRENT_TIMESTAMP
                            WHERE fingerprint = %s
                        """
                        cursor.execute(update_query, (fingerprint,))
                        conn.commit()
                        
                        return {
                            'brand': result['brand'],
                            'model': result['model'],
                            'refined_attributes': result['refined_attributes'],
                            'normalized_name': result['normalized_name'],
                            'confidence': float(result['confidence']) if result['confidence'] else 0.0,
                            'category_suggestion': result['category_suggestion'],
                            'model_used': result['model_used'],
                            'tokens_used': result['tokens_used'],
                            'quality_score': float(result['quality_score']) if result['quality_score'] else None,
                            'ai_response': result['ai_response']
                        }
                    return None
        except Exception as e:
            logger.error(f"Error obteniendo AI cache: {e}")
            return None
    
    def set(self, fingerprint: str, metadata: Dict, model_used: str = None,
           tokens_used: int = None, quality_score: float = None,
           batch_id: str = None, ttl_hours: int = 168):
        """Guardar en cache IA con metadatos GPT-5"""
        query = """
            INSERT INTO ai_metadata_cache (
                fingerprint, brand, model, refined_attributes,
                normalized_name, confidence, category_suggestion,
                model_used, tokens_used, processing_version, 
                batch_id, quality_score, ttl_hours, ai_response
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (fingerprint) DO UPDATE SET
                brand = EXCLUDED.brand,
                model = EXCLUDED.model,
                refined_attributes = EXCLUDED.refined_attributes,
                normalized_name = EXCLUDED.normalized_name,
                confidence = EXCLUDED.confidence,
                category_suggestion = EXCLUDED.category_suggestion,
                model_used = COALESCE(EXCLUDED.model_used, ai_metadata_cache.model_used),
                tokens_used = COALESCE(EXCLUDED.tokens_used, ai_metadata_cache.tokens_used),
                processing_version = 'v2.0',
                batch_id = COALESCE(EXCLUDED.batch_id, ai_metadata_cache.batch_id),
                quality_score = COALESCE(EXCLUDED.quality_score, ai_metadata_cache.quality_score),
                ttl_hours = EXCLUDED.ttl_hours,
                ai_response = EXCLUDED.ai_response,
                updated_at = CURRENT_TIMESTAMP
        """
        
        try:
            with self.connector.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (
                        fingerprint,
                        metadata.get('brand'),
                        metadata.get('model'),
                        json.dumps(metadata.get('refined_attributes', {})),
                        metadata.get('normalized_name'),
                        metadata.get('confidence', 0.0),
                        metadata.get('category_suggestion'),
                        model_used or metadata.get('model_used'),
                        tokens_used or metadata.get('tokens_used'),
                        'v2.0',  # Nueva versión GPT-5
                        batch_id,
                        quality_score or metadata.get('quality_score'),
                        ttl_hours,
                        json.dumps(metadata) if not metadata.get('ai_response') else json.dumps(metadata.get('ai_response'))
                    ))
                    conn.commit()
                    logger.debug(f"✅ Cache IA GPT-5 guardado: {fingerprint[:8]}...")
                    return True
        except Exception as e:
            logger.error(f"Error guardando AI cache GPT-5: {e}")
            return False

# ============================================================================
# 🎯 MAIN - Testing
# ============================================================================

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test de conexión
    print("🚀 Testing GPT-5 Database Connector...")
    
    connector = GPT5DatabaseConnector(
        host="34.176.197.136",
        port=5432,
        database="postgres",
        user="postgres",
        password="Osmar2503!",
        pool_size=5
    )
    
    # Test 1: Obtener configuración de modelos
    print("\n📊 Configuración de modelos:")
    models = connector.get_model_config()
    if models:
        for model in models:
            print(f"  - {model['model_name']}: ${model['cost_per_1k_input']}/1K input")
    
    # Test 2: Estadísticas del sistema
    print("\n📈 Estadísticas del sistema:")
    stats = connector.get_stats()
    for key, value in stats.items():
        print(f"  - {key}: {value}")
    
    # Test 3: Resumen de costos
    print("\n💰 Resumen de costos (últimos 7 días):")
    cost_summary = connector.get_cost_summary(days=7)
    print(f"  - Total: ${cost_summary.get('total_cost', 0):.4f}")
    print(f"  - Requests: {cost_summary.get('total_requests', 0)}")
    print(f"  - Ahorros por cache: ${cost_summary.get('cache_savings_usd', 0):.4f}")
    
    # Cerrar conexión
    connector.close()
    print("\n✅ Test completado exitosamente")