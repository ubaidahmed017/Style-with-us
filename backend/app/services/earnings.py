"""Shared finance calculations: commission, brand earnings, and payouts."""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    PlatformSettings, Payout, OrderItem, Order, Product, Brand,
    OrderStatus, Subscription, SubscriptionStatus,
)


async def get_settings(db: AsyncSession) -> PlatformSettings:
    """Return the singleton platform settings row, creating it if absent."""
    settings = await db.get(PlatformSettings, 1)
    if settings is None:
        settings = PlatformSettings(id=1, commission_percent=10.0)
        db.add(settings)
        await db.flush()
    return settings


async def brand_gross_sales(db: AsyncSession, brand_id) -> float:
    """Sum of confirmed order-item revenue for a brand's products."""
    stmt = (
        select(func.coalesce(func.sum(OrderItem.price_at_purchase * OrderItem.quantity), 0.0))
        .select_from(OrderItem)
        .join(Product, Product.product_id == OrderItem.product_id)
        .join(Order, Order.order_id == OrderItem.order_id)
        .where(Product.brand_id == brand_id, Order.status == OrderStatus.CONFIRMED)
    )
    return float((await db.execute(stmt)).scalar() or 0.0)


async def brand_paid_out(db: AsyncSession, brand_id) -> float:
    stmt = select(func.coalesce(func.sum(Payout.amount), 0.0)).where(Payout.brand_id == brand_id)
    return float((await db.execute(stmt)).scalar() or 0.0)


async def compute_brand_earnings(db: AsyncSession, brand: Brand, commission_percent: float) -> dict:
    gross = await brand_gross_sales(db, brand.brand_id)
    paid = await brand_paid_out(db, brand.brand_id)
    commission_amount = round(gross * commission_percent / 100.0, 2)
    net = round(gross - commission_amount, 2)
    remaining = round(net - paid, 2)
    return {
        "brand_id": str(brand.brand_id),
        "company_name": brand.company_name,
        "status": brand.status.value,
        "gross_sales": round(gross, 2),
        "commission_percent": commission_percent,
        "commission_amount": commission_amount,
        "net_earning": net,
        "paid": round(paid, 2),
        "remaining": remaining,
    }


async def subscription_totals(db: AsyncSession) -> tuple[int, float]:
    """(active subscription count, active subscription revenue per interval)."""
    count_stmt = select(func.count(Subscription.subscription_id)).where(
        Subscription.status == SubscriptionStatus.ACTIVE
    )
    rev_stmt = select(func.coalesce(func.sum(Subscription.price_at_subscription), 0.0)).where(
        Subscription.status == SubscriptionStatus.ACTIVE
    )
    count = int((await db.execute(count_stmt)).scalar() or 0)
    revenue = float((await db.execute(rev_stmt)).scalar() or 0.0)
    return count, round(revenue, 2)
