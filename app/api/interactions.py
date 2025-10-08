from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.site_config import SiteConfig
from app.schemas.interaction import (
    InteractionCreate, InteractionResponse, InteractionStats, InteractionList,
    LikeCreate, LikeResponse, CommentCreate, CommentUpdate, CommentResponse, CommentList,
    ReviewCreate, ReviewUpdate, ReviewResponse, ReviewList, ReviewRating,
    InteractionType, InteractionStatus
)
from app.services.interaction_service import InteractionService
from app.api.dependencies import (
    get_current_user, get_site_config, require_site_access, 
    require_user_ownership, require_active_user
)
from typing import Optional, List
import structlog

logger = structlog.get_logger()

router = APIRouter()

@router.post("/", response_model=InteractionResponse, status_code=status.HTTP_201_CREATED)
async def create_interaction(
    interaction_data: InteractionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear nueva interacción"""
    try:
        interaction_service = InteractionService(db)
        
        interaction = await interaction_service.create_interaction(
            interaction_data=interaction_data,
            user_id=current_user.id,
            site_id=current_user.site_id
        )
        
        if not interaction:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error creating interaction"
            )
        
        logger.info("Interaction created", 
                   interaction_id=interaction.id, 
                   user_id=current_user.id, 
                   site_id=current_user.site_id,
                   tipo=interaction_data.tipo_interaccion.value)
        
        return interaction
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating interaction", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating interaction"
        )

@router.post("/likes", response_model=LikeResponse, status_code=status.HTTP_201_CREATED)
async def create_like(
    like_data: LikeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear like"""
    try:
        interaction_service = InteractionService(db)
        
        like = await interaction_service.create_like(
            like_data=like_data,
            user_id=current_user.id,
            site_id=current_user.site_id
        )
        
        if not like:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error creating like"
            )
        
        logger.info("Like created", 
                   like_id=like.id, 
                   user_id=current_user.id, 
                   site_id=current_user.site_id,
                   contenido_id=like_data.contenido_id)
        
        return like
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating like", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating like"
        )

@router.delete("/likes/{contenido_id}/{contenido_tipo}")
async def remove_like(
    contenido_id: int,
    contenido_tipo: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remover like"""
    try:
        interaction_service = InteractionService(db)
        
        success = await interaction_service.remove_like(
            contenido_id=contenido_id,
            contenido_tipo=contenido_tipo,
            user_id=current_user.id,
            site_id=current_user.site_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Like not found"
            )
        
        logger.info("Like removed", 
                   user_id=current_user.id, 
                   site_id=current_user.site_id,
                   contenido_id=contenido_id)
        
        return {"message": "Like removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error removing like", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error removing like"
        )

@router.post("/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear comentario"""
    try:
        interaction_service = InteractionService(db)
        
        comment = await interaction_service.create_comment(
            comment_data=comment_data,
            user_id=current_user.id,
            site_id=current_user.site_id
        )
        
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error creating comment"
            )
        
        logger.info("Comment created", 
                   comment_id=comment.id, 
                   user_id=current_user.id, 
                   site_id=current_user.site_id,
                   contenido_id=comment_data.contenido_id)
        
        return comment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating comment", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating comment"
        )

@router.put("/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: int,
    comment_data: CommentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar comentario"""
    try:
        from app.models.interaction import Comment
        
        # Verificar que el comentario existe y pertenece al usuario
        comment = db.query(Comment).filter(
            Comment.id == comment_id,
            Comment.usuario_id == current_user.id,
            Comment.site_id == current_user.site_id
        ).first()
        
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )
        
        # Actualizar comentario
        comment.comentario = comment_data.comentario
        comment.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(comment)
        
        logger.info("Comment updated", 
                   comment_id=comment_id, 
                   user_id=current_user.id, 
                   site_id=current_user.site_id)
        
        return comment
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error updating comment", 
                    comment_id=comment_id, 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating comment"
        )

@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar comentario"""
    try:
        from app.models.interaction import Comment
        
        # Verificar que el comentario existe y pertenece al usuario
        comment = db.query(Comment).filter(
            Comment.id == comment_id,
            Comment.usuario_id == current_user.id,
            Comment.site_id == current_user.site_id
        ).first()
        
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )
        
        # Marcar como eliminado (soft delete)
        comment.status = InteractionStatus.DELETED
        comment.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info("Comment deleted", 
                   comment_id=comment_id, 
                   user_id=current_user.id, 
                   site_id=current_user.site_id)
        
        return {"message": "Comment deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error deleting comment", 
                    comment_id=comment_id, 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting comment"
        )

@router.post("/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear reseña"""
    try:
        interaction_service = InteractionService(db)
        
        review = await interaction_service.create_review(
            review_data=review_data,
            user_id=current_user.id,
            site_id=current_user.site_id
        )
        
        if not review:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error creating review"
            )
        
        logger.info("Review created", 
                   review_id=review.id, 
                   user_id=current_user.id, 
                   site_id=current_user.site_id,
                   contenido_id=review_data.contenido_id,
                   calificacion=review_data.calificacion.value)
        
        return review
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating review", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating review"
        )

@router.put("/reviews/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: int,
    review_data: ReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar reseña"""
    try:
        from app.models.interaction import Review
        
        # Verificar que la reseña existe y pertenece al usuario
        review = db.query(Review).filter(
            Review.id == review_id,
            Review.usuario_id == current_user.id,
            Review.site_id == current_user.site_id
        ).first()
        
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )
        
        # Actualizar reseña
        if review_data.calificacion is not None:
            review.calificacion = review_data.calificacion
        if review_data.titulo is not None:
            review.titulo = review_data.titulo
        if review_data.comentario is not None:
            review.comentario = review_data.comentario
        
        review.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(review)
        
        logger.info("Review updated", 
                   review_id=review_id, 
                   user_id=current_user.id, 
                   site_id=current_user.site_id)
        
        return review
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error updating review", 
                    review_id=review_id, 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating review"
        )

@router.delete("/reviews/{review_id}")
async def delete_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar reseña"""
    try:
        from app.models.interaction import Review
        
        # Verificar que la reseña existe y pertenece al usuario
        review = db.query(Review).filter(
            Review.id == review_id,
            Review.usuario_id == current_user.id,
            Review.site_id == current_user.site_id
        ).first()
        
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )
        
        # Marcar como eliminada (soft delete)
        review.status = InteractionStatus.DELETED
        review.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info("Review deleted", 
                   review_id=review_id, 
                   user_id=current_user.id, 
                   site_id=current_user.site_id)
        
        return {"message": "Review deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error deleting review", 
                    review_id=review_id, 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting review"
        )

@router.get("/content/{contenido_id}/{contenido_tipo}")
async def get_content_interactions(
    contenido_id: int,
    contenido_tipo: str,
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(20, ge=1, le=100, description="Tamaño de página"),
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Obtener interacciones de un contenido específico"""
    try:
        interaction_service = InteractionService(db)
        
        interactions = await interaction_service.get_content_interactions(
            contenido_id=contenido_id,
            contenido_tipo=contenido_tipo,
            site_id=site_config.site_id,
            page=page,
            size=size
        )
        
        logger.info("Content interactions retrieved", 
                   contenido_id=contenido_id, 
                   contenido_tipo=contenido_tipo, 
                   site_id=site_config.site_id)
        
        return interactions
        
    except Exception as e:
        logger.error("Error getting content interactions", 
                    contenido_id=contenido_id, 
                    contenido_tipo=contenido_tipo, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving content interactions"
        )

@router.get("/me", response_model=InteractionList)
async def get_my_interactions(
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(20, ge=1, le=100, description="Tamaño de página"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener interacciones del usuario actual"""
    try:
        interaction_service = InteractionService(db)
        
        result = await interaction_service.get_user_interactions(
            user_id=current_user.id,
            site_id=current_user.site_id,
            page=page,
            size=size
        )
        
        logger.info("User interactions retrieved", 
                   user_id=current_user.id, 
                   site_id=current_user.site_id, 
                   total=result["total"])
        
        return InteractionList(**result)
        
    except Exception as e:
        logger.error("Error getting user interactions", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user interactions"
        )

@router.get("/me/stats", response_model=InteractionStats)
async def get_my_interaction_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas de interacciones del usuario actual"""
    try:
        interaction_service = InteractionService(db)
        
        stats = await interaction_service.get_interaction_stats(
            site_id=current_user.site_id,
            user_id=current_user.id
        )
        
        logger.info("User interaction stats retrieved", 
                   user_id=current_user.id, 
                   site_id=current_user.site_id)
        
        return stats
        
    except Exception as e:
        logger.error("Error getting user interaction stats", 
                    user_id=current_user.id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user interaction statistics"
        )

@router.get("/stats/global", response_model=InteractionStats)
async def get_global_interaction_stats(
    site_config: SiteConfig = Depends(get_site_config),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas globales de interacciones del sitio"""
    try:
        interaction_service = InteractionService(db)
        
        stats = await interaction_service.get_interaction_stats(
            site_id=site_config.site_id
        )
        
        logger.info("Global interaction stats retrieved", 
                   site_id=site_config.site_id)
        
        return stats
        
    except Exception as e:
        logger.error("Error getting global interaction stats", 
                    site_id=site_config.site_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving global interaction statistics"
        )
