# 📦 Archivos Obsoletos - Diciembre 2024

## Resumen
Este directorio contiene archivos que han sido reemplazados por la nueva implementación GPT-5 o que eran scripts temporales de limpieza/debug.

## Archivos Archivados

### 📁 scripts_limpieza/
Scripts temporales de limpieza y mantenimiento de BD que ya no son necesarios:

- **clean_direct.py** - Script temporal de limpieza directa de BD
- **clean_productos_filtrados.py** - Limpieza de productos filtrados (reemplazado por validación GPT-5)
- **clean_simple.py** - Script simple de limpieza
- **eliminar_productos_problematicos.py** - Eliminación manual de productos (ahora manejado por quality gate)
- **eliminar_simple.py** - Script simple de eliminación
- **delete_others_products.py** - Eliminación de categoría "others" (ahora manejado por taxonomía mejorada)
- **analizar_categoria_others.py** - Análisis de categoría others (obsoleto con nueva taxonomía)
- **analyze_cache_discrepancy.py** - Debug de cache (reemplazado por cache L1 Redis)
- **debug_price_discrepancy.py** - Debug de precios (ya resuelto)
- **extract_10_products.py** - Extracción de prueba
- **extract_30_productos_variados.py** - Extracción de prueba
- **fix_products_bd.py** - Fix temporal de BD
- **verificar_productos_problematicos.py** - Verificación manual (reemplazado por validator.py)

### 📁 integracion_vieja/
Archivos de la integración anterior que han sido reemplazados por el sistema GPT-5:

- **normalize_integrated.py** - Reemplazado por `normalize_gpt5.py`
- **cli_integrated.py** - Reemplazado por `gpt5/main_e2e.py`
- **data_migrator.py** - Migración de datos vieja
- **modulomigracion.py** - Módulo de migración obsoleto
- **db_audit_simple.py** - Auditoría simple de BD
- **db_auditor.py** - Auditor de BD (funcionalidad incluida en gpt5_db_connector.py)
- **integrity_validator.py** - Validación de integridad (reemplazado por gpt5/validator.py)

### 📁 retail_normalizer/
Directorio duplicado del sistema original (mantenemos src/ principal):

- Todo el contenido es duplicado del directorio src/ principal
- Se mantiene como referencia histórica

## Archivos NO Archivados (Siguen siendo necesarios)

### ✅ Sistema Core Actual
- `src/cache.py` - Cache JSON básico (usado como fallback)
- `src/categorize.py` - Categorización base
- `src/cli.py` - CLI principal
- `src/enrich.py` - Enriquecimiento de datos
- `src/fingerprint.py` - Generación de fingerprints
- `src/ingest.py` - Ingesta de datos
- `src/match.py` - Matching de productos
- `src/models.py` - Modelos Pydantic
- `src/normalize.py` - Normalización base (fallback)
- `src/persistence.py` - Persistencia JSONL
- `src/utils.py` - Utilidades generales

### ✅ Sistema GPT-5 (Nuevo)
- `src/normalize_gpt5.py` - Normalización con GPT-5
- `src/gpt5_db_connector.py` - Conector BD para GPT-5
- `src/gpt5/*.py` - Todos los componentes GPT-5

### ✅ Conectores BD
- `src/googlecloudsqlconnector.py` - Conector Google Cloud SQL
- `src/unified_connector.py` - Conector unificado
- `src/simple_db_connector.py` - Conector simple
- `src/db_persistence.py` - Persistencia en BD

### ✅ LLM Connectors
- `src/llm_connectors.py` - Conectores LLM actuales
- `src/archived/llm_connectors_*.py` - Versiones anteriores archivadas

### ✅ Scrapers (NO TOCADOS)
- Todos los archivos en `scrapers_busqueda/`
- Todos los archivos en `Scrappers/`

### ✅ Migrations
- `migrations/*.sql` - Migraciones SQL
- `migrations/*.py` - Scripts de migración

## Recomendaciones

1. **No eliminar estos archivos aún** - Mantenerlos archivados por al menos 3 meses
2. **Referencia histórica** - Útiles para entender la evolución del sistema
3. **Posible rollback** - En caso de necesitar volver a versión anterior

## Fecha de Archivo
- **Fecha**: Diciembre 2024
- **Razón**: Implementación completa del sistema GPT-5
- **Archivado por**: Sistema de mantenimiento automático