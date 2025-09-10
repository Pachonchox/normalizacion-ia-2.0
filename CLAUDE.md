# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🎯 Visión General del Proyecto

**Normalización IA 2.0** es un pipeline avanzado de ingesta, categorización y normalización de productos retail para comparación de precios entre retailers. Utiliza GPT-5 (mini → full fallback) y PostgreSQL para persistencia.

## 📋 Comandos de Desarrollo Principales

### Instalación y Configuración
```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno (copiar y editar)
cp .env.example .env
```

### Comandos Core del Pipeline
```bash
# Pipeline integrado completo (recomendado)
python -m src.normalize_integrated

# Pipeline tradicional paso a paso
make normalize    # Normalización básica
make match       # Matching de productos
make profile     # Perfilado de datos

# Prueba rápida con 10 productos
PYTHONPATH=. python scripts/load_test_10.py
```

### Testing
```bash
# Ejecutar tests
pytest -q                    # Tests básicos (configurado en pytest.ini)
python test_e2e_completo.py  # Test end-to-end completo
python test_gpt5_simple.py   # Test específico GPT-5
```

### Base de Datos
```bash
# Migrar esquema
python execute_migrations_auto.py

# Auditoría de BD
python auditoria_bd_completa.py
```

## 🏗️ Arquitectura del Sistema

### Módulos Principales (src/)

**Pipeline Integrado (Recomendado)**
- `normalize_integrated.py` - Pipeline canónico: categorización → normalización → persistencia
- `unified_connector.py` - Conector unificado y seguro para PostgreSQL
- `categorize.py` - Categorización híbrida (BD + fallback JSON)

**Sistema GPT-5**
- `gpt5/router.py` - Router inteligente (gpt-5-mini → gpt-5 fallback)
- `gpt5/prompts.py` - Prompts optimizados por categoría
- `gpt5/batch_processor_db.py` - Procesamiento por lotes
- `llm_connectors.py` - Conectores LLM con validación

**Normalización Legacy (retail_normalizer/)**
- Módulos focales para normalización sin IA
- `ingest.py`, `categorize.py`, `normalize.py` - Pipeline básico
- `persistence.py` - Salida JSON (modo lite)

**Infraestructura Core**
- `cli.py` - CLI principal del sistema
- `utils.py` - Utilidades de parseo y validación
- `cache.py` - Sistema de caché JSON
- `fingerprint.py` - Identificación única de productos
- `metrics.py` - Monitoreo y métricas

### Esquema de Base de Datos
- `base.sql` - DDL completo (tablas, índices, triggers)
- `productos_maestros` - Catálogo normalizado
- `precios_actuales` - Precios actualizados por retailer
- `categorias` - Taxonomía jerárquica

## 🔧 Variables de Entorno Críticas

```bash
# IA y OpenAI
LLM_ENABLED=true                    # Activar IA (por defecto: true)
OPENAI_API_KEY=sk-proj-...         # API Key OpenAI
OPENAI_MODEL=gpt-5-mini            # Modelo por defecto

# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
DB_USER=your-user
DB_PASSWORD=your-password
DB_POOL_SIZE=5                     # Tamaño del pool de conexiones
```

## 🚀 Flujos de Trabajo Típicos

### Desarrollo Nuevo Feature
1. Usar `src/normalize_integrated.py` como punto de entrada
2. Extender prompts en `src/gpt5/prompts.py` si requiere IA
3. Tests en directorio `tests/`
4. Validar con `pytest -q`

### Debugging Pipeline
1. Activar `DEBUG=true` en `.env`
2. Revisar logs del sistema
3. Usar `python auditoria_bd_completa.py` para validar datos

### Optimización Performance
- Cache L1: `src/gpt5/cache_l1.py`
- Throttling: `src/gpt5/throttling.py` 
- Batch processing: `src/gpt5/batch_processor_db.py`

## 📂 Directorios Importantes

- `src/` - Código fuente principal
- `src/gpt5/` - Sistema GPT-5 avanzado
- `src/retail_normalizer/` - Normalización legacy sin IA
- `tests/` - Suite de testing
- `docs/` - Documentación técnica detallada
- `migrations/` - Migraciones de BD
- `schemas/` - Esquemas de validación
- `data/` - Datos de prueba

## 🎛️ Puntos de Entrada Críticos

**Para nuevas implementaciones:**
- `src.normalize_integrated.normalize_batch_integrated()` - Pipeline completo
- `src.unified_connector.get_unified_connector()` - Conexión BD
- `src.gpt5.router.GPT5Router` - Procesamiento IA

**Para análisis y debugging:**
- `src.metrics.Metrics` - Monitoreo
- `src.cache.JsonCache` - Sistema de caché
- `src.fingerprint.product_fingerprint()` - Identificación productos

## ⚡ Notas de Rendimiento

- El sistema soporta emojis nativamente en todos los módulos
- Usar `unified_connector.py` para todas las operaciones de BD
- GPT-5 router optimiza costos usando mini → full fallback
- Cache L1 reduce llamadas API redundantes
- Pool de conexiones configurado para alta concurrencia