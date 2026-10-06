"""
Text embeddings via Hugging Face Inference Providers (feature-extraction).

``HFEmbeddingModel`` exposes the subset of the ``SentenceTransformer`` API the
codebase uses (``encode`` / ``get_sentence_embedding_dimension``), so call
sites did not need to change shape when local torch models were removed.

The default model (``HF_EMBEDDING_MODEL`` = ``intfloat/multilingual-e5-large``)
is the same model that produced the vectors already stored in Qdrant, so
existing collections stay valid. E5 models expect ``query: `` / ``passage: ``
prefixes; callers keep adding them exactly as before.
"""
from __future__ import annotations

import asyncio
import logging
from typing import List, Optional, Sequence, Union

import numpy as np

from app.ai.hf_client import HFErrorKind, HFInferenceError, classify_exception, task_client

logger = logging.getLogger(__name__)

TextInput = Union[str, Sequence[str]]

# hf-inference accepts batched inputs; keep requests comfortably small.
DEFAULT_BATCH_SIZE = 32


class HFEmbeddingModel:
    """SentenceTransformer-compatible embedding client backed by HF."""

    def __init__(self, model: Optional[str] = None, dimension: Optional[int] = None):
        from app.core.config import settings

        self.model_name = model or settings.hf_embedding_model
        self._dimension = dimension or settings.embedding_dimension

    def get_sentence_embedding_dimension(self) -> int:
        return self._dimension

    def encode(
        self,
        sentences: TextInput,
        batch_size: Optional[int] = None,
        convert_to_numpy: bool = True,
        normalize_embeddings: bool = True,
        show_progress_bar: bool = False,  # accepted for API compatibility
        **_ignored,
    ) -> np.ndarray:
        """
        Embed one string (→ 1-D array) or a list of strings (→ 2-D array).

        Raises ``HFInferenceError`` on any upstream failure.
        """
        single = isinstance(sentences, str)
        texts: List[str] = [sentences] if single else list(sentences)
        if not texts:
            return np.zeros((0, self._dimension), dtype=np.float32)

        size = batch_size or DEFAULT_BATCH_SIZE
        client = task_client("embeddings")
        vectors = []
        for start in range(0, len(texts), size):
            batch = texts[start:start + size]
            try:
                out = client.feature_extraction(batch, model=self.model_name, truncate=True)
            except Exception as exc:  # noqa: BLE001
                err = classify_exception(exc, "embeddings")
                logger.warning("Embedding request failed: %s", err)
                raise err from None
            arr = np.asarray(out, dtype=np.float32)
            # Some backends return per-token vectors; mean-pool to one vector per text.
            if arr.ndim == 3:
                arr = arr.mean(axis=1)
            if arr.ndim == 1:
                arr = arr.reshape(1, -1)
            if arr.ndim != 2 or arr.shape[0] != len(batch):
                raise HFInferenceError(HFErrorKind.MALFORMED, "embeddings")
            vectors.append(arr)

        result = np.vstack(vectors)
        if result.shape[1] != self._dimension:
            logger.error(
                "Embedding dimension %d does not match configured %d for %s",
                result.shape[1], self._dimension, self.model_name,
            )
            raise HFInferenceError(HFErrorKind.MALFORMED, "embeddings")
        if normalize_embeddings:
            norms = np.linalg.norm(result, axis=1, keepdims=True)
            result = result / np.where(norms == 0, 1.0, norms)
        return result[0] if single else result

    async def aencode(self, sentences: TextInput, **kwargs) -> np.ndarray:
        """Async wrapper (the HTTP call runs in a worker thread)."""
        return await asyncio.to_thread(self.encode, sentences, **kwargs)


_default_model: Optional[HFEmbeddingModel] = None


def get_embedding_model() -> HFEmbeddingModel:
    """Process-wide embedding client for ``HF_EMBEDDING_MODEL``."""
    global _default_model
    if _default_model is None:
        _default_model = HFEmbeddingModel()
    return _default_model
