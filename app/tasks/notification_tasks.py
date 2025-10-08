from celery import current_task
from app.celery import celery_app
from app.database import SessionLocal
from app.services.notification_service import NotificationService
import structlog

logger = structlog.get_logger()

@celery_app.task(bind=True)
def send_notification(self, notification_id: int, site_id: str):
    """Enviar notificación"""
    try:
        db = SessionLocal()
        notification_service = NotificationService(db)
        
        # Obtener notificación
        from app.models.notification import Notification
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.site_id == site_id
        ).first()
        
        if not notification:
            logger.error("Notification not found", 
                        notification_id=notification_id, 
                        site_id=site_id)
            return {"status": "error", "message": "Notification not found"}
        
        # Enviar notificación
        success = notification_service._send_notification(notification, site_id)
        
        if success:
            logger.info("Notification sent", 
                       notification_id=notification_id, 
                       site_id=site_id)
            return {"status": "success", "message": "Notification sent"}
        else:
            logger.error("Failed to send notification", 
                        notification_id=notification_id, 
                        site_id=site_id)
            return {"status": "error", "message": "Failed to send notification"}
        
    except Exception as e:
        logger.error("Error sending notification", 
                    notification_id=notification_id, 
                    site_id=site_id, 
                    error=str(e))
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@celery_app.task(bind=True)
def send_batch_notifications(self, notification_data: dict, site_id: str):
    """Enviar notificaciones masivas"""
    try:
        db = SessionLocal()
        notification_service = NotificationService(db)
        
        from app.schemas.notification import NotificationBatch
        batch = NotificationBatch(**notification_data)
        
        result = notification_service.send_batch_notifications(batch, site_id)
        
        logger.info("Batch notifications sent", 
                   site_id=site_id, 
                   total_users=result["total_users"],
                   notifications_created=result["notifications_created"])
        
        return result
        
    except Exception as e:
        logger.error("Error sending batch notifications", 
                    site_id=site_id, 
                    error=str(e))
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@celery_app.task(bind=True)
def cleanup_expired_notifications(self):
    """Limpiar notificaciones expiradas"""
    try:
        db = SessionLocal()
        notification_service = NotificationService(db)
        
        deleted_count = notification_service.cleanup_expired_notifications()
        
        logger.info("Expired notifications cleaned up", 
                   deleted_count=deleted_count)
        
        return {"status": "success", "deleted_count": deleted_count}
        
    except Exception as e:
        logger.error("Error cleaning up expired notifications", error=str(e))
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@celery_app.task(bind=True)
def send_digest_notifications(self, site_id: str):
    """Enviar notificaciones de resumen"""
    try:
        db = SessionLocal()
        
        # Obtener usuarios con resúmenes habilitados
        from app.models.notification_preferences import NotificationPreferences
        from app.models.user import User
        
        users_with_digest = db.query(User).join(NotificationPreferences).filter(
            User.site_id == site_id,
            User.activo == True,
            NotificationPreferences.digest_enabled == True
        ).all()
        
        sent_count = 0
        for user in users_with_digest:
            try:
                # Crear notificación de resumen
                from app.schemas.notification import NotificationCreate
                from app.models.notification import NotificationType, NotificationPriority
                
                notification_data = NotificationCreate(
                    user_id=user.id,
                    type=NotificationType.SYSTEM,
                    title="Resumen de actividad",
                    message=f"Hola {user.nombre}, aquí tienes un resumen de tu actividad reciente.",
                    priority=NotificationPriority.LOW,
                    channels=["in_app"]
                )
                
                notification_service = NotificationService(db)
                notification = notification_service.create_notification(notification_data, site_id)
                
                if notification:
                    sent_count += 1
                    
            except Exception as e:
                logger.error("Error sending digest to user", 
                            user_id=user.id, 
                            error=str(e))
        
        logger.info("Digest notifications sent", 
                   site_id=site_id, 
                   sent_count=sent_count,
                   total_users=len(users_with_digest))
        
        return {"status": "success", "sent_count": sent_count}
        
    except Exception as e:
        logger.error("Error sending digest notifications", 
                    site_id=site_id, 
                    error=str(e))
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
