from __future__ import annotations
import re, hashlib, json, time, logging, unicodedata
from slugify import slugify

LOGGER = logging.getLogger("retail_normalizer")

def norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()

def strip_accents(s: str) -> str:
    if not s: return s
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def clean_text(s: str) -> str:
    if s is None: return ""
    s = s.replace("\u00A0"," ").replace("\u200b"," ")
    s = norm_space(s)
    return s

def parse_price_text(text: str) -> int | None:
    if not text: return None
    # CLP: "$1.299.990" -> 1299990
    digits = re.sub(r"[^\d]", "", text)
    if not digits: return None
    try:
        return int(digits)
    except Exception:
        return None

def fingerprint(parts: list[str]) -> str:
    base = "||".join([strip_accents(clean_text(p)).lower() for p in parts if p])
    return hashlib.sha1(base.encode("utf-8")).hexdigest()

def json_dumps(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",",":"))

def brand_key(brand: str) -> str:
    return strip_accents((brand or "").upper())

def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def setup_logging(log_path: str | None = None):
    LOGGER.setLevel(logging.INFO)
    fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(fmt)
    LOGGER.handlers.clear()
    LOGGER.addHandler(handler)
    if log_path:
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setFormatter(fmt)
        LOGGER.addHandler(fh)
