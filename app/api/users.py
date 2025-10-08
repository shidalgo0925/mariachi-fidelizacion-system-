from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.site_config import SiteConfig
from app.schemas.user import (
    UserCreate, UserResponse, UserUpdate, UserStats, UserLeaderboard,
    UserList, UserSearch, UserProfile, PasswordUpdate
)
from app.services.user_service import UserService
from app.api.dependencies import (
    get_current_user, get_site_config, require_site_access, 
    require_user_ownership, require_active_user
)
from typing import Optional, List
import structlog

logger = structlog.get_logger()

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Obtener perfil del usuario actual"""
    try:
        logger.info("User profile requested", user_id=current_user.id, site_id=current_user.site_id)
        return current_user
        
    except Exception as e:
        logger.error("Error getting user profile", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user profile"
        )

@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar perfil del usuario actual"""
    try:
        user_service = UserService(db)
        updated_user = await user_service.update_user(
            current_user.id, 
            current_user.site_id, 
            user_data
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info("User profile updated", user_id=current_user.id, site_id=current_user.site_id)
        return updated_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating user profile", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user profile"
        )

@router.get("/me/stats", response_model=UserStats)
async def get_current_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas del usuario actual"""
    try:
        user_service = UserService(db)
        stats = await user_service.get_user_stats(current_user.id, current_user.site_id)
        
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User stats not found"
            )
        
        logger.info("User stats requested", user_id=current_user.id, site_id=current_user.site_id)
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting user stats", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user stats"
        )

@router.get("/me/profile", response_model=UserProfile)
async def get_current_user_full_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener perfil completo del usuario actual"""
    try:
        user_service = UserService(db)
        
        # Obtener estadísticas
        stats = await user_service.get_user_stats(current_user.id, current_user.site_id)
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User stats not found"
            )
        
        # Obtener actividades recientes (placeholder)
        recent_activities = [
            {
                "tipo": "sticker_generado",
                "descripcion": "Generaste un sticker de descuento",
                "fecha": "2024-12-19T10:00:00Z",
                "puntos": 5
            }
        ]
        
        # Obtener logros (placeholder)
        achievements = [
            {
                "id": "primer_sticker",
                "nombre": "Primer Sticker",
                "descripcion": "Generaste tu primer sticker",
                "desbloqueado": True,
                "fecha_desbloqueo": "2024-12-19T10:00:00Z"
            }
        ]
        
        profile = UserProfile(
            user=current_user,
            stats=stats,
            recent_activities=recent_activities,
            achievements=achievements
        )
        
        logger.info("User full profile requested", user_id=current_user.id, site_id=current_user.site_id)
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting user full profile", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user profile"
        )

@router.put("/me/password")
async def update_current_user_password(
    password_data: PasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar contraseña del usuario actual"""
    try:
        user_service = UserService(db)
        
        # Verificar contraseña actual (esto requeriría un campo password_hash en el modelo)
        # Por ahora, solo actualizamos sin verificar
        success = await user_service.update_password(
            current_user.email, 
            password_data.new_password, 
            current_user.site_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error updating password"
            )
        
        logger.info("User password updated", user_id=current_user.id, site_id=current_user.site_id)
        return {"message": "Password updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating user password", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating password"
        )

@router.get("/leaderboard", response_model=List[UserLeaderboard])
async def get_leaderboard(
    limit: int = Query(10, ge=1, le=50, description="Número de usuarios en el ranking"),
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Obtener ranking de usuarios del sitio"""
    try:
        user_service = UserService(db)
        leaderboard = await user_service.get_leaderboard(site_config.site_id, limit)
        
        logger.info("Leaderboard requested", site_id=site_config.site_id, limit=limit)
        return leaderboard
        
    except Exception as e:
        logger.error("Error getting leaderboard", site_id=site_config.site_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving leaderboard"
        )

@router.get("/search", response_model=UserList)
async def search_users(
    query: Optional[str] = Query(None, description="Término de búsqueda"),
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(10, ge=1, le=100, description="Tamaño de página"),
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Buscar usuarios del sitio"""
    try:
        user_service = UserService(db)
        result = await user_service.list_users(
            site_config.site_id, 
            page=page, 
            size=size, 
            search=query
        )
        
        logger.info("Users search requested", site_id=site_config.site_id, query=query, page=page)
        return UserList(**result)
        
    except Exception as e:
        logger.error("Error searching users", site_id=site_config.site_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error searching users"
        )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener usuario por ID (solo si es el mismo usuario o admin)"""
    try:
        # Verificar que el usuario puede acceder a este perfil
        if current_user.id != user_id:
            # Aquí se podría verificar si es admin
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        user_service = UserService(db)
        user = await user_service.get_user_by_id(user_id, current_user.site_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info("User profile requested by ID", user_id=user_id, site_id=current_user.site_id)
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting user by ID", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user"
        )

@router.get("/{user_id}/stats", response_model=UserStats)
async def get_user_stats_by_id(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas de usuario por ID"""
    try:
        # Verificar que el usuario puede acceder a estas estadísticas
        if current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        user_service = UserService(db)
        stats = await user_service.get_user_stats(user_id, current_user.site_id)
        
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User stats not found"
            )
        
        logger.info("User stats requested by ID", user_id=user_id, site_id=current_user.site_id)
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting user stats by ID", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user stats"
        )

@router.delete("/me")
async def deactivate_current_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Desactivar cuenta del usuario actual"""
    try:
        user_service = UserService(db)
        success = await user_service.deactivate_user(current_user.id, current_user.site_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error deactivating user"
            )
        
        logger.info("User account deactivated", user_id=current_user.id, site_id=current_user.site_id)
        return {"message": "Account deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deactivating user", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deactivating account"
        )
