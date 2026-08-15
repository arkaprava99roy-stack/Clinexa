"""
Clinexa — RAG Agent (Phase 4)

Retrieves relevant document chunks via the HybridRetriever and
packages them as context + citations for the Response Agent.

RAG citation format (matches the DB schema and frontend SourceCitation component):
  {
    "report_id": str,
    "report_name": str,   # fetched from report metadata
    "page": int
  }
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

log = logging.getLogger(__name__)

# Maximum characters of context to inject into the LLM prompt
MAX_CONTEXT_CHARS = 8000


class RAGAgent:
    """
    Given a user query and user_id, retrieves the most relevant chunks
    and returns a (context_str, citations) tuple ready for the LLM.
    """

    def __init__(self) -> None:
        self._retriever = None
        self._report_name_cache: dict[str, str] = {}

    def _get_retriever(self):
        if self._retriever is None:
            from app.rag.retriever import HybridRetriever
            self._retriever = HybridRetriever()
        return self._retriever

    # ── Public API ─────────────────────────────────────────────────────────────

    async def run(
        self,
        query: str,
        user_id: str,
        top_k: int = 5,
        report_id: Optional[str] = None,
    ) -> dict:
        """
        Perform hybrid retrieval and format results.

        Returns:
            {
              "context": str,           # concatenated chunk text for LLM prompt
              "citations": list[dict],  # per-chunk citation metadata
              "chunks": list[dict],     # raw chunks (for debug / eval)
            }
        """
        retriever = self._get_retriever()

        chunks = await retriever.retrieve(
            query=query,
            user_id=user_id,
            top_k=top_k,
            report_id=report_id,
        )

        if not chunks:
            log.info("rag_agent.no_chunks", user_id=user_id)
            return {"context": "", "citations": [], "chunks": []}

        # Build context and citations
        context_parts: list[str] = []
        citations: list[dict] = []
        total_chars = 0
        seen_citation_keys: set[str] = set()

        for chunk in chunks:
            text = chunk.get("content", "").strip()
            if not text:
                continue

            # Respect MAX_CONTEXT_CHARS
            if total_chars + len(text) > MAX_CONTEXT_CHARS:
                text = text[: MAX_CONTEXT_CHARS - total_chars]
                context_parts.append(text)
                total_chars = MAX_CONTEXT_CHARS
            else:
                context_parts.append(text)
                total_chars += len(text)

            # Build citation (deduplicated by report_id + page)
            r_id = chunk.get("report_id", "")
            page = chunk.get("page_number", 1)
            citation_key = f"{r_id}:{page}"

            if citation_key not in seen_citation_keys:
                seen_citation_keys.add(citation_key)
                report_name = await self._get_report_name(r_id, user_id)
                citations.append({
                    "report_id": r_id,
                    "report_name": report_name,
                    "page": page,
                })

            if total_chars >= MAX_CONTEXT_CHARS:
                break

        context = "\n\n---\n\n".join(context_parts)

        log.info(
            "rag_agent.done",
            chunks_retrieved=len(chunks),
            context_chars=len(context),
            citations=len(citations),
        )

        return {
            "context": context,
            "citations": citations,
            "chunks": chunks,
        }

    # ── Helpers ────────────────────────────────────────────────────────────────

    async def _get_report_name(self, report_id: str, user_id: str) -> str:
        """Fetch the file_name for a report, using a simple in-memory cache."""
        if not report_id:
            return "Unknown report"

        if report_id in self._report_name_cache:
            return self._report_name_cache[report_id]

        try:
            from supabase import create_client
            from app.core.config import settings

            supabase = create_client(
                settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY
            )
            resp = await asyncio.to_thread(
                lambda: supabase.table("reports")
                    .select("file_name")
                    .eq("id", report_id)
                    .eq("user_id", user_id)
                    .single()
                    .execute()
            )
            name = resp.data.get("file_name", "Report") if resp.data else "Report"
        except Exception:
            name = "Report"

        self._report_name_cache[report_id] = name
        return name
