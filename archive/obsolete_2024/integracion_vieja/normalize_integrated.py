#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔄 Normalización Integrada con Base de Datos
Sistema completo que usa BD para categorización, cache IA y persistencia
"""

import re
import hashlib
import os
from typing import Dict, Any, Tuple, Optional

# Imports con compatibilidad
try:
    from .utils import parse_price, slugify
    from .enrich import guess_brand, extract_attributes, clean_model
    from .fingerprint import product_fingerprint
    from .cache import JsonCache
    from .categorize_db import load_taxonomy, categorize_enhanced, get_brand_aliases
    from .db_persistence import get_persistence_instance
    from .unified_connector import get_unified_connector
    from .llm_connectors import extract_with_llm, enrich_product_data, enabled as llm_enabled
except ImportError:
    from utils import parse_price, slugify
    from enrich import guess_brand, extract_attributes, clean_model
    from fingerprint import product_fingerprint
    from cache import JsonCache
    from categorize_db import load_taxonomy, categorize_enhanced, get_brand_aliases
    from db_persistence import get_persistence_instance
    from unified_connector import get_unified_connector
    try:
        from llm_connectors_optimized import extract_with_llm, enrich_product_data, enabled as llm_enabled
    except ImportError:
        from llm_connectors import extract_with_llm, enrich_product_data, enabled as llm_enabled
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

PRICE_KEYS_PREF = [
    ("card_price", "card_price_text"),
    ("normal_price", "normal_price_text"),
    ("ripley_price", "ripley_price_text"),
]

# Instancias globales
_db_persistence = None
_db_connector = None
_taxonomy = None

def get_db_connector():
    """Obtener conector unificado y seguro"""
    return get_unified_connector()

def get_persistence():
    """Obtener instancia de persistencia (singleton)"""
    global _db_persistence
    if _db_persistence is None:
        _db_persistence = get_persistence_instance()
    return _db_persistence

def get_taxonomy_cached():
    """Obtener taxonomía cached"""
    global _taxonomy
    if _taxonomy is None:
        _taxonomy = load_taxonomy("../configs/taxonomy_v1.json")
    return _taxonomy

def pick_price(item: Dict[str, Any]) -> Tuple[Optional[int], Optional[int]]:
    """Extraer precios del item crudo"""
    # current
    current = None
    for numk, textk in PRICE_KEYS_PREF:
        if numk in item:
            current = parse_price(item.get(numk))
        if current is None and textk in item:
            current = parse_price(item.get(textk))
        if current is not None:
            break
    
    # original
    original = None
    for k in ("original_price", "original_price_text", "normal_price", "normal_price_text"):
        val = parse_price(item.get(k))
        if val:
            original = val
            break
    
    return current, original

def normalize_one_integrated(raw: Dict[str, Any], metadata: Dict[str, Any], retailer: str) -> Dict[str, Any]:
    """
    Normalización integrada completa con BD
    Incluye: categorización BD, cache IA BD, persistencia BD
    """
    
    name = raw.get("name") or raw.get("title") or ""
    url = raw.get("product_link") or raw.get("url") or None
    
    print(f">> Normalizando: {name[:50]}...")
    
    # 1️⃣ CATEGORIZACIÓN HÍBRIDA (BD + JSON fallback)
    taxonomy = get_taxonomy_cached()
    categorization = categorize_enhanced(name, metadata, taxonomy)
    
    category_id = categorization["category_id"]
    category_confidence = categorization["confidence"]
    
    print(f"   Categoría: {category_id} (conf: {category_confidence:.2f}, fuente: {categorization.get('source')})")
    
    # 2️⃣ EXTRACCIÓN BÁSICA DE PRECIOS Y MARCA
    price_curr, price_orig = pick_price(raw)
    if price_curr is None:
        # fallback: try any text with $
        for k, v in raw.items():
            if "price" in k and isinstance(v, str):
                p = parse_price(v)
                if p:
                    price_curr = p
                    break
    
    # Marca mejorada con aliases de BD
    brand_aliases = get_brand_aliases()
    brand = raw.get("brand") or guess_brand(name) or "DESCONOCIDA"
    
    # Normalizar marca usando aliases de BD
    brand_upper = brand.upper()
    for canonical, aliases in brand_aliases.items():
        if brand_upper in [alias.upper() for alias in aliases]:
            brand = canonical
            break
    
    # 3️⃣ ATRIBUTOS BASADOS EN CATEGORÍA
    attrs = extract_attributes(name, category_id)
    model = clean_model(name, brand)
    
    # 4️⃣ CREAR PRODUCTO BASE PARA FINGERPRINT
    base_product = {
        "brand": brand,
        "category": category_id,
        "model": model or name,
        "attributes": attrs
    }
    
    # 5️⃣ FINGERPRINT PARA CACHE IA Y MATCHING
    fingerprint = product_fingerprint(base_product)
    
    # 6️⃣ CACHE IA INDEFINIDO EN BD
    ai_data = {}
    ai_enhanced = False
    ai_confidence = 0.0
    
    if llm_enabled():
        try:
            db_connector = get_db_connector()
            ai_cache = db_connector  # El conector unificado ya tiene métodos de cache
            
            # Buscar en cache BD por fingerprint
            ai_data = ai_cache.get_ai_cache(fingerprint) or {}
            
            if not ai_data:
                print(f"   IA: Enriqueciendo por primera vez...")
                ai_data = extract_with_llm(name, category_id)
                
                if ai_data and "error" not in ai_data:
                    ai_cache.set_ai_cache(fingerprint, ai_data)
                    print(f"   IA: Cache guardado en BD (conf: {ai_data.get('confidence', 0):.2f})")
                    ai_enhanced = True
                    ai_confidence = ai_data.get('confidence', 0.0)
                else:
                    print(f"   IA: Error - {ai_data.get('error', 'unknown')}")
            else:
                print(f"   IA: Cache hit desde BD (conf: {ai_data.get('confidence', 0):.2f})")
                ai_enhanced = True
                ai_confidence = ai_data.get('confidence', 0.0)
                
        except Exception as e:
            print(f"   IA: Error cache BD: {e}")
            # Fallback a archivo si es necesario
            try:
                os.makedirs("out", exist_ok=True)
                ai_cache = JsonCache("out/ai_metadata_cache.json", ttl_days=0)
                ai_data = ai_cache.get(fingerprint) or {}
                if not ai_data and llm_enabled():
                    print(f"   IA: Fallback a archivo...")
                    ai_data = extract_with_llm(name, category_id)
                    if ai_data and "error" not in ai_data:
                        ai_cache.set(fingerprint, ai_data)
                        ai_enhanced = True
                        ai_confidence = ai_data.get('confidence', 0.0)
            except Exception as e2:
                print(f"   IA: Error fallback: {e2}")
    
    # 7️⃣ ENRIQUECER DATOS BASE CON IA
    final_brand = ai_data.get('brand', brand)
    final_model = ai_data.get('model', model)
    final_name = ai_data.get('normalized_name', name)
    
    # Combinar atributos: básicos + IA
    final_attributes = attrs.copy()
    if ai_data.get('refined_attributes'):
        refined_attrs = ai_data['refined_attributes']
        for key, value in refined_attrs.items():
            if value:  # Solo agregar si tiene valor
                final_attributes[key] = value
    
    # 8️⃣ GENERAR PRODUCT_ID ÚNICO
    product_id = hashlib.sha1(
        f"{final_brand}|{final_model}|{category_id}|{price_curr}|{retailer}".encode()
    ).hexdigest()
    
    # 9️⃣ PRODUCTO NORMALIZADO FINAL
    normalized_product = {
        "product_id": product_id,
        "fingerprint": fingerprint,
        "retailer": retailer,
        "name": final_name,
        "brand": final_brand,
        "model": final_model,
        "category": category_id,
        "price_current": price_curr,
        "price_original": price_orig,
        "currency": "CLP",
        "url": url,
        "attributes": final_attributes,
        "source": {
            "metadata": metadata,
            "raw_keys": list(raw.keys()),
            "categorization": {
                "confidence": category_confidence,
                "source": categorization.get("source"),
                "suggestions": categorization.get("suggestions", [])
            }
        },
        "ai_enhanced": ai_enhanced,
        "ai_confidence": ai_confidence,
        "processing_version": "v1.1"
    }
    
    # 🔟 PERSISTENCIA EN BASE DE DATOS
    try:
        db_connector = get_db_connector()
        success = db_connector.save_normalized_product(normalized_product)
        
        if success:
            print(f"   BD: Producto guardado exitosamente")
        else:
            print(f"   BD: Error guardando producto (success='{success}')")
            
    except Exception as e:
        print(f"   BD: Error de persistencia: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"   OK: Normalizacion completada - AI:{ai_enhanced} BD:OK")
    
    return normalized_product

def normalize_batch_integrated(items: list, retailer: str = None) -> list:
    """Normalizar múltiples productos en lote"""
    
    print(f"=== NORMALIZACION INTEGRADA LOTE ===")
    print(f"Productos recibidos: {len(items)}")
    
    # APLICAR FILTRO ANTES DEL PROCESAMIENTO
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Scrappers'))
        from product_filter import ProductFilter
        
        filter_instance = ProductFilter()
        
        # Adaptar formato para el filtro
        products_for_filter = []
        for item in items:
            product = item.get("item", item)
            products_for_filter.append(product)
        
        filtered_products, stats = filter_instance.filter_products(products_for_filter)
        
        print(f"FILTRO APLICADO:")
        print(f"   Total original: {stats['total_original']}")
        print(f"   Filtrados por accesorio: {stats['filtered_accessory']}")
        print(f"   Filtrados por precio bajo (<$50.000): {stats['filtered_low_price']}")
        print(f"   Filtrados por reacondicionado: {stats['filtered_refurbished']}")
        print(f"   Total filtrados: {stats['total_filtered']}")
        print(f"   Productos válidos para procesar: {stats['total_remaining']}")
        
        # Reconstruir items filtrados
        filtered_items = []
        for product in filtered_products:
            # Encontrar el item original correspondiente
            for original_item in items:
                original_product = original_item.get("item", original_item)
                if original_product.get("name") == product.get("name"):
                    filtered_items.append(original_item)
                    break
        
        items = filtered_items
        
    except Exception as e:
        print(f"Error aplicando filtro, procesando todos los productos: {e}")
    
    print(f"Procesando {len(items)} productos (post-filtro)...")
    
    results = []
    errors = 0
    
    for i, item_data in enumerate(items, 1):
        try:
            raw = item_data.get("item", item_data)
            metadata = item_data.get("metadata", {})
            item_retailer = retailer or item_data.get("_retailer", item_data.get("retailer", "Unknown"))
            
            normalized = normalize_one_integrated(raw, metadata, item_retailer)
            results.append(normalized)
            
            print(f"   [{i}/{len(items)}] OK {normalized['name'][:40]}...")
            
        except Exception as e:
            print(f"   [{i}/{len(items)}] ERROR: {e}")
            errors += 1
    
    print(f"\\n=== LOTE COMPLETADO ===")
    print(f"Exitosos: {len(results)}, Errores: {errors}")
    
    # Estadísticas finales
    try:
        db_connector = get_db_connector()
        stats = db_connector.get_processing_stats()
        print(f"Total productos en BD: {stats.get('productos_maestros', 0)}")
        print(f"Total precios en BD: {stats.get('precios_actuales', 0)}")
    except:
        pass
    
    return results

if __name__ == "__main__":
    # Test del sistema integrado
    print("=== TEST NORMALIZACION INTEGRADA ===")
    
    # Producto de prueba
    test_raw = {
        "name": "PERFUME CAROLINA HERRERA 212 VIP ROSE MUJER EDP 80 ML",
        "ripley_price_text": "$129.990",
        "product_link": "https://www.ripley.cl/perfume-212-vip-rose"
    }
    
    test_metadata = {
        "scraped_at": "2025-09-09 05:45:00",
        "search_term": "perfumes",
        "search_name": "Perfumes 🌸",
        "base_url": "https://www.ripley.cl/perfumes"
    }
    
    # Normalizar
    result = normalize_one_integrated(test_raw, test_metadata, "Ripley")
    
    print(f"\\n=== RESULTADO ===")
    print(f"ID: {result['product_id']}")
    print(f"Nombre: {result['name']}")
    print(f"Marca: {result['brand']}")
    print(f"Categoría: {result['category']}")
    print(f"Precio: ${result['price_current']:,} CLP")
    print(f"IA Enhanced: {result['ai_enhanced']}")
    print(f"Atributos: {len(result['attributes'])} definidos")