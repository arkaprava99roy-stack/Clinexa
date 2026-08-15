"""
Clinexa — Trends API Router
GET /api/trends
GET /api/trends/parameters
"""
from __future__ import annotations

from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.auth import CurrentUser, get_current_user

log = structlog.get_logger(__name__)
router = APIRouter()


class DataPoint(BaseModel):
    date: str
    value: float
    status: str


class TrendResponse(BaseModel):
    parameter: str
    unit: Optional[str]
    direction: Optional[str]
    data_points: List[DataPoint]


@router.get("", response_model=TrendResponse)
async def get_trend(
    parameter: str = Query(..., description="Parameter name, e.g. Hemoglobin"),
    period: str = Query("6m", description="Period: 1m | 3m | 6m | 1y | all"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Return trend data for a specific health parameter."""
    from app.services.trend_service import TrendService
    return await TrendService.get_trend(
        user_id=current_user.user_id,
        parameter=parameter,
        period=period,
    )


@router.get("/parameters", response_model=List[str])
async def get_parameters(current_user: CurrentUser = Depends(get_current_user)):
    """Return list of parameters for which the user has historical data."""
    from app.services.trend_service import TrendService
    return await TrendService.get_trend_parameters(user_id=current_user.user_id)
