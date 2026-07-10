"""
Enumeration types for database models.
"""

from enum import Enum as PyEnum


class UserRole(PyEnum):
    """User role enumeration."""
    SHOPPER = "shopper"
    BRAND = "brand"
    ADMIN = "admin"


class Gender(PyEnum):
    """User gender enumeration."""
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"


class GenderTarget(PyEnum):
    """Product gender target enumeration."""
    MALE = "male"
    FEMALE = "female"
    UNISEX = "unisex"


class BodyShape(PyEnum):
    """Body shape classification."""
    HOURGLASS = "hourglass"
    PEAR = "pear"
    APPLE = "apple"
    RECTANGLE = "rectangle"
    INVERTED_TRIANGLE = "inverted_triangle"


class SkinTonePalette(PyEnum):
    """Seasonal color palette for skin tone."""
    WARM_SPRING = "warm_spring"
    WARM_AUTUMN = "warm_autumn"
    COOL_SUMMER = "cool_summer"
    COOL_WINTER = "cool_winter"
    NEUTRAL_LIGHT = "neutral_light"
    NEUTRAL_DEEP = "neutral_deep"


class UnitPreference(PyEnum):
    """User measurement unit preference."""
    METRIC = "metric"  # cm, kg
    IMPERIAL = "imperial"  # inches, lbs


class MLJobStatus(PyEnum):
    """Status of ML processing job."""
    UPLOADED = "uploaded"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class OrderStatus(PyEnum):
    """Status of purchase order."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"


class BrandStatus(PyEnum):
    """Approval status of a brand partner account."""
    PENDING = "pending"      # awaiting admin review
    APPROVED = "approved"    # can list products / be shown to shoppers
    REJECTED = "rejected"    # application declined


class ReportStatus(PyEnum):
    """Status of a user/brand issue report."""
    OPEN = "open"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class SubscriptionStatus(PyEnum):
    """Status of a shopper's premium subscription."""
    ACTIVE = "active"
    CANCELLED = "cancelled"
