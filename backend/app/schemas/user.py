"""
Pydantic schemas for user-related endpoints.
"""

import re
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, field_validator
from app.models.enums import UserRole, Gender, BodyShape, SkinTonePalette, UnitPreference

_HEX_RE = re.compile(r"^#?[0-9a-fA-F]{6}$")


def normalize_hex_color(v: Optional[str]) -> Optional[str]:
    """Validate and normalize a colour to '#RRGGBB' (uppercase)."""
    if v is None:
        return None
    if not _HEX_RE.match(v.strip()):
        raise ValueError("must be a hex colour like #C68642")
    return f"#{v.strip().lstrip('#').upper()}"


class UserBase(BaseModel):
    """Base user schema."""
    name: str
    email: EmailStr


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str
    role: UserRole = UserRole.SHOPPER


class UserRegisterRequest(BaseModel):
    """Optional body for POST /users/register.

    All fields are optional so existing callers that POST an empty body keep
    working. When provided, `role` selects shopper vs brand (admin is granted
    only via the server-side allowlist, never self-assigned), `name` sets the
    display name, and `company_name` seeds the Brand record for brand sign-ups.
    """
    role: Optional[UserRole] = None
    name: Optional[str] = None
    company_name: Optional[str] = None


class UserResponse(UserBase):
    """Schema for user response."""
    user_id: UUID
    role: UserRole
    created_at: str

    class Config:
        from_attributes = True


class UserProfileCreate(BaseModel):
    """Schema for creating/updating user profile."""
    gender: Gender  # Mandatory
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    age: Optional[int] = None
    chest_cm: Optional[float] = None
    waist_cm: Optional[float] = None
    hips_cm: Optional[float] = None
    inseam_cm: Optional[float] = None
    shoulder_width_cm: Optional[float] = None
    # On-device body-analysis results (optional). Sent by the Flutter client
    # after the user confirms the analysis; drive skin-tone/body-shape ranking.
    body_shape: Optional[BodyShape] = None
    skin_tone_hex: Optional[str] = None
    skin_tone_palette: Optional[SkinTonePalette] = None
    unit_preference: UnitPreference = UnitPreference.METRIC

    @field_validator("skin_tone_hex")
    @classmethod
    def valid_skin_hex(cls, v: Optional[str]) -> Optional[str]:
        """Reject garbage colours; normalize to '#RRGGBB' so downstream colour
        science (palette + suitability) always gets a parseable value."""
        return normalize_hex_color(v)

    @field_validator("height_cm", "weight_kg", "chest_cm", "waist_cm", "hips_cm", "inseam_cm", "shoulder_width_cm", mode="before")
    @classmethod
    def positive_measurements(cls, v: Optional[float]) -> Optional[float]:
        """Ensure measurements are positive if provided."""
        if v is not None and v <= 0:
            raise ValueError("Measurements must be positive")
        return v

    @field_validator("age", mode="before")
    @classmethod
    def positive_age(cls, v: Optional[int]) -> Optional[int]:
        """Ensure age is positive if provided."""
        if v is not None and v <= 0:
            raise ValueError("Age must be positive")
        return v


class UserProfileResponse(BaseModel):
    """Schema for user profile response."""
    profile_id: UUID
    user_id: UUID
    gender: Gender
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    age: Optional[int] = None
    chest_cm: Optional[float] = None
    waist_cm: Optional[float] = None
    hips_cm: Optional[float] = None
    inseam_cm: Optional[float] = None
    shoulder_width_cm: Optional[float] = None
    body_shape: Optional[BodyShape] = None
    skin_tone_hex: Optional[str] = None
    skin_tone_palette: Optional[SkinTonePalette] = None
    unit_preference: UnitPreference
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class BodyAnalysisResult(BaseModel):
    """Result of on-device body analysis."""
    body_shape: BodyShape
    skin_tone_hex: str
    skin_tone_palette: SkinTonePalette
    confidence_score: float  # 0.0-1.0
    shoulder_width_cm: Optional[float] = None
    bust_cm: Optional[float] = None
    waist_cm: Optional[float] = None
    hips_cm: Optional[float] = None

    @field_validator("confidence_score")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Ensure confidence score is in [0.0, 1.0]."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence_score must be between 0.0 and 1.0")
        return v
