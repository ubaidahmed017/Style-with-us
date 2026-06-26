"""
Pydantic schemas for ML job endpoints.
"""

from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, HttpUrl, field_validator
from app.models.enums import MLJobStatus


class MLJobRequest(BaseModel):
    """Base schema for ML job requests."""
    image_url: HttpUrl

    @field_validator("image_url", mode="before")
    @classmethod
    def validate_https_url(cls, v: str) -> str:
        """Ensure image URL is HTTPS and supported format."""
        if not v.startswith("https://"):
            raise ValueError("image_url must use HTTPS")
        if not any(v.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]):
            raise ValueError("image_url must be a supported format (jpg, png, webp)")
        return v


class StyleAnalysisRequest(MLJobRequest):
    """Request for style analysis job."""
    pass


class VirtualTryOnRequest(MLJobRequest):
    """Request for virtual try-on job."""
    product_id: UUID


class MLJobResponse(BaseModel):
    """Response when submitting an ML job."""
    job_id: UUID
    status: MLJobStatus
    created_at: str


class MLJobStatus(BaseModel):
    """Status of an ML job."""
    job_id: UUID
    status: MLJobStatus
    result_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class AIAnalysisResult(BaseModel):
    """Result of on-device AI analysis."""
    body_shape: str
    skin_tone_hex: str
    confidence_score: float
    recommended_style_ids: List[UUID] = []

    @field_validator("confidence_score")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Ensure confidence is in [0.0, 1.0]."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence_score must be between 0.0 and 1.0")
        return v
