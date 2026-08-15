"""
Clinexa — Safety Agent (Phase 5)

Wraps RiskClassifier & SafetyGuardrails into an agent interface.
Enforces safety rules prior to LLM processing and post-processing.
"""
from __future__ import annotations

import logging
from typing import Dict, Any, Tuple
from app.safety.guardrails import SafetyGuardrails, EMERGENCY_RESPONSE
from app.safety.risk_classifier import RiskLevel

log = logging.getLogger(__name__)


class SafetyAgent:
    def __init__(self) -> None:
        self.guardrails = SafetyGuardrails()

    async def evaluate_input(self, query: str) -> Tuple[RiskLevel, bool, Optional[str]]:
        """
        Evaluates user input.
        Returns (risk_level, is_emergency, emergency_override_text)
        """
        risk_level, is_emergency = self.guardrails.check_input(query)
        override = EMERGENCY_RESPONSE if is_emergency else None
        log.info("safety_agent.evaluated_input: risk=%s emergency=%s", risk_level, is_emergency)
        return risk_level, is_emergency, override

    def process_output(self, content: str, risk_level: RiskLevel) -> str:
        """Applies output guardrails and disclaimer injection."""
        return self.guardrails.format_output(content, risk_level)
