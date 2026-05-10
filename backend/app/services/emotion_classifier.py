"""
NLI-based emotion classifier — Phase T4.

Uses facebook/bart-large-mnli for zero-shot Natural Language Inference (NLI)
classification in English and Latin-script text.  For Arabic-dominant input,
the caller (classify_emotion in spiritual_guidance_service.py) routes to the
keyword classifier, which already carries a full Arabic keyword bank.

Architecture
------------
* One model, loaded lazily on first call, cached as a module-level singleton.
* GPU used when available; falls back to CPU transparently.
* `USE_TF=0` is set before transformers is imported to prevent tensorflow from
  being loaded (it is not needed, and its presence in this environment causes
  a NumPy 2.x compatibility error in ml_dtypes).
* Thread-safe: double-checked locking pattern protects concurrent warm-ups.
* Graceful degradation: if the model fails to load for any reason, `classify()`
  returns ('', 0.0) and the caller falls back to keyword matching.

Hypothesis template
-------------------
For each emotion label, the model scores:
    "This person is feeling <emotion>."
against the user's message using MNLI entailment probability (label index 2).
All 11 emotion hypotheses are encoded in a single batched forward pass.

Confidence threshold (default 0.4)
-----------------------------------
If the highest entailment score is below the threshold, the classifier returns
('', 0.0) to signal low confidence.  The caller should fall back to keywords.
This threshold was chosen empirically: clean English emotion text reliably
scores > 0.90; ambiguous or off-topic text scores below 0.4.

Language detection
------------------
`is_arabic_dominant(text)` returns True when > 30 % of characters fall in the
Arabic Unicode range (U+0600–U+06FF and extended blocks).  Callers should route
Arabic-dominant text directly to the keyword classifier, which has a full Arabic
keyword bank with good coverage.
"""
from __future__ import annotations

import logging
import os
import re
import threading
from typing import List, Optional, Tuple

import torch

logger = logging.getLogger(__name__)

# Prevent transformers from loading tensorflow (stale env install causes NumPy 2.x crash).
if "USE_TF" not in os.environ:
    os.environ["USE_TF"] = "0"

from app.models.therapy import EmotionCategory

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_MODEL_NAME = "facebook/bart-large-mnli"
DEFAULT_CONFIDENCE_THRESHOLD = 0.4

# Ordered list of emotion label strings used in NLI hypotheses.
# Using .value ensures the hypothesis reads "This person is feeling anxiety."
# "general" is omitted — it is the caller's fallback for low-confidence results.
EMOTION_LABELS: List[str] = [
    EmotionCategory.ANXIETY.value,
    EmotionCategory.SADNESS.value,
    EmotionCategory.GRIEF.value,
    EmotionCategory.FEAR.value,
    EmotionCategory.LONELINESS.value,
    EmotionCategory.HOPELESSNESS.value,
    EmotionCategory.ANGER.value,
    EmotionCategory.STRESS.value,
    EmotionCategory.GUILT.value,
    EmotionCategory.DOUBT.value,
    EmotionCategory.GRATITUDE.value,
]

# Arabic Unicode blocks: Basic Arabic, Supplement, Extended-A/B
_ARABIC_PATTERN = re.compile(
    r"[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]"
)


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def is_arabic_dominant(text: str, threshold: float = 0.30) -> bool:
    """Return True when Arabic-script characters exceed `threshold` fraction of text."""
    if not text:
        return False
    return len(_ARABIC_PATTERN.findall(text)) / len(text) > threshold


# ---------------------------------------------------------------------------
# NLI classifier
# ---------------------------------------------------------------------------

class NLIEmotionClassifier:
    """
    Zero-shot NLI emotion classifier backed by facebook/bart-large-mnli.

    Usage::

        clf = NLIEmotionClassifier()
        clf.warmup()          # optional; call during app startup
        emotion, confidence = clf.classify("I feel anxious about tomorrow")
        # → ('anxiety', 0.996)
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    ) -> None:
        self._model_name = model_name
        self._threshold = confidence_threshold
        self._tokenizer = None
        self._model = None
        self._device: Optional[torch.device] = None
        self._lock = threading.Lock()
        self._attempted = False
        self._ready = False

    # ------------------------------------------------------------------
    # Internal loading
    # ------------------------------------------------------------------

    def _load(self) -> bool:
        """Load tokenizer and model.  Called at most once (double-checked lock)."""
        if self._attempted:
            return self._ready
        with self._lock:
            if self._attempted:
                return self._ready
            try:
                from transformers import (  # noqa: PLC0415
                    AutoModelForSequenceClassification,
                    AutoTokenizer,
                )

                self._tokenizer = AutoTokenizer.from_pretrained(self._model_name)
                self._model = AutoModelForSequenceClassification.from_pretrained(
                    self._model_name
                )
                self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                self._model.eval().to(self._device)
                self._ready = True
                logger.info(
                    "NLI emotion classifier loaded: %s on %s",
                    self._model_name,
                    self._device,
                )
            except Exception as exc:
                logger.warning(
                    "NLI emotion classifier failed to load (%s): %s. "
                    "Keyword fallback will be used.",
                    self._model_name,
                    exc,
                )
                self._ready = False
            finally:
                self._attempted = True
        return self._ready

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def warmup(self) -> bool:
        """
        Pre-load the model.  Call during application startup so that the first
        HTTP request does not incur the model-loading latency (~5–30 s).

        Returns True if the model loaded successfully.
        """
        return self._load()

    @property
    def is_ready(self) -> bool:
        """True after a successful model load."""
        return self._ready

    def classify(self, text: str) -> Tuple[str, float]:
        """
        Classify `text` into an emotion category using zero-shot NLI.

        All 11 emotion hypotheses are encoded and scored in a single batched
        forward pass.

        Returns
        -------
        (emotion_key, confidence)
            ``emotion_key`` is an EmotionCategory string; ``confidence`` is the
            MNLI entailment probability [0.0, 1.0].

        Returns ('', 0.0) when:
        - the model is not loaded, or
        - max confidence < ``confidence_threshold`` (caller should fall back
          to keyword classification).
        """
        if not self._load():
            return ("", 0.0)

        try:
            hypotheses = [f"This person is feeling {lbl}." for lbl in EMOTION_LABELS]
            enc = self._tokenizer(
                [text] * len(EMOTION_LABELS),
                hypotheses,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=256,
            ).to(self._device)

            with torch.no_grad():
                logits = self._model(**enc).logits

            # BART MNLI label_ids: 0=contradiction, 1=neutral, 2=entailment
            entail_probs = torch.softmax(logits, dim=-1)[:, 2]
            best_idx = int(entail_probs.argmax())
            confidence = float(entail_probs[best_idx])

            if confidence < self._threshold:
                logger.debug(
                    "Low NLI confidence %.3f for text %.60r — keyword fallback",
                    confidence,
                    text,
                )
                return ("", confidence)

            return (EMOTION_LABELS[best_idx], confidence)

        except Exception as exc:
            logger.warning("NLI emotion inference error: %s", exc)
            return ("", 0.0)

    def classify_batch(self, texts: List[str]) -> List[Tuple[str, float]]:
        """
        Classify multiple texts.  Each text is handled independently.

        This is a convenience wrapper — useful for batch pre-warming caches.
        """
        return [self.classify(t) for t in texts]


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_instance: Optional[NLIEmotionClassifier] = None
_instance_lock = threading.Lock()


def get_classifier(
    model_name: str = DEFAULT_MODEL_NAME,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> NLIEmotionClassifier:
    """
    Return the module-level singleton classifier, creating it on first call.

    ``model_name`` and ``confidence_threshold`` are only used when the singleton
    has not yet been created.  Subsequent calls return the same instance.
    """
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = NLIEmotionClassifier(model_name, confidence_threshold)
    return _instance
