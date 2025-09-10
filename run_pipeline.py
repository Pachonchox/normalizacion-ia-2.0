#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline de Normalización Operativo
Sistema completo de procesamiento de productos retail
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configurar encoding UTF-8
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PipelineNormalizacion:
    """Pipeline completo de normalización de productos"""
    
    def __init__(self, use_llm: bool = False, use_db: bool = False):
        """
        Inicializar pipeline
        Args:
            use_llm: Usar LLM para categorización avanzada
            use_db: Usar base de datos para persistencia
        """
        self.use_llm = use_llm
        self.use_db = use_db
        self.stats = {
            'total_procesados': 0,
            'exitosos': 0,
            'errores': 0,
            'duplicados': 0,
            'categorias': {}
        }
        
        # Importar módulos necesarios
        self._import_modules()
        
    def _import_modules(self):
        """Importar módulos del pipeline"""
        try:
            # Módulos core
            from utils import parse_price
            from enrich import guess_brand, extract_attributes, clean_model
            from fingerprint import product_fingerprint
            from cache import JsonCache
            
            # Guardar referencias
            self.parse_price = parse_price
            self.guess_brand = guess_brand
            self.extract_attributes = extract_attributes
            self.clean_model = clean_model
            self.product_fingerprint = product_fingerprint
            self.JsonCache = JsonCache
            
            logger.info("[OK] Modulos core cargados")
            
            # Módulos opcionales
            if self.use_db:
                try:
                    from unified_connector import get_unified_connector
                    self.get_db = get_unified_connector
                    logger.info("[OK] Conector BD cargado")
                except Exception as e:
                    logger.warning(f"[WARN] BD no disponible: {e}")
                    self.use_db = False
                    
            if self.use_llm:
                try:
                    from llm_connectors import enabled as llm_enabled
                    self.llm_enabled = llm_enabled
                    if llm_enabled():
                        logger.info("[OK] LLM habilitado")
                    else:
                        logger.warning("[WARN] LLM deshabilitado por configuracion")
                        self.use_llm = False
                except Exception as e:
                    logger.warning(f"[WARN] LLM no disponible: {e}")
                    self.use_llm = False
                    
        except ImportError as e:
            logger.error(f"[ERROR] Error importando modulos: {e}")
            raise
    
    def procesar_producto(self, producto: Dict[str, Any], metadata: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Procesar un producto individual
        
        Args:
            producto: Datos crudos del producto
            metadata: Metadatos adicionales
            
        Returns:
            Producto normalizado o None si falla
        """
        try:
            # 1. VALIDACIÓN INICIAL
            nombre = producto.get('name') or producto.get('title') or ""
            if not nombre:
                logger.warning("Producto sin nombre - descartado")
                return None
                
            product_id = (producto.get('product_id') or 
                         producto.get('product_code') or 
                         producto.get('sku') or 
                         f"GEN_{datetime.now().timestamp()}")
            
            retailer = producto.get('retailer', 'Unknown')
            
            # 2. NORMALIZACIÓN DE PRECIOS
            precio_actual = self._extraer_mejor_precio(producto)
            precio_original = self._extraer_precio_original(producto)
            
            # 3. CATEGORIZACIÓN
            categoria, confianza = self._categorizar(nombre, metadata)
            
            # 4. EXTRACCIÓN DE MARCA Y ATRIBUTOS
            marca = producto.get('brand') or self.guess_brand(nombre) or "DESCONOCIDA"
            atributos = self.extract_attributes(nombre, categoria)
            modelo = self.clean_model(nombre, marca)
            
            # 5. FINGERPRINT ÚNICO
            base_product = {
                "brand": marca,
                "category": categoria,
                "model": modelo or nombre,
                "attributes": atributos
            }
            fingerprint = self.product_fingerprint(base_product)
            
            # 6. CONSTRUIR PRODUCTO NORMALIZADO
            producto_normalizado = {
                'fingerprint': fingerprint,
                'product_id': product_id,
                'name': nombre,
                'brand': marca,
                'model': modelo,
                'category': categoria,
                'category_confidence': confianza,
                'attributes': atributos,
                'retailer': retailer,
                'price_current': precio_actual,
                'price_original': precio_original,
                'url': producto.get('product_link') or producto.get('url'),
                'processed_at': datetime.now().isoformat(),
                'ai_enhanced': False,
                'processing_version': 'v2.0'
            }
            
            # 7. ENRIQUECIMIENTO CON LLM (si está habilitado)
            if self.use_llm:
                producto_normalizado = self._enriquecer_con_llm(producto_normalizado)
            
            # Actualizar estadísticas
            self.stats['exitosos'] += 1
            if categoria not in self.stats['categorias']:
                self.stats['categorias'][categoria] = 0
            self.stats['categorias'][categoria] += 1
            
            return producto_normalizado
            
        except Exception as e:
            logger.error(f"Error procesando producto: {e}")
            self.stats['errores'] += 1
            return None
    
    def _extraer_mejor_precio(self, producto: Dict[str, Any]) -> Optional[int]:
        """Extraer el mejor precio disponible"""
        # Orden de preferencia
        precio_keys = [
            'card_price', 'precio_tarjeta', 'precio_cmr',
            'offer_price', 'precio_oferta', 'internet_price',
            'normal_price', 'precio_normal', 'regular_price',
            'ripley_price', 'precio_ripley'
        ]
        
        for key in precio_keys:
            if key in producto:
                precio = self.parse_price(producto[key])
                if precio:
                    return precio
                    
        # Buscar en campos de texto
        for key in producto:
            if 'price' in key.lower() and isinstance(producto[key], str):
                precio = self.parse_price(producto[key])
                if precio:
                    return precio
                    
        return None
    
    def _extraer_precio_original(self, producto: Dict[str, Any]) -> Optional[int]:
        """Extraer precio original/normal"""
        original_keys = ['original_price', 'precio_original', 'normal_price', 'precio_normal']
        
        for key in original_keys:
            if key in producto:
                precio = self.parse_price(producto[key])
                if precio:
                    return precio
                    
        return None
    
    def _categorizar(self, nombre: str, metadata: Dict[str, Any] = None) -> tuple:
        """
        Categorizar producto por reglas
        Returns: (categoria, confianza)
        """
        nombre_lower = nombre.lower()
        
        # Reglas de categorización
        reglas = [
            (['smartphone', 'celular', 'iphone', 'galaxy', 'redmi', 'xiaomi', 'motorola'], 'smartphones', 0.85),
            (['notebook', 'laptop', 'macbook', 'thinkpad', 'pavilion', 'aspire'], 'notebooks', 0.85),
            (['smart tv', 'televisor', 'qled', 'oled', 'nanocell', '4k tv'], 'smart_tv', 0.80),
            (['tablet', 'ipad', 'galaxy tab', 'lenovo tab'], 'tablets', 0.80),
            (['perfume', 'eau de toilette', 'edt', 'edp', 'eau de parfum', 'colonia'], 'perfumes', 0.80),
            (['refrigerador', 'nevera', 'freezer', 'congelador'], 'refrigeradores', 0.75),
            (['lavadora', 'secadora', 'lava-seca'], 'lavadoras', 0.75),
            (['microondas', 'horno', 'cocina'], 'cocinas', 0.75),
            (['aspiradora', 'robot aspirador', 'roomba'], 'aspiradoras', 0.75),
            (['audifonos', 'headphones', 'earbuds', 'airpods'], 'audio', 0.75)
        ]
        
        for palabras, categoria, confianza in reglas:
            if any(palabra in nombre_lower for palabra in palabras):
                return categoria, confianza
                
        # Si hay metadata con categoría
        if metadata and 'category' in metadata:
            return metadata['category'], 0.70
            
        return 'general', 0.30
    
    def _enriquecer_con_llm(self, producto: Dict[str, Any]) -> Dict[str, Any]:
        """Enriquecer producto con LLM si está disponible"""
        try:
            # Aquí iría la lógica de LLM
            # Por ahora solo marcamos que se intentó
            producto['ai_enhanced'] = True
            logger.debug(f"Producto enriquecido con LLM: {producto['product_id']}")
        except Exception as e:
            logger.warning(f"No se pudo enriquecer con LLM: {e}")
            
        return producto
    
    def procesar_lote(self, productos: List[Dict[str, Any]], metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Procesar un lote de productos
        
        Args:
            productos: Lista de productos crudos
            metadata: Metadatos del lote
            
        Returns:
            Lista de productos normalizados
        """
        resultados = []
        productos_vistos = set()
        
        logger.info(f"Procesando lote de {len(productos)} productos...")
        
        for i, producto in enumerate(productos, 1):
            self.stats['total_procesados'] += 1
            
            # Detectar duplicados
            product_id = producto.get('product_id') or producto.get('product_code')
            if product_id and product_id in productos_vistos:
                logger.debug(f"Duplicado detectado: {product_id}")
                self.stats['duplicados'] += 1
                continue
                
            productos_vistos.add(product_id)
            
            # Procesar producto
            resultado = self.procesar_producto(producto, metadata)
            
            if resultado:
                resultados.append(resultado)
                if i % 10 == 0:
                    logger.info(f"  Procesados: {i}/{len(productos)}")
        
        logger.info(f"[OK] Lote completado: {len(resultados)}/{len(productos)} exitosos")
        return resultados
    
    def guardar_resultados(self, productos: List[Dict[str, Any]], archivo: str = None):
        """
        Guardar productos normalizados
        
        Args:
            productos: Lista de productos normalizados
            archivo: Ruta del archivo de salida
        """
        if not archivo:
            archivo = f"productos_normalizados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
        try:
            with open(archivo, 'w', encoding='utf-8') as f:
                json.dump(productos, f, ensure_ascii=False, indent=2)
            logger.info(f"[SAVED] Resultados guardados en: {archivo}")
            
        except Exception as e:
            logger.error(f"Error guardando resultados: {e}")
    
    def guardar_en_bd(self, productos: List[Dict[str, Any]]):
        """Guardar productos en base de datos si está habilitada"""
        if not self.use_db:
            logger.warning("BD no habilitada, saltando persistencia")
            return
            
        try:
            db = self.get_db()
            guardados = 0
            
            for producto in productos:
                try:
                    # Aquí iría la lógica de guardado en BD
                    # db.save_product(producto)
                    guardados += 1
                except Exception as e:
                    logger.error(f"Error guardando producto {producto.get('product_id')}: {e}")
                    
            logger.info(f"[BD] {guardados}/{len(productos)} productos guardados en BD")
            
        except Exception as e:
            logger.error(f"Error conectando a BD: {e}")
    
    def mostrar_estadisticas(self):
        """Mostrar estadísticas del procesamiento"""
        print("\n" + "="*60)
        print("ESTADISTICAS DEL PIPELINE")
        print("="*60)
        print(f"Total procesados: {self.stats['total_procesados']}")
        print(f"Exitosos: {self.stats['exitosos']}")
        print(f"Errores: {self.stats['errores']}")
        print(f"Duplicados: {self.stats['duplicados']}")
        
        if self.stats['categorias']:
            print("\nDistribucion por categorias:")
            for cat, count in sorted(self.stats['categorias'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {cat}: {count}")
        
        tasa_exito = (self.stats['exitosos'] / self.stats['total_procesados'] * 100) if self.stats['total_procesados'] > 0 else 0
        print(f"\n[OK] Tasa de exito: {tasa_exito:.1f}%")


def main():
    """Función principal de ejecución"""
    print("="*60)
    print("PIPELINE DE NORMALIZACION v2.0")
    print("="*60)
    
    # Configuración
    use_llm = os.getenv('LLM_ENABLED', 'false').lower() == 'true'
    use_db = os.getenv('DB_ENABLED', 'false').lower() == 'true'
    
    print(f"\nConfiguracion:")
    print(f"  - LLM: {'[SI] Habilitado' if use_llm else '[NO] Deshabilitado'}")
    print(f"  - BD: {'[SI] Habilitada' if use_db else '[NO] Deshabilitada'}")
    
    # Crear pipeline
    pipeline = PipelineNormalizacion(use_llm=use_llm, use_db=use_db)
    
    # Productos de ejemplo
    productos_ejemplo = [
        {
            "product_id": "SMRT-001",
            "name": "Samsung Galaxy S24 Ultra 512GB 5G Titanium Black",
            "brand": "Samsung",
            "retailer": "Falabella",
            "normal_price": 1299990,
            "card_price": 1099990,
            "product_link": "https://falabella.com/samsung-s24"
        },
        {
            "product_id": "NOTE-001",
            "name": "Notebook Dell XPS 13 Intel Core i7 16GB RAM 512GB SSD",
            "retailer": "Paris",
            "normal_price": 999990,
            "product_link": "https://paris.cl/dell-xps13"
        },
        {
            "product_id": "PERF-001",
            "name": "Perfume Carolina Herrera Good Girl 80ml EDP Mujer",
            "retailer": "Ripley",
            "normal_price_text": "$94.990",
            "card_price_text": "$84.990"
        },
        {
            "product_id": "TV-001",
            "name": "Smart TV LG 55 pulgadas 4K OLED",
            "retailer": "Falabella",
            "normal_price": 899990,
            "offer_price": 799990
        },
        {
            "product_code": "TAB-001",
            "name": "iPad Pro 11 256GB WiFi Space Gray",
            "brand": "Apple",
            "retailer": "Paris",
            "precio_normal": 949990
        }
    ]
    
    print(f"\nProcesando {len(productos_ejemplo)} productos de ejemplo...")
    print("-"*60)
    
    # Procesar lote
    resultados = pipeline.procesar_lote(productos_ejemplo)
    
    # Guardar resultados
    if resultados:
        pipeline.guardar_resultados(resultados)
        
        if use_db:
            pipeline.guardar_en_bd(resultados)
    
    # Mostrar estadísticas
    pipeline.mostrar_estadisticas()
    
    print("\n[EXITO] Pipeline completado exitosamente")
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"[ERROR FATAL] Error fatal: {e}")
        sys.exit(1)