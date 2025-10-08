#!/bin/bash

# Script para configurar base de datos en GCP (Python directo)
# Sin Docker, usando Python directo

set -e

echo "🗄️ Configurando base de datos para Mariachi Fidelización..."

# Variables
APP_DIR="/opt/mariachi-fidelizacion"
APP_USER="mariachi"

# 1. Activar entorno virtual
echo "🔧 Activando entorno virtual..."
cd $APP_DIR
source venv/bin/activate

# 2. Ejecutar migraciones
echo "📊 Ejecutando migraciones de base de datos..."
sudo -u $APP_USER bash -c "cd $APP_DIR && source venv/bin/activate && alembic upgrade head"

# 3. Inicializar datos de prueba
echo "📝 Inicializando datos de prueba..."
sudo -u $APP_USER bash -c "cd $APP_DIR && source venv/bin/activate && python scripts/init_data.py"

echo ""
echo "✅ Base de datos configurada correctamente!"
echo ""
echo "📋 Datos de prueba creados:"
echo "   - Sitio: Mariachi Sol del Aguila"
echo "   - Usuarios: juan.perez@example.com, maria.gonzalez@example.com"
echo "   - Videos: 5 videos de prueba"
echo "   - Templates: Templates de notificación"
echo ""
echo "🔧 Para verificar:"
echo "   curl http://localhost:8000/health"
echo ""
