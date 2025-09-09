#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 Conector Simple PostgreSQL 
Conector simplificado para conexiones directas a PostgreSQL
"""

import psycopg2
from psycopg2 import pool
import json
import logging
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class SimplePostgreSQLConnector:
    """Conector simplificado para PostgreSQL directo"""
    
    def __init__(self, host: str, port: int, database: str, user: str, password: str, pool_size: int = 5):
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
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                1, self.pool_size,
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            logger.info(f"Pool de conexiones PostgreSQL inicializado: {self.host}:{self.port}/{self.database}")
        except Exception as e:
            logger.error(f"Error inicializando pool: {e}")
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
    
    def get_ai_cache(self, fingerprint: str) -> Optional[Dict]:
        """Obtener metadata IA desde el cache en BD"""
        query = """
            SELECT fingerprint, brand, model, refined_attributes,
                   normalized_name, confidence, category_suggestion
            FROM ai_metadata_cache 
            WHERE fingerprint = %s
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (fingerprint,))
                    result = cursor.fetchone()
                    
                    if result:
                        # Convertir resultado a formato esperado
                        refined_attrs = result[3]
                        if isinstance(refined_attrs, str):
                            refined_attrs = json.loads(refined_attrs) if refined_attrs else {}
                        elif refined_attrs is None:
                            refined_attrs = {}
                        
                        return {
                            'brand': result[1],
                            'model': result[2],
                            'refined_attributes': refined_attrs,
                            'normalized_name': result[4],
                            'confidence': float(result[5]) if result[5] else 0.0,
                            'category_suggestion': result[6]
                        }
                    return None
        except Exception as e:
            logger.error(f"Error obteniendo AI cache: {e}")
            return None
    
    def set_ai_cache(self, fingerprint: str, metadata: Dict) -> bool:
        """Guardar metadata IA en el cache de BD"""
        query = """
            INSERT INTO ai_metadata_cache (
                fingerprint, brand, model, refined_attributes,
                normalized_name, confidence, category_suggestion
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (fingerprint) DO UPDATE SET
                brand = EXCLUDED.brand,
                model = EXCLUDED.model,
                refined_attributes = EXCLUDED.refined_attributes,
                normalized_name = EXCLUDED.normalized_name,
                confidence = EXCLUDED.confidence,
                category_suggestion = EXCLUDED.category_suggestion,
                updated_at = CURRENT_TIMESTAMP
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (
                        fingerprint,
                        metadata.get('brand'),
                        metadata.get('model'),
                        json.dumps(metadata.get('refined_attributes', {})),
                        metadata.get('normalized_name'),
                        metadata.get('confidence', 0.0),
                        metadata.get('category_suggestion')
                    ))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error guardando AI cache: {e}")
            return False

class SimpleDatabaseCache:
    """Clase wrapper simple para cache de base de datos"""
    
    def __init__(self, connector: SimplePostgreSQLConnector):
        self.connector = connector
    
    def get(self, fingerprint: str) -> Optional[Dict]:
        """Obtener del cache"""
        return self.connector.get_ai_cache(fingerprint)
    
    def set(self, fingerprint: str, metadata: Dict) -> bool:
        """Guardar en cache"""
        return self.connector.set_ai_cache(fingerprint, metadata)