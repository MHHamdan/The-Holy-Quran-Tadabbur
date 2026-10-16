"""
Sentence-level claim typing and per-type grounding for generated answers.

Every sentence of a generated answer is typed by the claims it makes, and
each claim type has its own grounding rule against the retrieved evidence
(the cited chunks' text and metadata, plus the stored text and English
translations of the verses those chunks explain):

=================  =========================================================
claim type         rule
=================  =========================================================
ruling             personal verdicts (to the reader, by the answer itself)
                   and takfir are never allowed: the whole answer is
                   withheld with the fatwa notice. A general ruling stands
                   only when the cited evidence states the same deontic
                   class (permitted / forbidden / obligatory / valid) about
                   the same subject; otherwise the answer is withheld.
attribution        every named person or work must be the author/work of a
                   retrieved chunk or be named in the cited text (bilingual
                   registry + transliteration). Collective claims
                   (consensus, majority, disagreement) need the evidence to
                   state that agreement or disagreement.
hadith / benefit   the evidence must carry a narration, every number and
                   collection named, and the reported content in one place.
quran claim        "the Qur'an / Allah / the verse says…" prose must be
                   carried by the text or English translation of a cited
                   retrieved verse (or its covering tafsir).
reference          loose or malformed references (bare "[2:153]", "(Ibn
                   Kathir 3:103)", vol./page, "[source: X]") and numbers the
                   evidence does not contain are not evidence.
synthesis          ordinary paraphrase must share its content with the cited
                   evidence; across scripts only a clear mismatch (content
                   the evidence does not carry at all) is removed.
=================  =========================================================

Instructions planted in evidence (see evidence_injection) never count as
support, and a sentence that repeats one is removed.

Cross-lingual checks (English answer, Arabic evidence) go through
xling.support(): verse translations, a lexicon learned from the parallel
Qur'an corpus, and transliteration. High-risk types fail closed when the
evidence cannot carry the claim; ordinary synthesis fails open unless the
claim is clearly foreign to the evidence.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Iterable, List, Mapping, Optional, Sequence, Set, Tuple

from app.safety import attribution as attr
from app.safety.evidence_injection import is_injected, split_tainted
from app.safety.grounding import (
    normalize_arabic,
    _ARABIC_INDIC,
    _HADITH_COLLECTIONS,
    _HADITH_CUE,
    _MUSLIM_AS_COLLECTOR,
    _AHMAD_AS_COLLECTOR,
    _PROPHET_IN_SOURCE,
    _QUOTED_SPANS,
    _SENTENCE_SPLIT,
    _mentioned_in,
    _name_pattern,
    has_quran_voice,
)
from app.safety.ruling_intent import (
    FIRST,
    FORBID,
    OBLIGE,
    PERMIT,
    SECOND,
    STATUS,
    RulingClaim,
    evidence_states_class,
    ruling_claims,
)
from app.safety import xling
from app.safety.xling import EvidenceView, Lexicon, Support

_log = logging.getLogger(__name__)

# Thresholds (local-window coverage of a claim's content by the evidence).
HIGH_RISK_SUPPORT = 0.6
ATTRIBUTED_QURAN_SUPPORT = 0.4
RULING_SUBJECT_SUPPORT = 0.5
SYNTHESIS_DROP = 0.3
CROSS_LINGUAL_SYNTHESIS_DROP = 0.2
SYNTHESIS_WEAK = 0.5
CROSS_LINGUAL_REASON = 0.25
# A synthesis sentence that carries its own valid citation is anchored to
# that evidence: across scripts it is judged by the citation (and every
# high-risk check before it), and dropped only when almost nothing of it is
# carried; in the evidence's script a run of three carried content words
# anchors the rest of the sentence as the writer's framing.
ANCHORED_CROSS_LINGUAL_DROP = 0.1
ANCHORED_SAME_SCRIPT_DROP = 0.2
ANCHOR_TOKENS = 3
# A reported narration paraphrased in the evidence's own script: most of its
# content words in one place (or a verbatim run of three plus over half).
REPORT_SAME_SCRIPT = 0.85
REPORT_SAME_SCRIPT_NGRAM = 0.65
MIN_CLAIM_TOKENS = 3

WITHHOLD_FATWA = "fatwa"


@dataclass
class ClaimReport:
    removed: List[Tuple[str, str]] = field(default_factory=list)   # (claim type, detail)
    withheld: Optional[Tuple[str, str]] = None                     # (kind, detail)
    weak: int = 0
    injected_chunks: List[str] = field(default_factory=list)

    @property
    def removed_count(self) -> int:
        return len(self.removed)


# ------------------------------------------------------------------- cues

_EXTRA_HADITH_CUE = re.compile(
    r"\b(narrations?|narrated|narrator|traditions?|it\s+is\s+(reported|related|narrated|transmitted)|"
    r"(a|one|another|the|sound|authentic|weak|famous)\s+(report|tradition|narration)|athar|isnad|"
    r"reported\s+that\s+the\s+prophet)\b"
    # "حديث" alone also means "discourse" (حديث القرآن عن التوحيد): only
    # narration forms and "in the hadith".
    r"|(?<![ء-ي])[وف]?(الأثر|الاثر|يروى|يُروى|روي|رُوي|ورد\s+أن|جاء\s+في\s+(الحديث|الأثر|الخبر)|"
    r"(في|وفي)\s+(ال)?(حديث|أثر|خبر)|الحديث\s+(الشريف|الصحيح|النبوي)|حديث\s+(صحيح|حسن|ضعيف|نبوي|شريف)|"
    r"برقم|رقم\s+الحديث)(?![ء-ي])",
    re.IGNORECASE,
)
# A hadith claim reports what the Prophet ﷺ said or did, or cites a
# narration; merely naming him ("as the Prophet ﷺ brought it") is not one.
# A named authority's own words or opinion: "X said / held / explained /
# interpreted…", "قال/نقل عن/فسرها X…".
_SPEECH_FRAME = re.compile(
    r"\b(said|says|stated|states|held|holds|explained|explains|interpreted|interprets|understood|commented|"
    r"argued|wrote|narrated|reported|read\s+it|recited|opined|maintained|viewed)\b"
    r"|(?<![ء-ي])[وف]?(قال|يقول|نقل|ينقل|فسر|فسرها|فسره|يرى|رأى|ذهب|روى|حكى|عن)(?![ء-ي])",
    re.IGNORECASE,
)
_SPEAKER_CLAUSES = re.compile(r"\s*[،,;؛]\s*(?=(?:و|ف)?(?:عن|قال|نقل|روى|ذكر)\b|\s*(?:while|and)\s+[A-Z])"
                              r"|\s+(?=(?:وعن|وقال|ونقل|وروى)\s)")
_HADITH_REPORT = re.compile(
    r"\b(the\s+)?(prophet|messenger(\s+of\s+(allah|god))?|rasul\s*allah|rasulullah)\b"
    r"(?!\s+(of|musa|moses|ibrahim|abraham|yusuf|joseph|nuh|noah|isa|jesus|yunus|jonah|sulayman|solomon|"
    r"dawud|david|ayyub|job|hud|salih|lut|lot|harun|aaron))"
    r"\s*(\(\s*(pbuh|saw|saws|s\.a\.w\.?)\s*\)|ﷺ)?\s*((?!(?:was|were|is|are|been|being|had|has)\b)\w+\s+)?"
    r"(said|says|stated|taught|told|declared|instructed|"
    r"commanded|forbade|prohibited|used\s+to|would\s+(say|recite|pray)|is\s+reported|was\s+reported|"
    r"reportedly|asked|replied|answered|recited|promised|warned|advised)\b"
    r"|\bhadiths?\b|\b(sunan|sahih|musnad|jami['’]?)\b"
    r"|(?<![ء-ي])[وف]?(قال|يقول|كان|سئل|سأل|أمر|نهى|أخبر)\s+(النبي|رسول\s+الله)(?![ء-ي])"
    r"|(النبي|رسول\s+الله)\s*(ﷺ|صلى\s+الله\s+عليه\s+وسلم)?\s*(قال|يقول|كان\s+يقول|كان\s+يقرأ|أمر|نهى|سئل|سأل)(?![ء-ي])"
    r"|(?<![ء-ي])[وف]?(رواه|أخرجه|اخرجه|خرجه|روى|يرويه|أحاديث)(?![ء-ي])",
    re.IGNORECASE,
)
_BENEFIT_CLAIM = re.compile(
    r"\b(recit\w*|read(s|ing)?\s+(it|this|the\s+verse)|whoever\s+(says|reads|recites|writes)|"
    r"listening\s+to\s+(it|this))\b[^.\n]{0,80}\b(cur\w*|heal\w*|treat\w*|guarantee\w*|protect\w*|"
    r"wealth\w*|rich\w*|poor|poverty|debts?|success\w*|pass\w*|marri\w*|job|jobs|disease\w*|illness\w*|"
    r"sick\w*|never|will\s+be|forgiv\w*|paradise|reward\w*)\b"
    r"|\b(proven|guaranteed|certain|definite)\s+(cure|treatment|remedy|protection|way|method)\b"
    r"|\bguarantees?\s+(success|wealth|health|protection|marriage|paradise)\b"
    r"|(?<![ء-ي])[وف]?(من\s+قرأ|من\s+قال|من\s+كتب|قراءتها|قراءة\s+(هذه|الآية)|تلاوتها)[^.\n]{0,80}"
    r"(شفي|يشفى|تشفي|يشفي|شفاء|غني|الغنى|يفتقر|رزق|حفظ|يحفظ|لم\s+يمرض|لا\s+يمرض|الجنة|غفر|يغفر|نجح|زواج)",
    re.IGNORECASE,
)
_REVELATION_CLAIM = re.compile(
    r"\b(was|were|is)\s+(revealed|sent\s+down|brought\s+down)\s+(about|after|before|in|concerning|regarding|when|"
    r"during|at|on|for)\b|\b(came|come|comes)\s+down\s+(about|after|during|when|in|on|concerning)\b"
    r"|\boccasion\s+of\s+revelation\b|\basbab\b"
    r"|(?<![ء-ي])[وف]?(نزلت|نزل|أنزلت|انزلت)\s+(في|بعد|قبل|عند|يوم|حين|لما|بسبب)(?![ء-ي])|سبب\s+النزول",
    re.IGNORECASE,
)
_REVELATION_IN_SOURCE = re.compile(r"نزل|أنزل|انزل|سبب|\brevealed\b|\brevelation\b", re.IGNORECASE)
_REFLECTION_LABEL = re.compile(
    r"^\s*(\*\*)?\s*(reflection|for\s+reflection|reflect|to\s+reflect|a\s+moment\s+of\s+reflection|"
    r"food\s+for\s+thought|questions?\s+for\s+reflection|للتأمل|تأمل|تأمّل|وقفة\s+تأمل|وقفة\s+تأملية|"
    r"سؤال\s+للتأمل|أسئلة\s+للتأمل)\s*(\*\*)?\s*[:：\-–—]",
    re.IGNORECASE,
)
# Reference-like text that is not a valid citation marker.
_LOOSE_REFS = re.compile(
    r"\[[^\[\]\n]*[0-9٠-٩][^\[\]\n]*\]"                                # [2:153], [Ibn Kathir 2:153]
    r"|[<{【⟨〈«][^<>{}【】⟨⟩〈〉«»\n]*[0-9٠-٩]{1,3}\s*[:/]\s*[0-9٠-٩]{1,3}[^<>{}【】⟨⟩〈〉«»\n]*[>}】⟩〉»]"
    r"|\[\s*(source|sources|ref|reference|المصدر|مصدر)\s*[:：][^\]]*\]"  # [source: X]
    r"|\((?=[^()\n]*[A-Za-zء-ي])[^()\n]*\d{1,3}\s*[:/]\s*\d{1,3}[^()\n]*\)"
    r"|\((?=[^()\n]*[A-Za-zء-ي])[^()\n]*[٠-٩]{1,3}\s*[:/]\s*[٠-٩]{1,3}[^()\n]*\)"
    r"|\b(vol(ume)?|v)\.?\s*\d+|\bp(p|age)?\.\s*\d+|\bpage\s+\d+"
    r"|(?<![ء-ي])(ج|جزء|الجزء)\s*[٠-٩0-9]+|(?<![ء-ي])(ص|صفحة|الصفحة)\s*[٠-٩0-9]+"
    r"|[—–]\s*(tafsir|ibn|al-|imam|تفسير|ابن)[^.\n]{0,40}\d",
    re.IGNORECASE,
)
_BRACKETED_NAME_ONLY = re.compile(r"\[\s*[^\[\]\n,،\d٠-٩]{3,40}\s*\]")
_VERSE_REF = re.compile(r"(?<![\d:])(\d{1,3})\s*:\s*(\d{1,3})(?:\s*[-–]\s*(\d{1,3}))?(?![\d:])")
_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")


# Number words (three and up: "one", "two" also mean "a", "both").
_NUMBER_WORDS = {
    "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
    "eighty": 80, "ninety": 90, "hundred": 100, "thousand": 1000,
    "ثلاث": 3, "ثلاثة": 3, "ثلاثه": 3, "أربع": 4, "اربع": 4, "أربعة": 4, "اربعه": 4, "خمس": 5, "خمسة": 5,
    "سبع": 7, "سبعة": 7, "سبعه": 7, "ثمان": 8, "ثمانية": 8, "تسع": 9, "تسعة": 9, "عشرة": 10, "عشره": 10,
    "عشرين": 20, "عشرون": 20, "ثلاثين": 30, "ثلاثون": 30, "أربعين": 40, "اربعين": 40, "أربعون": 40,
    "خمسين": 50, "خمسون": 50, "ستين": 60, "سبعين": 70, "سبعون": 70, "ثمانين": 80, "تسعين": 90,
    "مائة": 100, "مئة": 100, "مائه": 100, "ألف": 1000, "الف": 1000,
}
_NUMBER_WORD_RE = re.compile(
    r"(?<![\w\u0621-\u064a])[وفب]?(" + "|".join(sorted(map(re.escape, _NUMBER_WORDS), key=len, reverse=True))
    + r")(?![\w\u0621-\u064a])", re.IGNORECASE)


def _spell_numbers(text: str) -> str:
    return _NUMBER_WORD_RE.sub(lambda m: " " + str(_NUMBER_WORDS[m.group(1).lower()]) + " ", text or "")


def _digits(text: str) -> str:
    return (text or "").translate(_ARABIC_INDIC)


# ------------------------------------------------------------------ guard

class ClaimGuard:
    """
    Check an answer sentence by sentence.

    ``chunks``: retrieved chunks; ``cited``: valid citation marker -> chunk;
    ``quran_markers``: valid Qur'an self-citation marker -> (sura, a0, a1);
    ``verse_texts``: (sura, aya) -> stored English translations and
    canonical text; ``lexicon``: cross-lingual lexicon (may be empty).
    """

    def __init__(
        self,
        chunks: Sequence[object],
        cited: Mapping[str, object],
        quran_markers: Mapping[str, Tuple[int, int, int]],
        citation_pattern: str,
        verse_texts: Optional[Mapping[Tuple[int, int], List[str]]] = None,
        lexicon: Optional[Lexicon] = None,
        language: str = "en",
        question: str = "",
        parallel: Optional[Mapping[str, List[str]]] = None,
    ):
        self.cite_re = re.compile(citation_pattern)
        self.language = language
        self.verse_texts = verse_texts or {}
        # chunk_id -> the same work's edition in the other language for the
        # same verses (e.g. Ibn Kathir in English for an Arabic Ibn Kathir
        # chunk): the tafsir's own wording in the answer's language.
        self.parallel = {k: [split_tainted(t)[0] for t in v if t and split_tainted(t)[0].strip()]
                         for k, v in (parallel or {}).items()}
        self.lexicon = lexicon or Lexicon()
        # Instructions planted in evidence: each chunk text is split into its
        # ordinary part (still evidence) and the part an instruction controls
        # (the instruction and its payload: never evidence).
        self._clean_text: dict = {}
        self.tainted: List[str] = []
        self.injected = []
        for c in chunks:
            hit = False
            for t in self._all_texts(c):
                clean, taint = split_tainted(t)
                self._clean_text[t] = clean
                if taint:
                    hit = True
                    # Sentence by sentence: an instruction in one script
                    # appended to text in another is read in its own script.
                    self.tainted.extend(u for u in re.split(r"(?<=[.!?؟؛;\n])\s*", taint) if u.strip())
            if hit:
                self.injected.append(c)
        # A chunk is usable evidence while some ordinary text remains in it.
        self.clean = [c for c in chunks if any(re.search(r"\w", t) for t in self._raw_texts(c))]
        self.cited = dict(cited)
        self.quran_markers = dict(quran_markers)
        self.report = ClaimReport(injected_chunks=[getattr(c, "chunk_id", "") for c in self.injected])
        # Topic words of the question and every word the retrieved evidence
        # carries (any script, through the lexicon).
        self.topic: Set[str] = set()
        self.pool_tokens: Set[str] = set()
        if question:
            all_view = self._view(self._texts(self.clean))
            words = re.findall(r"[A-Za-z][A-Za-z'’-]+|[\u0621-\u064a]+", question)
            for w in words:
                toks = xling.claim_tokens(w)[1]
                if not toks:
                    continue
                self.topic.add(toks[0])
                if xling.support(w, all_view).local:
                    self.pool_tokens.add(toks[0])

    # ------------------------------------------------------------ evidence
    @staticmethod
    def _all_texts(chunk: object) -> List[str]:
        out = []
        for f in ("content", "content_ar", "content_en"):
            t = getattr(chunk, f, None)
            if t and t not in out:
                out.append(t)
        return out

    def _raw_texts(self, chunk: object) -> List[str]:
        """The chunk's texts with any planted instruction and its payload cut out."""
        out = []
        for t in self._all_texts(chunk):
            clean = self._clean_text.get(t)
            if clean is None:
                clean = split_tainted(t)[0]
                self._clean_text[t] = clean
            if clean and clean.strip() and clean not in out:
                out.append(clean)
        return out

    def _clean_chunks(self, chunks: Iterable[object]) -> List[object]:
        ok = {id(c) for c in self.clean}
        return [c for c in chunks if id(c) in ok]

    def _verses(self, chunks: Iterable[object]) -> List[Tuple[int, int]]:
        out = []
        for c in chunks:
            s = getattr(c, "sura_no", None)
            a0 = getattr(c, "aya_start", None)
            a1 = getattr(c, "aya_end", None) or a0
            if s is None or a0 is None:
                continue
            for a in range(a0, min(a1, a0 + 30) + 1):
                if (s, a) not in out:
                    out.append((s, a))
        return out

    def _texts(self, chunks: Sequence[object], refs: Sequence[Tuple[int, int]] = (),
               verses: bool = True) -> List[str]:
        """Clean evidence texts of ``chunks`` and (``verses``) the stored text
        and translations of the verses they explain."""
        out: List[str] = []
        for c in self._clean_chunks(chunks):
            for t in self._raw_texts(c) + self.parallel.get(getattr(c, "chunk_id", ""), []):
                if t not in out:
                    out.append(t)
        if not verses:
            return out
        for ref in list(refs) + self._verses(chunks):
            for t in self.verse_texts.get(ref, []):
                if t not in out:
                    out.append(t)
        return out

    def _verse_primary(self, ref: Tuple[int, int]) -> List[str]:
        """The verse itself: its canonical Arabic text and its primary stored
        English translation (Saheeh International, listed first) — not the
        glossed editions whose parenthetical commentary is not the verse."""
        texts = self.verse_texts.get(ref, [])
        english = [t for t in texts if not re.search(r"[ء-ي]", t)]
        arabic = [t for t in texts if re.search(r"[ء-ي]", t)]
        return english[:1] + arabic

    def _view(self, texts: Sequence[str]) -> EvidenceView:
        return EvidenceView.of(texts, self.lexicon)

    # ------------------------------------------------------------- driver
    def check(self, answer: str) -> Tuple[str, ClaimReport]:
        paragraphs = re.split(r"(\n{2,})", answer or "")
        out_paragraphs: List[str] = []
        for p_index, paragraph in enumerate(paragraphs):
            if p_index % 2 == 1:
                out_paragraphs.append(paragraph)
                continue
            para_chunks = [self.cited[m.group(0)] for m in self.cite_re.finditer(paragraph) if m.group(0) in self.cited]
            reflection = bool(_REFLECTION_LABEL.match(paragraph))
            parts = _SENTENCE_SPLIT.split(paragraph)
            kept: List[str] = []
            prev_hadith = False
            for i, part in enumerate(parts):
                if i % 2 == 1:
                    kept.append(part)
                    continue
                if not part.strip():
                    kept.append(part)
                    continue
                verdict, prev_hadith = self._judge(part, para_chunks, reflection, prev_hadith)
                if self.report.withheld:
                    return answer, self.report
                if verdict is None:
                    kept.append(part)
                else:
                    self.report.removed.append(verdict)
            out_paragraphs.append("".join(kept))
        text = "".join(out_paragraphs)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return re.sub(r"[ \t]+\n", "\n", text).strip(), self.report

    # -------------------------------------------------------------- judge
    def _judge(self, part: str, para_chunks: List[object], reflection: bool,
               prev_hadith: bool) -> Tuple[Optional[Tuple[str, str]], bool]:
        markers = [m.group(0) for m in self.cite_re.finditer(part)]
        own = [self.cited[m] for m in markers if m in self.cited]
        q_refs = [(s, a) for m in markers if m in self.quran_markers
                  for s, a0, a1 in [self.quran_markers[m]] for a in range(a0, a1 + 1)]
        chunks = own or para_chunks
        bare = self.cite_re.sub(" ", part)
        if reflection:
            bare = _REFLECTION_LABEL.sub(" ", bare)
        prose = _QUOTED_SPANS.sub(" ", bare)
        prose_ar_quotes_kept = bare
        texts = self._texts(chunks, q_refs)

        # Citations that point only at planted instructions.
        if own and not self._clean_chunks(own):
            if ruling_claims(prose):
                self.report.withheld = (WITHHOLD_FATWA, "ruling cited to planted instructions")
            return ("injection", "cites planted instructions"), False

        # 1. Planted instructions repeated by the answer.
        if self.injected and self._echoes_injection(prose, chunks):
            # A planted ruling in any wording ("absolutely prohibited in
            # every circumstance"): the whole answer is withheld, so no
            # citation-backed fragment of it can survive beside a disclaimer.
            from app.safety.quran_answer_guard import QuranAnswerGuard
            if ruling_claims(prose) or QuranAnswerGuard.has_ruling_vocabulary(prose) \
                    or xling.deontic_classes(prose):
                self.report.withheld = (WITHHOLD_FATWA, "ruling planted in evidence")
            return ("injection", "repeats planted instruction"), False

        # A question inside a paragraph labelled as reflection ("Reflection:
        # would it be right to…?") invites the reader to think; it asserts
        # nothing, so it states no ruling and needs no support.
        if reflection and _is_question(prose):
            return None, False

        # 2. Rulings. A ruling quoted word for word from the cited evidence
        #    ("…فرض الله عليكم الصيام" copied from the tafsir) is the
        #    source's statement, not the answer issuing one.
        for claim in ruling_claims(prose):
            if claim.cls != STATUS and self._verbatim_claim(claim, prose, chunks):
                continue
            v = self._judge_ruling(claim, chunks, texts, q_refs)
            if v:
                self.report.withheld = (WITHHOLD_FATWA, v)
                return (("ruling", v)), False

        # 3. Loose / malformed references and unretrieved verses.
        v = self._judge_references(bare, chunks, own, q_refs)
        if v:
            return ("reference", v), False

        # 4. Attributions: persons and works.
        persons = attr.find_person_names(bare)
        for name in persons:
            if not self._name_ok(name, chunks, texts):
                return ("attribution", name), False
        # What a named authority other than the cited work's author said
        # ("Ibn Abbas said…", "وقال مجاهد…") must be what the evidence reports.
        if chunks and any(attr.registry_key(n) is None for n in persons) and _SPEECH_FRAME.search(bare):
            originals = [t for c in self._clean_chunks(chunks) for t in self._raw_texts(c)]
            for clause in _SPEAKER_CLAUSES.split(prose):
                speakers = [n for n in attr.find_person_names(clause) if attr.registry_key(n) is None]
                if speakers and _SPEECH_FRAME.search(clause) and not self._said_supported(clause, originals):
                    return ("attribution", f"{speakers[0]}: words not in evidence"), False
        for kind in attr.collective_claims(prose):
            if not attr.collective_supported(kind, texts):
                return ("collective", kind), False

        # 5. Hadith reports and promised benefits.
        hadith = bool(_HADITH_REPORT.search(prose) or _EXTRA_HADITH_CUE.search(prose)
                      or any(_name_pattern(n).search(prose) for names in _HADITH_COLLECTIONS for n in names)
                      or _MUSLIM_AS_COLLECTOR.search(prose) or _AHMAD_AS_COLLECTOR.search(prose))
        # Reports and promised benefits must be in the tafsir text itself, not
        # in the verse it explains.
        report_texts = self._texts(chunks, verses=False) + [
            t for ref in self._verses(chunks) for t in self.verse_texts.get(ref, []) if not re.search(r"[ء-ي]", t)]
        if hadith:
            v = self._judge_hadith(prose_ar_quotes_kept, chunks, report_texts)
            if v:
                return ("hadith", v), True
        if _BENEFIT_CLAIM.search(prose):
            if not chunks or not self._report_supported(prose, report_texts):
                return ("benefit", "promised benefit not in evidence"), hadith
        # A number given right after a hadith sentence (a split-off hadith number).
        if prev_hadith and _NUMBER.search(_VERSE_REF.sub(" ", _digits(prose))) and not hadith:
            if not self._numbers_ok(prose, texts):
                return ("hadith", "number not in evidence"), False

        # 6. Numbers anywhere must be in the evidence.
        if not self._numbers_ok(prose, texts):
            return ("number", "number not in evidence"), hadith

        # 7. Revelation circumstances.
        if _REVELATION_CLAIM.search(prose):
            if not any(_REVELATION_IN_SOURCE.search(t) for t in texts) or not self._supported(
                    prose, texts, 0.5):
                return ("revelation", "occasion of revelation not in evidence"), hadith

        # 8. Qur'an claims (a hadith's own wording was checked as a hadith).
        v = None if hadith else self._judge_quran_claim(part, prose, chunks, own, q_refs)
        if v:
            return ("quran_claim", v), hadith

        # 8b. Scope and polarity: what the claim asserts beyond its words
        #     ("guaranteed", "never again", "without repentance") must be
        #     what the evidence states, not its opposite.
        if chunks and not (reflection and not own):
            v = self._judge_scope_polarity(prose, texts)
            if v:
                return v, hadith

        # 9. Proper names of places, groups, events and institutions
        #    ("the United Nations", "a merchant from Yemen") must be in the
        #    evidence like any other name.
        names = attr.find_person_names(bare)
        for ent in (_proper_nouns(prose) if self.lexicon else []):
            if any(ent in n or n in ent for n in names):
                continue  # a person name, checked as an attribution above
            if self._epithet(ent):
                continue
            if not self._entity_ok(ent, chunks, texts):
                return ("entity", ent), hadith

        # 10. Ordinary synthesis.
        if reflection and not own:
            return None, hadith
        if chunks:
            v = self._judge_synthesis(prose, texts, self._texts(chunks, verses=False), anchored=bool(own))
            if v:
                return ("synthesis", v), hadith
        return None, hadith

    # ---------------------------------------------------------- helpers
    def _strip_frame(self, text: str) -> str:
        """Remove names (attribution, not content) from a claim."""
        text = attr.strip_registry_names(text)
        for name in attr.find_person_names(text):
            text = text.replace(name, " ")
        for names in _HADITH_COLLECTIONS:
            for n in names:
                text = _name_pattern(n).sub(" ", text)
        return text

    def _support(self, claim: str, texts: Sequence[str], strict: bool = False) -> Support:
        per_word = xling.STRICT_TRANSLATIONS_PER_WORD if strict else xling.TRANSLATIONS_PER_WORD
        return xling.support(self._strip_frame(claim), self._view(texts), per_word=per_word)

    def _strong(self, claim: str, texts: Sequence[str]) -> bool:
        return self._supported(claim, texts, HIGH_RISK_SUPPORT)

    def _supported(self, claim: str, texts: Sequence[str], threshold: float) -> bool:
        sup = self._support(claim, texts)
        if sup.tokens == 0:
            return True
        return sup.comparable and sup.local_coverage >= threshold

    def _numbers_ok(self, prose: str, texts: Sequence[str]) -> bool:
        body = _VERSE_REF.sub(" ", _digits(_spell_numbers(prose)))
        nums = [n.replace(",", "") for n in _NUMBER.findall(body)]
        if not nums:
            return True
        have = set(re.findall(r"\d+(?:\.\d+)?", _digits(_spell_numbers(" ".join(texts)))))
        return all(n in have for n in nums)

    def _verbatim_ruling(self, prose: str, chunks: Sequence[object]) -> bool:
        """
        Every part of the sentence that states a ruling is copied word for
        word (normalised) from the clean text of the cited evidence. The
        sentence is cut at colons and quotation marks, which separate a
        framing clause ("ومعناها كما في التفسير الميسر:") from the excerpt.
        """
        evidence = [_flat(t) for c in self._clean_chunks(chunks) for t in self._raw_texts(c)]
        if not evidence:
            return False
        stating = [seg for seg in _EXCERPT_SPLIT.split(prose or "")
                   if ruling_claims(seg) or xling.deontic_classes(seg)]
        if not stating:
            return False
        for seg in stating:
            flat = _flat(seg)
            if len(flat.split()) < 4 or not any(flat in e for e in evidence):
                return False
        return True

    def _verbatim_claim(self, claim: RulingClaim, prose: str, chunks: Sequence[object]) -> bool:
        """The ruling is quoted: the whole sentence's ruling parts are a
        verbatim excerpt, or the clause carrying this claim is one once its
        reporting lead ("ذكر ابن كثير أن…", "Ibn Kathir notes that…") is cut."""
        if self._verbatim_ruling(prose, chunks):
            return True
        evidence = [_flat(t) for c in self._clean_chunks(chunks) for t in self._raw_texts(c)]
        subject = set(_flat(claim.subject).split())
        if not evidence or not subject:
            return False
        for clause in _RULING_CLAUSE.split(prose or ""):
            if not subject <= set(_flat(clause).split()):
                continue
            body = _flat(_REPORT_LEAD.sub(" ", clause))
            if len(body.split()) >= 3 and any(body in e for e in evidence):
                return True
        return False

    def _name_ok(self, name: str, chunks: Sequence[object], texts: Sequence[str]) -> bool:
        if attr.name_supported(name, self._clean_chunks(chunks), texts):
            return True
        # The work/author of any retrieved chunk ("present in retrieved
        # evidence metadata"), e.g. a second source mentioned in passing.
        key = attr.registry_key(name)
        if key is not None:
            from app.services.tafsir_sources import source_base_id
            return key in {source_base_id(getattr(c, "source_id", "") or "") for c in self.clean}
        return False

    def _echoes_injection(self, prose: str, chunks: Sequence[object]) -> bool:
        """
        The sentence carries what a planted instruction controls: it is
        carried by the instruction or its payload better than by any ordinary
        evidence (so a faithful paraphrase of the genuine part of a tampered
        chunk is not affected).
        """
        if not self.tainted:
            return False
        sup = xling.support(prose, self._view(self.tainted))
        if sup.tokens < 2 or sup.local_coverage < 0.6:
            return False
        clean = xling.support(prose, self._view(self._texts(self.clean)))
        return not (clean.comparable and clean.local_coverage >= sup.local_coverage)

    # ----------------------------------------------------------- rulings
    def _judge_ruling(self, claim: RulingClaim, chunks: Sequence[object], texts: Sequence[str],
                      q_refs: Sequence[Tuple[int, int]]) -> Optional[str]:
        if claim.cls == STATUS:
            return "takfir / religious status of a person"
        reported = claim.reported
        if claim.person in (SECOND, FIRST) and not reported:
            return f"personal ruling ({claim.person} person)"
        if not chunks and not q_refs:
            return "uncited ruling"
        if self._ruling_supported(claim, texts):
            _log.debug("ruling %s supported (clause) :: %s", claim.cls, claim.subject[:80])
            return None
        return f"ruling not stated by the evidence ({claim.cls})"

    def _ruling_supported(self, claim: RulingClaim, texts: Sequence[str]) -> bool:
        subject = self._strip_frame(claim.subject)
        script, toks, _ = xling.claim_tokens(subject)
        if not toks:
            return False
        want = {PERMIT: "§permit", FORBID: "§forbid", OBLIGE: "§oblige"}.get(claim.cls)
        for text, positions in evidence_states_class(claim.cls, texts):
            if not positions:
                continue
            for clause in _clauses(text):
                if not evidence_states_class(claim.cls, [clause])[0][1]:
                    continue
                sup = xling.support(subject, self._view([clause]))
                if not (sup.comparable and sup.local_coverage >= RULING_SUBJECT_SUPPORT):
                    continue
                if any(t.startswith("non") and len(t) > 4 for t in sup.unsupported):
                    continue  # "non-Muslim relatives" is not "relatives"
                if want and not self._sits_with(subject, clause, want):
                    continue
                return True
        return False

    def _sits_with(self, subject: str, clause: str, want: str) -> bool:
        """
        The subject must sit with a ruling of the claimed kind, in the same
        comma segment, and the segment must not state an opposite ruling
        ("zorb is permitted, while quux is forbidden": quux is forbidden; "they
        said trade is like riba, that both are lawful" is their claim, not the
        verse's ruling on riba).
        """
        for seg in _SEGMENTS.split(clause):
            classes = xling.deontic_classes(seg)
            if want not in classes:
                continue
            _log.debug("ruling segment %s %s :: %s", want, classes, seg[:120])
            sup = xling.support(subject, self._view([seg]))
            if not (sup.comparable and sup.local and sup.local_coverage >= RULING_SUBJECT_SUPPORT):
                continue
            if len(set(classes) - {want}) == 0:
                return True
            votes = xling.nearest_class(subject, seg, self.lexicon)
            if votes.get(want, 0) > max([v for k, v in votes.items() if k != want] or [0]):
                return True
        return False

    # -------------------------------------------------------- references
    def _judge_references(self, bare: str, chunks: Sequence[object], own: Sequence[object],
                          q_refs: Sequence[Tuple[int, int]]) -> Optional[str]:
        evidence = " ".join(self._texts(chunks))
        for loose in _LOOSE_REFS.finditer(bare):
            # Footnote marks and references quoted verbatim from the evidence
            # (a translation's "[98]") are part of the quotation.
            if loose.group(0).strip() in evidence:
                continue
            return f"loose reference {loose.group(0)[:40]!r}"
        m = _BRACKETED_NAME_ONLY.search(bare)
        if m and (attr.registry_key(m.group(0).strip("[] ")) or re.search(
                r"(tafsir|ibn|imam|source|تفسير|ابن|الإمام|مصدر)", m.group(0), re.IGNORECASE)):
            return f"source named without a verse {m.group(0)[:40]!r}"
        # Verses named in the prose must be ones the evidence covers.
        covered = set(self._verses(self.clean)) | set(q_refs) | {
            (s, a) for mk, (s, a0, a1) in self.quran_markers.items() for a in range(a0, a1 + 1)}
        for vm in _VERSE_REF.finditer(_digits(bare)):
            s, a0 = int(vm.group(1)), int(vm.group(2))
            a1 = int(vm.group(3) or a0)
            if not any((s, a) in covered for a in range(a0, a1 + 1)):
                return f"verse {s}:{a0} not retrieved"
        return None

    # ------------------------------------------------------------- hadith
    def _judge_hadith(self, text: str, chunks: Sequence[object], texts: Sequence[str]) -> Optional[str]:
        if not chunks:
            return "uncited hadith"
        source = " ".join(texts)
        if not _PROPHET_IN_SOURCE.search(source) and not re.search(r"روى|روي|يروى|الأثر|narrat", source):
            return "no narration in evidence"
        body = _digits(text)
        for names in _HADITH_COLLECTIONS:
            if any(_name_pattern(n).search(body) for n in names) and not _mentioned_in(names, source) \
                    and not any(attr.name_in_text(n, source) for n in names):
                return "collection not in evidence"
        if _MUSLIM_AS_COLLECTOR.search(body) and not _mentioned_in(("Muslim", "مسلم"), source):
            return "collection not in evidence"
        if _AHMAD_AS_COLLECTOR.search(body) and not _mentioned_in(("Ahmad", "أحمد"), source):
            return "collection not in evidence"
        if not self._numbers_ok(text, texts):
            return "number not in evidence"
        claim = _HADITH_REPORT.sub(" ", _HADITH_CUE.sub(" ", _EXTRA_HADITH_CUE.sub(" ", text)))
        if not self._report_supported(claim, texts):
            return "report not in evidence"
        return None

    def _said_supported(self, claim: str, texts: Sequence[str]) -> bool:
        """Words attributed to a named authority: near-verbatim in the
        evidence's own script, or half the content across scripts (a
        paraphrase of a quoted opinion)."""
        from app.safety.grounding import evidence_support
        claim = self._strip_frame(claim)
        same = evidence_support(claim, texts, ngram=3)
        if same.comparable and same.tokens >= 2:
            return same.local_coverage >= 0.6 or (same.ngram and same.local_coverage >= 0.5)
        return True  # across scripts the name's presence is what can be checked

    def _report_supported(self, claim: str, texts: Sequence[str]) -> bool:
        """
        A reported narration or promised benefit must be in one place of the
        evidence. In the evidence's own script that means (nearly) its
        wording: every content word in one window, or a run of three
        consecutive content words with most of the rest nearby. Across
        scripts (an English report of Arabic evidence) the content must be
        carried through the lexicon at the high-risk threshold.
        """
        from app.safety.grounding import evidence_support
        claim = self._strip_frame(_REPORT_LEAD.sub(" ", claim.strip()))
        # The report's own source is the tafsir text (its original edition);
        # a parallel edition in the answer's language and the verse's
        # translations only help read it across scripts.
        originals = {t for c in self.clean for t in self._raw_texts(c)}
        source = [t for t in texts if t in originals] or list(texts)
        same = evidence_support(claim, source, ngram=3)
        if same.comparable and same.tokens >= 3:
            return same.local_coverage >= REPORT_SAME_SCRIPT or (same.ngram and same.local_coverage >= REPORT_SAME_SCRIPT_NGRAM)
        if same.comparable and same.tokens:
            return same.local_coverage >= 0.99
        parallel = [t for ts in self.parallel.values() for t in ts if t in texts]
        if parallel:
            psame = evidence_support(claim, parallel, ngram=3)
            if psame.comparable and psame.tokens >= 3 and (
                    psame.local_coverage >= 0.85 or (psame.ngram and psame.local_coverage >= 0.65)):
                return True
        # The chain and the honorific frame of a report ("via Ibn Abbas",
        # "the Prophet ﷺ", "many times") are not its content.
        claim = _REPORT_FRAME.sub(" ", claim)
        sup = xling.support(claim, self._view(texts))
        _log.debug("report %s/%s unsupported=%s :: %s", sup.local, sup.tokens, sup.unsupported, claim[:100])
        if sup.tokens == 0:
            return True
        # Read through the lexicon only: nearly every content word of the
        # report must be carried (one specific invented detail — "in the
        # rain", "a house of pearls" — is exactly what an invented report adds).
        allowed = 0 if sup.tokens <= 4 else (1 if sup.tokens <= 6 else int(sup.tokens * 0.3))
        return sup.comparable and sup.tokens - sup.local <= allowed

    # -------------------------------------------------------- quran claims
    def _judge_quran_claim(self, part: str, prose: str, chunks: Sequence[object], own: Sequence[object],
                           q_refs: Sequence[Tuple[int, int]]) -> Optional[str]:
        covered = set(self._verses(self.clean))
        p_script, p_toks, _ = xling.claim_tokens(prose)
        substantive = len(set(p_toks)) >= 3
        # Prose whose only support is a Qur'an self-reference to a verse no
        # retrieved chunk covers.
        if q_refs and not own and substantive and not any(r in covered for r in q_refs):
            return "Qur'an citation to a verse that was not retrieved"
        if len(set(p_toks)) < 2 or not has_quran_voice(prose):
            return None
        claim = _quran_clause(prose)
        if len(set(xling.claim_tokens(claim)[1])) < 2:
            return None  # the claim is a quotation (verified separately)
        # What the Qur'an says must be in the verse: its canonical text or a
        # stored translation of it (a tafsir's explanation is not the verse).
        refs = list(q_refs) or self._verses(own or chunks)
        pool: List[str] = []
        for ref in refs:
            pool.extend(self._verse_primary(ref))
        threshold = HIGH_RISK_SUPPORT
        tafsir_cited = [c for c in own if c is not None]
        if tafsir_cited:
            # "The verse describes X [Ibn Kathir, 2:6]": the cited tafsir's
            # reading of the verse — the verse or that tafsir must carry X.
            pool.extend(self._texts(tafsir_cited))
        if _TAFSIR_FRAME.search(prose[:max(0, _quran_cue_start(prose))]) and tafsir_cited:
            # "Ibn Kathir explains that this verse is a call to…"
            claim = _QURAN_FRAME.sub(" ", prose)
            threshold = ATTRIBUTED_QURAN_SUPPORT
        sup = self._support(claim, pool, strict=True)
        if tafsir_cited and sup.comparable and sup.tokens >= MIN_CLAIM_TOKENS and sup.local_coverage < threshold \
                and _verse_reading(prose):
            # "The verse promises believers… [Al-Muyassar, 16:97]": a summary
            # of the verse as the cited tafsir reads it, not words put in
            # Allah's mouth — held to the standard of "Ibn Kathir explains
            # that this verse…", with synonyms read as for tafsir prose.
            sup = self._support(claim, pool)
            threshold = ATTRIBUTED_QURAN_SUPPORT
        _log.debug("quran_claim %s/%s unsupported=%s pool=%d :: %s", sup.local, sup.tokens, sup.unsupported,
                   len(pool), claim[:100])
        if not sup.comparable or sup.local_coverage < threshold:
            return f"not carried by the verse ({sup.local}/{sup.tokens})"
        return None

    # ------------------------------------------------- scope and polarity
    def _judge_scope_polarity(self, prose: str, texts: Sequence[str]) -> Optional[Tuple[str, str]]:
        for cls in xling.absolute_scope(prose):
            if not xling.scope_supported(cls, texts):
                return ("scope", f"{cls} scope not stated by the evidence")
        conflicts = xling.polarity_conflicts(self._strip_frame(prose), texts, self.lexicon)
        _log.debug("polarity conflicts=%s :: %s", conflicts, prose[:120])
        if conflicts:
            return ("polarity", f"opposite of the evidence: {', '.join(conflicts[:3])}")
        return None

    # ----------------------------------------------------------- synthesis
    def _judge_synthesis(self, prose: str, texts: Sequence[str],
                         chunk_texts: Sequence[str] = (), anchored: bool = False) -> Optional[str]:
        prose = _DISCOURSE_OPENER.sub(" ", self._drop_transliterations(prose))
        sup = self._support(prose, texts)
        if not sup.comparable or sup.tokens < MIN_CLAIM_TOKENS:
            return None
        foreign = [t for t in sup.unsupported if self._foreign(t)]
        _log.debug("synthesis %s/%s foreign=%s unsupported=%s :: %s", sup.local, sup.tokens, foreign,
                   sup.unsupported, prose[:120])
        script = xling.claim_tokens(prose)[0]
        same_script = any(xling.claim_tokens(t)[0] == script for t in chunk_texts)
        drop_below = SYNTHESIS_DROP if same_script else CROSS_LINGUAL_SYNTHESIS_DROP
        if anchored and not foreign:
            if not same_script:
                drop_below = ANCHORED_CROSS_LINGUAL_DROP
            elif sup.local >= ANCHOR_TOKENS:
                drop_below = ANCHORED_SAME_SCRIPT_DROP
        if sup.local_coverage < drop_below:
            return f"content not in evidence ({sup.local}/{sup.tokens})"
        if (len(foreign) >= 2 and sup.local_coverage <= SYNTHESIS_WEAK) or (foreign and sup.local_coverage <= 0.4):
            return f"content foreign to the evidence: {', '.join(foreign[:3])}"
        # The asked-about topic is absent from everything retrieved: the
        # answer is speaking beyond its evidence ("What does the Qur'an say
        # about cryptocurrency?" answered from 2:286).
        off_topic = [t for t in sup.unsupported if t in self.topic and t not in self.pool_tokens
                     and self._foreign(t)]
        if off_topic:
            return f"question topic not in evidence: {', '.join(off_topic[:3])}"
        # A reason or purpose given for the content ("because…", "لأن…")
        # is a claim of its own: it must be carried by the evidence, not
        # ride on the support of the clause it explains.
        m = _CAUSAL.search(prose)
        if m:
            reason = prose[m.end():]
            rsup = self._support(reason, texts)
            need = SYNTHESIS_WEAK if same_script else CROSS_LINGUAL_REASON
            if rsup.comparable and rsup.tokens >= 3 and rsup.local_coverage < need:
                return f"reason not in evidence ({rsup.local}/{rsup.tokens})"
        if sup.local_coverage < SYNTHESIS_WEAK:
            # Words put in a named author's mouth are held to the evidence:
            # a weakly supported attribution is removed, not just flagged.
            if same_script and (attr.strip_registry_names(prose) != prose or attr.find_person_names(prose)):
                return f"attributed content weakly supported ({sup.local}/{sup.tokens})"
            self.report.weak += 1
        return None

    def _epithet(self, ent: str) -> bool:
        """A capitalised English compound of ordinary words in the form the
        translations give divine names ("Self-Subsisting" beside
        "Self-Sustaining", "Ever-Living"): a rendering, not a named entity."""
        lex = self.lexicon
        if "-" not in ent or not lex:
            return False
        parts = [xling.en_fold(p) for p in ent.split("-") if p]
        if len(parts) < 2 or not all(xling.en_stem(p) in lex.vocab for p in parts):
            return False
        head = parts[0] + "-"
        return any(n.startswith(head) for n in lex.names)

    def _entity_ok(self, ent: str, chunks: Sequence[object], texts: Sequence[str]) -> bool:
        if attr.registry_key(ent) or attr.name_supported(ent, self._clean_chunks(chunks), texts):
            return True
        sup = xling.support(ent, self._view(texts))
        if sup.tokens == 0 or (sup.comparable and sup.local == sup.tokens):
            return True
        # Short names ("Uhud", "Matta") have two-consonant skeletons: they
        # match only a short, rare Arabic word with the same consonants.
        words = [w for w in re.split(r"[\s-]+", ent)
                 if w.lower() not in ("of", "the", "al", "ibn", "bin", "and", "dhu", "dhul", "dhi", "dha", "dhil")]
        ar_words = set()
        for t in texts:
            for w in normalize_arabic(t).split():
                w = w[2:] if w.startswith("ال") else (w[1:] if w[:1] in "وفب" and len(w) > 3 else w)
                if 2 <= len(w) <= 4 and self.lexicon.ar_freq.get(w, 0) <= xling.RARE_WORD:
                    ar_words.add(xling.arabic_skeleton(w))
        if bool(words) and all(
                (sk := xling.latin_skeleton(w)) and len(sk) <= 2 and sk in ar_words for w in words):
            return True
        # A name too short to verify by its consonants ("Uhud", "Matta":
        # homographs of common words) is judged with the rest of the sentence.
        return bool(words) and all(len(xling.latin_skeleton(w)) <= 2 for w in words)

    def _drop_transliterations(self, prose: str) -> str:
        """A short single-quoted run of words the English corpus never uses
        ('wa wassa rabbuka', 'qada') is a transliterated quotation of the
        Arabic, not an English claim."""
        if not self.lexicon:
            return prose

        def _sub(m: "re.Match") -> str:
            words = xling.en_words(m.group(1))
            if words and len(words) <= 6 and sum(
                    1 for w in words if self._foreign(xling.en_stem(w))) * 2 >= len(words):
                return " "
            return m.group(0)
        return re.sub(r"(?<![A-Za-z])['‘]([^'’\n]{1,60})['’](?![A-Za-z])", _sub, prose)

    def _foreign(self, token: str) -> bool:
        """A content word the parallel Qur'an corpus never uses (cryptocurrency,
        mortgage, blood pressure…): the evidence cannot be about it."""
        lex = self.lexicon
        if not lex or token.startswith("§"):
            return False
        return token not in lex.en2ar and token not in lex.ar2en and token not in lex.vocab


_QURAN_FRAME = re.compile(
    r"\b(allah|god|the\s+(holy\s+)?qur'?an|the\s+verse|this\s+verse|the\s+ayah|this\s+ayah|the\s+surah|"
    r"this\s+surah|revelation|the\s+lord|the\s+almighty)\b|\b(says?|said|states?|declares?|tells?\s+us|"
    r"promises?|informs?\s+us|commands?|reveals?|teaches|mentions?|clearly|plainly|that)\b"
    r"|(?<![ء-ي])[وف]?(قال|يقول|أخبر|يخبر|وعد|يعد|يقرر|قرر|نص|ينص|تخبرنا|يخبرنا|أخبرنا|القرآن|الآية|الله|"
    r"تعالى|سبحانه|أن|هذه)(?![ء-ي])",
    re.IGNORECASE,
)
_CLAUSE_BREAK = re.compile(r"\s*(?:[;؛]|,\s+(?:and|while|whereas|but)\s+|،\s*و|\s+(?:while|whereas)\s+)\s*", re.IGNORECASE)


_TAFSIR_FRAME = re.compile(
    r"\b(explains?|explained|notes?|noted|mentions?|mentioned|comments?|says|said|writes?|wrote|states?|adds?|"
    r"reports?|reported|clarifies|indicates?|interprets?|according\s+to)\b"
    r"|(?<![ء-ي])[وف]?(بين|يبين|ذكر|يذكر|أوضح|يوضح|قال|يقول|نقل|ينقل|أورد|يورد|فسر|يفسر|أفاد|يفيد)(?![ء-ي])",
    re.IGNORECASE,
)


def _quran_cue_start(prose: str) -> int:
    from app.safety.grounding import _QURAN_VOICE
    m = _QURAN_VOICE.search(prose)
    return m.start() if m else 0


_VERSE_SUBJECT = re.compile(r"\b(?:the|this|that)\s+(?:verse|ayah|passage)\b"
                            r"|(?<![ء-ي])(?:الآية|الاية|هذه\s+الآية|هذه\s+الاية)(?![ء-ي])", re.IGNORECASE)


def _verse_reading(prose: str) -> bool:
    """The Qur'an cue is the verse as subject ("the verse promises…", "تبين
    الآية…"), not Allah or the Qur'an speaking ("Allah says", "the Qur'an
    tells us"), and nothing is quoted."""
    from app.safety.grounding import _QURAN_VOICE
    m = _QURAN_VOICE.search(prose or "")
    if not m or _QUOTED_SPANS.search(prose or ""):
        return False
    cue = m.group(0)
    return bool(_VERSE_SUBJECT.search(cue)) and not re.search(
        r"\b(?:allah|god|lord|qur'?an)\b|(?<![ء-ي])(?:الله|تعالى|سبحانه|القرآن|القران|ربنا|ربك)(?![ء-ي])", cue, re.I)


def _quran_clause(prose: str) -> str:
    """The part of a sentence presented as the Qur'an's own words: from the
    Qur'an cue to the end of its clause, framing words removed."""
    from app.safety.grounding import _QURAN_VOICE
    m = _QURAN_VOICE.search(prose)
    if not m:
        return ""
    rest = prose[m.end():]
    head = prose[max(0, max(prose.rfind(p, 0, m.start()) for p in ",;:،؛") + 1):m.end()]
    clause = _CLAUSE_BREAK.split(rest, maxsplit=1)[0]
    # "…the verse states: ﴿…﴾ Al-Muyassar explains that…": the Qur'an's
    # words end where another speaker begins.
    marked = attr.strip_registry_names(clause.replace("§", " "))
    if marked != clause:
        cut = next((i for i, (a, b) in enumerate(zip(clause, marked)) if a != b), len(clause))
        clause = clause[:cut]
    return _QURAN_FRAME.sub(" ", head + " " + clause)


# Discourse openers carry no content ("In short,", "In other words,", "The
# point is that", "والخلاصة أن", "أي أن"): they are not words to support.
_DISCOURSE_OPENER = re.compile(
    r"^\W*(?:(?:so|thus|hence|basically|essentially|ultimately|in\s+short|in\s+brief|in\s+other\s+words|in\s+essence|"
    r"in\s+summary|in\s+a\s+nutshell|to\s+sum\s+up|put\s+simply|simply\s+put|that\s+is\s+to\s+say|that\s+is|"
    r"the\s+(?:point|idea|message|lesson|upshot|takeaway|gist)(?:\s+here)?\s+is(?:\s+that)?|this\s+means(?:\s+that)?|"
    r"in\s+practice|in\s+practical\s+terms)\b[\s,:;—–-]*)+"
    r"|^\W*(?:[وف]?(?:باختصار|بإيجاز|خلاصة\s+المعنى|الخلاصة|خلاصة\s+ذلك|حاصل\s+المعنى|حاصل\s+ذلك|المعنى|"
    r"معنى\s+ذلك|معنى\s+الآية|المقصود|المراد|أي|اي|يعني|بمعنى\s+آخر|بعبارة\s+أخرى)(?:\s+(?:أن|ان|أنه|انه))?"
    r"(?![ء-ي])[\s،,:؛]*)+",
    re.IGNORECASE,
)
_RULING_CLAUSE = re.compile(r"[,;:،؛«»“”\"﴿﴾]")
_REPORT_LEAD = re.compile(
    r"^\W*[وف]?(?:ذكر|يذكر|بين|بيّن|يبين|قال|يقول|أوضح|يوضح|نقل|ينقل|أفاد|يفيد|أورد|يورد|فسر|يفسر|يرى|رأى|أكد|يؤكد)"
    r"\s+(?:\S+\s+){0,4}?(?:أن|ان|أنّ|إن)\s+"
    r"|^\W*(?:(?:the\s+)?[A-Z][\w'’-]*\s+){1,5}?(?:explains?|explained|notes?|noted|states?|stated|says|said|"
    r"mentions?|mentioned|reports?|reported|writes?|wrote|adds?|added)\s+(?:that\s+)?",
    re.IGNORECASE,
)
_EXCERPT_SPLIT = re.compile(r"[:：«»“”\"﴿﴾]")
_FLAT_DROP = re.compile(r"[\u064b-\u0652\u0670\u0640\u06d6-\u06ed]")
_FLAT_FOLD = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ة": "ه", "ى": "ي", "ؤ": "و", "ئ": "ي"})


def _flat(text: str) -> str:
    """Text reduced for a verbatim comparison: no diacritics, folded letters,
    no punctuation, single spaces."""
    t = _FLAT_DROP.sub("", text or "").translate(_FLAT_FOLD).lower()
    t = re.sub(r"[^\w\s]|_", " ", t)
    return " " + re.sub(r"\s+", " ", t).strip() + " "


_REPORT_FRAME = re.compile(
    r"\b(?:via|through|on\s+the\s+authority\s+of|the\s+prophet|prophet|the\s+messenger(?:\s+of\s+(?:allah|god))?|"
    r"messenger|pbuh|saw|many\s+times|several\s+times)\b|ﷺ|\(\s*(?:pbuh|saw|s\.a\.w\.?)\s*\)",
    re.IGNORECASE,
)
_CAUSAL = re.compile(
    r"\b(?:because|since|due\s+to|owing\s+to|on\s+account\s+of|for\s+the\s+reason\s+that|the\s+reason\s+(?:is|being|was)|"
    r"in\s+order\s+to|so\s+that|as\s+a\s+result\s+of|caused\s+by)\b"
    r"|(?<![ء-ي])[وف]?(?:لأن|لان|لأنه|لانه|لأنها|لانها|بسبب|لكي|كي\s|لأجل|لاجل|من\s+أجل|من\s+اجل|إذ\s|والسبب|السبب\s+في)",
    re.IGNORECASE,
)
_SEGMENTS = re.compile(r"\s*[,،;؛:]\s*|\s+(?:while|whereas|but)\s+", re.IGNORECASE)
_CLAUSE_SPLIT = re.compile(r"(?<=[.!?؟؛;:\n])\s+|،\s*(?=و)|\s+(?=وقال|وقيل|وعن|وروى)")


def _clauses(text: str) -> List[str]:
    parts = [p for p in _CLAUSE_SPLIT.split(text or "") if p and p.strip()]
    # Keep neighbouring clauses together: a ruling and its subject often
    # straddle a comma in tafsir prose.
    out = []
    for i, p in enumerate(parts):
        out.append(p if i + 1 >= len(parts) else p + " " + parts[i + 1])
    return out or [text]


_CAP_WORD = r"[A-Z][A-Za-z’'`ʿāīūĀĪŪ]*(?:-[A-Za-z’'`ʿāīūĀĪŪ]+)*"
_CAP_RUN = re.compile(rf"\b({_CAP_WORD}(?:\s+(?:of|the|al-|ibn|bin|bint|abu|and)?\s*{_CAP_WORD})*)")
# Capitalised words that are not named entities to verify: God and His
# names, the Prophet, the Qur'an and its parts, acts of worship, sentence
# connectives. Places, peoples, events and institutions are not exempt.
_ENTITY_EXEMPT = frozenset((
    "allah god lord prophet messenger quran qur'an koran book scripture revelation tafsir tafseer hadith sunnah "
    "surah sura verse verses ayah ayat muhammad jibril gabriel islam iman muslims muslim believers believer "
    "salah salat prayer zakah zakat sawm fasting hajj umrah ramadan sharia shariah fiqh paradise jannah hell "
    "fire hereafter day judgement judgment resurrection most merciful gracious compassionate almighty exalted "
    "high ever-living living self-sustaining sustainer forgiving wise knowing all-knowing all-hearing seeing "
    "note reflection however therefore thus moreover furthermore indeed truly also according english arabic "
    "saheeh international sahih kursi throne fatihah baqarah imran nisa maidah kahf yasin rahman mulk ikhlas "
    "dhu dhul dhi muharram rajab safar shaban sha'ban shawwal qa'dah qadah hijjah "
    # the Qur'an's own figures
    "adam nuh noah ibrahim abraham musa moses isa jesus maryam mary yusuf joseph yaqub jacob dawud david "
    "sulayman solomon yunus jonah harun aaron ismail ishmael ishaq isaac lut lot hud salih shuayb ayyub job "
    "zakariyya zechariah yahya john idris ilyas elias luqman khidr pharaoh firawn iblis satan shaytan jibril "
    "gabriel mikail michael haman qarun korah talut saul jalut goliath imran "
    "falaq nas asr sharh inshirah duha kafirun nasr"
).split())
_PRONOUNS = frozenset("he his him himself i we our us you your me my it they them their".split())


def _proper_nouns(prose: str) -> List[str]:
    """Capitalised runs inside an English sentence (not its first word) that
    are not pronouns, the Qur'an's own vocabulary or a catalogue name."""
    if not re.search(r"[A-Za-z]{3}", prose or ""):
        return []
    text = attr.strip_registry_names(prose).strip()
    first = re.match(r"\W*\w+", text)
    out = []
    for m in _CAP_RUN.finditer(text):
        if first and m.start() < first.end():
            continue
        words = [w for w in re.split(r"[\s-]+", m.group(1)) if w]
        keep = [w for w in words
                if xling.en_fold(w).strip("-'") not in _ENTITY_EXEMPT
                and w.lower() not in _PRONOUNS
                and w.lower() not in ("of", "the", "al", "ibn", "bin", "bint", "abu", "and")]
        if keep:
            out.append(m.group(1))
    return out


def _is_question(sentence: str) -> bool:
    """A sentence put as a question (ends with "?" / "؟")."""
    return bool(re.search(r"[?؟]\s*[\)\]\*_\"'»”]*\s*$", (sentence or "").strip()))


def is_reflection_paragraph(paragraph: str) -> bool:
    """A paragraph explicitly labelled as reflection ("Reflection:", "للتأمل:")."""
    return bool(_REFLECTION_LABEL.match(paragraph or ""))
