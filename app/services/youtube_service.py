import httpx
import json
from sqlalchemy.orm import Session
from app.models.video import Video
from app.models.site_config import SiteConfig
from app.schemas.video import (
    VideoCreate, VideoImport, VideoImportResponse, VideoResponse,
    VideoType, VideoStatus
)
from typing import Optional, Dict, Any, List
import structlog
from datetime import datetime, timedelta
import re

logger = structlog.get_logger()

class YouTubeService:
    """Servicio para integración con YouTube Data API v3"""
    
    def __init__(self, db: Session):
        self.db = db
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.embed_base_url = "https://www.youtube.com/embed"
        self.thumbnail_base_url = "https://img.youtube.com/vi"
    
    async def get_video_info(
        self, 
        video_id: str, 
        api_key: str
    ) -> Optional[Dict[str, Any]]:
        """Obtener información de un video de YouTube"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/videos",
                    params={
                        "part": "snippet,contentDetails,statistics",
                        "id": video_id,
                        "key": api_key
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("items", [])
                    
                    if items:
                        video_data = items[0]
                        snippet = video_data.get("snippet", {})
                        content_details = video_data.get("contentDetails", {})
                        statistics = video_data.get("statistics", {})
                        
                        # Parsear duración
                        duration = self._parse_duration(content_details.get("duration", ""))
                        
                        return {
                            "id": video_data.get("id"),
                            "title": snippet.get("title"),
                            "description": snippet.get("description"),
                            "thumbnail_url": self._get_thumbnail_url(video_id),
                            "embed_url": f"{self.embed_base_url}/{video_id}",
                            "duration_seconds": duration,
                            "view_count": int(statistics.get("viewCount", 0)),
                            "like_count": int(statistics.get("likeCount", 0)),
                            "comment_count": int(statistics.get("commentCount", 0)),
                            "published_at": snippet.get("publishedAt"),
                            "channel_title": snippet.get("channelTitle"),
                            "tags": snippet.get("tags", [])
                        }
                    else:
                        logger.warning("Video not found", video_id=video_id)
                        return None
                else:
                    logger.error("YouTube API error", 
                               video_id=video_id, 
                               status_code=response.status_code,
                               response=response.text)
                    return None
            
        except Exception as e:
            logger.error("Error getting YouTube video info", 
                        video_id=video_id, 
                        error=str(e))
            return None
    
    async def get_playlist_videos(
        self, 
        playlist_id: str, 
        api_key: str,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """Obtener videos de una playlist de YouTube"""
        try:
            videos = []
            next_page_token = None
            
            async with httpx.AsyncClient() as client:
                while len(videos) < max_results:
                    params = {
                        "part": "snippet,contentDetails",
                        "playlistId": playlist_id,
                        "maxResults": min(50, max_results - len(videos)),
                        "key": api_key
                    }
                    
                    if next_page_token:
                        params["pageToken"] = next_page_token
                    
                    response = await client.get(
                        f"{self.base_url}/playlistItems",
                        params=params
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        items = data.get("items", [])
                        
                        for item in items:
                            snippet = item.get("snippet", {})
                            video_id = snippet.get("resourceId", {}).get("videoId")
                            
                            if video_id:
                                # Obtener información detallada del video
                                video_info = await self.get_video_info(video_id, api_key)
                                if video_info:
                                    videos.append(video_info)
                        
                        next_page_token = data.get("nextPageToken")
                        if not next_page_token:
                            break
                    else:
                        logger.error("YouTube API error getting playlist", 
                                   playlist_id=playlist_id, 
                                   status_code=response.status_code)
                        break
            
            logger.info("Playlist videos retrieved", 
                       playlist_id=playlist_id, 
                       video_count=len(videos))
            
            return videos
            
        except Exception as e:
            logger.error("Error getting YouTube playlist videos", 
                        playlist_id=playlist_id, 
                        error=str(e))
            return []
    
    async def get_playlist_info(
        self, 
        playlist_id: str, 
        api_key: str
    ) -> Optional[Dict[str, Any]]:
        """Obtener información de una playlist de YouTube"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/playlists",
                    params={
                        "part": "snippet,contentDetails",
                        "id": playlist_id,
                        "key": api_key
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("items", [])
                    
                    if items:
                        playlist_data = items[0]
                        snippet = playlist_data.get("snippet", {})
                        content_details = playlist_data.get("contentDetails", {})
                        
                        return {
                            "id": playlist_data.get("id"),
                            "title": snippet.get("title"),
                            "description": snippet.get("description"),
                            "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                            "video_count": int(content_details.get("itemCount", 0)),
                            "published_at": snippet.get("publishedAt"),
                            "channel_title": snippet.get("channelTitle")
                        }
                    else:
                        logger.warning("Playlist not found", playlist_id=playlist_id)
                        return None
                else:
                    logger.error("YouTube API error getting playlist info", 
                               playlist_id=playlist_id, 
                               status_code=response.status_code)
                    return None
            
        except Exception as e:
            logger.error("Error getting YouTube playlist info", 
                        playlist_id=playlist_id, 
                        error=str(e))
            return None
    
    async def import_videos_from_playlist(
        self, 
        site_id: str, 
        import_data: VideoImport
    ) -> VideoImportResponse:
        """Importar videos desde una playlist de YouTube"""
        try:
            # Obtener configuración del sitio
            site_config = self.db.query(SiteConfig).filter(
                SiteConfig.site_id == site_id
            ).first()
            
            if not site_config or not site_config.youtube_api_key:
                return VideoImportResponse(
                    success=False,
                    errors=["YouTube API key not configured for this site"]
                )
            
            # Obtener información de la playlist
            playlist_info = await self.get_playlist_info(
                import_data.playlist_id, 
                site_config.youtube_api_key
            )
            
            if not playlist_info:
                return VideoImportResponse(
                    success=False,
                    errors=[f"Playlist {import_data.playlist_id} not found or not accessible"]
                )
            
            # Obtener videos de la playlist
            if import_data.import_all:
                videos_data = await self.get_playlist_videos(
                    import_data.playlist_id, 
                    site_config.youtube_api_key
                )
            else:
                videos_data = []
                for video_id in import_data.video_ids or []:
                    video_info = await self.get_video_info(video_id, site_config.youtube_api_key)
                    if video_info:
                        videos_data.append(video_info)
            
            imported_videos = []
            skipped_count = 0
            errors = []
            
            # Obtener el siguiente orden disponible
            max_order = self.db.query(Video.orden).filter(
                Video.site_id == site_id
            ).order_by(Video.orden.desc()).first()
            
            next_order = (max_order[0] + 1) if max_order else 1
            
            for i, video_data in enumerate(videos_data):
                try:
                    # Verificar si el video ya existe
                    existing_video = self.db.query(Video).filter(
                        Video.youtube_id == video_data["id"],
                        Video.site_id == site_id
                    ).first()
                    
                    if existing_video:
                        skipped_count += 1
                        continue
                    
                    # Crear nuevo video
                    video = Video(
                        site_id=site_id,
                        titulo=video_data["title"],
                        descripcion=video_data["description"],
                        youtube_id=video_data["id"],
                        tipo_video=VideoType.ENTERTAINMENT,  # Por defecto
                        duracion_segundos=video_data["duration_seconds"],
                        orden=next_order + i,
                        puntos_por_completar=import_data.default_points,
                        activo=import_data.auto_activate,
                        thumbnail_url=video_data["thumbnail_url"],
                        embed_url=video_data["embed_url"],
                        view_count=video_data["view_count"],
                        like_count=video_data["like_count"],
                        comment_count=video_data["comment_count"],
                        published_at=datetime.fromisoformat(
                            video_data["published_at"].replace('Z', '+00:00')
                        ) if video_data["published_at"] else None,
                        status=VideoStatus.ACTIVE if import_data.auto_activate else VideoStatus.DRAFT
                    )
                    
                    self.db.add(video)
                    self.db.commit()
                    self.db.refresh(video)
                    
                    imported_videos.append(video)
                    
                except Exception as e:
                    error_msg = f"Error importing video {video_data.get('id', 'unknown')}: {str(e)}"
                    errors.append(error_msg)
                    logger.error("Error importing individual video", 
                               video_id=video_data.get("id"), 
                               error=str(e))
            
            logger.info("Videos imported from playlist", 
                       site_id=site_id, 
                       playlist_id=import_data.playlist_id,
                       imported_count=len(imported_videos),
                       skipped_count=skipped_count)
            
            return VideoImportResponse(
                success=len(imported_videos) > 0,
                imported_count=len(imported_videos),
                skipped_count=skipped_count,
                errors=errors,
                imported_videos=imported_videos
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error("Error importing videos from playlist", 
                        site_id=site_id, 
                        playlist_id=import_data.playlist_id, 
                        error=str(e))
            return VideoImportResponse(
                success=False,
                errors=[f"Import error: {str(e)}"]
            )
    
    async def update_video_stats(
        self, 
        video: Video, 
        api_key: str
    ) -> bool:
        """Actualizar estadísticas de un video desde YouTube"""
        try:
            video_info = await self.get_video_info(video.youtube_id, api_key)
            
            if not video_info:
                return False
            
            # Actualizar estadísticas
            video.view_count = video_info["view_count"]
            video.like_count = video_info["like_count"]
            video.comment_count = video_info["comment_count"]
            video.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info("Video stats updated", 
                       video_id=video.id, 
                       youtube_id=video.youtube_id)
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error("Error updating video stats", 
                        video_id=video.id, 
                        youtube_id=video.youtube_id, 
                        error=str(e))
            return False
    
    async def validate_youtube_video_id(self, video_id: str) -> bool:
        """Validar formato de ID de video de YouTube"""
        try:
            # YouTube video IDs son de 11 caracteres alfanuméricos
            if not video_id or len(video_id) != 11:
                return False
            
            # Verificar que solo contiene caracteres válidos
            pattern = r'^[a-zA-Z0-9_-]{11}$'
            return bool(re.match(pattern, video_id))
            
        except Exception as e:
            logger.error("Error validating YouTube video ID", 
                        video_id=video_id, 
                        error=str(e))
            return False
    
    def _parse_duration(self, duration: str) -> int:
        """Parsear duración ISO 8601 a segundos"""
        try:
            if not duration:
                return 0
            
            # Remover 'PT' del inicio
            duration = duration.replace('PT', '')
            
            total_seconds = 0
            
            # Parsear horas
            if 'H' in duration:
                hours = int(duration.split('H')[0])
                total_seconds += hours * 3600
                duration = duration.split('H')[1]
            
            # Parsear minutos
            if 'M' in duration:
                minutes = int(duration.split('M')[0])
                total_seconds += minutes * 60
                duration = duration.split('M')[1]
            
            # Parsear segundos
            if 'S' in duration:
                seconds = int(duration.split('S')[0])
                total_seconds += seconds
            
            return total_seconds
            
        except Exception as e:
            logger.error("Error parsing duration", duration=duration, error=str(e))
            return 0
    
    def _get_thumbnail_url(self, video_id: str, quality: str = "high") -> str:
        """Obtener URL de thumbnail de YouTube"""
        quality_map = {
            "default": "default.jpg",
            "medium": "mqdefault.jpg",
            "high": "hqdefault.jpg",
            "standard": "sddefault.jpg",
            "maxres": "maxresdefault.jpg"
        }
        
        filename = quality_map.get(quality, "hqdefault.jpg")
        return f"{self.thumbnail_base_url}/{video_id}/{filename}"
    
    async def search_videos(
        self, 
        query: str, 
        api_key: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Buscar videos en YouTube"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/search",
                    params={
                        "part": "snippet",
                        "q": query,
                        "type": "video",
                        "maxResults": max_results,
                        "key": api_key
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("items", [])
                    
                    videos = []
                    for item in items:
                        snippet = item.get("snippet", {})
                        video_id = item.get("id", {}).get("videoId")
                        
                        if video_id:
                            videos.append({
                                "id": video_id,
                                "title": snippet.get("title"),
                                "description": snippet.get("description"),
                                "thumbnail_url": self._get_thumbnail_url(video_id),
                                "channel_title": snippet.get("channelTitle"),
                                "published_at": snippet.get("publishedAt")
                            })
                    
                    logger.info("YouTube videos searched", 
                               query=query, 
                               result_count=len(videos))
                    
                    return videos
                else:
                    logger.error("YouTube API error searching videos", 
                               query=query, 
                               status_code=response.status_code)
                    return []
            
        except Exception as e:
            logger.error("Error searching YouTube videos", 
                        query=query, 
                        error=str(e))
            return []
