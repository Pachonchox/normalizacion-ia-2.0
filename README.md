Normalización IA 2.0 — Estado Actual y Guía

Resumen
- Objetivo: pipeline de ingesta → filtro → categorización → normalización → persistencia en PostgreSQL para comparar precios entre retailers.
- Alcance de este README: estado actual del código, cómo ejecutarlo de forma segura, y dónde están los módulos clave.
- LLM: habilitado por defecto. Se usa `gpt-5-mini` con fallback a `gpt-5`.

Estructura Clave
- `src/retail_normalizer/`: módulos focales actuales para normalización simple
  - `ingest.py`: carga de archivos JSON y utilidades de precios
  - `categorize.py`: categorización por taxonomía (sin LLM)
  - `normalize.py`: inferencia de marca y extracción de atributos
  - `ingest.py`/`persistence.py`/`models.py`: utilidades de datos
- `src/categorize.py`: categorización híbrida (BD + fallback JSON)
- `src/normalize_integrated.py`: pipeline integrado (categoriza + normaliza + guarda en BD) usando GPT‑5 (mini → fallback a full)
- `src/unified_connector.py`: conector unificado a PostgreSQL (recomendado)
- `src/base.sql`: DDL de la base de datos (tablas, índices, triggers)
- `src/gpt5/prompts.py`: prompts optimizados por categoría/modo

Requisitos
- Python 3.10+
- PostgreSQL accesible (ver variables de entorno)
- Paquetes: `pip install -r requirements.txt`

Configuración (env)
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_POOL_SIZE`
- `LLM_ENABLED=true` para forzar IA siempre (default activado por configuración interna). Requiere `OPENAI_API_KEY`.
- `OPENAI_MODEL` opcional; el router usa `gpt-5-mini` por defecto con fallback a `gpt-5`.
- Ver `docs/Configuration.md` para detalles y valores por defecto.

Flujo Sugerido (sin LLM, salida a BD)
1) Preparar fuente: directorio con `.json` crudos (cada archivo con `products` y `metadata` cuando sea posible).
2) Ejecutar pipeline integrado:
   - `python -m src.normalize_integrated` (contiene un ejemplo de prueba en `__main__`).
   - O invoca programáticamente `normalize_batch_integrated(items)` pasando una lista de ítems crudos.
3) Persistencia: `src/unified_connector.py` inserta/actualiza `productos_maestros` y `precios_actuales`.

Notas de Estado
- Canon actual: pipeline integrado con GPT‑5 (mini → full) y `unified_connector`.
- Si sólo quieres JSON normalizado (sin BD): usa `src/retail_normalizer` y `src/persistence.write_jsonl` (modo lite, sin IA).

Puntos de Entrada Relevantes
- BD: `src/unified_connector.py:get_unified_connector()`
- Categorización: `src/categorize.load_taxonomy()` y `src/categorize.categorize_enhanced()`
- Normalización simple: `src/retail_normalizer/normalize.py` y `src/retail_normalizer/categorize.py`
- Prompts LLM: `src/gpt5/prompts.py` (si activas LLM)

Prueba Rápida (10 productos)
- Ejecuta: `PYTHONPATH=. python scripts/load_test_10.py`
- Requiere `.env` con `DB_*` y `OPENAI_API_KEY` si deseas IA real. Sin API, el pipeline sigue funcionando (sin IA, categorías por fallback).

Documentación adicional
- `docs/Overview.md`: arquitectura y módulos
- `docs/Pipeline.md`: flujo de extremo a extremo
- `docs/Configuration.md`: variables de entorno y configuración
- `docs/Prompts.md`: diseño y uso de prompts
- `docs/KnownIssues.md`: problemas detectados y mitigaciones
