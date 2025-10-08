from app.models.site_config import SiteConfig, SiteType
from app.schemas.site_config import SiteConfigCreate
from typing import Dict, Any, List
import structlog

logger = structlog.get_logger()

class DefaultConfigService:
    """Servicio para manejar configuraciones por defecto"""
    
    @staticmethod
    def get_default_configs() -> Dict[SiteType, Dict[str, Any]]:
        """Obtener todas las configuraciones por defecto"""
        return {
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
                "welcome_message": "¡Bienvenido a Mariachi Sol del Águila! Obtén descuentos especiales registrándote y completando nuestras actividades.",
                "sticker_message": "¡Gracias por elegir Mariachi Sol del Águila! Disfruta tu descuento en nuestros servicios de música en vivo.",
                "video_completion_message": "¡Excelente! Has completado el video. Continúa viendo más videos para obtener descuentos adicionales.",
                "email_signature": "Mariachi Sol del Águila - Música en Vivo para tus Eventos Especiales"
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
                "welcome_message": "¡Bienvenido a nuestro restaurante! Obtén descuentos especiales registrándote y conociendo nuestros platos.",
                "sticker_message": "¡Disfruta de tu descuento en nuestro restaurante! Ven y prueba nuestros deliciosos platos.",
                "video_completion_message": "¡Gracias por ver nuestro video! Descubre más sobre nuestros platos y obtén descuentos adicionales.",
                "email_signature": "Restaurante - Sabores que Despiertan tus Sentidos"
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
                "welcome_message": "¡Bienvenido a nuestra tienda online! Obtén descuentos especiales registrándote y conociendo nuestros productos.",
                "sticker_message": "¡Aprovecha tu descuento en nuestra tienda! Encuentra los mejores productos al mejor precio.",
                "video_completion_message": "¡Gracias por ver nuestro video! Descubre más productos y obtén descuentos adicionales.",
                "email_signature": "Tienda Online - Productos de Calidad al Mejor Precio"
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
                "welcome_message": "¡Bienvenido a nuestros servicios! Obtén descuentos especiales registrándote y conociendo lo que ofrecemos.",
                "sticker_message": "¡Disfruta de tu descuento en nuestros servicios! Contamos con profesionales altamente capacitados.",
                "video_completion_message": "¡Gracias por ver nuestro video! Conoce más sobre nuestros servicios y obtén descuentos adicionales.",
                "email_signature": "Servicios Profesionales - Calidad y Confianza Garantizada"
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
                "welcome_message": "¡Bienvenido! Obtén descuentos especiales registrándote y participando en nuestras actividades.",
                "sticker_message": "¡Disfruta de tu descuento! Gracias por elegirnos.",
                "video_completion_message": "¡Gracias por ver nuestro video!",
                "email_signature": "Equipo de Atención al Cliente"
            }
        }
    
    @staticmethod
    def get_default_config(site_type: SiteType) -> Dict[str, Any]:
        """Obtener configuración por defecto para un tipo específico"""
        configs = DefaultConfigService.get_default_configs()
        return configs.get(site_type, configs[SiteType.GENERAL])
    
    @staticmethod
    def create_default_site_configs() -> List[SiteConfigCreate]:
        """Crear configuraciones por defecto para todos los tipos de sitio"""
        default_configs = []
        
        # Configuración para Mariachi Sol del Águila
        mariachi_config = SiteConfigCreate(
            site_id="mariachi-sol-aguila",
            site_name="Mariachi Sol del Águila",
            site_type=SiteType.MARIACHI,
            youtube_playlist_id="PL_MARIACHI_VIDEOS",  # Reemplazar con ID real
            allowed_domains=["mariachisoldelaguila.com", "www.mariachisoldelaguila.com"],
            **DefaultConfigService.get_default_config(SiteType.MARIACHI)
        )
        default_configs.append(mariachi_config)
        
        # Configuración de ejemplo para restaurante
        restaurant_config = SiteConfigCreate(
            site_id="mi-restaurante-ejemplo",
            site_name="Mi Restaurante",
            site_type=SiteType.RESTAURANT,
            youtube_playlist_id="PL_RESTAURANT_VIDEOS",  # Reemplazar con ID real
            allowed_domains=["mirestaurante.com", "www.mirestaurante.com"],
            **DefaultConfigService.get_default_config(SiteType.RESTAURANT)
        )
        default_configs.append(restaurant_config)
        
        # Configuración de ejemplo para ecommerce
        ecommerce_config = SiteConfigCreate(
            site_id="mi-tienda-ejemplo",
            site_name="Mi Tienda Online",
            site_type=SiteType.ECOMMERCE,
            youtube_playlist_id="PL_ECOMMERCE_VIDEOS",  # Reemplazar con ID real
            allowed_domains=["mitienda.com", "www.mitienda.com"],
            **DefaultConfigService.get_default_config(SiteType.ECOMMERCE)
        )
        default_configs.append(ecommerce_config)
        
        return default_configs
    
    @staticmethod
    def get_site_type_characteristics() -> Dict[SiteType, Dict[str, Any]]:
        """Obtener características específicas por tipo de sitio"""
        return {
            SiteType.MARIACHI: {
                "icon": "🎵",
                "description": "Servicios de música en vivo para eventos",
                "typical_services": ["Bodas", "Cumpleaños", "Eventos corporativos", "Serenatas"],
                "target_audience": "Personas organizando eventos especiales",
                "key_features": ["Música en vivo", "Repertorio tradicional", "Animación garantizada"]
            },
            SiteType.RESTAURANT: {
                "icon": "🍽️",
                "description": "Servicios de comida y bebida",
                "typical_services": ["Comida", "Bebidas", "Eventos privados", "Delivery"],
                "target_audience": "Amantes de la buena comida",
                "key_features": ["Platos especiales", "Ambiente acogedor", "Servicio personalizado"]
            },
            SiteType.ECOMMERCE: {
                "icon": "🛒",
                "description": "Tienda online de productos",
                "typical_services": ["Productos", "Envíos", "Garantías", "Soporte"],
                "target_audience": "Compradores online",
                "key_features": ["Productos de calidad", "Envío rápido", "Precios competitivos"]
            },
            SiteType.SERVICES: {
                "icon": "🔧",
                "description": "Servicios profesionales especializados",
                "typical_services": ["Consultoría", "Mantenimiento", "Reparaciones", "Instalaciones"],
                "target_audience": "Empresas y particulares",
                "key_features": ["Profesionales certificados", "Servicio garantizado", "Atención 24/7"]
            },
            SiteType.GENERAL: {
                "icon": "🏢",
                "description": "Negocio general o mixto",
                "typical_services": ["Servicios variados", "Productos", "Consultoría"],
                "target_audience": "Clientes generales",
                "key_features": ["Versatilidad", "Atención personalizada", "Calidad garantizada"]
            }
        }
    
    @staticmethod
    def validate_config_for_site_type(site_type: SiteType, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validar configuración específica para tipo de sitio"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        # Validaciones específicas por tipo
        if site_type == SiteType.MARIACHI:
            if not config.get("instagram_required", True):
                validation_result["warnings"].append("Mariachi sites typically benefit from Instagram integration")
            
            if config.get("max_discount_percentage", 0) > 20:
                validation_result["warnings"].append("High discount percentage may affect profitability")
        
        elif site_type == SiteType.RESTAURANT:
            if config.get("max_discount_percentage", 0) > 30:
                validation_result["warnings"].append("Very high discount percentage for restaurant")
            
            if not config.get("video_progression_enabled", True):
                validation_result["suggestions"].append("Video progression helps showcase menu and atmosphere")
        
        elif site_type == SiteType.ECOMMERCE:
            if config.get("max_discount_percentage", 0) < 10:
                validation_result["suggestions"].append("Ecommerce typically offers higher discounts")
            
            if config.get("instagram_required", False):
                validation_result["suggestions"].append("Instagram integration is optional for ecommerce")
        
        # Validaciones generales
        if config.get("discount_per_action", 0) > config.get("max_discount_percentage", 0):
            validation_result["errors"].append("Discount per action cannot be greater than max discount percentage")
        
        if config.get("sticker_expiration_days", 0) < 7:
            validation_result["warnings"].append("Very short sticker expiration period")
        
        validation_result["valid"] = len(validation_result["errors"]) == 0
        
        return validation_result
