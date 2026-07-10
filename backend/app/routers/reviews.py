"""Product reviews: shoppers create them; anyone can read; brands see theirs."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, require_role
from app.core.database import get_db
from app.models import User, Product, Brand, Review, UserRole
from app.schemas import ReviewCreate, ReviewResponse, RatingSummary

router = APIRouter(prefix="/reviews", tags=["reviews"])


def _to_response(review: Review, user_name: str | None) -> ReviewResponse:
    return ReviewResponse(
        review_id=review.review_id,
        user_id=review.user_id,
        user_name=user_name,
        product_id=review.product_id,
        rating=review.rating,
        comment=review.comment,
        created_at=review.created_at.isoformat(),
    )


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    payload: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReviewResponse:
    """Create or update the caller's review for a product (one per product)."""
    product = await db.get(Product, payload.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    stmt = select(Review).where(
        Review.user_id == current_user.user_id,
        Review.product_id == payload.product_id,
    )
    review = (await db.execute(stmt)).scalar_one_or_none()
    if review:
        review.rating = payload.rating
        review.comment = payload.comment
    else:
        review = Review(
            user_id=current_user.user_id,
            product_id=payload.product_id,
            brand_id=product.brand_id,
            rating=payload.rating,
            comment=payload.comment,
        )
        db.add(review)
    await db.commit()
    await db.refresh(review)
    return _to_response(review, current_user.name)


@router.get("/product/{product_id}", response_model=List[ReviewResponse])
async def list_product_reviews(
    product_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ReviewResponse]:
    stmt = (
        select(Review, User.name)
        .join(User, User.user_id == Review.user_id)
        .where(Review.product_id == product_id)
        .order_by(Review.created_at.desc())
    )
    rows = (await db.execute(stmt)).all()
    return [_to_response(r, name) for r, name in rows]


@router.get("/product/{product_id}/summary", response_model=RatingSummary)
async def product_rating_summary(
    product_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RatingSummary:
    stmt = select(func.avg(Review.rating), func.count(Review.review_id)).where(
        Review.product_id == product_id
    )
    avg, count = (await db.execute(stmt)).one()
    return RatingSummary(average=round(float(avg), 2) if avg else 0.0, count=int(count or 0))


@router.get("/brand/mine", response_model=List[ReviewResponse])
async def brand_reviews(
    current_user: User = Depends(require_role(UserRole.BRAND)),
    db: AsyncSession = Depends(get_db),
) -> List[ReviewResponse]:
    """Reviews left on the calling brand's products."""
    brand = (await db.execute(
        select(Brand).where(Brand.user_id == current_user.user_id)
    )).scalar_one_or_none()
    if not brand:
        return []
    stmt = (
        select(Review, User.name)
        .join(User, User.user_id == Review.user_id)
        .where(Review.brand_id == brand.brand_id)
        .order_by(Review.created_at.desc())
    )
    rows = (await db.execute(stmt)).all()
    return [_to_response(r, name) for r, name in rows]
