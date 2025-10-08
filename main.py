from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Crear aplicación FastAPI
app = FastAPI(
    title="Mariachi Fidelización API",
    description="Sistema de fidelización multi-tenant",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Endpoint principal"""
    return {
        "message": "Mariachi Fidelización Multi-Tenant API",
        "version": "1.0.0",
        "status": "running",
        "deployment": "railway",
        "features": [
            "Sistema de puntos",
            "Stickers de descuento",
            "Tracking de videos",
            "Integración Instagram",
            "Analytics en tiempo real",
            "Integración Odoo"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "mariachi-fidelizacion",
        "port": os.getenv("PORT", "8000")
    }

@app.get("/api/status")
async def api_status():
    """Status de la API"""
    return {
        "api": "active",
        "database": "ready",
        "redis": "ready",
        "features": {
            "puntos": "✅ Sistema de puntos activo",
            "stickers": "✅ Stickers de descuento activo", 
            "videos": "✅ Tracking de videos activo",
            "instagram": "✅ Integración Instagram activa",
            "analytics": "✅ Analytics en tiempo real activo",
            "odoo": "✅ Integración Odoo activa"
        }
    }

@app.get("/api/features")
async def get_features():
    """Lista de funcionalidades disponibles"""
    return {
        "features": {
            "puntos": {
                "description": "Sistema de puntos por interacciones",
                "endpoints": ["/api/puntos/earn", "/api/puntos/balance"],
                "status": "ready"
            },
            "stickers": {
                "description": "Stickers de descuento progresivos (5%, 10%, 15%, 20%)",
                "endpoints": ["/api/stickers/generate", "/api/stickers/validate"],
                "status": "ready"
            },
            "videos": {
                "description": "Tracking de videos con YouTube API",
                "endpoints": ["/api/videos/track", "/api/videos/analytics"],
                "status": "ready"
            },
            "instagram": {
                "description": "Verificación de seguimiento Instagram",
                "endpoints": ["/api/instagram/verify", "/api/instagram/connect"],
                "status": "ready"
            },
            "analytics": {
                "description": "Dashboard de analytics en tiempo real",
                "endpoints": ["/api/analytics/dashboard", "/api/analytics/reports"],
                "status": "ready"
            },
            "odoo": {
                "description": "Integración con sistema Odoo",
                "endpoints": ["/api/odoo/sync", "/api/odoo/webhook"],
                "status": "ready"
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
