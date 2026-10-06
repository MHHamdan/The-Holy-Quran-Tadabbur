"""
Grounding safeguards for AI-synthesised answers about the Qur'an.

Pure functions (no I/O) used by the RAG pipeline:

1. Source fencing — retrieved text is wrapped in <source> blocks and any
   sequence that could close the fence or impersonate prompt structure is
   neutralised, so instructions planted inside a source are data, not
   commands (prompt-injection defence; the system prompt says so too).
2. Quotation verification — every quoted Arabic passage in an answer must be
   verbatim canonical Qur'an text or verbatim retrieved tafsir. Anything else
   is removed from the answer: the model may paraphrase, it may not invent or
   alter Qur'an text or put words in a scholar's mouth.
3. Citation helpers — Qur'an self-references ("[Quran, 2:255]") are
   recognised so they are checked against the canonical corpus instead of
   being treated as tafsir sources.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Iterable, List, Sequence, Tuple

# ----------------------------------------------------------------- normalising

# Harakat, Qur'anic annotation marks, superscript alef, tatweel
_DIACRITICS = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭـ࣓-ࣿ]")
_NON_ARABIC_LETTER = re.compile(r"[^ء-ي\s]")
_SPACES = re.compile(r"\s+")


def normalize_arabic(text: str) -> str:
    """Letters-only Arabic normalisation for quotation matching."""
    text = unicodedata.normalize("NFKC", text or "")
    text = _DIACRITICS.sub("", text)
    # Uthmani and Imla'i spelling differ mostly in where alef is written
    # (dagger alef, defective plene spellings), so alef is dropped entirely.
    text = re.sub("[إأآٱا]", "", text)
    text = text.replace("ى", "ي").replace("ئ", "ي").replace("ؤ", "و").replace("ة", "ه").replace("ء", "")
    text = _NON_ARABIC_LETTER.sub(" ", text)
    return _SPACES.sub(" ", text).strip()


def build_corpus_index(texts: Iterable[str]) -> str:
    """Join normalised texts with a separator that never occurs inside a match."""
    return " | ".join(n for n in (normalize_arabic(t) for t in texts) if n)


# -------------------------------------------------------------- source fencing

_FENCE_BREAKERS = re.compile(r"</?\s*source\b[^>]*>", re.IGNORECASE)
_CHAT_TOKENS = re.compile(r"<\|[^|>]{0,40}\|>")
_PROMPT_HEADERS = re.compile(r"^\s*(#{1,6}\s|={3,})", re.MULTILINE)
_SOURCE_HEADER = re.compile(r"\[\s*source\s*:", re.IGNORECASE)


def sanitize_source_text(text: str) -> str:
    """
    Neutralise text that could break out of a <source> block or impersonate
    prompt structure. The scholarly text itself is left intact.
    """
    text = _FENCE_BREAKERS.sub(" ", text or "")
    text = _CHAT_TOKENS.sub(" ", text)
    text = _PROMPT_HEADERS.sub(" ", text)
    text = _SOURCE_HEADER.sub("(source:", text)
    return text.strip()


def _attr(value: str) -> str:
    return sanitize_source_text(str(value)).replace('"', "'")


def fence_source(chunk_id: str, source_name: str, verse_reference: str, content: str) -> str:
    return (
        f'<source id="{_attr(chunk_id)}" name="{_attr(source_name)}" verse="{_attr(verse_reference)}">\n'
        f"{sanitize_source_text(content)}\n"
        f"</source>"
    )


def fence_conversation(history: str) -> str:
    """Prior turns are user-controlled: fence them and mark them as non-evidence."""
    history = sanitize_source_text(history)
    if not history:
        return ""
    return f"<conversation_history>\n{history}\n</conversation_history>"


# --------------------------------------------------------- quotation checking

# Quoted spans: Qur'anic ornate brackets, guillemets, curly and straight quotes.
_QUOTE_PATTERNS = (
    re.compile(r"﴿([^﴾]+)﴾"),
    re.compile(r"«([^»]+)»"),
    re.compile(r"“([^”]+)”"),
    re.compile(r'"([^"\n]+)"'),
)
_ARABIC_LETTER = re.compile(r"[ء-ي]")
_ELLIPSIS = re.compile(r"\.\.\.|…")

UNVERIFIED_QUOTE_EN = "[quotation removed: not found verbatim in the Qur'an or the cited sources]"
UNVERIFIED_QUOTE_AR = "[حُذف اقتباس لم يُعثر عليه بنصه في القرآن أو المصادر]"


@dataclass
class QuotationReport:
    checked: int = 0
    removed: List[str] = field(default_factory=list)


def _is_arabic_quote(span: str, min_words: int) -> bool:
    # Diacritics and Qur'anic marks are not letters; drop them before measuring.
    bare = re.sub(r"\s", "", _DIACRITICS.sub("", span))
    letters = _ARABIC_LETTER.findall(bare)
    if len(letters) < 6 or len(letters) < 0.6 * len(bare):
        return False
    return len(normalize_arabic(span).split()) >= min_words


def _verified(span: str, corpora: Sequence[str]) -> bool:
    # A quotation may elide words with an ellipsis; each piece must match.
    pieces = [normalize_arabic(p) for p in _ELLIPSIS.split(span)]
    pieces = [p for p in pieces if len(p.split()) >= 2] or [normalize_arabic(span)]
    return all(any(piece in corpus for corpus in corpora if corpus) for piece in pieces)


def verify_quotations(
    answer: str,
    quran_index: str,
    evidence_index: str,
    language: str = "en",
    min_words: int = 3,
) -> Tuple[str, QuotationReport]:
    """
    Remove quoted Arabic passages that are neither canonical Qur'an text nor
    verbatim retrieved evidence. Returns (cleaned_answer, report).
    """
    report = QuotationReport()
    placeholder = UNVERIFIED_QUOTE_AR if language == "ar" else UNVERIFIED_QUOTE_EN
    corpora = (quran_index, evidence_index)

    for pattern in _QUOTE_PATTERNS:
        def _check(match: re.Match) -> str:
            span = match.group(1)
            if not _is_arabic_quote(span, min_words):
                return match.group(0)
            report.checked += 1
            if _verified(span, corpora):
                return match.group(0)
            report.removed.append(span.strip())
            return placeholder

        answer = pattern.sub(_check, answer)
    return answer, report


# ------------------------------------------------------------------ citations

_QURAN_SOURCE = re.compile(r"^\s*(the\s+)?(holy\s+)?(qur'?an|quran|koran|surah|sura|القرآن|سورة)\b", re.IGNORECASE)


def is_quran_self_citation(source_name: str) -> bool:
    """True for citations that reference the Qur'an itself rather than a tafsir work."""
    return bool(_QURAN_SOURCE.match(source_name or ""))


def strip_citation_markers(answer: str, markers: Iterable[str]) -> str:
    """Remove exact citation markers (e.g. invalid ones) from the answer text."""
    for marker in set(markers):
        answer = answer.replace(marker, "")
    # Tidy spaces left before punctuation by the removal.
    answer = re.sub(r"[ \t]+([.,،؛:!?])", r"\1", answer)
    return re.sub(r"[ \t]{2,}", " ", answer)


def contains_fiqh_disclaimer(answer: str) -> bool:
    low = (answer or "").lower()
    return "fatwa" in low or "فتوى" in low or "الفتوى" in low
