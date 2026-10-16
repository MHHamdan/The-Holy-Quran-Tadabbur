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
3. Shared lexical primitives for the sentence-level claim guard
   (app.safety.claim_guard): Arabic normalisation, hadith and Qur'an-voice
   cues, same-script evidence support.
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
    r"(قال الله تعالى|قال الله عز وجل|قال تعالى|يقول الله تعالى|يقول تعالى|قوله تعالى|قال الله سبحانه|قال الله"
    r"|قال جل وعلا|قال عز وجل|يقول الحق سبحانه|يقول الحق|قال سبحانه|يقول سبحانه"
    r"|(?:في|وفي|كما في|جاء في|ورد في|كما جاء في)\s+(?:محكم التنزيل|التنزيل|الذكر الحكيم|كتاب الله|القرآن الكريم"
    r"|الكتاب العزيز|القرآن)(?:\s+قوله(?:\s+تعالى)?)?)"
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


# ----------------------------------------------------- names and hadith cues


def _name_pattern(name: str) -> re.Pattern:
    if re.search(r"[؀-ۿ]", name):
        body = re.escape(name).replace(r"\ ", r"\s+")
        return re.compile(rf"(?<![ء-ي])[وفبل]?{body}(?![ء-ي])")
    body = re.escape(name).replace(r"\ ", r"[\s-]+").replace("'", "['’ʿ]?")
    return re.compile(rf"\b(?:al[\s-]|as[\s-]|at[\s-]|ar[\s-])?{body}\b", re.IGNORECASE)


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
    "ثم أو مع بن ابن أبي أبو تعالى سبحانه الآية آية الآيات عز وجل يعني أي معنى المعنى تفسير "
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
        # A stop word with a conjunction ("وعن", "فإن") is still a stop word.
        if len(t) > 2 and t not in _AR_STOP and not (t[:1] in "وف" and t[1:] in _AR_STOP):
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


# ------------------------------------------------------------ Qur'an voice

# Something presented as what the Qur'an itself says: a Qur'an-referring
# noun (Allah, the Lord, the Qur'an, the Book, revelation, the verse/ayah/
# surah/passage) with a speech/text predicate, a prepositional cue ("according
# to this ayah", "in the words of the Qur'an", "as the verse puts it"), or the
# Arabic equivalents (قال تعالى، يقول الحق، أخبر القرآن، تخبرنا الآية، في محكم
# التنزيل، كما في كتاب الله، قوله تعالى).
_DIVINE_NOUN_EN = r"(allah|god|the\s+lord|(our|your)\s+lord|the\s+almighty|the\s+exalted|the\s+most\s+high)"
_DIVINE_SPEECH_EN = (
    r"(says?|said|states?|stated|declares?|declared|tells?\s+us|told\s+us|informs?(\s+us)?|promises?|promised|"
    r"warns?|warned|proclaims?|announces?|puts\s+it|speaks\s+of|addresses|reveals?|revealed\s+that|mentions?)"
)
_QURAN_NOUN_EN = (
    r"(the\s+(holy\s+|noble\s+|glorious\s+|sacred\s+)?(qur'?an|koran|book|scripture|revelation)|revelation|"
    r"scripture|the\s+verse|this\s+verse|that\s+verse|the\s+ayah|this\s+ayah|that\s+ayah|the\s+surah|"
    r"this\s+surah|the\s+passage|this\s+passage|the\s+divine\s+(word|text|speech))"
)
_QURAN_PRED_EN = (
    r"(says?|said|states?|stated|declares?|declared|tells?(\s+us)?|told\s+us|promises?|promised|informs?(\s+us)?|"
    r"commands?|commanded|reveals?|revealed\s+that|teach(es)?|taught|mentions?|mentioned|shows?|affirms?|"
    r"confirms?|establishes|proclaims?|warns?|reads?|puts\s+it|announces?|assures?(\s+us)?|makes\s+(it\s+)?"
    r"clear|indicates?|guarantees?|decrees?|ordains?|explains?|describes?|speaks\s+of|calls?|"
    r"is\s+(clear|explicit|plain)(\s+that)?)"
)
_QURAN_VOICE = re.compile(
    rf"\b{_QURAN_NOUN_EN}\s+((also|itself|clearly|plainly|explicitly|here|then|further|even|"
    rf"indeed|truly|thus)\s+){{0,2}}{_QURAN_PRED_EN}\b"
    rf"|\b{_DIVINE_NOUN_EN}\s+(\w+\s+){{0,2}}{_DIVINE_SPEECH_EN}\b"
    r"|\b(according\s+to|in\s+the\s+words\s+of|as\s+(stated|mentioned|said|written|declared)\s+in|"
    r"in\s+the\s+language\s+of)\s+(the\s+|this\s+|that\s+)?(holy\s+|noble\s+)?(qur'?an|verse|ayah|surah|"
    r"book|revelation|lord|allah|scripture)\b"
    r"|\b(qur'?an|qur'?anic|divine)\s+(words|text|statement|declaration|wording)\b"
    r"|(?<![ء-ي])[وف]?(قال|يقول|أخبر|يخبر|وعد|يعد|قرر|يقرر|نص|ينص|أكد|يؤكد|ذكر|يذكر|بين|يبين|أمر|يأمر|"
    r"تخبر|تخبرنا|يخبرنا|أخبرنا|تقرر|تنص|تؤكد|تبين|تذكر|تعلمنا|يعلمنا|تقول)\s+(الله|تعالى|سبحانه|ربنا|ربك|"
    r"الحق|المولى|القرآن|القران|الآية|الاية|هذه\s+الآية|هذه\s+الاية|التنزيل|السورة|الكتاب)(?![ء-ي])"
    r"|(?<![ء-ي])(في|وفي|كما\s+في|جاء\s+في|ورد\s+في|كما\s+جاء\s+في|نص)\s+(محكم\s+التنزيل|التنزيل|"
    r"الذكر\s+الحكيم|كتاب\s+الله|القرآن\s+الكريم|الكتاب\s+العزيز|القرآن|القران)(?![ء-ي])"
    r"|(?<![ء-ي])(قوله\s+تعالى|قوله\s+سبحانه|قوله\s*[:：]|قال\s+جل\s+وعلا|قال\s+عز\s+وجل|"
    r"يقول\s+الحق|قال\s+الحق)"
    r"|في\s+(هذه\s+)?الآية\s+(يقول|يخبر|يعد)",
    re.IGNORECASE,
)


def has_quran_voice(text: str) -> bool:
    """True when the text presents something as what the Qur'an / Allah says."""
    return bool(_QURAN_VOICE.search(text or ""))


_QUOTED_SPANS = re.compile(r"﴿[^﴾]*﴾|«[^»]*»|“[^”]*”|\"[^\"\n]*\"")


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


def drop_uncited_paragraphs(
    answer: str, citation_pattern: str, min_length: int = 100, keep=None,
) -> Tuple[str, int]:
    """
    Every substantive paragraph must carry a citation (system prompt rule 3).
    Paragraphs of ``min_length``+ characters without one are removed, unless
    ``keep(paragraph)`` says the paragraph makes no claim (e.g. a labelled
    reflection prompt, whose sentences the claim guard has already checked).
    """
    cite_re = re.compile(citation_pattern)
    parts = re.split(r"(\n{2,})", answer)
    out, dropped = [], 0
    for i, part in enumerate(parts):
        if i % 2 == 0 and len(part.strip()) >= min_length and not cite_re.search(part) \
                and not (keep and keep(part)):
            dropped += 1
            continue
        out.append(part)
    text = re.sub(r"\n{3,}", "\n\n", "".join(out))
    return text.strip(), dropped


def contains_fiqh_disclaimer(answer: str) -> bool:
    low = (answer or "").lower()
    return "fatwa" in low or "فتوى" in low or "الفتوى" in low
