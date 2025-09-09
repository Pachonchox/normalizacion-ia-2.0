# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Proyecto
Pipeline E2E para **normalización, enriquecimiento, categorización, cache y matching inter-retail** (CLP). Sistema de procesamiento de datos de productos retail con soporte para múltiples retailers chilenos.

## Comandos Principales

### Desarrollo
- `make install` - Instala dependencias en entorno virtual
- `make test` - Ejecuta pytest con configuración pythonpath=src
- `pytest tests/test_categorize.py` - Ejecutar test específico
- `make clean` - Limpia archivos temporales y outputs

### Pipeline de Datos
- `make normalize` - Normaliza datos de `./tests/data` → `./out/normalized_products.jsonl`
- `make match` - Matching inter-retail usando datos normalizados
- `make profile` - Genera perfil de cobertura de campos de datos crudos
- `make evaluate` - Evalúa calidad de normalización generando reportes

### CLI Directa
```bash
python -m src.cli normalize --input ./tests/data --out ./out
python -m src.cli match --normalized ./out/normalized_products.jsonl --out ./out
python -m src.cli profile --input ./tests/data --out ./out
```

## Arquitectura

### Flujo Principal
1. **Ingest** (`src/ingest.py`) - Carga JSONs crudos desde directorio
2. **Categorize** (`src/categorize.py`) - Categorización usando taxonomía v1
3. **Normalize** (`src/normalize.py`) - Normalización de precios, marcas, atributos
4. **Match** (`src/match.py`) - Matching inter-retail por similitud semántica
5. **Persistence** (`src/persistence.py`) - Salida en formato JSONL

### Componentes Clave
- **CLI** (`src/cli.py`) - Orquestador principal con comandos normalize/match/profile
- **Models** (`src/models.py`) - Modelo Pydantic `NormalizedProduct` (schema v1)
- **Cache** (`src/cache.py`) - Cache JSON con TTL configurable
- **Enrich** (`src/enrich.py`) - Enriquecimiento de marcas y atributos
- **Metrics** (`src/metrics.py`) - Métricas de procesamiento

### Configuración
- **`configs/config.local.toml`** - Configuración principal (currency, cache, LLM, matching)
- **`configs/taxonomy_v1.json`** - Taxonomía de categorías
- **`configs/brand_aliases.json`** - Aliases de marcas para normalización
- **`schemas/normalized_product_v1.schema.json`** - JSON Schema para validación

### Estructura de Datos
- **Input**: JSONs crudos con estructura variable por retailer
- **Output**: JSONL normalizado siguiendo `NormalizedProduct` schema
- **Cache**: `out/cache.json` con TTL de 7 días por defecto
- **Matching**: Pares de productos similares con score de confianza

## Características Técnicas
- **Python 3.10+** requerido
- **Pydantic v2** para validación de esquemas
- **Sin dependencias nativas** - alta compatibilidad
- **LLMs deshabilitados** por defecto (configurable en config.local.toml)
- **Cache automático** para optimizar reprocesamiento
- **Tests unitarios** en directorio `tests/`

## Notas de Desarrollo
- Todos los outputs van a `./out/`
- Los tests de datos están en `./tests/data/`
- Configuración pytest: `pythonpath = src`
- Usar `make` para comandos comunes, CLI directa para opciones avanzadas