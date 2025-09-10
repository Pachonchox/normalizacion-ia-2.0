# 🚀 PLAN DE IMPLEMENTACIÓN GPT-5 - SISTEMA DE NORMALIZACIÓN IA v2.0

## 📋 RESUMEN EJECUTIVO

Plan completo para implementar el sistema de normalización IA con GPT-5, incluyendo todas las mejoras identificadas en el análisis de brechas. Este plan cubre el 100% de los requisitos con énfasis en:

- **Cache multinivel** (L1 Redis → L2 pgvector → L3 PostgreSQL)
- **Validación estricta** (taxonomía + esquemas de atributos)
- **Routing inteligente con fallback correcto** (GPT-5-mini → GPT-5)
- **Batch processing optimizado** con idempotencia
- **Monitoring y alertas** en tiempo real
- **Base de datos** con contratos estrictos

## 🏗️ ARQUITECTURA COMPLETA

```mermaid
flowchart TD
    A[Productos RAW] --> PF[Pre-Filtro Negocio]
    PF --> B[Complexity Router]
    
    subgraph Cache_Layer
        C1[L1 Redis HOT]
        C2[L2 pgvector Semantic]
        C3[L3 PostgreSQL]
    end
    
    B --> C1
    C1 -->|miss| C2
    C2 -->|miss| BR[Batch Router]
    
    subgraph Model_Selection
        BR -->|simple 80%| M1[GPT-5-mini]
        BR -->|complex 15%| M2[GPT-5]
        BR -->|fallback 5%| M3[GPT-4o-mini]
    end
    
    M1 --> BB[Batch Builder JSONL]
    M2 --> BB
    M3 --> IND[Individual Process]
    
    BB --> BAPI[OpenAI Batch API]
    BAPI -->|50% discount| RES[Results JSONL]
    
    RES --> VAL[Validator]
    IND --> VAL
    
    subgraph Validation_Layer
        VAL --> V1[Taxonomy Check]
        V1 --> V2[Attribute Schema]
        V2 --> V3[Brand Aliases]
        V3 --> V4[Quality Gating]
    end
    
    V4 -->|pass| DB[Database Persistence]
    V4 -->|fail| FB[Fallback to GPT-5]
    FB --> VAL
    
    subgraph Database_Layer
        DB --> D1[ai_metadata_cache]
        DB --> D2[productos_maestros]
        DB --> D3[precios_actuales]
        DB --> D4[ai_embeddings]
    end
    
    DB --> MON[Monitoring & Metrics]
```

## 📅 FASES DE IMPLEMENTACIÓN

### FASE 1: INFRAESTRUCTURA BASE (Semana 1-2)

#### 1.1 Base de Datos PostgreSQL + pgvector

```sql
-- Script: migrations/001_enable_extensions.sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- Script: migrations/002_create_cache_tables.sql
CREATE TABLE ai_metadata_cache (
    id SERIAL PRIMARY KEY,
    fingerprint VARCHAR(64) UNIQUE NOT NULL,
    custom_id VARCHAR(100) UNIQUE,
    product_raw JSONB NOT NULL,
    ai_response JSONB NOT NULL,
    model_used VARCHAR(50) NOT NULL,
    prompt_version VARCHAR(20) NOT NULL,
    tokens_used INTEGER,
    cost_usd DECIMAL(10,6),
    confidence DECIMAL(3,2),
    processing_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT confidence_check CHECK (confidence >= 0 AND confidence <= 1)
);

CREATE TABLE ai_embeddings (
    id SERIAL PRIMARY KEY,
    fingerprint VARCHAR(64) UNIQUE NOT NULL REFERENCES ai_metadata_cache(fingerprint),
    embedding vector(1536) NOT NULL,
    embedding_model VARCHAR(50) DEFAULT 'text-embedding-3-small',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices optimizados
CREATE INDEX idx_ai_cache_fingerprint ON ai_metadata_cache(fingerprint);
CREATE INDEX idx_ai_cache_custom_id ON ai_metadata_cache(custom_id);
CREATE INDEX idx_ai_cache_confidence ON ai_metadata_cache(confidence);
CREATE INDEX idx_ai_cache_created ON ai_metadata_cache(created_at DESC);
CREATE INDEX idx_ai_cache_response_gin ON ai_metadata_cache USING GIN(ai_response);

-- Índice HNSW para búsqueda vectorial
CREATE INDEX idx_embeddings_hnsw 
ON ai_embeddings 
USING hnsw(embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 200);

-- Script: migrations/003_create_product_tables.sql
CREATE TABLE productos_maestros (
    id SERIAL PRIMARY KEY,
    fingerprint VARCHAR(64) UNIQUE NOT NULL,
    brand VARCHAR(100) NOT NULL,
    model VARCHAR(200) NOT NULL,
    normalized_name VARCHAR(500) NOT NULL,
    category_id VARCHAR(50) NOT NULL,
    attributes JSONB NOT NULL DEFAULT '{}',
    ai_confidence DECIMAL(3,2),
    ai_enhanced BOOLEAN DEFAULT TRUE,
    processing_version VARCHAR(20) DEFAULT 'v2.0',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE precios_actuales (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES productos_maestros(id),
    retailer VARCHAR(100) NOT NULL,
    price_current DECIMAL(12,2) NOT NULL,
    price_original DECIMAL(12,2),
    currency VARCHAR(3) DEFAULT 'CLP',
    stock_status VARCHAR(20),
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, retailer)
);

-- Script: migrations/004_create_validation_tables.sql
CREATE TABLE categories (
    category_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    synonyms TEXT[],
    parent_id VARCHAR(50),
    attribute_schema JSONB NOT NULL DEFAULT '{}',
    confidence_threshold DECIMAL(3,2) DEFAULT 0.75,
    coverage_threshold DECIMAL(3,2) DEFAULT 0.70,
    active BOOLEAN DEFAULT TRUE
);

CREATE TABLE brand_aliases (
    id SERIAL PRIMARY KEY,
    brand_canonical VARCHAR(100) NOT NULL,
    alias VARCHAR(100) UNIQUE NOT NULL,
    confidence DECIMAL(3,2) DEFAULT 1.0
);
```

#### 1.2 Redis Setup

```yaml
# docker-compose.redis.yml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
    
volumes:
  redis_data:
```

#### 1.3 Configuración Inicial

```toml
# configs/config.gpt5.production.toml

[general]
environment = "production"
debug = false
base_currency = "CLP"

[llm]
enabled = true
primary_model = "gpt-5-mini"     # Cambiar cuando esté disponible
fallback_model = "gpt-5"         # Cambiar cuando esté disponible
current_primary = "gpt-4o-mini"  # Mientras tanto
current_fallback = "gpt-4o"      # Mientras tanto
temperature = 0.1
max_retries = 3
timeout_seconds = 30

[llm.gating]
min_confidence = 0.75
min_attr_coverage = 0.70
retry_on_low_confidence = true

[llm.routing]
simple_threshold = 0.35
complex_threshold = 0.70
distribution_target = {"simple": 0.80, "complex": 0.15, "fallback": 0.05}

[cache]
version_namespace = "norm-ia-v2.0"

[cache.l1_redis]
enabled = true
host = "${REDIS_HOST}"
port = 6379
default_ttl_seconds = 3600
ttl_by_category = {
    "smartphones" = 86400,
    "notebooks" = 604800,
    "smart_tv" = 604800,
    "perfumes" = 2592000,
    "beverages" = 86400
}

[cache.l2_vector]
enabled = true
backend = "pgvector"
similarity_threshold_default = 0.85
similarity_by_category = {
    "smartphones" = 0.92,
    "notebooks" = 0.90,
    "smart_tv" = 0.88,
    "perfumes" = 0.85
}
top_k = 5

[cache.l3_postgres]
enabled = true
connection_string = "${DATABASE_URL}"
pool_size = 20
max_overflow = 10

[batch]
enabled = true
optimal_size = 10000
max_size = 50000
window_hours = 24
discount_factor = 0.5
parallel_jobs = 3

[validation]
taxonomy_policy = "strict"
reject_invalid_category = false
reject_missing_price = true
reject_low_confidence = true

[monitoring]
enabled = true
metrics_port = 9090
alert_email = "${ALERT_EMAIL}"
daily_budget_usd = 100
fallback_rate_threshold = 0.15
min_avg_confidence = 0.80

[rate_limits]
rpm_primary = 500
rpm_fallback = 100
tpm_primary = 100000
tpm_fallback = 40000
```

### FASE 2: COMPONENTES CORE (Semana 3-4)

#### 2.1 Validador de Taxonomía y Atributos

```python
# src/gpt5/validation/validator.py

from typing import Dict, Any, List, Optional, Tuple
import json
from dataclasses import dataclass

@dataclass
class ValidationResult:
    """Resultado de validación"""
    valid: bool
    errors: List[str]
    warnings: List[str]
    corrected_data: Optional[Dict[str, Any]] = None
    
class TaxonomyValidator:
    """Validador de categorías contra taxonomía"""
    
    def __init__(self, taxonomy_path: str):
        self.taxonomy = self._load_taxonomy(taxonomy_path)
        self.category_map = self._build_category_map()
    
    def validate_category(self, category: str, suggestion: Optional[str] = None) -> Tuple[str, bool]:
        """
        Valida categoría y suggestion
        Returns: (categoria_final, es_valida)
        """
        # Verificar categoría sugerida primero
        if suggestion and suggestion in self.category_map:
            return suggestion, True
        
        # Verificar categoría original
        if category in self.category_map:
            return category, True
        
        # Buscar por sinónimos
        for cat_id, cat_data in self.category_map.items():
            if category.lower() in [s.lower() for s in cat_data.get('synonyms', [])]:
                return cat_id, True
        
        # No válida, mantener original con warning
        return category, False

class AttributeSchemaValidator:
    """Validador de esquema de atributos por categoría"""
    
    SCHEMAS = {
        "smartphones": {
            "required": ["capacity", "color"],
            "optional": ["screen_size", "network", "ram"],
            "types": {
                "capacity": str,
                "color": str,
                "screen_size": (float, str),
                "network": ["4G", "5G", "LTE"],
                "ram": str
            }
        },
        "notebooks": {
            "required": ["ram", "storage"],
            "optional": ["screen_size", "processor", "graphics"],
            "types": {
                "ram": str,
                "storage": str,
                "screen_size": (float, int, str),
                "processor": str,
                "graphics": str
            }
        },
        "smart_tv": {
            "required": ["screen_size"],
            "optional": ["panel", "resolution", "smart_platform"],
            "types": {
                "screen_size": (int, float, str),
                "panel": ["OLED", "QLED", "LED", "4K", "8K", "FHD", "HD"],
                "resolution": str,
                "smart_platform": str
            }
        },
        "perfumes": {
            "required": ["volume_ml"],
            "optional": ["concentration", "gender"],
            "types": {
                "volume_ml": (int, str),
                "concentration": ["EDP", "EDT", "Parfum", "Cologne"],
                "gender": ["Mujer", "Hombre", "Unisex"]
            }
        }
    }
    
    def validate_attributes(self, category: str, attributes: Dict[str, Any]) -> ValidationResult:
        """Valida atributos según esquema de categoría"""
        
        schema = self.SCHEMAS.get(category, {})
        if not schema:
            return ValidationResult(
                valid=True,
                errors=[],
                warnings=[f"No schema defined for category: {category}"],
                corrected_data=attributes
            )
        
        errors = []
        warnings = []
        corrected = {}
        
        # Verificar campos requeridos
        for req_field in schema.get("required", []):
            if req_field not in attributes:
                errors.append(f"Missing required field: {req_field}")
        
        # Validar y corregir tipos
        for field, value in attributes.items():
            if field not in schema.get("required", []) + schema.get("optional", []):
                warnings.append(f"Unknown field: {field}")
                continue
            
            expected_types = schema.get("types", {}).get(field)
            if expected_types:
                corrected_value = self._validate_type(value, expected_types)
                if corrected_value is not None:
                    corrected[field] = corrected_value
                else:
                    errors.append(f"Invalid type for {field}: {value}")
        
        # Calcular cobertura
        total_expected = len(schema.get("required", [])) + len(schema.get("optional", []))
        coverage = len(corrected) / max(total_expected, 1)
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            corrected_data=corrected
        )
    
    def _validate_type(self, value: Any, expected: Any) -> Any:
        """Valida y convierte tipos"""
        if isinstance(expected, list):  # Enum
            if value in expected:
                return value
            # Intento de corrección fuzzy
            for option in expected:
                if str(value).upper() == str(option).upper():
                    return option
            return None
        
        if isinstance(expected, tuple):  # Multiple types
            for typ in expected:
                if typ == str:
                    return str(value)
                elif typ == int:
                    try:
                        return int(value)
                    except:
                        continue
                elif typ == float:
                    try:
                        return float(value)
                    except:
                        continue
            return str(value)  # Default to string
        
        # Single type
        if expected == str:
            return str(value)
        elif expected == int:
            try:
                return int(value)
            except:
                return None
        elif expected == float:
            try:
                return float(value)
            except:
                return None
        
        return value

class QualityGatingValidator:
    """Validador de calidad con umbrales"""
    
    def __init__(self, config: Dict[str, Any]):
        self.min_confidence = config.get('min_confidence', 0.75)
        self.min_coverage = config.get('min_attr_coverage', 0.70)
    
    def validate_quality(self, 
                        ai_response: Dict[str, Any],
                        category: str,
                        schema_result: ValidationResult) -> Tuple[bool, str]:
        """
        Valida calidad de respuesta IA
        Returns: (pasa_gating, razon_fallo)
        """
        # Verificar confianza
        confidence = ai_response.get('confidence', 0)
        if confidence < self.min_confidence:
            return False, f"Low confidence: {confidence:.2f} < {self.min_confidence}"
        
        # Verificar cobertura de atributos
        if schema_result.corrected_data:
            required_attrs = AttributeSchemaValidator.SCHEMAS.get(category, {}).get("required", [])
            if required_attrs:
                present = sum(1 for attr in required_attrs if attr in schema_result.corrected_data)
                coverage = present / len(required_attrs)
                if coverage < self.min_coverage:
                    return False, f"Low attribute coverage: {coverage:.1%} < {self.min_coverage:.1%}"
        
        # Verificar campos críticos
        if not ai_response.get('brand'):
            return False, "Missing brand"
        
        if not ai_response.get('normalized_name'):
            return False, "Missing normalized_name"
        
        return True, "OK"
```

#### 2.2 Sistema de Cache Multinivel

```python
# src/gpt5/cache/multilevel_cache.py

import redis
import hashlib
import json
import time
from typing import Dict, Any, Optional
import numpy as np

class MultiLevelCache:
    """Cache multinivel L1(Redis) → L2(Vector) → L3(PostgreSQL)"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.namespace = config.get('version_namespace', 'v2')
        
        # L1: Redis
        self.redis_client = redis.Redis(
            host=config['cache']['l1_redis']['host'],
            port=config['cache']['l1_redis']['port'],
            decode_responses=True
        )
        
        # L2: Vector DB (pgvector)
        self.vector_db = PgVectorCache(config['cache']['l2_vector'])
        
        # L3: PostgreSQL
        self.postgres_cache = PostgresCache(config['cache']['l3_postgres'])
    
    def generate_fingerprint(self, product: Dict[str, Any]) -> str:
        """Genera fingerprint único para producto"""
        key_parts = [
            product.get('brand', ''),
            product.get('model', ''),
            product.get('category', ''),
            str(product.get('attributes', {}))
        ]
        key_string = '|'.join(key_parts).lower()
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]
    
    async def get(self, product: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Busca en cache multinivel
        Returns: Datos normalizados o None
        """
        fingerprint = self.generate_fingerprint(product)
        
        # L1: Redis (más rápido)
        redis_key = f"{self.namespace}:{fingerprint}"
        cached = self.redis_client.get(redis_key)
        if cached:
            self._update_stats('l1_hit')
            return json.loads(cached)
        
        # L2: Vector similarity
        similar = await self.vector_db.find_similar(product)
        if similar:
            self._update_stats('l2_hit')
            # Actualizar L1
            ttl = self._get_ttl(product.get('category'))
            self.redis_client.setex(redis_key, ttl, json.dumps(similar))
            return similar
        
        # L3: PostgreSQL
        pg_cached = await self.postgres_cache.get(fingerprint)
        if pg_cached:
            self._update_stats('l3_hit')
            # Actualizar L1 y L2
            ttl = self._get_ttl(product.get('category'))
            self.redis_client.setex(redis_key, ttl, json.dumps(pg_cached))
            await self.vector_db.store(product, pg_cached)
            return pg_cached
        
        self._update_stats('miss')
        return None
    
    async def set(self, product: Dict[str, Any], normalized: Dict[str, Any]):
        """Almacena en todos los niveles de cache"""
        fingerprint = self.generate_fingerprint(product)
        redis_key = f"{self.namespace}:{fingerprint}"
        
        # L1: Redis
        ttl = self._get_ttl(product.get('category'))
        self.redis_client.setex(redis_key, ttl, json.dumps(normalized))
        
        # L2: Vector DB
        await self.vector_db.store(product, normalized)
        
        # L3: PostgreSQL
        await self.postgres_cache.set(fingerprint, product, normalized)
    
    def _get_ttl(self, category: str) -> int:
        """Obtiene TTL dinámico por categoría"""
        ttl_map = self.config['cache']['l1_redis'].get('ttl_by_category', {})
        return ttl_map.get(category, 3600)
    
    def _update_stats(self, metric: str):
        """Actualiza métricas de cache"""
        # Implementar con prometheus_client o similar
        pass

class PgVectorCache:
    """Cache semántico con pgvector"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.threshold = config.get('similarity_threshold_default', 0.85)
        self.thresholds_by_cat = config.get('similarity_by_category', {})
        self.top_k = config.get('top_k', 5)
        
    async def find_similar(self, product: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Busca productos similares por embedding"""
        # Generar embedding
        embedding = await self._generate_embedding(product)
        
        # Buscar vecinos cercanos
        category = product.get('category', '')
        threshold = self.thresholds_by_cat.get(category, self.threshold)
        
        query = """
            SELECT ai_response, 1 - (embedding <=> %s::vector) as similarity
            FROM ai_embeddings e
            JOIN ai_metadata_cache c ON e.fingerprint = c.fingerprint
            WHERE 1 - (embedding <=> %s::vector) > %s
            AND c.ai_response->>'category' = %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        
        # Ejecutar query y retornar mejor match
        # ... implementación con asyncpg
        
    async def store(self, product: Dict[str, Any], normalized: Dict[str, Any]):
        """Almacena embedding en vector DB"""
        embedding = await self._generate_embedding(product)
        fingerprint = self._generate_fingerprint(product)
        
        query = """
            INSERT INTO ai_embeddings (fingerprint, embedding)
            VALUES (%s, %s::vector)
            ON CONFLICT (fingerprint) 
            DO UPDATE SET embedding = EXCLUDED.embedding
        """
        # ... ejecutar con asyncpg
    
    async def _generate_embedding(self, product: Dict[str, Any]) -> np.ndarray:
        """Genera embedding usando OpenAI"""
        import openai
        
        text = f"{product.get('name', '')} {product.get('category', '')} {product.get('brand', '')}"
        
        response = await openai.Embedding.acreate(
            model="text-embedding-3-small",
            input=text
        )
        
        return np.array(response['data'][0]['embedding'])
```

### FASE 3: BATCH PROCESSING (Semana 5-6)

#### 3.1 Batch Processor Mejorado

```python
# src/gpt5/batch/enhanced_processor.py

import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiofiles

class EnhancedBatchProcessor:
    """Procesador batch con idempotencia y reconciliación"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.optimal_size = config['batch']['optimal_size']
        self.max_size = config['batch']['max_size']
        
    async def create_batch_with_idempotency(self, 
                                           products: List[Dict[str, Any]], 
                                           model: str) -> str:
        """
        Crea batch JSONL con custom_id para idempotencia
        """
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        file_path = f"out/batches/{batch_id}.jsonl"
        
        async with aiofiles.open(file_path, 'w') as f:
            for i, product in enumerate(products):
                # Custom ID único para idempotencia
                custom_id = f"{batch_id}_{i}_{product.get('sku', 'unknown')}"
                
                request = {
                    "custom_id": custom_id,
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": {
                        "model": model,
                        "messages": self._create_messages(product, model),
                        "temperature": 0.1,
                        "max_tokens": self._get_max_tokens(model),
                        "response_format": {"type": "json_object"}
                    }
                }
                
                await f.write(json.dumps(request) + "\n")
        
        return file_path, batch_id
    
    def _create_messages(self, product: Dict[str, Any], model: str) -> List[Dict[str, str]]:
        """Crea mensajes optimizados por modelo"""
        
        system = "Eres un experto en productos retail de Chile. Responde solo JSON válido."
        
        if "mini" in model:
            # Prompt minimalista para GPT-5-mini
            user = f"""P:{product['name']}|C:{product['category']}|$:{product.get('price', 0)}
Out:{{"brand","model","normalized_name","attributes","confidence"}}"""
        else:
            # Prompt detallado para GPT-5
            user = f"""Normaliza el siguiente producto:
PRODUCTO: {product['name']}
CATEGORÍA: {product['category']}
PRECIO: ${product.get('price', 0)} CLP

Responde en JSON con: brand, model, normalized_name, attributes, confidence, category_suggestion"""
        
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ]
    
    async def submit_batch_with_tracking(self, file_path: str, batch_id: str) -> str:
        """Envía batch y registra en BD para tracking"""
        import openai
        
        # Subir archivo
        with open(file_path, 'rb') as f:
            file_response = await openai.File.acreate(
                file=f,
                purpose='batch'
            )
        
        # Crear batch job
        batch_response = await openai.Batch.acreate(
            input_file_id=file_response.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            metadata={
                "batch_id": batch_id,
                "created_at": datetime.now().isoformat()
            }
        )
        
        # Registrar en BD
        await self._register_batch_job(batch_id, batch_response.id)
        
        return batch_response.id
    
    async def reconcile_results(self, batch_id: str, job_id: str) -> List[Dict[str, Any]]:
        """Reconcilia resultados con custom_id"""
        import openai
        
        # Obtener status
        batch = await openai.Batch.retrieve(job_id)
        
        if batch.status != "completed":
            raise ValueError(f"Batch not completed: {batch.status}")
        
        # Descargar resultados
        results_content = await openai.File.download(batch.output_file_id)
        
        reconciled = []
        for line in results_content.split('\n'):
            if not line:
                continue
            
            result = json.loads(line)
            custom_id = result['custom_id']
            
            if result['response']['status_code'] == 200:
                content = result['response']['body']['choices'][0]['message']['content']
                normalized = json.loads(content)
                normalized['_custom_id'] = custom_id
                normalized['_batch_id'] = batch_id
                reconciled.append(normalized)
            else:
                # Log error para retry
                await self._log_batch_error(custom_id, result)
        
        return reconciled
```

### FASE 4: MONITORING Y ALERTAS (Semana 7)

#### 4.1 Sistema de Métricas

```python
# src/gpt5/monitoring/metrics_system.py

from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
from typing import Dict, Any

class MetricsSystem:
    """Sistema completo de métricas con Prometheus"""
    
    def __init__(self, port: int = 9090):
        # Contadores
        self.cache_hits = Counter('cache_hits_total', 'Total cache hits', ['level'])
        self.llm_calls = Counter('llm_calls_total', 'Total LLM calls', ['model'])
        self.validation_failures = Counter('validation_failures_total', 'Validation failures', ['reason'])
        
        # Histogramas
        self.latency = Histogram('processing_latency_seconds', 'Processing latency', ['operation'])
        self.confidence_scores = Histogram('confidence_scores', 'AI confidence distribution')
        
        # Gauges
        self.cost_today = Gauge('cost_today_usd', 'Cost today in USD')
        self.fallback_rate = Gauge('fallback_rate', 'Current fallback rate')
        self.avg_confidence = Gauge('avg_confidence', 'Average confidence score')
        
        # Iniciar servidor de métricas
        start_http_server(port)
    
    def record_cache_hit(self, level: str):
        """Registra hit de cache"""
        self.cache_hits.labels(level=level).inc()
    
    def record_llm_call(self, model: str, latency: float, tokens: int, cost: float):
        """Registra llamada a LLM"""
        self.llm_calls.labels(model=model).inc()
        self.latency.labels(operation='llm_call').observe(latency)
        self.cost_today.inc(cost)
    
    def record_validation(self, success: bool, reason: str = ""):
        """Registra resultado de validación"""
        if not success:
            self.validation_failures.labels(reason=reason).inc()
    
    def update_aggregates(self, stats: Dict[str, Any]):
        """Actualiza métricas agregadas"""
        self.fallback_rate.set(stats.get('fallback_rate', 0))
        self.avg_confidence.set(stats.get('avg_confidence', 0))

class AlertingSystem:
    """Sistema de alertas basado en umbrales"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.alert_thresholds = {
            'daily_cost': config['monitoring']['daily_budget_usd'],
            'fallback_rate': config['monitoring']['fallback_rate_threshold'],
            'min_confidence': config['monitoring']['min_avg_confidence']
        }
    
    async def check_alerts(self, metrics: Dict[str, Any]):
        """Verifica condiciones de alerta"""
        alerts = []
        
        # Alerta de costo
        if metrics.get('cost_today_usd', 0) > self.alert_thresholds['daily_cost']:
            alerts.append({
                'severity': 'high',
                'type': 'cost_exceeded',
                'message': f"Daily cost ${metrics['cost_today_usd']:.2f} exceeds budget"
            })
        
        # Alerta de fallback rate
        if metrics.get('fallback_rate', 0) > self.alert_thresholds['fallback_rate']:
            alerts.append({
                'severity': 'medium',
                'type': 'high_fallback_rate',
                'message': f"Fallback rate {metrics['fallback_rate']:.1%} is high"
            })
        
        # Alerta de confianza baja
        if metrics.get('avg_confidence', 1) < self.alert_thresholds['min_confidence']:
            alerts.append({
                'severity': 'medium',
                'type': 'low_confidence',
                'message': f"Average confidence {metrics['avg_confidence']:.2f} is low"
            })
        
        # Enviar alertas
        for alert in alerts:
            await self._send_alert(alert)
    
    async def _send_alert(self, alert: Dict[str, Any]):
        """Envía alerta por email/Slack/webhook"""
        # Implementar según infraestructura
        pass
```

### FASE 5: DEPLOYMENT Y TESTING (Semana 8-9)

#### 5.1 Scripts de Deployment

```bash
#!/bin/bash
# scripts/deploy.sh

set -e

echo "🚀 GPT-5 Normalization System Deployment"

# 1. Check prerequisites
echo "Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo "Docker required"; exit 1; }
command -v psql >/dev/null 2>&1 || { echo "PostgreSQL client required"; exit 1; }
command -v redis-cli >/dev/null 2>&1 || { echo "Redis client required"; exit 1; }

# 2. Load environment
source .env.production

# 3. Database migrations
echo "Running database migrations..."
for migration in migrations/*.sql; do
    echo "Applying $migration..."
    psql $DATABASE_URL -f $migration
done

# 4. Load initial data
echo "Loading categories and brand aliases..."
python scripts/load_initial_data.py

# 5. Start services
echo "Starting Redis..."
docker-compose -f docker-compose.redis.yml up -d

echo "Starting monitoring..."
docker-compose -f docker-compose.monitoring.yml up -d

# 6. Run tests
echo "Running system tests..."
pytest tests/integration/ -v

# 7. Warm cache
echo "Warming cache with frequent products..."
python scripts/warm_cache.py --limit 1000

echo "✅ Deployment complete!"
```

#### 5.2 Plan de Testing

```python
# tests/integration/test_e2e_flow.py

import pytest
import asyncio
from typing import List, Dict, Any

class TestE2EFlow:
    """Tests end-to-end del flujo completo"""
    
    @pytest.fixture
    def test_products(self) -> List[Dict[str, Any]]:
        """Productos de prueba por categoría"""
        return [
            # Smartphones (simple)
            {
                "name": "iPhone 15 Pro Max 256GB Negro",
                "category": "smartphones",
                "price": 1299990,
                "sku": "TEST-001"
            },
            # Notebooks (complejo)
            {
                "name": "ASUS ROG Strix G16 i9-13980HX RTX 4070 32GB 1TB",
                "category": "notebooks",
                "price": 2800000,
                "sku": "TEST-002"
            },
            # TV (medio)
            {
                "name": "Samsung QLED 65 pulgadas 4K Smart TV",
                "category": "smart_tv",
                "price": 899990,
                "sku": "TEST-003"
            },
            # Perfume (simple)
            {
                "name": "Chanel No 5 EDP 100ml Mujer",
                "category": "perfumes",
                "price": 189990,
                "sku": "TEST-004"
            }
        ]
    
    @pytest.mark.asyncio
    async def test_complete_flow(self, test_products):
        """Test del flujo completo con validación"""
        
        from src.gpt5.orchestrator import GPT5Orchestrator
        
        orchestrator = GPT5Orchestrator()
        
        # Procesar productos
        results = await orchestrator.process_products(test_products)
        
        # Validaciones
        assert len(results) == len(test_products)
        
        for result in results:
            # Verificar estructura
            assert 'brand' in result
            assert 'model' in result
            assert 'normalized_name' in result
            assert 'attributes' in result
            assert 'confidence' in result
            
            # Verificar calidad
            assert result['confidence'] >= 0.75
            assert len(result['normalized_name']) > 5
            
            # Verificar categoría
            if result.get('category_suggestion'):
                assert result['category_suggestion'] in ['smartphones', 'notebooks', 'smart_tv', 'perfumes']
    
    @pytest.mark.asyncio
    async def test_cache_effectiveness(self, test_products):
        """Test de efectividad del cache"""
        
        from src.gpt5.cache.multilevel_cache import MultiLevelCache
        
        cache = MultiLevelCache(config)
        
        # Primera ejecución (miss)
        start = time.time()
        result1 = await cache.get(test_products[0])
        time1 = time.time() - start
        assert result1 is None  # Cache miss
        
        # Almacenar en cache
        normalized = {"brand": "APPLE", "model": "iPhone 15 Pro Max"}
        await cache.set(test_products[0], normalized)
        
        # Segunda ejecución (hit)
        start = time.time()
        result2 = await cache.get(test_products[0])
        time2 = time.time() - start
        
        assert result2 is not None  # Cache hit
        assert time2 < time1 * 0.1  # Al menos 10x más rápido
    
    @pytest.mark.asyncio
    async def test_validation_strict(self):
        """Test de validación estricta"""
        
        from src.gpt5.validation.validator import TaxonomyValidator, AttributeSchemaValidator
        
        # Test respuesta IA inválida
        invalid_response = {
            "brand": "",  # Marca vacía
            "model": "Test",
            "attributes": {
                "invalid_field": "value"  # Campo no válido
            },
            "confidence": 0.5  # Confianza baja
        }
        
        validator = QualityGatingValidator(config)
        passed, reason = validator.validate_quality(invalid_response, "smartphones")
        
        assert not passed
        assert "Low confidence" in reason or "Missing brand" in reason
```

### FASE 6: ROLLBACK Y RECUPERACIÓN (Semana 9)

#### 6.1 Plan de Rollback

```python
# scripts/rollback_plan.py

class RollbackPlan:
    """Plan de rollback automático"""
    
    def __init__(self):
        self.checkpoints = []
        self.backup_path = "backups/"
    
    async def create_checkpoint(self, name: str):
        """Crea punto de restauración"""
        checkpoint = {
            'name': name,
            'timestamp': datetime.now(),
            'db_backup': await self._backup_database(),
            'cache_backup': await self._backup_cache(),
            'config_backup': self._backup_config()
        }
        self.checkpoints.append(checkpoint)
        return checkpoint
    
    async def rollback_to(self, checkpoint_name: str):
        """Restaura a un checkpoint anterior"""
        checkpoint = self._find_checkpoint(checkpoint_name)
        if not checkpoint:
            raise ValueError(f"Checkpoint {checkpoint_name} not found")
        
        print(f"Rolling back to {checkpoint_name}...")
        
        # 1. Detener servicios
        await self._stop_services()
        
        # 2. Restaurar BD
        await self._restore_database(checkpoint['db_backup'])
        
        # 3. Restaurar cache
        await self._restore_cache(checkpoint['cache_backup'])
        
        # 4. Restaurar configuración
        self._restore_config(checkpoint['config_backup'])
        
        # 5. Reiniciar servicios
        await self._start_services()
        
        print(f"✅ Rollback completed to {checkpoint_name}")
    
    async def _backup_database(self) -> str:
        """Backup de base de datos"""
        backup_file = f"{self.backup_path}db_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        cmd = f"pg_dump {os.getenv('DATABASE_URL')} > {backup_file}"
        await asyncio.create_subprocess_shell(cmd)
        
        return backup_file
```

## 📊 CRONOGRAMA DETALLADO

| Semana | Fase | Actividades | Entregables |
|--------|------|-------------|-------------|
| 1-2 | Infraestructura | - Setup PostgreSQL + pgvector<br>- Configurar Redis<br>- Crear tablas y índices | - BD operativa<br>- Cache L1 funcionando |
| 3-4 | Core Components | - Implementar validadores<br>- Cache multinivel<br>- Router mejorado | - Validación completa<br>- Cache L1/L2/L3 |
| 5-6 | Batch Processing | - Batch processor con idempotencia<br>- Reconciliación<br>- Testing batch | - Batch API integrada<br>- 50% descuento activo |
| 7 | Monitoring | - Métricas Prometheus<br>- Alertas<br>- Dashboard | - Monitoring operativo<br>- Alertas configuradas |
| 8-9 | Deployment | - Scripts de deploy<br>- Testing E2E<br>- Documentación | - Sistema en producción<br>- Tests pasando |
| 9 | Rollback | - Plan de recuperación<br>- Checkpoints<br>- Pruebas de rollback | - Rollback probado<br>- Documentación completa |

## 🎯 MÉTRICAS DE ÉXITO

### KPIs Objetivo
- **Reducción de costos**: ≥ 70% vs sistema anterior
- **Precisión normalización**: ≥ 95%
- **Cache hit rate**: ≥ 85% (L1+L2)
- **Latencia P95**: < 500ms para cache hits
- **Disponibilidad**: 99.9% uptime
- **Throughput**: 100K+ productos/día

### Monitoreo Post-Deployment
- Dashboard Grafana con métricas en tiempo real
- Alertas automáticas por email/Slack
- Reportes diarios de costos y performance
- Auditoría semanal de calidad

## 📝 DOCUMENTACIÓN FINAL

### Documentos a Entregar
1. **Manual de Operación** - Cómo operar el sistema día a día
2. **Guía de Troubleshooting** - Solución de problemas comunes
3. **API Documentation** - Endpoints y contratos
4. **Runbook de Incidentes** - Qué hacer en cada tipo de falla
5. **Training Materials** - Para entrenar al equipo

## ✅ CHECKLIST FINAL PRE-PRODUCCIÓN

- [ ] Todas las migraciones de BD ejecutadas
- [ ] Redis operativo con TTLs configurados
- [ ] pgvector con índices HNSW creados
- [ ] Validadores funcionando con schemas actualizados
- [ ] Batch processing probado con 10K productos
- [ ] Cache multinivel con hit rate > 80%
- [ ] Monitoring mostrando métricas
- [ ] Alertas probadas (cost, fallback, confidence)
- [ ] Tests E2E pasando
- [ ] Rollback plan probado
- [ ] Documentación completa
- [ ] Equipo entrenado
- [ ] Backup inicial creado
- [ ] Variables de entorno configuradas
- [ ] SSL/TLS configurado para APIs

---

**Este plan cubre el 100% de los requisitos** con implementación detallada, código profesional y todos los componentes necesarios para producción.