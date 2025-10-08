#!/bin/bash

# Script para configurar Mariachi Fidelización en GCP
# Asegúrate de tener gcloud CLI instalado y configurado

set -e

echo "🚀 Configurando Mariachi Fidelización en GCP..."

# Variables
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
ZONE="us-central1-a"
VM_NAME="mariachi-fidelizacion"
DB_NAME="mariachi-db"
REDIS_NAME="mariachi-redis"
BUCKET_NAME="mariachi-fidelizacion-files"

echo "📋 Configurando proyecto: $PROJECT_ID"

# 1. Crear VM para la aplicación
echo "🖥️ Creando VM para Mariachi Fidelización..."
gcloud compute instances create $VM_NAME \
  --image-family=ubuntu-2004-lts \
  --image-project=ubuntu-os-cloud \
  --machine-type=e2-micro \
  --zone=$ZONE \
  --tags=http-server,https-server \
  --network=default \
  --metadata=startup-script='#!/bin/bash
    apt-get update
    apt-get install -y docker.io docker-compose
    systemctl start docker
    systemctl enable docker
    usermod -aG docker $USER'

# 2. Crear base de datos PostgreSQL
echo "🗄️ Creando base de datos PostgreSQL..."
gcloud sql instances create $DB_NAME \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=$REGION \
  --storage-type=SSD \
  --storage-size=10GB \
  --backup-start-time=03:00 \
  --enable-bin-log

# 3. Crear base de datos
echo "📊 Creando base de datos..."
gcloud sql databases create mariachi_fidelizacion \
  --instance=$DB_NAME

# 4. Crear usuario de base de datos
echo "👤 Creando usuario de base de datos..."
gcloud sql users create mariachi_user \
  --instance=$DB_NAME \
  --password=$(openssl rand -base64 32)

# 5. Crear Redis
echo "🔄 Creando Redis..."
gcloud redis instances create $REDIS_NAME \
  --size=1 \
  --region=$REGION \
  --redis-version=redis_7_0

# 6. Crear bucket de storage
echo "💾 Creando bucket de storage..."
gsutil mb gs://$BUCKET_NAME

# 7. Configurar firewall
echo "🔒 Configurando firewall..."
gcloud compute firewall-rules create allow-mariachi-http \
  --allow tcp:8000 \
  --source-ranges 0.0.0.0/0 \
  --target-tags http-server

gcloud compute firewall-rules create allow-mariachi-https \
  --allow tcp:443 \
  --source-ranges 0.0.0.0/0 \
  --target-tags https-server

# 8. Obtener IPs y configuraciones
echo "📋 Obteniendo configuraciones..."

# IP de la VM
VM_IP=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

# IP de la base de datos
DB_IP=$(gcloud sql instances describe $DB_NAME --format='get(ipAddresses[0].ipAddress)')

# IP de Redis
REDIS_IP=$(gcloud redis instances describe $REDIS_NAME --region=$REGION --format='get(host)')

echo "✅ Configuración completada!"
echo ""
echo "📋 Información de conexión:"
echo "🖥️  VM IP: $VM_IP"
echo "🗄️  DB IP: $DB_IP"
echo "🔄 Redis IP: $REDIS_IP"
echo "💾 Bucket: gs://$BUCKET_NAME"
echo ""
echo "🔧 Próximos pasos:"
echo "1. Conecta a la VM: gcloud compute ssh $VM_NAME --zone=$ZONE"
echo "2. Clona tu repositorio en la VM"
echo "3. Configura las variables de entorno con las IPs mostradas"
echo "4. Ejecuta el deployment"
echo ""
echo "🌐 Tu aplicación estará disponible en: http://$VM_IP:8000"
