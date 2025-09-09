\
from __future__ import annotations
import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

def enabled() -> bool:
    return os.environ.get("LLM_ENABLED","false").lower() in ("1","true","yes")

def extract_with_llm(title: str, category: str = "") -> Dict[str, Any]:
    """
    Extrae metadatos enriquecidos usando OpenAI para máxima calidad de normalización
    Enfocado en preparar datos perfectos para base de datos de comparación de precios 💎
    """
    if not enabled():
        return {}
    
    try:
        import openai
        
        # Configurar cliente OpenAI
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("⚠️  OPENAI_API_KEY no configurada")
            return {}
        
        client = openai.OpenAI(api_key=api_key)
        
        # Prompt optimizado para retail chileno 🇨🇱
        prompt = f"""
Eres un experto en productos retail chilenos. Extrae metadatos estructurados del siguiente producto:

PRODUCTO: "{title}"
CATEGORÍA: "{category}"

Responde SOLO en JSON válido con esta estructura exacta:
{{
    "brand": "marca normalizada (ej: APPLE, SAMSUNG)",
    "model": "modelo específico (ej: iPhone 16 Pro Max 256GB)",
    "refined_attributes": {{
        "capacity": "capacidad si aplica (ej: 256GB, 1TB)",
        "color": "color normalizado (ej: negro, blanco, azul)",
        "screen_size": "tamaño de pantalla si aplica (ej: 6.7, 55)",
        "volume_ml": "volumen en ml para perfumes (ej: 100)",
        "network": "red móvil si aplica (ej: 5G, 4G)",
        "ram": "RAM para tecnología (ej: 8GB, 16GB)",
        "storage": "almacenamiento (ej: 512GB SSD, 1TB)"
    }},
    "normalized_name": "nombre limpio y consistente",
    "confidence": 0.95,
    "category_suggestion": "categoría sugerida si difiere"
}}

Enfócate en datos que ayuden a comparar precios entre retailers chilenos.
"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Modelo más económico pero potente
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,  # Baja variabilidad para consistencia
            max_tokens=500,
            timeout=15
        )
        
        # Parsear respuesta JSON
        content = response.choices[0].message.content.strip()
        
        # Limpiar markdown si existe
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
            
        ai_data = json.loads(content)
        
        # Validar estructura mínima
        if not isinstance(ai_data, dict):
            return {"error": "Invalid JSON structure"}
            
        return ai_data
        
    except ImportError:
        print("⚠️  pip install openai requerido para IA")
        return {"error": "openai package not installed"}
    except json.JSONDecodeError as e:
        print(f"⚠️  Error parsing OpenAI JSON: {e}")
        return {"error": "json_parse_error", "raw_response": content}
    except Exception as e:
        print(f"⚠️  Error LLM: {e}")
        return {"error": str(e)}

def enrich_product_data(base_data: Dict[str, Any], ai_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Combina datos base con enriquecimiento IA manteniendo prioridades correctas
    """
    if not ai_data or "error" in ai_data:
        return base_data
    
    enriched = base_data.copy()
    
    # Mejorar marca si IA la detectó mejor
    if ai_data.get("brand") and not base_data.get("brand"):
        enriched["brand"] = ai_data["brand"]
    
    # Mejorar modelo si IA lo refinó
    if ai_data.get("model") and len(ai_data["model"]) > len(base_data.get("model", "")):
        enriched["model"] = ai_data["model"]
    
    # Enriquecer atributos con datos IA
    if ai_data.get("refined_attributes"):
        current_attrs = enriched.get("attributes", {})
        ai_attrs = ai_data["refined_attributes"]
        
        # Combinar atributos priorizando IA si es más específica
        for key, ai_value in ai_attrs.items():
            if ai_value and (not current_attrs.get(key) or len(str(ai_value)) > len(str(current_attrs.get(key, "")))):
                current_attrs[key] = ai_value
                
        enriched["attributes"] = current_attrs
    
    # Agregar metadatos de IA para auditoría
    enriched["ai_enhanced"] = True
    enriched["ai_confidence"] = ai_data.get("confidence", 0.0)
    
    return enriched
