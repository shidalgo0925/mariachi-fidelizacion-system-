from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func, or_
from app.models.interaction import Interaction, Like, Comment, Review
from app.models.user import User
from app.models.site_config import SiteConfig
from app.schemas.interaction import (
    InteractionCreate, InteractionUpdate, InteractionStats, InteractionAnalytics,
    LikeCreate, CommentCreate, CommentUpdate, ReviewCreate, ReviewUpdate,
    InteractionType, InteractionStatus, ReviewRating
)
from app.services.points_service import PointsService
from app.services.notification_service import NotificationService
from typing import Optional, List, Dict, Any
import structlog
from datetime import datetime, timedelta

logger = structlog.get_logger()

class InteractionService:
    """Servicio para manejar interacciones multi-tenant"""
    
    def __init__(self, db: Session):
        self.db = db
        self.points_service = PointsService(db)
        self.notification_service = NotificationService(db)
    
    async def create_interaction(
        self, 
        interaction_data: InteractionCreate, 
        user_id: int, 
        site_id: str
    ) -> Optional[Interaction]:
        """Crear nueva interacción"""
        try:
            # Verificar que el usuario existe
            user = self.db.query(User).filter(
                and_(
                    User.id == user_id,
                    User.site_id == site_id,
                    User.activo == True
                )
            ).first()
            
            if not user:
                logger.warning("User not found or inactive", user_id=user_id, site_id=site_id)
                return None
            
            # Crear interacción
            interaction = Interaction(
                site_id=site_id,
                usuario_id=user_id,
                tipo_interaccion=interaction_data.tipo_interaccion,
                contenido_id=interaction_data.contenido_id,
                contenido_tipo=interaction_data.contenido_tipo,
                contenido=interaction_data.contenido,
                metadata=str(interaction_data.metadata) if interaction_data.metadata else None,
                puntos_obtenidos=0,
                status=InteractionStatus.ACTIVE
            )
            
            self.db.add(interaction)
            self.db.commit()
            self.db.refresh(interaction)
            
            # Otorgar puntos según el tipo de interacción
            points_earned = await self._calculate_points_for_interaction(
                interaction_data.tipo_interaccion, 
                site_id
            )
            
            if points_earned > 0:
                interaction.puntos_obtenidos = points_earned
                await self.points_service.award_points_for_interaction(
                    user_id=user_id,
                    site_id=site_id,
                    interaction_type=interaction_data.tipo_interaccion,
                    content_id=interaction_data.contenido_id
                )
                
                # Enviar notificación
                await self.notification_service.send_points_earned_notification(
                    user_id=user_id,
                    site_id=site_id,
                    points=points_earned,
                    reason=f"interacción: {interaction_data.tipo_interaccion.value}"
                )
                
                self.db.commit()
            
            logger.info("Interaction created", 
                       interaction_id=interaction.id, 
                       user_id=user_id, 
                       site_id=site_id,
                       tipo=interaction_data.tipo_interaccion.value,
                       points_earned=points_earned)
            
            return interaction
            
        except Exception as e:
            self.db.rollback()
            logger.error("Error creating interaction", 
                        user_id=user_id, 
                        site_id=site_id, 
                        tipo=interaction_data.tipo_interaccion.value, 
                        error=str(e))
            return None
    
    async def create_like(
        self, 
        like_data: LikeCreate, 
        user_id: int, 
        site_id: str
    ) -> Optional[Like]:
        """Crear like"""
        try:
            # Verificar que no existe ya un like del usuario para este contenido
            existing_like = self.db.query(Like).filter(
                and_(
                    Like.usuario_id == user_id,
                    Like.site_id == site_id,
                    Like.contenido_id == like_data.contenido_id,
                    Like.contenido_tipo == like_data.contenido_tipo
                )
            ).first()
            
            if existing_like:
                logger.warning("Like already exists", 
                             user_id=user_id, 
                             contenido_id=like_data.contenido_id)
                return existing_like
            
            # Crear like
            like = Like(
                site_id=site_id,
                usuario_id=user_id,
                contenido_id=like_data.contenido_id,
                contenido_tipo=like_data.contenido_tipo
            )
            
            self.db.add(like)
            self.db.commit()
            self.db.refresh(like)
            
            # Crear interacción asociada
            interaction_data = InteractionCreate(
                tipo_interaccion=InteractionType.LIKE,
                contenido_id=like_data.contenido_id,
                contenido_tipo=like_data.contenido_tipo,
                metadata={"like_id": like.id}
            )
            
            await self.create_interaction(interaction_data, user_id, site_id)
            
            logger.info("Like created", 
                       like_id=like.id, 
                       user_id=user_id, 
                       site_id=site_id,
                       contenido_id=like_data.contenido_id)
            
            return like
            
        except Exception as e:
            self.db.rollback()
            logger.error("Error creating like", 
                        user_id=user_id, 
                        site_id=site_id, 
                        contenido_id=like_data.contenido_id, 
                        error=str(e))
            return None
    
    async def remove_like(
        self, 
        contenido_id: int, 
        contenido_tipo: str, 
        user_id: int, 
        site_id: str
    ) -> bool:
        """Remover like"""
        try:
            like = self.db.query(Like).filter(
                and_(
                    Like.usuario_id == user_id,
                    Like.site_id == site_id,
                    Like.contenido_id == contenido_id,
                    Like.contenido_tipo == contenido_tipo
                )
            ).first()
            
            if not like:
                return False
            
            self.db.delete(like)
            self.db.commit()
            
            logger.info("Like removed", 
                       user_id=user_id, 
                       site_id=site_id,
                       contenido_id=contenido_id)
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error("Error removing like", 
                        user_id=user_id, 
                        site_id=site_id, 
                        contenido_id=contenido_id, 
                        error=str(e))
            return False
    
    async def create_comment(
        self, 
        comment_data: CommentCreate, 
        user_id: int, 
        site_id: str
    ) -> Optional[Comment]:
        """Crear comentario"""
        try:
            # Obtener información del usuario
            user = self.db.query(User).filter(
                and_(
                    User.id == user_id,
                    User.site_id == site_id,
                    User.activo == True
                )
            ).first()
            
            if not user:
                return None
            
            # Crear comentario
            comment = Comment(
                site_id=site_id,
                usuario_id=user_id,
                contenido_id=comment_data.contenido_id,
                contenido_tipo=comment_data.contenido_tipo,
                comentario=comment_data.comentario,
                parent_id=comment_data.parent_id,
                puntos_obtenidos=0,
                status=InteractionStatus.ACTIVE
            )
            
            self.db.add(comment)
            self.db.commit()
            self.db.refresh(comment)
            
            # Crear interacción asociada
            interaction_data = InteractionCreate(
                tipo_interaccion=InteractionType.COMMENT,
                contenido_id=comment_data.contenido_id,
                contenido_tipo=comment_data.contenido_tipo,
                contenido=comment_data.comentario,
                metadata={"comment_id": comment.id, "parent_id": comment_data.parent_id}
            )
            
            interaction = await self.create_interaction(interaction_data, user_id, site_id)
            if interaction:
                comment.puntos_obtenidos = interaction.puntos_obtenidos
                self.db.commit()
            
            # Actualizar contador de respuestas si es una respuesta
            if comment_data.parent_id:
                parent_comment = self.db.query(Comment).filter(
                    Comment.id == comment_data.parent_id
                ).first()
                if parent_comment:
                    parent_comment.replies_count += 1
                    self.db.commit()
            
            logger.info("Comment created", 
                       comment_id=comment.id, 
                       user_id=user_id, 
                       site_id=site_id,
                       contenido_id=comment_data.contenido_id)
            
            return comment
            
        except Exception as e:
            self.db.rollback()
            logger.error("Error creating comment", 
                        user_id=user_id, 
                        site_id=site_id, 
                        contenido_id=comment_data.contenido_id, 
                        error=str(e))
            return None
    
    async def create_review(
        self, 
        review_data: ReviewCreate, 
        user_id: int, 
        site_id: str
    ) -> Optional[Review]:
        """Crear reseña"""
        try:
            # Verificar que no existe ya una reseña del usuario para este contenido
            existing_review = self.db.query(Review).filter(
                and_(
                    Review.usuario_id == user_id,
                    Review.site_id == site_id,
                    Review.contenido_id == review_data.contenido_id,
                    Review.contenido_tipo == review_data.contenido_tipo
                )
            ).first()
            
            if existing_review:
                logger.warning("Review already exists", 
                             user_id=user_id, 
                             contenido_id=review_data.contenido_id)
                return existing_review
            
            # Obtener información del usuario
            user = self.db.query(User).filter(
                and_(
                    User.id == user_id,
                    User.site_id == site_id,
                    User.activo == True
                )
            ).first()
            
            if not user:
                return None
            
            # Crear reseña
            review = Review(
                site_id=site_id,
                usuario_id=user_id,
                contenido_id=review_data.contenido_id,
                contenido_tipo=review_data.contenido_tipo,
                calificacion=review_data.calificacion,
                titulo=review_data.titulo,
                comentario=review_data.comentario,
                puntos_obtenidos=0,
                status=InteractionStatus.ACTIVE
            )
            
            self.db.add(review)
            self.db.commit()
            self.db.refresh(review)
            
            # Crear interacción asociada
            interaction_data = InteractionCreate(
                tipo_interaccion=InteractionType.REVIEW,
                contenido_id=review_data.contenido_id,
                contenido_tipo=review_data.contenido_tipo,
                contenido=review_data.comentario,
                metadata={
                    "review_id": review.id, 
                    "calificacion": review_data.calificacion.value,
                    "titulo": review_data.titulo
                }
            )
            
            interaction = await self.create_interaction(interaction_data, user_id, site_id)
            if interaction:
                review.puntos_obtenidos = interaction.puntos_obtenidos
                self.db.commit()
            
            # Actualizar contador de reseñas del usuario
            user.reseñas_dejadas += 1
            self.db.commit()
            
            logger.info("Review created", 
                       review_id=review.id, 
                       user_id=user_id, 
                       site_id=site_id,
                       contenido_id=review_data.contenido_id,
                       calificacion=review_data.calificacion.value)
            
            return review
            
        except Exception as e:
            self.db.rollback()
            logger.error("Error creating review", 
                        user_id=user_id, 
                        site_id=site_id, 
                        contenido_id=review_data.contenido_id, 
                        error=str(e))
            return None
    
    async def get_content_interactions(
        self, 
        contenido_id: int, 
        contenido_tipo: str, 
        site_id: str,
        page: int = 1,
        size: int = 20
    ) -> Dict[str, Any]:
        """Obtener interacciones de un contenido específico"""
        try:
            # Obtener likes
            likes_query = self.db.query(Like).filter(
                and_(
                    Like.contenido_id == contenido_id,
                    Like.contenido_tipo == contenido_tipo,
                    Like.site_id == site_id
                )
            )
            
            total_likes = likes_query.count()
            likes = likes_query.offset((page - 1) * size).limit(size).all()
            
            # Obtener comentarios
            comments_query = self.db.query(Comment).filter(
                and_(
                    Comment.contenido_id == contenido_id,
                    Comment.contenido_tipo == contenido_tipo,
                    Comment.site_id == site_id,
                    Comment.status == InteractionStatus.ACTIVE
                )
            ).order_by(Comment.fecha_comentario.desc())
            
            total_comments = comments_query.count()
            comments = comments_query.offset((page - 1) * size).limit(size).all()
            
            # Obtener reseñas
            reviews_query = self.db.query(Review).filter(
                and_(
                    Review.contenido_id == contenido_id,
                    Review.contenido_tipo == contenido_tipo,
                    Review.site_id == site_id,
                    Review.status == InteractionStatus.ACTIVE
                )
            ).order_by(Review.fecha_reseña.desc())
            
            total_reviews = reviews_query.count()
            reviews = reviews_query.offset((page - 1) * size).limit(size).all()
            
            # Calcular calificación promedio
            avg_rating = reviews_query.with_entities(
                func.avg(Review.calificacion)
            ).scalar() or 0
            
            result = {
                "likes": {
                    "items": likes,
                    "total": total_likes
                },
                "comments": {
                    "items": comments,
                    "total": total_comments
                },
                "reviews": {
                    "items": reviews,
                    "total": total_reviews,
                    "average_rating": round(avg_rating, 2)
                }
            }
            
            logger.info("Content interactions retrieved", 
                       contenido_id=contenido_id, 
                       contenido_tipo=contenido_tipo, 
                       site_id=site_id)
            
            return result
            
        except Exception as e:
            logger.error("Error getting content interactions", 
                        contenido_id=contenido_id, 
                        contenido_tipo=contenido_tipo, 
                        site_id=site_id, 
                        error=str(e))
            return {"likes": {"items": [], "total": 0}, "comments": {"items": [], "total": 0}, "reviews": {"items": [], "total": 0, "average_rating": 0}}
    
    async def get_user_interactions(
        self, 
        user_id: int, 
        site_id: str,
        page: int = 1,
        size: int = 20
    ) -> Dict[str, Any]:
        """Obtener interacciones de un usuario"""
        try:
            # Obtener todas las interacciones del usuario
            interactions_query = self.db.query(Interaction).filter(
                and_(
                    Interaction.usuario_id == user_id,
                    Interaction.site_id == site_id,
                    Interaction.status == InteractionStatus.ACTIVE
                )
            ).order_by(Interaction.fecha_interaccion.desc())
            
            total = interactions_query.count()
            interactions = interactions_query.offset((page - 1) * size).limit(size).all()
            
            # Obtener estadísticas
            stats = {
                "total_interactions": total,
                "total_likes": interactions_query.filter(Interaction.tipo_interaccion == InteractionType.LIKE).count(),
                "total_comments": interactions_query.filter(Interaction.tipo_interaccion == InteractionType.COMMENT).count(),
                "total_reviews": interactions_query.filter(Interaction.tipo_interaccion == InteractionType.REVIEW).count(),
                "total_points": sum(i.puntos_obtenidos for i in interactions)
            }
            
            result = {
                "interactions": interactions,
                "total": total,
                "page": page,
                "size": size,
                "total_pages": (total + size - 1) // size,
                "stats": stats
            }
            
            logger.info("User interactions retrieved", 
                       user_id=user_id, 
                       site_id=site_id, 
                       total=total)
            
            return result
            
        except Exception as e:
            logger.error("Error getting user interactions", 
                        user_id=user_id, 
                        site_id=site_id, 
                        error=str(e))
            return {"interactions": [], "total": 0, "page": page, "size": size, "total_pages": 0, "stats": {}}
    
    async def get_interaction_stats(self, site_id: str, user_id: Optional[int] = None) -> InteractionStats:
        """Obtener estadísticas de interacciones"""
        try:
            if user_id:
                # Estadísticas del usuario específico
                interactions_query = self.db.query(Interaction).filter(
                    and_(
                        Interaction.usuario_id == user_id,
                        Interaction.site_id == site_id,
                        Interaction.status == InteractionStatus.ACTIVE
                    )
                )
            else:
                # Estadísticas globales del sitio
                interactions_query = self.db.query(Interaction).filter(
                    and_(
                        Interaction.site_id == site_id,
                        Interaction.status == InteractionStatus.ACTIVE
                    )
                )
            
            total_interactions = interactions_query.count()
            total_likes = interactions_query.filter(Interaction.tipo_interaccion == InteractionType.LIKE).count()
            total_comments = interactions_query.filter(Interaction.tipo_interaccion == InteractionType.COMMENT).count()
            total_reviews = interactions_query.filter(Interaction.tipo_interaccion == InteractionType.REVIEW).count()
            
            # Calcular calificación promedio
            avg_rating = self.db.query(Review).filter(
                and_(
                    Review.site_id == site_id,
                    Review.status == InteractionStatus.ACTIVE
                )
            ).with_entities(func.avg(Review.calificacion)).scalar() or 0
            
            # Calcular tasa de engagement (simplificada)
            total_users = self.db.query(User).filter(
                and_(
                    User.site_id == site_id,
                    User.activo == True
                )
            ).count()
            
            engagement_rate = (total_interactions / total_users * 100) if total_users > 0 else 0
            
            # Contenido más gustado
            most_liked = interactions_query.filter(
                Interaction.tipo_interaccion == InteractionType.LIKE
            ).group_by(Interaction.contenido_id).order_by(
                func.count(Interaction.id).desc()
            ).first()
            
            most_liked_content = None
            if most_liked:
                most_liked_content = {
                    "contenido_id": most_liked.contenido_id,
                    "contenido_tipo": most_liked.contenido_tipo,
                    "likes_count": interactions_query.filter(
                        and_(
                            Interaction.contenido_id == most_liked.contenido_id,
                            Interaction.tipo_interaccion == InteractionType.LIKE
                        )
                    ).count()
                }
            
            # Contenido más comentado
            most_commented = interactions_query.filter(
                Interaction.tipo_interaccion == InteractionType.COMMENT
            ).group_by(Interaction.contenido_id).order_by(
                func.count(Interaction.id).desc()
            ).first()
            
            most_commented_content = None
            if most_commented:
                most_commented_content = {
                    "contenido_id": most_commented.contenido_id,
                    "contenido_tipo": most_commented.contenido_tipo,
                    "comments_count": interactions_query.filter(
                        and_(
                            Interaction.contenido_id == most_commented.contenido_id,
                            Interaction.tipo_interaccion == InteractionType.COMMENT
                        )
                    ).count()
                }
            
            stats = InteractionStats(
                total_interactions=total_interactions,
                total_likes=total_likes,
                total_comments=total_comments,
                total_reviews=total_reviews,
                average_rating=round(avg_rating, 2),
                engagement_rate=round(engagement_rate, 2),
                most_liked_content=most_liked_content,
                most_commented_content=most_commented_content
            )
            
            logger.info("Interaction stats retrieved", 
                       site_id=site_id, 
                       user_id=user_id)
            
            return stats
            
        except Exception as e:
            logger.error("Error getting interaction stats", 
                        site_id=site_id, 
                        user_id=user_id, 
                        error=str(e))
            return InteractionStats()
    
    async def _calculate_points_for_interaction(
        self, 
        interaction_type: InteractionType, 
        site_id: str
    ) -> int:
        """Calcular puntos para un tipo de interacción"""
        try:
            # Obtener configuración del sitio
            site_config = self.db.query(SiteConfig).filter(
                SiteConfig.site_id == site_id
            ).first()
            
            if not site_config:
                return 0
            
            # Mapear tipos de interacción a puntos
            points_map = {
                InteractionType.LIKE: site_config.points_per_like,
                InteractionType.COMMENT: site_config.points_per_comment,
                InteractionType.REVIEW: site_config.points_per_review,
                InteractionType.SHARE: 3,
                InteractionType.VIEW: 1,
                InteractionType.CLICK: 1,
                InteractionType.DOWNLOAD: 5,
                InteractionType.SUBSCRIBE: 10
            }
            
            return points_map.get(interaction_type, 0)
            
        except Exception as e:
            logger.error("Error calculating points for interaction", 
                        interaction_type=interaction_type.value, 
                        site_id=site_id, 
                        error=str(e))
            return 0
