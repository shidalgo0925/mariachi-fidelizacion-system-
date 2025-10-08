from celery import current_task
from app.celery import celery_app
from app.database import SessionLocal
from app.services.analytics_service import AnalyticsService
from app.services.report_service import ReportService
import structlog

logger = structlog.get_logger()

@celery_app.task(bind=True)
def generate_daily_reports(self, site_id: str):
    """Generar reportes diarios automáticos"""
    try:
        db = SessionLocal()
        report_service = ReportService(db)
        
        from app.schemas.analytics import ReportRequest, ReportType, ReportFormat
        from datetime import datetime, timedelta
        
        # Generar reporte de actividad diaria
        report_request = ReportRequest(
            site_id=site_id,
            report_type=ReportType.USER_ACTIVITY,
            format=ReportFormat.PDF,
            period="1d",
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow()
        )
        
        result = report_service.generate_report(report_request)
        
        if result.status == "completed":
            logger.info("Daily report generated", 
                       site_id=site_id, 
                       report_id=result.report_id)
            return {"status": "success", "report_id": result.report_id}
        else:
            logger.error("Daily report generation failed", 
                        site_id=site_id, 
                        error=result.error_message)
            return {"status": "error", "message": result.error_message}
        
    except Exception as e:
        logger.error("Error generating daily report", 
                    site_id=site_id, 
                    error=str(e))
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@celery_app.task(bind=True)
def update_analytics_cache(self, site_id: str):
    """Actualizar caché de analytics"""
    try:
        db = SessionLocal()
        analytics_service = AnalyticsService(db)
        
        # Actualizar métricas del dashboard
        dashboard = analytics_service.get_dashboard_metrics(site_id, "30d")
        
        # Actualizar métricas en tiempo real
        realtime = analytics_service.get_realtime_metrics(site_id)
        
        logger.info("Analytics cache updated", 
                   site_id=site_id)
        
        return {"status": "success", "dashboard_updated": True, "realtime_updated": True}
        
    except Exception as e:
        logger.error("Error updating analytics cache", 
                    site_id=site_id, 
                    error=str(e))
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@celery_app.task(bind=True)
def generate_weekly_summary(self, site_id: str):
    """Generar resumen semanal"""
    try:
        db = SessionLocal()
        analytics_service = AnalyticsService(db)
        
        from datetime import datetime, timedelta
        
        # Obtener métricas de la semana
        week_start = datetime.utcnow() - timedelta(days=7)
        week_end = datetime.utcnow()
        
        # Generar resumen
        summary = analytics_service.get_weekly_summary(site_id, week_start, week_end)
        
        logger.info("Weekly summary generated", 
                   site_id=site_id, 
                   summary=summary)
        
        return {"status": "success", "summary": summary}
        
    except Exception as e:
        logger.error("Error generating weekly summary", 
                    site_id=site_id, 
                    error=str(e))
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@celery_app.task(bind=True)
def cleanup_old_analytics_data(self, site_id: str, days_to_keep: int = 90):
    """Limpiar datos de analytics antiguos"""
    try:
        db = SessionLocal()
        
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Limpiar datos de analytics antiguos
        from app.models.interaction import Interaction
        from app.models.notification import Notification
        
        # Limpiar interacciones antiguas
        old_interactions = db.query(Interaction).filter(
            Interaction.site_id == site_id,
            Interaction.fecha_interaccion < cutoff_date
        ).count()
        
        db.query(Interaction).filter(
            Interaction.site_id == site_id,
            Interaction.fecha_interaccion < cutoff_date
        ).delete()
        
        # Limpiar notificaciones antiguas
        old_notifications = db.query(Notification).filter(
            Notification.site_id == site_id,
            Notification.created_at < cutoff_date
        ).count()
        
        db.query(Notification).filter(
            Notification.site_id == site_id,
            Notification.created_at < cutoff_date
        ).delete()
        
        db.commit()
        
        logger.info("Old analytics data cleaned up", 
                   site_id=site_id, 
                   old_interactions=old_interactions,
                   old_notifications=old_notifications)
        
        return {
            "status": "success", 
            "old_interactions": old_interactions,
            "old_notifications": old_notifications
        }
        
    except Exception as e:
        logger.error("Error cleaning up old analytics data", 
                    site_id=site_id, 
                    error=str(e))
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@celery_app.task(bind=True)
def generate_monthly_report(self, site_id: str):
    """Generar reporte mensual"""
    try:
        db = SessionLocal()
        report_service = ReportService(db)
        
        from app.schemas.analytics import ReportRequest, ReportType, ReportFormat
        from datetime import datetime, timedelta
        
        # Generar reporte mensual
        report_request = ReportRequest(
            site_id=site_id,
            report_type=ReportType.ENGAGEMENT,
            format=ReportFormat.XLSX,
            period="30d",
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow()
        )
        
        result = report_service.generate_report(report_request)
        
        if result.status == "completed":
            logger.info("Monthly report generated", 
                       site_id=site_id, 
                       report_id=result.report_id)
            return {"status": "success", "report_id": result.report_id}
        else:
            logger.error("Monthly report generation failed", 
                        site_id=site_id, 
                        error=result.error_message)
            return {"status": "error", "message": result.error_message}
        
    except Exception as e:
        logger.error("Error generating monthly report", 
                    site_id=site_id, 
                    error=str(e))
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
