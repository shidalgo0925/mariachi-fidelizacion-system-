from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class StickerType(str, enum.Enum):
    REGISTRO = "registro"
    INSTAGRAM = "instagram"
    RESENA = "reseña"
    VIDEO = "video"
    ENGAGEMENT = "engagement"

class Sticker(Base):
    __tablename__ = "stickers"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String(50), ForeignKey("site_configs.site_id"), nullable=False, index=True)
    usuario_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Información del sticker
    tipo_sticker = Column(Enum(StickerType), nullable=False)
    codigo_descuento = Column(String(20), unique=True, index=True, nullable=False)
    porcentaje_descuento = Column(Integer, default=5)
    
    # Fechas
    fecha_generacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_expiracion = Column(DateTime(timezone=True), nullable=False)
    
    # Estado del sticker
    usado = Column(Boolean, default=False)
    fecha_uso = Column(DateTime(timezone=True))
    usado_por = Column(String(100))  # Información de quién lo usó
    
    # Archivos generados
    pdf_path = Column(String(500))  # Ruta al PDF generado
    qr_code_path = Column(String(500))  # Ruta al QR code
    
    # Integración con sistemas externos
    sincronizado_odoo = Column(Boolean, default=False)
    id_odoo = Column(String(50))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    site_config = relationship("SiteConfig", back_populates="stickers")
    usuario = relationship("User", back_populates="stickers")
    
    def __repr__(self):
        return f"<Sticker(id={self.id}, codigo='{self.codigo_descuento}', tipo='{self.tipo_sticker}')>"
