#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📂 Categorización Híbrida (Base de Datos + JSON Fallback)
Sistema de categorización que usa BD como fuente primaria con fallback a taxonomy_v1.json
"""

import json
import re
from typing import Dict, Any, Tuple, Optional, List
from simple_db_connector import SimplePostgreSQLConnector

# Cache global para evitar múltiples consultas BD
_categories_cache = None
_db_connector = None

def get_db_connector():
    """Obtener conector a base de datos (singleton)"""
    global _db_connector
    if _db_connector is None:
        _db_connector = SimplePostgreSQLConnector(
            host="34.176.197.136",
            port=5432,
            database="postgres",
            user="postgres",
            password="Osmar2503!",
            pool_size=3
        )
    return _db_connector

def load_categories_from_db() -> Dict[str, Any]:
    """Cargar categorías desde base de datos con formato compatible"""
    global _categories_cache
    
    if _categories_cache is not None:
        return _categories_cache
    
    try:
        connector = get_db_connector()
        
        with connector.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT category_id, name, synonyms, active
                    FROM categories 
                    WHERE active = true
                    ORDER BY category_id
                """)
                
                categories = cursor.fetchall()
                
                # Convertir a formato compatible con taxonomy_v1.json
                nodes = []
                for cat in categories:
                    nodes.append({
                        "id": cat[0],
                        "name": cat[1],
                        "synonyms": cat[2] or []  # Manejar NULL synonyms
                    })
                
                _categories_cache = {
                    "version": "bd_v1.0",
                    "source": "database", 
                    "nodes": nodes
                }
                
                print(f"OK: {len(nodes)} categorias cargadas desde BD")
                return _categories_cache
                
    except Exception as e:
        print(f"WARNING: Error cargando categorias desde BD: {e}")
        return None

def load_taxonomy(path: str) -> Dict[str, Any]:
    """Cargar taxonomía híbrida: BD primero, JSON fallback"""
    
    # Intentar cargar desde BD primero
    taxonomy = load_categories_from_db()
    
    if taxonomy is not None:
        return taxonomy
    
    # Fallback a archivo JSON
    print("INFO: Usando fallback a archivo JSON")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            taxonomy = json.load(fh)
            taxonomy["source"] = "json_fallback"
            return taxonomy
    except Exception as e:
        print(f"ERROR: No se pudo cargar taxonomia desde {path}: {e}")
        # Devolver taxonomía mínima de emergencia
        return {
            "version": "emergency",
            "source": "hardcoded",
            "nodes": [
                {"id": "others", "name": "Otros", "synonyms": []}
            ]
        }

def categorize(name: str, metadata: Dict[str, Any], taxonomy: Dict[str, Any]) -> Tuple[str, float, list]:
    """
    Categorización mejorada con ponderación de fuentes
    Return (category_id, confidence, suggestions_if_low).
    """
    
    # Preparar texto para análisis
    text = " ".join([
        str(metadata.get("search_name") or ""),
        str(metadata.get("search_term") or ""),
        str(name or ""),
    ]).lower()

    best = ("others", 0.0)
    scored = []
    
    for node in taxonomy["nodes"]:
        score = 0.0
        
        # Ponderación mejorada según fuente de datos
        confidence_multiplier = 1.0
        if taxonomy.get("source") == "database":
            confidence_multiplier = 1.2  # Mayor confianza en BD
        
        # Coincidencia exacta nombre categoría
        if node["name"].lower() in text:
            score += 0.6 * confidence_multiplier
        
        # Coincidencias con sinónimos (más flexible)
        for syn in node.get("synonyms", []):
            if syn:
                syn_lower = syn.lower()
                # Búsqueda exacta con límites de palabra
                if re.search(rf"\\b{re.escape(syn_lower)}\\b", text):
                    score += 0.25 * confidence_multiplier
                # Búsqueda parcial para casos como "iphone" en texto
                elif syn_lower in text:
                    score += 0.15 * confidence_multiplier
        
        # Bonus por coincidencias múltiples
        if score > 0.5:
            # Contar número de términos que coinciden
            matches = sum(1 for syn in node.get("synonyms", []) if syn and syn.lower() in text)
            if matches > 1:
                score += 0.1 * matches
        
        scored.append((node["id"], score))
        
        if score > best[1]:
            best = (node["id"], min(1.0, score))

    # Umbral de confianza ajustado según fuente
    confidence_threshold = 0.6
    if taxonomy.get("source") == "database":
        confidence_threshold = 0.5  # Menor umbral para BD más confiable
    
    if best[1] >= confidence_threshold:
        return best[0], best[1], []
    
    # Sugerencias: top 3 ordenadas por score
    scored.sort(key=lambda x: x[1], reverse=True)
    suggestions = [c for c, s in scored[:3] if s > 0.1]
    
    return best[0], best[1], suggestions

def get_category_attributes_schema(category_id: str) -> List[Dict[str, Any]]:
    """Obtener esquema de atributos para una categoría específica"""
    
    try:
        connector = get_db_connector()
        
        with connector.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT attribute_name, attribute_type, required, default_value
                    FROM attributes_schema 
                    WHERE category_id = %s
                    ORDER BY display_order, attribute_name
                """, (category_id,))
                
                attributes = cursor.fetchall()
                
                return [
                    {
                        "name": attr[0],
                        "type": attr[1], 
                        "required": attr[2],
                        "default": attr[3]
                    }
                    for attr in attributes
                ]
                
    except Exception as e:
        print(f"WARNING: Error obteniendo esquema de atributos para {category_id}: {e}")
        return []

def get_brand_aliases() -> Dict[str, List[str]]:
    """Obtener aliases de marcas desde BD"""
    
    try:
        connector = get_db_connector()
        
        with connector.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT brand_canonical, aliases
                    FROM brands 
                    WHERE active = true
                """)
                
                brands = cursor.fetchall()
                
                return {brand[0]: brand[1] for brand in brands}
                
    except Exception as e:
        print(f"WARNING: Error obteniendo aliases de marcas: {e}")
        return {}

# Función de compatibilidad con API existente
def load_taxonomy_original(path: str) -> Dict[str, Any]:
    """Función original mantenida para compatibilidad"""
    return load_taxonomy(path)

def categorize_enhanced(name: str, metadata: Dict[str, Any], taxonomy: Dict[str, Any]) -> Dict[str, Any]:
    """Categorización mejorada que retorna información adicional"""
    
    category_id, confidence, suggestions = categorize(name, metadata, taxonomy)
    
    # Obtener esquema de atributos para la categoría
    attributes_schema = get_category_attributes_schema(category_id)
    
    return {
        "category_id": category_id,
        "confidence": confidence,
        "suggestions": suggestions,
        "source": taxonomy.get("source", "unknown"),
        "attributes_schema": attributes_schema,
        "enhanced": True
    }

if __name__ == "__main__":
    # Test de la funcionalidad
    print("=== TEST CATEGORIZACION HIBRIDA ===")
    
    # Cargar taxonomía
    taxonomy = load_taxonomy("../configs/taxonomy_v1.json")
    print(f"Taxonomía cargada desde: {taxonomy.get('source')}")
    
    # Casos de prueba
    test_cases = [
        ("PERFUME CAROLINA HERRERA 212 VIP ROSE", {"search_term": "perfumes"}),
        ("iPhone 16 Pro Max 256GB", {"search_term": "smartphone"}),
        ("Smart TV 55 4K OLED", {"search_term": "televisor"}),
        ("Producto desconocido XYZ", {"search_term": ""})
    ]
    
    for name, metadata in test_cases:
        result = categorize_enhanced(name, metadata, taxonomy)
        print(f"\\nProducto: {name[:40]}...")
        print(f"Categoría: {result['category_id']} (confianza: {result['confidence']:.2f})")
        print(f"Esquema atributos: {len(result['attributes_schema'])} definidos")
        if result['suggestions']:
            print(f"Sugerencias: {result['suggestions']}")