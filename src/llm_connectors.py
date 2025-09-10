#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 GPT-5 LLM Connector
Conector principal con routing inteligente, batch processing y cache semántico
Reemplazo completo del sistema anterior con arquitectura GPT-5
"""

from __future__ import annotations
import os
import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
import logging
from dotenv import load_dotenv

# Importar componentes GPT-5
from .gpt5.router import GPT5Router, ModelType
from .gpt5.batch.processor import BatchProcessor, BatchOrchestrator
from .gpt5.cache.semantic_cache import SemanticCache
from .gpt5.prompt_optimizer import PromptOptimizer

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GPT5Connector:
    """
    Conector unificado para GPT-5 con todas las optimizaciones
    """
    
    def __init__(self, config_path: str = "configs/config.gpt5.toml"):
        self.config = self._load_config(config_path)
        self.router = GPT5Router()
        self.batch_processor = BatchProcessor()
        self.semantic_cache = None
        self.prompt_optimizer = PromptOptimizer()
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'batch_processed': 0,
            'total_cost': 0.0
        }
        
        # Inicializar cache semántico si está habilitado
        if self.config.get('cache', {}).get('l2', {}).get('type') == 'semantic':
            self._init_semantic_cache()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Carga configuración desde archivo TOML"""
        try:
            import tomli
            with open(config_path, 'rb') as f:
                config = tomli.load(f)
            
            # Reemplazar variables de entorno
            config = self._replace_env_vars(config)
            return config
            
        except Exception as e:
            logger.warning(f"Could not load config: {e}, using defaults")
            return self._get_default_config()
    
    def _replace_env_vars(self, config: Any) -> Any:
        """Reemplaza ${VAR} con variables de entorno"""
        if isinstance(config, dict):
            return {k: self._replace_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._replace_env_vars(item) for item in config]
        elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
            var_name = config[2:-1]
            return os.getenv(var_name, config)
        return config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Configuración por defecto si falla la carga"""
        return {
            'llm': {
                'enabled': True,
                'routing_enabled': True,
                'batch_enabled': True,
                'default_model': 'gpt-5-mini'
            },
            'cache': {
                'l2': {'type': 'memory', 'similarity_threshold': 0.85}
            },
            'batch': {
                'enabled': True,
                'optimal_batch_size': 10000
            }
        }
    
    def _init_semantic_cache(self):
        """Inicializa cache semántico"""
        try:
            cache_config = self.config['cache']['l2']
            self.semantic_cache = SemanticCache(
                backend=cache_config.get('backend', 'memory'),
                similarity_threshold=cache_config.get('similarity_threshold', 0.85)
            )
            logger.info("✅ Semantic cache initialized")
        except Exception as e:
            logger.error(f"Failed to init semantic cache: {e}")
    
    def enabled(self) -> bool:
        """Verifica si LLM está habilitado"""
        env_enabled = os.environ.get("LLM_ENABLED", "false").lower() in ("1", "true", "yes")
        config_enabled = self.config.get('llm', {}).get('enabled', False)
        return env_enabled or config_enabled
    
    async def extract_with_llm(self, title: str, category: str = "") -> Dict[str, Any]:
        """
        Extracción individual con routing inteligente y cache semántico
        Compatible con interfaz anterior pero optimizada
        """
        if not self.enabled():
            return {"error": "llm_disabled", "confidence": 0.0}
        
        self.stats['total_requests'] += 1
        
        # Preparar producto para procesamiento
        product = {
            'name': title,
            'category': category,
            'price': 0  # Se podría extraer del título si está presente
        }
        
        # Buscar en cache semántico primero
        if self.semantic_cache:
            cached_result = await self.semantic_cache.find_similar(product)
            if cached_result:
                self.stats['cache_hits'] += 1
                logger.info(f"🎯 Semantic cache hit for: {title[:50]}...")
                return cached_result
        
        # Determinar modelo óptimo con router
        model_type, complexity = self.router.route_single(product)
        model = model_type.value
        
        # Optimizar prompt según modelo
        prompt = self.prompt_optimizer.optimize_prompt(product, model)
        system_prompt = self.prompt_optimizer.get_system_prompt(model)
        
        try:
            import openai
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # Llamada a API con modelo optimizado
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_completion_tokens=250 if "mini" in model else 500,
                response_format={"type": "json_object"} if "gpt-5" in model else None
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parsear respuesta
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
            
            normalized_data = json.loads(content)
            
            # Agregar metadata
            normalized_data['_model_used'] = model
            normalized_data['_complexity_score'] = complexity
            
            # Guardar en cache semántico
            if self.semantic_cache and 'error' not in normalized_data:
                await self.semantic_cache.store(product, normalized_data)
            
            # Actualizar estadísticas de costo
            self._update_cost_stats(model, prompt)
            
            return normalized_data
            
        except Exception as e:
            logger.error(f"LLM extraction error: {e}")
            return {"error": str(e), "confidence": 0.0}
    
    async def extract_batch_with_llm(self, products: List[Dict[str, Any]], 
                                    batch_size: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Procesamiento batch masivo con 50% descuento
        Ideal para población inicial de datos
        """
        if not self.enabled():
            return [{"error": "llm_disabled"} for _ in products]
        
        if not self.config.get('batch', {}).get('enabled', False):
            # Fallback a procesamiento individual
            results = []
            for product in products:
                result = await self.extract_with_llm(
                    product.get('name', ''),
                    product.get('category', '')
                )
                results.append(result)
            return results
        
        # Usar batch processor para máximo ahorro
        batch_size = batch_size or self.config['batch'].get('optimal_batch_size', 10000)
        
        logger.info(f"📦 Starting batch processing for {len(products)} products")
        
        # Dividir productos por modelo usando router
        batches = self.router.route_batch(products)
        optimized_batches = self.router.optimize_batches(batches, batch_size)
        
        all_results = []
        
        for batch_config in optimized_batches:
            model = batch_config['model']
            batch_products = batch_config['products']
            
            # Generar prompts optimizados para batch
            prompts = self.prompt_optimizer.optimize_batch_prompts(batch_products, model)
            
            # Procesar batch con API
            results = await self.batch_processor.process_batch_with_fallback(
                batch_products,
                model,
                prompts[0] if prompts else ""  # Template base
            )
            
            all_results.extend(results)
            self.stats['batch_processed'] += len(results)
        
        logger.info(f"✅ Batch processing completed: {len(all_results)} products")
        
        # Calcular y mostrar ahorros
        savings = self.router.estimate_savings(products)
        logger.info(f"💰 Estimated savings: ${savings['savings_usd']:.2f} ({savings['savings_percent']}%)")
        
        return all_results
    
    async def process_initial_population(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Modo especial para población inicial masiva
        Optimizado para máximo ahorro en primera carga
        """
        if not self.config.get('batch', {}).get('initial_population_mode', False):
            return await self.extract_batch_with_llm(products)
        
        logger.info(f"🚀 INITIAL POPULATION MODE: {len(products)} products")
        
        orchestrator = BatchOrchestrator()
        results = await orchestrator.process_initial_population(
            products,
            batch_size=self.config['batch'].get('optimal_batch_size', 10000)
        )
        
        return results
    
    def _update_cost_stats(self, model: str, prompt: str):
        """Actualiza estadísticas de costo"""
        tokens = len(prompt.split()) * 1.3  # Estimación simple
        cost_per_1k = self.config.get('models', {}).get(model, {}).get('cost_per_1k_tokens', 0.001)
        cost = (tokens / 1000) * cost_per_1k
        self.stats['total_cost'] += cost
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de uso"""
        cache_stats = self.semantic_cache.get_stats() if self.semantic_cache else {}
        
        return {
            **self.stats,
            'cache_hit_rate': self.stats['cache_hits'] / max(self.stats['total_requests'], 1),
            'batch_percentage': self.stats['batch_processed'] / max(self.stats['total_requests'], 1),
            'cache_stats': cache_stats
        }
    
    def enrich_product_data(self, base_data: Dict[str, Any], ai_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combina datos base con enriquecimiento IA
        Compatible con interfaz anterior
        """
        if not ai_data or "error" in ai_data:
            return base_data
        
        enriched = base_data.copy()
        
        # Enriquecer con datos IA
        if ai_data.get("brand") and not base_data.get("brand"):
            enriched["brand"] = ai_data["brand"]
        
        if ai_data.get("model"):
            enriched["model"] = ai_data["model"]
        
        if ai_data.get("attributes"):
            current_attrs = enriched.get("attributes", {})
            ai_attrs = ai_data["attributes"]
            
            for key, value in ai_attrs.items():
                if value and value != "N/A":
                    current_attrs[key] = value
            
            enriched["attributes"] = current_attrs
        
        # Agregar metadata IA
        enriched["ai_enhanced"] = True
        enriched["ai_confidence"] = ai_data.get("confidence", 0.0)
        
        if "_model_used" in ai_data:
            enriched["ai_model"] = ai_data["_model_used"]
        
        return enriched


# Instancia global para compatibilidad
_connector = GPT5Connector()

# Funciones de compatibilidad con interfaz anterior
def enabled() -> bool:
    """Compatibilidad: verificar si IA está habilitada"""
    return _connector.enabled()

def extract_with_llm(title: str, category: str = "") -> Dict[str, Any]:
    """Compatibilidad: extracción síncrona"""
    # Ejecutar async en sync context
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(_connector.extract_with_llm(title, category))

def extract_batch_with_llm(products: List[Dict[str, Any]], batch_size: int = 100) -> List[Dict[str, Any]]:
    """Compatibilidad: batch processing"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(_connector.extract_batch_with_llm(products, batch_size))

def enrich_product_data(base_data: Dict[str, Any], ai_data: Dict[str, Any]) -> Dict[str, Any]:
    """Compatibilidad: enriquecimiento de datos"""
    return _connector.enrich_product_data(base_data, ai_data)


if __name__ == "__main__":
    # Test del nuevo conector
    print("🚀 Testing GPT-5 Connector\n")
    
    # Test routing individual
    result = extract_with_llm("iPhone 15 Pro Max 256GB", "smartphones")
    print(f"Individual result: {result}\n")
    
    # Test batch processing
    test_products = [
        {"name": f"Product {i}", "category": "test", "price": 1000 * i}
        for i in range(5)
    ]
    
    batch_results = extract_batch_with_llm(test_products, batch_size=5)
    print(f"Batch results: {len(batch_results)} processed")
    
    # Mostrar estadísticas
    stats = _connector.get_stats()
    print(f"\nStats: {json.dumps(stats, indent=2)}")