"""Schemas for product reviews."""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, field_validator


class ReviewCreate(BaseModel):
    product_id: UUID
    rating: int
    comment: Optional[str] = None

    @field_validator("rating")
    @classmethod
    def rating_range(cls, v: int) -> int:
        if v < 1 or v > 5:
            raise ValueError("rating must be between 1 and 5")
        return v


class ReviewResponse(BaseModel):
    review_id: UUID
    user_id: UUID
    user_name: Optional[str] = None
    product_id: UUID
    rating: int
    comment: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class RatingSummary(BaseModel):
    average: float
    count: int
