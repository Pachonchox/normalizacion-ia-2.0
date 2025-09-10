#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ðŸš€ GPT-5 Intelligent Router with Batch Support
Sistema de routing inteligente que determina el modelo Ã³ptimo basado en complejidad
y agrupa productos para procesamiento batch masivo (50% descuento en costos)
"""

from __future__ import annotations
import hashlib
import re
from typing import Dict, Any, List, Tuple, Optional
from enum import Enum
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Modelos disponibles con sus caracterÃ­sticas"""
    GPT5_MINI = "gpt-5-mini"  # RÃ¡pido y econÃ³mico (80% casos)
    GPT5 = "gpt-5"  # Complejo y preciso (15% casos)  
    GPT4O_MINI = "gpt-4o-mini"  # Fallback legacy (5% casos)
    GPT4O = "gpt-4o"  # Modelo mÃ¡s potente para fallback final


@dataclass
class ModelConfig:
    """ConfiguraciÃ³n especÃ­fica por modelo"""
    name: str
    max_completion_tokens: int
    temperature: float
    timeout: int
    cost_per_1k_tokens: float
    batch_discount: float = 0.5  # 50% descuento en batch API


class ComplexityAnalyzer:
    """Analizador de complejidad de productos para routing Ã³ptimo"""
    
    def __init__(self):
        self.technical_terms = {
            'processor', 'cpu', 'gpu', 'ram', 'ssd', 'nvme', 'ddr4', 'ddr5',
            'ghz', 'mhz', 'gb', 'tb', 'mb', 'core', 'thread', 'cache',
            'wifi', 'bluetooth', '5g', '4g', 'lte', 'usb', 'hdmi', 'displayport'
        }
        
        self.complex_categories = {
            'notebooks': 0.7,
            'smartphones': 0.6,
            'smart_tv': 0.6,
            'tablets': 0.5,
            'monitors': 0.5,
            'components': 0.8,
            'gaming': 0.7
        }
        
        self.simple_categories = {
            'perfumes': 0.2,
            'clothing': 0.1,
            'books': 0.1,
            'food': 0.2,
            'beverages': 0.1,
            'accessories': 0.3
        }
    
    def calculate_complexity(self, product: Dict[str, Any]) -> float:
        """
        Calcula score de complejidad de 0.0 a 1.0
        0.0-0.3: Simple (GPT-5-mini)
        0.3-0.7: Medio (GPT-5-mini con validaciÃ³n)
        0.7-1.0: Complejo (GPT-5 full)
        """
        name = product.get('name', '').lower()
        category = product.get('category', '').lower()
        price = product.get('price', 0)
        
        complexity_factors = []
        
        # Factor 1: Longitud del nombre (productos con descripciones largas)
        name_length_score = min(len(name) / 300, 1.0)
        complexity_factors.append(name_length_score * 0.15)
        
        # Factor 2: TÃ©rminos tÃ©cnicos
        technical_count = sum(1 for term in self.technical_terms if term in name)
        technical_score = min(technical_count / 5, 1.0)
        complexity_factors.append(technical_score * 0.25)
        
        # Factor 3: CategorÃ­a
        if category in self.complex_categories:
            complexity_factors.append(self.complex_categories[category] * 0.3)
        elif category in self.simple_categories:
            complexity_factors.append(self.simple_categories[category] * 0.3)
        else:
            complexity_factors.append(0.4 * 0.3)  # CategorÃ­a desconocida = medio
        
        # Factor 4: Precio (productos caros suelen ser mÃ¡s complejos)
        if price > 1000000:  # > 1M CLP
            complexity_factors.append(0.8 * 0.15)
        elif price > 500000:  # > 500K CLP
            complexity_factors.append(0.6 * 0.15)
        elif price > 100000:  # > 100K CLP
            complexity_factors.append(0.4 * 0.15)
        else:
            complexity_factors.append(0.2 * 0.15)
        
        # Factor 5: Multi-variante (productos con mÃºltiples opciones)
        has_variants = bool(re.search(r'\d+GB|\d+TB|/|\||,\s*\d+', name))
        complexity_factors.append(0.7 * 0.15 if has_variants else 0.2 * 0.15)
        
        return sum(complexity_factors)


class GPT5Router:
    """Router inteligente con soporte para batch processing"""
    
    def __init__(self):
        self.analyzer = ComplexityAnalyzer()
        
        self.models = {
            ModelType.GPT5_MINI: ModelConfig(
                name="gpt-5-mini",
                max_completion_tokens=250,
                temperature=0.1,
                timeout=10,
                cost_per_1k_tokens=0.0003  # Estimado
            ),
            ModelType.GPT5: ModelConfig(
                name="gpt-5",
                max_completion_tokens=500,
                temperature=0.2,
                timeout=20,
                cost_per_1k_tokens=0.001  # Estimado
            ),
            ModelType.GPT4O_MINI: ModelConfig(
                name="gpt-4o-mini",
                max_completion_tokens=300,
                temperature=0.1,
                timeout=15,
                cost_per_1k_tokens=0.0015  # Real actual
            )
        }
        
        # Umbrales de complejidad
        self.thresholds = {
            'simple': 0.35,  # <= 0.35 = GPT-5-mini
            'complex': 0.70  # >= 0.70 = GPT-5
        }
    
    def route_single(self, product: Dict[str, Any]) -> Tuple[ModelType, float]:
        """
        Determina el modelo Ã³ptimo para un producto individual
        Returns: (modelo, complexity_score)
        """
        complexity = self.analyzer.calculate_complexity(product)
        
        if complexity <= self.thresholds['simple']:
            return ModelType.GPT5_MINI, complexity
        elif complexity >= self.thresholds['complex']:
            return ModelType.GPT5, complexity
        else:
            # Zona media: GPT-5-mini con validaciÃ³n adicional
            return ModelType.GPT5_MINI, complexity
    
    def route_batch(self, products: List[Dict[str, Any]]) -> Dict[ModelType, List[Dict[str, Any]]]:
        """
        Agrupa productos por modelo Ã³ptimo para batch processing
        Maximiza el ahorro agrupando productos similares
        """
        batches = {
            ModelType.GPT5_MINI: [],
            ModelType.GPT5: [],
            ModelType.GPT4O_MINI: []
        }
        
        for product in products:
            model, complexity = self.route_single(product)
            
            # Enriquecer producto con metadata de routing
            product['_routing_metadata'] = {
                'model': model.value,
                'complexity_score': round(complexity, 3),
                'batch_eligible': True
            }
            
            batches[model].append(product)
        
        # Log de distribuciÃ³n
        total = len(products)
        if total > 0:
            logger.info(f"ðŸ“Š Batch Routing Distribution:")
            logger.info(f"  - GPT-5-mini: {len(batches[ModelType.GPT5_MINI])} ({len(batches[ModelType.GPT5_MINI])*100/total:.1f}%)")
            logger.info(f"  - GPT-5: {len(batches[ModelType.GPT5])} ({len(batches[ModelType.GPT5])*100/total:.1f}%)")
            logger.info(f"  - GPT-4o-mini: {len(batches[ModelType.GPT4O_MINI])} ({len(batches[ModelType.GPT4O_MINI])*100/total:.1f}%)")
        
        return batches
    
    def optimize_batches(self, batches: Dict[ModelType, List[Dict[str, Any]]], 
                        max_batch_size: int = 100) -> List[Dict[str, Any]]:
        """
        Optimiza batches para mÃ¡ximo ahorro
        - Agrupa hasta max_batch_size productos por request
        - Prioriza modelos econÃ³micos
        - Retorna lista de batches optimizados
        """
        optimized = []
        
        for model_type, products in batches.items():
            if not products:
                continue
            
            config = self.models[model_type]
            
            # Dividir en sub-batches de tamaÃ±o Ã³ptimo
            for i in range(0, len(products), max_batch_size):
                batch = products[i:i + max_batch_size]
                
                optimized.append({
                    'model': model_type.value,
                    'config': config,
                    'products': batch,
                    'batch_size': len(batch),
                    'estimated_cost': self._estimate_batch_cost(batch, config),
                    'priority': self._calculate_priority(model_type, len(batch))
                })
        
        # Ordenar por prioridad (procesar primero los mÃ¡s econÃ³micos/grandes)
        optimized.sort(key=lambda x: x['priority'], reverse=True)
        
        return optimized
    
    def get_fallback_chain(self, model: ModelType) -> List[ModelType]:
        """
        Obtener cadena de fallback para un modelo (siempre a modelo superior)
        IMPORTANTE: El fallback siempre va a un modelo mÃ¡s potente, nunca a uno menor
        """
        chains = {
            ModelType.GPT5_MINI: [ModelType.GPT5_MINI, ModelType.GPT5],  # Fallback a GPT-5 (superior)
            ModelType.GPT5: [ModelType.GPT5, ModelType.GPT4O],  # Fallback a GPT-4o (mÃ¡s potente)
            ModelType.GPT4O_MINI: [ModelType.GPT4O_MINI, ModelType.GPT4O],  # Fallback a GPT-4o
            ModelType.GPT4O: [ModelType.GPT4O]  # No hay fallback superior
        }
        return chains.get(model, [model])
    
    def route_single_extended(self, product: Dict[str, Any]) -> Tuple[str, float, str]:
        """
        Routing extendido con informaciÃ³n detallada
        Returns: (model_name, complexity_score, routing_reason)
        """
        model_type, complexity = self.route_single(product)
        
        if complexity <= self.thresholds['simple']:
            reason = f"Simple product (complexity={complexity:.2f})"
        elif complexity >= self.thresholds['complex']:
            reason = f"Complex product (complexity={complexity:.2f})"
        else:
            reason = f"Medium complexity (complexity={complexity:.2f})"
        
        return model_type.value, complexity, reason
    
    def _estimate_batch_cost(self, products: List[Dict[str, Any]], config: ModelConfig) -> float:
        """Estima costo de procesar un batch"""
        avg_tokens_per_product = 150  # Estimado
        total_tokens = len(products) * avg_tokens_per_product
        
        # Aplicar descuento batch (50%)
        base_cost = (total_tokens / 1000) * config.cost_per_1k_tokens
        batch_cost = base_cost * config.batch_discount
        
        return round(batch_cost, 4)
    
    def _calculate_priority(self, model_type: ModelType, batch_size: int) -> float:
        """
        Calcula prioridad de procesamiento
        Favorece batches grandes de modelos econÃ³micos
        """
        model_weights = {
            ModelType.GPT5_MINI: 1.0,  # MÃ¡xima prioridad
            ModelType.GPT5: 0.5,  # Media prioridad
            ModelType.GPT4O_MINI: 0.3  # Baja prioridad (fallback)
        }
        
        return model_weights.get(model_type, 0.1) * batch_size
    
    def get_fallback_chain(self, primary_model: ModelType) -> List[ModelType]:
        """
        Cadena de fallback: gpt-5-mini → gpt-5. Sin 4o/4o-mini.
        """
        chains = {
            ModelType.GPT5_MINI: [ModelType.GPT5_MINI, ModelType.GPT5],
            ModelType.GPT5: [ModelType.GPT5],
        }
        return chains.get(primary_model, [ModelType.GPT5_MINI])
    
    def estimate_savings(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcula ahorro estimado usando routing inteligente + batch
        """
        batches = self.route_batch(products)
        optimized = self.optimize_batches(batches)
        
        # Costo con modelo Ãºnico (GPT-4o-mini)
        baseline_config = self.models[ModelType.GPT4O_MINI]
        baseline_cost = len(products) * 150 / 1000 * baseline_config.cost_per_1k_tokens
        
        # Costo con routing + batch
        optimized_cost = sum(batch['estimated_cost'] for batch in optimized)
        
        # Ahorro
        savings = baseline_cost - optimized_cost
        savings_percent = (savings / baseline_cost * 100) if baseline_cost > 0 else 0
        
        return {
            'total_products': len(products),
            'baseline_cost_usd': round(baseline_cost, 2),
            'optimized_cost_usd': round(optimized_cost, 2),
            'savings_usd': round(savings, 2),
            'savings_percent': round(savings_percent, 1),
            'batch_count': len(optimized),
            'distribution': {
                model.value: len(products) 
                for model, products in batches.items() if products
            }
        }


if __name__ == "__main__":
    # Test del router
    router = GPT5Router()
    
    test_products = [
        {"name": "iPhone 15 Pro Max 256GB Negro", "category": "smartphones", "price": 1200000},
        {"name": "Perfume Chanel No 5 100ml", "category": "perfumes", "price": 150000},
        {"name": "Notebook ASUS ROG Strix G16 RTX 4070 32GB RAM 1TB SSD", "category": "notebooks", "price": 2500000},
        {"name": "Coca Cola 500ml", "category": "beverages", "price": 1500},
        {"name": "Samsung Galaxy S24 Ultra 512GB 5G", "category": "smartphones", "price": 1500000},
    ]
    
    # Test routing individual
    print("ðŸŽ¯ Individual Routing:")
    for product in test_products:
        model, complexity = router.route_single(product)
        print(f"  {product['name'][:40]}: {model.value} (complexity: {complexity:.2f})")
    
    # Test batch routing
    print("\nðŸ“¦ Batch Processing:")
    savings = router.estimate_savings(test_products * 20)  # Simular 100 productos
    print(f"  Total Products: {savings['total_products']}")
    print(f"  Baseline Cost: ${savings['baseline_cost_usd']}")
    print(f"  Optimized Cost: ${savings['optimized_cost_usd']}")
    print(f"  Savings: ${savings['savings_usd']} ({savings['savings_percent']}%)")
    print(f"  Distribution: {savings['distribution']}")
