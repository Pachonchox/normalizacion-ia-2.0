#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.normalize_integrated import normalize_batch_integrated

items = [
    {"item": {"name": "iPhone 15 Pro Max 256GB Negro Liberado", "normal_price_text": "$1.299.990"}, "metadata": {"search_term": "smartphone"}},
    {"item": {"name": "Samsung Galaxy S24 Ultra 512GB 5G Titanium", "normal_price_text": "$1.499.990"}, "metadata": {"search_term": "smartphone"}},
    {"item": {"name": "Smart TV OLED 55\" 4K LG C3", "normal_price_text": "$899.990"}, "metadata": {"search_term": "televisor"}},
    {"item": {"name": "Notebook ASUS ROG Strix G16 RTX 4070 32GB RAM 1TB SSD", "normal_price_text": "$2.499.990"}, "metadata": {"search_term": "notebook"}},
    {"item": {"name": "Perfume Chanel No 5 EDP 100ml Mujer", "normal_price_text": "$159.990"}, "metadata": {"search_term": "perfumes"}},
    {"item": {"name": "Perfume Carolina Herrera 212 VIP Rose EDP 80ml", "normal_price_text": "$129.990"}, "metadata": {"search_term": "perfumes"}},
    {"item": {"name": "Impresora HP Smart Tank 580 All-in-One", "normal_price_text": "$129.990"}, "metadata": {"search_term": "impresora"}},
    {"item": {"name": "Xiaomi Redmi Note 13 Pro 256GB Azul 5G", "normal_price_text": "$299.990"}, "metadata": {"search_term": "smartphone"}},
    {"item": {"name": "Smart TV Samsung QLED 65\" 4K Q80C", "normal_price_text": "$1.199.990"}, "metadata": {"search_term": "televisor"}},
    {"item": {"name": "Notebook Apple MacBook Air M2 13 16GB 512GB", "normal_price_text": "$1.499.990"}, "metadata": {"search_term": "notebook"}}
]

if __name__ == "__main__":
    results = normalize_batch_integrated(items, retailer="Paris")
    print("\nSUMMARY:", len(results), "productos normalizados")
    for r in results:
        print(f"- {r['category']}: {r['brand']} {r.get('model') or ''} ${r['price_current']}")

