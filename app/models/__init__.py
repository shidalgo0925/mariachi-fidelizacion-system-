# Import all models to ensure they are registered with SQLAlchemy
from .site_config import SiteConfig
from .user import User
from .sticker import Sticker
from .instagram_user import InstagramUser
from .notification import Notification
from .video import Video, VideoCompletion, VideoWatchSession
from .interaction import Interaction, Like, Comment, Review, InteractionReport, InteractionModeration
from .odoo_sync_log import OdooSyncLog, OdooConfig, OdooWebhook, OdooReport
from .notification_template import NotificationTemplate, NotificationSubscription, NotificationPreferences, NotificationDigest, NotificationCampaign

__all__ = [
    "SiteConfig",
    "User", 
    "Sticker",
    "Video",
    "VideoCompletion",
    "VideoWatchSession",
    "Interaction",
    "Like",
    "Comment",
    "Review",
    "InteractionReport",
    "InteractionModeration",
    "OdooSyncLog",
    "OdooConfig",
    "OdooWebhook",
    "OdooReport",
    "NotificationTemplate",
    "NotificationSubscription",
    "NotificationPreferences",
    "NotificationDigest",
    "NotificationCampaign",
    "InstagramUser",
    "Notification"
]
