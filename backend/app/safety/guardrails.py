"""
Clinexa — Safety Guardrails (Phase 5)

Applies medical safety rules:
  - Input validation & red-flag detection
  - Emergency response override for high-risk inputs
  - Medical disclaimers injection based on risk level
"""
from __future__ import annotations

import logging
from typing import Optional
from app.safety.risk_classifier import RiskClassifier, RiskLevel

log = logging.getLogger(__name__)

EMERGENCY_RESPONSE = (
    "⚠️ **MEDICAL EMERGENCY NOTICE** ⚠️\n\n"
    "Your message indicates a potential emergency or severe medical condition. "
    "Clinexa is an AI tool and **cannot provide medical care or emergency assistance**.\n\n"
    "**Please take immediate action:**\n"
    "- Call your local emergency services (e.g., **911** in the US/Canada, **112** in Europe, **102/108** in India).\n"
    "- Go to the nearest Emergency Room or Urgent Care facility.\n"
    "- Contact your physician or healthcare provider right away.\n"
)

STANDARD_DISCLAIMER = (
    "\n\n---\n*Disclaimer: Clinexa provides AI-generated information for educational and informational purposes only. "
    "It is not a substitute for professional medical advice, diagnosis, or treatment.*"
)


class SafetyGuardrails:
    def __init__(self, classifier: Optional[RiskClassifier] = None) -> None:
        self.classifier = classifier or RiskClassifier()

    def check_input(self, user_query: str) -> tuple[RiskLevel, bool]:
        """
        Returns (risk_level, is_emergency).
        If is_emergency is True, the system should short-circuit with EMERGENCY_RESPONSE.
        """
        risk_level = self.classifier.classify_text(user_query)
        is_emergency = (risk_level == "high")
        return risk_level, is_emergency

    def format_output(self, response_text: str, risk_level: RiskLevel) -> str:
        """Appends appropriate disclaimers to outgoing assistant messages."""
        if risk_level == "high":
            return EMERGENCY_RESPONSE

        if risk_level == "medium" and "Disclaimer:" not in response_text:
            return response_text.strip() + STANDARD_DISCLAIMER

        return response_text.strip()
