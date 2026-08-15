"""
Clinexa — Embedding Service (Phase 4)

Uses HuggingFace sentence-transformers to produce 384-dim embeddings.
Model: all-MiniLM-L6-v2 (default) or any model configured via EMBEDDING_MODEL.

The model is loaded lazily on first use and kept as a module-level singleton.
Encoding runs synchronously; call via asyncio.to_thread() in async contexts.
"""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np

from app.core.config import settings

log = logging.getLogger(__name__)

# Embedding dimension for all-MiniLM-L6-v2
DEFAULT_DIMENSION = 384


class EmbeddingService:
    """
    Wraps a SentenceTransformer model.
    Thread-safe for inference; the model is loaded once and reused.
    """

    def __init__(self, model_name: Optional[str] = None) -> None:
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self._model = None  # lazy load

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            log.info("embedding.model_loading", model=self.model_name)
            self._model = SentenceTransformer(self.model_name)
            log.info("embedding.model_ready", model=self.model_name)
        return self._model

    # ── Public API ─────────────────────────────────────────────────────────────

    def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a batch of texts.
        Returns a list of float lists (each is a 384-dim unit vector).
        Texts are normalized so cosine similarity == dot product.
        """
        if not texts:
            return []

        model = self._get_model()
        embeddings: np.ndarray = model.encode(
            texts,
            normalize_embeddings=True,   # unit vectors → cosine sim = dot product
            show_progress_bar=False,
            batch_size=32,
        )
        return embeddings.tolist()

    def embed_single(self, text: str) -> list[float]:
        """Embed a single text. Convenience wrapper around embed()."""
        results = self.embed([text])
        return results[0] if results else []

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        return DEFAULT_DIMENSION

    def is_available(self) -> bool:
        """Check whether sentence-transformers is installed."""
        try:
            import sentence_transformers  # noqa: F401
            return True
        except ImportError:
            return False


# ── Module-level singleton ────────────────────────────────────────────────────

_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
