"""
Admin dashboard and analytics endpoints (Admin only).
"""

from typing import List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.auth import get_current_user, require_role
from app.core.database import get_db
from app.models import User, UserRole, Order, Brand, Product, MLJob
from app.models.enums import OrderStatus, MLJobStatus
from app.schemas import UserResponse

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
    company_name: str
    logo_url: str = None
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


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    page: int = 1,
    page_size: int = 20,
    role: str = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> List[UserResponse]:
    """Get paginated list of all users."""
    stmt = select(User)

    if role:
        stmt = stmt.where(User.role == role)

    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    result = await db.execute(stmt)
    users = result.scalars().all()

    return [
        UserResponse(
            user_id=u.user_id,
            name=u.name,
            email=u.email,
            role=u.role,
            created_at=u.created_at.isoformat(),
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
                company_name=brand.company_name,
                logo_url=brand.logo_url,
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
    input_image_url: str = None
    result_url: str = None
    error_message: str = None


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
