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
    name = Column(String(100), nullable=False, description="Nombre del template")
    type = Column(Enum('email', 'sms', 'push', 'in_app', name='template_type'), 
                  nullable=False, description="Tipo de template")
    subject = Column(String(200), nullable=True, description="Asunto (para email)")
    content = Column(Text, nullable=False, description="Contenido del template")
    
    # Variables y configuración
    variables = Column(Text, nullable=True, description="Variables disponibles (JSON)")
    is_active = Column(Boolean, default=True, nullable=False, description="Si el template está activo")
    
    # Metadatos
    description = Column(Text, nullable=True, description="Descripción del template")
    category = Column(String(50), nullable=True, description="Categoría del template")
    tags = Column(Text, nullable=True, description="Tags del template (JSON)")
    
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
                              nullable=False, description="Tipo de notificación")
    channels = Column(Text, nullable=False, description="Canales habilitados (JSON)")
    is_enabled = Column(Boolean, default=True, nullable=False, description="Si la suscripción está habilitada")
    
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
    email_enabled = Column(Boolean, default=True, nullable=False, description="Notificaciones por email habilitadas")
    push_enabled = Column(Boolean, default=True, nullable=False, description="Notificaciones push habilitadas")
    sms_enabled = Column(Boolean, default=False, nullable=False, description="Notificaciones por SMS habilitadas")
    in_app_enabled = Column(Boolean, default=True, nullable=False, description="Notificaciones in-app habilitadas")
    
    # Configuración de horarios
    quiet_hours_start = Column(String(5), nullable=True, description="Hora de inicio de silencio (HH:MM)")
    quiet_hours_end = Column(String(5), nullable=True, description="Hora de fin de silencio (HH:MM)")
    timezone = Column(String(50), default="UTC", nullable=False, description="Zona horaria del usuario")
    
    # Configuración de idioma
    language = Column(String(10), default="es", nullable=False, description="Idioma preferido")
    
    # Configuración de frecuencia
    digest_enabled = Column(Boolean, default=False, nullable=False, description="Resumen diario habilitado")
    digest_frequency = Column(Enum('daily', 'weekly', 'monthly', name='digest_frequency'), 
                             default='daily', nullable=False, description="Frecuencia del resumen")
    digest_time = Column(String(5), default="09:00", nullable=False, description="Hora del resumen (HH:MM)")
    
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
                        nullable=False, description="Tipo de resumen")
    period_start = Column(DateTime(timezone=True), nullable=False, description="Inicio del período")
    period_end = Column(DateTime(timezone=True), nullable=False, description="Fin del período")
    
    # Contenido del resumen
    title = Column(String(200), nullable=False, description="Título del resumen")
    content = Column(Text, nullable=False, description="Contenido del resumen")
    notification_count = Column(Integer, default=0, nullable=False, description="Número de notificaciones")
    
    # Estado del resumen
    status = Column(Enum('pending', 'sent', 'failed', name='digest_status'), 
                   default='pending', nullable=False, description="Estado del resumen")
    sent_at = Column(DateTime(timezone=True), nullable=True, description="Fecha de envío")
    error_message = Column(Text, nullable=True, description="Mensaje de error si falló")
    
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
    name = Column(String(200), nullable=False, description="Nombre de la campaña")
    description = Column(Text, nullable=True, description="Descripción de la campaña")
    campaign_type = Column(Enum('promotional', 'informational', 'reminder', 'welcome', name='campaign_type'), 
                          nullable=False, description="Tipo de campaña")
    
    # Configuración de la campaña
    target_audience = Column(Text, nullable=True, description="Audiencia objetivo (JSON)")
    channels = Column(Text, nullable=False, description="Canales de la campaña (JSON)")
    template_id = Column(Integer, ForeignKey("notification_templates.id"), nullable=True, description="Template a usar")
    
    # Programación
    scheduled_at = Column(DateTime(timezone=True), nullable=True, description="Fecha programada de envío")
    expires_at = Column(DateTime(timezone=True), nullable=True, description="Fecha de expiración")
    
    # Estado de la campaña
    status = Column(Enum('draft', 'scheduled', 'running', 'completed', 'cancelled', name='campaign_status'), 
                   default='draft', nullable=False, description="Estado de la campaña")
    
    # Estadísticas
    total_recipients = Column(Integer, default=0, nullable=False, description="Total de destinatarios")
    sent_count = Column(Integer, default=0, nullable=False, description="Notificaciones enviadas")
    delivered_count = Column(Integer, default=0, nullable=False, description="Notificaciones entregadas")
    read_count = Column(Integer, default=0, nullable=False, description="Notificaciones leídas")
    failed_count = Column(Integer, default=0, nullable=False, description="Notificaciones fallidas")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True, description="Fecha de inicio")
    completed_at = Column(DateTime(timezone=True), nullable=True, description="Fecha de finalización")
    
    # Relaciones
    template = relationship("NotificationTemplate")
    
    def __repr__(self):
        return f"<NotificationCampaign(id={self.id}, name='{self.name}', type='{self.campaign_type}', site_id='{self.site_id}')>"
