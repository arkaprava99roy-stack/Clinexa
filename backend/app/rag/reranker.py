"""
Clinexa — Reranker (Phase 4)

Merges and reranks results from semantic and keyword searches.

Strategy — Reciprocal Rank Fusion (RRF):
  score(d) = Σ_r  1 / (k + rank_r(d))
  where k=60 (standard RRF constant), r iterates over result lists,
  and rank_r(d) is the 1-based position of document d in list r.

RRF is parameter-free and consistently outperforms simple score averaging
when combining heterogeneous ranking signals.

Optional LLM rerank: when `use_llm=True`, the top-N candidates are sent
to the LLM to pick the most relevant (Phase 9 extension).
"""
from __future__ import annotations

import logging
from typing import Optional

log = logging.getLogger(__name__)

RRF_K = 60  # RRF constant — standard value from the 2009 Cormack et al. paper


class Reranker:
    """
    Merges multiple ranked result lists into a single deduplicated ranking
    using Reciprocal Rank Fusion (RRF), then truncates to top_k.
    """

    def rerank(
        self,
        ranked_lists: list[list[dict]],
        top_k: int = 5,
    ) -> list[dict]:
        """
        Merge N ranked lists into one using RRF.

        Args:
            ranked_lists: Each inner list is already ranked best-first.
                          Each dict must have an 'id' key.
            top_k: Number of results to return.

        Returns:
            Deduplicated list of chunks sorted by RRF score descending,
            truncated to top_k.
            Each result gets an additional 'rrf_score' and 'sources' field.
        """
        if not ranked_lists:
            return []

        # Accumulate RRF scores per chunk id
        scores: dict[str, float] = {}
        # Track the best representative dict for each id
        best: dict[str, dict] = {}
        # Track which sources contributed to each chunk
        source_sets: dict[str, set[str]] = {}

        for result_list in ranked_lists:
            for rank, chunk in enumerate(result_list, start=1):
                chunk_id = chunk["id"]
                rrf_contrib = 1.0 / (RRF_K + rank)
                scores[chunk_id] = scores.get(chunk_id, 0.0) + rrf_contrib

                # Keep the variant with the highest raw similarity score
                if chunk_id not in best or chunk.get("similarity", 0) > best[chunk_id].get("similarity", 0):
                    best[chunk_id] = chunk

                source_sets.setdefault(chunk_id, set()).add(
                    chunk.get("source", "unknown")
                )

        # Sort by accumulated RRF score
        sorted_ids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)

        results = []
        for cid in sorted_ids[:top_k]:
            entry = {**best[cid]}
            entry["rrf_score"] = round(scores[cid], 6)
            entry["sources"] = sorted(source_sets[cid])
            results.append(entry)

        log.info(
            "reranker.done",
            input_lists=len(ranked_lists),
            unique_chunks=len(scores),
            top_k=top_k,
            returned=len(results),
        )
        return results

    async def llm_rerank(
        self,
        query: str,
        chunks: list[dict],
        top_k: int = 5,
    ) -> list[dict]:
        """
        Optional LLM-based reranking: send chunk summaries to the LLM,
        ask it to rank by relevance to the query, return top_k.
        Phase 9 extension — falls back to RRF result if LLM fails.
        """
        if not chunks or len(chunks) <= top_k:
            return chunks[:top_k]

        try:
            from app.services.llm_service import get_llm_service
            import asyncio

            llm = get_llm_service()
            numbered_chunks = "\n\n".join(
                f"[{i+1}] {c['content'][:300]}" for i, c in enumerate(chunks)
            )
            prompt = (
                f"Query: {query}\n\n"
                f"Rank the following {len(chunks)} passages by relevance to the query "
                f"(most relevant first). "
                f"Respond with ONLY a comma-separated list of numbers (e.g. '3,1,5,2,4').\n\n"
                f"{numbered_chunks}"
            )

            response, _ = await asyncio.to_thread(
                llm.completion,
                "You are a precise relevance ranker.",
                prompt,
                max_tokens=50,
                temperature=0.0,
            )

            # Parse the ranking
            import re
            nums = [int(x) - 1 for x in re.findall(r"\d+", response)]
            valid_nums = [n for n in nums if 0 <= n < len(chunks)]
            # dedupe while preserving order
            seen: set[int] = set()
            ordered = []
            for n in valid_nums:
                if n not in seen:
                    seen.add(n)
                    ordered.append(chunks[n])
            # Append any missed chunks
            for i, c in enumerate(chunks):
                if i not in seen:
                    ordered.append(c)

            return ordered[:top_k]

        except Exception as exc:
            log.warning("reranker.llm_rerank.failed", error=str(exc), fallback="rrf_order")
            return chunks[:top_k]
