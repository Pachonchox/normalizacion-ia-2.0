#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
💾 Sistema de Persistencia Completa Base de Datos
Maneja guardado de productos maestros, precios y metadatos en PostgreSQL
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from simple_db_connector import SimplePostgreSQLConnector

class DatabasePersistence:
    """Sistema completo de persistencia en base de datos"""
    
    def __init__(self, connector: SimplePostgreSQLConnector):
        self.connector = connector
    
    def save_normalized_product(self, product: Dict[str, Any]) -> bool:
        """
        Guardar producto normalizado completo en BD
        Maneja productos_maestros y precios_actuales
        """
        
        try:
            with self.connector.get_connection() as conn:
                with conn.cursor() as cursor:
                    # 1. Guardar/actualizar producto maestro
                    self._upsert_product_master(cursor, product)
                    
                    # 2. Guardar/actualizar precios actuales
                    self._upsert_current_prices(cursor, product)
                    
                    # 3. Log de procesamiento
                    self._log_processing(cursor, 'product_save', 'success', product)
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            print(f"ERROR guardando producto en BD: {e}")
            return False
    
    def _upsert_product_master(self, cursor, product: Dict[str, Any]):
        """Insertar/actualizar en productos_maestros"""
        
        query = """
            INSERT INTO productos_maestros (
                fingerprint, product_id, name, brand, model, category,
                attributes, ai_enhanced, ai_confidence, processing_version, active
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
        
        cursor.execute(query, (
            product.get('fingerprint'),
            product.get('product_id'),
            product.get('name'),
            product.get('brand'),
            product.get('model'),
            product.get('category'),
            json.dumps(product.get('attributes', {})),
            product.get('ai_enhanced', False),
            product.get('ai_confidence', 0.0),
            product.get('processing_version', 'v1.1'),
            True  # active
        ))
    
    def _upsert_current_prices(self, cursor, product: Dict[str, Any]):
        """Insertar/actualizar en precios_actuales"""
        
        # Obtener retailer_id
        retailer_id = self._get_retailer_id(cursor, product.get('retailer'))
        
        # Determinar tipos de precio
        price_current = product.get('price_current', 0)
        price_original = product.get('price_original')
        
        # Mapear precios según contexto (simplificado)
        precio_normal = price_original or price_current
        precio_tarjeta = price_current if price_original else None
        precio_oferta = None  # Se detectará en actualizaciones futuras
        
        query = """
            INSERT INTO precios_actuales (
                fingerprint, retailer_id, product_id,
                precio_normal, precio_tarjeta, precio_oferta,
                currency, stock_status, url, metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (fingerprint, retailer_id) DO UPDATE SET
                precio_normal = EXCLUDED.precio_normal,
                precio_tarjeta = EXCLUDED.precio_tarjeta,
                precio_oferta = EXCLUDED.precio_oferta,
                currency = EXCLUDED.currency,
                stock_status = EXCLUDED.stock_status,
                url = EXCLUDED.url,
                metadata = EXCLUDED.metadata,
                ultima_actualizacion = CURRENT_TIMESTAMP
        """
        
        metadata = {
            'source': product.get('source', {}),
            'processing_timestamp': datetime.now().isoformat(),
            'ai_enhanced': product.get('ai_enhanced', False)
        }
        
        cursor.execute(query, (
            product.get('fingerprint'),
            retailer_id,
            product.get('product_id'),
            precio_normal,
            precio_tarjeta,
            precio_oferta,
            product.get('currency', 'CLP'),
            'available',  # stock_status por defecto
            product.get('url'),
            json.dumps(metadata)
        ))
    
    def _get_retailer_id(self, cursor, retailer_name: str) -> int:
        """Obtener o crear retailer_id"""
        
        if not retailer_name:
            retailer_name = 'Unknown'
        
        # Buscar existente
        cursor.execute("SELECT id FROM retailers WHERE name = %s", (retailer_name,))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
        # Crear nuevo retailer
        cursor.execute("""
            INSERT INTO retailers (name, active) 
            VALUES (%s, %s) 
            RETURNING id
        """, (retailer_name, True))
        
        return cursor.fetchone()[0]
    
    def _log_processing(self, cursor, operation: str, status: str, product: Dict[str, Any]):
        """Log de operación de procesamiento"""
        
        metadata = {
            'product_id': product.get('product_id'),
            'fingerprint': product.get('fingerprint'),
            'retailer': product.get('retailer'),
            'category': product.get('category'),
            'ai_enhanced': product.get('ai_enhanced', False)
        }
        
        cursor.execute("""
            INSERT INTO processing_logs (
                module_name, operation, status, affected_records, metadata
            ) VALUES (%s, %s, %s, %s, %s)
        """, ('db_persistence', operation, status, 1, json.dumps(metadata)))
    
    def get_existing_product(self, fingerprint: str) -> Optional[Dict[str, Any]]:
        """Obtener producto existente por fingerprint"""
        
        try:
            with self.connector.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT pm.*, pa.precio_normal, pa.precio_tarjeta, pa.precio_oferta
                        FROM productos_maestros pm
                        LEFT JOIN precios_actuales pa ON pm.fingerprint = pa.fingerprint
                        WHERE pm.fingerprint = %s AND pm.active = true
                        LIMIT 1
                    """, (fingerprint,))
                    
                    result = cursor.fetchone()
                    
                    if result:
                        return {
                            'id': result[0],
                            'fingerprint': result[1],
                            'product_id': result[2],
                            'name': result[3],
                            'brand': result[4],
                            'model': result[5],
                            'category': result[6],
                            'attributes': result[7],
                            'ai_enhanced': result[8],
                            'ai_confidence': result[9],
                            'precio_normal': result[13] if len(result) > 13 else None,
                            'precio_tarjeta': result[14] if len(result) > 14 else None,
                            'precio_oferta': result[15] if len(result) > 15 else None
                        }
                        
        except Exception as e:
            print(f"ERROR obteniendo producto existente: {e}")
        
        return None
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de procesamiento"""
        
        try:
            with self.connector.get_connection() as conn:
                with conn.cursor() as cursor:
                    stats = {}
                    
                    # Productos maestros
                    cursor.execute("SELECT COUNT(*) FROM productos_maestros WHERE active = true")
                    stats['productos_maestros'] = cursor.fetchone()[0]
                    
                    # Precios actuales
                    cursor.execute("SELECT COUNT(*) FROM precios_actuales")
                    stats['precios_actuales'] = cursor.fetchone()[0]
                    
                    # Productos con IA
                    cursor.execute("SELECT COUNT(*) FROM productos_maestros WHERE ai_enhanced = true AND active = true")
                    stats['productos_ai_enhanced'] = cursor.fetchone()[0]
                    
                    # Retailers activos
                    cursor.execute("SELECT COUNT(*) FROM retailers WHERE active = true")
                    stats['retailers_activos'] = cursor.fetchone()[0]
                    
                    # Categorías
                    cursor.execute("SELECT COUNT(*) FROM categories WHERE active = true")
                    stats['categorias'] = cursor.fetchone()[0]
                    
                    # Logs recientes (últimas 24h)
                    cursor.execute("""
                        SELECT COUNT(*) FROM processing_logs 
                        WHERE created_at > NOW() - INTERVAL '24 hours'
                    """)
                    stats['logs_24h'] = cursor.fetchone()[0]
                    
                    return stats
                    
        except Exception as e:
            print(f"ERROR obteniendo estadísticas: {e}")
            return {}
    
    def batch_save_products(self, products: List[Dict[str, Any]]) -> Dict[str, int]:
        """Guardar múltiples productos en lote (más eficiente)"""
        
        results = {
            'success': 0,
            'errors': 0,
            'skipped': 0
        }
        
        for product in products:
            if self.save_normalized_product(product):
                results['success'] += 1
            else:
                results['errors'] += 1
        
        return results

def get_persistence_instance() -> DatabasePersistence:
    """Factory para obtener instancia de persistencia"""
    
    connector = SimplePostgreSQLConnector(
        host="34.176.197.136",
        port=5432,
        database="postgres",
        user="postgres",
        password="Osmar2503!",
        pool_size=5
    )
    
    return DatabasePersistence(connector)

if __name__ == "__main__":
    # Test de persistencia
    print("=== TEST PERSISTENCIA BD ===")
    
    persistence = get_persistence_instance()
    
    # Producto de prueba
    test_product = {
        'fingerprint': 'test_fingerprint_123',
        'product_id': 'test_product_456',
        'name': 'Producto de Prueba TEST',
        'brand': 'TEST BRAND',
        'model': 'Test Model v1.0',
        'category': 'others',
        'retailer': 'Test Store',
        'price_current': 99990,
        'price_original': 119990,
        'currency': 'CLP',
        'url': 'https://test.com/product',
        'attributes': {
            'test_attr': 'test_value',
            'capacity': '256GB'
        },
        'ai_enhanced': True,
        'ai_confidence': 0.85,
        'processing_version': 'v1.1',
        'source': {
            'test': True,
            'origin': 'test_script'
        }
    }
    
    # Guardar producto
    success = persistence.save_normalized_product(test_product)
    print(f"Guardado de producto: {'EXITOSO' if success else 'FALLIDO'}")
    
    # Obtener estadísticas
    stats = persistence.get_processing_stats()
    print("\\nEstadísticas de BD:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")