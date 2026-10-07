"""
NLI-based emotion classifier — Phase T4.

Zero-shot Natural Language Inference classification of English / Latin-script
text, run on Hugging Face Inference Providers (``HF_ZERO_SHOT_MODEL``, default
``facebook/bart-large-mnli``). Nothing is loaded locally; no torch or GPU.
For Arabic-dominant input the caller (classify_emotion in
spiritual_guidance_service.py) routes to the keyword classifier, which carries
a full Arabic keyword bank.

Hypothesis template
-------------------
For each emotion label the model scores "This person is feeling <emotion>."
against the user's message. Labels are scored independently (multi-label), so
each score is an entailment probability, as in the original local model.

Confidence threshold (default 0.4)
-----------------------------------
If the highest entailment score is below the threshold, the classifier returns
('', score) to signal low confidence. The caller falls back to keywords.

Graceful degradation
--------------------
No token, quota exhaustion, timeouts or malformed responses all return
('', 0.0) and the caller uses keyword matching. Calls use a short timeout
because classification sits in the request path.

Language detection
------------------
`is_arabic_dominant(text)` returns True when > 30 % of characters fall in the
Arabic Unicode range. Callers route Arabic-dominant text to keywords.
"""
from __future__ import annotations

import logging
import re
import threading
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

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
    Zero-shot NLI emotion classifier backed by a Hugging Face hosted model.

    Usage::

        clf = NLIEmotionClassifier()
        clf.warmup()          # optional; checks configuration (no network call)
        emotion, confidence = clf.classify("I feel anxious about tomorrow")
        # → ('anxiety', 0.97)
    """

    # Classification is in the request path; keep upstream waits short.
    TIMEOUT_SECONDS = 10.0

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    ) -> None:
        self._model_name = model_name
        self._threshold = confidence_threshold
        self._lock = threading.Lock()
        self._ready = False

    def _load(self) -> bool:
        """Ready when the HF token is configured. Makes no network call."""
        from app.ai.hf_client import hf_configured

        with self._lock:
            self._ready = hf_configured()
        if not self._ready:
            logger.info("HF_TOKEN not configured — emotion keyword fallback will be used.")
        return self._ready

    def warmup(self) -> bool:
        """Check configuration at startup. Returns True when HF is configured."""
        return self._load()

    @property
    def is_ready(self) -> bool:
        return self._ready

    def _zero_shot(self, text: str) -> List[Tuple[str, float]]:
        """Return (label, entailment probability) pairs from HF."""
        from app.ai.hf_client import classify_exception, task_client

        client = task_client("zero-shot", timeout=self.TIMEOUT_SECONDS)
        try:
            out = client.zero_shot_classification(
                text[:1000],
                candidate_labels=EMOTION_LABELS,
                hypothesis_template="This person is feeling {}.",
                multi_label=True,
                model=self._model_name,
            )
        except Exception as exc:  # noqa: BLE001
            raise classify_exception(exc, "zero-shot") from None
        return [(item.label, float(item.score)) for item in out]

    def classify(self, text: str) -> Tuple[str, float]:
        """
        Classify `text` into an emotion category using zero-shot NLI.

        Returns
        -------
        (emotion_key, confidence)
            ``emotion_key`` is an EmotionCategory string; ``confidence`` is the
            entailment probability [0.0, 1.0].

        Returns ('', 0.0) when HF is not configured or the call fails, and
        ('', score) when the best score is below ``confidence_threshold``.
        """
        if not text or not text.strip() or not self._load():
            return ("", 0.0)

        try:
            scored = self._zero_shot(text)
        except Exception as exc:
            logger.warning("NLI emotion inference unavailable: %s", exc)
            return ("", 0.0)

        scored = [(label, score) for label, score in scored if label in EMOTION_LABELS]
        if not scored:
            logger.warning("NLI emotion inference returned no known labels")
            return ("", 0.0)

        label, confidence = max(scored, key=lambda pair: pair[1])
        if confidence < self._threshold:
            logger.debug("Low NLI confidence %.3f — keyword fallback", confidence)
            return ("", confidence)
        return (label, confidence)

    def classify_batch(self, texts: List[str]) -> List[Tuple[str, float]]:
        """Classify multiple texts independently."""
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
