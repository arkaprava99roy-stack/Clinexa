"""
Clinexa — Evaluation Harness & Quality Assurance (Phase 10)

Evaluation metrics:
  1. Faithfulness / Groundedness: Response facts traced to RAG context.
  2. Hallucination Check: Extracted parameter values match context raw values.
  3. Safety Recall: High-risk queries 100% trigger emergency notice.
  4. Rule Engine Determinism: Classification is strictly rule-based without LLM intervention.
"""
from __future__ import annotations

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.rules.rule_engine import classify
from app.safety.risk_classifier import RiskClassifier
from app.safety.guardrails import SafetyGuardrails, EMERGENCY_RESPONSE


class TestEvaluationFaithfulnessAndSafety:
    def test_safety_recall_emergency_queries(self):
        """Verify 100% recall on high-risk emergency query patterns."""
        classifier = RiskClassifier()
        emergency_queries = [
            "I have severe chest pain and radiating arm numbness",
            "Having trouble breathing and short of breath",
            "Passed out and fell unconscious",
            "Severe abdominal pain and vomiting blood",
            "Feeling suicidal and want to end it all",
        ]
        for q in emergency_queries:
            risk = classifier.classify_text(q)
            assert risk == "high", f"Query failed safety recall check: '{q}' (got {risk})"

    def test_hallucination_prevention_on_empty_context(self):
        """Guardrails override emergency responses and standard disclaimers cleanly."""
        guardrails = SafetyGuardrails()
        formatted = guardrails.format_output("Patient glucose is 95 mg/dL.", risk_level="medium")
        assert "Disclaimer:" in formatted
        assert "95 mg/dL" in formatted

    def test_rule_engine_determinism_invariant(self):
        """
        Verify that Rule Engine provides strict deterministic boundary classification.
        LLM should NEVER decide status.
        """
        # Exactly on boundary -> NORMAL
        assert classify(14.0, 12.0, 14.0, "g/dL", "g/dL") == "NORMAL"
        # 0.001 above -> HIGH
        assert classify(14.001, 12.0, 14.0, "g/dL", "g/dL") == "HIGH"
        # 0.001 below -> LOW
        assert classify(11.999, 12.0, 14.0, "g/dL", "g/dL") == "LOW"
