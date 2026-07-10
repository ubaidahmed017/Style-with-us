"""Shopper-facing premium subscription plans."""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models import User, SubscriptionPlan, Subscription, SubscriptionStatus
from app.schemas import SubscriptionPlanResponse, SubscriptionResponse, SubscribeRequest

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


def _plan_response(p: SubscriptionPlan) -> SubscriptionPlanResponse:
    return SubscriptionPlanResponse(
        plan_id=p.plan_id, name=p.name, price=p.price, interval=p.interval,
        features=p.features, is_active=p.is_active, created_at=p.created_at.isoformat(),
    )


def _sub_response(s: Subscription, plan_name: str) -> SubscriptionResponse:
    return SubscriptionResponse(
        subscription_id=s.subscription_id,
        plan_id=s.plan_id,
        plan_name=plan_name,
        status=s.status.value,
        price_at_subscription=s.price_at_subscription,
        started_at=s.started_at.isoformat(),
        current_period_end=s.current_period_end.isoformat() if s.current_period_end else None,
    )


@router.get("/plans", response_model=List[SubscriptionPlanResponse])
async def list_active_plans(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[SubscriptionPlanResponse]:
    stmt = select(SubscriptionPlan).where(SubscriptionPlan.is_active == True).order_by(SubscriptionPlan.price)  # noqa: E712
    plans = (await db.execute(stmt)).scalars().all()
    return [_plan_response(p) for p in plans]


async def _active_subscription(db: AsyncSession, user_id) -> Optional[Subscription]:
    stmt = select(Subscription).where(
        Subscription.user_id == user_id,
        Subscription.status == SubscriptionStatus.ACTIVE,
    )
    return (await db.execute(stmt)).scalar_one_or_none()


@router.get("/me", response_model=Optional[SubscriptionResponse])
async def my_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Optional[SubscriptionResponse]:
    sub = await _active_subscription(db, current_user.user_id)
    if not sub:
        return None
    plan = await db.get(SubscriptionPlan, sub.plan_id)
    return _sub_response(sub, plan.name if plan else "")


@router.post("/subscribe", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def subscribe(
    payload: SubscribeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionResponse:
    plan = await db.get(SubscriptionPlan, payload.plan_id)
    if not plan or not plan.is_active:
        raise HTTPException(status_code=404, detail="Plan not found or inactive")

    # Cancel any existing active subscription first.
    existing = await _active_subscription(db, current_user.user_id)
    if existing:
        existing.status = SubscriptionStatus.CANCELLED

    days = 365 if plan.interval == "year" else 30
    now = datetime.utcnow()
    sub = Subscription(
        user_id=current_user.user_id,
        plan_id=plan.plan_id,
        status=SubscriptionStatus.ACTIVE,
        price_at_subscription=plan.price,
        started_at=now,
        current_period_end=now + timedelta(days=days),
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return _sub_response(sub, plan.name)


@router.post("/cancel", status_code=status.HTTP_200_OK)
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    sub = await _active_subscription(db, current_user.user_id)
    if not sub:
        raise HTTPException(status_code=404, detail="No active subscription")
    sub.status = SubscriptionStatus.CANCELLED
    await db.commit()
    return {"status": "cancelled"}
