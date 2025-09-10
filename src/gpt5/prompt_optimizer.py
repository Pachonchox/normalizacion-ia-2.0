#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📝 GPT-5 Prompt Optimizer
Sistema adaptativo de prompts que optimiza tokens y calidad según modelo
Reduce costos mediante prompts minimalistas para casos simples
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from enum import Enum
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PromptStyle(Enum):
    """Estilos de prompt según complejidad"""
    MINIMAL = "minimal"  # Ultra-compacto para GPT-5-mini
    STANDARD = "standard"  # Balanceado
    DETAILED = "detailed"  # Completo para GPT-5
    BATCH = "batch"  # Optimizado para batch processing


class PromptOptimizer:
    """
    Optimizador de prompts adaptativo para GPT-5
    Minimiza tokens mientras mantiene calidad
    """
    
    def __init__(self):
        self.templates = self._load_templates()
        self.token_estimates = {
            PromptStyle.MINIMAL: 50,
            PromptStyle.STANDARD: 100,
            PromptStyle.DETAILED: 200,
            PromptStyle.BATCH: 40  # Ultra-optimizado para batch
        }
    
    def _load_templates(self) -> Dict[str, Dict[str, str]]:
        """Carga templates optimizados por modelo y estilo"""
        return {
            "gpt-5-mini": {
                PromptStyle.MINIMAL: self._get_minimal_template(),
                PromptStyle.STANDARD: self._get_standard_template(),
                PromptStyle.BATCH: self._get_batch_template()
            },
            "gpt-5": {
                PromptStyle.STANDARD: self._get_standard_template(),
                PromptStyle.DETAILED: self._get_detailed_template()
            },
            "gpt-4o-mini": {
                PromptStyle.STANDARD: self._get_legacy_template()
            }
        }
    
    def _get_minimal_template(self) -> str:
        """
        Template ultra-minimalista para GPT-5-mini
        ~50 tokens promedio
        """
        return """{name}
Cat:{category}
${price}

JSON:
{{brand,model,attrs:{{cap,color,size}},conf}}"""
    
    def _get_batch_template(self) -> str:
        """
        Template optimizado para batch processing
        ~40 tokens, máxima eficiencia
        """
        return """P:{name}|C:{category}|$:{price}
Out:{{b,m,a:{{c,cl,s}},cf}}"""
    
    def _get_standard_template(self) -> str:
        """
        Template estándar balanceado
        ~100 tokens
        """
        return """Producto: {name}
Categoría: {category}
Precio: ${price} CLP
Retailer: {retailer}

Normaliza a JSON:
{{
  "brand": "marca detectada",
  "model": "modelo específico",
  "attributes": {{
    "capacity": "si aplica",
    "color": "si detectado",
    "size": "tamaño/dimensión"
  }},
  "confidence": 0.0-1.0
}}"""
    
    def _get_detailed_template(self) -> str:
        """
        Template detallado para GPT-5 full
        ~200 tokens, máxima precisión
        """
        return """Analiza el siguiente producto chileno para sistema de comparación de precios:

PRODUCTO: {name}
CATEGORÍA: {category}
PRECIO: ${price} CLP
RETAILER: {retailer}
SKU: {sku}

Extrae y normaliza TODOS los atributos relevantes para matching inter-retail.
Considera variantes, especificaciones técnicas y características diferenciadoras.

Responde en JSON con estructura completa:
{{
  "brand": "marca normalizada en mayúsculas",
  "model": "modelo específico sin marca",
  "attributes": {{
    "capacity": "capacidad de almacenamiento",
    "color": "color normalizado",
    "size": "tamaño o diagonal de pantalla",
    "ram": "memoria RAM si aplica",
    "network": "tipo de red (5G, 4G, WiFi)",
    "volume_ml": "volumen para perfumes/líquidos",
    "screen_type": "tipo de pantalla (OLED, LCD, etc)"
  }},
  "normalized_name": "nombre limpio y consistente",
  "confidence": 0.95,
  "category_suggestion": "categoría si difiere de la actual"
}}

Asegura consistencia para comparación precisa entre retailers."""
    
    def _get_legacy_template(self) -> str:
        """Template para fallback a GPT-4o-mini"""
        return """Normaliza producto retail:
{name} | {category} | ${price}

JSON: {{brand, model, attributes: {{capacity, color}}, confidence}}"""
    
    def optimize_prompt(self, product: Dict[str, Any], model: str, 
                        style: Optional[PromptStyle] = None) -> str:
        """
        Genera prompt optimizado según modelo y complejidad
        """
        # Determinar estilo si no se especifica
        if style is None:
            style = self._determine_style(product, model)
        
        # Obtener template
        template = self.templates.get(model, {}).get(style)
        if not template:
            # Fallback a standard
            template = self.templates.get(model, {}).get(PromptStyle.STANDARD, "")
        
        # Formatear con datos del producto
        return self._format_template(template, product)
    
    def _determine_style(self, product: Dict[str, Any], model: str) -> PromptStyle:
        """
        Determina estilo óptimo basado en complejidad
        """
        # Para batch processing siempre usar BATCH
        if product.get('_batch_mode'):
            return PromptStyle.BATCH
        
        # Para GPT-5-mini preferir MINIMAL
        if model == "gpt-5-mini":
            complexity = product.get('_routing_metadata', {}).get('complexity_score', 0.3)
            if complexity < 0.2:
                return PromptStyle.MINIMAL
            else:
                return PromptStyle.STANDARD
        
        # Para GPT-5 usar STANDARD o DETAILED
        elif model == "gpt-5":
            complexity = product.get('_routing_metadata', {}).get('complexity_score', 0.5)
            if complexity > 0.8:
                return PromptStyle.DETAILED
            else:
                return PromptStyle.STANDARD
        
        # Default
        return PromptStyle.STANDARD
    
    def _format_template(self, template: str, product: Dict[str, Any]) -> str:
        """
        Formatea template con datos del producto
        Maneja valores faltantes elegantemente
        """
        # Preparar datos con defaults
        data = {
            'name': product.get('name', ''),
            'category': product.get('category', 'general'),
            'price': product.get('price', 0),
            'retailer': product.get('retailer', ''),
            'sku': product.get('sku', ''),
        }
        
        # Limpiar datos para reducir tokens
        data = {k: self._clean_value(v) for k, v in data.items()}
        
        try:
            return template.format(**data)
        except KeyError as e:
            logger.warning(f"Missing key in template: {e}")
            return template.format_map(DefaultDict(data))
    
    def _clean_value(self, value: Any) -> str:
        """
        Limpia valores para minimizar tokens
        """
        if isinstance(value, str):
            # Remover espacios extra
            value = ' '.join(value.split())
            # Truncar si es muy largo
            if len(value) > 200:
                value = value[:197] + "..."
        elif value is None:
            value = ""
        
        return str(value)
    
    def optimize_batch_prompts(self, products: List[Dict[str, Any]], 
                              model: str) -> List[str]:
        """
        Optimiza prompts para procesamiento batch masivo
        Máxima eficiencia en tokens
        """
        # Marcar productos para batch mode
        for product in products:
            product['_batch_mode'] = True
        
        # Generar prompts optimizados
        prompts = []
        for product in products:
            prompt = self.optimize_prompt(product, model, PromptStyle.BATCH)
            prompts.append(prompt)
        
        logger.info(f"📦 Optimized {len(prompts)} batch prompts for {model}")
        return prompts
    
    def estimate_tokens(self, prompt: str, style: PromptStyle) -> int:
        """
        Estima tokens del prompt
        Útil para calcular costos
        """
        # Estimación simple: ~1.3 tokens por palabra en español/inglés
        word_count = len(prompt.split())
        base_estimate = int(word_count * 1.3)
        
        # Ajustar según estilo
        style_multiplier = {
            PromptStyle.MINIMAL: 0.8,
            PromptStyle.BATCH: 0.7,
            PromptStyle.STANDARD: 1.0,
            PromptStyle.DETAILED: 1.2
        }
        
        return int(base_estimate * style_multiplier.get(style, 1.0))
    
    def get_system_prompt(self, model: str, context: str = "retail_cl") -> str:
        """
        Obtiene system prompt optimizado por modelo
        """
        prompts = {
            "gpt-5-mini": "Experto en productos retail CL. JSON only.",
            "gpt-5": "Experto en normalización de productos retail chilenos. Responde en JSON estructurado.",
            "gpt-4o-mini": "Normaliza productos retail. Responde solo en JSON válido."
        }
        
        return prompts.get(model, prompts["gpt-5-mini"])
    
    def create_few_shot_examples(self, category: str) -> List[Dict[str, str]]:
        """
        Crea ejemplos few-shot para mejorar precisión
        Especialmente útil para categorías complejas
        """
        examples = {
            "smartphones": [
                {
                    "input": "iPhone 15 Pro Max 256GB Negro Liberado",
                    "output": json.dumps({
                        "brand": "APPLE",
                        "model": "iPhone 15 Pro Max",
                        "attributes": {
                            "capacity": "256GB",
                            "color": "negro",
                            "network": "liberado"
                        },
                        "confidence": 0.98
                    }, ensure_ascii=False)
                }
            ],
            "perfumes": [
                {
                    "input": "Perfume Chanel No 5 EDP 100ml Mujer",
                    "output": json.dumps({
                        "brand": "CHANEL",
                        "model": "No 5",
                        "attributes": {
                            "volume_ml": "100",
                            "type": "EDP",
                            "gender": "mujer"
                        },
                        "confidence": 0.96
                    }, ensure_ascii=False)
                }
            ]
        }
        
        return examples.get(category, [])


class DefaultDict(dict):
    """Helper para template formatting con defaults"""
    def __init__(self, data):
        super().__init__(data)
    
    def __missing__(self, key):
        return ""


if __name__ == "__main__":
    # Test del optimizador
    optimizer = PromptOptimizer()
    
    # Producto simple
    simple_product = {
        "name": "Coca Cola 500ml",
        "category": "beverages",
        "price": 1500,
        "_routing_metadata": {"complexity_score": 0.1}
    }
    
    # Producto complejo
    complex_product = {
        "name": "MacBook Pro 16 M3 Max 48GB RAM 1TB SSD Space Gray",
        "category": "notebooks",
        "price": 3500000,
        "retailer": "Falabella",
        "_routing_metadata": {"complexity_score": 0.9}
    }
    
    # Test diferentes modelos y estilos
    print("🎯 Prompt Optimization Tests:\n")
    
    # GPT-5-mini con producto simple
    prompt1 = optimizer.optimize_prompt(simple_product, "gpt-5-mini")
    print(f"GPT-5-mini (simple):\n{prompt1}\n")
    print(f"Estimated tokens: {optimizer.estimate_tokens(prompt1, PromptStyle.MINIMAL)}\n")
    
    # GPT-5 con producto complejo
    prompt2 = optimizer.optimize_prompt(complex_product, "gpt-5")
    print(f"GPT-5 (complex):\n{prompt2[:200]}...\n")
    print(f"Estimated tokens: {optimizer.estimate_tokens(prompt2, PromptStyle.DETAILED)}\n")
    
    # Batch optimization
    batch_products = [simple_product, complex_product] * 10
    batch_prompts = optimizer.optimize_batch_prompts(batch_products, "gpt-5-mini")
    print(f"Batch prompts generated: {len(batch_prompts)}")
    print(f"Sample batch prompt:\n{batch_prompts[0]}\n")
    
    # Few-shot examples
    examples = optimizer.create_few_shot_examples("smartphones")
    print(f"Few-shot examples: {len(examples)} for smartphones")