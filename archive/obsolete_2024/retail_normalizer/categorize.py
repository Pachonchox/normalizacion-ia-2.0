from __future__ import annotations
import json, re, os
from typing import Dict, Any, Tuple

def load_taxonomy(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _walk_nodes(node, acc):
    acc.append(node)
    for ch in node.get("children", []):
        _walk_nodes(ch, acc)

def categorize(name: str, taxonomy: Dict[str, Any]) -> Tuple[str, float, str | None]:
    """Devuelve (category_id, confidence, suggested_new)"""
    text = name.lower()
    nodes = []
    for r in taxonomy["roots"]:
        _walk_nodes(r, nodes)
    best = ("otros", 0.0)
    for n in nodes:
        syns = [n["name"].lower()] + [s.lower() for s in n.get("synonyms",[])]
        score = 0
        for s in syns:
            # suma puntos por cada sinónimo presente
            if s in text:
                score += 1
            # palabras separadas
            for tok in re.findall(r"[a-z0-9\+\-\.]+", s):
                if tok and tok in text:
                    score += 0.25
        if score > best[1]:
            best = (n["id"], float(score))
    cat, conf = best
    if conf == 0.0:
        return ("otros", 0.0, "Sugerir nueva categoría")
    return (cat, min(conf/3.0,1.0), None)
