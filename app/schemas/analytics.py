from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

class AnalyticsPeriod(str, Enum):
    """Períodos de análisis"""
    HOUR = "1h"
    DAY = "1d"
    WEEK = "1w"
    MONTH = "1m"
    QUARTER = "3m"
    YEAR = "1y"
    CUSTOM = "custom"

class ReportFormat(str, Enum):
    """Formatos de reporte"""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    XLSX = "xlsx"
    HTML = "html"

class ReportType(str, Enum):
    """Tipos de reporte"""
    USER_ACTIVITY = "user_activity"
    ENGAGEMENT = "engagement"
    STICKER_USAGE = "sticker_usage"
    VIDEO_ANALYTICS = "video_analytics"
    NOTIFICATION_PERFORMANCE = "notification_performance"
    REVENUE = "revenue"
    CUSTOM = "custom"

class MetricType(str, Enum):
    """Tipos de métricas"""
    COUNT = "count"
    SUM = "sum"
    AVERAGE = "average"
    PERCENTAGE = "percentage"
    RATIO = "ratio"
    GROWTH_RATE = "growth_rate"

class AnalyticsMetric(BaseModel):
    """Schema para métricas de analytics"""
    name: str = Field(..., description="Nombre de la métrica")
    value: float = Field(..., description="Valor de la métrica")
    type: MetricType = Field(..., description="Tipo de métrica")
    unit: Optional[str] = Field(None, description="Unidad de medida")
    change_percentage: Optional[float] = Field(None, description="Cambio porcentual")
    previous_value: Optional[float] = Field(None, description="Valor anterior")
    trend: Optional[str] = Field(None, description="Tendencia (up, down, stable)")

class AnalyticsDimension(BaseModel):
    """Schema para dimensiones de analytics"""
    name: str = Field(..., description="Nombre de la dimensión")
    value: str = Field(..., description="Valor de la dimensión")
    count: int = Field(..., description="Cantidad")
    percentage: float = Field(..., description="Porcentaje")

class TimeSeriesData(BaseModel):
    """Schema para datos de series temporales"""
    timestamp: datetime = Field(..., description="Timestamp del dato")
    value: float = Field(..., description="Valor en el timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadatos adicionales")

class AnalyticsQuery(BaseModel):
    """Schema para consultas de analytics"""
    site_id: str = Field(..., description="ID del sitio")
    period: AnalyticsPeriod = Field(AnalyticsPeriod.DAY, description="Período de análisis")
    start_date: Optional[datetime] = Field(None, description="Fecha de inicio (para período personalizado)")
    end_date: Optional[datetime] = Field(None, description="Fecha de fin (para período personalizado)")
    metrics: List[str] = Field(..., description="Lista de métricas a calcular")
    dimensions: Optional[List[str]] = Field(None, description="Dimensiones para agrupar")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filtros adicionales")
    group_by: Optional[str] = Field(None, description="Agrupación temporal (hour, day, week, month)")

class AnalyticsResponse(BaseModel):
    """Schema para respuesta de analytics"""
    site_id: str = Field(..., description="ID del sitio")
    period: str = Field(..., description="Período analizado")
    start_date: datetime = Field(..., description="Fecha de inicio")
    end_date: datetime = Field(..., description="Fecha de fin")
    metrics: List[AnalyticsMetric] = Field(..., description="Métricas calculadas")
    dimensions: Optional[List[AnalyticsDimension]] = Field(None, description="Dimensiones")
    time_series: Optional[List[TimeSeriesData]] = Field(None, description="Datos de series temporales")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Fecha de generación")

class UserActivityAnalytics(BaseModel):
    """Schema para analytics de actividad de usuarios"""
    total_users: int = Field(0, description="Total de usuarios")
    active_users: int = Field(0, description="Usuarios activos")
    new_users: int = Field(0, description="Usuarios nuevos")
    returning_users: int = Field(0, description="Usuarios que regresan")
    user_retention_rate: float = Field(0.0, description="Tasa de retención")
    average_session_duration: float = Field(0.0, description="Duración promedio de sesión")
    users_by_source: List[AnalyticsDimension] = Field(default_factory=list, description="Usuarios por fuente")
    users_by_device: List[AnalyticsDimension] = Field(default_factory=list, description="Usuarios por dispositivo")
    daily_active_users: List[TimeSeriesData] = Field(default_factory=list, description="Usuarios activos diarios")

class EngagementAnalytics(BaseModel):
    """Schema para analytics de engagement"""
    total_interactions: int = Field(0, description="Total de interacciones")
    interactions_per_user: float = Field(0.0, description="Interacciones por usuario")
    engagement_rate: float = Field(0.0, description="Tasa de engagement")
    most_engaged_content: List[AnalyticsDimension] = Field(default_factory=list, description="Contenido más interactivo")
    interactions_by_type: List[AnalyticsDimension] = Field(default_factory=list, description="Interacciones por tipo")
    engagement_trend: List[TimeSeriesData] = Field(default_factory=list, description="Tendencia de engagement")
    top_users: List[AnalyticsDimension] = Field(default_factory=list, description="Usuarios más activos")

class StickerAnalytics(BaseModel):
    """Schema para analytics de stickers"""
    total_stickers_generated: int = Field(0, description="Total de stickers generados")
    total_stickers_used: int = Field(0, description="Total de stickers usados")
    sticker_usage_rate: float = Field(0.0, description="Tasa de uso de stickers")
    average_discount_percentage: float = Field(0.0, description="Descuento promedio")
    total_discount_value: float = Field(0.0, description="Valor total de descuentos")
    stickers_by_type: List[AnalyticsDimension] = Field(default_factory=list, description="Stickers por tipo")
    sticker_generation_trend: List[TimeSeriesData] = Field(default_factory=list, description="Tendencia de generación")
    top_discount_codes: List[AnalyticsDimension] = Field(default_factory=list, description="Códigos más usados")

class VideoAnalytics(BaseModel):
    """Schema para analytics de videos"""
    total_videos: int = Field(0, description="Total de videos")
    total_views: int = Field(0, description="Total de visualizaciones")
    total_completions: int = Field(0, description="Total de completaciones")
    completion_rate: float = Field(0.0, description="Tasa de completación")
    average_watch_time: float = Field(0.0, description="Tiempo promedio de visualización")
    most_watched_videos: List[AnalyticsDimension] = Field(default_factory=list, description="Videos más vistos")
    video_performance_trend: List[TimeSeriesData] = Field(default_factory=list, description="Tendencia de rendimiento")
    user_engagement_by_video: List[AnalyticsDimension] = Field(default_factory=list, description="Engagement por video")

class NotificationAnalytics(BaseModel):
    """Schema para analytics de notificaciones"""
    total_notifications_sent: int = Field(0, description="Total de notificaciones enviadas")
    total_notifications_delivered: int = Field(0, description="Total de notificaciones entregadas")
    total_notifications_read: int = Field(0, description="Total de notificaciones leídas")
    delivery_rate: float = Field(0.0, description="Tasa de entrega")
    read_rate: float = Field(0.0, description="Tasa de lectura")
    notifications_by_type: List[AnalyticsDimension] = Field(default_factory=list, description="Notificaciones por tipo")
    notifications_by_channel: List[AnalyticsDimension] = Field(default_factory=list, description="Notificaciones por canal")
    notification_performance_trend: List[TimeSeriesData] = Field(default_factory=list, description="Tendencia de rendimiento")

class RevenueAnalytics(BaseModel):
    """Schema para analytics de ingresos"""
    total_revenue: float = Field(0.0, description="Ingresos totales")
    revenue_growth_rate: float = Field(0.0, description="Tasa de crecimiento de ingresos")
    average_order_value: float = Field(0.0, description="Valor promedio de orden")
    revenue_by_source: List[AnalyticsDimension] = Field(default_factory=list, description="Ingresos por fuente")
    revenue_trend: List[TimeSeriesData] = Field(default_factory=list, description="Tendencia de ingresos")
    top_revenue_generators: List[AnalyticsDimension] = Field(default_factory=list, description="Generadores de ingresos")

class DashboardMetrics(BaseModel):
    """Schema para métricas del dashboard"""
    site_id: str = Field(..., description="ID del sitio")
    period: str = Field(..., description="Período del dashboard")
    user_activity: UserActivityAnalytics = Field(..., description="Métricas de actividad de usuarios")
    engagement: EngagementAnalytics = Field(..., description="Métricas de engagement")
    stickers: StickerAnalytics = Field(..., description="Métricas de stickers")
    videos: VideoAnalytics = Field(..., description="Métricas de videos")
    notifications: NotificationAnalytics = Field(..., description="Métricas de notificaciones")
    revenue: Optional[RevenueAnalytics] = Field(None, description="Métricas de ingresos")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Fecha de generación")

class ReportRequest(BaseModel):
    """Schema para solicitud de reporte"""
    site_id: str = Field(..., description="ID del sitio")
    report_type: ReportType = Field(..., description="Tipo de reporte")
    format: ReportFormat = Field(ReportFormat.PDF, description="Formato del reporte")
    period: AnalyticsPeriod = Field(AnalyticsPeriod.MONTH, description="Período del reporte")
    start_date: Optional[datetime] = Field(None, description="Fecha de inicio")
    end_date: Optional[datetime] = Field(None, description="Fecha de fin")
    metrics: List[str] = Field(..., description="Métricas a incluir")
    dimensions: Optional[List[str]] = Field(None, description="Dimensiones a incluir")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filtros adicionales")
    include_charts: bool = Field(True, description="Incluir gráficos")
    include_raw_data: bool = Field(False, description="Incluir datos raw")
    email_to: Optional[List[str]] = Field(None, description="Emails para envío")

class ReportResponse(BaseModel):
    """Schema para respuesta de reporte"""
    report_id: str = Field(..., description="ID del reporte")
    report_type: ReportType = Field(..., description="Tipo de reporte")
    format: ReportFormat = Field(..., description="Formato del reporte")
    status: str = Field(..., description="Estado del reporte")
    download_url: Optional[str] = Field(None, description="URL de descarga")
    file_size: Optional[int] = Field(None, description="Tamaño del archivo")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Fecha de generación")
    expires_at: Optional[datetime] = Field(None, description="Fecha de expiración")
    error_message: Optional[str] = Field(None, description="Mensaje de error si falló")

class ExportRequest(BaseModel):
    """Schema para solicitud de exportación"""
    site_id: str = Field(..., description="ID del sitio")
    data_type: str = Field(..., description="Tipo de datos a exportar")
    format: ReportFormat = Field(ReportFormat.CSV, description="Formato de exportación")
    start_date: Optional[datetime] = Field(None, description="Fecha de inicio")
    end_date: Optional[datetime] = Field(None, description="Fecha de fin")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filtros adicionales")
    fields: Optional[List[str]] = Field(None, description="Campos específicos a exportar")
    include_headers: bool = Field(True, description="Incluir encabezados")

class ExportResponse(BaseModel):
    """Schema para respuesta de exportación"""
    export_id: str = Field(..., description="ID de la exportación")
    data_type: str = Field(..., description="Tipo de datos exportados")
    format: ReportFormat = Field(..., description="Formato de exportación")
    status: str = Field(..., description="Estado de la exportación")
    download_url: Optional[str] = Field(None, description="URL de descarga")
    file_size: Optional[int] = Field(None, description="Tamaño del archivo")
    record_count: Optional[int] = Field(None, description="Número de registros")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Fecha de generación")
    expires_at: Optional[datetime] = Field(None, description="Fecha de expiración")
    error_message: Optional[str] = Field(None, description="Mensaje de error si falló")

class RealTimeMetrics(BaseModel):
    """Schema para métricas en tiempo real"""
    site_id: str = Field(..., description="ID del sitio")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp de las métricas")
    active_users: int = Field(0, description="Usuarios activos ahora")
    total_sessions: int = Field(0, description="Total de sesiones activas")
    interactions_last_hour: int = Field(0, description="Interacciones en la última hora")
    notifications_sent_today: int = Field(0, description="Notificaciones enviadas hoy")
    stickers_generated_today: int = Field(0, description="Stickers generados hoy")
    videos_watched_today: int = Field(0, description="Videos vistos hoy")
    system_health: Dict[str, Any] = Field(default_factory=dict, description="Estado del sistema")

class AnalyticsAlert(BaseModel):
    """Schema para alertas de analytics"""
    alert_id: str = Field(..., description="ID de la alerta")
    site_id: str = Field(..., description="ID del sitio")
    alert_type: str = Field(..., description="Tipo de alerta")
    metric_name: str = Field(..., description="Nombre de la métrica")
    threshold_value: float = Field(..., description="Valor umbral")
    current_value: float = Field(..., description="Valor actual")
    severity: str = Field(..., description="Severidad (low, medium, high, critical)")
    message: str = Field(..., description="Mensaje de la alerta")
    triggered_at: datetime = Field(default_factory=datetime.utcnow, description="Fecha de activación")
    resolved_at: Optional[datetime] = Field(None, description="Fecha de resolución")
    status: str = Field("active", description="Estado de la alerta")

class AnalyticsComparison(BaseModel):
    """Schema para comparación de analytics"""
    metric_name: str = Field(..., description="Nombre de la métrica")
    current_period: AnalyticsMetric = Field(..., description="Métrica del período actual")
    previous_period: AnalyticsMetric = Field(..., description="Métrica del período anterior")
    change_absolute: float = Field(..., description="Cambio absoluto")
    change_percentage: float = Field(..., description="Cambio porcentual")
    trend: str = Field(..., description="Tendencia (up, down, stable)")
    significance: str = Field(..., description="Significancia del cambio")

class AnalyticsInsight(BaseModel):
    """Schema para insights de analytics"""
    insight_id: str = Field(..., description="ID del insight")
    site_id: str = Field(..., description="ID del sitio")
    insight_type: str = Field(..., description="Tipo de insight")
    title: str = Field(..., description="Título del insight")
    description: str = Field(..., description="Descripción del insight")
    confidence: float = Field(..., description="Nivel de confianza (0-1)")
    impact: str = Field(..., description="Impacto (low, medium, high)")
    recommendations: List[str] = Field(default_factory=list, description="Recomendaciones")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Fecha de generación")
    expires_at: Optional[datetime] = Field(None, description="Fecha de expiración")
