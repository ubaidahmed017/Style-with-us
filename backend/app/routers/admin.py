"""
Admin dashboard and analytics endpoints (Admin only).
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.auth import get_current_user, require_role
from app.core.database import get_db
from app.models import (
    User, UserRole, Order, Brand, Product, MLJob, INDEFINITE_BLOCK,
    BrandStatus, IssueReport, ReportStatus, Payout, SubscriptionPlan, Subscription,
)
from app.models.enums import OrderStatus, MLJobStatus
from app.schemas import (
    UserResponse, ReportResponse, ReportUpdate,
    PlatformSettingsResponse, PlatformSettingsUpdate, PayoutCreate, PayoutResponse,
    BrandEarnings, FinanceOverview, SubscriptionPlanCreate, SubscriptionPlanUpdate,
    SubscriptionPlanResponse,
)
from app.services.earnings import (
    get_settings, compute_brand_earnings, subscription_totals, brand_paid_out, brand_gross_sales,
)

router = APIRouter(prefix="/admin", tags=["admin"])


# Response schemas
class AnalyticsOverview(BaseModel):
    total_users: int
    total_brands: int
    total_orders: int
    total_revenue: float
    active_ml_jobs: int


class MLJobStats(BaseModel):
    queued: int
    processing: int
    completed: int
    failed: int


class SalesDataPoint(BaseModel):
    date: str
    revenue: float


class BrandInfo(BaseModel):
    brand_id: str
    user_id: str
    company_name: str
    logo_url: Optional[str] = None
    status: str
    rejection_reason: Optional[str] = None
    product_count: int


@router.get("/analytics/overview", response_model=AnalyticsOverview)
async def get_analytics_overview(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsOverview:
    """Get overview analytics for the admin dashboard."""
    # Count total users
    user_stmt = select(func.count(User.user_id))
    user_result = await db.execute(user_stmt)
    total_users = user_result.scalar() or 0

    # Count total brands
    brand_stmt = select(func.count(Brand.brand_id))
    brand_result = await db.execute(brand_stmt)
    total_brands = brand_result.scalar() or 0

    # Count total orders
    order_stmt = select(func.count(Order.order_id))
    order_result = await db.execute(order_stmt)
    total_orders = order_result.scalar() or 0

    # Sum total revenue (from confirmed orders)
    revenue_stmt = select(func.sum(Order.total_amount)).where(
        Order.status == OrderStatus.CONFIRMED
    )
    revenue_result = await db.execute(revenue_stmt)
    total_revenue = revenue_result.scalar() or 0.0

    # Count active ML jobs (queued + processing)
    ml_stmt = select(func.count(MLJob.job_id)).where(
        MLJob.status.in_([MLJobStatus.QUEUED, MLJobStatus.PROCESSING])
    )
    ml_result = await db.execute(ml_stmt)
    active_ml_jobs = ml_result.scalar() or 0

    return AnalyticsOverview(
        total_users=total_users,
        total_brands=total_brands,
        total_orders=total_orders,
        total_revenue=float(total_revenue),
        active_ml_jobs=active_ml_jobs,
    )


@router.get("/analytics/ml-jobs", response_model=MLJobStats)
async def get_ml_job_stats(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> MLJobStats:
    """Get ML job queue statistics."""
    stats = {}
    for status in [MLJobStatus.QUEUED, MLJobStatus.PROCESSING, MLJobStatus.COMPLETED, MLJobStatus.FAILED]:
        stmt = select(func.count(MLJob.job_id)).where(MLJob.status == status)
        result = await db.execute(stmt)
        count = result.scalar() or 0
        stats[status.value] = count

    return MLJobStats(
        queued=stats.get("queued", 0),
        processing=stats.get("processing", 0),
        completed=stats.get("completed", 0),
        failed=stats.get("failed", 0),
    )


@router.get("/analytics/sales-over-time", response_model=List[SalesDataPoint])
async def get_sales_over_time(
    days: int = 30,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> List[SalesDataPoint]:
    """Get daily sales revenue for the last N days."""
    # Get confirmed orders from the last N days
    start_date = datetime.utcnow() - timedelta(days=days)

    stmt = select(
        func.date(Order.created_at).label("date"),
        func.sum(Order.total_amount).label("revenue")
    ).where(
        Order.status == OrderStatus.CONFIRMED,
        Order.created_at >= start_date
    ).group_by(
        func.date(Order.created_at)
    ).order_by(
        func.date(Order.created_at)
    )

    result = await db.execute(stmt)
    rows = result.all()

    return [
        SalesDataPoint(
            date=str(row[0]),
            revenue=float(row[1]) if row[1] else 0.0
        )
        for row in rows
    ]


class AdminUserInfo(BaseModel):
    user_id: str
    name: str
    email: str
    role: str
    created_at: str
    is_blocked: bool
    blocked_until: Optional[str] = None
    block_reason: Optional[str] = None


@router.get("/users", response_model=List[AdminUserInfo])
async def list_users(
    page: int = 1,
    page_size: int = 20,
    role: str = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> List[AdminUserInfo]:
    """Get paginated list of all users (with moderation status)."""
    stmt = select(User)

    if role:
        stmt = stmt.where(User.role == role)

    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    result = await db.execute(stmt)
    users = result.scalars().all()

    return [
        AdminUserInfo(
            user_id=str(u.user_id),
            name=u.name,
            email=u.email,
            role=u.role.value,
            created_at=u.created_at.isoformat(),
            is_blocked=u.is_blocked,
            blocked_until=(
                "indefinite" if u.block_is_indefinite
                else (u.blocked_until.isoformat() if u.blocked_until else None)
            ),
            block_reason=u.block_reason,
        )
        for u in users
    ]


@router.patch("/users/{user_id}")
async def update_user_role(
    user_id: str,
    new_role: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Update a user's role (Admin only)."""
    from uuid import UUID

    # Validate new role
    try:
        role_enum = UserRole[new_role.upper()]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join([r.value for r in UserRole])}"
        )

    # Get user
    stmt = select(User).where(User.user_id == UUID(user_id))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update role
    user.role = role_enum
    await db.commit()
    await db.refresh(user)

    return UserResponse(
        user_id=user.user_id,
        name=user.name,
        email=user.email,
        role=user.role,
        created_at=user.created_at.isoformat(),
    )


@router.get("/brands", response_model=List[BrandInfo])
async def list_brands(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> List[BrandInfo]:
    """Get paginated list of all brands with product counts."""
    # Get brands with product counts
    stmt = select(Brand)

    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    result = await db.execute(stmt)
    brands = result.scalars().all()

    brand_infos = []
    for brand in brands:
        # Count products for this brand
        product_stmt = select(func.count(Product.product_id)).where(
            Product.brand_id == brand.brand_id
        )
        product_result = await db.execute(product_stmt)
        product_count = product_result.scalar() or 0

        brand_infos.append(
            BrandInfo(
                brand_id=str(brand.brand_id),
                user_id=str(brand.user_id),
                company_name=brand.company_name,
                logo_url=brand.logo_url,
                status=brand.status.value,
                rejection_reason=brand.rejection_reason,
                product_count=product_count,
            )
        )

    return brand_infos


class MLJobInfo(BaseModel):
    job_id: str
    user_id: str
    job_type: str
    status: str
    created_at: str
    input_image_url: Optional[str] = None
    result_url: Optional[str] = None
    error_message: Optional[str] = None


@router.get("/ml-jobs", response_model=List[MLJobInfo])
async def list_ml_jobs(
    page: int = 1,
    page_size: int = 20,
    status: str = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> List[MLJobInfo]:
    stmt = select(MLJob)
    if status:
        try:
            status_enum = MLJobStatus(status.lower())
            stmt = stmt.where(MLJob.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")

    stmt = stmt.order_by(MLJob.created_at.desc())
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)
    result = await db.execute(stmt)
    jobs = result.scalars().all()

    return [
        MLJobInfo(
            job_id=str(j.job_id),
            user_id=str(j.user_id),
            job_type=j.job_type,
            status=j.status.value,
            created_at=j.created_at.isoformat(),
            input_image_url=j.input_image_url,
            result_url=j.result_url,
            error_message=j.error_message,
        )
        for j in jobs
    ]


# ============================================================================
# Brand approval
# ============================================================================
async def _get_brand(db: AsyncSession, brand_id: str) -> Brand:
    from uuid import UUID
    brand = await db.get(Brand, UUID(brand_id))
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand


@router.post("/brands/{brand_id}/approve")
async def approve_brand(
    brand_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    brand = await _get_brand(db, brand_id)
    brand.status = BrandStatus.APPROVED
    brand.rejection_reason = None
    await db.commit()
    return {"brand_id": brand_id, "status": brand.status.value}


class RejectRequest(BaseModel):
    reason: Optional[str] = None


@router.post("/brands/{brand_id}/reject")
async def reject_brand(
    brand_id: str,
    payload: RejectRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    brand = await _get_brand(db, brand_id)
    brand.status = BrandStatus.REJECTED
    brand.rejection_reason = payload.reason
    await db.commit()
    return {"brand_id": brand_id, "status": brand.status.value}


# ============================================================================
# Moderation: block / unblock / delete users & brands
# ============================================================================
async def _get_user(db: AsyncSession, user_id: str) -> User:
    from uuid import UUID
    user = await db.get(User, UUID(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


class BlockRequest(BaseModel):
    # Duration in days; 0 or negative => indefinite (until manually unblocked).
    duration_days: int = 0
    reason: Optional[str] = None


@router.post("/users/{user_id}/block")
async def block_user(
    user_id: str,
    payload: BlockRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    user = await _get_user(db, user_id)
    if user.role == UserRole.ADMIN:
        raise HTTPException(status_code=400, detail="Cannot block an admin account")
    if payload.duration_days and payload.duration_days > 0:
        user.blocked_until = datetime.utcnow() + timedelta(days=payload.duration_days)
    else:
        user.blocked_until = INDEFINITE_BLOCK
    user.block_reason = payload.reason
    await db.commit()
    return {
        "user_id": user_id,
        "blocked_until": "indefinite" if user.block_is_indefinite else user.blocked_until.isoformat(),
    }


@router.post("/users/{user_id}/unblock")
async def unblock_user(
    user_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    user = await _get_user(db, user_id)
    user.blocked_until = None
    user.block_reason = None
    await db.commit()
    return {"user_id": user_id, "is_blocked": False}


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_user(
    user_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a user (and, via cascade, their brand/profile/orders)."""
    user = await _get_user(db, user_id)
    if user.user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account here")
    await db.delete(user)
    await db.commit()


# ============================================================================
# Issue reports
# ============================================================================
@router.get("/reports", response_model=List[ReportResponse])
async def list_reports(
    status_filter: Optional[str] = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> List[ReportResponse]:
    stmt = select(IssueReport, User).join(User, User.user_id == IssueReport.reporter_id)
    if status_filter:
        try:
            stmt = stmt.where(IssueReport.status == ReportStatus(status_filter.lower()))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")
    stmt = stmt.order_by(IssueReport.created_at.desc())
    rows = (await db.execute(stmt)).all()
    return [
        ReportResponse(
            report_id=r.report_id,
            reporter_id=r.reporter_id,
            reporter_role=r.reporter_role,
            reporter_name=u.name,
            reporter_email=u.email,
            target_type=r.target_type,
            target_id=r.target_id,
            subject=r.subject,
            message=r.message,
            status=r.status,
            admin_note=r.admin_note,
            created_at=r.created_at.isoformat(),
        )
        for r, u in rows
    ]


@router.patch("/reports/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: str,
    payload: ReportUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    from uuid import UUID
    report = await db.get(IssueReport, UUID(report_id))
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report.status = payload.status
    if payload.admin_note is not None:
        report.admin_note = payload.admin_note
    await db.commit()
    await db.refresh(report)
    reporter = await db.get(User, report.reporter_id)
    return ReportResponse(
        report_id=report.report_id,
        reporter_id=report.reporter_id,
        reporter_role=report.reporter_role,
        reporter_name=reporter.name if reporter else None,
        reporter_email=reporter.email if reporter else None,
        target_type=report.target_type,
        target_id=report.target_id,
        subject=report.subject,
        message=report.message,
        status=report.status,
        admin_note=report.admin_note,
        created_at=report.created_at.isoformat(),
    )


# ============================================================================
# Commission settings
# ============================================================================
@router.get("/settings", response_model=PlatformSettingsResponse)
async def get_platform_settings(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> PlatformSettingsResponse:
    settings = await get_settings(db)
    await db.commit()
    return PlatformSettingsResponse(commission_percent=settings.commission_percent)


@router.patch("/settings", response_model=PlatformSettingsResponse)
async def update_platform_settings(
    payload: PlatformSettingsUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> PlatformSettingsResponse:
    settings = await get_settings(db)
    settings.commission_percent = payload.commission_percent
    await db.commit()
    return PlatformSettingsResponse(commission_percent=settings.commission_percent)


# ============================================================================
# Earnings, payouts & finance
# ============================================================================
@router.get("/earnings", response_model=List[BrandEarnings])
async def list_brand_earnings(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> List[BrandEarnings]:
    settings = await get_settings(db)
    brands = (await db.execute(select(Brand))).scalars().all()
    out = []
    for brand in brands:
        data = await compute_brand_earnings(db, brand, settings.commission_percent)
        out.append(BrandEarnings(**data))
    await db.commit()
    out.sort(key=lambda e: e.gross_sales, reverse=True)
    return out


@router.post("/brands/{brand_id}/payouts", response_model=PayoutResponse, status_code=status.HTTP_201_CREATED)
async def record_payout(
    brand_id: str,
    payload: PayoutCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> PayoutResponse:
    brand = await _get_brand(db, brand_id)
    payout = Payout(brand_id=brand.brand_id, amount=payload.amount, note=payload.note)
    db.add(payout)
    await db.commit()
    await db.refresh(payout)
    return PayoutResponse(
        payout_id=payout.payout_id,
        brand_id=payout.brand_id,
        amount=payout.amount,
        note=payout.note,
        created_at=payout.created_at.isoformat(),
    )


@router.get("/finance", response_model=FinanceOverview)
async def finance_overview(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> FinanceOverview:
    settings = await get_settings(db)
    brands = (await db.execute(select(Brand))).scalars().all()
    total_gross = total_commission = total_net = total_paid = 0.0
    for brand in brands:
        gross = await brand_gross_sales(db, brand.brand_id)
        paid = await brand_paid_out(db, brand.brand_id)
        commission = gross * settings.commission_percent / 100.0
        total_gross += gross
        total_commission += commission
        total_net += (gross - commission)
        total_paid += paid
    sub_count, sub_revenue = await subscription_totals(db)
    await db.commit()
    return FinanceOverview(
        commission_percent=settings.commission_percent,
        total_gross_sales=round(total_gross, 2),
        total_commission=round(total_commission, 2),
        total_brand_net=round(total_net, 2),
        total_paid_out=round(total_paid, 2),
        total_owed_to_brands=round(total_net - total_paid, 2),
        subscription_active_count=sub_count,
        subscription_revenue=sub_revenue,
        total_platform_revenue=round(total_commission + sub_revenue, 2),
    )


# ============================================================================
# Subscription plans (admin CRUD)
# ============================================================================
def _plan_out(p: SubscriptionPlan) -> SubscriptionPlanResponse:
    return SubscriptionPlanResponse(
        plan_id=p.plan_id, name=p.name, price=p.price, interval=p.interval,
        features=p.features, is_active=p.is_active, created_at=p.created_at.isoformat(),
    )


@router.get("/subscription-plans", response_model=List[SubscriptionPlanResponse])
async def admin_list_plans(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> List[SubscriptionPlanResponse]:
    plans = (await db.execute(select(SubscriptionPlan).order_by(SubscriptionPlan.price))).scalars().all()
    return [_plan_out(p) for p in plans]


@router.post("/subscription-plans", response_model=SubscriptionPlanResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_plan(
    payload: SubscriptionPlanCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionPlanResponse:
    plan = SubscriptionPlan(
        name=payload.name, price=payload.price, interval=payload.interval,
        features=payload.features, is_active=payload.is_active,
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return _plan_out(plan)


@router.patch("/subscription-plans/{plan_id}", response_model=SubscriptionPlanResponse)
async def admin_update_plan(
    plan_id: str,
    payload: SubscriptionPlanUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionPlanResponse:
    from uuid import UUID
    plan = await db.get(SubscriptionPlan, UUID(plan_id))
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    for field in ("name", "price", "interval", "features", "is_active"):
        val = getattr(payload, field)
        if val is not None:
            setattr(plan, field, val)
    await db.commit()
    await db.refresh(plan)
    return _plan_out(plan)


@router.delete("/subscription-plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_plan(
    plan_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Deactivate a plan (soft delete so existing subscriptions keep their FK)."""
    from uuid import UUID
    plan = await db.get(SubscriptionPlan, UUID(plan_id))
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    plan.is_active = False
    await db.commit()
