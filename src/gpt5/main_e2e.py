#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Sistema E2E GPT-5 - Orquestador Principal
Pipeline completo con todos los componentes integrados
"""

import asyncio
import logging
import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import sys

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Imports del sistema
from normalize_gpt5 import (
    normalize_with_gpt5, 
    process_batch_gpt5,
    ProcessingMode,
    get_gpt5_connector,
    get_router,
    get_prompt_manager,
    get_validator,
    get_l1_cache,
    get_rate_limiter
)
from gpt5.batch_processor_db import BatchOrchestrator
from gpt5_db_connector import GPT5DatabaseConnector
from ingest import ingest_from_dir
from persistence import persist_jsonl

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('gpt5_e2e.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class GPT5Pipeline:
    """Pipeline E2E completo con GPT-5"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Inicializar pipeline
        
        Args:
            config: Configuración personalizada
        """
        self.config = config or self._default_config()
        
        # Inicializar componentes
        self.db = get_gpt5_connector()
        self.router = get_router()
        self.prompt_manager = get_prompt_manager()
        self.validator = get_validator()
        self.l1_cache = get_l1_cache()
        self.rate_limiter = get_rate_limiter()
        
        # Estadísticas
        self.stats = {
            'total_products': 0,
            'processed': 0,
            'cache_hits': 0,
            'errors': 0,
            'cost_usd': 0.0,
            'start_time': None,
            'end_time': None
        }
    
    def _default_config(self) -> Dict[str, Any]:
        """Configuración por defecto"""
        return {
            'input_dir': './tests/data',
            'output_dir': './out',
            'cache_dir': './out/cache',
            'batch_size': 100,
            'max_batch_size': 50000,
            'processing_mode': ProcessingMode.HYBRID,
            'enable_semantic_cache': True,
            'enable_quality_gate': True,
            'min_quality_score': 0.7,
            'enable_throttling': True,
            'save_to_db': True,
            'save_to_jsonl': True
        }
    
    async def run(self, input_path: Optional[str] = None, 
                  output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Ejecutar pipeline completo
        
        Args:
            input_path: Directorio de entrada (override config)
            output_path: Directorio de salida (override config)
        
        Returns:
            Estadísticas del procesamiento
        """
        self.stats['start_time'] = datetime.now()
        
        try:
            # 1️⃣ INGEST: Cargar productos
            input_dir = input_path or self.config['input_dir']
            logger.info(f"📂 Cargando productos desde {input_dir}")
            
            raw_products = []
            for item in ingest_from_dir(input_dir):
                raw_products.extend(item['products'])
            
            self.stats['total_products'] = len(raw_products)
            logger.info(f"📦 Productos cargados: {self.stats['total_products']}")
            
            if not raw_products:
                logger.warning("⚠️ No se encontraron productos")
                return self.stats
            
            # 2️⃣ PRE-PROCESS: Análisis de complejidad y routing
            logger.info("🎯 Analizando complejidad y routing...")
            
            for product in raw_products:
                model, complexity, reason = self.router.route_single_extended(product)
                product['_routing'] = {
                    'model': model,
                    'complexity': complexity,
                    'reason': reason
                }
            
            # Estadísticas de routing
            routing_stats = {}
            for p in raw_products:
                model = p['_routing']['model']
                routing_stats[model] = routing_stats.get(model, 0) + 1
            
            logger.info(f"📊 Distribución de routing: {routing_stats}")
            
            # 3️⃣ CACHE WARMUP: Pre-calentar cache si está vacío
            cache_stats = self.l1_cache.get_stats()
            if cache_stats['total_requests'] == 0:
                logger.info("🔥 Calentando cache L1...")
                await self._warmup_cache()
            
            # 4️⃣ PROCESS: Según modo configurado
            mode = self.config['processing_mode']
            logger.info(f"🚀 Procesando en modo {mode.value}")
            
            if mode == ProcessingMode.BATCH:
                # Procesamiento batch puro
                normalized = await self._process_batch(raw_products)
            elif mode == ProcessingMode.SINGLE:
                # Procesamiento individual
                normalized = await self._process_single(raw_products)
            else:  # HYBRID
                # Modo híbrido: cache + batch para nuevos
                normalized = await self._process_hybrid(raw_products)
            
            self.stats['processed'] = len(normalized)
            
            # 5️⃣ VALIDATE: Control de calidad
            if self.config['enable_quality_gate']:
                logger.info("✅ Ejecutando control de calidad...")
                normalized = await self._quality_control(normalized)
            
            # 6️⃣ PERSIST: Guardar resultados
            output_dir = output_path or self.config['output_dir']
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Guardar en JSONL
            if self.config['save_to_jsonl']:
                output_file = Path(output_dir) / 'normalized_gpt5.jsonl'
                persist_jsonl(normalized, str(output_file))
                logger.info(f"💾 Guardado en {output_file}")
            
            # Guardar en BD
            if self.config['save_to_db']:
                await self._save_to_database(normalized)
            
            # 7️⃣ STATS: Calcular estadísticas finales
            self.stats['end_time'] = datetime.now()
            self.stats['duration_seconds'] = (
                self.stats['end_time'] - self.stats['start_time']
            ).total_seconds()
            
            # Obtener costos desde BD
            cost_summary = self.db.get_cost_summary(days=1)
            self.stats['cost_usd'] = cost_summary.get('total_cost', 0)
            
            # Cache stats
            cache_stats = self.l1_cache.get_stats()
            self.stats['cache_hits'] = cache_stats['hits']
            self.stats['cache_hit_rate'] = cache_stats.get('hit_rate', '0%')
            
            # Rate limiter stats
            rl_stats = self.rate_limiter.get_status()
            self.stats['requests_throttled'] = rl_stats['stats'].get('requests_throttled', 0)
            
            # Imprimir resumen
            self._print_summary()
            
            return self.stats
            
        except Exception as e:
            logger.error(f"❌ Error en pipeline: {e}", exc_info=True)
            self.stats['errors'] += 1
            raise
        finally:
            # Limpiar recursos
            if hasattr(self, 'db'):
                self.db.close()
    
    async def _process_hybrid(self, products: List[Dict]) -> List[Dict]:
        """Procesamiento híbrido: cache + batch"""
        normalized = []
        to_batch = []
        
        for product in products:
            # Intentar normalizar con cache
            result = await normalize_with_gpt5(
                product, 
                mode=ProcessingMode.SINGLE,
                force_model=None
            )
            
            if result.get('pending_batch'):
                to_batch.append(product)
            else:
                normalized.append(result)
                if result.get('ai_model') == 'cache':
                    self.stats['cache_hits'] += 1
        
        # Procesar pendientes en batch
        if to_batch:
            logger.info(f"📦 Procesando {len(to_batch)} productos en batch...")
            batch_results = await process_batch_gpt5(to_batch)
            normalized.extend(batch_results)
        
        return normalized
    
    async def _process_batch(self, products: List[Dict]) -> List[Dict]:
        """Procesamiento batch puro"""
        return await process_batch_gpt5(
            products, 
            max_batch_size=self.config['max_batch_size']
        )
    
    async def _process_single(self, products: List[Dict]) -> List[Dict]:
        """Procesamiento individual"""
        normalized = []
        
        for i, product in enumerate(products, 1):
            try:
                result = await normalize_with_gpt5(
                    product,
                    mode=ProcessingMode.SINGLE
                )
                normalized.append(result)
                
                if i % 10 == 0:
                    logger.info(f"Progreso: {i}/{len(products)}")
                    
            except Exception as e:
                logger.error(f"Error procesando producto {i}: {e}")
                self.stats['errors'] += 1
        
        return normalized
    
    async def _quality_control(self, products: List[Dict]) -> List[Dict]:
        """Control de calidad con validación estricta"""
        validated = []
        
        for product in products:
            # Validar con QualityGate
            quality_gate = self.validator.quality_gate
            
            is_valid, score, issues = self.validator.validate_quality(
                product,
                product.get('category', 'general')
            )
            
            if score >= self.config['min_quality_score']:
                validated.append(product)
            else:
                logger.warning(
                    f"⚠️ Producto rechazado por calidad ({score:.2f}): "
                    f"{product.get('name', '')[:50]}... Issues: {issues}"
                )
                self.stats['errors'] += 1
        
        logger.info(
            f"✅ Control de calidad: {len(validated)}/{len(products)} aprobados"
        )
        
        return validated
    
    async def _save_to_database(self, products: List[Dict]):
        """Guardar productos en base de datos con idempotencia"""
        saved = 0
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                for product in products:
                    try:
                        # Insertar con ON CONFLICT para idempotencia
                        cursor.execute("""
                            INSERT INTO productos_maestros (
                                fingerprint,
                                retailer,
                                nombre_normalizado,
                                marca,
                                modelo,
                                categoria,
                                precio_actual,
                                precio_original,
                                moneda,
                                url,
                                atributos,
                                ai_confidence,
                                ai_model_used,
                                ai_processing_version
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (fingerprint) DO UPDATE
                            SET precio_actual = EXCLUDED.precio_actual,
                                updated_at = CURRENT_TIMESTAMP
                        """, (
                            product['fingerprint'],
                            product['retailer'],
                            product['name'],
                            product['brand'],
                            product['model'],
                            product['category'],
                            product['price_current'],
                            product.get('price_original'),
                            product['currency'],
                            product.get('url'),
                            json.dumps(product.get('attributes', {})),
                            product.get('ai_confidence', 0),
                            product.get('ai_model'),
                            product.get('processing_version', 'v2.0-gpt5')
                        ))
                        saved += 1
                    except Exception as e:
                        logger.error(f"Error guardando producto: {e}")
                
                conn.commit()
        
        logger.info(f"💾 Guardados {saved} productos en BD")
    
    async def _warmup_cache(self):
        """Pre-calentar cache con productos frecuentes"""
        try:
            # Obtener productos más consultados de BD
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT fingerprint, metadata, model_used
                        FROM ai_metadata_cache
                        WHERE quality_score > 0.8
                        ORDER BY hit_count DESC
                        LIMIT 1000
                    """)
                    
                    for row in cursor.fetchall():
                        fingerprint, metadata, model = row
                        self.l1_cache.set(
                            fingerprint,
                            json.loads(metadata) if isinstance(metadata, str) else metadata,
                            category='general'
                        )
            
            logger.info("🔥 Cache L1 calentado con productos frecuentes")
            
        except Exception as e:
            logger.warning(f"No se pudo calentar cache: {e}")
    
    def _print_summary(self):
        """Imprimir resumen del procesamiento"""
        duration = self.stats.get('duration_seconds', 0)
        
        print("""
╔══════════════════════════════════════════════════════════════════╗
║                 🎯 RESUMEN DE PROCESAMIENTO GPT-5                ║
╚══════════════════════════════════════════════════════════════════╝
        """)
        
        print(f"""
📊 ESTADÍSTICAS:
  • Total productos: {self.stats['total_products']:,}
  • Procesados: {self.stats['processed']:,}
  • Cache hits: {self.stats['cache_hits']:,} ({self.stats.get('cache_hit_rate', '0%')})
  • Errores: {self.stats['errors']:,}
  
💰 COSTOS:
  • Costo total: ${self.stats['cost_usd']:.4f} USD
  • Costo promedio: ${self.stats['cost_usd']/max(self.stats['processed'], 1):.6f} USD/producto
  
⏱️ RENDIMIENTO:
  • Duración: {duration:.1f} segundos
  • Velocidad: {self.stats['processed']/max(duration, 1):.1f} productos/segundo
  • Requests throttled: {self.stats.get('requests_throttled', 0)}
        """)


async def main():
    """Función principal"""
    
    # Configuración personalizada
    config = {
        'input_dir': './tests/data',
        'output_dir': './out',
        'processing_mode': ProcessingMode.HYBRID,
        'batch_size': 100,
        'enable_quality_gate': True,
        'min_quality_score': 0.7,
        'save_to_db': True,
        'save_to_jsonl': True
    }
    
    # Crear y ejecutar pipeline
    pipeline = GPT5Pipeline(config)
    
    try:
        stats = await pipeline.run()
        
        # Guardar estadísticas
        stats_file = Path(config['output_dir']) / 'processing_stats.json'
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, default=str)
        
        logger.info(f"📊 Estadísticas guardadas en {stats_file}")
        
    except Exception as e:
        logger.error(f"❌ Pipeline falló: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    # Ejecutar pipeline
    exit_code = asyncio.run(main())
    sys.exit(exit_code)