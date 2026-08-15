"""
Clinexa — Vector Store (Phase 4)

Handles:
  - Upserting chunk embeddings into the `document_chunks` pgvector column.
  - Semantic (cosine) similarity search via pgvector `<=>` operator.
  - Full-text keyword search via PostgreSQL tsvector / tsquery.

Uses asyncpg directly for raw SQL since PostgREST doesn't natively expose
pgvector operators or ts_rank scoring.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Optional

from app.core.config import settings

log = logging.getLogger(__name__)


def _asyncpg_dsn() -> str:
    """
    Convert the SQLAlchemy-style DATABASE_URL (postgresql+asyncpg://...)
    to the plain asyncpg DSN (postgresql://...).
    """
    url = settings.DATABASE_URL
    return url.replace("postgresql+asyncpg://", "postgresql://", 1)


def _vector_literal(embedding: list[float]) -> str:
    """Format a float list as a pgvector literal string, e.g. '[0.1,0.2,...]'."""
    return "[" + ",".join(f"{x:.8f}" for x in embedding) + "]"


def _make_tsquery(query: str) -> str:
    """
    Convert a free-text query into a safe PostgreSQL tsquery string.
    Uses AND-joined lexemes; strips non-alphanumeric characters.
    Example: "blood glucose level" → "blood & glucose & level"
    """
    words = re.findall(r"[a-zA-Z0-9]+", query)
    if not words:
        return "''"
    # Use prefix-match for each word (:*)
    return " & ".join(f"{w}:*" for w in words)


class VectorStore:
    """
    Low-level data-access layer for vector and full-text operations on
    document_chunks.
    """

    # ── Embedding upsert ───────────────────────────────────────────────────────

    async def update_embeddings(
        self,
        chunks: list[dict],  # each dict must have 'id' and 'embedding'
    ) -> None:
        """
        Update the `embedding` column for each chunk by its `id`.
        Runs in a single transaction for efficiency.
        """
        if not chunks:
            return

        import asyncpg

        conn = await asyncpg.connect(_asyncpg_dsn())
        try:
            async with conn.transaction():
                for chunk in chunks:
                    vec_str = _vector_literal(chunk["embedding"])
                    await conn.execute(
                        """
                        UPDATE document_chunks
                        SET embedding = $1::vector
                        WHERE id = $2
                        """,
                        vec_str,
                        chunk["id"],
                    )
            log.info("vector_store.embeddings_updated", count=len(chunks))
        finally:
            await conn.close()

    # ── Semantic search ────────────────────────────────────────────────────────

    async def semantic_search(
        self,
        embedding: list[float],
        user_id: str,
        k: int = 10,
        report_id: Optional[str] = None,
    ) -> list[dict]:
        """
        Return the top-k chunks by cosine similarity to the query embedding.
        Filters by user_id (RLS guarantee at app layer).
        Optionally scoped to a single report_id.
        """
        import asyncpg

        vec_str = _vector_literal(embedding)

        where_clauses = ["user_id = $2", "embedding IS NOT NULL"]
        params: list = [vec_str, user_id]

        if report_id:
            params.append(report_id)
            where_clauses.append(f"report_id = ${len(params)}")

        params.append(k)
        limit_param = f"${len(params)}"
        where_sql = " AND ".join(where_clauses)

        sql = f"""
            SELECT
                id,
                report_id,
                page_number,
                content,
                (1 - (embedding <=> $1::vector)) AS similarity,
                'semantic' AS source
            FROM document_chunks
            WHERE {where_sql}
            ORDER BY embedding <=> $1::vector
            LIMIT {limit_param}
        """

        conn = await asyncpg.connect(_asyncpg_dsn())
        try:
            rows = await conn.fetch(sql, *params)
            results = [dict(r) for r in rows]
            log.debug(
                "vector_store.semantic_search",
                k=k,
                returned=len(results),
            )
            return results
        finally:
            await conn.close()

    # ── Full-text search ───────────────────────────────────────────────────────

    async def keyword_search(
        self,
        query: str,
        user_id: str,
        k: int = 10,
        report_id: Optional[str] = None,
    ) -> list[dict]:
        """
        Return top-k chunks by PostgreSQL full-text rank (ts_rank).
        Falls back gracefully if the query produces no tsquery terms.
        """
        import asyncpg

        tsquery_str = _make_tsquery(query)
        if not tsquery_str or tsquery_str == "''":
            return []

        where_clauses = ["user_id = $2", f"content_tsvector @@ to_tsquery('english', $1)"]
        params: list = [tsquery_str, user_id]

        if report_id:
            params.append(report_id)
            where_clauses.append(f"report_id = ${len(params)}")

        params.append(k)
        limit_param = f"${len(params)}"
        where_sql = " AND ".join(where_clauses)

        sql = f"""
            SELECT
                id,
                report_id,
                page_number,
                content,
                ts_rank(content_tsvector, to_tsquery('english', $1)) AS similarity,
                'keyword' AS source
            FROM document_chunks
            WHERE {where_sql}
            ORDER BY similarity DESC
            LIMIT {limit_param}
        """

        conn = await asyncpg.connect(_asyncpg_dsn())
        try:
            rows = await conn.fetch(sql, *params)
            results = [dict(r) for r in rows]
            log.debug(
                "vector_store.keyword_search",
                k=k,
                returned=len(results),
            )
            return results
        except Exception as exc:
            # tsquery syntax errors (e.g. stop-words only) → empty result
            log.warning("vector_store.keyword_search.error", error=str(exc))
            return []
        finally:
            await conn.close()
