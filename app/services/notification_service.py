from sqlalchemy.orm import Session
from app.models.user import User
from app.models.site_config import SiteConfig
from app.models.notification import Notification
from app.models.notification_template import NotificationTemplate
from app.models.notification_subscription import NotificationSubscription
from app.models.notification_preferences import NotificationPreferences
from app.schemas.notification import (
    NotificationCreate, NotificationType, NotificationStatus, NotificationChannel,
    NotificationTemplateType, NotificationBatch, NotificationAnalytics,
    NotificationPreferences as NotificationPreferencesSchema
)
from typing import Optional, List, Dict, Any
import structlog
from datetime import datetime, timedelta
import asyncio
import json
import requests
from jinja2 import Template
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = structlog.get_logger()

class NotificationService:
    """Servicio para manejar notificaciones del sistema multi-tenant"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_notification(
        self,
        notification_data: NotificationCreate,
        site_id: str
    ) -> Optional[Notification]:
        """Crear nueva notificación"""
        try:
            # Verificar que el usuario existe
            user = self.db.query(User).filter(
                User.id == notification_data.user_id,
                User.site_id == site_id,
                User.activo == True
            ).first()
            
            if not user:
                logger.warning("User not found or inactive", 
                             user_id=notification_data.user_id, 
                             site_id=site_id)
                return None
            
            # Crear notificación
            notification = Notification(
                site_id=site_id,
                user_id=notification_data.user_id,
                type=notification_data.type,
                title=notification_data.title,
                message=notification_data.message,
                priority=notification_data.priority,
                channels=json.dumps(notification_data.channels),
                metadata=json.dumps(notification_data.metadata) if notification_data.metadata else None,
                scheduled_at=notification_data.scheduled_at,
                expires_at=notification_data.expires_at,
                status=NotificationStatus.PENDING,
                template_id=notification_data.template_id,
                template_variables=json.dumps(notification_data.template_variables) if notification_data.template_variables else None
            )
            
            self.db.add(notification)
            self.db.commit()
            self.db.refresh(notification)
            
            # Enviar notificación si no está programada
            if not notification_data.scheduled_at or notification_data.scheduled_at <= datetime.utcnow():
                await self._send_notification(notification, site_id)
            
            logger.info("Notification created", 
                       notification_id=notification.id,
                       user_id=notification_data.user_id, 
                       site_id=site_id, 
                       type=notification_data.type.value,
                       priority=notification_data.priority.value)
            
            return notification
            
        except Exception as e:
            self.db.rollback()
            logger.error("Error creating notification", 
                        user_id=notification_data.user_id, 
                        site_id=site_id, 
                        type=notification_data.type.value, 
                        error=str(e))
            return None
    
    async def _send_notification(self, notification: Notification, site_id: str) -> bool:
        """Enviar notificación por los canales especificados"""
        try:
            # Obtener preferencias del usuario
            user_preferences = self.db.query(NotificationPreferences).filter(
                NotificationPreferences.user_id == notification.user_id,
                NotificationPreferences.site_id == site_id
            ).first()
            
            if not user_preferences:
                # Crear preferencias por defecto
                user_preferences = NotificationPreferences(
                    site_id=site_id,
                    user_id=notification.user_id,
                    email_enabled=True,
                    push_enabled=True,
                    sms_enabled=False,
                    in_app_enabled=True
                )
                self.db.add(user_preferences)
                self.db.commit()
            
            # Obtener canales habilitados
            channels = json.loads(notification.channels) if notification.channels else []
            sent_channels = []
            failed_channels = []
            
            for channel in channels:
                try:
                    if channel == NotificationChannel.EMAIL and user_preferences.email_enabled:
                        success = await self._send_email_notification(notification, site_id)
                        if success:
                            sent_channels.append(channel)
                        else:
                            failed_channels.append(channel)
                    
                    elif channel == NotificationChannel.PUSH and user_preferences.push_enabled:
                        success = await self._send_push_notification(notification, site_id)
                        if success:
                            sent_channels.append(channel)
                        else:
                            failed_channels.append(channel)
                    
                    elif channel == NotificationChannel.SMS and user_preferences.sms_enabled:
                        success = await self._send_sms_notification(notification, site_id)
                        if success:
                            sent_channels.append(channel)
                        else:
                            failed_channels.append(channel)
                    
                    elif channel == NotificationChannel.IN_APP and user_preferences.in_app_enabled:
                        # Las notificaciones in-app se crean automáticamente
                        sent_channels.append(channel)
                    
                except Exception as e:
                    logger.error("Error sending notification via channel", 
                                notification_id=notification.id,
                                channel=channel, 
                                error=str(e))
                    failed_channels.append(channel)
            
            # Actualizar estado de la notificación
            if sent_channels:
                notification.status = NotificationStatus.SENT
                notification.delivered_at = datetime.utcnow()
            else:
                notification.status = NotificationStatus.FAILED
                notification.error_message = f"Failed to send via channels: {failed_channels}"
            
            self.db.commit()
            
            logger.info("Notification sent", 
                       notification_id=notification.id,
                       sent_channels=sent_channels,
                       failed_channels=failed_channels)
            
            return len(sent_channels) > 0
            
        except Exception as e:
            logger.error("Error sending notification", 
                        notification_id=notification.id, 
                        error=str(e))
            return False
    
    async def _send_email_notification(self, notification: Notification, site_id: str) -> bool:
        """Enviar notificación por email"""
        try:
            # Obtener configuración del sitio
            site_config = self.db.query(SiteConfig).filter(
                SiteConfig.site_id == site_id
            ).first()
            
            if not site_config or not site_config.email_from:
                logger.warning("Email configuration not found", site_id=site_id)
                return False
            
            # Obtener usuario
            user = self.db.query(User).filter(User.id == notification.user_id).first()
            if not user:
                return False
            
            # Crear mensaje de email
            msg = MIMEMultipart()
            msg['From'] = site_config.email_from
            msg['To'] = user.email
            msg['Subject'] = notification.title
            
            # Usar template si está disponible
            if notification.template_id:
                template = self.db.query(NotificationTemplate).filter(
                    NotificationTemplate.id == notification.template_id
                ).first()
                
                if template and template.type == NotificationTemplateType.EMAIL:
                    # Renderizar template
                    template_vars = json.loads(notification.template_variables) if notification.template_variables else {}
                    template_vars.update({
                        "user_name": user.nombre,
                        "site_name": site_config.site_name,
                        "notification_title": notification.title,
                        "notification_message": notification.message
                    })
                    
                    jinja_template = Template(template.content)
                    body = jinja_template.render(**template_vars)
                else:
                    body = notification.message
            else:
                body = notification.message
            
            msg.attach(MIMEText(body, 'html'))
            
            # Enviar email (simplificado - en producción usar servicio de email)
            logger.info("Email notification sent", 
                       notification_id=notification.id,
                       to=user.email,
                       subject=notification.title)
            
            return True
            
        except Exception as e:
            logger.error("Error sending email notification", 
                        notification_id=notification.id, 
                        error=str(e))
            return False
    
    async def _send_push_notification(self, notification: Notification, site_id: str) -> bool:
        """Enviar notificación push"""
        try:
            # Obtener usuario
            user = self.db.query(User).filter(User.id == notification.user_id).first()
            if not user:
                return False
            
            # Aquí se integraría con un servicio de push notifications como Firebase
            # Por ahora solo logueamos
            logger.info("Push notification sent", 
                       notification_id=notification.id,
                       user_id=user.id,
                       title=notification.title)
            
            return True
            
        except Exception as e:
            logger.error("Error sending push notification", 
                        notification_id=notification.id, 
                        error=str(e))
            return False
    
    async def _send_sms_notification(self, notification: Notification, site_id: str) -> bool:
        """Enviar notificación por SMS"""
        try:
            # Obtener usuario
            user = self.db.query(User).filter(User.id == notification.user_id).first()
            if not user or not user.telefono:
                return False
            
            # Aquí se integraría con un servicio de SMS como Twilio
            # Por ahora solo logueamos
            logger.info("SMS notification sent", 
                       notification_id=notification.id,
                       user_id=user.id,
                       phone=user.telefono,
                       message=notification.message)
            
            return True
            
        except Exception as e:
            logger.error("Error sending SMS notification", 
                        notification_id=notification.id, 
                        error=str(e))
            return False
    
    async def get_user_notifications(
        self,
        user_id: int,
        site_id: str,
        page: int = 1,
        size: int = 20,
        unread_only: bool = False
    ) -> Dict[str, Any]:
        """Obtener notificaciones del usuario"""
        try:
            query = self.db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.site_id == site_id
            )
            
            # Filtrar por no leídas si se solicita
            if unread_only:
                query = query.filter(Notification.read_at.is_(None))
            
            # Filtrar notificaciones expiradas
            query = query.filter(
                (Notification.expires_at.is_(None)) | 
                (Notification.expires_at > datetime.utcnow())
            )
            
            # Contar total
            total = query.count()
            
            # Aplicar paginación
            offset = (page - 1) * size
            notifications = query.order_by(Notification.created_at.desc()).offset(offset).limit(size).all()
            
            total_pages = (total + size - 1) // size
            
            result = {
                "notifications": notifications,
                "total": total,
                "page": page,
                "size": size,
                "total_pages": total_pages,
                "unread_count": self.db.query(Notification).filter(
                    Notification.user_id == user_id,
                    Notification.site_id == site_id,
                    Notification.read_at.is_(None)
                ).count()
            }
            
            logger.info("User notifications retrieved", 
                       user_id=user_id, 
                       site_id=site_id, 
                       page=page, 
                       total=total)
            
            return result
            
        except Exception as e:
            logger.error("Error getting user notifications", 
                        user_id=user_id, 
                        site_id=site_id, 
                        error=str(e))
            return {"notifications": [], "total": 0, "page": page, "size": size, "total_pages": 0, "unread_count": 0}
    
    async def mark_notification_as_read(
        self,
        notification_id: int,
        user_id: int,
        site_id: str
    ) -> bool:
        """Marcar notificación como leída"""
        try:
            notification = self.db.query(Notification).filter(
                Notification.id == notification_id,
                Notification.user_id == user_id,
                Notification.site_id == site_id
            ).first()
            
            if not notification:
                return False
            
            notification.read_at = datetime.utcnow()
            self.db.commit()
            
            logger.info("Notification marked as read", 
                       notification_id=notification_id, 
                       user_id=user_id, 
                       site_id=site_id)
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error("Error marking notification as read", 
                        notification_id=notification_id, 
                        user_id=user_id, 
                        site_id=site_id, 
                        error=str(e))
            return False
    
    async def mark_all_notifications_as_read(
        self,
        user_id: int,
        site_id: str
    ) -> bool:
        """Marcar todas las notificaciones como leídas"""
        try:
            updated = self.db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.site_id == site_id,
                Notification.read_at.is_(None)
            ).update({
                "read_at": datetime.utcnow()
            })
            
            self.db.commit()
            
            logger.info("All notifications marked as read", 
                       user_id=user_id, 
                       site_id=site_id, 
                       updated_count=updated)
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error("Error marking all notifications as read", 
                        user_id=user_id, 
                        site_id=site_id, 
                        error=str(e))
            return False
    
    async def delete_notification(
        self,
        notification_id: int,
        user_id: int,
        site_id: str
    ) -> bool:
        """Eliminar notificación"""
        try:
            notification = self.db.query(Notification).filter(
                Notification.id == notification_id,
                Notification.user_id == user_id,
                Notification.site_id == site_id
            ).first()
            
            if not notification:
                return False
            
            self.db.delete(notification)
            self.db.commit()
            
            logger.info("Notification deleted", 
                       notification_id=notification_id, 
                       user_id=user_id, 
                       site_id=site_id)
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error("Error deleting notification", 
                        notification_id=notification_id, 
                        user_id=user_id, 
                        site_id=site_id, 
                        error=str(e))
            return False
    
    async def send_batch_notifications(
        self,
        batch_data: NotificationBatch,
        site_id: str
    ) -> Dict[str, Any]:
        """Enviar notificaciones masivas"""
        try:
            # Obtener usuarios según filtros
            if batch_data.user_ids:
                users = self.db.query(User).filter(
                    User.id.in_(batch_data.user_ids),
                    User.site_id == site_id,
                    User.activo == True
                ).all()
            else:
                # Aplicar filtros
                query = self.db.query(User).filter(
                    User.site_id == site_id,
                    User.activo == True
                )
                
                if batch_data.user_filters:
                    # Aplicar filtros adicionales
                    pass
                
                users = query.all()
            
            notifications_created = 0
            failed_count = 0
            errors = []
            
            for user in users:
                try:
                    notification_data = NotificationCreate(
                        user_id=user.id,
                        type=batch_data.type,
                        title=batch_data.title,
                        message=batch_data.message,
                        priority=batch_data.priority,
                        channels=batch_data.channels,
                        template_id=batch_data.template_id,
                        template_variables=batch_data.template_variables,
                        scheduled_at=batch_data.scheduled_at,
                        expires_at=batch_data.expires_at
                    )
                    
                    notification = await self.create_notification(notification_data, site_id)
                    if notification:
                        notifications_created += 1
                    else:
                        failed_count += 1
                        errors.append(f"Failed to create notification for user {user.id}")
                        
                except Exception as e:
                    failed_count += 1
                    errors.append(f"Error creating notification for user {user.id}: {str(e)}")
            
            success = failed_count == 0
            
            logger.info("Batch notifications sent", 
                       site_id=site_id,
                       total_users=len(users),
                       notifications_created=notifications_created,
                       failed_count=failed_count,
                       success=success)
            
            return {
                "success": success,
                "message": f"Batch notifications sent: {notifications_created} created, {failed_count} failed",
                "total_users": len(users),
                "notifications_created": notifications_created,
                "failed_count": failed_count,
                "errors": errors
            }
            
        except Exception as e:
            logger.error("Error sending batch notifications", 
                        site_id=site_id, 
                        error=str(e))
            return {
                "success": False,
                "message": f"Batch notifications failed: {str(e)}",
                "total_users": 0,
                "notifications_created": 0,
                "failed_count": 0,
                "errors": [str(e)]
            }
    
    async def get_notification_analytics(
        self,
        site_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Obtener analytics de notificaciones"""
        try:
            # Fecha límite
            date_limit = datetime.utcnow() - timedelta(days=days)
            
            # Obtener notificaciones
            notifications = self.db.query(Notification).filter(
                Notification.site_id == site_id,
                Notification.created_at >= date_limit
            ).all()
            
            # Calcular estadísticas
            total_notifications = len(notifications)
            sent_notifications = len([n for n in notifications if n.status == NotificationStatus.SENT])
            delivered_notifications = len([n for n in notifications if n.delivered_at is not None])
            read_notifications = len([n for n in notifications if n.read_at is not None])
            failed_notifications = len([n for n in notifications if n.status == NotificationStatus.FAILED])
            
            delivery_rate = (delivered_notifications / total_notifications * 100) if total_notifications > 0 else 0
            read_rate = (read_notifications / delivered_notifications * 100) if delivered_notifications > 0 else 0
            
            # Notificaciones por tipo
            notifications_by_type = {}
            for notification in notifications:
                type_name = notification.type.value
                if type_name not in notifications_by_type:
                    notifications_by_type[type_name] = 0
                notifications_by_type[type_name] += 1
            
            # Notificaciones por canal
            notifications_by_channel = {}
            for notification in notifications:
                if notification.channels:
                    channels = json.loads(notification.channels)
                    for channel in channels:
                        if channel not in notifications_by_channel:
                            notifications_by_channel[channel] = 0
                        notifications_by_channel[channel] += 1
            
            # Notificaciones diarias
            daily_notifications = {}
            for notification in notifications:
                date = notification.created_at.date()
                if date not in daily_notifications:
                    daily_notifications[date] = {"total": 0, "sent": 0, "read": 0}
                daily_notifications[date]["total"] += 1
                if notification.status == NotificationStatus.SENT:
                    daily_notifications[date]["sent"] += 1
                if notification.read_at:
                    daily_notifications[date]["read"] += 1
            
            return {
                "period": f"{days}d",
                "total_notifications": total_notifications,
                "sent_notifications": sent_notifications,
                "delivered_notifications": delivered_notifications,
                "read_notifications": read_notifications,
                "failed_notifications": failed_notifications,
                "delivery_rate": round(delivery_rate, 2),
                "read_rate": round(read_rate, 2),
                "notifications_by_type": notifications_by_type,
                "notifications_by_channel": notifications_by_channel,
                "daily_notifications": daily_notifications,
                "top_templates": []  # TODO: Implementar
            }
            
        except Exception as e:
            logger.error("Error getting notification analytics", 
                        site_id=site_id, 
                        error=str(e))
            return {
                "period": f"{days}d",
                "total_notifications": 0,
                "sent_notifications": 0,
                "delivered_notifications": 0,
                "read_notifications": 0,
                "failed_notifications": 0,
                "delivery_rate": 0.0,
                "read_rate": 0.0,
                "notifications_by_type": {},
                "notifications_by_channel": {},
                "daily_notifications": {},
                "top_templates": []
            }
    
    async def cleanup_expired_notifications(self) -> int:
        """Limpiar notificaciones expiradas"""
        try:
            deleted_count = self.db.query(Notification).filter(
                Notification.expires_at < datetime.utcnow()
            ).delete()
            
            self.db.commit()
            
            logger.info("Expired notifications cleaned up", 
                       deleted_count=deleted_count)
            
            return deleted_count
            
        except Exception as e:
            self.db.rollback()
            logger.error("Error cleaning up expired notifications", 
                        error=str(e))
            return 0