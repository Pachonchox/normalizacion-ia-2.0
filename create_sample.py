#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

# Cargar el archivo original
with open('test_single/busqueda_perfume_ciclo001_2025-09-09_16-06-08.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Tomar solo los primeros 3 productos
data['products'] = data['products'][:3]

# Guardar archivo reducido
with open('test_single/perfumes_sample.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f'Archivo creado con {len(data["products"])} productos')
for i, product in enumerate(data['products'], 1):
    print(f'{i}. {product["name"]} - ${product.get("normal_price", 0):,}')