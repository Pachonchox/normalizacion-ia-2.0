#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 LLM Connectors Optimizado
Sistema IA optimizado para grandes volúmenes con reintentos, timeouts y cache inteligente
"""

from __future__ import annotations
import os
import json
import time
import random
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class LLMOptimizer:
    """Optimizador para consultas IA con reintentos y cache inteligente"""
    
    def __init__(self):
        self.max_retries = 3
        self.base_timeout = 20  # segundos
        self.rate_limit_delay = 1.0  # segundos entre requests
        self.last_request_time = 0
        
    def enabled(self) -> bool:
        return os.environ.get("LLM_ENABLED","false").lower() in ("1","true","yes")
    
    def extract_with_llm_optimized(self, title: str, category: str = "") -> Dict[str, Any]:
        """
        Extracción IA optimizada con reintentos, timeouts progresivos y rate limiting
        """
        if not self.enabled():
            return {"error": "llm_disabled", "confidence": 0.0}
        
        for attempt in range(self.max_retries + 1):
            try:
                # Rate limiting - esperar entre requests
                self._wait_rate_limit()
                
                # Timeout progresivo: 20s, 30s, 45s
                timeout = self.base_timeout + (attempt * 10)
                
                result = self._make_llm_request(title, category, timeout)
                
                if "error" not in result:
                    return result
                
                # Si es error de rate limit, esperar más tiempo
                if "rate_limit" in str(result.get("error", "")).lower():
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"   IA: Rate limit detectado, esperando {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                # Si es último intento, devolver el error
                if attempt == self.max_retries:
                    return result
                    
                print(f"   IA: Intento {attempt + 1} falló, reintentando...")
                time.sleep(1 + attempt)  # Backoff progresivo
                
            except Exception as e:
                print(f"   IA: Error intento {attempt + 1}: {e}")
                if attempt == self.max_retries:
                    return {"error": f"max_retries_exceeded: {str(e)}", "confidence": 0.0}
                time.sleep(2 + attempt)
        
        return {"error": "unknown_failure", "confidence": 0.0}
    
    def _wait_rate_limit(self):
        """Implementar rate limiting simple"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _make_llm_request(self, title: str, category: str, timeout: int) -> Dict[str, Any]:
        """Hacer request IA individual con timeout específico"""
        
        try:
            import openai
        except ImportError:
            return {"error": "openai_not_installed", "confidence": 0.0}
        
        # Configurar cliente OpenAI
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return {"error": "openai_api_key_missing", "confidence": 0.0}
        
        client = openai.OpenAI(api_key=api_key)
        
        # Prompt optimizado y más corto para reducir tokens
        prompt = f"""
Extrae metadatos del producto chileno:
PRODUCTO: "{title}"
CATEGORÍA: "{category}"

Responde SOLO JSON:
{{
    "brand": "marca (ej: APPLE, SAMSUNG)",
    "model": "modelo específico", 
    "refined_attributes": {{
        "capacity": "capacidad si aplica",
        "color": "color si aplica",
        "screen_size": "pantalla si aplica", 
        "volume_ml": "volumen perfumes",
        "network": "red móvil si aplica",
        "ram": "RAM si aplica"
    }},
    "normalized_name": "nombre limpio",
    "confidence": 0.95
}}
"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Modelo más rápido
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=300,  # Reducido para respuesta más rápida
            timeout=timeout
        )
        
        # Parsear respuesta
        content = response.choices[0].message.content.strip()
        
        # Limpiar markdown
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
        
        ai_data = json.loads(content)
        
        # Validar estructura básica
        if not isinstance(ai_data, dict) or "brand" not in ai_data:
            return {"error": "invalid_structure", "confidence": 0.0}
        
        # Asegurar confidence
        if "confidence" not in ai_data:
            ai_data["confidence"] = 0.85
        
        return ai_data

    def batch_process_products(self, products: List[Dict[str, Any]], batch_size: int = 5) -> List[Dict[str, Any]]:
        """
        Procesar productos en lotes para evitar saturar la API
        """
        results = []
        total_batches = (len(products) + batch_size - 1) // batch_size
        
        print(f"   IA: Procesando {len(products)} productos en {total_batches} lotes de {batch_size}")
        
        for i in range(0, len(products), batch_size):
            batch = products[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            print(f"   IA: Procesando lote {batch_num}/{total_batches}...")
            
            batch_results = []
            for product in batch:
                name = product.get('name', '')
                category = product.get('category', '')
                
                result = self.extract_with_llm_optimized(name, category)
                batch_results.append(result)
                
                # Pequeña pausa entre productos del mismo lote
                time.sleep(0.5)
            
            results.extend(batch_results)
            
            # Pausa más larga entre lotes
            if batch_num < total_batches:
                print(f"   IA: Pausa entre lotes...")
                time.sleep(3)
        
        return results

# Instancia global optimizada
_optimizer = LLMOptimizer()

def enabled() -> bool:
    """Verificar si IA está habilitada"""
    return _optimizer.enabled()

def extract_with_llm(title: str, category: str = "") -> Dict[str, Any]:
    """
    Interfaz compatible con sistema existente pero optimizada
    """
    return _optimizer.extract_with_llm_optimized(title, category)

def extract_batch_with_llm(products: List[Dict[str, Any]], batch_size: int = 5) -> List[Dict[str, Any]]:
    """
    Nueva función para procesamiento en lotes
    """
    return _optimizer.batch_process_products(products, batch_size)

def enrich_product_data(base_data: Dict[str, Any], ai_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Combina datos base con enriquecimiento IA manteniendo prioridades correctas
    """
    if "error" in ai_data:
        return base_data
    
    enriched = base_data.copy()
    
    # Enriquecer marca si IA es más específica
    if ai_data.get('brand') and len(ai_data['brand']) > len(base_data.get('brand', '')):
        enriched['brand'] = ai_data['brand']
    
    # Modelo mejorado
    if ai_data.get('model'):
        enriched['model'] = ai_data['model']
    
    # Nombre normalizado
    if ai_data.get('normalized_name'):
        enriched['name'] = ai_data['normalized_name']
    
    # Combinar atributos
    if ai_data.get('refined_attributes'):
        current_attrs = enriched.get('attributes', {})
        refined_attrs = ai_data['refined_attributes']
        
        for key, value in refined_attrs.items():
            if value and value != "N/A":  # Solo agregar valores válidos
                current_attrs[key] = value
        
        enriched['attributes'] = current_attrs
    
    return enriched

if __name__ == "__main__":
    # Test del optimizador
    print("=== TEST OPTIMIZADOR IA ===")
    
    test_products = [
        {"name": "iPhone 15 Pro Max 256GB", "category": "smartphones"},
        {"name": "Samsung QLED 65 Smart TV", "category": "smart_tv"},
        {"name": "MacBook Pro M3", "category": "notebooks"}
    ]
    
    optimizer = LLMOptimizer()
    
    if optimizer.enabled():
        print("Testing individual extraction...")
        result = optimizer.extract_with_llm_optimized("iPhone 15 Pro Max 256GB", "smartphones")
        print(f"Result: {result}")
        
        print("\nTesting batch processing...")
        batch_results = optimizer.batch_process_products(test_products, batch_size=2)
        print(f"Batch results: {len(batch_results)} processed")
    else:
        print("IA disabled - skipping tests")