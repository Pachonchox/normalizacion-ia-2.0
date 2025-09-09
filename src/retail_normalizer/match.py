from __future__ import annotations
from typing import List, Dict, Any, Tuple, Iterable
from rapidfuzz import fuzz
from .utils import brand_key

def blocking_key(p: Dict[str, Any]) -> str:
    return f"{p['category']}::{brand_key(p['brand'])}"

def base_name(p: Dict[str, Any]) -> str:
    # nombre sin marca
    n = p["name"]
    b = p["brand"]
    return n.replace(b, "").strip() if b and b in n else n

def attr_match_score(a: Dict[str, Any], b: Dict[str, Any]) -> float:
    keys = set(a.keys()) & set(b.keys())
    if not keys: return 0.0
    score = 0.0
    for k in keys:
        score += 1.0 if str(a[k]).lower() == str(b[k]).lower() else 0.0
    return score / max(len(keys),1)

def find_matches(products: List[Dict[str, Any]], min_token_similarity: int=85, min_attr_score: float=0.6, top_k: int=10) -> List[Dict[str, Any]]:
    # agrupa por blocking key
    buckets: Dict[str, List[Dict[str, Any]]] = {}
    for p in products:
        buckets.setdefault(blocking_key(p), []).append(p)
    pairs = []
    # compara dentro de cada bucket por retailer distinto
    for key, plist in buckets.items():
        for i in range(len(plist)):
            for j in range(i+1, len(plist)):
                a, b = plist[i], plist[j]
                if a["source"].get("retailer")==b["source"].get("retailer"):
                    continue
                s = fuzz.token_set_ratio(base_name(a), base_name(b))
                if s >= min_token_similarity:
                    am = attr_match_score(a.get("attributes",{}), b.get("attributes",{}))
                    if am >= min_attr_score or s >= 95:
                        pairs.append({
                            "a_id": a["product_id"],
                            "b_id": b["product_id"],
                            "similarity": int(s),
                            "attr_score": am
                        })
    return pairs
