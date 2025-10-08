from celery import current_task
from app.celery import celery_app
from app.database import SessionLocal
from app.services.notification_service import NotificationService
import structlog

logger = structlog.get_logger()

@celery_app.task(bind=True)
def send_email_notification(self, notification_id: int, site_id: str):
    """Enviar notificación por email"""
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
        
        # Enviar email
        success = notification_service._send_email_notification(notification, site_id)
        
        if success:
            logger.info("Email notification sent", 
                       notification_id=notification_id, 
                       site_id=site_id)
            return {"status": "success", "message": "Email sent"}
        else:
            logger.error("Failed to send email notification", 
                        notification_id=notification_id, 
                        site_id=site_id)
            return {"status": "error", "message": "Failed to send email"}
        
    except Exception as e:
        logger.error("Error sending email notification", 
                    notification_id=notification_id, 
                    site_id=site_id, 
                    error=str(e))
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@celery_app.task(bind=True)
def send_bulk_emails(self, notification_ids: list, site_id: str):
    """Enviar emails masivos"""
    try:
        db = SessionLocal()
        notification_service = NotificationService(db)
        
        results = []
        total = len(notification_ids)
        
        for i, notification_id in enumerate(notification_ids):
            # Actualizar progreso
            current_task.update_state(
                state="PROGRESS",
                meta={"current": i + 1, "total": total, "status": "Sending emails"}
            )
            
            result = send_email_notification.delay(notification_id, site_id)
            results.append(result.get())
        
        logger.info("Bulk emails sent", 
                   site_id=site_id, 
                   total=total)
        
        return {"status": "success", "total": total, "results": results}
        
    except Exception as e:
        logger.error("Error sending bulk emails", 
                    site_id=site_id, 
                    error=str(e))
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
