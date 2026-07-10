"""
User and UserProfile models.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, ForeignKey, Enum, Index, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import UserRole, Gender, BodyShape, SkinTonePalette, UnitPreference

# Sentinel far-future date used for an indefinite block (until admin unblocks).
INDEFINITE_BLOCK = datetime(9999, 12, 31)


class User(Base, TimestampMixin):
    """User account model (Firebase-backed)."""

    __tablename__ = "users"

    user_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    firebase_uid = Column(
        String(128),
        unique=True,
        nullable=False,
        index=True
    )
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    role = Column(
        Enum(UserRole),
        nullable=False,
        default=UserRole.SHOPPER
    )

    # Moderation: when set to a future time, the account is blocked until then.
    # INDEFINITE_BLOCK (year 9999) means blocked until an admin unblocks.
    blocked_until = Column(DateTime, nullable=True)
    block_reason = Column(String(500), nullable=True)

    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    brand = relationship("Brand", back_populates="user", uselist=False, cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    ml_jobs = relationship("MLJob", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_users_firebase_uid", "firebase_uid"),
    )

    @property
    def is_blocked(self) -> bool:
        """True if the account is currently blocked."""
        return self.blocked_until is not None and self.blocked_until > datetime.utcnow()

    @property
    def block_is_indefinite(self) -> bool:
        return self.blocked_until == INDEFINITE_BLOCK


class UserProfile(Base, TimestampMixin):
    """Shopper profile with measurements and body analysis results."""

    __tablename__ = "user_profiles"

    profile_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    # Gender is mandatory
    gender = Column(
        Enum(Gender),
        nullable=False
    )

    # Measurements (stored in metric: cm, kg)
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    age = Column(Integer, nullable=True)
    chest_cm = Column(Float, nullable=True)
    waist_cm = Column(Float, nullable=True)
    hips_cm = Column(Float, nullable=True)
    inseam_cm = Column(Float, nullable=True)
    shoulder_width_cm = Column(Float, nullable=True)

    # Body analysis results (on-device analysis)
    body_shape = Column(Enum(BodyShape), nullable=True)
    skin_tone_hex = Column(String(7), nullable=True)  # e.g., "#C68642"
    skin_tone_palette = Column(Enum(SkinTonePalette), nullable=True)

    # User preferences
    unit_preference = Column(
        Enum(UnitPreference),
        default=UnitPreference.METRIC,
        nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="profile")

    __table_args__ = (
        Index("idx_user_profiles_user_id", "user_id"),
    )
