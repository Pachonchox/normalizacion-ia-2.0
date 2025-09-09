# retail-normalizer

Pipeline E2E para **normalización, enriquecimiento, categorización, cache y matching inter-retail** (CLP). Optimizado para pruebas locales.

## Requisitos
- Python >= 3.10
- `pip install -r requirements.txt`

## Uso rápido
```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

# Normaliza y categoriza todos los JSON de ./tests/data
python -m src.cli normalize --input ./tests/data --out ./out

# Matching inter-retail con el archivo normalizado
python -m src.cli match --normalized ./out/normalized_products.jsonl --out ./out
```

## Config
Edita `configs/config.local.toml` para umbrales, TTL y LLM gating.

## Esquema
`schemas/normalized_product_v1.schema.json` y `src/models.py` (Pydantic).

## Notas
- LLMs deshabilitados por defecto.
- Cache en `out/cache.json` (TTL configurable).
- Sin dependencias nativas: compatibilidad alta.
