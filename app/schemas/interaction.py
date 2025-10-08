from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class InteractionType(str, Enum):
    """Tipos de interacciones"""
    LIKE = "like"
    COMMENT = "comment"
    REVIEW = "review"
    SHARE = "share"
    VIEW = "view"
    CLICK = "click"
    DOWNLOAD = "download"
    SUBSCRIBE = "subscribe"

class InteractionStatus(str, Enum):
    """Estados de interacciones"""
    ACTIVE = "active"
    HIDDEN = "hidden"
    DELETED = "deleted"
    MODERATED = "moderated"

class ReviewRating(int, Enum):
    """Calificaciones de reseñas"""
    ONE_STAR = 1
    TWO_STARS = 2
    THREE_STARS = 3
    FOUR_STARS = 4
    FIVE_STARS = 5

class InteractionBase(BaseModel):
    """Schema base para interacciones"""
    tipo_interaccion: InteractionType = Field(..., description="Tipo de interacción")
    contenido_id: Optional[int] = Field(None, description="ID del contenido relacionado")
    contenido_tipo: Optional[str] = Field(None, description="Tipo de contenido (video, sticker, etc.)")
    contenido: Optional[str] = Field(None, description="Contenido de la interacción (comentario, reseña)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadatos adicionales")

class InteractionCreate(InteractionBase):
    """Schema para crear una nueva interacción"""
    pass

class InteractionUpdate(BaseModel):
    """Schema para actualizar una interacción"""
    contenido: Optional[str] = Field(None, description="Contenido actualizado")
    status: Optional[InteractionStatus] = Field(None, description="Estado de la interacción")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadatos actualizados")

class InteractionResponse(InteractionBase):
    """Schema para respuesta de interacción"""
    id: int
    site_id: str
    usuario_id: int
    puntos_obtenidos: int = 0
    status: InteractionStatus = InteractionStatus.ACTIVE
    fecha_interaccion: datetime
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class LikeBase(BaseModel):
    """Schema base para likes"""
    contenido_id: int = Field(..., description="ID del contenido")
    contenido_tipo: str = Field(..., description="Tipo de contenido")

class LikeCreate(LikeBase):
    """Schema para crear un like"""
    pass

class LikeResponse(LikeBase):
    """Schema para respuesta de like"""
    id: int
    site_id: str
    usuario_id: int
    fecha_like: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

class CommentBase(BaseModel):
    """Schema base para comentarios"""
    contenido_id: int = Field(..., description="ID del contenido")
    contenido_tipo: str = Field(..., description="Tipo de contenido")
    comentario: str = Field(..., min_length=1, max_length=1000, description="Texto del comentario")
    parent_id: Optional[int] = Field(None, description="ID del comentario padre (para respuestas)")

class CommentCreate(CommentBase):
    """Schema para crear un comentario"""
    pass

class CommentUpdate(BaseModel):
    """Schema para actualizar un comentario"""
    comentario: str = Field(..., min_length=1, max_length=1000, description="Texto actualizado del comentario")

class CommentResponse(CommentBase):
    """Schema para respuesta de comentario"""
    id: int
    site_id: str
    usuario_id: int
    usuario_nombre: str
    puntos_obtenidos: int = 0
    status: InteractionStatus = InteractionStatus.ACTIVE
    likes_count: int = 0
    replies_count: int = 0
    fecha_comentario: datetime
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class ReviewBase(BaseModel):
    """Schema base para reseñas"""
    contenido_id: int = Field(..., description="ID del contenido")
    contenido_tipo: str = Field(..., description="Tipo de contenido")
    calificacion: ReviewRating = Field(..., description="Calificación de 1 a 5 estrellas")
    titulo: Optional[str] = Field(None, max_length=200, description="Título de la reseña")
    comentario: Optional[str] = Field(None, max_length=2000, description="Comentario de la reseña")

class ReviewCreate(ReviewBase):
    """Schema para crear una reseña"""
    pass

class ReviewUpdate(BaseModel):
    """Schema para actualizar una reseña"""
    calificacion: Optional[ReviewRating] = Field(None, description="Calificación actualizada")
    titulo: Optional[str] = Field(None, max_length=200, description="Título actualizado")
    comentario: Optional[str] = Field(None, max_length=2000, description="Comentario actualizado")

class ReviewResponse(ReviewBase):
    """Schema para respuesta de reseña"""
    id: int
    site_id: str
    usuario_id: int
    usuario_nombre: str
    puntos_obtenidos: int = 0
    status: InteractionStatus = InteractionStatus.ACTIVE
    likes_count: int = 0
    fecha_reseña: datetime
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class InteractionStats(BaseModel):
    """Schema para estadísticas de interacciones"""
    total_interactions: int = Field(0, description="Total de interacciones")
    total_likes: int = Field(0, description="Total de likes")
    total_comments: int = Field(0, description="Total de comentarios")
    total_reviews: int = Field(0, description="Total de reseñas")
    average_rating: float = Field(0.0, description="Calificación promedio")
    engagement_rate: float = Field(0.0, description="Tasa de engagement")
    most_liked_content: Optional[Dict[str, Any]] = Field(None, description="Contenido más gustado")
    most_commented_content: Optional[Dict[str, Any]] = Field(None, description="Contenido más comentado")

class InteractionAnalytics(BaseModel):
    """Schema para analytics de interacciones"""
    period: str = Field("30d", description="Período de análisis")
    total_interactions: int = Field(0, description="Total de interacciones")
    interactions_by_type: Dict[str, int] = Field(default_factory=dict, description="Interacciones por tipo")
    daily_interactions: List[Dict[str, Any]] = Field(default_factory=list, description="Interacciones diarias")
    top_content: List[Dict[str, Any]] = Field(default_factory=list, description="Contenido más interactivo")
    user_engagement: Dict[str, Any] = Field(default_factory=dict, description="Engagement de usuarios")

class InteractionSearch(BaseModel):
    """Schema para búsqueda de interacciones"""
    query: Optional[str] = Field(None, description="Término de búsqueda")
    tipo_interaccion: Optional[InteractionType] = Field(None, description="Filtrar por tipo")
    contenido_tipo: Optional[str] = Field(None, description="Filtrar por tipo de contenido")
    contenido_id: Optional[int] = Field(None, description="Filtrar por ID de contenido")
    usuario_id: Optional[int] = Field(None, description="Filtrar por usuario")
    fecha_desde: Optional[datetime] = Field(None, description="Fecha desde")
    fecha_hasta: Optional[datetime] = Field(None, description="Fecha hasta")
    page: int = Field(1, ge=1, description="Número de página")
    size: int = Field(10, ge=1, le=100, description="Tamaño de página")
    sort_by: str = Field("fecha_interaccion", description="Campo de ordenamiento")
    sort_order: str = Field("desc", description="Orden de clasificación")

class InteractionList(BaseModel):
    """Schema para listado de interacciones"""
    interactions: List[InteractionResponse]
    total: int
    page: int
    size: int
    total_pages: int

class CommentList(BaseModel):
    """Schema para listado de comentarios"""
    comments: List[CommentResponse]
    total: int
    page: int
    size: int
    total_pages: int

class ReviewList(BaseModel):
    """Schema para listado de reseñas"""
    reviews: List[ReviewResponse]
    total: int
    page: int
    size: int
    total_pages: int

class LikeList(BaseModel):
    """Schema para listado de likes"""
    likes: List[LikeResponse]
    total: int
    page: int
    size: int
    total_pages: int

class ContentEngagement(BaseModel):
    """Schema para engagement de contenido"""
    contenido_id: int
    contenido_tipo: str
    titulo: Optional[str] = None
    total_likes: int = 0
    total_comments: int = 0
    total_reviews: int = 0
    total_views: int = 0
    average_rating: float = 0.0
    engagement_score: float = 0.0
    last_interaction: Optional[datetime] = None

class UserEngagement(BaseModel):
    """Schema para engagement de usuario"""
    usuario_id: int
    usuario_nombre: str
    total_interactions: int = 0
    total_likes_given: int = 0
    total_comments: int = 0
    total_reviews: int = 0
    total_points_earned: int = 0
    engagement_level: str = "beginner"
    last_activity: Optional[datetime] = None

class InteractionNotification(BaseModel):
    """Schema para notificaciones de interacciones"""
    id: int
    tipo: str = Field(..., description="Tipo de notificación")
    titulo: str = Field(..., description="Título de la notificación")
    mensaje: str = Field(..., description="Mensaje de la notificación")
    interaction_id: int = Field(..., description="ID de la interacción")
    usuario_id: int = Field(..., description="ID del usuario")
    leida: bool = Field(False, description="Si la notificación fue leída")
    fecha_creacion: datetime
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadatos adicionales")

class InteractionModeration(BaseModel):
    """Schema para moderación de interacciones"""
    interaction_id: int = Field(..., description="ID de la interacción")
    action: str = Field(..., description="Acción de moderación (approve, hide, delete)")
    reason: Optional[str] = Field(None, description="Razón de la moderación")
    moderator_id: int = Field(..., description="ID del moderador")

class InteractionReport(BaseModel):
    """Schema para reportar interacciones"""
    interaction_id: int = Field(..., description="ID de la interacción a reportar")
    reason: str = Field(..., description="Razón del reporte")
    description: Optional[str] = Field(None, description="Descripción adicional")

class InteractionReportResponse(BaseModel):
    """Schema para respuesta de reporte"""
    success: bool = Field(..., description="Si el reporte fue exitoso")
    message: str = Field(..., description="Mensaje de respuesta")
    report_id: Optional[int] = Field(None, description="ID del reporte generado")
