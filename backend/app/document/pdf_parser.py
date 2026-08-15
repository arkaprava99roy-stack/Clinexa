"""
Clinexa — PDF Parser
Phase 2: Full implementation using PDFPlumber (text layer) + PyMuPDF (rasterizer).

Pipeline decision:
  1. Open with PDFPlumber.
  2. For each page: if extract_text() returns content → has_text_layer=True.
  3. If page has no text layer → rasterize with PyMuPDF at 200 DPI → PNG bytes
     ready for OCR.
"""
from __future__ import annotations

import io
import logging
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)


@dataclass
class ParsedPage:
    page_number: int                  # 1-indexed
    text: str                         # extracted or OCR'd text
    has_text_layer: bool              # True if PDFPlumber found a text layer
    image_bytes: Optional[bytes] = field(default=None, repr=False)
    # image_bytes is populated only when has_text_layer=False (for OCR callers)


class PDFParser:
    """
    Extracts text from every page of a PDF.
    For pages without a text layer, returns raw PNG image bytes so the
    OCREngine can process them.
    """

    MIN_TEXT_LEN = 10  # chars needed to consider a page 'has text'
    RASTER_DPI = 200

    def extract_pages(self, file_bytes: bytes) -> list[ParsedPage]:
        """
        Parse all pages in a PDF.

        Returns a list of ParsedPage objects:
        - has_text_layer=True  → text is the PDFPlumber extraction
        - has_text_layer=False → text is "" and image_bytes contains the rasterized PNG
        """
        import pdfplumber

        results: list[ParsedPage] = []

        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for i, page in enumerate(pdf.pages, start=1):
                    raw_text: str = page.extract_text() or ""
                    has_text = len(raw_text.strip()) >= self.MIN_TEXT_LEN

                    if has_text:
                        results.append(ParsedPage(
                            page_number=i,
                            text=raw_text,
                            has_text_layer=True,
                        ))
                        log.debug("pdf_parser.text_layer", page=i, chars=len(raw_text))
                    else:
                        # Rasterize for OCR
                        img_bytes = self._rasterize_page(file_bytes, page_number=i)
                        results.append(ParsedPage(
                            page_number=i,
                            text="",
                            has_text_layer=False,
                            image_bytes=img_bytes,
                        ))
                        log.debug("pdf_parser.no_text_layer", page=i)

        except Exception as exc:
            log.error("pdf_parser.error", error=str(exc))
            raise ValueError(f"Failed to parse PDF: {exc}") from exc

        return results

    def _rasterize_page(self, file_bytes: bytes, page_number: int) -> bytes:
        """
        Render a single PDF page to a PNG image using PyMuPDF.
        page_number is 1-indexed.
        """
        import fitz  # PyMuPDF

        doc = fitz.open(stream=file_bytes, filetype="pdf")
        try:
            page = doc[page_number - 1]
            scale = self.RASTER_DPI / 72  # 72 is the default PDF DPI
            mat = fitz.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            return pix.tobytes("png")
        finally:
            doc.close()

    @staticmethod
    def is_pdf(file_bytes: bytes) -> bool:
        """Quick check: does the file start with the PDF magic bytes?"""
        return file_bytes[:4] == b"%PDF"

    def count_pages(self, file_bytes: bytes) -> int:
        """Return the number of pages in a PDF without full extraction."""
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            return len(pdf.pages)
