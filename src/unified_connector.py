#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conector unificado para PostgreSQL
Reemplaza múltiples conectores por uno consistente y seguro
"""

import psycopg2
from psycopg2 import pool, extras
from contextlib import contextmanager
from typing import Dict, List, Any, Optional
import json
from datetime import datetime

from config_manager import get_config

class UnifiedPostgreSQLConnector:
    """
    Conector unificado y seguro para PostgreSQL
    Reemplaza SimplePostgreSQLConnector y otros conectores
    """
    
    def __init__(self):
        self.config = get_config()
        self.connection_pool = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Inicializar pool de conexiones seguro"""
        try:
            conn_params = self.config.get_connection_params()
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                1, self.config.database.pool_size,
                **conn_params
            )
        except Exception as e:
            raise ConnectionError(f"Error inicializando pool de conexiones: {e}")
    
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
    
    def execute_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Ejecutar consulta SELECT"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                cursor.execute(query, params or {})
                return [dict(row) for row in cursor.fetchall()]
    
    def execute_update(self, query: str, params: Dict[str, Any] = None) -> int:
        """Ejecutar INSERT/UPDATE/DELETE"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params or {})
                conn.commit()
                return cursor.rowcount
    
    def get_ai_cache(self, fingerprint: str) -> Optional[Dict[str, Any]]:
        """Obtener entrada de cache IA"""
        query = """
            SELECT metadata, hits 
            FROM ai_metadata_cache 
            WHERE fingerprint = %(fingerprint)s
        """
        results = self.execute_query(query, {'fingerprint': fingerprint})
        
        if results:
            # Incrementar contador de hits
            self.execute_update(
                "UPDATE ai_metadata_cache SET hits = hits + 1 WHERE fingerprint = %(fingerprint)s",
                {'fingerprint': fingerprint}
            )
            return results[0]['metadata']
        return None
    
    def set_ai_cache(self, fingerprint: str, metadata: Dict[str, Any]) -> bool:
        """Guardar entrada en cache IA"""
        try:
            query = """
                INSERT INTO ai_metadata_cache (
                    fingerprint, brand, model, refined_attributes, 
                    normalized_name, confidence, category_suggestion,
                    ai_processing_time, metadata
                ) VALUES (
                    %(fingerprint)s, %(brand)s, %(model)s, %(refined_attributes)s,
                    %(normalized_name)s, %(confidence)s, %(category_suggestion)s,
                    %(ai_processing_time)s, %(metadata)s
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
            
            params = {
                'fingerprint': fingerprint,
                'brand': metadata.get('brand'),
                'model': metadata.get('model'),
                'refined_attributes': json.dumps(metadata.get('refined_attributes', {})),
                'normalized_name': metadata.get('normalized_name'),
                'confidence': metadata.get('confidence', 0.0),
                'category_suggestion': metadata.get('category_suggestion'),
                'ai_processing_time': metadata.get('ai_processing_time', 0.0),
                'metadata': json.dumps(metadata)
            }
            
            self.execute_update(query, params)
            return True
            
        except Exception as e:
            print(f"Error guardando cache IA: {e}")
            return False
    
    def save_normalized_product(self, product: Dict[str, Any]) -> bool:
        """Guardar producto normalizado con validación completa"""
        try:
            print(f"   BD: Guardando producto {product['product_id'][:16]}...")
            
            # 1. Guardar producto maestro
            self._upsert_product_master(product)
            print(f"   BD: OK Producto maestro guardado")
            
            # 2. Guardar precio actual  
            self._upsert_current_price(product)
            print(f"   BD: OK Precio guardado")
            
            # 3. Validación post-inserción
            self._validate_product_integrity(product['product_id'])
            print(f"   BD: OK Integridad verificada")
            
            # 4. Log de procesamiento
            self._log_processing('product_save', 'success', product)
            
            return True
            
        except Exception as e:
            print(f"   BD: ERROR en save_normalized_product: {e}")
            import traceback
            traceback.print_exc()
            self._log_processing('product_save', 'error', {'error': str(e)})
            return False
    
    def _upsert_product_master(self, product: Dict[str, Any]):
        """Insertar/actualizar producto maestro"""
        query = """
            INSERT INTO productos_maestros (
                fingerprint, product_id, name, brand, model, category,
                attributes, ai_enhanced, ai_confidence, processing_version
            ) VALUES (
                %(fingerprint)s, %(product_id)s, %(name)s, %(brand)s, %(model)s, %(category)s,
                %(attributes)s, %(ai_enhanced)s, %(ai_confidence)s, %(processing_version)s
            )
            ON CONFLICT (fingerprint) DO UPDATE SET
                name = EXCLUDED.name,
                brand = EXCLUDED.brand,
                model = EXCLUDED.model,
                category = EXCLUDED.category,
                attributes = EXCLUDED.attributes,
                ai_enhanced = EXCLUDED.ai_enhanced,
                ai_confidence = EXCLUDED.ai_confidence,
                processing_version = EXCLUDED.processing_version,
                updated_at = CURRENT_TIMESTAMP
        """
        
        params = {
            'fingerprint': product['fingerprint'],
            'product_id': product['product_id'],
            'name': product['name'],
            'brand': product['brand'],
            'model': product.get('model'),
            'category': product['category'],
            'attributes': json.dumps(product.get('attributes', {})),
            'ai_enhanced': product.get('ai_enhanced', False),
            'ai_confidence': product.get('ai_confidence', 0.0),
            'processing_version': product.get('processing_version', 'v1.0')
        }
        
        self.execute_update(query, params)
    
    def _upsert_current_price(self, product: Dict[str, Any]):
        """Insertar/actualizar precio actual"""
        # Obtener retailer_id con manejo robusto
        retailer_query = "SELECT id FROM retailers WHERE name = %(retailer)s"
        retailers = self.execute_query(retailer_query, {'retailer': product['retailer']})
        
        if retailers:
            retailer_id = retailers[0]['id']
        else:
            # Si no existe el retailer, crear uno o usar default válido
            print(f"   ADVERTENCIA: Retailer '{product['retailer']}' no encontrado, usando Paris como default")
            retailer_id = 1  # Paris como default
            
            # Verificar que Paris existe
            paris_check = self.execute_query("SELECT id FROM retailers WHERE id = 1")
            if not paris_check:
                raise ValueError(f"Retailer default (Paris) no existe. Retailer solicitado: '{product['retailer']}'")
        
        print(f"   Precio: Usando retailer_id={retailer_id} para '{product['retailer']}'")
        
        query = """
            INSERT INTO precios_actuales (
                fingerprint, retailer_id, product_id, precio_normal, 
                precio_tarjeta, precio_oferta, currency, stock_status, url
            ) VALUES (
                %(fingerprint)s, %(retailer_id)s, %(product_id)s, %(precio_normal)s,
                %(precio_tarjeta)s, %(precio_oferta)s, %(currency)s, %(stock_status)s, %(url)s
            )
            ON CONFLICT (fingerprint, retailer_id) DO UPDATE SET
                product_id = EXCLUDED.product_id,
                precio_normal = EXCLUDED.precio_normal,
                precio_tarjeta = EXCLUDED.precio_tarjeta,
                precio_oferta = EXCLUDED.precio_oferta,
                currency = EXCLUDED.currency,
                stock_status = EXCLUDED.stock_status,
                url = EXCLUDED.url,
                updated_at = CURRENT_TIMESTAMP
        """
        
        params = {
            'fingerprint': product['fingerprint'],
            'retailer_id': retailer_id,
            'product_id': product['product_id'],
            'precio_normal': product.get('price_original'),
            'precio_tarjeta': product.get('price_current'),
            'precio_oferta': None,  # No hay precio oferta en el producto actual
            'currency': product.get('currency', 'CLP'),
            'stock_status': 'available',
            'url': product.get('url')
        }
        
        self.execute_update(query, params)
    
    def _log_processing(self, action: str, status: str, details: Dict[str, Any]):
        """Registrar log de procesamiento"""
        query = """
            INSERT INTO processing_logs (action, status, details)
            VALUES (%(action)s, %(status)s, %(details)s)
        """
        
        params = {
            'action': action,
            'status': status,
            'details': json.dumps(details)
        }
        
        try:
            self.execute_update(query, params)
        except:
            pass  # No fallar por logs
    
    def _validate_product_integrity(self, product_id: str):
        """Validar integridad post-inserción"""
        # Verificar que el producto existe
        product_exists = self.execute_query(
            "SELECT COUNT(*) as count FROM productos_maestros WHERE product_id = %(product_id)s AND active = true",
            {'product_id': product_id}
        )[0]['count'] > 0
        
        # Verificar que el precio existe  
        price_exists = self.execute_query(
            "SELECT COUNT(*) as count FROM precios_actuales WHERE product_id = %(product_id)s",
            {'product_id': product_id}
        )[0]['count'] > 0
        
        if not product_exists:
            raise ValueError(f"Producto {product_id} no se insertó correctamente")
        
        if not price_exists:
            raise ValueError(f"Precio para producto {product_id} no se insertó correctamente")
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de procesamiento"""
        stats = {}
        
        # Contar productos maestros
        result = self.execute_query("SELECT COUNT(*) as count FROM productos_maestros WHERE active = true")
        stats['productos_maestros'] = result[0]['count']
        
        # Contar precios actuales
        result = self.execute_query("SELECT COUNT(*) as count FROM precios_actuales")
        stats['precios_actuales'] = result[0]['count']
        
        # Contar cache IA
        result = self.execute_query("SELECT COUNT(*) as count FROM ai_metadata_cache")
        stats['cache_ia'] = result[0]['count']
        
        return stats
    
    def close(self):
        """Cerrar pool de conexiones"""
        if self.connection_pool:
            self.connection_pool.closeall()

# Cache de instancia singleton
_unified_connector: Optional[UnifiedPostgreSQLConnector] = None

def get_unified_connector() -> UnifiedPostgreSQLConnector:
    """Obtener instancia singleton del conector unificado"""
    global _unified_connector
    if _unified_connector is None:
        _unified_connector = UnifiedPostgreSQLConnector()
    return _unified_connector