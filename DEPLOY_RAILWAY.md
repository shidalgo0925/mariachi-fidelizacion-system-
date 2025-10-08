# 🚂 Deploy en Railway

Railway es la opción más fácil para deployar tu aplicación Python con base de datos PostgreSQL incluida.

## 📋 Pasos para Deploy

### 1. Preparar el repositorio
```bash
# Asegúrate de que tu código esté en GitHub
git add .
git commit -m "Preparar para deployment"
git push origin main
```

### 2. Crear cuenta en Railway
1. Ve a [railway.app](https://railway.app)
2. Conecta tu cuenta de GitHub
3. Haz clic en "New Project"
4. Selecciona "Deploy from GitHub repo"
5. Elige tu repositorio

### 3. Configurar variables de entorno
En Railway, ve a tu proyecto → Variables:

```env
# Base de datos (Railway la crea automáticamente)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Redis (opcional, Railway tiene Redis)
REDIS_URL=${{Redis.REDIS_URL}}

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

### 4. Deploy automático
Railway detectará automáticamente que es una aplicación Python y:
- Instalará las dependencias de `requirements.txt`
- Ejecutará el comando de `railway.json`
- Creará la base de datos PostgreSQL
- Ejecutará las migraciones

### 5. Configurar dominio personalizado
1. Ve a Settings → Domains
2. Agrega tu dominio personalizado
3. Configura los DNS records

## 🔧 Comandos útiles

### Ver logs
```bash
railway logs
```

### Conectar a la base de datos
```bash
railway connect postgres
```

### Ejecutar comandos
```bash
railway run python scripts/init_data.py
```

## 💰 Costos
- **Gratis**: $5 de crédito mensual
- **Hobby**: $5/mes por servicio
- **Pro**: $20/mes por servicio

## ✅ Ventajas de Railway
- ✅ Deploy automático desde GitHub
- ✅ Base de datos PostgreSQL incluida
- ✅ Redis incluido
- ✅ SSL automático
- ✅ Dominio personalizado
- ✅ Logs en tiempo real
- ✅ Escalado automático

## 🚨 Limitaciones
- ❌ No hay workers de Celery (solo web)
- ❌ Límite de memoria en plan gratuito
- ❌ No hay backup automático
