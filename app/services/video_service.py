from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from app.models.video import Video, VideoCompletion, VideoWatchSession
from app.models.user import User
from app.models.site_config import SiteConfig
from app.schemas.video import (
    VideoCreate, VideoUpdate, VideoStats, VideoProgress, VideoPlaylist,
    VideoCompletionCreate, VideoCompletionResponse, VideoWatchSession as VideoWatchSessionSchema,
    VideoSearch, VideoList, VideoType, VideoStatus, VideoCompletionStatus
)
from app.services.youtube_service import YouTubeService
from app.services.points_service import PointsService
from app.services.notification_service import NotificationService
from typing import Optional, List, Dict, Any
import structlog
from datetime import datetime, timedelta

logger = structlog.get_logger()

class VideoService:
    """Servicio para manejar videos multi-tenant"""
    
    def __init__(self, db: Session):
        self.db = db
        self.youtube_service = YouTubeService(db)
        self.points_service = PointsService(db)
        self.notification_service = NotificationService(db)
    
    async def create_video(
        self, 
        video_data: VideoCreate, 
        site_id: str
    ) -> Optional[Video]:
        """Crear nuevo video"""
        try:
            # Verificar que el sitio existe
            site_config = self.db.query(SiteConfig).filter(
                SiteConfig.site_id == site_id,
                SiteConfig.activo == True
            ).first()
            
            if not site_config:
                logger.warning("Site not found or inactive", site_id=site_id)
                return None
            
            # Validar ID de YouTube
            if not await self.youtube_service.validate_youtube_video_id(video_data.youtube_id):
                logger.warning("Invalid YouTube video ID", youtube_id=video_data.youtube_id)
                return None
            
            # Obtener información del video desde YouTube
            video_info = await self.youtube_service.get_video_info(
                video_data.youtube_id, 
                site_config.youtube_api_key
            )
            
            if not video_info:
                logger.warning("Could not fetch video info from YouTube", youtube_id=video_data.youtube_id)
                return None
            
            # Crear video
            video = Video(
                site_id=site_id,
                titulo=video_data.titulo or video_info["title"],
                descripcion=video_data.descripcion or video_info["description"],
                youtube_id=video_data.youtube_id,
                tipo_video=video_data.tipo_video,
                duracion_segundos=video_data.duracion_segundos or video_info["duration_seconds"],
                orden=video_data.orden,
                puntos_por_completar=video_data.puntos_por_completar,
                activo=video_data.activo,
                thumbnail_url=video_info["thumbnail_url"],
                embed_url=video_info["embed_url"],
                view_count=video_info["view_count"],
                like_count=video_info["like_count"],
                comment_count=video_info["comment_count"],
                published_at=datetime.fromisoformat(
                    video_info["published_at"].replace('Z', '+00:00')
                ) if video_info["published_at"] else None,
                status=VideoStatus.ACTIVE if video_data.activo else VideoStatus.DRAFT
            )
            
            self.db.add(video)
            self.db.commit()
            self.db.refresh(video)
            
            logger.info("Video created", 
                       video_id=video.id, 
                       site_id=site_id, 
                       youtube_id=video_data.youtube_id)
            
            return video
            
        except Exception as e:
            self.db.rollback()
            logger.error("Error creating video", 
                        site_id=site_id, 
                        youtube_id=video_data.youtube_id, 
                        error=str(e))
            return None
    
    async def get_video_by_id(self, video_id: int, site_id: str) -> Optional[Video]:
        """Obtener video por ID"""
        try:
            video = self.db.query(Video).filter(
                and_(
                    Video.id == video_id,
                    Video.site_id == site_id,
                    Video.activo == True
                )
            ).first()
            
            if video:
                logger.debug("Video retrieved", video_id=video_id, site_id=site_id)
            else:
                logger.warning("Video not found", video_id=video_id, site_id=site_id)
            
            return video
            
        except Exception as e:
            logger.error("Error getting video by ID", 
                        video_id=video_id, 
                        site_id=site_id, 
                        error=str(e))
            return None
    
    async def get_videos_by_site(
        self, 
        site_id: str, 
        page: int = 1, 
        size: int = 10,
        search: Optional[VideoSearch] = None
    ) -> Dict[str, Any]:
        """Obtener videos del sitio con filtros"""
        try:
            query = self.db.query(Video).filter(
                Video.site_id == site_id
            )
            
            # Aplicar filtros si se proporcionan
            if search:
                if search.query:
                    query = query.filter(
                        Video.titulo.ilike(f"%{search.query}%") |
                        Video.descripcion.ilike(f"%{search.query}%")
                    )
                
                if search.tipo_video:
                    query = query.filter(Video.tipo_video == search.tipo_video)
                
                if search.activo is not None:
                    query = query.filter(Video.activo == search.activo)
                
                if search.min_duration:
                    query = query.filter(Video.duracion_segundos >= search.min_duration)
                
                if search.max_duration:
                    query = query.filter(Video.duracion_segundos <= search.max_duration)
            
            # Contar total
            total = query.count()
            
            # Aplicar ordenamiento
            if search and search.sort_by:
                if search.sort_order == "desc":
                    query = query.order_by(desc(getattr(Video, search.sort_by)))
                else:
                    query = query.order_by(getattr(Video, search.sort_by))
            else:
                query = query.order_by(Video.orden.asc())
            
            # Aplicar paginación
            offset = (page - 1) * size
            videos = query.offset(offset).limit(size).all()
            
            total_pages = (total + size - 1) // size
            
            result = {
                "videos": videos,
                "total": total,
                "page": page,
                "size": size,
                "total_pages": total_pages
            }
            
            logger.info("Videos retrieved", 
                       site_id=site_id, 
                       page=page, 
                       total=total)
            
            return result
            
        except Exception as e:
            logger.error("Error getting videos by site", 
                        site_id=site_id, 
                        error=str(e))
            return {"videos": [], "total": 0, "page": page, "size": size, "total_pages": 0}
    
    async def get_user_video_progress(
        self, 
        user_id: int, 
        site_id: str
    ) -> List[VideoProgress]:
        """Obtener progreso de videos del usuario"""
        try:
            # Obtener todos los videos activos del sitio
            videos = self.db.query(Video).filter(
                and_(
                    Video.site_id == site_id,
                    Video.activo == True
                )
            ).order_by(Video.orden.asc()).all()
            
            progress_list = []
            
            for video in videos:
                # Obtener completación del usuario para este video
                completion = self.db.query(VideoCompletion).filter(
                    and_(
                        VideoCompletion.video_id == video.id,
                        VideoCompletion.user_id == user_id,
                        VideoCompletion.site_id == site_id
                    )
                ).first()
                
                # Determinar si el video puede ser reproducido
                can_play = True
                if video.orden > 1:
                    # Verificar si el video anterior fue completado
                    previous_video = self.db.query(Video).filter(
                        and_(
                            Video.site_id == site_id,
                            Video.orden == video.orden - 1,
                            Video.activo == True
                        )
                    ).first()
                    
                    if previous_video:
                        previous_completion = self.db.query(VideoCompletion).filter(
                            and_(
                                VideoCompletion.video_id == previous_video.id,
                                VideoCompletion.user_id == user_id,
                                VideoCompletion.site_id == site_id,
                                VideoCompletion.completion_status == VideoCompletionStatus.COMPLETED
                            )
                        ).first()
                        
                        can_play = previous_completion is not None
                
                progress = VideoProgress(
                    video_id=video.id,
                    titulo=video.titulo,
                    youtube_id=video.youtube_id,
                    orden=video.orden,
                    completion_status=completion.completion_status if completion else VideoCompletionStatus.NOT_STARTED,
                    completion_percentage=completion.completion_percentage if completion else 0,
                    time_watched=completion.time_watched if completion else 0,
                    duracion_segundos=video.duracion_segundos,
                    points_earned=completion.points_earned if completion else 0,
                    can_play=can_play,
                    thumbnail_url=video.thumbnail_url
                )
                
                progress_list.append(progress)
            
            logger.info("User video progress retrieved", 
                       user_id=user_id, 
                       site_id=site_id, 
                       video_count=len(progress_list))
            
            return progress_list
            
        except Exception as e:
            logger.error("Error getting user video progress", 
                        user_id=user_id, 
                        site_id=site_id, 
                        error=str(e))
            return []
    
    async def record_video_completion(
        self, 
        completion_data: VideoCompletionCreate, 
        user_id: int, 
        site_id: str
    ) -> Optional[VideoCompletionResponse]:
        """Registrar completación de video"""
        try:
            # Verificar que el video existe
            video = await self.get_video_by_id(completion_data.video_id, site_id)
            if not video:
                logger.warning("Video not found for completion", 
                             video_id=completion_data.video_id, 
                             site_id=site_id)
                return None
            
            # Buscar completación existente
            existing_completion = self.db.query(VideoCompletion).filter(
                and_(
                    VideoCompletion.video_id == completion_data.video_id,
                    VideoCompletion.user_id == user_id,
                    VideoCompletion.site_id == site_id
                )
            ).first()
            
            # Calcular puntos ganados
            points_earned = 0
            if completion_data.completion_percentage >= 100:
                points_earned = video.puntos_por_completar
                completion_status = VideoCompletionStatus.COMPLETED
            elif completion_data.completion_percentage >= 50:
                points_earned = int(video.puntos_por_completar * 0.5)
                completion_status = VideoCompletionStatus.IN_PROGRESS
            else:
                completion_status = VideoCompletionStatus.IN_PROGRESS
            
            if existing_completion:
                # Actualizar completación existente
                existing_completion.completion_percentage = completion_data.completion_percentage
                existing_completion.time_watched = completion_data.time_watched
                existing_completion.completion_status = completion_status
                existing_completion.points_earned = points_earned
                
                if completion_status == VideoCompletionStatus.COMPLETED:
                    existing_completion.completed_at = datetime.utcnow()
                
                existing_completion.updated_at = datetime.utcnow()
                completion = existing_completion
            else:
                # Crear nueva completación
                completion = VideoCompletion(
                    site_id=site_id,
                    user_id=user_id,
                    video_id=completion_data.video_id,
                    completion_percentage=completion_data.completion_percentage,
                    time_watched=completion_data.time_watched,
                    completion_status=completion_status,
                    points_earned=points_earned,
                    completed_at=datetime.utcnow() if completion_status == VideoCompletionStatus.COMPLETED else None
                )
                self.db.add(completion)
            
            self.db.commit()
            self.db.refresh(completion)
            
            # Otorgar puntos si es una nueva completación
            if not existing_completion and points_earned > 0:
                await self.points_service.award_points_for_video_completion(
                    user_id=user_id,
                    site_id=site_id,
                    video_id=completion_data.video_id,
                    completion_percentage=completion_data.completion_percentage
                )
                
                # Enviar notificación
                await self.notification_service.send_points_earned_notification(
                    user_id=user_id,
                    site_id=site_id,
                    points=points_earned,
                    reason=f"completar video: {video.titulo}"
                )
            
            logger.info("Video completion recorded", 
                       video_id=completion_data.video_id, 
                       user_id=user_id, 
                       site_id=site_id,
                       completion_percentage=completion_data.completion_percentage,
                       points_earned=points_earned)
            
            return completion
            
        except Exception as e:
            self.db.rollback()
            logger.error("Error recording video completion", 
                        video_id=completion_data.video_id, 
                        user_id=user_id, 
                        site_id=site_id, 
                        error=str(e))
            return None
    
    async def get_video_stats(self, site_id: str, user_id: Optional[int] = None) -> VideoStats:
        """Obtener estadísticas de videos"""
        try:
            query = self.db.query(Video).filter(Video.site_id == site_id)
            
            if user_id:
                # Estadísticas del usuario específico
                user_completions = self.db.query(VideoCompletion).filter(
                    and_(
                        VideoCompletion.user_id == user_id,
                        VideoCompletion.site_id == site_id
                    )
                )
                
                total_videos = query.count()
                active_videos = query.filter(Video.activo == True).count()
                total_views = user_completions.count()
                total_completions = user_completions.filter(
                    VideoCompletion.completion_status == VideoCompletionStatus.COMPLETED
                ).count()
                
                # Calcular tiempo promedio de visualización
                avg_watch_time = user_completions.with_entities(
                    func.avg(VideoCompletion.time_watched)
                ).scalar() or 0
                
                # Video más visto por el usuario
                most_watched = user_completions.order_by(
                    desc(VideoCompletion.time_watched)
                ).first()
                
                most_watched_video = None
                if most_watched:
                    video = await self.get_video_by_id(most_watched.video_id, site_id)
                    if video:
                        most_watched_video = {
                            "id": video.id,
                            "titulo": video.titulo,
                            "time_watched": most_watched.time_watched
                        }
                
                completion_rate = (total_completions / total_videos * 100) if total_videos > 0 else 0
                
            else:
                # Estadísticas globales del sitio
                total_videos = query.count()
                active_videos = query.filter(Video.activo == True).count()
                
                # Estadísticas de completaciones
                completions_query = self.db.query(VideoCompletion).filter(
                    VideoCompletion.site_id == site_id
                )
                
                total_views = completions_query.count()
                total_completions = completions_query.filter(
                    VideoCompletion.completion_status == VideoCompletionStatus.COMPLETED
                ).count()
                
                # Calcular tiempo promedio de visualización
                avg_watch_time = completions_query.with_entities(
                    func.avg(VideoCompletion.time_watched)
                ).scalar() or 0
                
                # Video más visto globalmente
                most_watched = completions_query.order_by(
                    desc(VideoCompletion.time_watched)
                ).first()
                
                most_watched_video = None
                if most_watched:
                    video = await self.get_video_by_id(most_watched.video_id, site_id)
                    if video:
                        most_watched_video = {
                            "id": video.id,
                            "titulo": video.titulo,
                            "total_views": most_watched.time_watched
                        }
                
                completion_rate = (total_completions / total_views * 100) if total_views > 0 else 0
            
            # Videos por tipo
            videos_by_type = {}
            for video_type in VideoType:
                count = query.filter(Video.tipo_video == video_type).count()
                videos_by_type[video_type.value] = count
            
            stats = VideoStats(
                total_videos=total_videos,
                active_videos=active_videos,
                total_views=total_views,
                total_completions=total_completions,
                completion_rate=round(completion_rate, 2),
                average_watch_time=round(avg_watch_time, 2),
                most_watched_video=most_watched_video,
                videos_by_type=videos_by_type
            )
            
            logger.info("Video stats retrieved", 
                       site_id=site_id, 
                       user_id=user_id)
            
            return stats
            
        except Exception as e:
            logger.error("Error getting video stats", 
                        site_id=site_id, 
                        user_id=user_id, 
                        error=str(e))
            return VideoStats()
    
    async def update_video(
        self, 
        video_id: int, 
        site_id: str, 
        video_data: VideoUpdate
    ) -> Optional[Video]:
        """Actualizar video"""
        try:
            video = await self.get_video_by_id(video_id, site_id)
            if not video:
                return None
            
            # Actualizar campos proporcionados
            update_data = video_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(video, field, value)
            
            video.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(video)
            
            logger.info("Video updated", 
                       video_id=video_id, 
                       site_id=site_id)
            
            return video
            
        except Exception as e:
            self.db.rollback()
            logger.error("Error updating video", 
                        video_id=video_id, 
                        site_id=site_id, 
                        error=str(e))
            return None
    
    async def delete_video(self, video_id: int, site_id: str) -> bool:
        """Eliminar video (soft delete)"""
        try:
            video = await self.get_video_by_id(video_id, site_id)
            if not video:
                return False
            
            video.activo = False
            video.status = VideoStatus.ARCHIVED
            video.updated_at = datetime.utcnow()
            self.db.commit()
            
            logger.info("Video deleted", 
                       video_id=video_id, 
                       site_id=site_id)
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error("Error deleting video", 
                        video_id=video_id, 
                        site_id=site_id, 
                        error=str(e))
            return False
