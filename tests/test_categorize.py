\
from src.categorize import load_taxonomy, categorize

def test_categorize_basic():
    tax = load_taxonomy("configs/taxonomy_v1.json")
    cat, conf, sugg = categorize("Smart TV LG 55 UHD", {"search_name": "Smart TV"}, tax)
    assert cat in ("smart_tv","smarttv","smart_tv")
    assert conf >= 0.6
