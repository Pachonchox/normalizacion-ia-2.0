# 🚀 Sistema de Scrapers Intercalados

Sistema independiente de scrapers para retailers chilenos con orquestación automática.

## 📁 Estructura

```
Scrappers/
├── ripley_ultra_stealth_v3.py     # Scraper Ripley (ultra stealth)
├── falabella_busqueda_continuo.py # Scraper Falabella  
├── paris_busqueda_continuo.py     # Scraper Paris
├── scraper_orchestrator.py        # Orquestador principal
├── requirements.txt               # Dependencias
└── README.md                      # Este archivo

data/
├── ripley/                        # Datos scrapeados de Ripley
├── falabella/                     # Datos scrapeados de Falabella  
├── paris/                         # Datos scrapeados de Paris
└── logs/                          # Logs del orquestador
```

## ⚙️ Configuración

**Todos los scrapers configurados a 10 páginas exactas:**
- ✅ Ripley: 10 páginas fijas
- ✅ Falabella: 10 páginas fijas  
- ✅ Paris: 10 páginas fijas

**Almacenamiento independiente:**
- Cada retailer guarda en su carpeta `/data/{retailer}/`
- Logs centralizados en `/data/logs/`

## 🚀 Instalación

```bash
# Desde carpeta Scrappers
cd Scrappers
pip install -r requirements.txt
```

## 📋 Uso

### Ejecutar un solo ciclo (todos los scrapers una vez)
```bash
python scraper_orchestrator.py
```

### Ejecutar modo continuo
```bash
# Continuo infinito
python scraper_orchestrator.py --mode continuous

# Continuo con límite de ciclos
python scraper_orchestrator.py --mode continuous --max-cycles 5
```

### Ejecutar scraper específico
```bash
# Solo Ripley
python scraper_orchestrator.py --scraper ripley

# Solo Falabella
python scraper_orchestrator.py --scraper falabella

# Solo Paris
python scraper_orchestrator.py --scraper paris
```

### Ver estado
```bash
python scraper_orchestrator.py --mode status
```

### Ejecución directa de scrapers
```bash
# Ejecutar scrapers individualmente
python ripley_ultra_stealth_v3.py
python falabella_busqueda_continuo.py  
python paris_busqueda_continuo.py
```

## 🔄 Funcionamiento Intercalado

El orquestador ejecuta los scrapers de forma inteligente:

1. **Orden aleatorio** cada ciclo
2. **Pausas intercaladas** entre scrapers (5-15 min)
3. **Pausas entre ciclos** completos (30-60 min)
4. **Ejecución independiente** de cada scraper
5. **Logs centralizados** para monitoreo

## 📊 Salida de Datos

Cada scraper genera archivos JSON en su carpeta correspondiente:

```json
{
  "metadata": {
    "scraped_at": "2025-09-09 06:45:00",
    "search_term": "celulares",
    "total_products": 240,
    "pages_scraped": 10,
    "retailer": "ripley"
  },
  "products": [...]
}
```

## 🛡️ Características de Seguridad

- **Ultra-stealth** para Ripley (bypass Cloudflare)
- **Rotación de User Agents** 
- **Delays humanos** aleatorios
- **Manejo de errores** robusto
- **Reintentos automáticos**

## 📈 Monitoreo

```bash
# Ver logs en tiempo real
tail -f ../data/logs/orchestrator.log

# Verificar archivos generados
ls -la ../data/*/
```

## ⚠️ Consideraciones

- **Independiente** del sistema de normalización
- **Sin configuración centralizada** (como solicitado)
- **10 páginas fijas** por scraper
- **Ejecución intercalada** para evitar bloqueos
- **Almacenamiento separado** por retailer