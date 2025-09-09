# Normalización IA 2.0 — Retail Chile

Sistema E2E para normalización de productos, enriquecimiento opcional con IA, categorización, cache y persistencia en PostgreSQL/Google Cloud SQL, con auditoría y vistas materializadas para análisis.

## Características
- Persistencia completa en PostgreSQL (tablas: productos_maestros, precios_actuales, precios_historicos, ai_metadata_cache, etc.)
- Conectores listos para PostgreSQL local y Google Cloud SQL
- IA opcional (OpenAI) con cache indefinido por fingerprint
- CLI clásico y CLI integrado con BD
- Auditoría de datos y vistas materializadas para reportes

## Requisitos
- Python >= 3.10
- PostgreSQL 13+ o Google Cloud SQL (PostgreSQL)
- `pip install -r requirements.txt`

## Configuración
- Copia `.env.example` a `.env` y completa credenciales:
  - `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_POOL_SIZE`
  - `OPENAI_API_KEY` y `LLM_ENABLED=true` si usarás IA
- Inicializa el esquema ejecutando `src/base.sql` en tu BD (psql o cliente favorito)
- Opcional Google Cloud SQL: configura `configs/config.local.toml` con una sección `[database]` como ejemplo:

```toml
[database]
project_id = "tu-proyecto"
region = "us-central1"
instance_name = "instancia-sql"
database_name = "retail_prices"
user = "postgres"
password = "${DB_PASSWORD}"
use_cloud_sql_proxy = true
```

## Uso rápido
```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

# A) CLI clásico (archivos JSON → JSONL)
python -m src.cli normalize --input ./tests/data --out ./out
python -m src.cli match --normalized ./out/normalized_products.jsonl --out ./out

# B) CLI integrado con BD (recomendado)
python -m src.cli_integrated normalize --input ./data --out ./out
python -m src.cli_integrated stats
```

Notas de configuración IA:
- Por defecto el código desactiva IA si no defines `LLM_ENABLED`; actívala en `.env`.
- El cache IA integrado usa BD; si falla, hay fallback a `out/ai_metadata_cache.json`.

## Base de datos
- Esquema completo: `src/base.sql`
  - Tablas principales: `productos_maestros`, `precios_actuales` (hot table), `precios_historicos` (particionada mensual)
  - Cache IA: `ai_metadata_cache` (indefinido, con hits/last_hit)
  - Configuración: `categories`, `brands`, `attributes_schema`, `retailers`, `system_config`
  - Auditoría/alertas: `processing_logs`, `price_alerts`
  - Vistas materializadas: `mv_comparacion_precios`, `mv_cache_metrics`

Aplicación del esquema (ejemplo):
```bash
psql postgresql://USER:PASS@HOST:PORT/DB -f src/base.sql
```

## Migración de archivos a BD
Módulo: `src/modulomigracion.py` (CLI)

Migra taxonomía, marcas, cache IA y productos normalizados (.jsonl) a la base de datos, con backup automático de archivos y validación final.

```bash
# Config desde TOML (Cloud SQL) o variables de entorno
python -m src.modulomigracion \
  --config configs/config.local.toml \
  --taxonomy configs/taxonomy_v1.json \
  --brands configs/brand_aliases.json \
  --cache out/ai_metadata_cache.json \
  --products out/products_normalized.jsonl

# Validar sin migrar
python -m src.modulomigracion --validate-only
```

Salida típica: reporte `migration_report_YYYYMMDD_HHMMSS.json` y refresco de vistas materializadas.

## Conectores de BD
- PostgreSQL local/unificado: `src/unified_connector.py` + `src/config_manager.py` (lee `.env` y usa psycopg2 con pool)
- Google Cloud SQL: `src/googlecloudsqlconnector.py` (Connector + SQLAlchemy; lectura `configs/config.local.toml`)

Funciones destacadas (Cloud SQL):
- `get_ai_cache` / `set_ai_cache` en BD (reemplaza archivos JSON)
- `upsert_price` con detección de cambios y triggers
- `detect_price_changes`, `create_alert`, `check_alerts`, `refresh_materialized_views`

## Scripts útiles
- Auditorías: `src/db_audit_simple.py`, `src/db_auditor.py`
- Persistencia BD: `src/db_persistence.py`
- Normalización integrada: `src/normalize_integrated.py`, `src/cli_integrated.py`
- Limpieza y verificación: `cleanup_obsolete_files.py`, `verify_products.py`, `verify_migration.py`
- Pipeline shell: `pipeline_completo.sh`

## Estructura de carpetas (resumen)
- `src/` código principal (CLI, normalización, BD, conectores, schema)
- `configs/` taxonomía, marcas, configuración local
- `data/` datos de scrapers (entrada)
- `out/` resultados, perfiles y cache alternativo
- `Scrappers/` orquestadores y scrapers (independientes)

## Seguridad y buenas prácticas
- Usa `.env` para credenciales (no commitees `.env`); base en `.env.example`
- Revisa `SECURITY_RECOMMENDATIONS.md`
- Evita credenciales hardcodeadas; algunos scripts legacy las incluyen para pruebas (migrarlas a `.env`)

## Documentación relacionada
- Guía completa de uso: `GUIA_COMPLETA_USO.md`
- Guía de consultas SQL: `GUIA_SQL_CONSULTAS.md`
- Pruebas e integridad: `PRUEBAS_INTEGRIDAD_REALIZADAS.md`, `README_PRUEBAS.md`

## Troubleshooting
- Verifica conexión BD y `.env`
- Ejecuta `src/db_audit_simple.py` para un estado rápido
- IA: confirma `LLM_ENABLED=true` y `OPENAI_API_KEY`
