from sqlalchemy.orm import Session
from app.models.user import User
from app.models.site_config import SiteConfig
from app.models.interaction import Interaction, InteractionType
from app.models.sticker import Sticker, StickerType
from app.models.video import VideoCompletion
from typing import Dict, Any, List, Optional
import structlog

logger = structlog.get_logger()

class PointsService:
    """Servicio para manejar sistema de puntos parametrizado"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def award_points_for_action(
        self, 
        user_id: int, 
        site_id: str, 
        action_type: str, 
        points: int, 
        reason: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Otorgar puntos por una acción específica"""
        try:
            # Obtener usuario
            user = self.db.query(User).filter(
                User.id == user_id,
                User.site_id == site_id,
                User.activo == True
            ).first()
            
            if not user:
                logger.warning("User not found for points award", user_id=user_id, site_id=site_id)
                return False
            
            # Obtener configuración del sitio
            site_config = self.db.query(SiteConfig).filter(
                SiteConfig.site_id == site_id
            ).first()
            
            if not site_config:
                logger.warning("Site config not found for points award", site_id=site_id)
                return False
            
            # Validar que los puntos no excedan los límites del sitio
            max_points = self._get_max_points_for_action(action_type, site_config)
            if points > max_points:
                points = max_points
                logger.warning("Points capped to site maximum", 
                             user_id=user_id, 
                             requested_points=points, 
                             max_points=max_points)
            
            # Agregar puntos al usuario
            user.puntos_acumulados += points
            
            # Crear registro de interacción
            interaction = Interaction(
                site_id=site_id,
                usuario_id=user_id,
                tipo_interaccion=InteractionType.ENGAGEMENT,
                contenido=f"Puntos otorgados: {reason}",
                puntos_obtenidos=points,
                metadata=str(metadata) if metadata else None
            )
            
            self.db.add(interaction)
            self.db.commit()
            
            logger.info("Points awarded", 
                       user_id=user_id, 
                       site_id=site_id, 
                       action_type=action_type, 
                       points=points, 
                       reason=reason)
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error("Error awarding points", 
                        user_id=user_id, 
                        site_id=site_id, 
                        action_type=action_type, 
                        error=str(e))
            return False
    
    async def award_points_for_sticker_generation(
        self, 
        user_id: int, 
        site_id: str, 
        sticker_type: StickerType
    ) -> bool:
        """Otorgar puntos por generación de sticker"""
        try:
            site_config = self.db.query(SiteConfig).filter(
                SiteConfig.site_id == site_id
            ).first()
            
            if not site_config:
                return False
            
            # Determinar puntos según tipo de sticker
            points = self._get_points_for_sticker_type(sticker_type, site_config)
            
            # Otorgar puntos
            success = await self.award_points_for_action(
                user_id=user_id,
                site_id=site_id,
                action_type="sticker_generation",
                points=points,
                reason=f"Sticker {sticker_type.value} generado",
                metadata={"sticker_type": sticker_type.value}
            )
            
            if success:
                # Actualizar contador de stickers del usuario
                user = self.db.query(User).filter(
                    User.id == user_id,
                    User.site_id == site_id
                ).first()
                
                if user:
                    user.stickers_generados += 1
                    self.db.commit()
            
            return success
            
        except Exception as e:
            logger.error("Error awarding points for sticker", 
                        user_id=user_id, 
                        site_id=site_id, 
                        sticker_type=sticker_type.value, 
                        error=str(e))
            return False
    
    async def award_points_for_video_completion(
        self, 
        user_id: int, 
        site_id: str, 
        video_id: int,
        completion_percentage: int = 100
    ) -> bool:
        """Otorgar puntos por completar video"""
        try:
            site_config = self.db.query(SiteConfig).filter(
                SiteConfig.site_id == site_id
            ).first()
            
            if not site_config:
                return False
            
            # Solo otorgar puntos si el video se completó al 100%
            if completion_percentage < 100:
                logger.info("Video not fully completed, no points awarded", 
                           user_id=user_id, 
                           video_id=video_id, 
                           completion_percentage=completion_percentage)
                return False
            
            # Obtener puntos del video
            points = site_config.points_per_video
            
            # Otorgar puntos
            success = await self.award_points_for_action(
                user_id=user_id,
                site_id=site_id,
                action_type="video_completion",
                points=points,
                reason=f"Video {video_id} completado",
                metadata={"video_id": video_id, "completion_percentage": completion_percentage}
            )
            
            if success:
                # Actualizar contador de videos del usuario
                user = self.db.query(User).filter(
                    User.id == user_id,
                    User.site_id == site_id
                ).first()
                
                if user:
                    user.videos_completados += 1
                    self.db.commit()
            
            return success
            
        except Exception as e:
            logger.error("Error awarding points for video completion", 
                        user_id=user_id, 
                        site_id=site_id, 
                        video_id=video_id, 
                        error=str(e))
            return False
    
    async def award_points_for_interaction(
        self, 
        user_id: int, 
        site_id: str, 
        interaction_type: InteractionType,
        content_id: Optional[int] = None
    ) -> bool:
        """Otorgar puntos por interacción (like, comentario, reseña)"""
        try:
            site_config = self.db.query(SiteConfig).filter(
                SiteConfig.site_id == site_id
            ).first()
            
            if not site_config:
                return False
            
            # Determinar puntos según tipo de interacción
            points = self._get_points_for_interaction_type(interaction_type, site_config)
            
            # Otorgar puntos
            success = await self.award_points_for_action(
                user_id=user_id,
                site_id=site_id,
                action_type="interaction",
                points=points,
                reason=f"Interacción {interaction_type.value}",
                metadata={"interaction_type": interaction_type.value, "content_id": content_id}
            )
            
            if success and interaction_type == InteractionType.RESENA:
                # Actualizar contador de reseñas del usuario
                user = self.db.query(User).filter(
                    User.id == user_id,
                    User.site_id == site_id
                ).first()
                
                if user:
                    user.reseñas_dejadas += 1
                    self.db.commit()
            
            return success
            
        except Exception as e:
            logger.error("Error awarding points for interaction", 
                        user_id=user_id, 
                        site_id=site_id, 
                        interaction_type=interaction_type.value, 
                        error=str(e))
            return False
    
    async def award_points_for_instagram_verification(
        self, 
        user_id: int, 
        site_id: str
    ) -> bool:
        """Otorgar puntos por verificación de Instagram"""
        try:
            site_config = self.db.query(SiteConfig).filter(
                SiteConfig.site_id == site_id
            ).first()
            
            if not site_config:
                return False
            
            # Puntos especiales por verificación de Instagram
            points = 25  # Puntos fijos por verificación
            
            # Otorgar puntos
            success = await self.award_points_for_action(
                user_id=user_id,
                site_id=site_id,
                action_type="instagram_verification",
                points=points,
                reason="Instagram verificado",
                metadata={"verification_type": "instagram"}
            )
            
            if success:
                # Marcar Instagram como seguido
                user = self.db.query(User).filter(
                    User.id == user_id,
                    User.site_id == site_id
                ).first()
                
                if user:
                    user.instagram_seguido = True
                    self.db.commit()
            
            return success
            
        except Exception as e:
            logger.error("Error awarding points for Instagram verification", 
                        user_id=user_id, 
                        site_id=site_id, 
                        error=str(e))
            return False
    
    async def get_user_points_history(
        self, 
        user_id: int, 
        site_id: str, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Obtener historial de puntos del usuario"""
        try:
            interactions = self.db.query(Interaction).filter(
                Interaction.usuario_id == user_id,
                Interaction.site_id == site_id,
                Interaction.puntos_obtenidos > 0
            ).order_by(Interaction.fecha_interaccion.desc()).limit(limit).all()
            
            history = []
            for interaction in interactions:
                history.append({
                    "fecha": interaction.fecha_interaccion,
                    "tipo": interaction.tipo_interaccion.value,
                    "puntos": interaction.puntos_obtenidos,
                    "descripcion": interaction.contenido,
                    "metadata": interaction.metadata
                })
            
            logger.info("User points history retrieved", user_id=user_id, site_id=site_id, count=len(history))
            return history
            
        except Exception as e:
            logger.error("Error getting user points history", 
                        user_id=user_id, 
                        site_id=site_id, 
                        error=str(e))
            return []
    
    def _get_points_for_sticker_type(self, sticker_type: StickerType, site_config: SiteConfig) -> int:
        """Obtener puntos para tipo de sticker"""
        # Todos los stickers dan los mismos puntos por defecto
        return 5
    
    def _get_points_for_interaction_type(self, interaction_type: InteractionType, site_config: SiteConfig) -> int:
        """Obtener puntos para tipo de interacción"""
        points_map = {
            InteractionType.LIKE: site_config.points_per_like,
            InteractionType.COMENTARIO: site_config.points_per_comment,
            InteractionType.RESENA: site_config.points_per_review,
        }
        
        return points_map.get(interaction_type, 0)
    
    def _get_max_points_for_action(self, action_type: str, site_config: SiteConfig) -> int:
        """Obtener máximo de puntos permitidos para una acción"""
        max_points_map = {
            "sticker_generation": 10,
            "video_completion": site_config.points_per_video,
            "interaction": max(site_config.points_per_like, site_config.points_per_comment, site_config.points_per_review),
            "instagram_verification": 50,
        }
        
        return max_points_map.get(action_type, 10)
    
    async def calculate_user_level(self, points: int) -> Dict[str, Any]:
        """Calcular nivel del usuario basado en puntos"""
        levels = [
            {"name": "Principiante", "min_points": 0, "max_points": 49, "color": "#6c757d"},
            {"name": "Bronce", "min_points": 50, "max_points": 199, "color": "#cd7f32"},
            {"name": "Plata", "min_points": 200, "max_points": 499, "color": "#c0c0c0"},
            {"name": "Oro", "min_points": 500, "max_points": 999, "color": "#ffd700"},
            {"name": "Diamante", "min_points": 1000, "max_points": float('inf'), "color": "#b9f2ff"},
        ]
        
        for level in levels:
            if level["min_points"] <= points <= level["max_points"]:
                # Calcular progreso hacia el siguiente nivel
                next_level = None
                progress = 0
                
                current_index = levels.index(level)
                if current_index < len(levels) - 1:
                    next_level = levels[current_index + 1]
                    progress = min(100, (points - level["min_points"]) / (next_level["min_points"] - level["min_points"]) * 100)
                
                return {
                    "current_level": level,
                    "next_level": next_level,
                    "progress_percentage": progress,
                    "points_to_next": next_level["min_points"] - points if next_level else 0
                }
        
        # Fallback
        return {
            "current_level": levels[0],
            "next_level": levels[1],
            "progress_percentage": 0,
            "points_to_next": 50
        }
