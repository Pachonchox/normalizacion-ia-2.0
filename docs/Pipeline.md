Pipeline

Ingesta
- Entrada: directorio con JSONs (lista de `products` + `metadata` cuando esté disponible).
- Carga:
  - Simple: `src/retail_normalizer/ingest.load_products()`.
  - Genérica: `src/ingest.load_items()` (revisar KnownIssues por artefactos de sintaxis).
- Opcional filtro de calidad: actualmente acoplado a `Scrappers/product_filter.py` (recomendado migrarlo a `src/` para reducir dependencia).

Categorización
- Híbrida (recomendada): `src/categorize.load_taxonomy()` → `categorize_enhanced()`.
  - Fuente primaria: tabla `categories` en BD.
  - Fallback: `configs/taxonomy_v1.json`.
  - Devuelve `category_id`, `confidence`, y sugerencias si la confianza es baja.
- Alternativa simple: `src/retail_normalizer/categorize.categorize()` con sinónimos locales.

Normalización
- Atributos básicos por categoría: `src/retail_normalizer/normalize.extract_attributes()`.
- Inferencia de marca: `infer_brand()` con `configs/brand_aliases.json`.
- Fingerprint: `src/fingerprint.product_fingerprint()` para matching inter‑retail.
- LLM (por defecto ON): `src/llm_connectors` y prompts definidos en `src/gpt5/prompts.py`.
  - Modelo base: `gpt-5-mini` con fallback a `gpt-5` (ver `src/gpt5/router.py`).

Persistencia en BD
- Conector recomendado: `src/unified_connector.py`.
- Inserta/actualiza:
  - `productos_maestros` (upsert por `fingerprint`).
  - `precios_actuales` (upsert por `fingerprint`, `retailer_id`).
- Integridad: verificación posterior a inserción y logging en `processing_logs`.

Históricos y Monitoreo
- `create_daily_snapshot()` en `src/base.sql` genera snapshots en `precios_historicos`.
- Índices y triggers: optimizaciones en tablas calientes (`precios_actuales`).

Ejemplo (modo integrado)
- `python -m src.normalize_integrated` para un caso de prueba.
- Programático: `normalize_batch_integrated(items)` produce y guarda en BD, respetando configuración `env`.
