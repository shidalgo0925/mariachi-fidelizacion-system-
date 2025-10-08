from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class VideoStatus(str, Enum):
    """Estados de video"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    ARCHIVED = "archived"

class VideoCompletionStatus(str, Enum):
    """Estados de completación de video"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"

class VideoType(str, Enum):
    """Tipos de video"""
    TUTORIAL = "tutorial"
    PROMOTIONAL = "promotional"
    ENTERTAINMENT = "entertainment"
    EDUCATIONAL = "educational"
    TESTIMONIAL = "testimonial"

class VideoBase(BaseModel):
    """Schema base para videos"""
    titulo: str = Field(..., min_length=1, max_length=200, description="Título del video")
    descripcion: Optional[str] = Field(None, description="Descripción del video")
    youtube_id: str = Field(..., description="ID del video en YouTube")
    tipo_video: VideoType = Field(VideoType.ENTERTAINMENT, description="Tipo de video")
    duracion_segundos: Optional[int] = Field(None, ge=1, description="Duración en segundos")
    orden: int = Field(..., ge=1, description="Orden de visualización")
    puntos_por_completar: int = Field(10, ge=0, description="Puntos otorgados por completar")
    activo: bool = Field(True, description="Si el video está activo")

class VideoCreate(VideoBase):
    """Schema para crear un nuevo video"""
    playlist_id: Optional[str] = Field(None, description="ID de la playlist de YouTube")
    
    @validator('youtube_id')
    def validate_youtube_id(cls, v):
        if not v or len(v) < 11:
            raise ValueError('Invalid YouTube video ID')
        return v

class VideoUpdate(BaseModel):
    """Schema para actualizar un video"""
    titulo: Optional[str] = Field(None, min_length=1, max_length=200)
    descripcion: Optional[str] = None
    tipo_video: Optional[VideoType] = None
    duracion_segundos: Optional[int] = Field(None, ge=1)
    orden: Optional[int] = Field(None, ge=1)
    puntos_por_completar: Optional[int] = Field(None, ge=0)
    activo: Optional[bool] = None

class VideoResponse(VideoBase):
    """Schema para respuesta de video"""
    id: int
    site_id: str
    thumbnail_url: Optional[str] = None
    embed_url: Optional[str] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    published_at: Optional[datetime] = None
    status: VideoStatus = VideoStatus.ACTIVE
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class VideoCompletionBase(BaseModel):
    """Schema base para completación de video"""
    video_id: int = Field(..., description="ID del video")
    completion_percentage: int = Field(..., ge=0, le=100, description="Porcentaje de completación")
    time_watched: int = Field(..., ge=0, description="Tiempo visto en segundos")
    completion_status: VideoCompletionStatus = Field(..., description="Estado de completación")

class VideoCompletionCreate(VideoCompletionBase):
    """Schema para crear completación de video"""
    pass

class VideoCompletionResponse(VideoCompletionBase):
    """Schema para respuesta de completación de video"""
    id: int
    user_id: int
    site_id: str
    points_earned: int = 0
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class VideoProgress(BaseModel):
    """Schema para progreso de video"""
    video_id: int
    titulo: str
    youtube_id: str
    orden: int
    completion_status: VideoCompletionStatus
    completion_percentage: int
    time_watched: int
    duracion_segundos: Optional[int]
    points_earned: int
    can_play: bool = True
    thumbnail_url: Optional[str] = None

class VideoPlaylist(BaseModel):
    """Schema para playlist de videos"""
    id: str = Field(..., description="ID de la playlist")
    titulo: str = Field(..., description="Título de la playlist")
    descripcion: Optional[str] = Field(None, description="Descripción de la playlist")
    video_count: int = Field(0, description="Número de videos en la playlist")
    videos: List[VideoResponse] = Field(default_factory=list, description="Videos de la playlist")
    total_duration: Optional[int] = Field(None, description="Duración total en segundos")
    total_points: int = Field(0, description="Puntos totales disponibles")

class VideoStats(BaseModel):
    """Schema para estadísticas de videos"""
    total_videos: int = Field(0, description="Total de videos")
    active_videos: int = Field(0, description="Videos activos")
    total_views: int = Field(0, description="Total de visualizaciones")
    total_completions: int = Field(0, description="Total de completaciones")
    completion_rate: float = Field(0.0, description="Tasa de completación")
    average_watch_time: float = Field(0.0, description="Tiempo promedio de visualización")
    most_watched_video: Optional[Dict[str, Any]] = Field(None, description="Video más visto")
    videos_by_type: Dict[str, int] = Field(default_factory=dict, description="Videos por tipo")

class VideoAnalytics(BaseModel):
    """Schema para analytics de videos"""
    period: str = Field("30d", description="Período de análisis")
    total_views: int = Field(0, description="Total de visualizaciones")
    total_completions: int = Field(0, description="Total de completaciones")
    unique_viewers: int = Field(0, description="Visualizadores únicos")
    completion_rate: float = Field(0.0, description="Tasa de completación")
    average_watch_time: float = Field(0.0, description="Tiempo promedio de visualización")
    daily_stats: List[Dict[str, Any]] = Field(default_factory=list, description="Estadísticas diarias")
    top_videos: List[Dict[str, Any]] = Field(default_factory=list, description="Videos más populares")
    engagement_metrics: Dict[str, Any] = Field(default_factory=dict, description="Métricas de engagement")

class VideoSearch(BaseModel):
    """Schema para búsqueda de videos"""
    query: Optional[str] = Field(None, description="Término de búsqueda")
    tipo_video: Optional[VideoType] = Field(None, description="Filtrar por tipo")
    activo: Optional[bool] = Field(None, description="Filtrar por estado activo")
    min_duration: Optional[int] = Field(None, description="Duración mínima en segundos")
    max_duration: Optional[int] = Field(None, description="Duración máxima en segundos")
    page: int = Field(1, ge=1, description="Número de página")
    size: int = Field(10, ge=1, le=100, description="Tamaño de página")
    sort_by: str = Field("orden", description="Campo de ordenamiento")
    sort_order: str = Field("asc", description="Orden de clasificación")

class VideoList(BaseModel):
    """Schema para listado de videos"""
    videos: List[VideoResponse]
    total: int
    page: int
    size: int
    total_pages: int

class VideoImport(BaseModel):
    """Schema para importar videos desde YouTube"""
    playlist_id: str = Field(..., description="ID de la playlist de YouTube")
    import_all: bool = Field(True, description="Importar todos los videos de la playlist")
    video_ids: Optional[List[str]] = Field(None, description="IDs específicos de videos a importar")
    auto_activate: bool = Field(True, description="Activar videos automáticamente")
    default_points: int = Field(10, ge=0, description="Puntos por defecto para videos importados")

class VideoImportResponse(BaseModel):
    """Schema para respuesta de importación"""
    success: bool = Field(..., description="Si la importación fue exitosa")
    imported_count: int = Field(0, description="Número de videos importados")
    skipped_count: int = Field(0, description="Número de videos omitidos")
    errors: List[str] = Field(default_factory=list, description="Errores encontrados")
    imported_videos: List[VideoResponse] = Field(default_factory=list, description="Videos importados")

class VideoWatchSession(BaseModel):
    """Schema para sesión de visualización"""
    video_id: int = Field(..., description="ID del video")
    start_time: datetime = Field(..., description="Hora de inicio")
    end_time: Optional[datetime] = Field(None, description="Hora de fin")
    duration_watched: int = Field(0, description="Duración vista en segundos")
    completion_percentage: int = Field(0, ge=0, le=100, description="Porcentaje de completación")
    paused_count: int = Field(0, description="Número de pausas")
    seek_count: int = Field(0, description="Número de saltos")
    quality: Optional[str] = Field(None, description="Calidad de video")
    device_type: Optional[str] = Field(None, description="Tipo de dispositivo")

class VideoWatchSessionResponse(VideoWatchSession):
    """Schema para respuesta de sesión de visualización"""
    id: int
    user_id: int
    site_id: str
    points_earned: int = 0
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class VideoRecommendation(BaseModel):
    """Schema para recomendaciones de video"""
    video_id: int
    titulo: str
    youtube_id: str
    thumbnail_url: Optional[str] = None
    duracion_segundos: Optional[int] = None
    tipo_video: VideoType
    reason: str = Field(..., description="Razón de la recomendación")
    score: float = Field(..., ge=0, le=1, description="Puntuación de recomendación")

class VideoRecommendationResponse(BaseModel):
    """Schema para respuesta de recomendaciones"""
    recommendations: List[VideoRecommendation]
    user_id: int
    total_recommendations: int
    algorithm_version: str = "v1.0"

class VideoEngagement(BaseModel):
    """Schema para engagement de video"""
    video_id: int
    titulo: str
    youtube_id: str
    total_views: int = 0
    total_completions: int = 0
    completion_rate: float = 0.0
    average_watch_time: float = 0.0
    engagement_score: float = 0.0
    last_viewed: Optional[datetime] = None
    trending: bool = False

class VideoEngagementResponse(BaseModel):
    """Schema para respuesta de engagement"""
    videos: List[VideoEngagement]
    total_videos: int
    average_engagement: float
    most_engaged_video: Optional[VideoEngagement] = None
    least_engaged_video: Optional[VideoEngagement] = None
