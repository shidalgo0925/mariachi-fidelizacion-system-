@echo off
echo ========================================
echo CONFIGURACION DE BASE DE DATOS
echo ========================================

echo.
echo [1/4] Verificando PostgreSQL...
psql --version
if %errorlevel% neq 0 (
    echo.
    echo ERROR: PostgreSQL no esta instalado
    echo.
    echo OPCIONES:
    echo 1. Instalar PostgreSQL: https://postgresql.org/download
    echo 2. Usar Docker: docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:15
    echo 3. Usar SQLite (solo para desarrollo): Modificar .env
    echo.
    pause
    exit /b 1
)

echo.
echo [2/4] Creando base de datos...
psql -U postgres -c "CREATE DATABASE mariachi_fidelizacion_dev;" 2>nul
if %errorlevel% neq 0 (
    echo Base de datos ya existe o error de conexion
)

echo.
echo [3/4] Ejecutando migraciones...
call venv\Scripts\activate.bat
alembic upgrade head
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron ejecutar las migraciones
    echo Verifica la conexion a la base de datos en .env
    pause
    exit /b 1
)

echo.
echo [4/4] Inicializando datos de prueba...
python scripts/init_data.py
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron inicializar los datos
    pause
    exit /b 1
)

echo.
echo ✅ Base de datos configurada correctamente!
echo.
echo Datos de prueba creados:
echo - Sitio: Mariachi Sol del Aguila
echo - Usuarios: juan.perez@example.com, maria.gonzalez@example.com
echo - Videos: 5 videos de prueba
echo - Templates: Templates de notificacion
echo.
pause
