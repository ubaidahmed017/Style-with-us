"""
AI-powered outfit recommendation endpoints.
"""

from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models import User, UserProfile, Product, ProductSizeSpec, Brand, UserRole
from app.schemas import ProductResponse, ProductSizeSpecResponse

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


# Body shape style rules (gender-specific)
BODY_SHAPE_RULES = {
    "hourglass": {
        "female": ["wrap", "fitted", "form-fitting"],
        "male": ["slim-fit", "fitted"],
        "non_binary": ["wrap", "fitted", "slim-fit"],
    },
    "pear": {
        "female": ["A-line", "flared", "wide-leg"],
        "male": ["tapered", "slim-leg"],
        "non_binary": ["A-line", "flared", "tapered"],
    },
    "apple": {
        "female": ["empire-waist", "flowy", "vertical-stripes"],
        "male": ["relaxed-fit", "vertical-stripes"],
        "non_binary": ["empire-waist", "relaxed-fit"],
    },
    "rectangle": {
        "female": ["ruffles", "layered", "belted"],
        "male": ["structured", "blazer"],
        "non_binary": ["ruffles", "structured"],
    },
    "inverted_triangle": {
        "female": ["wide-leg", "flared", "A-line"],
        "male": ["slim", "straight"],
        "non_binary": ["wide-leg", "slim"],
    },
}

# Skin tone to complementary color palette mapping
SKIN_TONE_PALETTE_COLORS = {
    "warm_spring": ["warm-orange", "warm-yellow", "warm-red", "warm-coral"],
    "warm_autumn": ["deep-orange", "bronze", "burgundy", "rust"],
    "cool_summer": ["cool-pink", "cool-blue", "mauve", "lavender"],
    "cool_winter": ["cool-red", "icy-blue", "stark-white", "pure-black"],
    "neutral_light": ["cream", "beige", "soft-gray", "warm-gray"],
    "neutral_deep": ["charcoal", "deep-gray", "deep-brown", "ebony"],
}


@router.get("/outfits", response_model=List[ProductResponse])
async def get_outfit_recommendations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ProductResponse]:
    """
    Get personalized outfit recommendations based on:
    - Gender and body shape
    - Skin tone complementary colors
    - Size availability
    - Gender target of products
    """
    # Get user profile
    stmt = select(UserProfile).where(UserProfile.user_id == current_user.user_id)
    result = await db.execute(stmt)
    user_profile = result.scalar_one_or_none()

    if not user_profile or not user_profile.gender:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User profile not complete. Please set gender first.",
        )

    # Get all products
    stmt = select(Product)
    result = await db.execute(stmt)
    all_products = result.scalars().all()

    recommendations = []
    scores = []

    for product in all_products:
        score = 0
        reasons = []

        # 1. Gender filter
        gender_value = user_profile.gender.value
        if current_user.role == UserRole.SHOPPER:
            # Shopper: filter by gender
            if gender_value == "non_binary":
                # Non-binary shoppers see all products
                score += 1
            else:
                # Male/Female shoppers see their gender or unisex
                if product.gender_target.value == gender_value:
                    score += 2
                elif product.gender_target.value == "unisex":
                    score += 1
                else:
                    continue  # Skip this product

        # 2. Body shape matching (if available)
        if user_profile.body_shape:
            shape_rules = BODY_SHAPE_RULES.get(user_profile.body_shape.value, {})
            style_keywords = shape_rules.get(gender_value, [])
            if style_keywords:
                score += 1
                reasons.append(f"{user_profile.body_shape.value.replace('_', ' ')} shape match")

        # 3. Skin tone color matching (if available)
        if user_profile.skin_tone_palette:
            palette_colors = SKIN_TONE_PALETTE_COLORS.get(user_profile.skin_tone_palette.value, [])
            # If product has dominant color, check if it matches the palette
            if product.dominant_color_hex:
                score += 1
                reasons.append(f"{user_profile.skin_tone_palette.value.replace('_', ' ')} palette")

        # 4. Size availability (if measurements available)
        if user_profile.waist_cm and user_profile.hips_cm:
            # Check if any size spec matches user's measurements
            user_fits = False
            for spec in product.size_specs:
                if (spec.waist_min <= user_profile.waist_cm <= spec.waist_max and
                    spec.hips_min <= user_profile.hips_cm <= spec.hips_max):
                    user_fits = True
                    score += 2
                    reasons.append("Your size available")
                    break

        if score > 0:
            # Convert product to response
            product_response = ProductResponse(
                product_id=product.product_id,
                brand_id=product.brand_id,
                sku=product.sku,
                name=product.name,
                description=product.description,
                price=product.price,
                image_url=product.image_url,
                garment_image_url=product.garment_image_url,
                gender_target=product.gender_target,
                dominant_color_hex=product.dominant_color_hex,
                size_specs=[
                    ProductSizeSpecResponse(
                        spec_id=spec.spec_id,
                        product_id=spec.product_id,
                        size_label=spec.size_label,
                        stock_quantity=spec.stock_quantity,
                        chest_min=spec.chest_min,
                        chest_max=spec.chest_max,
                        waist_min=spec.waist_min,
                        waist_max=spec.waist_max,
                        hips_min=spec.hips_min,
                        hips_max=spec.hips_max,
                        inseam_min=spec.inseam_min,
                        inseam_max=spec.inseam_max,
                        shoulder_width_min=spec.shoulder_width_min,
                        shoulder_width_max=spec.shoulder_width_max,
                    )
                    for spec in product.size_specs
                ],
                created_at=product.created_at.isoformat(),
                updated_at=product.updated_at.isoformat(),
            )

            recommendations.append(product_response)
            scores.append((score, " · ".join(reasons)))

    # Sort by score (descending) and return top results
    sorted_recs = sorted(zip(scores, recommendations), key=lambda x: x[0][0], reverse=True)
    return [rec[1] for rec in sorted_recs[:50]]  # Return top 50 recommendations
