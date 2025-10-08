from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.site_config import SiteConfig
from app.models.odoo_sync_log import OdooSyncLog, OdooConfig
from app.schemas.odoo import (
    OdooConfigCreate, OdooConfigUpdate, OdooConfigResponse,
    OdooConnectionTest, OdooConnectionTestResponse,
    OdooSyncRequest, OdooSyncResponse, OdooSyncLogResponse,
    OdooAnalytics, OdooDashboard, OdooRetryRequest, OdooRetryResponse
)
from app.services.odoo_service import OdooService
from app.services.sync_service import SyncService
from app.api.dependencies import (
    get_current_user, get_site_config, require_site_access, 
    require_user_ownership, require_active_user
)
from typing import Optional, List
import structlog
from datetime import datetime, timedelta

logger = structlog.get_logger()

router = APIRouter()

@router.post("/config", response_model=OdooConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_odoo_config(
    config_data: OdooConfigCreate,
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Crear configuración de Odoo para el sitio"""
    try:
        # Verificar si ya existe configuración
        existing_config = db.query(OdooConfig).filter(
            OdooConfig.site_id == site_config.site_id
        ).first()
        
        if existing_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Odoo configuration already exists for this site"
            )
        
        # Crear nueva configuración
        odoo_config = OdooConfig(
            site_id=site_config.site_id,
            odoo_url=config_data.odoo_url,
            odoo_database=config_data.odoo_database,
            odoo_username=config_data.odoo_username,
            odoo_password=config_data.odoo_password,
            auto_sync=config_data.auto_sync,
            sync_interval=config_data.sync_interval,
            max_retries=config_data.max_retries
        )
        
        db.add(odoo_config)
        db.commit()
        db.refresh(odoo_config)
        
        # Habilitar integración en SiteConfig
        site_config.odoo_integration = True
        site_config.odoo_url = config_data.odoo_url
        site_config.odoo_database = config_data.odoo_database
        site_config.odoo_username = config_data.odoo_username
        site_config.odoo_password = config_data.odoo_password
        db.commit()
        
        logger.info("Odoo configuration created", 
                   site_id=site_config.site_id, 
                   odoo_url=config_data.odoo_url)
        
        return odoo_config
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error creating Odoo configuration", 
                    site_id=site_config.site_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating Odoo configuration"
        )

@router.put("/config", response_model=OdooConfigResponse)
async def update_odoo_config(
    config_data: OdooConfigUpdate,
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Actualizar configuración de Odoo"""
    try:
        # Obtener configuración existente
        odoo_config = db.query(OdooConfig).filter(
            OdooConfig.site_id == site_config.site_id
        ).first()
        
        if not odoo_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Odoo configuration not found"
            )
        
        # Actualizar campos
        for field, value in config_data.dict(exclude_unset=True).items():
            setattr(odoo_config, field, value)
        
        odoo_config.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(odoo_config)
        
        # Actualizar SiteConfig
        if config_data.odoo_url:
            site_config.odoo_url = config_data.odoo_url
        if config_data.odoo_database:
            site_config.odoo_database = config_data.odoo_database
        if config_data.odoo_username:
            site_config.odoo_username = config_data.odoo_username
        if config_data.odoo_password:
            site_config.odoo_password = config_data.odoo_password
        
        db.commit()
        
        logger.info("Odoo configuration updated", 
                   site_id=site_config.site_id)
        
        return odoo_config
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error updating Odoo configuration", 
                    site_id=site_config.site_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating Odoo configuration"
        )

@router.get("/config", response_model=OdooConfigResponse)
async def get_odoo_config(
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Obtener configuración de Odoo"""
    try:
        odoo_config = db.query(OdooConfig).filter(
            OdooConfig.site_id == site_config.site_id
        ).first()
        
        if not odoo_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Odoo configuration not found"
            )
        
        return odoo_config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting Odoo configuration", 
                    site_id=site_config.site_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving Odoo configuration"
        )

@router.delete("/config")
async def delete_odoo_config(
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Eliminar configuración de Odoo"""
    try:
        odoo_config = db.query(OdooConfig).filter(
            OdooConfig.site_id == site_config.site_id
        ).first()
        
        if not odoo_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Odoo configuration not found"
            )
        
        # Deshabilitar integración en SiteConfig
        site_config.odoo_integration = False
        site_config.odoo_url = None
        site_config.odoo_database = None
        site_config.odoo_username = None
        site_config.odoo_password = None
        db.commit()
        
        # Eliminar configuración
        db.delete(odoo_config)
        db.commit()
        
        logger.info("Odoo configuration deleted", 
                   site_id=site_config.site_id)
        
        return {"message": "Odoo configuration deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error deleting Odoo configuration", 
                    site_id=site_config.site_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting Odoo configuration"
        )

@router.post("/test-connection", response_model=OdooConnectionTestResponse)
async def test_odoo_connection(
    test_data: OdooConnectionTest,
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Probar conexión con Odoo"""
    try:
        # Crear configuración temporal para la prueba
        temp_config = SiteConfig(
            site_id=site_config.site_id,
            odoo_url=test_data.odoo_url,
            odoo_database=test_data.odoo_database,
            odoo_username=test_data.odoo_username,
            odoo_password=test_data.odoo_password
        )
        
        odoo_service = OdooService(db)
        result = await odoo_service.test_connection(temp_config)
        
        logger.info("Odoo connection test completed", 
                   site_id=site_config.site_id, 
                   success=result.success)
        
        return result
        
    except Exception as e:
        logger.error("Error testing Odoo connection", 
                    site_id=site_config.site_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error testing Odoo connection"
        )

@router.post("/sync", response_model=OdooSyncResponse)
async def sync_data(
    sync_request: OdooSyncRequest,
    background_tasks: BackgroundTasks,
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Sincronizar datos con Odoo"""
    try:
        if not site_config.odoo_integration:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Odoo integration not enabled for this site"
            )
        
        sync_service = SyncService(db)
        
        if sync_request.sync_all:
            # Sincronizar todos los datos del sitio
            result = await sync_service.sync_site_data(
                site_id=site_config.site_id,
                force_sync=sync_request.force_sync
            )
        else:
            # Sincronizar registros específicos
            result = await sync_service.sync_specific_records(
                site_id=site_config.site_id,
                model_type=sync_request.model_type,
                record_ids=sync_request.record_ids,
                force_sync=sync_request.force_sync
            )
        
        logger.info("Odoo sync completed", 
                   site_id=site_config.site_id, 
                   success=result.success,
                   synced_count=result.synced_count)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error syncing data", 
                    site_id=site_config.site_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error syncing data"
        )

@router.get("/sync-logs", response_model=List[OdooSyncLogResponse])
async def get_sync_logs(
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(20, ge=1, le=100, description="Tamaño de página"),
    model_type: Optional[str] = Query(None, description="Filtrar por tipo de modelo"),
    status: Optional[str] = Query(None, description="Filtrar por estado"),
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Obtener logs de sincronización"""
    try:
        query = db.query(OdooSyncLog).filter(
            OdooSyncLog.site_id == site_config.site_id
        )
        
        # Aplicar filtros
        if model_type:
            query = query.filter(OdooSyncLog.model_type == model_type)
        if status:
            query = query.filter(OdooSyncLog.status == status)
        
        # Ordenar por timestamp descendente
        query = query.order_by(OdooSyncLog.sync_timestamp.desc())
        
        # Paginación
        logs = query.offset((page - 1) * size).limit(size).all()
        
        logger.info("Sync logs retrieved", 
                   site_id=site_config.site_id, 
                   count=len(logs))
        
        return logs
        
    except Exception as e:
        logger.error("Error getting sync logs", 
                    site_id=site_config.site_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving sync logs"
        )

@router.post("/retry", response_model=OdooRetryResponse)
async def retry_failed_syncs(
    retry_request: OdooRetryRequest,
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Reintentar sincronizaciones fallidas"""
    try:
        sync_service = SyncService(db)
        
        if retry_request.sync_log_id:
            # Reintentar sincronización específica
            result = await sync_service.retry_specific_sync(
                site_id=site_config.site_id,
                sync_log_id=retry_request.sync_log_id,
                force_retry=retry_request.force_retry
            )
        else:
            # Reintentar todas las sincronizaciones fallidas
            result = await sync_service.retry_failed_syncs(
                site_id=site_config.site_id
            )
        
        logger.info("Retry completed", 
                   site_id=site_config.site_id, 
                   success=result.success)
        
        return OdooRetryResponse(
            success=result.success,
            message=result.message,
            new_sync_log=result.sync_logs[0] if result.sync_logs else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrying syncs", 
                    site_id=site_config.site_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrying syncs"
        )

@router.get("/analytics", response_model=OdooAnalytics)
async def get_odoo_analytics(
    period: str = Query("30d", description="Período de análisis"),
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Obtener analytics de Odoo"""
    try:
        sync_service = SyncService(db)
        
        # Convertir período a días
        days = 30
        if period.endswith('d'):
            days = int(period[:-1])
        elif period.endswith('w'):
            days = int(period[:-1]) * 7
        elif period.endswith('m'):
            days = int(period[:-1]) * 30
        
        analytics = await sync_service.get_sync_statistics(
            site_id=site_config.site_id,
            days=days
        )
        
        logger.info("Odoo analytics retrieved", 
                   site_id=site_config.site_id, 
                   period=period)
        
        return OdooAnalytics(**analytics)
        
    except Exception as e:
        logger.error("Error getting Odoo analytics", 
                    site_id=site_config.site_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving Odoo analytics"
        )

@router.get("/dashboard", response_model=OdooDashboard)
async def get_odoo_dashboard(
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Obtener dashboard de Odoo"""
    try:
        # Obtener configuración de Odoo
        odoo_config = db.query(OdooConfig).filter(
            OdooConfig.site_id == site_config.site_id
        ).first()
        
        if not odoo_config:
            return OdooDashboard(
                connection_status="disconnected",
                message="Odoo configuration not found"
            )
        
        # Obtener estadísticas de sincronización
        sync_service = SyncService(db)
        sync_stats = await sync_service.get_sync_statistics(
            site_id=site_config.site_id,
            days=7
        )
        
        # Obtener contadores
        total_partners = db.query(User).filter(
            and_(
                User.site_id == site_config.site_id,
                User.activo == True
            )
        ).count()
        
        total_products = db.query(Sticker).filter(
            Sticker.site_id == site_config.site_id
        ).count()
        
        # Obtener logs recientes
        recent_logs = db.query(OdooSyncLog).filter(
            OdooSyncLog.site_id == site_config.site_id
        ).order_by(OdooSyncLog.sync_timestamp.desc()).limit(10).all()
        
        recent_activities = []
        for log in recent_logs:
            recent_activities.append({
                "id": log.id,
                "model_type": log.model_type.value,
                "operation": log.operation.value,
                "status": log.status.value,
                "timestamp": log.sync_timestamp,
                "error_message": log.error_message
            })
        
        dashboard = OdooDashboard(
            connection_status=odoo_config.connection_status,
            last_sync=odoo_config.last_sync,
            total_partners=total_partners,
            total_products=total_products,
            total_orders=0,  # TODO: Implementar contador de órdenes
            pending_syncs=len([log for log in recent_logs if log.status == "pending"]),
            failed_syncs=len([log for log in recent_logs if log.status == "failed"]),
            sync_success_rate=sync_stats["success_rate"],
            recent_activities=recent_activities,
            sync_statistics=sync_stats
        )
        
        logger.info("Odoo dashboard retrieved", 
                   site_id=site_config.site_id)
        
        return dashboard
        
    except Exception as e:
        logger.error("Error getting Odoo dashboard", 
                    site_id=site_config.site_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving Odoo dashboard"
        )
