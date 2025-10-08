from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.config import settings
from app.middleware.multitenant import MultiTenantMiddleware
from app.middleware.logging import LoggingMiddleware
from app.api import auth, users, stickers, videos, interactions, sites, instagram
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Create FastAPI application
app = FastAPI(
    title="Mariachi Fidelización Multi-Tenant API",
    description="Sistema de fidelización reutilizable para múltiples sitios",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.debug else ["mariachisoldelaguila.com", "*.mariachisoldelaguila.com"]
)

# Add multi-tenant middleware
app.add_middleware(MultiTenantMiddleware)

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Include routers
app.include_router(sites.router, prefix="/api/sites", tags=["sites"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(stickers.router, prefix="/api/stickers", tags=["stickers"])
app.include_router(videos.router, prefix="/api/videos", tags=["videos"])
app.include_router(interactions.router, prefix="/api/interactions", tags=["interactions"])
app.include_router(instagram.router, prefix="/api/instagram", tags=["instagram"])

@app.get("/")
async def root():
    return {
        "message": "Mariachi Fidelización Multi-Tenant API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "multi_tenant": settings.enable_multi_tenant}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
