# ☁️ PROMPT AVANZADO: Sistema Google Cloud SQL PostgreSQL para Análisis de Precios Retail Chileno

## 📋 CONTEXTO DEL PROYECTO

Eres un **arquitecto senior de Google Cloud SQL PostgreSQL** especializado en sistemas de análisis de precios retail de alta frecuencia en la nube. Debes diseñar e implementar una base de datos **Google Cloud SQL PostgreSQL enterprise-ready** que se integre perfectamente con un pipeline de normalización retail existente, aprovechando al máximo las características nativas de Google Cloud Platform.

## 🎯 REQUERIMIENTOS ESPECÍFICOS

### **ARQUITECTURA COMPLETA DE DATOS DEL PIPELINE**

El sistema completo incluye múltiples componentes que DEBEN ser migrados a base de datos:

#### 🎯 **PRODUCTO NORMALIZADO (Output Principal)**
```json
{
  "product_id": "abc123",
  "fingerprint": "def456",  // Hash único para matching inter-retail
  "retailer": "Paris",
  "name": "iPhone 16 Pro Max 256GB Negro", 
  "brand": "APPLE",
  "model": "iPhone 16 Pro Max 256GB",
  "category": "smartphones",
  "price_current": 1299990,  // Precio tarjeta (CLP)
  "price_original": 1469990, // Precio normal (CLP)
  "precio_oferta": null,     // Precio promocional (NUEVO)
  "currency": "CLP",
  "attributes": {"capacity": "256GB", "color": "negro", "screen_size": "6.7"},
  "ai_enhanced": true,
  "ai_confidence": 0.95,
  "processing_version": "v1.1",
  "source": {"metadata": {...}, "raw_keys": [...]}
}
```

#### 🤖 **CACHE IA (CRÍTICO - Archivo → BD)**
```json
// Actualmente: out/ai_metadata_cache.json
{
  "fingerprint_hash": {
    "brand": "APPLE",
    "model": "iPhone 16 Pro Max 256GB", 
    "refined_attributes": {
      "capacity": "256GB",
      "color": "negro",
      "screen_size": "6.7",
      "network": "5G"
    },
    "normalized_name": "iPhone 16 Pro Max 256GB Negro",
    "confidence": 0.95,
    "category_suggestion": "smartphones",
    "ai_processing_time": 1.2,
    "created_at": "2024-01-01T10:00:00Z"
  }
}
```

#### 🏷️ **TAXONOMÍAS (Archivo → BD Configurable)**
```json
// Actualmente: configs/taxonomy_v1.json
{
  "version": "1.0",
  "nodes": [
    {
      "id": "smartphones",
      "name": "Smartphones", 
      "synonyms": ["celular", "smartphone", "iphone", "android"],
      "parent_category": null,
      "attributes_schema": ["capacity", "color", "screen_size", "network"]
    }
  ]
}
```

#### 🏢 **MARCAS Y ALIASES (Archivo → BD)**
```json
// Actualmente: configs/brand_aliases.json
{
  "APPLE": ["APPLE", "Apple", "IPhone", "iPhone", "IPHONE"],
  "SAMSUNG": ["SAMSUNG", "Samsung", "Galaxy", "GALAXY"]
}
```

#### 🛍️ **RETAILERS CONFIGURACIÓN**
```json
// NUEVO: Configuración por retailer
{
  "retailers": [
    {
      "id": 1,
      "name": "Paris",
      "base_url": "https://www.paris.cl",
      "price_fields": ["card_price", "normal_price", "original_price"],
      "scraping_frequency": 6,  // veces al día
      "active": true
    }
  ]
}
```

### **REQUERIMIENTOS CRÍTICOS**

#### 🏷️ **PRECIOS - ESTRUCTURA DE 3 NIVELES** (CRÍTICO)
1. **precio_normal**: Precio regular sin descuentos
2. **precio_tarjeta**: Precio con descuento tarjeta del retailer
3. **precio_oferta**: Precio promocional especial (cyber, flash sales, etc.)

#### ⚡ **FRECUENCIA Y ESCALABILIDAD**
- **10,000 productos únicos** inicialmente (escalable a 100K+)
- **3 retailers** actuales (escalable a 10+ retailers)
- **4-8 scraping sessions/día** por retailer
- **32,000-64,000 actualizaciones de precio/día** mínimo

#### 📅 **GESTIÓN DE PRECIOS INTRA-DÍA (CRÍTICA)**

**ARQUITECTURA DE 2 TABLAS OPTIMIZADA:**

1. **`precios_actuales`** (Hot Table - 30K registros max):
   - Solo 1 registro por producto-retailer
   - UPDATE únicamente si precio cambia (no por scraping)
   - Contador de cambios intra-día
   - Precio anterior para cálculo de % cambio

2. **`precios_historicos`** (Partitioned Archive - Millones de registros):
   - Snapshot diario automático a las 23:59 hora Chile
   - Particionado mensual nativo Google Cloud SQL
   - Retención histórica completa (años)

**FLUJO INTRA-DÍA:**
```sql
-- 1. CHECK cambio (no UPDATE si precio igual)
-- 2. UPDATE solo 3 precios que cambiaron
-- 3. INCREMENT contador cambios_hoy
-- 4. TRIGGER automático para alertas
-- 5. SNAPSHOT nocturno vía Cloud Scheduler
```

#### 🚨 **SISTEMA DE ALERTAS INTELIGENTE**
- **Alertas por producto individual** con umbrales configurables
- **Detección cambios intra-día** (tiempo real)
- **Análisis de tendencias históricas**
- **Configuración flexible por categoría/marca/retailer**

### **CASOS DE USO PRINCIPALES**

1. **Comparación de precios inter-retail en tiempo real**
2. **Análisis histórico de tendencias de precios**
3. **Alertas automáticas de cambios de precios significativos** 
4. **Matching de productos entre retailers usando fingerprints**
5. **Reportes de competencia y posicionamiento de precios**
6. **Detección de patrones promocionales**

### **CONSTRAINTS TÉCNICOS GOOGLE CLOUD**

- **Google Cloud SQL PostgreSQL 15+** con flags y extensiones optimizadas
- **Alta concurrencia**: Múltiples scrapers desde diferentes regiones escribiendo simultáneamente
- **Read replicas** para consultas analíticas sin afectar escrituras principales
- **Cloud SQL Proxy** para conexiones seguras desde el pipeline
- **Backup automático** y **point-in-time recovery** nativos de Google Cloud
- **Monitoring con Cloud Monitoring** integrado
- **Alertas Cloud Functions** para notificaciones en tiempo real
- **Índices optimizados** para consultas temporales y por fingerprint
- **Connection pooling** con PgBouncer integrado
- **Escalado automático** de compute y storage

## 🏗️ DELIVERABLES ESPERADOS

### **1. CONFIGURACIÓN GOOGLE CLOUD SQL OPTIMIZADA**
- **Instance specs** recomendadas (CPU, RAM, SSD) para el workload
- **Database flags** específicas para alta frecuencia de escritura
- **Network configuration** con Cloud SQL Proxy
- **Read replica** configurada para analytics
- **Connection pooling** con PgBouncer integrado

### **2. ESQUEMA DE BASE DE DATOS COMPLETO**

#### 🗄️ **TABLAS PRINCIPALES REQUERIDAS**
1. **`productos_maestros`** - Registro único por fingerprint con atributos consolidados
2. **`precios_actuales`** - Precios vigentes intra-día (3 tipos: normal, tarjeta, oferta)
3. **`precios_historicos`** - Snapshots diarios particionados por mes
4. **`ai_metadata_cache`** - Cache indefinido de metadatos IA por fingerprint
5. **`categories`** - Taxonomías configurables con sinónimos dinámicos
6. **`brands`** - Marcas maestras con aliases múltiples
7. **`retailers`** - Configuración de retailers y sus patrones de scraping
8. **`attributes_schema`** - Esquemas de atributos por categoría
9. **`price_alerts`** - Configuración y log de alertas por producto
10. **`processing_logs`** - Auditoría completa del pipeline
11. **`system_config`** - Configuraciones dinámicas del sistema

#### 🔧 **REQUERIMIENTOS TÉCNICOS**
- DDL completo con todas las tablas, índices, constraints
- **Particionado nativo Google Cloud SQL** por meses automático
- Triggers para gestión de datos históricos y cache IA
- Funciones almacenadas para migración de archivos JSON existentes
- **Extensiones específicas** habilitadas (pg_stat_statements, btree_gin, etc.)
- **JSONB** optimizado para atributos dinámicos y metadatos IA

### **3. SISTEMA DE ALERTAS CLOUD-NATIVE**
- Tabla de configuración de alertas por producto/categoría
- **Cloud Functions** para procesamiento de alertas en tiempo real
- **Pub/Sub integration** para notificaciones asíncronas
- **Cloud Monitoring** custom metrics para umbrales
- **Cloud Scheduler** para snapshots diarios automáticos

### **4. MÓDULO DE INTEGRACIÓN PYTHON CLOUD-OPTIMIZED**

#### 📦 **MIGRACIÓN DE ARCHIVOS EXISTENTES**
- **Función de migración** `configs/taxonomy_v1.json` → tabla `categories`
- **Función de migración** `configs/brand_aliases.json` → tabla `brands`
- **Función de migración** `out/ai_metadata_cache.json` → tabla `ai_metadata_cache`
- **Preservar data integrity** durante migración
- **Rollback automático** en caso de errores

#### 🔧 **CONECTOR PRINCIPAL**
- Clase `CloudSQLConnector` con **Cloud SQL Proxy** integrado
- **Service Account** authentication automática
- Funciones de inserción masiva optimizadas para Cloud SQL
- **Connection pooling** con SQLAlchemy + Cloud SQL Python Connector
- **Retry logic** con exponential backoff para resilencia

#### 🤖 **INTEGRACIÓN CACHE IA**
- **Función `get_ai_cache(fingerprint)`** que consulte BD en lugar de archivo
- **Función `set_ai_cache(fingerprint, metadata)`** que escriba a BD
- **Compatibilidad** con TTL indefinido existente
- **Métricas** de hit/miss ratio del cache IA

### **5. OPTIMIZACIONES GOOGLE CLOUD ESPECÍFICAS**
- **Cloud SQL Insights** configurado para query optimization
- **Automatic storage increase** configurado
- **High availability** con failover automático
- **Point-in-time recovery** configurado
- **Cloud SQL Auth proxy** deployment guides

### **6. QUERIES DE ANÁLISIS ESENCIALES PARA RETAIL**

#### 🔍 **CONSULTAS CRÍTICAS QUE DEBE OPTIMIZAR**
1. **Comparación precios inter-retail** por fingerprint único
2. **Evolución histórica** de precios con percentiles y tendencias
3. **Rankings competitividad** por categoría y marca
4. **Detección sincronización** de precios entre retailers
5. **Análisis cache IA** - productos más procesados, calidad de confianza
6. **Performance categorización** - precisión por taxonomía
7. **Alertas dashboard** - cambios significativos en tiempo real
8. **Métricas pipeline** - throughput, errores, tiempos procesamiento

### **7. MONITORING Y OBSERVABILIDAD**
- **Cloud Monitoring dashboards** para métricas de base de datos
- **Cloud Logging** estructurado para auditoría completa del pipeline
- **Alertas Cloud Monitoring** para performance issues y cache IA
- **Cloud Trace** integration para query performance
- **Error Reporting** para exceptions del pipeline y migración
- **Custom metrics** para calidad de datos IA y precisión categorización

## 📊 CONSIDERACIONES ESPECIALES PARA RETAIL CHILENO

- **Moneda CLP**: Precios como integers (sin decimales)
- **Retailers chilenos**: Paris, Ripley, Falabella, etc.
- **Categorías**: Smartphones, notebooks, smart TV, perfumes
- **Eventos especiales**: CyberDay, Hot Sale, Black Friday
- **Horarios comerciales**: Considerar zonas horarias Chile

## 🔧 INTEGRACIÓN COMPLETA CON PIPELINE EXISTENTE

### **📁 MODIFICACIONES REQUERIDAS AL PIPELINE**

#### **NUEVOS MÓDULOS PRINCIPALES**
- **`src/database.py`** - Conector principal Google Cloud SQL
- **`src/migrations.py`** - Migración de archivos JSON existentes  
- **`src/cache_db.py`** - Reemplazo de cache IA basado en archivos

#### **MODIFICACIONES A MÓDULOS EXISTENTES**
- **`src/normalize.py`** - Integrar consultas BD para cache IA
- **`src/categorize.py`** - Consultar taxonomías desde BD en lugar de archivo
- **`src/enrich.py`** - Consultar marcas y aliases desde BD
- **`src/cli.py`** - Nuevos comandos para gestión BD y migración

#### **CONFIGURACIÓN EXTENDIDA**
```toml
# config.local.toml - NUEVAS SECCIONES CRÍTICAS
[database]
provider = "google_cloud_sql"
instance_connection_name = "project:region:instance"
database_name = "retail_prices"
use_cloud_sql_proxy = true

[migration]
migrate_on_startup = false
backup_json_files = true
validate_migration = true

[cache_ia_db]
enabled = true
fallback_to_file = false
metrics_enabled = true
```

#### **COMPATIBILIDAD Y MIGRACIÓN CRÍTICA**
- **Mantener output JSONL** existente intacto durante transición
- **Fase de migración gradual** sin interrumpir pipeline activo
- **Fallback automático** a archivos JSON si BD no disponible
- **Comandos de rollback** para revertir a archivos JSON
- **Validación de integridad** post-migración automática

## ☁️ CONFIGURACIÓN ESPECÍFICA GOOGLE CLOUD

### **SPECS DE INSTANCIA RECOMENDADAS**
```yaml
# Para 64K updates/día iniciales
machine_type: db-custom-4-26624  # 4 vCPUs, 26GB RAM
storage_type: SSD
storage_size: 100GB (auto-resize enabled)
availability_type: REGIONAL  # HA para producción
backup_enabled: true
point_in_time_recovery: true
```

### **FLAGS CRÍTICAS PARA ALTA FRECUENCIA**
```yaml
database_flags:
  - name: shared_preload_libraries
    value: "pg_stat_statements,auto_explain"
  - name: max_connections
    value: "200"
  - name: shared_buffers
    value: "6GB"  # ~25% de RAM
  - name: effective_cache_size
    value: "20GB"  # ~75% de RAM
  - name: wal_buffers
    value: "64MB"
  - name: checkpoint_completion_target
    value: "0.9"
  - name: log_min_duration_statement
    value: "1000"  # Log queries >1s
```

### **INTEGRACIÓN TIMEZONE CHILE**
```sql
-- Configuración timezone para snapshots 23:59 Chile
ALTER DATABASE retail_prices SET timezone = 'America/Santiago';
```

## 💡 INSTRUCCIONES FINALES

**Prioriza (Google Cloud Specific)**:
1. **Cloud-native patterns** sobre soluciones on-premise
2. **Managed services integration** (Cloud Functions, Pub/Sub, Scheduler)
3. **Auto-scaling capabilities** y **cost optimization**
4. **Security best practices** con IAM y Service Accounts
5. **Observabilidad completa** con stack Google Cloud

**Incluye**:
- **Terraform/gcloud** commands para deployment
- **Service Account permissions** mínimas necesarias
- **Cloud SQL Proxy** setup detallado
- **Cost estimation** para diferentes cargas de trabajo
- **Disaster recovery** procedures específicas Google Cloud
- **Performance tuning** específico para Cloud SQL flags

**Genera una solución cloud-native COMPLETA que incluya:**

#### 🎯 **MIGRACIÓN TOTAL DEL SISTEMA**
1. **11 tablas principales** con esquemas completos y optimizados
2. **Migración automatizada** de todos los archivos JSON existentes:
   - `configs/taxonomy_v1.json` → `categories` table
   - `configs/brand_aliases.json` → `brands` table  
   - `out/ai_metadata_cache.json` → `ai_metadata_cache` table
3. **Modificaciones** a 4 módulos Python existentes para usar BD
4. **3 nuevos módulos** Python para conectividad y migración
5. **Configuración completa** Google Cloud SQL con specs exactas

#### 🚀 **SISTEMA ENTERPRISE-READY**
- Escalable de 10K a 1M+ productos con costos controlados
- **Cache IA indefinido** migrado completamente a BD
- **3 tipos de precios** (normal, tarjeta, oferta) con gestión intra-día
- **Alertas tiempo real** integradas con Google Cloud
- **Particionado mensual** automático para datos históricos
- **Observabilidad completa** y monitoreo proactivo

---

*Este prompt está diseñado para generar una migración COMPLETA del pipeline retail chileno desde archivos JSON a Google Cloud SQL PostgreSQL enterprise-ready, sin perder NINGUNA funcionalidad existente y agregando capacidades avanzadas de análisis y alertas.*