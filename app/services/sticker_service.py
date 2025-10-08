from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from app.models.sticker import Sticker
from app.models.user import User
from app.models.site_config import SiteConfig
from app.schemas.sticker import (
    StickerCreate, StickerUpdate, StickerStats, StickerValidation,
    StickerValidationResponse, StickerType, StickerStatus
)
from app.services.points_service import PointsService
from app.services.odoo_service import OdooService
from app.utils.code_generator import CodeGenerator
from app.utils.qr_generator import QRGenerator
from app.utils.pdf_generator import PDFGenerator
from typing import Optional, List, Dict, Any
import structlog
from datetime import datetime, timedelta
import secrets
import string

logger = structlog.get_logger()

class StickerService:
    """Servicio para manejar stickers multi-tenant"""
    
    def __init__(self, db: Session):
        self.db = db
        self.points_service = PointsService(db)
        self.odoo_service = OdooService(db)
        self.code_generator = CodeGenerator()
        self.qr_generator = QRGenerator()
        self.pdf_generator = PDFGenerator()
    
    async def create_sticker(
        self, 
        sticker_data: StickerCreate, 
        site_id: str,
        user_id: int
    ) -> Optional[Sticker]:
        """Crear nuevo sticker"""
        try:
            # Verificar que el sitio existe
            site_config = self.db.query(SiteConfig).filter(
                SiteConfig.site_id == site_id,
                SiteConfig.activo == True
            ).first()
            
            if not site_config:
                logger.warning("Site not found or inactive", site_id=site_id)
                return None
            
            # Verificar que el usuario existe y pertenece al sitio
            user = self.db.query(User).filter(
                and_(
                    User.id == user_id,
                    User.site_id == site_id,
                    User.activo == True
                )
            ).first()
            
            if not user:
                logger.warning("User not found or inactive", user_id=user_id, site_id=site_id)
                return None
            
            # Verificar límites de descuento
            if not self._validate_discount_limits(user, sticker_data.porcentaje_descuento, site_config):
                logger.warning("Discount limit exceeded", 
                             user_id=user_id, 
                             requested_discount=sticker_data.porcentaje_descuento,
                             current_discount=user.total_descuento,
                             max_discount=site_config.max_discount_percentage)
                return None
            
            # Generar código único
            codigo_descuento = await self._generate_unique_code(site_id)
            
            # Crear sticker
            sticker = Sticker(
                site_id=site_id,
                usuario_id=user_id,
                tipo_sticker=sticker_data.tipo_sticker,
                codigo_descuento=codigo_descuento,
                porcentaje_descuento=sticker_data.porcentaje_descuento,
                fecha_expiracion=sticker_data.fecha_expiracion,
                usado=False,
                sincronizado_odoo=False,
                metadata=str(sticker_data.metadata) if sticker_data.metadata else None
            )
            
            self.db.add(sticker)
            self.db.commit()
            self.db.refresh(sticker)
            
            # Generar QR code
            qr_url = await self._generate_qr_code(sticker, site_config)
            if qr_url:
                sticker.qr_code_url = qr_url
                self.db.commit()
            
            # Generar imagen del sticker
            imagen_url = await self._generate_sticker_image(sticker, site_config)
            if imagen_url:
                sticker.imagen_url = imagen_url
                self.db.commit()
            
            # Otorgar puntos por generación de sticker
            await self.points_service.award_points_for_sticker_generation(
                user_id, site_id, sticker_data.tipo_sticker
            )
            
            # Actualizar descuento total del usuario
            new_total_discount = min(
                user.total_descuento + sticker_data.porcentaje_descuento,
                site_config.max_discount_percentage
            )
            await self.points_service.update_discount(user_id, site_id, new_total_discount)
            
            # Sincronizar con Odoo si está habilitado
            if site_config.odoo_integration:
                await self.odoo_service.sync_sticker_to_odoo(sticker, site_config)
            
            logger.info("Sticker created successfully", 
                       sticker_id=sticker.id, 
                       user_id=user_id, 
                       site_id=site_id,
                       codigo=codigo_descuento)
            
            return sticker
            
        except Exception as e:
            self.db.rollback()
            logger.error("Error creating sticker", 
                        user_id=user_id, 
                        site_id=site_id, 
                        error=str(e))
            return None
    
    async def get_sticker_by_id(self, sticker_id: int, site_id: str) -> Optional[Sticker]:
        """Obtener sticker por ID"""
        try:
            sticker = self.db.query(Sticker).filter(
                and_(
                    Sticker.id == sticker_id,
                    Sticker.site_id == site_id
                )
            ).first()
            
            if sticker:
                logger.debug("Sticker retrieved", sticker_id=sticker_id, site_id=site_id)
            else:
                logger.warning("Sticker not found", sticker_id=sticker_id, site_id=site_id)
            
            return sticker
            
        except Exception as e:
            logger.error("Error getting sticker by ID", 
                        sticker_id=sticker_id, 
                        site_id=site_id, 
                        error=str(e))
            return None
    
    async def get_sticker_by_code(self, codigo: str, site_id: str) -> Optional[Sticker]:
        """Obtener sticker por código"""
        try:
            sticker = self.db.query(Sticker).filter(
                and_(
                    Sticker.codigo_descuento == codigo,
                    Sticker.site_id == site_id
                )
            ).first()
            
            if sticker:
                logger.debug("Sticker retrieved by code", codigo=codigo, site_id=site_id)
            else:
                logger.debug("Sticker not found by code", codigo=codigo, site_id=site_id)
            
            return sticker
            
        except Exception as e:
            logger.error("Error getting sticker by code", 
                        codigo=codigo, 
                        site_id=site_id, 
                        error=str(e))
            return None
    
    async def validate_sticker(self, validation_data: StickerValidation, site_id: str) -> StickerValidationResponse:
        """Validar sticker para uso"""
        try:
            sticker = await self.get_sticker_by_code(validation_data.codigo_descuento, site_id)
            
            if not sticker:
                return StickerValidationResponse(
                    valido=False,
                    mensaje="Código de descuento no encontrado"
                )
            
            # Verificar si ya fue usado
            if sticker.usado:
                return StickerValidationResponse(
                    valido=False,
                    mensaje="Este código de descuento ya ha sido utilizado"
                )
            
            # Verificar expiración
            if datetime.utcnow() > sticker.fecha_expiracion:
                return StickerValidationResponse(
                    valido=False,
                    mensaje="Este código de descuento ha expirado"
                )
            
            # Verificar si el usuario puede usar este sticker (opcional)
            if validation_data.usuario_id and sticker.usuario_id != validation_data.usuario_id:
                return StickerValidationResponse(
                    valido=False,
                    mensaje="Este código de descuento no pertenece al usuario actual"
                )
            
            return StickerValidationResponse(
                valido=True,
                sticker=sticker,
                mensaje="Código de descuento válido",
                descuento_aplicable=sticker.porcentaje_descuento
            )
            
        except Exception as e:
            logger.error("Error validating sticker", 
                        codigo=validation_data.codigo_descuento, 
                        site_id=site_id, 
                        error=str(e))
            return StickerValidationResponse(
                valido=False,
                mensaje="Error interno al validar el código"
            )
    
    async def use_sticker(self, codigo: str, site_id: str, usuario_id: Optional[int] = None) -> bool:
        """Marcar sticker como usado"""
        try:
            sticker = await self.get_sticker_by_code(codigo, site_id)
            
            if not sticker:
                logger.warning("Sticker not found for use", codigo=codigo, site_id=site_id)
                return False
            
            if sticker.usado:
                logger.warning("Sticker already used", codigo=codigo, site_id=site_id)
                return False
            
            if datetime.utcnow() > sticker.fecha_expiracion:
                logger.warning("Sticker expired", codigo=codigo, site_id=site_id)
                return False
            
            # Marcar como usado
            sticker.usado = True
            sticker.fecha_uso = datetime.utcnow()
            self.db.commit()
            
            # Sincronizar con Odoo si está habilitado
            site_config = self.db.query(SiteConfig).filter(
                SiteConfig.site_id == site_id
            ).first()
            
            if site_config and site_config.odoo_integration:
                await self.odoo_service.update_sticker_in_odoo(sticker, site_config)
            
            logger.info("Sticker marked as used", 
                       codigo=codigo, 
                       site_id=site_id, 
                       usuario_id=usuario_id)
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error("Error using sticker", 
                        codigo=codigo, 
                        site_id=site_id, 
                        error=str(e))
            return False
    
    async def get_user_stickers(
        self, 
        user_id: int, 
        site_id: str, 
        page: int = 1, 
        size: int = 10,
        tipo_sticker: Optional[StickerType] = None
    ) -> Dict[str, Any]:
        """Obtener stickers de un usuario"""
        try:
            query = self.db.query(Sticker).filter(
                and_(
                    Sticker.usuario_id == user_id,
                    Sticker.site_id == site_id
                )
            )
            
            # Filtrar por tipo si se especifica
            if tipo_sticker:
                query = query.filter(Sticker.tipo_sticker == tipo_sticker)
            
            # Contar total
            total = query.count()
            
            # Aplicar paginación
            offset = (page - 1) * size
            stickers = query.order_by(desc(Sticker.fecha_generacion)).offset(offset).limit(size).all()
            
            total_pages = (total + size - 1) // size
            
            result = {
                "stickers": stickers,
                "total": total,
                "page": page,
                "size": size,
                "total_pages": total_pages
            }
            
            logger.info("User stickers retrieved", 
                       user_id=user_id, 
                       site_id=site_id, 
                       page=page, 
                       total=total)
            
            return result
            
        except Exception as e:
            logger.error("Error getting user stickers", 
                        user_id=user_id, 
                        site_id=site_id, 
                        error=str(e))
            return {"stickers": [], "total": 0, "page": page, "size": size, "total_pages": 0}
    
    async def get_sticker_stats(self, site_id: str, user_id: Optional[int] = None) -> StickerStats:
        """Obtener estadísticas de stickers"""
        try:
            query = self.db.query(Sticker).filter(Sticker.site_id == site_id)
            
            if user_id:
                query = query.filter(Sticker.usuario_id == user_id)
            
            # Estadísticas básicas
            total_generados = query.count()
            total_usados = query.filter(Sticker.usado == True).count()
            total_expirados = query.filter(Sticker.fecha_expiracion < datetime.utcnow()).count()
            
            porcentaje_uso = (total_usados / total_generados * 100) if total_generados > 0 else 0
            
            # Stickers por tipo
            stickers_por_tipo = {}
            for tipo in StickerType:
                count = query.filter(Sticker.tipo_sticker == tipo).count()
                stickers_por_tipo[tipo.value] = count
            
            # Stickers por mes (últimos 12 meses)
            stickers_por_mes = []
            for i in range(12):
                fecha_inicio = datetime.utcnow() - timedelta(days=30 * (i + 1))
                fecha_fin = datetime.utcnow() - timedelta(days=30 * i)
                
                count = query.filter(
                    and_(
                        Sticker.fecha_generacion >= fecha_inicio,
                        Sticker.fecha_generacion < fecha_fin
                    )
                ).count()
                
                stickers_por_mes.append({
                    "mes": fecha_inicio.strftime("%Y-%m"),
                    "cantidad": count
                })
            
            stats = StickerStats(
                total_generados=total_generados,
                total_usados=total_usados,
                total_expirados=total_expirados,
                porcentaje_uso=round(porcentaje_uso, 2),
                stickers_por_tipo=stickers_por_tipo,
                stickers_por_mes=stickers_por_mes
            )
            
            logger.info("Sticker stats retrieved", 
                       site_id=site_id, 
                       user_id=user_id, 
                       total_generados=total_generados)
            
            return stats
            
        except Exception as e:
            logger.error("Error getting sticker stats", 
                        site_id=site_id, 
                        user_id=user_id, 
                        error=str(e))
            return StickerStats()
    
    async def _generate_unique_code(self, site_id: str) -> str:
        """Generar código único para el sticker"""
        max_attempts = 10
        
        for attempt in range(max_attempts):
            # Generar código con formato: SITE-XXXX-YYYY
            site_prefix = site_id.upper()[:4]
            random_part = ''.join(secrets.choices(string.ascii_uppercase + string.digits, k=8))
            codigo = f"{site_prefix}-{random_part}"
            
            # Verificar que no exista
            existing = self.db.query(Sticker).filter(
                Sticker.codigo_descuento == codigo
            ).first()
            
            if not existing:
                return codigo
        
        # Si no se puede generar código único, usar timestamp
        timestamp = int(datetime.utcnow().timestamp())
        return f"{site_id.upper()[:4]}-{timestamp}"
    
    async def _generate_qr_code(self, sticker: Sticker, site_config: SiteConfig) -> Optional[str]:
        """Generar QR code para el sticker"""
        try:
            # URL del sticker (esto sería la URL de validación)
            qr_data = f"https://{site_config.site_id}.com/validate/{sticker.codigo_descuento}"
            
            # Generar QR code
            qr_url = await self.qr_generator.generate_qr(
                data=qr_data,
                filename=f"sticker_{sticker.id}_qr.png",
                size=200
            )
            
            return qr_url
            
        except Exception as e:
            logger.error("Error generating QR code", 
                        sticker_id=sticker.id, 
                        error=str(e))
            return None
    
    async def _generate_sticker_image(self, sticker: Sticker, site_config: SiteConfig) -> Optional[str]:
        """Generar imagen del sticker"""
        try:
            # Generar imagen del sticker usando el template
            imagen_url = await self.pdf_generator.generate_sticker_image(
                sticker=sticker,
                site_config=site_config,
                template_id="default"
            )
            
            return imagen_url
            
        except Exception as e:
            logger.error("Error generating sticker image", 
                        sticker_id=sticker.id, 
                        error=str(e))
            return None
    
    def _validate_discount_limits(self, user: User, new_discount: int, site_config: SiteConfig) -> bool:
        """Validar límites de descuento"""
        total_discount = user.total_descuento + new_discount
        return total_discount <= site_config.max_discount_percentage
