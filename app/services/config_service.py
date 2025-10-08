from sqlalchemy.orm import Session
from app.models.site_config import SiteConfig, SiteType
from app.schemas.site_config import SiteConfigCreate, SiteConfigUpdate
from typing import Optional, Dict, Any
import structlog

logger = structlog.get_logger()

class ConfigService:
    """Servicio para manejar configuraciones de sitios"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_site_config(self, site_id: str) -> Optional[SiteConfig]:
        """Obtener configuración de un sitio"""
        try:
            site_config = self.db.query(SiteConfig).filter(
                SiteConfig.site_id == site_id,
                SiteConfig.activo == True
            ).first()
            
            if site_config:
                logger.info("Site config retrieved", site_id=site_id, site_name=site_config.site_name)
            else:
                logger.warning("Site config not found", site_id=site_id)
            
            return site_config
        except Exception as e:
            logger.error("Error getting site config", site_id=site_id, error=str(e))
            return None
    
    async def create_site_config(self, config_data: SiteConfigCreate) -> SiteConfig:
        """Crear nueva configuración de sitio"""
        try:
            # Aplicar configuración por defecto según tipo de sitio
            default_config = self._get_default_config(config_data.site_type)
            
            # Combinar configuración por defecto con datos proporcionados
            config_dict = config_data.dict()
            final_config = {**default_config, **config_dict}
            
            # Crear objeto SiteConfig
            site_config = SiteConfig(**final_config)
            
            self.db.add(site_config)
            self.db.commit()
            self.db.refresh(site_config)
            
            logger.info("Site config created", site_id=site_config.site_id, site_name=site_config.site_name)
            return site_config
            
        except Exception as e:
            self.db.rollback()
            logger.error("Error creating site config", error=str(e))
            raise
    
    async def update_site_config(self, site_id: str, config_data: SiteConfigUpdate) -> Optional[SiteConfig]:
        """Actualizar configuración de sitio"""
        try:
            site_config = await self.get_site_config(site_id)
            if not site_config:
                return None
            
            # Actualizar campos proporcionados
            update_data = config_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(site_config, field, value)
            
            self.db.commit()
            self.db.refresh(site_config)
            
            logger.info("Site config updated", site_id=site_id)
            return site_config
            
        except Exception as e:
            self.db.rollback()
            logger.error("Error updating site config", site_id=site_id, error=str(e))
            raise
    
    async def delete_site_config(self, site_id: str) -> bool:
        """Eliminar configuración de sitio (soft delete)"""
        try:
            site_config = await self.get_site_config(site_id)
            if not site_config:
                return False
            
            site_config.activo = False
            self.db.commit()
            
            logger.info("Site config deactivated", site_id=site_id)
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error("Error deleting site config", site_id=site_id, error=str(e))
            raise
    
    async def list_site_configs(self, active_only: bool = True) -> list[SiteConfig]:
        """Listar todas las configuraciones de sitios"""
        try:
            query = self.db.query(SiteConfig)
            if active_only:
                query = query.filter(SiteConfig.activo == True)
            
            site_configs = query.all()
            logger.info("Site configs listed", count=len(site_configs))
            return site_configs
            
        except Exception as e:
            logger.error("Error listing site configs", error=str(e))
            raise
    
    def _get_default_config(self, site_type: SiteType) -> Dict[str, Any]:
        """Obtener configuración por defecto según tipo de sitio"""
        
        default_configs = {
            SiteType.MARIACHI: {
                "primary_color": "#e74c3c",
                "secondary_color": "#2c3e50",
                "max_discount_percentage": 15,
                "discount_per_action": 5,
                "sticker_expiration_days": 30,
                "points_per_video": 10,
                "points_per_like": 1,
                "points_per_comment": 2,
                "points_per_review": 5,
                "video_progression_enabled": True,
                "instagram_required": True,
                "welcome_message": "¡Bienvenido a Mariachi Sol del Águila! Obtén descuentos especiales registrándote.",
                "sticker_message": "¡Gracias por elegir Mariachi Sol del Águila! Disfruta tu descuento.",
                "video_completion_message": "¡Excelente! Has completado el video. Continúa para obtener más descuentos."
            },
            SiteType.RESTAURANT: {
                "primary_color": "#ff6b35",
                "secondary_color": "#004e89",
                "max_discount_percentage": 20,
                "discount_per_action": 5,
                "sticker_expiration_days": 30,
                "points_per_video": 10,
                "points_per_like": 1,
                "points_per_comment": 2,
                "points_per_review": 5,
                "video_progression_enabled": True,
                "instagram_required": True,
                "welcome_message": "¡Bienvenido a nuestro restaurante! Obtén descuentos especiales registrándote.",
                "sticker_message": "¡Disfruta de tu descuento en nuestro restaurante!",
                "video_completion_message": "¡Gracias por ver nuestro video! Continúa para obtener más descuentos."
            },
            SiteType.ECOMMERCE: {
                "primary_color": "#007bff",
                "secondary_color": "#6c757d",
                "max_discount_percentage": 25,
                "discount_per_action": 5,
                "sticker_expiration_days": 30,
                "points_per_video": 10,
                "points_per_like": 1,
                "points_per_comment": 2,
                "points_per_review": 5,
                "video_progression_enabled": True,
                "instagram_required": False,
                "welcome_message": "¡Bienvenido a nuestra tienda! Obtén descuentos especiales registrándote.",
                "sticker_message": "¡Aprovecha tu descuento en nuestra tienda!",
                "video_completion_message": "¡Gracias por ver nuestro video! Continúa para obtener más descuentos."
            },
            SiteType.SERVICES: {
                "primary_color": "#28a745",
                "secondary_color": "#343a40",
                "max_discount_percentage": 15,
                "discount_per_action": 5,
                "sticker_expiration_days": 30,
                "points_per_video": 10,
                "points_per_like": 1,
                "points_per_comment": 2,
                "points_per_review": 5,
                "video_progression_enabled": True,
                "instagram_required": False,
                "welcome_message": "¡Bienvenido a nuestros servicios! Obtén descuentos especiales registrándote.",
                "sticker_message": "¡Disfruta de tu descuento en nuestros servicios!",
                "video_completion_message": "¡Gracias por ver nuestro video! Continúa para obtener más descuentos."
            },
            SiteType.GENERAL: {
                "primary_color": "#6f42c1",
                "secondary_color": "#495057",
                "max_discount_percentage": 10,
                "discount_per_action": 5,
                "sticker_expiration_days": 30,
                "points_per_video": 10,
                "points_per_like": 1,
                "points_per_comment": 2,
                "points_per_review": 5,
                "video_progression_enabled": False,
                "instagram_required": False,
                "welcome_message": "¡Bienvenido! Obtén descuentos especiales registrándote.",
                "sticker_message": "¡Disfruta de tu descuento!",
                "video_completion_message": "¡Gracias por ver nuestro video!"
            }
        }
        
        return default_configs.get(site_type, default_configs[SiteType.GENERAL])
    
    async def validate_site_config(self, site_id: str) -> Dict[str, Any]:
        """Validar configuración de sitio y retornar estado"""
        try:
            site_config = await self.get_site_config(site_id)
            if not site_config:
                return {"valid": False, "errors": ["Site not found"]}
            
            errors = []
            warnings = []
            
            # Validaciones básicas
            if not site_config.site_name:
                errors.append("Site name is required")
            
            if not site_config.primary_color:
                errors.append("Primary color is required")
            
            if site_config.max_discount_percentage > 50:
                warnings.append("Max discount percentage is very high")
            
            if site_config.instagram_required and not site_config.instagram_client_id:
                warnings.append("Instagram is required but client ID not configured")
            
            if site_config.odoo_integration and not site_config.odoo_url:
                warnings.append("Odoo integration enabled but URL not configured")
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "site_config": site_config
            }
            
        except Exception as e:
            logger.error("Error validating site config", site_id=site_id, error=str(e))
            return {"valid": False, "errors": [f"Validation error: {str(e)}"]}
