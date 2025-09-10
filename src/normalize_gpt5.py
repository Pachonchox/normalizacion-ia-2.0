#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Normalize con GPT-5 - Sistema Optimizado
Normalización inteligente con routing, batch processing y cache semántico
"""

from __future__ import annotations
import re
import hashlib
import os
import json
import logging
import asyncio
from typing import Dict, Any, Tuple, Optional, List
from pathlib import Path
import numpy as np
from datetime import datetime
from enum import Enum

# Imports del sistema actual
try:
    from .utils import parse_price, slugify
    from .enrich import guess_brand, extract_attributes, clean_model
    from .fingerprint import product_fingerprint
    from .cache import JsonCache
    from .gpt5_db_connector import GPT5DatabaseConnector, GPT5AICache, ModelType
    from .gpt5.router import GPT5Router, ComplexityAnalyzer
    from .gpt5.batch_processor_db import BatchProcessorDB, BatchOrchestrator
    from .gpt5.prompts import PromptManager, PromptMode
    from .gpt5.validator import StrictValidator, QualityGate
    from .gpt5.cache_l1 import L1RedisCache, CacheManager
    from .gpt5.throttling import RateLimiter, CircuitBreaker, get_rate_limiter
    from .llm_connectors import enabled as llm_enabled
except ImportError:
    from utils import parse_price, slugify
    from enrich import guess_brand, extract_attributes, clean_model
    from fingerprint import product_fingerprint
    from cache import JsonCache
    from gpt5_db_connector import GPT5DatabaseConnector, GPT5AICache, ModelType
    from gpt5.router import GPT5Router, ComplexityAnalyzer
    from gpt5.batch_processor_db import BatchProcessorDB, BatchOrchestrator
    from gpt5.prompts import PromptManager, PromptMode
    from gpt5.validator import StrictValidator, QualityGate
    from gpt5.cache_l1 import L1RedisCache, CacheManager
    from gpt5.throttling import RateLimiter, CircuitBreaker, get_rate_limiter
    from llm_connectors import enabled as llm_enabled

logger = logging.getLogger(__name__)

# ============================================================================
# 🎯 CONFIGURACIÓN GLOBAL
# ============================================================================

class ProcessingMode(Enum):
    """Modos de procesamiento"""
    SINGLE = "single"      # Producto individual
    BATCH = "batch"        # Lote con descuento 50%
    HYBRID = "hybrid"      # Mixto: cache + batch para nuevos

# Configuración de componentes globales
_db_connector = None
_router = None
_batch_processor = None
_prompt_manager = None
_validator = None
_l1_cache = None
_rate_limiter = None
_cache_manager = None

def get_gpt5_connector() -> GPT5DatabaseConnector:
    """Obtener conector GPT-5 (singleton)"""
    global _db_connector
    if _db_connector is None:
        _db_connector = GPT5DatabaseConnector(
            host=os.getenv("DB_HOST", "34.176.197.136"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "postgres"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "Osmar2503!"),
            pool_size=10
        )
    return _db_connector

def get_router() -> GPT5Router:
    """Obtener router inteligente (singleton)"""
    global _router
    if _router is None:
        _router = GPT5Router(db_connector=get_gpt5_connector())
    return _router

def get_batch_processor() -> BatchProcessorDB:
    """Obtener procesador batch (singleton)"""
    global _batch_processor
    if _batch_processor is None:
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            logger.warning("⚠️ OPENAI_API_KEY no configurada")
        _batch_processor = BatchProcessorDB(
            api_key=api_key,
            db_connector=get_gpt5_connector()
        )
    return _batch_processor

def get_prompt_manager() -> PromptManager:
    """Obtener gestor de prompts (singleton)"""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager

def get_validator() -> StrictValidator:
    """Obtener validador estricto (singleton)"""
    global _validator
    if _validator is None:
        _validator = StrictValidator()
    return _validator

def get_l1_cache() -> L1RedisCache:
    """Obtener cache L1 Redis (singleton)"""
    global _l1_cache
    if _l1_cache is None:
        _l1_cache = L1RedisCache(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD"),
            use_mock=os.getenv("REDIS_MOCK", "false").lower() == "true"
        )
    return _l1_cache

def get_cache_manager() -> CacheManager:
    """Obtener gestor de cache multicapa (singleton)"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(
            l1_cache=get_l1_cache(),
            l2_cache=None,  # Semantic cache vía DB
            l3_cache=get_gpt5_connector()  # PostgreSQL
        )
    return _cache_manager

# ============================================================================
# 🎯 EXTRACCIÓN DE PRECIOS (reutilizado del sistema actual)
# ============================================================================

PRICE_KEYS_PREF = [
    ("card_price", "card_price_text"),
    ("normal_price", "normal_price_text"),
    ("ripley_price", "ripley_price_text"),
]

def pick_price(item: Dict[str, Any]) -> Tuple[Optional[int], Optional[int]]:
    """Extraer precios del producto (compatible con sistema actual)"""
    current = None
    for numk, textk in PRICE_KEYS_PREF:
        if numk in item:
            current = parse_price(item.get(numk))
        if current is None and textk in item:
            current = parse_price(item.get(textk))
        if current is not None:
            break
    
    original = None
    for k in ("original_price", "original_price_text", "normal_price", "normal_price_text"):
        val = parse_price(item.get(k))
        if val:
            original = val
            break
    
    return current, original

# ============================================================================
# 🚀 NORMALIZACIÓN CON GPT-5
# ============================================================================

async def normalize_with_gpt5(product: Dict[str, Any], 
                             mode: ProcessingMode = ProcessingMode.HYBRID,
                             force_model: str = None) -> Dict[str, Any]:
    """
    Normalizar producto con sistema GPT-5 optimizado
    
    Args:
        product: Datos crudos del producto
        mode: Modo de procesamiento (SINGLE, BATCH, HYBRID)
        force_model: Forzar uso de modelo específico (debug)
    
    Returns:
        Producto normalizado con metadatos GPT-5
    """
    
    db = get_gpt5_connector()
    router = get_router()
    prompt_manager = get_prompt_manager()
    validator = get_validator()
    l1_cache = get_l1_cache()
    rate_limiter = get_rate_limiter()
    cache_manager = get_cache_manager()
    ai_cache = GPT5AICache(db)
    
    # 1️⃣ PREPARACIÓN: Crear fingerprint para cache
    name = product.get("name") or product.get("title") or ""
    brand = product.get("brand") or guess_brand(name) or "DESCONOCIDA"
    category = product.get("category", "general")
    
    base_product = {
        "brand": brand,
        "category": category,
        "model": clean_model(name, brand) or name,
        "attributes": extract_attributes(name, category)
    }
    
    fingerprint = product_fingerprint(base_product)
    
    # 2️⃣ CACHE CHECK: Buscar en cache L1 primero (más rápido)
    l1_cached = l1_cache.get(fingerprint)
    if l1_cached and not force_model:
        logger.info(f"⚡ L1 Cache hit: {name[:50]}...")
        return _build_final_product(product, l1_cached, fingerprint)
    
    # Cache L2/L3 vía cache manager
    cached = await cache_manager.get(fingerprint)
    
    if cached and not force_model:
        logger.info(f"✨ Cache hit exacto: {name[:50]}...")
        db.log_processing_metric(
            model=cached.get('model_used', 'cache'),
            request_type='single',
            tokens_input=0,
            tokens_output=0,
            cost_usd=0.0,
            cache_hit=True,
            cache_type='exact',
            fingerprint=fingerprint,
            category=category
        )
        return _build_final_product(product, cached, fingerprint)
    
    # 3️⃣ SEMANTIC CACHE: Buscar por similitud (si no hay hit exacto)
    if mode in [ProcessingMode.HYBRID, ProcessingMode.SINGLE]:
        # Generar embedding del producto
        embedding = await _generate_embedding(name, category)
        
        if embedding is not None:
            similar = db.search_semantic_cache(
                embedding=embedding,
                similarity_threshold=0.85,
                limit=1
            )
            
            if similar:
                logger.info(f"🧠 Cache semántico hit (sim={similar[0]['similarity']:.3f}): {name[:50]}...")
                
                # Usar datos del producto similar
                normalized_data = json.loads(similar[0]['normalized_data'])
                
                # Guardar en cache exacto para futuro
                ai_cache.set(
                    fingerprint=fingerprint,
                    metadata=normalized_data,
                    model_used=similar[0]['model_used'],
                    quality_score=similar[0]['similarity']
                )
                
                db.log_processing_metric(
                    model=similar[0]['model_used'],
                    request_type='single',
                    tokens_input=0,
                    tokens_output=0,
                    cost_usd=0.0,
                    cache_hit=True,
                    cache_type='semantic',
                    fingerprint=fingerprint,
                    category=category
                )
                
                return _build_final_product(product, normalized_data, fingerprint)
    
    # 4️⃣ ROUTING: Determinar modelo apropiado
    if force_model:
        model = force_model
        complexity = 0.5
        routing_reason = "Modelo forzado por usuario"
    else:
        model, complexity, routing_reason = router.route_single_extended(product)
    
    # Guardar análisis de complejidad
    db.save_complexity_analysis(
        fingerprint=fingerprint,
        complexity_score=complexity,
        model_assigned=model,
        routing_reason=routing_reason,
        weights=router.analyzer.get_weights()
    )
    
    logger.info(f"🎯 Routing: {name[:50]}... → {model} (complex={complexity:.2f})")
    
    # 5️⃣ PROCESSING: Según modo
    if mode == ProcessingMode.BATCH:
        # Agregar a cola de batch
        return await _queue_for_batch(product, model, fingerprint)
    
    else:
        # Procesamiento individual (con fallback)
        normalized_data = await _process_single_with_fallback(
            product=product,
            model=model,
            fingerprint=fingerprint,
            embedding=embedding if 'embedding' in locals() else None
        )
        
        return _build_final_product(product, normalized_data, fingerprint)

async def _generate_embedding(text: str, category: str = None) -> Optional[np.ndarray]:
    """Generar embedding usando OpenAI"""
    try:
        import openai
        
        # Texto optimizado para embedding
        embedding_text = f"{category}: {text}" if category else text
        
        response = await openai.Embedding.acreate(
            model="text-embedding-3-small",
            input=embedding_text[:8000]  # Límite de tokens
        )
        
        embedding = np.array(response['data'][0]['embedding'])
        return embedding
        
    except Exception as e:
        logger.error(f"Error generando embedding: {e}")
        return None

async def _process_single_with_fallback(product: Dict, model: str, 
                                       fingerprint: str, 
                                       embedding: np.ndarray = None) -> Dict:
    """Procesar producto individual con cadena de fallback"""
    
    db = get_gpt5_connector()
    router = get_router()
    ai_cache = GPT5AICache(db)
    
    # Obtener cadena de fallback
    fallback_chain = router.get_fallback_chain(ModelType(model))
    
    for attempt, current_model in enumerate(fallback_chain):
        try:
            logger.info(f"🔄 Intento {attempt + 1}: {current_model.value}")
            
            # Verificar rate limit y circuit breaker
            if not await rate_limiter.acquire(current_model.value, estimated_tokens=250):
                logger.warning(f"⏳ Rate limited para {current_model.value}, esperando...")
                if not await rate_limiter.acquire_with_backoff(current_model.value):
                    raise Exception(f"Rate limit exceeded for {current_model.value}")
            
            # Obtener prompt optimizado
            prompt_mode = PromptMode.STANDARD if attempt == 0 else PromptMode.FALLBACK
            prompt = prompt_manager.get_prompt(
                model=current_model.value,
                category=product.get('category', 'default'),
                mode=prompt_mode,
                product=product,
                previous_attempt=locals().get('normalized_data'),
                error=locals().get('last_error')
            )
            
            # System prompt específico por modelo
            system_prompt = prompt_manager.system_prompts.get(
                current_model.value,
                "Eres un experto en normalización de productos retail. Responde en JSON."
            )
            
            # Llamar a OpenAI con circuit breaker
            import openai
            circuit_breaker = rate_limiter.circuit_breakers.get(current_model.value)
            
            async def make_openai_call():
                return await openai.ChatCompletion.acreate(
                    model=current_model.value,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_completion_tokens=500,
                    response_format={"type": "json_object"}
                )
            
            # Ejecutar con circuit breaker si existe
            if circuit_breaker:
                response = await circuit_breaker.call_async(make_openai_call)
            else:
                response = await make_openai_call()
            
            # Parsear respuesta
            content = response.choices[0].message.content
            normalized_data = json.loads(content)
            
            # VALIDACIÓN ESTRICTA
            # 1. Validar taxonomía
            if 'category_suggestion' in normalized_data:
                valid_tax, final_cat, tax_msg = validator.validate_taxonomy(
                    normalized_data['category_suggestion'],
                    product.get('category', 'general')
                )
                if not valid_tax:
                    logger.warning(f"⚠️ Taxonomía inválida: {tax_msg}")
                normalized_data['category_suggestion'] = final_cat
            
            # 2. Validar atributos
            if 'attributes' in normalized_data:
                valid_attrs, clean_attrs, attr_warnings = validator.validate_attributes(
                    normalized_data['attributes'],
                    normalized_data.get('category_suggestion', product.get('category', 'general'))
                )
                if attr_warnings:
                    logger.debug(f"Advertencias de atributos: {attr_warnings}")
                normalized_data['attributes'] = clean_attrs
            
            # 3. Validar calidad
            valid_quality, quality_score, quality_issues = validator.validate_quality(
                normalized_data,
                normalized_data.get('category_suggestion', product.get('category', 'general'))
            )
            
            if not valid_quality:
                logger.warning(f"⚠️ Calidad insuficiente ({quality_score:.2f}): {quality_issues}")
                if attempt < len(fallback_chain) - 1:
                    last_error = f"Quality issues: {', '.join(quality_issues)}"
                    continue  # Intentar con siguiente modelo
            
            normalized_data['confidence'] = quality_score
            
            # Calcular métricas
            tokens_used = response.usage.total_tokens
            cost = db.get_model_config(current_model.value)
            
            if cost:
                cost_usd = (
                    (response.usage.prompt_tokens / 1000) * cost['cost_per_1k_input'] +
                    (response.usage.completion_tokens / 1000) * cost['cost_per_1k_output']
                )
            else:
                cost_usd = tokens_used * 0.0003 / 1000  # Estimado
            
            # Guardar en múltiples niveles de cache
            # L1 Cache (Redis)
            l1_cache.set(
                fingerprint=fingerprint,
                data=normalized_data,
                category=normalized_data.get('category_suggestion', product.get('category')),
                ttl_override=None  # Usar TTL por categoría
            )
            
            # Cache tradicional (PostgreSQL)
            ai_cache.set(
                fingerprint=fingerprint,
                metadata=normalized_data,
                model_used=current_model.value,
                tokens_used=tokens_used,
                quality_score=quality_score
            )
            
            # Guardar en cache semántico si tenemos embedding
            if embedding is not None:
                db.store_semantic_cache(
                    fingerprint=fingerprint,
                    embedding=embedding,
                    product_data=product,
                    normalized_data=normalized_data,
                    model_used=current_model.value
                )
            
            # Log métricas
            db.log_processing_metric(
                model=current_model.value,
                request_type='fallback' if attempt > 0 else 'single',
                tokens_input=response.usage.prompt_tokens,
                tokens_output=response.usage.completion_tokens,
                cost_usd=cost_usd,
                latency_ms=int(response.response_ms) if hasattr(response, 'response_ms') else None,
                cache_hit=False,
                complexity_score=product.get('_complexity', 0.5),
                success=True,
                fingerprint=fingerprint,
                category=product.get('category')
            )
            
            # Reportar éxito al rate limiter
            rate_limiter.report_success(current_model.value)
            
            logger.info(f"✅ Normalizado con {current_model.value} ({tokens_used} tokens, ${cost_usd:.4f}, Q:{quality_score:.2f})")
            return normalized_data
            
        except Exception as e:
            logger.error(f"❌ Error con {current_model.value}: {e}")
            last_error = str(e)
            
            # Reportar fallo al rate limiter
            rate_limiter.report_failure(current_model.value, e)
            
            # Log error
            db.log_processing_metric(
                model=current_model.value,
                request_type='fallback' if attempt > 0 else 'single',
                tokens_input=0,
                tokens_output=0,
                cost_usd=0,
                success=False,
                error_type=type(e).__name__,
                fingerprint=fingerprint
            )
            
            # Continuar con siguiente modelo
            if attempt < len(fallback_chain) - 1:
                continue
            else:
                # Fallback final: datos básicos
                logger.warning(f"⚠️ Usando fallback básico para {product.get('name', '')[:50]}")
                return {
                    'brand': guess_brand(product.get('name', '')),
                    'model': clean_model(product.get('name', ''), ''),
                    'refined_attributes': extract_attributes(product.get('name', ''), product.get('category', '')),
                    'normalized_name': product.get('name', ''),
                    'confidence': 0.3,
                    'error': 'fallback_basic'
                }

async def _queue_for_batch(product: Dict, model: str, fingerprint: str) -> Dict:
    """Agregar producto a cola de batch processing con idempotencia"""
    
    db = get_gpt5_connector()
    
    # Generar custom_id único para idempotencia
    custom_id = f"{fingerprint}_{int(datetime.now().timestamp())}"
    
    # Guardar en cola con ON CONFLICT para idempotencia
    with db.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO processing_queue 
                (fingerprint, product_data, assigned_model, status, priority, custom_id)
                VALUES (%s, %s, %s, 'pending', %s, %s)
                ON CONFLICT (fingerprint) DO UPDATE
                SET assigned_model = EXCLUDED.assigned_model,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                fingerprint,
                json.dumps(product),
                model,
                5,  # Prioridad media
                custom_id
            ))
            conn.commit()
    
    logger.info(f"📦 Producto agregado a cola batch: {fingerprint[:8]}...")
    
    # Retornar producto con marca de pendiente
    return _build_final_product(
        product,
        {
            'brand': guess_brand(product.get('name', '')),
            'model': product.get('name', ''),
            'refined_attributes': {},
            'normalized_name': product.get('name', ''),
            'confidence': 0.0,
            'pending_batch': True
        },
        fingerprint
    )

def _build_final_product(raw: Dict, ai_data: Dict, fingerprint: str) -> Dict:
    """Construir producto final con todos los datos"""
    
    # Extraer precios (volátiles, no se cachean)
    price_curr, price_orig = pick_price(raw)
    
    if price_curr is None and price_orig:
        price_curr = price_orig
    
    # Construir producto final
    return {
        "product_id": hashlib.sha1(
            f"{raw.get('retailer', '')}|{fingerprint}".encode()
        ).hexdigest(),
        "fingerprint": fingerprint,
        "retailer": raw.get("retailer", "unknown"),
        "name": ai_data.get("normalized_name") or raw.get("name", ""),
        "brand": ai_data.get("brand", "DESCONOCIDA"),
        "model": ai_data.get("model"),
        "category": ai_data.get("category_suggestion") or raw.get("category", "general"),
        "price_current": int(price_curr) if price_curr is not None else 0,
        "price_original": int(price_orig) if price_orig is not None else None,
        "currency": "CLP",
        "url": raw.get("product_link") or raw.get("url"),
        "attributes": ai_data.get("refined_attributes", {}),
        "source": {
            "metadata": raw.get("metadata", {}),
            "raw_keys": list(raw.keys())
        },
        # Metadatos GPT-5
        "ai_enhanced": not ai_data.get("pending_batch", False),
        "ai_confidence": float(ai_data.get("confidence", 0.0)),
        "ai_model": ai_data.get("model_used"),
        "processing_version": "v2.0-gpt5",
        "pending_batch": ai_data.get("pending_batch", False)
    }

# ============================================================================
# 🚀 PROCESAMIENTO BATCH
# ============================================================================

async def process_batch_gpt5(products: List[Dict], 
                            max_batch_size: int = 50000) -> List[Dict]:
    """
    Procesar lote de productos con batch API (50% descuento)
    
    Args:
        products: Lista de productos a procesar
        max_batch_size: Tamaño máximo por batch
    
    Returns:
        Lista de productos normalizados
    """
    
    db = get_gpt5_connector()
    router = get_router()
    processor = get_batch_processor()
    orchestrator = BatchOrchestrator(
        api_key=os.getenv("OPENAI_API_KEY", ""),
        db_connector=db
    )
    
    logger.info(f"📦 Iniciando batch processing de {len(products)} productos")
    
    # 1️⃣ FILTRAR: Separar productos ya cacheados
    to_process = []
    cached_results = []
    ai_cache = GPT5AICache(db)
    
    for product in products:
        # Generar fingerprint
        base = {
            "brand": product.get("brand") or guess_brand(product.get("name", "")),
            "category": product.get("category", "general"),
            "model": clean_model(product.get("name", ""), product.get("brand", "")),
            "attributes": extract_attributes(product.get("name", ""), product.get("category", ""))
        }
        fingerprint = product_fingerprint(base)
        product['_fingerprint'] = fingerprint
        
        # Verificar cache
        cached = ai_cache.get(fingerprint)
        if cached:
            cached_results.append(_build_final_product(product, cached, fingerprint))
        else:
            to_process.append(product)
    
    logger.info(f"📊 Cache hits: {len(cached_results)}, A procesar: {len(to_process)}")
    
    if not to_process:
        return cached_results
    
    # 2️⃣ ROUTING: Clasificar por complejidad
    for product in to_process:
        model, complexity, reason = router.route_single_extended(product)
        product['_model'] = model
        product['_complexity'] = complexity
        
        # Guardar análisis
        db.save_complexity_analysis(
            fingerprint=product['_fingerprint'],
            complexity_score=complexity,
            model_assigned=model,
            routing_reason=reason
        )
    
    # 3️⃣ CREAR BATCHES: Optimizados por modelo
    batches = orchestrator.create_optimized_batches(to_process, max_batch_size)
    
    logger.info(f"📦 Creados {len(batches)} batches optimizados")
    
    # 4️⃣ PROCESAR: Cada batch en paralelo
    all_results = cached_results.copy()
    
    for batch_info in batches:
        batch_id = batch_info['batch_id']
        model = batch_info['model']
        batch_products = batch_info['products']
        
        logger.info(f"🚀 Procesando batch {batch_id}: {len(batch_products)} productos con {model}")
        
        try:
            # Procesar batch (incluye espera)
            results = await processor.process_products_batch(
                products=batch_products,
                model=model,
                prompt_template="Normalize: {name}"
            )
            
            # Convertir resultados a productos finales
            for result in results:
                # Buscar producto original por fingerprint
                original = next(
                    (p for p in batch_products if p.get('_fingerprint') == result.get('fingerprint')),
                    None
                )
                
                if original and result.get('normalized'):
                    final_product = _build_final_product(
                        original,
                        result['normalized'],
                        result['fingerprint']
                    )
                    all_results.append(final_product)
            
        except Exception as e:
            logger.error(f"❌ Error procesando batch {batch_id}: {e}")
            
            # Procesar individualmente como fallback
            for product in batch_products:
                try:
                    normalized = await normalize_with_gpt5(
                        product,
                        mode=ProcessingMode.SINGLE
                    )
                    all_results.append(normalized)
                except Exception as e2:
                    logger.error(f"Error procesando producto individual: {e2}")
    
    # 5️⃣ ESTADÍSTICAS FINALES
    stats = db.get_cost_summary(days=1)
    logger.info(f"""
    ✅ Batch processing completado:
    - Productos procesados: {len(all_results)}
    - Cache hits: {len(cached_results)} ({len(cached_results)/len(products)*100:.1f}%)
    - Nuevos procesados: {len(all_results) - len(cached_results)}
    - Costo estimado: ${stats.get('total_cost', 0):.4f}
    """)
    
    return all_results

# ============================================================================
# 🔄 COMPATIBILIDAD CON SISTEMA ACTUAL
# ============================================================================

def normalize_one(raw: Dict[str, Any], metadata: Dict[str, Any], 
                 retailer: str, category_id: str) -> Dict[str, Any]:
    """
    Función de compatibilidad con normalize.py actual
    """
    # Agregar metadatos al producto
    raw['retailer'] = retailer
    raw['category'] = category_id
    raw['metadata'] = metadata
    
    # Usar modo híbrido por defecto
    try:
        # Ejecutar asíncronamente
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Si ya hay un loop, crear tarea
            task = asyncio.create_task(
                normalize_with_gpt5(raw, mode=ProcessingMode.HYBRID)
            )
            return asyncio.run_coroutine_threadsafe(task, loop).result()
        else:
            # Crear nuevo loop
            return asyncio.run(
                normalize_with_gpt5(raw, mode=ProcessingMode.HYBRID)
            )
    except Exception as e:
        logger.error(f"Error en normalización GPT-5: {e}")
        
        # Fallback al sistema anterior
        from normalize import normalize_one as normalize_one_legacy
        return normalize_one_legacy(raw, metadata, retailer, category_id)

# ============================================================================
# 🎯 MAIN - Testing y CLI
# ============================================================================

async def main():
    """Función principal para testing"""
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║        🚀 NORMALIZACIÓN GPT-5 - Sistema Optimizado      ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Productos de prueba
    test_products = [
        {
            "name": "iPhone 15 Pro Max 256GB Titanio Natural",
            "category": "smartphones",
            "price": 1299990,
            "retailer": "falabella"
        },
        {
            "name": "Coca Cola Sin Azúcar 2L",
            "category": "beverages",
            "price": 2190,
            "retailer": "jumbo"
        },
        {
            "name": "MacBook Pro 16 M3 Max 48GB RAM 1TB SSD",
            "category": "notebooks",
            "price": 3899990,
            "retailer": "paris"
        }
    ]
    
    # Test 1: Procesamiento individual
    print("\n📝 Test 1: Procesamiento Individual")
    print("-" * 40)
    
    for product in test_products[:1]:
        result = await normalize_with_gpt5(product, mode=ProcessingMode.SINGLE)
        print(f"✅ {result['name']}")
        print(f"   Marca: {result['brand']}")
        print(f"   Modelo: {result['model']}")
        print(f"   Confianza: {result['ai_confidence']:.2f}")
        print(f"   Modelo IA: {result.get('ai_model', 'N/A')}")
    
    # Test 2: Procesamiento batch
    print("\n📦 Test 2: Procesamiento Batch")
    print("-" * 40)
    
    if os.getenv("OPENAI_API_KEY"):
        results = await process_batch_gpt5(test_products)
        print(f"✅ Procesados {len(results)} productos en batch")
        
        for r in results:
            print(f"   - {r['name'][:50]}... [{r.get('ai_model', 'cache')}]")
    else:
        print("⚠️ OPENAI_API_KEY no configurada - saltando test de batch")
    
    # Test 3: Estadísticas
    print("\n📊 Test 3: Estadísticas del Sistema")
    print("-" * 40)
    
    db = get_gpt5_connector()
    stats = db.get_stats()
    
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Estadísticas de cache L1
    l1_cache = get_l1_cache()
    l1_stats = l1_cache.get_stats()
    print("\n📊 Cache L1 Stats:")
    for key, value in l1_stats.items():
        print(f"   {key}: {value}")
    
    # Estadísticas de rate limiter
    rate_limiter = get_rate_limiter()
    rl_status = rate_limiter.get_status()
    print("\n⚡ Rate Limiter Status:")
    print(f"   Requests: {rl_status['stats']}")
    
    # Cerrar conexiones
    db.close()
    print("\n✅ Tests completados")

if __name__ == "__main__":
    asyncio.run(main())