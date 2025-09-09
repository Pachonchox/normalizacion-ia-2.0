#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Prueba del Sistema Integrado con Base de Datos
Prueba la normalización de un producto usando PostgreSQL
"""

import sys
import os

# Agregar directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Importar módulos individuales para evitar imports relativos
import utils
import enrich
import fingerprint
import cache
import googlecloudsqlconnector
import llm_connectors
import normalize

def main():
    """Prueba el sistema integrado de normalización"""
    
    print(">> Iniciando prueba del sistema integrado...")
    
    # Producto de prueba (similar al de out/normalized_products.jsonl)
    raw_product = {
        "name": "PERFUME CAROLINA HERRERA 212 VIP ROSE MUJER EDP 80 ML",
        "ripley_price_text": "$129.990",
        "product_link": "https://www.ripley.cl/perfume-212-vip-rose"
    }
    
    metadata = {
        "scraped_at": "2025-09-09 02:24:06",
        "search_term": "perfumes",
        "search_name": "Perfumes",
        "base_url": "https://www.ripley.cl/perfumes"
    }
    
    retailer = "Ripley"
    category_id = "perfumes"
    
    print(f"-> Normalizando producto: {raw_product['name'][:50]}...")
    
    try:
        # Ejecutar normalización (esto usará DatabaseCache)
        normalized = normalize.normalize_one(raw_product, metadata, retailer, category_id)
        
        print("SUCCESS: Producto normalizado exitosamente!")
        print("--- RESULTADO ---")
        print(f"ID Producto: {normalized.get('product_id', 'N/A')}")
        print(f"Fingerprint: {normalized.get('fingerprint', 'N/A')}")
        print(f"Nombre: {normalized.get('name', 'N/A')}")
        print(f"Marca: {normalized.get('brand', 'N/A')}")
        print(f"Modelo: {normalized.get('model', 'N/A')}")
        print(f"Precio: ${normalized.get('price_current', 'N/A'):,} CLP")
        print(f"Categoria: {normalized.get('category', 'N/A')}")
        print(f"AI Enhanced: {normalized.get('ai_enhanced', False)}")
        print(f"AI Confidence: {normalized.get('ai_confidence', 0.0)}")
        
        if 'attributes' in normalized:
            print("Atributos:")
            for key, value in normalized['attributes'].items():
                if value:
                    print(f"  - {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Error en la normalización: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    print(f"\nResultado final: {'EXITO' if success else 'FALLO'}")