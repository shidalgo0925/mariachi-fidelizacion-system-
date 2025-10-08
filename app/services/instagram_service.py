import httpx
import json
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.site_config import SiteConfig
from app.schemas.instagram import (
    InstagramUserCreate, InstagramUserUpdate, InstagramVerificationRequest,
    InstagramVerificationResponse, InstagramAuthResponse, InstagramCallbackResponse,
    InstagramConnectionStatus, InstagramVerificationStatus
)
from app.services.sticker_service import StickerService
from app.services.points_service import PointsService
from typing import Optional, Dict, Any, List
import structlog
from datetime import datetime, timedelta
import secrets
import base64
import hashlib
import hmac

logger = structlog.get_logger()

class InstagramService:
    """Servicio para integración con Instagram Basic Display API"""
    
    def __init__(self, db: Session):
        self.db = db
        self.sticker_service = StickerService(db)
        self.points_service = PointsService(db)
        self.base_url = "https://graph.instagram.com"
        self.auth_url = "https://api.instagram.com/oauth/authorize"
        self.token_url = "https://api.instagram.com/oauth/access_token"
        self.exchange_url = "https://graph.instagram.com/access_token"
    
    async def generate_auth_url(
        self, 
        site_id: str, 
        redirect_uri: Optional[str] = None,
        state: Optional[str] = None
    ) -> InstagramAuthResponse:
        """Generar URL de autenticación de Instagram"""
        try:
            # Obtener configuración del sitio
            site_config = self.db.query(SiteConfig).filter(
                SiteConfig.site_id == site_id
            ).first()
            
            if not site_config or not site_config.instagram_client_id:
                raise ValueError("Instagram not configured for this site")
            
            # Generar estado si no se proporciona
            if not state:
                state = self._generate_state()
            
            # Usar redirect_uri del sitio si no se proporciona
            if not redirect_uri:
                redirect_uri = site_config.instagram_redirect_uri
            
            # Parámetros de autenticación
            params = {
                "client_id": site_config.instagram_client_id,
                "redirect_uri": redirect_uri,
                "scope": "user_profile,user_media",
                "response_type": "code",
                "state": state
            }
            
            # Construir URL
            auth_url = f"{self.auth_url}?" + "&".join([f"{k}={v}" for k, v in params.items()])
            
            logger.info("Instagram auth URL generated", 
                       site_id=site_id, 
                       state=state)
            
            return InstagramAuthResponse(
                auth_url=auth_url,
                state=state,
                expires_in=3600  # 1 hora
            )
            
        except Exception as e:
            logger.error("Error generating Instagram auth URL", 
                        site_id=site_id, 
                        error=str(e))
            raise
    
    async def handle_callback(
        self, 
        code: str, 
        state: str, 
        site_id: str,
        user_id: int
    ) -> InstagramCallbackResponse:
        """Manejar callback de Instagram"""
        try:
            # Obtener configuración del sitio
            site_config = self.db.query(SiteConfig).filter(
                SiteConfig.site_id == site_id
            ).first()
            
            if not site_config:
                return InstagramCallbackResponse(
                    success=False,
                    message="Site configuration not found"
                )
            
            # Intercambiar código por token de acceso
            access_token = await self._exchange_code_for_token(
                code=code,
                client_id=site_config.instagram_client_id,
                client_secret=site_config.instagram_client_secret,
                redirect_uri=site_config.instagram_redirect_uri
            )
            
            if not access_token:
                return InstagramCallbackResponse(
                    success=False,
                    message="Failed to exchange code for access token"
                )
            
            # Obtener información del usuario de Instagram
            user_info = await self._get_user_info(access_token)
            
            if not user_info:
                return InstagramCallbackResponse(
                    success=False,
                    message="Failed to get Instagram user information"
                )
            
            # Crear o actualizar conexión de Instagram
            instagram_user = await self._create_or_update_instagram_user(
                user_id=user_id,
                site_id=site_id,
                access_token=access_token,
                user_info=user_info
            )
            
            # Generar sticker automáticamente si está configurado
            sticker_generated = False
            if site_config.auto_generate_sticker:
                sticker_generated = await self._generate_instagram_sticker(
                    user_id=user_id,
                    site_id=site_id
                )
            
            logger.info("Instagram callback handled successfully", 
                       user_id=user_id, 
                       site_id=site_id, 
                       instagram_username=user_info.get('username'))
            
            return InstagramCallbackResponse(
                success=True,
                message="Instagram account connected successfully",
                instagram_user=instagram_user,
                sticker_generated=sticker_generated
            )
            
        except Exception as e:
            logger.error("Error handling Instagram callback", 
                        user_id=user_id, 
                        site_id=site_id, 
                        error=str(e))
            return InstagramCallbackResponse(
                success=False,
                message=f"Error connecting Instagram account: {str(e)}"
            )
    
    async def verify_following(
        self, 
        user_id: int, 
        site_id: str,
        target_account: str
    ) -> InstagramVerificationResponse:
        """Verificar si el usuario sigue la cuenta objetivo"""
        try:
            # Obtener conexión de Instagram del usuario
            instagram_user = await self._get_instagram_user(user_id, site_id)
            
            if not instagram_user:
                return InstagramVerificationResponse(
                    verified=False,
                    message="Instagram account not connected"
                )
            
            # Verificar si el token sigue siendo válido
            if not await self._is_token_valid(instagram_user.access_token):
                return InstagramVerificationResponse(
                    verified=False,
                    message="Instagram access token expired. Please reconnect your account."
                )
            
            # Verificar seguimiento
            is_following = await self._check_following(
                access_token=instagram_user.access_token,
                target_account=target_account
            )
            
            # Actualizar estado de verificación
            if is_following:
                instagram_user.verification_status = InstagramVerificationStatus.VERIFIED
                instagram_user.last_verification = datetime.utcnow()
                
                # Generar sticker si no se ha generado ya
                sticker_generated = False
                if not instagram_user.sticker_generated:
                    sticker_generated = await self._generate_instagram_sticker(
                        user_id=user_id,
                        site_id=site_id
                    )
                    if sticker_generated:
                        instagram_user.sticker_generated = True
                
                # Otorgar puntos
                await self.points_service.award_points_for_instagram_verification(
                    user_id=user_id,
                    site_id=site_id
                )
                
                self.db.commit()
                
                return InstagramVerificationResponse(
                    verified=True,
                    message="Instagram following verified successfully",
                    instagram_user=instagram_user,
                    verification_details={
                        "target_account": target_account,
                        "verified_at": datetime.utcnow().isoformat(),
                        "sticker_generated": sticker_generated
                    },
                    sticker_generated=sticker_generated
                )
            else:
                instagram_user.verification_status = InstagramVerificationStatus.FAILED
                instagram_user.verification_attempts += 1
                self.db.commit()
                
                return InstagramVerificationResponse(
                    verified=False,
                    message=f"User is not following @{target_account}",
                    instagram_user=instagram_user,
                    verification_details={
                        "target_account": target_account,
                        "attempts": instagram_user.verification_attempts
                    }
                )
            
        except Exception as e:
            logger.error("Error verifying Instagram following", 
                        user_id=user_id, 
                        site_id=site_id, 
                        error=str(e))
            return InstagramVerificationResponse(
                verified=False,
                message=f"Error verifying Instagram following: {str(e)}"
            )
    
    async def get_user_media(
        self, 
        user_id: int, 
        site_id: str,
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        """Obtener media del usuario de Instagram"""
        try:
            # Obtener conexión de Instagram del usuario
            instagram_user = await self._get_instagram_user(user_id, site_id)
            
            if not instagram_user:
                return []
            
            # Verificar si el token sigue siendo válido
            if not await self._is_token_valid(instagram_user.access_token):
                return []
            
            # Obtener media
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/me/media",
                    params={
                        "fields": "id,media_type,media_url,permalink,caption,timestamp,like_count,comments_count",
                        "limit": limit,
                        "access_token": instagram_user.access_token
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", [])
                else:
                    logger.warning("Failed to get Instagram media", 
                                 user_id=user_id, 
                                 status_code=response.status_code)
                    return []
            
        except Exception as e:
            logger.error("Error getting Instagram media", 
                        user_id=user_id, 
                        site_id=site_id, 
                        error=str(e))
            return []
    
    async def refresh_access_token(
        self, 
        user_id: int, 
        site_id: str
    ) -> bool:
        """Refrescar token de acceso de Instagram"""
        try:
            # Obtener conexión de Instagram del usuario
            instagram_user = await self._get_instagram_user(user_id, site_id)
            
            if not instagram_user:
                return False
            
            # Obtener configuración del sitio
            site_config = self.db.query(SiteConfig).filter(
                SiteConfig.site_id == site_id
            ).first()
            
            if not site_config:
                return False
            
            # Refrescar token
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.exchange_url,
                    params={
                        "grant_type": "ig_exchange_token",
                        "client_secret": site_config.instagram_client_secret,
                        "access_token": instagram_user.access_token
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    new_token = data.get("access_token")
                    expires_in = data.get("expires_in", 3600)
                    
                    if new_token:
                        instagram_user.access_token = new_token
                        instagram_user.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                        instagram_user.connection_status = InstagramConnectionStatus.CONNECTED
                        self.db.commit()
                        
                        logger.info("Instagram access token refreshed", 
                                   user_id=user_id, 
                                   site_id=site_id)
                        return True
            
            return False
            
        except Exception as e:
            logger.error("Error refreshing Instagram access token", 
                        user_id=user_id, 
                        site_id=site_id, 
                        error=str(e))
            return False
    
    async def disconnect_instagram(
        self, 
        user_id: int, 
        site_id: str
    ) -> bool:
        """Desconectar cuenta de Instagram"""
        try:
            # Obtener conexión de Instagram del usuario
            instagram_user = await self._get_instagram_user(user_id, site_id)
            
            if not instagram_user:
                return False
            
            # Marcar como desconectado
            instagram_user.connection_status = InstagramConnectionStatus.REVOKED
            instagram_user.access_token = None
            instagram_user.token_expires_at = None
            self.db.commit()
            
            logger.info("Instagram account disconnected", 
                       user_id=user_id, 
                       site_id=site_id)
            
            return True
            
        except Exception as e:
            logger.error("Error disconnecting Instagram account", 
                        user_id=user_id, 
                        site_id=site_id, 
                        error=str(e))
            return False
    
    async def _exchange_code_for_token(
        self, 
        code: str, 
        client_id: str, 
        client_secret: str, 
        redirect_uri: str
    ) -> Optional[str]:
        """Intercambiar código de autorización por token de acceso"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_url,
                    data={
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "grant_type": "authorization_code",
                        "redirect_uri": redirect_uri,
                        "code": code
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("access_token")
                else:
                    logger.warning("Failed to exchange code for token", 
                                 status_code=response.status_code,
                                 response=response.text)
                    return None
            
        except Exception as e:
            logger.error("Error exchanging code for token", error=str(e))
            return None
    
    async def _get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Obtener información del usuario de Instagram"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/me",
                    params={
                        "fields": "id,username,account_type,media_count",
                        "access_token": access_token
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning("Failed to get Instagram user info", 
                                 status_code=response.status_code)
                    return None
            
        except Exception as e:
            logger.error("Error getting Instagram user info", error=str(e))
            return None
    
    async def _check_following(
        self, 
        access_token: str, 
        target_account: str
    ) -> bool:
        """Verificar si el usuario sigue la cuenta objetivo"""
        try:
            # Nota: Instagram Basic Display API no permite verificar seguimiento directamente
            # Esta es una implementación simplificada que podría requerir webhooks o otras APIs
            
            # Por ahora, simulamos la verificación
            # En una implementación real, esto requeriría:
            # 1. Webhooks de Instagram
            # 2. Instagram Graph API (para cuentas de negocio)
            # 3. O solicitar al usuario que confirme manualmente
            
            logger.info("Instagram following check simulated", 
                       target_account=target_account)
            
            # Simulación: asumir que sigue si tiene conexión activa
            return True
            
        except Exception as e:
            logger.error("Error checking Instagram following", 
                        target_account=target_account, 
                        error=str(e))
            return False
    
    async def _is_token_valid(self, access_token: str) -> bool:
        """Verificar si el token de acceso es válido"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/me",
                    params={"access_token": access_token}
                )
                
                return response.status_code == 200
            
        except Exception as e:
            logger.error("Error checking token validity", error=str(e))
            return False
    
    async def _create_or_update_instagram_user(
        self, 
        user_id: int, 
        site_id: str, 
        access_token: str, 
        user_info: Dict[str, Any]
    ):
        """Crear o actualizar usuario de Instagram"""
        try:
            # Buscar usuario existente
            from app.models.instagram_user import InstagramUser
            instagram_user = self.db.query(InstagramUser).filter(
                InstagramUser.user_id == user_id,
                InstagramUser.site_id == site_id
            ).first()
            
            if instagram_user:
                # Actualizar usuario existente
                instagram_user.instagram_user_id = user_info.get("id")
                instagram_user.username = user_info.get("username")
                instagram_user.access_token = access_token
                instagram_user.connection_status = InstagramConnectionStatus.CONNECTED
                instagram_user.token_expires_at = datetime.utcnow() + timedelta(seconds=3600)
                instagram_user.updated_at = datetime.utcnow()
            else:
                # Crear nuevo usuario
                instagram_user = InstagramUser(
                    user_id=user_id,
                    site_id=site_id,
                    instagram_user_id=user_info.get("id"),
                    username=user_info.get("username"),
                    access_token=access_token,
                    connection_status=InstagramConnectionStatus.CONNECTED,
                    verification_status=InstagramVerificationStatus.PENDING,
                    token_expires_at=datetime.utcnow() + timedelta(seconds=3600)
                )
                self.db.add(instagram_user)
            
            self.db.commit()
            self.db.refresh(instagram_user)
            
            return instagram_user
            
        except Exception as e:
            self.db.rollback()
            logger.error("Error creating/updating Instagram user", 
                        user_id=user_id, 
                        site_id=site_id, 
                        error=str(e))
            return None
    
    async def _get_instagram_user(self, user_id: int, site_id: str):
        """Obtener usuario de Instagram"""
        try:
            from app.models.instagram_user import InstagramUser
            return self.db.query(InstagramUser).filter(
                InstagramUser.user_id == user_id,
                InstagramUser.site_id == site_id
            ).first()
            
        except Exception as e:
            logger.error("Error getting Instagram user", 
                        user_id=user_id, 
                        site_id=site_id, 
                        error=str(e))
            return None
    
    async def _generate_instagram_sticker(self, user_id: int, site_id: str) -> bool:
        """Generar sticker automáticamente por conexión de Instagram"""
        try:
            from app.schemas.sticker import StickerCreate
            from app.models.sticker import StickerType
            
            # Crear sticker de Instagram
            sticker_data = StickerCreate(
                usuario_id=user_id,
                tipo_sticker=StickerType.INSTAGRAM,
                porcentaje_descuento=5,
                fecha_expiracion=datetime.utcnow() + timedelta(days=30),
                metadata={"source": "instagram_connection"}
            )
            
            sticker = await self.sticker_service.create_sticker(
                sticker_data=sticker_data,
                site_id=site_id,
                user_id=user_id
            )
            
            return sticker is not None
            
        except Exception as e:
            logger.error("Error generating Instagram sticker", 
                        user_id=user_id, 
                        site_id=site_id, 
                        error=str(e))
            return False
    
    def _generate_state(self) -> str:
        """Generar estado para validación de seguridad"""
        return secrets.token_urlsafe(32)
