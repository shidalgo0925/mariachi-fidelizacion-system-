from jinja2 import Template, Environment, FileSystemLoader
from app.models.site_config import SiteConfig
from typing import Dict, Any, Optional
import structlog

logger = structlog.get_logger()

class TemplateService:
    """Servicio para manejar templates parametrizados"""
    
    def __init__(self):
        # Configurar Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader('templates'),
            autoescape=True
        )
    
    def render_sticker_template(self, site_config: SiteConfig, sticker_data: Dict[str, Any]) -> str:
        """Renderizar template de sticker con configuración del sitio"""
        try:
            # Template base parametrizado
            template_str = self._get_sticker_template(site_config.site_type)
            template = Template(template_str)
            
            # Contexto para el template
            context = {
                "site_name": site_config.site_name,
                "site_type": site_config.site_type,
                "primary_color": site_config.primary_color,
                "secondary_color": site_config.secondary_color,
                "logo_url": site_config.logo_url,
                "codigo": sticker_data.get("codigo", ""),
                "porcentaje": sticker_data.get("porcentaje", 5),
                "tipo": sticker_data.get("tipo", "descuento"),
                "fecha_expiracion": sticker_data.get("fecha_expiracion", ""),
                "sticker_message": site_config.sticker_message or "¡Disfruta de tu descuento!",
                "qr_code_url": sticker_data.get("qr_code_url", "")
            }
            
            html_content = template.render(**context)
            logger.info("Sticker template rendered", site_id=site_config.site_id, tipo=sticker_data.get("tipo"))
            return html_content
            
        except Exception as e:
            logger.error("Error rendering sticker template", site_id=site_config.site_id, error=str(e))
            return self._get_fallback_template(sticker_data)
    
    def render_email_template(self, site_config: SiteConfig, template_name: str, data: Dict[str, Any]) -> str:
        """Renderizar template de email"""
        try:
            template = self.env.get_template(f"emails/{template_name}.html")
            
            context = {
                "site_name": site_config.site_name,
                "site_type": site_config.site_type,
                "primary_color": site_config.primary_color,
                "secondary_color": site_config.secondary_color,
                "logo_url": site_config.logo_url,
                "email_signature": site_config.email_signature or f"Equipo de {site_config.site_name}",
                **data
            }
            
            html_content = template.render(**context)
            logger.info("Email template rendered", site_id=site_config.site_id, template=template_name)
            return html_content
            
        except Exception as e:
            logger.error("Error rendering email template", site_id=site_config.site_id, template=template_name, error=str(e))
            return self._get_fallback_email_template(site_config, data)
    
    def render_widget_template(self, site_config: SiteConfig, widget_data: Dict[str, Any]) -> str:
        """Renderizar template de widget"""
        try:
            template_str = self._get_widget_template(site_config.site_type)
            template = Template(template_str)
            
            context = {
                "site_name": site_config.site_name,
                "site_type": site_config.site_type,
                "primary_color": site_config.primary_color,
                "secondary_color": site_config.secondary_color,
                "logo_url": site_config.logo_url,
                "welcome_message": site_config.welcome_message or f"¡Bienvenido a {site_config.site_name}!",
                "max_discount": site_config.max_discount_percentage,
                **widget_data
            }
            
            html_content = template.render(**context)
            logger.info("Widget template rendered", site_id=site_config.site_id)
            return html_content
            
        except Exception as e:
            logger.error("Error rendering widget template", site_id=site_config.site_id, error=str(e))
            return self._get_fallback_widget_template(site_config)
    
    def _get_sticker_template(self, site_type: str) -> str:
        """Obtener template de sticker según tipo de sitio"""
        
        templates = {
            "mariachi": """
            <div style="background: {{ primary_color }}; color: white; padding: 20px; border-radius: 10px; text-align: center; font-family: Arial, sans-serif;">
                {% if logo_url %}
                <img src="{{ logo_url }}" alt="{{ site_name }}" style="height: 60px; margin-bottom: 15px;">
                {% endif %}
                <h1 style="margin: 0 0 10px 0; color: white; font-size: 24px;">{{ site_name }}</h1>
                <h2 style="margin: 0 0 15px 0; color: white; font-size: 18px;">🎵 Código de Descuento</h2>
                <div style="background: white; color: {{ primary_color }}; padding: 20px; border-radius: 8px; margin: 15px 0;">
                    <h1 style="margin: 0; font-size: 28px; font-weight: bold;">{{ codigo }}</h1>
                </div>
                <p style="margin: 10px 0; font-size: 16px;">Descuento: {{ porcentaje }}%</p>
                <p style="margin: 10px 0; font-size: 14px;">Válido hasta: {{ fecha_expiracion }}</p>
                <p style="margin: 15px 0 0 0; font-size: 12px; opacity: 0.9;">{{ sticker_message }}</p>
            </div>
            """,
            "restaurant": """
            <div style="background: {{ primary_color }}; color: white; padding: 20px; border-radius: 10px; text-align: center; font-family: Arial, sans-serif;">
                {% if logo_url %}
                <img src="{{ logo_url }}" alt="{{ site_name }}" style="height: 60px; margin-bottom: 15px;">
                {% endif %}
                <h1 style="margin: 0 0 10px 0; color: white; font-size: 24px;">{{ site_name }}</h1>
                <h2 style="margin: 0 0 15px 0; color: white; font-size: 18px;">🍽️ Código de Descuento</h2>
                <div style="background: white; color: {{ primary_color }}; padding: 20px; border-radius: 8px; margin: 15px 0;">
                    <h1 style="margin: 0; font-size: 28px; font-weight: bold;">{{ codigo }}</h1>
                </div>
                <p style="margin: 10px 0; font-size: 16px;">Descuento: {{ porcentaje }}%</p>
                <p style="margin: 10px 0; font-size: 14px;">Válido hasta: {{ fecha_expiracion }}</p>
                <p style="margin: 15px 0 0 0; font-size: 12px; opacity: 0.9;">{{ sticker_message }}</p>
            </div>
            """,
            "ecommerce": """
            <div style="background: {{ primary_color }}; color: white; padding: 20px; border-radius: 10px; text-align: center; font-family: Arial, sans-serif;">
                {% if logo_url %}
                <img src="{{ logo_url }}" alt="{{ site_name }}" style="height: 60px; margin-bottom: 15px;">
                {% endif %}
                <h1 style="margin: 0 0 10px 0; color: white; font-size: 24px;">{{ site_name }}</h1>
                <h2 style="margin: 0 0 15px 0; color: white; font-size: 18px;">🛒 Código de Descuento</h2>
                <div style="background: white; color: {{ primary_color }}; padding: 20px; border-radius: 8px; margin: 15px 0;">
                    <h1 style="margin: 0; font-size: 28px; font-weight: bold;">{{ codigo }}</h1>
                </div>
                <p style="margin: 10px 0; font-size: 16px;">Descuento: {{ porcentaje }}%</p>
                <p style="margin: 10px 0; font-size: 14px;">Válido hasta: {{ fecha_expiracion }}</p>
                <p style="margin: 15px 0 0 0; font-size: 12px; opacity: 0.9;">{{ sticker_message }}</p>
            </div>
            """
        }
        
        return templates.get(site_type, templates["mariachi"])
    
    def _get_widget_template(self, site_type: str) -> str:
        """Obtener template de widget según tipo de sitio"""
        
        templates = {
            "mariachi": """
            <div class="fidelizacion-widget mariachi-theme" style="background: {{ primary_color }}; color: white; padding: 15px; border-radius: 10px; text-align: center; font-family: Arial, sans-serif; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                <div class="widget-header" style="margin-bottom: 10px;">
                    <span class="icon" style="font-size: 24px;">🎵</span>
                    <h3 style="margin: 5px 0; font-size: 18px;">Descuentos Especiales</h3>
                </div>
                <div class="widget-content">
                    <p style="margin: 10px 0; font-size: 14px;">Regístrate y obtén hasta {{ max_discount }}% de descuento</p>
                    <button onclick="openFidelizacionModal()" class="btn-primary" style="background: white; color: {{ primary_color }}; border: none; padding: 10px 20px; border-radius: 5px; font-weight: bold; cursor: pointer;">
                        🎵 Obtener Descuentos
                    </button>
                </div>
            </div>
            """,
            "restaurant": """
            <div class="fidelizacion-widget restaurant-theme" style="background: {{ primary_color }}; color: white; padding: 15px; border-radius: 10px; text-align: center; font-family: Arial, sans-serif; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                <div class="widget-header" style="margin-bottom: 10px;">
                    <span class="icon" style="font-size: 24px;">🍽️</span>
                    <h3 style="margin: 5px 0; font-size: 18px;">Descuentos Especiales</h3>
                </div>
                <div class="widget-content">
                    <p style="margin: 10px 0; font-size: 14px;">Regístrate y obtén hasta {{ max_discount }}% de descuento</p>
                    <button onclick="openFidelizacionModal()" class="btn-primary" style="background: white; color: {{ primary_color }}; border: none; padding: 10px 20px; border-radius: 5px; font-weight: bold; cursor: pointer;">
                        🍽️ Obtener Descuentos
                    </button>
                </div>
            </div>
            """,
            "ecommerce": """
            <div class="fidelizacion-widget ecommerce-theme" style="background: {{ primary_color }}; color: white; padding: 15px; border-radius: 10px; text-align: center; font-family: Arial, sans-serif; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                <div class="widget-header" style="margin-bottom: 10px;">
                    <span class="icon" style="font-size: 24px;">🛒</span>
                    <h3 style="margin: 5px 0; font-size: 18px;">Descuentos Especiales</h3>
                </div>
                <div class="widget-content">
                    <p style="margin: 10px 0; font-size: 14px;">Regístrate y obtén hasta {{ max_discount }}% de descuento</p>
                    <button onclick="openFidelizacionModal()" class="btn-primary" style="background: white; color: {{ primary_color }}; border: none; padding: 10px 20px; border-radius: 5px; font-weight: bold; cursor: pointer;">
                        🛒 Obtener Descuentos
                    </button>
                </div>
            </div>
            """
        }
        
        return templates.get(site_type, templates["mariachi"])
    
    def _get_fallback_template(self, sticker_data: Dict[str, Any]) -> str:
        """Template de fallback para stickers"""
        return f"""
        <div style="background: #e74c3c; color: white; padding: 20px; border-radius: 10px; text-align: center;">
            <h2>Código de Descuento</h2>
            <h1>{sticker_data.get('codigo', 'ERROR')}</h1>
            <p>Descuento: {sticker_data.get('porcentaje', 5)}%</p>
        </div>
        """
    
    def _get_fallback_email_template(self, site_config: SiteConfig, data: Dict[str, Any]) -> str:
        """Template de fallback para emails"""
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: {site_config.primary_color};">{site_config.site_name}</h1>
            <p>{data.get('message', 'Gracias por contactarnos.')}</p>
            <p>Saludos,<br>Equipo de {site_config.site_name}</p>
        </div>
        """
    
    def _get_fallback_widget_template(self, site_config: SiteConfig) -> str:
        """Template de fallback para widgets"""
        return f"""
        <div style="background: {site_config.primary_color}; color: white; padding: 15px; border-radius: 10px; text-align: center;">
            <h3>Descuentos Especiales</h3>
            <p>Regístrate y obtén descuentos</p>
            <button onclick="openFidelizacionModal()" style="background: white; color: {site_config.primary_color}; border: none; padding: 10px 20px; border-radius: 5px;">
                Obtener Descuentos
            </button>
        </div>
        """
