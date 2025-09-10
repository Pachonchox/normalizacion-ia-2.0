@echo off
chcp 65001 >nul
echo.
echo ========================================================
echo       MIGRACION GPT-5 - Normalizacion IA 2.0
echo ========================================================
echo.
echo Configuracion:
echo - Servidor: 34.176.197.136:5432
echo - Base de datos: postgres
echo - Usuario: postgres
echo.

REM Configurar variables de entorno para psql
set PGPASSWORD=Osmar2503!
set PGHOST=34.176.197.136
set PGPORT=5432
set PGDATABASE=postgres
set PGUSER=postgres

echo ========================================================
echo PASO 1: Ejecutando migracion de esquema inicial...
echo ========================================================
psql -f "migrations\001_gpt5_initial_schema.sql"
if %errorlevel% neq 0 (
    echo ERROR: Fallo la migracion 001
    pause
    exit /b 1
)
echo OK: Migracion 001 completada

echo.
echo ========================================================
echo PASO 2: Actualizando tablas existentes...
echo ========================================================
psql -f "migrations\002_update_existing_tables.sql"
if %errorlevel% neq 0 (
    echo ERROR: Fallo la migracion 002
    pause
    exit /b 1
)
echo OK: Migracion 002 completada

echo.
echo ========================================================
echo PASO 3: Truncando datos existentes...
echo ========================================================
echo ADVERTENCIA: Se eliminaran TODOS los datos!
echo.
set /p confirm="Escriba SI para confirmar el TRUNCATE: "
if /i "%confirm%" neq "SI" (
    echo Operacion cancelada
    pause
    exit /b 0
)

psql -f "migrations\003_truncate_all_data.sql"
if %errorlevel% neq 0 (
    echo ERROR: Fallo el truncate
    pause
    exit /b 1
)
echo OK: Datos truncados

echo.
echo ========================================================
echo MIGRACION COMPLETADA EXITOSAMENTE
echo ========================================================
echo.
echo Estado final:
psql -c "SELECT COUNT(*) as tablas_gpt5 FROM information_schema.tables WHERE table_name LIKE 'gpt5_%' OR table_name LIKE '%_cache';"
psql -c "SELECT model_name, family, active FROM model_config WHERE active = TRUE;"
echo.
echo Proximos pasos:
echo 1. Verificar logs de migracion
echo 2. Ejecutar tests de validacion
echo 3. Comenzar procesamiento con GPT-5
echo.
pause