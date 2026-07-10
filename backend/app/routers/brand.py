"""Brand-facing endpoints (earnings, account status)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_role, get_current_user
from app.core.database import get_db
from app.models import User, Brand, UserRole
from app.schemas import BrandEarnings
from app.services.earnings import get_settings, compute_brand_earnings

router = APIRouter(prefix="/brand", tags=["brand"])


@router.get("/earnings", response_model=BrandEarnings)
async def my_earnings(
    current_user: User = Depends(require_role(UserRole.BRAND)),
    db: AsyncSession = Depends(get_db),
) -> BrandEarnings:
    """The calling brand's own earnings, commission, paid and remaining balance."""
    brand = (await db.execute(
        select(Brand).where(Brand.user_id == current_user.user_id)
    )).scalar_one_or_none()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    settings = await get_settings(db)
    data = await compute_brand_earnings(db, brand, settings.commission_percent)
    await db.commit()  # persist settings row if it was just created
    return BrandEarnings(**data)


@router.get("/status")
async def my_brand_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Approval status of the caller's brand (used to show a pending banner)."""
    brand = (await db.execute(
        select(Brand).where(Brand.user_id == current_user.user_id)
    )).scalar_one_or_none()
    if not brand:
        return {"has_brand": False}
    return {
        "has_brand": True,
        "company_name": brand.company_name,
        "status": brand.status.value,
        "rejection_reason": brand.rejection_reason,
    }
