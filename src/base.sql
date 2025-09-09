-- ============================================
-- ESQUEMA COMPLETO GOOGLE CLOUD SQL POSTGRESQL
-- Sistema de Análisis de Precios Retail Chile
-- ============================================

-- Configuración de timezone para Chile
ALTER DATABASE postgres SET timezone = 'America/Santiago';

-- Habilitar extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================
-- 1. TABLA: productos_maestros
-- Registro único por fingerprint con atributos consolidados
-- ============================================
CREATE TABLE IF NOT EXISTS productos_maestros (
    id SERIAL PRIMARY KEY,
    fingerprint VARCHAR(64) UNIQUE NOT NULL,
    product_id VARCHAR(100) NOT NULL,
    name VARCHAR(500) NOT NULL,
    brand VARCHAR(100),
    model VARCHAR(200),
    category VARCHAR(100),
    attributes JSONB DEFAULT '{}',
    ai_enhanced BOOLEAN DEFAULT FALSE,
    ai_confidence NUMERIC(3,2) CHECK (ai_confidence >= 0 AND ai_confidence <= 1),
    processing_version VARCHAR(20),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_product_fingerprint UNIQUE(fingerprint)
);

CREATE INDEX idx_productos_fingerprint ON productos_maestros(fingerprint);
CREATE INDEX idx_productos_brand ON productos_maestros(brand);
CREATE INDEX idx_productos_category ON productos_maestros(category);
CREATE INDEX idx_productos_attributes_gin ON productos_maestros USING gin(attributes);
CREATE INDEX idx_productos_active ON productos_maestros(active) WHERE active = TRUE;

-- ============================================
-- 2. TABLA: retailers
-- Configuración de retailers y sus patrones de scraping
-- ============================================
CREATE TABLE IF NOT EXISTS retailers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    base_url VARCHAR(500),
    price_fields JSONB DEFAULT '["card_price", "normal_price", "original_price"]',
    scraping_frequency INTEGER DEFAULT 6, -- veces al día
    active BOOLEAN DEFAULT TRUE,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insertar retailers iniciales
INSERT INTO retailers (name, base_url, scraping_frequency) VALUES
    ('Paris', 'https://www.paris.cl', 6),
    ('Ripley', 'https://www.ripley.cl', 6),
    ('Falabella', 'https://www.falabella.com/falabella-cl', 6)
ON CONFLICT (name) DO NOTHING;

-- ============================================
-- 3. TABLA: precios_actuales (HOT TABLE)
-- Precios vigentes intra-día (solo 1 registro por producto-retailer)
-- ============================================
CREATE TABLE IF NOT EXISTS precios_actuales (
    id SERIAL PRIMARY KEY,
    fingerprint VARCHAR(64) NOT NULL,
    retailer_id INTEGER NOT NULL REFERENCES retailers(id),
    product_id VARCHAR(100) NOT NULL,
    precio_normal INTEGER, -- Precio regular sin descuentos
    precio_tarjeta INTEGER, -- Precio con descuento tarjeta
    precio_oferta INTEGER, -- Precio promocional especial
    precio_anterior_normal INTEGER,
    precio_anterior_tarjeta INTEGER,
    precio_anterior_oferta INTEGER,
    cambio_porcentaje_normal NUMERIC(5,2),
    cambio_porcentaje_tarjeta NUMERIC(5,2),
    cambio_porcentaje_oferta NUMERIC(5,2),
    cambios_hoy INTEGER DEFAULT 0, -- Contador de cambios intra-día
    currency VARCHAR(3) DEFAULT 'CLP',
    stock_status VARCHAR(20) DEFAULT 'available',
    url VARCHAR(1000),
    ultima_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ultimo_cambio TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    CONSTRAINT uk_precio_actual UNIQUE(fingerprint, retailer_id)
);

CREATE INDEX idx_precios_act_fingerprint ON precios_actuales(fingerprint);
CREATE INDEX idx_precios_act_retailer ON precios_actuales(retailer_id);
CREATE INDEX idx_precios_act_cambios ON precios_actuales(cambios_hoy) WHERE cambios_hoy > 0;
CREATE INDEX idx_precios_act_ultimo_cambio ON precios_actuales(ultimo_cambio);

-- ============================================
-- 4. TABLA: precios_historicos (PARTITIONED)
-- Snapshots diarios particionados por mes
-- ============================================
CREATE TABLE IF NOT EXISTS precios_historicos (
    id BIGSERIAL,
    fingerprint VARCHAR(64) NOT NULL,
    retailer_id INTEGER NOT NULL,
    product_id VARCHAR(100) NOT NULL,
    precio_normal INTEGER,
    precio_tarjeta INTEGER,
    precio_oferta INTEGER,
    currency VARCHAR(3) DEFAULT 'CLP',
    stock_status VARCHAR(20),
    fecha_snapshot DATE NOT NULL,
    hora_snapshot TIME NOT NULL,
    metadata JSONB DEFAULT '{}',
    PRIMARY KEY (id, fecha_snapshot)
) PARTITION BY RANGE (fecha_snapshot);

-- Crear particiones para los próximos 12 meses
DO $$
DECLARE
    start_date DATE := DATE_TRUNC('month', CURRENT_DATE);
    end_date DATE;
    partition_name TEXT;
BEGIN
    FOR i IN 0..11 LOOP
        end_date := start_date + INTERVAL '1 month';
        partition_name := 'precios_historicos_' || TO_CHAR(start_date, 'YYYY_MM');
        
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS %I PARTITION OF precios_historicos
            FOR VALUES FROM (%L) TO (%L)',
            partition_name, start_date, end_date
        );
        
        -- Crear índices en cada partición
        EXECUTE format('
            CREATE INDEX IF NOT EXISTS idx_%I_fingerprint ON %I(fingerprint);
            CREATE INDEX IF NOT EXISTS idx_%I_retailer ON %I(retailer_id);
            CREATE INDEX IF NOT EXISTS idx_%I_fecha ON %I(fecha_snapshot);',
            partition_name, partition_name,
            partition_name, partition_name,
            partition_name, partition_name
        );
        
        start_date := end_date;
    END LOOP;
END $$;

-- ============================================
-- 5. TABLA: ai_metadata_cache
-- Cache indefinido de metadatos IA por fingerprint
-- ============================================
CREATE TABLE IF NOT EXISTS ai_metadata_cache (
    id SERIAL PRIMARY KEY,
    fingerprint VARCHAR(64) UNIQUE NOT NULL,
    brand VARCHAR(100),
    model VARCHAR(200),
    refined_attributes JSONB DEFAULT '{}',
    normalized_name VARCHAR(500),
    confidence NUMERIC(3,2),
    category_suggestion VARCHAR(100),
    ai_processing_time NUMERIC(10,2),
    hits INTEGER DEFAULT 0, -- Contador de hits del cache
    last_hit TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_ai_cache_fingerprint ON ai_metadata_cache(fingerprint);
CREATE INDEX idx_ai_cache_confidence ON ai_metadata_cache(confidence);
CREATE INDEX idx_ai_cache_hits ON ai_metadata_cache(hits);

-- ============================================
-- 6. TABLA: categories
-- Taxonomías configurables con sinónimos dinámicos
-- ============================================
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    category_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    synonyms TEXT[], -- Array de sinónimos
    parent_category VARCHAR(100),
    attributes_schema TEXT[], -- Esquema de atributos esperados
    level INTEGER DEFAULT 1,
    active BOOLEAN DEFAULT TRUE,
    version VARCHAR(20) DEFAULT '1.0',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_categories_parent ON categories(parent_category);
CREATE INDEX idx_categories_synonyms_gin ON categories USING gin(synonyms);
CREATE INDEX idx_categories_active ON categories(active) WHERE active = TRUE;

-- ============================================
-- 7. TABLA: brands
-- Marcas maestras con aliases múltiples
-- ============================================
CREATE TABLE IF NOT EXISTS brands (
    id SERIAL PRIMARY KEY,
    brand_canonical VARCHAR(100) UNIQUE NOT NULL,
    aliases TEXT[], -- Array de aliases
    active BOOLEAN DEFAULT TRUE,
    confidence_threshold NUMERIC(3,2) DEFAULT 0.8,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_brands_canonical ON brands(brand_canonical);
CREATE INDEX idx_brands_aliases_gin ON brands USING gin(aliases);

-- ============================================
-- 8. TABLA: attributes_schema
-- Esquemas de atributos por categoría
-- ============================================
CREATE TABLE IF NOT EXISTS attributes_schema (
    id SERIAL PRIMARY KEY,
    category_id VARCHAR(100) NOT NULL,
    attribute_name VARCHAR(100) NOT NULL,
    attribute_type VARCHAR(50) NOT NULL, -- string, number, boolean, array
    required BOOLEAN DEFAULT FALSE,
    default_value TEXT,
    validation_rules JSONB DEFAULT '{}',
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_category_attribute UNIQUE(category_id, attribute_name)
);

CREATE INDEX idx_attr_schema_category ON attributes_schema(category_id);

-- ============================================
-- 9. TABLA: price_alerts
-- Configuración y log de alertas por producto
-- ============================================
CREATE TABLE IF NOT EXISTS price_alerts (
    id SERIAL PRIMARY KEY,
    fingerprint VARCHAR(64),
    retailer_id INTEGER REFERENCES retailers(id),
    alert_type VARCHAR(50) NOT NULL, -- 'price_drop', 'price_increase', 'out_of_stock', etc.
    threshold_value NUMERIC(10,2),
    threshold_percentage NUMERIC(5,2),
    category VARCHAR(100),
    brand VARCHAR(100),
    active BOOLEAN DEFAULT TRUE,
    notification_channels JSONB DEFAULT '["email", "webhook"]',
    last_triggered TIMESTAMP WITH TIME ZONE,
    trigger_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    config JSONB DEFAULT '{}'
);

CREATE INDEX idx_alerts_fingerprint ON price_alerts(fingerprint);
CREATE INDEX idx_alerts_active ON price_alerts(active) WHERE active = TRUE;
CREATE INDEX idx_alerts_type ON price_alerts(alert_type);
CREATE INDEX idx_alerts_last_triggered ON price_alerts(last_triggered);

-- ============================================
-- 10. TABLA: processing_logs
-- Auditoría completa del pipeline
-- ============================================
CREATE TABLE IF NOT EXISTS processing_logs (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID DEFAULT uuid_generate_v4(),
    module_name VARCHAR(100) NOT NULL,
    operation VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL, -- 'success', 'error', 'warning'
    affected_records INTEGER DEFAULT 0,
    processing_time_ms INTEGER,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Particionado mensual para logs
CREATE INDEX idx_logs_session ON processing_logs(session_id);
CREATE INDEX idx_logs_module ON processing_logs(module_name);
CREATE INDEX idx_logs_status ON processing_logs(status);
CREATE INDEX idx_logs_created ON processing_logs(created_at);

-- ============================================
-- 11. TABLA: system_config
-- Configuraciones dinámicas del sistema
-- ============================================
CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    module VARCHAR(100),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Configuraciones iniciales
INSERT INTO system_config (config_key, config_value, description, module) VALUES
    ('snapshot_time', '"23:59:00"', 'Hora diaria para snapshot histórico', 'scheduler'),
    ('alert_cooldown_minutes', '60', 'Minutos mínimos entre alertas del mismo tipo', 'alerts'),
    ('cache_ttl_indefinite', 'true', 'Cache IA sin expiración', 'ai_cache'),
    ('max_price_changes_per_day', '10', 'Máximo de cambios de precio antes de alerta', 'monitoring')
ON CONFLICT (config_key) DO NOTHING;

-- ============================================
-- TRIGGERS Y FUNCIONES
-- ============================================

-- Función para actualizar timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar trigger a todas las tablas con updated_at
DO $$
DECLARE
    t TEXT;
BEGIN
    FOR t IN 
        SELECT table_name 
        FROM information_schema.columns 
        WHERE column_name = 'updated_at' 
        AND table_schema = 'public'
    LOOP
        EXECUTE format('
            CREATE TRIGGER update_%I_updated_at 
            BEFORE UPDATE ON %I 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column()',
            t, t
        );
    END LOOP;
END $$;

-- Función para detectar cambios de precio
CREATE OR REPLACE FUNCTION check_price_change()
RETURNS TRIGGER AS $$
DECLARE
    cambio_normal BOOLEAN := FALSE;
    cambio_tarjeta BOOLEAN := FALSE;
    cambio_oferta BOOLEAN := FALSE;
BEGIN
    -- Verificar cambios en cada tipo de precio
    IF COALESCE(NEW.precio_normal, 0) != COALESCE(OLD.precio_normal, 0) THEN
        cambio_normal := TRUE;
        NEW.precio_anterior_normal := OLD.precio_normal;
        IF OLD.precio_normal > 0 THEN
            NEW.cambio_porcentaje_normal := ((NEW.precio_normal - OLD.precio_normal)::NUMERIC / OLD.precio_normal) * 100;
        END IF;
    END IF;
    
    IF COALESCE(NEW.precio_tarjeta, 0) != COALESCE(OLD.precio_tarjeta, 0) THEN
        cambio_tarjeta := TRUE;
        NEW.precio_anterior_tarjeta := OLD.precio_tarjeta;
        IF OLD.precio_tarjeta > 0 THEN
            NEW.cambio_porcentaje_tarjeta := ((NEW.precio_tarjeta - OLD.precio_tarjeta)::NUMERIC / OLD.precio_tarjeta) * 100;
        END IF;
    END IF;
    
    IF COALESCE(NEW.precio_oferta, 0) != COALESCE(OLD.precio_oferta, 0) THEN
        cambio_oferta := TRUE;
        NEW.precio_anterior_oferta := OLD.precio_oferta;
        IF OLD.precio_oferta > 0 THEN
            NEW.cambio_porcentaje_oferta := ((NEW.precio_oferta - OLD.precio_oferta)::NUMERIC / OLD.precio_oferta) * 100;
        END IF;
    END IF;
    
    -- Si hubo algún cambio, actualizar contadores
    IF cambio_normal OR cambio_tarjeta OR cambio_oferta THEN
        NEW.cambios_hoy := OLD.cambios_hoy + 1;
        NEW.ultimo_cambio := CURRENT_TIMESTAMP;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_check_price_change
BEFORE UPDATE ON precios_actuales
FOR EACH ROW
EXECUTE FUNCTION check_price_change();

-- Función para snapshot nocturno automático
CREATE OR REPLACE FUNCTION create_daily_snapshot()
RETURNS void AS $$
BEGIN
    INSERT INTO precios_historicos (
        fingerprint, retailer_id, product_id,
        precio_normal, precio_tarjeta, precio_oferta,
        currency, stock_status, fecha_snapshot, hora_snapshot, metadata
    )
    SELECT 
        fingerprint, retailer_id, product_id,
        precio_normal, precio_tarjeta, precio_oferta,
        currency, stock_status, 
        CURRENT_DATE, CURRENT_TIME,
        jsonb_build_object(
            'cambios_dia', cambios_hoy,
            'ultimo_cambio', ultimo_cambio
        )
    FROM precios_actuales;
    
    -- Resetear contador de cambios diarios
    UPDATE precios_actuales SET cambios_hoy = 0;
    
    -- Log de la operación
    INSERT INTO processing_logs (
        module_name, operation, status, affected_records
    ) VALUES (
        'snapshot_scheduler', 'daily_snapshot', 'success',
        (SELECT COUNT(*) FROM precios_actuales)
    );
END;
$$ LANGUAGE plpgsql;

-- Función para actualizar hits del cache IA
CREATE OR REPLACE FUNCTION update_ai_cache_hit(p_fingerprint VARCHAR)
RETURNS TABLE(
    brand VARCHAR,
    model VARCHAR,
    refined_attributes JSONB,
    normalized_name VARCHAR,
    confidence NUMERIC,
    category_suggestion VARCHAR
) AS $$
BEGIN
    -- Actualizar contador de hits
    UPDATE ai_metadata_cache 
    SET hits = hits + 1,
        last_hit = CURRENT_TIMESTAMP
    WHERE fingerprint = p_fingerprint;
    
    -- Retornar datos del cache
    RETURN QUERY
    SELECT 
        c.brand, c.model, c.refined_attributes,
        c.normalized_name, c.confidence, c.category_suggestion
    FROM ai_metadata_cache c
    WHERE c.fingerprint = p_fingerprint;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- VISTAS MATERIALIZADAS PARA ANÁLISIS
-- ============================================

-- Vista de comparación de precios entre retailers
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_comparacion_precios AS
SELECT 
    pm.fingerprint,
    pm.name,
    pm.brand,
    pm.category,
    json_object_agg(
        r.name,
        json_build_object(
            'precio_normal', pa.precio_normal,
            'precio_tarjeta', pa.precio_tarjeta,
            'precio_oferta', pa.precio_oferta,
            'ultimo_cambio', pa.ultimo_cambio
        )
    ) as precios_por_retailer,
    MIN(COALESCE(pa.precio_oferta, pa.precio_tarjeta, pa.precio_normal)) as precio_minimo,
    MAX(COALESCE(pa.precio_normal, pa.precio_tarjeta, pa.precio_oferta)) as precio_maximo
FROM productos_maestros pm
JOIN precios_actuales pa ON pm.fingerprint = pa.fingerprint
JOIN retailers r ON pa.retailer_id = r.id
WHERE pm.active = TRUE
GROUP BY pm.fingerprint, pm.name, pm.brand, pm.category;

CREATE UNIQUE INDEX idx_mv_comp_fingerprint ON mv_comparacion_precios(fingerprint);

-- Vista de métricas de cache IA
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_cache_metrics AS
SELECT 
    DATE(created_at) as fecha,
    COUNT(*) as total_cached,
    AVG(confidence) as confidence_promedio,
    SUM(hits) as total_hits,
    AVG(ai_processing_time) as tiempo_promedio_ms,
    COUNT(DISTINCT category_suggestion) as categorias_unicas
FROM ai_metadata_cache
GROUP BY DATE(created_at);

CREATE UNIQUE INDEX idx_mv_cache_fecha ON mv_cache_metrics(fecha);

-- ============================================
-- PERMISOS Y SEGURIDAD
-- ============================================

-- Crear roles específicos
CREATE ROLE retail_reader;
CREATE ROLE retail_writer;
CREATE ROLE retail_admin;

-- Permisos para retail_reader
GRANT SELECT ON ALL TABLES IN SCHEMA public TO retail_reader;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO retail_reader;

-- Permisos para retail_writer
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO retail_writer;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO retail_writer;

-- Permisos para retail_admin
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO retail_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO retail_admin;

-- ============================================
-- ÍNDICES ADICIONALES PARA QUERIES COMPLEJAS
-- ============================================

-- Índices para análisis temporal
CREATE INDEX idx_precios_hist_fingerprint_fecha ON precios_historicos(fingerprint, fecha_snapshot);
CREATE INDEX idx_precios_hist_retailer_fecha ON precios_historicos(retailer_id, fecha_snapshot);

-- Índices para búsqueda de texto
CREATE INDEX idx_productos_name_trgm ON productos_maestros USING gin(name gin_trgm_ops);
CREATE INDEX idx_productos_model_trgm ON productos_maestros USING gin(model gin_trgm_ops);

-- ============================================
-- ESTADÍSTICAS Y MAINTENANCE
-- ============================================

-- Actualizar estadísticas
ANALYZE productos_maestros;
ANALYZE precios_actuales;
ANALYZE precios_historicos;
ANALYZE ai_metadata_cache;

-- Configurar autovacuum agresivo para tablas hot
ALTER TABLE precios_actuales SET (
    autovacuum_vacuum_scale_factor = 0.1,
    autovacuum_analyze_scale_factor = 0.05
);

-- ============================================
-- COMENTARIOS DE DOCUMENTACIÓN
-- ============================================

COMMENT ON TABLE productos_maestros IS 'Tabla maestra de productos únicos identificados por fingerprint';
COMMENT ON TABLE precios_actuales IS 'Hot table con precios vigentes, máximo 1 registro por producto-retailer';
COMMENT ON TABLE precios_historicos IS 'Tabla particionada con snapshots diarios de precios históricos';
COMMENT ON TABLE ai_metadata_cache IS 'Cache permanente de procesamiento IA para optimizar pipeline';
COMMENT ON COLUMN precios_actuales.cambios_hoy IS 'Contador de cambios intra-día, se resetea a las 23:59';
COMMENT ON COLUMN precios_actuales.precio_oferta IS 'Precio promocional especial (cyber, flash sales, etc)';

-- ============================================
-- FIN DEL ESQUEMA
-- ============================================