"""
Clinexa — Reports API Router (Phase 2: BackgroundTasks wired)
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.api.auth import CurrentUser, get_current_user
from app.core.config import settings

log = logging.getLogger(__name__)
router = APIRouter()


# ── Response Schemas ───────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    report_id: str
    status: str = "processing"


class HealthParameterOut(BaseModel):
    parameter: str
    value: Optional[float] = None
    unit: Optional[str] = None
    ref_min: Optional[float] = None
    ref_max: Optional[float] = None
    status: Optional[str] = None
    page_number: Optional[int] = None


class ReportSummary(BaseModel):
    id: str
    file_name: str
    report_type: Optional[str] = None
    status: str
    uploaded_at: datetime


class ReportDetail(BaseModel):
    id: str
    file_name: str
    status: str
    parameters: List[HealthParameterOut]


# ── Allowed MIME types ─────────────────────────────────────────────────────────

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/tiff",
}


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/upload", status_code=status.HTTP_202_ACCEPTED, response_model=UploadResponse)
async def upload_report(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Accept a PDF or image file.
    Validates MIME type and size, stores in Supabase Storage,
    creates a report row, and enqueues the document pipeline
    as a FastAPI background task.
    """
    # Validate MIME type
    content_type = file.content_type or ""
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "invalid_file_type",
                    "message": (
                        f"Unsupported file type: '{content_type}'. "
                        f"Allowed: PDF, JPEG, PNG, TIFF."
                    ),
                }
            },
        )

    # Read & validate size
    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "file_too_large",
                    "message": f"File exceeds the {settings.MAX_UPLOAD_MB} MB limit.",
                }
            },
        )

    from app.services.report_service import ReportService

    report_id = await ReportService.create_and_enqueue(
        user_id=current_user.user_id,
        file_name=file.filename or "upload",
        file_bytes=contents,
        mime_type=content_type,
        background_tasks=background_tasks,
    )

    log.info(
        "report.upload.accepted",
        report_id=report_id,
        user_id=current_user.user_id,
        bytes=len(contents),
    )
    return UploadResponse(report_id=report_id)


@router.get("", response_model=List[ReportSummary])
async def list_reports(current_user: CurrentUser = Depends(get_current_user)):
    from app.services.report_service import ReportService
    return await ReportService.list_reports(user_id=current_user.user_id)


@router.get("/{report_id}", response_model=ReportDetail)
async def get_report(
    report_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    from app.services.report_service import ReportService
    report = await ReportService.get_report(
        report_id=report_id, user_id=current_user.user_id
    )
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "not_found", "message": "Report not found."}},
        )
    return report


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    from app.services.report_service import ReportService
    deleted = await ReportService.delete_report(
        report_id=report_id, user_id=current_user.user_id
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "not_found", "message": "Report not found."}},
        )
