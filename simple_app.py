from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Crear aplicación FastAPI simplificada
app = FastAPI(
    title="Mariachi Fidelización API",
    description="Sistema de fidelización multi-tenant simplificado",
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
    return {"status": "healthy", "service": "mariachi-fidelizacion"}

@app.get("/api/features")
async def get_features():
    """Lista de funcionalidades disponibles"""
    return {
        "features": {
            "puntos": {
                "description": "Sistema de puntos por interacciones",
                "endpoints": ["/api/puntos/earn", "/api/puntos/balance"]
            },
            "stickers": {
                "description": "Stickers de descuento progresivos",
                "endpoints": ["/api/stickers/generate", "/api/stickers/validate"]
            },
            "videos": {
                "description": "Tracking de videos con YouTube",
                "endpoints": ["/api/videos/track", "/api/videos/analytics"]
            },
            "instagram": {
                "description": "Verificación de seguimiento Instagram",
                "endpoints": ["/api/instagram/verify", "/api/instagram/connect"]
            },
            "analytics": {
                "description": "Dashboard de analytics en tiempo real",
                "endpoints": ["/api/analytics/dashboard", "/api/analytics/reports"]
            },
            "odoo": {
                "description": "Integración con sistema Odoo",
                "endpoints": ["/api/odoo/sync", "/api/odoo/webhook"]
            }
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
