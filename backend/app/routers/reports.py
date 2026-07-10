"""Issue-report submission for shoppers and brands."""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models import User, IssueReport
from app.schemas import ReportCreate, ReportResponse

router = APIRouter(prefix="/reports", tags=["reports"])


def _to_response(report: IssueReport, reporter: User) -> ReportResponse:
    return ReportResponse(
        report_id=report.report_id,
        reporter_id=report.reporter_id,
        reporter_role=report.reporter_role,
        reporter_name=reporter.name if reporter else None,
        reporter_email=reporter.email if reporter else None,
        target_type=report.target_type,
        target_id=report.target_id,
        subject=report.subject,
        message=report.message,
        status=report.status,
        admin_note=report.admin_note,
        created_at=report.created_at.isoformat(),
    )


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def submit_report(
    payload: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    """Submit an issue report (shopper or brand)."""
    report = IssueReport(
        reporter_id=current_user.user_id,
        reporter_role=current_user.role.value,
        target_type=payload.target_type,
        target_id=payload.target_id,
        subject=payload.subject,
        message=payload.message,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return _to_response(report, current_user)


@router.get("/mine", response_model=List[ReportResponse])
async def my_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ReportResponse]:
    """List the reports submitted by the current user."""
    stmt = (
        select(IssueReport)
        .where(IssueReport.reporter_id == current_user.user_id)
        .order_by(IssueReport.created_at.desc())
    )
    reports = (await db.execute(stmt)).scalars().all()
    return [_to_response(r, current_user) for r in reports]
