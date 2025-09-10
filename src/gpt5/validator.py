#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
✅ Sistema de Validación Estricta GPT-5
Validación de taxonomía, esquemas de atributos, marcas y quality gating
"""

import json
import re
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class StrictValidator:
    """Validador estricto para productos normalizados"""
    
    def __init__(self, config_path: str = "configs"):
        self.config_path = Path(config_path)
        self._load_taxonomy()
        self._load_brand_aliases()
        self._load_attribute_schemas()
        self._init_quality_thresholds()
    
    def _load_taxonomy(self):
        """Cargar taxonomía de categorías"""
        try:
            taxonomy_file = self.config_path / "taxonomy_v1.json"
            if taxonomy_file.exists():
                with open(taxonomy_file, 'r', encoding='utf-8') as f:
                    self.taxonomy = json.load(f)
            else:
                # Taxonomía por defecto
                self.taxonomy = {
                    "smartphones": {
                        "id": "smartphones",
                        "name": "Smartphones",
                        "synonyms": ["celulares", "teléfonos", "móviles", "iphone", "galaxy"],
                        "parent": "electronics"
                    },
                    "notebooks": {
                        "id": "notebooks",
                        "name": "Notebooks",
                        "synonyms": ["laptops", "portátiles", "notebook", "macbook", "ultrabook"],
                        "parent": "computing"
                    },
                    "smart_tv": {
                        "id": "smart_tv",
                        "name": "Smart TV",
                        "synonyms": ["televisores", "tv", "televisor", "smart", "qled", "oled"],
                        "parent": "electronics"
                    },
                    "perfumes": {
                        "id": "perfumes",
                        "name": "Perfumes",
                        "synonyms": ["fragancias", "perfume", "colonia", "eau de toilette", "edp", "edt"],
                        "parent": "beauty"
                    },
                    "tablets": {
                        "id": "tablets",
                        "name": "Tablets",
                        "synonyms": ["tablet", "ipad", "tab"],
                        "parent": "electronics"
                    },
                    "smartwatches": {
                        "id": "smartwatches",
                        "name": "Smartwatches",
                        "synonyms": ["smartwatch", "reloj inteligente", "watch", "apple watch"],
                        "parent": "wearables"
                    }
                }
            
            # Crear índice inverso para búsqueda rápida
            self.category_index = {}
            for cat_id, cat_data in self.taxonomy.items():
                # Por ID
                self.category_index[cat_id.lower()] = cat_id
                # Por nombre
                self.category_index[cat_data['name'].lower()] = cat_id
                # Por sinónimos
                for syn in cat_data.get('synonyms', []):
                    self.category_index[syn.lower()] = cat_id
                    
        except Exception as e:
            logger.error(f"Error cargando taxonomía: {e}")
            self.taxonomy = {}
            self.category_index = {}
    
    def _load_brand_aliases(self):
        """Cargar aliases de marcas"""
        try:
            brands_file = self.config_path / "brand_aliases.json"
            if brands_file.exists():
                with open(brands_file, 'r', encoding='utf-8') as f:
                    self.brand_aliases = json.load(f)
            else:
                # Marcas por defecto
                self.brand_aliases = {
                    "APPLE": ["apple", "iphone", "mac", "macbook", "ipad"],
                    "SAMSUNG": ["samsung", "galaxy", "sam"],
                    "XIAOMI": ["xiaomi", "mi", "redmi", "poco"],
                    "LG": ["lg", "lg electronics"],
                    "SONY": ["sony", "playstation", "ps"],
                    "HP": ["hp", "hewlett packard", "hewlett-packard"],
                    "DELL": ["dell", "alienware"],
                    "LENOVO": ["lenovo", "thinkpad", "ideapad", "legion"],
                    "ASUS": ["asus", "rog", "zenbook", "vivobook"],
                    "ACER": ["acer", "predator", "aspire"],
                    "MICROSOFT": ["microsoft", "surface", "xbox"],
                    "HUAWEI": ["huawei", "honor"],
                    "MOTOROLA": ["motorola", "moto"],
                    "CHANEL": ["chanel", "coco chanel"],
                    "DIOR": ["dior", "christian dior", "j'adore"],
                    "VERSACE": ["versace", "versus"],
                    "CALVIN KLEIN": ["calvin klein", "ck", "calvin"],
                    "HUGO BOSS": ["hugo boss", "boss", "hugo"],
                    "TOMMY HILFIGER": ["tommy hilfiger", "tommy"],
                    "RALPH LAUREN": ["ralph lauren", "polo", "polo ralph lauren"]
                }
            
            # Crear índice inverso
            self.brand_index = {}
            for canonical, aliases in self.brand_aliases.items():
                for alias in aliases:
                    self.brand_index[alias.lower()] = canonical
                    
        except Exception as e:
            logger.error(f"Error cargando marcas: {e}")
            self.brand_aliases = {}
            self.brand_index = {}
    
    def _load_attribute_schemas(self):
        """Definir esquemas de atributos por categoría"""
        self.attribute_schemas = {
            "smartphones": {
                "required": ["capacity", "color"],
                "optional": ["screen_size", "network", "processor", "ram", "camera"],
                "types": {
                    "capacity": "string",  # 128GB, 256GB, etc
                    "color": "string",
                    "screen_size": "float",  # 6.7
                    "network": "enum:4G,5G",
                    "processor": "string",
                    "ram": "string",  # 8GB
                    "camera": "string"  # 48MP
                },
                "validators": {
                    "capacity": lambda x: bool(re.match(r'^\d+[GT]B$', str(x).upper())),
                    "screen_size": lambda x: 3.0 <= float(x) <= 10.0 if x else True,
                    "network": lambda x: x in ["4G", "5G", "LTE"]
                }
            },
            "notebooks": {
                "required": ["ram", "storage"],
                "optional": ["screen_size", "processor", "graphics", "os"],
                "types": {
                    "ram": "string",  # 16GB
                    "storage": "string",  # 512GB SSD
                    "screen_size": "float",
                    "processor": "string",
                    "graphics": "string",
                    "os": "string"
                },
                "validators": {
                    "ram": lambda x: bool(re.match(r'^\d+GB', str(x))),
                    "storage": lambda x: bool(re.match(r'^\d+[GT]B', str(x))),
                    "screen_size": lambda x: 10.0 <= float(x) <= 20.0 if x else True
                }
            },
            "smart_tv": {
                "required": ["screen_size"],
                "optional": ["panel", "resolution", "smart_platform", "hdr"],
                "types": {
                    "screen_size": "float",
                    "panel": "enum:OLED,QLED,LED,LCD,4K,8K",
                    "resolution": "enum:HD,FHD,4K,8K",
                    "smart_platform": "string",
                    "hdr": "boolean"
                },
                "validators": {
                    "screen_size": lambda x: 20.0 <= float(x) <= 100.0,
                    "panel": lambda x: x in ["OLED", "QLED", "LED", "LCD", "4K", "8K"],
                    "resolution": lambda x: x in ["HD", "FHD", "4K", "8K", "1080p", "720p"]
                }
            },
            "perfumes": {
                "required": ["volume_ml"],
                "optional": ["concentration", "gender", "fragrance_family"],
                "types": {
                    "volume_ml": "integer",
                    "concentration": "enum:EDP,EDT,Parfum,Cologne,EDC",
                    "gender": "enum:Mujer,Hombre,Unisex",
                    "fragrance_family": "string"
                },
                "validators": {
                    "volume_ml": lambda x: 5 <= int(x) <= 500,
                    "concentration": lambda x: x in ["EDP", "EDT", "Parfum", "Cologne", "EDC"],
                    "gender": lambda x: x in ["Mujer", "Hombre", "Unisex", "Women", "Men"]
                }
            }
        }
        
        # Schema por defecto
        self.default_schema = {
            "required": [],
            "optional": ["size", "color", "material", "weight", "dimensions"],
            "types": {},
            "validators": {}
        }
    
    def _init_quality_thresholds(self):
        """Definir umbrales de calidad por categoría"""
        self.quality_thresholds = {
            "smartphones": {
                "min_confidence": 0.85,
                "min_coverage": 0.90,  # 90% de atributos requeridos
                "min_attributes": 2
            },
            "notebooks": {
                "min_confidence": 0.80,
                "min_coverage": 0.85,
                "min_attributes": 2
            },
            "smart_tv": {
                "min_confidence": 0.75,
                "min_coverage": 0.80,
                "min_attributes": 1
            },
            "perfumes": {
                "min_confidence": 0.70,
                "min_coverage": 0.75,
                "min_attributes": 1
            },
            "default": {
                "min_confidence": 0.70,
                "min_coverage": 0.70,
                "min_attributes": 0
            }
        }
    
    # ============================================================================
    # MÉTODOS DE VALIDACIÓN
    # ============================================================================
    
    def validate_taxonomy(self, category_suggestion: str, category_base: str) -> Tuple[bool, str, str]:
        """
        Validar categoría contra taxonomía
        
        Returns:
            (is_valid, final_category, reason)
        """
        if not category_suggestion:
            return True, category_base, "No suggestion"
        
        # Buscar en índice
        suggested_lower = category_suggestion.lower()
        
        # Exacto o sinónimo
        if suggested_lower in self.category_index:
            final_category = self.category_index[suggested_lower]
            return True, final_category, "Valid category"
        
        # Búsqueda parcial
        for key, cat_id in self.category_index.items():
            if suggested_lower in key or key in suggested_lower:
                return True, cat_id, "Partial match"
        
        # No válida, mantener base
        return False, category_base, f"Invalid category: {category_suggestion}"
    
    def validate_brand(self, brand: str) -> Tuple[str, bool]:
        """
        Validar y normalizar marca
        
        Returns:
            (canonical_brand, is_known)
        """
        if not brand:
            return "DESCONOCIDA", False
        
        brand_lower = brand.lower().strip()
        
        # Buscar en índice
        if brand_lower in self.brand_index:
            return self.brand_index[brand_lower], True
        
        # Búsqueda parcial
        for alias, canonical in self.brand_index.items():
            if alias in brand_lower or brand_lower in alias:
                return canonical, True
        
        # Marca desconocida pero válida
        if len(brand) > 1:
            return brand.upper(), False
        
        return "DESCONOCIDA", False
    
    def validate_attributes(self, attributes: Dict[str, Any], category: str) -> Tuple[bool, Dict[str, Any], List[str]]:
        """
        Validar atributos según esquema de categoría
        
        Returns:
            (is_valid, cleaned_attributes, errors)
        """
        schema = self.attribute_schemas.get(category, self.default_schema)
        cleaned = {}
        errors = []
        
        # Validar requeridos
        for req_attr in schema.get('required', []):
            if req_attr not in attributes or not attributes[req_attr]:
                errors.append(f"Missing required: {req_attr}")
            else:
                cleaned[req_attr] = attributes[req_attr]
        
        # Validar opcionales y tipos
        all_allowed = schema.get('required', []) + schema.get('optional', [])
        
        for attr, value in attributes.items():
            if attr not in all_allowed and all_allowed:
                # Atributo no permitido, omitir
                continue
            
            # Validar con función específica
            validators = schema.get('validators', {})
            if attr in validators:
                try:
                    if validators[attr](value):
                        cleaned[attr] = self._normalize_value(value, schema.get('types', {}).get(attr))
                    else:
                        errors.append(f"Invalid {attr}: {value}")
                except Exception as e:
                    errors.append(f"Validation error {attr}: {e}")
            else:
                # Sin validador específico, aceptar
                cleaned[attr] = self._normalize_value(value, schema.get('types', {}).get(attr))
        
        is_valid = len(errors) == 0 or len(errors) <= 1  # Tolerar 1 error
        return is_valid, cleaned, errors
    
    def _normalize_value(self, value: Any, type_hint: str = None) -> Any:
        """Normalizar valor según tipo"""
        if not type_hint:
            return value
        
        if type_hint == "integer":
            try:
                return int(float(str(value).replace(',', '')))
            except:
                return value
        
        elif type_hint == "float":
            try:
                return float(str(value).replace(',', '.'))
            except:
                return value
        
        elif type_hint.startswith("enum:"):
            allowed = type_hint.split(":", 1)[1].split(",")
            if str(value) in allowed:
                return value
            # Buscar match parcial
            value_lower = str(value).lower()
            for opt in allowed:
                if opt.lower() in value_lower or value_lower in opt.lower():
                    return opt
            return value
        
        elif type_hint == "boolean":
            return str(value).lower() in ["true", "yes", "sí", "1", "verdadero"]
        
        return value
    
    def validate_quality(self, result: Dict[str, Any], category: str) -> Tuple[bool, float, List[str]]:
        """
        Validar calidad del resultado (confidence y coverage)
        
        Returns:
            (passes_quality, quality_score, issues)
        """
        thresholds = self.quality_thresholds.get(category, self.quality_thresholds['default'])
        issues = []
        
        # Validar confidence
        confidence = result.get('confidence', 0.0)
        if confidence < thresholds['min_confidence']:
            issues.append(f"Low confidence: {confidence:.2f} < {thresholds['min_confidence']}")
        
        # Validar coverage de atributos
        schema = self.attribute_schemas.get(category, self.default_schema)
        required_attrs = schema.get('required', [])
        attributes = result.get('attributes', {})
        
        if required_attrs:
            present = sum(1 for attr in required_attrs if attr in attributes and attributes[attr])
            coverage = present / len(required_attrs) if required_attrs else 1.0
            
            if coverage < thresholds['min_coverage']:
                issues.append(f"Low coverage: {coverage:.1%} < {thresholds['min_coverage']:.1%}")
        else:
            coverage = 1.0
        
        # Validar cantidad mínima de atributos
        if len(attributes) < thresholds.get('min_attributes', 0):
            issues.append(f"Too few attributes: {len(attributes)} < {thresholds['min_attributes']}")
        
        # Calcular score de calidad
        quality_score = (confidence * 0.6) + (coverage * 0.4)
        
        passes = len(issues) == 0
        return passes, quality_score, issues
    
    def validate_complete(self, result: Dict[str, Any], category_base: str = None) -> Dict[str, Any]:
        """
        Validación completa de un resultado
        
        Returns:
            {
                'valid': bool,
                'result': cleaned_result,
                'errors': [],
                'warnings': [],
                'quality_score': float
            }
        """
        errors = []
        warnings = []
        
        # 1. Validar estructura básica
        required_fields = ['brand', 'model', 'normalized_name', 'attributes', 'confidence']
        for field in required_fields:
            if field not in result:
                errors.append(f"Missing field: {field}")
                result[field] = "" if field != 'attributes' else {}
        
        # 2. Validar y corregir marca
        brand, is_known = self.validate_brand(result.get('brand', ''))
        result['brand'] = brand
        if not is_known and brand != "DESCONOCIDA":
            warnings.append(f"Unknown brand: {brand}")
        
        # 3. Validar taxonomía
        category_suggestion = result.get('category_suggestion', '')
        is_valid_cat, final_category, reason = self.validate_taxonomy(
            category_suggestion, 
            category_base or category_suggestion or 'general'
        )
        
        if not is_valid_cat:
            warnings.append(reason)
        
        result['category'] = final_category
        
        # 4. Validar atributos
        attributes = result.get('attributes', {})
        attr_valid, cleaned_attrs, attr_errors = self.validate_attributes(attributes, final_category)
        result['attributes'] = cleaned_attrs
        
        if not attr_valid:
            warnings.extend(attr_errors)
        
        # 5. Validar calidad
        passes_quality, quality_score, quality_issues = self.validate_quality(result, final_category)
        
        if not passes_quality:
            warnings.extend(quality_issues)
        
        # 6. Validar nombre normalizado
        if not result.get('normalized_name') or len(result['normalized_name']) < 5:
            result['normalized_name'] = f"{brand} {result.get('model', 'Producto')}"
            warnings.append("Generated normalized_name")
        
        # Determinar si es válido
        is_valid = len(errors) == 0 and (passes_quality or len(warnings) <= 2)
        
        return {
            'valid': is_valid,
            'result': result,
            'errors': errors,
            'warnings': warnings,
            'quality_score': quality_score,
            'needs_fallback': not passes_quality and quality_score < 0.6
        }

# ============================================================================
# Quality Gating Functions
# ============================================================================

class QualityGate:
    """Sistema de quality gating para decisiones de fallback"""
    
    def __init__(self, validator: StrictValidator):
        self.validator = validator
    
    def should_fallback(self, result: Dict[str, Any], category: str) -> Tuple[bool, str]:
        """
        Determinar si se debe hacer fallback a modelo superior
        
        Returns:
            (should_fallback, reason)
        """
        # JSON inválido
        if not isinstance(result, dict):
            return True, "Invalid JSON structure"
        
        # Campos críticos faltantes
        if not result.get('brand') or not result.get('model'):
            return True, "Missing critical fields"
        
        # Validar calidad
        passes, score, issues = self.validator.validate_quality(result, category)
        
        if not passes and score < 0.5:
            return True, f"Low quality score: {score:.2f}"
        
        # Categoría inválida
        if result.get('category_suggestion'):
            is_valid, _, _ = self.validator.validate_taxonomy(
                result['category_suggestion'], 
                category
            )
            if not is_valid and result.get('confidence', 0) > 0.8:
                return True, "Invalid category with high confidence"
        
        return False, "OK"
    
    def should_retry(self, error: Exception) -> bool:
        """Determinar si se debe reintentar"""
        error_str = str(error).lower()
        
        # Errores que ameritan retry
        retry_errors = [
            'timeout', 'connection', 'rate limit',
            'temporary', 'unavailable', '503', '429'
        ]
        
        return any(err in error_str for err in retry_errors)

# Singleton
_validator = None
_quality_gate = None

def get_validator() -> StrictValidator:
    """Obtener instancia singleton del validador"""
    global _validator
    if _validator is None:
        _validator = StrictValidator()
    return _validator

def get_quality_gate() -> QualityGate:
    """Obtener instancia singleton del quality gate"""
    global _quality_gate
    if _quality_gate is None:
        _quality_gate = QualityGate(get_validator())
    return _quality_gate

if __name__ == "__main__":
    # Testing
    validator = get_validator()
    gate = get_quality_gate()
    
    # Test resultado
    test_result = {
        "brand": "apple",
        "model": "iPhone 15 Pro Max",
        "normalized_name": "APPLE iPhone 15 Pro Max 256GB Negro",
        "attributes": {
            "capacity": "256GB",
            "color": "negro",
            "screen_size": 6.7,
            "network": "5G"
        },
        "confidence": 0.92,
        "category_suggestion": "smartphones"
    }
    
    validation = validator.validate_complete(test_result, "smartphones")
    
    print("=== VALIDATION RESULT ===")
    print(f"Valid: {validation['valid']}")
    print(f"Quality Score: {validation['quality_score']:.2f}")
    print(f"Errors: {validation['errors']}")
    print(f"Warnings: {validation['warnings']}")
    print(f"Needs Fallback: {validation['needs_fallback']}")
    
    # Test fallback decision
    should_fallback, reason = gate.should_fallback(test_result, "smartphones")
    print(f"\nShould Fallback: {should_fallback} ({reason})")