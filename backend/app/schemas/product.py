"""
Pydantic schemas for product and inventory endpoints.
"""

from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, HttpUrl, field_validator
from app.models.enums import GenderTarget


class ProductSizeSpecCreate(BaseModel):
    """Schema for creating a product size specification."""
    size_label: str
    stock_quantity: int = 0
    chest_min: float
    chest_max: float
    waist_min: float
    waist_max: float
    hips_min: float
    hips_max: float
    inseam_min: Optional[float] = None
    inseam_max: Optional[float] = None
    shoulder_width_min: Optional[float] = None
    shoulder_width_max: Optional[float] = None

    @field_validator("stock_quantity")
    @classmethod
    def non_negative_stock(cls, v: int) -> int:
        """Ensure stock quantity is non-negative."""
        if v < 0:
            raise ValueError("stock_quantity must be non-negative")
        return v

    @field_validator("chest_min", "waist_min", "hips_min", "inseam_min", "shoulder_width_min", mode="before")
    @classmethod
    def positive_minimums(cls, v: Optional[float]) -> Optional[float]:
        """Ensure minimum measurements are positive."""
        if v is not None and v <= 0:
            raise ValueError("Minimum measurements must be positive")
        return v

    @field_validator("chest_max", "waist_max", "hips_max", "inseam_max", "shoulder_width_max", mode="before")
    @classmethod
    def positive_maximums(cls, v: Optional[float]) -> Optional[float]:
        """Ensure maximum measurements are positive."""
        if v is not None and v <= 0:
            raise ValueError("Maximum measurements must be positive")
        return v

    def validate_ranges(self):
        """Validate that min <= max for all measurement pairs."""
        checks = [
            ("chest", self.chest_min, self.chest_max),
            ("waist", self.waist_min, self.waist_max),
            ("hips", self.hips_min, self.hips_max),
        ]
        if self.inseam_min is not None and self.inseam_max is not None:
            checks.append(("inseam", self.inseam_min, self.inseam_max))
        if self.shoulder_width_min is not None and self.shoulder_width_max is not None:
            checks.append(("shoulder_width", self.shoulder_width_min, self.shoulder_width_max))

        for name, min_val, max_val in checks:
            if min_val > max_val:
                raise ValueError(f"{name}_min must be <= {name}_max")


class ProductSizeSpecResponse(ProductSizeSpecCreate):
    """Schema for product size specification response."""
    spec_id: UUID
    product_id: UUID

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    """Schema for creating a product."""
    sku: str
    name: str
    description: Optional[str] = None
    price: float
    image_url: Optional[HttpUrl] = None
    garment_image_url: Optional[HttpUrl] = None
    gender_target: GenderTarget
    dominant_color_hex: Optional[str] = None
    # Optional size specs supplied inline so a brand can upload a product plus
    # its sizes in a single request (Requirement 8.1).
    size_specs: List[ProductSizeSpecCreate] = []

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v: float) -> float:
        """Ensure price is positive."""
        if v <= 0:
            raise ValueError("price must be greater than zero")
        return v

    @field_validator("image_url", "garment_image_url", mode="before")
    @classmethod
    def validate_https_urls(cls, v: Optional[str]) -> Optional[str]:
        """Ensure image URLs are HTTPS."""
        if v is not None and isinstance(v, str):
            if not v.startswith("https://"):
                raise ValueError("image_url must use HTTPS")
            if not any(v.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                raise ValueError("image_url must be a supported format (jpg, png, webp)")
        return v

    @field_validator("dominant_color_hex")
    @classmethod
    def valid_color_hex(cls, v: Optional[str]) -> Optional[str]:
        """Normalize to '#RRGGBB' so skin-tone suitability scoring can parse it."""
        from app.schemas.user import normalize_hex_color
        return normalize_hex_color(v)


class ProductResponse(ProductCreate):
    """Schema for product response."""
    product_id: UUID
    brand_id: UUID
    size_specs: List[ProductSizeSpecResponse] = []
    # Populated by the recommendation engine ("why recommended" label).
    why_recommended: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class BrandCreate(BaseModel):
    """Schema for creating a brand."""
    company_name: str
    logo_url: Optional[HttpUrl] = None


class BrandResponse(BrandCreate):
    """Schema for brand response."""
    brand_id: UUID
    user_id: UUID
    products: List[ProductResponse] = []
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
