# 🗄️ Esquema Completo de Base de Datos - Normalizacion IA 2.0

## 📊 Diagrama Entidad-Relación (ERD)

```mermaid
erDiagram
    %% Tablas Core del Sistema
    productos_maestros {
        int id PK
        varchar(500) nombre
        varchar(100) marca
        varchar(200) modelo
        varchar(50) categoria_id FK
        jsonb atributos
        varchar(500) descripcion
        varchar(2000) imagen_url
        varchar(64) fingerprint
        timestamp created_at
        timestamp updated_at
        boolean active
    }
    
    categories {
        varchar(50) category_id PK
        varchar(100) name
        text[] synonyms
        boolean active
        jsonb metadata
        timestamp created_at
        timestamp updated_at
    }
    
    attributes_schema {
        int id PK
        varchar(50) category_id FK
        varchar(100) attribute_name
        varchar(50) attribute_type
        boolean required
        text default_value
        int display_order
        jsonb validation_rules
        boolean active
    }
    
    brands {
        int id PK
        varchar(100) brand_canonical PK
        text[] aliases
        boolean active
        jsonb metadata
        timestamp created_at
        timestamp updated_at
    }
    
    %% Sistema de Precios
    precios_actuales {
        int id PK
        int producto_id FK
        varchar(50) retailer_id FK
        numeric(12,0) precio_actual
        numeric(12,0) precio_oferta
        varchar(10) currency
        varchar(2000) url_producto
        jsonb metadata_adicional
        timestamp fecha_actualizacion
        timestamp created_at
    }
    
    precios_historicos {
        int id PK
        int producto_id FK
        varchar(50) retailer_id FK
        numeric(12,0) precio
        numeric(12,0) precio_oferta
        varchar(10) currency
        timestamp fecha_precio
        varchar(50) fuente
        jsonb metadata_scraping
        timestamp created_at
    }
    
    retailers {
        varchar(50) retailer_id PK
        varchar(200) name
        varchar(500) base_url
        varchar(100) country
        boolean active
        jsonb scraping_config
        jsonb api_config
        timestamp created_at
        timestamp updated_at
    }
    
    %% Sistema de Cache IA
    ai_metadata_cache {
        int id PK
        varchar(64) fingerprint UK
        varchar(100) brand
        varchar(200) model
        jsonb refined_attributes
        varchar(500) normalized_name
        numeric(3,2) confidence
        varchar(100) category_suggestion
        numeric(10,2) ai_processing_time
        int hits
        timestamp last_hit
        timestamp created_at
    }
    
    %% Sistema de Alertas
    price_alerts {
        int id PK
        int producto_id FK
        varchar(50) retailer_id FK
        varchar(200) user_email
        numeric(12,0) precio_objetivo
        varchar(50) condition_type
        boolean active
        timestamp created_at
        timestamp triggered_at
    }
    
    %% Sistema de Logs
    processing_logs {
        int id PK
        varchar(100) process_type
        varchar(50) status
        text message
        jsonb details
        numeric(10,2) execution_time
        timestamp created_at
    }
    
    %% Configuración del Sistema
    system_config {
        varchar(100) config_key PK
        text config_value
        varchar(500) description
        varchar(50) category
        timestamp updated_at
        varchar(100) updated_by
    }
    
    %% Tablas de Partición (Precios Históricos por Mes)
    precios_historicos_2025_09 {
        int id PK
        int producto_id FK
        varchar(50) retailer_id FK
        numeric(12,0) precio
        timestamp fecha_precio
    }
    
    precios_historicos_2025_10 {
        int id PK
        int producto_id FK
        varchar(50) retailer_id FK
        numeric(12,0) precio
        timestamp fecha_precio
    }
    
    precios_historicos_2025_11 {
        int id PK
        int producto_id FK
        varchar(50) retailer_id FK
        numeric(12,0) precio
        timestamp fecha_precio
    }
    
    precios_historicos_2025_12 {
        int id PK
        int producto_id FK
        varchar(50) retailer_id FK
        numeric(12,0) precio
        timestamp fecha_precio
    }
    
    precios_historicos_2026_01 {
        int id PK
        int producto_id FK
        varchar(50) retailer_id FK
        numeric(12,0) precio
        timestamp fecha_precio
    }
    
    precios_historicos_2026_02 {
        int id PK
        int producto_id FK
        varchar(50) retailer_id FK
        numeric(12,0) precio
        timestamp fecha_precio
    }
    
    precios_historicos_2026_03 {
        int id PK
        int producto_id FK
        varchar(50) retailer_id FK
        numeric(12,0) precio
        timestamp fecha_precio
    }
    
    precios_historicos_2026_04 {
        int id PK
        int producto_id FK
        varchar(50) retailer_id FK
        numeric(12,0) precio
        timestamp fecha_precio
    }
    
    precios_historicos_2026_05 {
        int id PK
        int producto_id FK
        varchar(50) retailer_id FK
        numeric(12,0) precio
        timestamp fecha_precio
    }
    
    precios_historicos_2026_06 {
        int id PK
        int producto_id FK
        varchar(50) retailer_id FK
        numeric(12,0) precio
        timestamp fecha_precio
    }
    
    precios_historicos_2026_07 {
        int id PK
        int producto_id FK
        varchar(50) retailer_id FK
        numeric(12,0) precio
        timestamp fecha_precio
    }
    
    precios_historicos_2026_08 {
        int id PK
        int producto_id FK
        varchar(50) retailer_id FK
        numeric(12,0) precio
        timestamp fecha_precio
    }
    
    %% Tablas del Sistema PostgreSQL
    pg_stat_statements {
        bigint userid
        bigint dbid
        bigint queryid
        text query
        bigint calls
        double total_exec_time
    }
    
    pg_stat_statements_info {
        bigint dealloc
        bigint stats_reset
    }

    %% RELACIONES
    productos_maestros ||--o{ precios_actuales : "tiene precios"
    productos_maestros ||--o{ precios_historicos : "historial precios"
    productos_maestros ||--o{ price_alerts : "alertas configuradas"
    
    categories ||--o{ productos_maestros : "categoriza"
    categories ||--o{ attributes_schema : "define atributos"
    
    retailers ||--o{ precios_actuales : "vende en"
    retailers ||--o{ precios_historicos : "historial ventas"
    retailers ||--o{ price_alerts : "alertas retailer"
    
    %% Particiones heredan de tabla principal
    precios_historicos ||--|| precios_historicos_2025_09 : "particion"
    precios_historicos ||--|| precios_historicos_2025_10 : "particion"
    precios_historicos ||--|| precios_historicos_2025_11 : "particion"
    precios_historicos ||--|| precios_historicos_2025_12 : "particion"
    precios_historicos ||--|| precios_historicos_2026_01 : "particion"
    precios_historicos ||--|| precios_historicos_2026_02 : "particion"
    precios_historicos ||--|| precios_historicos_2026_03 : "particion"
    precios_historicos ||--|| precios_historicos_2026_04 : "particion"
    precios_historicos ||--|| precios_historicos_2026_05 : "particion"
    precios_historicos ||--|| precios_historicos_2026_06 : "particion"
    precios_historicos ||--|| precios_historicos_2026_07 : "particion"
    precios_historicos ||--|| precios_historicos_2026_08 : "particion"
```

## 📋 Descripción Detallada de Tablas

### 🎯 **Tablas Core del Sistema**

#### `productos_maestros` (Tabla Principal de Productos)
- **PK:** `id` (integer, auto-increment)
- **Descripción:** Catálogo maestro de productos normalizados
- **Campos clave:**
  - `fingerprint` (varchar 64): Hash único para matching inter-retail
  - `categoria_id` (FK): Referencia a categorías
  - `atributos` (jsonb): Atributos dinámicos por categoría
- **Relaciones:** 1:N con precios_actuales, precios_historicos, price_alerts

#### `categories` (Sistema de Categorización)
- **PK:** `category_id` (varchar 50)
- **Descripción:** Taxonomía de categorías para productos
- **Campos clave:**
  - `synonyms` (text[]): Array de sinónimos para matching
  - `metadata` (jsonb): Configuración adicional
- **Relaciones:** 1:N con productos_maestros, attributes_schema

#### `attributes_schema` (Esquema de Atributos por Categoría)
- **PK:** `id` (integer)
- **FK:** `category_id` → categories
- **Descripción:** Define atributos esperados por categoría
- **Campos clave:**
  - `attribute_type` (varchar 50): Tipo de dato (string, numeric, etc.)
  - `validation_rules` (jsonb): Reglas de validación

#### `brands` (Marcas y Aliases)
- **PK:** `brand_canonical` (varchar 100)
- **Descripción:** Normalización de marcas con aliases
- **Campos clave:**
  - `aliases` (text[]): Variaciones del nombre de marca

### 💰 **Sistema de Precios**

#### `precios_actuales` (Precios Vigentes)
- **PK:** `id` (integer)
- **FK:** `producto_id` → productos_maestros, `retailer_id` → retailers
- **Descripción:** Precios actuales por retailer
- **Campos clave:**
  - `precio_actual`, `precio_oferta` (numeric 12,0): Precios en centavos
  - `metadata_adicional` (jsonb): Info de scraping

#### `precios_historicos` (Tabla Particionada por Mes)
- **PK:** `id` (integer)
- **FK:** `producto_id`, `retailer_id`
- **Descripción:** Historial completo de precios
- **Particionado:** Por mes (2025-09 a 2026-08)
- **Estrategia:** Partición range por `fecha_precio`

#### `retailers` (Información de Retailers)
- **PK:** `retailer_id` (varchar 50)
- **Descripción:** Catálogo de retailers monitoreados
- **Campos clave:**
  - `scraping_config` (jsonb): Configuración de scraping
  - `api_config` (jsonb): Configuración de APIs

### 🤖 **Sistema de IA y Cache**

#### `ai_metadata_cache` (Cache de Enriquecimiento IA)
- **PK:** `id` (integer)
- **UK:** `fingerprint` (varchar 64)
- **Descripción:** Cache de metadatos procesados por IA
- **Campos clave:**
  - `refined_attributes` (jsonb): Atributos extraídos por IA
  - `confidence` (numeric 3,2): Nivel de confianza
  - `hits`: Contador de reutilización

### 🔔 **Sistema de Alertas y Monitoreo**

#### `price_alerts` (Alertas de Precio)
- **PK:** `id` (integer)
- **FK:** `producto_id`, `retailer_id`
- **Descripción:** Alertas configurables de precios
- **Campos clave:**
  - `precio_objetivo` (numeric 12,0): Precio objetivo
  - `condition_type`: Tipo de condición (menor_que, mayor_que, etc.)

#### `processing_logs` (Logs del Sistema)
- **PK:** `id` (integer)
- **Descripción:** Auditoría de procesamiento
- **Campos clave:**
  - `process_type`: Tipo de proceso (normalize, scrape, etc.)
  - `details` (jsonb): Detalles técnicos

### ⚙️ **Configuración del Sistema**

#### `system_config` (Configuración Global)
- **PK:** `config_key` (varchar 100)
- **Descripción:** Parámetros configurables del sistema
- **Ejemplos:** timeouts, umbrales, API keys, etc.

## 🔗 Relaciones Principales

### **1:N (Uno a Muchos)**
- `productos_maestros` → `precios_actuales`
- `productos_maestros` → `precios_historicos`
- `categories` → `productos_maestros`
- `retailers` → `precios_actuales`

### **Particionamiento**
- `precios_historicos` particionada por mes (range)
- Automática creación de particiones mensuales
- Optimizada para consultas por rango de fechas

## 📊 Estadísticas y Optimización

### **Índices Principales**
- `productos_maestros.fingerprint` (UNIQUE)
- `precios_actuales(producto_id, retailer_id)` (COMPOSITE)
- `precios_historicos.fecha_precio` (RANGE para particionamiento)
- `ai_metadata_cache.fingerprint` (UNIQUE)

### **Extensiones PostgreSQL**
- `pg_stat_statements`: Monitoreo de queries
- Soporte JSONB para atributos dinámicos
- Arrays nativos para sinónimos y aliases

## 🎯 Consideraciones de Diseño

### **Escalabilidad**
- Particionamiento por tiempo en precios_historicos
- JSONB para atributos flexibles por categoría
- Cache IA con TTL implícito via hits/last_hit

### **Integridad Referencial**
- Foreign Keys entre tablas core
- Soft deletes via campo `active`
- Timestamps de auditoría automáticos

### **Performance**
- Índices optimizados para queries frecuentes
- Particionamiento automático mensual
- Cache inteligente de metadatos IA

---

**📅 Última actualización:** 2025-09-09  
**🗄️ Total tablas:** 25 (incluyendo particiones y sistema)  
**🔗 Motor:** PostgreSQL con extensiones avanzadas