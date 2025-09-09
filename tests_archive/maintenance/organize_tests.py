#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📁 Organizador de Tests
Mover y organizar archivos de test en estructura ordenada
"""

import os
import shutil
import glob

def organize_tests():
    print("ORGANIZACION DE ARCHIVOS TEST")
    print("=" * 40)
    
    # Crear estructura de carpetas
    test_structure = {
        'tests_archive/unit_tests': [
            # Tests unitarios específicos
        ],
        'tests_archive/integration_tests': [
            # Tests de integración con BD
            'test_bd_connection.py',
            'test_single_product.py',
            'test_30_productos_completo.py',
            'test_real_integrity_fixed.py'
        ],
        'tests_archive/performance_tests': [
            # Tests de rendimiento y carga masiva
            'insert_200_productos_masivo.py',
            'insert_200_productos_segunda_tanda.py',
            'extract_200_productos_masivo.py'
        ],
        'tests_archive/data_validation': [
            # Tests de filtros y validación
            'test_filtro_corregido.py',
            'test_filtro_integrado.py',
            'test_ia_optimized.py',
            'test_ia_quick.py',
            'test_final_optimizado.py'
        ],
        'tests_archive/legacy_tests': [
            # Tests legacy y experimentales
            'test_price_changes_simple.py',
            'test_price_mapping.py',
            'test_prices_keep_data.py',
            'test_retailer_fix.py',
            'test_simple_clean.py',
            'test_fix_retailer.py'
        ],
        'tests_archive/maintenance': [
            # Scripts de mantenimiento
            'cleanup_test_data.py',
            'limpiar_integridad_bd.py',
            'limpiar_integridad_urgente.py',
            'sincronizar_productos_sin_precios.py',
            'eliminar_directo.py'
        ],
        'tests_archive/docs': [
            # Documentación de análisis
            'analisis_causa_problemas_integridad.md',
            'informe_integridad_solucionado.md'
        ]
    }
    
    # Mover archivos a sus carpetas correspondientes
    moved_files = 0
    
    for target_dir, files in test_structure.items():
        # Crear directorio si no existe
        os.makedirs(target_dir, exist_ok=True)
        
        for file in files:
            if os.path.exists(file):
                try:
                    shutil.move(file, os.path.join(target_dir, file))
                    print(f"   OK: {file} -> {target_dir}")
                    moved_files += 1
                except Exception as e:
                    print(f"   ERROR: No se pudo mover {file} - {e}")
    
    # Mover carpetas de datos test
    test_data_dirs = [
        'test_productos_10',
        'test_productos_30', 
        'test_productos_200',
        'test_salida_bd',
        'test_sample'
    ]
    
    data_archive_dir = 'tests_archive/test_data'
    os.makedirs(data_archive_dir, exist_ok=True)
    
    for test_dir in test_data_dirs:
        if os.path.exists(test_dir):
            try:
                shutil.move(test_dir, os.path.join(data_archive_dir, test_dir))
                print(f"   OK: {test_dir} -> {data_archive_dir}")
                moved_files += 1
            except Exception as e:
                print(f"   ERROR: No se pudo mover {test_dir} - {e}")
    
    # Crear archivo README en tests_archive
    readme_content = """# 📁 Tests Archive

Esta carpeta contiene todos los archivos de test organizados por categoría.

## 📂 Estructura:

### 🔧 unit_tests/
Tests unitarios específicos de componentes individuales

### 🔗 integration_tests/
Tests de integración con base de datos y APIs
- `test_bd_connection.py` - Conexión a base de datos
- `test_single_product.py` - Inserción producto individual
- `test_30_productos_completo.py` - Test con 30 productos
- `test_real_integrity_fixed.py` - Validación integridad

### ⚡ performance_tests/
Tests de rendimiento y carga masiva
- `insert_200_productos_masivo.py` - Inserción masiva 200 productos
- `insert_200_productos_segunda_tanda.py` - Segunda tanda (duplicados)
- `extract_200_productos_masivo.py` - Extracción datos test

### 🛡️ data_validation/
Tests de filtros y validación de datos
- `test_filtro_corregido.py` - Validación filtros
- `test_ia_optimized.py` - Optimización IA
- `test_final_optimizado.py` - Test final optimizado

### 🗄️ legacy_tests/
Tests legacy y experimentales
- Tests de precios y retailers
- Experimentos antiguos

### 🧹 maintenance/
Scripts de mantenimiento y limpieza
- Scripts de limpieza BD
- Sincronización datos
- Corrección integridad

### 📊 docs/
Documentación de análisis y reportes
- Análisis de problemas
- Informes de corrección

### 💾 test_data/
Datos de test y archivos de salida
- Productos de prueba
- Resultados de test
- Archivos JSON/JSONL

## 🚀 Sistema Productivo

El sistema principal está en la raíz del proyecto, completamente limpio y listo para producción.

**Validación automática:** `src/integrity_validator.py`
"""
    
    with open('tests_archive/README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"\nOK: ORGANIZACION COMPLETADA")
    print(f"   Archivos movidos: {moved_files}")
    print(f"   Estructura creada en: tests_archive/")
    print(f"   README generado: tests_archive/README.md")
    
    # Verificar que el sistema productivo está limpio
    print(f"\nVERIFICACION SISTEMA PRODUCTIVO:")
    
    remaining_test_files = []
    for file in glob.glob("test_*.py"):
        remaining_test_files.append(file)
    
    for file in glob.glob("*test*.py"):
        if "integrity_validator" not in file:
            remaining_test_files.append(file)
    
    if remaining_test_files:
        print(f"   ADVERTENCIA: Quedan archivos test en raíz:")
        for f in remaining_test_files:
            print(f"      - {f}")
    else:
        print(f"   OK: Raíz del proyecto limpia")
    
    print(f"\nEstructura final tests_archive/:")
    for root, dirs, files in os.walk('tests_archive'):
        level = root.replace('tests_archive', '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f"{subindent}{file}")

if __name__ == "__main__":
    organize_tests()