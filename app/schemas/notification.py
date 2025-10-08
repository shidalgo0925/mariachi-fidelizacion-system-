from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    """Tipos de notificaciones"""
    STICKER = "sticker"
    INSTAGRAM = "instagram"
    POINTS = "points"
    LEVEL_UP = "level_up"
    SYSTEM = "system"
    VIDEO_COMPLETED = "video_completed"
    REVIEW = "review"
    COMMENT = "comment"
    LIKE = "like"
    WELCOME = "welcome"
    REMINDER = "reminder"
    PROMOTION = "promotion"
    BIRTHDAY = "birthday"
    ANNIVERSARY = "anniversary"

class NotificationPriority(str, Enum):
    """Prioridades de notificaciones"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class NotificationStatus(str, Enum):
    """Estados de notificaciones"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    CANCELLED = "cancelled"

class NotificationChannel(str, Enum):
    """Canales de notificación"""
    EMAIL = "email"
    PUSH = "push"
    SMS = "sms"
    IN_APP = "in_app"
    WEBHOOK = "webhook"

class NotificationTemplateType(str, Enum):
    """Tipos de templates"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"

class NotificationBase(BaseModel):
    """Schema base para notificaciones"""
    type: NotificationType = Field(..., description="Tipo de notificación")
    title: str = Field(..., min_length=1, max_length=200, description="Título de la notificación")
    message: str = Field(..., min_length=1, max_length=1000, description="Mensaje de la notificación")
    priority: NotificationPriority = Field(NotificationPriority.MEDIUM, description="Prioridad de la notificación")
    channels: List[NotificationChannel] = Field(default_factory=list, description="Canales de envío")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadatos adicionales")
    scheduled_at: Optional[datetime] = Field(None, description="Fecha programada de envío")
    expires_at: Optional[datetime] = Field(None, description="Fecha de expiración")

class NotificationCreate(NotificationBase):
    """Schema para crear notificación"""
    user_id: int = Field(..., description="ID del usuario destinatario")
    template_id: Optional[int] = Field(None, description="ID del template a usar")
    template_variables: Optional[Dict[str, Any]] = Field(None, description="Variables para el template")

class NotificationUpdate(BaseModel):
    """Schema para actualizar notificación"""
    status: Optional[NotificationStatus] = Field(None, description="Estado de la notificación")
    read_at: Optional[datetime] = Field(None, description="Fecha de lectura")
    delivered_at: Optional[datetime] = Field(None, description="Fecha de entrega")
    error_message: Optional[str] = Field(None, description="Mensaje de error si falló")

class NotificationResponse(NotificationBase):
    """Schema para respuesta de notificación"""
    id: int
    site_id: str
    user_id: int
    status: NotificationStatus = NotificationStatus.PENDING
    template_id: Optional[int] = None
    template_variables: Optional[Dict[str, Any]] = None
    read_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class NotificationTemplateBase(BaseModel):
    """Schema base para templates de notificación"""
    name: str = Field(..., min_length=1, max_length=100, description="Nombre del template")
    type: NotificationTemplateType = Field(..., description="Tipo de template")
    subject: Optional[str] = Field(None, max_length=200, description="Asunto (para email)")
    content: str = Field(..., min_length=1, description="Contenido del template")
    variables: List[str] = Field(default_factory=list, description="Variables disponibles en el template")
    is_active: bool = Field(True, description="Si el template está activo")

class NotificationTemplateCreate(NotificationTemplateBase):
    """Schema para crear template de notificación"""
    pass

class NotificationTemplateUpdate(BaseModel):
    """Schema para actualizar template de notificación"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[NotificationTemplateType] = None
    subject: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    variables: Optional[List[str]] = None
    is_active: Optional[bool] = None

class NotificationTemplateResponse(NotificationTemplateBase):
    """Schema para respuesta de template de notificación"""
    id: int
    site_id: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class NotificationSubscriptionBase(BaseModel):
    """Schema base para suscripciones de notificación"""
    user_id: int = Field(..., description="ID del usuario")
    notification_type: NotificationType = Field(..., description="Tipo de notificación")
    channels: List[NotificationChannel] = Field(..., description="Canales habilitados")
    is_enabled: bool = Field(True, description="Si la suscripción está habilitada")

class NotificationSubscriptionCreate(NotificationSubscriptionBase):
    """Schema para crear suscripción de notificación"""
    pass

class NotificationSubscriptionUpdate(BaseModel):
    """Schema para actualizar suscripción de notificación"""
    channels: Optional[List[NotificationChannel]] = None
    is_enabled: Optional[bool] = None

class NotificationSubscriptionResponse(NotificationSubscriptionBase):
    """Schema para respuesta de suscripción de notificación"""
    id: int
    site_id: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class NotificationPreferences(BaseModel):
    """Schema para preferencias de notificación del usuario"""
    user_id: int = Field(..., description="ID del usuario")
    email_enabled: bool = Field(True, description="Notificaciones por email habilitadas")
    push_enabled: bool = Field(True, description="Notificaciones push habilitadas")
    sms_enabled: bool = Field(False, description="Notificaciones por SMS habilitadas")
    in_app_enabled: bool = Field(True, description="Notificaciones in-app habilitadas")
    quiet_hours_start: Optional[str] = Field(None, description="Hora de inicio de silencio (HH:MM)")
    quiet_hours_end: Optional[str] = Field(None, description="Hora de fin de silencio (HH:MM)")
    timezone: str = Field("UTC", description="Zona horaria del usuario")
    language: str = Field("es", description="Idioma preferido")

class NotificationPreferencesUpdate(BaseModel):
    """Schema para actualizar preferencias de notificación"""
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None

class NotificationBatch(BaseModel):
    """Schema para envío masivo de notificaciones"""
    type: NotificationType = Field(..., description="Tipo de notificación")
    title: str = Field(..., min_length=1, max_length=200, description="Título de la notificación")
    message: str = Field(..., min_length=1, max_length=1000, description="Mensaje de la notificación")
    priority: NotificationPriority = Field(NotificationPriority.MEDIUM, description="Prioridad de la notificación")
    channels: List[NotificationChannel] = Field(..., description="Canales de envío")
    user_ids: Optional[List[int]] = Field(None, description="IDs específicos de usuarios")
    user_filters: Optional[Dict[str, Any]] = Field(None, description="Filtros para seleccionar usuarios")
    template_id: Optional[int] = Field(None, description="ID del template a usar")
    template_variables: Optional[Dict[str, Any]] = Field(None, description="Variables para el template")
    scheduled_at: Optional[datetime] = Field(None, description="Fecha programada de envío")
    expires_at: Optional[datetime] = Field(None, description="Fecha de expiración")

class NotificationBatchResponse(BaseModel):
    """Schema para respuesta de envío masivo"""
    success: bool = Field(..., description="Si el envío fue exitoso")
    message: str = Field(..., description="Mensaje de resultado")
    total_users: int = Field(0, description="Total de usuarios")
    notifications_created: int = Field(0, description="Notificaciones creadas")
    failed_count: int = Field(0, description="Número de fallos")
    errors: List[str] = Field(default_factory=list, description="Lista de errores")

class NotificationAnalytics(BaseModel):
    """Schema para analytics de notificaciones"""
    period: str = Field("30d", description="Período de análisis")
    total_notifications: int = Field(0, description="Total de notificaciones")
    sent_notifications: int = Field(0, description="Notificaciones enviadas")
    delivered_notifications: int = Field(0, description="Notificaciones entregadas")
    read_notifications: int = Field(0, description="Notificaciones leídas")
    failed_notifications: int = Field(0, description="Notificaciones fallidas")
    delivery_rate: float = Field(0.0, description="Tasa de entrega")
    read_rate: float = Field(0.0, description="Tasa de lectura")
    notifications_by_type: Dict[str, int] = Field(default_factory=dict, description="Notificaciones por tipo")
    notifications_by_channel: Dict[str, int] = Field(default_factory=dict, description="Notificaciones por canal")
    daily_notifications: List[Dict[str, Any]] = Field(default_factory=list, description="Notificaciones diarias")
    top_templates: List[Dict[str, Any]] = Field(default_factory=list, description="Templates más usados")

class NotificationSearch(BaseModel):
    """Schema para búsqueda de notificaciones"""
    query: Optional[str] = Field(None, description="Término de búsqueda")
    type: Optional[NotificationType] = Field(None, description="Filtrar por tipo")
    status: Optional[NotificationStatus] = Field(None, description="Filtrar por estado")
    channel: Optional[NotificationChannel] = Field(None, description="Filtrar por canal")
    priority: Optional[NotificationPriority] = Field(None, description="Filtrar por prioridad")
    user_id: Optional[int] = Field(None, description="Filtrar por usuario")
    date_from: Optional[datetime] = Field(None, description="Fecha desde")
    date_to: Optional[datetime] = Field(None, description="Fecha hasta")
    page: int = Field(1, ge=1, description="Número de página")
    size: int = Field(20, ge=1, le=100, description="Tamaño de página")
    sort_by: str = Field("created_at", description="Campo de ordenamiento")
    sort_order: str = Field("desc", description="Orden de clasificación")

class NotificationList(BaseModel):
    """Schema para listado de notificaciones"""
    notifications: List[NotificationResponse]
    total: int
    page: int
    size: int
    total_pages: int

class NotificationTemplateList(BaseModel):
    """Schema para listado de templates"""
    templates: List[NotificationTemplateResponse]
    total: int
    page: int
    size: int
    total_pages: int

class NotificationSubscriptionList(BaseModel):
    """Schema para listado de suscripciones"""
    subscriptions: List[NotificationSubscriptionResponse]
    total: int
    page: int
    size: int
    total_pages: int

class NotificationWebhook(BaseModel):
    """Schema para webhook de notificación"""
    event_type: str = Field(..., description="Tipo de evento")
    notification_id: int = Field(..., description="ID de la notificación")
    user_id: int = Field(..., description="ID del usuario")
    status: NotificationStatus = Field(..., description="Estado de la notificación")
    channel: NotificationChannel = Field(..., description="Canal de la notificación")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp del evento")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadatos adicionales")

class NotificationWebhookResponse(BaseModel):
    """Schema para respuesta de webhook"""
    success: bool = Field(..., description="Si el webhook fue procesado exitosamente")
    message: str = Field(..., description="Mensaje de resultado")
    processed: bool = Field(False, description="Si el evento fue procesado")

class NotificationTest(BaseModel):
    """Schema para prueba de notificación"""
    type: NotificationType = Field(..., description="Tipo de notificación")
    title: str = Field(..., min_length=1, max_length=200, description="Título de prueba")
    message: str = Field(..., min_length=1, max_length=1000, description="Mensaje de prueba")
    channels: List[NotificationChannel] = Field(..., description="Canales de prueba")
    test_email: Optional[str] = Field(None, description="Email de prueba")
    test_phone: Optional[str] = Field(None, description="Teléfono de prueba")
    template_id: Optional[int] = Field(None, description="ID del template a probar")
    template_variables: Optional[Dict[str, Any]] = Field(None, description="Variables para el template")

class NotificationTestResponse(BaseModel):
    """Schema para respuesta de prueba de notificación"""
    success: bool = Field(..., description="Si la prueba fue exitosa")
    message: str = Field(..., description="Mensaje de resultado")
    test_results: Dict[str, Any] = Field(default_factory=dict, description="Resultados de la prueba por canal")
