# 🚀 Guía Completa de Deployment

Esta guía te explica cómo deployar el sistema de fidelización multi-tenant en diferentes plataformas.

## 🎯 Opciones de Deployment

### 1. 🏠 **DESARROLLO LOCAL** (Recomendado para empezar)
- ✅ Más fácil de configurar
- ✅ Control total del entorno
- ✅ Ideal para desarrollo y pruebas
- ❌ No accesible desde internet

### 2. ☁️ **CLOUD PLATFORMS** (Recomendado para producción)
- ✅ Deploy automático
- ✅ Base de datos incluida
- ✅ SSL automático
- ✅ Escalado automático
- ❌ Costos mensuales

### 3. 🐳 **DOCKER** (Para VPS o servidor propio)
- ✅ Control total del servidor
- ✅ Más económico a largo plazo
- ✅ Flexibilidad total
- ❌ Requiere conocimiento de servidores

---

## 🏠 OPCIÓN 1: DESARROLLO LOCAL

### Requisitos
- Python 3.9+
- PostgreSQL 15+
- Redis (opcional)

### Pasos
1. **Instalar dependencias**:
   ```bash
   # Ejecutar en Windows
   install_local.bat
   
   # O manualmente
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configurar base de datos**:
   ```bash
   # Ejecutar en Windows
   setup_database.bat
   
   # O manualmente
   createdb mariachi_fidelizacion_dev
   alembic upgrade head
   python scripts/init_data.py
   ```

3. **Iniciar servidor**:
   ```bash
   # Ejecutar en Windows
   start_local.bat
   
   # O manualmente
   uvicorn app.main:app --reload
   ```

4. **Acceder a la aplicación**:
   - 🌐 Servidor: http://localhost:8000
   - 📚 Documentación: http://localhost:8000/docs
   - 🔧 Admin: http://localhost:8000/redoc

---

## ☁️ OPCIÓN 2: CLOUD PLATFORMS

### 🚂 Railway (Más fácil)

1. **Preparar repositorio**:
   ```bash
   git add .
   git commit -m "Preparar para deployment"
   git push origin main
   ```

2. **Crear cuenta en Railway**:
   - Ve a [railway.app](https://railway.app)
   - Conecta tu GitHub
   - Crea nuevo proyecto desde repositorio

3. **Configurar variables de entorno**:
   ```env
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   REDIS_URL=${{Redis.REDIS_URL}}
   SECRET_KEY=tu-clave-super-secreta
   INSTAGRAM_CLIENT_ID=tu-instagram-client-id
   INSTAGRAM_CLIENT_SECRET=tu-instagram-client-secret
   YOUTUBE_API_KEY=tu-youtube-api-key
   ODOO_URL=https://tu-odoo-instance.com
   ODOO_DATABASE=tu-odoo-database
   ODOO_USERNAME=tu-odoo-username
   ODOO_PASSWORD=tu-odoo-password
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=tu-email@gmail.com
   SMTP_PASSWORD=tu-app-password
   EMAIL_FROM=no-reply@tudominio.com
   CORS_ORIGINS=["https://tudominio.com"]
   DEBUG=false
   LOG_LEVEL=info
   ```

4. **Deploy automático**:
   - Railway detectará automáticamente la aplicación Python
   - Instalará dependencias
   - Creará base de datos PostgreSQL
   - Ejecutará migraciones

### 🎨 Render (Alternativa)

1. **Crear cuenta en Render**:
   - Ve a [render.com](https://render.com)
   - Conecta tu GitHub
   - Crea Web Service

2. **Configurar servicio**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

3. **Crear base de datos**:
   - New + → PostgreSQL
   - Configurar variables de entorno

4. **Deploy**:
   - Render construirá y desplegará automáticamente

---

## 🐳 OPCIÓN 3: DOCKER

### Requisitos
- Docker Desktop
- Docker Compose

### Pasos
1. **Configurar variables de entorno**:
   ```bash
   copy env.example .env
   # Editar .env con tus configuraciones
   ```

2. **Deploy con Docker**:
   ```bash
   # Ejecutar en Windows
   deploy_docker.bat
   
   # O manualmente
   docker-compose build
   docker-compose up -d
   docker-compose exec app alembic upgrade head
   ```

3. **Acceder a la aplicación**:
   - 🌐 Servidor: http://localhost:8000
   - 📚 Documentación: http://localhost:8000/docs
   - 🌸 Flower: http://localhost:5555

---

## 🔧 Configuración de Variables de Entorno

### Variables Obligatorias
```env
# Base de datos
DATABASE_URL=postgresql://user:password@host:5432/database

# JWT
SECRET_KEY=tu-clave-super-secreta-aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Variables Opcionales
```env
# Redis (para cache y colas)
REDIS_URL=redis://host:6379/0

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

---

## 🚨 Troubleshooting

### Error: "Database connection failed"
- Verifica que PostgreSQL esté corriendo
- Revisa la URL de conexión en `.env`
- Asegúrate de que la base de datos existe

### Error: "Module not found"
- Activa el entorno virtual: `venv\Scripts\activate`
- Instala dependencias: `pip install -r requirements.txt`

### Error: "Port already in use"
- Cambia el puerto en el comando: `--port 8001`
- O mata el proceso que usa el puerto 8000

### Error: "Migration failed"
- Verifica la conexión a la base de datos
- Ejecuta: `alembic upgrade head`
- Si persiste, recrea la base de datos

---

## 📞 Soporte

Si tienes problemas con el deployment:

1. **Revisa los logs**:
   ```bash
   # Local
   uvicorn app.main:app --reload
   
   # Docker
   docker-compose logs -f
   
   # Railway
   railway logs
   ```

2. **Verifica las variables de entorno**:
   - Asegúrate de que todas las variables estén configuradas
   - Revisa que no haya espacios extra
   - Verifica que las URLs sean correctas

3. **Consulta la documentación**:
   - README.md
   - Documentación de la API en `/docs`
   - Logs de la aplicación

---

## 🎯 Recomendaciones

### Para Desarrollo
- Usa **desarrollo local** con PostgreSQL
- Configura todas las variables de entorno
- Usa datos de prueba

### Para Producción
- Usa **Railway** o **Render** para facilidad
- Configura dominio personalizado
- Habilita SSL
- Configura backup automático
- Monitorea logs y métricas

### Para Empresas
- Usa **Docker** en VPS propio
- Configura CI/CD con GitHub Actions
- Implementa monitoreo avanzado
- Configura backup y disaster recovery
