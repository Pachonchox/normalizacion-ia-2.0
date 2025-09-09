\
import json, os
from src.match import do_match

def test_match_pairs(tmp_path):
    # two similar products different retailers
    rows = [
        {
            "product_id":"a", "retailer":"Paris", "name":"iPhone 16 128GB Negro",
            "brand":"APPLE","model":"iPhone 16 128GB Negro","category":"smartphones",
            "price_current":999990,"currency":"CLP","attributes":{"capacity":"128 GB"}
        },
        {
            "product_id":"b", "retailer":"Ripley", "name":"APPLE iPhone 16 Negro 128Gb",
            "brand":"APPLE","model":"iPhone 16 Negro 128Gb","category":"smartphones",
            "price_current":999990,"currency":"CLP","attributes":{"capacity":"128 GB"}
        }
    ]
    pairs = do_match(rows, threshold=0.8, max_cands=20)
    assert len(pairs) >= 1
