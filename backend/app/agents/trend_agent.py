"""
Clinexa — Trend Agent (Phase 5)

Analyzes historical health parameter trends and explains trajectories
(increasing, decreasing, stable) over time in simple language.
"""
from __future__ import annotations

import asyncio
import logging
from typing import List, Dict, Any, Optional

log = logging.getLogger(__name__)

TREND_PROMPT = """You are an AI health trend analyst.
Your job is to explain parameter trends over time based on structured data.

Trend Data:
{trend_summary}

Instructions:
1. Explain how the value of each parameter has changed across the dates provided.
2. Note whether it has been increasing, decreasing, or remaining stable, and whether it's within normal bounds.
3. Keep the tone encouraging, educational, and easy to understand.
"""


class TrendAgent:
    def __init__(self) -> None:
        self._llm = None

    def _get_llm(self):
        if self._llm is None:
            from app.services.llm_service import get_llm_service
            self._llm = get_llm_service()
        return self._llm

    async def run(self, trend_data: List[Dict[str, Any]], query: Optional[str] = None) -> str:
        """
        trend_data list containing items with:
          parameter, direction, data_points: [{date, value, unit, status}]
        """
        if not trend_data:
            return "No historical trend data is available yet for your parameters."

        formatted_lines = []
        for t in trend_data:
            param = t.get("parameter", "Unknown")
            direction = t.get("direction", "stable")
            points = t.get("data_points", [])
            points_str = ", ".join(f"{dp.get('date')}: {dp.get('value')} ({dp.get('status')})" for dp in points)
            formatted_lines.append(f"Parameter: {param} | Direction: {direction} | Points: [{points_str}]")

        summary_text = "\n".join(formatted_lines)
        user_msg = f"User Query: {query or 'Explain my health trends'}\n\nTrend Details:\n{summary_text}"

        llm = self._get_llm()
        try:
            content, _ = await asyncio.to_thread(
                llm.completion,
                system_prompt="You are a health trend specialist.",
                user_message=user_msg,
                max_tokens=1024,
                temperature=0.2,
            )
            return content
        except Exception as exc:
            log.error("trend_agent.error: %s", str(exc))
            return f"Here is your health trend summary:\n\n{summary_text}"
