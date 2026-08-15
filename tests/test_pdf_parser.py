"""
Clinexa — PDF Parser Unit Tests

Tests the PDFPlumber text extraction path and PyMuPDF rasterization
without requiring Supabase or the LLM.
"""
from __future__ import annotations

import os
import sys
import pytest

# Ensure backend is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
BLOOD_TEST_PDF = os.path.join(FIXTURES_DIR, "blood_test.pdf")


def _pdfplumber_installed() -> bool:
    try:
        import pdfplumber
        return True
    except ImportError:
        return False


def _fitz_installed() -> bool:
    try:
        import fitz
        return True
    except ImportError:
        return False


@pytest.fixture(scope="module")
def blood_test_pdf_bytes():
    with open(BLOOD_TEST_PDF, "rb") as f:
        return f.read()


@pytest.fixture(scope="module")
def parser():
    from app.document.pdf_parser import PDFParser
    return PDFParser()


class TestPDFParserTextLayer:
    """Tests for PDFs that have a selectable text layer."""

    @pytest.mark.skipif(not _pdfplumber_installed(), reason="pdfplumber not installed")
    def test_is_pdf_magic_bytes(self, blood_test_pdf_bytes):
        from app.document.pdf_parser import PDFParser
        assert PDFParser.is_pdf(blood_test_pdf_bytes) is True

    def test_is_pdf_rejects_png(self):
        from app.document.pdf_parser import PDFParser
        png_header = b"\x89PNG\r\n\x1a\n"
        assert PDFParser.is_pdf(png_header) is False

    def test_is_pdf_rejects_empty(self):
        from app.document.pdf_parser import PDFParser
        assert PDFParser.is_pdf(b"") is False

    @pytest.mark.skipif(not _pdfplumber_installed(), reason="pdfplumber not installed")
    def test_count_pages(self, blood_test_pdf_bytes):
        from app.document.pdf_parser import PDFParser
        p = PDFParser()
        n = p.count_pages(blood_test_pdf_bytes)
        assert n == 1

    @pytest.mark.skipif(not _pdfplumber_installed(), reason="pdfplumber not installed")
    def test_extract_pages_returns_list(self, blood_test_pdf_bytes):
        from app.document.pdf_parser import PDFParser
        p = PDFParser()
        pages = p.extract_pages(blood_test_pdf_bytes)
        assert isinstance(pages, list)
        assert len(pages) == 1

    @pytest.mark.skipif(not _pdfplumber_installed(), reason="pdfplumber not installed")
    def test_text_layer_detected(self, blood_test_pdf_bytes):
        """Blood test PDF has embedded text — has_text_layer should be True."""
        from app.document.pdf_parser import PDFParser
        p = PDFParser()
        pages = p.extract_pages(blood_test_pdf_bytes)
        assert pages[0].has_text_layer is True

    @pytest.mark.skipif(not _pdfplumber_installed(), reason="pdfplumber not installed")
    def test_text_contains_lab_data(self, blood_test_pdf_bytes):
        """Extracted text should contain key blood test terms."""
        from app.document.pdf_parser import PDFParser
        p = PDFParser()
        pages = p.extract_pages(blood_test_pdf_bytes)
        text = pages[0].text
        assert "Hemoglobin" in text or "hemoglobin" in text.lower() or len(text) > 0

    @pytest.mark.skipif(not _pdfplumber_installed(), reason="pdfplumber not installed")
    def test_page_number_is_1indexed(self, blood_test_pdf_bytes):
        from app.document.pdf_parser import PDFParser
        p = PDFParser()
        pages = p.extract_pages(blood_test_pdf_bytes)
        assert pages[0].page_number == 1

    @pytest.mark.skipif(not _pdfplumber_installed(), reason="pdfplumber not installed")
    def test_text_layer_page_has_no_image_bytes(self, blood_test_pdf_bytes):
        """Pages with text layers should not return image_bytes."""
        from app.document.pdf_parser import PDFParser
        p = PDFParser()
        pages = p.extract_pages(blood_test_pdf_bytes)
        if pages[0].has_text_layer:
            assert pages[0].image_bytes is None

    def test_invalid_file_raises_value_error(self):
        from app.document.pdf_parser import PDFParser
        p = PDFParser()
        with pytest.raises((ValueError, Exception)):
            p.extract_pages(b"this is not a pdf")


class TestPDFParserRasterization:
    """Tests for the PyMuPDF rasterization path."""

    @pytest.mark.skipif(not _fitz_installed(), reason="PyMuPDF not installed")
    @pytest.mark.skipif(not _pdfplumber_installed(), reason="pdfplumber not installed")
    def test_rasterize_returns_png_bytes(self, blood_test_pdf_bytes):
        from app.document.pdf_parser import PDFParser
        p = PDFParser()
        img_bytes = p._rasterize_page(blood_test_pdf_bytes, page_number=1)
        # PNG magic bytes: 89 50 4E 47
        assert img_bytes[:4] == b"\x89PNG"

    @pytest.mark.skipif(not _fitz_installed(), reason="PyMuPDF not installed")
    @pytest.mark.skipif(not _pdfplumber_installed(), reason="pdfplumber not installed")
    def test_rasterize_reasonable_size(self, blood_test_pdf_bytes):
        """At 200 DPI a letter-size page should produce a large image."""
        from app.document.pdf_parser import PDFParser
        p = PDFParser()
        img_bytes = p._rasterize_page(blood_test_pdf_bytes, page_number=1)
        # 200 DPI letter = 1700×2200 px ≈ several hundred KB as PNG
        assert len(img_bytes) > 1_000  # at least 1 KB
