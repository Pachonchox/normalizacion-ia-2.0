#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ Validador de Integridad Automático
Sistema preventivo para garantizar integridad ANTES de cualquier operación
"""

import sys
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Agregar src al path si no está
if os.path.dirname(__file__) not in sys.path:
    sys.path.append(os.path.dirname(__file__))

from unified_connector import get_unified_connector

class IntegrityValidator:
    """Validador automático de integridad para sistema productivo"""
    
    def __init__(self):
        self.connector = get_unified_connector()
        self.errors = []
        self.warnings = []
        
    def validate_all(self) -> Tuple[bool, Dict]:
        """Ejecutar todas las validaciones de integridad"""
        self.errors = []
        self.warnings = []
        
        print("VALIDACION AUTOMATICA DE INTEGRIDAD")
        print("=" * 40)
        
        # 1. Validar integridad productos-precios
        products_prices_ok = self._validate_products_prices_integrity()
        
        # 2. Validar cache IA
        cache_ok = self._validate_ai_cache_integrity()
        
        # 3. Validar retailers
        retailers_ok = self._validate_retailers()
        
        # 4. Validar datos corruptos
        data_ok = self._validate_data_quality()
        
        # 5. Validar productos test residuales
        test_data_ok = self._validate_no_test_data()
        
        # Resultado final
        all_validations_ok = all([
            products_prices_ok,
            cache_ok, 
            retailers_ok,
            data_ok,
            test_data_ok
        ])
        
        # Generar reporte
        report = {
            'integrity_ok': all_validations_ok,
            'timestamp': datetime.now().isoformat(),
            'validations': {
                'products_prices': products_prices_ok,
                'ai_cache': cache_ok,
                'retailers': retailers_ok,
                'data_quality': data_ok,
                'no_test_data': test_data_ok
            },
            'errors': self.errors,
            'warnings': self.warnings,
            'stats': self._get_current_stats()
        }
        
        self._print_validation_summary(report)
        
        return all_validations_ok, report
    
    def _validate_products_prices_integrity(self) -> bool:
        """Validar integridad productos-precios 1:1"""
        try:
            stats = self.connector.execute_query("""
                SELECT 
                    (SELECT COUNT(*) FROM productos_maestros WHERE active = true) as productos_activos,
                    (SELECT COUNT(*) FROM precios_actuales) as precios_totales,
                    (SELECT COUNT(*) FROM productos_maestros pm WHERE pm.active = true 
                     AND pm.product_id NOT IN (SELECT DISTINCT product_id FROM precios_actuales)) as productos_sin_precios,
                    (SELECT COUNT(*) FROM precios_actuales pa 
                     WHERE pa.product_id NOT IN (SELECT DISTINCT product_id FROM productos_maestros WHERE active = true)) as precios_huerfanos
            """)[0]
            
            productos_sin_precios = stats['productos_sin_precios']
            precios_huerfanos = stats['precios_huerfanos']
            productos_activos = stats['productos_activos']
            precios_totales = stats['precios_totales']
            
            print(f"\n1. INTEGRIDAD PRODUCTOS-PRECIOS:")
            print(f"   Productos activos: {productos_activos}")
            print(f"   Precios totales: {precios_totales}")
            print(f"   Productos sin precios: {productos_sin_precios}")
            print(f"   Precios huerfanos: {precios_huerfanos}")
            
            # Validaciones críticas
            if productos_sin_precios > 0:
                self.errors.append(f"{productos_sin_precios} productos sin precios")
                
            if precios_huerfanos > 0:
                self.errors.append(f"{precios_huerfanos} precios huerfanos")
                
            if productos_activos != precios_totales:
                self.errors.append(f"Desbalance: {productos_activos} productos != {precios_totales} precios")
            
            integrity_ok = (productos_sin_precios == 0 and 
                           precios_huerfanos == 0 and 
                           productos_activos == precios_totales)
            
            print(f"   Estado: {'OK' if integrity_ok else 'ERROR'}")
            return integrity_ok
            
        except Exception as e:
            self.errors.append(f"Error validando productos-precios: {e}")
            return False
    
    def _validate_ai_cache_integrity(self) -> bool:
        """Validar integridad cache IA"""
        try:
            stats = self.connector.execute_query("""
                SELECT 
                    (SELECT COUNT(*) FROM productos_maestros WHERE active = true) as productos_activos,
                    (SELECT COUNT(*) FROM ai_metadata_cache) as cache_total,
                    (SELECT COUNT(*) FROM ai_metadata_cache amc 
                     WHERE amc.fingerprint NOT IN (SELECT DISTINCT fingerprint FROM productos_maestros WHERE active = true)) as cache_huerfano
            """)[0]
            
            productos_activos = stats['productos_activos']
            cache_total = stats['cache_total']
            cache_huerfano = stats['cache_huerfano']
            
            print(f"\n2. INTEGRIDAD CACHE IA:")
            print(f"   Productos activos: {productos_activos}")
            print(f"   Cache IA total: {cache_total}")
            print(f"   Cache huerfano: {cache_huerfano}")
            
            # El cache puede ser >= productos (productos similares comparten cache)
            if cache_huerfano > 0:
                self.warnings.append(f"{cache_huerfano} entradas cache IA huerfanas")
                
            # El cache debe tener al menos tantas entradas como productos únicos
            if cache_total < productos_activos * 0.8:  # Permitir 20% margen
                self.warnings.append(f"Cache IA bajo: {cache_total} vs {productos_activos} productos")
            
            cache_ok = cache_huerfano == 0
            print(f"   Estado: {'OK' if cache_ok else 'ADVERTENCIA'}")
            return True  # No es crítico para el funcionamiento
            
        except Exception as e:
            self.errors.append(f"Error validando cache IA: {e}")
            return False
    
    def _validate_retailers(self) -> bool:
        """Validar retailers activos"""
        try:
            retailers = self.connector.execute_query("""
                SELECT id, name, active FROM retailers ORDER BY id
            """)
            
            active_retailers = [r for r in retailers if r['active']]
            
            print(f"\n3. RETAILERS:")
            print(f"   Total retailers: {len(retailers)}")
            print(f"   Retailers activos: {len(active_retailers)}")
            
            for retailer in active_retailers:
                print(f"   - {retailer['id']}: {retailer['name']}")
            
            # Debe haber al menos 1 retailer activo
            if len(active_retailers) == 0:
                self.errors.append("No hay retailers activos")
                return False
                
            # Verificar que Paris (ID=1) esté disponible como fallback
            paris_active = any(r['id'] == 1 and r['active'] for r in retailers)
            if not paris_active:
                self.warnings.append("Paris (ID=1) no está activo como fallback")
            
            print(f"   Estado: OK")
            return True
            
        except Exception as e:
            self.errors.append(f"Error validando retailers: {e}")
            return False
    
    def _validate_data_quality(self) -> bool:
        """Validar calidad de datos"""
        try:
            print(f"\n4. CALIDAD DE DATOS:")
            
            # Verificar productos con nombres vacíos
            empty_names = self.connector.execute_query("""
                SELECT COUNT(*) as count FROM productos_maestros 
                WHERE active = true AND (name IS NULL OR TRIM(name) = '')
            """)[0]['count']
            
            if empty_names > 0:
                self.errors.append(f"{empty_names} productos con nombres vacíos")
            
            # Verificar precios en 0 o negativos
            invalid_prices = self.connector.execute_query("""
                SELECT COUNT(*) as count FROM precios_actuales 
                WHERE (precio_normal <= 0 OR precio_normal IS NULL) 
                AND (precio_tarjeta <= 0 OR precio_tarjeta IS NULL)
            """)[0]['count']
            
            if invalid_prices > 0:
                self.errors.append(f"{invalid_prices} productos con precios inválidos")
            
            # Verificar productos sin categoría
            no_category = self.connector.execute_query("""
                SELECT COUNT(*) as count FROM productos_maestros 
                WHERE active = true AND (category IS NULL OR TRIM(category) = '')
            """)[0]['count']
            
            if no_category > 0:
                self.warnings.append(f"{no_category} productos sin categoría")
            
            print(f"   Nombres vacíos: {empty_names}")
            print(f"   Precios inválidos: {invalid_prices}")
            print(f"   Sin categoría: {no_category}")
            
            data_ok = empty_names == 0 and invalid_prices == 0
            print(f"   Estado: {'OK' if data_ok else 'ERROR'}")
            return data_ok
            
        except Exception as e:
            self.errors.append(f"Error validando calidad de datos: {e}")
            return False
    
    def _validate_no_test_data(self) -> bool:
        """Validar que no hay datos de test"""
        try:
            result = self.connector.execute_query("""
                SELECT COUNT(*) as count FROM productos_maestros 
                WHERE active = true 
                AND (LOWER(name) LIKE %s OR LOWER(name) LIKE %s)
            """, ['%test%', '%prueba%'])
            
            test_products = result[0]['count'] if result else 0
            
            print(f"\n5. DATOS TEST:")
            print(f"   Productos test: {test_products}")
            
            if test_products > 0:
                self.errors.append(f"{test_products} productos de test encontrados")
                print(f"   Estado: ERROR")
                return False
            
            print(f"   Estado: OK")
            return True
            
        except Exception as e:
            self.errors.append(f"Error validando datos test: {e}")
            return False
    
    def _get_current_stats(self) -> Dict:
        """Obtener estadísticas actuales"""
        try:
            stats = self.connector.execute_query("""
                SELECT 
                    (SELECT COUNT(*) FROM productos_maestros WHERE active = true) as productos_activos,
                    (SELECT COUNT(*) FROM precios_actuales) as precios_totales,
                    (SELECT COUNT(*) FROM ai_metadata_cache) as cache_ia,
                    (SELECT COUNT(*) FROM retailers WHERE active = true) as retailers_activos
            """)[0]
            return stats
        except:
            return {}
    
    def _print_validation_summary(self, report: Dict):
        """Imprimir resumen de validación"""
        print(f"\n" + "=" * 40)
        print(f"RESUMEN VALIDACION")
        print(f"=" * 40)
        
        if report['integrity_ok']:
            print("OK: SISTEMA LISTO PARA PRODUCCION")
            print("OK: Todas las validaciones pasaron")
            print("OK: Integridad garantizada")
        else:
            print("ERROR: SISTEMA NO LISTO PARA PRODUCCION")
            print("ERROR: Errores de integridad detectados")
            
        if self.errors:
            print(f"\nERRORES CRITICOS:")
            for error in self.errors:
                print(f"   - {error}")
                
        if self.warnings:
            print(f"\nADVERTENCIAS:")
            for warning in self.warnings:
                print(f"   - {warning}")
        
        stats = report.get('stats', {})
        if stats:
            print(f"\nESTADISTICAS:")
            print(f"   Productos: {stats.get('productos_activos', 0)}")
            print(f"   Precios: {stats.get('precios_totales', 0)}")
            print(f"   Cache IA: {stats.get('cache_ia', 0)}")
            print(f"   Retailers: {stats.get('retailers_activos', 0)}")

def validate_before_operation(operation_name: str = "operación") -> bool:
    """Función utilitaria para validar antes de cualquier operación"""
    validator = IntegrityValidator()
    integrity_ok, report = validator.validate_all()
    
    if not integrity_ok:
        print(f"\nERROR: OPERACION CANCELADA")
        print(f"ERROR: No se puede ejecutar '{operation_name}' con errores de integridad")
        print(f"ERROR: Corregir errores antes de continuar")
        return False
    
    print(f"\nOK: Integridad verificada, '{operation_name}' puede proceder")
    return True

if __name__ == "__main__":
    validator = IntegrityValidator()
    integrity_ok, report = validator.validate_all()
    
    if integrity_ok:
        print("\nOK: Sistema productivo verificado y listo")
    else:
        print("\nADVERTENCIA: Sistema requiere correccion antes de usar en produccion")