#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Normalización Integrada con Base de Datos
Pipeline canónico: categorización (BD→JSON), normalización y persistencia sin dependencias a Scrappers.
"""

from __future__ import annotations
import hashlib
import os
from typing import Dict, Any, Tuple, Optional, List

# Imports con compatibilidad relativa/absoluta
try:
    from .utils import parse_price
    from .enrich import guess_brand, extract_attributes, clean_model
    from .fingerprint import product_fingerprint
    from .cache import JsonCache
    from .categorize import load_taxonomy, categorize_enhanced, get_brand_aliases
    from .unified_connector import get_unified_connector
    from .llm_connectors import extract_with_llm, enrich_product_data, enabled as llm_enabled
except ImportError:
    from utils import parse_price
    from enrich import guess_brand, extract_attributes, clean_model
    from fingerprint import product_fingerprint
    from cache import JsonCache
    from categorize import load_taxonomy, categorize_enhanced, get_brand_aliases
    from unified_connector import get_unified_connector
    try:
        from llm_connectors_optimized import extract_with_llm, enrich_product_data, enabled as llm_enabled
    except ImportError:
        from llm_connectors import extract_with_llm, enrich_product_data, enabled as llm_enabled

from dotenv import load_dotenv
load_dotenv()


PRICE_KEYS_PREF: List[Tuple[str, str]] = [
    ("card_price", "card_price_text"),
    ("normal_price", "normal_price_text"),
    ("ripley_price", "ripley_price_text"),
]

_db_connector = None
_taxonomy = None


def get_db_connector():
    """Obtener conector unificado y seguro"""
    return get_unified_connector()


def get_taxonomy_cached():
    """Obtener taxonomía con cache local en memoria"""
    global _taxonomy
    if _taxonomy is None:
        _taxonomy = load_taxonomy("../configs/taxonomy_v1.json")
    return _taxonomy


def _parse_price(val: Any) -> Optional[int]:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        try:
            return int(val)
        except Exception:
            return None
    if isinstance(val, str):
        return parse_price(val)
    return None


def pick_price(item: Dict[str, Any]) -> Tuple[Optional[int], Optional[int]]:
    """Extraer precio actual y original a partir de llaves conocidas."""
    current = None
    for numk, textk in PRICE_KEYS_PREF:
        if numk in item:
            current = _parse_price(item.get(numk))
        if current is None and textk in item:
            current = _parse_price(item.get(textk))
        if current is not None:
            break

    original = None
    for k in ("original_price", "original_price_text", "normal_price", "normal_price_text"):
        val = _parse_price(item.get(k))
        if val:
            original = val
            break
    return current, original


def normalize_one_integrated(raw: Dict[str, Any], metadata: Dict[str, Any], retailer: str) -> Dict[str, Any]:
    """Normalización integrada completa con BD y cache IA opcional"""

    name = raw.get("name") or raw.get("title") or ""
    url = raw.get("product_link") or raw.get("url") or None

    print(f">> Normalizando: {str(name)[:50]}...")

    # 1) Categorización híbrida
    taxonomy = get_taxonomy_cached()
    categorization = categorize_enhanced(name, metadata, taxonomy)
    category_id = categorization["category_id"]
    category_confidence = categorization["confidence"]
    print(f"   Categoría: {category_id} (conf: {category_confidence:.2f}, fuente: {categorization.get('source')})")

    # 2) Precios y marca
    price_curr, price_orig = pick_price(raw)
    if price_curr is None:
        # Fallback: buscar cualquier key con texto de precio
        for k, v in raw.items():
            if "price" in k and isinstance(v, str):
                p = _parse_price(v)
                if p:
                    price_curr = p
                    break

    brand_aliases = get_brand_aliases()
    brand = raw.get("brand") or guess_brand(name) or "DESCONOCIDA"
    # Normalizar marca con aliases
    brand_upper = brand.upper()
    for canonical, aliases in brand_aliases.items():
        if brand_upper in [alias.upper() for alias in aliases]:
            brand = canonical
            break

    # 3) Atributos por categoría y modelo
    attrs = extract_attributes(name, category_id)
    model = clean_model(name, brand)

    # 4) Producto base y fingerprint
    base_product = {"brand": brand, "category": category_id, "model": model or name, "attributes": attrs}
    fingerprint = product_fingerprint(base_product)

    # 5) Cache/IA opcional
    ai_data: Dict[str, Any] = {}
    ai_enhanced = False
    ai_confidence = 0.0

    if llm_enabled():
        try:
            db = get_db_connector()
            ai_cached = db.get_ai_cache(fingerprint)
            if ai_cached:
                print(f"   IA: Cache hit (conf: {ai_cached.get('confidence', 0):.2f})")
                ai_data = ai_cached
                ai_enhanced = True
                ai_confidence = ai_cached.get('confidence', 0.0)
            else:
                print("   IA: Enriqueciendo por primera vez...")
                ai_data = extract_with_llm(name, category_id)
                if ai_data and "error" not in ai_data:
                    db.set_ai_cache(fingerprint, ai_data)
                    ai_enhanced = True
                    ai_confidence = ai_data.get('confidence', 0.0)
                else:
                    print(f"   IA: Error - {ai_data.get('error', 'unknown')}")
        except Exception as e:
            print(f"   IA: Error cache BD: {e}")
            # Fallback a archivo
            try:
                os.makedirs("out", exist_ok=True)
                file_cache = JsonCache("out/ai_metadata_cache.json", ttl_days=0)
                ai_data = file_cache.get(fingerprint) or {}
                if not ai_data:
                    ai_data = extract_with_llm(name, category_id)
                    if ai_data and "error" not in ai_data:
                        file_cache.set(fingerprint, ai_data)
                        ai_enhanced = True
                        ai_confidence = ai_data.get('confidence', 0.0)
            except Exception as e2:
                print(f"   IA: Error fallback: {e2}")

    # 6) Enriquecer datos base con IA
    final_brand = ai_data.get('brand', brand)
    final_model = ai_data.get('model', model)
    final_name = ai_data.get('normalized_name', name)
    final_attributes = attrs.copy()
    for k, v in (ai_data.get('refined_attributes') or {}).items():
        if v is not None and v != "":
            final_attributes[k] = v

    # 7) product_id y producto final
    product_id = hashlib.sha1(f"{final_brand}|{final_model}|{category_id}|{price_curr}|{retailer}".encode()).hexdigest()
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
        "processing_version": "v1.1",
    }

    # 8) Persistencia en BD
    try:
        db_connector = get_db_connector()
        success = db_connector.save_normalized_product(normalized_product)
        if success:
            print("   BD: Producto guardado exitosamente")
        else:
            print("   BD: Error guardando producto (success='False')")
    except Exception as e:
        print(f"   BD: Error de persistencia: {e}")
        import traceback
        traceback.print_exc()

    print(f"   OK: Normalizacion completada - AI:{ai_enhanced} BD:OK")
    return normalized_product


def normalize_batch_integrated(items: list, retailer: str = None) -> list:
    """Normalizar múltiples productos en lote (pipeline canónico, sin Scrappers)."""

    print("=== NORMALIZACION INTEGRADA LOTE ===")
    print(f"Productos recibidos: {len(items)}")

    # Filtro opcional (controlado por ENABLE_PRODUCT_FILTER)
    try:
        if os.getenv("ENABLE_PRODUCT_FILTER", "false").lower() in ("1", "true", "yes"):
            try:
                from .filter import ProductFilter  # filtro local opcional
            except Exception:
                from filter import ProductFilter  # fallback relativo

            filter_instance = ProductFilter()
            products_for_filter = [ (item.get("item", item)) for item in items ]
            filtered_products, stats = filter_instance.filter_products(products_for_filter)

            tot_orig = stats.get('total_original', len(items))
            tot_rem = stats.get('total_remaining', len(filtered_products))
            print("FILTRO APLICADO:")
            print(f"   Total original: {tot_orig}")
            print(f"   Total filtrados: {tot_orig - tot_rem}")
            print(f"   Productos válidos para procesar: {tot_rem}")

            names = set(p.get("name") for p in filtered_products)
            items = [orig for orig in items if (orig.get("item", orig).get("name") in names)]
        else:
            print("Filtro deshabilitado (ENABLE_PRODUCT_FILTER=false)")
    except Exception as e:
        print(f"Filtro opcional no aplicado: {e}")

    print(f"Procesando {len(items)} productos (post-filtro)...")

    results: List[Dict[str, Any]] = []
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

    print("\n=== LOTE COMPLETADO ===")
    print(f"Exitosos: {len(results)}, Errores: {errors}")

    # Estadísticas finales
    try:
        db_connector = get_db_connector()
        stats = db_connector.get_processing_stats()
        print(f"Total productos en BD: {stats.get('productos_maestros', 0)}")
        print(f"Total precios en BD: {stats.get('precios_actuales', 0)}")
    except Exception:
        pass

    return results


if __name__ == "__main__":
    # Test del sistema integrado
    print("=== TEST NORMALIZACION INTEGRADA ===")

    test_raw = {
        "name": "PERFUME CAROLINA HERRERA 212 VIP ROSE MUJER EDP 80 ML",
        "ripley_price_text": "$129.990",
        "product_link": "https://www.ripley.cl/perfume-212-vip-rose"
    }

    test_metadata = {
        "scraped_at": "2025-09-09 05:45:00",
        "search_term": "perfumes",
        "search_name": "Perfumes ejemplo",
        "base_url": "https://www.ripley.cl/perfumes"
    }

    result = normalize_one_integrated(test_raw, test_metadata, "Ripley")

    print("\n=== RESULTADO ===")
    print(f"ID: {result['product_id']}")
    print(f"Nombre: {result['name']}")
    print(f"Marca: {result['brand']}")
    print(f"Categoría: {result['category']}")
    print(f"Precio: ${result['price_current']:,} CLP")
    print(f"IA Enhanced: {result['ai_enhanced']}")
    print(f"Atributos: {len(result['attributes'])} definidos")
