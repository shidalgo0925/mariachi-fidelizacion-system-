from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class InstagramUser(Base):
    """Modelo para usuarios de Instagram conectados"""
    __tablename__ = "instagram_users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    site_id = Column(String(50), nullable=False, index=True)
    
    # Datos de Instagram
    instagram_user_id = Column(String(100), nullable=False, unique=True, index=True)
    username = Column(String(100), nullable=False)
    full_name = Column(String(200), nullable=True)
    profile_picture_url = Column(String(500), nullable=True)
    follower_count = Column(Integer, nullable=True)
    following_count = Column(Integer, nullable=True)
    media_count = Column(Integer, nullable=True)
    
    # Estado de conexión
    connection_status = Column(Enum('not_connected', 'connected', 'expired', 'revoked', 'error', name='connection_status'), 
                              default='not_connected', nullable=False)
    verification_status = Column(Enum('pending', 'verified', 'failed', 'expired', name='verification_status'), 
                                default='pending', nullable=False)
    
    # Tokens y autenticación
    access_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Verificación
    last_verification = Column(DateTime(timezone=True), nullable=True)
    verification_attempts = Column(Integer, default=0)
    sticker_generated = Column(Boolean, default=False)
    
    # Metadatos
    extra_data = Column(Text, nullable=True)  # JSON string para datos adicionales
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    user = relationship("User", back_populates="instagram_connection")
    
    def __repr__(self):
        return f"<InstagramUser(username='{self.username}', user_id='{self.user_id}', site_id='{self.site_id}')>"
