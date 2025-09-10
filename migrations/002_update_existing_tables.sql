-- 🔄 MIGRACIÓN GPT-5: Actualización de Tablas Existentes
-- Fecha: 2025-09-10
-- Descripción: Modificaciones a tablas existentes para soporte GPT-5
-- ============================================================================

-- Verificar que estamos en la BD correcta
\c postgres;

-- ============================================================================
-- 1️⃣ ACTUALIZACIÓN DE TABLA: ai_metadata_cache
-- ============================================================================

-- Agregar nuevas columnas para soporte GPT-5
DO $$
BEGIN
    -- model_used: Modelo que generó el cache
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'ai_metadata_cache' AND column_name = 'model_used') THEN
        ALTER TABLE ai_metadata_cache 
        ADD COLUMN model_used VARCHAR(50);
        
        -- Actualizar registros existentes con modelo por defecto
        UPDATE ai_metadata_cache 
        SET model_used = 'gpt-4o-mini' 
        WHERE model_used IS NULL;
    END IF;
    
    -- tokens_used: Total de tokens consumidos
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'ai_metadata_cache' AND column_name = 'tokens_used') THEN
        ALTER TABLE ai_metadata_cache 
        ADD COLUMN tokens_used INTEGER DEFAULT 0;
    END IF;
    
    -- processing_version: Versión del sistema de procesamiento
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'ai_metadata_cache' AND column_name = 'processing_version') THEN
        ALTER TABLE ai_metadata_cache 
        ADD COLUMN processing_version VARCHAR(20) DEFAULT 'v1.0';
        
        -- Marcar registros existentes como v1.0
        UPDATE ai_metadata_cache 
        SET processing_version = 'v1.0' 
        WHERE processing_version IS NULL;
    END IF;
    
    -- batch_id: ID del batch si fue procesado en lote
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'ai_metadata_cache' AND column_name = 'batch_id') THEN
        ALTER TABLE ai_metadata_cache 
        ADD COLUMN batch_id VARCHAR(100);
    END IF;
    
    -- quality_score: Puntuación de calidad del resultado
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'ai_metadata_cache' AND column_name = 'quality_score') THEN
        ALTER TABLE ai_metadata_cache 
        ADD COLUMN quality_score NUMERIC(3,2) CHECK (quality_score >= 0 AND quality_score <= 1);
    END IF;
    
    -- ttl_hours: Time to live configurable
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'ai_metadata_cache' AND column_name = 'ttl_hours') THEN
        ALTER TABLE ai_metadata_cache 
        ADD COLUMN ttl_hours INTEGER DEFAULT 168; -- 7 días por defecto
    END IF;
    
    -- ai_response: Respuesta completa de IA (para debugging)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'ai_metadata_cache' AND column_name = 'ai_response') THEN
        ALTER TABLE ai_metadata_cache 
        ADD COLUMN ai_response JSONB;
    END IF;
    
    -- embedding: Vector de embedding para búsqueda semántica
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'ai_metadata_cache' AND column_name = 'embedding') THEN
        ALTER TABLE ai_metadata_cache 
        ADD COLUMN embedding vector(1536);
    END IF;
    
    -- updated_at: Timestamp de última actualización
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'ai_metadata_cache' AND column_name = 'updated_at') THEN
        ALTER TABLE ai_metadata_cache 
        ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
        
        -- Inicializar con created_at para registros existentes
        UPDATE ai_metadata_cache 
        SET updated_at = created_at 
        WHERE updated_at IS NULL;
    END IF;
END $$;

-- Crear índices adicionales para ai_metadata_cache
CREATE INDEX IF NOT EXISTS idx_ai_cache_model ON ai_metadata_cache(model_used);
CREATE INDEX IF NOT EXISTS idx_ai_cache_batch ON ai_metadata_cache(batch_id) WHERE batch_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ai_cache_ttl ON ai_metadata_cache(created_at, ttl_hours);
CREATE INDEX IF NOT EXISTS idx_ai_cache_quality ON ai_metadata_cache(quality_score) WHERE quality_score IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ai_cache_version ON ai_metadata_cache(processing_version);

-- Índice para embeddings (si existe la columna)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'ai_metadata_cache' AND column_name = 'embedding') THEN
        CREATE INDEX IF NOT EXISTS idx_ai_cache_embedding 
        ON ai_metadata_cache 
        USING hnsw (embedding vector_cosine_ops)
        WHERE embedding IS NOT NULL;
    END IF;
END $$;

-- ============================================================================
-- 2️⃣ ACTUALIZACIÓN DE TABLA: productos_maestros
-- ============================================================================

DO $$
BEGIN
    -- complexity_score: Puntuación de complejidad del producto
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'productos_maestros' AND column_name = 'complexity_score') THEN
        ALTER TABLE productos_maestros 
        ADD COLUMN complexity_score NUMERIC(3,2);
    END IF;
    
    -- last_model_used: Último modelo que procesó el producto
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'productos_maestros' AND column_name = 'last_model_used') THEN
        ALTER TABLE productos_maestros 
        ADD COLUMN last_model_used VARCHAR(50);
    END IF;
    
    -- processing_confidence: Confianza del último procesamiento
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'productos_maestros' AND column_name = 'processing_confidence') THEN
        ALTER TABLE productos_maestros 
        ADD COLUMN processing_confidence NUMERIC(3,2);
    END IF;
    
    -- last_processed_at: Timestamp del último procesamiento
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'productos_maestros' AND column_name = 'last_processed_at') THEN
        ALTER TABLE productos_maestros 
        ADD COLUMN last_processed_at TIMESTAMP;
    END IF;
    
    -- processing_count: Contador de veces procesado
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'productos_maestros' AND column_name = 'processing_count') THEN
        ALTER TABLE productos_maestros 
        ADD COLUMN processing_count INTEGER DEFAULT 0;
    END IF;
END $$;

-- Crear índices para productos_maestros
CREATE INDEX IF NOT EXISTS idx_productos_complexity ON productos_maestros(complexity_score) WHERE complexity_score IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_productos_last_model ON productos_maestros(last_model_used);
CREATE INDEX IF NOT EXISTS idx_productos_confidence ON productos_maestros(processing_confidence) WHERE processing_confidence IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_productos_processed ON productos_maestros(last_processed_at DESC) WHERE last_processed_at IS NOT NULL;

-- ============================================================================
-- 3️⃣ ACTUALIZACIÓN DE TABLA: processing_logs
-- ============================================================================

DO $$
BEGIN
    -- model_used: Modelo utilizado en el procesamiento
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'processing_logs' AND column_name = 'model_used') THEN
        ALTER TABLE processing_logs 
        ADD COLUMN model_used VARCHAR(50);
    END IF;
    
    -- tokens_consumed: Tokens consumidos
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'processing_logs' AND column_name = 'tokens_consumed') THEN
        ALTER TABLE processing_logs 
        ADD COLUMN tokens_consumed INTEGER;
    END IF;
    
    -- cost_usd: Costo en USD
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'processing_logs' AND column_name = 'cost_usd') THEN
        ALTER TABLE processing_logs 
        ADD COLUMN cost_usd NUMERIC(10,6);
    END IF;
    
    -- batch_id: Referencia al batch si aplica
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'processing_logs' AND column_name = 'batch_id') THEN
        ALTER TABLE processing_logs 
        ADD COLUMN batch_id VARCHAR(100);
    END IF;
END $$;

-- ============================================================================
-- 4️⃣ ACTUALIZACIÓN DE TABLA: categories
-- ============================================================================

DO $$
BEGIN
    -- complexity_weight: Peso de complejidad para esta categoría
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'categories' AND column_name = 'complexity_weight') THEN
        ALTER TABLE categories 
        ADD COLUMN complexity_weight NUMERIC(3,2) DEFAULT 0.5;
    END IF;
    
    -- preferred_model: Modelo preferido para esta categoría
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'categories' AND column_name = 'preferred_model') THEN
        ALTER TABLE categories 
        ADD COLUMN preferred_model VARCHAR(50);
    END IF;
    
    -- avg_tokens: Promedio de tokens para productos de esta categoría
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'categories' AND column_name = 'avg_tokens') THEN
        ALTER TABLE categories 
        ADD COLUMN avg_tokens INTEGER;
    END IF;
END $$;

-- ============================================================================
-- 5️⃣ ACTUALIZACIÓN DE TABLA: retailers
-- ============================================================================

DO $$
BEGIN
    -- priority: Prioridad de procesamiento
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'retailers' AND column_name = 'priority') THEN
        ALTER TABLE retailers 
        ADD COLUMN priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10);
    END IF;
    
    -- batch_enabled: Si está habilitado para batch processing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'retailers' AND column_name = 'batch_enabled') THEN
        ALTER TABLE retailers 
        ADD COLUMN batch_enabled BOOLEAN DEFAULT TRUE;
    END IF;
    
    -- last_batch_id: Último batch procesado
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'retailers' AND column_name = 'last_batch_id') THEN
        ALTER TABLE retailers 
        ADD COLUMN last_batch_id VARCHAR(100);
    END IF;
END $$;

-- ============================================================================
-- 6️⃣ CONSTRAINTS Y FOREIGN KEYS
-- ============================================================================

-- Agregar FK de ai_metadata_cache a gpt5_batch_jobs (si existe)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_ai_cache_batch'
    ) THEN
        ALTER TABLE ai_metadata_cache 
        ADD CONSTRAINT fk_ai_cache_batch 
        FOREIGN KEY (batch_id) 
        REFERENCES gpt5_batch_jobs(batch_id) 
        ON DELETE SET NULL;
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'No se pudo crear FK a gpt5_batch_jobs (tabla puede no existir aún)';
END $$;

-- ============================================================================
-- 7️⃣ TRIGGERS PARA UPDATED_AT
-- ============================================================================

-- Trigger para ai_metadata_cache
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.triggers 
        WHERE trigger_name = 'update_ai_metadata_cache_updated_at'
    ) THEN
        CREATE TRIGGER update_ai_metadata_cache_updated_at 
        BEFORE UPDATE ON ai_metadata_cache
        FOR EACH ROW 
        EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- Trigger para productos_maestros (si tiene updated_at)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'productos_maestros' AND column_name = 'updated_at') 
       AND NOT EXISTS (
        SELECT 1 FROM information_schema.triggers 
        WHERE trigger_name = 'update_productos_maestros_updated_at'
    ) THEN
        CREATE TRIGGER update_productos_maestros_updated_at 
        BEFORE UPDATE ON productos_maestros
        FOR EACH ROW 
        EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- ============================================================================
-- 8️⃣ ACTUALIZAR VALORES POR DEFECTO EN CATEGORÍAS
-- ============================================================================

-- Asignar pesos de complejidad basados en categoría
UPDATE categories SET complexity_weight = CASE
    WHEN category_id IN ('smartphones', 'notebooks', 'tablets', 'smartwatches') THEN 0.8
    WHEN category_id IN ('home_appliances', 'electronics', 'gaming') THEN 0.7
    WHEN category_id IN ('clothing', 'shoes', 'accessories') THEN 0.6
    WHEN category_id IN ('beauty', 'perfumes', 'personal_care') THEN 0.5
    WHEN category_id IN ('groceries', 'beverages', 'snacks') THEN 0.3
    ELSE 0.5
END
WHERE complexity_weight IS NULL OR complexity_weight = 0.5;

-- Asignar modelos preferidos por categoría
UPDATE categories SET preferred_model = CASE
    WHEN complexity_weight >= 0.7 THEN 'gpt-5'
    WHEN complexity_weight >= 0.5 THEN 'gpt-5-mini'
    ELSE 'gpt-5-mini'
END
WHERE preferred_model IS NULL;

-- ============================================================================
-- 9️⃣ ESTADÍSTICAS Y VALIDACIÓN
-- ============================================================================

-- Crear función para validar integridad de datos
CREATE OR REPLACE FUNCTION validate_gpt5_migration() RETURNS TABLE (
    check_name VARCHAR(100),
    status VARCHAR(20),
    details TEXT
) AS $$
BEGIN
    -- Check 1: ai_metadata_cache tiene nuevas columnas
    RETURN QUERY
    SELECT 
        'ai_metadata_cache columns'::VARCHAR(100),
        CASE 
            WHEN COUNT(*) >= 8 THEN 'PASS'::VARCHAR(20)
            ELSE 'FAIL'::VARCHAR(20)
        END,
        'Nuevas columnas: ' || COUNT(*)::TEXT
    FROM information_schema.columns
    WHERE table_name = 'ai_metadata_cache'
      AND column_name IN ('model_used', 'tokens_used', 'processing_version', 
                          'batch_id', 'quality_score', 'ttl_hours', 
                          'ai_response', 'embedding', 'updated_at');
    
    -- Check 2: productos_maestros tiene nuevas columnas
    RETURN QUERY
    SELECT 
        'productos_maestros columns'::VARCHAR(100),
        CASE 
            WHEN COUNT(*) >= 4 THEN 'PASS'::VARCHAR(20)
            ELSE 'FAIL'::VARCHAR(20)
        END,
        'Nuevas columnas: ' || COUNT(*)::TEXT
    FROM information_schema.columns
    WHERE table_name = 'productos_maestros'
      AND column_name IN ('complexity_score', 'last_model_used', 
                          'processing_confidence', 'last_processed_at',
                          'processing_count');
    
    -- Check 3: Índices creados
    RETURN QUERY
    SELECT 
        'Índices GPT-5'::VARCHAR(100),
        CASE 
            WHEN COUNT(*) >= 5 THEN 'PASS'::VARCHAR(20)
            ELSE 'WARNING'::VARCHAR(20)
        END,
        'Índices creados: ' || COUNT(*)::TEXT
    FROM pg_indexes
    WHERE schemaname = 'public'
      AND indexname LIKE 'idx_%'
      AND tablename IN ('ai_metadata_cache', 'productos_maestros');
    
    -- Check 4: Categories actualizado
    RETURN QUERY
    SELECT 
        'Categories config'::VARCHAR(100),
        CASE 
            WHEN COUNT(*) > 0 THEN 'PASS'::VARCHAR(20)
            ELSE 'WARNING'::VARCHAR(20)
        END,
        'Categorías con modelo preferido: ' || COUNT(*)::TEXT
    FROM categories
    WHERE preferred_model IS NOT NULL;
    
END;
$$ LANGUAGE plpgsql;

-- Ejecutar validación
SELECT * FROM validate_gpt5_migration();

-- ============================================================================
-- 🎯 RESUMEN DE CAMBIOS
-- ============================================================================

DO $$
DECLARE
    v_ai_cache_cols INTEGER;
    v_productos_cols INTEGER;
    v_indices INTEGER;
BEGIN
    -- Contar columnas agregadas
    SELECT COUNT(*) INTO v_ai_cache_cols
    FROM information_schema.columns
    WHERE table_name = 'ai_metadata_cache'
      AND column_name IN ('model_used', 'tokens_used', 'processing_version', 
                          'batch_id', 'quality_score', 'ttl_hours');
    
    SELECT COUNT(*) INTO v_productos_cols
    FROM information_schema.columns
    WHERE table_name = 'productos_maestros'
      AND column_name IN ('complexity_score', 'last_model_used', 
                          'processing_confidence');
    
    SELECT COUNT(*) INTO v_indices
    FROM pg_indexes
    WHERE schemaname = 'public'
      AND indexname LIKE 'idx_%'
      AND created > CURRENT_DATE;
    
    RAISE NOTICE '✅ Actualización de tablas existentes completada';
    RAISE NOTICE '📊 ai_metadata_cache: % nuevas columnas', v_ai_cache_cols;
    RAISE NOTICE '📊 productos_maestros: % nuevas columnas', v_productos_cols;
    RAISE NOTICE '🔍 Nuevos índices creados: %', v_indices;
    RAISE NOTICE '⚡ Triggers actualizados: updated_at automático';
    RAISE NOTICE '🎯 Categorías configuradas con modelos preferidos';
END $$;

-- FIN DE MIGRACIÓN 002