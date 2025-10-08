import xmlrpc.client
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.sticker import Sticker
from app.models.site_config import SiteConfig
from app.models.odoo_sync_log import OdooSyncLog
from app.schemas.odoo import (
    OdooPartnerData, OdooProductData, OdooConnectionTestResponse,
    OdooModelType, OdooSyncStatus
)
from typing import Optional, Dict, Any, List
import structlog
from datetime import datetime, timedelta
import asyncio

logger = structlog.get_logger()

class OdooService:
    """Servicio para integración con Odoo"""
    
    def __init__(self, db: Session):
        self.db = db
        self._connections = {}  # Cache de conexiones por sitio
    
    def _get_odoo_connection(self, site_config: SiteConfig):
        """Obtener conexión a Odoo para un sitio específico"""
        if not site_config.odoo_integration or not site_config.odoo_url:
            return None
        
        # Usar cache si existe
        cache_key = f"{site_config.site_id}_{site_config.odoo_url}"
        if cache_key in self._connections:
            return self._connections[cache_key]
        
        try:
            # Crear conexión
            common = xmlrpc.client.ServerProxy(f'{site_config.odoo_url}/xmlrpc/2/common')
            models = xmlrpc.client.ServerProxy(f'{site_config.odoo_url}/xmlrpc/2/object')
            
            # Verificar conexión
            version = common.version()
            logger.info("Odoo connection established", 
                       site_id=site_config.site_id, 
                       odoo_url=site_config.odoo_url, 
                       version=version)
            
            connection = {
                'common': common,
                'models': models,
                'database': site_config.odoo_database,
                'username': site_config.odoo_username,
                'password': site_config.odoo_password
            }
            
            # Cachear conexión
            self._connections[cache_key] = connection
            return connection
            
        except Exception as e:
            logger.error("Error connecting to Odoo", 
                        site_id=site_config.site_id, 
                        odoo_url=site_config.odoo_url, 
                        error=str(e))
            return None
    
    async def test_connection(self, site_config: SiteConfig) -> OdooConnectionTestResponse:
        """Probar conexión con Odoo"""
        try:
            connection = self._get_odoo_connection(site_config)
            if not connection:
                return OdooConnectionTestResponse(
                    success=False,
                    message="Failed to establish connection to Odoo"
                )
            
            # Obtener información de la versión
            version = connection['common'].version()
            
            # Obtener información de la base de datos
            db_info = connection['common'].about()
            
            # Obtener información del usuario
            uid = connection['common'].authenticate(
                connection['database'],
                connection['username'],
                connection['password'],
                {}
            )
            
            if not uid:
                return OdooConnectionTestResponse(
                    success=False,
                    message="Authentication failed"
                )
            
            user_info = connection['models'].execute_kw(
                connection['database'],
                uid,
                connection['password'],
                'res.users',
                'read',
                [uid],
                {'fields': ['name', 'login', 'email']}
            )
            
            return OdooConnectionTestResponse(
                success=True,
                message="Connection successful",
                version=version.get('server_version'),
                database_info=db_info,
                user_info=user_info[0] if user_info else None
            )
            
        except Exception as e:
            logger.error("Error testing Odoo connection", 
                        site_id=site_config.site_id, 
                        error=str(e))
            return OdooConnectionTestResponse(
                success=False,
                message=f"Connection test failed: {str(e)}"
            )
    
    async def sync_user_to_odoo(self, user: User, site_config: SiteConfig) -> Optional[str]:
        """Sincronizar usuario con Odoo"""
        try:
            # Crear log de sincronización
            sync_log = OdooSyncLog(
                site_id=site_config.site_id,
                model_type=OdooModelType.PARTNER,
                record_id=user.id,
                operation="create" if not user.id_odoo else "update",
                status=OdooSyncStatus.SYNCING
            )
            self.db.add(sync_log)
            self.db.commit()
            
            connection = self._get_odoo_connection(site_config)
            if not connection:
                sync_log.status = OdooSyncStatus.FAILED
                sync_log.error_message = "No Odoo connection available"
                self.db.commit()
                return None
            
            # Verificar si el usuario ya existe en Odoo
            if user.id_odoo:
                # Actualizar contacto existente
                partner_data = OdooPartnerData(
                    name=user.nombre,
                    email=user.email,
                    phone=user.telefono or '',
                    is_company=False,
                    customer_rank=1,
                    x_site_id=site_config.site_id,
                    x_user_id=user.id,
                    x_puntos_acumulados=user.puntos_acumulados,
                    x_total_descuento=user.total_descuento,
                    x_instagram_seguido=user.instagram_seguido,
                    x_activo=user.activo
                )
                
                # Autenticar en Odoo
                uid = connection['common'].authenticate(
                    connection['database'],
                    connection['username'],
                    connection['password'],
                    {}
                )
                
                if not uid:
                    sync_log.status = OdooSyncStatus.FAILED
                    sync_log.error_message = "Odoo authentication failed"
                    self.db.commit()
                    return None
                
                # Actualizar contacto
                connection['models'].execute_kw(
                    connection['database'],
                    uid,
                    connection['password'],
                    'res.partner',
                    'write',
                    [[int(user.id_odoo)], partner_data.dict()]
                )
                
                sync_log.status = OdooSyncStatus.COMPLETED
                sync_log.odoo_id = int(user.id_odoo)
                self.db.commit()
                
                return user.id_odoo
            else:
                # Crear nuevo contacto
                partner_data = OdooPartnerData(
                    name=user.nombre,
                    email=user.email,
                    phone=user.telefono or '',
                    is_company=False,
                    customer_rank=1,
                    x_site_id=site_config.site_id,
                    x_user_id=user.id,
                    x_puntos_acumulados=user.puntos_acumulados,
                    x_total_descuento=user.total_descuento,
                    x_instagram_seguido=user.instagram_seguido,
                    x_activo=user.activo
                )
                
                # Autenticar en Odoo
                uid = connection['common'].authenticate(
                    connection['database'],
                    connection['username'],
                    connection['password'],
                    {}
                )
                
                if not uid:
                    sync_log.status = OdooSyncStatus.FAILED
                    sync_log.error_message = "Odoo authentication failed"
                    self.db.commit()
                    return None
                
                # Crear contacto
                contact_id = connection['models'].execute_kw(
                    connection['database'],
                    uid,
                    connection['password'],
                    'res.partner',
                    'create',
                    [partner_data.dict()]
                )
                
                # Actualizar usuario con ID de Odoo
                user.id_odoo = str(contact_id)
                user.sincronizado_odoo = True
                
                sync_log.status = OdooSyncStatus.COMPLETED
                sync_log.odoo_id = contact_id
                self.db.commit()
                
                logger.info("User synced to Odoo", 
                           user_id=user.id, 
                           site_id=site_config.site_id, 
                           odoo_contact_id=contact_id)
                
                return str(contact_id)
            
        except Exception as e:
            if 'sync_log' in locals():
                sync_log.status = OdooSyncStatus.FAILED
                sync_log.error_message = str(e)
                self.db.commit()
            
            logger.error("Error syncing user to Odoo", 
                        user_id=user.id, 
                        site_id=site_config.site_id, 
                        error=str(e))
            return None
    
    async def sync_sticker_to_odoo(self, sticker: Sticker, site_config: SiteConfig) -> Optional[str]:
        """Sincronizar sticker con Odoo como producto"""
        try:
            connection = self._get_odoo_connection(site_config)
            if not connection:
                return None
            
            # Verificar si el sticker ya existe en Odoo
            if sticker.id_odoo:
                return sticker.id_odoo
            
            # Crear producto en Odoo
            product_data = {
                'name': f"Descuento {sticker.porcentaje_descuento}% - {sticker.codigo_descuento}",
                'type': 'service',
                'categ_id': 1,  # Categoría por defecto
                'list_price': 0.0,
                'standard_price': 0.0,
                'sale_ok': True,
                'purchase_ok': False,
                'x_site_id': site_config.site_id,
                'x_sticker_id': sticker.id,
                'x_codigo_descuento': sticker.codigo_descuento,
                'x_porcentaje_descuento': sticker.porcentaje_descuento,
                'x_tipo_sticker': sticker.tipo_sticker.value,
                'x_usuario_id': sticker.usuario_id,
                'x_fecha_expiracion': sticker.fecha_expiracion.isoformat() if sticker.fecha_expiracion else None,
                'x_usado': sticker.usado
            }
            
            # Autenticar en Odoo
            uid = connection['common'].authenticate(
                connection['database'],
                connection['username'],
                connection['password'],
                {}
            )
            
            if not uid:
                return None
            
            # Crear producto
            product_id = connection['models'].execute_kw(
                connection['database'],
                uid,
                connection['password'],
                'product.product',
                'create',
                [product_data]
            )
            
            # Actualizar sticker con ID de Odoo
            sticker.id_odoo = str(product_id)
            sticker.sincronizado_odoo = True
            self.db.commit()
            
            logger.info("Sticker synced to Odoo", 
                       sticker_id=sticker.id, 
                       site_id=site_config.site_id, 
                       odoo_product_id=product_id)
            
            return str(product_id)
            
        except Exception as e:
            logger.error("Error syncing sticker to Odoo", 
                        sticker_id=sticker.id, 
                        site_id=site_config.site_id, 
                        error=str(e))
            return None
    
    async def update_user_in_odoo(self, user: User, site_config: SiteConfig) -> bool:
        """Actualizar usuario en Odoo"""
        try:
            if not user.id_odoo:
                logger.warning("User has no Odoo ID", user_id=user.id, site_id=site_config.site_id)
                return False
            
            connection = self._get_odoo_connection(site_config)
            if not connection:
                return False
            
            # Datos actualizados
            update_data = {
                'x_puntos_acumulados': user.puntos_acumulados,
                'x_total_descuento': user.total_descuento,
                'x_instagram_seguido': user.instagram_seguido,
                'x_stickers_generados': user.stickers_generados,
                'x_videos_completados': user.videos_completados,
                'x_reseñas_dejadas': user.reseñas_dejadas,
                'x_activo': user.activo,
                'x_verificado': user.verificado
            }
            
            # Autenticar en Odoo
            uid = connection['common'].authenticate(
                connection['database'],
                connection['username'],
                connection['password'],
                {}
            )
            
            if not uid:
                return False
            
            # Actualizar contacto
            connection['models'].execute_kw(
                connection['database'],
                uid,
                connection['password'],
                'res.partner',
                'write',
                [[int(user.id_odoo)], update_data]
            )
            
            logger.info("User updated in Odoo", 
                       user_id=user.id, 
                       site_id=site_config.site_id, 
                       odoo_contact_id=user.id_odoo)
            
            return True
            
        except Exception as e:
            logger.error("Error updating user in Odoo", 
                        user_id=user.id, 
                        site_id=site_config.site_id, 
                        error=str(e))
            return False
    
    async def sync_all_pending_users(self, site_id: str) -> Dict[str, Any]:
        """Sincronizar todos los usuarios pendientes de un sitio"""
        try:
            site_config = self.db.query(SiteConfig).filter(
                SiteConfig.site_id == site_id
            ).first()
            
            if not site_config or not site_config.odoo_integration:
                return {"success": False, "message": "Odoo integration not enabled"}
            
            # Obtener usuarios no sincronizados
            pending_users = self.db.query(User).filter(
                User.site_id == site_id,
                User.sincronizado_odoo == False,
                User.activo == True
            ).all()
            
            results = {
                "total": len(pending_users),
                "synced": 0,
                "failed": 0,
                "errors": []
            }
            
            for user in pending_users:
                try:
                    odoo_id = await self.sync_user_to_odoo(user, site_config)
                    if odoo_id:
                        results["synced"] += 1
                    else:
                        results["failed"] += 1
                        results["errors"].append(f"Failed to sync user {user.id}")
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(f"Error syncing user {user.id}: {str(e)}")
            
            logger.info("Bulk user sync completed", 
                       site_id=site_id, 
                       total=results["total"], 
                       synced=results["synced"], 
                       failed=results["failed"])
            
            return results
            
        except Exception as e:
            logger.error("Error in bulk user sync", site_id=site_id, error=str(e))
            return {"success": False, "message": f"Bulk sync error: {str(e)}"}
    
    async def sync_all_pending_stickers(self, site_id: str) -> Dict[str, Any]:
        """Sincronizar todos los stickers pendientes de un sitio"""
        try:
            site_config = self.db.query(SiteConfig).filter(
                SiteConfig.site_id == site_id
            ).first()
            
            if not site_config or not site_config.odoo_integration:
                return {"success": False, "message": "Odoo integration not enabled"}
            
            # Obtener stickers no sincronizados
            pending_stickers = self.db.query(Sticker).filter(
                Sticker.site_id == site_id,
                Sticker.sincronizado_odoo == False
            ).all()
            
            results = {
                "total": len(pending_stickers),
                "synced": 0,
                "failed": 0,
                "errors": []
            }
            
            for sticker in pending_stickers:
                try:
                    odoo_id = await self.sync_sticker_to_odoo(sticker, site_config)
                    if odoo_id:
                        results["synced"] += 1
                    else:
                        results["failed"] += 1
                        results["errors"].append(f"Failed to sync sticker {sticker.id}")
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(f"Error syncing sticker {sticker.id}: {str(e)}")
            
            logger.info("Bulk sticker sync completed", 
                       site_id=site_id, 
                       total=results["total"], 
                       synced=results["synced"], 
                       failed=results["failed"])
            
            return results
            
        except Exception as e:
            logger.error("Error in bulk sticker sync", site_id=site_id, error=str(e))
            return {"success": False, "message": f"Bulk sync error: {str(e)}"}
    
    async def get_odoo_connection_status(self, site_id: str) -> Dict[str, Any]:
        """Verificar estado de conexión con Odoo"""
        try:
            site_config = self.db.query(SiteConfig).filter(
                SiteConfig.site_id == site_id
            ).first()
            
            if not site_config:
                return {"connected": False, "message": "Site not found"}
            
            if not site_config.odoo_integration:
                return {"connected": False, "message": "Odoo integration not enabled"}
            
            connection = self._get_odoo_connection(site_config)
            if not connection:
                return {"connected": False, "message": "Connection failed"}
            
            # Verificar conexión
            version = connection['common'].version()
            
            return {
                "connected": True,
                "version": version,
                "database": site_config.odoo_database,
                "url": site_config.odoo_url
            }
            
        except Exception as e:
            logger.error("Error checking Odoo connection", site_id=site_id, error=str(e))
            return {"connected": False, "message": f"Connection error: {str(e)}"}
