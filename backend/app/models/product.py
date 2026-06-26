"""
Brand and Product models with size specifications.
"""

import uuid
from sqlalchemy import Column, String, Float, Integer, ForeignKey, Enum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import GenderTarget


class Brand(Base, TimestampMixin):
    """Brand partner account linked to a User."""

    __tablename__ = "brands"

    brand_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    company_name = Column(String(255), nullable=False)
    logo_url = Column(String(1024), nullable=True)

    # Relationships
    user = relationship("User", back_populates="brand")
    products = relationship("Product", back_populates="brand", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_brands_user_id", "user_id"),
    )


class Product(Base, TimestampMixin):
    """Product catalog item."""

    __tablename__ = "products"

    product_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    brand_id = Column(
        UUID(as_uuid=True),
        ForeignKey("brands.brand_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    sku = Column(String(100), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(2000), nullable=True)
    price = Column(Float, nullable=False)  # Must be > 0
    image_url = Column(String(1024), nullable=True)
    garment_image_url = Column(String(1024), nullable=True)  # For virtual try-on
    gender_target = Column(
        Enum(GenderTarget),
        nullable=False
    )
    dominant_color_hex = Column(String(7), nullable=True)  # e.g., "#E63946"

    # Relationships
    brand = relationship("Brand", back_populates="products")
    size_specs = relationship("ProductSizeSpec", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_products_brand_id", "brand_id"),
        Index("idx_products_gender_target", "gender_target"),
    )


class ProductSizeSpec(Base, TimestampMixin):
    """Size specification for a product (e.g., size M with measurement ranges)."""

    __tablename__ = "product_size_specs"

    spec_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("products.product_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    size_label = Column(String(20), nullable=False)  # XS, S, M, L, XL, XXL, or custom
    stock_quantity = Column(Integer, default=0, nullable=False)  # Must be >= 0

    # Measurement ranges (all in cm)
    chest_min = Column(Float, nullable=False)
    chest_max = Column(Float, nullable=False)
    waist_min = Column(Float, nullable=False)
    waist_max = Column(Float, nullable=False)
    hips_min = Column(Float, nullable=False)
    hips_max = Column(Float, nullable=False)
    inseam_min = Column(Float, nullable=True)  # Optional for tops
    inseam_max = Column(Float, nullable=True)
    shoulder_width_min = Column(Float, nullable=True)
    shoulder_width_max = Column(Float, nullable=True)

    # Relationships
    product = relationship("Product", back_populates="size_specs")

    __table_args__ = (
        Index("idx_product_size_specs_product_id", "product_id"),
        Index("idx_product_size_specs_product_size", "product_id", "size_label"),
    )
