from pydantic import BaseModel, validator, Field
from typing import Optional, List, Dict, Any
from app.models.site_config import SiteType
from datetime import datetime

class SiteConfigBase(BaseModel):
    site_id: str = Field(..., min_length=3, max_length=50, description="Unique site identifier")
    site_name: str = Field(..., min_length=1, max_length=100, description="Site display name")
    site_type: SiteType = Field(default=SiteType.MARIACHI, description="Type of business")
    
    # Branding
    primary_color: str = Field(default="#e74c3c", regex="^#[0-9A-Fa-f]{6}$", description="Primary color in hex format")
    secondary_color: str = Field(default="#2c3e50", regex="^#[0-9A-Fa-f]{6}$", description="Secondary color in hex format")
    logo_url: Optional[str] = Field(None, max_length=500, description="URL to site logo")
    favicon_url: Optional[str] = Field(None, max_length=500, description="URL to site favicon")
    
    # Discount configuration
    max_discount_percentage: int = Field(default=15, ge=0, le=100, description="Maximum discount percentage")
    discount_per_action: int = Field(default=5, ge=0, le=50, description="Discount percentage per action")
    sticker_expiration_days: int = Field(default=30, ge=1, le=365, description="Sticker expiration in days")
    
    # Points configuration
    points_per_video: int = Field(default=10, ge=0, le=1000, description="Points per video completion")
    points_per_like: int = Field(default=1, ge=0, le=100, description="Points per like")
    points_per_comment: int = Field(default=2, ge=0, le=100, description="Points per comment")
    points_per_review: int = Field(default=5, ge=0, le=100, description="Points per review")
    
    # Video configuration
    youtube_playlist_id: Optional[str] = Field(None, max_length=100, description="YouTube playlist ID")
    video_progression_enabled: bool = Field(default=True, description="Enable video progression")
    
    # Integration configuration
    instagram_required: bool = Field(default=True, description="Require Instagram follow")
    odoo_integration: bool = Field(default=False, description="Enable Odoo integration")
    odoo_url: Optional[str] = Field(None, max_length=500, description="Odoo server URL")
    odoo_database: Optional[str] = Field(None, max_length=100, description="Odoo database name")
    odoo_username: Optional[str] = Field(None, max_length=100, description="Odoo username")
    odoo_password: Optional[str] = Field(None, max_length=100, description="Odoo password")
    
    # Email configuration
    email_from: Optional[str] = Field(None, max_length=100, description="Email sender address")
    email_signature: Optional[str] = Field(None, description="Email signature")
    
    # Text configuration
    welcome_message: Optional[str] = Field(None, description="Welcome message for new users")
    sticker_message: Optional[str] = Field(None, description="Message for generated stickers")
    video_completion_message: Optional[str] = Field(None, description="Message for video completion")
    
    # Domain configuration
    allowed_domains: Optional[List[str]] = Field(None, description="Allowed domains for this site")

class SiteConfigCreate(SiteConfigBase):
    """Schema for creating a new site configuration"""
    pass

class SiteConfigUpdate(BaseModel):
    """Schema for updating site configuration"""
    site_name: Optional[str] = Field(None, min_length=1, max_length=100)
    site_type: Optional[SiteType] = None
    
    # Branding
    primary_color: Optional[str] = Field(None, regex="^#[0-9A-Fa-f]{6}$")
    secondary_color: Optional[str] = Field(None, regex="^#[0-9A-Fa-f]{6}$")
    logo_url: Optional[str] = Field(None, max_length=500)
    favicon_url: Optional[str] = Field(None, max_length=500)
    
    # Discount configuration
    max_discount_percentage: Optional[int] = Field(None, ge=0, le=100)
    discount_per_action: Optional[int] = Field(None, ge=0, le=50)
    sticker_expiration_days: Optional[int] = Field(None, ge=1, le=365)
    
    # Points configuration
    points_per_video: Optional[int] = Field(None, ge=0, le=1000)
    points_per_like: Optional[int] = Field(None, ge=0, le=100)
    points_per_comment: Optional[int] = Field(None, ge=0, le=100)
    points_per_review: Optional[int] = Field(None, ge=0, le=100)
    
    # Video configuration
    youtube_playlist_id: Optional[str] = Field(None, max_length=100)
    video_progression_enabled: Optional[bool] = None
    
    # Integration configuration
    instagram_required: Optional[bool] = None
    odoo_integration: Optional[bool] = None
    odoo_url: Optional[str] = Field(None, max_length=500)
    odoo_database: Optional[str] = Field(None, max_length=100)
    odoo_username: Optional[str] = Field(None, max_length=100)
    odoo_password: Optional[str] = Field(None, max_length=100)
    
    # Email configuration
    email_from: Optional[str] = Field(None, max_length=100)
    email_signature: Optional[str] = None
    
    # Text configuration
    welcome_message: Optional[str] = None
    sticker_message: Optional[str] = None
    video_completion_message: Optional[str] = None
    
    # Domain configuration
    allowed_domains: Optional[List[str]] = None

class SiteConfigResponse(SiteConfigBase):
    """Schema for site configuration response"""
    id: int
    activo: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class SiteConfigValidation(BaseModel):
    """Schema for site configuration validation response"""
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    site_config: Optional[SiteConfigResponse] = None

class SiteConfigList(BaseModel):
    """Schema for listing site configurations"""
    site_configs: List[SiteConfigResponse]
    total: int
    page: int
    size: int

# Validators
@validator('site_id')
def validate_site_id(cls, v):
    if not v.replace('_', '').replace('-', '').isalnum():
        raise ValueError('Site ID must contain only alphanumeric characters, hyphens, and underscores')
    return v.lower()

@validator('allowed_domains')
def validate_domains(cls, v):
    if v is not None:
        for domain in v:
            if not domain.replace('.', '').replace('-', '').isalnum():
                raise ValueError(f'Invalid domain format: {domain}')
    return v

@validator('max_discount_percentage')
def validate_max_discount(cls, v, values):
    if 'discount_per_action' in values and values['discount_per_action']:
        if v < values['discount_per_action']:
            raise ValueError('Max discount percentage must be greater than or equal to discount per action')
    return v
