"""
Clinexa — Admin API Router (stretch goal, admin role required)
GET /api/admin/eval
GET /api/admin/metrics
"""
from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from app.api.auth import CurrentUser, get_current_admin

log = structlog.get_logger(__name__)
router = APIRouter()


class EvalMetrics(BaseModel):
    retrieval_recall: Optional[float] = None
    context_relevance: Optional[float] = None
    answer_faithfulness: Optional[float] = None
    hallucination_rate: Optional[float] = None
    safety_accuracy: Optional[float] = None
    message: str = "Eval harness not yet run."


class OperationalMetrics(BaseModel):
    avg_latency_ms: Optional[float] = None
    error_rate: Optional[float] = None
    today_token_spend_usd: Optional[float] = None
    total_requests_today: Optional[int] = None


@router.get("/eval", response_model=EvalMetrics)
async def get_eval_metrics(admin: CurrentUser = Depends(get_current_admin)):
    """Return RAG + safety eval metrics (Phase 10)."""
    # Phase 10 will populate this from the eval harness
    return EvalMetrics()


@router.get("/metrics", response_model=OperationalMetrics)
async def get_operational_metrics(admin: CurrentUser = Depends(get_current_admin)):
    """Return live latency, error rate, and token cost metrics (Phase 11)."""
    from app.services.metrics_service import MetricsService
    return await MetricsService.get_today_summary()
