1) Veredicto rápido

Cobertura actual (muy buena, ~80%)

Routing por complejidad con distribución por modelo y batching (incluye ejemplos de prompts “minimal”, “standard” y “detailed”). ✔️

OpenAI Batch API con JSONL, custom_id para idempotency mapping y recuperación asincrónica (incluye estructura exacta de archivo de requests y resultados). ✔️

Cache semántico con embeddings y pgvector/HNSW (persistencia y búsqueda por similitud). ✔️

Análisis de costos/ROI y métricas de performance (throughput/latencia/precisión). ✔️

Checklist de producción razonable (config de pgvector, índices, monitoreo, pruebas previas, rollback). ✔️

Brechas y desalineaciones (críticas a corregir)

Modelos y fallback: el documento usa “GPT‑5‑mini / GPT‑5” y hasta un fallback a GPT‑4o‑mini (!). En tus requisitos pediste gpt‑4o‑mini como primario y gpt‑4o como fallback (o en su variante previa, GPT‑5‑mini→GPT‑5). Debe parametrizarse para evitar mezclar familias/modelos y asegurar fallback a un modelo más potente, no a uno menor. ⚠️

Validación estricta (taxonomía/esquema): no aparece un bloque explícito que valide la categoría devuelta por IA contra la taxonomía ni una validación por esquema de atributos por categoría antes de insertar en BD. Esto fue un pilar de la propuesta (calidad/consistencia). ⚠️

Cache L1 (hot) y política de TTL: el doc cubre cache semántico y persistencia con pgvector, pero no especifica un L1 in‑memory/Redis (para hits sub‑200ms) ni TTLs adaptativos por volatilidad (precios/cambios frecuentes). ⚠️

Gating de calidad: hay confidence en la salida, pero falta la política de aceptación (umbrales por categoría/campo) y la re‑invocación/fallback automática condicionada a esos umbrales (calidad de JSON, cobertura de atributos clave, etc.). ⚠️

Rate limiting proactivo / backpressure: el doc define monitoring y estados del batch, pero no deja claro el throttling proactivo (por ejemplo, token bucket por modelo) ni circuit‑breakers para contener errores 429/5xx o picos. ⚠️

Inserción en BD y contratos de datos: faltan pasos formales (y campos) de mapeo final a productos_maestros/ai_metadata_cache con idempotency keys y validaciones previas a INSERT (e.g., marca conocida/alias, atributos esperados por categoría, normalized_name consistente). ⚠️

Conclusión: Tu documento ya resuelve routing + batch + cache semántico + costos. Para llegar al 100% del plan, necesitas: (a) parametrizar modelos y corregir fallback, (b) insertar una fase formal de validación (taxonomía/esquema) y (c) completar operativa/fiabilidad (L1 cache, throttling, idempotencia e inserción BD).

2) Matriz de alineación (lo que cubre vs. lo faltante)
Requisito del plan	Estado en tu doc	Observación
Routing por complejidad	Cubre	Distribución 80/15/5 y prompts por modo. Ajustar modelos/fallback.
OpenAI Batch API	Cubre	JSONL requests/responses + custom_id ✔️.
Cache semántico	Cubre	pgvector/HNSW; falta L1‑Redis y TTLs.
Validación taxonomía/esquema	Falta	Añadir bloque de validator y reglas por categoría.
Fallback inteligente	Parcial	Fallback apunta a modelo menor en un tramo. Debe ir a modelo mayor.
Gating de calidad	Parcial	Usa confidence, falta umbrales, retry y escalado formal.
Inserción en BD	Parcial	Falta pipeline de inserción con idempotencia y contratos.
Throttling/Backpressure	Falta	Añadir rate limits por modelo y circuit breakers.
Observabilidad de costos	Cubre	Métricas y dashboard de batch.
3) Plan de cambio para cubrir el 100%
A. Modelos y fallback (parametrización y corrección)

Qué cambiar: Centralizar en config.llm.toml los modelos primary_model y fallback_model.

Opción A (tu doc actual): gpt‑5‑mini → gpt‑5.

Opción B (tu requerimiento previo): gpt‑4o‑mini → gpt‑4o.

Regla: fallback siempre a un modelo más potente (jamás a uno menor), condicionado por: JSON inválido, confidence < umbral, o atributos críticos ausentes.

Dónde reflejarlo: sección FASE DE ROUTING y Flujo de Fallback (intercambiar el “GPT‑4o‑mini legacy” por el full model y dejar rules como último recurso).

B. Validación estricta (taxonomía y esquema de atributos)

Insertar nueva fase entre “Resultados” → “Productos Normalizados”:

Taxonomy check: si category_suggestion existe, verificar contra taxonomía (ID/nombre/sinónimos). Si no es válida, conservar categoría base.

Attribute schema por categoría: whitelist de claves + tipos/conversión (e.g., screen_size numérico, volume_ml entero). Descartar claves fuera de esquema.

Gating por confianza: confidence_global y coverage (porcentaje de atributos clave extraídos) ≥ umbrales (p.ej. 0.7 y 0.8). Si no, reintentar o fallback.

Brand alias mapping: normalizar marca contra catálogo/aliases.

Resultado: JSON validado listo para insertar (o marcado para retry/review).

C. Cache inteligente multinivel

Añadir L1 (Redis): clave = fingerprint + schema_version; TTL adaptativo por categoría/volatilidad (ej. TVs 1d, perfumes 30d).

Mantener L2 (pgvector): como en el doc; añadir umbral de similitud por categoría (ej. smartphones ≥0.92; perfumes ≥0.90).

Política de adaptación: si reuso semántico, permitir ajuste de diferencias evidentes (p.ej., capacity 128GB vs 256GB) antes de validación.

Invalidación: por nueva versión de prompts/modelo o cambios estructurales (añadir namespace en la clave).

D. Batch y asincronía (end‑to‑end)

Batch builder: mantener JSONL como muestras (ok). Añadir response_format: json_object (ya está) y seed/version en system para trazabilidad.

Submit/Status: mantener ciclo de vida y monitoring; añadir reconciliación por custom_id → upsert cache/BD.

Plan B: si el batch timeout/falla, caer a procesamiento individual con throttling (tu fallback chain ya lo sugiere; reordenar para usar modelo full antes que legacy mini).

E. Inserción en BD (idempotencia y contratos)

Idempotencia: usar custom_id y/o fingerprint como llave natural en ai_metadata_cache y productos_maestros (ON CONFLICT DO UPDATE).

Contratos: Validar antes de INSERT:

brand no vacía (o “DESCONOCIDA”), category válida, normalized_name no trivial.

attributes conforme a esquema.

price_current presente y positivo.

Trazabilidad: guardar model_used, tokens, cost_usd_est, prompt_version.

F. Throttling, backpressure y retries

Rate Limits: por modelo y canal (batch vs individual) usando token bucket.

Circuit breaker: cortar envíos si tasa de error por encima de umbral.

Retry policy: exponencial con jitter y máximo por item.

G. Observabilidad y costos

Métricas: %cache_hit_l1, %cache_hit_l2, %llm_calls, %fallback_full, avg_confidence, cost_per_product, tokens_in/out.

Alertas: cost budget diario y % de fallback_full (si supera X%).

A/B de prompts: tu doc ya separa minimal vs detailed; añade banderas para experimentar por categoría.

4) Cambios concretos al documento (qué actualizar en tu MD)

Arquitectura (Mermaid)

Añadir L1 Redis antes de “Semantic Cache / pgvector”.

Insertar un bloque “Taxonomy & Schema Validator” entre “Resultados” y “Productos Normalizados”.

Modelos

Parametrizar: “Primary = gpt‑X‑mini, Fallback = gpt‑X (mismo family id)”.

Corregir flujo de fallback para que nunca degrade a un modelo menor.

FASE DE BATCH

Mantener JSONL y custom_id.

Añadir nota: “custom_id se usa como idempotency key en BD/cache”.

FASE DE RECUPERACIÓN Y CACHE

Indicar L1 Redis → L2 pgvector (con umbrales por categoría) y TTL.

Añadir “Adaptación de diferencias” cuando se reutiliza un vecino semántico.

Validación (nuevo capítulo)

Reglas de taxonomía/atributos (listas por categoría).

Umbrales de aceptación (confidence, coverage).

Inserción BD

Paso‑a‑paso: validado → upsert ai_cache → upsert productos_maestros → upsert precios.

Campos de auditoría: model_used, prompt_version, ai_confidence.

Checklist

Agregar: Redis, rate limits, circuit breakers, versionado de prompts.

5) ¿Cubre lo esencial de mi propuesta?

Sí, en gran medida. Tu BATCH_PROCESSING_FLOW.md ya resuelve las piezas más costosas y diferenciales: routing, batch API, cache semántico y medición de costos/throughput. Con los ajustes anteriores (modelos/fallback, validación estricta, L1 cache, throttling y contratos de BD) quedará totalmente alineado con el plan de Normalización IA 2.0 y listo para producción robusta.

6) Próximos pasos (prácticos)

Actualizar el doc con los cambios de secciones A–G (arriba) y el diagrama.

Parametrizar modelos en config y corregir fallback.

Implementar L1 Redis + TTL + hit counters.

Añadir “Taxonomy & Schema Validator” en el flujo post‑batch.

Definir umbrales (confidence, coverage) por categoría.

Conectar inserción BD con idempotencia (custom_id/fingerprint).

Prueba controlada con 1.000 productos (medir %cache_hit, %fallback_full, costo/producto).

Si quieres, te preparo el addendum del documento con los bloques exactos de Validación, Inserción BD y el diagrama actualizado para que tu equipo lo incorpore tal cual.

Tú dijiste:
actualiza el documento completo, sugiere los promp exactos, y los flujos, para que cumpla 100% el plan, debe ser detallado. y con todas las recomendaciones. necesito que sea profesional para que un equipo pueda seguir las indicaciones 
ChatGPT Plus
Solicitud de GPT-5 pro
Reasoned for 5m 23s

Below is the updated BATCH_PROCESSING_FLOW.md (v2) you can drop into your repo to fully cover the 100% IA plan, with exact prompts, end‑to‑end flows, validation, cache strategy, routing/fallback, batch, DB insertion and operational runbooks. It supersedes the prior document and keeps what already works (Batch API, custom_id, pgvector) while fixing gaps (taxonomy/attribute validation, L1 cache, strict gating, throttling, DB contracts). Where I reference your previous doc (v1), I cite it inline.

📦 FLUJO DE PROCESAMIENTO BATCH (IA) — Normalización E2E v2

Objetivo: Normalización 100% IA con cache inteligente multinivel, routing de modelos con fallback, Batch API, validación estricta (taxonomía + esquema de atributos) y persistencia idempotente.
Compatibilidad: mantiene Batch JSONL + custom_id e indexación vectorial (pgvector) ya definidas en v1.

🧭 Resumen Ejecutivo (qué cambia vs v1)

Model Routing parametrizable (default primary = gpt‑4o‑mini, fallback = gpt‑4o) con gating de calidad (JSON válido, confianza y cobertura de atributos).

Cache IA Multinivel: L1 Redis (hot, TTL dinámico) → L2 Semántico (pgvector/Milvus) → L3 Postgres (persistente).

Validación estricta pre‑BD: Taxonomía (ID/sinónimo válido), Esquema de atributos por categoría (tipado/whitelist), mapeo de marca por aliases, umbrales por categoría.

Batch end‑to‑end: sigue OpenAI Batch API con JSONL + custom_id (idempotencia) y reconciliación de respuestas.

Operabilidad: throttling proactivo, circuit breakers, métricas de costo/latencia/confianza, rollback plan.

⚙️ Configuración (toml / env)
[llm]
enabled = true
primary_model = "gpt-4o-mini"   # alternativo soportado: "gpt-5-mini"
fallback_model = "gpt-4o"       # alternativo soportado: "gpt-5"
temperature = 0.1
max_tokens_primary = 400
max_tokens_fallback = 800
response_format = "json_object" # estricto
timeout_seconds = 30

[llm.gating]
min_confidence = 0.70           # global mínimo aceptable
min_attr_coverage = 0.70        # % claves esperadas presentes

[llm.routing_weights]
simple = 0.80
complex = 0.20

[cache]
version_namespace = "norm-ia-v2"
l1_redis_ttl_seconds_default = 3600
l1_redis_ttl_seconds_by_category.smartphones = 86400
l1_redis_ttl_seconds_by_category.perfumes    = 2592000
l1_redis_ttl_seconds_by_category.smart_tv    = 604800
l1_redis_ttl_seconds_by_category.notebooks   = 604800

[vector]
# usar uno de ambos backends
backend = "pgvector"            # "milvus" alternativo
similarity_threshold.global = 0.90
similarity_threshold.smartphones = 0.92
similarity_threshold.perfumes = 0.90
similarity_threshold.smart_tv = 0.88
similarity_threshold.notebooks = 0.92
top_k = 3

[rate_limits]
rpm_primary = 500
rpm_fallback = 100
batch_size_optimal = 10000      # por archivo JSONL

[validation]
taxonomy_policy = "strict"      # strict|lenient|disabled
reject_if_price_missing = true


Nota: v1 ya estandariza JSONL + custom_id y Batch API; se mantiene y refuerza con idempotencia/reconciliación.

🏗️ Arquitectura (Mermaid)
flowchart TD
  A[Productos RAW] --> F[Pre‑Filtro negocio (opc)]
  F --> B[Routing Complejidad]
  subgraph Model Router
    B -->|simple| M1[primary_model (gpt-4o-mini)]
    B -->|complejo| M2[fallback_candidate (gpt-4o)]
  end

  A --> C{Cache IA L1?}
  C -->|hit| R1[Respuesta cache L1]
  C -->|miss| D{Cache IA L2 semántico?}
  D -->|hit sim>=θ| R2[Reutilización + Adaptación]
  D -->|miss| E[Batch Builder JSONL]
  E --> H[OpenAI Batch API]
  H --> I[Resultados JSONL]

  R1 --> V[Validador Taxonomía/Atributos]
  R2 --> V
  I --> V
  V -->|ok| J[Persistencia BD]
  V -->|fail| K{Fallback/Retry?}
  K -->|yes| M2
  M2 --> V

  subgraph Cache Persistente
    V --> L3[(PostgreSQL ai_metadata_cache)]
    V --> L1[(Redis HOT)]
    V --> L2[(Vector DB: pgvector/Milvus)]
  end

  J --> O[productos_maestros + precios]

🔁 Flujo E2E (paso a paso)

Ingesta & Pre‑Filtro (opcional)

Descarta reacondicionados/accesorios si tu negocio lo requiere.

Categoría inicial (from taxonomía)

Determina category_id tentativa para guiar prompts (se corregirá si IA sugiere otra válida).

Cache L1 (Redis)

Clave: {namespace}:{fingerprint}; TTL por categoría/volatilidad. Hit ⇒ saltar a validación.

Cache L2 Semántico (pgvector/Milvus)

Embedding de name_raw; busca vecinos top_k, si cosine_sim ≥ θ_cat, reutiliza metadata y adapta diferencias obvias (p. ej., capacity 128→256 si difiere solo eso).

Batch Builder JSONL (si hay N≥100–1k productos)

Agrupa por modelo (primary_model vs candidatos complejos) y categoría.

Genera JSONL (uno por modelo) con custom_id = {batch_id}_{i}_{sku|source_id}.

Submit Batch API

Sube archivos, crea job (ventana 24h), guarda batch_id, coste -50% (v1).

Polling & Download

Estados: validating → in_progress → completed; descarga *_results.jsonl. (v1)

Parsing & Reconciliación

Reconcilia por custom_id; reintenta individuales fallidos con throttling.

Validación estricta (nuevo, ver abajo)

Taxonomía, atributos por categoría, marca (aliases), gating (confianza/cobertura).

Persistencia & Cache

Upsert en ai_metadata_cache + L1 + L2; upsert productos_maestros y precios_actuales.

Métricas/Alertas

%cache_hits L1/L2, %fallback_full, cost_per_product, avg_confidence, tokens_in/out, latencias, errores por causa. (v1 ya agrega costos/throughput; aquí ampliamos)

🧪 Contratos de Datos
1) Request (por ítem) → LLM
{
  "retailer": "Falabella",
  "source_id": "SKU123",
  "name_raw": "iPhone 15 Pro Max 256GB Negro Liberado",
  "category_hint": "smartphones",
  "price_clp": 1299990
}

2) Respuesta IA (obligatorio JSON estricto)
{
  "brand": "APPLE",
  "model": "iPhone 15 Pro Max",
  "normalized_name": "APPLE iPhone 15 Pro Max 256GB Negro",
  "attributes": {
    "capacity": "256GB",
    "color": "negro",
    "screen_size": "6.7",
    "network": "5G"
  },
  "confidence": 0.93,
  "category_suggestion": "smartphones"
}


Claves mínimas requeridas (antes de BD): brand, model, normalized_name, attributes (objeto), confidence.
Observación: v1 ya enfatizaba JSON only en Batch; mantenemos response_format = json_object.

🧩 Validación estricta (previa a BD)

Taxonomía:

Si category_suggestion ≠ category_hint, aceptar solo si existe en taxonomía (ID/nombre/sinónimo). Si no, conservar category_hint (o marcar para revisión).

Esquema de atributos por categoría:

Whitelist y tipado por categoría:

smartphones: capacity(str), color(str), screen_size(num), network(enum: 4G/5G).

notebooks: screen_size(num), ram(str), storage(str/enum).

smart_tv: screen_size(num), panel(enum: OLED/QLED/4K/8K/FHD/HD).

perfumes: volume_ml(int), concentration(enum: EDP/EDT/Parfum), gender(enum: Mujer/Hombre/Unisex).

Normalizar tipos (e.g., "6.7" → 6.7), descartar claves no válidas para la categoría.

Marca (aliases):

Mapear a BRAND canónica; si desconocida, DESCONOCIDA y log de alerta.

Gating de calidad:

confidence ≥ min_confidence y attr_coverage ≥ min_attr_coverage.

Si falla: fallback al modelo superior o retry.

Precio:

Rechazar si price_current ausente/≤0 (configurable).

Nombre normalizado:

No vacío, no genérico; preferir “BRAND MODEL + atributo clave”.

Saneamiento:

Prohibidas palabras de descarte (“reacondicionado”) tras pre‑filtro; limpiar HTML/emoji si aplicara.

🧠 Routing de modelos + Fallback

Heurística de complejidad (score 0–1): longitud del nombre, tecnicismos detectados, categoría, rareza de marca, presencia de múltiples specs.

score < 0.3 ⇒ primary_model (p.ej., gpt‑4o‑mini).

0.3 ≤ score < 0.7 ⇒ primary_model + gating.

score ≥ 0.7 ⇒ fallback_model (p.ej., gpt‑4o).

Fallback automático si:

Respuesta no es JSON válido,

confidence < umbral,

Faltan atributos esenciales por categoría,

Categoría sugerida inválida.

En v1 el “fallback chain” mezclaba modelos; aquí aseguramos siempre subir a un modelo más potente.

🧾 Prompts EXACTOS (System/User) — por categoría y modo

Reglas comunes

System (constante): “Eres un experto en productos retail de Chile. Responde solo JSON válido (RFC 8259), sin texto extra.”

response_format: json_object

temperature: 0.1 (0.05 en fallback)

Idioma de salida: valores normalizados (marca mayúsculas, enums definidos).

A) Smartphones

STANDARD (primary_model)

[system]
Eres un experto en productos retail de Chile. Responde solo JSON válido (RFC 8259), sin texto extra.

[user]
Normaliza el siguiente producto para comparación inter-retail:

PRODUCTO: "{name_raw}"
CATEGORÍA: "smartphones"
PRECIO_CLP: {price_clp}
RETAILER: "{retailer}"

Estructura EXACTA:
{
  "brand": "MARCA EN MAYÚSCULAS (ej: APPLE, SAMSUNG, XIAOMI)",
  "model": "modelo específico sin la marca",
  "normalized_name": "nombre limpio y consistente",
  "attributes": {
    "capacity": "ej: 128GB, 256GB, 1TB",
    "color": "ej: negro, blanco, azul",
    "screen_size": "ej: 6.7",
    "network": "4G o 5G"
  },
  "confidence": 0.0,
  "category_suggestion": "smartphones o vacío si coincide"
}
Solo JSON.


MINIMAL (batch ultra‑compacto)

[system]
Eres experto retail CL. Solo JSON válido.

[user]
P:{name_raw}|C:smartphones|$:${price_clp}
Out:{"brand","model","normalized_name","attributes":{"capacity","color","screen_size","network"},"confidence","category_suggestion"}


FALLBACK (fallback_model, más tokens, temperatura 0.05)

[system]
Experto retail CL. Responde SOLO JSON válido.

[user]
Corrige y completa normalización (JSON). Si datos faltantes, infiere con cautela.
PRODUCTO: "{name_raw}"
CATEGORÍA_REFERENCIA: "smartphones"
PRECIO_CLP: {price_clp}
RETAILER: "{retailer}"

Estructura EXACTA y tipos correctos:
{ ... (misma estructura que STANDARD) ... }

B) Notebooks

STANDARD

[system] (igual)

[user]
Normaliza:

PRODUCTO: "{name_raw}"
CATEGORÍA: "notebooks"
PRECIO_CLP: {price_clp}
RETAILER: "{retailer}"

JSON EXACTO:
{
  "brand": "MAYÚSCULAS",
  "model": "modelo sin marca",
  "normalized_name": "BRAND MODEL + specs clave",
  "attributes": {
    "screen_size": "ej: 16",
    "ram": "ej: 16GB",
    "storage": "ej: 512GB SSD"
  },
  "confidence": 0.0,
  "category_suggestion": "notebooks|notebooks_premium|vacío"
}
Solo JSON.


MINIMAL (batch)

[system] (igual)
[user]
P:{name_raw}|C:notebooks|$:${price_clp}
Out:{"brand","model","normalized_name","attributes":{"screen_size","ram","storage"},"confidence","category_suggestion"}

C) Smart TV

STANDARD

[system] (igual)
[user]
Normaliza:

PRODUCTO: "{name_raw}"
CATEGORÍA: "smart_tv"
PRECIO_CLP: {price_clp}
RETAILER: "{retailer}"

JSON EXACTO:
{
  "brand": "MAYÚSCULAS",
  "model": "modelo sin marca",
  "normalized_name": "BRAND MODEL tamaño + panel",
  "attributes": {
    "screen_size": "ej: 55",
    "panel": "OLED|QLED|4K|8K|FHD|HD"
  },
  "confidence": 0.0,
  "category_suggestion": "smart_tv|vacío"
}
Solo JSON.

D) Perfumes

STANDARD

[system] (igual)
[user]
Normaliza:

PRODUCTO: "{name_raw}"
CATEGORÍA: "perfumes"
PRECIO_CLP: {price_clp}
RETAILER: "{retailer}"

JSON EXACTO:
{
  "brand": "MAYÚSCULAS",
  "model": "línea/fragancia sin marca",
  "normalized_name": "BRAND FRAGANCIA volumen + tipo",
  "attributes": {
    "volume_ml": 0,
    "concentration": "EDP|EDT|Parfum",
    "gender": "Mujer|Hombre|Unisex"
  },
  "confidence": 0.0,
  "category_suggestion": "perfumes|vacío"
}
Solo JSON.

📦 Batch API — Construcción y Envío

Archivo JSONL (por modelo):

{"custom_id":"b20250910_00001_FAL-SKU123","method":"POST","url":"/v1/chat/completions","body":{"model":"gpt-4o-mini","messages":[{"role":"system","content":"Eres experto retail CL. Solo JSON válido."},{"role":"user","content":"P:iPhone 15 Pro Max 256GB Negro|C:smartphones|$:1299990\nOut:{\"brand\",\"model\",\"normalized_name\",\"attributes\":{\"capacity\",\"color\",\"screen_size\",\"network\"},\"confidence\",\"category_suggestion\"}"}],"temperature":0.1,"max_tokens":300,"response_format":{"type":"json_object"}}}


Ciclo de vida: upload → create batch (24h) → poll → download *_results.jsonl → reconcilia por custom_id.
Costo: Batch ‑50% vs individual (según v1).

🧠 Cache Inteligente (L1/L2/L3)

L1 (Redis hot): clave {ns}:{fingerprint} → JSON IA; TTL por categoría; hit <200ms.

L2 (Semántico): embeddings (OpenAI text-embedding-3-small u otro) en pgvector (o Milvus). Índice HNSW/IVFFlat.

Umbral por categoría (similarity_threshold.*); si sim ≥ θ, reutiliza y adapta diferencias simples (capacidad, color).

L3 (PostgreSQL): ai_metadata_cache (persistente) con custom_id/fingerprint, model_used, prompt_version, ai_confidence, metadata (JSONB).

Invalidación: version_namespace en clave; bump al cambiar prompts/modelos/esquemas.

🧱 Persistencia (idempotente)

Orden

ai_metadata_cache UPSERT (por fingerprint o custom_id).

Vector DB UPSERT (embedding de name_raw/normalized_name).

productos_maestros UPSERT (fingerprint único), campos: brand, model, normalized_name, category, attributes, ai_enhanced=true, ai_confidence, processing_version="v2".

precios_actuales UPSERT por product_id con price_current, currency="CLP".

Índices recomendados

pgvector: CREATE INDEX idx_vec_name ON ai_embeddings USING hnsw(embedding vector_cosine_ops) WITH (m=16, ef_construction=64);

JSONB: GIN sobre ai_metadata_cache(metadata) para queries analíticas.

🧯 Throttling, Retries y Resiliencia

Rate limits: token‑bucket por modelo (rpm_primary, rpm_fallback).

Circuit breakers: si %429/%5xx supera umbral (p.ej., 3% en 5 min), pausar envíos y degradar a cache/individual.

Retries: exponencial con jitter (p.ej., 1s, 2s, 4s, máx 3 intentos por ítem).

Plan B: si batch falla/timeout, reintentar individuales con primary; si gating falla, fallback.

📊 Observabilidad

Métricas clave

%cache_hit_l1, %cache_hit_l2, %llm_invocations, %fallback_full

avg_confidence, attr_coverage, precision_sampled

tokens_in/out, cost_usd_total, cost_per_product

latency_cache_hit, latency_llm, latency_batch_end2end

Alertas

Budget diario (p.ej., $50)

Fallback rate > umbral (p.ej., 12%)

Confidence avg < 0.8 por categoría

A/B de prompts

Bandera prompt_version en system y en cache; comparar costo/precisión por versión.

v1 ya detallaba KPIs de batch y ahorro; v2 incorpora gating/validación métricas.

✅ Checklists de Producción

 OPENAI_API_KEY y modelos en config (primary_model, fallback_model)

 Redis operativo + TTL por categoría

 pgvector (o Milvus) con índices y umbrales configurados

 Taxonomía cargada y attribute schema por categoría (whitelist + tipos)

 Gating (umbrales) y fallback activados

 Idempotencia por custom_id y fingerprint en BD y cache

 Dashboards de métricas/costos/errores

 Prueba piloto (1.000 ítems) y rollback plan

 Versionado de prompts (prompt_version) y namespace de cache

🗂️ Qué debes sustituir / agregar (paso a paso)

Reemplazar BATCH_PROCESSING_FLOW.md por este v2. (Este archivo)

Configurar config.llm.toml (bloques llm, validation, vector, cache, rate_limits).

Prompts

Crear prompts/ con sub‑carpetas por categoría y archivos: standard.md, minimal.md, fallback.md (usar textos exactos arriba).

Añadir prompt_version para trazabilidad.

Cache

Desplegar Redis (L1), definir TTLs por categoría.

Montar pgvector/Milvus (L2); crear índice; implementar upsert embedding.

Validador

Añadir módulo validator/ con:

taxonomy_validator.py (check ID/sinónimo)

attributes_schema.py (whitelist/tipado por categoría)

brand_aliases.py (mapping)

gating.py (confidence + coverage)

Persistencia

Asegurar UPSERTs (ai_metadata_cache, productos_maestros, precios_actuales) con custom_id/fingerprint.

Throttling/Resiliencia

Implementar token‑bucket y circuit breakers en el submitter (batch/individual).

Métricas

Exponer contadores (%cache_hit_l1/l2, %fallback_full, costs, latencies).

📚 Apéndice A — JSON Schema (salida IA)

Úsalo para validar respuestas antes de BD (ej. jsonschema).

{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "IA Normalized Product v2",
  "type": "object",
  "required": ["brand","model","normalized_name","attributes","confidence"],
  "properties": {
    "brand": { "type": "string", "minLength": 1 },
    "model": { "type": "string", "minLength": 1 },
    "normalized_name": { "type": "string", "minLength": 5 },
    "attributes": { "type": "object", "additionalProperties": true },
    "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
    "category_suggestion": { "type": "string" }
  },
  "additionalProperties": false
}

📚 Apéndice B — SQL (pgvector & JSONB)
-- Extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabla de embeddings (si separada)
CREATE TABLE IF NOT EXISTS ai_embeddings (
  fingerprint TEXT PRIMARY KEY,
  embedding vector(1536),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Índice HNSW
CREATE INDEX IF NOT EXISTS idx_ai_embeddings_hnsw
ON ai_embeddings USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- GIN sobre metadata JSONB (consultas analíticas)
CREATE INDEX IF NOT EXISTS idx_ai_cache_metadata_gin
ON ai_metadata_cache USING GIN ((metadata));

📚 Apéndice C — Redis keys & TTL

Key: {version_namespace}:{fingerprint}

Value: JSON IA completo (brand, model, normalized_name, attributes, confidence, category_suggestion, model_used, prompt_version).

TTL: por categoría (config) + ajuste si detectas mayor volatilidad (e.g., TVs en campañas → TTL más corto).

🧭 Notas de alineación con v1

Se mantiene Batch API + JSONL con custom_id para idempotency mapping y descarga de resultados (tu v1 ya lo detalla).
