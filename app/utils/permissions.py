from enum import Enum
from typing import List, Dict, Any
from app.models.user import User
from app.models.site_config import SiteConfig, SiteType
import structlog

logger = structlog.get_logger()

class Permission(str, Enum):
    """Permisos disponibles en el sistema"""
    # Permisos de usuario
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # Permisos de stickers
    STICKER_CREATE = "sticker:create"
    STICKER_READ = "sticker:read"
    STICKER_UPDATE = "sticker:update"
    STICKER_DELETE = "sticker:delete"
    
    # Permisos de videos
    VIDEO_READ = "video:read"
    VIDEO_COMPLETE = "video:complete"
    
    # Permisos de interacciones
    INTERACTION_CREATE = "interaction:create"
    INTERACTION_READ = "interaction:read"
    INTERACTION_UPDATE = "interaction:update"
    INTERACTION_DELETE = "interaction:delete"
    
    # Permisos de administración
    ADMIN_READ = "admin:read"
    ADMIN_UPDATE = "admin:update"
    ADMIN_DELETE = "admin:delete"

class Role(str, Enum):
    """Roles disponibles en el sistema"""
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class PermissionService:
    """Servicio para manejar permisos y roles"""
    
    # Mapeo de roles a permisos
    ROLE_PERMISSIONS: Dict[Role, List[Permission]] = {
        Role.USER: [
            Permission.USER_READ,
            Permission.USER_UPDATE,
            Permission.STICKER_CREATE,
            Permission.STICKER_READ,
            Permission.VIDEO_READ,
            Permission.VIDEO_COMPLETE,
            Permission.INTERACTION_CREATE,
            Permission.INTERACTION_READ,
        ],
        Role.MODERATOR: [
            Permission.USER_READ,
            Permission.USER_UPDATE,
            Permission.STICKER_CREATE,
            Permission.STICKER_READ,
            Permission.STICKER_UPDATE,
            Permission.VIDEO_READ,
            Permission.VIDEO_COMPLETE,
            Permission.INTERACTION_CREATE,
            Permission.INTERACTION_READ,
            Permission.INTERACTION_UPDATE,
            Permission.ADMIN_READ,
        ],
        Role.ADMIN: [
            Permission.USER_READ,
            Permission.USER_UPDATE,
            Permission.USER_DELETE,
            Permission.STICKER_CREATE,
            Permission.STICKER_READ,
            Permission.STICKER_UPDATE,
            Permission.STICKER_DELETE,
            Permission.VIDEO_READ,
            Permission.VIDEO_COMPLETE,
            Permission.INTERACTION_CREATE,
            Permission.INTERACTION_READ,
            Permission.INTERACTION_UPDATE,
            Permission.INTERACTION_DELETE,
            Permission.ADMIN_READ,
            Permission.ADMIN_UPDATE,
        ],
        Role.SUPER_ADMIN: [
            # Todos los permisos
            *[permission for permission in Permission]
        ]
    }
    
    # Permisos específicos por tipo de sitio
    SITE_TYPE_PERMISSIONS: Dict[SiteType, List[Permission]] = {
        SiteType.MARIACHI: [
            Permission.STICKER_CREATE,
            Permission.VIDEO_READ,
            Permission.VIDEO_COMPLETE,
            Permission.INTERACTION_CREATE,
        ],
        SiteType.RESTAURANT: [
            Permission.STICKER_CREATE,
            Permission.VIDEO_READ,
            Permission.VIDEO_COMPLETE,
            Permission.INTERACTION_CREATE,
        ],
        SiteType.ECOMMERCE: [
            Permission.STICKER_CREATE,
            Permission.VIDEO_READ,
            Permission.VIDEO_COMPLETE,
            Permission.INTERACTION_CREATE,
        ],
        SiteType.SERVICES: [
            Permission.STICKER_CREATE,
            Permission.VIDEO_READ,
            Permission.VIDEO_COMPLETE,
            Permission.INTERACTION_CREATE,
        ],
        SiteType.GENERAL: [
            Permission.STICKER_CREATE,
            Permission.VIDEO_READ,
            Permission.VIDEO_COMPLETE,
            Permission.INTERACTION_CREATE,
        ]
    }
    
    @classmethod
    def get_user_permissions(cls, user: User, site_config: SiteConfig) -> List[Permission]:
        """Obtener permisos de un usuario en un sitio específico"""
        try:
            # Obtener permisos base del rol (por defecto USER)
            user_role = cls._get_user_role(user)
            base_permissions = cls.ROLE_PERMISSIONS.get(user_role, cls.ROLE_PERMISSIONS[Role.USER])
            
            # Obtener permisos específicos del tipo de sitio
            site_permissions = cls.SITE_TYPE_PERMISSIONS.get(site_config.site_type, [])
            
            # Combinar permisos (intersección)
            user_permissions = list(set(base_permissions) & set(site_permissions))
            
            # Agregar permisos adicionales basados en el estado del usuario
            additional_permissions = cls._get_additional_permissions(user, site_config)
            user_permissions.extend(additional_permissions)
            
            # Remover duplicados
            user_permissions = list(set(user_permissions))
            
            logger.debug("User permissions calculated", 
                        user_id=user.id, 
                        site_id=site_config.site_id, 
                        role=user_role,
                        permissions=user_permissions)
            
            return user_permissions
            
        except Exception as e:
            logger.error("Error calculating user permissions", 
                        user_id=user.id, 
                        site_id=site_config.site_id, 
                        error=str(e))
            return cls.ROLE_PERMISSIONS[Role.USER]  # Permisos mínimos por defecto
    
    @classmethod
    def has_permission(cls, user: User, site_config: SiteConfig, permission: Permission) -> bool:
        """Verificar si un usuario tiene un permiso específico"""
        user_permissions = cls.get_user_permissions(user, site_config)
        return permission in user_permissions
    
    @classmethod
    def has_any_permission(cls, user: User, site_config: SiteConfig, permissions: List[Permission]) -> bool:
        """Verificar si un usuario tiene alguno de los permisos especificados"""
        user_permissions = cls.get_user_permissions(user, site_config)
        return any(permission in user_permissions for permission in permissions)
    
    @classmethod
    def has_all_permissions(cls, user: User, site_config: SiteConfig, permissions: List[Permission]) -> bool:
        """Verificar si un usuario tiene todos los permisos especificados"""
        user_permissions = cls.get_user_permissions(user, site_config)
        return all(permission in user_permissions for permission in permissions)
    
    @classmethod
    def can_access_resource(cls, user: User, site_config: SiteConfig, resource_type: str, action: str) -> bool:
        """Verificar si un usuario puede acceder a un recurso específico"""
        permission_name = f"{resource_type}:{action}"
        
        try:
            permission = Permission(permission_name)
            return cls.has_permission(user, site_config, permission)
        except ValueError:
            logger.warning("Unknown permission", permission=permission_name)
            return False
    
    @classmethod
    def _get_user_role(cls, user: User) -> Role:
        """Determinar el rol de un usuario"""
        # Por ahora, todos los usuarios tienen rol USER
        # En el futuro, esto se puede expandir con un campo de rol en la base de datos
        return Role.USER
    
    @classmethod
    def _get_additional_permissions(cls, user: User, site_config: SiteConfig) -> List[Permission]:
        """Obtener permisos adicionales basados en el estado del usuario"""
        additional_permissions = []
        
        # Usuarios verificados pueden tener permisos adicionales
        if user.verificado:
            additional_permissions.append(Permission.INTERACTION_UPDATE)
        
        # Usuarios con Instagram verificado pueden tener permisos adicionales
        if user.instagram_seguido and site_config.instagram_required:
            additional_permissions.append(Permission.STICKER_CREATE)
        
        # Usuarios con muchos puntos pueden tener permisos adicionales
        if user.puntos_acumulados > 100:
            additional_permissions.append(Permission.INTERACTION_UPDATE)
        
        return additional_permissions
    
    @classmethod
    def get_permission_description(cls, permission: Permission) -> str:
        """Obtener descripción de un permiso"""
        descriptions = {
            Permission.USER_READ: "Leer información de usuario",
            Permission.USER_UPDATE: "Actualizar información de usuario",
            Permission.USER_DELETE: "Eliminar usuario",
            Permission.STICKER_CREATE: "Crear stickers de descuento",
            Permission.STICKER_READ: "Leer stickers",
            Permission.STICKER_UPDATE: "Actualizar stickers",
            Permission.STICKER_DELETE: "Eliminar stickers",
            Permission.VIDEO_READ: "Ver videos",
            Permission.VIDEO_COMPLETE: "Completar videos",
            Permission.INTERACTION_CREATE: "Crear interacciones",
            Permission.INTERACTION_READ: "Leer interacciones",
            Permission.INTERACTION_UPDATE: "Actualizar interacciones",
            Permission.INTERACTION_DELETE: "Eliminar interacciones",
            Permission.ADMIN_READ: "Acceso de lectura administrativo",
            Permission.ADMIN_UPDATE: "Acceso de actualización administrativo",
            Permission.ADMIN_DELETE: "Acceso de eliminación administrativo",
        }
        
        return descriptions.get(permission, "Permiso desconocido")
    
    @classmethod
    def get_role_description(cls, role: Role) -> str:
        """Obtener descripción de un rol"""
        descriptions = {
            Role.USER: "Usuario estándar con permisos básicos",
            Role.MODERATOR: "Moderador con permisos de edición",
            Role.ADMIN: "Administrador con permisos completos",
            Role.SUPER_ADMIN: "Super administrador con todos los permisos",
        }
        
        return descriptions.get(role, "Rol desconocido")
