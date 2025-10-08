from celery import current_task
from app.celery import celery_app
from app.database import SessionLocal
from app.services.sync_service import SyncService
import structlog

logger = structlog.get_logger()

@celery_app.task(bind=True)
def sync_site_data(self, site_id: str, force_sync: bool = False):
    """Sincronizar datos de un sitio con Odoo"""
    try:
        db = SessionLocal()
        sync_service = SyncService(db)
        
        # Actualizar estado de la tarea
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": "Starting sync"}
        )
        
        # Sincronizar datos
        result = sync_service.sync_site_data(site_id, force_sync)
        
        if result.success:
            logger.info("Site data synced successfully", 
                       site_id=site_id, 
                       synced_count=result.synced_count)
            return {
                "status": "success", 
                "synced_count": result.synced_count,
                "failed_count": result.failed_count
            }
        else:
            logger.error("Site data sync failed", 
                        site_id=site_id, 
                        errors=result.errors)
            return {
                "status": "error", 
                "message": result.message,
                "errors": result.errors
            }
        
    except Exception as e:
        logger.error("Error syncing site data", 
                    site_id=site_id, 
                    error=str(e))
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@celery_app.task(bind=True)
def sync_all_sites(self):
    """Sincronizar todos los sitios con Odoo"""
    try:
        db = SessionLocal()
        sync_service = SyncService(db)
        
        # Obtener todos los sitios con integración Odoo habilitada
        from app.models.site_config import SiteConfig
        sites = db.query(SiteConfig).filter(
            SiteConfig.odoo_integration == True
        ).all()
        
        results = []
        total = len(sites)
        
        for i, site in enumerate(sites):
            # Actualizar progreso
            current_task.update_state(
                state="PROGRESS",
                meta={"current": i + 1, "total": total, "status": f"Syncing {site.site_id}"}
            )
            
            # Sincronizar sitio
            result = sync_service.sync_site_data(site.site_id)
            results.append({
                "site_id": site.site_id,
                "success": result.success,
                "synced_count": result.synced_count,
                "failed_count": result.failed_count
            })
        
        logger.info("All sites synced", 
                   total_sites=total, 
                   successful_sites=len([r for r in results if r["success"]]))
        
        return {"status": "success", "total": total, "results": results}
        
    except Exception as e:
        logger.error("Error syncing all sites", error=str(e))
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@celery_app.task(bind=True)
def retry_failed_syncs(self, site_id: str):
    """Reintentar sincronizaciones fallidas"""
    try:
        db = SessionLocal()
        sync_service = SyncService(db)
        
        result = sync_service.retry_failed_syncs(site_id)
        
        if result.success:
            logger.info("Failed syncs retried successfully", 
                       site_id=site_id, 
                       synced_count=result.synced_count)
            return {
                "status": "success", 
                "synced_count": result.synced_count,
                "failed_count": result.failed_count
            }
        else:
            logger.error("Retry failed syncs failed", 
                        site_id=site_id, 
                        errors=result.errors)
            return {
                "status": "error", 
                "message": result.message,
                "errors": result.errors
            }
        
    except Exception as e:
        logger.error("Error retrying failed syncs", 
                    site_id=site_id, 
                    error=str(e))
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
