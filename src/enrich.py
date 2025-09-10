from __future__ import annotations
import re
from typing import Dict, Any, Tuple

BRANDS = [
  # Smartphones/TV/IT
  "SAMSUNG","APPLE","XIAOMI","MOTOROLA","HONOR","HUAWEI","OPPO","NOKIA","ZTE","LG","PHILIPS","TCL","HISENSE","AOC","CAIXUN","AIWA","MASTER-G","IFFALCON","DELL","HP","LENOVO","ASUS","ACER","MSI",
  # Perfumes
  "CAROLINA HERRERA","RALPH LAUREN","RABANNE","PACO RABANNE","LANCÔME","YVES SAINT LAURENT","VERSACE","DOLCE & GABBANA","DOLCE AND GABBANA","CALVIN KLEIN","GIVENCHY","VALENTINO","MICHAEL KORS","MONTBLANC","NINA RICCI","ARIANA GRANDE","BILLIE EILISH","ANTONIO BANDERAS","LATTAFA","RASASI","TOMMY HILFIGER","BURBERRY","CHANEL","LANCOME"
]

COLOR_WORDS = ["negro","black","blanco","white","grafito","gris","azul","icyblue","lavanda","morado","verde","navy","plata","titanio","rojo","pink","gold"]
RES_WORDS = ["4k","uhd","full hd","fhd","hd","8k","qled","oled","mini led","nanocell","crystal"]

GB_RX = re.compile(r"(\d+)\s*gb", re.I)
TB_RX = re.compile(r"(\d+)\s*tb", re.I)
INCH_RX = re.compile(r'(\d{2,3}(?:\.\d{1,2})?)\s*(?:\"|inch|pulgadas?)', re.I)
ML_RX = re.compile(r"(\d{1,4})\s*ml", re.I)
ED_RX = re.compile(r"\b(EDP|EDT|PARFUM)\b", re.I)

def guess_brand(name: str) -> str | None:
    upper = name.upper()
    for b in BRANDS:
        if b in upper:
            # Normalize aliases
            if b == "PACO RABANNE": return "RABANNE"
            if b == "DOLCE AND GABBANA": return "DOLCE & GABBANA"
            if b == "LANCOME": return "LANCÔME"
            return b
    return None

def extract_attributes(name: str, category_id: str) -> Dict[str, Any]:
    t = name
    attrs: Dict[str, Any] = {}

    if category_id == "smartphones":
        cap = GB_RX.search(t) or TB_RX.search(t)
        if cap:
            val = cap.group(1)
            unit = "TB" if "tb" in cap.group(0).lower() else "GB"
            attrs["capacity"] = f"{val} {unit}"
        col = [c for c in COLOR_WORDS if c in t.lower()]
        if col: attrs["color"] = col[0]
        if "5g" in t.lower(): attrs["network"] = "5G"

        inc = INCH_RX.search(t)
        if inc:
            try: attrs["screen_size_in"] = float(inc.group(1))
            except: pass

    elif category_id == "notebooks":
        inc = INCH_RX.search(t)
        if inc:
            try: attrs["screen_size_in"] = float(inc.group(1))
            except: pass
        ram = GB_RX.search(t)
        if ram: attrs["ram"] = f"{ram.group(1)} GB"
        # storage: prefer second GB/TB occurrence
        caps = (list(GB_RX.finditer(t)) + list(TB_RX.finditer(t)))
        if len(caps) >= 2:
            c = caps[1]
            unit = "TB" if "tb" in c.group(0).lower() else "GB"
            attrs["storage"] = f"{c.group(1)} {unit}"

    elif category_id == "smart_tv":
        inc = INCH_RX.search(t)
        if inc:
            try: attrs["screen_size_in"] = float(inc.group(1))
            except: pass
        res = [r for r in RES_WORDS if r in t.lower()]
        if res: attrs["panel"] = res[0].upper()

    elif category_id == "perfumes":
        ml = ML_RX.search(t)
        if ml: attrs["volume_ml"] = int(ml.group(1))
        ed = ED_RX.search(t)
        if ed: attrs["concentration"] = ed.group(1).upper()
        gender = None
        low = t.lower()
        if "mujer" in low: gender = "Mujer"
        elif "hombre" in low: gender = "Hombre"
        elif "unisex" in low: gender = "Unisex"
        if gender: attrs["gender"] = gender

    return attrs

def clean_model(name: str, brand: str | None) -> str | None:
    t = name
    if brand and brand.lower() in t.lower():
        t = re.sub(re.escape(brand), "", t, flags=re.I)
    # remove generic words
    t = re.sub(r"\b(smartphone|celular|iphone|galaxy|smart tv|televisor|notebook|laptop|perfume|set)\b", "", t, flags=re.I)
    t = re.sub(r"\s+", " ", t).strip()
    return t or None
