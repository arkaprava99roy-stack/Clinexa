"""
Clinexa — Response Agent (Phase 5)

Final response generator. Takes context, agent outputs, citations, and risk level,
and synthesizes a coherent, empathetic response to the user.
"""
from __future__ import annotations

import asyncio
import logging
from typing import List, Dict, Any, Optional
from app.safety.risk_classifier import RiskLevel
from app.safety.guardrails import SafetyGuardrails

log = logging.getLogger(__name__)

RESPONSE_PROMPT = """You are Clinexa, an intelligent AI healthcare assistant.
Your goal is to answer the user's health question clearly, empathetically, and accurately based on the context provided.

Context & Information:
{context_str}

User Question: {query}

Guidelines:
- Explain medical terms in simple language.
- Do not invent facts or diagnosis not present in the context.
- Be supportive, objective, and clear.
"""


class ResponseAgent:
    def __init__(self) -> None:
        self._llm = None
        self.guardrails = SafetyGuardrails()

    def _get_llm(self):
        if self._llm is None:
            from app.services.llm_service import get_llm_service
            self._llm = get_llm_service()
        return self._llm

    async def run(
        self,
        query: str,
        context_parts: List[str],
        citations: List[Dict[str, Any]],
        risk_level: RiskLevel = "low",
    ) -> Dict[str, Any]:
        """
        Synthesizes final user response with citations and safety disclaimers.
        Returns dict with:
          content, citations, risk_level
        """
        combined_context = "\n\n---\n\n".join(part for part in context_parts if part.strip())
        if not combined_context:
            combined_context = "No specific report context available for this question."

        llm = self._get_llm()
        user_msg = RESPONSE_PROMPT.format(
            context_str=combined_context,
            query=query,
        )

        try:
            raw_content, _ = await asyncio.to_thread(
                llm.completion,
                system_prompt="You are Clinexa, an empathetic health AI assistant.",
                user_message=user_msg,
                max_tokens=1024,
                temperature=0.3,
            )
        except Exception as exc:
            log.error("response_agent.llm_failed: %s", str(exc))
            raw_content = "I was unable to process your request at this moment. Please try asking again."

        # Apply output safety guardrails (inject disclaimer / emergency override if needed)
        final_content = self.guardrails.format_output(raw_content, risk_level)

        return {
            "content": final_content,
            "citations": citations,
            "risk_level": risk_level,
        }
