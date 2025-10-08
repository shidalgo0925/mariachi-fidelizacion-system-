from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from app.models.user import User
from app.models.sticker import Sticker
from app.models.site_config import SiteConfig
from app.models.odoo_sync_log import OdooSyncLog, OdooConfig
from app.services.odoo_service import OdooService
from app.schemas.odoo import (
    OdooModelType, OdooSyncStatus, OdooSyncRequest, OdooSyncResponse
)
from typing import Optional, List, Dict, Any
import structlog
from datetime import datetime, timedelta
import asyncio
import json

logger = structlog.get_logger()

class SyncService:
    """Servicio para sincronización automática con Odoo"""
    
    def __init__(self, db: Session):
        self.db = db
        self.odoo_service = OdooService(db)
    
    async def sync_site_data(self, site_id: str, force_sync: bool = False) -> OdooSyncResponse:
        """Sincronizar todos los datos de un sitio"""
        try:
            # Obtener configuración del sitio
            site_config = self.db.query(SiteConfig).filter(
                SiteConfig.site_id == site_id
            ).first()
            
            if not site_config or not site_config.odoo_integration:
                return OdooSyncResponse(
                    success=False,
                    message="Odoo integration not enabled for this site"
                )
            
            # Obtener configuración de Odoo
            odoo_config = self.db.query(OdooConfig).filter(
                OdooConfig.site_id == site_id
            ).first()
            
            if not odoo_config:
                return OdooSyncResponse(
                    success=False,
                    message="Odoo configuration not found"
                )
            
            # Verificar si debe sincronizar
            if not force_sync and odoo_config.auto_sync:
                last_sync = odoo_config.last_sync
                if last_sync and datetime.utcnow() - last_sync < timedelta(minutes=odoo_config.sync_interval):
                    return OdooSyncResponse(
                        success=True,
                        message="Sync skipped - too recent",
                        synced_count=0
                    )
            
            synced_count = 0
            failed_count = 0
            errors = []
            sync_logs = []
            
            # Sincronizar usuarios
            user_sync_result = await self._sync_users(site_id, site_config, force_sync)
            synced_count += user_sync_result["synced"]
            failed_count += user_sync_result["failed"]
            errors.extend(user_sync_result["errors"])
            sync_logs.extend(user_sync_result["logs"])
            
            # Sincronizar stickers
            sticker_sync_result = await self._sync_stickers(site_id, site_config, force_sync)
            synced_count += sticker_sync_result["synced"]
            failed_count += sticker_sync_result["failed"]
            errors.extend(sticker_sync_result["errors"])
            sync_logs.extend(sticker_sync_result["logs"])
            
            # Actualizar última sincronización
            odoo_config.last_sync = datetime.utcnow()
            odoo_config.connection_status = "connected" if synced_count > 0 else "error"
            self.db.commit()
            
            success = failed_count == 0
            
            logger.info("Site data sync completed", 
                       site_id=site_id, 
                       synced_count=synced_count, 
                       failed_count=failed_count,
                       success=success)
            
            return OdooSyncResponse(
                success=success,
                message=f"Sync completed: {synced_count} synced, {failed_count} failed",
                synced_count=synced_count,
                failed_count=failed_count,
                errors=errors,
                sync_logs=sync_logs
            )
            
        except Exception as e:
            logger.error("Error syncing site data", 
                        site_id=site_id, 
                        error=str(e))
            return OdooSyncResponse(
                success=False,
                message=f"Sync failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _sync_users(self, site_id: str, site_config: SiteConfig, force_sync: bool) -> Dict[str, Any]:
        """Sincronizar usuarios del sitio"""
        try:
            # Obtener usuarios que necesitan sincronización
            if force_sync:
                users = self.db.query(User).filter(
                    and_(
                        User.site_id == site_id,
                        User.activo == True
                    )
                ).all()
            else:
                users = self.db.query(User).filter(
                    and_(
                        User.site_id == site_id,
                        User.activo == True,
                        User.sincronizado_odoo == False
                    )
                ).all()
            
            synced = 0
            failed = 0
            errors = []
            logs = []
            
            for user in users:
                try:
                    # Crear log de sincronización
                    sync_log = OdooSyncLog(
                        site_id=site_id,
                        model_type=OdooModelType.PARTNER,
                        record_id=user.id,
                        operation="create" if not user.id_odoo else "update",
                        status=OdooSyncStatus.SYNCING
                    )
                    self.db.add(sync_log)
                    self.db.commit()
                    
                    # Sincronizar usuario
                    odoo_id = await self.odoo_service.sync_user_to_odoo(user, site_config)
                    
                    if odoo_id:
                        sync_log.status = OdooSyncStatus.COMPLETED
                        sync_log.odoo_id = int(odoo_id)
                        synced += 1
                    else:
                        sync_log.status = OdooSyncStatus.FAILED
                        sync_log.error_message = "Failed to sync user"
                        failed += 1
                        errors.append(f"Failed to sync user {user.id}")
                    
                    self.db.commit()
                    logs.append(sync_log)
                    
                except Exception as e:
                    if 'sync_log' in locals():
                        sync_log.status = OdooSyncStatus.FAILED
                        sync_log.error_message = str(e)
                        self.db.commit()
                    
                    failed += 1
                    errors.append(f"Error syncing user {user.id}: {str(e)}")
                    logger.error("Error syncing user", 
                                user_id=user.id, 
                                site_id=site_id, 
                                error=str(e))
            
            return {
                "synced": synced,
                "failed": failed,
                "errors": errors,
                "logs": logs
            }
            
        except Exception as e:
            logger.error("Error in _sync_users", 
                        site_id=site_id, 
                        error=str(e))
            return {
                "synced": 0,
                "failed": 0,
                "errors": [str(e)],
                "logs": []
            }
    
    async def _sync_stickers(self, site_id: str, site_config: SiteConfig, force_sync: bool) -> Dict[str, Any]:
        """Sincronizar stickers del sitio"""
        try:
            # Obtener stickers que necesitan sincronización
            if force_sync:
                stickers = self.db.query(Sticker).filter(
                    and_(
                        Sticker.site_id == site_id
                    )
                ).all()
            else:
                stickers = self.db.query(Sticker).filter(
                    and_(
                        Sticker.site_id == site_id,
                        Sticker.sincronizado_odoo == False
                    )
                ).all()
            
            synced = 0
            failed = 0
            errors = []
            logs = []
            
            for sticker in stickers:
                try:
                    # Crear log de sincronización
                    sync_log = OdooSyncLog(
                        site_id=site_id,
                        model_type=OdooModelType.PRODUCT,
                        record_id=sticker.id,
                        operation="create" if not sticker.id_odoo else "update",
                        status=OdooSyncStatus.SYNCING
                    )
                    self.db.add(sync_log)
                    self.db.commit()
                    
                    # Sincronizar sticker
                    odoo_id = await self.odoo_service.sync_sticker_to_odoo(sticker, site_config)
                    
                    if odoo_id:
                        sync_log.status = OdooSyncStatus.COMPLETED
                        sync_log.odoo_id = int(odoo_id)
                        synced += 1
                    else:
                        sync_log.status = OdooSyncStatus.FAILED
                        sync_log.error_message = "Failed to sync sticker"
                        failed += 1
                        errors.append(f"Failed to sync sticker {sticker.id}")
                    
                    self.db.commit()
                    logs.append(sync_log)
                    
                except Exception as e:
                    if 'sync_log' in locals():
                        sync_log.status = OdooSyncStatus.FAILED
                        sync_log.error_message = str(e)
                        self.db.commit()
                    
                    failed += 1
                    errors.append(f"Error syncing sticker {sticker.id}: {str(e)}")
                    logger.error("Error syncing sticker", 
                                sticker_id=sticker.id, 
                                site_id=site_id, 
                                error=str(e))
            
            return {
                "synced": synced,
                "failed": failed,
                "errors": errors,
                "logs": logs
            }
            
        except Exception as e:
            logger.error("Error in _sync_stickers", 
                        site_id=site_id, 
                        error=str(e))
            return {
                "synced": 0,
                "failed": 0,
                "errors": [str(e)],
                "logs": []
            }
    
    async def retry_failed_syncs(self, site_id: str, max_retries: int = 3) -> OdooSyncResponse:
        """Reintentar sincronizaciones fallidas"""
        try:
            # Obtener logs de sincronización fallidos
            failed_logs = self.db.query(OdooSyncLog).filter(
                and_(
                    OdooSyncLog.site_id == site_id,
                    OdooSyncLog.status == OdooSyncStatus.FAILED,
                    OdooSyncLog.retry_count < max_retries
                )
            ).all()
            
            if not failed_logs:
                return OdooSyncResponse(
                    success=True,
                    message="No failed syncs to retry",
                    synced_count=0
                )
            
            synced = 0
            failed = 0
            errors = []
            logs = []
            
            for sync_log in failed_logs:
                try:
                    # Incrementar contador de reintentos
                    sync_log.retry_count += 1
                    sync_log.status = OdooSyncStatus.SYNCING
                    self.db.commit()
                    
                    # Obtener configuración del sitio
                    site_config = self.db.query(SiteConfig).filter(
                        SiteConfig.site_id == site_id
                    ).first()
                    
                    if not site_config:
                        sync_log.status = OdooSyncStatus.FAILED
                        sync_log.error_message = "Site configuration not found"
                        self.db.commit()
                        failed += 1
                        continue
                    
                    # Reintentar sincronización según el tipo de modelo
                    if sync_log.model_type == OdooModelType.PARTNER:
                        user = self.db.query(User).filter(User.id == sync_log.record_id).first()
                        if user:
                            odoo_id = await self.odoo_service.sync_user_to_odoo(user, site_config)
                            if odoo_id:
                                sync_log.status = OdooSyncStatus.COMPLETED
                                sync_log.odoo_id = int(odoo_id)
                                synced += 1
                            else:
                                sync_log.status = OdooSyncStatus.FAILED
                                sync_log.error_message = "Retry failed"
                                failed += 1
                        else:
                            sync_log.status = OdooSyncStatus.FAILED
                            sync_log.error_message = "User not found"
                            failed += 1
                    
                    elif sync_log.model_type == OdooModelType.PRODUCT:
                        sticker = self.db.query(Sticker).filter(Sticker.id == sync_log.record_id).first()
                        if sticker:
                            odoo_id = await self.odoo_service.sync_sticker_to_odoo(sticker, site_config)
                            if odoo_id:
                                sync_log.status = OdooSyncStatus.COMPLETED
                                sync_log.odoo_id = int(odoo_id)
                                synced += 1
                            else:
                                sync_log.status = OdooSyncStatus.FAILED
                                sync_log.error_message = "Retry failed"
                                failed += 1
                        else:
                            sync_log.status = OdooSyncStatus.FAILED
                            sync_log.error_message = "Sticker not found"
                            failed += 1
                    
                    self.db.commit()
                    logs.append(sync_log)
                    
                except Exception as e:
                    sync_log.status = OdooSyncStatus.FAILED
                    sync_log.error_message = str(e)
                    self.db.commit()
                    
                    failed += 1
                    errors.append(f"Error retrying sync {sync_log.id}: {str(e)}")
                    logger.error("Error retrying sync", 
                                sync_log_id=sync_log.id, 
                                site_id=site_id, 
                                error=str(e))
            
            success = failed == 0
            
            logger.info("Retry failed syncs completed", 
                       site_id=site_id, 
                       synced=synced, 
                       failed=failed,
                       success=success)
            
            return OdooSyncResponse(
                success=success,
                message=f"Retry completed: {synced} synced, {failed} failed",
                synced_count=synced,
                failed_count=failed,
                errors=errors,
                sync_logs=logs
            )
            
        except Exception as e:
            logger.error("Error retrying failed syncs", 
                        site_id=site_id, 
                        error=str(e))
            return OdooSyncResponse(
                success=False,
                message=f"Retry failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def get_sync_statistics(self, site_id: str, days: int = 30) -> Dict[str, Any]:
        """Obtener estadísticas de sincronización"""
        try:
            # Fecha límite
            date_limit = datetime.utcnow() - timedelta(days=days)
            
            # Obtener logs de sincronización
            sync_logs = self.db.query(OdooSyncLog).filter(
                and_(
                    OdooSyncLog.site_id == site_id,
                    OdooSyncLog.sync_timestamp >= date_limit
                )
            ).all()
            
            # Calcular estadísticas
            total_syncs = len(sync_logs)
            successful_syncs = len([log for log in sync_logs if log.status == OdooSyncStatus.COMPLETED])
            failed_syncs = len([log for log in sync_logs if log.status == OdooSyncStatus.FAILED])
            success_rate = (successful_syncs / total_syncs * 100) if total_syncs > 0 else 0
            
            # Sincronizaciones por modelo
            syncs_by_model = {}
            for log in sync_logs:
                model = log.model_type.value
                if model not in syncs_by_model:
                    syncs_by_model[model] = 0
                syncs_by_model[model] += 1
            
            # Sincronizaciones diarias
            daily_syncs = {}
            for log in sync_logs:
                date = log.sync_timestamp.date()
                if date not in daily_syncs:
                    daily_syncs[date] = {"total": 0, "successful": 0, "failed": 0}
                daily_syncs[date]["total"] += 1
                if log.status == OdooSyncStatus.COMPLETED:
                    daily_syncs[date]["successful"] += 1
                elif log.status == OdooSyncStatus.FAILED:
                    daily_syncs[date]["failed"] += 1
            
            # Resumen de errores
            error_summary = {}
            for log in sync_logs:
                if log.status == OdooSyncStatus.FAILED and log.error_message:
                    error = log.error_message
                    if error not in error_summary:
                        error_summary[error] = 0
                    error_summary[error] += 1
            
            return {
                "period": f"{days}d",
                "total_syncs": total_syncs,
                "successful_syncs": successful_syncs,
                "failed_syncs": failed_syncs,
                "success_rate": round(success_rate, 2),
                "syncs_by_model": syncs_by_model,
                "daily_syncs": daily_syncs,
                "error_summary": error_summary
            }
            
        except Exception as e:
            logger.error("Error getting sync statistics", 
                        site_id=site_id, 
                        error=str(e))
            return {
                "period": f"{days}d",
                "total_syncs": 0,
                "successful_syncs": 0,
                "failed_syncs": 0,
                "success_rate": 0.0,
                "syncs_by_model": {},
                "daily_syncs": {},
                "error_summary": {}
            }
