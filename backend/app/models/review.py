"""Product review left by a shopper (rolls up to a brand rating)."""

import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Review(Base, TimestampMixin):
    __tablename__ = "reviews"

    review_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False, index=True)
    # Denormalized so brand ratings can be aggregated without a join to products.
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.brand_id", ondelete="CASCADE"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 1..5
    comment = Column(String(2000), nullable=True)

    user = relationship("User")

    __table_args__ = (
        # One review per product per shopper.
        UniqueConstraint("user_id", "product_id", name="uq_reviews_user_product"),
        Index("idx_reviews_product_id", "product_id"),
        Index("idx_reviews_brand_id", "brand_id"),
    )
