# Sistema de Fidelización Multi-Tenant

Sistema completo de fidelización de clientes con soporte multi-tenant, desarrollado en Python con FastAPI.

## 🎯 Características Principales

- **Multi-Tenant**: Soporte para múltiples sitios/clientes
- **Sistema de Puntos**: Acumulación de puntos por acciones
- **Stickers de Descuento**: Generación automática de códigos de descuento
- **Videos Progresivos**: Sistema de videos con tracking de progreso
- **Engagement**: Likes, comentarios, reseñas
- **Integración Instagram**: Verificación de seguimiento
- **Integración Odoo**: Sincronización de datos
- **Notificaciones**: Multi-canal (email, push, SMS, in-app)
- **Analytics**: Dashboard completo con métricas y reportes

## 🛠️ Tecnologías

- **Backend**: Python 3.9+ + FastAPI
- **Base de Datos**: PostgreSQL
- **Cache**: Redis
- **Tareas**: Celery
- **Migraciones**: Alembic
- **Validación**: Pydantic
- **Logging**: Structlog

## 📦 Instalación

### 1. Clonar el repositorio
```bash
git clone <repository-url>
cd mariachi-fidelizacion-multitenant
```

### 2. Crear entorno virtual
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
```bash
cp env.example .env
# Editar .env con tus configuraciones
```

### 5. Configurar base de datos
```bash
# Crear base de datos PostgreSQL
createdb mariachi_fidelizacion

# Ejecutar migraciones
alembic upgrade head
```

### 6. Inicializar datos de prueba
```bash
python scripts/init_data.py
```

## 🚀 Ejecución

### Desarrollo
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Producción
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 📚 API Documentation

Una vez ejecutado el servidor, la documentación estará disponible en:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 Configuración

### Variables de Entorno

```env
# Base de datos
DATABASE_URL="postgresql://user:password@localhost:5432/mariachi_fidelizacion"

# Redis
REDIS_URL="redis://localhost:6379/0"

# JWT
SECRET_KEY="your-super-secret-key"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# APIs Externas
INSTAGRAM_CLIENT_ID=""
INSTAGRAM_CLIENT_SECRET=""
YOUTUBE_API_KEY=""

# Odoo
ODOO_URL=""
ODOO_DATABASE=""
ODOO_USERNAME=""
ODOO_PASSWORD=""

# Email
SMTP_HOST=""
SMTP_PORT=587
SMTP_USERNAME=""
SMTP_PASSWORD=""
EMAIL_FROM="no-reply@example.com"
```

## 🏗️ Arquitectura

```
app/
├── api/                 # Endpoints de la API
├── models/              # Modelos de base de datos
├── schemas/             # Esquemas Pydantic
├── services/            # Lógica de negocio
├── middleware/          # Middleware personalizado
├── utils/               # Utilidades
└── main.py             # Aplicación principal
```

## 📊 Endpoints Principales

### Autenticación
- `POST /api/auth/register` - Registro de usuario
- `POST /api/auth/login` - Inicio de sesión
- `POST /api/auth/refresh` - Renovar token

### Usuarios
- `GET /api/users/me` - Perfil del usuario
- `PUT /api/users/me` - Actualizar perfil
- `GET /api/users/me/stats` - Estadísticas del usuario

### Stickers
- `GET /api/stickers/me` - Stickers del usuario
- `POST /api/stickers/generate` - Generar sticker
- `GET /api/stickers/download/{id}` - Descargar sticker

### Videos
- `GET /api/videos/playlist` - Lista de videos
- `POST /api/videos/{id}/watch` - Marcar video como visto
- `GET /api/videos/{id}/progress` - Progreso del video

### Interacciones
- `POST /api/interactions/likes` - Dar like
- `POST /api/interactions/comments` - Comentar
- `POST /api/interactions/reviews` - Dejar reseña

### Instagram
- `POST /api/instagram/connect` - Conectar Instagram
- `POST /api/instagram/verify` - Verificar seguimiento

### Odoo
- `GET /api/odoo/config` - Configuración de Odoo
- `POST /api/odoo/sync` - Sincronizar datos
- `GET /api/odoo/analytics` - Analytics de sincronización

### Notificaciones
- `GET /api/notifications/me` - Notificaciones del usuario
- `PUT /api/notifications/{id}/read` - Marcar como leída
- `GET /api/notifications/preferences` - Preferencias

### Analytics
- `GET /api/analytics/dashboard` - Dashboard de métricas
- `POST /api/analytics/query` - Consulta personalizada
- `GET /api/analytics/realtime` - Métricas en tiempo real
- `POST /api/analytics/reports` - Generar reporte

## 🔒 Seguridad

- **JWT Tokens**: Autenticación basada en tokens
- **CORS**: Configuración de orígenes permitidos
- **Rate Limiting**: Límites de velocidad por endpoint
- **Validación**: Validación de datos con Pydantic
- **Logging**: Logs estructurados para auditoría

## 📈 Monitoreo

- **Health Check**: `/health` - Estado del sistema
- **Metrics**: `/metrics` - Métricas de Prometheus
- **Logs**: Logs estructurados con contexto
- **Analytics**: Dashboard de métricas de negocio

## 🚀 Deployment

### Docker
```bash
docker build -t mariachi-fidelizacion .
docker run -p 8000:8000 mariachi-fidelizacion
```

### Railway
1. Conectar repositorio GitHub
2. Configurar variables de entorno
3. Deploy automático

### Heroku
```bash
heroku create mariachi-fidelizacion
heroku addons:create heroku-postgresql:hobby-dev
heroku addons:create heroku-redis:hobby-dev
git push heroku main
```

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama para feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 📞 Soporte

Para soporte técnico o preguntas:
- Email: support@example.com
- Documentación: [docs.example.com](https://docs.example.com)
- Issues: [GitHub Issues](https://github.com/example/issues)

## 🎯 Roadmap

- [ ] Integración con WhatsApp
- [ ] Sistema de gamificación avanzado
- [ ] Dashboard de administración
- [ ] API móvil nativa
- [ ] Integración con más ERPs
- [ ] Sistema de afiliados
- [ ] Análisis predictivo con ML
