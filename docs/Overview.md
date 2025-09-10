Overview
- Dominio: normalización de productos retail (CLP) para comparación inter‑retail.
- Pipeline: ingesta de JSON → filtro → categorización → normalización → persistencia en PostgreSQL.
- Modos: simple (sin LLM) y “integrado” (BD/LLM/caché) con ahorro de costos vía prompts y batch.

Módulos Clave
- Ingesta
  - `src/retail_normalizer/ingest.py`: carga de archivos y detección de retailer; unificación heurística de precios.
  - `src/ingest.py`: cargador genérico (nota: contiene artefacto de sintaxis; ver KnownIssues).
- Categorización
  - `src/categorize.py`: híbrido BD→JSON (obtiene categorías desde tabla `categories`; fallback a `configs/taxonomy_v1.json`).
  - `src/retail_normalizer/categorize.py`: basada en sinónimos locales.
- Normalización
  - `src/retail_normalizer/normalize.py`: inferencia de marca y extracción de atributos (smartphones, TVs, perfumes).
  - `src/normalize_integrated.py`: orquesta categorización/normalización y persiste en BD. Integra GPT‑5 con default `gpt-5-mini` y fallback a `gpt-5`.
- Persistencia a BD
  - Recomendado: `src/unified_connector.py` (pool + operaciones idempotentes; integra logs/validación).
  - Legacy: `src/db_persistence.py` (usa `SimplePostgreSQLConnector`, credenciales hard‑coded; ver KnownIssues).
- LLM y Prompts (opcional)
  - `src/gpt5/prompts.py`: prompts por categoría y modo (minimal/batch/standard/detailed/fallback).
  - `src/gpt5/prompt_optimizer.py`: compresión/plantillas por complejidad.
  - `src/gpt5/router.py`: routing y fallback mini → full (sin modelos 4o en fallback).

Esquema de Datos
- Ver `src/base.sql` (tablas principales):
  - `productos_maestros`: entidad consolidada por `fingerprint` (marca, modelo, atributos, etc.).
  - `retailers`: catálogo de retailers.
  - `precios_actuales`: precios vigentes por (fingerprint, retailer).
  - `precios_historicos`: snapshots diarios particionados.
  - `ai_metadata_cache`, `semantic_cache`, `processing_logs`, etc.

Camino Recomendado
- Carga y normalización inicial: `normalize_one_integrated`/`normalize_batch_integrated` (usa categorización híbrida y conector unificado).
- Si LLM está desactivado: funcionan las rutas de extracción de atributos sin IA.
