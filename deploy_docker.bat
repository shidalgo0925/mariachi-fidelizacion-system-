@echo off
echo ========================================
echo DEPLOY CON DOCKER - MARIACHI FIDELIZACION
echo ========================================

echo.
echo [1/6] Verificando Docker...
docker --version
if %errorlevel% neq 0 (
    echo ERROR: Docker no esta instalado
    echo Descarga Docker Desktop desde: https://docker.com
    pause
    exit /b 1
)

echo.
echo [2/6] Verificando Docker Compose...
docker-compose --version
if %errorlevel% neq 0 (
    echo ERROR: Docker Compose no esta instalado
    pause
    exit /b 1
)

echo.
echo [3/6] Configurando variables de entorno...
if not exist .env (
    copy env.example .env
    echo.
    echo ⚠️  IMPORTANTE: Edita el archivo .env con tus configuraciones
    echo    - DATABASE_URL
    echo    - REDIS_URL
    echo    - SECRET_KEY
    echo    - APIs externas (Instagram, YouTube, Odoo)
    echo.
    pause
)

echo.
echo [4/6] Construyendo imagenes Docker...
docker-compose build
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron construir las imagenes
    pause
    exit /b 1
)

echo.
echo [5/6] Iniciando servicios...
docker-compose up -d
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron iniciar los servicios
    pause
    exit /b 1
)

echo.
echo [6/6] Ejecutando migraciones...
docker-compose exec app alembic upgrade head
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron ejecutar las migraciones
    pause
    exit /b 1
)

echo.
echo ✅ Deploy completado!
echo.
echo 🌐 Servidor: http://localhost:8000
echo 📚 Documentacion: http://localhost:8000/docs
echo 🔧 Admin: http://localhost:8000/redoc
echo 🌸 Flower: http://localhost:5555
echo.
echo Comandos utiles:
echo - Ver logs: docker-compose logs -f
echo - Detener: docker-compose down
echo - Reiniciar: docker-compose restart
echo - Shell: docker-compose exec app bash
echo.
pause
