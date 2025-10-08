from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class SiteType(str, enum.Enum):
    MARIACHI = "mariachi"
    RESTAURANT = "restaurant"
    ECOMMERCE = "ecommerce"
    SERVICES = "services"
    GENERAL = "general"

class SiteConfig(Base):
    __tablename__ = "site_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String(50), unique=True, index=True, nullable=False)  # cliente-123
    site_name = Column(String(100), nullable=False)  # "Mariachi Sol del Águila"
    site_type = Column(Enum(SiteType), default=SiteType.MARIACHI)
    
    # Configuración de branding
    primary_color = Column(String(7), default="#e74c3c")
    secondary_color = Column(String(7), default="#2c3e50")
    logo_url = Column(String(500))
    favicon_url = Column(String(500))
    
    # Configuración de descuentos
    max_discount_percentage = Column(Integer, default=15)
    discount_per_action = Column(Integer, default=5)
    sticker_expiration_days = Column(Integer, default=30)
    
    # Configuración de puntos
    points_per_video = Column(Integer, default=10)
    points_per_like = Column(Integer, default=1)
    points_per_comment = Column(Integer, default=2)
    points_per_review = Column(Integer, default=5)
    
    # Configuración de videos
    youtube_playlist_id = Column(String(100))
    video_progression_enabled = Column(Boolean, default=True)
    
    # Configuración de integraciones
    instagram_required = Column(Boolean, default=True)
    odoo_integration = Column(Boolean, default=False)
    odoo_url = Column(String(500))
    odoo_database = Column(String(100))
    odoo_username = Column(String(100))
    odoo_password = Column(String(100))
    
    # Configuración de emails
    email_from = Column(String(100))
    email_signature = Column(Text)
    
    # Configuración de textos
    welcome_message = Column(Text)
    sticker_message = Column(Text)
    video_completion_message = Column(Text)
    
    # Configuración de dominio
    allowed_domains = Column(JSON)  # ["mariachisoldelaguila.com", "www.mariachisoldelaguila.com"]
    
    # Estado del sitio
    activo = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones (temporalmente comentadas para evitar errores de FK)
    # users = relationship("User", back_populates="site_config", cascade="all, delete-orphan")
    # stickers = relationship("Sticker", back_populates="site_config", cascade="all, delete-orphan")
    # videos = relationship("Video", back_populates="site_config", cascade="all, delete-orphan")
    # interactions = relationship("Interaction", back_populates="site_config", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SiteConfig(site_id='{self.site_id}', site_name='{self.site_name}')>"
