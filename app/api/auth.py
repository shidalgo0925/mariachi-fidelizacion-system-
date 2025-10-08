from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.site_config import SiteConfig
from app.schemas.user import UserCreate, UserResponse, UserLogin, TokenResponse
from app.services.user_service import UserService
from app.utils.security import SecurityUtils
from app.middleware.multitenant import MultiTenantMiddleware
import structlog

logger = structlog.get_logger()
security = HTTPBearer()

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Registrar nuevo usuario"""
    try:
        # Obtener configuración del sitio desde el middleware
        site_config = getattr(request.state, 'site_config', None)
        if not site_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Site configuration not found"
            )
        
        user_service = UserService(db)
        
        # Verificar si el usuario ya existe en este sitio
        existing_user = await user_service.get_user_by_email(user_data.email, site_config.site_id)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists in this site"
            )
        
        # Crear usuario
        user = await user_service.create_user(user_data, site_config.site_id)
        
        logger.info("User registered", user_id=user.id, site_id=site_config.site_id, email=user.email)
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error registering user", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error registering user"
        )

@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """Iniciar sesión de usuario"""
    try:
        # Obtener configuración del sitio
        site_config = getattr(request.state, 'site_config', None)
        if not site_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Site configuration not found"
            )
        
        user_service = UserService(db)
        
        # Verificar credenciales
        user = await user_service.authenticate_user(login_data.email, login_data.password, site_config.site_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Verificar que el usuario esté activo
        if not user.activo:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive"
            )
        
        # Crear tokens
        access_token = SecurityUtils.create_user_token(
            user_id=user.id,
            site_id=site_config.site_id,
            email=user.email
        )
        
        refresh_token = SecurityUtils.create_refresh_token({
            "sub": str(user.id),
            "site_id": site_config.site_id,
            "email": user.email
        })
        
        logger.info("User logged in", user_id=user.id, site_id=site_config.site_id, email=user.email)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error logging in user", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error logging in user"
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Renovar token de acceso"""
    try:
        # Verificar token de refresh
        payload = SecurityUtils.verify_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
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
        if not user or not user.activo:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Crear nuevo token de acceso
        access_token = SecurityUtils.create_user_token(
            user_id=user.id,
            site_id=site_config.site_id,
            email=user.email
        )
        
        logger.info("Token refreshed", user_id=user.id, site_id=site_config.site_id)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,  # Mantener el mismo refresh token
            token_type="bearer",
            user=UserResponse.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error refreshing token", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error refreshing token"
        )

@router.post("/logout")
async def logout_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None
):
    """Cerrar sesión de usuario"""
    try:
        # En un sistema más complejo, aquí se invalidaría el token
        # Por ahora, solo logueamos la acción
        token = credentials.credentials
        payload = SecurityUtils.verify_token(token)
        
        logger.info("User logged out", user_id=payload.get("sub"), site_id=payload.get("site_id"))
        
        return {"message": "Successfully logged out"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error logging out user", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error logging out user"
        )

@router.get("/verify")
async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None
):
    """Verificar token de acceso"""
    try:
        token = credentials.credentials
        payload = SecurityUtils.verify_token(token)
        
        # Obtener configuración del sitio
        site_config = getattr(request.state, 'site_config', None)
        if site_config:
            # Validar acceso al sitio
            if not SecurityUtils.validate_site_access(payload, site_config.site_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied for this site"
                )
        
        return {
            "valid": True,
            "user_id": payload.get("sub"),
            "site_id": payload.get("site_id"),
            "email": payload.get("email")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error verifying token", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error verifying token"
        )

@router.post("/forgot-password")
async def forgot_password(
    email: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Solicitar reset de contraseña"""
    try:
        # Obtener configuración del sitio
        site_config = getattr(request.state, 'site_config', None)
        if not site_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Site configuration not found"
            )
        
        user_service = UserService(db)
        user = await user_service.get_user_by_email(email, site_config.site_id)
        
        if user:
            # Generar token de reset
            reset_token = SecurityUtils.generate_password_reset_token(email, site_config.site_id)
            
            # Aquí se enviaría el email con el token
            # Por ahora, solo logueamos
            logger.info("Password reset requested", email=email, site_id=site_config.site_id)
        
        # Siempre retornar éxito por seguridad
        return {"message": "If the email exists, a reset link has been sent"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error requesting password reset", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error requesting password reset"
        )

@router.post("/reset-password")
async def reset_password(
    token: str,
    new_password: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Resetear contraseña con token"""
    try:
        # Verificar token
        payload = SecurityUtils.verify_password_reset_token(token)
        
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
        
        # Actualizar contraseña
        user_service = UserService(db)
        success = await user_service.update_password(payload["sub"], new_password, site_config.site_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )
        
        logger.info("Password reset completed", email=payload["sub"], site_id=site_config.site_id)
        
        return {"message": "Password reset successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error resetting password", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error resetting password"
        )
