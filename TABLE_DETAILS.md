# 📊 Análisis Detallado de Tablas - Base de Datos

## 🎯 Tablas Core del Sistema

### 1. `productos_maestros` - Catálogo Principal
```sql
CREATE TABLE productos_maestros (
    id                INTEGER PRIMARY KEY,
    nombre            VARCHAR(500),
    marca             VARCHAR(100), 
    modelo            VARCHAR(200),
    categoria_id      VARCHAR(50) REFERENCES categories(category_id),
    atributos         JSONB,
    descripcion       VARCHAR(500),
    imagen_url        VARCHAR(2000),
    fingerprint       VARCHAR(64) UNIQUE,
    created_at        TIMESTAMP WITH TIME ZONE,
    updated_at        TIMESTAMP WITH TIME ZONE,
    active            BOOLEAN
);
```
**Propósito:** Catálogo maestro normalizado de productos  
**Registros estimados:** Miles a millones  
**Optimizaciones:** Índice único en fingerprint para matching

### 2. `categories` - Sistema de Taxonomía
```sql
CREATE TABLE categories (
    category_id       VARCHAR(50) PRIMARY KEY,
    name              VARCHAR(100),
    synonyms          TEXT[],
    active            BOOLEAN,
    metadata          JSONB,
    created_at        TIMESTAMP WITH TIME ZONE,
    updated_at        TIMESTAMP WITH TIME ZONE
);
```
**Propósito:** Taxonomía extensible de categorías  
**Datos actuales:** smartphones, notebooks, smart_tv, perfumes, printers, others  
**Sinónimos:** Arrays de términos para matching automático

### 3. `attributes_schema` - Esquemas Dinámicos
```sql
CREATE TABLE attributes_schema (
    id                INTEGER PRIMARY KEY,
    category_id       VARCHAR(50) REFERENCES categories(category_id),
    attribute_name    VARCHAR(100),
    attribute_type    VARCHAR(50),
    required          BOOLEAN,
    default_value     TEXT,
    display_order     INTEGER,
    validation_rules  JSONB,
    active            BOOLEAN
);
```
**Propósito:** Define atributos esperados por categoría  
**Ejemplo:** smartphones → {capacity, color, network, storage}  
**Validación:** Reglas JSONB para tipos y rangos

### 4. `brands` - Normalización de Marcas
```sql
CREATE TABLE brands (
    id                INTEGER PRIMARY KEY,
    brand_canonical   VARCHAR(100) UNIQUE,
    aliases           TEXT[],
    active            BOOLEAN,
    metadata          JSONB,
    created_at        TIMESTAMP WITH TIME ZONE,
    updated_at        TIMESTAMP WITH TIME ZONE
);
```
**Propósito:** Unificación de variantes de marcas  
**Ejemplo:** Samsung → ["samsung", "samsumg", "samung"]  
**Uso:** Normalización automática en pipeline

## 💰 Sistema de Precios

### 5. `precios_actuales` - Precios Vigentes
```sql
CREATE TABLE precios_actuales (
    id                    INTEGER PRIMARY KEY,
    producto_id           INTEGER REFERENCES productos_maestros(id),
    retailer_id           VARCHAR(50) REFERENCES retailers(retailer_id),
    precio_actual         NUMERIC(12,0),  -- En centavos CLP
    precio_oferta         NUMERIC(12,0),  -- En centavos CLP
    currency              VARCHAR(10) DEFAULT 'CLP',
    url_producto          VARCHAR(2000),
    metadata_adicional    JSONB,
    fecha_actualizacion   TIMESTAMP WITH TIME ZONE,
    created_at            TIMESTAMP WITH TIME ZONE
);
```
**Propósito:** Precios actuales por retailer  
**Moneda:** Centavos para evitar decimales  
**Metadata:** Info de scraping, descuentos, stock

### 6. `precios_historicos` - Historial Completo (PARTICIONADA)
```sql
CREATE TABLE precios_historicos (
    id                    INTEGER PRIMARY KEY,
    producto_id           INTEGER REFERENCES productos_maestros(id),
    retailer_id           VARCHAR(50) REFERENCES retailers(retailer_id),
    precio                NUMERIC(12,0),
    precio_oferta         NUMERIC(12,0),
    currency              VARCHAR(10),
    fecha_precio          TIMESTAMP WITH TIME ZONE,
    fuente                VARCHAR(50),
    metadata_scraping     JSONB,
    created_at            TIMESTAMP WITH TIME ZONE
) PARTITION BY RANGE (fecha_precio);
```
**Particiones actuales:**
- `precios_historicos_2025_09` (Sep 2025)
- `precios_historicos_2025_10` (Oct 2025)
- `precios_historicos_2025_11` (Nov 2025)
- `precios_historicos_2025_12` (Dic 2025)
- `precios_historicos_2026_01` (Ene 2026)
- `precios_historicos_2026_02` (Feb 2026)
- `precios_historicos_2026_03` (Mar 2026)
- `precios_historicos_2026_04` (Abr 2026)
- `precios_historicos_2026_05` (May 2026)
- `precios_historicos_2026_06` (Jun 2026)
- `precios_historicos_2026_07` (Jul 2026)
- `precios_historicos_2026_08` (Ago 2026)

**Estrategia:** Particionamiento mensual automático  
**Beneficio:** Consultas optimizadas por rango de fechas

### 7. `retailers` - Catálogo de Retailers
```sql
CREATE TABLE retailers (
    retailer_id           VARCHAR(50) PRIMARY KEY,
    name                  VARCHAR(200),
    base_url              VARCHAR(500),
    country               VARCHAR(100),
    active                BOOLEAN,
    scraping_config       JSONB,
    api_config            JSONB,
    created_at            TIMESTAMP WITH TIME ZONE,
    updated_at            TIMESTAMP WITH TIME ZONE
);
```
**Propósito:** Configuración de retailers monitoreados  
**Config scraping:** Headers, delays, selectors CSS  
**Config API:** Endpoints, auth, rate limits

## 🤖 Sistema de IA y Cache

### 8. `ai_metadata_cache` - Cache Inteligente
```sql
CREATE TABLE ai_metadata_cache (
    id                    INTEGER PRIMARY KEY,
    fingerprint           VARCHAR(64) UNIQUE,
    brand                 VARCHAR(100),
    model                 VARCHAR(200),
    refined_attributes    JSONB DEFAULT '{}'::jsonb,
    normalized_name       VARCHAR(500),
    confidence            NUMERIC(3,2),
    category_suggestion   VARCHAR(100),
    ai_processing_time    NUMERIC(10,2),
    hits                  INTEGER DEFAULT 0,
    last_hit              TIMESTAMP WITH TIME ZONE,
    created_at            TIMESTAMP WITH TIME ZONE,
    updated_at            TIMESTAMP WITH TIME ZONE
);
```
**Propósito:** Cache de enriquecimiento IA para optimizar costos  
**TTL implícito:** Via hits y last_hit  
**Fingerprint:** SHA-256 del nombre original  
**Atributos refinados:** Extraídos por OpenAI

## 🔔 Sistema de Alertas

### 9. `price_alerts` - Alertas de Precio
```sql
CREATE TABLE price_alerts (
    id                    INTEGER PRIMARY KEY,
    producto_id           INTEGER REFERENCES productos_maestros(id),
    retailer_id           VARCHAR(50) REFERENCES retailers(retailer_id),
    user_email            VARCHAR(200),
    precio_objetivo       NUMERIC(12,0),
    condition_type        VARCHAR(50),  -- 'menor_que', 'mayor_que', 'igual_a'
    active                BOOLEAN,
    created_at            TIMESTAMP WITH TIME ZONE,
    triggered_at          TIMESTAMP WITH TIME ZONE
);
```
**Propósito:** Sistema de notificaciones automáticas  
**Condiciones:** Múltiples tipos de triggers  
**Usuario:** Email para notificaciones

## 📋 Sistema de Logs y Auditoría

### 10. `processing_logs` - Logs del Sistema
```sql
CREATE TABLE processing_logs (
    id                    INTEGER PRIMARY KEY,
    process_type          VARCHAR(100),  -- 'normalize', 'scrape', 'match'
    status                VARCHAR(50),   -- 'success', 'error', 'warning'
    message               TEXT,
    details               JSONB,
    execution_time        NUMERIC(10,2),
    created_at            TIMESTAMP WITH TIME ZONE
);
```
**Propósito:** Auditoría completa de procesos  
**Tipos:** normalize, scrape, match, categorize  
**Detalles:** Stack traces, métricas, contexto

### 11. `system_config` - Configuración Global
```sql
CREATE TABLE system_config (
    config_key            VARCHAR(100) PRIMARY KEY,
    config_value          TEXT,
    description           VARCHAR(500),
    category              VARCHAR(50),
    updated_at            TIMESTAMP WITH TIME ZONE,
    updated_by            VARCHAR(100)
);
```
**Propósito:** Parámetros configurables del sistema  
**Ejemplos:**
- `ai_cache_ttl_days`: 7
- `scraping_delay_ms`: 2000
- `confidence_threshold`: 0.6

## 📊 Tablas del Sistema PostgreSQL

### 12. `pg_stat_statements` - Monitoreo de Queries
**Propósito:** Estadísticas de performance de queries  
**Campos clave:**
- `query`: SQL normalizado
- `calls`: Número de ejecuciones
- `total_exec_time`: Tiempo total de ejecución

### 13. `pg_stat_statements_info` - Info del Monitoreo
**Propósito:** Metadatos del sistema de estadísticas  
**Uso:** Reset de estadísticas, deallocation

## 🔗 Índices y Optimizaciones

### **Índices Principales**
```sql
-- Productos
CREATE UNIQUE INDEX idx_productos_fingerprint ON productos_maestros(fingerprint);
CREATE INDEX idx_productos_categoria ON productos_maestros(categoria_id);
CREATE INDEX idx_productos_marca ON productos_maestros(marca);

-- Precios
CREATE INDEX idx_precios_actuales_producto_retailer ON precios_actuales(producto_id, retailer_id);
CREATE INDEX idx_precios_historicos_fecha ON precios_historicos(fecha_precio);
CREATE INDEX idx_precios_historicos_producto ON precios_historicos(producto_id);

-- Cache IA
CREATE UNIQUE INDEX idx_ai_cache_fingerprint ON ai_metadata_cache(fingerprint);
CREATE INDEX idx_ai_cache_last_hit ON ai_metadata_cache(last_hit);

-- Categorías
CREATE INDEX idx_categories_active ON categories(active) WHERE active = true;
CREATE INDEX idx_attributes_category ON attributes_schema(category_id);
```

### **Triggers y Funciones**
- **Auto-update timestamps:** updated_at automático
- **Soft deletes:** active = false en lugar de DELETE
- **Partition management:** Creación automática de particiones mensuales

## 📈 Métricas de Uso

### **Estimaciones de Volumen**
- `productos_maestros`: ~100K productos
- `precios_actuales`: ~500K registros (5 retailers promedio)
- `precios_historicos`: ~50M registros (crecimiento mensual)
- `ai_metadata_cache`: ~50K entradas (alta reutilización)

### **Patrones de Acceso**
- **Lectura intensiva:** precios_actuales, ai_metadata_cache
- **Escritura intensiva:** precios_historicos (particionada)
- **Consultas complejas:** JOINs productos + precios + retailers

---

**📅 Generado:** 2025-09-09  
**🔄 Actualización:** Automática via extractor de esquema  
**📊 Total campos:** 200+ campos across 25 tablas