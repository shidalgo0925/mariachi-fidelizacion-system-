from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.site_config import SiteConfig
from app.schemas.sticker import (
    StickerCreate, StickerResponse, StickerUpdate, StickerStats,
    StickerValidation, StickerValidationResponse, StickerList,
    StickerSearch, StickerDownload, StickerFormat, StickerType
)
from app.services.sticker_service import StickerService
from app.api.dependencies import (
    get_current_user, get_site_config, require_site_access, 
    require_user_ownership, require_active_user
)
from typing import Optional, List
import structlog
from datetime import datetime, timedelta
import os

logger = structlog.get_logger()

router = APIRouter()

@router.post("/", response_model=StickerResponse, status_code=status.HTTP_201_CREATED)
async def create_sticker(
    sticker_data: StickerCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear nuevo sticker para el usuario actual"""
    try:
        sticker_service = StickerService(db)
        
        # Crear sticker
        sticker = await sticker_service.create_sticker(
            sticker_data=sticker_data,
            site_id=current_user.site_id,
            user_id=current_user.id
        )
        
        if not sticker:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error creating sticker. Check discount limits and user status."
            )
        
        logger.info("Sticker created", 
                   sticker_id=sticker.id, 
                   user_id=current_user.id, 
                   site_id=current_user.site_id)
        
        return sticker
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating sticker", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating sticker"
        )

@router.get("/me", response_model=StickerList)
async def get_my_stickers(
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(10, ge=1, le=100, description="Tamaño de página"),
    tipo_sticker: Optional[StickerType] = Query(None, description="Filtrar por tipo de sticker"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener stickers del usuario actual"""
    try:
        sticker_service = StickerService(db)
        
        result = await sticker_service.get_user_stickers(
            user_id=current_user.id,
            site_id=current_user.site_id,
            page=page,
            size=size,
            tipo_sticker=tipo_sticker
        )
        
        logger.info("User stickers retrieved", 
                   user_id=current_user.id, 
                   site_id=current_user.site_id, 
                   page=page)
        
        return StickerList(**result)
        
    except Exception as e:
        logger.error("Error getting user stickers", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving stickers"
        )

@router.get("/me/stats", response_model=StickerStats)
async def get_my_sticker_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas de stickers del usuario actual"""
    try:
        sticker_service = StickerService(db)
        
        stats = await sticker_service.get_sticker_stats(
            site_id=current_user.site_id,
            user_id=current_user.id
        )
        
        logger.info("User sticker stats retrieved", 
                   user_id=current_user.id, 
                   site_id=current_user.site_id)
        
        return stats
        
    except Exception as e:
        logger.error("Error getting user sticker stats", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving sticker stats"
        )

@router.get("/{sticker_id}", response_model=StickerResponse)
async def get_sticker_by_id(
    sticker_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener sticker por ID (solo si pertenece al usuario)"""
    try:
        sticker_service = StickerService(db)
        
        sticker = await sticker_service.get_sticker_by_id(sticker_id, current_user.site_id)
        
        if not sticker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sticker not found"
            )
        
        # Verificar que el sticker pertenece al usuario
        if sticker.usuario_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        logger.info("Sticker retrieved by ID", 
                   sticker_id=sticker_id, 
                   user_id=current_user.id)
        
        return sticker
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting sticker by ID", 
                    sticker_id=sticker_id, 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving sticker"
        )

@router.post("/validate", response_model=StickerValidationResponse)
async def validate_sticker(
    validation_data: StickerValidation,
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Validar código de descuento"""
    try:
        sticker_service = StickerService(db)
        
        response = await sticker_service.validate_sticker(
            validation_data=validation_data,
            site_id=site_config.site_id
        )
        
        logger.info("Sticker validation requested", 
                   codigo=validation_data.codigo_descuento, 
                   site_id=site_config.site_id,
                   valido=response.valido)
        
        return response
        
    except Exception as e:
        logger.error("Error validating sticker", 
                    codigo=validation_data.codigo_descuento, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error validating sticker"
        )

@router.post("/use/{codigo}")
async def use_sticker(
    codigo: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Usar código de descuento"""
    try:
        sticker_service = StickerService(db)
        
        success = await sticker_service.use_sticker(
            codigo=codigo,
            site_id=current_user.site_id,
            usuario_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error using sticker. Check if code is valid and not expired."
            )
        
        logger.info("Sticker used", 
                   codigo=codigo, 
                   user_id=current_user.id, 
                   site_id=current_user.site_id)
        
        return {"message": "Sticker used successfully", "codigo": codigo}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error using sticker", 
                    codigo=codigo, 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error using sticker"
        )

@router.get("/download/{sticker_id}")
async def download_sticker(
    sticker_id: int,
    formato: StickerFormat = Query(StickerFormat.PNG, description="Formato de descarga"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Descargar sticker en formato específico"""
    try:
        sticker_service = StickerService(db)
        
        sticker = await sticker_service.get_sticker_by_id(sticker_id, current_user.site_id)
        
        if not sticker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sticker not found"
            )
        
        # Verificar que el sticker pertenece al usuario
        if sticker.usuario_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Determinar archivo a descargar
        if formato == StickerFormat.PNG and sticker.imagen_url:
            file_path = f"static/pdfs/{os.path.basename(sticker.imagen_url)}"
        elif formato == StickerFormat.PDF:
            # Generar PDF si no existe
            from app.utils.pdf_generator import PDFGenerator
            pdf_generator = PDFGenerator()
            
            sticker_data = {
                'codigo_descuento': sticker.codigo_descuento,
                'porcentaje_descuento': sticker.porcentaje_descuento,
                'tipo_sticker': sticker.tipo_sticker.value,
                'fecha_expiracion': sticker.fecha_expiracion.strftime('%d/%m/%Y'),
                'usuario_nombre': current_user.nombre,
                'fecha_generacion': sticker.fecha_generacion.strftime('%d/%m/%Y'),
                'qr_code_url': sticker.qr_code_url
            }
            
            site_config_data = {
                'site_name': 'Mariachi Sol del Águila',  # Esto debería venir de la configuración
                'primary_color': '#e74c3c',
                'secondary_color': '#2c3e50'
            }
            
            filename = f"sticker_{sticker_id}.pdf"
            pdf_url = await pdf_generator.generate_sticker_pdf(
                sticker_data=sticker_data,
                site_config=site_config_data,
                filename=filename
            )
            
            if not pdf_url:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error generating PDF"
                )
            
            file_path = f"static/pdfs/{filename}"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format not available for this sticker"
            )
        
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Determinar tipo de contenido
        content_type = "image/png" if formato == StickerFormat.PNG else "application/pdf"
        
        logger.info("Sticker downloaded", 
                   sticker_id=sticker_id, 
                   formato=formato.value, 
                   user_id=current_user.id)
        
        return FileResponse(
            path=file_path,
            media_type=content_type,
            filename=f"sticker_{sticker_id}.{formato.value}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error downloading sticker", 
                    sticker_id=sticker_id, 
                    formato=formato.value, 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error downloading sticker"
        )

@router.get("/search", response_model=StickerList)
async def search_stickers(
    query: Optional[str] = Query(None, description="Término de búsqueda"),
    tipo_sticker: Optional[StickerType] = Query(None, description="Filtrar por tipo"),
    usado: Optional[bool] = Query(None, description="Filtrar por estado de uso"),
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(10, ge=1, le=100, description="Tamaño de página"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Buscar stickers del usuario actual"""
    try:
        sticker_service = StickerService(db)
        
        # Por ahora, solo buscar en los stickers del usuario
        result = await sticker_service.get_user_stickers(
            user_id=current_user.id,
            site_id=current_user.site_id,
            page=page,
            size=size,
            tipo_sticker=tipo_sticker
        )
        
        # Filtrar por query si se proporciona
        if query:
            filtered_stickers = [
                sticker for sticker in result["stickers"]
                if query.lower() in sticker.codigo_descuento.lower()
            ]
            result["stickers"] = filtered_stickers
            result["total"] = len(filtered_stickers)
        
        # Filtrar por estado de uso si se proporciona
        if usado is not None:
            filtered_stickers = [
                sticker for sticker in result["stickers"]
                if sticker.usado == usado
            ]
            result["stickers"] = filtered_stickers
            result["total"] = len(filtered_stickers)
        
        logger.info("Stickers search performed", 
                   user_id=current_user.id, 
                   query=query, 
                   page=page)
        
        return StickerList(**result)
        
    except Exception as e:
        logger.error("Error searching stickers", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error searching stickers"
        )

@router.delete("/{sticker_id}")
async def delete_sticker(
    sticker_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar sticker (solo si no ha sido usado)"""
    try:
        sticker_service = StickerService(db)
        
        sticker = await sticker_service.get_sticker_by_id(sticker_id, current_user.site_id)
        
        if not sticker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sticker not found"
            )
        
        # Verificar que el sticker pertenece al usuario
        if sticker.usuario_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Verificar que no ha sido usado
        if sticker.usado:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete used sticker"
            )
        
        # Eliminar sticker
        db.delete(sticker)
        db.commit()
        
        logger.info("Sticker deleted", 
                   sticker_id=sticker_id, 
                   user_id=current_user.id)
        
        return {"message": "Sticker deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        self.db.rollback()
        logger.error("Error deleting sticker", 
                    sticker_id=sticker_id, 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting sticker"
        )

@router.get("/stats/global", response_model=StickerStats)
async def get_global_sticker_stats(
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas globales de stickers del sitio"""
    try:
        sticker_service = StickerService(db)
        
        stats = await sticker_service.get_sticker_stats(
            site_id=site_config.site_id
        )
        
        logger.info("Global sticker stats retrieved", 
                   site_id=site_config.site_id)
        
        return stats
        
    except Exception as e:
        logger.error("Error getting global sticker stats", 
                    site_id=site_config.site_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving global sticker stats"
        )
