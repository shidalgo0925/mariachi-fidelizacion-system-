@echo off
echo ========================================
echo INICIANDO MARIACHI FIDELIZACION
echo ========================================

echo.
echo Activando entorno virtual...
call venv\Scripts\activate.bat

echo.
echo Iniciando servidor de desarrollo...
echo.
echo 🌐 Servidor: http://localhost:8000
echo 📚 Documentacion: http://localhost:8000/docs
echo 🔧 Admin: http://localhost:8000/redoc
echo.
echo Presiona Ctrl+C para detener el servidor
echo.

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
