#!/usr/bin/env python3
"""
🧪 Test con 20 productos variados para prueba completa del pipeline
"""
import json
import os
from datetime import datetime
from pathlib import Path

# Datos de prueba: 20 productos de diferentes categorías y retailers
PRODUCTOS_TEST = [
    # Smartphones (5 productos)
    {
        "producto_id": "test_001",
        "nombre": "iPhone 15 Pro Max 256GB Titanio Natural",
        "precio": 1299990,
        "retailer": "Falabella",
        "url": "https://falabella.com/iphone-15-pro-max",
        "categoria_scraping": "Celulares y Telefonía",
        "marca": "Apple",
        "descripcion": "Smartphone Apple iPhone 15 Pro Max con 256GB almacenamiento, pantalla 6.7 pulgadas, chip A17 Pro",
        "sku": "FAL-IPH15PM-256"
    },
    {
        "producto_id": "test_002", 
        "nombre": "Samsung Galaxy S24 Ultra 512GB Negro",
        "precio": 1149990,
        "retailer": "Paris",
        "url": "https://paris.cl/galaxy-s24-ultra",
        "categoria_scraping": "Smartphones",
        "marca": "Samsung",
        "descripcion": "Galaxy S24 Ultra con S Pen integrado, 512GB, cámara 200MP, pantalla Dynamic AMOLED 2X",
        "sku": "PAR-S24U-512"
    },
    {
        "producto_id": "test_003",
        "nombre": "Xiaomi 14 Ultra 16GB RAM 512GB",
        "precio": 899990,
        "retailer": "Ripley",
        "url": "https://ripley.cl/xiaomi-14-ultra",
        "categoria_scraping": "Celulares",
        "marca": "Xiaomi",
        "descripcion": "Xiaomi 14 Ultra con cámara Leica, Snapdragon 8 Gen 3, 16GB RAM",
        "sku": "RIP-MI14U-512"
    },
    {
        "producto_id": "test_004",
        "nombre": "Google Pixel 8 Pro 128GB Bay Blue",
        "precio": 799990,
        "retailer": "Falabella",
        "url": "https://falabella.com/pixel-8-pro",
        "categoria_scraping": "Smartphones",
        "marca": "Google",
        "descripcion": "Pixel 8 Pro con tensor G3, cámara con IA avanzada, 7 años actualizaciones",
        "sku": "FAL-PIX8P-128"
    },
    {
        "producto_id": "test_005",
        "nombre": "OnePlus 12 256GB Flowy Emerald",
        "precio": 699990,
        "retailer": "Paris",
        "url": "https://paris.cl/oneplus-12",
        "categoria_scraping": "Celulares",
        "marca": "OnePlus",
        "descripcion": "OnePlus 12 con pantalla 2K 120Hz, carga rápida 100W, Hasselblad camera",
        "sku": "PAR-OP12-256"
    },
    
    # Notebooks (4 productos)
    {
        "producto_id": "test_006",
        "nombre": "MacBook Pro 14 M3 Pro 18GB 512GB Space Black",
        "precio": 2299990,
        "retailer": "Falabella",
        "url": "https://falabella.com/macbook-pro-14-m3",
        "categoria_scraping": "Computadores",
        "marca": "Apple",
        "descripcion": "MacBook Pro 14 pulgadas con chip M3 Pro, 18GB memoria unificada, 512GB SSD",
        "sku": "FAL-MBP14-M3P"
    },
    {
        "producto_id": "test_007",
        "nombre": "Dell XPS 15 Intel Core i9 32GB 1TB RTX 4060",
        "precio": 1899990,
        "retailer": "Ripley",
        "url": "https://ripley.cl/dell-xps-15",
        "categoria_scraping": "Notebooks",
        "marca": "Dell",
        "descripcion": "Dell XPS 15 con Intel i9-13900H, 32GB RAM, 1TB SSD, NVIDIA RTX 4060",
        "sku": "RIP-XPS15-I9"
    },
    {
        "producto_id": "test_008",
        "nombre": "ASUS ROG Strix G16 i7 16GB 1TB RTX 4070",
        "precio": 1599990,
        "retailer": "Paris",
        "url": "https://paris.cl/asus-rog-strix",
        "categoria_scraping": "Gaming",
        "marca": "ASUS",
        "descripcion": "Notebook gamer ROG Strix G16, Intel i7-13650HX, RTX 4070, pantalla 165Hz",
        "sku": "PAR-ROG-G16"
    },
    {
        "producto_id": "test_009",
        "nombre": "Lenovo ThinkPad X1 Carbon Gen 11 i7 16GB 512GB",
        "precio": 1399990,
        "retailer": "Falabella",
        "url": "https://falabella.com/thinkpad-x1",
        "categoria_scraping": "Notebooks",
        "marca": "Lenovo",
        "descripcion": "ThinkPad X1 Carbon ultraliviano, Intel i7-1365U, 16GB RAM, pantalla 2.8K",
        "sku": "FAL-X1C-G11"
    },
    
    # Smart TV (4 productos)
    {
        "producto_id": "test_010",
        "nombre": "Samsung Neo QLED 65 pulgadas 8K QN900C",
        "precio": 2999990,
        "retailer": "Ripley",
        "url": "https://ripley.cl/samsung-neo-qled-8k",
        "categoria_scraping": "Televisores",
        "marca": "Samsung",
        "descripcion": "Smart TV Neo QLED 8K 65 pulgadas, Quantum Matrix Pro, Neural Quantum Processor 8K",
        "sku": "RIP-QN900C-65"
    },
    {
        "producto_id": "test_011",
        "nombre": "LG OLED 55 C3 4K Smart TV 2023",
        "precio": 1499990,
        "retailer": "Paris",
        "url": "https://paris.cl/lg-oled-c3",
        "categoria_scraping": "TV y Video",
        "marca": "LG",
        "descripcion": "OLED evo 55 pulgadas, α9 AI Processor Gen6, Dolby Vision y Atmos",
        "sku": "PAR-OLED55C3"
    },
    {
        "producto_id": "test_012",
        "nombre": "Sony BRAVIA XR 65 A95L QD-OLED 4K",
        "precio": 2799990,
        "retailer": "Falabella",
        "url": "https://falabella.com/sony-bravia-qd-oled",
        "categoria_scraping": "Televisores",
        "marca": "Sony",
        "descripcion": "QD-OLED 65 pulgadas con Cognitive Processor XR, Google TV, Acoustic Surface Audio+",
        "sku": "FAL-A95L-65"
    },
    {
        "producto_id": "test_013",
        "nombre": "TCL 55 QLED 4K Google TV 55C645",
        "precio": 449990,
        "retailer": "Ripley",
        "url": "https://ripley.cl/tcl-qled-55",
        "categoria_scraping": "Smart TV",
        "marca": "TCL",
        "descripcion": "QLED 55 pulgadas, 4K HDR, Google TV, Game Master 2.0, 120Hz",
        "sku": "RIP-TCL55C645"
    },
    
    # Perfumes (4 productos)
    {
        "producto_id": "test_014",
        "nombre": "Dior Sauvage Eau de Parfum 100ml",
        "precio": 129990,
        "retailer": "Paris",
        "url": "https://paris.cl/dior-sauvage",
        "categoria_scraping": "Perfumes",
        "marca": "Dior",
        "descripcion": "Fragancia masculina Sauvage EDP, notas de bergamota y ámbar, 100ml",
        "sku": "PAR-SAUV-100"
    },
    {
        "producto_id": "test_015",
        "nombre": "Chanel Coco Mademoiselle EDP 50ml",
        "precio": 119990,
        "retailer": "Falabella",
        "url": "https://falabella.com/coco-mademoiselle",
        "categoria_scraping": "Belleza",
        "marca": "Chanel",
        "descripcion": "Perfume femenino Coco Mademoiselle, notas orientales frescas, 50ml",
        "sku": "FAL-COCO-50"
    },
    {
        "producto_id": "test_016",
        "nombre": "Carolina Herrera Good Girl Supreme 80ml",
        "precio": 94990,
        "retailer": "Ripley",
        "url": "https://ripley.cl/good-girl-supreme",
        "categoria_scraping": "Fragancias",
        "marca": "Carolina Herrera",
        "descripcion": "Good Girl Supreme EDP, notas de jazmín y cacao, zapato stiletto, 80ml",
        "sku": "RIP-GGSU-80"
    },
    {
        "producto_id": "test_017",
        "nombre": "Paco Rabanne 1 Million Parfum 100ml",
        "precio": 89990,
        "retailer": "Paris",
        "url": "https://paris.cl/one-million",
        "categoria_scraping": "Perfumes Hombre",
        "marca": "Paco Rabanne",
        "descripcion": "1 Million Parfum intenso, notas de cuero y resina, lingote dorado, 100ml",
        "sku": "PAR-1MIL-100"
    },
    
    # Electrodomésticos (3 productos)
    {
        "producto_id": "test_018",
        "nombre": "Refrigerador Samsung Side by Side 617L RS65R5411B4",
        "precio": 1299990,
        "retailer": "Falabella",
        "url": "https://falabella.com/samsung-side-by-side",
        "categoria_scraping": "Electrodomésticos",
        "marca": "Samsung",
        "descripcion": "Refrigerador Side by Side 617 litros, All Around Cooling, Digital Inverter",
        "sku": "FAL-RS65R-617"
    },
    {
        "producto_id": "test_019",
        "nombre": "Lavadora LG 22kg AI DD Steam TurboWash",
        "precio": 899990,
        "retailer": "Ripley",
        "url": "https://ripley.cl/lg-lavadora-22kg",
        "categoria_scraping": "Línea Blanca",
        "marca": "LG",
        "descripcion": "Lavadora 22kg con inteligencia artificial, vapor, TurboWash 360",
        "sku": "RIP-LG22-AI"
    },
    {
        "producto_id": "test_020",
        "nombre": "Horno Microondas Whirlpool 30L WMS30 Crisp",
        "precio": 189990,
        "retailer": "Paris",
        "url": "https://paris.cl/whirlpool-crisp",
        "categoria_scraping": "Cocina",
        "marca": "Whirlpool",
        "descripcion": "Microondas 30 litros con función Crisp para dorar, 900W, vapor",
        "sku": "PAR-WMS30"
    }
]

def crear_archivo_test():
    """Crear archivo JSON con los 20 productos de prueba"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_20_productos_{timestamp}.json"
    
    # Agregar timestamp a cada producto
    for producto in PRODUCTOS_TEST:
        producto["fecha_captura"] = datetime.now().isoformat()
        producto["test_batch"] = f"test_20_{timestamp}"
    
    # Guardar archivo
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(PRODUCTOS_TEST, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Archivo creado: {filename}")
    print(f"📊 Total productos: {len(PRODUCTOS_TEST)}")
    print(f"📁 Categorías: Smartphones (5), Notebooks (4), Smart TV (4), Perfumes (4), Electrodomésticos (3)")
    
    return filename

if __name__ == "__main__":
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    archivo = crear_archivo_test()
    print(f"\n🚀 Ejecuta el pipeline con:")
    print(f"   python run_pipeline_with_db.py --input {archivo}")