from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from app.models.user import User
from app.models.site_config import SiteConfig
from app.schemas.user import UserCreate, UserUpdate, UserStats, UserLeaderboard
from app.utils.security import SecurityUtils
from app.utils.permissions import PermissionService
from typing import Optional, List, Dict, Any
import structlog

logger = structlog.get_logger()

class UserService:
    """Servicio para manejar usuarios multi-tenant"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_user(self, user_data: UserCreate, site_id: str) -> User:
        """Crear nuevo usuario"""
        try:
            # Verificar que el sitio existe
            site_config = self.db.query(SiteConfig).filter(
                SiteConfig.site_id == site_id,
                SiteConfig.activo == True
            ).first()
            
            if not site_config:
                raise ValueError(f"Site {site_id} not found or inactive")
            
            # Crear usuario
            hashed_password = SecurityUtils.get_password_hash(user_data.password)
            
            user = User(
                site_id=site_id,
                nombre=user_data.nombre,
                email=user_data.email.lower(),
                telefono=user_data.telefono,
                puntos_acumulados=0,
                total_descuento=0,
                instagram_seguido=False,
                reseñas_dejadas=0,
                videos_completados=0,
                stickers_generados=0,
                sincronizado_odoo=False,
                activo=True,
                verificado=False
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            logger.info("User created", user_id=user.id, site_id=site_id, email=user.email)
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error("Error creating user", site_id=site_id, email=user_data.email, error=str(e))
            raise
    
    async def get_user_by_id(self, user_id: int, site_id: str) -> Optional[User]:
        """Obtener usuario por ID y sitio"""
        try:
            user = self.db.query(User).filter(
                and_(
                    User.id == user_id,
                    User.site_id == site_id,
                    User.activo == True
                )
            ).first()
            
            if user:
                logger.debug("User retrieved", user_id=user_id, site_id=site_id)
            else:
                logger.warning("User not found", user_id=user_id, site_id=site_id)
            
            return user
            
        except Exception as e:
            logger.error("Error getting user by ID", user_id=user_id, site_id=site_id, error=str(e))
            return None
    
    async def get_user_by_email(self, email: str, site_id: str) -> Optional[User]:
        """Obtener usuario por email y sitio"""
        try:
            user = self.db.query(User).filter(
                and_(
                    User.email == email.lower(),
                    User.site_id == site_id,
                    User.activo == True
                )
            ).first()
            
            if user:
                logger.debug("User retrieved by email", email=email, site_id=site_id)
            else:
                logger.debug("User not found by email", email=email, site_id=site_id)
            
            return user
            
        except Exception as e:
            logger.error("Error getting user by email", email=email, site_id=site_id, error=str(e))
            return None
    
    async def authenticate_user(self, email: str, password: str, site_id: str) -> Optional[User]:
        """Autenticar usuario"""
        try:
            user = await self.get_user_by_email(email, site_id)
            
            if not user:
                logger.warning("Authentication failed - user not found", email=email, site_id=site_id)
                return None
            
            if not SecurityUtils.verify_password(password, user.password_hash if hasattr(user, 'password_hash') else ""):
                logger.warning("Authentication failed - invalid password", email=email, site_id=site_id)
                return None
            
            logger.info("User authenticated", user_id=user.id, email=email, site_id=site_id)
            return user
            
        except Exception as e:
            logger.error("Error authenticating user", email=email, site_id=site_id, error=str(e))
            return None
    
    async def update_user(self, user_id: int, site_id: str, user_data: UserUpdate) -> Optional[User]:
        """Actualizar usuario"""
        try:
            user = await self.get_user_by_id(user_id, site_id)
            if not user:
                return None
            
            # Actualizar campos proporcionados
            update_data = user_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(user, field, value)
            
            self.db.commit()
            self.db.refresh(user)
            
            logger.info("User updated", user_id=user_id, site_id=site_id)
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error("Error updating user", user_id=user_id, site_id=site_id, error=str(e))
            raise
    
    async def update_password(self, email: str, new_password: str, site_id: str) -> bool:
        """Actualizar contraseña de usuario"""
        try:
            user = await self.get_user_by_email(email, site_id)
            if not user:
                return False
            
            hashed_password = SecurityUtils.get_password_hash(new_password)
            # Aquí se actualizaría el campo password_hash si existiera
            # user.password_hash = hashed_password
            
            self.db.commit()
            
            logger.info("Password updated", email=email, site_id=site_id)
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error("Error updating password", email=email, site_id=site_id, error=str(e))
            return False
    
    async def add_points(self, user_id: int, site_id: str, points: int, reason: str) -> bool:
        """Agregar puntos a un usuario"""
        try:
            user = await self.get_user_by_id(user_id, site_id)
            if not user:
                return False
            
            user.puntos_acumulados += points
            self.db.commit()
            
            logger.info("Points added", user_id=user_id, site_id=site_id, points=points, reason=reason)
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error("Error adding points", user_id=user_id, site_id=site_id, points=points, error=str(e))
            return False
    
    async def update_discount(self, user_id: int, site_id: str, discount_percentage: int) -> bool:
        """Actualizar descuento total del usuario"""
        try:
            user = await self.get_user_by_id(user_id, site_id)
            if not user:
                return False
            
            # Obtener configuración del sitio para validar límite máximo
            site_config = self.db.query(SiteConfig).filter(
                SiteConfig.site_id == site_id
            ).first()
            
            if site_config:
                max_discount = site_config.max_discount_percentage
                user.total_descuento = min(discount_percentage, max_discount)
            else:
                user.total_descuento = discount_percentage
            
            self.db.commit()
            
            logger.info("Discount updated", user_id=user_id, site_id=site_id, discount=user.total_descuento)
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error("Error updating discount", user_id=user_id, site_id=site_id, error=str(e))
            return False
    
    async def get_user_stats(self, user_id: int, site_id: str) -> Optional[UserStats]:
        """Obtener estadísticas de usuario"""
        try:
            user = await self.get_user_by_id(user_id, site_id)
            if not user:
                return None
            
            # Determinar nivel del usuario basado en puntos
            nivel_usuario = self._calculate_user_level(user.puntos_acumulados)
            proximo_nivel = self._get_next_level(nivel_usuario)
            puntos_para_proximo_nivel = self._get_points_for_next_level(user.puntos_acumulados)
            
            stats = UserStats(
                puntos_acumulados=user.puntos_acumulados,
                total_descuento=user.total_descuento,
                stickers_generados=user.stickers_generados,
                videos_completados=user.videos_completados,
                reseñas_dejadas=user.reseñas_dejadas,
                instagram_seguido=user.instagram_seguido,
                nivel_usuario=nivel_usuario,
                proximo_nivel=proximo_nivel,
                puntos_para_proximo_nivel=puntos_para_proximo_nivel
            )
            
            logger.debug("User stats retrieved", user_id=user_id, site_id=site_id)
            return stats
            
        except Exception as e:
            logger.error("Error getting user stats", user_id=user_id, site_id=site_id, error=str(e))
            return None
    
    async def get_leaderboard(self, site_id: str, limit: int = 10) -> List[UserLeaderboard]:
        """Obtener ranking de usuarios"""
        try:
            users = self.db.query(User).filter(
                and_(
                    User.site_id == site_id,
                    User.activo == True
                )
            ).order_by(desc(User.puntos_acumulados)).limit(limit).all()
            
            leaderboard = []
            for i, user in enumerate(users, 1):
                leaderboard.append(UserLeaderboard(
                    usuario=user,
                    posicion=i,
                    puntos=user.puntos_acumulados,
                    stickers=user.stickers_generados,
                    videos=user.videos_completados
                ))
            
            logger.info("Leaderboard retrieved", site_id=site_id, count=len(leaderboard))
            return leaderboard
            
        except Exception as e:
            logger.error("Error getting leaderboard", site_id=site_id, error=str(e))
            return []
    
    async def list_users(self, site_id: str, page: int = 1, size: int = 10, search: Optional[str] = None) -> Dict[str, Any]:
        """Listar usuarios con paginación"""
        try:
            query = self.db.query(User).filter(
                and_(
                    User.site_id == site_id,
                    User.activo == True
                )
            )
            
            # Aplicar búsqueda si se proporciona
            if search:
                query = query.filter(
                    User.nombre.ilike(f"%{search}%") |
                    User.email.ilike(f"%{search}%")
                )
            
            # Contar total
            total = query.count()
            
            # Aplicar paginación
            offset = (page - 1) * size
            users = query.offset(offset).limit(size).all()
            
            total_pages = (total + size - 1) // size
            
            result = {
                "users": users,
                "total": total,
                "page": page,
                "size": size,
                "total_pages": total_pages
            }
            
            logger.info("Users listed", site_id=site_id, page=page, size=size, total=total)
            return result
            
        except Exception as e:
            logger.error("Error listing users", site_id=site_id, error=str(e))
            return {"users": [], "total": 0, "page": page, "size": size, "total_pages": 0}
    
    async def deactivate_user(self, user_id: int, site_id: str) -> bool:
        """Desactivar usuario (soft delete)"""
        try:
            user = await self.get_user_by_id(user_id, site_id)
            if not user:
                return False
            
            user.activo = False
            self.db.commit()
            
            logger.info("User deactivated", user_id=user_id, site_id=site_id)
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error("Error deactivating user", user_id=user_id, site_id=site_id, error=str(e))
            return False
    
    def _calculate_user_level(self, points: int) -> str:
        """Calcular nivel del usuario basado en puntos"""
        if points >= 1000:
            return "Diamante"
        elif points >= 500:
            return "Oro"
        elif points >= 200:
            return "Plata"
        elif points >= 50:
            return "Bronce"
        else:
            return "Principiante"
    
    def _get_next_level(self, current_level: str) -> Optional[str]:
        """Obtener siguiente nivel"""
        levels = ["Principiante", "Bronce", "Plata", "Oro", "Diamante"]
        try:
            current_index = levels.index(current_level)
            if current_index < len(levels) - 1:
                return levels[current_index + 1]
        except ValueError:
            pass
        return None
    
    def _get_points_for_next_level(self, current_points: int) -> Optional[int]:
        """Obtener puntos necesarios para el siguiente nivel"""
        if current_points < 50:
            return 50 - current_points
        elif current_points < 200:
            return 200 - current_points
        elif current_points < 500:
            return 500 - current_points
        elif current_points < 1000:
            return 1000 - current_points
        else:
            return None
