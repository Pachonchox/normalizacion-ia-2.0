#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
import os
from pathlib import Path

# Tomar UN solo producto del archivo real
with open('datos/falabella/busqueda_perfume_ciclo001_2025-09-09_16-06-08.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Seleccionar solo el primer producto
producto = data['products'][0]

print("=== PRODUCTO REAL SELECCIONADO ===")
print(f"Nombre: {producto['name']}")
print(f"Marca: {producto['brand']}")
print(f"Precio: ${producto.get('normal_price', 0):,}")
print(f"Retailer: Falabella")

# Crear archivo con UN solo producto
single_data = {
    "retailer": "falabella",
    "category": "perfumes", 
    "products": [producto]
}

os.makedirs('test_uno', exist_ok=True)
with open('test_uno/un_producto.json', 'w', encoding='utf-8') as f:
    json.dump(single_data, f, indent=2, ensure_ascii=False)

print("\nArchivo creado: test_uno/un_producto.json")
print("Listo para procesar con el sistema")