# 🎯 EJEMPLOS PRÁCTICOS - Sistema Normalización IA 2.0

Ejemplos reales de uso del sistema con casos de negocio específicos y comandos ejecutables.

## 📋 CASOS DE USO REALES

### 1. 🏪 ANÁLISIS COMPETITIVO DE PRECIOS

**Escenario**: Comparar precios de iPhone entre retailers para encontrar mejores oportunidades.

```bash
# 1. Scrapear datos de todos los retailers
cd Scrappers
python scraper_orchestrator.py

# 2. Normalizar datos obtenidos
cd ../src
python cli_integrated.py normalize --input-dir ../data/ --recursive

# 3. Consultar precios de iPhones
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
SELECT 
    pm.name,
    r.name as retailer,
    pa.precio_normal,
    pa.precio_tarjeta,
    ROUND((pa.precio_normal - pa.precio_tarjeta)::numeric * 100 / pa.precio_normal, 1) as descuento_pct
FROM productos_maestros pm
JOIN precios_actuales pa ON pm.fingerprint = pa.fingerprint
JOIN retailers r ON pa.retailer_id = r.id
WHERE pm.name ILIKE '%iphone%'
  AND pm.active = true
ORDER BY pm.name, pa.precio_tarjeta;
"
```

**Resultado esperado:**
```
         name          | retailer  | precio_normal | precio_tarjeta | descuento_pct
-----------------------+-----------+---------------+----------------+---------------
iPhone 15 Pro 128GB   | Ripley    |    1299990    |    1199990     |     7.7
iPhone 15 Pro 128GB   | Falabella |    1299990    |    1249990     |     3.8
iPhone 15 Pro 128GB   | Paris     |    1299990    |    1179990     |     9.2
```

### 2. 📊 MONITOREO DIARIO DE INVENTARIO

**Escenario**: Dashboard diario para revisar el estado del sistema.

```bash
# Script de monitoreo diario
cat > monitoreo_diario.sh << 'EOF'
#!/bin/bash
echo "📊 DASHBOARD DIARIO - $(date)"
echo "================================"

cd src

echo "🏥 HEALTH CHECK:"
python db_audit_simple.py | grep -E "(Health Score|Estado|Total)"

echo ""
echo "📈 ESTADÍSTICAS RÁPIDAS:"
python -c "
from unified_connector import get_unified_connector
c = get_unified_connector()
stats = c.get_processing_stats()
print(f'✅ Productos: {stats[\"productos_maestros\"]}')
print(f'💰 Precios: {stats[\"precios_actuales\"]}') 
print(f'🤖 Cache IA: {stats[\"cache_ia\"]}')
"

echo ""
echo "🕷️ SCRAPERS HOY:"
find ../data -name "*.json" -newermt "$(date +%Y-%m-%d)" | wc -l | xargs echo "Archivos nuevos:"

echo ""
echo "🔍 TOP 5 PRODUCTOS MÁS CAROS HOY:"
python -c "
from unified_connector import get_unified_connector
c = get_unified_connector()
results = c.execute_query('''
    SELECT pm.name, pm.brand, pa.precio_tarjeta, r.name as retailer
    FROM productos_maestros pm
    JOIN precios_actuales pa ON pm.fingerprint = pa.fingerprint
    JOIN retailers r ON pa.retailer_id = r.id
    WHERE pm.active = true
    ORDER BY pa.precio_tarjeta DESC
    LIMIT 5
''')
for r in results:
    print(f'💎 {r[\"name\"][:30]}... - ${r[\"precio_tarjeta\"]:,} ({r[\"retailer\"]})')
"

EOF

chmod +x monitoreo_diario.sh
./monitoreo_diario.sh
```

### 3. 🎯 BÚSQUEDA DE OPORTUNIDADES DE ARBITRAJE

**Escenario**: Encontrar productos con grandes diferencias de precio entre retailers.

```bash
# Ejecutar análisis de oportunidades
cd src
python -c "
from unified_connector import get_unified_connector
import json

c = get_unified_connector()

# Productos con mayor diferencia de precio
query = '''
WITH precio_stats AS (
    SELECT 
        pm.fingerprint,
        pm.name,
        pm.brand,
        MIN(pa.precio_tarjeta) as precio_min,
        MAX(pa.precio_tarjeta) as precio_max,
        COUNT(DISTINCT pa.retailer_id) as num_retailers
    FROM productos_maestros pm
    JOIN precios_actuales pa ON pm.fingerprint = pa.fingerprint
    WHERE pm.active = true AND pa.precio_tarjeta > 0
    GROUP BY pm.fingerprint, pm.name, pm.brand
    HAVING COUNT(DISTINCT pa.retailer_id) > 1
)
SELECT 
    name,
    brand,
    precio_min,
    precio_max,
    (precio_max - precio_min) as diferencia,
    ROUND((precio_max - precio_min)::numeric * 100 / precio_min, 1) as diferencia_pct,
    num_retailers
FROM precio_stats
WHERE precio_max > precio_min
ORDER BY diferencia_pct DESC
LIMIT 10;
'''

results = c.execute_query(query)
print('🚀 TOP 10 OPORTUNIDADES DE ARBITRAJE:')
print('=' * 50)
for i, r in enumerate(results, 1):
    print(f'{i:2d}. {r[\"name\"][:40]}')
    print(f'    Marca: {r[\"brand\"]}')
    print(f'    Rango: ${r[\"precio_min\"]:,} - ${r[\"precio_max\"]:,}')
    print(f'    Diferencia: ${r[\"diferencia\"]:,} ({r[\"diferencia_pct\"]}%)')
    print(f'    Retailers: {r[\"num_retailers\"]}')
    print()
"
```

### 4. 🔄 PIPELINE AUTOMÁTICO CON CRON

**Escenario**: Automatizar scrapers y normalización cada 6 horas.

```bash
# 1. Crear script automatizado
cat > auto_pipeline.sh << 'EOF'
#!/bin/bash
LOG_DIR="/path/to/normalizacion/data/logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M")

echo "🤖 AUTO PIPELINE - $TIMESTAMP" >> "$LOG_DIR/auto_pipeline.log"

cd /path/to/normalizacion/Scrappers
timeout 3600 python scraper_orchestrator.py >> "$LOG_DIR/auto_pipeline.log" 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Scrapers OK" >> "$LOG_DIR/auto_pipeline.log"
    
    cd ../src
    python cli_integrated.py normalize --input-dir ../data/ --recursive >> "$LOG_DIR/auto_pipeline.log" 2>&1
    
    if [ $? -eq 0 ]; then
        echo "✅ Normalización OK" >> "$LOG_DIR/auto_pipeline.log"
        python db_audit_simple.py >> "$LOG_DIR/auto_pipeline.log" 2>&1
    else
        echo "❌ Error normalización" >> "$LOG_DIR/auto_pipeline.log"
    fi
else
    echo "❌ Error scrapers" >> "$LOG_DIR/auto_pipeline.log"
fi

echo "🏁 Fin pipeline - $(date)" >> "$LOG_DIR/auto_pipeline.log"
EOF

chmod +x auto_pipeline.sh

# 2. Configurar cron (ejecutar cada 6 horas)
echo "0 */6 * * * /path/to/auto_pipeline.sh" | crontab -

# 3. Verificar cron
crontab -l
```

### 5. 📈 ANÁLISIS DE TENDENCIAS DE PRECIOS

**Escenario**: Analizar cómo han cambiado los precios en los últimos días.

```bash
cd src
python -c "
from unified_connector import get_unified_connector
from datetime import datetime, timedelta

c = get_unified_connector()

# Productos procesados por día (últimos 7 días)
query = '''
SELECT 
    DATE(created_at) as fecha,
    COUNT(*) as productos,
    COUNT(CASE WHEN ai_enhanced THEN 1 END) as con_ia,
    ROUND(AVG(CASE WHEN ai_enhanced THEN ai_confidence END)::numeric, 3) as confianza_promedio
FROM productos_maestros
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
  AND active = true
GROUP BY DATE(created_at)
ORDER BY fecha DESC;
'''

results = c.execute_query(query)
print('📅 ACTIVIDAD ÚLTIMOS 7 DÍAS:')
print('=' * 50)
print('Fecha       | Productos | Con IA | Confianza IA')
print('-' * 50)
for r in results:
    fecha = r['fecha'].strftime('%Y-%m-%d')
    productos = r['productos']
    con_ia = r['con_ia'] or 0
    confianza = r['confianza_promedio'] or 0
    print(f'{fecha} |    {productos:4d}   | {con_ia:4d}   |   {confianza:.3f}')

# Top marcas más procesadas
print('\n🏷️ TOP MARCAS PROCESADAS:')
print('=' * 30)
query2 = '''
SELECT brand, COUNT(*) as cantidad
FROM productos_maestros 
WHERE active = true AND brand != 'DESCONOCIDA'
GROUP BY brand 
ORDER BY cantidad DESC 
LIMIT 10;
'''

results2 = c.execute_query(query2)
for r in results2:
    print(f'{r[\"brand\"]:15s}: {r[\"cantidad\"]:3d} productos')
"
```

### 6. 🛒 ANÁLISIS ESPECÍFICO POR RETAILER

**Escenario**: Analizar el catálogo y precios de un retailer específico.

```bash
# Función de análisis por retailer
analyze_retailer() {
    RETAILER=$1
    echo "🔍 ANÁLISIS DE $RETAILER"
    echo "========================"
    
    cd src
    python -c "
retailer = '$RETAILER'
from unified_connector import get_unified_connector
c = get_unified_connector()

# Estadísticas generales
query = '''
SELECT 
    COUNT(*) as productos,
    COUNT(DISTINCT pm.category) as categorias,
    COUNT(DISTINCT pm.brand) as marcas,
    ROUND(AVG(pa.precio_tarjeta)::numeric, 0) as precio_promedio,
    MIN(pa.precio_tarjeta) as precio_min,
    MAX(pa.precio_tarjeta) as precio_max
FROM precios_actuales pa
JOIN retailers r ON pa.retailer_id = r.id
JOIN productos_maestros pm ON pa.fingerprint = pm.fingerprint
WHERE r.name = %s AND pm.active = true;
'''

result = c.execute_query(query, {'retailer': retailer})[0]
print(f'📊 ESTADÍSTICAS GENERALES:')
print(f'   Productos: {result[\"productos\"]}')
print(f'   Categorías: {result[\"categorias\"]}')
print(f'   Marcas: {result[\"marcas\"]}')
print(f'   Precio promedio: \${result[\"precio_promedio\"]:,}')
print(f'   Rango: \${result[\"precio_min\"]:,} - \${result[\"precio_max\"]:,}')

# Top categorías
print(f'\n🏷️ TOP CATEGORÍAS EN {retailer}:')
query2 = '''
SELECT pm.category, COUNT(*) as productos,
       ROUND(AVG(pa.precio_tarjeta)::numeric, 0) as precio_prom
FROM precios_actuales pa
JOIN retailers r ON pa.retailer_id = r.id  
JOIN productos_maestros pm ON pa.fingerprint = pm.fingerprint
WHERE r.name = %s AND pm.active = true
GROUP BY pm.category
ORDER BY productos DESC
LIMIT 5;
'''

results2 = c.execute_query(query2, {'retailer': retailer})
for r in results2:
    print(f'   {r[\"category\"]:15s}: {r[\"productos\"]:3d} productos (prom: \${r[\"precio_prom\"]:,})')
"
}

# Usar la función
analyze_retailer "Ripley"
analyze_retailer "Falabella" 
analyze_retailer "Paris"
```

### 7. 🤖 ANÁLISIS DE CALIDAD DE IA

**Escenario**: Evaluar qué tan bien está funcionando el enriquecimiento con IA.

```bash
cd src
python -c "
from unified_connector import get_unified_connector
c = get_unified_connector()

print('🤖 ANÁLISIS DE CALIDAD IA')
print('=' * 30)

# Estadísticas generales de IA
query = '''
SELECT 
    COUNT(*) as total,
    COUNT(CASE WHEN ai_enhanced THEN 1 END) as con_ia,
    ROUND(COUNT(CASE WHEN ai_enhanced THEN 1 END)::numeric * 100 / COUNT(*), 1) as cobertura_pct,
    ROUND(AVG(CASE WHEN ai_enhanced THEN ai_confidence END)::numeric, 3) as confianza_prom,
    COUNT(CASE WHEN ai_confidence >= 0.9 THEN 1 END) as alta_confianza,
    COUNT(CASE WHEN ai_confidence < 0.7 THEN 1 END) as baja_confianza
FROM productos_maestros WHERE active = true;
'''

result = c.execute_query(query)[0]
print(f'📊 COBERTURA IA:')
print(f'   Total productos: {result[\"total\"]}')
print(f'   Con IA: {result[\"con_ia\"]} ({result[\"cobertura_pct\"]}%)')
print(f'   Confianza promedio: {result[\"confianza_prom\"]}')
print(f'   Alta confianza (≥0.9): {result[\"alta_confianza\"]}')
print(f'   Baja confianza (<0.7): {result[\"baja_confianza\"]}')

# Cache más utilizado
print(f'\n💾 CACHE MÁS UTILIZADO:')
query2 = '''
SELECT pm.name, pm.brand, aic.hits, aic.confidence
FROM ai_metadata_cache aic
JOIN productos_maestros pm ON aic.fingerprint = pm.fingerprint
WHERE pm.active = true
ORDER BY aic.hits DESC
LIMIT 5;
'''

results2 = c.execute_query(query2)
for r in results2:
    name = r['name'][:30] + '...' if len(r['name']) > 30 else r['name']
    print(f'   {name:35s} - {r[\"hits\"]:2d} hits (conf: {r[\"confidence\"]:.3f})')

# Productos que necesitan revisión
print(f'\n⚠️  PRODUCTOS QUE NECESITAN REVISIÓN:')
query3 = '''
SELECT name, brand, ai_confidence, 
       CASE 
           WHEN ai_confidence < 0.7 THEN 'Baja confianza'
           WHEN brand = 'DESCONOCIDA' THEN 'Marca desconocida'
           ELSE 'Otro'
       END as problema
FROM productos_maestros
WHERE active = true 
  AND (ai_confidence < 0.7 OR brand = 'DESCONOCIDA')
ORDER BY ai_confidence ASC
LIMIT 5;
'''

results3 = c.execute_query(query3)
for r in results3:
    name = r['name'][:25] + '...' if len(r['name']) > 25 else r['name']
    print(f'   {name:30s} - {r[\"problema\"]} (conf: {r[\"ai_confidence\"] or 0:.3f})')
"
```

### 8. 📱 CASO ESPECÍFICO: ANÁLISIS DE CELULARES

**Escenario**: Análisis detallado del mercado de celulares.

```bash
cd src
python -c "
from unified_connector import get_unified_connector
c = get_unified_connector()

print('📱 ANÁLISIS MERCADO CELULARES')
print('=' * 35)

# Estadísticas de celulares
query = '''
SELECT 
    COUNT(*) as total_celulares,
    COUNT(DISTINCT pm.brand) as marcas,
    COUNT(DISTINCT pa.retailer_id) as retailers,
    ROUND(AVG(pa.precio_tarjeta)::numeric, 0) as precio_promedio,
    MIN(pa.precio_tarjeta) as precio_min,
    MAX(pa.precio_tarjeta) as precio_max
FROM productos_maestros pm
JOIN precios_actuales pa ON pm.fingerprint = pa.fingerprint
WHERE pm.category = 'celulares' AND pm.active = true;
'''

result = c.execute_query(query)[0]
print(f'📊 RESUMEN CELULARES:')
print(f'   Productos: {result[\"total_celulares\"]}')
print(f'   Marcas: {result[\"marcas\"]}') 
print(f'   Retailers: {result[\"retailers\"]}')
print(f'   Precio promedio: \${result[\"precio_promedio\"]:,}')
print(f'   Rango: \${result[\"precio_min\"]:,} - \${result[\"precio_max\"]:,}')

# Marcas más populares
print(f'\n🏷️ MARCAS MÁS POPULARES:')
query2 = '''
SELECT pm.brand, COUNT(*) as productos, 
       ROUND(AVG(pa.precio_tarjeta)::numeric, 0) as precio_prom
FROM productos_maestros pm
JOIN precios_actuales pa ON pm.fingerprint = pa.fingerprint
WHERE pm.category = 'celulares' AND pm.active = true 
  AND pm.brand != 'DESCONOCIDA'
GROUP BY pm.brand
ORDER BY productos DESC
LIMIT 5;
'''

results2 = c.execute_query(query2)
for r in results2:
    print(f'   {r[\"brand\"]:12s}: {r[\"productos\"]:2d} productos (prom: \${r[\"precio_prom\"]:,})')

# Mejores ofertas
print(f'\n💰 MEJORES OFERTAS CELULARES:')
query3 = '''
SELECT pm.name, pm.brand, r.name as retailer, pa.precio_tarjeta,
       ROUND((pa.precio_normal - pa.precio_tarjeta)::numeric * 100 / pa.precio_normal, 1) as descuento
FROM productos_maestros pm
JOIN precios_actuales pa ON pm.fingerprint = pa.fingerprint
JOIN retailers r ON pa.retailer_id = r.id
WHERE pm.category = 'celulares' AND pm.active = true
  AND pa.precio_normal > pa.precio_tarjeta
ORDER BY descuento DESC
LIMIT 3;
'''

results3 = c.execute_query(query3)
for r in results3:
    name = r['name'][:30] + '...' if len(r['name']) > 30 else r['name']
    print(f'   {name:35s}')
    print(f'     {r[\"brand\"]} en {r[\"retailer\"]} - \${r[\"precio_tarjeta\"]:,} (-{r[\"descuento\"]}%)')
"
```

## 🎯 COMANDOS QUICK REFERENCE

### Scrapers
```bash
# Ciclo único todos los scrapers
cd Scrappers && python scraper_orchestrator.py

# Solo Ripley
python scraper_orchestrator.py --scraper ripley

# Modo continuo
python scraper_orchestrator.py --mode continuous --max-cycles 3
```

### Normalización
```bash
# Normalizar todo
cd src && python cli_integrated.py normalize --input-dir ../data/ --recursive

# Solo un retailer
python cli_integrated.py normalize --retailer ripley --input-dir ../data/ripley/

# Ver estadísticas
python cli_integrated.py stats
```

### Monitoreo
```bash
# Health check
cd src && python db_audit_simple.py

# Estadísticas rápidas
python -c "from unified_connector import get_unified_connector; c=get_unified_connector(); print(c.get_processing_stats())"

# Ver logs
tail -f data/logs/*.log
```

### Pipeline Completo
```bash
# Ejecutar pipeline completo
./pipeline_completo.sh

# Ver reporte generado
cat reports/*/pipeline_summary.txt
```

## 🛠️ TROUBLESHOOTING RÁPIDO

### Error de conexión BD
```bash
python -c "from config_manager import get_config; print(get_config().database.host)"
```

### Sin archivos scrapeados
```bash
find data/ -name "*.json" -newermt "$(date +%Y-%m-%d)" | wc -l
```

### IA no funciona
```bash
python -c "from llm_connectors import enabled; print(f'IA enabled: {enabled()}')"
```

### Reset cache IA
```bash
cd src && python -c "from unified_connector import get_unified_connector; c=get_unified_connector(); c.execute_update('TRUNCATE ai_metadata_cache CASCADE'); print('Cache limpiado')"
```

---

**💡 TIP: Guarda los comandos más utilizados como aliases en tu ~/.bashrc:**

```bash
alias norm-stats="cd /path/to/normalizacion/src && python cli_integrated.py stats"
alias norm-audit="cd /path/to/normalizacion/src && python db_audit_simple.py"  
alias norm-scrapers="cd /path/to/normalizacion/Scrappers && python scraper_orchestrator.py"
alias norm-pipeline="/path/to/normalizacion/pipeline_completo.sh"
```

---

**Sistema desarrollado con ❤️ y 🤖 por Claude Code**