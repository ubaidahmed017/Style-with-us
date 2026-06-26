"""
Database models package.
"""

from app.models.base import Base, TimestampMixin
from app.models.enums import (
    UserRole,
    Gender,
    GenderTarget,
    BodyShape,
    SkinTonePalette,
    UnitPreference,
    MLJobStatus,
    OrderStatus,
)
from app.models.user import User, UserProfile
from app.models.product import Brand, Product, ProductSizeSpec
from app.models.order import Order, OrderItem
from app.models.ml_job import MLJob

__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    # Enums
    "UserRole",
    "Gender",
    "GenderTarget",
    "BodyShape",
    "SkinTonePalette",
    "UnitPreference",
    "MLJobStatus",
    "OrderStatus",
    # Models
    "User",
    "UserProfile",
    "Brand",
    "Product",
    "ProductSizeSpec",
    "Order",
    "OrderItem",
    "MLJob",
]
