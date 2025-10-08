from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.site_config import SiteConfig
from app.schemas.instagram import (
    InstagramAuthRequest, InstagramAuthResponse, InstagramCallbackRequest,
    InstagramCallbackResponse, InstagramVerificationRequest, InstagramVerificationResponse,
    InstagramUserResponse, InstagramStats, InstagramReconnectRequest, InstagramReconnectResponse
)
from app.services.instagram_service import InstagramService
from app.api.dependencies import (
    get_current_user, get_site_config, require_site_access, 
    require_user_ownership, require_active_user
)
from typing import Optional, List
import structlog

logger = structlog.get_logger()

router = APIRouter()

@router.get("/auth", response_model=InstagramAuthResponse)
async def get_instagram_auth_url(
    redirect_uri: Optional[str] = Query(None, description="URI de redirección personalizada"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener URL de autenticación de Instagram"""
    try:
        instagram_service = InstagramService(db)
        
        auth_response = await instagram_service.generate_auth_url(
            site_id=current_user.site_id,
            redirect_uri=redirect_uri
        )
        
        logger.info("Instagram auth URL requested", 
                   user_id=current_user.id, 
                   site_id=current_user.site_id)
        
        return auth_response
        
    except Exception as e:
        logger.error("Error getting Instagram auth URL", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating Instagram authentication URL"
        )

@router.post("/callback", response_model=InstagramCallbackResponse)
async def handle_instagram_callback(
    callback_data: InstagramCallbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manejar callback de autenticación de Instagram"""
    try:
        if callback_data.error:
            return InstagramCallbackResponse(
                success=False,
                message=f"Instagram authorization failed: {callback_data.error_description or callback_data.error}"
            )
        
        instagram_service = InstagramService(db)
        
        response = await instagram_service.handle_callback(
            code=callback_data.code,
            state=callback_data.state,
            site_id=current_user.site_id,
            user_id=current_user.id
        )
        
        logger.info("Instagram callback handled", 
                   user_id=current_user.id, 
                   site_id=current_user.site_id,
                   success=response.success)
        
        return response
        
    except Exception as e:
        logger.error("Error handling Instagram callback", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing Instagram callback"
        )

@router.get("/me", response_model=InstagramUserResponse)
async def get_my_instagram_connection(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener conexión de Instagram del usuario actual"""
    try:
        instagram_service = InstagramService(db)
        
        instagram_user = await instagram_service._get_instagram_user(
            user_id=current_user.id,
            site_id=current_user.site_id
        )
        
        if not instagram_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instagram account not connected"
            )
        
        logger.info("Instagram connection retrieved", 
                   user_id=current_user.id, 
                   site_id=current_user.site_id)
        
        return instagram_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting Instagram connection", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving Instagram connection"
        )

@router.post("/verify", response_model=InstagramVerificationResponse)
async def verify_instagram_following(
    verification_data: InstagramVerificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verificar si el usuario sigue la cuenta objetivo en Instagram"""
    try:
        instagram_service = InstagramService(db)
        
        response = await instagram_service.verify_following(
            user_id=current_user.id,
            site_id=current_user.site_id,
            target_account=verification_data.target_account
        )
        
        logger.info("Instagram following verification requested", 
                   user_id=current_user.id, 
                   site_id=current_user.site_id,
                   target_account=verification_data.target_account,
                   verified=response.verified)
        
        return response
        
    except Exception as e:
        logger.error("Error verifying Instagram following", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error verifying Instagram following"
        )

@router.get("/media")
async def get_my_instagram_media(
    limit: int = Query(25, ge=1, le=100, description="Número de posts a obtener"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener media del usuario de Instagram"""
    try:
        instagram_service = InstagramService(db)
        
        media = await instagram_service.get_user_media(
            user_id=current_user.id,
            site_id=current_user.site_id,
            limit=limit
        )
        
        logger.info("Instagram media requested", 
                   user_id=current_user.id, 
                   site_id=current_user.site_id,
                   media_count=len(media))
        
        return {
            "media": media,
            "total_count": len(media),
            "user_id": current_user.id
        }
        
    except Exception as e:
        logger.error("Error getting Instagram media", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving Instagram media"
        )

@router.post("/refresh-token")
async def refresh_instagram_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Refrescar token de acceso de Instagram"""
    try:
        instagram_service = InstagramService(db)
        
        success = await instagram_service.refresh_access_token(
            user_id=current_user.id,
            site_id=current_user.site_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to refresh Instagram access token"
            )
        
        logger.info("Instagram token refreshed", 
                   user_id=current_user.id, 
                   site_id=current_user.site_id)
        
        return {"message": "Instagram access token refreshed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error refreshing Instagram token", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error refreshing Instagram access token"
        )

@router.post("/reconnect", response_model=InstagramReconnectResponse)
async def reconnect_instagram_account(
    reconnect_data: InstagramReconnectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reconectar cuenta de Instagram"""
    try:
        instagram_service = InstagramService(db)
        
        # Generar nueva URL de autenticación
        auth_response = await instagram_service.generate_auth_url(
            site_id=current_user.site_id
        )
        
        logger.info("Instagram reconnection requested", 
                   user_id=current_user.id, 
                   site_id=current_user.site_id)
        
        return InstagramReconnectResponse(
            success=True,
            message="Instagram reconnection initiated",
            auth_url=auth_response.auth_url
        )
        
    except Exception as e:
        logger.error("Error reconnecting Instagram account", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error reconnecting Instagram account"
        )

@router.delete("/disconnect")
async def disconnect_instagram_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Desconectar cuenta de Instagram"""
    try:
        instagram_service = InstagramService(db)
        
        success = await instagram_service.disconnect_instagram(
            user_id=current_user.id,
            site_id=current_user.site_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to disconnect Instagram account"
            )
        
        logger.info("Instagram account disconnected", 
                   user_id=current_user.id, 
                   site_id=current_user.site_id)
        
        return {"message": "Instagram account disconnected successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error disconnecting Instagram account", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error disconnecting Instagram account"
        )

@router.get("/stats", response_model=InstagramStats)
async def get_instagram_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas de Instagram del usuario"""
    try:
        instagram_service = InstagramService(db)
        
        # Obtener conexión de Instagram
        instagram_user = await instagram_service._get_instagram_user(
            user_id=current_user.id,
            site_id=current_user.site_id
        )
        
        if not instagram_user:
            return InstagramStats()
        
        # Obtener media para estadísticas
        media = await instagram_service.get_user_media(
            user_id=current_user.id,
            site_id=current_user.site_id,
            limit=100
        )
        
        # Calcular estadísticas
        total_connections = 1 if instagram_user else 0
        verified_followers = 1 if instagram_user.verification_status == "verified" else 0
        pending_verifications = 1 if instagram_user.verification_status == "pending" else 0
        failed_verifications = 1 if instagram_user.verification_status == "failed" else 0
        stickers_generated = 1 if instagram_user.sticker_generated else 0
        
        stats = InstagramStats(
            total_connections=total_connections,
            verified_followers=verified_followers,
            pending_verifications=pending_verifications,
            failed_verifications=failed_verifications,
            stickers_generated=stickers_generated,
            last_verification=instagram_user.last_verification
        )
        
        logger.info("Instagram stats retrieved", 
                   user_id=current_user.id, 
                   site_id=current_user.site_id)
        
        return stats
        
    except Exception as e:
        logger.error("Error getting Instagram stats", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving Instagram statistics"
        )

@router.get("/stats/global", response_model=InstagramStats)
async def get_global_instagram_stats(
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas globales de Instagram del sitio"""
    try:
        from app.models.instagram_user import InstagramUser
        
        # Obtener estadísticas globales
        total_connections = db.query(InstagramUser).filter(
            InstagramUser.site_id == site_config.site_id
        ).count()
        
        verified_followers = db.query(InstagramUser).filter(
            InstagramUser.site_id == site_config.site_id,
            InstagramUser.verification_status == "verified"
        ).count()
        
        pending_verifications = db.query(InstagramUser).filter(
            InstagramUser.site_id == site_config.site_id,
            InstagramUser.verification_status == "pending"
        ).count()
        
        failed_verifications = db.query(InstagramUser).filter(
            InstagramUser.site_id == site_config.site_id,
            InstagramUser.verification_status == "failed"
        ).count()
        
        stickers_generated = db.query(InstagramUser).filter(
            InstagramUser.site_id == site_config.site_id,
            InstagramUser.sticker_generated == True
        ).count()
        
        # Obtener última verificación
        last_verification = db.query(InstagramUser.last_verification).filter(
            InstagramUser.site_id == site_config.site_id,
            InstagramUser.last_verification.isnot(None)
        ).order_by(InstagramUser.last_verification.desc()).first()
        
        stats = InstagramStats(
            total_connections=total_connections,
            verified_followers=verified_followers,
            pending_verifications=pending_verifications,
            failed_verifications=failed_verifications,
            stickers_generated=stickers_generated,
            last_verification=last_verification[0] if last_verification else None
        )
        
        logger.info("Global Instagram stats retrieved", 
                   site_id=site_config.site_id)
        
        return stats
        
    except Exception as e:
        logger.error("Error getting global Instagram stats", 
                    site_id=site_config.site_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving global Instagram statistics"
        )
