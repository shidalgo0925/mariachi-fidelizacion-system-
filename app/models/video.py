from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Video(Base):
    """Modelo para videos del sistema"""
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String(50), nullable=False, index=True)
    
    # Información del video
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    youtube_id = Column(String(50), nullable=False, unique=True, index=True)
    tipo_video = Column(Enum('tutorial', 'promotional', 'entertainment', 'educational', 'testimonial', name='video_type'), 
                       default='entertainment', nullable=False)
    
    # Metadatos del video
    duracion_segundos = Column(Integer, nullable=True)
    orden = Column(Integer, nullable=False, default=1)
    puntos_por_completar = Column(Integer, default=10, nullable=False)
    
    # URLs y enlaces
    thumbnail_url = Column(String(500), nullable=True)
    embed_url = Column(String(500), nullable=True)
    
    # Estadísticas de YouTube
    view_count = Column(Integer, nullable=True)
    like_count = Column(Integer, nullable=True)
    comment_count = Column(Integer, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    # Estado del video
    activo = Column(Boolean, default=True, nullable=False)
    status = Column(Enum('active', 'inactive', 'draft', 'archived', name='video_status'), 
                   default='active', nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    completions = relationship("VideoCompletion", back_populates="video", cascade="all, delete-orphan")
    watch_sessions = relationship("VideoWatchSession", back_populates="video", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Video(id={self.id}, titulo='{self.titulo}', youtube_id='{self.youtube_id}', site_id='{self.site_id}')>"

class VideoCompletion(Base):
    """Modelo para completaciones de video"""
    __tablename__ = "video_completions"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String(50), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    
    # Datos de completación
    completion_percentage = Column(Integer, nullable=False, default=0)
    time_watched = Column(Integer, nullable=False, default=0)  # en segundos
    completion_status = Column(Enum('not_started', 'in_progress', 'completed', 'skipped', name='completion_status'), 
                              default='not_started', nullable=False)
    
    # Puntos y recompensas
    points_earned = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    user = relationship("User", back_populates="video_completions")
    video = relationship("Video", back_populates="completions")
    
    def __repr__(self):
        return f"<VideoCompletion(id={self.id}, user_id={self.user_id}, video_id={self.video_id}, completion_percentage={self.completion_percentage})>"

class VideoWatchSession(Base):
    """Modelo para sesiones de visualización de video"""
    __tablename__ = "video_watch_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String(50), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    
    # Datos de la sesión
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_watched = Column(Integer, default=0, nullable=False)  # en segundos
    completion_percentage = Column(Integer, default=0, nullable=False)
    
    # Interacciones del usuario
    paused_count = Column(Integer, default=0, nullable=False)
    seek_count = Column(Integer, default=0, nullable=False)
    
    # Metadatos técnicos
    quality = Column(String(20), nullable=True)  # 360p, 720p, 1080p, etc.
    device_type = Column(String(50), nullable=True)  # desktop, mobile, tablet
    
    # Puntos ganados en esta sesión
    points_earned = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    user = relationship("User", back_populates="video_watch_sessions")
    video = relationship("Video", back_populates="watch_sessions")
    
    def __repr__(self):
        return f"<VideoWatchSession(id={self.id}, user_id={self.user_id}, video_id={self.video_id}, duration_watched={self.duration_watched})>"