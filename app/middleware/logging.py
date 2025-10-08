from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import structlog

logger = structlog.get_logger()

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logging estructurado de requests"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Obtener información del request
        site_id = getattr(request.state, 'site_id', None)
        site_name = getattr(request.state.site_config, 'site_name', None) if hasattr(request.state, 'site_config') and request.state.site_config else None
        
        # Log del request
        logger.info(
            "Request started",
            method=request.method,
            url=str(request.url),
            site_id=site_id,
            site_name=site_name,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        # Procesar request
        response = await call_next(request)
        
        # Calcular tiempo de procesamiento
        process_time = time.time() - start_time
        
        # Log del response
        logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=round(process_time, 4),
            site_id=site_id,
            site_name=site_name
        )
        
        # Agregar header con tiempo de procesamiento
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
