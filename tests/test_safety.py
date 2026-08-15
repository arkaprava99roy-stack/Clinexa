"""
Clinexa — Safety & Guardrails Unit Tests (Phase 5)

Tests:
  - RiskClassifier: high, medium, low risk categorization
  - SafetyGuardrails: emergency detection, short-circuit override, disclaimer formatting
  - SafetyAgent: integration with classifier and guardrails
"""
from __future__ import annotations

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.safety.risk_classifier import RiskClassifier
from app.safety.guardrails import SafetyGuardrails, EMERGENCY_RESPONSE, STANDARD_DISCLAIMER
from app.agents.safety_agent import SafetyAgent


class TestRiskClassifier:
    def setup_method(self):
        self.classifier = RiskClassifier()

    def test_high_risk_chest_pain(self):
        assert self.classifier.classify_text("I have severe chest pain and trouble breathing") == "high"

    def test_high_risk_stroke(self):
        assert self.classifier.classify_text("My arm is suddenly numb and face is drooping stroke") == "high"

    def test_high_risk_suicide(self):
        assert self.classifier.classify_text("Thinking about suicide") == "high"

    def test_medium_risk_dosage(self):
        assert self.classifier.classify_text("What dosage of medication should I take?") == "medium"

    def test_medium_risk_diagnose(self):
        assert self.classifier.classify_text("Can you diagnose me based on these blood test results?") == "medium"

    def test_low_risk_general_info(self):
        assert self.classifier.classify_text("What is hemoglobin?") == "low"

    def test_low_risk_empty_query(self):
        assert self.classifier.classify_text("") == "low"

    def test_abnormal_param_upgrades_low_to_medium(self):
        params = [{"parameter": "Glucose", "value": 180, "status": "HIGH"}]
        risk = self.classifier.classify_with_context("What is glucose?", parameters=params)
        assert risk == "medium"


class TestSafetyGuardrails:
    def setup_method(self):
        self.guardrails = SafetyGuardrails()

    def test_emergency_query_triggers_is_emergency(self):
        risk, is_emergency = self.guardrails.check_input("Severe chest pain, short of breath")
        assert risk == "high"
        assert is_emergency is True

    def test_high_risk_format_output_returns_emergency_notice(self):
        output = self.guardrails.format_output("Here is some text", risk_level="high")
        assert EMERGENCY_RESPONSE in output

    def test_medium_risk_format_output_appends_disclaimer(self):
        output = self.guardrails.format_output("Your glucose level is slightly elevated.", risk_level="medium")
        assert "Disclaimer:" in output
        assert STANDARD_DISCLAIMER.strip() in output

    def test_low_risk_format_output_no_disclaimer(self):
        output = self.guardrails.format_output("Hemoglobin carries oxygen in red blood cells.", risk_level="low")
        assert "Disclaimer:" not in output


class TestSafetyAgent:
    @pytest.mark.asyncio
    async def test_evaluate_input_emergency(self):
        agent = SafetyAgent()
        risk, is_emergency, override = await agent.evaluate_input("I'm having a heart attack")
        assert risk == "high"
        assert is_emergency is True
        assert override == EMERGENCY_RESPONSE

    @pytest.mark.asyncio
    async def test_evaluate_input_normal(self):
        agent = SafetyAgent()
        risk, is_emergency, override = await agent.evaluate_input("What is TSH?")
        assert risk == "low"
        assert is_emergency is False
        assert override is None
