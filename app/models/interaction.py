from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class InteractionType(str, enum.Enum):
    LIKE = "like"
    COMMENT = "comment"
    REVIEW = "review"
    SHARE = "share"
    VIEW = "view"
    CLICK = "click"
    DOWNLOAD = "download"
    SUBSCRIBE = "subscribe"

class Interaction(Base):
    """Modelo para interacciones del sistema"""
    __tablename__ = "interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String(50), nullable=False, index=True)
    usuario_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Tipo y contenido de la interacción
    tipo_interaccion = Column(Enum('like', 'comment', 'review', 'share', 'view', 'click', 'download', 'subscribe', name='interaction_type'), 
                             nullable=False)
    contenido_id = Column(Integer, nullable=True)  # ID del contenido relacionado
    contenido_tipo = Column(String(50), nullable=True)  # Tipo de contenido (video, sticker, etc.)
    contenido = Column(Text, nullable=True)  # Contenido de la interacción (comentario, reseña)
    
    # Metadatos y estado
    extra_data = Column(Text, nullable=True)  # JSON string para datos adicionales
    puntos_obtenidos = Column(Integer, default=0, nullable=False)
    status = Column(Enum('active', 'hidden', 'deleted', 'moderated', name='interaction_status'), 
                   default='active', nullable=False)
    
    # Timestamps
    fecha_interaccion = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    usuario = relationship("User", back_populates="interactions")
    
    def __repr__(self):
        return f"<Interaction(id={self.id}, tipo='{self.tipo_interaccion}', user_id={self.usuario_id}, site_id='{self.site_id}')>"

class Like(Base):
    """Modelo para likes"""
    __tablename__ = "likes"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String(50), nullable=False, index=True)
    usuario_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Contenido que se le dio like
    contenido_id = Column(Integer, nullable=False)
    contenido_tipo = Column(String(50), nullable=False)  # video, sticker, comment, review, etc.
    
    # Timestamps
    fecha_like = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    usuario = relationship("User", back_populates="likes")
    
    def __repr__(self):
        return f"<Like(id={self.id}, user_id={self.usuario_id}, contenido_id={self.contenido_id}, tipo='{self.contenido_tipo}')>"

class Comment(Base):
    """Modelo para comentarios"""
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String(50), nullable=False, index=True)
    usuario_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Contenido del comentario
    contenido_id = Column(Integer, nullable=False)
    contenido_tipo = Column(String(50), nullable=False)
    comentario = Column(Text, nullable=False)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)  # Para respuestas
    
    # Metadatos y estado
    puntos_obtenidos = Column(Integer, default=0, nullable=False)
    status = Column(Enum('active', 'hidden', 'deleted', 'moderated', name='comment_status'), 
                   default='active', nullable=False)
    likes_count = Column(Integer, default=0, nullable=False)
    replies_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    fecha_comentario = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    usuario = relationship("User", back_populates="comments")
    parent = relationship("Comment", remote_side=[id], back_populates="replies")
    replies = relationship("Comment", back_populates="parent", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Comment(id={self.id}, user_id={self.usuario_id}, contenido_id={self.contenido_id}, parent_id={self.parent_id})>"

class Review(Base):
    """Modelo para reseñas"""
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String(50), nullable=False, index=True)
    usuario_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Contenido de la reseña
    contenido_id = Column(Integer, nullable=False)
    contenido_tipo = Column(String(50), nullable=False)
    calificacion = Column(Integer, nullable=False)  # 1-5 estrellas
    titulo = Column(String(200), nullable=True)
    comentario = Column(Text, nullable=True)
    
    # Metadatos y estado
    puntos_obtenidos = Column(Integer, default=0, nullable=False)
    status = Column(Enum('active', 'hidden', 'deleted', 'moderated', name='review_status'), 
                   default='active', nullable=False)
    likes_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    fecha_reseña = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    usuario = relationship("User", back_populates="reviews")
    
    def __repr__(self):
        return f"<Review(id={self.id}, user_id={self.usuario_id}, contenido_id={self.contenido_id}, calificacion={self.calificacion})>"

class InteractionReport(Base):
    """Modelo para reportes de interacciones"""
    __tablename__ = "interaction_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String(50), nullable=False, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Interacción reportada
    interaction_id = Column(Integer, nullable=False)
    interaction_type = Column(String(50), nullable=False)  # like, comment, review
    
    # Detalles del reporte
    reason = Column(String(100), nullable=False)  # spam, inappropriate, harassment, etc.
    description = Column(Text, nullable=True)
    status = Column(Enum('pending', 'reviewed', 'resolved', 'dismissed', name='report_status'), 
                   default='pending', nullable=False)
    
    # Moderación
    moderator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    moderator_notes = Column(Text, nullable=True)
    action_taken = Column(String(100), nullable=True)  # hidden, deleted, no_action, etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    reporter = relationship("User", foreign_keys=[reporter_id], back_populates="reports_made")
    moderator = relationship("User", foreign_keys=[moderator_id], back_populates="reports_moderated")
    
    def __repr__(self):
        return f"<InteractionReport(id={self.id}, reporter_id={self.reporter_id}, interaction_id={self.interaction_id}, status='{self.status}')>"

class InteractionModeration(Base):
    """Modelo para moderación de interacciones"""
    __tablename__ = "interaction_moderations"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String(50), nullable=False, index=True)
    moderator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Interacción moderada
    interaction_id = Column(Integer, nullable=False)
    interaction_type = Column(String(50), nullable=False)
    
    # Acción de moderación
    action = Column(Enum('approve', 'hide', 'delete', 'warn', name='moderation_action'), 
                   nullable=False)
    reason = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    moderator = relationship("User", back_populates="moderations")
    
    def __repr__(self):
        return f"<InteractionModeration(id={self.id}, moderator_id={self.moderator_id}, interaction_id={self.interaction_id}, action='{self.action}')>"