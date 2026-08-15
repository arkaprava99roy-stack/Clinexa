"""
Clinexa — Parameter Extractor
Phase 2: Orchestrates LLM extraction + rule-engine classification per page.

Critical rule (Section 4 / Section 6 of spec):
  The LLM extracts raw {parameter, value, unit, ref_min, ref_max, page}.
  The rule engine (rules/rule_engine.py) assigns status.
  NEVER let the LLM decide NORMAL/HIGH/LOW.
"""
from __future__ import annotations

import logging
from typing import Optional

log = logging.getLogger(__name__)


class ParameterExtractor:
    """
    Extracts lab parameters from page text and classifies them
    using the deterministic rule engine.
    """

    def __init__(self) -> None:
        # Lazy import to avoid circular deps at module load time
        self._llm: Optional[object] = None

    def _get_llm(self):
        if self._llm is None:
            from app.services.llm_service import get_llm_service
            self._llm = get_llm_service()
        return self._llm

    async def extract(self, text: str, page_number: int) -> list[dict]:
        """
        Extract and classify parameters from a page's text.

        Steps:
          1. LLM extracts raw parameter structs (no status).
          2. Rule engine classifies each as NORMAL/HIGH/LOW/UNKNOWN.

        Returns list of dicts with keys:
          parameter, value, unit, ref_min, ref_max, status, page
        """
        import asyncio

        llm = self._get_llm()

        # Run LLM in thread pool (it's a sync SDK call)
        raw_params: list[dict] = await asyncio.to_thread(
            llm.extract_parameters, text, page_number
        )

        if not raw_params:
            log.debug("extractor.no_params_found", page=page_number)
            return []

        # Classify with the deterministic rule engine (no LLM)
        from app.rules.rule_engine import classify_parameters
        classified = classify_parameters(raw_params)

        log.info(
            "extractor.classified",
            page=page_number,
            total=len(classified),
            abnormal=sum(1 for p in classified if p.get("status") in ("HIGH", "LOW")),
        )
        return classified
