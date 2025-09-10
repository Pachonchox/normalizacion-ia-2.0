#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 Prompts Específicos Optimizados para GPT-5
Prompts por modelo, categoría y modo de procesamiento
"""

from enum import Enum
from typing import Dict, Any

class PromptMode(Enum):
    """Modos de prompt según contexto"""
    MINIMAL = "minimal"      # 30 tokens - Ultra compacto para batch
    BATCH = "batch"          # 40 tokens - Optimizado batch
    STANDARD = "standard"    # 100 tokens - Balance calidad/costo
    DETAILED = "detailed"    # 200 tokens - Máxima precisión
    FALLBACK = "fallback"    # Variable - Corrección con contexto

class PromptManager:
    """Gestor de prompts optimizados por modelo y categoría"""
    
    def __init__(self):
        self.version = "v2.0"
        self._init_prompts()
        self._init_system_prompts()
    
    def _init_system_prompts(self):
        """System prompts por modelo"""
        self.system_prompts = {
            "gpt-5-mini": "Eres un experto en normalización de productos retail chilenos. Responde SOLO en formato JSON válido sin texto adicional.",
            "gpt-5": "Eres un especialista en análisis de productos retail con conocimiento profundo del mercado chileno. Genera JSON estructurado y preciso.",
            "gpt-4o-mini": "Experto retail Chile. Solo JSON válido RFC 8259.",
            "gpt-4o": "Analista experto de productos retail chilenos. Respuesta exclusivamente en JSON válido con alta precisión."
        }
    
    def _init_prompts(self):
        """Definir todos los prompts específicos"""
        self.prompts = {
            "gpt-5-mini": {
                "smartphones": {
                    PromptMode.MINIMAL: self._minimal_smartphone,
                    PromptMode.BATCH: self._batch_smartphone,
                    PromptMode.STANDARD: self._standard_smartphone
                },
                "notebooks": {
                    PromptMode.MINIMAL: self._minimal_notebook,
                    PromptMode.BATCH: self._batch_notebook,
                    PromptMode.STANDARD: self._standard_notebook
                },
                "smart_tv": {
                    PromptMode.MINIMAL: self._minimal_tv,
                    PromptMode.BATCH: self._batch_tv,
                    PromptMode.STANDARD: self._standard_tv
                },
                "perfumes": {
                    PromptMode.MINIMAL: self._minimal_perfume,
                    PromptMode.BATCH: self._batch_perfume,
                    PromptMode.STANDARD: self._standard_perfume
                },
                "default": {
                    PromptMode.MINIMAL: self._minimal_default,
                    PromptMode.BATCH: self._batch_default,
                    PromptMode.STANDARD: self._standard_default
                }
            },
            "gpt-5": {
                "smartphones": {PromptMode.DETAILED: self._detailed_smartphone},
                "notebooks": {PromptMode.DETAILED: self._detailed_notebook},
                "smart_tv": {PromptMode.DETAILED: self._detailed_tv},
                "perfumes": {PromptMode.DETAILED: self._detailed_perfume},
                "default": {PromptMode.DETAILED: self._detailed_default}
            },
            "gpt-4o-mini": {
                "all": {PromptMode.FALLBACK: self._fallback_prompt}
            },
            "gpt-4o": {
                "all": {PromptMode.FALLBACK: self._fallback_detailed}
            }
        }
    
    def get_prompt(self, model: str, category: str, mode: PromptMode, 
                   product: Dict[str, Any], **kwargs) -> str:
        """Obtener prompt apropiado"""
        
        # Buscar prompt específico
        model_prompts = self.prompts.get(model, {})
        
        # Intentar categoría específica
        category_prompts = model_prompts.get(category, {})
        if not category_prompts:
            # Fallback a default o all
            category_prompts = model_prompts.get("default", model_prompts.get("all", {}))
        
        # Obtener función de prompt
        prompt_func = category_prompts.get(mode)
        
        if prompt_func:
            return prompt_func(product, **kwargs)
        
        # Fallback a standard
        return self._standard_default(product)
    
    # ============================================================================
    # SMARTPHONES - Prompts
    # ============================================================================
    
    def _minimal_smartphone(self, product: Dict, **kwargs) -> str:
        """Ultra compacto para batch masivo"""
        return f"N:{product.get('name', '')[:80]}|C:smartphones|$:{product.get('price', 0)}"
    
    def _batch_smartphone(self, product: Dict, **kwargs) -> str:
        """Optimizado para batch"""
        return f"""Smartphone:{product.get('name', '')[:100]}[${product.get('price', 0)}]
JSON:brand,model,capacity,color,screen_size,network"""
    
    def _standard_smartphone(self, product: Dict, **kwargs) -> str:
        """Balance calidad/costo"""
        return f"""Normaliza el siguiente smartphone:

PRODUCTO: "{product.get('name', '')}"
PRECIO: ${product.get('price', 0):,} CLP
RETAILER: "{product.get('retailer', '')}"

Extrae y estructura en JSON:
{{
  "brand": "MARCA_MAYUSCULAS",
  "model": "modelo sin marca",
  "normalized_name": "MARCA Modelo Capacidad Color",
  "attributes": {{
    "capacity": "128GB/256GB/512GB/1TB",
    "color": "color en español",
    "screen_size": "pulgadas como número",
    "network": "4G/5G"
  }},
  "confidence": 0.00,
  "category_suggestion": "smartphones"
}}"""
    
    def _detailed_smartphone(self, product: Dict, **kwargs) -> str:
        """Análisis exhaustivo con GPT-5"""
        return f"""Analiza exhaustivamente este smartphone del mercado chileno:

DATOS DE ENTRADA:
- Nombre completo: "{product.get('name', '')}"
- Precio CLP: ${product.get('price', 0):,}
- Retailer: {product.get('retailer', '')}
- SKU/ID: {product.get('sku', 'N/A')}

INSTRUCCIONES DE EXTRACCIÓN:
1. Identificar marca exacta (verificar aliases y variaciones)
2. Extraer modelo completo con variante si existe
3. Detectar TODOS los atributos técnicos presentes
4. Normalizar nombre para matching inter-retail
5. Evaluar confianza basada en completitud de datos

ESTRUCTURA JSON REQUERIDA:
{{
  "brand": "MARCA_OFICIAL_MAYUSCULAS",
  "model": "modelo completo con variante",
  "normalized_name": "MARCA Modelo Capacidad Color (atributos clave)",
  "attributes": {{
    "capacity": "almacenamiento exacto",
    "color": "color normalizado",
    "screen_size": "tamaño en pulgadas",
    "network": "tecnología de red",
    "processor": "procesador si se menciona",
    "ram": "RAM si se menciona",
    "camera": "MP cámara principal si se menciona"
  }},
  "confidence": 0.00,
  "category_suggestion": "smartphones",
  "extraction_notes": "notas sobre ambigüedades o inferencias"
}}"""
    
    # ============================================================================
    # NOTEBOOKS - Prompts
    # ============================================================================
    
    def _minimal_notebook(self, product: Dict, **kwargs) -> str:
        return f"N:{product.get('name', '')[:80]}|C:notebooks|$:{product.get('price', 0)}"
    
    def _batch_notebook(self, product: Dict, **kwargs) -> str:
        return f"""Notebook:{product.get('name', '')[:100]}[${product.get('price', 0)}]
JSON:brand,model,screen_size,ram,storage,processor"""
    
    def _standard_notebook(self, product: Dict, **kwargs) -> str:
        return f"""Normaliza el siguiente notebook:

PRODUCTO: "{product.get('name', '')}"
PRECIO: ${product.get('price', 0):,} CLP

Estructura JSON:
{{
  "brand": "MARCA_MAYUSCULAS",
  "model": "modelo sin marca",
  "normalized_name": "MARCA Modelo RAM Storage",
  "attributes": {{
    "screen_size": "pulgadas",
    "ram": "GB RAM",
    "storage": "capacidad y tipo",
    "processor": "procesador si se menciona"
  }},
  "confidence": 0.00,
  "category_suggestion": "notebooks"
}}"""
    
    def _detailed_notebook(self, product: Dict, **kwargs) -> str:
        return f"""Análisis detallado de notebook:

ENTRADA: "{product.get('name', '')}"
PRECIO: ${product.get('price', 0):,} CLP

Extraer TODO incluyendo:
- Marca y línea de producto
- Procesador específico (generación)
- RAM (capacidad y tipo)
- Almacenamiento (SSD/HDD, capacidad)
- Pantalla (tamaño, resolución si existe)
- GPU si se menciona
- Sistema operativo

JSON con todos los atributos detectados."""
    
    # ============================================================================
    # SMART TV - Prompts
    # ============================================================================
    
    def _minimal_tv(self, product: Dict, **kwargs) -> str:
        return f"N:{product.get('name', '')[:80]}|C:smart_tv|$:{product.get('price', 0)}"
    
    def _batch_tv(self, product: Dict, **kwargs) -> str:
        return f"""TV:{product.get('name', '')[:100]}[${product.get('price', 0)}]
JSON:brand,model,screen_size,panel,resolution"""
    
    def _standard_tv(self, product: Dict, **kwargs) -> str:
        return f"""Normaliza Smart TV:

"{product.get('name', '')}"
${product.get('price', 0):,} CLP

JSON:
{{
  "brand": "MARCA",
  "model": "modelo",
  "normalized_name": "MARCA Modelo Pulgadas Panel",
  "attributes": {{
    "screen_size": "pulgadas",
    "panel": "OLED/QLED/LED/4K/8K",
    "resolution": "4K/8K/FHD/HD"
  }},
  "confidence": 0.00,
  "category_suggestion": "smart_tv"
}}"""
    
    def _detailed_tv(self, product: Dict, **kwargs) -> str:
        return f"""Smart TV análisis completo:
{product.get('name', '')}

Extraer marca, línea, tecnología de panel, resolución, 
smart features, HDR, audio, año si existe."""
    
    # ============================================================================
    # PERFUMES - Prompts
    # ============================================================================
    
    def _minimal_perfume(self, product: Dict, **kwargs) -> str:
        return f"N:{product.get('name', '')[:80]}|C:perfumes|$:{product.get('price', 0)}"
    
    def _batch_perfume(self, product: Dict, **kwargs) -> str:
        return f"""Perfume:{product.get('name', '')[:100]}[${product.get('price', 0)}]
JSON:brand,model,volume_ml,concentration,gender"""
    
    def _standard_perfume(self, product: Dict, **kwargs) -> str:
        return f"""Normaliza perfume:

"{product.get('name', '')}"
${product.get('price', 0):,} CLP

JSON:
{{
  "brand": "MARCA",
  "model": "fragancia",
  "normalized_name": "MARCA Fragancia Volume Tipo",
  "attributes": {{
    "volume_ml": numero_entero,
    "concentration": "EDP/EDT/Parfum/Cologne",
    "gender": "Mujer/Hombre/Unisex"
  }},
  "confidence": 0.00,
  "category_suggestion": "perfumes"
}}"""
    
    def _detailed_perfume(self, product: Dict, **kwargs) -> str:
        return f"""Perfume análisis:
{product.get('name', '')}

Identificar marca exacta, línea de fragancia, 
volumen en ml, concentración (EDP/EDT/Parfum),
género target, notas si se mencionan."""
    
    # ============================================================================
    # DEFAULT - Prompts genéricos
    # ============================================================================
    
    def _minimal_default(self, product: Dict, **kwargs) -> str:
        return f"N:{product.get('name', '')[:100]}|C:{product.get('category', '')}|$:{product.get('price', 0)}"
    
    def _batch_default(self, product: Dict, **kwargs) -> str:
        return f"""Producto:{product.get('name', '')[:120]}[{product.get('category', '')}]
Precio:${product.get('price', 0)}
JSON:brand,model,normalized_name,attributes,confidence"""
    
    def _standard_default(self, product: Dict, **kwargs) -> str:
        return f"""Normaliza producto:

NOMBRE: "{product.get('name', '')}"
CATEGORÍA: "{product.get('category', '')}"
PRECIO: ${product.get('price', 0):,} CLP

Estructura JSON con:
- brand (marca en mayúsculas)
- model (modelo sin marca)
- normalized_name (nombre limpio)
- attributes (objeto con atributos relevantes)
- confidence (0.0 a 1.0)
- category_suggestion (si difiere)"""
    
    def _detailed_default(self, product: Dict, **kwargs) -> str:
        return f"""Análisis exhaustivo:

PRODUCTO COMPLETO: {product.get('name', '')}
CATEGORÍA BASE: {product.get('category', '')}
PRECIO: ${product.get('price', 0):,} CLP
RETAILER: {product.get('retailer', '')}

Extraer TODOS los atributos detectables.
Normalizar para comparación inter-retail.
Evaluar confianza de extracción."""
    
    # ============================================================================
    # FALLBACK - Prompts de corrección
    # ============================================================================
    
    def _fallback_prompt(self, product: Dict, **kwargs) -> str:
        """Fallback básico para corrección"""
        previous = kwargs.get('previous_attempt', {})
        error = kwargs.get('error', 'JSON inválido o incompleto')
        
        return f"""Corrige el siguiente resultado:

PRODUCTO ORIGINAL: "{product.get('name', '')}"
CATEGORÍA: "{product.get('category', '')}"

INTENTO ANTERIOR:
{previous}

ERROR: {error}

Genera JSON válido corregido con todos los campos requeridos:
brand, model, normalized_name, attributes, confidence, category_suggestion"""
    
    def _fallback_detailed(self, product: Dict, **kwargs) -> str:
        """Fallback detallado con GPT-4o"""
        previous = kwargs.get('previous_attempt', {})
        error = kwargs.get('error', '')
        
        return f"""Análisis y corrección experta:

CONTEXTO:
- Producto: "{product.get('name', '')}"
- Categoría: "{product.get('category', '')}"
- Precio: ${product.get('price', 0):,} CLP
- Retailer: {product.get('retailer', '')}

PROBLEMA DETECTADO:
{error}

INTENTO PREVIO:
{previous}

INSTRUCCIONES:
1. Identificar qué faltó o falló en el intento anterior
2. Completar TODOS los campos requeridos
3. Inferir datos faltantes con alta precisión
4. Asegurar JSON válido y completo

ESTRUCTURA REQUERIDA:
{{
  "brand": "obligatorio",
  "model": "obligatorio", 
  "normalized_name": "obligatorio",
  "attributes": {{}},
  "confidence": 0.0,
  "category_suggestion": "opcional"
}}"""
    
    def get_tokens_estimate(self, mode: PromptMode) -> int:
        """Estimar tokens por modo"""
        estimates = {
            PromptMode.MINIMAL: 30,
            PromptMode.BATCH: 40,
            PromptMode.STANDARD: 100,
            PromptMode.DETAILED: 200,
            PromptMode.FALLBACK: 150
        }
        return estimates.get(mode, 100)

# ============================================================================
# Singleton para uso global
# ============================================================================

_prompt_manager = None

def get_prompt_manager() -> PromptManager:
    """Obtener instancia singleton del gestor de prompts"""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager

if __name__ == "__main__":
    # Testing
    pm = get_prompt_manager()
    
    test_product = {
        "name": "iPhone 15 Pro Max 256GB Negro Liberado",
        "category": "smartphones",
        "price": 1299990,
        "retailer": "Falabella"
    }
    
    # Test diferentes modos
    for mode in [PromptMode.MINIMAL, PromptMode.BATCH, PromptMode.STANDARD]:
        prompt = pm.get_prompt("gpt-5-mini", "smartphones", mode, test_product)
        tokens = pm.get_tokens_estimate(mode)
        print(f"\n=== {mode.value.upper()} ({tokens} tokens) ===")
        print(prompt[:200] + "..." if len(prompt) > 200 else prompt)