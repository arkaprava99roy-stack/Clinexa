"""
Clinexa — Multi-Agent System Unit Tests (Phase 5)

Tests:
  - Orchestrator intent classification (report_analysis, trend_analysis, rag_qa)
  - Emergency short-circuit in Orchestrator
  - AnalysisAgent parameter explanation output
  - TrendAgent parameter trend trajectory output
  - ResponseAgent synthesis & disclaimer inclusion
"""
from __future__ import annotations

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.agents.orchestrator import Orchestrator
from app.agents.analysis_agent import AnalysisAgent
from app.agents.trend_agent import TrendAgent
from app.agents.response_agent import ResponseAgent
from app.safety.guardrails import EMERGENCY_RESPONSE


class TestOrchestratorIntentClassification:
    def setup_method(self):
        self.orchestrator = Orchestrator()

    def test_intent_trend_analysis(self):
        assert self.orchestrator.classify_intent("How are my glucose levels tracking over time?") == "trend_analysis"

    def test_intent_report_analysis(self):
        assert self.orchestrator.classify_intent("Explain my blood test report parameters") == "report_analysis"

    def test_intent_rag_qa(self):
        assert self.orchestrator.classify_intent("What causes high cholesterol?") == "rag_qa"


class TestOrchestratorPipeline:
    @pytest.mark.asyncio
    async def test_emergency_query_short_circuits(self):
        orchestrator = Orchestrator()
        res = await orchestrator.run("I have severe chest pain and cannot breathe", user_id="u1")
        assert res["risk_level"] == "high"
        assert EMERGENCY_RESPONSE in res["content"]
        assert res["citations"] == []

    @pytest.mark.asyncio
    async def test_normal_query_flow(self):
        orchestrator = Orchestrator()

        mock_rag_res = {
            "context": "Sample lab text content",
            "citations": [{"report_id": "r1", "report_name": "Test.pdf", "page": 1}],
            "chunks": []
        }

        with patch.object(orchestrator.rag_agent, "run", new=AsyncMock(return_value=mock_rag_res)), \
             patch.object(orchestrator, "_fetch_user_parameters", new=AsyncMock(return_value=[])), \
             patch.object(orchestrator.response_agent, "run", new=AsyncMock(return_value={
                 "content": "Hemoglobin is normal.",
                 "citations": mock_rag_res["citations"],
                 "risk_level": "low"
             })):

            res = await orchestrator.run("What is my hemoglobin level?", user_id="u1")

            assert res["content"] == "Hemoglobin is normal."
            assert len(res["citations"]) == 1
            assert res["risk_level"] == "low"


class TestAnalysisAgent:
    @pytest.mark.asyncio
    async def test_analysis_agent_no_params(self):
        agent = AnalysisAgent()
        res = await agent.run([])
        assert "No specific lab parameters" in res

    @pytest.mark.asyncio
    async def test_analysis_agent_with_params(self):
        agent = AnalysisAgent()
        mock_llm = MagicMock()
        mock_llm.completion.return_value = ("Hemoglobin 14.2 g/dL is within normal range.", {})

        with patch.object(agent, "_get_llm", return_value=mock_llm):
            params = [{
                "parameter": "Hemoglobin",
                "value": 14.2,
                "unit": "g/dL",
                "ref_min": 13.5,
                "ref_max": 17.5,
                "status": "NORMAL"
            }]
            res = await agent.run(params)
            assert "Hemoglobin" in res or "normal" in res.lower()


class TestTrendAgent:
    @pytest.mark.asyncio
    async def test_trend_agent_no_data(self):
        agent = TrendAgent()
        res = await agent.run([])
        assert "No historical trend data" in res

    @pytest.mark.asyncio
    async def test_trend_agent_with_data(self):
        agent = TrendAgent()
        mock_llm = MagicMock()
        mock_llm.completion.return_value = ("Your glucose has been stable around 95 mg/dL.", {})

        with patch.object(agent, "_get_llm", return_value=mock_llm):
            trends = [{
                "parameter": "Glucose",
                "direction": "stable",
                "data_points": [{"date": "2024-01-01", "value": 95, "unit": "mg/dL", "status": "NORMAL"}]
            }]
            res = await agent.run(trends)
            assert "Glucose" in res or "stable" in res.lower()


class TestResponseAgent:
    @pytest.mark.asyncio
    async def test_response_agent_medium_risk_disclaimer(self):
        agent = ResponseAgent()
        mock_llm = MagicMock()
        mock_llm.completion.return_value = ("Your TSH level is slightly elevated.", {})

        with patch.object(agent, "_get_llm", return_value=mock_llm):
            res = await agent.run(
                query="What does high TSH mean?",
                context_parts=["TSH reference range 0.4 - 4.0 mIU/L"],
                citations=[],
                risk_level="medium"
            )
            assert "Disclaimer:" in res["content"]
            assert res["risk_level"] == "medium"
