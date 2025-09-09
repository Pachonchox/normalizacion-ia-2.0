# Operación, métricas y runbooks

- Logs en `outputs/logs/{run_id}.log` (JSONL).
- Reporte final `outputs/report.json` con:
  - productos_procesados, por_categoria
  - tiempos_por_etapa_ms
  - uso_llm: mini/full, tokens y costo estimado
  - cache_hits, cache_misses
  - sugerencias_categoria
  - matches_encontrados

## Fallos comunes
- Esquema inválido: revisar `schemas/normalized_product_v1.schema.json` y errores Pydantic.
- Falta de RAM/permiso escritura: probar `--outdir ./outputs` en carpeta con permisos.
- LLM sin API key: usar `--llm=off` o definir `OPENAI_API_KEY`.
