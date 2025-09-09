# 🤖 SISTEMA INTEGRADO DE SCRAPING CON FILTROS AUTOMÁTICOS

## 📋 RESUMEN
Sistema orquestado que ejecuta scrapers de forma secuencial cada hora con filtrado automático de productos ruidosos antes del procesamiento con IA.

## 🎯 CARACTERÍSTICAS PRINCIPALES
- ✅ **Ejecución secuencial**: Falabella → Ripley → Paris cada hora
- ✅ **Ciclo único por scraper**: Cada scraper ejecuta todas sus búsquedas una vez
- ✅ **Filtrado automático**: Elimina accesorios, productos bajo $50.000 y reacondicionados
- ✅ **Sin modificación de lógica de extracción**: Mantiene selectores y métodos originales
- ✅ **Datos centralizados**: Todo se guarda en `D:\Normalizacion IA 2.0\datos\`

## 🗂️ ESTRUCTURA DE ARCHIVOS

### Scrapers Principales
- `ripley_ultra_stealth_v3.py` - Scraper Ripley con anti-detección
- `falabella_busqueda_continuo.py` - Scraper Falabella headless  
- `paris_busqueda_continuo.py` - Scraper Paris headless

### Sistema de Filtros
- `product_filter.py` - Filtro principal de productos ruidosos
- `auto_filter.py` - Auto-filtrador que procesa archivos recientes

### Orquestador
- `scraper_orchestrator.py` - Orquestador principal con múltiples modos
- `hourly_scheduler.py` - Orquestador específico para ejecución horaria

## 🚀 MODOS DE EJECUCIÓN

### 1. Orquestador Principal
```bash
# Scraper individual
python scraper_orchestrator.py --scraper falabella

# Ciclo único de todos
python scraper_orchestrator.py --mode single

# Modo horario (recomendado)
python scraper_orchestrator.py --mode hourly

# Modo continuo con límite de ciclos
python scraper_orchestrator.py --mode continuous --max-cycles 5

# Ver estado
python scraper_orchestrator.py --mode status
```

### 2. Orquestador Horario Dedicado
```bash
python hourly_scheduler.py
```

### 3. Filtros Manuales
```bash
# Filtrar archivo específico
python product_filter.py archivo.json

# Auto-filtrar archivos recientes (una vez)
python auto_filter.py --mode once

# Monitorear y filtrar continuamente
python auto_filter.py --mode monitor --interval 60
```

## 📊 FLUJO DE TRABAJO AUTOMÁTICO

### Secuencia Horaria
1. **16:00** - Ejecuta Falabella (todas las búsquedas)
2. **16:XX** - Aplica filtros automáticos
3. **16:XX** - Ejecuta Ripley (todas las búsquedas)  
4. **16:XX** - Aplica filtros automáticos
5. **16:XX** - Ejecuta Paris (todas las búsquedas)
6. **16:XX** - Aplica filtros automáticos
7. **17:00** - Repite secuencia

### Filtrado Automático
- Se ejecuta después de cada scraper exitoso
- Detecta y elimina:
  - 🔧 **Accesorios**: cables, fundas, soportes, etc.
  - 💰 **Productos bajo $50.000**
  - 🔄 **Productos reacondicionados/usados**

## 📁 ESTRUCTURA DE DATOS

```
D:\Normalizacion IA 2.0\datos\
├── falabella/
│   ├── busqueda_perfume_ciclo001_2025-09-09.json
│   ├── busqueda_perfume_ciclo001_2025-09-09_filtered.json
│   └── falabella_continuo.log
├── ripley/
│   ├── ultra_smartphones_c001_2025-09-09.json
│   ├── ultra_smartphones_c001_2025-09-09_filtered.json
│   └── ripley_ultra_stealth_v3.log
├── paris/
│   ├── busqueda_tv_ciclo001_2025-09-09.json
│   ├── busqueda_tv_ciclo001_2025-09-09_filtered.json
│   └── paris_busqueda_continuo.log
└── scheduler/
    ├── orchestrator.log
    └── hourly_scheduler.log
```

## 🎛️ CONFIGURACIÓN DE BÚSQUEDAS

### Ripley - ULTRA_BUSQUEDAS
- smartphones: Términos Android, Samsung, iPhone
- laptops: Términos notebook, laptop, gaming  
- electrodomesticos: Términos refrigerador, lavadora, TV

### Falabella - BUSQUEDAS_CONTINUAS
- perfume: Perfumes y fragancias
- smartv: Smart TV y televisores
- notebook: Laptops y notebooks
- smartphone: Celulares y smartphones
- electrohogar: Electrodomésticos

### Paris - BUSQUEDAS_CONTINUAS  
- tv: Televisores y Smart TV
- notebook: Laptops y computadores
- smartphone: Celulares y accesorios

## 🛡️ CARACTERÍSTICAS DE SEGURIDAD

### Ripley Ultra-Stealth
- Undetected ChromeDriver
- Rotación de User-Agent realista
- Proxies chilenos 
- Delays aleatorios anti-detección
- Bypass Cloudflare/WAF

### Falabella y Paris
- Chrome headless
- Headers realistas
- Delays entre páginas
- Manejo de errores robusto

## 📈 ESTADÍSTICAS DE FILTRADO

El sistema reporta automáticamente:
- Productos originales encontrados
- Productos filtrados por categoría (accesorio/precio/reacondicionado)
- Productos válidos resultantes
- Porcentaje de reducción

## 🔧 MANTENIMIENTO

### Logs de Monitoreo
- `orchestrator.log` - Actividad del orquestador
- `auto_filter.log` - Actividad del filtro automático
- `[tienda]_continuo.log` - Logs específicos por scraper

### Comandos Útiles
```bash
# Ver últimos logs del orquestador
tail -f ../datos/scheduler/orchestrator.log

# Ver archivos filtrados recientes
ls -la ../datos/*/​*filtered*.json

# Limpiar logs antiguos (opcional)
find ../datos -name "*.log" -mtime +7 -delete
```

## ⚠️ CONSIDERACIONES IMPORTANTES

1. **No modificar lógica de extracción**: Los selectores y métodos de scraping están optimizados
2. **Filtros aplicados post-extracción**: Los filtros no interfieren con el proceso de scraping
3. **Datos originales preservados**: Los archivos originales se mantienen junto con los filtrados
4. **Ejecución secuencial**: Solo un scraper activo a la vez para evitar sobrecargas
5. **Detección automática de archivos**: El auto-filtro detecta archivos nuevos por timestamp

## 🚨 SOLUCIÓN DE PROBLEMAS

### Scraper no ejecuta
- Verificar que Chrome/ChromeDriver estén instalados
- Comprobar conectividad de red
- Revisar logs específicos del scraper

### Filtros no se aplican
- Verificar que `product_filter.py` esté en la misma carpeta
- Comprobar permisos de escritura en carpeta de datos
- Revisar `auto_filter.log`

### Orquestador se detiene
- Verificar `orchestrator.log` 
- Comprobar recursos del sistema
- Usar Ctrl+C para detener limpiamente

---

**Sistema desarrollado para normalización de datos con IA 2.0**
*Versión: 1.0 | Fecha: 2025-09-09*