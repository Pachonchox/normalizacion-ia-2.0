from __future__ import annotations
import re, json
from typing import Dict, Any, Tuple
from .utils import clean_text, strip_accents, brand_key

def load_brand_aliases(path: str) -> Dict[str, list[str]]:
    import json
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def infer_brand(name: str, explicit_brand: str | None, aliases: Dict[str, list[str]]) -> str | None:
    if explicit_brand:
        return explicit_brand
    text = strip_accents(name).upper()
    for canon, syns in aliases.items():
        for s in syns:
            if strip_accents(s).upper() in text:
                return canon
    # fallback: first token capitalized
    m = re.match(r"([A-Za-z0-9\-\+\.]+)", name.strip())
    if m:
        return m.group(1).upper()
    return None

def extract_attributes(name: str, category: str) -> Tuple[Dict[str, Any], str | None]:
    n = name
    attrs: Dict[str, Any] = {}
    model_hint = None
    # Common
    cap = re.search(r"(\d+)\s?(TB|GB)", n, flags=re.I)
    if cap:
        attrs["capacity"] = f"{cap.group(1)} {cap.group(2).upper()}"
    color = re.search(r"\b(Negro|Black|Blanco|White|Azul|Blue|Verde|Green|Gris|Graphite|Icyblue|Morado|Purple|Titanium|Titanio)\b", n, flags=re.I)
    if color:
        attrs["color"] = color.group(1)
    # Smartphones
    if category == "smartphones":
        size = re.search(r"(\d{1,2}(\.\d)?)\s?\"|\b(\d{1,2}(\.\d)?)\s?inch", n, flags=re.I)
        if size:
            val = size.group(1) or size.group(3)
            attrs["screen_size_in"] = float(val)
        if "5g" in n.lower():
            attrs["network"] = "5G"
        # model hint (remove brand words)
        model_hint = re.sub(r"\b(smartphone|celular|liberado)\b", "", n, flags=re.I).strip()
    # TVs
    if category == "tvs":
        size = re.search(r"(\d{2,3})(?:\"|\s?inch|\s?”)", n, flags=re.I)
        if size:
            attrs["screen_size_in"] = int(size.group(1))
        if re.search(r"\b(4k|uhd)\b", n, flags=re.I):
            attrs["resolution"] = "4K UHD"
        if re.search(r"\b(qled|oled|led)\b", n, flags=re.I):
            attrs["panel"] = re.search(r"\b(qled|oled|led)\b", n, flags=re.I).group(1).upper()
        model_code = re.search(r"\b([A-Z0-9]{4,})\b", n)
        if model_code:
            attrs["model_code"] = model_code.group(1)
    # Perfumes
    if category == "perfumes":
        vol = re.search(r"(\d{2,4})\s?ml", n, flags=re.I)
        if vol:
            attrs["volume_ml"] = int(vol.group(1))
        conc = re.search(r"\b(EDP|EDT|Parfum|Eau de Parfum|Eau de Toilette)\b", n, flags=re.I)
        if conc:
            attrs["concentration"] = conc.group(1).upper() if conc.group(1) in ["EDP","EDT"] else "PARFUM"
        gender = re.search(r"\b(Mujer|Hombre|Unisex)\b", n, flags=re.I)
        if gender:
            attrs["gender"] = gender.group(1).capitalize()
        if "set" in n.lower():
            attrs["is_set"] = True
    return attrs, model_hint
