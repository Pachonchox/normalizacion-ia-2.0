"""
Módulo de Migración de Archivos JSON a Google Cloud SQL
Sistema de Análisis de Precios Retail Chile
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
import shutil
from tqdm import tqdm
import hashlib

from googlecloudsqlconnector import CloudSQLConnector, CloudSQLConfig, DatabaseCache

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RetailDataMigration:
    """
    Migración completa de archivos JSON del pipeline retail a Cloud SQL
    """
    
    def __init__(self, connector: CloudSQLConnector, backup_dir: str = "backups"):
        self.connector = connector
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.migration_stats = {
            'categories': {'total': 0, 'migrated': 0, 'errors': 0},
            'brands': {'total': 0, 'migrated': 0, 'errors': 0},
            'ai_cache': {'total': 0, 'migrated': 0, 'errors': 0},
            'products': {'total': 0, 'migrated': 0, 'errors': 0}
        }
        
    def backup_file(self, file_path: str) -> str:
        """
        Crear backup del archivo antes de migrar
        """
        file_path = Path(file_path)
        if not file_path.exists():
            logger.warning(f"Archivo no encontrado para backup: {file_path}")
            return ""
        
        # Crear nombre de backup con timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = self.backup_dir / backup_name
        
        # Copiar archivo
        shutil.copy2(file_path, backup_path)
        logger.info(f"✅ Backup creado: {backup_path}")
        
        return str(backup_path)
    
    def migrate_taxonomy(self, taxonomy_file: str = "configs/taxonomy_v1.json") -> Tuple[int, int]:
        """
        Migrar taxonomías desde archivo JSON a tabla categories
        
        Args:
            taxonomy_file: Ruta al archivo taxonomy_v1.json
            
        Returns:
            Tuple de (categorías migradas, errores)
        """
        logger.info("🔄 Iniciando migración de taxonomías...")
        
        # Backup del archivo
        self.backup_file(taxonomy_file)
        
        try:
            with open(taxonomy_file, 'r', encoding='utf-8') as f:
                taxonomy_data = json.load(f)
            
            version = taxonomy_data.get('version', '1.0')
            nodes = taxonomy_data.get('nodes', [])
            
            self.migration_stats['categories']['total'] = len(nodes)
            
            migrated = 0
            errors = 0
            
            for node in tqdm(nodes, desc="Migrando categorías"):
                try:
                    # Preparar datos para inserción
                    category_data = {
                        'category_id': node.get('id'),
                        'name': node.get('name'),
                        'synonyms': node.get('synonyms', []),
                        'parent_category': node.get('parent_category'),
                        'attributes_schema': node.get('attributes_schema', []),
                        'version': version,
                        'metadata': json.dumps(node.get('metadata', {}))
                    }
                    
                    # Insertar en BD
                    query = """
                        INSERT INTO categories (
                            category_id, name, synonyms, parent_category,
                            attributes_schema, version, metadata
                        ) VALUES (
                            :category_id, :name, :synonyms, :parent_category,
                            :attributes_schema, :version, :metadata::jsonb
                        )
                        ON CONFLICT (category_id) DO UPDATE SET
                            name = EXCLUDED.name,
                            synonyms = EXCLUDED.synonyms,
                            parent_category = EXCLUDED.parent_category,
                            attributes_schema = EXCLUDED.attributes_schema,
                            version = EXCLUDED.version,
                            metadata = EXCLUDED.metadata,
                            updated_at = CURRENT_TIMESTAMP
                    """
                    
                    self.connector.execute_update(query, category_data)
                    migrated += 1
                    
                    # Migrar esquema de atributos si existe
                    if node.get('attributes_schema'):
                        self._migrate_attributes_schema(
                            node['id'], 
                            node['attributes_schema']
                        )
                    
                except Exception as e:
                    logger.error(f"Error migrando categoría {node.get('id')}: {e}")
                    errors += 1
            
            self.migration_stats['categories']['migrated'] = migrated
            self.migration_stats['categories']['errors'] = errors
            
            # Log en BD
            self.connector.log_processing(
                module='migration',
                operation='migrate_taxonomy',
                status='success' if errors == 0 else 'warning',
                affected_records=migrated,
                metadata={'version': version, 'errors': errors}
            )
            
            logger.info(f"✅ Taxonomías migradas: {migrated}/{len(nodes)} (Errores: {errors})")
            return migrated, errors
            
        except Exception as e:
            logger.error(f"❌ Error crítico en migración de taxonomías: {e}")
            self.connector.log_processing(
                module='migration',
                operation='migrate_taxonomy',
                status='error',
                error=str(e)
            )
            return 0, 1
    
    def _migrate_attributes_schema(self, category_id: str, attributes: List[str]):
        """
        Migrar esquema de atributos para una categoría
        """
        for idx, attr in enumerate(attributes):
            try:
                query = """
                    INSERT INTO attributes_schema (
                        category_id, attribute_name, attribute_type,
                        required, display_order
                    ) VALUES (
                        :category_id, :attribute_name, :attribute_type,
                        :required, :display_order
                    )
                    ON CONFLICT (category_id, attribute_name) DO UPDATE SET
                        display_order = EXCLUDED.display_order
                """
                
                self.connector.execute_update(query, {
                    'category_id': category_id,
                    'attribute_name': attr,
                    'attribute_type': 'string',  # Por defecto
                    'required': False,
                    'display_order': idx
                })
            except Exception as e:
                logger.warning(f"Error migrando atributo {attr} para {category_id}: {e}")
    
    def migrate_brands(self, brands_file: str = "configs/brand_aliases.json") -> Tuple[int, int]:
        """
        Migrar marcas y aliases desde archivo JSON a tabla brands
        
        Args:
            brands_file: Ruta al archivo brand_aliases.json
            
        Returns:
            Tuple de (marcas migradas, errores)
        """
        logger.info("🔄 Iniciando migración de marcas...")
        
        # Backup del archivo
        self.backup_file(brands_file)
        
        try:
            with open(brands_file, 'r', encoding='utf-8') as f:
                brands_data = json.load(f)
            
            self.migration_stats['brands']['total'] = len(brands_data)
            
            migrated = 0
            errors = 0
            
            for brand_canonical, aliases in tqdm(brands_data.items(), desc="Migrando marcas"):
                try:
                    # Asegurar que la marca canónica esté en los aliases
                    if brand_canonical not in aliases:
                        aliases.append(brand_canonical)
                    
                    query = """
                        INSERT INTO brands (
                            brand_canonical, aliases, active
                        ) VALUES (
                            :brand_canonical, :aliases, TRUE
                        )
                        ON CONFLICT (brand_canonical) DO UPDATE SET
                            aliases = EXCLUDED.aliases,
                            updated_at = CURRENT_TIMESTAMP
                    """
                    
                    self.connector.execute_update(query, {
                        'brand_canonical': brand_canonical,
                        'aliases': aliases
                    })
                    
                    migrated += 1
                    
                except Exception as e:
                    logger.error(f"Error migrando marca {brand_canonical}: {e}")
                    errors += 1
            
            self.migration_stats['brands']['migrated'] = migrated
            self.migration_stats['brands']['errors'] = errors
            
            # Log en BD
            self.connector.log_processing(
                module='migration',
                operation='migrate_brands',
                status='success' if errors == 0 else 'warning',
                affected_records=migrated,
                metadata={'errors': errors}
            )
            
            logger.info(f"✅ Marcas migradas: {migrated}/{len(brands_data)} (Errores: {errors})")
            return migrated, errors
            
        except Exception as e:
            logger.error(f"❌ Error crítico en migración de marcas: {e}")
            self.connector.log_processing(
                module='migration',
                operation='migrate_brands',
                status='error',
                error=str(e)
            )
            return 0, 1
    
    def migrate_ai_cache(self, cache_file: str = "out/ai_metadata_cache.json") -> Tuple[int, int]:
        """
        Migrar cache IA desde archivo JSON a tabla ai_metadata_cache
        
        Args:
            cache_file: Ruta al archivo ai_metadata_cache.json
            
        Returns:
            Tuple de (registros migrados, errores)
        """
        logger.info("🔄 Iniciando migración de cache IA...")
        
        # Backup del archivo
        self.backup_file(cache_file)
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            self.migration_stats['ai_cache']['total'] = len(cache_data)
            
            migrated = 0
            errors = 0
            
            # Preparar datos para inserción masiva
            batch_data = []
            
            for fingerprint, metadata in tqdm(cache_data.items(), desc="Migrando cache IA"):
                try:
                    # Validar y limpiar datos
                    cache_entry = {
                        'fingerprint': fingerprint,
                        'brand': metadata.get('brand'),
                        'model': metadata.get('model'),
                        'refined_attributes': json.dumps(metadata.get('refined_attributes', {})),
                        'normalized_name': metadata.get('normalized_name'),
                        'confidence': float(metadata.get('confidence', 0.0)),
                        'category_suggestion': metadata.get('category_suggestion'),
                        'ai_processing_time': float(metadata.get('ai_processing_time', 0.0)),
                        'metadata': json.dumps({
                            'created_at': metadata.get('created_at'),
                            'source': 'migration'
                        })
                    }
                    
                    batch_data.append(cache_entry)
                    
                    # Insertar en lotes de 100
                    if len(batch_data) >= 100:
                        self._insert_cache_batch(batch_data)
                        migrated += len(batch_data)
                        batch_data = []
                    
                except Exception as e:
                    logger.error(f"Error procesando cache para {fingerprint}: {e}")
                    errors += 1
            
            # Insertar registros restantes
            if batch_data:
                self._insert_cache_batch(batch_data)
                migrated += len(batch_data)
            
            self.migration_stats['ai_cache']['migrated'] = migrated
            self.migration_stats['ai_cache']['errors'] = errors
            
            # Log en BD
            self.connector.log_processing(
                module='migration',
                operation='migrate_ai_cache',
                status='success' if errors == 0 else 'warning',
                affected_records=migrated,
                metadata={'errors': errors, 'total_entries': len(cache_data)}
            )
            
            logger.info(f"✅ Cache IA migrado: {migrated}/{len(cache_data)} (Errores: {errors})")
            return migrated, errors
            
        except Exception as e:
            logger.error(f"❌ Error crítico en migración de cache IA: {e}")
            self.connector.log_processing(
                module='migration',
                operation='migrate_ai_cache',
                status='error',
                error=str(e)
            )
            return 0, 1
    
    def _insert_cache_batch(self, batch_data: List[Dict]):
        """
        Insertar lote de registros de cache
        """
        if not batch_data:
            return
        
        try:
            # Usar inserción masiva con ON CONFLICT
            on_conflict = """
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
            
            self.connector.bulk_insert('ai_metadata_cache', batch_data, on_conflict)
            
        except Exception as e:
            logger.error(f"Error insertando batch de cache: {e}")
            # Intentar insertar uno por uno si falla el batch
            for entry in batch_data:
                try:
                    self.connector.set_ai_cache(entry['fingerprint'], entry)
                except Exception as e2:
                    logger.error(f"Error insertando cache individual {entry['fingerprint']}: {e2}")
    
    def migrate_products_from_jsonl(self, jsonl_file: str = "out/products_normalized.jsonl") -> Tuple[int, int]:
        """
        Migrar productos desde archivo JSONL a tablas de productos y precios
        
        Args:
            jsonl_file: Ruta al archivo products_normalized.jsonl
            
        Returns:
            Tuple de (productos migrados, errores)
        """
        logger.info("🔄 Iniciando migración de productos...")
        
        if not Path(jsonl_file).exists():
            logger.warning(f"Archivo {jsonl_file} no encontrado")
            return 0, 0
        
        # Backup del archivo
        self.backup_file(jsonl_file)
        
        migrated = 0
        errors = 0
        
        # Obtener mapeo de retailers
        retailers = self._get_retailers_map()
        
        try:
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            self.migration_stats['products']['total'] = len(lines)
            
            for line in tqdm(lines, desc="Migrando productos"):
                try:
                    product = json.loads(line)
                    
                    # Migrar a productos_maestros
                    self._migrate_product_master(product)
                    
                    # Migrar a precios_actuales
                    retailer_id = retailers.get(product.get('retailer'), 1)
                    self._migrate_current_price(product, retailer_id)
                    
                    migrated += 1
                    
                except Exception as e:
                    logger.error(f"Error migrando producto: {e}")
                    errors += 1
            
            self.migration_stats['products']['migrated'] = migrated
            self.migration_stats['products']['errors'] = errors
            
            # Log en BD
            self.connector.log_processing(
                module='migration',
                operation='migrate_products',
                status='success' if errors == 0 else 'warning',
                affected_records=migrated,
                metadata={'source_file': jsonl_file, 'errors': errors}
            )
            
            logger.info(f"✅ Productos migrados: {migrated}/{len(lines)} (Errores: {errors})")
            return migrated, errors
            
        except Exception as e:
            logger.error(f"❌ Error crítico en migración de productos: {e}")
            self.connector.log_processing(
                module='migration',
                operation='migrate_products',
                status='error',
                error=str(e)
            )
            return 0, 1
    
    def _get_retailers_map(self) -> Dict[str, int]:
        """
        Obtener mapeo de nombres de retailers a IDs
        """
        query = "SELECT id, name FROM retailers"
        results = self.connector.execute_query(query)
        return {r['name']: r['id'] for r in results}
    
    def _migrate_product_master(self, product: Dict):
        """
        Migrar producto a tabla productos_maestros
        """
        query = """
            INSERT INTO productos_maestros (
                fingerprint, product_id, name, brand, model,
                category, attributes, ai_enhanced, ai_confidence,
                processing_version
            ) VALUES (
                :fingerprint, :product_id, :name, :brand, :model,
                :category, :attributes::jsonb, :ai_enhanced, :ai_confidence,
                :processing_version
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
        
        self.connector.execute_update(query, {
            'fingerprint': product.get('fingerprint'),
            'product_id': product.get('product_id'),
            'name': product.get('name'),
            'brand': product.get('brand'),
            'model': product.get('model'),
            'category': product.get('category'),
            'attributes': json.dumps(product.get('attributes', {})),
            'ai_enhanced': product.get('ai_enhanced', False),
            'ai_confidence': product.get('ai_confidence', 0.0),
            'processing_version': product.get('processing_version', 'v1.0')
        })
    
    def _migrate_current_price(self, product: Dict, retailer_id: int):
        """
        Migrar precio actual del producto
        """
        price_data = {
            'fingerprint': product.get('fingerprint'),
            'retailer_id': retailer_id,
            'product_id': product.get('product_id'),
            'precio_normal': product.get('price_original'),
            'precio_tarjeta': product.get('price_current'),
            'precio_oferta': product.get('precio_oferta'),
            'currency': product.get('currency', 'CLP'),
            'stock_status': 'available',
            'url': product.get('source', {}).get('url', ''),
            'metadata': product.get('source', {}).get('metadata', {})
        }
        
        self.connector.upsert_price(price_data)
    
    def validate_migration(self) -> Dict[str, Any]:
        """
        Validar integridad de la migración
        """
        logger.info("🔍 Validando migración...")
        
        validation_results = {}
        
        # Validar categorías
        query = "SELECT COUNT(*) as count FROM categories"
        result = self.connector.execute_query(query)
        validation_results['categories_in_db'] = result[0]['count']
        
        # Validar marcas
        query = "SELECT COUNT(*) as count FROM brands"
        result = self.connector.execute_query(query)
        validation_results['brands_in_db'] = result[0]['count']
        
        # Validar cache IA
        query = "SELECT COUNT(*) as count FROM ai_metadata_cache"
        result = self.connector.execute_query(query)
        validation_results['ai_cache_in_db'] = result[0]['count']
        
        # Validar productos
        query = "SELECT COUNT(*) as count FROM productos_maestros"
        result = self.connector.execute_query(query)
        validation_results['products_in_db'] = result[0]['count']
        
        # Validar precios
        query = "SELECT COUNT(*) as count FROM precios_actuales"
        result = self.connector.execute_query(query)
        validation_results['prices_in_db'] = result[0]['count']
        
        # Comparar con estadísticas de migración
        validation_results['migration_stats'] = self.migration_stats
        
        # Determinar si la migración fue exitosa
        total_errors = sum(stat['errors'] for stat in self.migration_stats.values())
        validation_results['success'] = total_errors == 0
        validation_results['total_errors'] = total_errors
        
        # Log de validación
        self.connector.log_processing(
            module='migration',
            operation='validate_migration',
            status='success' if validation_results['success'] else 'warning',
            metadata=validation_results
        )
        
        return validation_results
    
    def rollback_migration(self, restore_from_backup: bool = False, confirm_rollback: bool = False):
        """
        Rollback de la migración con protección de confirmación
        """
        if not confirm_rollback and not os.getenv('ALLOW_ROLLBACK', '').lower() == 'true':
            logger.error("❌ ROLLBACK BLOQUEADO: Debe confirmar explícitamente con confirm_rollback=True o ALLOW_ROLLBACK=true")
            return
            
        logger.warning("⚠️ Iniciando rollback de migración...")
        
        try:
            # Limpiar tablas en orden inverso de dependencias
            tables_to_clean = [
                'processing_logs',
                'price_alerts',
                'precios_historicos',
                'precios_actuales',
                'ai_metadata_cache',
                'attributes_schema',
                'categories',
                'brands',
                'productos_maestros'
            ]
            
            for table in tables_to_clean:
                try:
                    query = f"TRUNCATE TABLE {table} CASCADE"
                    self.connector.execute_update(query)
                    logger.info(f"✅ Tabla {table} limpiada")
                except Exception as e:
                    logger.error(f"Error limpiando tabla {table}: {e}")
            
            if restore_from_backup:
                # Restaurar archivos desde backup
                logger.info("Restaurando archivos desde backup...")
                # Implementar lógica de restauración si es necesario
            
            logger.info("✅ Rollback completado")
            
        except Exception as e:
            logger.error(f"❌ Error en rollback: {e}")
    
    def run_full_migration(self, 
                          taxonomy_file: str = "configs/taxonomy_v1.json",
                          brands_file: str = "configs/brand_aliases.json",
                          cache_file: str = "out/ai_metadata_cache.json",
                          products_file: str = "out/products_normalized.jsonl") -> Dict[str, Any]:
        """
        Ejecutar migración completa de todos los archivos
        """
        logger.info("=" * 50)
        logger.info("🚀 INICIANDO MIGRACIÓN COMPLETA")
        logger.info("=" * 50)
        
        results = {
            'start_time': datetime.now(),
            'components': {}
        }
        
        # 1. Migrar taxonomías
        if Path(taxonomy_file).exists():
            migrated, errors = self.migrate_taxonomy(taxonomy_file)
            results['components']['taxonomy'] = {
                'migrated': migrated, 
                'errors': errors
            }
        
        # 2. Migrar marcas
        if Path(brands_file).exists():
            migrated, errors = self.migrate_brands(brands_file)
            results['components']['brands'] = {
                'migrated': migrated,
                'errors': errors
            }
        
        # 3. Migrar cache IA
        if Path(cache_file).exists():
            migrated, errors = self.migrate_ai_cache(cache_file)
            results['components']['ai_cache'] = {
                'migrated': migrated,
                'errors': errors
            }
        
        # 4. Migrar productos
        if Path(products_file).exists():
            migrated, errors = self.migrate_products_from_jsonl(products_file)
            results['components']['products'] = {
                'migrated': migrated,
                'errors': errors
            }
        
        # 5. Validar migración
        validation = self.validate_migration()
        results['validation'] = validation
        
        # 6. Refrescar vistas materializadas
        self.connector.refresh_materialized_views()
        
        results['end_time'] = datetime.now()
        results['duration'] = (results['end_time'] - results['start_time']).total_seconds()
        
        # Resumen final
        logger.info("=" * 50)
        logger.info("📊 RESUMEN DE MIGRACIÓN")
        logger.info("=" * 50)
        
        for component, stats in results['components'].items():
            logger.info(f"{component}: {stats['migrated']} migrados, {stats['errors']} errores")
        
        logger.info(f"Duración total: {results['duration']:.2f} segundos")
        logger.info(f"Estado: {'✅ EXITOSA' if validation['success'] else '⚠️ CON ERRORES'}")
        
        return results


# CLI para migración
def main():
    """
    CLI para ejecutar migración
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Migración de datos retail a Cloud SQL')
    parser.add_argument('--config', default='config.local.toml', help='Archivo de configuración')
    parser.add_argument('--taxonomy', default='configs/taxonomy_v1.json', help='Archivo de taxonomías')
    parser.add_argument('--brands', default='configs/brand_aliases.json', help='Archivo de marcas')
    parser.add_argument('--cache', default='out/ai_metadata_cache.json', help='Archivo de cache IA')
    parser.add_argument('--products', default='out/products_normalized.jsonl', help='Archivo de productos')
    parser.add_argument('--rollback', action='store_true', help='Hacer rollback de la migración')
    parser.add_argument('--validate-only', action='store_true', help='Solo validar sin migrar')
    
    args = parser.parse_args()
    
    # Crear conector
    from googlecloudsqlconnector import create_connector_from_config
    connector = create_connector_from_config(args.config)
    
    # Crear migrador
    migrator = RetailDataMigration(connector)
    
    try:
        if args.rollback:
            # Ejecutar rollback
            migrator.rollback_migration()
            
        elif args.validate_only:
            # Solo validar
            validation = migrator.validate_migration()
            print(json.dumps(validation, indent=2))
            
        else:
            # Ejecutar migración completa
            results = migrator.run_full_migration(
                taxonomy_file=args.taxonomy,
                brands_file=args.brands,
                cache_file=args.cache,
                products_file=args.products
            )
            
            # Guardar reporte
            report_file = f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"📄 Reporte guardado en: {report_file}")
            
    finally:
        connector.close()


if __name__ == "__main__":
    main()