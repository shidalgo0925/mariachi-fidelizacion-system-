#!/bin/bash

# Script para deployar Mariachi Fidelización en GCP sin Docker
# Usando Python directo con venv

set -e

echo "🚀 Deployando Mariachi Fidelización en GCP (Python directo)..."

# Variables
APP_DIR="/opt/mariachi-fidelizacion"
APP_USER="mariachi"
SERVICE_NAME="mariachi-fidelizacion"

# 1. Crear usuario para la aplicación
echo "👤 Creando usuario para la aplicación..."
sudo useradd -r -s /bin/false $APP_USER || echo "Usuario ya existe"

# 2. Crear directorio de la aplicación
echo "📁 Creando directorio de la aplicación..."
sudo mkdir -p $APP_DIR
sudo chown $APP_USER:$APP_USER $APP_DIR

# 3. Clonar repositorio
echo "📥 Clonando repositorio..."
cd /tmp
git clone https://github.com/shidalgo0925/mariachi-fidelizacion-system-.git
sudo cp -r mariachi-fidelizacion-system-/* $APP_DIR/
sudo chown -R $APP_USER:$APP_USER $APP_DIR

# 4. Instalar Python y dependencias del sistema
echo "🐍 Instalando Python y dependencias..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv postgresql-client redis-tools

# 5. Crear entorno virtual
echo "🔧 Creando entorno virtual..."
cd $APP_DIR
sudo -u $APP_USER python3 -m venv venv
sudo -u $APP_USER ./venv/bin/pip install --upgrade pip
sudo -u $APP_USER ./venv/bin/pip install -r requirements.txt

# 6. Crear directorios necesarios
echo "📂 Creando directorios necesarios..."
sudo -u $APP_USER mkdir -p logs reports exports uploads

# 7. Configurar variables de entorno
echo "⚙️ Configurando variables de entorno..."
sudo -u $APP_USER cp env.gcp .env
echo "⚠️  IMPORTANTE: Edita el archivo .env con tus configuraciones:"
echo "   nano $APP_DIR/.env"

# 8. Crear servicio systemd
echo "🔧 Creando servicio systemd..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=Mariachi Fidelización API
After=network.target

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 9. Habilitar y iniciar servicio
echo "🚀 Habilitando e iniciando servicio..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

# 10. Configurar firewall
echo "🔒 Configurando firewall..."
sudo ufw allow 8000/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 11. Verificar estado
echo "📊 Verificando estado del servicio..."
sleep 5
sudo systemctl status $SERVICE_NAME --no-pager

echo ""
echo "✅ Deploy completado!"
echo ""
echo "📋 Información importante:"
echo "🖥️  Aplicación: http://$(curl -s ifconfig.me):8000"
echo "📚 Documentación: http://$(curl -s ifconfig.me):8000/docs"
echo "🔧 Admin: http://$(curl -s ifconfig.me):8000/redoc"
echo ""
echo "🔧 Comandos útiles:"
echo "   Ver logs: sudo journalctl -u $SERVICE_NAME -f"
echo "   Reiniciar: sudo systemctl restart $SERVICE_NAME"
echo "   Estado: sudo systemctl status $SERVICE_NAME"
echo "   Detener: sudo systemctl stop $SERVICE_NAME"
echo ""
echo "⚠️  PRÓXIMOS PASOS:"
echo "1. Edita las variables de entorno: sudo nano $APP_DIR/.env"
echo "2. Reinicia el servicio: sudo systemctl restart $SERVICE_NAME"
echo "3. Verifica que funcione: curl http://localhost:8000/health"
echo ""
