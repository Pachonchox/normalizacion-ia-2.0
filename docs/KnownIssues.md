Known Issues

Críticos
- Credenciales hard‑coded:
  - `src/normalize.py`: credenciales PostgreSQL embebidas (IP y password). Debe migrarse a variables de entorno o `config_manager`.
  - `src/db_persistence.py`: `get_persistence_instance()` crea un conector con IP/credenciales fijas.
- Artefactos de sintaxis (línea inicial `\`) que rompen importación/ejecución:
  - `src/cli.py`, `src/ingest.py`, `src/persistence.py`, `src/normalize.py`, `src/orchestrator.py`, `src/pipeline.py`, `src/enrich.py`, `src/fingerprint.py`, `src/cache.py`, `src/metrics.py`.
  - Corregir retirando el caracter y validando imports.

Funcionales
- Doble camino de código:
  - Conjunto `src/retail_normalizer/*` vs. módulos de nivel `src/*` con lógica solapada. Riesgo de deriva y confusión.
  - Recomendar consolidar en un único camino (preferentemente el integrado con `unified_connector`).
- Filtro acoplado a scrapers:
  - `normalize_integrated` usa `Scrappers/product_filter.py`. Mover el filtro a `src/` para desacoplar y poder testearlo.
- Unificación de precios (heurística):
  - `src/retail_normalizer/ingest.unify_prices`: usa `min(candidates)` como precio actual y `max(candidates)` como original. Ajustar a reglas por retailer/metadata para evitar falsos mapeos.
- Categorización simple sin normalizar acentos:
  - `src/retail_normalizer/categorize.py` no usa `strip_accents` y hace `in` sobre cadenas; puede generar falsos positivos/negativos con acentos.
- Inferencia de marca agresiva:
  - `src/retail_normalizer/normalize.infer_brand` cae en “primer token” si no encuentra alias; puede confundir marcas con modelos.

Calidad/Observabilidad
- `load_products` silencia errores de parsing; agregar log estructurado y contador de archivos fallidos.
- Validación post‑persistencia existe en `unified_connector`, pero falta uniformidad en todos los caminos.

Seguridad
- No commitear secretos ni IPs públicas. Centralizar en `src/config_manager.py` + `.env` (solo dev).

Rendimiento
- Batch: usar rutas batch cuando LLM está activo (prompts `BATCH` y `optimize_batch_prompts`).
- DB: índices/DDL están bien cubiertos en `src/base.sql`; validar VACUUM/ANALYZE en producción.

Acciones Recomendadas (prioridad)
1) Eliminar credenciales hard‑coded y unificar con `config_manager`.
2) Quitar artefactos `\` en módulos afectados y agregar tests de import.
3) Desacoplar filtro de `Scrappers/` y moverlo a `src/` con tests.
4) Afinar mapeo de precios por retailer y agregar validaciones.
5) Consolidar pipelines (reducir duplicación entre `src/retail_normalizer` y `src/*`).
6) Añadir logs/metricas de error en ingesta y normalización.

