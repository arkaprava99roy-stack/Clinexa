"""
Clinexa — Report Service (Phase 2: pipeline trigger added)
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List

import logging
from supabase import create_client, Client

from app.core.config import settings

log = logging.getLogger(__name__)


def _get_supabase() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


class ReportService:

    @staticmethod
    async def create_and_enqueue(
        user_id: str,
        file_name: str,
        file_bytes: bytes,
        mime_type: str,
        background_tasks=None,  # fastapi.BackgroundTasks, optional
    ) -> str:
        """
        Upload file to Supabase Storage, create the report row,
        and enqueue the document pipeline as a background task.
        """
        supabase = _get_supabase()
        report_id = str(uuid.uuid4())

        # ── 1. Store raw file in Supabase Storage ──────────────────────────────
        storage_path = f"{user_id}/{report_id}/{file_name}"
        try:
            supabase.storage.from_("reports").upload(
                path=storage_path,
                file=file_bytes,
                file_options={"content-type": mime_type},
            )
        except Exception as exc:
            # If the bucket doesn't exist yet or upload fails, log but continue.
            # The pipeline will attempt re-download from storage.
            log.warning("report.storage_upload_warning", error=str(exc))
            storage_path = f"{user_id}/{report_id}/{file_name}"  # keep path

        # ── 2. Create report row ───────────────────────────────────────────────
        supabase.table("reports").insert({
            "id": report_id,
            "user_id": user_id,
            "file_name": file_name,
            "file_path": storage_path,
            "status": "processing",
        }).execute()

        log.info("report.created", report_id=report_id, user_id=user_id)

        # ── 3. Kick off document pipeline ─────────────────────────────────────
        if background_tasks is not None:
            from app.agents.document_agent import DocumentAgent
            agent = DocumentAgent()
            background_tasks.add_task(
                agent.run,
                report_id=report_id,
                user_id=user_id,
                file_bytes=file_bytes,
                file_name=file_name,
            )
            log.info("report.pipeline_enqueued", report_id=report_id)

        return report_id

    @staticmethod
    async def list_reports(user_id: str) -> List[dict]:
        supabase = _get_supabase()
        response = supabase.table("reports")\
            .select("id, file_name, report_type, status, uploaded_at")\
            .eq("user_id", user_id)\
            .order("uploaded_at", desc=True)\
            .execute()
        return response.data or []

    @staticmethod
    async def get_report(report_id: str, user_id: str) -> Optional[dict]:
        supabase = _get_supabase()

        report_resp = supabase.table("reports")\
            .select("id, file_name, status")\
            .eq("id", report_id)\
            .eq("user_id", user_id)\
            .single()\
            .execute()

        if not report_resp.data:
            return None

        params_resp = supabase.table("health_parameters")\
            .select("parameter, value, unit, ref_min, ref_max, status, page_number")\
            .eq("report_id", report_id)\
            .eq("user_id", user_id)\
            .execute()

        return {
            **report_resp.data,
            "parameters": params_resp.data or [],
        }

    @staticmethod
    async def delete_report(report_id: str, user_id: str) -> bool:
        supabase = _get_supabase()

        check = supabase.table("reports")\
            .select("id, file_path")\
            .eq("id", report_id)\
            .eq("user_id", user_id)\
            .execute()

        if not check.data:
            return False

        # Delete from storage
        try:
            file_path = check.data[0].get("file_path")
            if file_path:
                supabase.storage.from_("reports").remove([file_path])
        except Exception as exc:
            log.warning("report.storage_delete_failed", report_id=report_id, error=str(exc))

        supabase.table("reports")\
            .delete()\
            .eq("id", report_id)\
            .eq("user_id", user_id)\
            .execute()

        log.info("report.deleted", report_id=report_id, user_id=user_id)
        return True
