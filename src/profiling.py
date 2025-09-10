from __future__ import annotations
import json, os
from typing import Dict, Any, Iterable

def profile_items(items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    fields = {}
    total = 0
    for obj in items:
        total += 1
        for k in obj.keys():
            fields.setdefault(k, 0)
            fields[k] += 1
    coverage = {k: v/total for k,v in fields.items()}
    return {"total": total, "field_counts": fields, "coverage": coverage}

def save_profile(profile: Dict[str, Any], outpath: str):
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w", encoding="utf-8") as fh:
        json.dump(profile, fh, ensure_ascii=False, indent=2)
