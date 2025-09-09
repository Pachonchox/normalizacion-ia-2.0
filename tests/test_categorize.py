#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Tests para Sistema de Categorización Híbrida
===============================================
Tests unitarios para validar la nueva integración categorize.py con BD + JSON fallback
"""

import pytest
import os
import json
from unittest.mock import patch, MagicMock
from src.categorize import (
    load_taxonomy, 
    categorize, 
    categorize_enhanced,
    get_category_attributes_schema,
    load_categories_from_db
)

# 🎯 Test Data - Casos de prueba controlados
TEST_CASES = [
    # (nombre_producto, metadata, categoria_esperada, confianza_minima)
    ("iPhone 16 Pro Max 256GB", {"search_term": "smartphone"}, "smartphones", 0.6),
    ("PERFUME CAROLINA HERRERA 212 VIP ROSE", {"search_term": "perfumes"}, "perfumes", 0.6),
    ("Smart TV 55 4K OLED Samsung", {"search_term": "televisor"}, "smart_tv", 0.6),
    ("Notebook HP Pavilion Gaming", {"search_term": "notebook"}, "notebooks", 0.6),
    ("Impresora HP LaserJet Pro", {"search_term": "impresora"}, "printers", 0.6),
    ("Producto completamente desconocido XYZ", {}, "others", 0.0),
]

TAXONOMY_MOCK = {
    "version": "test_v1.0",
    "source": "json_fallback",
    "nodes": [
        {
            "id": "smartphones",
            "name": "Smartphones",
            "synonyms": ["celular", "smartphone", "iphone", "android", "galaxy"]
        },
        {
            "id": "notebooks", 
            "name": "Notebooks",
            "synonyms": ["laptop", "notebook", "portátil", "hp pavilion", "gaming"]
        },
        {
            "id": "smart_tv",
            "name": "Smart TV", 
            "synonyms": ["tv", "televisor", "smart tv", "oled", "4k"]
        },
        {
            "id": "perfumes",
            "name": "Perfumes",
            "synonyms": ["perfume", "fragrance", "eau de parfum", "carolina herrera"]
        },
        {
            "id": "printers",
            "name": "Printers",
            "synonyms": ["impresora", "printer", "laserjet", "hp ink"]
        },
        {
            "id": "others",
            "name": "Otros",
            "synonyms": []
        }
    ]
}

class TestCategorizationSystem:
    """🎯 Tests principales del sistema de categorización"""
    
    def test_load_taxonomy_json_fallback(self):
        """✅ Test: Fallback a JSON cuando BD no disponible"""
        with patch('src.categorize.load_categories_from_db', return_value=None):
            with patch('builtins.open', mock_open_taxonomy()):
                taxonomy = load_taxonomy("fake_path.json")
                
                assert taxonomy is not None
                assert taxonomy["source"] == "json_fallback"
                assert "nodes" in taxonomy
                assert len(taxonomy["nodes"]) > 0
    
    def test_load_taxonomy_database_priority(self):
        """✅ Test: BD tiene prioridad sobre JSON"""
        mock_db_taxonomy = {
            "version": "bd_v1.0", 
            "source": "database",
            "nodes": [{"id": "test", "name": "Test", "synonyms": []}]
        }
        
        with patch('src.categorize.load_categories_from_db', return_value=mock_db_taxonomy):
            taxonomy = load_taxonomy("fake_path.json")
            
            assert taxonomy["source"] == "database"
            assert taxonomy["version"] == "bd_v1.0"
    
    def test_categorize_basic_functionality(self):
        """✅ Test: Categorización básica funciona correctamente"""
        for name, metadata, expected_cat, min_conf in TEST_CASES:
            cat_id, confidence, suggestions = categorize(name, metadata, TAXONOMY_MOCK)
            
            assert cat_id == expected_cat, f"Producto '{name}' -> esperado: {expected_cat}, obtenido: {cat_id}"
            
            if expected_cat != "others":
                assert confidence >= min_conf, f"Confianza muy baja: {confidence} < {min_conf}"
    
    def test_categorize_with_search_context(self):
        """✅ Test: Contexto de búsqueda mejora precisión"""
        # Caso ambiguo: Galaxy puede ser smartphone o notebook
        ambiguous_product = "Samsung Galaxy Book Pro"
        
        # Con contexto smartphone
        cat_smart, conf_smart, _ = categorize(
            ambiguous_product, 
            {"search_term": "smartphone"}, 
            TAXONOMY_MOCK
        )
        
        # Con contexto notebook
        cat_note, conf_note, _ = categorize(
            ambiguous_product,
            {"search_term": "notebook"}, 
            TAXONOMY_MOCK
        )
        
        # El contexto debería influir en la decisión
        assert cat_smart != cat_note or conf_smart != conf_note
    
    def test_confidence_threshold_logic(self):
        """✅ Test: Umbral de confianza y sugerencias"""
        # Producto con poca coincidencia -> debería dar sugerencias
        weak_product = "Producto medio relevante"
        cat_id, confidence, suggestions = categorize(weak_product, {}, TAXONOMY_MOCK)
        
        if confidence < 0.6:
            assert suggestions is not None
            assert len(suggestions) >= 0  # Puede tener 0 o más sugerencias
        else:
            assert suggestions == []
    
    def test_enhanced_categorization_with_attributes(self):
        """✅ Test: Categorización enhanced incluye esquema atributos"""
        with patch('src.categorize.get_category_attributes_schema') as mock_attrs:
            mock_attrs.return_value = [
                {"name": "brand", "type": "string", "required": True, "default": None}
            ]
            
            result = categorize_enhanced("iPhone 16", {"search_term": "smartphone"}, TAXONOMY_MOCK)
            
            assert "category_id" in result
            assert "confidence" in result
            assert "suggestions" in result
            assert "attributes_schema" in result
            assert "enhanced" in result
            assert result["enhanced"] is True
            assert len(result["attributes_schema"]) > 0
    
    def test_database_connection_fallback(self):
        """✅ Test: Manejo de errores de conexión BD"""
        with patch('src.categorize.get_db_connector') as mock_connector:
            # Simular error de conexión
            mock_connector.side_effect = Exception("Connection failed")
            
            with patch('builtins.open', mock_open_taxonomy()):
                taxonomy = load_taxonomy("fake_path.json")
                
                # Debería usar fallback JSON sin fallar
                assert taxonomy is not None
                assert taxonomy["source"] == "json_fallback"
    
    def test_environment_variables_integration(self):
        """✅ Test: Variables de entorno se leen correctamente"""
        test_env_vars = {
            'DB_HOST': 'test_host',
            'DB_PORT': '5433',
            'DB_NAME': 'test_db',
            'DB_USER': 'test_user',
            'DB_PASSWORD': 'test_pass'
        }
        
        with patch.dict(os.environ, test_env_vars):
            with patch('src.categorize.SimplePostgreSQLConnector') as mock_connector:
                # Forzar nueva conexión
                import src.categorize
                src.categorize._db_connector = None
                
                from src.categorize import get_db_connector
                get_db_connector()
                
                # Verificar que se llamó con los valores correctos
                mock_connector.assert_called_with(
                    host='test_host',
                    port=5433,
                    database='test_db',
                    user='test_user',
                    password='test_pass',
                    pool_size=3
                )

class TestRegressionBugs:
    """🐛 Tests de regresión para bugs identificados en auditoría"""
    
    def test_galaxy_disambiguation(self):
        """🐛 Test: Galaxy no debe confundir smartphone vs notebook"""
        galaxy_phone = "Samsung Galaxy S24 Ultra"
        galaxy_laptop = "Samsung Galaxy Book Pro 15"
        
        # Con contexto adecuado, debería categorizar correctamente
        phone_cat, _, _ = categorize(galaxy_phone, {"search_term": "smartphone"}, TAXONOMY_MOCK)
        laptop_cat, _, _ = categorize(galaxy_laptop, {"search_term": "notebook laptop"}, TAXONOMY_MOCK)
        
        assert phone_cat == "smartphones"
        assert laptop_cat == "notebooks"
    
    def test_android_tv_vs_smartphone(self):
        """🐛 Test: Android TV no debe categorizarse como smartphone"""
        android_tv = "Smart TV 55 Android TV 4K"
        
        tv_cat, _, _ = categorize(android_tv, {"search_term": "tv"}, TAXONOMY_MOCK)
        
        # Con contexto TV, no debería ir a smartphones
        assert tv_cat != "smartphones"
    
    def test_stopwords_not_causing_false_positives(self):
        """🐛 Test: Palabras comunes no causan falsos positivos"""
        irrelevant_product = "Producto de mesa decorativo"
        
        cat_id, confidence, _ = categorize(irrelevant_product, {}, TAXONOMY_MOCK)
        
        # "de" no debería hacer que vaya a perfumes
        if cat_id == "perfumes":
            assert confidence < 0.6, "Falso positivo por palabra común 'de'"

def mock_open_taxonomy():
    """🔧 Helper: Mock para abrir archivo taxonomy JSON"""
    from unittest.mock import mock_open
    return mock_open(read_data=json.dumps(TAXONOMY_MOCK))

if __name__ == "__main__":
    # 🚀 Ejecutar tests directamente
    pytest.main([__file__, "-v", "--tb=short"])