from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class InstagramConnectionStatus(str, Enum):
    """Estados de conexión con Instagram"""
    NOT_CONNECTED = "not_connected"
    CONNECTED = "connected"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ERROR = "error"

class InstagramVerificationStatus(str, Enum):
    """Estados de verificación de seguimiento"""
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"

class InstagramUserBase(BaseModel):
    """Schema base para usuario de Instagram"""
    instagram_user_id: str = Field(..., description="ID del usuario en Instagram")
    username: str = Field(..., description="Nombre de usuario de Instagram")
    full_name: Optional[str] = Field(None, description="Nombre completo del usuario")
    profile_picture_url: Optional[str] = Field(None, description="URL de la foto de perfil")
    follower_count: Optional[int] = Field(None, description="Número de seguidores")
    following_count: Optional[int] = Field(None, description="Número de seguidos")
    media_count: Optional[int] = Field(None, description="Número de publicaciones")

class InstagramUserCreate(InstagramUserBase):
    """Schema para crear conexión de Instagram"""
    access_token: str = Field(..., description="Token de acceso de Instagram")
    token_expires_at: Optional[datetime] = Field(None, description="Fecha de expiración del token")
    user_id: int = Field(..., description="ID del usuario en nuestro sistema")

class InstagramUserUpdate(BaseModel):
    """Schema para actualizar datos de Instagram"""
    username: Optional[str] = None
    full_name: Optional[str] = None
    profile_picture_url: Optional[str] = None
    follower_count: Optional[int] = None
    following_count: Optional[int] = None
    media_count: Optional[int] = None
    connection_status: Optional[InstagramConnectionStatus] = None

class InstagramUserResponse(InstagramUserBase):
    """Schema para respuesta de usuario de Instagram"""
    id: int
    user_id: int
    site_id: str
    connection_status: InstagramConnectionStatus
    verification_status: InstagramVerificationStatus
    access_token: Optional[str] = None  # Solo para respuestas internas
    token_expires_at: Optional[datetime] = None
    last_verification: Optional[datetime] = None
    verification_attempts: int = 0
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class InstagramVerificationRequest(BaseModel):
    """Schema para solicitar verificación de seguimiento"""
    instagram_username: str = Field(..., description="Nombre de usuario de Instagram a verificar")
    target_account: str = Field(..., description="Cuenta objetivo a verificar si sigue")
    
    @validator('instagram_username')
    def validate_username(cls, v):
        if not v or len(v) < 1:
            raise ValueError('Instagram username cannot be empty')
        return v.strip().lower()

class InstagramVerificationResponse(BaseModel):
    """Schema para respuesta de verificación"""
    verified: bool = Field(..., description="Si la verificación fue exitosa")
    message: str = Field(..., description="Mensaje de la verificación")
    instagram_user: Optional[InstagramUserResponse] = Field(None, description="Datos del usuario de Instagram")
    verification_details: Optional[Dict[str, Any]] = Field(None, description="Detalles de la verificación")
    sticker_generated: bool = Field(False, description="Si se generó un sticker automáticamente")

class InstagramAuthRequest(BaseModel):
    """Schema para solicitud de autenticación con Instagram"""
    redirect_uri: Optional[str] = Field(None, description="URI de redirección personalizada")
    state: Optional[str] = Field(None, description="Estado para validación de seguridad")

class InstagramAuthResponse(BaseModel):
    """Schema para respuesta de autenticación"""
    auth_url: str = Field(..., description="URL de autenticación de Instagram")
    state: str = Field(..., description="Estado para validación")
    expires_in: int = Field(..., description="Tiempo de expiración en segundos")

class InstagramCallbackRequest(BaseModel):
    """Schema para callback de Instagram"""
    code: str = Field(..., description="Código de autorización")
    state: str = Field(..., description="Estado de validación")
    error: Optional[str] = Field(None, description="Error si la autorización falló")
    error_description: Optional[str] = Field(None, description="Descripción del error")

class InstagramCallbackResponse(BaseModel):
    """Schema para respuesta del callback"""
    success: bool = Field(..., description="Si la conexión fue exitosa")
    message: str = Field(..., description="Mensaje de resultado")
    instagram_user: Optional[InstagramUserResponse] = Field(None, description="Datos del usuario conectado")
    sticker_generated: bool = Field(False, description="Si se generó un sticker automáticamente")

class InstagramMedia(BaseModel):
    """Schema para media de Instagram"""
    id: str = Field(..., description="ID del media")
    media_type: str = Field(..., description="Tipo de media (IMAGE, VIDEO, CAROUSEL_ALBUM)")
    media_url: str = Field(..., description="URL del media")
    permalink: str = Field(..., description="URL permanente del post")
    caption: Optional[str] = Field(None, description="Descripción del post")
    timestamp: datetime = Field(..., description="Fecha de creación")
    like_count: Optional[int] = Field(None, description="Número de likes")
    comments_count: Optional[int] = Field(None, description="Número de comentarios")

class InstagramFeed(BaseModel):
    """Schema para feed de Instagram"""
    media: List[InstagramMedia] = Field(..., description="Lista de media")
    total_count: int = Field(..., description="Total de media disponible")
    has_more: bool = Field(..., description="Si hay más media disponible")
    next_cursor: Optional[str] = Field(None, description="Cursor para la siguiente página")

class InstagramStats(BaseModel):
    """Schema para estadísticas de Instagram"""
    total_connections: int = Field(0, description="Total de conexiones de Instagram")
    verified_followers: int = Field(0, description="Seguidores verificados")
    pending_verifications: int = Field(0, description="Verificaciones pendientes")
    failed_verifications: int = Field(0, description="Verificaciones fallidas")
    stickers_generated: int = Field(0, description="Stickers generados por Instagram")
    last_verification: Optional[datetime] = Field(None, description="Última verificación")

class InstagramNotification(BaseModel):
    """Schema para notificaciones de Instagram"""
    id: int
    user_id: int
    type: str = Field(..., description="Tipo de notificación")
    title: str = Field(..., description="Título de la notificación")
    message: str = Field(..., description="Mensaje de la notificación")
    instagram_username: Optional[str] = Field(None, description="Usuario de Instagram relacionado")
    read: bool = Field(False, description="Si la notificación fue leída")
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadatos adicionales")

class InstagramWebhook(BaseModel):
    """Schema para webhook de Instagram"""
    object: str = Field(..., description="Tipo de objeto")
    entry: List[Dict[str, Any]] = Field(..., description="Entradas del webhook")
    timestamp: Optional[int] = Field(None, description="Timestamp del webhook")

class InstagramWebhookVerification(BaseModel):
    """Schema para verificación de webhook"""
    hub_mode: str = Field(..., description="Modo del webhook")
    hub_challenge: str = Field(..., description="Challenge del webhook")
    hub_verify_token: str = Field(..., description="Token de verificación")

class InstagramConfig(BaseModel):
    """Schema para configuración de Instagram por sitio"""
    client_id: str = Field(..., description="Client ID de Instagram")
    client_secret: str = Field(..., description="Client Secret de Instagram")
    redirect_uri: str = Field(..., description="URI de redirección")
    webhook_verify_token: str = Field(..., description="Token de verificación de webhook")
    target_account: str = Field(..., description="Cuenta objetivo a verificar")
    auto_generate_sticker: bool = Field(True, description="Generar sticker automáticamente")
    verification_interval: int = Field(24, description="Intervalo de verificación en horas")
    max_verification_attempts: int = Field(3, description="Máximo de intentos de verificación")

class InstagramConfigUpdate(BaseModel):
    """Schema para actualizar configuración de Instagram"""
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    redirect_uri: Optional[str] = None
    webhook_verify_token: Optional[str] = None
    target_account: Optional[str] = None
    auto_generate_sticker: Optional[bool] = None
    verification_interval: Optional[int] = None
    max_verification_attempts: Optional[int] = None

class InstagramAnalytics(BaseModel):
    """Schema para analytics de Instagram"""
    period: str = Field("30d", description="Período de análisis")
    total_connections: int = Field(0, description="Total de conexiones")
    successful_verifications: int = Field(0, description="Verificaciones exitosas")
    failed_verifications: int = Field(0, description="Verificaciones fallidas")
    stickers_generated: int = Field(0, description="Stickers generados")
    conversion_rate: float = Field(0.0, description="Tasa de conversión")
    daily_stats: List[Dict[str, Any]] = Field(default_factory=list, description="Estadísticas diarias")
    top_performing_posts: List[Dict[str, Any]] = Field(default_factory=list, description="Posts con mejor rendimiento")

class InstagramError(BaseModel):
    """Schema para errores de Instagram"""
    error_type: str = Field(..., description="Tipo de error")
    error_message: str = Field(..., description="Mensaje de error")
    error_code: Optional[str] = Field(None, description="Código de error")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp del error")
    user_id: Optional[int] = Field(None, description="ID del usuario afectado")
    site_id: Optional[str] = Field(None, description="ID del sitio")

class InstagramReconnectRequest(BaseModel):
    """Schema para reconectar cuenta de Instagram"""
    user_id: int = Field(..., description="ID del usuario")
    reason: Optional[str] = Field(None, description="Razón de la reconexión")

class InstagramReconnectResponse(BaseModel):
    """Schema para respuesta de reconexión"""
    success: bool = Field(..., description="Si la reconexión fue exitosa")
    message: str = Field(..., description="Mensaje de resultado")
    auth_url: Optional[str] = Field(None, description="URL de autenticación si es necesaria")
    instagram_user: Optional[InstagramUserResponse] = Field(None, description="Datos del usuario reconectado")
