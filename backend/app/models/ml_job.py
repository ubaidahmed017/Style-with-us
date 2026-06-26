"""
ML Job model for async processing of style analysis and virtual try-on tasks.
"""

import uuid
from sqlalchemy import Column, String, ForeignKey, Enum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import MLJobStatus


class MLJob(Base, TimestampMixin):
    """Async ML job tracking (style analysis, virtual try-on)."""

    __tablename__ = "ml_jobs"

    job_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    job_type = Column(
        String(50),
        nullable=False
    )  # "style_analysis" | "virtual_tryon"
    status = Column(
        Enum(MLJobStatus),
        default=MLJobStatus.UPLOADED,
        nullable=False
    )
    input_image_url = Column(String(1024), nullable=True)
    result_url = Column(String(1024), nullable=True)
    error_message = Column(String(1024), nullable=True)
    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("products.product_id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    user = relationship("User", back_populates="ml_jobs")

    __table_args__ = (
        Index("idx_ml_jobs_user_id", "user_id"),
        Index("idx_ml_jobs_status", "status"),
        Index("idx_ml_jobs_user_status", "user_id", "status"),
    )
