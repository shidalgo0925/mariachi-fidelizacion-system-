from celery import Celery
from app.config import settings

# Crear instancia de Celery
celery_app = Celery(
    "mariachi_fidelizacion",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.email_tasks",
        "app.tasks.odoo_tasks",
        "app.tasks.notification_tasks",
        "app.tasks.analytics_tasks"
    ]
)

# Configuración de Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutos
    task_soft_time_limit=25 * 60,  # 25 minutos
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 hora
    task_routes={
        "app.tasks.email_tasks.*": {"queue": "email"},
        "app.tasks.odoo_tasks.*": {"queue": "odoo"},
        "app.tasks.notification_tasks.*": {"queue": "notifications"},
        "app.tasks.analytics_tasks.*": {"queue": "analytics"},
    },
    beat_schedule={
        "sync-odoo-data": {
            "task": "app.tasks.odoo_tasks.sync_all_sites",
            "schedule": 30.0 * 60,  # Cada 30 minutos
        },
        "cleanup-expired-notifications": {
            "task": "app.tasks.notification_tasks.cleanup_expired_notifications",
            "schedule": 24.0 * 60 * 60,  # Diario
        },
        "generate-daily-reports": {
            "task": "app.tasks.analytics_tasks.generate_daily_reports",
            "schedule": 24.0 * 60 * 60,  # Diario
        },
        "update-analytics-cache": {
            "task": "app.tasks.analytics_tasks.update_analytics_cache",
            "schedule": 5.0 * 60,  # Cada 5 minutos
        },
    },
)

# Configuración de colas
celery_app.conf.task_default_queue = "default"
celery_app.conf.task_queues = {
    "default": {
        "exchange": "default",
        "routing_key": "default",
    },
    "email": {
        "exchange": "email",
        "routing_key": "email",
    },
    "odoo": {
        "exchange": "odoo",
        "routing_key": "odoo",
    },
    "notifications": {
        "exchange": "notifications",
        "routing_key": "notifications",
    },
    "analytics": {
        "exchange": "analytics",
        "routing_key": "analytics",
    },
}
