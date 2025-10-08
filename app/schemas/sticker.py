from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class StickerType(str, Enum):
    """Tipos de stickers disponibles"""
    REGISTRO = "registro"
    INSTAGRAM = "instagram"
    RESENA = "reseña"
    VIDEO = "video"
    ESPECIAL = "especial"

class StickerStatus(str, Enum):
    """Estados del sticker"""
    GENERADO = "generado"
    DESCARGADO = "descargado"
    USADO = "usado"
    EXPIRADO = "expirado"

class StickerFormat(str, Enum):
    """Formatos de descarga"""
    PNG = "png"
    PDF = "pdf"
    SVG = "svg"
    JPG = "jpg"

class StickerBase(BaseModel):
    """Schema base para stickers"""
    tipo_sticker: StickerType = Field(..., description="Tipo de sticker")
    porcentaje_descuento: int = Field(..., ge=1, le=100, description="Porcentaje de descuento")
    fecha_expiracion: datetime = Field(..., description="Fecha de expiración del sticker")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadatos adicionales")

class StickerCreate(StickerBase):
    """Schema para crear un nuevo sticker"""
    usuario_id: int = Field(..., description="ID del usuario que genera el sticker")
    
    @validator('porcentaje_descuento')
    def validate_discount_percentage(cls, v):
        if v < 1 or v > 100:
            raise ValueError('Discount percentage must be between 1 and 100')
        return v

class StickerUpdate(BaseModel):
    """Schema para actualizar un sticker"""
    porcentaje_descuento: Optional[int] = Field(None, ge=1, le=100)
    fecha_expiracion: Optional[datetime] = None
    usado: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None

class StickerResponse(StickerBase):
    """Schema para respuesta de sticker"""
    id: int
    site_id: str
    usuario_id: int
    codigo_descuento: str
    qr_code_url: Optional[str] = None
    imagen_url: Optional[str] = None
    usado: bool = False
    fecha_uso: Optional[datetime] = None
    fecha_generacion: datetime
    sincronizado_odoo: bool = False
    id_odoo: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class StickerDownload(BaseModel):
    """Schema para descarga de sticker"""
    formato: StickerFormat = Field(..., description="Formato de descarga")
    calidad: str = Field("alta", description="Calidad de la imagen")
    incluir_qr: bool = Field(True, description="Incluir código QR")
    personalizado: Optional[Dict[str, Any]] = Field(None, description="Personalizaciones adicionales")

class StickerTemplate(BaseModel):
    """Schema para template de sticker"""
    id: str = Field(..., description="ID del template")
    nombre: str = Field(..., description="Nombre del template")
    descripcion: str = Field(..., description="Descripción del template")
    preview_url: str = Field(..., description="URL de preview")
    configuracion: Dict[str, Any] = Field(..., description="Configuración del template")
    activo: bool = Field(True, description="Si el template está activo")

class StickerDesign(BaseModel):
    """Schema para diseño de sticker"""
    template_id: str = Field(..., description="ID del template a usar")
    colores: Dict[str, str] = Field(..., description="Colores personalizados")
    logo_url: Optional[str] = Field(None, description="URL del logo personalizado")
    texto_personalizado: Optional[str] = Field(None, description="Texto adicional")
    elementos: List[Dict[str, Any]] = Field(default_factory=list, description="Elementos adicionales")

class StickerBatch(BaseModel):
    """Schema para generación masiva de stickers"""
    usuario_id: int = Field(..., description="ID del usuario")
    cantidad: int = Field(..., ge=1, le=10, description="Cantidad de stickers a generar")
    tipo_sticker: StickerType = Field(..., description="Tipo de stickers")
    porcentaje_descuento: int = Field(..., ge=1, le=100)
    fecha_expiracion: datetime
    metadata: Optional[Dict[str, Any]] = None

class StickerStats(BaseModel):
    """Schema para estadísticas de stickers"""
    total_generados: int = Field(0, description="Total de stickers generados")
    total_usados: int = Field(0, description="Total de stickers usados")
    total_expirados: int = Field(0, description="Total de stickers expirados")
    porcentaje_uso: float = Field(0.0, description="Porcentaje de uso")
    stickers_por_tipo: Dict[str, int] = Field(default_factory=dict, description="Stickers por tipo")
    stickers_por_mes: List[Dict[str, Any]] = Field(default_factory=list, description="Stickers por mes")

class StickerValidation(BaseModel):
    """Schema para validación de sticker"""
    codigo_descuento: str = Field(..., description="Código a validar")
    usuario_id: Optional[int] = Field(None, description="ID del usuario (opcional)")

class StickerValidationResponse(BaseModel):
    """Schema para respuesta de validación"""
    valido: bool = Field(..., description="Si el código es válido")
    sticker: Optional[StickerResponse] = Field(None, description="Datos del sticker si es válido")
    mensaje: str = Field(..., description="Mensaje de validación")
    descuento_aplicable: Optional[int] = Field(None, description="Descuento aplicable")

class StickerList(BaseModel):
    """Schema para listado de stickers"""
    stickers: List[StickerResponse]
    total: int
    page: int
    size: int
    total_pages: int

class StickerSearch(BaseModel):
    """Schema para búsqueda de stickers"""
    query: Optional[str] = Field(None, description="Término de búsqueda")
    tipo_sticker: Optional[StickerType] = Field(None, description="Filtrar por tipo")
    usuario_id: Optional[int] = Field(None, description="Filtrar por usuario")
    usado: Optional[bool] = Field(None, description="Filtrar por estado de uso")
    fecha_desde: Optional[datetime] = Field(None, description="Fecha desde")
    fecha_hasta: Optional[datetime] = Field(None, description="Fecha hasta")
    page: int = Field(1, ge=1, description="Número de página")
    size: int = Field(10, ge=1, le=100, description="Tamaño de página")
    sort_by: str = Field("fecha_generacion", description="Campo de ordenamiento")
    sort_order: str = Field("desc", description="Orden de clasificación")

class StickerExport(BaseModel):
    """Schema para exportar stickers"""
    formato: str = Field("csv", description="Formato de exportación")
    filtros: Optional[StickerSearch] = Field(None, description="Filtros a aplicar")
    incluir_metadatos: bool = Field(True, description="Incluir metadatos en la exportación")

class StickerAnalytics(BaseModel):
    """Schema para analytics de stickers"""
    periodo: str = Field("30d", description="Período de análisis")
    metricas: Dict[str, Any] = Field(default_factory=dict, description="Métricas calculadas")
    tendencias: List[Dict[str, Any]] = Field(default_factory=list, description="Tendencias")
    comparacion: Optional[Dict[str, Any]] = Field(None, description="Comparación con período anterior")

class StickerNotification(BaseModel):
    """Schema para notificaciones de sticker"""
    tipo: str = Field(..., description="Tipo de notificación")
    titulo: str = Field(..., description="Título de la notificación")
    mensaje: str = Field(..., description="Mensaje de la notificación")
    sticker_id: int = Field(..., description="ID del sticker relacionado")
    usuario_id: int = Field(..., description="ID del usuario")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadatos adicionales")

class StickerCampaign(BaseModel):
    """Schema para campaña de stickers"""
    nombre: str = Field(..., description="Nombre de la campaña")
    descripcion: str = Field(..., description="Descripción de la campaña")
    tipo_sticker: StickerType = Field(..., description="Tipo de stickers de la campaña")
    porcentaje_descuento: int = Field(..., ge=1, le=100)
    fecha_inicio: datetime = Field(..., description="Fecha de inicio")
    fecha_fin: datetime = Field(..., description="Fecha de fin")
    max_stickers: Optional[int] = Field(None, description="Máximo de stickers a generar")
    condiciones: Dict[str, Any] = Field(default_factory=dict, description="Condiciones de la campaña")
    activa: bool = Field(True, description="Si la campaña está activa")

class StickerCampaignResponse(StickerCampaign):
    """Schema para respuesta de campaña"""
    id: int
    site_id: str
    stickers_generados: int = Field(0, description="Stickers generados en la campaña")
    stickers_usados: int = Field(0, description="Stickers usados en la campaña")
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True
