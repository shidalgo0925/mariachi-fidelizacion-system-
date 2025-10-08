from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String(50), ForeignKey("site_configs.site_id"), nullable=False, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, index=True)
    telefono = Column(String(20))
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    
    # Sistema de puntos
    puntos_acumulados = Column(Integer, default=0)
    total_descuento = Column(Integer, default=0)
    
    # Estado de integraciones
    instagram_seguido = Column(Boolean, default=False)
    instagram_user_id = Column(String(100))
    instagram_access_token = Column(String(500))
    
    # Contadores de actividad
    reseñas_dejadas = Column(Integer, default=0)
    videos_completados = Column(Integer, default=0)
    stickers_generados = Column(Integer, default=0)
    
    # Integración con sistemas externos
    sincronizado_odoo = Column(Boolean, default=False)
    id_odoo = Column(String(50))
    fecha_sincronizacion = Column(DateTime(timezone=True))
    
    # Estado del usuario
    activo = Column(Boolean, default=True)
    verificado = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    site_config = relationship("SiteConfig", back_populates="users")
    stickers = relationship("Sticker", back_populates="usuario", cascade="all, delete-orphan")
    interactions = relationship("Interaction", back_populates="usuario", cascade="all, delete-orphan")
    instagram_connection = relationship("InstagramUser", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    video_completions = relationship("VideoCompletion", back_populates="user", cascade="all, delete-orphan")
    video_watch_sessions = relationship("VideoWatchSession", back_populates="user", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="usuario", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="usuario", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="usuario", cascade="all, delete-orphan")
    reports_made = relationship("InteractionReport", foreign_keys="InteractionReport.reporter_id", back_populates="reporter", cascade="all, delete-orphan")
    reports_moderated = relationship("InteractionReport", foreign_keys="InteractionReport.moderator_id", back_populates="moderator", cascade="all, delete-orphan")
    moderations = relationship("InteractionModeration", back_populates="moderator", cascade="all, delete-orphan")
    notification_subscriptions = relationship("NotificationSubscription", back_populates="user", cascade="all, delete-orphan")
    notification_preferences = relationship("NotificationPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notification_digests = relationship("NotificationDigest", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', site_id='{self.site_id}')>"
