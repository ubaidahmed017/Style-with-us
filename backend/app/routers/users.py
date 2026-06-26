"""
User authentication and profile management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import verify_firebase_token, DecodedToken, get_current_user
from app.core.database import get_db
from app.models import User, UserProfile, UserRole
from app.schemas import (
    UserResponse,
    UserProfileCreate,
    UserProfileResponse,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user: DecodedToken = Depends(verify_firebase_token),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Register a new user after Firebase auth creation.

    This endpoint is called after the user has already created a Firebase account.
    It creates a User record in PostgreSQL.
    """
    # Check if user already exists
    stmt = select(User).where(User.firebase_uid == user.uid)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        return UserResponse(
            user_id=existing_user.user_id,
            name=existing_user.name,
            email=existing_user.email,
            role=existing_user.role,
            created_at=existing_user.created_at.isoformat(),
        )

    # Create new user
    new_user = User(
        firebase_uid=user.uid,
        name=user.email or "User",  # Default name
        email=user.email or "",
        role=UserRole.SHOPPER,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return UserResponse(
        user_id=new_user.user_id,
        name=new_user.name,
        email=new_user.email,
        role=new_user.role,
        created_at=new_user.created_at.isoformat(),
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
