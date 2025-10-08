from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Database Configuration
    database_url: str = "postgresql://user:password@localhost:5432/mariachi_fidelizacion_multitenant"
    redis_url: str = "redis://localhost:6379"
    
    # Security
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # External APIs
    instagram_client_id: Optional[str] = None
    instagram_client_secret: Optional[str] = None
    youtube_api_key: Optional[str] = None
    
    # Odoo Configuration
    odoo_url: Optional[str] = None
    odoo_database: Optional[str] = None
    odoo_username: Optional[str] = None
    odoo_password: Optional[str] = None
    
    # Email Configuration
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    
    # Application Settings
    debug: bool = True
    log_level: str = "INFO"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Multi-tenant Settings
    default_site_type: str = "mariachi"
    enable_multi_tenant: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
