from pydantic import BaseModel, validator, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.user import User

class UserBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100, description="Nombre completo del usuario")
    email: str = Field(..., description="Email del usuario")
    telefono: Optional[str] = Field(None, max_length=20, description="Teléfono del usuario")

class UserCreate(UserBase):
    """Schema para crear un nuevo usuario"""
    password: str = Field(..., min_length=6, max_length=100, description="Contraseña del usuario")
    
    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class UserUpdate(BaseModel):
    """Schema para actualizar un usuario"""
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)
    
    @validator('telefono')
    def validate_telefono(cls, v):
        if v and not v.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise ValueError('Invalid phone number format')
        return v

class UserLogin(BaseModel):
    """Schema para login de usuario"""
    email: str = Field(..., description="Email del usuario")
    password: str = Field(..., description="Contraseña del usuario")

class UserResponse(UserBase):
    """Schema para respuesta de usuario"""
    id: int
    site_id: str
    fecha_registro: datetime
    puntos_acumulados: int
    total_descuento: int
    instagram_seguido: bool
    reseñas_dejadas: int
    videos_completados: int
    stickers_generados: int
    activo: bool
    verificado: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class UserStats(BaseModel):
    """Schema para estadísticas de usuario"""
    puntos_acumulados: int
    total_descuento: int
    stickers_generados: int
    videos_completados: int
    reseñas_dejadas: int
    instagram_seguido: bool
    nivel_usuario: str
    proximo_nivel: Optional[str]
    puntos_para_proximo_nivel: Optional[int]

class UserLeaderboard(BaseModel):
    """Schema para ranking de usuarios"""
    usuario: UserResponse
    posicion: int
    puntos: int
    stickers: int
    videos: int

class TokenResponse(BaseModel):
    """Schema para respuesta de token"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

class PasswordReset(BaseModel):
    """Schema para reset de contraseña"""
    email: str = Field(..., description="Email del usuario")
    
    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower()

class PasswordUpdate(BaseModel):
    """Schema para actualizar contraseña"""
    current_password: str = Field(..., description="Contraseña actual")
    new_password: str = Field(..., min_length=6, max_length=100, description="Nueva contraseña")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 6:
            raise ValueError('New password must be at least 6 characters long')
        return v

class UserProfile(BaseModel):
    """Schema para perfil completo de usuario"""
    user: UserResponse
    stats: UserStats
    recent_activities: List[Dict[str, Any]]
    achievements: List[Dict[str, Any]]

class UserList(BaseModel):
    """Schema para listado de usuarios"""
    users: List[UserResponse]
    total: int
    page: int
    size: int
    total_pages: int

class UserSearch(BaseModel):
    """Schema para búsqueda de usuarios"""
    query: Optional[str] = Field(None, description="Término de búsqueda")
    page: int = Field(1, ge=1, description="Número de página")
    size: int = Field(10, ge=1, le=100, description="Tamaño de página")
    sort_by: str = Field("puntos_acumulados", description="Campo de ordenamiento")
    sort_order: str = Field("desc", description="Orden de clasificación")

class UserActivity(BaseModel):
    """Schema para actividad de usuario"""
    id: int
    tipo_actividad: str
    descripcion: str
    puntos_obtenidos: int
    fecha_actividad: datetime
    metadata: Optional[Dict[str, Any]]

class UserAchievement(BaseModel):
    """Schema para logros de usuario"""
    id: str
    nombre: str
    descripcion: str
    icono: str
    puntos_requeridos: int
    desbloqueado: bool
    fecha_desbloqueo: Optional[datetime]

class UserNotification(BaseModel):
    """Schema para notificaciones de usuario"""
    id: int
    titulo: str
    mensaje: str
    tipo: str
    leida: bool
    fecha_creacion: datetime
    metadata: Optional[Dict[str, Any]]

class UserPreferences(BaseModel):
    """Schema para preferencias de usuario"""
    notificaciones_email: bool = True
    notificaciones_push: bool = True
    compartir_actividad: bool = True
    idioma: str = "es"
    zona_horaria: str = "America/Panama"

class UserPreferencesUpdate(BaseModel):
    """Schema para actualizar preferencias de usuario"""
    notificaciones_email: Optional[bool] = None
    notificaciones_push: Optional[bool] = None
    compartir_actividad: Optional[bool] = None
    idioma: Optional[str] = None
    zona_horaria: Optional[str] = None

class UserExport(BaseModel):
    """Schema para exportar datos de usuario"""
    user: UserResponse
    activities: List[UserActivity]
    achievements: List[UserAchievement]
    stickers: List[Dict[str, Any]]
    interactions: List[Dict[str, Any]]
    export_date: datetime
