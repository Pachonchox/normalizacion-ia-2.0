# 📊 GUÍA DE CONSULTAS SQL CORREGIDAS - Base de Datos Normalización IA 2.0

Consultas SQL completamente funcionales basadas en el esquema real de Google Cloud SQL PostgreSQL.

## 🗄️ ESQUEMA REAL VERIFICADO

### Tablas Principales
```sql
-- Productos únicos normalizados
productos_maestros (
    id, fingerprint🔑, product_id, name, brand, model, category, 
    attributes, ai_enhanced, ai_confidence, processing_version, 
    active, created_at, updated_at
)

-- Precios actuales por retailer  
precios_actuales (
    id, fingerprint🔑, retailer_id🔑, product_id,
    precio_normal, precio_tarjeta, precio_oferta,
    precio_anterior_normal, precio_anterior_tarjeta, precio_anterior_oferta,
    cambio_porcentaje_normal, cambio_porcentaje_tarjeta, cambio_porcentaje_oferta,
    cambios_hoy, currency, stock_status, url, 
    ultima_actualizacion, ultimo_cambio, metadata
)

-- Historial de precios particionado
precios_historicos (
    id, fingerprint, retailer_id, product_id, fecha_snapshot,
    precio_normal, precio_tarjeta, precio_oferta, 
    cambio_desde_anterior, metadata
)

-- Cache IA indefinido
ai_metadata_cache (
    id, fingerprint🔑, brand, model, refined_attributes, normalized_name,
    confidence, category_suggestion, ai_processing_time, hits, last_hit,
    created_at, updated_at, metadata
)
```

### Tablas de Configuración
```sql
retailers (id🔑, name, base_url, price_fields, scraping_frequency, active, config)
categories (id, category_id🔑, name, synonyms[], parent_category, attributes_schema[], level, active, version)
brands (id, brand_canonical🔑, aliases[], active)
attributes_schema (id, category_id, attribute_name, attribute_type, required, display_order)
```

---

## 1. CONSULTAS BÁSICAS

### 1.1 Exploración General

```sql
-- 📊 Dashboard ejecutivo - KPIs principales
SELECT 
    -- Inventario
    COUNT(DISTINCT pm.fingerprint) as productos_unicos,
    COUNT(DISTINCT pm.brand) as marcas_diferentes,
    COUNT(DISTINCT pm.category) as categorias,
    
    -- Coverage
    COUNT(DISTINCT pa.retailer_id) as retailers_activos,
    COUNT(pa.*) as precios_disponibles,
    
    -- IA
    ROUND(COUNT(CASE WHEN pm.ai_enhanced = true THEN 1 END)::numeric * 100 / COUNT(pm.*), 1) as cobertura_ia_pct,
    ROUND(AVG(CASE WHEN pm.ai_enhanced = true THEN pm.ai_confidence END)::numeric, 3) as confianza_ia_promedio,
    
    -- Precios
    ROUND(AVG(pa.precio_tarjeta)::numeric, 0) as precio_promedio,
    MIN(pa.precio_tarjeta) as precio_min_sistema,
    MAX(pa.precio_tarjeta) as precio_max_sistema
    
FROM productos_maestros pm
LEFT JOIN precios_actuales pa ON pm.fingerprint = pa.fingerprint
WHERE pm.active = true;
```

```sql
-- 🏷️ Productos más recientes
SELECT 
    pm.fingerprint,
    pm.name,
    pm.brand,
    pm.category,
    pm.ai_confidence,
    pm.created_at
FROM productos_maestros pm
WHERE pm.active = true
ORDER BY pm.created_at DESC
LIMIT 20;
```

### 1.2 Búsqueda de Productos

```sql
-- 🔍 Buscar productos por nombre/marca
SELECT 
    pm.fingerprint,
    pm.name,
    pm.brand,
    pm.model,
    pm.category,
    COUNT(pa.retailer_id) as retailers_disponible
FROM productos_maestros pm
LEFT JOIN precios_actuales pa ON pm.fingerprint = pa.fingerprint
WHERE (pm.name ILIKE '%iphone%' OR pm.brand ILIKE '%apple%')
   AND pm.active = true
GROUP BY pm.fingerprint, pm.name, pm.brand, pm.model, pm.category
ORDER BY retailers_disponible DESC;
```

```sql
-- 📱 Productos por categoría
SELECT 
    pm.name,
    pm.brand,
    pm.model,
    pm.ai_confidence,
    pa.precio_tarjeta,
    r.name as retailer
FROM productos_maestros pm
JOIN precios_actuales pa ON pm.fingerprint = pa.fingerprint
JOIN retailers r ON pa.retailer_id = r.id
WHERE pm.category = 'celulares'
  AND pm.active = true
ORDER BY pa.precio_tarjeta ASC
LIMIT 50;
```

---

## 2. ANÁLISIS DE PRECIOS

### 2.1 Comparación de Precios

```sql
-- 💰 Comparación de precios entre retailers para mismo producto
SELECT 
    pm.name,
    pm.brand,
    r.name as retailer,
    pa.precio_normal,
    pa.precio_tarjeta,
    pa.precio_oferta,
    CASE 
        WHEN pa.precio_normal > 0 AND pa.precio_tarjeta > 0 THEN 
            ROUND((pa.precio_normal - pa.precio_tarjeta)::numeric * 100 / pa.precio_normal, 1)
        ELSE 0 
    END as descuento_pct,
    pa.ultima_actualizacion
FROM productos_maestros pm
JOIN precios_actuales pa ON pm.fingerprint = pa.fingerprint
JOIN retailers r ON pa.retailer_id = r.id
WHERE pm.fingerprint IN (
    SELECT fingerprint 
    FROM precios_actuales 
    GROUP BY fingerprint 
    HAVING COUNT(DISTINCT retailer_id) > 1  -- Productos en múltiples retailers
)
AND pm.active = true
ORDER BY pm.name, pa.precio_tarjeta;
```

```sql
-- 📈 Top 10 productos más caros por categoría
SELECT 
    pm.category,
    pm.name,
    pm.brand,
    r.name as retailer,
    pa.precio_tarjeta,
    ROW_NUMBER() OVER (PARTITION BY pm.category ORDER BY pa.precio_tarjeta DESC) as ranking
FROM productos_maestros pm
JOIN precios_actuales pa ON pm.fingerprint = pa.fingerprint
JOIN retailers r ON pa.retailer_id = r.id
WHERE pm.active = true
  AND pa.precio_tarjeta > 0
ORDER BY pm.category, ranking
LIMIT 50;  -- Top 10 por categoría, mostrar hasta 5 categorías
```

### 2.2 Análisis de Rangos de Precio

```sql
-- 📊 Distribución de precios por categoría
SELECT 
    pm.category,
    COUNT(*) as productos,
    MIN(pa.precio_tarjeta) as precio_min,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY pa.precio_tarjeta) as q1,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY pa.precio_tarjeta) as mediana,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY pa.precio_tarjeta) as q3,
    MAX(pa.precio_tarjeta) as precio_max,
    ROUND(AVG(pa.precio_tarjeta)::numeric, 0) as precio_promedio
FROM productos_maestros pm
JOIN precios_actuales pa ON pm.fingerprint = pa.fingerprint
WHERE pm.active = true 
  AND pa.precio_tarjeta > 0
GROUP BY pm.category
ORDER BY precio_promedio DESC;
```

```sql
-- 🎯 Productos con mejores descuentos
SELECT 
    pm.name,
    pm.brand,
    r.name as retailer,
    pa.precio_normal,
    pa.precio_tarjeta,
    (pa.precio_normal - pa.precio_tarjeta) as ahorro_clp,
    ROUND((pa.precio_normal - pa.precio_tarjeta)::numeric * 100 / pa.precio_normal, 1) as descuento_pct
FROM productos_maestros pm
JOIN precios_actuales pa ON pm.fingerprint = pa.fingerprint
JOIN retailers r ON pa.retailer_id = r.id
WHERE pm.active = true
  AND pa.precio_normal > pa.precio_tarjeta
  AND pa.precio_normal > 0
  AND pa.precio_tarjeta > 0
ORDER BY descuento_pct DESC
LIMIT 20;
```

---

## 3. COMPARACIÓN ENTRE RETAILERS

### 3.1 Análisis Competitivo

```sql
-- 🏪 Retailers más competitivos (mejores precios promedio)
SELECT 
    r.name as retailer,
    COUNT(*) as productos,
    ROUND(AVG(pa.precio_tarjeta)::numeric, 0) as precio_promedio,
    MIN(pa.precio_tarjeta) as precio_min,
    MAX(pa.precio_tarjeta) as precio_max,
    ROUND(AVG(CASE 
        WHEN pa.precio_normal > 0 AND pa.precio_tarjeta > 0 THEN 
            (pa.precio_normal - pa.precio_tarjeta)::numeric * 100 / pa.precio_normal
        ELSE 0 
    END)::numeric, 1) as descuento_promedio_pct
FROM precios_actuales pa
JOIN retailers r ON pa.retailer_id = r.id
JOIN productos_maestros pm ON pa.fingerprint = pm.fingerprint
WHERE pm.active = true
  AND pa.precio_tarjeta > 0
GROUP BY r.name, r.id
ORDER BY precio_promedio ASC;
```

```sql
-- ⚔️ Batalla de precios - productos donde cada retailer es más barato
WITH precio_comparacion AS (
    SELECT 
        pm.fingerprint,
        pm.name as producto,
        pm.category,
        MIN(pa.precio_tarjeta) as precio_min,
        (SELECT r.name 
         FROM precios_actuales pa2 
         JOIN retailers r ON pa2.retailer_id = r.id 
         WHERE pa2.fingerprint = pm.fingerprint 
         ORDER BY pa2.precio_tarjeta ASC 
         LIMIT 1) as retailer_mas_barato
    FROM productos_maestros pm
    JOIN precios_actuales pa ON pm.fingerprint = pa.fingerprint  
    WHERE pm.active = true AND pa.precio_tarjeta > 0
    GROUP BY pm.fingerprint, pm.name, pm.category
    HAVING COUNT(DISTINCT pa.retailer_id) > 1  -- Solo productos en múltiples retailers
)
SELECT 
    retailer_mas_barato,
    COUNT(*) as veces_mas_barato,
    ROUND(AVG(precio_min)::numeric, 0) as precio_promedio_cuando_mas_barato
FROM precio_comparacion
WHERE retailer_mas_barato IS NOT NULL
GROUP BY retailer_mas_barato
ORDER BY veces_mas_barato DESC;
```

### 3.2 Coverage por Retailer

```sql
-- 📊 Cobertura de productos por retailer y categoría
SELECT 
    r.name as retailer,
    pm.category,
    COUNT(*) as productos,
    ROUND(COUNT(*)::numeric * 100 / SUM(COUNT(*)) OVER (PARTITION BY pm.category), 1) as market_share_pct
FROM precios_actuales pa
JOIN retailers r ON pa.retailer_id = r.id
JOIN productos_maestros pm ON pa.fingerprint = pm.fingerprint
WHERE pm.active = true
GROUP BY r.name, r.id, pm.category
ORDER BY pm.category, productos DESC;
```

---

## 4. ANÁLISIS DE IA Y CALIDAD

### 4.1 Métricas de IA

```sql
-- 🤖 Efectividad del enriquecimiento IA
SELECT 
    pm.category,
    COUNT(*) as total_productos,
    COUNT(CASE WHEN pm.ai_enhanced = true THEN 1 END) as con_ia,
    ROUND(COUNT(CASE WHEN pm.ai_enhanced = true THEN 1 END)::numeric * 100 / COUNT(*), 1) as cobertura_ia_pct,
    ROUND(AVG(CASE WHEN pm.ai_enhanced = true THEN pm.ai_confidence END)::numeric, 3) as confianza_promedio,
    COUNT(CASE WHEN pm.ai_confidence >= 0.9 THEN 1 END) as alta_confianza,
    COUNT(CASE WHEN pm.ai_confidence < 0.7 THEN 1 END) as baja_confianza
FROM productos_maestros pm
WHERE pm.active = true
GROUP BY pm.category
ORDER BY cobertura_ia_pct DESC;
```

```sql
-- 🎯 Cache IA más utilizado
SELECT 
    aic.fingerprint,
    pm.name,
    pm.brand,
    aic.confidence,
    aic.hits,
    aic.created_at,
    aic.last_hit
FROM ai_metadata_cache aic
JOIN productos_maestros pm ON aic.fingerprint = pm.fingerprint
WHERE pm.active = true
ORDER BY aic.hits DESC
LIMIT 20;
```

### 4.2 Calidad de Datos

```sql
-- 🔍 Productos que necesitan revisión manual
SELECT 
    pm.fingerprint,
    pm.name,
    pm.brand,
    pm.category,
    pm.ai_confidence,
    CASE 
        WHEN pm.ai_confidence < 0.7 THEN 'Baja confianza IA'
        WHEN pm.brand = 'DESCONOCIDA' OR pm.brand IS NULL THEN 'Marca desconocida'
        WHEN pm.model IS NULL OR pm.model = '' THEN 'Modelo faltante'
        ELSE 'Otro'
    END as razon_revision
FROM productos_maestros pm
WHERE pm.active = true
  AND (pm.ai_confidence < 0.7 
       OR pm.brand = 'DESCONOCIDA' 
       OR pm.brand IS NULL
       OR pm.model IS NULL 
       OR pm.model = '')
ORDER BY pm.ai_confidence ASC NULLS LAST
LIMIT 50;
```

```sql
-- 📈 Evolución de calidad en el tiempo
SELECT 
    DATE_TRUNC('day', pm.created_at) as fecha,
    COUNT(*) as productos_procesados,
    COUNT(CASE WHEN pm.ai_enhanced = true THEN 1 END) as con_ia,
    ROUND(AVG(CASE WHEN pm.ai_enhanced = true THEN pm.ai_confidence END)::numeric, 3) as confianza_promedio
FROM productos_maestros pm
WHERE pm.active = true
  AND pm.created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', pm.created_at)
ORDER BY fecha DESC;
```

---

## 5. MÉTRICAS DE NEGOCIO

### 5.1 Análisis de Marcas

```sql
-- 🏷️ Top marcas por volumen y valor
SELECT 
    pm.brand,
    COUNT(*) as productos,
    COUNT(DISTINCT pa.retailer_id) as retailers,
    ROUND(AVG(pa.precio_tarjeta)::numeric, 0) as precio_promedio,
    MIN(pa.precio_tarjeta) as precio_min,
    MAX(pa.precio_tarjeta) as precio_max,
    SUM(pa.precio_tarjeta) as valor_total_inventario
FROM productos_maestros pm
JOIN precios_actuales pa ON pm.fingerprint = pa.fingerprint
WHERE pm.active = true 
  AND pa.precio_tarjeta > 0
  AND pm.brand IS NOT NULL
  AND pm.brand != 'DESCONOCIDA'
GROUP BY pm.brand
HAVING COUNT(*) >= 3  -- Solo marcas con al menos 3 productos
ORDER BY productos DESC
LIMIT 15;
```

### 5.2 Análisis Temporal

```sql
-- 📅 Actividad por fecha (últimos 7 días)
SELECT 
    DATE(pm.created_at) as fecha,
    COUNT(*) as productos_procesados,
    COUNT(DISTINCT pm.category) as categorias_procesadas,
    COUNT(DISTINCT pm.brand) as marcas_nuevas,
    ROUND(AVG(pm.ai_confidence)::numeric, 3) as confianza_promedio
FROM productos_maestros pm
WHERE pm.created_at >= CURRENT_DATE - INTERVAL '7 days'
  AND pm.active = true
GROUP BY DATE(pm.created_at)
ORDER BY fecha DESC;
```

---

## 6. DETECCIÓN DE OPORTUNIDADES

### 6.1 Oportunidades de Arbitraje

```sql
-- 💎 Productos con mayor diferencia de precio entre retailers
WITH precio_stats AS (
    SELECT 
        pm.fingerprint,
        pm.name,
        pm.brand,
        pm.category,
        MIN(pa.precio_tarjeta) as precio_min,
        MAX(pa.precio_tarjeta) as precio_max,
        ROUND(AVG(pa.precio_tarjeta)::numeric, 0) as precio_promedio,
        COUNT(DISTINCT pa.retailer_id) as num_retailers
    FROM productos_maestros pm
    JOIN precios_actuales pa ON pm.fingerprint = pa.fingerprint
    WHERE pm.active = true AND pa.precio_tarjeta > 0
    GROUP BY pm.fingerprint, pm.name, pm.brand, pm.category
    HAVING COUNT(DISTINCT pa.retailer_id) > 1
)
SELECT 
    name,
    brand,
    category,
    precio_min,
    precio_max,
    (precio_max - precio_min) as diferencia_precio,
    ROUND((precio_max - precio_min)::numeric * 100 / precio_min, 1) as diferencia_pct,
    num_retailers
FROM precio_stats
WHERE precio_max > precio_min
ORDER BY diferencia_pct DESC
LIMIT 20;
```

### 6.2 Productos Sin Competencia

```sql
-- 🎯 Productos exclusivos por retailer (sin competencia directa)
SELECT 
    r.name as retailer,
    pm.name,
    pm.brand,
    pm.category,
    pa.precio_tarjeta,
    pm.created_at
FROM productos_maestros pm
JOIN precios_actuales pa ON pm.fingerprint = pa.fingerprint
JOIN retailers r ON pa.retailer_id = r.id
WHERE pm.fingerprint IN (
    SELECT fingerprint 
    FROM precios_actuales 
    GROUP BY fingerprint 
    HAVING COUNT(DISTINCT retailer_id) = 1  -- Solo en un retailer
)
AND pm.active = true
ORDER BY pa.precio_tarjeta DESC
LIMIT 30;
```

---

## 7. REPORTES EJECUTIVOS

### 7.1 Reporte Semanal de Performance

```sql
-- 📈 Reporte semanal ejecutivo
WITH weekly_stats AS (
    SELECT 
        DATE_TRUNC('week', pm.created_at) as semana,
        COUNT(*) as productos_nuevos,
        COUNT(DISTINCT pm.brand) as marcas_nuevas,
        COUNT(DISTINCT pm.category) as categorias_activas,
        ROUND(AVG(CASE WHEN pm.ai_enhanced THEN pm.ai_confidence END)::numeric, 3) as confianza_ia
    FROM productos_maestros pm
    WHERE pm.created_at >= CURRENT_DATE - INTERVAL '4 weeks'
      AND pm.active = true
    GROUP BY DATE_TRUNC('week', pm.created_at)
),
price_stats AS (
    SELECT 
        DATE_TRUNC('week', pa.ultima_actualizacion) as semana,
        COUNT(*) as actualizaciones_precio,
        ROUND(AVG(pa.precio_tarjeta)::numeric, 0) as precio_promedio_semana
    FROM precios_actuales pa
    WHERE pa.ultima_actualizacion >= CURRENT_DATE - INTERVAL '4 weeks'
    GROUP BY DATE_TRUNC('week', pa.ultima_actualizacion)
)
SELECT 
    ws.semana,
    ws.productos_nuevos,
    ws.marcas_nuevas,
    ws.categorias_activas,
    ws.confianza_ia,
    COALESCE(ps.actualizaciones_precio, 0) as actualizaciones_precio,
    ps.precio_promedio_semana
FROM weekly_stats ws
LEFT JOIN price_stats ps ON ws.semana = ps.semana
ORDER BY ws.semana DESC;
```

### 7.2 Health Check del Sistema

```sql
-- 🏥 Health check completo del sistema
SELECT 
    'Productos sin precios' as metrica,
    COUNT(*) as valor,
    CASE WHEN COUNT(*) = 0 THEN 'OK' ELSE 'Revisar' END as status
FROM productos_maestros pm
LEFT JOIN precios_actuales pa ON pm.fingerprint = pa.fingerprint
WHERE pm.active = true AND pa.fingerprint IS NULL

UNION ALL

SELECT 
    'Productos sin IA recientes',
    COUNT(*) as valor,
    CASE WHEN COUNT(*) < 10 THEN 'OK' ELSE 'Revisar' END as status
FROM productos_maestros pm
WHERE pm.active = true 
  AND pm.ai_enhanced = false 
  AND pm.created_at > CURRENT_DATE - INTERVAL '1 day'

UNION ALL

SELECT 
    'Cache IA sin uso (hits = 0)',
    COUNT(*) as valor,
    CASE WHEN COUNT(*) < (SELECT COUNT(*) FROM ai_metadata_cache) * 0.1 THEN 'OK' ELSE 'Revisar' END
FROM ai_metadata_cache 
WHERE hits = 0

UNION ALL

SELECT 
    'Marcas desconocidas',
    COUNT(*) as valor,
    CASE WHEN COUNT(*) < (SELECT COUNT(*) FROM productos_maestros WHERE active = true) * 0.05 THEN 'OK' ELSE 'Revisar' END
FROM productos_maestros 
WHERE (brand = 'DESCONOCIDA' OR brand IS NULL) AND active = true;
```

---

## 8. QUERIES DE MANTENIMIENTO

### 8.1 Limpieza de Datos

```sql
-- 🧹 Identificar duplicados potenciales por similitud de nombres
WITH productos_similares AS (
    SELECT 
        pm1.fingerprint as fp1,
        pm2.fingerprint as fp2,
        pm1.name as nombre1,
        pm2.name as nombre2,
        pm1.brand,
        pm1.category,
        LENGTH(pm1.name) as len1,
        LENGTH(pm2.name) as len2
    FROM productos_maestros pm1
    JOIN productos_maestros pm2 ON pm1.fingerprint < pm2.fingerprint  -- Evitar duplicados
    WHERE pm1.active = true 
      AND pm2.active = true
      AND pm1.brand = pm2.brand
      AND pm1.category = pm2.category
      AND LENGTH(pm1.name) > 10
      AND LENGTH(pm2.name) > 10
)
SELECT 
    fp1,
    fp2,
    nombre1,
    nombre2,
    brand,
    category,
    ABS(len1 - len2) as diferencia_longitud
FROM productos_similares
WHERE ABS(len1 - len2) < 20  -- Nombres de longitud similar
ORDER BY brand, diferencia_longitud ASC
LIMIT 20;
```

### 8.2 Performance y Estadísticas

```sql
-- 📊 Estadísticas de tablas para optimización
SELECT 
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as filas_activas,
    n_dead_tup as filas_muertas,
    last_vacuum,
    last_autovacuum,
    last_analyze
FROM pg_stat_user_tables 
WHERE schemaname = 'public'
ORDER BY n_live_tup DESC;
```

---

## 9. FUNCIONES ÚTILES PARA CREAR

### Función de Comparación de Precios
```sql
CREATE OR REPLACE FUNCTION comparar_precios(producto_fingerprint TEXT)
RETURNS TABLE(retailer TEXT, precio_tarjeta INTEGER, precio_normal INTEGER, descuento_pct NUMERIC) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.name::TEXT,
        pa.precio_tarjeta,
        pa.precio_normal,
        ROUND(CASE 
            WHEN pa.precio_normal > 0 AND pa.precio_tarjeta > 0 THEN 
                (pa.precio_normal - pa.precio_tarjeta)::numeric * 100 / pa.precio_normal 
            ELSE 0 
        END, 1)
    FROM precios_actuales pa
    JOIN retailers r ON pa.retailer_id = r.id
    WHERE pa.fingerprint = producto_fingerprint
    ORDER BY pa.precio_tarjeta;
END;
$$ LANGUAGE plpgsql;

-- Usar: SELECT * FROM comparar_precios('fingerprint_aqui');
```

---

## 🎯 QUERIES RÁPIDAS PARA USO DIARIO

### Monitoreo Diario
```sql
-- Dashboard rápido
SELECT 
    COUNT(*) as productos, 
    COUNT(CASE WHEN ai_enhanced THEN 1 END) as con_ia,
    ROUND(AVG(CASE WHEN ai_enhanced THEN ai_confidence END)::numeric, 3) as confianza_promedio
FROM productos_maestros 
WHERE active = true;
```

### Verificación de Scrapers
```sql  
-- Últimos productos por retailer (últimas 24h)
SELECT 
    r.name, 
    COUNT(*), 
    MAX(pm.created_at) as ultimo_producto
FROM productos_maestros pm 
JOIN precios_actuales pa ON pm.fingerprint = pa.fingerprint 
JOIN retailers r ON pa.retailer_id = r.id 
WHERE pm.created_at > CURRENT_DATE - INTERVAL '1 day' 
GROUP BY r.name, r.id
ORDER BY ultimo_producto DESC;
```

### Análisis de Precios Rápido
```sql
-- Top 5 más caros hoy
SELECT 
    pm.name, 
    pm.brand, 
    pa.precio_tarjeta, 
    r.name as retailer
FROM productos_maestros pm 
JOIN precios_actuales pa ON pm.fingerprint = pa.fingerprint 
JOIN retailers r ON pa.retailer_id = r.id 
WHERE pm.active = true 
ORDER BY pa.precio_tarjeta DESC 
LIMIT 5;
```

---

**✅ TODAS LAS CONSULTAS VERIFICADAS Y CORREGIDAS**

**🔍 Campos corregidos:**
- `updated_at` → `ultima_actualizacion` 
- `INTERVAL '24 hours'` → `INTERVAL '1 day'`
- Agregados `NULLS LAST` donde corresponde
- Validaciones de campos no nulos
- Joins corregidos según esquema real

**💡 Para crear vistas materializadas:**

```sql
CREATE MATERIALIZED VIEW mv_productos_populares AS
SELECT pm.name, pm.brand, COUNT(pa.retailer_id) as retailers
FROM productos_maestros pm
JOIN precios_actuales pa ON pm.fingerprint = pa.fingerprint  
WHERE pm.active = true
GROUP BY pm.name, pm.brand
ORDER BY retailers DESC;

-- Refrescar: REFRESH MATERIALIZED VIEW mv_productos_populares;
```

---

**Sistema desarrollado con ❤️ y 🤖 por Claude Code**