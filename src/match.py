\
from __future__ import annotations
import json, os
from collections import defaultdict
from typing import Dict, Any, List, Tuple
from difflib import SequenceMatcher

def load_normalized(path: str) -> List[Dict[str, Any]]:
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line: continue
            rows.append(json.loads(line))
    return rows

def key_for_compare(prod: Dict[str, Any]) -> str:
    attrs = prod.get("attributes",{})
    sig = " ".join([
        prod.get("brand",""),
        prod.get("model") or prod.get("name",""),
        str(attrs.get("capacity","")),
        str(attrs.get("volume_ml","")),
        str(attrs.get("screen_size_in","")),
    ]).lower()
    return " ".join(sig.split())

def sim(a: str, b: str) -> float:
    return SequenceMatcher(a=a, b=b).ratio()

def do_match(rows: List[Dict[str, Any]], threshold: float = 0.86, max_cands: int = 50) -> List[Dict[str, Any]]:
    # Blocking: category+brand
    blocks = defaultdict(list)
    for p in rows:
        key = (p.get("category",""), p.get("brand","").lower())
        blocks[key].append(p)

    pairs = []
    for key, items in blocks.items():
        # split by retailer
        by_retailer = defaultdict(list)
        for p in items:
            by_retailer[p["retailer"]].append(p)
        retailers = list(by_retailer.keys())
        for i in range(len(retailers)):
            for j in range(i+1, len(retailers)):
                a_list = by_retailer[retailers[i]][:max_cands]
                b_list = by_retailer[retailers[j]][:max_cands]
                # compare
                for a in a_list:
                    akey = key_for_compare(a)
                    best = (None, 0.0)
                    for b in b_list:
                        bkey = key_for_compare(b)
                        s = sim(akey, bkey)
                        if s > best[1]:
                            best = (b, s)
                    if best[0] and best[1] >= threshold:
                        pairs.append({
                            "left": a,
                            "right": best[0],
                            "similarity": round(best[1], 4),
                            "block": {"category": key[0], "brand": key[1]}
                        })
    return pairs
