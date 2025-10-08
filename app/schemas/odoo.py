from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class OdooConnectionStatus(str, Enum):
    """Estados de conexión con Odoo"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    TESTING = "testing"

class OdooSyncStatus(str, Enum):
    """Estados de sincronización"""
    PENDING = "pending"
    SYNCING = "syncing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"

class OdooModelType(str, Enum):
    """Tipos de modelos de Odoo"""
    PARTNER = "res.partner"
    PRODUCT = "product.product"
    SALE_ORDER = "sale.order"
    ACCOUNT_MOVE = "account.move"
    PROJECT = "project.project"
    TASK = "project.task"

class OdooConfigBase(BaseModel):
    """Schema base para configuración de Odoo"""
    odoo_url: str = Field(..., description="URL del servidor Odoo")
    odoo_database: str = Field(..., description="Nombre de la base de datos")
    odoo_username: str = Field(..., description="Usuario de Odoo")
    odoo_password: str = Field(..., description="Contraseña de Odoo")
    auto_sync: bool = Field(True, description="Sincronización automática habilitada")
    sync_interval: int = Field(30, ge=1, description="Intervalo de sincronización en minutos")
    max_retries: int = Field(3, ge=1, le=10, description="Máximo de reintentos")

class OdooConfigCreate(OdooConfigBase):
    """Schema para crear configuración de Odoo"""
    pass

class OdooConfigUpdate(BaseModel):
    """Schema para actualizar configuración de Odoo"""
    odoo_url: Optional[str] = None
    odoo_database: Optional[str] = None
    odoo_username: Optional[str] = None
    odoo_password: Optional[str] = None
    auto_sync: Optional[bool] = None
    sync_interval: Optional[int] = Field(None, ge=1)
    max_retries: Optional[int] = Field(None, ge=1, le=10)

class OdooConfigResponse(OdooConfigBase):
    """Schema para respuesta de configuración de Odoo"""
    id: int
    site_id: str
    connection_status: OdooConnectionStatus
    last_sync: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class OdooSyncLogBase(BaseModel):
    """Schema base para logs de sincronización"""
    model_type: OdooModelType = Field(..., description="Tipo de modelo sincronizado")
    record_id: int = Field(..., description="ID del registro local")
    odoo_id: Optional[int] = Field(None, description="ID en Odoo")
    operation: str = Field(..., description="Operación realizada (create, update, delete)")
    status: OdooSyncStatus = Field(..., description="Estado de la sincronización")
    error_message: Optional[str] = Field(None, description="Mensaje de error si falló")

class OdooSyncLogCreate(OdooSyncLogBase):
    """Schema para crear log de sincronización"""
    pass

class OdooSyncLogResponse(OdooSyncLogBase):
    """Schema para respuesta de log de sincronización"""
    id: int
    site_id: str
    sync_timestamp: datetime
    retry_count: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True

class OdooPartnerData(BaseModel):
    """Schema para datos de partner en Odoo"""
    name: str = Field(..., description="Nombre del partner")
    email: Optional[str] = Field(None, description="Email del partner")
    phone: Optional[str] = Field(None, description="Teléfono del partner")
    is_company: bool = Field(False, description="Si es una empresa")
    customer_rank: int = Field(1, description="Ranking de cliente")
    supplier_rank: int = Field(0, description="Ranking de proveedor")
    x_site_id: str = Field(..., description="ID del sitio")
    x_user_id: int = Field(..., description="ID del usuario local")
    x_puntos_acumulados: int = Field(0, description="Puntos acumulados")
    x_total_descuento: int = Field(0, description="Total de descuento")
    x_instagram_seguido: bool = Field(False, description="Si sigue en Instagram")
    x_activo: bool = Field(True, description="Si está activo")

class OdooProductData(BaseModel):
    """Schema para datos de producto en Odoo"""
    name: str = Field(..., description="Nombre del producto")
    type: str = Field("service", description="Tipo de producto")
    categ_id: int = Field(1, description="ID de categoría")
    list_price: float = Field(0.0, description="Precio de lista")
    standard_price: float = Field(0.0, description="Precio estándar")
    sale_ok: bool = Field(True, description="Disponible para venta")
    purchase_ok: bool = Field(False, description="Disponible para compra")
    x_site_id: str = Field(..., description="ID del sitio")
    x_sticker_id: int = Field(..., description="ID del sticker local")
    x_codigo_descuento: str = Field(..., description="Código de descuento")
    x_porcentaje_descuento: int = Field(..., description="Porcentaje de descuento")
    x_tipo_sticker: str = Field(..., description="Tipo de sticker")
    x_usuario_id: int = Field(..., description="ID del usuario")
    x_fecha_expiracion: Optional[datetime] = Field(None, description="Fecha de expiración")
    x_usado: bool = Field(False, description="Si fue usado")

class OdooSyncRequest(BaseModel):
    """Schema para solicitud de sincronización"""
    model_type: OdooModelType = Field(..., description="Tipo de modelo a sincronizar")
    record_ids: Optional[List[int]] = Field(None, description="IDs específicos a sincronizar")
    force_sync: bool = Field(False, description="Forzar sincronización aunque ya esté sincronizado")
    sync_all: bool = Field(False, description="Sincronizar todos los registros del tipo")

class OdooSyncResponse(BaseModel):
    """Schema para respuesta de sincronización"""
    success: bool = Field(..., description="Si la sincronización fue exitosa")
    message: str = Field(..., description="Mensaje de resultado")
    synced_count: int = Field(0, description="Número de registros sincronizados")
    failed_count: int = Field(0, description="Número de registros que fallaron")
    errors: List[str] = Field(default_factory=list, description="Lista de errores")
    sync_logs: List[OdooSyncLogResponse] = Field(default_factory=list, description="Logs de sincronización")

class OdooConnectionTest(BaseModel):
    """Schema para prueba de conexión"""
    odoo_url: str = Field(..., description="URL del servidor Odoo")
    odoo_database: str = Field(..., description="Nombre de la base de datos")
    odoo_username: str = Field(..., description="Usuario de Odoo")
    odoo_password: str = Field(..., description="Contraseña de Odoo")

class OdooConnectionTestResponse(BaseModel):
    """Schema para respuesta de prueba de conexión"""
    success: bool = Field(..., description="Si la conexión fue exitosa")
    message: str = Field(..., description="Mensaje de resultado")
    version: Optional[str] = Field(None, description="Versión de Odoo")
    database_info: Optional[Dict[str, Any]] = Field(None, description="Información de la base de datos")
    user_info: Optional[Dict[str, Any]] = Field(None, description="Información del usuario")

class OdooAnalytics(BaseModel):
    """Schema para analytics de Odoo"""
    period: str = Field("30d", description="Período de análisis")
    total_syncs: int = Field(0, description="Total de sincronizaciones")
    successful_syncs: int = Field(0, description="Sincronizaciones exitosas")
    failed_syncs: int = Field(0, description="Sincronizaciones fallidas")
    success_rate: float = Field(0.0, description="Tasa de éxito")
    syncs_by_model: Dict[str, int] = Field(default_factory=dict, description="Sincronizaciones por modelo")
    daily_syncs: List[Dict[str, Any]] = Field(default_factory=list, description="Sincronizaciones diarias")
    error_summary: List[Dict[str, Any]] = Field(default_factory=list, description="Resumen de errores")

class OdooReport(BaseModel):
    """Schema para reportes de Odoo"""
    report_type: str = Field(..., description="Tipo de reporte")
    date_from: Optional[datetime] = Field(None, description="Fecha desde")
    date_to: Optional[datetime] = Field(None, description="Fecha hasta")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filtros adicionales")
    format: str = Field("json", description="Formato del reporte")

class OdooReportResponse(BaseModel):
    """Schema para respuesta de reporte"""
    success: bool = Field(..., description="Si el reporte fue generado exitosamente")
    message: str = Field(..., description="Mensaje de resultado")
    report_data: Optional[Dict[str, Any]] = Field(None, description="Datos del reporte")
    download_url: Optional[str] = Field(None, description="URL de descarga si es archivo")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Fecha de generación")

class OdooWebhook(BaseModel):
    """Schema para webhook de Odoo"""
    event_type: str = Field(..., description="Tipo de evento")
    model: str = Field(..., description="Modelo de Odoo")
    record_id: int = Field(..., description="ID del registro")
    data: Dict[str, Any] = Field(..., description="Datos del evento")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp del evento")

class OdooWebhookResponse(BaseModel):
    """Schema para respuesta de webhook"""
    success: bool = Field(..., description="Si el webhook fue procesado exitosamente")
    message: str = Field(..., description="Mensaje de resultado")
    processed: bool = Field(False, description="Si el evento fue procesado")

class OdooDashboard(BaseModel):
    """Schema para dashboard de Odoo"""
    connection_status: OdooConnectionStatus
    last_sync: Optional[datetime] = None
    total_partners: int = 0
    total_products: int = 0
    total_orders: int = 0
    pending_syncs: int = 0
    failed_syncs: int = 0
    sync_success_rate: float = 0.0
    recent_activities: List[Dict[str, Any]] = Field(default_factory=list, description="Actividades recientes")
    sync_statistics: Dict[str, Any] = Field(default_factory=dict, description="Estadísticas de sincronización")

class OdooError(BaseModel):
    """Schema para errores de Odoo"""
    error_type: str = Field(..., description="Tipo de error")
    error_message: str = Field(..., description="Mensaje de error")
    error_code: Optional[str] = Field(None, description="Código de error")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp del error")
    site_id: Optional[str] = Field(None, description="ID del sitio")
    model_type: Optional[OdooModelType] = Field(None, description="Tipo de modelo")
    record_id: Optional[int] = Field(None, description="ID del registro")

class OdooRetryRequest(BaseModel):
    """Schema para solicitud de reintento"""
    sync_log_id: int = Field(..., description="ID del log de sincronización")
    force_retry: bool = Field(False, description="Forzar reintento")

class OdooRetryResponse(BaseModel):
    """Schema para respuesta de reintento"""
    success: bool = Field(..., description="Si el reintento fue exitoso")
    message: str = Field(..., description="Mensaje de resultado")
    new_sync_log: Optional[OdooSyncLogResponse] = Field(None, description="Nuevo log de sincronización")
