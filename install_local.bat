@echo off
echo ========================================
echo INSTALACION LOCAL - MARIACHI FIDELIZACION
echo ========================================

echo.
echo [1/6] Verificando Python...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python no esta instalado
    echo Descarga Python desde: https://python.org
    pause
    exit /b 1
)

echo.
echo [2/6] Creando entorno virtual...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: No se pudo crear el entorno virtual
    pause
    exit /b 1
)

echo.
echo [3/6] Activando entorno virtual...
call venv\Scripts\activate.bat

echo.
echo [4/6] Instalando dependencias...
pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron instalar las dependencias
    pause
    exit /b 1
)

echo.
echo [5/6] Configurando variables de entorno...
if not exist .env (
    copy env.example .env
    echo Archivo .env creado. Editalo con tus configuraciones.
)

echo.
echo [6/6] Instalacion completada!
echo.
echo Para iniciar el servidor:
echo 1. Activa el entorno virtual: venv\Scripts\activate.bat
echo 2. Ejecuta: python -m uvicorn app.main:app --reload
echo 3. Abre: http://localhost:8000/docs
echo.
pause
