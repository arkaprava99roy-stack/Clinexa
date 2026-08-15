"""
Clinexa — OCR Engine
Phase 2: Tesseract backend (default) with PaddleOCR fallback path.

Used only when a PDF page has no text layer (scanned document).
"""
from __future__ import annotations

import io
import logging
from typing import Optional

from app.core.config import settings

log = logging.getLogger(__name__)


class OCREngine:
    """
    Extracts text from image bytes using Tesseract (default) or PaddleOCR.
    Engine is controlled by the OCR_ENGINE environment variable.
    """

    def __init__(self, engine: Optional[str] = None) -> None:
        self.engine = engine or settings.OCR_ENGINE  # "tesseract" | "paddleocr"

    def extract_text(self, image_bytes: bytes) -> str:
        """
        Run OCR on raw image bytes (PNG / JPEG / TIFF).
        Returns the extracted text string.
        """
        if self.engine == "paddleocr":
            return self._paddle_ocr(image_bytes)
        return self._tesseract_ocr(image_bytes)

    # ── Tesseract ─────────────────────────────────────────────────────────────

    def _tesseract_ocr(self, image_bytes: bytes) -> str:
        import pytesseract
        from PIL import Image

        try:
            image = Image.open(io.BytesIO(image_bytes))
            # Convert to RGB if needed (Tesseract chokes on RGBA / palette modes)
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")

            text: str = pytesseract.image_to_string(
                image,
                lang="eng",
                config="--oem 3 --psm 6",  # LSTM engine, assume uniform block
            )
            log.debug("ocr.tesseract.done", chars=len(text))
            return text.strip()

        except Exception as exc:
            log.error("ocr.tesseract.error", error=str(exc))
            return ""

    # ── PaddleOCR (optional) ─────────────────────────────────────────────────

    def _paddle_ocr(self, image_bytes: bytes) -> str:
        try:
            import numpy as np
            from PIL import Image

            # PaddleOCR is imported lazily so Tesseract-only installs don't fail.
            from paddleocr import PaddleOCR  # type: ignore

            ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            img_array = np.array(image)
            result = ocr.ocr(img_array, cls=True)

            lines = []
            for block in (result or []):
                for line in (block or []):
                    if line and len(line) >= 2:
                        text_conf = line[1]
                        if text_conf and len(text_conf) >= 1:
                            lines.append(str(text_conf[0]))

            text = "\n".join(lines)
            log.debug("ocr.paddle.done", chars=len(text))
            return text.strip()

        except ImportError:
            log.warning("ocr.paddle.not_installed", fallback="tesseract")
            return self._tesseract_ocr(image_bytes)
        except Exception as exc:
            log.error("ocr.paddle.error", error=str(exc))
            return ""
