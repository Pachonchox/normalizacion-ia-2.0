# 📘 GUÍA COMPLETA DE USO - Sistema Normalización IA 2.0

Sistema integral de normalización de productos retail con IA, PostgreSQL y scrapers automáticos.

## 🏗️ ARQUITECTURA DEL SISTEMA

```
📦 Normalización IA 2.0
├── 🕷️ Scrapers (Independientes)     # Extracción de datos
├── 🧠 Normalización con IA          # Procesamiento inteligente  
├── 🗄️ Base de Datos PostgreSQL     # Persistencia y cache
├── 📊 Sistema de Auditoría          # Monitoreo y métricas
└── 🔒 Configuración Segura          # Gestión de credenciales
```

## 📋 TABLA DE CONTENIDOS

1. [Configuración Inicial](#1-configuración-inicial)
2. [Sistema de Scrapers](#2-sistema-de-scrapers)
3. [Normalización con IA](#3-normalización-con-ia)
4. [Base de Datos](#4-base-de-datos)
5. [Flujo Completo E2E](#5-flujo-completo-e2e)
6. [Monitoreo y Auditoría](#6-monitoreo-y-auditoría)
7. [Mantenimiento](#7-mantenimiento)
8. [Solución de Problemas](#8-solución-de-problemas)

---

## 1. CONFIGURACIÓN INICIAL

### 1.1 Instalación de Dependencias

```bash
# Dependencias principales
pip install -r requirements.txt

# Dependencias de scrapers
cd Scrappers
pip install -r requirements.txt
```

### 1.2 Configuración de Variables de Entorno

```bash
# Copiar plantilla de configuración
cp .env.example .env
```

**Editar `.env` con tus credenciales:**

```bash
# Base de Datos PostgreSQL
DB_HOST=tu-host-postgresql
DB_PORT=5432
DB_NAME=postgres
DB_USER=tu-usuario
DB_PASSWORD=tu-password-seguro
DB_POOL_SIZE=5

# OpenAI
OPENAI_API_KEY=sk-proj-tu-nueva-key-aqui
LLM_ENABLED=true
OPENAI_MODEL=gpt-4o-mini

# Configuraciones adicionales
DEBUG=false
ENVIRONMENT=production
```

### 1.3 Verificación de Conexiones

```bash
# Verificar conexión a PostgreSQL
python test_simple_connection.py

# Verificar conexión OpenAI
python -c "from src.config_manager import get_config; print('✅ Configuración válida')"
```

---

## 2. SISTEMA DE SCRAPERS

### 2.1 Configuración de Scrapers

Los scrapers están **configurados automáticamente** a 10 páginas cada uno y son **completamente independientes**.

```bash
cd Scrappers
```

### 2.2 Modos de Ejecución

#### 🔄 Ciclo Único (Recomendado para inicio)
```bash
# Ejecutar todos los scrapers una vez, intercalado
python scraper_orchestrator.py
```

#### 🔁 Modo Continuo
```bash
# Ejecutar de forma continua (infinito)
python scraper_orchestrator.py --mode continuous

# Ejecutar con límite de ciclos
python scraper_orchestrator.py --mode continuous --max-cycles 3
```

#### 🎯 Scrapers Individuales
```bash
# Solo Ripley (ultra stealth)
python scraper_orchestrator.py --scraper ripley

# Solo Falabella
python scraper_orchestrator.py --scraper falabella

# Solo Paris
python scraper_orchestrator.py --scraper paris
```

#### 📊 Monitoreo de Scrapers
```bash
# Ver estado actual
python scraper_orchestrator.py --mode status

# Ver logs en tiempo real
tail -f ../data/logs/orchestrator.log

# Ver archivos generados
ls -la ../data/*/
```

### 2.3 Salida de Scrapers

**Ubicación de datos:**
- `data/ripley/` - Productos de Ripley
- `data/falabella/` - Productos de Falabella  
- `data/paris/` - Productos de Paris
- `data/logs/` - Logs del orquestador

**Formato de archivos:**
```json
{
  "metadata": {
    "scraped_at": "2025-09-09 06:45:00",
    "search_term": "celulares",
    "total_products": 240,
    "pages_scraped": 10,
    "retailer": "ripley"
  },
  "products": [
    {
      "name": "iPhone 15 Pro 128GB",
      "brand": "Apple",
      "price": "$899990",
      "url": "https://...",
      "page_scraped": 1
    }
  ]
}
```

---

## 3. NORMALIZACIÓN CON IA

### 3.1 Sistemas de Normalización

#### 🧠 Normalización Integrada (Recomendado)
```bash
cd src

# Normalizar archivo específico
python normalize_integrated.py --file ../data/ripley/ultra_celulares_c001_2025-09-09.json

# Normalizar productos de un retailer
python cli_integrated.py normalize --retailer ripley --input-dir ../data/ripley/

# Normalizar todo (todos los retailers)
python cli_integrated.py normalize --input-dir ../data/ --recursive
```

#### 📊 CLI Completo
```bash
# Ver comandos disponibles
python cli_integrated.py --help

# Normalizar con configuración específica
python cli_integrated.py normalize \
  --retailer ripley \
  --input-dir ../data/ripley/ \
  --batch-size 50

# Ver estadísticas tras normalización
python cli_integrated.py stats
```

### 3.2 Flujo de Normalización

```
📥 Datos Raw (JSON) 
    ↓
🏷️ Categorización (BD + IA)
    ↓
🧠 Enriquecimiento IA (con cache indefinido)
    ↓
🔍 Generación de Fingerprint
    ↓
💾 Persistencia en PostgreSQL
    ↓
📊 Productos Normalizados
```

### 3.3 Características de la IA

- **Cache Indefinido**: Una vez procesado, nunca se vuelve a consultar IA
- **GPT-4o-mini**: Modelo optimizado para extracción de atributos
- **Fingerprinting**: Matching inteligente de productos duplicados
- **Confianza**: Score de confianza por cada enriquecimiento

---

## 4. BASE DE DATOS

### 4.1 Estructura de Tablas

**Principales:**
- `productos_maestros` - Productos únicos normalizados
- `precios_actuales` - Precios actuales por retailer
- `precios_historicos` - Historial de precios
- `ai_metadata_cache` - Cache de enriquecimientos IA

**Configuración:**
- `categories` - Taxonomía de categorías
- `brands` - Marcas y aliases
- `retailers` - Retailers activos
- `attributes_schema` - Esquemas de atributos

**Control:**
- `processing_logs` - Logs de procesamiento
- `price_alerts` - Alertas de cambios de precio

### 4.2 Acceso a Datos

#### 🔍 Consultas Básicas
```sql
-- Productos más recientes
SELECT * FROM productos_maestros 
WHERE ai_enhanced = true 
ORDER BY created_at DESC 
LIMIT 10;

-- Precios por retailer
SELECT pm.name, pm.brand, pa.precio_normal, pa.precio_tarjeta, r.name as retailer
FROM productos_maestros pm
JOIN precios_actuales pa ON pm.fingerprint = pa.fingerprint
JOIN retailers r ON pa.retailer_id = r.id
WHERE pm.category = 'celulares'
ORDER BY pa.precio_tarjeta ASC;
```

#### 📊 Script de Auditoría
```bash
cd src
python db_audit_simple.py
```

**Output ejemplo:**
```
=== AUDITORIA COMPLETA BASE DE DATOS ===
Total productos maestros: 37
Total precios actuales: 37  
Total cache IA: 37
Productos con IA: 37/37 (100.0%)
Score de salud: 100%
Estado: EXCELENTE
```

---

## 5. FLUJO COMPLETO E2E

### 5.1 Proceso Completo Automatizado

```bash
# 1. Ejecutar scrapers (obtener datos raw)
cd Scrappers
python scraper_orchestrator.py

# 2. Normalizar todos los datos obtenidos
cd ../src
python cli_integrated.py normalize --input-dir ../data/ --recursive

# 3. Auditar resultados
python db_audit_simple.py

# 4. Ver estadísticas
python cli_integrated.py stats
```

### 5.2 Pipeline Automático (Script Completo)

```bash
# Crear script de pipeline completo
cat > pipeline_completo.sh << 'EOF'
#!/bin/bash
echo "🚀 INICIANDO PIPELINE COMPLETO"

# 1. Scrapers
echo "📥 Ejecutando scrapers..."
cd Scrappers
python scraper_orchestrator.py

# 2. Normalización  
echo "🧠 Normalizando productos..."
cd ../src
python cli_integrated.py normalize --input-dir ../data/ --recursive

# 3. Auditoría
echo "📊 Auditando resultados..."
python db_audit_simple.py

echo "✅ PIPELINE COMPLETADO"
EOF

chmod +x pipeline_completo.sh
./pipeline_completo.sh
```

### 5.3 Monitoreo del Pipeline

```bash
# Ver progreso de normalización
tail -f out/processing.log

# Ver estado de base de datos en tiempo real
watch -n 30 'cd src && python -c "from unified_connector import get_unified_connector; c=get_unified_connector(); stats=c.get_processing_stats(); print(f\"Productos: {stats['productos_maestros']}, Precios: {stats['precios_actuales']}, Cache IA: {stats['cache_ia']}\")"'
```

---

## 6. MONITOREO Y AUDITORÍA

### 6.1 Auditoría de Base de Datos

```bash
cd src
python db_audit_simple.py
```

**Indicadores clave:**
- ✅ **Health Score 100%**: Sistema perfecto
- ⚠️ **Health Score 80-99%**: Atención menor requerida  
- ❌ **Health Score <80%**: Requiere intervención

### 6.2 Análisis de Cache IA

```bash
# Verificar discrepancias en cache
python analyze_cache_discrepancy.py
```

### 6.3 Estadísticas de Procesamiento

```bash
# Stats desde CLI
python cli_integrated.py stats

# Stats detalladas
python -c "
from unified_connector import get_unified_connector
c = get_unified_connector()
stats = c.get_processing_stats()
print('📊 ESTADÍSTICAS:')
print(f'Productos maestros: {stats['productos_maestros']}')
print(f'Precios actuales: {stats['precios_actuales']}') 
print(f'Cache IA: {stats['cache_ia']}')
"
```

---

## 7. MANTENIMIENTO

### 7.1 Limpieza de Datos

```bash
# Limpiar archivos temporales
find data/ -name "*.tmp" -delete
find out/ -name "*.log" -older +7d -delete

# Verificar integridad BD
cd src
python -c "
from unified_connector import get_unified_connector
c = get_unified_connector()
# Ejecutar verificaciones de integridad
"
```

### 7.2 Optimización de Performance

```bash
# Verificar uso de conexiones
python -c "
from config_manager import get_config
config = get_config()
print(f'Pool size configurado: {config.database.pool_size}')
"

# Monitorear memoria
ps aux | grep python | grep normalize
```

### 7.3 Backup y Restore

```bash
# Backup de configuraciones
tar -czf backup_configs_$(date +%Y%m%d).tar.gz configs/ .env.example

# Backup de datos procesados
tar -czf backup_data_$(date +%Y%m%d).tar.gz data/ out/
```

---

## 8. SOLUCIÓN DE PROBLEMAS

### 8.1 Problemas Comunes

#### 🚫 Error de Conexión a PostgreSQL
```bash
# Verificar credenciales
python -c "from config_manager import get_config; c = get_config(); print('DB Host:', c.database.host)"

# Test de conexión
python test_simple_connection.py
```

#### 🤖 Error de OpenAI API
```bash
# Verificar API key
python -c "from config_manager import get_config; c = get_config(); print('API Key válida:', len(c.openai.api_key) > 20)"

# Test de IA
python -c "from llm_connectors import enabled; print('IA habilitada:', enabled())"
```

#### 📂 Archivos no encontrados
```bash
# Verificar estructura
ls -la data/*/
ls -la Scrappers/
ls -la src/
```

### 8.2 Logs de Debug

```bash
# Habilitar debug
export DEBUG=true

# Ver logs detallados
tail -f data/logs/*.log
tail -f out/*.log
```

### 8.3 Reset Completo

```bash
# CUIDADO: Esto borra todo el cache y datos
rm -rf data/*/
rm -rf out/
python -c "
from unified_connector import get_unified_connector
c = get_unified_connector()
c.execute_update('TRUNCATE TABLE ai_metadata_cache CASCADE')
print('✅ Cache IA limpiado')
"
```

---

## 🎯 MEJORES PRÁCTICAS

### ✅ DO (Hacer)

1. **Ejecutar auditoría** después de cada normalización masiva
2. **Monitorear health score** regularmente
3. **Usar modo single cycle** para tests iniciales
4. **Verificar .env** antes de producción
5. **Backup regular** de configuraciones

### ❌ DON'T (No hacer)

1. **No commitear** archivos .env al repositorio
2. **No ejecutar** scrapers en modo continuo sin monitoreo
3. **No modificar** directamente los archivos de cache
4. **No usar** credenciales hardcodeadas
5. **No ignorar** alertas de health score bajo

---

## 📞 SOPORTE

Para problemas o mejoras:
1. Revisar logs en `data/logs/` y `out/`
2. Ejecutar auditoría: `python db_audit_simple.py`
3. Verificar configuración: `python -c "from config_manager import get_config; print('✅ Config válida')"`
4. Consultar esta guía y la [Guía SQL](GUIA_SQL_CONSULTAS.md)

---

**Sistema desarrollado con ❤️ y 🤖 por Claude Code**