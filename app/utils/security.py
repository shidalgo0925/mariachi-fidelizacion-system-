from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from app.config import settings
import structlog

logger = structlog.get_logger()

# Configurar contexto de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class SecurityUtils:
    """Utilidades de seguridad para autenticación y autorización"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verificar contraseña"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Obtener hash de contraseña"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Crear token de acceso JWT"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        
        try:
            encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
            logger.info("Access token created", user_id=data.get("sub"), site_id=data.get("site_id"))
            return encoded_jwt
        except Exception as e:
            logger.error("Error creating access token", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating access token"
            )
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """Crear token de refresh"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)  # Refresh token válido por 7 días
        to_encode.update({"exp": expire, "type": "refresh"})
        
        try:
            encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
            logger.info("Refresh token created", user_id=data.get("sub"), site_id=data.get("site_id"))
            return encoded_jwt
        except Exception as e:
            logger.error("Error creating refresh token", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating refresh token"
            )
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verificar y decodificar token JWT"""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            
            # Verificar que el token no haya expirado
            exp = payload.get("exp")
            if exp is None or datetime.utcnow() > datetime.fromtimestamp(exp):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Verificar campos requeridos
            user_id = payload.get("sub")
            site_id = payload.get("site_id")
            
            if user_id is None or site_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            logger.info("Token verified", user_id=user_id, site_id=site_id)
            return payload
            
        except JWTError as e:
            logger.error("JWT error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error("Token verification error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    def create_user_token(user_id: int, site_id: str, email: str, additional_data: Optional[Dict[str, Any]] = None) -> str:
        """Crear token específico para usuario"""
        data = {
            "sub": str(user_id),
            "site_id": site_id,
            "email": email,
            "type": "access"
        }
        
        if additional_data:
            data.update(additional_data)
        
        return SecurityUtils.create_access_token(data)
    
    @staticmethod
    def create_site_token(site_id: str, additional_data: Optional[Dict[str, Any]] = None) -> str:
        """Crear token específico para sitio (para operaciones del sistema)"""
        data = {
            "sub": f"site_{site_id}",
            "site_id": site_id,
            "type": "site_access"
        }
        
        if additional_data:
            data.update(additional_data)
        
        return SecurityUtils.create_access_token(data)
    
    @staticmethod
    def extract_token_from_header(authorization: str) -> str:
        """Extraer token del header Authorization"""
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return token
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    def validate_site_access(token_payload: Dict[str, Any], required_site_id: str) -> bool:
        """Validar que el token tiene acceso al sitio requerido"""
        token_site_id = token_payload.get("site_id")
        
        if token_site_id != required_site_id:
            logger.warning("Site access denied", 
                         token_site_id=token_site_id, 
                         required_site_id=required_site_id)
            return False
        
        return True
    
    @staticmethod
    def validate_user_ownership(token_payload: Dict[str, Any], user_id: int) -> bool:
        """Validar que el token pertenece al usuario especificado"""
        token_user_id = token_payload.get("sub")
        
        if str(user_id) != token_user_id:
            logger.warning("User ownership denied", 
                         token_user_id=token_user_id, 
                         required_user_id=user_id)
            return False
        
        return True
    
    @staticmethod
    def generate_password_reset_token(email: str, site_id: str) -> str:
        """Generar token para reset de contraseña"""
        data = {
            "sub": email,
            "site_id": site_id,
            "type": "password_reset",
            "exp": datetime.utcnow() + timedelta(hours=1)  # Válido por 1 hora
        }
        
        return jwt.encode(data, settings.secret_key, algorithm=settings.algorithm)
    
    @staticmethod
    def verify_password_reset_token(token: str) -> Dict[str, Any]:
        """Verificar token de reset de contraseña"""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            
            if payload.get("type") != "password_reset":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token type"
                )
            
            return payload
            
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
    
    @staticmethod
    def generate_email_verification_token(email: str, site_id: str) -> str:
        """Generar token para verificación de email"""
        data = {
            "sub": email,
            "site_id": site_id,
            "type": "email_verification",
            "exp": datetime.utcnow() + timedelta(days=1)  # Válido por 1 día
        }
        
        return jwt.encode(data, settings.secret_key, algorithm=settings.algorithm)
    
    @staticmethod
    def verify_email_verification_token(token: str) -> Dict[str, Any]:
        """Verificar token de verificación de email"""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            
            if payload.get("type") != "email_verification":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token type"
                )
            
            return payload
            
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
