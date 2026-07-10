"""Issue reports submitted by shoppers and brands, managed by admins."""

import uuid
from sqlalchemy import Column, String, ForeignKey, Enum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import ReportStatus


class IssueReport(Base, TimestampMixin):
    __tablename__ = "issue_reports"

    report_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    reporter_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    reporter_role = Column(String(20), nullable=False)  # shopper | brand
    # What the report is about: product | brand | order | account | other.
    target_type = Column(String(30), nullable=False, default="other")
    target_id = Column(String(64), nullable=True)  # optional id of the target
    subject = Column(String(200), nullable=False)
    message = Column(String(2000), nullable=False)
    status = Column(Enum(ReportStatus), nullable=False, default=ReportStatus.OPEN)
    admin_note = Column(String(1000), nullable=True)

    reporter = relationship("User")

    __table_args__ = (
        Index("idx_issue_reports_status", "status"),
        Index("idx_issue_reports_reporter", "reporter_id"),
    )
