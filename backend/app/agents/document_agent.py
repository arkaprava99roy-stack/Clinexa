"""
Clinexa — Document Agent (Phase 2 + 4)

Full pipeline:
  file_bytes
    → PDF parse (text layer or rasterize)
    → OCR fallback for image pages
    → store in report_pages
    → LLM document classification
    → LLM parameter extraction (per page)
    → rule-engine status classification
    → store in health_parameters
    → chunk page text (~500 tokens, 50-token overlap)
    → embed chunks (sentence-transformers Phase 4)
    → store embeddings in document_chunks via pgvector
    → update report status → 'ready'
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

log = logging.getLogger(__name__)


class DocumentAgent:
    """
    Orchestrates the full document ingestion pipeline for a single report.
    Called as a FastAPI BackgroundTask after file upload is accepted.
    """

    def __init__(self) -> None:
        from app.document.pdf_parser import PDFParser
        from app.document.ocr import OCREngine
        from app.document.chunker import chunk_text
        from app.document.extractor import ParameterExtractor
        from app.services.llm_service import get_llm_service

        self.parser = PDFParser()
        self.ocr = OCREngine()
        self.chunk_text = chunk_text
        self.extractor = ParameterExtractor()
        self.llm = get_llm_service()

    async def run(
        self,
        report_id: str,
        user_id: str,
        file_bytes: bytes,
        file_name: str,
    ) -> None:
        """
        Entry point — called as a background task.
        Updates `reports.status` to 'ready' on success or 'failed' on error.
        """
        log.info(
            "document_agent.start",
            report_id=report_id,
            user_id=user_id,
            file_name=file_name,
            size_bytes=len(file_bytes),
        )
        supabase = self._get_supabase()

        try:
            # ── 1. Parse PDF pages ─────────────────────────────────────────────
            if not self.parser.is_pdf(file_bytes):
                # Treat single-image uploads as a 1-page "PDF"
                pages = await self._handle_image_upload(file_bytes)
            else:
                pages = await asyncio.to_thread(
                    self.parser.extract_pages, file_bytes
                )

            log.info(
                "document_agent.parsed",
                report_id=report_id,
                num_pages=len(pages),
            )

            # ── 2. OCR fallback for pages without a text layer ────────────────
            page_texts: list[tuple[int, str]] = []  # (page_number, text)

            for page in pages:
                if page.has_text_layer:
                    page_texts.append((page.page_number, page.text))
                else:
                    log.info(
                        "document_agent.ocr_page",
                        report_id=report_id,
                        page=page.page_number,
                    )
                    ocr_text = await asyncio.to_thread(
                        self.ocr.extract_text, page.image_bytes or b""
                    )
                    page_texts.append((page.page_number, ocr_text))

            # ── 3. Store report_pages ─────────────────────────────────────────
            page_rows = [
                {
                    "report_id": report_id,
                    "page_number": pnum,
                    "raw_text": text,
                    "used_ocr": not pages[i].has_text_layer,
                }
                for i, (pnum, text) in enumerate(page_texts)
            ]
            if page_rows:
                supabase.table("report_pages").insert(page_rows).execute()

            # ── 4. Classify document type ──────────────────────────────────────
            full_text = "\n\n".join(t for _, t in page_texts)
            report_type = await asyncio.to_thread(
                self.llm.classify_document, full_text
            )
            log.info(
                "document_agent.classified",
                report_id=report_id,
                report_type=report_type,
            )

            # Update report_type while still processing
            supabase.table("reports").update(
                {"report_type": report_type}
            ).eq("id", report_id).execute()

            # ── 5. Extract parameters per page ────────────────────────────────
            all_parameters: list[dict] = []
            for page_number, text in page_texts:
                params = await self.extractor.extract(text, page_number)
                for p in params:
                    p["report_id"] = report_id
                    p["user_id"] = user_id
                all_parameters.extend(params)

            # ── 6. Store health_parameters ────────────────────────────────────
            if all_parameters:
                param_rows = [
                    {
                        "id": str(uuid.uuid4()),
                        "report_id": p["report_id"],
                        "user_id": p["user_id"],
                        "parameter": p["parameter"],
                        "value": p.get("value"),
                        "unit": p.get("unit"),
                        "ref_min": p.get("ref_min"),
                        "ref_max": p.get("ref_max"),
                        "status": p.get("status", "UNKNOWN"),
                        "page_number": p.get("page"),
                    }
                    for p in all_parameters
                    if p.get("parameter")
                ]
                supabase.table("health_parameters").insert(param_rows).execute()
                log.info(
                    "document_agent.params_stored",
                    report_id=report_id,
                    count=len(param_rows),
                )

            # ── 7. Chunk text, embed, and store document_chunks ──────────────
            chunk_rows = []
            for page_number, text in page_texts:
                chunks = self.chunk_text(text, chunk_tokens=500, overlap_tokens=50)
                for content in chunks:
                    chunk_rows.append({
                        "id": str(uuid.uuid4()),
                        "report_id": report_id,
                        "user_id": user_id,
                        "page_number": page_number,
                        "content": content,
                    })

            if chunk_rows:
                # 7a. Insert chunk rows without embeddings first
                supabase.table("document_chunks").insert(chunk_rows).execute()
                log.info(
                    "document_agent.chunks_inserted",
                    report_id=report_id,
                    count=len(chunk_rows),
                )

                # 7b. Embed in batch and update via VectorStore
                try:
                    from app.rag.embeddings import get_embedding_service
                    from app.rag.vector_store import VectorStore

                    embedder = get_embedding_service()
                    store = VectorStore()
                    texts = [c["content"] for c in chunk_rows]
                    embeddings: list[list[float]] = await asyncio.to_thread(
                        embedder.embed, texts
                    )
                    chunks_with_embeddings = [
                        {"id": c["id"], "embedding": emb}
                        for c, emb in zip(chunk_rows, embeddings)
                    ]
                    await store.update_embeddings(chunks_with_embeddings)
                    log.info(
                        "document_agent.embeddings_stored",
                        report_id=report_id,
                        count=len(chunk_rows),
                    )
                except Exception as emb_exc:
                    # Embeddings are non-critical for Phase 2; pipeline continues.
                    log.warning(
                        "document_agent.embedding_failed",
                        report_id=report_id,
                        error=str(emb_exc),
                    )

            # ── 8. Update health_trends (Phase 6 expands this) ───────────────
            await self._update_trends(
                supabase, user_id, all_parameters, report_id
            )

            # ── 9. Mark report ready ──────────────────────────────────────────
            supabase.table("reports").update({
                "status": "ready",
                "processed_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", report_id).execute()

            log.info("document_agent.done", report_id=report_id)

        except Exception as exc:
            log.error(
                "document_agent.error",
                report_id=report_id,
                error=str(exc),
                exc_info=True,
            )
            try:
                supabase.table("reports").update({
                    "status": "failed",
                }).eq("id", report_id).execute()
            except Exception:
                pass

    # ── Private helpers ────────────────────────────────────────────────────────

    def _get_supabase(self):
        from supabase import create_client
        from app.core.config import settings
        return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

    async def _handle_image_upload(self, file_bytes: bytes) -> list:
        """Treat a raw image (non-PDF) as a single page needing OCR."""
        from app.document.pdf_parser import ParsedPage
        return [ParsedPage(
            page_number=1,
            text="",
            has_text_layer=False,
            image_bytes=file_bytes,
        )]

    async def _update_trends(
        self,
        supabase,
        user_id: str,
        parameters: list[dict],
        report_id: str,
    ) -> None:
        """
        Update health_trends for each extracted parameter.
        Adds a data point with the current date and upserts the row.
        Phase 6 will add direction calculation.
        """
        if not parameters:
            return

        today = datetime.now(timezone.utc).date().isoformat()

        # Fetch the report upload date for the data point timestamp
        try:
            rep = supabase.table("reports")\
                .select("uploaded_at")\
                .eq("id", report_id)\
                .single()\
                .execute()
            date_str = rep.data.get("uploaded_at", today)[:10] if rep.data else today
        except Exception:
            date_str = today

        # Group by parameter name — use the first occurrence on this report
        seen: set[str] = set()
        for p in parameters:
            name = p.get("parameter", "").strip()
            if not name or p.get("value") is None or name in seen:
                continue
            seen.add(name)

            new_point = {
                "date": date_str,
                "value": float(p["value"]),
                "unit": p.get("unit"),
                "status": p.get("status", "UNKNOWN"),
            }

            # Fetch existing trend
            existing = supabase.table("health_trends")\
                .select("id, data_points")\
                .eq("user_id", user_id)\
                .eq("parameter", name)\
                .execute()

            if existing.data:
                row = existing.data[0]
                data_points = list(row.get("data_points") or [])
                # Avoid exact duplicate dates from re-processing
                data_points = [dp for dp in data_points if dp.get("date") != date_str]
                data_points.append(new_point)
                # Sort by date ascending
                data_points.sort(key=lambda x: x.get("date", ""))

                direction = _compute_direction(data_points)

                supabase.table("health_trends").update({
                    "data_points": data_points,
                    "direction": direction,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }).eq("id", row["id"]).execute()
            else:
                supabase.table("health_trends").insert({
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "parameter": name,
                    "data_points": [new_point],
                    "direction": "stable",
                }).execute()


def _compute_direction(data_points: list[dict]) -> str:
    """
    Compute trend direction from chronologically sorted data points.
    Uses linear regression slope sign.
    Requires ≥ 2 points.
    """
    if len(data_points) < 2:
        return "stable"

    values = [float(dp["value"]) for dp in data_points if dp.get("value") is not None]
    if len(values) < 2:
        return "stable"

    n = len(values)
    mean_x = (n - 1) / 2
    mean_y = sum(values) / n
    numerator = sum((i - mean_x) * (v - mean_y) for i, v in enumerate(values))
    denominator = sum((i - mean_x) ** 2 for i in range(n))

    if denominator == 0:
        return "stable"

    slope = numerator / denominator
    threshold = 0.01 * mean_y if mean_y else 0.01

    if slope > threshold:
        return "increasing"
    elif slope < -threshold:
        return "decreasing"
    return "stable"
