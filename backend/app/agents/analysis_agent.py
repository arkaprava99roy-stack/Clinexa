"""
Clinexa — Analysis Agent (Phase 5)

Generates patient-friendly explanations for lab report parameters and health status.
Strict rule: Does NOT decide NORMAL/HIGH/LOW (Rule Engine does that).
Only explains the given status and parameter meanings in plain language.
"""
from __future__ import annotations

import asyncio
import logging
from typing import List, Dict, Any, Optional

log = logging.getLogger(__name__)

ANALYSIS_PROMPT = """You are a compassionate, clear, and accurate AI health educator.
Your task is to explain the user's laboratory parameters to them in plain language.

Parameters to explain (Rule Engine has ALREADY classified status):
{parameters_summary}

Instructions:
1. Explain what each parameter is in simple terms (e.g. Hemoglobin is the protein in red blood cells that carries oxygen).
2. For parameters marked HIGH or LOW, explain what that might generally mean in plain language without making a definitive medical diagnosis.
3. Be reassuring, objective, and easy to understand for someone without medical training.
4. Keep the summary structured and concise.
"""


class AnalysisAgent:
    def __init__(self) -> None:
        self._llm = None

    def _get_llm(self):
        if self._llm is None:
            from app.services.llm_service import get_llm_service
            self._llm = get_llm_service()
        return self._llm

    async def run(self, parameters: List[Dict[str, Any]], query: Optional[str] = None) -> str:
        """
        Explains parameters provided in list format.
        Each item has: {parameter, value, unit, ref_min, ref_max, status}
        """
        if not parameters:
            return "No specific lab parameters were found in the report data."

        formatted_lines = []
        for p in parameters:
            name = p.get("parameter", "Unknown")
            val = p.get("value")
            unit = p.get("unit") or ""
            ref_min = p.get("ref_min")
            ref_max = p.get("ref_max")
            status = p.get("status", "UNKNOWN")

            val_str = f"{val} {unit}".strip() if val is not None else "N/A"
            ref_str = f"[{ref_min} - {ref_max}]" if ref_min is not None and ref_max is not None else "No ref range"
            formatted_lines.append(f"- {name}: {val_str} (Reference: {ref_str}) -> Status: {status}")

        param_summary_text = "\n".join(formatted_lines)
        prompt = ANALYSIS_PROMPT.format(parameters_summary=param_summary_text)

        if query:
            user_msg = f"User Question: {query}\n\nReport Data:\n{param_summary_text}"
        else:
            user_msg = f"Please explain these lab parameters:\n{param_summary_text}"

        llm = self._get_llm()
        try:
            content, _ = await asyncio.to_thread(
                llm.completion,
                system_prompt="You are a clear and empathetic medical report analyst.",
                user_message=user_msg,
                max_tokens=1024,
                temperature=0.2,
            )
            return content
        except Exception as exc:
            log.error("analysis_agent.error: %s", str(exc))
            # Fallback deterministic response
            return f"Here is a summary of your lab results:\n\n{param_summary_text}"
