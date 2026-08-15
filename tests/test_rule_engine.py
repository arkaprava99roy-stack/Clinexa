"""
Clinexa — Rule Engine Unit Tests

Covers: exact boundary, missing reference range, negative values,
unit mismatch, and normal/high/low cases.
"""
import pytest

from app.rules.rule_engine import classify, classify_parameters, units_are_compatible


# ── classify() tests ───────────────────────────────────────────────────────────

class TestClassify:
    def test_normal_in_range(self):
        assert classify(5.0, 4.0, 6.0) == "NORMAL"

    def test_high_above_max(self):
        assert classify(7.0, 4.0, 6.0) == "HIGH"

    def test_low_below_min(self):
        assert classify(3.0, 4.0, 6.0) == "LOW"

    def test_exact_lower_boundary_is_normal(self):
        assert classify(4.0, 4.0, 6.0) == "NORMAL"

    def test_exact_upper_boundary_is_normal(self):
        assert classify(6.0, 4.0, 6.0) == "NORMAL"

    def test_just_above_upper_boundary_is_high(self):
        assert classify(6.001, 4.0, 6.0) == "HIGH"

    def test_just_below_lower_boundary_is_low(self):
        assert classify(3.999, 4.0, 6.0) == "LOW"

    def test_missing_ref_min_returns_unknown(self):
        assert classify(5.0, None, 6.0) == "UNKNOWN"

    def test_missing_ref_max_returns_unknown(self):
        assert classify(5.0, 4.0, None) == "UNKNOWN"

    def test_both_ref_missing_returns_unknown(self):
        assert classify(5.0, None, None) == "UNKNOWN"

    def test_negative_value_within_range(self):
        # Some parameters (e.g. temperature deltas) can be negative
        assert classify(-1.0, -2.0, 0.0) == "NORMAL"

    def test_negative_value_below_range(self):
        assert classify(-3.0, -2.0, 0.0) == "LOW"

    def test_negative_value_above_range(self):
        assert classify(1.0, -2.0, 0.0) == "HIGH"

    def test_unit_mismatch_returns_unknown(self):
        assert classify(100.0, 70.0, 110.0, value_unit="mg/dL", ref_unit="mmol/L") == "UNKNOWN"

    def test_compatible_units_classified_normally(self):
        assert classify(100.0, 70.0, 110.0, value_unit="mg/dL", ref_unit="mg/dL") == "NORMAL"

    def test_no_units_provided_classified_normally(self):
        assert classify(100.0, 70.0, 110.0) == "NORMAL"

    def test_zero_value_normal(self):
        assert classify(0.0, 0.0, 10.0) == "NORMAL"

    def test_zero_value_low(self):
        assert classify(0.0, 1.0, 10.0) == "LOW"


# ── units_are_compatible() tests ───────────────────────────────────────────────

class TestUnitsCompatible:
    def test_same_units_compatible(self):
        assert units_are_compatible("mg/dL", "mg/dL") is True

    def test_known_incompatible_pair(self):
        assert units_are_compatible("mg/dL", "mmol/L") is False

    def test_reversed_incompatible_pair(self):
        assert units_are_compatible("mmol/L", "mg/dL") is False

    def test_none_value_unit_compatible(self):
        assert units_are_compatible(None, "mg/dL") is True

    def test_none_ref_unit_compatible(self):
        assert units_are_compatible("mg/dL", None) is True

    def test_both_none_compatible(self):
        assert units_are_compatible(None, None) is True

    def test_unknown_unit_pair_compatible(self):
        # If we don't know it's incompatible, we don't block it
        assert units_are_compatible("fL", "pg") is True


# ── classify_parameters() tests ───────────────────────────────────────────────

class TestClassifyParameters:
    def test_adds_status_to_each_param(self):
        params = [
            {"parameter": "Hemoglobin", "value": 15.0, "unit": "g/dL", "ref_min": 12.0, "ref_max": 16.0},
            {"parameter": "Glucose", "value": 200.0, "unit": "mg/dL", "ref_min": 70.0, "ref_max": 100.0},
        ]
        result = classify_parameters(params)
        assert result[0]["status"] == "NORMAL"
        assert result[1]["status"] == "HIGH"

    def test_missing_value_returns_unknown(self):
        params = [{"parameter": "TSH", "value": None, "unit": "mIU/L", "ref_min": 0.4, "ref_max": 4.0}]
        result = classify_parameters(params)
        assert result[0]["status"] == "UNKNOWN"

    def test_original_fields_preserved(self):
        params = [{"parameter": "WBC", "value": 5.0, "unit": "×10³/μL", "ref_min": 4.5, "ref_max": 11.0, "page": 2}]
        result = classify_parameters(params)
        assert result[0]["parameter"] == "WBC"
        assert result[0]["page"] == 2
