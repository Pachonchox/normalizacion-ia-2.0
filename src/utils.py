from __future__ import annotations
import re
from typing import Optional

_CLP_RX = re.compile(r"[^\d,\.]")

def parse_price(value) -> Optional[int]:
    """Parsea precios chilenos con miles '.' y decimales ',' o enteros.
    Retorna CLP como entero o None.
    Valida que el precio esté en rango razonable para retail chileno.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        price = int(round(float(value)))
    elif isinstance(value, str):
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
            price = int(s)
        except Exception:
            return None
    else:
        return None
    
    # Validar rango de precios razonables (1 CLP a 100 millones CLP)
    if price < 1 or price > 100_000_000:
        return None
    
    return price

def slugify(text: str) -> str:
    t = text.lower().strip()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[^a-z0-9áéíóúüñ\s\-]", "", t)
    return t
