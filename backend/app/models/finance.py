"""Finance models: commission settings, brand payouts, and shopper subscriptions."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, ForeignKey, Enum, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import SubscriptionStatus


class PlatformSettings(Base, TimestampMixin):
    """Singleton (id=1) row holding platform-wide financial settings."""
    __tablename__ = "platform_settings"

    id = Column(Integer, primary_key=True, default=1)
    # Commission the platform takes from every brand sale (percent, 0..100).
    commission_percent = Column(Float, nullable=False, default=10.0)


class Payout(Base, TimestampMixin):
    """A payment recorded as sent from the platform to a brand."""
    __tablename__ = "payouts"

    payout_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.brand_id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    note = Column(String(500), nullable=True)

    __table_args__ = (Index("idx_payouts_brand_id", "brand_id"),)


class SubscriptionPlan(Base, TimestampMixin):
    """A premium plan shoppers can subscribe to (managed by admins)."""
    __tablename__ = "subscription_plans"

    plan_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)          # per interval
    interval = Column(String(20), nullable=False, default="month")  # month | year
    features = Column(String(1000), nullable=True)  # newline-separated bullet list
    is_active = Column(Boolean, nullable=False, default=True)  # visible/subscribable


class Subscription(Base, TimestampMixin):
    """A shopper's subscription to a plan."""
    __tablename__ = "subscriptions"

    subscription_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("subscription_plans.plan_id", ondelete="RESTRICT"), nullable=False, index=True)
    status = Column(Enum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.ACTIVE)
    price_at_subscription = Column(Float, nullable=False)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    current_period_end = Column(DateTime, nullable=True)

    plan = relationship("SubscriptionPlan")

    __table_args__ = (Index("idx_subscriptions_user_id", "user_id"),)
