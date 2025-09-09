\
from __future__ import annotations
import re
from typing import Optional

_CLP_RX = re.compile(r"[^\d,\.]")

def parse_price(value) -> Optional[int]:
    """Parsea precios chilenos con miles '.' y decimales ',' o enteros.
    Retorna CLP como entero o None.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(round(float(value)))
    if not isinstance(value, str):
        return None
    s = value.strip()
    if not s:
        return None
    s = _CLP_RX.sub("", s)
    if not s:
        return None
    # Caso típico: 1.299.990 o 1299990
    # Eliminamos separadores y mantenemos dígitos
    s = s.replace(".", "").replace(",", "")
    try:
        return int(s)
    except Exception:
        return None

def slugify(text: str) -> str:
    t = text.lower().strip()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[^a-z0-9áéíóúüñ\s\-]", "", t)
    return t
