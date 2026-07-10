"""
Machine learning job submission and status endpoints.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models import User, MLJob, Product
from app.models.enums import MLJobStatus
from app.schemas import (
    StyleAnalysisRequest,
    VirtualTryOnRequest,
    MLJobResponse,
    MLJobStatus as MLJobStatusSchema,
)

router = APIRouter(prefix="/ml", tags=["ml"])


@router.post("/style-analysis", response_model=MLJobResponse, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("10/minute")
async def submit_style_analysis(
    request: Request,
    payload: StyleAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MLJobResponse:
    """
    Submit a style analysis job (on-device body shape and skin tone analysis).

    Returns HTTP 202 (Accepted) with job ID for polling.
    The actual ML processing happens asynchronously via Celery worker.
    """
    # Create ML job record. Note: the actual analysis runs on-device (Flutter);
    # this endpoint only records the job for auditing/admin visibility.
    job = MLJob(
        user_id=current_user.user_id,
        job_type="style_analysis",
        status=MLJobStatus.QUEUED,
        input_image_url=str(payload.image_url),
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    return MLJobResponse(
        job_id=job.job_id,
        status=job.status.value,
        created_at=job.created_at.isoformat(),
    )


@router.post("/virtual-tryon", response_model=MLJobResponse, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("10/minute")
async def submit_virtual_tryon(
    request: Request,
    payload: VirtualTryOnRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MLJobResponse:
    """
    Submit a virtual try-on job (on-device garment compositing).

    Gender-gating is performed on the client side before this endpoint is called.
    Returns HTTP 202 (Accepted) with job ID for polling.
    """
    # Verify product exists
    stmt = select(Product).where(Product.product_id == payload.product_id)
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Create ML job record. Actual compositing runs on-device (Flutter).
    job = MLJob(
        user_id=current_user.user_id,
        job_type="virtual_tryon",
        status=MLJobStatus.QUEUED,
        input_image_url=str(payload.image_url),
        product_id=payload.product_id,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    return MLJobResponse(
        job_id=job.job_id,
        status=job.status.value,
        created_at=job.created_at.isoformat(),
    )


@router.get("/jobs/{job_id}", response_model=MLJobStatusSchema)
async def get_job_status(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MLJobStatusSchema:
    """
    Get the status of an ML job.

    Returns current status (QUEUED, PROCESSING, COMPLETED, FAILED).
    When status is COMPLETED, result_url contains the composited image or analysis results.
    """
    # Get job
    stmt = select(MLJob).where(MLJob.job_id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # Verify ownership
    if job.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this job"
        )

    return MLJobStatusSchema(
        job_id=job.job_id,
        status=job.status.value,
        result_url=job.result_url,
        error_message=job.error_message,
        created_at=job.created_at.isoformat(),
        updated_at=job.updated_at.isoformat(),
    )
