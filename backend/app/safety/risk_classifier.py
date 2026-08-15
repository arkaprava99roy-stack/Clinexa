"""
Clinexa — Risk Classifier (Phase 5)

Classifies user queries into three risk tiers:
  - HIGH: Acute medical emergency, severe red-flag symptoms, self-harm, active severe pain.
  - MEDIUM: Queries seeking specific diagnostic advice, prescription guidance, or interpretation of abnormal lab values.
  - LOW: General educational health queries, definition requests, report contents lookup.
"""
from __future__ import annotations

import logging
import re
from typing import Literal

log = logging.getLogger(__name__)

RiskLevel = Literal["low", "medium", "high"]

HIGH_RISK_KEYWORDS = [
    r"\bchest pain\b",
    r"\bshortness of breath\b",
    r"\bdifficulty breathing\b",
    r"\btrouble breathing\b",
    r"\bsevere bleeding\b",
    r"\bstroke\b",
    r"\bheart attack\b",
    r"\bsudden numbness\b",
    r"\bsuicide\b",
    r"\bsuicidal\b",
    r"\bself-harm\b",
    r"\bend it all\b",
    r"\bwant to die\b",
    r"\boverdose\b",
    r"\bpoisoning\b",
    r"\bpass out\b",
    r"\bunconscious\b",
    r"\bsevere abdominal pain\b",
    r"\bhigh fever in infant\b",
    r"\banaphylaxis\b",
]

MEDIUM_RISK_KEYWORDS = [
    r"\bshould i take\b",
    r"\bdosage\b",
    r"\bdiagnose me\b",
    r"\bwhat disease do i have\b",
    r"\bcancer\b",
    r"\btumor\b",
    r"\binfection\b",
    r"\babnormal result\b",
    r"\bprescription\b",
    r"\bside effects of\b",
    r"\bshould i go to the doctor\b",
]


class RiskClassifier:
    """Classifies risk level of user inputs using rule-based pattern matching and optional LLM verification."""

    def classify_text(self, text: str) -> RiskLevel:
        if not text or not text.strip():
            return "low"

        text_lower = text.lower()

        # Check HIGH risk patterns first
        for pattern in HIGH_RISK_KEYWORDS:
            if re.search(pattern, text_lower):
                log.warning("risk_classifier.high_risk_detected: pattern=%s", pattern)
                return "high"

        # Check MEDIUM risk patterns
        for pattern in MEDIUM_RISK_KEYWORDS:
            if re.search(pattern, text_lower):
                log.info("risk_classifier.medium_risk_detected: pattern=%s", pattern)
                return "medium"

        return "low"

    def classify_with_context(self, query: str, parameters: list[dict] = None) -> RiskLevel:
        base_risk = self.classify_text(query)
        if base_risk == "high":
            return "high"

        # Check if query touches abnormal critical lab parameters
        if parameters:
            has_abnormal = any(p.get("status") in ("HIGH", "LOW") for p in parameters)
            if has_abnormal and base_risk == "low":
                return "medium"

        return base_risk
