-- 🚀 MIGRACIÓN GPT-5: Esquema Inicial
-- Fecha: 2025-09-10
-- Descripción: Creación de nuevas tablas para soporte GPT-5 con batch processing
-- ============================================================================

-- Verificar que estamos en la BD correcta
\c postgres;

-- ============================================================================
-- 1️⃣ EXTENSIONES REQUERIDAS
-- ============================================================================

-- Habilitar extensión para vectores (embeddings)
CREATE EXTENSION IF NOT EXISTS vector;

-- Habilitar UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 2️⃣ NUEVAS TABLAS PARA GPT-5
-- ============================================================================

-- Tabla: Configuración de Modelos
DROP TABLE IF EXISTS model_config CASCADE;
CREATE TABLE model_config (
    model_name VARCHAR(50) PRIMARY KEY,
    family VARCHAR(50) NOT NULL,
    cost_per_1k_input NUMERIC(10,6) NOT NULL,
    cost_per_1k_output NUMERIC(10,6) NOT NULL,
    batch_discount NUMERIC(3,2) DEFAULT 0.50,
    max_tokens INTEGER NOT NULL,
    timeout_ms INTEGER DEFAULT 30000,
    fallback_model VARCHAR(50),
    complexity_threshold_min NUMERIC(3,2) DEFAULT 0.0,
    complexity_threshold_max NUMERIC(3,2) DEFAULT 1.0,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Comentarios de documentación
COMMENT ON TABLE model_config IS 'Configuración de modelos GPT disponibles y sus costos';
COMMENT ON COLUMN model_config.batch_discount IS 'Descuento aplicado en modo batch (0.50 = 50% descuento)';

-- Datos iniciales de configuración
INSERT INTO model_config 
(model_name, family, cost_per_1k_input, cost_per_1k_output, batch_discount, max_tokens, timeout_ms, fallback_model, complexity_threshold_min, complexity_threshold_max) 
VALUES
('gpt-5-mini', 'gpt-5', 0.0003, 0.0012, 0.50, 16384, 30000, 'gpt-5', 0.0, 0.35),
('gpt-5', 'gpt-5', 0.0030, 0.0120, 0.50, 32768, 60000, 'gpt-4o-mini', 0.35, 0.75),
('gpt-4o-mini', 'gpt-4o', 0.00015, 0.0006, 0.50, 128000, 30000, null, 0.75, 1.0),
('gpt-4o', 'gpt-4o', 0.0025, 0.0100, 0.50, 128000, 60000, null, 0.0, 1.0);

-- ============================================================================

-- Tabla: Trabajos de Batch Processing
DROP TABLE IF EXISTS gpt5_batch_jobs CASCADE;
CREATE TABLE gpt5_batch_jobs (
    batch_id VARCHAR(100) PRIMARY KEY DEFAULT ('batch_' || uuid_generate_v4()::text),
    model VARCHAR(50) NOT NULL REFERENCES model_config(model_name),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    total_products INTEGER NOT NULL,
    processed_products INTEGER DEFAULT 0,
    successful_products INTEGER DEFAULT 0,
    failed_products INTEGER DEFAULT 0,
    estimated_cost NUMERIC(10,4),
    actual_cost NUMERIC(10,4),
    tokens_used_input INTEGER DEFAULT 0,
    tokens_used_output INTEGER DEFAULT 0,
    file_path VARCHAR(500),
    output_file_path VARCHAR(500),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT valid_status CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled'))
);

-- Índices para batch jobs
CREATE INDEX idx_batch_jobs_status ON gpt5_batch_jobs(status);
CREATE INDEX idx_batch_jobs_created ON gpt5_batch_jobs(created_at DESC);
CREATE INDEX idx_batch_jobs_model ON gpt5_batch_jobs(model);

COMMENT ON TABLE gpt5_batch_jobs IS 'Registro de trabajos batch para procesamiento masivo con GPT-5';

-- ============================================================================

-- Tabla: Cache de Complejidad de Productos
DROP TABLE IF EXISTS product_complexity_cache CASCADE;
CREATE TABLE product_complexity_cache (
    fingerprint VARCHAR(64) PRIMARY KEY,
    complexity_score NUMERIC(3,2) NOT NULL CHECK (complexity_score >= 0 AND complexity_score <= 1),
    model_assigned VARCHAR(50) NOT NULL REFERENCES model_config(model_name),
    routing_reason VARCHAR(200),
    category_weight NUMERIC(3,2) DEFAULT 0.0,
    name_length_weight NUMERIC(3,2) DEFAULT 0.0,
    price_weight NUMERIC(3,2) DEFAULT 0.0,
    attributes_weight NUMERIC(3,2) DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices
CREATE INDEX idx_complexity_score ON product_complexity_cache(complexity_score);
CREATE INDEX idx_complexity_model ON product_complexity_cache(model_assigned);

COMMENT ON TABLE product_complexity_cache IS 'Cache de análisis de complejidad para routing inteligente';

-- ============================================================================

-- Tabla: Cache Semántico con Embeddings
DROP TABLE IF EXISTS semantic_cache CASCADE;
CREATE TABLE semantic_cache (
    id SERIAL PRIMARY KEY,
    fingerprint VARCHAR(64) NOT NULL,
    embedding vector(1536) NOT NULL,
    product_data JSONB NOT NULL,
    normalized_data JSONB NOT NULL,
    model_used VARCHAR(50) REFERENCES model_config(model_name),
    similarity_threshold NUMERIC(3,2) DEFAULT 0.85,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    ttl_hours INTEGER DEFAULT 168 -- 7 días por defecto
);

-- Índice HNSW para búsqueda vectorial eficiente
CREATE INDEX idx_semantic_embedding ON semantic_cache 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Índices adicionales
CREATE INDEX idx_semantic_fingerprint ON semantic_cache(fingerprint);
CREATE INDEX idx_semantic_accessed ON semantic_cache(last_accessed DESC);

COMMENT ON TABLE semantic_cache IS 'Cache semántico con embeddings para búsqueda por similitud';

-- ============================================================================

-- Tabla: Métricas de Procesamiento
DROP TABLE IF EXISTS processing_metrics CASCADE;
CREATE TABLE processing_metrics (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(100) DEFAULT uuid_generate_v4()::text,
    model VARCHAR(50) NOT NULL,
    request_type VARCHAR(50) NOT NULL,
    tokens_input INTEGER NOT NULL DEFAULT 0,
    tokens_output INTEGER NOT NULL DEFAULT 0,
    cost_usd NUMERIC(10,6) NOT NULL DEFAULT 0,
    latency_ms INTEGER,
    cache_hit BOOLEAN DEFAULT FALSE,
    cache_type VARCHAR(50), -- 'exact', 'semantic', 'none'
    complexity_score NUMERIC(3,2),
    batch_id VARCHAR(100) REFERENCES gpt5_batch_jobs(batch_id),
    success BOOLEAN DEFAULT TRUE,
    error_type VARCHAR(100),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fingerprint VARCHAR(64),
    retailer VARCHAR(50),
    category VARCHAR(50),
    CONSTRAINT valid_request_type CHECK (request_type IN ('single', 'batch', 'fallback', 'retry'))
);

-- Índices para métricas
CREATE INDEX idx_metrics_created ON processing_metrics(created_at DESC);
CREATE INDEX idx_metrics_model ON processing_metrics(model);
CREATE INDEX idx_metrics_success ON processing_metrics(success);
CREATE INDEX idx_metrics_batch ON processing_metrics(batch_id) WHERE batch_id IS NOT NULL;
CREATE INDEX idx_metrics_cache ON processing_metrics(cache_hit) WHERE cache_hit = TRUE;

COMMENT ON TABLE processing_metrics IS 'Métricas detalladas de cada request a modelos GPT';

-- ============================================================================

-- Tabla: Cola de Procesamiento (para gestión de prioridades)
DROP TABLE IF EXISTS processing_queue CASCADE;
CREATE TABLE processing_queue (
    id SERIAL PRIMARY KEY,
    fingerprint VARCHAR(64) NOT NULL,
    product_data JSONB NOT NULL,
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    status VARCHAR(50) DEFAULT 'pending',
    assigned_model VARCHAR(50),
    batch_id VARCHAR(100),
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    CONSTRAINT valid_queue_status CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'skipped'))
);

-- Índices para cola
CREATE INDEX idx_queue_status_priority ON processing_queue(status, priority DESC) WHERE status = 'pending';
CREATE INDEX idx_queue_batch ON processing_queue(batch_id) WHERE batch_id IS NOT NULL;

COMMENT ON TABLE processing_queue IS 'Cola de procesamiento con gestión de prioridades';

-- ============================================================================

-- Tabla: Embeddings de Categorías (para mejorar routing)
DROP TABLE IF EXISTS category_embeddings CASCADE;
CREATE TABLE category_embeddings (
    category_id VARCHAR(50) PRIMARY KEY,
    category_name VARCHAR(200) NOT NULL,
    embedding vector(1536) NOT NULL,
    sample_count INTEGER DEFAULT 0,
    avg_complexity NUMERIC(3,2),
    typical_attributes JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índice vectorial
CREATE INDEX idx_category_embedding ON category_embeddings 
USING hnsw (embedding vector_cosine_ops);

COMMENT ON TABLE category_embeddings IS 'Embeddings de categorías para routing mejorado';

-- ============================================================================
-- 3️⃣ FUNCIONES AUXILIARES
-- ============================================================================

-- Función: Calcular costo estimado
CREATE OR REPLACE FUNCTION calculate_estimated_cost(
    p_model VARCHAR(50),
    p_tokens_input INTEGER,
    p_tokens_output INTEGER,
    p_is_batch BOOLEAN DEFAULT FALSE
) RETURNS NUMERIC AS $$
DECLARE
    v_cost_input NUMERIC;
    v_cost_output NUMERIC;
    v_discount NUMERIC;
    v_total_cost NUMERIC;
BEGIN
    SELECT 
        cost_per_1k_input,
        cost_per_1k_output,
        CASE WHEN p_is_batch THEN batch_discount ELSE 1.0 END
    INTO v_cost_input, v_cost_output, v_discount
    FROM model_config
    WHERE model_name = p_model AND active = TRUE;
    
    IF v_cost_input IS NULL THEN
        RAISE EXCEPTION 'Model % not found or inactive', p_model;
    END IF;
    
    v_total_cost := ((p_tokens_input::NUMERIC / 1000.0 * v_cost_input) + 
                     (p_tokens_output::NUMERIC / 1000.0 * v_cost_output)) * v_discount;
    
    RETURN v_total_cost;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================

-- Función: Obtener modelo por complejidad
CREATE OR REPLACE FUNCTION get_model_by_complexity(
    p_complexity NUMERIC
) RETURNS VARCHAR AS $$
DECLARE
    v_model VARCHAR(50);
BEGIN
    SELECT model_name INTO v_model
    FROM model_config
    WHERE active = TRUE
      AND p_complexity >= complexity_threshold_min
      AND p_complexity < complexity_threshold_max
    ORDER BY cost_per_1k_input ASC
    LIMIT 1;
    
    RETURN COALESCE(v_model, 'gpt-4o-mini'); -- Fallback por defecto
END;
$$ LANGUAGE plpgsql;

-- ============================================================================

-- Función: Limpiar cache antiguo
CREATE OR REPLACE FUNCTION cleanup_old_cache() RETURNS INTEGER AS $$
DECLARE
    v_deleted INTEGER;
BEGIN
    -- Eliminar semantic_cache antiguo
    DELETE FROM semantic_cache
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 hour' * ttl_hours
      AND access_count < 5;
    
    GET DIAGNOSTICS v_deleted = ROW_COUNT;
    
    -- Eliminar métricas antiguas (>90 días)
    DELETE FROM processing_metrics
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '90 days';
    
    RETURN v_deleted;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 4️⃣ TRIGGERS
-- ============================================================================

-- Trigger: Actualizar timestamp en update
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_model_config_updated_at 
    BEFORE UPDATE ON model_config
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_complexity_cache_updated_at 
    BEFORE UPDATE ON product_complexity_cache
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 5️⃣ VISTAS MATERIALIZADAS
-- ============================================================================

-- Vista: Productos por Complejidad
DROP MATERIALIZED VIEW IF EXISTS mv_products_by_complexity CASCADE;
CREATE MATERIALIZED VIEW mv_products_by_complexity AS
SELECT 
    pm.categoria_id,
    c.name as category_name,
    COUNT(DISTINCT pm.id) as total_products,
    COUNT(DISTINCT pcc.fingerprint) as analyzed_products,
    AVG(pcc.complexity_score) as avg_complexity,
    MIN(pcc.complexity_score) as min_complexity,
    MAX(pcc.complexity_score) as max_complexity,
    SUM(CASE WHEN pcc.model_assigned = 'gpt-5-mini' THEN 1 ELSE 0 END) as gpt5_mini_count,
    SUM(CASE WHEN pcc.model_assigned = 'gpt-5' THEN 1 ELSE 0 END) as gpt5_count,
    SUM(CASE WHEN pcc.model_assigned = 'gpt-4o-mini' THEN 1 ELSE 0 END) as gpt4o_mini_count,
    CURRENT_TIMESTAMP as last_refresh
FROM productos_maestros pm
LEFT JOIN categories c ON pm.categoria_id = c.category_id
LEFT JOIN product_complexity_cache pcc ON pm.fingerprint = pcc.fingerprint
GROUP BY pm.categoria_id, c.name;

-- Índice para la vista
CREATE UNIQUE INDEX idx_mv_complexity_category ON mv_products_by_complexity(categoria_id);

-- ============================================================================

-- Vista: Métricas de Costo Diarias
DROP MATERIALIZED VIEW IF EXISTS mv_daily_cost_metrics CASCADE;
CREATE MATERIALIZED VIEW mv_daily_cost_metrics AS
SELECT 
    DATE(created_at) as date,
    model,
    request_type,
    COUNT(*) as total_requests,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_requests,
    SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed_requests,
    SUM(tokens_input) as total_input_tokens,
    SUM(tokens_output) as total_output_tokens,
    SUM(cost_usd) as total_cost_usd,
    AVG(cost_usd) as avg_cost_per_request,
    AVG(latency_ms) as avg_latency_ms,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY latency_ms) as median_latency_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency_ms,
    SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END)::FLOAT / NULLIF(COUNT(*), 0) as cache_hit_rate,
    AVG(complexity_score) as avg_complexity,
    CURRENT_TIMESTAMP as last_refresh
FROM processing_metrics
GROUP BY DATE(created_at), model, request_type;

-- Índice para la vista
CREATE UNIQUE INDEX idx_mv_cost_date_model ON mv_daily_cost_metrics(date, model, request_type);

-- ============================================================================
-- 6️⃣ PERMISOS Y SEGURIDAD
-- ============================================================================

-- Crear rol de aplicación si no existe
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_gpt5') THEN
        CREATE ROLE app_gpt5 WITH LOGIN PASSWORD 'secure_password_here';
    END IF;
END $$;

-- Otorgar permisos
GRANT USAGE ON SCHEMA public TO app_gpt5;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO app_gpt5;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_gpt5;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO app_gpt5;

-- ============================================================================
-- 7️⃣ JOBS PROGRAMADOS (con pg_cron si está disponible)
-- ============================================================================

-- Intentar crear job de limpieza (requiere pg_cron)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_cron') THEN
        PERFORM cron.schedule('cleanup-old-cache', '0 2 * * *', 'SELECT cleanup_old_cache();');
        PERFORM cron.schedule('refresh-materialized-views', '0 */6 * * *', 
            'REFRESH MATERIALIZED VIEW CONCURRENTLY mv_products_by_complexity; 
             REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_cost_metrics;');
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'pg_cron not available, skipping scheduled jobs';
END $$;

-- ============================================================================
-- 📊 ESTADÍSTICAS INICIALES
-- ============================================================================

-- Análisis de espacio requerido
SELECT 
    'Nuevas tablas creadas' as status,
    COUNT(*) as count
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('model_config', 'gpt5_batch_jobs', 'product_complexity_cache', 
                     'semantic_cache', 'processing_metrics', 'processing_queue',
                     'category_embeddings');

-- ============================================================================
-- ✅ VERIFICACIÓN FINAL
-- ============================================================================

DO $$
DECLARE
    v_count INTEGER;
BEGIN
    -- Verificar que las tablas críticas existen
    SELECT COUNT(*) INTO v_count
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
      AND table_name IN ('model_config', 'gpt5_batch_jobs', 'semantic_cache');
    
    IF v_count < 3 THEN
        RAISE EXCEPTION 'Error: No todas las tablas críticas fueron creadas';
    END IF;
    
    -- Verificar que hay modelos configurados
    SELECT COUNT(*) INTO v_count FROM model_config WHERE active = TRUE;
    
    IF v_count < 3 THEN
        RAISE EXCEPTION 'Error: Modelos no configurados correctamente';
    END IF;
    
    RAISE NOTICE '✅ Migración inicial GPT-5 completada exitosamente';
    RAISE NOTICE '📊 Tablas creadas: 7';
    RAISE NOTICE '🔧 Funciones creadas: 4';
    RAISE NOTICE '📈 Vistas materializadas: 2';
    RAISE NOTICE '🎯 Modelos configurados: %', v_count;
END $$;

-- FIN DE MIGRACIÓN 001