from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, Union
from app.database import get_db
from app.models.user import User
from app.models.site_config import SiteConfig
from app.services.user_service import UserService
from app.utils.security import SecurityUtils
import structlog

logger = structlog.get_logger()
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None,
    db: Session = Depends(get_db)
) -> User:
    """Obtener usuario actual desde token JWT"""
    try:
        # Verificar token
        token = credentials.credentials
        payload = SecurityUtils.verify_token(token)
        
        # Obtener configuración del sitio
        site_config = getattr(request.state, 'site_config', None)
        if not site_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Site configuration not found"
            )
        
        # Validar acceso al sitio
        if not SecurityUtils.validate_site_access(payload, site_config.site_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this site"
            )
        
        # Obtener usuario
        user_service = UserService(db)
        user = await user_service.get_user_by_id(int(payload["sub"]), site_config.site_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not user.activo:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive"
            )
        
        # Agregar usuario al request state para uso posterior
        request.state.current_user = user
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting current user", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

async def get_current_user_optional(
    request: Request = None,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Obtener usuario actual opcionalmente (para endpoints que pueden funcionar sin autenticación)"""
    try:
        # Verificar si hay token en el header
        authorization = request.headers.get("Authorization")
        if not authorization:
            return None
        
        # Extraer token
        token = SecurityUtils.extract_token_from_header(authorization)
        
        # Verificar token
        payload = SecurityUtils.verify_token(token)
        
        # Obtener configuración del sitio
        site_config = getattr(request.state, 'site_config', None)
        if not site_config:
            return None
        
        # Validar acceso al sitio
        if not SecurityUtils.validate_site_access(payload, site_config.site_id):
            return None
        
        # Obtener usuario
        user_service = UserService(db)
        user = await user_service.get_user_by_id(int(payload["sub"]), site_config.site_id)
        
        if not user or not user.activo:
            return None
        
        # Agregar usuario al request state
        request.state.current_user = user
        
        return user
        
    except Exception as e:
        logger.debug("Optional user authentication failed", error=str(e))
        return None

async def get_site_config(request: Request) -> SiteConfig:
    """Obtener configuración del sitio actual"""
    site_config = getattr(request.state, 'site_config', None)
    if not site_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Site configuration not found"
        )
    return site_config

async def get_site_id(request: Request) -> str:
    """Obtener ID del sitio actual"""
    site_id = getattr(request.state, 'site_id', None)
    if not site_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Site ID not found"
        )
    return site_id

async def require_site_access(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependencia que requiere acceso al sitio y usuario autenticado"""
    # El usuario ya está validado por get_current_user
    # Solo verificamos que tenga acceso al sitio
    site_config = await get_site_config(request)
    
    if current_user.site_id != site_config.site_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied for this site"
        )
    
    return current_user

async def require_user_ownership(
    user_id: int,
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependencia que requiere que el usuario sea el propietario del recurso"""
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: insufficient permissions"
        )
    
    return current_user

async def require_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependencia que requiere usuario activo"""
    if not current_user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return current_user

async def require_verified_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependencia que requiere usuario verificado"""
    if not current_user.verificado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not verified"
        )
    
    return current_user

async def require_instagram_verified(
    current_user: User = Depends(get_current_user),
    site_config: SiteConfig = Depends(get_site_config)
) -> User:
    """Dependencia que requiere verificación de Instagram si está habilitada"""
    if site_config.instagram_required and not current_user.instagram_seguido:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Instagram verification required"
        )
    
    return current_user

# Dependencias para diferentes niveles de acceso
RequireAuth = Depends(get_current_user)
RequireOptionalAuth = Depends(get_current_user_optional)
RequireSiteAccess = Depends(require_site_access)
RequireActiveUser = Depends(require_active_user)
RequireVerifiedUser = Depends(require_verified_user)
RequireInstagramVerified = Depends(require_instagram_verified)
