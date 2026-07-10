"""Schemas for commission settings, payouts, earnings, and subscriptions."""

from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, field_validator


# ----- Commission / platform settings -----
class PlatformSettingsResponse(BaseModel):
    commission_percent: float


class PlatformSettingsUpdate(BaseModel):
    commission_percent: float

    @field_validator("commission_percent")
    @classmethod
    def pct_range(cls, v: float) -> float:
        if v < 0 or v > 100:
            raise ValueError("commission_percent must be between 0 and 100")
        return v


# ----- Payouts -----
class PayoutCreate(BaseModel):
    amount: float
    note: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("amount must be greater than zero")
        return v


class PayoutResponse(BaseModel):
    payout_id: UUID
    brand_id: UUID
    amount: float
    note: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


# ----- Earnings -----
class BrandEarnings(BaseModel):
    brand_id: str
    company_name: str
    status: str
    gross_sales: float
    commission_percent: float
    commission_amount: float
    net_earning: float
    paid: float
    remaining: float


class FinanceOverview(BaseModel):
    commission_percent: float
    total_gross_sales: float
    total_commission: float
    total_brand_net: float
    total_paid_out: float
    total_owed_to_brands: float
    subscription_active_count: int
    subscription_revenue: float
    total_platform_revenue: float  # commission + subscription revenue


# ----- Subscription plans -----
class SubscriptionPlanCreate(BaseModel):
    name: str
    price: float
    interval: str = "month"
    features: Optional[str] = None
    is_active: bool = True

    @field_validator("price")
    @classmethod
    def non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("price must be non-negative")
        return v


class SubscriptionPlanUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    interval: Optional[str] = None
    features: Optional[str] = None
    is_active: Optional[bool] = None


class SubscriptionPlanResponse(BaseModel):
    plan_id: UUID
    name: str
    price: float
    interval: str
    features: Optional[str] = None
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


class SubscriptionResponse(BaseModel):
    subscription_id: UUID
    plan_id: UUID
    plan_name: str
    status: str
    price_at_subscription: float
    started_at: str
    current_period_end: Optional[str] = None


class SubscribeRequest(BaseModel):
    plan_id: UUID
