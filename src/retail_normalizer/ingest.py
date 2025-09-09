from __future__ import annotations
import json, os, glob
from typing import Dict, Any, List
from .utils import parse_price_text, clean_text

def load_products(input_dir: str, patterns: List[str]) -> List[Dict[str, Any]]:
    files = []
    for pat in patterns:
        files.extend(glob.glob(os.path.join(input_dir, pat)))
    items: List[Dict[str, Any]] = []
    for fp in files:
        try:
            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)
            meta = {}
            if isinstance(data, dict) and "metadata" in data:
                meta = data.get("metadata", {})
            src_items = data["products"] if isinstance(data, dict) and "products" in data else (data if isinstance(data, list) else [])
            for it in src_items:
                rec = dict(it)
                rec["_file"] = os.path.basename(fp)
                rec["_metadata"] = meta
                items.append(rec)
        except Exception as e:
            # skip bad file
            continue
    return items

def unify_prices(rec: Dict[str, Any]) -> Dict[str, Any]:
    # prefer numeric fields if available, else parse text
    candidates = []
    for k in ["card_price","normal_price","original_price"]:
        if rec.get(k) is not None:
            candidates.append(int(rec[k]))
    for k in ["card_price_text","ripley_price_text","normal_price_text","original_price_text"]:
        val = parse_price_text(rec.get(k))
        if val is not None:
            candidates.append(val)
    price_current = None
    price_original = None
    price_card = None
    # choose current as min non-null candidate that is not zero, and original as max (heuristic)
    if candidates:
        price_current = min(candidates)
        price_original = max(candidates)
    # explicit card if provided
    if rec.get("card_price") is not None:
        price_card = int(rec["card_price"])
    elif rec.get("card_price_text"):
        price_card = parse_price_text(rec["card_price_text"])
    return {"price_current": price_current, "price_original": price_original, "price_card": price_card}

def detect_retailer(rec: Dict[str, Any]) -> str | None:
    url = rec.get("product_link") or rec.get("url") or ""
    filehint = (rec.get("_file") or "").lower()
    if "paris" in url or "paris" in filehint:
        return "paris"
    if "ripley" in url or "ripley" in filehint:
        return "ripley"
    return rec.get("_metadata",{}).get("scraper")

