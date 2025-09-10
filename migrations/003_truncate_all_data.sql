-- 🗑️ TRUNCATE DE DATOS - Sistema GPT-5
-- Fecha: 2025-09-10
-- Descripción: Limpia TODOS los datos de las tablas sin eliminar el esquema
-- ⚠️ ADVERTENCIA: Este script ELIMINARÁ TODOS LOS DATOS de forma permanente
-- ============================================================================

-- Verificar que estamos en la BD correcta
\c postgres;

-- ============================================================================
-- 🚨 CONFIRMACIÓN DE SEGURIDAD
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '════════════════════════════════════════════════════════════';
    RAISE NOTICE '⚠️  ADVERTENCIA: TRUNCATE MASIVO DE DATOS';
    RAISE NOTICE '════════════════════════════════════════════════════════════';
    RAISE NOTICE '';
    RAISE NOTICE 'Este script eliminará TODOS los datos de las siguientes tablas:';
    RAISE NOTICE '  • ai_metadata_cache (cache de IA)';
    RAISE NOTICE '  • productos_maestros (catálogo de productos)';
    RAISE NOTICE '  • precios_actuales (precios vigentes)';
    RAISE NOTICE '  • precios_historicos (historial completo)';
    RAISE NOTICE '  • processing_logs (logs de procesamiento)';
    RAISE NOTICE '  • price_alerts (alertas de precio)';
    RAISE NOTICE '  • Todas las tablas nuevas de GPT-5';
    RAISE NOTICE '';
    RAISE NOTICE '⏱️ Esperando 5 segundos antes de continuar...';
    RAISE NOTICE '   (Cancele con Ctrl+C si no desea continuar)';
    RAISE NOTICE '';
    
    -- Esperar 5 segundos
    PERFORM pg_sleep(5);
    
    RAISE NOTICE '🚀 Iniciando TRUNCATE de datos...';
    RAISE NOTICE '';
END $$;

-- ============================================================================
-- 📊 ESTADÍSTICAS PRE-TRUNCATE
-- ============================================================================

DO $$
DECLARE
    v_count_productos INTEGER;
    v_count_ai_cache INTEGER;
    v_count_precios INTEGER;
    v_count_historicos INTEGER;
    v_total_size TEXT;
BEGIN
    -- Contar registros actuales
    SELECT COUNT(*) INTO v_count_productos FROM productos_maestros;
    SELECT COUNT(*) INTO v_count_ai_cache FROM ai_metadata_cache;
    SELECT COUNT(*) INTO v_count_precios FROM precios_actuales;
    SELECT COUNT(*) INTO v_count_historicos FROM precios_historicos;
    
    -- Tamaño total de BD
    SELECT pg_size_pretty(pg_database_size(current_database())) INTO v_total_size;
    
    RAISE NOTICE '📊 ESTADÍSTICAS ACTUALES:';
    RAISE NOTICE '  • productos_maestros: % registros', v_count_productos;
    RAISE NOTICE '  • ai_metadata_cache: % registros', v_count_ai_cache;
    RAISE NOTICE '  • precios_actuales: % registros', v_count_precios;
    RAISE NOTICE '  • precios_historicos: % registros', v_count_historicos;
    RAISE NOTICE '  • Tamaño total BD: %', v_total_size;
    RAISE NOTICE '';
END $$;

-- ============================================================================
-- 🗑️ TRUNCATE DE TABLAS GPT-5 (Nuevas)
-- ============================================================================

-- Deshabilitar temporalmente las foreign keys
SET session_replication_role = 'replica';

-- Tablas de GPT-5 (si existen)
DO $$
BEGIN
    -- processing_queue
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'processing_queue') THEN
        TRUNCATE TABLE processing_queue CASCADE;
        RAISE NOTICE '✓ Truncado: processing_queue';
    END IF;
    
    -- processing_metrics
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'processing_metrics') THEN
        TRUNCATE TABLE processing_metrics CASCADE;
        RAISE NOTICE '✓ Truncado: processing_metrics';
    END IF;
    
    -- semantic_cache
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'semantic_cache') THEN
        TRUNCATE TABLE semantic_cache CASCADE;
        RAISE NOTICE '✓ Truncado: semantic_cache';
    END IF;
    
    -- product_complexity_cache
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'product_complexity_cache') THEN
        TRUNCATE TABLE product_complexity_cache CASCADE;
        RAISE NOTICE '✓ Truncado: product_complexity_cache';
    END IF;
    
    -- gpt5_batch_jobs
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'gpt5_batch_jobs') THEN
        TRUNCATE TABLE gpt5_batch_jobs CASCADE;
        RAISE NOTICE '✓ Truncado: gpt5_batch_jobs';
    END IF;
    
    -- category_embeddings
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'category_embeddings') THEN
        TRUNCATE TABLE category_embeddings CASCADE;
        RAISE NOTICE '✓ Truncado: category_embeddings';
    END IF;
    
    -- NO truncar model_config (configuración del sistema)
    RAISE NOTICE '⏭️ Preservado: model_config (configuración)';
    
END $$;

-- ============================================================================
-- 🗑️ TRUNCATE DE TABLAS EXISTENTES (Sistema actual)
-- ============================================================================

-- Cache de IA
TRUNCATE TABLE ai_metadata_cache CASCADE;
RAISE NOTICE '✓ Truncado: ai_metadata_cache';

-- Logs de procesamiento
TRUNCATE TABLE processing_logs CASCADE;
RAISE NOTICE '✓ Truncado: processing_logs';

-- Alertas de precio
TRUNCATE TABLE price_alerts CASCADE;
RAISE NOTICE '✓ Truncado: price_alerts';

-- Precios (orden importante por dependencias)
TRUNCATE TABLE precios_historicos CASCADE;
RAISE NOTICE '✓ Truncado: precios_historicos (y todas sus particiones)';

TRUNCATE TABLE precios_actuales CASCADE;
RAISE NOTICE '✓ Truncado: precios_actuales';

-- Productos maestros (al final por las FK)
TRUNCATE TABLE productos_maestros CASCADE;
RAISE NOTICE '✓ Truncado: productos_maestros';

-- ============================================================================
-- 🔧 RESET DE SECUENCIAS
-- ============================================================================

DO $$
DECLARE
    r RECORD;
BEGIN
    -- Reset todas las secuencias a 1
    FOR r IN 
        SELECT sequence_name 
        FROM information_schema.sequences 
        WHERE sequence_schema = 'public'
    LOOP
        EXECUTE 'ALTER SEQUENCE ' || r.sequence_name || ' RESTART WITH 1';
    END LOOP;
    
    RAISE NOTICE '✓ Secuencias reiniciadas';
END $$;

-- ============================================================================
-- 🔄 REFRESCAR VISTAS MATERIALIZADAS
-- ============================================================================

DO $$
BEGIN
    -- Refrescar vistas materializadas (ahora estarán vacías)
    IF EXISTS (SELECT 1 FROM pg_matviews WHERE matviewname = 'mv_products_by_complexity') THEN
        REFRESH MATERIALIZED VIEW mv_products_by_complexity;
        RAISE NOTICE '✓ Vista materializada refrescada: mv_products_by_complexity';
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_matviews WHERE matviewname = 'mv_daily_cost_metrics') THEN
        REFRESH MATERIALIZED VIEW mv_daily_cost_metrics;
        RAISE NOTICE '✓ Vista materializada refrescada: mv_daily_cost_metrics';
    END IF;
END $$;

-- ============================================================================
-- 🧹 VACUUM Y ANALYZE
-- ============================================================================

-- Rehabilitar foreign keys
SET session_replication_role = 'origin';

-- Limpiar espacio y actualizar estadísticas
VACUUM ANALYZE;
RAISE NOTICE '✓ VACUUM y ANALYZE completado';

-- ============================================================================
-- 📊 ESTADÍSTICAS POST-TRUNCATE
-- ============================================================================

DO $$
DECLARE
    v_count_total INTEGER;
    v_total_size TEXT;
    v_tables_count INTEGER;
BEGIN
    -- Contar registros totales en todas las tablas
    SELECT 
        SUM(n_live_tup)::INTEGER,
        COUNT(*)::INTEGER
    INTO v_count_total, v_tables_count
    FROM pg_stat_user_tables 
    WHERE schemaname = 'public';
    
    -- Tamaño total de BD
    SELECT pg_size_pretty(pg_database_size(current_database())) INTO v_total_size;
    
    RAISE NOTICE '';
    RAISE NOTICE '════════════════════════════════════════════════════════════';
    RAISE NOTICE '✅ TRUNCATE COMPLETADO EXITOSAMENTE';
    RAISE NOTICE '════════════════════════════════════════════════════════════';
    RAISE NOTICE '';
    RAISE NOTICE '📊 ESTADÍSTICAS FINALES:';
    RAISE NOTICE '  • Total de registros en BD: %', COALESCE(v_count_total, 0);
    RAISE NOTICE '  • Tablas procesadas: %', v_tables_count;
    RAISE NOTICE '  • Tamaño BD después: %', v_total_size;
    RAISE NOTICE '';
    RAISE NOTICE '📝 Datos preservados:';
    RAISE NOTICE '  • model_config (configuración de modelos GPT)';
    RAISE NOTICE '  • categories (taxonomía de categorías)';
    RAISE NOTICE '  • brands (catálogo de marcas)';
    RAISE NOTICE '  • retailers (configuración de retailers)';
    RAISE NOTICE '  • attributes_schema (esquemas de atributos)';
    RAISE NOTICE '  • system_config (configuración del sistema)';
    RAISE NOTICE '  • migration_history (historial de migraciones)';
    RAISE NOTICE '';
    RAISE NOTICE '🚀 La base de datos está lista para recibir datos nuevos';
    RAISE NOTICE '';
END $$;

-- ============================================================================
-- 🎯 INSERTAR REGISTRO DE AUDITORÍA
-- ============================================================================

INSERT INTO processing_logs (process_type, status, message, details, execution_time)
VALUES (
    'TRUNCATE_ALL_DATA',
    'completed',
    'Truncate masivo de datos para migración GPT-5',
    jsonb_build_object(
        'script', '003_truncate_all_data.sql',
        'timestamp', CURRENT_TIMESTAMP,
        'user', CURRENT_USER,
        'database', current_database()
    ),
    0
);

-- FIN DE TRUNCATE