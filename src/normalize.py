\
from __future__ import annotations
import re, hashlib, os
from typing import Dict, Any, Tuple, Optional
try:
    # Imports relativos (cuando se ejecuta como módulo)
    from .utils import parse_price, slugify
    from .enrich import guess_brand, extract_attributes, clean_model
    from .fingerprint import product_fingerprint
    from .cache import JsonCache
    from .googlecloudsqlconnector import CloudSQLConnector, DatabaseCache
    from .simple_db_connector import SimplePostgreSQLConnector, SimpleDatabaseCache
    from .llm_connectors import extract_with_llm, enrich_product_data, enabled as llm_enabled
except ImportError:
    # Imports absolutos (cuando se ejecuta directamente)
    from utils import parse_price, slugify
    from enrich import guess_brand, extract_attributes, clean_model
    from fingerprint import product_fingerprint
    from cache import JsonCache
    from googlecloudsqlconnector import CloudSQLConnector, DatabaseCache
    from simple_db_connector import SimplePostgreSQLConnector, SimpleDatabaseCache
    from llm_connectors import extract_with_llm, enrich_product_data, enabled as llm_enabled

# Configuración de base de datos global
_db_connector = None

def get_db_connector():
    """Obtener conector a base de datos (singleton)"""
    global _db_connector
    if _db_connector is None:
        # Usar conector simple para conexión directa PostgreSQL
        _db_connector = SimplePostgreSQLConnector(
            host="34.176.197.136",
            port=5432,
            database="postgres",
            user="postgres",
            password="Osmar2503!",
            pool_size=5
        )
    return _db_connector

PRICE_KEYS_PREF = [
    # prefer order for "current"
    ("card_price", "card_price_text"),
    ("normal_price", "normal_price_text"),
    ("ripley_price", "ripley_price_text"),
]

def pick_price(item: Dict[str, Any]) -> Tuple[Optional[int], Optional[int]]:
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
    for k in ("original_price","original_price_text","normal_price","normal_price_text"):
        val = parse_price(item.get(k))
        if val:
            original = val
            break
    return current, original

def normalize_one(raw: Dict[str, Any], metadata: Dict[str, Any], retailer: str, category_id: str) -> Dict[str, Any]:
    name = raw.get("name") or raw.get("title") or ""
    url = raw.get("product_link") or raw.get("url") or None
    brand = raw.get("brand") or guess_brand(name) or "DESCONOCIDA"

    # 1️⃣ EXTRACCIÓN BÁSICA (rápida, siempre)
    price_curr, price_orig = pick_price(raw)
    if price_curr is None:
        # fallback: try any text with $
        for k,v in raw.items():
            if "price" in k and isinstance(v, str):
                p = parse_price(v)
                if p: price_curr = p; break

    attrs = extract_attributes(name, category_id)
    model = clean_model(name, brand)

    # 2️⃣ CREAR PRODUCTO BASE para fingerprint
    base_product = {
        "brand": brand,
        "category": category_id,
        "model": model or name,
        "attributes": attrs
    }
    
    # 3️⃣ FINGERPRINT para cache IA indefinido 🎯
    fingerprint = product_fingerprint(base_product)
    
    # 4️⃣ CACHE IA INDEFINIDO EN BD - Solo metadatos, NO precios
    ai_data = {}
    
    if llm_enabled():
        try:
            # Usar SimpleDatabaseCache para cache indefinido de metadatos IA
            db_connector = get_db_connector()
            ai_cache = SimpleDatabaseCache(db_connector)
            
            # Buscar en cache por fingerprint
            ai_data = ai_cache.get(fingerprint) or {}
            
            if not ai_data:
                # Primera vez: Llamar a OpenAI (costoso)
                print(f"AI Enriqueciendo: {name[:50]}...")
                ai_data = extract_with_llm(name, category_id)
                
                if ai_data and "error" not in ai_data:
                    # Cache IA guardado indefinidamente en BD
                    ai_cache.set(fingerprint, ai_data)
                    print(f"OK Cache IA guardado en BD: {fingerprint[:8]}...")
                else:
                    print(f"WARNING Error IA: {ai_data.get('error', 'unknown')}")
            else:
                print(f"FAST Cache IA hit desde BD: {name[:50]}...")
                
        except Exception as e:
            print(f"WARNING Error cache IA BD: {e}")
            # Fallback a cache de archivos si falla BD
            try:
                os.makedirs("out", exist_ok=True)
                ai_cache = JsonCache("out/ai_metadata_cache.json", ttl_days=0)
                ai_data = ai_cache.get(fingerprint) or {}
                if not ai_data:
                    print(f"Fallback: AI Enriqueciendo con archivo...")
                    ai_data = extract_with_llm(name, category_id)
                    if ai_data and "error" not in ai_data:
                        ai_cache.set(fingerprint, ai_data)
            except Exception as e2:
                print(f"ERROR Fallback cache: {e2}")
                ai_data = {}

    # 5️⃣ ENRIQUECER datos base con IA (si disponible)
    base_normalized = {
        "retailer": retailer,
        "name": name,
        "brand": brand.title() if brand and brand != brand.upper() else brand,
        "model": model,
        "category": category_id,
        "attributes": attrs,
        "source": {"metadata": metadata, "raw_keys": list(raw.keys())}
    }
    
    # Combinar datos base + IA
    enriched = enrich_product_data(base_normalized, ai_data)
    
    # 6️⃣ AGREGAR DATOS VOLÁTILES (precios, URL) - NUNCA cacheados
    price_curr, price_orig = pick_price(raw)
    if price_curr is None and price_orig:
        price_curr = price_orig  # Fallback si no hay precio de tarjeta
    
    # product_id fingerprint (incluye retailer para uniqueness)
    sig_parts = [retailer, enriched.get("brand", ""), enriched.get("model", ""), category_id]
    final_attrs = enriched.get("attributes", {})
    for k in ("capacity","volume_ml","screen_size_in","panel","ram","storage","color"):
        if k in final_attrs:
            sig_parts.append(f"{k}={final_attrs[k]}")
    sig = "|".join(str(x) for x in sig_parts)
    product_id = hashlib.sha1(sig.encode("utf-8")).hexdigest()

    # 7️⃣ PRODUCTO FINAL optimizado para BD
    final_product = {
        "product_id": product_id,
        "fingerprint": fingerprint,  # 🔑 Para matching inter-retail
        "retailer": retailer,
        "name": enriched.get("normalized_name") or enriched["name"],
        "brand": enriched["brand"],
        "model": enriched.get("model"),
        "category": enriched["category"],
        "price_current": int(price_curr) if price_curr is not None else 0,
        "price_original": int(price_orig) if price_orig is not None else None,
        "currency": "CLP",
        "url": url,
        "attributes": final_attrs,
        "source": enriched["source"],
        # 🎯 Metadatos para auditoría BD
        "ai_enhanced": enriched.get("ai_enhanced", False),
        "ai_confidence": enriched.get("ai_confidence", 0.0),
        "processing_version": "v1.1"
    }
    
    return final_product
