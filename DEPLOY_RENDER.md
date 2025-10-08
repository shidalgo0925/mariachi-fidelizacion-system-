# 🎨 Deploy en Render

Render es una excelente alternativa a Railway con soporte completo para Python, PostgreSQL y Redis.

## 📋 Pasos para Deploy

### 1. Preparar el repositorio
```bash
# Asegúrate de que tu código esté en GitHub
git add .
git commit -m "Preparar para deployment"
git push origin main
```

### 2. Crear cuenta en Render
1. Ve a [render.com](https://render.com)
2. Conecta tu cuenta de GitHub
3. Haz clic en "New +"
4. Selecciona "Web Service"
5. Conecta tu repositorio

### 3. Configurar el servicio web
- **Name**: `mariachi-fidelizacion`
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 4. Crear base de datos PostgreSQL
1. Ve a "New +" → "PostgreSQL"
2. **Name**: `mariachi-fidelizacion-db`
3. **Database**: `mariachi_fidelizacion`
4. **User**: `postgres`
5. **Password**: (se genera automáticamente)

### 5. Crear Redis (opcional)
1. Ve a "New +" → "Redis"
2. **Name**: `mariachi-fidelizacion-redis`

### 6. Configurar variables de entorno
En tu servicio web → Environment:

```env
# Base de datos
DATABASE_URL=postgresql://user:password@host:5432/mariachi_fidelizacion

# Redis
REDIS_URL=redis://host:6379/0

# JWT
SECRET_KEY=tu-clave-super-secreta-aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# APIs Externas
INSTAGRAM_CLIENT_ID=tu-instagram-client-id
INSTAGRAM_CLIENT_SECRET=tu-instagram-client-secret
YOUTUBE_API_KEY=tu-youtube-api-key

# Odoo
ODOO_URL=https://tu-odoo-instance.com
ODOO_DATABASE=tu-odoo-database
ODOO_USERNAME=tu-odoo-username
ODOO_PASSWORD=tu-odoo-password

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=tu-email@gmail.com
SMTP_PASSWORD=tu-app-password
EMAIL_FROM=no-reply@tudominio.com

# CORS
CORS_ORIGINS=["https://tudominio.com"]

# Debug
DEBUG=false
LOG_LEVEL=info
```

### 7. Deploy
1. Haz clic en "Create Web Service"
2. Render construirá y desplegará tu aplicación
3. Ejecutará las migraciones automáticamente

## 🔧 Comandos útiles

### Ver logs
```bash
# En el dashboard de Render
```

### Conectar a la base de datos
```bash
# Usa la información de conexión del dashboard
```

### Ejecutar comandos
```bash
# En el dashboard de Render → Shell
```

## 💰 Costos
- **Gratis**: 750 horas/mes
- **Starter**: $7/mes
- **Standard**: $25/mes

## ✅ Ventajas de Render
- ✅ Deploy automático desde GitHub
- ✅ Base de datos PostgreSQL incluida
- ✅ Redis incluido
- ✅ SSL automático
- ✅ Dominio personalizado
- ✅ Logs en tiempo real
- ✅ Workers de Celery soportados
- ✅ Backup automático

## 🚨 Limitaciones
- ❌ Plan gratuito tiene límites de tiempo
- ❌ No hay escalado automático en plan gratuito
