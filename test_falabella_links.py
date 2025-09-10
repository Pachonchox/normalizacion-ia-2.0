#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Test rápido para verificar corrección de links en Falabella
"""

import sys
import os
import json
from datetime import datetime

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Scrappers'))

# Importar el scraper corregido
from falabella_busqueda_continuo import scrape_single_page

def test_falabella_links():
    """Test de links de Falabella con la corrección aplicada"""
    print("🧪 PROBANDO CORRECCIÓN DE LINKS FALABELLA")
    print("=" * 50)
    
    try:
        # Probar con una sola página de perfumes
        search_term = "perfume"
        page_num = 1
        search_name = "Perfumes Test"
        search_key = "perfume_test"
        base_url = f"https://www.falabella.com/falabella-cl/search?Ntt={search_term}"
        
        print(f"🔍 Buscando: {search_term}")
        print(f"🔗 URL: {base_url}")
        
        # Ejecutar scraping
        products = scrape_single_page(
            search_term=search_term,
            page_num=page_num,
            search_name=search_name,
            search_key=search_key,
            base_url=base_url
        )
        
        if products:
            print(f"✅ Productos encontrados: {len(products)}")
            
            # Verificar links
            links_found = 0
            links_empty = 0
            
            for i, product in enumerate(products[:5], 1):  # Solo los primeros 5
                link = product.get('product_link', '')
                name = product.get('name', 'Sin nombre')[:40]
                
                if link and link.strip():
                    links_found += 1
                    print(f"✅ P{i}: {name}")
                    print(f"   🔗 {link}")
                else:
                    links_empty += 1
                    print(f"❌ P{i}: {name}")
                    print(f"   🔗 LINK VACÍO")
                print()
            
            print("📊 RESUMEN:")
            print(f"   Links encontrados: {links_found}")
            print(f"   Links vacíos: {links_empty}")
            print(f"   Total probados: {links_found + links_empty}")
            
            # Resultado final
            if links_found > 0:
                print("🎉 ¡CORRECCIÓN EXITOSA! - Los links se están extrayendo")
                return True
            else:
                print("❌ CORRECCIÓN FALLIDA - Todos los links están vacíos")
                return False
                
        else:
            print("❌ No se encontraron productos")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    test_falabella_links()