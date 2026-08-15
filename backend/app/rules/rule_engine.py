"""
Clinexa — Rule Engine (deterministic abnormality detection)

IMPORTANT: No LLM is involved here. Classification is purely algorithmic.
The LLM only explains a status it's given by this engine.
"""
from __future__ import annotations

from typing import Optional
import structlog

log = structlog.get_logger(__name__)

# Known incompatible unit pairs — flag as UNKNOWN rather than silently comparing.
# Add entries as more unit pairs are discovered.
INCOMPATIBLE_UNIT_PAIRS: set[frozenset[str]] = {
    frozenset({"mg/dL", "mmol/L"}),
    frozenset({"g/dL", "g/L"}),
    frozenset({"IU/L", "μkat/L"}),
    frozenset({"mEq/L", "mmol/L"}),
}


def units_are_compatible(value_unit: Optional[str], ref_unit: Optional[str]) -> bool:
    """
    Return False if the value unit and reference unit are from a known
    incompatible pair (e.g. mg/dL vs mmol/L for the same parameter).
    Missing units are treated as compatible (no unit information to conflict).
    """
    if value_unit is None or ref_unit is None:
        return True
    if value_unit.strip().lower() == ref_unit.strip().lower():
        return True
    pair = frozenset({value_unit.strip(), ref_unit.strip()})
    return pair not in INCOMPATIBLE_UNIT_PAIRS


def classify(
    value: float,
    ref_min: Optional[float],
    ref_max: Optional[float],
    value_unit: Optional[str] = None,
    ref_unit: Optional[str] = None,
) -> str:
    """
    Classify a numeric lab value as NORMAL, HIGH, LOW, or UNKNOWN.

    Rules (in priority order):
    1. If units are incompatible → UNKNOWN (avoids silent cross-unit comparison)
    2. If ref_min or ref_max is missing → UNKNOWN
    3. If value < ref_min → LOW
    4. If value > ref_max → HIGH
    5. Otherwise → NORMAL

    Boundary values are inclusive (value == ref_min → NORMAL,
                                   value == ref_max → NORMAL).
    """
    if not units_are_compatible(value_unit, ref_unit):
        log.warning(
            "rule_engine.unit_mismatch",
            value_unit=value_unit,
            ref_unit=ref_unit,
        )
        return "UNKNOWN"

    if ref_min is None or ref_max is None:
        return "UNKNOWN"

    if value < ref_min:
        return "LOW"

    if value > ref_max:
        return "HIGH"

    return "NORMAL"


def classify_parameters(
    parameters: list[dict],
) -> list[dict]:
    """
    Apply classify() to a list of extracted parameter dicts.
    Each dict should have keys: parameter, value, unit, ref_min, ref_max.
    Returns the same list with a 'status' key added/overwritten on each item.
    """
    results = []
    for param in parameters:
        value = param.get("value")
        ref_min = param.get("ref_min")
        ref_max = param.get("ref_max")
        value_unit = param.get("unit")
        ref_unit = param.get("ref_unit")  # optional reference-range unit

        if value is None:
            status = "UNKNOWN"
        else:
            status = classify(
                value=float(value),
                ref_min=float(ref_min) if ref_min is not None else None,
                ref_max=float(ref_max) if ref_max is not None else None,
                value_unit=value_unit,
                ref_unit=ref_unit,
            )

        results.append({**param, "status": status})

    return results
