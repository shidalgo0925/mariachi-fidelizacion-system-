from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Notification(Base):
    """Modelo para notificaciones del sistema"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    site_id = Column(String(50), nullable=False, index=True)
    
    # Contenido de la notificación
    type = Column(Enum('sticker_generated', 'instagram_connected', 'instagram_verified', 
                      'points_earned', 'level_up', 'sticker_expiring', 'welcome', 'system', 
                      name='notification_type'), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(Enum('low', 'medium', 'high', 'urgent', name='notification_priority'), 
                     default='medium', nullable=False)
    
    # Estado de la notificación
    read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadatos y expiración
    extra_data = Column(Text, nullable=True)  # JSON string para datos adicionales
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    user = relationship("User", back_populates="notifications")
    
    def __repr__(self):
        return f"<Notification(id={self.id}, type='{self.type}', user_id={self.user_id}, read={self.read})>"
