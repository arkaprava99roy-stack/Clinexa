"""
Clinexa — Parameter Extractor Unit Tests

Tests the LLM extraction path with a mocked Groq client.
CRITICAL: verifies the extractor NEVER assigns status itself —
  that's always the rule engine's job.
"""
from __future__ import annotations

import os
import sys
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


# ── Fixtures ───────────────────────────────────────────────────────────────────

SAMPLE_LLM_RESPONSE = {
    "parameters": [
        {
            "parameter": "Hemoglobin",
            "value": 14.2,
            "unit": "g/dL",
            "reference_range": {"min": 13.5, "max": 17.5},
            "page": 1,
        },
        {
            "parameter": "WBC",
            "value": 11.5,
            "unit": "x10^3/uL",
            "reference_range": {"min": 4.5, "max": 11.0},
            "page": 1,
        },
        {
            "parameter": "Glucose",
            "value": 65.0,
            "unit": "mg/dL",
            "reference_range": {"min": 70.0, "max": 99.0},
            "page": 1,
        },
        {
            "parameter": "TSH",
            "value": 2.1,
            "unit": "mIU/L",
            "reference_range": {"min": 0.4, "max": 4.0},
            "page": 1,
        },
        {
            # Missing reference range → UNKNOWN
            "parameter": "Cortisol",
            "value": 18.0,
            "unit": "ug/dL",
            "reference_range": {"min": None, "max": None},
            "page": 1,
        },
    ]
}

SAMPLE_PAGE_TEXT = """
LABORATORY REPORT
Hemoglobin    14.2  g/dL    [13.5-17.5]
WBC           11.5  x10^3/uL [4.5-11.0]
Glucose       65    mg/dL    [70-99]
TSH           2.1   mIU/L   [0.4-4.0]
Cortisol      18    ug/dL
"""


def make_mock_llm(response_json: dict = None):
    """Create a mock LLMService that returns a fixed extraction response."""
    mock = MagicMock()
    mock.extract_parameters.return_value = [
        {
            "parameter": p["parameter"],
            "value": p["value"],
            "unit": p.get("unit"),
            "ref_min": (p.get("reference_range") or {}).get("min"),
            "ref_max": (p.get("reference_range") or {}).get("max"),
            "page": p.get("page", 1),
        }
        for p in (response_json or SAMPLE_LLM_RESPONSE)["parameters"]
    ]
    return mock


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestParameterExtractorRuleEngineEnforcement:
    """
    CRITICAL: The extractor must NEVER set status itself.
    Status must always come from the rule engine.
    """

    @pytest.mark.asyncio
    async def test_status_assigned_by_rule_engine_not_llm(self):
        """
        Mock LLM returns raw params with no status.
        Rule engine must add status.
        """
        from app.document.extractor import ParameterExtractor

        extractor = ParameterExtractor()
        mock_llm = make_mock_llm()

        with patch.object(extractor, "_get_llm", return_value=mock_llm):
            results = await extractor.extract(SAMPLE_PAGE_TEXT, page_number=1)

        assert len(results) > 0
        for r in results:
            # Every result must have a status set by the rule engine
            assert "status" in r
            assert r["status"] in ("NORMAL", "HIGH", "LOW", "UNKNOWN"), \
                f"Unexpected status: {r['status']}"

    @pytest.mark.asyncio
    async def test_hemoglobin_is_normal(self):
        """14.2 g/dL with range [13.5-17.5] → NORMAL."""
        from app.document.extractor import ParameterExtractor
        extractor = ParameterExtractor()
        mock_llm = make_mock_llm()

        with patch.object(extractor, "_get_llm", return_value=mock_llm):
            results = await extractor.extract(SAMPLE_PAGE_TEXT, page_number=1)

        hgb = next((r for r in results if r["parameter"] == "Hemoglobin"), None)
        assert hgb is not None
        assert hgb["status"] == "NORMAL"

    @pytest.mark.asyncio
    async def test_wbc_is_high(self):
        """WBC = 11.5 with max=11.0 → HIGH."""
        from app.document.extractor import ParameterExtractor
        extractor = ParameterExtractor()
        mock_llm = make_mock_llm()

        with patch.object(extractor, "_get_llm", return_value=mock_llm):
            results = await extractor.extract(SAMPLE_PAGE_TEXT, page_number=1)

        wbc = next((r for r in results if r["parameter"] == "WBC"), None)
        assert wbc is not None
        assert wbc["status"] == "HIGH"

    @pytest.mark.asyncio
    async def test_glucose_is_low(self):
        """Glucose = 65 with min=70 → LOW."""
        from app.document.extractor import ParameterExtractor
        extractor = ParameterExtractor()
        mock_llm = make_mock_llm()

        with patch.object(extractor, "_get_llm", return_value=mock_llm):
            results = await extractor.extract(SAMPLE_PAGE_TEXT, page_number=1)

        gluc = next((r for r in results if r["parameter"] == "Glucose"), None)
        assert gluc is not None
        assert gluc["status"] == "LOW"

    @pytest.mark.asyncio
    async def test_missing_ref_range_is_unknown(self):
        """Cortisol has no reference range → UNKNOWN."""
        from app.document.extractor import ParameterExtractor
        extractor = ParameterExtractor()
        mock_llm = make_mock_llm()

        with patch.object(extractor, "_get_llm", return_value=mock_llm):
            results = await extractor.extract(SAMPLE_PAGE_TEXT, page_number=1)

        cortisol = next((r for r in results if r["parameter"] == "Cortisol"), None)
        assert cortisol is not None
        assert cortisol["status"] == "UNKNOWN"


class TestParameterExtractorEdgeCases:

    @pytest.mark.asyncio
    async def test_empty_text_returns_empty_list(self):
        """Empty page text → no parameters extracted."""
        from app.document.extractor import ParameterExtractor
        extractor = ParameterExtractor()
        # Should short-circuit before calling LLM
        results = await extractor.extract("", page_number=1)
        assert results == []

    @pytest.mark.asyncio
    async def test_llm_returns_empty_list(self):
        """LLM finds no parameters → empty result."""
        from app.document.extractor import ParameterExtractor
        extractor = ParameterExtractor()
        mock_llm = MagicMock()
        mock_llm.extract_parameters.return_value = []

        with patch.object(extractor, "_get_llm", return_value=mock_llm):
            results = await extractor.extract("Some text", page_number=1)
        assert results == []

    @pytest.mark.asyncio
    async def test_page_number_passed_through(self):
        """page number from the LLM response should be preserved."""
        from app.document.extractor import ParameterExtractor
        extractor = ParameterExtractor()

        mock_llm = MagicMock()
        mock_llm.extract_parameters.return_value = [{
            "parameter": "TestParam",
            "value": 5.0,
            "unit": "mg/dL",
            "ref_min": 1.0,
            "ref_max": 10.0,
            "page": 3,
        }]

        with patch.object(extractor, "_get_llm", return_value=mock_llm):
            results = await extractor.extract("TestParam: 5.0 mg/dL", page_number=3)

        assert results[0]["page"] == 3

    @pytest.mark.asyncio
    async def test_null_value_returns_unknown_status(self):
        """A parameter with value=None must be UNKNOWN (not error)."""
        from app.document.extractor import ParameterExtractor
        extractor = ParameterExtractor()

        mock_llm = MagicMock()
        mock_llm.extract_parameters.return_value = [{
            "parameter": "Mystery",
            "value": None,
            "unit": "mg/dL",
            "ref_min": 1.0,
            "ref_max": 10.0,
            "page": 1,
        }]

        with patch.object(extractor, "_get_llm", return_value=mock_llm):
            results = await extractor.extract("Mystery: pending", page_number=1)

        # null value should classify as UNKNOWN
        if results:
            assert results[0]["status"] == "UNKNOWN"


class TestLLMServiceClassification:
    """Unit tests for the classify_document method (mocked Groq)."""

    def test_classify_blood_test(self, monkeypatch):
        """Mock Groq returning 'blood_test'."""
        from app.services.llm_service import LLMService
        svc = LLMService()

        monkeypatch.setattr(svc, "completion", lambda *a, **kw: ("blood_test", {}))
        result = svc.classify_document("Hemoglobin WBC Platelets laboratory")
        assert result == "blood_test"

    def test_classify_invalid_label_defaults_to_other(self, monkeypatch):
        """If LLM returns garbage, should default to 'other'."""
        from app.services.llm_service import LLMService
        svc = LLMService()

        monkeypatch.setattr(svc, "completion", lambda *a, **kw: ("GARBAGE_LABEL_123", {}))
        result = svc.classify_document("Some medical text")
        assert result == "other"

    def test_classify_valid_labels(self, monkeypatch):
        """All 4 valid labels should pass through."""
        from app.services.llm_service import LLMService
        svc = LLMService()

        for label in ("blood_test", "prescription", "imaging_report", "other"):
            monkeypatch.setattr(svc, "completion", lambda *a, label=label, **kw: (label, {}))
            assert svc.classify_document("text") == label
