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
    BrandStatus,
    ReportStatus,
    SubscriptionStatus,
)
from app.models.user import User, UserProfile, INDEFINITE_BLOCK
from app.models.product import Brand, Product, ProductSizeSpec
from app.models.order import Order, OrderItem
from app.models.ml_job import MLJob
from app.models.review import Review
from app.models.report import IssueReport
from app.models.finance import (
    PlatformSettings,
    Payout,
    SubscriptionPlan,
    Subscription,
)

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
    "BrandStatus",
    "ReportStatus",
    "SubscriptionStatus",
    # Models
    "User",
    "UserProfile",
    "INDEFINITE_BLOCK",
    "Brand",
    "Product",
    "ProductSizeSpec",
    "Order",
    "OrderItem",
    "MLJob",
    "Review",
    "IssueReport",
    "PlatformSettings",
    "Payout",
    "SubscriptionPlan",
    "Subscription",
]
