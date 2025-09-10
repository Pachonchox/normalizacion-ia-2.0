from __future__ import annotations
import hashlib
from typing import Dict, Any

def product_fingerprint(prod: Dict[str, Any]) -> str:
    base = "|".join([
        prod.get("brand",""),
        prod.get("category",""),
        (prod.get("model") or prod.get("name","")),
        str(prod.get("attributes",{}).get("capacity","")),
        str(prod.get("attributes",{}).get("volume_ml","")),
        str(prod.get("attributes",{}).get("screen_size_in","")),
    ])
    return hashlib.sha1(base.encode("utf-8")).hexdigest()
