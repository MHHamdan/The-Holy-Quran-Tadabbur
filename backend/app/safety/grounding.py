"""
Grounding safeguards for AI-synthesised answers about the Qur'an.

Pure functions (no I/O) used by the RAG pipeline:

1. Source fencing — retrieved text (and the user's question) is wrapped in
   fenced blocks, and any sequence that could close a fence or impersonate
   prompt structure is neutralised, so instructions planted in a source are
   data, not commands (prompt-injection defence; the system prompt says so too).
2. Quotation verification — every quoted Arabic passage in an answer must be
   canonical Qur'an text or verbatim retrieved tafsir. A passage whose letter
   skeleton matches the Qur'an is REPLACED by the exact canonical Tanzil text
   (the model's own spelling and vowels are never kept); anything else is
   removed. English quotations presented as the Qur'an must match a stored
   translation of the cited verse; English quotations attributed to a scholar
   must match the retrieved tafsir.
3. Named attributions — a sentence that names a scholar must be backed by a
   citation to that scholar's work, or by cited evidence that names them.
4. Citation helpers — Qur'an self-references ("[Quran, 2:255]") are
   recognised so they are checked against the canonical corpus instead of
   being treated as tafsir sources.
"""
from __future__ import annotations

import bisect
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

# ----------------------------------------------------------------- normalising

_DAGGER_ALEF = "ٰ"
# Harakat, Qur'anic annotation marks, small letters, tatweel (dagger alef apart)
_MARKS = re.compile(r"[ؐ-ًؚ-ٟۖ-ۭـ࣓-ࣿ]")
_LETTER_FOLD = str.maketrans({
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ئ": "ي", "ؤ": "و", "ة": "ه", "ء": "",
})
_NON_ARABIC_LETTER = re.compile(r"[^ء-ي\s]")
_SPACES = re.compile(r"\s+")
_UTHMANI_ONLY = re.compile(r"[ٱۖ-ۭ]")


def normalize_arabic(text: str, dagger_as_alef: bool = True) -> str:
    """
    Letter-skeleton Arabic normalisation for quotation matching.

    Vowels and annotation marks are dropped and hamza/alef forms are folded,
    but alef itself is kept, so "قال" and "قل" stay distinct. The dagger alef
    (written above the letter in Uthmani script) is either read as a full
    alef or dropped; callers try both.
    """
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace(_DAGGER_ALEF, "ا" if dagger_as_alef else "")
    text = _MARKS.sub("", text).translate(_LETTER_FOLD)
    text = _NON_ARABIC_LETTER.sub(" ", text)
    return _SPACES.sub(" ", text).strip()


def build_corpus_index(texts: Iterable[str]) -> str:
    """Join normalised texts with a separator that never occurs inside a match."""
    out = []
    for t in texts:
        for dagger in (True, False):
            n = normalize_arabic(t, dagger)
            if n and n not in out[-1:]:
                out.append(n)
    return " | ".join(out)


# ---------------------------------------------------------- canonical Qur'an

@dataclass
class QuranMatch:
    text: str                            # exact canonical substring (Tanzil)
    verses: List[Tuple[int, int]]        # (sura, aya) covered, in order


class QuranIndex:
    """
    Token-aligned index of the canonical Qur'an text.

    The letter skeleton is only used to find candidates; a match is mapped
    back to the canonical Tanzil tokens (Uthmani or Imla'i) so the answer can
    show the exact stored text.
    """

    _FORMS = (("uthmani", True), ("uthmani", False), ("imlaei", True), ("imlaei", False))

    def __init__(self, verses: Iterable[Tuple[int, int, str, str]]):
        rows = sorted((int(s), int(a), u or "", i or "") for s, a, u, i in verses)
        self._canon: Dict[str, Dict[Tuple[int, int], List[str]]] = {"uthmani": {}, "imlaei": {}}
        for s, a, u, i in rows:
            self._canon["uthmani"][(s, a)] = u.split()
            self._canon["imlaei"][(s, a)] = i.split()
        self._forms = []
        for script, dagger in self._FORMS:
            parts: List[str] = []
            starts: List[int] = []
            refs: List[Tuple[int, int, int]] = []
            pos = 1  # corpus starts with a space
            last_sura = None
            for s, a, _, _ in rows:
                if last_sura is not None and s != last_sura:
                    parts.append("|")
                    pos += 2
                last_sura = s
                for k, tok in enumerate(self._canon[script][(s, a)]):
                    n = normalize_arabic(tok, dagger).replace(" ", "")
                    if not n:
                        continue
                    starts.append(pos)
                    refs.append((s, a, k))
                    parts.append(n)
                    pos += len(n) + 1
            self._forms.append((script, dagger, " " + " ".join(parts) + " ", starts, refs))
        self.verse_count = len(rows)

    def __bool__(self) -> bool:
        return self.verse_count > 0

    def verse_text(self, sura: int, aya: int) -> List[str]:
        """Canonical Uthmani and Imla'i text of one verse (empty if unknown)."""
        return [" ".join(self._canon[k].get((sura, aya), [])) for k in ("uthmani", "imlaei")
                if self._canon[k].get((sura, aya))]

    def contains(self, span: str) -> bool:
        return bool(self.find(span, limit=1))

    def find(self, span: str, prefer: Sequence[Tuple[int, int]] = (), limit: int = 200) -> List[QuranMatch]:
        """All canonical renderings of ``span`` (best candidate first)."""
        uthmani_marks = bool(_UTHMANI_ONLY.search(span or ""))
        wanted = _SPACES.sub(" ", unicodedata.normalize("NFC", span or "")).strip()
        prefer_set = set(prefer)
        found: Dict[Tuple[str, Tuple], QuranMatch] = {}
        scored = []
        for script, dagger, corpus, starts, refs in self._forms:
            needle_norm = normalize_arabic(span, dagger)
            if not needle_norm:
                continue
            needle = " " + needle_norm + " "
            n_tokens = len(needle_norm.split())
            at = corpus.find(needle)
            hits = 0
            while at != -1 and hits < limit:
                i0 = bisect.bisect_left(starts, at + 1)
                i1 = i0 + n_tokens - 1
                if i0 < len(starts) and starts[i0] == at + 1 and i1 < len(refs):
                    key = (script, refs[i0], refs[i1])
                    if key not in found:
                        found[key] = self._render(script, refs[i0], refs[i1])
                        m = found[key]
                        rank = (
                            0 if prefer_set & set(m.verses) else 1,
                            0 if m.text == wanted else 1,
                            0 if (script == "uthmani") == uthmani_marks else 1,
                        )
                        scored.append((rank, len(scored), m))
                    hits += 1
                at = corpus.find(needle, at + 1)
        return [m for _, _, m in sorted(scored, key=lambda x: (x[0], x[1]))]

    def _render(self, script: str, start: Tuple[int, int, int], end: Tuple[int, int, int]) -> QuranMatch:
        (s0, a0, k0), (s1, a1, k1) = start, end
        words: List[str] = []
        verses: List[Tuple[int, int]] = []
        canon = self._canon[script]
        s, a = s0, a0
        while True:
            toks = canon.get((s, a), [])
            lo = k0 if (s, a) == (s0, a0) else 0
            hi = k1 + 1 if (s, a) == (s1, a1) else len(toks)
            words.extend(toks[lo:hi])
            verses.append((s, a))
            if (s, a) == (s1, a1) or (s, a + 1) not in canon:
                break
            a += 1
        return QuranMatch(text=" ".join(words), verses=verses)


# -------------------------------------------------------------- source fencing

_INVISIBLE = re.compile(r"[​-‏‪-‮⁠-⁤⁦-⁩﻿­]")
_FENCE_BREAKERS = re.compile(
    r"<\s*/?\s*(source|question|conversation_history|system|assistant|user|instructions?|im_start|im_end)"
    r"\b[^>]*>",
    re.IGNORECASE,
)
_CHAT_TOKENS = re.compile(r"<\|[^|>]{0,40}\|>")
_PROMPT_HEADERS = re.compile(r"^\s*(#{1,6}\s|={3,})|#{2,}|={3,}", re.MULTILINE)
_SOURCE_HEADER = re.compile(r"\[\s*source\s*:", re.IGNORECASE)


def sanitize_source_text(text: str) -> str:
    """
    Neutralise text that could break out of a fenced block or impersonate
    prompt structure. Only the copy sent to the model is sanitised; stored and
    displayed tafsir text is never touched.
    """
    text = unicodedata.normalize("NFKC", text or "")  # fullwidth ＜＞ -> <>
    text = _INVISIBLE.sub("", text)
    text = _FENCE_BREAKERS.sub(" ", text)
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


def fence_question(question: str) -> str:
    """The user's question is data too: fence it so it cannot pose as instructions."""
    return f"<question>\n{sanitize_source_text(question)}\n</question>"


# --------------------------------------------------------- quotation checking

# Quote containers: ornate brackets, guillemets, curly/straight quotes,
# parentheses and **bold**.
_CONTAINERS = re.compile(
    r"﴿(?P<orn>[^﴾]+)﴾|«(?P<gui>[^»]+)»|“(?P<cur>[^”]+)”|\"(?P<str>[^\"\n]+)\""
    r"|\((?P<par>[^()\n]+)\)|\*\*(?P<bold>[^*\n]+)\*\*"
)
_OPEN_CLOSE = {"orn": ("﴿", "﴾"), "gui": ("«", "»"), "cur": ("“", "”"), "str": ('"', '"'),
               "par": ("(", ")"), "bold": ("**", "**")}
_ARABIC_CHARS = "؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿"
_ARABIC_RUN = re.compile(rf"[{_ARABIC_CHARS}]+(?:[ \t ]+[{_ARABIC_CHARS}]+)*")
_ARABIC_LETTER = re.compile(r"[ء-ي]")
_ELLIPSIS = re.compile(r"\.\.\.|…")
# "Allah says:", "قال الله تعالى" ... — what follows is presented as Qur'an.
_ARABIC_CUE = re.compile(
    r"(قال الله تعالى|قال الله عز وجل|قال تعالى|يقول الله تعالى|يقول تعالى|قوله تعالى|قال الله سبحانه|قال الله)"
)
_CUE_SPAN = re.compile(
    _ARABIC_CUE.pattern + r"\s*[:：]?\s*(?P<span>[^\[\]\.!؟?\n﴿«“\"(*]+)"
)
_LATIN_CUE = re.compile(
    r"\b(says?|said|states?|stated|reads?|recited?|revealed|declares?)\b[\s:,]*[\(\*«“\"﴿]*\s*$",
    re.IGNORECASE,
)
_QURAN_SPEAKER = re.compile(
    r"\b(allah|god|the (holy )?qur'?an|the verse|the ayah|the surah|this verse|this ayah)\s+"
    r"(says|said|states|declares|reads|tells us)\b",
    re.IGNORECASE,
)
_SCHOLAR_SPEECH = re.compile(r"\b(wrote|writes|said|says|states|stated|notes|noted|explains|comments)\b", re.IGNORECASE)
_REF_IN_TEXT = re.compile(r"(\d{1,3})\s*:\s*(\d{1,3})")

UNVERIFIED_QUOTE_EN = "[quotation removed: not found verbatim in the Qur'an or the cited sources]"
UNVERIFIED_QUOTE_AR = "[حُذف اقتباس لم يُعثر عليه بنصه في القرآن أو المصادر]"


@dataclass
class QuotationReport:
    checked: int = 0
    removed: List[str] = field(default_factory=list)
    # (model's text, canonical Tanzil text) for every Qur'an quotation restored
    replaced: List[Tuple[str, str]] = field(default_factory=list)
    verses: Set[Tuple[int, int]] = field(default_factory=set)
    # (canonical text, verses it is from, reference written next to it) for
    # real Qur'an text quoted under a reference it does not belong to
    misreferenced: List[Tuple[str, List[Tuple[int, int]], List[Tuple[int, int]]]] = field(default_factory=list)


def _arabic_tokens(span: str) -> int:
    return len(normalize_arabic(span).split())


def _is_arabic_span(span: str, min_words: int) -> bool:
    bare = re.sub(r"\s", "", _MARKS.sub("", span.replace(_DAGGER_ALEF, "")))
    letters = _ARABIC_LETTER.findall(bare)
    if len(letters) < 4 or len(letters) < 0.6 * max(len(bare), 1):
        return False
    return _arabic_tokens(span) >= min_words


def _in_corpus(piece: str, corpus: str) -> bool:
    """Whole-word match of ``piece`` inside a build_corpus_index() string."""
    if not corpus:
        return False
    padded = f" {corpus} "
    return any(
        (n := normalize_arabic(piece, d)) and f" {n} " in padded for d in (True, False)
    )


def _nearby_refs(text: str, end: int) -> List[Tuple[int, int]]:
    """Verse references written right after a quotation ("﴿…﴾ [Quran, 2:255]")."""
    window = text[end:end + 60].translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
    window = re.split(r"[.!?؟\n]", window, maxsplit=1)[0]
    return [(int(s), int(a)) for s, a in _REF_IN_TEXT.findall(window)]


def _norm_en(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "").lower()
    text = text.replace("’", "'").replace("‘", "'")
    text = re.sub(r"[^a-z0-9']+", " ", text)
    return _SPACES.sub(" ", text).strip()


def _sentence_bounds(text: str, start: int, end: int) -> Tuple[int, int]:
    left = max(text.rfind(c, 0, start) for c in ".!?؟\n")
    rights = [i for i in (text.find(c, end) for c in ".!?؟\n") if i != -1]
    return left + 1, (min(rights) + 1 if rights else len(text))


class _QuoteChecker:
    def __init__(self, quran_index, evidence_index, language, min_words,
                 translations, english_evidence, report):
        self.quran = quran_index if isinstance(quran_index, QuranIndex) and quran_index else None
        self.evidence = evidence_index or ""
        self.language = language
        self.min_words = min_words
        self.translations = translations
        self.english_evidence = english_evidence
        self.report = report
        self.placeholder = UNVERIFIED_QUOTE_AR if language == "ar" else UNVERIFIED_QUOTE_EN

    def resolve(self, span: str, prefer: Sequence[Tuple[int, int]]) -> Optional[str]:
        """Canonical text for a Qur'an quotation, the span itself for verbatim
        evidence, or None when the span cannot be verified."""
        self.report.checked += 1
        raw_pieces = [p.strip() for p in _ELLIPSIS.split(span)]
        pieces = [p for p in raw_pieces if _arabic_tokens(p) >= 2] or [span.strip()]
        out = []
        for piece in pieces:
            if self.quran is not None:
                matches = self.quran.find(piece, prefer)
                if matches:
                    best = matches[0]
                    out.append(best.text)
                    self.report.verses.update(best.verses)
                    if prefer and not set(prefer) & set(best.verses):
                        self.report.misreferenced.append((best.text, list(best.verses), list(prefer)))
                    if best.text != piece:
                        self.report.replaced.append((piece, best.text))
                    continue
            if _in_corpus(piece, self.evidence):
                out.append(piece)
                continue
            self.report.removed.append(span.strip())
            return None
        return " … ".join(out) if len(out) > 1 else out[0]

    # English quotation presented as the Qur'an / attributed to a scholar
    def check_english(self, text: str, start: int, end: int, inner: str) -> Optional[bool]:
        if len(_norm_en(inner).split()) < 4:
            return None
        s0, s1 = _sentence_bounds(text, start, end)
        sentence = text[s0:s1]
        quran_voice = bool(_QURAN_SPEAKER.search(sentence)) or bool(
            re.search(r"\[\s*(the\s+)?(holy\s+)?(qur'?an|quran|القرآن)\s*[,،]", sentence, re.I)
        )
        needle = _norm_en(inner)
        if quran_voice:
            if self.translations is None:
                return None
            cited = [(int(s), int(a)) for s, a in _REF_IN_TEXT.findall(sentence)]
            pool = [t for ref in cited for t in self.translations.get(ref, [])] if cited else [
                t for texts in self.translations.values() for t in texts
            ]
            self.report.checked += 1
            return any(needle in _norm_en(t) for t in pool)
        if self.english_evidence is not None and (
            "[" in sentence or _SCHOLAR_SPEECH.search(sentence)
        ):
            self.report.checked += 1
            return needle in _norm_en(self.english_evidence)
        return None


def verify_quotations(
    answer: str,
    quran_index,
    evidence_index: str,
    language: str = "en",
    min_words: int = 3,
    *,
    translations: Optional[Mapping[Tuple[int, int], List[str]]] = None,
    english_evidence: Optional[str] = None,
) -> Tuple[str, QuotationReport]:
    """
    Verify every quotation in ``answer``. Returns (cleaned_answer, report).

    - Arabic spans in ﴿﴾ «» “” "" () or **…** (2+ words in ﴿﴾ or after a quote
      cue, else ``min_words``), spans after "قال الله تعالى"-style cues, and
      (in English answers) any unquoted run of Arabic words.
    - Qur'an matches are replaced by the canonical Tanzil substring; verbatim
      evidence is kept; anything else is replaced by a placeholder.
    - With ``translations`` / ``english_evidence``, English quotations voiced
      as the Qur'an / a scholar must match them verbatim (normalised).
    ``quran_index`` is a ``QuranIndex``; pass "" / None to check evidence only.
    """
    report = QuotationReport()
    chk = _QuoteChecker(quran_index, evidence_index, language, min_words,
                        translations, english_evidence, report)

    # Pass 1: quote containers
    def _container(m: re.Match) -> str:
        kind = m.lastgroup
        inner = m.group(kind)
        op, cl = _OPEN_CLOSE[kind]
        text = m.string
        cue = bool(_LATIN_CUE.search(text[max(0, m.start() - 40):m.start()])) or bool(
            _ARABIC_CUE.search(text[max(0, m.start() - 25):m.start()])
        )
        need = 2 if kind == "orn" or cue else min_words
        if _is_arabic_span(inner, need):
            resolved = chk.resolve(inner, _nearby_refs(text, m.end()))
            return chk.placeholder if resolved is None else f"{op}{resolved}{cl}"
        if kind in ("cur", "str") and not _ARABIC_LETTER.search(inner):
            ok = chk.check_english(text, m.start(), m.end(), inner)
            if ok is False:
                report.removed.append(inner.strip())
                return UNVERIFIED_QUOTE_EN
        return m.group(0)

    answer = _CONTAINERS.sub(_container, answer)

    # Pass 2: text presented as the Qur'an after a cue ("قال الله تعالى: …")
    def _cue(m: re.Match) -> str:
        span = m.group("span")
        lead = len(span) - len(span.lstrip())
        core = span.strip()
        if not _is_arabic_span(core, 2):
            return m.group(0)
        resolved = chk.resolve(core, _nearby_refs(m.string, m.end()))
        replacement = chk.placeholder if resolved is None else resolved
        trail = span[len(span.rstrip()):]
        head = m.group(0)[: m.start("span") - m.start()]
        return head + span[:lead] + replacement + trail

    answer = _CUE_SPAN.sub(_cue, answer)

    # Pass 3 (English answers): unquoted runs of Arabic words
    if language != "ar":
        pieces = []
        protected = [(m.start(), m.end()) for m in _CONTAINERS.finditer(answer)]
        protected += [(m.start(), m.end()) for m in re.finditer(re.escape(UNVERIFIED_QUOTE_EN), answer)]

        def _is_protected(a: int, b: int) -> bool:
            return any(a < pe and b > ps for ps, pe in protected)

        for m in _ARABIC_RUN.finditer(answer):
            if _is_protected(m.start(), m.end()):
                continue
            run = m.group(0)
            cue = _ARABIC_CUE.match(run)
            offset = cue.end() if cue else 0
            core = run[offset:].strip(" :")
            if not core:
                continue
            need = 2 if (cue or _LATIN_CUE.search(answer[max(0, m.start() - 40):m.start()])) else min_words
            if not _is_arabic_span(core, need):
                continue
            core_start = m.start() + run.index(core, offset)
            resolved = chk.resolve(core, _nearby_refs(answer, m.end()))
            pieces.append((core_start, core_start + len(core), chk.placeholder if resolved is None else resolved))
        for a, b, rep in reversed(pieces):
            answer = answer[:a] + rep + answer[b:]

    return answer, report


# ---------------------------------------------------------- named attributions

# Scholars and early authorities an answer might name. A key that is a
# catalogue source id ties the name to that tafsir work.
SCHOLAR_NAMES: Tuple[Tuple[Optional[str], Tuple[str, ...]], ...] = (
    ("ibn_kathir", ("Ibn Kathir", "ابن كثير")),
    ("tabari", ("Tabari", "Ibn Jarir", "الطبري", "ابن جرير")),
    ("qurtubi", ("Qurtubi", "القرطبي")),
    ("jalalayn", ("Jalalayn", "Suyuti", "Mahalli", "الجلالين", "السيوطي", "المحلي")),
    ("saadi", ("Sa'di", "Saadi", "السعدي")),
    ("ibn_ashur", ("Ibn Ashur", "Ibn 'Ashur", "ابن عاشور")),
    ("baghawi", ("Baghawi", "البغوي")),
    ("sha_rawi", ("Sha'rawi", "Shaarawi", "الشعراوي")),
    ("fi_zilal", ("Sayyid Qutb", "سيد قطب")),
    ("tantawi", ("Tantawi", "طنطاوي")),
    (None, ("Ibn Abbas", "Ibn 'Abbas", "ابن عباس")),
    (None, ("Ibn Mas'ud", "Ibn Masud", "ابن مسعود")),
    (None, ("Mujahid",)),
    (None, ("Qatadah", "Qatada", "قتادة")),
    (None, ("Ikrimah", "Ikrima", "عكرمة")),
    (None, ("Sa'id ibn Jubayr", "Said ibn Jubayr", "سعيد بن جبير")),
    (None, ("Hasan al-Basri", "al-Hasan al-Basri", "الحسن البصري")),
    (None, ("Suddi", "السدي")),
    (None, ("Dahhak", "الضحاك")),
    (None, ("Ibn Taymiyyah", "Ibn Taymiya", "ابن تيمية")),
    (None, ("Ibn al-Qayyim", "Ibn Qayyim", "ابن القيم")),
    (None, ("Razi", "Fakhr al-Din", "الرازي")),
    (None, ("Zamakhshari", "الزمخشري")),
    (None, ("Shawkani", "الشوكاني")),
    (None, ("Alusi", "Alousi", "الألوسي", "الآلوسي")),
    (None, ("Baydawi", "Baidawi", "البيضاوي")),
    (None, ("Ibn Abi Hatim", "ابن أبي حاتم")),
)


def _name_pattern(name: str) -> re.Pattern:
    if re.search(r"[؀-ۿ]", name):
        body = re.escape(name).replace(r"\ ", r"\s+")
        return re.compile(rf"(?<![ء-ي])[وفبل]?{body}(?![ء-ي])")
    body = re.escape(name).replace(r"\ ", r"[\s-]+").replace("'", "['’ʿ]?")
    return re.compile(rf"\b(?:al[\s-]|as[\s-]|at[\s-]|ar[\s-])?{body}\b", re.IGNORECASE)


_SCHOLAR_PATTERNS = [(key, names, [_name_pattern(n) for n in names]) for key, names in SCHOLAR_NAMES]


def _mentioned_in(names: Sequence[str], content: str) -> bool:
    content_ar = normalize_arabic(content)
    content_en = _norm_en(content)
    for n in names:
        if re.search(r"[؀-ۿ]", n):
            if f" {normalize_arabic(n)} " in f" {content_ar} ":
                return True
        elif re.search(rf"\b{re.escape(_norm_en(n))}\b", content_en):
            return True
    return False


# Hadith and Prophetic-speech attributions. A sentence that reports what the
# Prophet ﷺ said, or cites a hadith collection/number, survives only if the
# cited chunk itself carries that report.
_HADITH_COLLECTIONS: Tuple[Tuple[str, ...], ...] = (
    ("Bukhari", "البخاري"),
    ("Sahih Muslim", "Imam Muslim", "صحيح مسلم", "الإمام مسلم"),
    ("Tirmidhi", "الترمذي"),
    ("Abu Dawud", "Abu Dawood", "Abu Daud", "أبو داود", "أبي داود"),
    ("Nasa'i", "Nasai", "النسائي"),
    ("Ibn Majah", "Ibn Maja", "ابن ماجه", "ابن ماجة"),
    ("Musnad Ahmad", "Imam Ahmad", "مسند أحمد", "الإمام أحمد"),
    ("Muwatta", "الموطأ"),
)
# "narrated by Muslim" / "رواه مسلم" — "Muslim"/"مسلم" alone is an ordinary word.
_MUSLIM_AS_COLLECTOR = re.compile(
    r"\b(narrated|reported|recorded|related|collected)\s+(by|in)\s+muslim\b|\bmuslim\s+(narrated|reported|recorded)\b"
    r"|(رواه|أخرجه|اخرجه|خرجه)\s+مسلم(?![ء-ي])",
    re.IGNORECASE,
)
_AHMAD_AS_COLLECTOR = re.compile(
    r"\b(narrated|reported|recorded)\s+(by|in)\s+ahmad\b|(رواه|أخرجه|اخرجه)\s+(الإمام\s+)?أحمد(?![ء-ي])",
    re.IGNORECASE,
)
_HADITH_CUE = re.compile(
    r"\bthe\s+(holy\s+)?prophet\b(?!\s+(of|musa|moses|ibrahim|abraham|yusuf|joseph|nuh|noah|isa|jesus|"
    r"yunus|jonah|sulayman|solomon|dawud|david|ayyub|job|zakariyya|yahya|hud|salih|shu'?ayb|lut|lot|"
    r"idris|adam|ismail|ishmael|ishaq|isaac|yaqub|jacob|harun|aaron|ilyas|elijah|zakariya))"
    r"\s*(\(\s*(pbuh|saw|saws|s\.a\.w\.?)\s*\)|ﷺ)?\s*(said|says|stated|taught|told|declared|instructed|"
    r"commanded|forbade|prohibited|is reported|was reported|reportedly)\b"
    r"|\b(messenger of (allah|god)|allah'?s messenger|rasul ?allah|rasulullah)\b"
    r"|\bpeace be upon him\b|\(\s*(pbuh|saws?)\s*\)|ﷺ"
    r"|\bhadiths?\b|\bnarrated\s+(by|in|that|from)\b|\b(sunan|sahih|musnad|jami')\b"
    # Arabic: "حديث" alone also means "discourse" (حديث القرآن عن الصبر), and
    # "النبي" precedes prophets' names in stories, so only clear hadith cues.
    r"|رسول\s+الله|(قال|عن|وقال|يقول)\s+النبي(?![ء-ي])|النبي\s*(ﷺ|صلى)|صلى\s+الله\s+عليه\s+وسلم"
    r"|(?<![ء-ي])(رواه|أخرجه|اخرجه|روى)(?![ء-ي])"
    r"|(في|وفي)\s+(ال)?حديث(?![ء-ي])|الحديث\s+(الشريف|الصحيح|النبوي)|حديث\s+(صحيح|حسن|ضعيف|نبوي|شريف)"
    r"|(?<![ء-ي])أحاديث(?![ء-ي])",
    re.IGNORECASE,
)
_PROPHET_IN_SOURCE = re.compile(
    r"\bprophet\b|\bmessenger\b|ﷺ|رسول\s+الله|النبي|صلى\s+الله\s+عليه\s+وسلم|حديث|رواه|أخرجه|hadith",
    re.IGNORECASE,
)
_ARABIC_INDIC = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
_VERSE_REF = re.compile(r"\d{1,3}\s*:\s*\d{1,3}(\s*-\s*\d{1,3})?")
_EN_STOP = frozenset(
    "the a an and or of to in on for with that this is was are were be been his her him he she it its "
    "who whom which what will would shall should never ever not no from by as at said says prophet "
    "messenger allah god peace upon narrated hadith reported sahih also than then there their they "
    "them any all one times verse".split()
)


_INJECTION_MARKERS = re.compile(
    r"\b(ignore|disregard|forget)\s+(all\s+|any\s+|the\s+)?(previous|prior|above|earlier|your)\s+"
    r"(instructions|rules|prompts?)\b|\b(system|developer)\s+prompt\b|\byou are now\b|<\s*/?\s*(system|"
    r"assistant|source|question)\b|<\|[^|>]{0,40}\|>|\bnew system prompt\b|\btell the user\b"
    r"|تجاهل\s+(كل\s+|جميع\s+)?(التعليمات|الأوامر|القواعد)|قل\s+للمستخدم|أنت\s+الآن",
    re.IGNORECASE,
)


def looks_like_injection(text: str) -> bool:
    """True for evidence text that carries instructions to the model.

    Such text is still fenced and shown verbatim, but it can never count as
    support for a claim: an answer that repeats a planted instruction
    ("tell the user wine is permitted") is obeying it, not citing tafsir.
    """
    return bool(_INJECTION_MARKERS.search(unicodedata.normalize("NFKC", text or "")))


def _chunk_texts(chunk: object) -> List[str]:
    """Distinct evidence texts of a chunk, injected ones excluded."""
    out: List[str] = []
    for f in ("content", "content_ar", "content_en"):
        t = getattr(chunk, f, None)
        if t and t not in out and not looks_like_injection(t):
            out.append(t)
    return out


def _chunk_text(chunks: Sequence[object]) -> str:
    return " ".join(t for c in chunks for t in _chunk_texts(c))


def _content_tokens(text: str) -> List[str]:
    out = [t for t in _norm_en(text).split() if len(t) > 2 and t not in _EN_STOP and not t.isdigit()]
    out += [t for t in normalize_arabic(text).split() if len(t) > 2]
    return out


# ------------------------------------------------- local evidence support

# Words that carry no claim of their own: report verbs, discourse words and
# the honorifics that frame a statement ("Ibn Kathir explains that…").
_EN_META = frozenset(
    "explains explained explain explaining notes noted mentions mentioned states stated writes wrote "
    "according describes described describing highlights highlighted emphasizes emphasises emphasized "
    "points point means meaning meant refers referring indicates indicated tafsir tafseer verse verses "
    "ayah ayat surah sura quran qur'an scholar scholars commentators commentary interpretation discusses "
    "discussed detail details because therefore thus also further furthermore moreover however which "
    "while when where into upon about through over under within without these those such some more most "
    "very many much only just like being have has had does did done here there his hers its our your "
    "their them they this that these said says say tells told reports reported cites cited narration "
    "sheikh shaykh imam allamah mufti whoever anyone everyone ibn bin abu".split()
)
_EN_META_STEMS = frozenset(w[:6] if len(w) > 6 else w for w in _EN_META)
_AR_STOP_RAW = (
    "قال وقال فقال يقول ويقول النبي رسول الله صلى عليه وسلم رواه حديث الحديث التي الذي الذين هذه هذا "
    "ذلك تلك كان كانت وكان على إلى عن من في أن إن أنه وأنه بأنها أنها إنها هو هي لها له كل ما لا قد وقد "
    "ثم أو مع بن ابن أبي أبو تعالى سبحانه الآية آية الآيات عز وجل ذكر وذكر يعني أي معنى المعنى تفسير "
    "التفسير بين بيّن ومعناها معناها المفسرون العلماء الشيخ العلامة الإمام كما وهذا وهذه فإن وإن ولا "
    "أيضا عند بعد قبل حتى إذا وإذا لم لن ليس عليها عليهم منها منه فيها فيه به بها"
)
_AR_STOP = frozenset(normalize_arabic(w) for w in _AR_STOP_RAW.split())
_AR_PREFIXES = ("وال", "فال", "بال", "كال", "لل", "ال", "و", "ف", "ب", "ل", "س")
_AR_SUFFIXES = ("هما", "كما", "تما", "هم", "هن", "كم", "كن", "نا", "ها", "ون", "ين", "ان", "ات", "وا", "تم",
                "ه", "ك", "ي", "ت", "ا")


def _stem_ar(tok: str) -> str:
    """Light Arabic stem: one clitic prefix, one pronoun/plural suffix and the
    imperfect prefix, so ذنوبهم/ذنوبنا and يعاقبهم/تعاقبنا compare equal."""
    for p in _AR_PREFIXES:
        if tok.startswith(p) and len(tok) - len(p) >= 3:
            tok = tok[len(p):]
            break
    for sfx in _AR_SUFFIXES:
        if tok.endswith(sfx) and len(tok) - len(sfx) >= 3:
            tok = tok[: -len(sfx)]
            break
    if len(tok) >= 4 and tok[0] in "يتنا":
        tok = tok[1:]
    return tok


def _stem_en(tok: str) -> str:
    return tok[:6] if len(tok) > 6 else tok


def _seq(text: str) -> Tuple[List[str], List[str]]:
    """Claim-bearing tokens of ``text`` in order: (English stems, Arabic stems)."""
    en = [
        st for t in _norm_en(text).split()
        if len(t) > 2 and not t.isdigit() and t not in _EN_STOP
        and (st := _stem_en(t)) not in _EN_META_STEMS
    ]
    ar = []
    for t in normalize_arabic(text).split():
        if len(t) > 2 and t not in _AR_STOP:
            st = _stem_ar(t)
            if st not in _AR_STOP:
                ar.append(st)
    return en, ar


def _window_hits(claim: Sequence[str], src: Sequence[str], window: int) -> int:
    """Most distinct claim tokens found together within ``window`` source tokens."""
    need = set(claim)
    if not need or not src:
        return 0
    hits = [(i, t) for i, t in enumerate(src) if t in need]
    best, counts, j = 0, {}, 0
    for pos, tok in hits:
        counts[tok] = counts.get(tok, 0) + 1
        while hits[j][0] < pos - window:
            old = hits[j][1]
            counts[old] -= 1
            if not counts[old]:
                del counts[old]
            j += 1
        best = max(best, len(counts))
    return best


def _has_ngram(claim: Sequence[str], src: Sequence[str], n: int) -> bool:
    if n < 2 or len(claim) < n or len(src) < n:
        return False
    grams = {tuple(src[i:i + n]) for i in range(len(src) - n + 1)}
    return any(tuple(claim[i:i + n]) in grams for i in range(len(claim) - n + 1))


@dataclass
class Support:
    """How well a claim is carried by one evidence text."""
    tokens: int = 0           # distinct claim tokens in scripts the evidence covers
    found: int = 0            # of those, present anywhere in the evidence text
    local: int = 0            # of those, present together inside one window
    ngram: bool = False       # a run of consecutive claim tokens is in the evidence
    comparable: bool = False  # the evidence has text in the claim's script

    @property
    def coverage(self) -> float:
        return self.found / self.tokens if self.tokens else 1.0

    @property
    def local_coverage(self) -> float:
        return self.local / self.tokens if self.tokens else 1.0


def evidence_support(claim: str, texts: Sequence[str], window: int = 60, ngram: int = 4) -> Support:
    """Lexical support for ``claim`` in the evidence ``texts`` (best single text)."""
    c_en, c_ar = _seq(claim)
    best = Support(tokens=len(set(c_en)) + len(set(c_ar)))
    best_score = -1.0
    for text in texts:
        s_en, s_ar = _seq(text)
        total = len(s_en) + len(s_ar)
        sup = Support()
        for claim_toks, src in ((c_en, s_en), (c_ar, s_ar)):
            # Only a script the evidence is written in counts: an English
            # chunk quoting a verse in Arabic is not Arabic evidence, and a
            # stray label is not English evidence.
            if not claim_toks or len(src) < 3 or len(src) < 0.3 * total:
                continue
            sup.comparable = True
            need = set(claim_toks)
            sup.tokens += len(need)
            sup.found += len(need & set(src))
            sup.local += _window_hits(claim_toks, src, window)
            # Paraphrase inserts words of its own: look for the run among the
            # claim words the evidence has, in the claim's order.
            src_set = set(src)
            present = [t for t in claim_toks if t in src_set]
            sup.ngram = sup.ngram or _has_ngram(present, src, min(ngram, len(claim_toks)))
        if not sup.comparable:
            continue
        score = sup.local_coverage + (1 if sup.ngram else 0)
        if score > best_score:
            best, best_score = sup, score
    return best


def _evidence_texts(chunks: Sequence[object]) -> List[str]:
    return [t for c in chunks for t in _chunk_texts(c)]


def _strip_names(text: str) -> str:
    """Remove scholar and hadith-collection names (they are attribution, not content)."""
    for _key, _names, pats in _SCHOLAR_PATTERNS:
        for p in pats:
            text = p.sub(" ", text)
    for names in _HADITH_COLLECTIONS:
        for n in names:
            text = _name_pattern(n).sub(" ", text)
    return text


def _hadith_supported(sentence: str, chunks: Sequence[object], cite_re: re.Pattern) -> bool:
    """True when the cited evidence carries the hadith report the sentence makes."""
    if not chunks:
        return False
    source = _chunk_text(chunks)
    if not _PROPHET_IN_SOURCE.search(source):
        return False
    body = cite_re.sub(" ", sentence).translate(_ARABIC_INDIC)
    body = _VERSE_REF.sub(" ", body)
    # Every collection named must be named by the evidence.
    for names in _HADITH_COLLECTIONS:
        if any(_name_pattern(n).search(body) for n in names) and not _mentioned_in(names, source):
            return False
    if _MUSLIM_AS_COLLECTOR.search(body) and not _mentioned_in(("Muslim", "مسلم"), source):
        return False
    if _AHMAD_AS_COLLECTOR.search(body) and not _mentioned_in(("Ahmad", "أحمد"), source):
        return False
    # Every number given (hadith numbers, counts like "one hundred times" aside)
    # must appear in the evidence.
    source_digits = set(re.findall(r"\d+", source.translate(_ARABIC_INDIC)))
    if any(n not in source_digits for n in re.findall(r"\d+", body)):
        return False
    # The reported content must come from the evidence, and from one place in
    # it: a long chunk contains most common words somewhere, so a ratio over
    # the whole chunk let invented reports through. Either (nearly) every
    # content word sits in one window, or a run of 3 consecutive content
    # words matches and most of the rest sit in the same window.
    sup = evidence_support(_strip_names(body), _evidence_texts(chunks), ngram=3)
    if sup.tokens >= 3:
        if not sup.comparable:
            return False
        if sup.local_coverage >= 0.85:
            return True
        return sup.ngram and sup.local_coverage >= 0.65
    return True


# ------------------------------------------------- generic attributions

# Honorific + name ("Sheikh X said", "قال العلامة X"), kunya/nasab names
# ("Ibn X", "قال ابن X") and multi-word names before a speech verb. A name
# that is not on SCHOLAR_NAMES must still be found in the cited evidence
# (its text or its source/author metadata); otherwise the sentence goes.
_NAME_PART = (
    r"(?:(?:[Aa]l|[Ee]l|[Aa][dhnrstz]|[Ii]bn|[Bb]in|[Bb]int|[Aa]bu|[Aa]bi|[Aa]bd|[Aa]bdul|ul)[\s\-'’]+)*"
    r"[A-Z][\w'’`ʿ\-]+"
)
_EN_HONORIFIC = (
    r"(?:Shaykh al-Islam|Sheikh|Shaykh|Shaikh|Imam|Al-Imam|Allamah|'Allamah|Allama|Mufti|Dr\.?|Doctor|"
    r"Professor|Prof\.?|Hafiz|Al-Hafiz|Qadi|Mawlana|Maulana|Ustadh|Ustaz|Sayyid)"
)
_EN_SPEECH = (
    r"(?:said|says|stated|states|wrote|writes|narrated|narrates|reported|reports|mentioned|mentions|"
    r"explained|explains|held|holds|argued|argues|commented|comments|opined|ruled|taught|"
    r"transmitted|related|relates|recorded|records|claimed|claims)"
)
_EN_ATTRIBUTIONS = (
    re.compile(rf"\b{_EN_HONORIFIC}\s+(?P<name>{_NAME_PART}(?:\s+{_NAME_PART}){{0,3}})"),
    re.compile(rf"\b(?P<name>(?:Ibn|Abu|Abi|Bint)\s+{_NAME_PART}(?:\s+{_NAME_PART}){{0,2}})"),
    re.compile(rf"\b(?P<name>{_NAME_PART}(?:\s+{_NAME_PART}){{1,3}})\s+(?:also\s+|further\s+)?{_EN_SPEECH}\b"),
)
# Capitalised words that start a sentence or name the Qur'an, God, a prophet
# or a tafsir work rather than a scholar.
_EN_NOT_NAMES = frozenset(
    "the this that these those in according allah god he she it they we his her their prophet messenger "
    "quran qur'an tafsir tafseer surah sura verse ayah ayat book lord almighty exalted most high sahih "
    "sunan musnad hadith muhammad jibril gabriel adam nuh noah ibrahim abraham musa moses isa jesus "
    "maryam mary yusuf joseph yaqub jacob dawud david sulayman solomon yunus jonah harun aaron ismail "
    "ishmael ishaq isaac lut lot hud salih shuayb ayyub job zakariyya yahya idris ilyas luqman "
    "dhul qarnayn pharaoh firawn iblis satan shaytan muslims believers people children israel "
    "companions sahabah ummah when while after before then and but also all some many one kursi throne "
    "fatiha fatihah baqarah baqara imran nisa maidah anam araf anfal tawbah kahf maryam ta ha yasin "
    "rahman mulk ikhlas falaq nas kawthar asr salah zakah hajj ramadan makkah madinah jannah".split()
)
_EN_PARTICLES = frozenset(
    "al el ad an ar as at az ibn bin bint abu abi abd abdul ul sheikh shaykh shaikh imam allamah allama "
    "mufti dr doctor professor prof hafiz qadi mawlana maulana ustadh ustaz sayyid islam".split()
)

_AR_HONORIFIC = re.compile(
    r"(?<![ء-ي])[وف]?(?:ال)?(?:شيخ|علامة|إمام|امام|حافظ|دكتور|مفتي|قاضي|أستاذ|استاذ|فقيه|محدث|مفسر)"
    r"(?![ء-ي])\s+(?P<rest>[^\[\].:؛،,؟!\n]{2,80})"
)
_AR_KUNYA = re.compile(
    r"(?<![ء-ي])[وف]?(?:قال|يقول|ذكر|روى|يرى|أورد|نقل|حكى|رأى|أكد|صرح|أشار|بين|بيّن|أفاد|يذكر|يروي)"
    r"\s+(?P<rest>(?:ابن|أبو|أبي|ابو|ابي)\s+[^\[\].:؛،,؟!\n]{2,60})"
)
_AR_NAME_STOP = frozenset(normalize_arabic(w) for w in (
    "إن أن ان إنه أنه إنها أنها في عن بأن بان رحمه قال يقول ذكر هذه هذا الآية على من إلى عند لأن "
    "حيث وهو وهي هو هي ما لا قد كما تعالى"
).split())
_AR_NOT_NAMES = frozenset(normalize_arabic(w) for w in "الله النبي رسول تعالى القرآن".split())
_AR_PARTICLES = frozenset(normalize_arabic(w) for w in "ابن أبو أبي بن".split())


def _arabic_name(rest: str, max_words: int = 3) -> str:
    words = []
    for w in rest.split():
        n = normalize_arabic(w)
        if not n or n in _AR_NAME_STOP or len(words) >= max_words:
            break
        words.append(w)
    return " ".join(words)


def _known_scholar(name: str) -> bool:
    return any(p.search(name) for _key, _names, pats in _SCHOLAR_PATTERNS for p in pats)


def find_attributed_names(sentence: str) -> List[str]:
    """Names a sentence attributes a statement to, outside SCHOLAR_NAMES."""
    out: List[str] = []
    for pat in _EN_ATTRIBUTIONS:
        for m in pat.finditer(sentence):
            toks = [t for t in re.split(r"[\s\-]+", m.group("name").strip(" -'’")) if t]
            while toks and toks[0].lower() in _EN_NOT_NAMES:
                toks.pop(0)
            distinctive = [t for t in toks if t.lower().strip("'’") not in _EN_PARTICLES
                           and t.lower() not in _EN_NOT_NAMES]
            name = " ".join(toks)
            if distinctive and not _known_scholar(name) and name not in out:
                out.append(name)
    for pat in (_AR_HONORIFIC, _AR_KUNYA):
        for m in pat.finditer(sentence):
            name = _arabic_name(m.group("rest"))
            norm = [w for w in normalize_arabic(name).split() if w not in _AR_PARTICLES]
            if not norm or all(w in _AR_NOT_NAMES for w in norm):
                continue
            if not _known_scholar(name) and name not in out:
                out.append(name)
    return out


def _chunk_metadata(chunk: object) -> str:
    return " ".join(filter(None, (
        str(getattr(chunk, f, "") or "") for f in
        ("source_name", "source_name_ar", "author", "author_name", "author_name_ar", "source_id")
    )))


def _name_supported(name: str, chunks: Sequence[object]) -> bool:
    """Every distinctive part of ``name`` appears in a cited chunk's text or metadata."""
    if re.search(r"[؀-ۿ]", name):
        parts = [_stem_ar(w) for w in normalize_arabic(name).split() if w not in _AR_PARTICLES and len(w) > 1]
        for c in chunks:
            hay = " ".join(_chunk_texts(c)) + " " + _chunk_metadata(c)
            words = {_stem_ar(w) for w in normalize_arabic(hay).split()}
            if parts and all(p in words for p in parts):
                return True
        return False
    parts = [t for t in _norm_en(name).split() if t not in _EN_PARTICLES and len(t) > 2]
    if not parts:
        return bool(chunks)
    for c in chunks:
        hay = f" {_norm_en(' '.join(_chunk_texts(c)) + ' ' + _chunk_metadata(c).replace('_', ' '))} "
        if all(f" {p} " in hay for p in parts):
            return True
    return False


# "All the scholars agree", "أجمع العلماء": a consensus claim needs a
# consensus statement in the cited evidence.
_CONSENSUS_CLAIM = re.compile(
    r"\b(all\s+(of\s+)?(the\s+)?scholars|the\s+scholars|scholars|the\s+ummah|all\s+(the\s+)?muslims|"
    r"all\s+(the\s+)?(mufassirun|commentators|exegetes))\s+(have\s+)?(unanimously\s+|all\s+)?"
    r"(agree|agreed|are\s+unanimous|were\s+unanimous|concur|concurred)\b"
    r"|\b(unanimous(ly)?|consensus|ijma['’]?)\b"
    r"|(أجمع|اجمع|أجمعت|اجمعت|اتفق|اتفقت)\s+(العلماء|الأمة|الامة|المفسرون|المسلمون|أهل\s+العلم|السلف)"
    r"|(?<![ء-ي])(إجماع|اجماع|بالإجماع|بالاجماع)(?![ء-ي])|لا\s+خلاف\s+بين",
    re.IGNORECASE,
)
_CONSENSUS_IN_SOURCE = re.compile(
    r"\b(consensus|unanimous\w*|agree\w*|ijma\w*|no\s+(disagreement|difference))\b"
    r"|أجمع|اجمع|إجماع|اجماع|اتفق|لا\s+خلاف",
    re.IGNORECASE,
)

# Promised benefits of reciting a verse ("whoever recites it will never be
# poor", "قراءتها سبعين مرة تشفي من كل داء") are a common fabrication. The
# benefit words and any count must be in one cited evidence text, near the
# rest of the claim.
_RECITATION_CUE = re.compile(
    r"\b(recit\w*|reads?\s+(it|this)|reading\s+(it|this)|whoever\s+(says|reads|recites))\b"
    r"|(?<![ء-ي])[وف]?(قرأ|قرأها|يقرأ|يقرؤها|قراءتها|قراءة|تلاها|تلاوتها|يتلوها|من\s+قال)(?![ء-ي])",
    re.IGNORECASE,
)
_BENEFIT = re.compile(
    r"\b(wealth\w*|rich\w*|poor|poverty|cur(e|es|ed|ing)|disease\w*|illness\w*|sick\w*|heal\w*|"
    r"guarantee\w*|protect\w*|forgiv\w*|paradise|jannah|debts?|jobs?|marriage|success\w*|rizq|"
    r"provision)\b"
    r"|(?<![ء-ي])[وف]?(شفاء|يشفي|تشفي|شفي|داء|مرض|الأمراض|الغنى|غني|يفتقر|فقر|الفقر|رزق|الرزق|الجنة|"
    r"يغفر|غفر|غفرت|ذنوب|الذنوب|ذنوبه|حساب|يحفظ|حفظ|حفظه|ديون|زواج)(?![ء-ي])",
    re.IGNORECASE,
)


def _benefit_supported(sentence: str, chunks: Sequence[object], cite_re: re.Pattern) -> bool:
    body = _strip_names(cite_re.sub(" ", sentence)).translate(_ARABIC_INDIC)
    body = _VERSE_REF.sub(" ", body)
    texts = _evidence_texts(chunks)
    if not texts:
        return False
    digits = set(re.findall(r"\d+", " ".join(texts).translate(_ARABIC_INDIC)))
    if any(n not in digits for n in re.findall(r"\d+", body)):
        return False
    b_en, b_ar = _seq(" ".join(m.group(0) for m in _BENEFIT.finditer(body)))
    for text in texts:
        s_en, s_ar = _seq(text)
        if set(b_en) <= set(s_en) and set(b_ar) <= set(s_ar):
            sup = evidence_support(body, [text])
            if sup.comparable and sup.local_coverage >= 0.6:
                return True
    return False


def verdict_supported(subject: str, chunks: Sequence[object], window: int = 40) -> bool:
    """
    True when the cited evidence itself says ``subject`` is permitted (each
    word of the subject within ``window`` tokens of a permission word).
    Pronoun subjects ("it is permissible") are never supported: the claim
    names nothing the evidence could be checked against.
    """
    s_en, s_ar = _seq(subject)
    if not s_en and not s_ar:
        return False
    perm_en = {_stem_en(w) for w in ("permitted", "permissible", "permission", "permits", "permit",
                                       "lawful", "halal", "allowed", "allow", "allows")}
    perm_ar = {_stem_ar(normalize_arabic(w)) for w in ("أحل", "أحلت", "حلال", "مباح", "يجوز", "جائز", "أباح",
                                                        "يحل", "تحل", "رخص", "رخصة")}
    for text in _evidence_texts(chunks):
        t_en, t_ar = _seq(text)
        for subj, src, perm in ((s_en, t_en, perm_en), (s_ar, t_ar, perm_ar)):
            if not subj:
                continue
            spots = [i for i, t in enumerate(src) if t in perm]
            if not spots:
                continue
            where = {}
            for j, t in enumerate(src):
                where.setdefault(t, []).append(j)
            if all(any(abs(i - j) <= window for i in spots for j in where.get(tok, ())) for tok in set(subj)):
                return True
    return False


def ruling_report_supported(
    claim: str, chunks: Sequence[object], min_coverage: float = 0.6, min_local: float = 0.5,
) -> bool:
    """
    True when the cited evidence itself states the ruling a sentence reports
    ("the verse tells you that you must not eat the property of orphans").
    The claim is scored with its reporting frame and the reader's address
    removed: what must be in the evidence is the content of the command.
    No comparable evidence (an English claim against Arabic-only text, or
    only planted instructions) is no support.
    """
    texts = _evidence_texts(chunks)
    if not texts:
        return False
    claim = _RULING_REPORT_NOISE.sub(" ", _strip_names(claim))
    sup = evidence_support(claim, texts)
    if not sup.comparable or not sup.tokens:
        return False
    return sup.coverage >= min_coverage and sup.local_coverage >= min_local


_RULING_REPORT_NOISE = re.compile(
    r"\b(you|your|yours|yourself|must|should|need|needs|ought|may|might|have|has|believers?|muslims?|"
    r"tells?|told|commands?|commanded|instructs?|instructed|teach(es)?|taught|orders?|ordered|urges?|"
    r"urged|enjoins?|enjoined|reminds?|reminded|warns?|warned|address(es)?|addressed|directs?|directed|"
    r"forbids?|forbade|requires?|obliges?|promises?|promised|instance|case)\b",
    re.IGNORECASE,
)


def _digits_supported(sentence: str, chunks: Sequence[object], cite_re: re.Pattern) -> bool:
    body = _VERSE_REF.sub(" ", cite_re.sub(" ", sentence).translate(_ARABIC_INDIC))
    numbers = re.findall(r"\d+", body)
    if not numbers:
        return True
    digits = set(re.findall(r"\d+", _chunk_text(chunks).translate(_ARABIC_INDIC)))
    return all(n in digits for n in numbers)


def check_named_attributions(
    answer: str,
    cited: Mapping[str, object],
    citation_pattern: str,
) -> Tuple[str, List[str]]:
    """
    Drop sentences whose attributions the cited evidence does not support.

    ``cited`` maps each VALID citation marker (exact text) to its chunk. The
    evidence for a sentence is the chunks it cites (or, for an uncited
    sentence, those its paragraph cites). A sentence is removed when:

    - it names a scholar on SCHOLAR_NAMES that is neither the cited work's
      author nor named in the cited text;
    - it attributes a statement to any other name (an honorific such as
      Sheikh/Imam/الشيخ/العلامة, an Ibn/Abu/ابن/أبو name, or a multi-word
      name before a speech verb) that the cited text and source metadata
      do not contain;
    - it reports a hadith the cited text does not carry (collection, number
      and wording, matched in one place of the text);
    - it claims scholarly consensus the cited text does not state;
    - it promises a benefit for reciting something ("whoever recites it will
      never be poor") that the cited text does not state;
    - it follows a hadith sentence and gives a number (a hadith number split
      off after "no.") the cited text does not contain.

    Returns (answer, removed_reasons).
    """
    cite_re = re.compile(citation_pattern)
    from app.services.tafsir_sources import source_base_id

    removed: List[str] = []
    paragraphs = re.split(r"(\n{2,})", answer)
    out_paragraphs = []
    for p_index, paragraph in enumerate(paragraphs):
        if p_index % 2 == 1:
            out_paragraphs.append(paragraph)
            continue
        para_chunks = [cited[m.group(0)] for m in cite_re.finditer(paragraph) if m.group(0) in cited]
        parts = _SENTENCE_SPLIT.split(paragraph)
        kept = []
        prev_hadith = False
        for i, part in enumerate(parts):
            if i % 2 == 1:
                kept.append(part)
                continue
            bare = cite_re.sub(" ", part)
            named = [(key, names) for key, names, pats in _SCHOLAR_PATTERNS
                     if any(p.search(part) for p in pats)]
            others = find_attributed_names(bare)
            hadith = bool(_HADITH_CUE.search(bare))
            consensus = bool(_CONSENSUS_CLAIM.search(bare))
            benefit = bool(_RECITATION_CUE.search(bare) and _BENEFIT.search(bare))
            follows_hadith = prev_hadith and bool(re.search(r"\d", _VERSE_REF.sub(" ", bare.translate(_ARABIC_INDIC))))
            prev_hadith = hadith
            if not (named or others or hadith or consensus or benefit or follows_hadith):
                kept.append(part)
                continue
            chunks = [cited[m.group(0)] for m in cite_re.finditer(part) if m.group(0) in cited]
            chunks = chunks or para_chunks
            ok = True
            if hadith and not _hadith_supported(part, chunks, cite_re):
                ok = False
                removed.append("hadith attribution")
            if follows_hadith and not hadith and not _digits_supported(part, chunks, cite_re):
                ok = False
                removed.append("hadith number")
            for key, names in named:
                own_work = key is not None and any(
                    source_base_id(getattr(c, "source_id", "")) == key for c in chunks
                )
                in_text = any(_mentioned_in(names, " ".join(_chunk_texts(c))) for c in chunks)
                if not (own_work or in_text):
                    ok = False
                    removed.append(names[0])
            for name in others:
                if not _name_supported(name, chunks):
                    ok = False
                    removed.append(name)
            if consensus and not any(_CONSENSUS_IN_SOURCE.search(t) for t in _evidence_texts(chunks)):
                ok = False
                removed.append("consensus claim")
            if benefit and not _benefit_supported(part, chunks, cite_re):
                ok = False
                removed.append("recitation benefit")
            if ok:
                kept.append(part)
        out_paragraphs.append("".join(kept))
    text = "".join(out_paragraphs)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return re.sub(r"[ \t]+\n", "\n", text).strip(), removed


# ------------------------------------------------ claim-to-evidence checks

# Text presented as what the Qur'an itself says, without a quotation:
# "In this verse Allah says that…", "يخبر الله تعالى أن…".
_QURAN_VOICE = re.compile(
    r"\b(allah|god|the\s+(holy\s+)?qur'?an|the\s+verse|this\s+verse|the\s+ayah|this\s+ayah|the\s+surah|"
    r"this\s+surah)\b[^.;\n]{0,40}?\b(says?|said|states?|declares?|tells\s+us|promises?|informs?\s+us|"
    r"commands?|reveals?)\b"
    r"|(?<![ء-ي])[وف]?(قال|يقول|أخبر|يخبر|وعد|يعد)\s+(الله|تعالى|سبحانه|ربنا)(?![ء-ي])"
    r"|في\s+(هذه\s+)?الآية\s+(يقول|يخبر|يعد)",
    re.IGNORECASE,
)


def has_quran_voice(text: str) -> bool:
    """True when the text presents something as what the Qur'an / Allah says."""
    return bool(_QURAN_VOICE.search(text or ""))


_QUOTED_SPANS = re.compile(r"﴿[^﴾]*﴾|«[^»]*»|“[^”]*”|\"[^\"\n]*\"")
_ORNATE = re.compile(r"﴿[^﴾]*﴾")


def _verses_covered(refs: Iterable[Tuple[int, int]], chunks: Sequence[object]) -> bool:
    for s, a in refs:
        for c in chunks:
            lo = getattr(c, "aya_start", None)
            hi = getattr(c, "aya_end", None) or lo
            if getattr(c, "sura_no", None) == s and lo is not None and lo <= a <= hi:
                return True
    return False


def check_quran_self_citations(
    answer: str,
    quran_markers: Mapping[str, Tuple[int, int, int]],
    tafsir_markers: Mapping[str, object],
    chunks: Sequence[object],
    citation_pattern: str,
    verse_texts: Optional[Mapping[Tuple[int, int], List[str]]] = None,
) -> Tuple[str, List[str]]:
    """
    Prose backed only by a Qur'an self-reference ("[Quran, 5:90]") is not
    evidence: the citation validator accepts any existing verse, so an
    invented claim could pass as paraphrase. A sentence is removed when:

    - all its citations are Qur'an self-references to verses no retrieved
      chunk covers, and it says more than a verified quotation (``﴿…﴾``
      quotations are checked separately against the canonical text);
    - it presents unquoted text as the Qur'an's own words ("Allah says
      that…") and that text is not carried by the stored translation or
      text of the cited verse, or by the retrieved tafsir of it.

    ``quran_markers`` maps valid Qur'an self-citation markers to
    (sura, first ayah, last ayah); ``tafsir_markers`` maps valid tafsir
    citation markers to their chunk; ``verse_texts`` holds the stored
    translations / canonical text per (sura, ayah).
    Returns (answer, removed_reasons).
    """
    cite_re = re.compile(citation_pattern)
    verse_texts = verse_texts or {}
    removed: List[str] = []
    parts = _SENTENCE_SPLIT.split(answer)
    out = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(part)
            continue
        markers = [m.group(0) for m in cite_re.finditer(part)]
        q_refs = [
            (s, a) for mk in markers if mk in quran_markers
            for s, a0, a1 in [quran_markers[mk]] for a in range(a0, a1 + 1)
        ]
        t_chunks = [tafsir_markers[mk] for mk in markers if mk in tafsir_markers]
        prose = _QUOTED_SPANS.sub(" ", cite_re.sub(" ", part))
        p_en, p_ar = _seq(prose)
        substantive = len(set(p_en)) + len(set(p_ar)) >= 3

        if q_refs and not t_chunks and substantive and not _verses_covered(q_refs, chunks):
            removed.append("uncovered Qur'an citation")
            continue

        if substantive and _QURAN_VOICE.search(prose) and not _QUOTED_SPANS.search(part):
            refs = q_refs or [
                (getattr(c, "sura_no", 0), a) for c in t_chunks
                for a in range(getattr(c, "aya_start", 0), (getattr(c, "aya_end", None) or getattr(c, "aya_start", 0)) + 1)
            ]
            pool = [t for ref in refs for t in verse_texts.get(ref, [])]
            covering = [c for c in chunks if _verses_covered(refs, [c])] if refs else []
            pool += _evidence_texts(covering + t_chunks)
            claim = _QURAN_VOICE.sub(" ", prose)
            sup = evidence_support(claim, pool)
            if not sup.comparable or sup.coverage < 0.6:
                removed.append("unverified Qur'an paraphrase")
                continue
        out.append(part)
    text = "".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return re.sub(r"[ \t]+\n", "\n", text).strip(), removed


def check_claim_support(
    answer: str,
    tafsir_markers: Mapping[str, object],
    citation_pattern: str,
    *,
    min_tokens: int = 4,
    drop_below: float = 0.25,
    weak_below: float = 0.5,
) -> Tuple[str, int, int]:
    """
    Claim-to-evidence relevance: a sentence citing a retrieved chunk must
    share its content words with that chunk. Only comparable text counts (an
    English sentence is not scored against an Arabic-only chunk).

    - coverage < ``drop_below`` (e.g. a claim about cryptocurrency cited to
      the tafsir of 94:5): the sentence is removed;
    - coverage < ``weak_below``: kept, but counted as weakly supported so the
      confidence score can be lowered;
    - every text of the cited chunks is a planted instruction: removed.

    Returns (answer, dropped, weak).
    """
    cite_re = re.compile(citation_pattern)
    dropped = weak = 0
    parts = _SENTENCE_SPLIT.split(answer)
    out = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(part)
            continue
        chunks = [tafsir_markers[m.group(0)] for m in cite_re.finditer(part) if m.group(0) in tafsir_markers]
        if not chunks:
            out.append(part)
            continue
        texts = _evidence_texts(chunks)
        has_text = any(getattr(c, f, None) for c in chunks for f in ("content", "content_ar", "content_en"))
        if has_text and not texts:
            dropped += 1
            continue
        claim = _strip_names(_ORNATE.sub(" ", cite_re.sub(" ", part)))
        sup = evidence_support(claim, texts)
        if sup.comparable and sup.tokens >= min_tokens:
            if sup.coverage < drop_below:
                dropped += 1
                continue
            if sup.coverage < weak_below:
                weak += 1
        out.append(part)
    text = "".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return re.sub(r"[ \t]+\n", "\n", text).strip(), dropped, weak


# ------------------------------------------------------------------ citations

_QURAN_SOURCE = re.compile(r"^\s*(the\s+)?(holy\s+)?(qur'?an|quran|koran|surah|sura|القرآن|القران|سورة)\b", re.IGNORECASE)


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


# Split on sentence ends and line breaks, keeping the separators. A full
# stop that ends a common abbreviation ("hadith no. 5010", "vol. 2", "e.g.")
# does not end the sentence: splitting there detached a hadith number from
# its hadith cue, so the number escaped the evidence check.
_ABBREVIATIONS = (
    r"(?<!\bno\.)(?<!\bNo\.)(?<!\bNO\.)(?<!\bnos\.)(?<!\bNos\.)(?<!\bvol\.)(?<!\bVol\.)"
    r"(?<!\bvols\.)(?<!\bp\.)(?<!\bpp\.)(?<!\bch\.)(?<!\bCh\.)(?<!\bcf\.)(?<!\bed\.)(?<!\bEd\.)"
    r"(?<!\bDr\.)(?<!\bdr\.)(?<!\bProf\.)(?<!\bSt\.)(?<!\bvs\.)(?<!\bal\.)(?<!\bet\.)"
    r"(?<!e\.g\.)(?<!i\.e\.)(?<!\bviz\.)(?<!\bapprox\.)(?<!\bhad\.)(?<!رقم\.)(?<!ج\.)(?<!ص\.)"
)
_SENTENCE_SPLIT = re.compile(r"(\n+|(?<=[.!?؟۔])" + _ABBREVIATIONS + r"[ \t]+)")


def split_sentences(text: str) -> List[str]:
    return [p for i, p in enumerate(_SENTENCE_SPLIT.split(text or "")) if i % 2 == 0 and p.strip()]


def drop_unsupported_sentences(answer: str, invalid_markers: Iterable[str], citation_pattern: str) -> str:
    """
    Remove sentences whose only citations were rejected; elsewhere just strip
    the rejected markers. A claim attributed to a source that was not
    retrieved must not survive as unattributed text.
    """
    invalid = set(invalid_markers)
    if not invalid:
        return answer
    cite_re = re.compile(citation_pattern)
    parts = _SENTENCE_SPLIT.split(answer)
    out = []
    for i, part in enumerate(parts):
        if i % 2 == 1:  # separator
            out.append(part)
            continue
        markers = [m.group(0) for m in cite_re.finditer(part)]
        bad = [m for m in markers if m in invalid]
        if bad and len(bad) == len(markers):
            continue  # every citation in this sentence was rejected
        out.append(strip_citation_markers(part, bad) if bad else part)
    text = "".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return re.sub(r"[ \t]+\n", "\n", text).strip()


def drop_uncited_paragraphs(answer: str, citation_pattern: str, min_length: int = 100) -> Tuple[str, int]:
    """
    Every substantive paragraph must carry a citation (system prompt rule 3).
    Paragraphs of ``min_length``+ characters without one are removed.
    """
    cite_re = re.compile(citation_pattern)
    parts = re.split(r"(\n{2,})", answer)
    out, dropped = [], 0
    for i, part in enumerate(parts):
        if i % 2 == 0 and len(part.strip()) >= min_length and not cite_re.search(part):
            dropped += 1
            continue
        out.append(part)
    text = re.sub(r"\n{3,}", "\n\n", "".join(out))
    return text.strip(), dropped


def contains_fiqh_disclaimer(answer: str) -> bool:
    low = (answer or "").lower()
    return "fatwa" in low or "فتوى" in low or "الفتوى" in low
