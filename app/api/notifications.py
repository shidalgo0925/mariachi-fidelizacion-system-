from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.site_config import SiteConfig
from app.schemas.notification import (
    NotificationCreate, NotificationResponse, NotificationList, NotificationSearch,
    NotificationTemplateCreate, NotificationTemplateUpdate, NotificationTemplateResponse, NotificationTemplateList,
    NotificationSubscriptionCreate, NotificationSubscriptionUpdate, NotificationSubscriptionResponse, NotificationSubscriptionList,
    NotificationPreferences, NotificationPreferencesUpdate,
    NotificationBatch, NotificationBatchResponse,
    NotificationAnalytics, NotificationTest, NotificationTestResponse
)
from app.services.notification_service import NotificationService
from app.api.dependencies import (
    get_current_user, get_site_config, require_site_access, 
    require_user_ownership, require_active_user
)
from typing import Optional, List
import structlog
from datetime import datetime, timedelta

logger = structlog.get_logger()

router = APIRouter()

@router.post("/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(
    notification_data: NotificationCreate,
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Crear nueva notificación"""
    try:
        notification_service = NotificationService(db)
        
        notification = await notification_service.create_notification(
            notification_data=notification_data,
            site_id=site_config.site_id
        )
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error creating notification"
            )
        
        logger.info("Notification created", 
                   notification_id=notification.id, 
                   user_id=notification_data.user_id, 
                   site_id=site_config.site_id,
                   type=notification_data.type.value)
        
        return notification
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating notification", 
                    user_id=notification_data.user_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating notification"
        )

@router.get("/me", response_model=NotificationList)
async def get_my_notifications(
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(20, ge=1, le=100, description="Tamaño de página"),
    unread_only: bool = Query(False, description="Solo notificaciones no leídas"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener notificaciones del usuario actual"""
    try:
        notification_service = NotificationService(db)
        
        result = await notification_service.get_user_notifications(
            user_id=current_user.id,
            site_id=current_user.site_id,
            page=page,
            size=size,
            unread_only=unread_only
        )
        
        logger.info("User notifications retrieved", 
                   user_id=current_user.id, 
                   site_id=current_user.site_id, 
                   total=result["total"])
        
        return NotificationList(**result)
        
    except Exception as e:
        logger.error("Error getting user notifications", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user notifications"
        )

@router.put("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marcar notificación como leída"""
    try:
        notification_service = NotificationService(db)
        
        success = await notification_service.mark_notification_as_read(
            notification_id=notification_id,
            user_id=current_user.id,
            site_id=current_user.site_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        logger.info("Notification marked as read", 
                   notification_id=notification_id, 
                   user_id=current_user.id, 
                   site_id=current_user.site_id)
        
        return {"message": "Notification marked as read"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error marking notification as read", 
                    notification_id=notification_id, 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error marking notification as read"
        )

@router.put("/read-all")
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marcar todas las notificaciones como leídas"""
    try:
        notification_service = NotificationService(db)
        
        success = await notification_service.mark_all_notifications_as_read(
            user_id=current_user.id,
            site_id=current_user.site_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error marking all notifications as read"
            )
        
        logger.info("All notifications marked as read", 
                   user_id=current_user.id, 
                   site_id=current_user.site_id)
        
        return {"message": "All notifications marked as read"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error marking all notifications as read", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error marking all notifications as read"
        )

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar notificación"""
    try:
        notification_service = NotificationService(db)
        
        success = await notification_service.delete_notification(
            notification_id=notification_id,
            user_id=current_user.id,
            site_id=current_user.site_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        logger.info("Notification deleted", 
                   notification_id=notification_id, 
                   user_id=current_user.id, 
                   site_id=current_user.site_id)
        
        return {"message": "Notification deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting notification", 
                    notification_id=notification_id, 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting notification"
        )

@router.post("/batch", response_model=NotificationBatchResponse)
async def send_batch_notifications(
    batch_data: NotificationBatch,
    background_tasks: BackgroundTasks,
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Enviar notificaciones masivas"""
    try:
        notification_service = NotificationService(db)
        
        result = await notification_service.send_batch_notifications(
            batch_data=batch_data,
            site_id=site_config.site_id
        )
        
        logger.info("Batch notifications sent", 
                   site_id=site_config.site_id,
                   total_users=result["total_users"],
                   notifications_created=result["notifications_created"])
        
        return NotificationBatchResponse(**result)
        
    except Exception as e:
        logger.error("Error sending batch notifications", 
                    site_id=site_config.site_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error sending batch notifications"
        )

@router.get("/analytics", response_model=NotificationAnalytics)
async def get_notification_analytics(
    period: str = Query("30d", description="Período de análisis"),
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Obtener analytics de notificaciones"""
    try:
        notification_service = NotificationService(db)
        
        # Convertir período a días
        days = 30
        if period.endswith('d'):
            days = int(period[:-1])
        elif period.endswith('w'):
            days = int(period[:-1]) * 7
        elif period.endswith('m'):
            days = int(period[:-1]) * 30
        
        analytics = await notification_service.get_notification_analytics(
            site_id=site_config.site_id,
            days=days
        )
        
        logger.info("Notification analytics retrieved", 
                   site_id=site_config.site_id, 
                   period=period)
        
        return NotificationAnalytics(**analytics)
        
    except Exception as e:
        logger.error("Error getting notification analytics", 
                    site_id=site_config.site_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving notification analytics"
        )

@router.post("/test", response_model=NotificationTestResponse)
async def test_notification(
    test_data: NotificationTest,
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Probar notificación"""
    try:
        notification_service = NotificationService(db)
        
        # Crear notificación de prueba
        test_notification_data = NotificationCreate(
            user_id=1,  # Usuario de prueba
            type=test_data.type,
            title=test_data.title,
            message=test_data.message,
            channels=test_data.channels,
            template_id=test_data.template_id,
            template_variables=test_data.template_variables
        )
        
        # Enviar notificación de prueba
        test_results = {}
        for channel in test_data.channels:
            try:
                if channel == "email" and test_data.test_email:
                    # Simular envío de email
                    test_results[channel] = {"success": True, "message": "Test email sent"}
                elif channel == "sms" and test_data.test_phone:
                    # Simular envío de SMS
                    test_results[channel] = {"success": True, "message": "Test SMS sent"}
                elif channel == "push":
                    # Simular envío de push
                    test_results[channel] = {"success": True, "message": "Test push sent"}
                elif channel == "in_app":
                    # Simular notificación in-app
                    test_results[channel] = {"success": True, "message": "Test in-app notification created"}
                else:
                    test_results[channel] = {"success": False, "message": "Test data not provided"}
            except Exception as e:
                test_results[channel] = {"success": False, "message": str(e)}
        
        success = all(result["success"] for result in test_results.values())
        
        logger.info("Notification test completed", 
                   site_id=site_config.site_id,
                   success=success,
                   test_results=test_results)
        
        return NotificationTestResponse(
            success=success,
            message="Notification test completed",
            test_results=test_results
        )
        
    except Exception as e:
        logger.error("Error testing notification", 
                    site_id=site_config.site_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error testing notification"
        )

@router.get("/templates", response_model=NotificationTemplateList)
async def get_notification_templates(
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(20, ge=1, le=100, description="Tamaño de página"),
    type: Optional[str] = Query(None, description="Filtrar por tipo"),
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Obtener templates de notificaciones"""
    try:
        from app.models.notification_template import NotificationTemplate
        
        query = db.query(NotificationTemplate).filter(
            NotificationTemplate.site_id == site_config.site_id
        )
        
        if type:
            query = query.filter(NotificationTemplate.type == type)
        
        total = query.count()
        templates = query.order_by(NotificationTemplate.created_at.desc()).offset((page - 1) * size).limit(size).all()
        total_pages = (total + size - 1) // size
        
        logger.info("Notification templates retrieved", 
                   site_id=site_config.site_id, 
                   total=total)
        
        return NotificationTemplateList(
            templates=templates,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error("Error getting notification templates", 
                    site_id=site_config.site_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving notification templates"
        )

@router.post("/templates", response_model=NotificationTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_notification_template(
    template_data: NotificationTemplateCreate,
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Crear template de notificación"""
    try:
        from app.models.notification_template import NotificationTemplate
        
        template = NotificationTemplate(
            site_id=site_config.site_id,
            name=template_data.name,
            type=template_data.type,
            subject=template_data.subject,
            content=template_data.content,
            variables=json.dumps(template_data.variables) if template_data.variables else None,
            is_active=template_data.is_active
        )
        
        db.add(template)
        db.commit()
        db.refresh(template)
        
        logger.info("Notification template created", 
                   template_id=template.id, 
                   site_id=site_config.site_id,
                   name=template_data.name)
        
        return template
        
    except Exception as e:
        db.rollback()
        logger.error("Error creating notification template", 
                    site_id=site_config.site_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating notification template"
        )

@router.get("/preferences", response_model=NotificationPreferences)
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener preferencias de notificación del usuario"""
    try:
        from app.models.notification_template import NotificationPreferences as NotificationPreferencesModel
        
        preferences = db.query(NotificationPreferencesModel).filter(
            NotificationPreferencesModel.user_id == current_user.id,
            NotificationPreferencesModel.site_id == current_user.site_id
        ).first()
        
        if not preferences:
            # Crear preferencias por defecto
            preferences = NotificationPreferencesModel(
                site_id=current_user.site_id,
                user_id=current_user.id,
                email_enabled=True,
                push_enabled=True,
                sms_enabled=False,
                in_app_enabled=True,
                timezone="UTC",
                language="es"
            )
            db.add(preferences)
            db.commit()
            db.refresh(preferences)
        
        logger.info("Notification preferences retrieved", 
                   user_id=current_user.id, 
                   site_id=current_user.site_id)
        
        return preferences
        
    except Exception as e:
        logger.error("Error getting notification preferences", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving notification preferences"
        )

@router.put("/preferences", response_model=NotificationPreferences)
async def update_notification_preferences(
    preferences_data: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar preferencias de notificación del usuario"""
    try:
        from app.models.notification_template import NotificationPreferences as NotificationPreferencesModel
        
        preferences = db.query(NotificationPreferencesModel).filter(
            NotificationPreferencesModel.user_id == current_user.id,
            NotificationPreferencesModel.site_id == current_user.site_id
        ).first()
        
        if not preferences:
            # Crear preferencias si no existen
            preferences = NotificationPreferencesModel(
                site_id=current_user.site_id,
                user_id=current_user.id
            )
            db.add(preferences)
        
        # Actualizar campos
        for field, value in preferences_data.dict(exclude_unset=True).items():
            setattr(preferences, field, value)
        
        preferences.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(preferences)
        
        logger.info("Notification preferences updated", 
                   user_id=current_user.id, 
                   site_id=current_user.site_id)
        
        return preferences
        
    except Exception as e:
        db.rollback()
        logger.error("Error updating notification preferences", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating notification preferences"
        )
