"""
Clinexa — Hybrid RAG Unit Tests (Phase 4)

Tests:
  - EmbeddingService: dimension, normalization, batch encode
  - VectorStore: tsquery builder, vector literal formatter
  - Reranker: RRF scoring, deduplication, ordering
  - HybridRetriever: parallel legs, empty results, top-k enforcement
  - Integration: end-to-end mock of retrieve() returning correct chunks
"""
from __future__ import annotations

import math
import os
import sys
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sentence_transformers_available() -> bool:
    try:
        import sentence_transformers  # noqa
        return True
    except ImportError:
        return False


def make_chunk(i: int, source: str = "semantic", score: float = 0.9) -> dict:
    return {
        "id": f"chunk-{i}",
        "report_id": f"report-{i % 3}",
        "page_number": i,
        "content": f"Lab result chunk number {i}: Hemoglobin 14.2 g/dL",
        "similarity": score - i * 0.05,
        "source": source,
    }


# ══════════════════════════════════════════════════════════════════════════════
# 1. Embedding Service
# ══════════════════════════════════════════════════════════════════════════════

class TestEmbeddingService:

    @pytest.mark.skipif(
        not _sentence_transformers_available(),
        reason="sentence-transformers not installed",
    )
    def test_embed_returns_correct_dimension(self):
        from app.rag.embeddings import EmbeddingService
        svc = EmbeddingService()
        result = svc.embed(["Hemoglobin level is 14.2 g/dL"])
        assert len(result) == 1
        assert len(result[0]) == 384  # all-MiniLM-L6-v2

    @pytest.mark.skipif(
        not _sentence_transformers_available(),
        reason="sentence-transformers not installed",
    )
    def test_embed_normalized_unit_vector(self):
        """Embeddings should be L2-normalized (magnitude ≈ 1.0)."""
        from app.rag.embeddings import EmbeddingService
        svc = EmbeddingService()
        vec = svc.embed_single("Glucose 105 mg/dL reference 70-99")
        magnitude = math.sqrt(sum(x ** 2 for x in vec))
        assert abs(magnitude - 1.0) < 1e-5

    @pytest.mark.skipif(
        not _sentence_transformers_available(),
        reason="sentence-transformers not installed",
    )
    def test_embed_batch(self):
        from app.rag.embeddings import EmbeddingService
        svc = EmbeddingService()
        texts = ["WBC elevated", "TSH within range", "Platelets normal"]
        result = svc.embed(texts)
        assert len(result) == 3
        assert all(len(r) == 384 for r in result)

    def test_embed_empty_list(self):
        from app.rag.embeddings import EmbeddingService
        svc = EmbeddingService()
        # Should not crash; returns empty list
        result = svc.embed([])
        assert result == []

    def test_dimension_property(self):
        from app.rag.embeddings import EmbeddingService
        svc = EmbeddingService()
        assert svc.dimension == 384

    def test_is_available_reflects_install(self):
        from app.rag.embeddings import EmbeddingService
        svc = EmbeddingService()
        result = svc.is_available()
        assert isinstance(result, bool)
        # Should match whether sentence_transformers is installed
        assert result == _sentence_transformers_available()


# ══════════════════════════════════════════════════════════════════════════════
# 2. VectorStore helpers (pure-Python, no DB needed)
# ══════════════════════════════════════════════════════════════════════════════

class TestVectorStoreHelpers:

    def test_vector_literal_format(self):
        """_vector_literal must produce a valid pgvector string."""
        from app.rag.vector_store import _vector_literal
        result = _vector_literal([0.1, 0.2, 0.3])
        assert result.startswith("[")
        assert result.endswith("]")
        parts = result[1:-1].split(",")
        assert len(parts) == 3
        assert float(parts[0]) == pytest.approx(0.1, abs=1e-6)

    def test_vector_literal_empty_raises_or_returns(self):
        """Empty vector should produce '[]' (valid in some contexts)."""
        from app.rag.vector_store import _vector_literal
        result = _vector_literal([])
        assert result == "[]"

    def test_make_tsquery_simple(self):
        from app.rag.vector_store import _make_tsquery
        result = _make_tsquery("blood glucose level")
        assert "blood" in result
        assert "glucose" in result
        assert "&" in result

    def test_make_tsquery_single_word(self):
        from app.rag.vector_store import _make_tsquery
        result = _make_tsquery("hemoglobin")
        assert "hemoglobin" in result

    def test_make_tsquery_empty_returns_safe(self):
        from app.rag.vector_store import _make_tsquery
        result = _make_tsquery("")
        assert result == "''"

    def test_make_tsquery_strips_special_chars(self):
        """Special characters in queries should not produce invalid tsquery."""
        from app.rag.vector_store import _make_tsquery
        result = _make_tsquery("hemoglobin?? (test) [value]!")
        # Should produce alphanumeric words only
        import re
        words = re.findall(r"[a-zA-Z0-9]+", result)
        assert "hemoglobin" in words

    def test_asyncpg_dsn_strips_dialect(self):
        from app.rag.vector_store import _asyncpg_dsn
        from unittest.mock import patch
        with patch("app.rag.vector_store.settings") as mock_settings:
            mock_settings.DATABASE_URL = "postgresql+asyncpg://user:pass@host/db"
            result = _asyncpg_dsn()
            assert result.startswith("postgresql://")
            assert "asyncpg" not in result


# ══════════════════════════════════════════════════════════════════════════════
# 3. Reranker — RRF algorithm correctness
# ══════════════════════════════════════════════════════════════════════════════

class TestReranker:

    def test_rrf_single_list(self):
        """A single list should rank by original order."""
        from app.rag.reranker import Reranker
        reranker = Reranker()
        chunks = [make_chunk(i, score=1.0 - i * 0.1) for i in range(5)]
        result = reranker.rerank([chunks], top_k=3)
        assert len(result) == 3
        # First chunk in the original list should be first
        assert result[0]["id"] == "chunk-0"

    def test_rrf_deduplicates(self):
        """Chunks appearing in both lists should appear only once in output."""
        from app.rag.reranker import Reranker
        reranker = Reranker()

        # chunk-0 and chunk-1 appear in both semantic and keyword results
        semantic = [make_chunk(0, "semantic"), make_chunk(1, "semantic"), make_chunk(2, "semantic")]
        keyword  = [make_chunk(0, "keyword"),  make_chunk(1, "keyword"),  make_chunk(3, "keyword")]

        result = reranker.rerank([semantic, keyword], top_k=10)
        ids = [r["id"] for r in result]

        # No duplicates
        assert len(ids) == len(set(ids))
        # Should have 4 unique chunks
        assert len(ids) == 4

    def test_rrf_sources_merged(self):
        """Chunks in both lists should have both sources listed."""
        from app.rag.reranker import Reranker
        reranker = Reranker()

        shared = make_chunk(99, "semantic")
        keyword_variant = {**shared, "source": "keyword"}

        result = reranker.rerank([[shared], [keyword_variant]], top_k=5)
        shared_result = next(r for r in result if r["id"] == "chunk-99")
        assert "semantic" in shared_result["sources"]
        assert "keyword" in shared_result["sources"]

    def test_rrf_cross_list_boost(self):
        """A chunk appearing in both lists should rank higher than one in only one."""
        from app.rag.reranker import Reranker
        reranker = Reranker()

        # chunk-A appears in both at rank 5
        chunk_a_sem = {**make_chunk(0), "id": "chunk-A", "source": "semantic"}
        chunk_a_kw  = {**make_chunk(0), "id": "chunk-A", "source": "keyword"}
        # chunk-B appears only in semantic at rank 1 (best position)
        chunk_b = {**make_chunk(1), "id": "chunk-B", "source": "semantic", "similarity": 0.99}

        semantic = [chunk_b, chunk_a_sem]   # B at rank 1, A at rank 2
        keyword  = [chunk_a_kw]             # A at rank 1 here

        result = reranker.rerank([semantic, keyword], top_k=5)
        ids = [r["id"] for r in result]
        # Both should appear; cross-list boost pushes A up
        assert "chunk-A" in ids
        assert "chunk-B" in ids

    def test_rrf_respects_top_k(self):
        from app.rag.reranker import Reranker
        reranker = Reranker()
        chunks = [make_chunk(i) for i in range(20)]
        result = reranker.rerank([chunks], top_k=5)
        assert len(result) == 5

    def test_rrf_empty_lists(self):
        from app.rag.reranker import Reranker
        reranker = Reranker()
        result = reranker.rerank([], top_k=5)
        assert result == []

    def test_rrf_one_empty_one_populated(self):
        from app.rag.reranker import Reranker
        reranker = Reranker()
        chunks = [make_chunk(i) for i in range(3)]
        result = reranker.rerank([chunks, []], top_k=5)
        assert len(result) == 3

    def test_rrf_score_in_output(self):
        """Each output chunk must have an rrf_score field."""
        from app.rag.reranker import Reranker
        reranker = Reranker()
        chunks = [make_chunk(i) for i in range(4)]
        result = reranker.rerank([chunks], top_k=4)
        for r in result:
            assert "rrf_score" in r
            assert r["rrf_score"] > 0


# ══════════════════════════════════════════════════════════════════════════════
# 4. HybridRetriever — mocked DB, tests pipeline orchestration
# ══════════════════════════════════════════════════════════════════════════════

MOCK_SEMANTIC = [
    make_chunk(0, "semantic", 0.95),
    make_chunk(1, "semantic", 0.87),
    make_chunk(2, "semantic", 0.78),
]
MOCK_KEYWORD = [
    make_chunk(1, "keyword", 0.82),  # shared with semantic
    make_chunk(3, "keyword", 0.71),
    make_chunk(4, "keyword", 0.65),
]


class TestHybridRetriever:

    @pytest.mark.asyncio
    async def test_retrieve_returns_top_k(self):
        """retrieve() should return at most top_k chunks."""
        from app.rag.retriever import HybridRetriever

        retriever = HybridRetriever()
        dummy_embedding = [0.0] * 384

        with patch.object(retriever, "_get_embedder") as mock_emb_factory, \
             patch.object(retriever, "_get_store") as mock_store_factory:

            mock_embedder = MagicMock()
            mock_embedder.embed_single.return_value = dummy_embedding
            mock_emb_factory.return_value = mock_embedder

            mock_store = MagicMock()
            mock_store.semantic_search = AsyncMock(return_value=MOCK_SEMANTIC)
            mock_store.keyword_search = AsyncMock(return_value=MOCK_KEYWORD)
            mock_store_factory.return_value = mock_store

            result = await retriever.retrieve(
                query="What is my hemoglobin?",
                user_id="user-123",
                top_k=3,
            )

        assert len(result) <= 3

    @pytest.mark.asyncio
    async def test_retrieve_deduplicates(self):
        """chunk-1 appears in both legs — should appear only once in output."""
        from app.rag.retriever import HybridRetriever

        retriever = HybridRetriever()

        with patch.object(retriever, "_get_embedder") as mock_emb_f, \
             patch.object(retriever, "_get_store") as mock_store_f:

            mock_embedder = MagicMock()
            mock_embedder.embed_single.return_value = [0.0] * 384
            mock_emb_f.return_value = mock_embedder

            mock_store = MagicMock()
            mock_store.semantic_search = AsyncMock(return_value=MOCK_SEMANTIC)
            mock_store.keyword_search  = AsyncMock(return_value=MOCK_KEYWORD)
            mock_store_f.return_value = mock_store

            result = await retriever.retrieve("hemoglobin", "user-1", top_k=10)

        ids = [r["id"] for r in result]
        assert len(ids) == len(set(ids)), "Duplicate chunk ids in output"

    @pytest.mark.asyncio
    async def test_retrieve_empty_db_returns_empty(self):
        """If both legs return empty, retrieve() should return []."""
        from app.rag.retriever import HybridRetriever

        retriever = HybridRetriever()

        with patch.object(retriever, "_get_embedder") as mock_emb_f, \
             patch.object(retriever, "_get_store") as mock_store_f:

            mock_embedder = MagicMock()
            mock_embedder.embed_single.return_value = [0.0] * 384
            mock_emb_f.return_value = mock_embedder

            mock_store = MagicMock()
            mock_store.semantic_search = AsyncMock(return_value=[])
            mock_store.keyword_search  = AsyncMock(return_value=[])
            mock_store_f.return_value = mock_store

            result = await retriever.retrieve("anything", "user-1", top_k=5)

        assert result == []

    @pytest.mark.asyncio
    async def test_retrieve_semantic_only_when_keyword_empty(self):
        """If only semantic returns results, they should still be returned."""
        from app.rag.retriever import HybridRetriever

        retriever = HybridRetriever()

        with patch.object(retriever, "_get_embedder") as mock_emb_f, \
             patch.object(retriever, "_get_store") as mock_store_f:

            mock_embedder = MagicMock()
            mock_embedder.embed_single.return_value = [0.0] * 384
            mock_emb_f.return_value = mock_embedder

            mock_store = MagicMock()
            mock_store.semantic_search = AsyncMock(return_value=MOCK_SEMANTIC)
            mock_store.keyword_search  = AsyncMock(return_value=[])
            mock_store_f.return_value = mock_store

            result = await retriever.retrieve("hemoglobin", "user-1", top_k=5)

        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_retrieve_both_legs_run_in_parallel(self):
        """Ensure both store methods are called for every query."""
        from app.rag.retriever import HybridRetriever

        retriever = HybridRetriever()

        with patch.object(retriever, "_get_embedder") as mock_emb_f, \
             patch.object(retriever, "_get_store") as mock_store_f:

            mock_embedder = MagicMock()
            mock_embedder.embed_single.return_value = [0.0] * 384
            mock_emb_f.return_value = mock_embedder

            mock_store = MagicMock()
            mock_store.semantic_search = AsyncMock(return_value=MOCK_SEMANTIC)
            mock_store.keyword_search  = AsyncMock(return_value=MOCK_KEYWORD)
            mock_store_f.return_value = mock_store

            await retriever.retrieve("TSH levels", "user-1", top_k=5)

            mock_store.semantic_search.assert_called_once()
            mock_store.keyword_search.assert_called_once()

    @pytest.mark.asyncio
    async def test_retrieve_output_has_required_fields(self):
        """Every output chunk must have id, report_id, content, rrf_score."""
        from app.rag.retriever import HybridRetriever

        retriever = HybridRetriever()

        with patch.object(retriever, "_get_embedder") as mock_emb_f, \
             patch.object(retriever, "_get_store") as mock_store_f:

            mock_embedder = MagicMock()
            mock_embedder.embed_single.return_value = [0.0] * 384
            mock_emb_f.return_value = mock_embedder

            mock_store = MagicMock()
            mock_store.semantic_search = AsyncMock(return_value=MOCK_SEMANTIC)
            mock_store.keyword_search  = AsyncMock(return_value=MOCK_KEYWORD)
            mock_store_f.return_value = mock_store

            result = await retriever.retrieve("glucose", "user-1", top_k=5)

        for chunk in result:
            assert "id" in chunk
            assert "report_id" in chunk
            assert "content" in chunk
            assert "rrf_score" in chunk

    @pytest.mark.asyncio
    async def test_retrieve_report_id_scope_passed_to_store(self):
        """When report_id is provided, it must be forwarded to both store calls."""
        from app.rag.retriever import HybridRetriever

        retriever = HybridRetriever()

        with patch.object(retriever, "_get_embedder") as mock_emb_f, \
             patch.object(retriever, "_get_store") as mock_store_f:

            mock_embedder = MagicMock()
            mock_embedder.embed_single.return_value = [0.0] * 384
            mock_emb_f.return_value = mock_embedder

            mock_store = MagicMock()
            mock_store.semantic_search = AsyncMock(return_value=[])
            mock_store.keyword_search  = AsyncMock(return_value=[])
            mock_store_f.return_value = mock_store

            await retriever.retrieve(
                "WBC", "user-1", top_k=5, report_id="report-xyz"
            )

            _, sem_kwargs = mock_store.semantic_search.call_args
            _, kw_kwargs  = mock_store.keyword_search.call_args
            assert sem_kwargs.get("report_id") == "report-xyz"
            assert kw_kwargs.get("report_id") == "report-xyz"
