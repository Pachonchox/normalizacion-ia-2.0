\
from __future__ import annotations
import json, os
from typing import Dict, Iterable, Any, List

def _iter_json_files(input_dir: str) -> Iterable[str]:
    for root, _, files in os.walk(input_dir):
        for f in files:
            if f.endswith(".json"):
                yield os.path.join(root, f)

def load_items(input_dir: str) -> Iterable[Dict[str, Any]]:
    """Yields dicts with keys: item (raw product), metadata (dict), retailer (str)"""
    for path in _iter_json_files(input_dir):
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        products: List[dict] = []
        metadata: Dict[str, Any] = {}

        if isinstance(data, dict) and "products" in data:
            products = data.get("products", [])
            metadata = data.get("metadata", {})
        elif isinstance(data, list):
            products = data
            metadata = {}
        else:
            # try to find list in known keys
            for key in ("items", "data", "result"):
                if isinstance(data, dict) and isinstance(data.get(key), list):
                    products = data[key]
                    metadata = data.get("metadata", {})
                    break

        retailer = _infer_retailer(metadata)
        for it in products:
            yield {"item": it, "metadata": metadata, "retailer": retailer, "source_path": path}

def _infer_retailer(metadata: Dict[str, Any]) -> str:
    base = (metadata.get("base_url") or metadata.get("origin") or "").lower()
    scr = (metadata.get("scraper") or "").lower()
    for s in (base, scr):
        if "falabella" in s: return "Falabella"
        if "paris.cl" in s or "parís" in s or "paris " in s: return "Paris"
        if "ripley" in s: return "Ripley"
        if "jumbo" in s: return "Jumbo"
        if "sodimac" in s: return "Sodimac"
    return "Unknown"
