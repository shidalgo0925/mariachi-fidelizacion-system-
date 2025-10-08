from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.database import SessionLocal
from app.models.site_config import SiteConfig
from app.config import settings
import structlog

logger = structlog.get_logger()

class MultiTenantMiddleware(BaseHTTPMiddleware):
    """Middleware para manejar multi-tenancy basado en headers o subdominios"""
    
    async def dispatch(self, request: Request, call_next):
        # Obtener site_id desde header o subdominio
        site_id = self._get_site_id(request)
        
        if site_id:
            # Validar que el sitio existe y está activo
            site_config = await self._get_site_config(site_id)
            if not site_config:
                raise HTTPException(
                    status_code=404,
                    detail=f"Site '{site_id}' not found or inactive"
                )
            
            # Agregar configuración del sitio al request
            request.state.site_config = site_config
            request.state.site_id = site_id
            
            logger.info("Site identified", site_id=site_id, site_name=site_config.site_name)
        else:
            # Usar configuración por defecto si no se especifica sitio
            if settings.enable_multi_tenant:
                logger.warning("No site_id provided in multi-tenant mode")
            request.state.site_config = None
            request.state.site_id = None
        
        response = await call_next(request)
        return response
    
    def _get_site_id(self, request: Request) -> str:
        """Obtener site_id desde header X-Site-ID o subdominio"""
        
        # Prioridad 1: Header X-Site-ID
        site_id = request.headers.get("X-Site-ID")
        if site_id:
            return site_id
        
        # Prioridad 2: Subdominio
        host = request.headers.get("host", "")
        if "." in host:
            subdomain = host.split(".")[0]
            if subdomain not in ["www", "api", "admin"]:
                return subdomain
        
        # Prioridad 3: Query parameter (para testing)
        site_id = request.query_params.get("site_id")
        if site_id:
            return site_id
        
        return None
    
    async def _get_site_config(self, site_id: str) -> SiteConfig:
        """Obtener configuración del sitio desde la base de datos"""
        db = SessionLocal()
        try:
            site_config = db.query(SiteConfig).filter(
                SiteConfig.site_id == site_id,
                SiteConfig.activo == True
            ).first()
            return site_config
        except Exception as e:
            logger.error("Error getting site config", site_id=site_id, error=str(e))
            return None
        finally:
            db.close()
