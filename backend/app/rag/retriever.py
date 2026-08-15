"""
Clinexa — Hybrid Retriever (Phase 4)

Orchestrates the two-leg retrieval pipeline:
  1. Semantic leg: pgvector cosine similarity (top-K=10)
  2. Keyword leg:  Postgres full-text search (top-K=10)
  3. Merge → RRF rerank → top 5 chunks returned to RAG agent

Also logs retrieval scores for the Phase 10 eval harness.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional

log = logging.getLogger(__name__)

# How many results to fetch from each leg before merging
SEMANTIC_K = 10
KEYWORD_K = 10
# Final number of chunks to pass to the RAG agent
TOP_K_FINAL = 5


class HybridRetriever:
    """
    Runs semantic + keyword retrieval in parallel and merges via RRF.
    """

    def __init__(self) -> None:
        self._store = None
        self._embedder = None
        self._reranker = None

    def _get_store(self):
        if self._store is None:
            from app.rag.vector_store import VectorStore
            self._store = VectorStore()
        return self._store

    def _get_embedder(self):
        if self._embedder is None:
            from app.rag.embeddings import get_embedding_service
            self._embedder = get_embedding_service()
        return self._embedder

    def _get_reranker(self):
        if self._reranker is None:
            from app.rag.reranker import Reranker
            self._reranker = Reranker()
        return self._reranker

    # ── Public API ─────────────────────────────────────────────────────────────

    async def retrieve(
        self,
        query: str,
        user_id: str,
        top_k: int = TOP_K_FINAL,
        report_id: Optional[str] = None,
        use_llm_rerank: bool = False,
    ) -> list[dict]:
        """
        Retrieve the most relevant chunks for `query` owned by `user_id`.

        Returns:
            List of chunk dicts with keys:
              id, report_id, page_number, content,
              similarity, source ('semantic'|'keyword'),
              rrf_score, sources
        """
        t0 = time.perf_counter()

        store = self._get_store()
        embedder = self._get_embedder()
        reranker = self._get_reranker()

        # ── Step 1: Embed the query ───────────────────────────────────────────
        query_embedding: list[float] = await asyncio.to_thread(
            embedder.embed_single, query
        )

        # ── Step 2: Run both legs in parallel ─────────────────────────────────
        semantic_task = store.semantic_search(
            embedding=query_embedding,
            user_id=user_id,
            k=SEMANTIC_K,
            report_id=report_id,
        )
        keyword_task = store.keyword_search(
            query=query,
            user_id=user_id,
            k=KEYWORD_K,
            report_id=report_id,
        )
        semantic_results, keyword_results = await asyncio.gather(
            semantic_task, keyword_task
        )

        log.info(
            "retriever.legs_done",
            semantic=len(semantic_results),
            keyword=len(keyword_results),
            query_preview=query[:80],
        )

        # ── Step 3: Merge + rerank ────────────────────────────────────────────
        ranked_lists = [l for l in [semantic_results, keyword_results] if l]

        if not ranked_lists:
            log.warning("retriever.no_results user_id=%s", user_id)
            return []

        if use_llm_rerank:
            # First RRF-merge to get candidates, then LLM rerank
            candidates = reranker.rerank(ranked_lists, top_k=top_k * 2)
            final_chunks = await reranker.llm_rerank(query, candidates, top_k=top_k)
        else:
            final_chunks = reranker.rerank(ranked_lists, top_k=top_k)

        latency_ms = int((time.perf_counter() - t0) * 1000)

        log.info(
            "retriever.done",
            returned=len(final_chunks),
            latency_ms=latency_ms,
            had_semantic=bool(semantic_results),
            had_keyword=bool(keyword_results),
        )

        # Log retrieval scores for the eval harness (Phase 10)
        self._log_retrieval_scores(
            query=query,
            semantic_results=semantic_results,
            keyword_results=keyword_results,
            final_chunks=final_chunks,
            latency_ms=latency_ms,
        )

        return final_chunks

    # ── Eval logging ──────────────────────────────────────────────────────────

    def _log_retrieval_scores(
        self,
        query: str,
        semantic_results: list[dict],
        keyword_results: list[dict],
        final_chunks: list[dict],
        latency_ms: int,
    ) -> None:
        """
        Persist retrieval metrics for the Phase 10 evaluation harness.
        Uses structured logging; Phase 10 will also write to Redis/DB.
        """
        log.info(
            "retrieval_eval",
            query_preview=query[:80],
            semantic_k=len(semantic_results),
            keyword_k=len(keyword_results),
            final_k=len(final_chunks),
            top_semantic_score=semantic_results[0].get("similarity") if semantic_results else None,
            top_keyword_score=keyword_results[0].get("similarity") if keyword_results else None,
            top_rrf_score=final_chunks[0].get("rrf_score") if final_chunks else None,
            latency_ms=latency_ms,
        )
