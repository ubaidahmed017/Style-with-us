"""
User authentication and profile management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import verify_firebase_token, DecodedToken, get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models import User, UserProfile, UserRole, Brand
from app.models.enums import SkinTonePalette
from app.schemas import (
    UserRegisterRequest,
    UserResponse,
    UserProfileCreate,
    UserProfileResponse,
    BrandCreate,
    BrandResponse,
)
from app.services.color import palette_from_hex

router = APIRouter(prefix="/users", tags=["users"])


def _authoritative_palette(profile_data: UserProfileCreate) -> SkinTonePalette | None:
    """Server-side palette: recomputed from the measured hex when present.

    The hex is the ground truth; the palette is derived. Recomputing here keeps
    one classifier (services/color.py) authoritative even if an older client
    sends a stale or differently-computed palette.
    """
    if profile_data.skin_tone_hex:
        computed = palette_from_hex(profile_data.skin_tone_hex)
        if computed:
            return SkinTonePalette(computed)
    return profile_data.skin_tone_palette


def _is_admin_email(email: str | None) -> bool:
    """True if this email is in the configured admin allowlist."""
    if not email:
        return False
    allow = {e.strip().lower() for e in settings.admin_emails.split(",") if e.strip()}
    return email.strip().lower() in allow


async def _ensure_brand(db: AsyncSession, user: User, company_name: str | None) -> Brand:
    """Create the caller's Brand record if it doesn't exist yet (idempotent)."""
    stmt = select(Brand).where(Brand.user_id == user.user_id)
    result = await db.execute(stmt)
    brand = result.scalar_one_or_none()
    if brand is None:
        brand = Brand(
            user_id=user.user_id,
            company_name=company_name or user.name or "My Brand",
        )
        db.add(brand)
        await db.flush()
    elif company_name:
        brand.company_name = company_name
    return brand


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: UserRegisterRequest | None = None,
    user: DecodedToken = Depends(verify_firebase_token),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Register (or reconcile) a user after Firebase account creation.

    Accepts an optional body ``{role, name, company_name}``. The requested role
    may be ``shopper`` or ``brand``; ``admin`` is granted only via the server
    allowlist (``ADMIN_EMAILS``) and can never be self-assigned. For a brand
    sign-up, the linked ``Brand`` record is created so product uploads work.
    """
    payload = payload or UserRegisterRequest()

    # A caller may only request shopper or brand; admin comes from the allowlist.
    requested_role = payload.role if payload.role in (UserRole.SHOPPER, UserRole.BRAND) else None

    # Check if user already exists
    stmt = select(User).where(User.firebase_uid == user.uid)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    # Fall back to matching a pre-seeded account by email (e.g. an admin seeded
    # before its first login) and bind it to this Firebase identity.
    if existing_user is None and user.email:
        stmt = select(User).where(User.email == user.email)
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()
        if existing_user is not None and existing_user.firebase_uid != user.uid:
            existing_user.firebase_uid = user.uid

    force_admin = _is_admin_email(user.email)

    if existing_user:
        # Guarantee configured admin emails always hold the admin role.
        if force_admin and existing_user.role != UserRole.ADMIN:
            existing_user.role = UserRole.ADMIN
        # Allow a one-way shopper -> brand upgrade when a brand sign-up is
        # explicitly requested (never downgrade, never touch admins here).
        elif requested_role == UserRole.BRAND and existing_user.role == UserRole.SHOPPER:
            existing_user.role = UserRole.BRAND
        if existing_user.role == UserRole.BRAND:
            await _ensure_brand(db, existing_user, payload.company_name)
        await db.commit()
        await db.refresh(existing_user)
        return UserResponse(
            user_id=existing_user.user_id,
            name=existing_user.name,
            email=existing_user.email,
            role=existing_user.role,
            created_at=existing_user.created_at.isoformat(),
        )

    # Create new user. Admin wins (allowlist); otherwise honor the requested
    # role, defaulting to shopper.
    if force_admin:
        role = UserRole.ADMIN
    else:
        role = requested_role or UserRole.SHOPPER

    new_user = User(
        firebase_uid=user.uid,
        name=payload.name or user.email or "User",
        email=user.email or "",
        role=role,
    )
    db.add(new_user)
    await db.flush()

    # For brand sign-ups, create the linked Brand so /inventory/products works.
    if role == UserRole.BRAND:
        await _ensure_brand(db, new_user, payload.company_name)

    await db.commit()
    await db.refresh(new_user)

    return UserResponse(
        user_id=new_user.user_id,
        name=new_user.name,
        email=new_user.email,
        role=new_user.role,
        created_at=new_user.created_at.isoformat(),
    )


@router.post("/brand", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_brand(
    brand_data: BrandCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BrandResponse:
    """
    Create or update the calling user's Brand record (idempotent).

    Requires the user to hold the brand (or admin) role. Brands created here let
    the user upload products via /inventory/products.
    """
    if current_user.role not in (UserRole.BRAND, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only brand accounts can create a brand profile",
        )

    brand = await _ensure_brand(db, current_user, brand_data.company_name)
    if brand_data.logo_url is not None:
        brand.logo_url = str(brand_data.logo_url)
    await db.commit()
    await db.refresh(brand)

    return BrandResponse(
        brand_id=brand.brand_id,
        user_id=brand.user_id,
        company_name=brand.company_name,
        logo_url=brand.logo_url,
        products=[],
        created_at=brand.created_at.isoformat(),
        updated_at=brand.updated_at.isoformat(),
    )


@router.post("/profile", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_profile(
    profile_data: UserProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    """
    Create or update user profile with measurements.

    Gender is mandatory on first creation.
    """
    # Check if profile exists
    stmt = select(UserProfile).where(UserProfile.user_id == current_user.user_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if profile:
        # Update existing profile
        profile.gender = profile_data.gender
        profile.height_cm = profile_data.height_cm
        profile.weight_kg = profile_data.weight_kg
        profile.age = profile_data.age
        profile.chest_cm = profile_data.chest_cm
        profile.waist_cm = profile_data.waist_cm
        profile.hips_cm = profile_data.hips_cm
        profile.inseam_cm = profile_data.inseam_cm
        profile.shoulder_width_cm = profile_data.shoulder_width_cm
        if profile_data.body_shape is not None:
            profile.body_shape = profile_data.body_shape
        if profile_data.skin_tone_hex is not None:
            profile.skin_tone_hex = profile_data.skin_tone_hex
        authoritative = _authoritative_palette(profile_data)
        if authoritative is not None:
            profile.skin_tone_palette = authoritative
        profile.unit_preference = profile_data.unit_preference
    else:
        # Create new profile
        profile = UserProfile(
            user_id=current_user.user_id,
            gender=profile_data.gender,
            height_cm=profile_data.height_cm,
            weight_kg=profile_data.weight_kg,
            age=profile_data.age,
            chest_cm=profile_data.chest_cm,
            waist_cm=profile_data.waist_cm,
            hips_cm=profile_data.hips_cm,
            inseam_cm=profile_data.inseam_cm,
            shoulder_width_cm=profile_data.shoulder_width_cm,
            body_shape=profile_data.body_shape,
            skin_tone_hex=profile_data.skin_tone_hex,
            skin_tone_palette=_authoritative_palette(profile_data),
            unit_preference=profile_data.unit_preference,
        )
        db.add(profile)

    await db.commit()
    await db.refresh(profile)

    return UserProfileResponse(
        profile_id=profile.profile_id,
        user_id=profile.user_id,
        gender=profile.gender,
        height_cm=profile.height_cm,
        weight_kg=profile.weight_kg,
        age=profile.age,
        chest_cm=profile.chest_cm,
        waist_cm=profile.waist_cm,
        hips_cm=profile.hips_cm,
        inseam_cm=profile.inseam_cm,
        shoulder_width_cm=profile.shoulder_width_cm,
        body_shape=profile.body_shape,
        skin_tone_hex=profile.skin_tone_hex,
        skin_tone_palette=profile.skin_tone_palette,
        unit_preference=profile.unit_preference,
        created_at=profile.created_at.isoformat(),
        updated_at=profile.updated_at.isoformat(),
    )


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    """Get the current user's profile."""
    stmt = select(UserProfile).where(UserProfile.user_id == current_user.user_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found. Please complete profile setup.",
        )

    return UserProfileResponse(
        profile_id=profile.profile_id,
        user_id=profile.user_id,
        gender=profile.gender,
        height_cm=profile.height_cm,
        weight_kg=profile.weight_kg,
        age=profile.age,
        chest_cm=profile.chest_cm,
        waist_cm=profile.waist_cm,
        hips_cm=profile.hips_cm,
        inseam_cm=profile.inseam_cm,
        shoulder_width_cm=profile.shoulder_width_cm,
        body_shape=profile.body_shape,
        skin_tone_hex=profile.skin_tone_hex,
        skin_tone_palette=profile.skin_tone_palette,
        unit_preference=profile.unit_preference,
        created_at=profile.created_at.isoformat(),
        updated_at=profile.updated_at.isoformat(),
    )


@router.patch("/profile", response_model=UserProfileResponse)
async def patch_profile(
    profile_data: UserProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    """Partially update user profile."""
    stmt = select(UserProfile).where(UserProfile.user_id == current_user.user_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found",
        )

    # Update only provided fields
    if profile_data.gender is not None:
        profile.gender = profile_data.gender
    if profile_data.height_cm is not None:
        profile.height_cm = profile_data.height_cm
    if profile_data.weight_kg is not None:
        profile.weight_kg = profile_data.weight_kg
    if profile_data.age is not None:
        profile.age = profile_data.age
    if profile_data.chest_cm is not None:
        profile.chest_cm = profile_data.chest_cm
    if profile_data.waist_cm is not None:
        profile.waist_cm = profile_data.waist_cm
    if profile_data.hips_cm is not None:
        profile.hips_cm = profile_data.hips_cm
    if profile_data.inseam_cm is not None:
        profile.inseam_cm = profile_data.inseam_cm
    if profile_data.shoulder_width_cm is not None:
        profile.shoulder_width_cm = profile_data.shoulder_width_cm
    if profile_data.body_shape is not None:
        profile.body_shape = profile_data.body_shape
    if profile_data.skin_tone_hex is not None:
        profile.skin_tone_hex = profile_data.skin_tone_hex
    authoritative = _authoritative_palette(profile_data)
    if authoritative is not None:
        profile.skin_tone_palette = authoritative
    if profile_data.unit_preference is not None:
        profile.unit_preference = profile_data.unit_preference

    await db.commit()
    await db.refresh(profile)

    return UserProfileResponse(
        profile_id=profile.profile_id,
        user_id=profile.user_id,
        gender=profile.gender,
        height_cm=profile.height_cm,
        weight_kg=profile.weight_kg,
        age=profile.age,
        chest_cm=profile.chest_cm,
        waist_cm=profile.waist_cm,
        hips_cm=profile.hips_cm,
        inseam_cm=profile.inseam_cm,
        shoulder_width_cm=profile.shoulder_width_cm,
        body_shape=profile.body_shape,
        skin_tone_hex=profile.skin_tone_hex,
        skin_tone_palette=profile.skin_tone_palette,
        unit_preference=profile.unit_preference,
        created_at=profile.created_at.isoformat(),
        updated_at=profile.updated_at.isoformat(),
    )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete the current user's account and all associated data."""
    # Delete the user (cascades delete profile, orders, ml_jobs)
    await db.delete(current_user)
    await db.commit()
