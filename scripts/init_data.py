#!/usr/bin/env python3
"""
Script de inicialización de datos para el sistema de fidelización multi-tenant
"""

import asyncio
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Base, SiteConfig, User, Sticker, Video, NotificationTemplate
from app.utils.security import get_password_hash
from app.services.default_config_service import DefaultConfigService
import structlog

logger = structlog.get_logger()

async def create_tables():
    """Crear todas las tablas"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tables created successfully")
    except Exception as e:
        logger.error("Error creating tables", error=str(e))
        raise

async def create_default_site_config():
    """Crear configuración por defecto para Mariachi Sol del Águila"""
    try:
        db = SessionLocal()
        
        # Verificar si ya existe
        existing_config = db.query(SiteConfig).filter(
            SiteConfig.site_id == "mariachi-sol-aguila"
        ).first()
        
        if existing_config:
            logger.info("Site config already exists", site_id="mariachi-sol-aguila")
            db.close()
            return existing_config
        
        # Obtener configuración por defecto para mariachi
        default_config = DefaultConfigService.get_default_config("mariachi")
        
        # Crear configuración del sitio
        site_config = SiteConfig(
            site_id="mariachi-sol-aguila",
            site_name="Mariachi Sol del Águila",
            site_type="mariachi",
            **default_config
        )
        
        db.add(site_config)
        db.commit()
        db.refresh(site_config)
        
        logger.info("Default site config created", 
                   site_id=site_config.site_id, 
                   site_name=site_config.site_name)
        
        db.close()
        return site_config
        
    except Exception as e:
        logger.error("Error creating default site config", error=str(e))
        db.rollback()
        db.close()
        raise

async def create_test_users():
    """Crear usuarios de prueba"""
    try:
        db = SessionLocal()
        
        # Obtener configuración del sitio
        site_config = db.query(SiteConfig).filter(
            SiteConfig.site_id == "mariachi-sol-aguila"
        ).first()
        
        if not site_config:
            logger.error("Site config not found")
            db.close()
            return
        
        # Usuarios de prueba
        test_users = [
            {
                "nombre": "Juan Pérez",
                "email": "juan.perez@example.com",
                "telefono": "+50761234567",
                "puntos_acumulados": 150,
                "instagram_seguido": True,
                "reseñas_dejadas": 2,
                "videos_completados": 3,
                "total_descuento": 15
            },
            {
                "nombre": "María González",
                "email": "maria.gonzalez@example.com",
                "telefono": "+50767654321",
                "puntos_acumulados": 75,
                "instagram_seguido": False,
                "reseñas_dejadas": 1,
                "videos_completados": 1,
                "total_descuento": 5
            },
            {
                "nombre": "Carlos Rodríguez",
                "email": "carlos.rodriguez@example.com",
                "telefono": "+50769876543",
                "puntos_acumulados": 200,
                "instagram_seguido": True,
                "reseñas_dejadas": 3,
                "videos_completados": 5,
                "total_descuento": 25
            }
        ]
        
        created_users = []
        for user_data in test_users:
            # Verificar si el usuario ya existe
            existing_user = db.query(User).filter(
                User.email == user_data["email"]
            ).first()
            
            if existing_user:
                logger.info("User already exists", email=user_data["email"])
                continue
            
            # Crear usuario
            user = User(
                site_config_id=site_config.id,
                nombre=user_data["nombre"],
                email=user_data["email"],
                password_hash=get_password_hash("password123"),
                telefono=user_data["telefono"],
                puntos_acumulados=user_data["puntos_acumulados"],
                instagram_seguido=user_data["instagram_seguido"],
                reseñas_dejadas=user_data["reseñas_dejadas"],
                videos_completados=user_data["videos_completados"],
                total_descuento=user_data["total_descuento"]
            )
            
            db.add(user)
            created_users.append(user)
        
        db.commit()
        
        for user in created_users:
            db.refresh(user)
            logger.info("Test user created", 
                       user_id=user.id, 
                       email=user.email, 
                       nombre=user.nombre)
        
        db.close()
        
    except Exception as e:
        logger.error("Error creating test users", error=str(e))
        db.rollback()
        db.close()
        raise

async def create_test_videos():
    """Crear videos de prueba"""
    try:
        db = SessionLocal()
        
        # Obtener configuración del sitio
        site_config = db.query(SiteConfig).filter(
            SiteConfig.site_id == "mariachi-sol-aguila"
        ).first()
        
        if not site_config:
            logger.error("Site config not found")
            db.close()
            return
        
        # Videos de prueba
        test_videos = [
            {
                "orden": 1,
                "titulo": "Serenata para Mamá",
                "descripcion": "Una hermosa serenata dedicada a todas las madres",
                "youtube_id": "dQw4w9WgXcQ",
                "duracion_segundos": 213,
                "puntos_por_completar": 10
            },
            {
                "orden": 2,
                "titulo": "Las Mañanitas",
                "descripcion": "La canción tradicional de cumpleaños",
                "youtube_id": "dQw4w9WgXcQ",
                "duracion_segundos": 180,
                "puntos_por_completar": 10
            },
            {
                "orden": 3,
                "titulo": "Cielito Lindo",
                "descripcion": "Una de las canciones más populares del mariachi",
                "youtube_id": "dQw4w9WgXcQ",
                "duracion_segundos": 165,
                "puntos_por_completar": 10
            },
            {
                "orden": 4,
                "titulo": "El Rey",
                "descripcion": "Clásico de José Alfredo Jiménez",
                "youtube_id": "dQw4w9WgXcQ",
                "duracion_segundos": 195,
                "puntos_por_completar": 15
            },
            {
                "orden": 5,
                "titulo": "La Bikina",
                "descripcion": "Ranchera tradicional mexicana",
                "youtube_id": "dQw4w9WgXcQ",
                "duracion_segundos": 210,
                "puntos_por_completar": 15
            }
        ]
        
        created_videos = []
        for video_data in test_videos:
            # Verificar si el video ya existe
            existing_video = db.query(Video).filter(
                Video.site_config_id == site_config.id,
                Video.orden == video_data["orden"]
            ).first()
            
            if existing_video:
                logger.info("Video already exists", 
                           orden=video_data["orden"], 
                           titulo=video_data["titulo"])
                continue
            
            # Crear video
            video = Video(
                site_config_id=site_config.id,
                orden=video_data["orden"],
                titulo=video_data["titulo"],
                descripcion=video_data["descripcion"],
                youtube_id=video_data["youtube_id"],
                duracion_segundos=video_data["duracion_segundos"],
                puntos_por_completar=video_data["puntos_por_completar"]
            )
            
            db.add(video)
            created_videos.append(video)
        
        db.commit()
        
        for video in created_videos:
            db.refresh(video)
            logger.info("Test video created", 
                       video_id=video.id, 
                       titulo=video.titulo, 
                       orden=video.orden)
        
        db.close()
        
    except Exception as e:
        logger.error("Error creating test videos", error=str(e))
        db.rollback()
        db.close()
        raise

async def create_notification_templates():
    """Crear templates de notificación por defecto"""
    try:
        db = SessionLocal()
        
        # Obtener configuración del sitio
        site_config = db.query(SiteConfig).filter(
            SiteConfig.site_id == "mariachi-sol-aguila"
        ).first()
        
        if not site_config:
            logger.error("Site config not found")
            db.close()
            return
        
        # Templates de notificación
        templates = [
            {
                "name": "Bienvenida",
                "type": "email",
                "subject": "¡Bienvenido al Mariachi Sol del Águila!",
                "content": """
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2>¡Hola {{ user_name }}!</h2>
                    <p>¡Bienvenido al sistema de fidelización del Mariachi Sol del Águila!</p>
                    <p>Comienza a ganar puntos y descuentos participando en nuestras actividades:</p>
                    <ul>
                        <li>Ver videos de nuestro repertorio</li>
                        <li>Seguirnos en Instagram</li>
                        <li>Dejar reseñas</li>
                        <li>Interactuar con nuestro contenido</li>
                    </ul>
                    <p>¡Disfruta de tu experiencia musical!</p>
                    <p>El equipo del Mariachi Sol del Águila</p>
                </body>
                </html>
                """,
                "variables": ["user_name"]
            },
            {
                "name": "Sticker Generado",
                "type": "email",
                "subject": "¡Tu sticker de descuento está listo!",
                "content": """
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2>¡Felicidades {{ user_name }}!</h2>
                    <p>Has generado un sticker de descuento del {{ discount_percentage }}%</p>
                    <p><strong>Código:</strong> {{ discount_code }}</p>
                    <p>Válido hasta: {{ expiration_date }}</p>
                    <p>¡Disfruta de tu descuento en tu próxima serenata!</p>
                    <p>El equipo del Mariachi Sol del Águila</p>
                </body>
                </html>
                """,
                "variables": ["user_name", "discount_percentage", "discount_code", "expiration_date"]
            },
            {
                "name": "Puntos Ganados",
                "type": "in_app",
                "subject": None,
                "content": "¡Has ganado {{ points }} puntos por {{ reason }}! Total: {{ total_points }} puntos",
                "variables": ["points", "reason", "total_points"]
            }
        ]
        
        created_templates = []
        for template_data in templates:
            # Verificar si el template ya existe
            existing_template = db.query(NotificationTemplate).filter(
                NotificationTemplate.site_id == site_config.site_id,
                NotificationTemplate.name == template_data["name"]
            ).first()
            
            if existing_template:
                logger.info("Template already exists", 
                           name=template_data["name"])
                continue
            
            # Crear template
            template = NotificationTemplate(
                site_id=site_config.site_id,
                name=template_data["name"],
                type=template_data["type"],
                subject=template_data["subject"],
                content=template_data["content"],
                variables=template_data["variables"]
            )
            
            db.add(template)
            created_templates.append(template)
        
        db.commit()
        
        for template in created_templates:
            db.refresh(template)
            logger.info("Notification template created", 
                       template_id=template.id, 
                       name=template.name, 
                       type=template.type)
        
        db.close()
        
    except Exception as e:
        logger.error("Error creating notification templates", error=str(e))
        db.rollback()
        db.close()
        raise

async def main():
    """Función principal de inicialización"""
    try:
        logger.info("Starting data initialization...")
        
        # Crear tablas
        await create_tables()
        
        # Crear configuración por defecto
        await create_default_site_config()
        
        # Crear usuarios de prueba
        await create_test_users()
        
        # Crear videos de prueba
        await create_test_videos()
        
        # Crear templates de notificación
        await create_notification_templates()
        
        logger.info("Data initialization completed successfully!")
        
    except Exception as e:
        logger.error("Error during initialization", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
