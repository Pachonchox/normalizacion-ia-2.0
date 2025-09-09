#!/bin/bash

# 🚀 PIPELINE COMPLETO - Sistema Normalización IA 2.0
# Script automatizado que ejecuta el flujo end-to-end completo

set -e  # Salir si cualquier comando falla

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Funciones de logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
    echo "----------------------------------------"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "GUIA_COMPLETA_USO.md" ]; then
    log_error "No estás en el directorio raíz del proyecto. Ejecuta desde D:\\Normalizacion IA 2.0\\"
    exit 1
fi

# Variables
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_FILE="data/logs/pipeline_${TIMESTAMP}.log"

# Crear directorio de logs si no existe
mkdir -p data/logs

# Función para logging a archivo
log_to_file() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

echo "========================================"
echo "🚀 PIPELINE COMPLETO NORMALIZACIÓN IA 2.0"
echo "========================================"
echo "Inicio: $(date)"
echo "Log: $LOG_FILE"
echo "========================================"

# Iniciar logging
log_to_file "INICIO PIPELINE COMPLETO"

# ============================================
# PASO 1: VERIFICAR CONFIGURACIÓN
# ============================================
log_step "🔧 PASO 1: Verificando configuración"

if [ ! -f ".env" ]; then
    log_error "Archivo .env no encontrado. Copia .env.example y configúralo."
    log_to_file "ERROR: .env no encontrado"
    exit 1
fi

log_info "Verificando conexión a PostgreSQL..."
if python -c "from src.config_manager import get_config; get_config().database" 2>/dev/null; then
    log_success "Configuración de BD válida"
    log_to_file "Configuración BD: OK"
else
    log_error "Error en configuración de base de datos"
    log_to_file "ERROR: Configuración BD inválida"
    exit 1
fi

log_info "Verificando configuración de OpenAI..."
if python -c "from src.config_manager import get_config; get_config().openai" 2>/dev/null; then
    log_success "Configuración de OpenAI válida"
    log_to_file "Configuración OpenAI: OK"
else
    log_warning "OpenAI no configurado correctamente - continuando sin IA"
    log_to_file "WARNING: OpenAI no configurado"
fi

# ============================================
# PASO 2: EJECUTAR SCRAPERS
# ============================================
log_step "🕷️ PASO 2: Ejecutando scrapers"

cd Scrappers

log_info "Verificando dependencias de scrapers..."
if python -c "import selenium, undetected_chromedriver, bs4" 2>/dev/null; then
    log_success "Dependencias de scrapers OK"
    log_to_file "Dependencias scrapers: OK"
else
    log_error "Dependencias de scrapers faltantes. Ejecuta: pip install -r Scrappers/requirements.txt"
    log_to_file "ERROR: Dependencias scrapers faltantes"
    exit 1
fi

log_info "Iniciando orquestador de scrapers (ciclo único)..."
if python scraper_orchestrator.py 2>&1 | tee -a "../$LOG_FILE"; then
    log_success "Scrapers completados exitosamente"
    log_to_file "Scrapers: COMPLETADOS"
else
    log_warning "Scrapers completados con advertencias"
    log_to_file "Scrapers: COMPLETADOS CON WARNINGS"
fi

# Verificar datos scrapeados
SCRAPED_FILES=$(find ../data/ripley ../data/falabella ../data/paris -name "*.json" 2>/dev/null | wc -l)
log_info "Archivos scrapeados encontrados: $SCRAPED_FILES"
log_to_file "Archivos scrapeados: $SCRAPED_FILES"

if [ "$SCRAPED_FILES" -eq 0 ]; then
    log_error "No se encontraron archivos scrapeados. Revisa logs de scrapers."
    log_to_file "ERROR: Sin archivos scrapeados"
    exit 1
fi

cd ..

# ============================================
# PASO 3: NORMALIZACIÓN CON IA
# ============================================
log_step "🧠 PASO 3: Normalizando productos con IA"

cd src

log_info "Iniciando normalización integrada..."
if python cli_integrated.py normalize --input-dir ../data/ --recursive 2>&1 | tee -a "../$LOG_FILE"; then
    log_success "Normalización completada"
    log_to_file "Normalización: COMPLETADA"
else
    log_error "Error en normalización"
    log_to_file "ERROR: Normalización falló"
    cd ..
    exit 1
fi

cd ..

# ============================================
# PASO 4: AUDITORÍA Y VERIFICACIÓN
# ============================================
log_step "📊 PASO 4: Auditoría de resultados"

cd src

log_info "Ejecutando auditoría de base de datos..."
if python db_audit_simple.py 2>&1 | tee -a "../$LOG_FILE"; then
    log_success "Auditoría completada"
    log_to_file "Auditoría: COMPLETADA"
else
    log_warning "Auditoría completada con advertencias"
    log_to_file "Auditoría: COMPLETADA CON WARNINGS"
fi

log_info "Obteniendo estadísticas finales..."
python cli_integrated.py stats 2>&1 | tee -a "../$LOG_FILE"

cd ..

# ============================================
# PASO 5: GENERACIÓN DE REPORTES
# ============================================
log_step "📈 PASO 5: Generando reportes"

# Crear directorio de reportes
mkdir -p "reports/${TIMESTAMP}"

log_info "Generando reporte de ejecución..."

# Reporte básico de archivos
cat > "reports/${TIMESTAMP}/pipeline_summary.txt" << EOF
RESUMEN PIPELINE COMPLETO - ${TIMESTAMP}
==========================================

SCRAPERS:
- Archivos generados: $(find data/ripley data/falabella data/paris -name "*.json" 2>/dev/null | wc -l)
- Ripley: $(find data/ripley -name "*.json" 2>/dev/null | wc -l) archivos
- Falabella: $(find data/falabella -name "*.json" 2>/dev/null | wc -l) archivos  
- Paris: $(find data/paris -name "*.json" 2>/dev/null | wc -l) archivos

NORMALIZACIÓN:
- Estado: Ver logs para detalles
- Productos procesados: Ver auditoría

ARCHIVOS GENERADOS:
$(ls -la data/*/*.json 2>/dev/null | head -10)

LOGS:
- Pipeline: $LOG_FILE
- Scrapers: data/logs/orchestrator.log
- Normalización: Ver logs específicos

PRÓXIMOS PASOS:
1. Revisar auditoría en logs
2. Ejecutar consultas SQL desde GUIA_SQL_CONSULTAS.md
3. Monitorear sistema con queries de mantenimiento
EOF

log_success "Reporte generado en reports/${TIMESTAMP}/pipeline_summary.txt"

# ============================================
# PASO 6: LIMPIEZA Y FINALIZACIÓN
# ============================================
log_step "🧹 PASO 6: Finalización"

log_info "Verificando integridad final..."

# Verificar que los procesos han terminado correctamente
if pgrep -f "python.*scraper" > /dev/null; then
    log_warning "Aún hay procesos de scraper ejecutándose"
    log_to_file "WARNING: Procesos scraper aún activos"
fi

# Comprimir logs antiguos (más de 7 días)
find data/logs -name "*.log" -mtime +7 -exec gzip {} \; 2>/dev/null || true

log_info "Estadísticas de almacenamiento:"
du -sh data/ 2>/dev/null || log_warning "No se pudo obtener estadísticas de almacenamiento"

# ============================================
# RESUMEN FINAL
# ============================================
echo ""
echo "========================================"
echo "✅ PIPELINE COMPLETO FINALIZADO"
echo "========================================"
echo "Fin: $(date)"
echo "Duración: $(($(date +%s) - $(date -d "$(head -1 "$LOG_FILE" | cut -d' ' -f1-2)" +%s 2>/dev/null || echo 0))) segundos"
echo ""
echo "📁 ARCHIVOS GENERADOS:"
echo "- Datos scrapeados: data/{retailer}/*.json"
echo "- Logs: $LOG_FILE"
echo "- Reporte: reports/${TIMESTAMP}/pipeline_summary.txt"
echo ""
echo "📊 PRÓXIMOS PASOS:"
echo "1. Revisar logs para detalles: cat $LOG_FILE"
echo "2. Ejecutar consultas SQL: ver GUIA_SQL_CONSULTAS.md"
echo "3. Monitorear auditoría: cd src && python db_audit_simple.py"
echo ""
echo "🔍 MONITOREO CONTINUO:"
echo "- Ver estado BD: cd src && python cli_integrated.py stats"
echo "- Scrapers continuos: cd Scrappers && python scraper_orchestrator.py --mode continuous"
echo ""
echo "========================================"

log_to_file "PIPELINE COMPLETO: FINALIZADO EXITOSAMENTE"

# Mostrar resumen del reporte
if [ -f "reports/${TIMESTAMP}/pipeline_summary.txt" ]; then
    echo "📋 RESUMEN:"
    cat "reports/${TIMESTAMP}/pipeline_summary.txt"
fi