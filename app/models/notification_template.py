from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class NotificationTemplate(Base):
    """Modelo para templates de notificaciones"""
    __tablename__ = "notification_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String(50), nullable=False, index=True)
    
    # Información del template
    name = Column(String(100), nullable=False)
    type = Column(Enum('email', 'sms', 'push', 'in_app', name='template_type'), 
                  nullable=False)
    subject = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)
    
    # Variables y configuración
    variables = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Metadatos
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)
    tags = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<NotificationTemplate(id={self.id}, name='{self.name}', type='{self.type}', site_id='{self.site_id}')>"

class NotificationSubscription(Base):
    """Modelo para suscripciones de notificaciones"""
    __tablename__ = "notification_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String(50), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Configuración de suscripción
    notification_type = Column(Enum('sticker', 'instagram', 'points', 'level_up', 'system', 'video_completed', 'review', 'comment', 'like', 'welcome', 'reminder', 'promotion', 'birthday', 'anniversary', name='notification_type'), 
                              nullable=False)
    channels = Column(Text, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    user = relationship("User", back_populates="notification_subscriptions")
    
    def __repr__(self):
        return f"<NotificationSubscription(id={self.id}, user_id={self.user_id}, type='{self.notification_type}', site_id='{self.site_id}')>"

class NotificationPreferences(Base):
    """Modelo para preferencias de notificación del usuario"""
    __tablename__ = "notification_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String(50), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Configuración de canales
    email_enabled = Column(Boolean, default=True, nullable=False)
    push_enabled = Column(Boolean, default=True, nullable=False)
    sms_enabled = Column(Boolean, default=False, nullable=False)
    in_app_enabled = Column(Boolean, default=True, nullable=False)
    
    # Configuración de horarios
    quiet_hours_start = Column(String(5), nullable=True)
    quiet_hours_end = Column(String(5), nullable=True)
    timezone = Column(String(50), default="UTC", nullable=False)
    
    # Configuración de idioma
    language = Column(String(10), default="es", nullable=False)
    
    # Configuración de frecuencia
    digest_enabled = Column(Boolean, default=False, nullable=False)
    digest_frequency = Column(Enum('daily', 'weekly', 'monthly', name='digest_frequency'), 
                             default='daily', nullable=False)
    digest_time = Column(String(5), default="09:00", nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    user = relationship("User", back_populates="notification_preferences")
    
    def __repr__(self):
        return f"<NotificationPreferences(id={self.id}, user_id={self.user_id}, site_id='{self.site_id}')>"

class NotificationDigest(Base):
    """Modelo para resúmenes de notificaciones"""
    __tablename__ = "notification_digests"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String(50), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Información del resumen
    digest_type = Column(Enum('daily', 'weekly', 'monthly', name='digest_type'), 
                        nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Contenido del resumen
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    notification_count = Column(Integer, default=0, nullable=False)
    
    # Estado del resumen
    status = Column(Enum('pending', 'sent', 'failed', name='digest_status'), 
                   default='pending', nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    user = relationship("User", back_populates="notification_digests")
    
    def __repr__(self):
        return f"<NotificationDigest(id={self.id}, user_id={self.user_id}, type='{self.digest_type}', site_id='{self.site_id}')>"

class NotificationCampaign(Base):
    """Modelo para campañas de notificaciones"""
    __tablename__ = "notification_campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String(50), nullable=False, index=True)
    
    # Información de la campaña
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    campaign_type = Column(Enum('promotional', 'informational', 'reminder', 'welcome', name='campaign_type'), 
                          nullable=False)
    
    # Configuración de la campaña
    target_audience = Column(Text, nullable=True)
    channels = Column(Text, nullable=False)
    template_id = Column(Integer, ForeignKey("notification_templates.id"), nullable=True)
    
    # Programación
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Estado de la campaña
    status = Column(Enum('draft', 'scheduled', 'running', 'completed', 'cancelled', name='campaign_status'), 
                   default='draft', nullable=False)
    
    # Estadísticas
    total_recipients = Column(Integer, default=0, nullable=False)
    sent_count = Column(Integer, default=0, nullable=False)
    delivered_count = Column(Integer, default=0, nullable=False)
    read_count = Column(Integer, default=0, nullable=False)
    failed_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relaciones
    template = relationship("NotificationTemplate")
    
    def __repr__(self):
        return f"<NotificationCampaign(id={self.id}, name='{self.name}', type='{self.campaign_type}', site_id='{self.site_id}')>"
