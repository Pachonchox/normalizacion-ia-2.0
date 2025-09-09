#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧹 FILTRO DE PRODUCTOS RUIDOSOS
Elimina productos que no son útiles para análisis de IA:
- Accesorios 
- Productos bajo $50.000
- Productos reacondicionados/usados
"""

import json
import re
import os
import logging
from typing import Dict, List, Any
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ProductFilter:
    """Filtro de productos ruidosos"""
    
    def __init__(self):
        # Palabras clave para detectar accesorios
        self.accessory_keywords = [
            'accesorio', 'accesoria', 'cable', 'cargador', 'funda', 'case',
            'protector', 'mica', 'audifonos', 'audifono', 'parlante', 'bocina',
            'soporte', 'base', 'tripode', 'adaptador', 'convertidor',
            'correa', 'pulsera', 'brazalete', 'control', 'mando', 'joystick',
            'teclado', 'mouse', 'raton', 'pad', 'alfombrilla', 'mousepad',
            'memoria', 'usb', 'pendrive', 'tarjeta', 'sd', 'micro',
            'bateria', 'pila', 'powerbank', 'carga', 'repuesto',
            'filtro', 'bolsa', 'estuche', 'maletin', 'kit'
        ]
        
        # Palabras clave para detectar reacondicionados
        self.refurbished_keywords = [
            'reacondicionado', 'usado', 'segunda mano', 'refurbished',
            'open box', 'demo', 'demostracion', 'exhibicion', 'muestra',
            'dañado', 'defecto', 'reparado', 'restaurado', 'seminuevo'
        ]
        
        # Precio mínimo (50.000 pesos chilenos)
        self.min_price = 50000
    
    def extract_price(self, price_text: str) -> float:
        """Extraer precio numérico del texto"""
        if not price_text:
            return 0.0
        
        # Remover caracteres no numéricos excepto puntos y comas
        clean_price = re.sub(r'[^\d.,]', '', str(price_text))
        
        # Manejar diferentes formatos de precio
        if ',' in clean_price and '.' in clean_price:
            # Formato: 1.234,56 -> 1234.56
            clean_price = clean_price.replace('.', '').replace(',', '.')
        elif ',' in clean_price:
            # Formato: 1,234 -> 1234 o 12,34 -> 12.34
            parts = clean_price.split(',')
            if len(parts[-1]) <= 2:  # Decimales
                clean_price = clean_price.replace(',', '.')
            else:  # Miles
                clean_price = clean_price.replace(',', '')
        
        try:
            return float(clean_price)
        except ValueError:
            logging.warning(f"No se pudo convertir precio: {price_text}")
            return 0.0
    
    def is_accessory(self, product: Dict[str, Any]) -> bool:
        """Verificar si es un accesorio"""
        text_to_check = ""
        
        # Obtener texto del producto - campos reales de nuestros scrapers
        for field in ['name', 'nombre', 'titulo', 'title', 'descripcion', 'description', 'categoria', 'category']:
            if field in product and product[field]:
                text_to_check += f" {product[field]}"
        
        text_to_check = text_to_check.lower()
        
        # Buscar palabras clave de accesorios
        for keyword in self.accessory_keywords:
            if keyword in text_to_check:
                return True
        
        return False
    
    def is_low_price(self, product: Dict[str, Any]) -> bool:
        """Verificar si el precio está bajo el mínimo"""
        # Campos reales de nuestros scrapers
        price_fields = [
            'card_price', 'normal_price', 'ripley_price', 'original_price',
            'precio', 'price', 'precio_actual', 'precio_normal'
        ]
        
        for field in price_fields:
            if field in product and product[field]:
                price = self.extract_price(str(product[field]))
                if price > 0:
                    return price < self.min_price
        
        return False
    
    def is_refurbished(self, product: Dict[str, Any]) -> bool:
        """Verificar si es reacondicionado"""
        text_to_check = ""
        
        # Obtener texto del producto - campos reales de nuestros scrapers
        for field in ['name', 'nombre', 'titulo', 'title', 'descripcion', 'description', 'condicion', 'condition']:
            if field in product and product[field]:
                text_to_check += f" {product[field]}"
        
        text_to_check = text_to_check.lower()
        
        # Buscar palabras clave de reacondicionados
        for keyword in self.refurbished_keywords:
            if keyword in text_to_check:
                return True
        
        return False
    
    def should_filter_out(self, product: Dict[str, Any]) -> tuple[bool, str]:
        """Determinar si un producto debe ser filtrado"""
        reasons = []
        
        if self.is_accessory(product):
            reasons.append("accesorio")
        
        if self.is_low_price(product):
            reasons.append("precio_bajo")
        
        if self.is_refurbished(product):
            reasons.append("reacondicionado")
        
        should_filter = len(reasons) > 0
        reason = ", ".join(reasons) if reasons else ""
        
        return should_filter, reason
    
    def filter_products(self, products: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], Dict[str, int]]:
        """Filtrar lista de productos"""
        filtered_products = []
        stats = {
            'total_original': len(products),
            'filtered_accessory': 0,
            'filtered_low_price': 0,
            'filtered_refurbished': 0,
            'total_filtered': 0,
            'total_remaining': 0
        }
        
        for product in products:
            should_filter, reason = self.should_filter_out(product)
            
            if should_filter:
                stats['total_filtered'] += 1
                if 'accesorio' in reason:
                    stats['filtered_accessory'] += 1
                if 'precio_bajo' in reason:
                    stats['filtered_low_price'] += 1
                if 'reacondicionado' in reason:
                    stats['filtered_refurbished'] += 1
                
                logging.debug(f"Producto filtrado ({reason}): {product.get('nombre', 'Sin nombre')}")
            else:
                filtered_products.append(product)
        
        stats['total_remaining'] = len(filtered_products)
        
        return filtered_products, stats
    
    def filter_json_file(self, input_file: str, output_file: str = None, replace_original: bool = False) -> Dict[str, int]:
        """Filtrar archivo JSON de productos"""
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Archivo no encontrado: {input_file}")
        
        # Leer archivo original
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extraer productos (puede estar en diferentes estructuras)
        products = []
        if isinstance(data, list):
            products = data
        elif isinstance(data, dict):
            # Buscar lista de productos en el JSON
            for key in ['products', 'productos', 'items', 'data', 'results']:
                if key in data and isinstance(data[key], list):
                    products = data[key]
                    break
        
        if not products:
            logging.warning(f"No se encontraron productos en {input_file}")
            return {'total_original': 0, 'total_remaining': 0, 'total_filtered': 0}
        
        # Filtrar productos
        filtered_products, stats = self.filter_products(products)
        
        # Crear archivo de salida
        if replace_original:
            # Reemplazar el archivo original
            output_file = input_file
        elif output_file is None:
            path = Path(input_file)
            output_file = str(path.parent / f"{path.stem}_filtered{path.suffix}")
        
        # Guardar productos filtrados
        if isinstance(data, list):
            filtered_data = filtered_products
        else:
            filtered_data = data.copy()
            # Actualizar la lista de productos en la estructura original
            for key in ['products', 'productos', 'items', 'data', 'results']:
                if key in filtered_data:
                    filtered_data[key] = filtered_products
                    break
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, ensure_ascii=False, indent=2)
        
        # Log de estadísticas
        logging.info(f"📊 Filtrado completado para {input_file}")
        logging.info(f"  Total original: {stats['total_original']}")
        logging.info(f"  Filtrados por accesorio: {stats['filtered_accessory']}")
        logging.info(f"  Filtrados por precio bajo: {stats['filtered_low_price']}")
        logging.info(f"  Filtrados por reacondicionado: {stats['filtered_refurbished']}")
        logging.info(f"  Total filtrados: {stats['total_filtered']}")
        logging.info(f"  Productos válidos restantes: {stats['total_remaining']}")
        logging.info(f"  Archivo guardado: {output_file}")
        
        return stats

def main():
    """Función principal para testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Filtrar productos ruidosos')
    parser.add_argument('input_file', help='Archivo JSON de entrada')
    parser.add_argument('--output', help='Archivo JSON de salida (opcional)')
    parser.add_argument('--verbose', action='store_true', help='Modo verbose')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    filter_instance = ProductFilter()
    try:
        stats = filter_instance.filter_json_file(args.input_file, args.output)
        print(f"Filtrado exitoso: {stats['total_remaining']}/{stats['total_original']} productos validos")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())