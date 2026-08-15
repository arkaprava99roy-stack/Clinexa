"""
Clinexa — Trend Service (Phase 6)

Computes health parameter trends over time from `health_trends` table and `health_parameters` data.
Calculates trend directions (increasing, decreasing, stable) using linear regression slope analysis.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

from app.core.config import settings

log = logging.getLogger(__name__)


def _get_supabase():
    from supabase import create_client
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def compute_direction(data_points: List[Dict[str, Any]]) -> str:
    """
    Compute trend direction from chronologically sorted data points.
    Uses linear regression slope.
    """
    if len(data_points) < 2:
        return "stable"

    values = [float(dp["value"]) for dp in data_points if dp.get("value") is not None]
    if len(values) < 2:
        return "stable"

    n = len(values)
    mean_x = (n - 1) / 2.0
    mean_y = sum(values) / float(n)
    numerator = sum((i - mean_x) * (v - mean_y) for i, v in enumerate(values))
    denominator = sum((i - mean_x) ** 2 for i in range(n))

    if denominator == 0:
        return "stable"

    slope = numerator / denominator
    threshold = 0.01 * abs(mean_y) if mean_y != 0 else 0.01

    if slope > threshold:
        return "increasing"
    elif slope < -threshold:
        return "decreasing"
    return "stable"


class TrendService:
    @staticmethod
    async def get_trend_parameters(user_id: str) -> List[str]:
        """Returns list of unique parameter names tracked for the user."""
        supabase = _get_supabase()
        try:
            res = supabase.table("health_trends")\
                .select("parameter")\
                .eq("user_id", user_id)\
                .execute()
            params = list(set(row["parameter"] for row in (res.data or []) if row.get("parameter")))
            params.sort()
            return params
        except Exception as exc:
            log.error("trend_service.get_parameters_failed: %s", str(exc))
            return []

    @staticmethod
    async def get_trend(user_id: str, parameter: str, period: str = "6m") -> Dict[str, Any]:
        """
        Retrieves historical trend data for a specific parameter filtered by time period.
        period: "1m" | "3m" | "6m" | "1y" | "all"
        """
        supabase = _get_supabase()
        try:
            res = supabase.table("health_trends")\
                .select("id, parameter, data_points, direction, updated_at")\
                .eq("user_id", user_id)\
                .eq("parameter", parameter)\
                .execute()

            if not res.data:
                return {
                    "parameter": parameter,
                    "unit": None,
                    "direction": "stable",
                    "data_points": [],
                }

            row = res.data[0]
            raw_points: List[Dict[str, Any]] = row.get("data_points") or []

            # Sort chronologically
            raw_points.sort(key=lambda x: x.get("date", ""))

            # Filter by period if needed
            filtered_points = TrendService._filter_by_period(raw_points, period)
            direction = compute_direction(filtered_points)
            unit = filtered_points[-1].get("unit") if filtered_points else None

            return {
                "parameter": parameter,
                "unit": unit,
                "direction": direction,
                "data_points": filtered_points,
            }
        except Exception as exc:
            log.error("trend_service.get_trend_failed: %s", str(exc))
            return {
                "parameter": parameter,
                "unit": None,
                "direction": "stable",
                "data_points": [],
            }

    @staticmethod
    def _filter_by_period(data_points: List[Dict[str, Any]], period: str) -> List[Dict[str, Any]]:
        if period == "all" or not data_points:
            return data_points

        days_map = {
            "1m": 30,
            "3m": 90,
            "6m": 180,
            "1y": 365,
        }
        days = days_map.get(period, 180)
        cutoff = datetime.now(timezone.utc).date() - timedelta(days=days)

        filtered = []
        for dp in data_points:
            try:
                dp_date = datetime.strptime(dp["date"][:10], "%Y-%m-%d").date()
                if dp_date >= cutoff:
                    filtered.append(dp)
            except Exception:
                filtered.append(dp)

        return filtered
