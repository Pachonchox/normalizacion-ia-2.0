from __future__ import annotations
import os, json, time, hashlib
from typing import List, Dict, Any
import yaml
from .utils import setup_logging, LOGGER, fingerprint, clean_text, now_iso
from .ingest import load_products, unify_prices, detect_retailer
from .normalize import load_brand_aliases, infer_brand, extract_attributes
from .categorize import load_taxonomy, categorize
from .cache import Cache
from .models import NormalizedProduct, SourceInfo
from .metrics import Metrics
from .match import find_matches

def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def normalize_record(raw: Dict[str, Any], cfg: Dict[str, Any], brand_map: Dict[str, List[str]], taxonomy: Dict[str, Any], metrics: Metrics) -> Dict[str, Any]:
    name = clean_text(raw.get("name",""))
    prices = unify_prices(raw)
    # categorización por nombre + metadata
    cat_id, conf, sug = categorize(name, taxonomy)
    if sug: metrics.inc("suggested_categories")
    # marca
    brand = infer_brand(name, raw.get("brand"), brand_map) or "DESCONOCIDA"
    attrs, model_hint = extract_attributes(name, cat_id)
    # modelo: limpia name sin marca y descriptores
    model = model_hint
    # fingerprint con campos fuertes
    fp = fingerprint([brand, model or name, cat_id, attrs.get("capacity",""), str(attrs.get("screen_size_in","")), str(attrs.get("volume_ml",""))])
    src = SourceInfo(retailer=detect_retailer(raw), product_code=str(raw.get("product_code") or raw.get("sku") or ""),
                     url=raw.get("product_link") or raw.get("url"), scraped_at=(raw.get("scraped_at") or raw.get("_metadata",{}).get("scraped_at")))
    np = NormalizedProduct(
        product_id=fp,
        source=src,
        name=name,
        brand=brand,
        model=model,
        variant=attrs.get("color"),
        category=cat_id,
        price_current=float(prices["price_current"] or 0),
        price_original=float(prices["price_original"] or 0) if prices["price_original"] else None,
        price_card=float(prices["price_card"] or 0) if prices["price_card"] else None,
        attributes=attrs,
        fingerprint=fp,
        created_at=now_iso(),
        updated_at=now_iso()
    )
    metrics.inc("products_processed")
    metrics.inc_cat(cat_id)
    return np.model_dump()

def run_pipeline(input_dir: str, patterns: List[str], outdir: str, enable_cache: bool, llm_mode: str, stage: str="all") -> Dict[str, Any]:
    os.makedirs(outdir, exist_ok=True)
    setup_logging(os.path.join(outdir, "logs", f"run.log"))
    metrics = Metrics()
    cfg = load_config(os.path.join(os.path.dirname(os.path.dirname(__file__)), "..","configs","config.local.yaml"))
    taxonomy = load_taxonomy(os.path.join(os.path.dirname(os.path.dirname(__file__)), "..","configs","taxonomy_v1.json"))
    brand_map = load_brand_aliases(os.path.join(os.path.dirname(os.path.dirname(__file__)), "..","configs","brand_aliases.json"))
    cache = Cache(cfg["cache"]["sqlite_path"]) if enable_cache else None

    # Ingesta
    t0 = time.time()
    raw_items = load_products(input_dir, patterns)
    metrics.record_timing("ingest_ms", (time.time()-t0)*1000)

    normed: List[Dict[str, Any]] = []
    if stage in ("all","normalize","match"):
        t0 = time.time()
        for r in raw_items:
            # cache lookup
            fp_preview = None
            try:
                # preview brand/cat for deterministic fp? we need name first
                pass
            except Exception:
                pass
            rec = None
            if cache:
                # can't compute fp before normalization; rely on cache only post
                pass
            rec = normalize_record(r, cfg, brand_map, taxonomy, metrics)
            if cache:
                cache.put(rec["fingerprint"], rec); metrics.inc("cache_misses")
            normed.append(rec)
        metrics.record_timing("normalize_ms", (time.time()-t0)*1000)
        # Persist
        with open(os.path.join(outdir, "normalized_products.jsonl"), "w", encoding="utf-8") as f:
            for n in normed:
                f.write(json.dumps(n, ensure_ascii=False)+"\n")

    # Matching
    matches = []
    if stage in ("all","match"):
        t0 = time.time()
        # if stage == "match" and user provided normalized file, that's handled in CLI
        matches = find_matches(normed, min_token_similarity=cfg["matching"]["min_token_similarity"],
                               min_attr_score=cfg["matching"]["min_attr_score"], top_k=cfg["matching"]["top_k"])
        metrics.counts["matches_found"] = len(matches)
        metrics.record_timing("match_ms", (time.time()-t0)*1000)
        with open(os.path.join(outdir, "matches.jsonl"), "w", encoding="utf-8") as f:
            for m in matches:
                f.write(json.dumps(m, ensure_ascii=False)+"\n")

    # Reporte
    report = metrics.report(os.path.join(outdir, "report.json"))
    return {"normalized": len(normed), "matches": len(matches), "report": report}
