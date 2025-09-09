# 📁 Tests Archive

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
