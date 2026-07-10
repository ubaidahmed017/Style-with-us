"""Schemas for issue reports."""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from app.models.enums import ReportStatus


class ReportCreate(BaseModel):
    subject: str
    message: str
    target_type: str = "other"       # product | brand | order | account | other
    target_id: Optional[str] = None


class ReportUpdate(BaseModel):
    status: ReportStatus
    admin_note: Optional[str] = None


class ReportResponse(BaseModel):
    report_id: UUID
    reporter_id: UUID
    reporter_role: str
    reporter_name: Optional[str] = None
    reporter_email: Optional[str] = None
    target_type: str
    target_id: Optional[str] = None
    subject: str
    message: str
    status: ReportStatus
    admin_note: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True
