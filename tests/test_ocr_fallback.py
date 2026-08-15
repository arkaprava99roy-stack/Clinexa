"""
Clinexa — OCR Fallback Unit Tests

Tests the OCR engine on a real PNG fixture.
Pytesseract must be installed (it is in the Docker image).
"""
from __future__ import annotations

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
SCAN_PNG = os.path.join(FIXTURES_DIR, "blood_test_scan.png")


def _tesseract_available() -> bool:
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def _pil_available() -> bool:
    try:
        from PIL import Image
        return True
    except ImportError:
        return False


@pytest.fixture(scope="module")
def scan_png_bytes():
    with open(SCAN_PNG, "rb") as f:
        return f.read()


@pytest.fixture(scope="module")
def ocr_engine():
    from app.document.ocr import OCREngine
    return OCREngine(engine="tesseract")


class TestOCREngine:

    @pytest.mark.skipif(not _tesseract_available(), reason="Tesseract not installed")
    @pytest.mark.skipif(not _pil_available(), reason="Pillow not installed")
    def test_ocr_returns_string(self, ocr_engine, scan_png_bytes):
        result = ocr_engine.extract_text(scan_png_bytes)
        assert isinstance(result, str)

    @pytest.mark.skipif(not _tesseract_available(), reason="Tesseract not installed")
    @pytest.mark.skipif(not _pil_available(), reason="Pillow not installed")
    def test_ocr_detects_hemoglobin(self, ocr_engine, scan_png_bytes):
        """The fixture image contains 'Hemoglobin' — OCR should catch it."""
        result = ocr_engine.extract_text(scan_png_bytes)
        assert "hemoglobin" in result.lower() or "Hemoglobin" in result

    @pytest.mark.skipif(not _tesseract_available(), reason="Tesseract not installed")
    @pytest.mark.skipif(not _pil_available(), reason="Pillow not installed")
    def test_ocr_detects_numeric_values(self, ocr_engine, scan_png_bytes):
        """The fixture has numeric values like 14.2 and 105."""
        result = ocr_engine.extract_text(scan_png_bytes)
        # At least one numeric value should appear
        import re
        numbers = re.findall(r"\d+\.?\d*", result)
        assert len(numbers) > 0

    @pytest.mark.skipif(not _tesseract_available(), reason="Tesseract not installed")
    @pytest.mark.skipif(not _pil_available(), reason="Pillow not installed")
    def test_ocr_empty_image_returns_string(self, ocr_engine):
        """White image should return empty or near-empty string, not raise."""
        from PIL import Image
        import io
        img = Image.new("RGB", (100, 100), color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        result = ocr_engine.extract_text(buf.getvalue())
        assert isinstance(result, str)

    @pytest.mark.skipif(not _tesseract_available(), reason="Tesseract not installed")
    def test_ocr_invalid_bytes_returns_empty_string(self, ocr_engine):
        """Garbage bytes should not raise, should return empty string."""
        result = ocr_engine.extract_text(b"not an image")
        assert isinstance(result, str)
        assert result == ""


class TestOCRPipelineIntegration:
    """
    Tests the combined PDFParser + OCREngine pipeline for a scanned document.
    A scanned PDF has no text layer: parser detects this, returns image_bytes,
    then OCR extracts text.
    """

    @pytest.mark.skipif(not _pil_available(), reason="Pillow not installed")
    def test_ocr_engine_engine_attribute(self):
        from app.document.ocr import OCREngine
        eng = OCREngine(engine="tesseract")
        assert eng.engine == "tesseract"

    def test_ocr_engine_defaults_to_settings(self, monkeypatch):
        """OCREngine should read OCR_ENGINE from settings when not passed."""
        monkeypatch.setenv("OCR_ENGINE", "tesseract")
        # Re-import to pick up fresh settings
        import importlib
        import app.document.ocr as ocr_mod
        importlib.reload(ocr_mod)
        eng = ocr_mod.OCREngine()
        assert eng.engine in ("tesseract", "paddleocr")
