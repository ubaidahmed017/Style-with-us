"""
Core application modules (configuration, database, auth).
"""

from app.core.config import settings
from app.core.database import engine, AsyncSessionLocal, get_db, Base
from app.core.auth import (
    DecodedToken,
    verify_firebase_token,
    require_role,
    get_current_user,
)
from app.core.firebase import init_firebase, verify_id_token, send_fcm_notification

__all__ = [
    # Config
    "settings",
    # Database
    "engine",
    "AsyncSessionLocal",
    "get_db",
    "Base",
    # Auth
    "DecodedToken",
    "verify_firebase_token",
    "require_role",
    "get_current_user",
    # Firebase
    "init_firebase",
    "verify_id_token",
    "send_fcm_notification",
]
