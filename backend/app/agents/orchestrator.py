"""
Clinexa — Multi-Agent Orchestrator (Phase 5)

Orchestrates user queries through the multi-agent pipeline:
  1. Safety Evaluation (SafetyAgent) -> short-circuit emergency
  2. Intent Routing (classify intent: report_analysis | trend_analysis | rag_qa | general)
  3. Sub-Agent Execution (AnalysisAgent / TrendAgent / RAGAgent)
  4. Response Synthesis (ResponseAgent) -> final output with citations and safety disclaimers
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Dict, Any, List, Optional

from app.agents.safety_agent import SafetyAgent
from app.agents.rag_agent import RAGAgent
from app.agents.analysis_agent import AnalysisAgent
from app.agents.trend_agent import TrendAgent
from app.agents.response_agent import ResponseAgent

log = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self) -> None:
        self.safety_agent = SafetyAgent()
        self.rag_agent = RAGAgent()
        self.analysis_agent = AnalysisAgent()
        self.trend_agent = TrendAgent()
        self.response_agent = ResponseAgent()

    def classify_intent(self, query: str) -> str:
        """Determines query intent."""
        q_lower = query.lower()
        if any(w in q_lower for w in ["trend", "over time", "progress", "history", "tracking", "trajectory"]):
            return "trend_analysis"
        if any(w in q_lower for w in ["report", "lab result", "blood test", "parameter", "range", "explain my", "what is my"]):
            return "report_analysis"
        return "rag_qa"

    async def run(
        self,
        query: str,
        user_id: str,
        report_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Main entry point for multi-agent query processing.
        """
        log.info("orchestrator.start query=%s user_id=%s", query[:50], user_id)

        # 1. Safety check
        risk_level, is_emergency, emergency_text = await self.safety_agent.evaluate_input(query)
        if is_emergency and emergency_text:
            log.warning("orchestrator.short_circuit_emergency user_id=%s", user_id)
            return {
                "content": emergency_text,
                "citations": [],
                "risk_level": "high",
            }

        # 2. Intent classification
        intent = self.classify_intent(query)
        log.info("orchestrator.intent_classified intent=%s", intent)

        context_parts: List[str] = []
        citations: List[Dict[str, Any]] = []

        # 3. Retrieve RAG context
        rag_res = await self.rag_agent.run(
            query=query,
            user_id=user_id,
            top_k=5,
            report_id=report_id,
        )

        if rag_res.get("context"):
            context_parts.append(f"Retrieved Medical Document Context:\n{rag_res['context']}")
        if rag_res.get("citations"):
            citations.extend(rag_res["citations"])

        # 4. Invoke specialized domain agents based on intent
        if intent == "report_analysis":
            # Fetch user parameters from DB
            params = await self._fetch_user_parameters(user_id, report_id)
            if params:
                analysis_text = await self.analysis_agent.run(params, query)
                context_parts.append(f"Analysis Agent Findings:\n{analysis_text}")

        elif intent == "trend_analysis":
            # Fetch user trend data from DB
            trends = await self._fetch_user_trends(user_id)
            if trends:
                trend_text = await self.trend_agent.run(trends, query)
                context_parts.append(f"Trend Agent Findings:\n{trend_text}")

        # 5. Synthesize final response
        final_res = await self.response_agent.run(
            query=query,
            context_parts=context_parts,
            citations=citations,
            risk_level=risk_level,
        )

        return final_res

    async def _fetch_user_parameters(self, user_id: str, report_id: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            from supabase import create_client
            from app.core.config import settings

            supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
            q = supabase.table("health_parameters").select("*").eq("user_id", user_id)
            if report_id:
                q = q.eq("report_id", report_id)
            res = await asyncio.to_thread(lambda: q.execute())
            return res.data or []
        except Exception as exc:
            log.warning("orchestrator.fetch_params_failed: %s", str(exc))
            return []

    async def _fetch_user_trends(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            from supabase import create_client
            from app.core.config import settings

            supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
            res = await asyncio.to_thread(
                lambda: supabase.table("health_trends").select("*").eq("user_id", user_id).execute()
            )
            return res.data or []
        except Exception as exc:
            log.warning("orchestrator.fetch_trends_failed: %s", str(exc))
            return []
