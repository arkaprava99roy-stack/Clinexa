"""
Clinexa — Trend Service Unit Tests (Phase 6)

Tests:
  - Direction slope calculation (increasing, decreasing, stable)
  - Period filtering logic (1m, 3m, 6m, 1y, all)
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.trend_service import compute_direction, TrendService


class TestComputeDirection:
    def test_single_point_returns_stable(self):
        pts = [{"date": "2024-01-01", "value": 14.0}]
        assert compute_direction(pts) == "stable"

    def test_empty_points_returns_stable(self):
        assert compute_direction([]) == "stable"

    def test_increasing_trend(self):
        pts = [
            {"date": "2024-01-01", "value": 10.0},
            {"date": "2024-02-01", "value": 12.0},
            {"date": "2024-03-01", "value": 15.0},
        ]
        assert compute_direction(pts) == "increasing"

    def test_decreasing_trend(self):
        pts = [
            {"date": "2024-01-01", "value": 150.0},
            {"date": "2024-02-01", "value": 130.0},
            {"date": "2024-03-01", "value": 110.0},
        ]
        assert compute_direction(pts) == "decreasing"

    def test_stable_flat_trend(self):
        pts = [
            {"date": "2024-01-01", "value": 14.0},
            {"date": "2024-02-01", "value": 14.1},
            {"date": "2024-03-01", "value": 14.0},
        ]
        assert compute_direction(pts) == "stable"


class TestPeriodFilter:
    def test_all_period_returns_all(self):
        pts = [{"date": "2020-01-01", "value": 10}, {"date": "2024-01-01", "value": 20}]
        res = TrendService._filter_by_period(pts, "all")
        assert len(res) == 2

    def test_recent_period_filters_old_dates(self):
        today = datetime.now(timezone.utc).date()
        recent_date = (today - timedelta(days=10)).isoformat()
        old_date = (today - timedelta(days=400)).isoformat()

        pts = [
            {"date": old_date, "value": 10},
            {"date": recent_date, "value": 20},
        ]
        res = TrendService._filter_by_period(pts, "6m")
        assert len(res) == 1
        assert res[0]["value"] == 20
