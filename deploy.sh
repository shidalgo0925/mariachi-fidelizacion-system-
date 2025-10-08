#!/bin/bash

# Script de deployment para el sistema de fidelización multi-tenant
# Uso: ./deploy.sh [environment] [action]
# environment: development, staging, production
# action: deploy, rollback, status

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Verificar argumentos
if [ $# -lt 2 ]; then
    error "Usage: $0 [environment] [action]"
    error "Environments: development, staging, production"
    error "Actions: deploy, rollback, status, backup"
    exit 1
fi

ENVIRONMENT=$1
ACTION=$2

# Validar environment
case $ENVIRONMENT in
    development|staging|production)
        ;;
    *)
        error "Invalid environment: $ENVIRONMENT"
        exit 1
        ;;
esac

# Validar action
case $ACTION in
    deploy|rollback|status|backup)
        ;;
    *)
        error "Invalid action: $ACTION"
        exit 1
        ;;
esac

# Configuración por environment
case $ENVIRONMENT in
    development)
        ENV_FILE=".env.development"
        COMPOSE_FILE="docker-compose.yml"
        ;;
    staging)
        ENV_FILE=".env.staging"
        COMPOSE_FILE="docker-compose.staging.yml"
        ;;
    production)
        ENV_FILE=".env.production"
        COMPOSE_FILE="docker-compose.prod.yml"
        ;;
esac

# Verificar que el archivo de environment existe
if [ ! -f "$ENV_FILE" ]; then
    error "Environment file not found: $ENV_FILE"
    exit 1
fi

# Función para cargar variables de environment
load_env() {
    log "Loading environment variables from $ENV_FILE"
    export $(grep -v '^#' "$ENV_FILE" | xargs)
}

# Función para verificar dependencias
check_dependencies() {
    log "Checking dependencies..."
    
    # Verificar Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    # Verificar Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi
    
    # Verificar que Docker está corriendo
    if ! docker info &> /dev/null; then
        error "Docker is not running"
        exit 1
    fi
    
    success "All dependencies are available"
}

# Función para hacer backup
backup() {
    log "Creating backup..."
    
    # Crear directorio de backup
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup de base de datos
    if [ -f "scripts/backup.py" ]; then
        log "Running database backup..."
        python scripts/backup.py
    fi
    
    # Backup de archivos importantes
    log "Backing up important files..."
    tar -czf "$BACKUP_DIR/files.tar.gz" \
        reports/ exports/ logs/ uploads/ \
        .env* alembic.ini alembic/versions/ \
        2>/dev/null || true
    
    success "Backup created in $BACKUP_DIR"
}

# Función para deploy
deploy() {
    log "Starting deployment to $ENVIRONMENT..."
    
    # Cargar variables de environment
    load_env
    
    # Verificar dependencias
    check_dependencies
    
    # Hacer backup antes del deploy
    if [ "$ENVIRONMENT" = "production" ]; then
        backup
    fi
    
    # Construir imágenes
    log "Building Docker images..."
    docker-compose -f "$COMPOSE_FILE" build
    
    # Ejecutar migraciones
    log "Running database migrations..."
    docker-compose -f "$COMPOSE_FILE" run --rm app alembic upgrade head
    
    # Inicializar datos si es necesario
    if [ "$ENVIRONMENT" = "development" ]; then
        log "Initializing development data..."
        docker-compose -f "$COMPOSE_FILE" run --rm app python scripts/init_data.py
    fi
    
    # Levantar servicios
    log "Starting services..."
    docker-compose -f "$COMPOSE_FILE" up -d
    
    # Esperar a que los servicios estén listos
    log "Waiting for services to be ready..."
    sleep 30
    
    # Verificar salud de los servicios
    log "Checking service health..."
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        success "Services are running"
    else
        error "Some services failed to start"
        docker-compose -f "$COMPOSE_FILE" logs
        exit 1
    fi
    
    # Verificar endpoint de health
    if [ -n "$HEALTH_CHECK_URL" ]; then
        log "Checking application health..."
        if curl -f "$HEALTH_CHECK_URL" &> /dev/null; then
            success "Application is healthy"
        else
            error "Application health check failed"
            exit 1
        fi
    fi
    
    success "Deployment to $ENVIRONMENT completed successfully"
}

# Función para rollback
rollback() {
    log "Starting rollback for $ENVIRONMENT..."
    
    # Cargar variables de environment
    load_env
    
    # Verificar dependencias
    check_dependencies
    
    # Hacer backup antes del rollback
    backup
    
    # Obtener versión anterior
    PREVIOUS_VERSION=$(docker-compose -f "$COMPOSE_FILE" ps -q | head -1)
    
    if [ -z "$PREVIOUS_VERSION" ]; then
        error "No previous version found for rollback"
        exit 1
    fi
    
    # Detener servicios actuales
    log "Stopping current services..."
    docker-compose -f "$COMPOSE_FILE" down
    
    # Restaurar versión anterior
    log "Restoring previous version..."
    docker-compose -f "$COMPOSE_FILE" up -d
    
    # Esperar a que los servicios estén listos
    log "Waiting for services to be ready..."
    sleep 30
    
    # Verificar salud de los servicios
    log "Checking service health..."
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        success "Rollback completed successfully"
    else
        error "Rollback failed"
        docker-compose -f "$COMPOSE_FILE" logs
        exit 1
    fi
}

# Función para status
status() {
    log "Checking status of $ENVIRONMENT..."
    
    # Cargar variables de environment
    load_env
    
    # Verificar dependencias
    check_dependencies
    
    # Mostrar estado de los servicios
    log "Service status:"
    docker-compose -f "$COMPOSE_FILE" ps
    
    # Mostrar logs recientes
    log "Recent logs:"
    docker-compose -f "$COMPOSE_FILE" logs --tail=20
    
    # Verificar salud de la aplicación
    if [ -n "$HEALTH_CHECK_URL" ]; then
        log "Application health:"
        if curl -f "$HEALTH_CHECK_URL" &> /dev/null; then
            success "Application is healthy"
        else
            error "Application health check failed"
        fi
    fi
}

# Ejecutar acción
case $ACTION in
    deploy)
        deploy
        ;;
    rollback)
        rollback
        ;;
    status)
        status
        ;;
    backup)
        backup
        ;;
esac
