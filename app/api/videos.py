from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.site_config import SiteConfig
from app.schemas.video import (
    VideoCreate, VideoResponse, VideoUpdate, VideoStats, VideoProgress,
    VideoCompletionCreate, VideoCompletionResponse, VideoList, VideoSearch,
    VideoImport, VideoImportResponse, VideoType
)
from app.services.video_service import VideoService
from app.api.dependencies import (
    get_current_user, get_site_config, require_site_access, 
    require_user_ownership, require_active_user
)
from typing import Optional, List
import structlog

logger = structlog.get_logger()

router = APIRouter()

@router.post("/", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
async def create_video(
    video_data: VideoCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear nuevo video (solo para administradores)"""
    try:
        # Por ahora, permitir a todos los usuarios crear videos
        # En producción, esto debería estar restringido a administradores
        video_service = VideoService(db)
        
        video = await video_service.create_video(
            video_data=video_data,
            site_id=current_user.site_id
        )
        
        if not video:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error creating video. Check YouTube ID and site configuration."
            )
        
        logger.info("Video created", 
                   video_id=video.id, 
                   user_id=current_user.id, 
                   site_id=current_user.site_id)
        
        return video
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating video", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating video"
        )

@router.get("/", response_model=VideoList)
async def get_videos(
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(10, ge=1, le=100, description="Tamaño de página"),
    query: Optional[str] = Query(None, description="Término de búsqueda"),
    tipo_video: Optional[VideoType] = Query(None, description="Filtrar por tipo de video"),
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Obtener videos del sitio"""
    try:
        video_service = VideoService(db)
        
        # Crear objeto de búsqueda
        search = VideoSearch(
            query=query,
            tipo_video=tipo_video,
            activo=activo,
            page=page,
            size=size
        )
        
        result = await video_service.get_videos_by_site(
            site_id=site_config.site_id,
            page=page,
            size=size,
            search=search
        )
        
        logger.info("Videos retrieved", 
                   site_id=site_config.site_id, 
                   page=page, 
                   total=result["total"])
        
        return VideoList(**result)
        
    except Exception as e:
        logger.error("Error getting videos", 
                    site_id=site_config.site_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving videos"
        )

@router.get("/progress", response_model=List[VideoProgress])
async def get_my_video_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener progreso de videos del usuario actual"""
    try:
        video_service = VideoService(db)
        
        progress = await video_service.get_user_video_progress(
            user_id=current_user.id,
            site_id=current_user.site_id
        )
        
        logger.info("User video progress retrieved", 
                   user_id=current_user.id, 
                   site_id=current_user.site_id,
                   video_count=len(progress))
        
        return progress
        
    except Exception as e:
        logger.error("Error getting user video progress", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving video progress"
        )

@router.get("/{video_id}", response_model=VideoResponse)
async def get_video_by_id(
    video_id: int,
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Obtener video por ID"""
    try:
        video_service = VideoService(db)
        
        video = await video_service.get_video_by_id(
            video_id=video_id,
            site_id=site_config.site_id
        )
        
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found"
            )
        
        logger.info("Video retrieved by ID", 
                   video_id=video_id, 
                   site_id=site_config.site_id)
        
        return video
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting video by ID", 
                    video_id=video_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving video"
        )

@router.post("/{video_id}/complete", response_model=VideoCompletionResponse)
async def complete_video(
    video_id: int,
    completion_data: VideoCompletionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Registrar completación de video"""
    try:
        # Verificar que el video_id coincide
        if completion_data.video_id != video_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Video ID mismatch"
            )
        
        video_service = VideoService(db)
        
        completion = await video_service.record_video_completion(
            completion_data=completion_data,
            user_id=current_user.id,
            site_id=current_user.site_id
        )
        
        if not completion:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error recording video completion"
            )
        
        logger.info("Video completion recorded", 
                   video_id=video_id, 
                   user_id=current_user.id, 
                   site_id=current_user.site_id,
                   completion_percentage=completion_data.completion_percentage)
        
        return completion
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error recording video completion", 
                    video_id=video_id, 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error recording video completion"
        )

@router.get("/me/stats", response_model=VideoStats)
async def get_my_video_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas de videos del usuario actual"""
    try:
        video_service = VideoService(db)
        
        stats = await video_service.get_video_stats(
            site_id=current_user.site_id,
            user_id=current_user.id
        )
        
        logger.info("User video stats retrieved", 
                   user_id=current_user.id, 
                   site_id=current_user.site_id)
        
        return stats
        
    except Exception as e:
        logger.error("Error getting user video stats", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving video statistics"
        )

@router.get("/stats/global", response_model=VideoStats)
async def get_global_video_stats(
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas globales de videos del sitio"""
    try:
        video_service = VideoService(db)
        
        stats = await video_service.get_video_stats(
            site_id=site_config.site_id
        )
        
        logger.info("Global video stats retrieved", 
                   site_id=site_config.site_id)
        
        return stats
        
    except Exception as e:
        logger.error("Error getting global video stats", 
                    site_id=site_config.site_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving global video statistics"
        )

@router.post("/import", response_model=VideoImportResponse)
async def import_videos_from_youtube(
    import_data: VideoImport,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Importar videos desde YouTube (solo para administradores)"""
    try:
        # Por ahora, permitir a todos los usuarios importar videos
        # En producción, esto debería estar restringido a administradores
        video_service = VideoService(db)
        
        response = await video_service.youtube_service.import_videos_from_playlist(
            site_id=current_user.site_id,
            import_data=import_data
        )
        
        logger.info("Videos imported from YouTube", 
                   user_id=current_user.id, 
                   site_id=current_user.site_id,
                   playlist_id=import_data.playlist_id,
                   imported_count=response.imported_count)
        
        return response
        
    except Exception as e:
        logger.error("Error importing videos from YouTube", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error importing videos from YouTube"
        )

@router.put("/{video_id}", response_model=VideoResponse)
async def update_video(
    video_id: int,
    video_data: VideoUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar video (solo para administradores)"""
    try:
        # Por ahora, permitir a todos los usuarios actualizar videos
        # En producción, esto debería estar restringido a administradores
        video_service = VideoService(db)
        
        video = await video_service.update_video(
            video_id=video_id,
            site_id=current_user.site_id,
            video_data=video_data
        )
        
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found"
            )
        
        logger.info("Video updated", 
                   video_id=video_id, 
                   user_id=current_user.id, 
                   site_id=current_user.site_id)
        
        return video
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating video", 
                    video_id=video_id, 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating video"
        )

@router.delete("/{video_id}")
async def delete_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar video (solo para administradores)"""
    try:
        # Por ahora, permitir a todos los usuarios eliminar videos
        # En producción, esto debería estar restringido a administradores
        video_service = VideoService(db)
        
        success = await video_service.delete_video(
            video_id=video_id,
            site_id=current_user.site_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found"
            )
        
        logger.info("Video deleted", 
                   video_id=video_id, 
                   user_id=current_user.id, 
                   site_id=current_user.site_id)
        
        return {"message": "Video deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting video", 
                    video_id=video_id, 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting video"
        )

@router.get("/{video_id}/embed")
async def get_video_embed_info(
    video_id: int,
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Obtener información de embed del video"""
    try:
        video_service = VideoService(db)
        
        video = await video_service.get_video_by_id(
            video_id=video_id,
            site_id=site_config.site_id
        )
        
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found"
            )
        
        embed_info = {
            "video_id": video.id,
            "youtube_id": video.youtube_id,
            "embed_url": video.embed_url,
            "thumbnail_url": video.thumbnail_url,
            "titulo": video.titulo,
            "duracion_segundos": video.duracion_segundos,
            "orden": video.orden
        }
        
        logger.info("Video embed info retrieved", 
                   video_id=video_id, 
                   site_id=site_config.site_id)
        
        return embed_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting video embed info", 
                    video_id=video_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving video embed information"
        )
