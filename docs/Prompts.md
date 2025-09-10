Prompts

Diseño
- Objetivo: maximizar precisión con costo acotado.
- Modos (`src/gpt5/prompts.py`):
  - `MINIMAL` (~30–50 tokens): ultra‑compacto, ideal para batch en casos simples.
  - `BATCH` (~40–60 tokens): compacto con campos dirigidos por categoría.
  - `STANDARD` (~100 tokens): balance calidad/costo.
  - `DETAILED` (~200 tokens): máxima precisión para casos complejos.
  - `FALLBACK`: prompt de corrección con contexto previo.

Selección
- Router/optimizer decide por complejidad y costo (ver `src/gpt5/prompt_optimizer.py`).
- System prompts por modelo fuerzan “JSON only” y contexto retail Chile.
- Fallback chain: `gpt-5-mini` → `gpt-5` (sin uso de 4o/4o-mini en fallback).

Buenas Prácticas
- Siempre exigir JSON válido (RFC 8259) y campos clave: `brand`, `model`, `normalized_name`, `attributes`, `confidence`.
- Incluir pocos ejemplos few‑shot cuando la categoría sea ambigua (ver `create_few_shot_examples`).
- Medir tokens y costos por lote; ajustar `BATCH`/`MINIMAL` cuando la precisión sea suficiente.

Riesgos Observados
- Prompts ultra‑compactos pueden degradar la calidad en productos complejos.
- Validar salidas con `src/gpt5/validator.py` y umbrales de calidad.
