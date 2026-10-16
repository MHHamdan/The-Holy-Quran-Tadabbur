"""
Hallucination / اختلاق Prevention Guard

Validates every AI-assisted Quranic answer before it reaches users.

Rules enforced:
  1. Every ayah reference must exist in the 114-surah, 6236-ayah canonical corpus.
  2. Every source_id must be in the trusted registry.
  3. No answer may be returned without at least one citation.
  4. No fatwa may be generated — fatwa-like queries are hard-blocked.
  5. Scientific miracle claims must carry a mandatory caution label.
  6. Translation text must be labeled as translation, never as Quran.
  7. Quran text must not be mutated or inventively modified.

Reference: "تجربة تفسير القرآن الكريم بالذكاء الاصطناعي"
           Prof. Dr. Abdulrahman Al-Shehri — Platform design implication §4
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from app.rag.source_validator import TRUSTED_SOURCE_IDS

# ---------------------------------------------------------------------------
# Canonical ayah count per surah (surah 1–114)
# Source: standard Hafs 'an 'Asim recitation, 6236 total ayahs
# ---------------------------------------------------------------------------

SURAH_AYAH_COUNTS: tuple = (
    7, 286, 200, 176, 120, 165, 206, 75, 129, 109,
    123, 111,  43,  52,  99, 128, 111, 110,  98, 135,
    112,  78, 118,  64,  77, 227,  93,  88,  69,  60,
     34,  30,  73,  54,  45,  83, 182,  88,  75,  85,
     54,  53,  89,  59,  37,  35,  38,  29,  18,  45,
     60,  49,  62,  55,  78,  96,  29,  22,  24,  13,
     14,  11,  11,  18,  12,  12,  30,  52,  52,  44,
     28,  28,  20,  56,  40,  31,  50,  40,  46,  42,
     29,  19,  36,  25,  22,  17,  19,  26,  30,  20,
     15,  21,  11,   8,   8,  19,   5,   8,   8,  11,
     11,   8,   3,   9,   5,   4,   7,   3,   6,   3,
      5,   4,   5,   6,
)

TOTAL_SURAHS: int = len(SURAH_AYAH_COUNTS)  # 114

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Matches verse refs like: 2:255, 3:1-10, Al-Baqarah:255, Surah 2:255
_VERSE_REF_PATTERN = re.compile(
    r'\b(?:Surah\s+)?(\d{1,3})\s*:\s*(\d{1,3})(?:\s*-\s*(\d{1,3}))?',
    re.IGNORECASE,
)

# Keywords that indicate a fatwa-like query or response
_FATWA_KEYWORDS = frozenset({
    "is it halal", "is it haram", "is it permissible", "is it forbidden",
    "am i allowed", "can i", "should i", "must i", "religious ruling",
    "fatwa", "حكم", "هل يجوز", "هل يحل", "هل يحرم", "هل يباح",
    "فتوى", "يجوز", "يحرم", "المسألة الفقهية",
})

# Generated answers: phrases where the answer ITSELF asserts a ruling.
# Keyword spotting ("يجوز", "can i", "حكم") over-blocks ordinary tafsir prose,
# so model output is checked against these assertions instead.
_RULING_ASSERTIONS = tuple(re.compile(p, re.IGNORECASE) for p in (
    r"\b(it|this|that|doing (so|this|that)|such an act|such a thing)\s+is\s+"
    r"(strictly\s+|absolutely\s+|clearly\s+|therefore\s+)?(haram|halal|forbidden|prohibited|"
    r"impermissible|permissible|obligatory|mandatory|a (major |grave |minor )?sin|sinful|makruh|"
    r"lawful|unlawful)\b",
    r"\bwhoever\b[^.]{0,80}\b(is|are|becomes?)\s+(sinful|a sinner|in sin|cursed|a disbeliever|"
    r"out of islam)\b",
    r"\b(you|muslims|a muslim)\s+(are|is)\s+(not\s+)?(allowed|permitted|obliged|required)\s+to\b",
    r"\b(i|we)\s+(rule|declare)\s+(that|it)\b|\bmy (ruling|fatwa)\b",
    r"(هذا|ذلك|فهو|فهي|وهو|وهي|إنه|إنها|فإنه|فإنها)\s+(حرام|حلال|محرم|محرمة|مباح|مباحة|واجب|"
    r"واجبة|جائز|جائزة|مكروه|مكروهة)",
    r"(لا\s+)?يجوز\s+(لك|لكم|للمسلم|للمسلمة|للمرأة|للرجل)",
    r"(يأثم|فهو آثم|فهي آثمة)",
    r"(أفتي|نفتي|فتواي)",
))

# Verdicts no generated answer may give, whether or not a citation follows:
# a ruling addressed to the reader, the validity of their worship or
# contract, and takfir. A citation does not turn a personal fatwa into
# tafsir, so these are checked on every sentence (quotations aside).
_PERSONAL_VERDICTS = tuple(re.compile(p, re.IGNORECASE) for p in (
    # "Your prayer is not valid…", "your divorce is binding". Repentance is
    # left out: "your repentance is accepted when sincere" restates the
    # promise of a verse (39:53), the hope tafsir gives, not a fiqh verdict.
    r"\byour\s+(prayers?|salah|salat|fast|fasting|sawm|wudu|wudhu|ablution|ghusl|marriage|nikah|"
    r"divorce|talaq|hajj|umrah|zakat|zakah|oath)\s+(is|are|was|will\s+be|would\s+be|"
    r"becomes?|remains?)\s+(still\s+|now\s+)?(not\s+)?(valid|invalid|void|accepted|unaccepted|correct|"
    r"sound|nullified|broken|binding|effective|counted)\b",
    r"\bdivorce\s+(does\s+not|doesn'?t|does|will|will\s+not|won'?t)\s+(count|take\s+effect|occur)\b",
    r"\b(you|muslims|a muslim)\s+(are|is)\s+(not\s+)?(allowed|permitted|obliged|required)\s+to\b",
    r"\b(yes|no)\s*[,،]\s*(you|it|your|this|that)\b[^.\n]{0,60}\b(allowed|permitted|permissible|valid|"
    r"invalid|halal|haram|lawful|must|may)\b",
    r"\b(i|we)\s+(rule|declare)\s+(that|it)\b|\bmy\s+(ruling|fatwa)\b",
    # Takfir as a general rule: "Anyone who doubts this is a disbeliever
    # (kafir)", "a Muslim who … becomes an apostate". Not "they are
    # disbelievers who were warned", which describes a verse's own subjects.
    r"\b(anyone|anybody|whoever|whosoever|someone|somebody|a\s+person|any\s+person|a\s+muslim|"
    r"any\s+muslim|muslims\s+who|one\s+who|he\s+who|she\s+who|everyone\s+who)"
    r"\b[^.;\n]{0,80}?\b(is|are|becomes?|has\s+become|will\s+become|would\s+be)\s+(a\s+|an\s+)?"
    r"(disbelievers?|kafirs?|kaafirs?|kuffar|apostates?|murtads?|non-?muslims?)\b",
    r"\b(has|have|had)\s+left\s+(the\s+fold\s+of\s+)?islam\b|\bout\s+of\s+(the\s+fold\s+of\s+)?islam\b"
    r"|\bexpelled\s+from\s+islam\b",
    r"\bis\s+(a\s+)?k[aā]fir\b|\(\s*k[aā]fir\s*\)",
    # Arabic: divorce verdicts, validity of the reader's worship, rulings
    # addressed to the reader (singular — plural عليكم/لكم is the Qur'an's
    # own address and appears in verse paraphrase), takfir.
    r"(?<![ء-ي])[وف]?(لا\s+)?(يقع|تقع|وقع|يُحتسب|يحتسب)\s+(طلاقك|طلاقه|طلاقها|الطلاق|الطلقة|طلقة)(?![ء-ي])",
    r"(?<![ء-ي])(طلاقك|الطلاق)\s+(لا\s+)?(يقع|واقع|صحيح|باطل|نافذ)(?![ء-ي])",
    r"(?<![ء-ي])(صلاتك|صومك|صيامك|وضوؤك|وضوءك|غسلك|زواجك|نكاحك|طلاقك|حجك|عمرتك|زكاتك|يمينك)\s+"
    r"(لا\s+|غير\s+)?(صحيحة|صحيح|باطلة|باطل|مقبولة|مقبول|فاسدة|فاسد|تصح|يصح|تبطل|يبطل|تقبل|يقبل)(?![ء-ي])",
    r"(?<![ء-ي])[وف]?(لا\s+)?(يجوز|تجوز|يحل|تحل|يحرم|تحرم|يجب|تجب|يلزم|يلزمك|يباح)\s+(لك|عليك|لكِ|عليكِ)(?![ء-ي])",
    r"(?<![ء-ي])(فهو|فهي|فإنه|فإنها)\s+(آثم|آثمة)(?![ء-ي])|(?<![ء-ي])[وف]?(تأثم|أثمت)(?![ء-ي])",
    r"(?<![ء-ي])(عليك|فعليك)\s+(أن|ان)\s+(تعيد|تقضي|تصلي|تصوم|تخرج|تدفع|تطلق|تزيل|تتوضأ|تغتسل|تكفر|تترك)",
    r"(?<![ء-ي])نعم\s*[،,]\s*(يقع|يجوز|تجوز|يجب|تجب|يحل|تحل|يحرم|تحرم|صلاتك|صومك|طلاقك)(?![ء-ي])",
    r"(?<![ء-ي])(فهو|فهي|فهم|فإنه|فإنها|إنه|إنها|وهو|وهي|هو|هي)\s+(كافر|كافرة|كفار|مرتد|مرتدة|مشرك)(?![ء-ي])",
    r"(?<![ء-ي])[وف]?(تارك|من\s+ترك|من\s+شك|من\s+أنكر|من\s+ينكر|من\s+لم)[^.،؟\n]{0,60}?(?<![ء-ي])"
    r"(كافر|مرتد|خارج\s+(عن|من)\s+(الملة|الإسلام))(?![ء-ي])",
    r"(خرج|يخرج|خارج)\s+(عن|من)\s+(الملة|ملة\s+الإسلام|الإسلام)(?![ء-ي])",
))

# "You must remove it…", "you should repeat your prayer", "you may not
# marry…": a ruling addressed to the reader, unless the sentence reports
# what the verse itself commands ("In this verse Allah tells the believers:
# you must not eat the property of orphans unjustly") - second-person
# paraphrase of a Qur'anic command is ordinary tafsir style.
_YOU_MUST = re.compile(
    r"\byou\s+(must|should|have\s+to|need\s+to|are\s+(required|obliged|obligated)\s+to|may\s+not|"
    r"must\s+not|should\s+not|cannot|can'?t|are\s+not\s+allowed\s+to|are\s+allowed\s+to)\s+"
    r"(?:\w+\s+){0,2}?(pray|fast|remove|repeat|redo|re-?perform|perform|pay|give|divorce|marry|remarry|"
    r"break|make\s+up|wash|recite|wear|stop|eat|drink|take|abandon|leave)\b",
    re.IGNORECASE,
)
# The frame that makes such a sentence a report of the verse.
REPORTING_FRAME = re.compile(
    r"\b(the\s+(verse|ayah|ayat|passage|surah|sura|qur'?an|koran|tafsir|commentary|command)|"
    r"this\s+(verse|ayah|passage|surah)|these\s+verses|allah|god|the\s+lord)\b[^.;\n]{0,40}?\b"
    r"(tells?|told|commands?|commanded|instructs?|instructed|teach(es)?|taught|says|said|orders?|ordered|"
    r"urges?|urged|enjoins?|enjoined|reminds?|reminded|warns?|warned|address(es)?|addressed|explains?|"
    r"directs?|directed|forbids?|forbade|requires?|obliges?)\b",
    re.IGNORECASE,
)
# General statements of a rule ("divorce is binding in the third
# instance"): tafsir may report them, so they stand only when the cited
# evidence states them (see grounding.ruling_report_supported).
_GENERAL_RULINGS = tuple(re.compile(p, re.IGNORECASE) for p in (
    r"\b(the\s+|a\s+|such\s+a\s+)?(prayer|salah|fast|wudu|ablution|ghusl|divorce|talaq|marriage|nikah)\s+"
    r"(is|are)\s+(still\s+)?(not\s+)?(valid|invalid|void|nullified|binding)\b",
))

# Permissibility claims with any subject ("Wine is permitted for believers",
# "والربا حلال للمؤمنين"). Tafsir legitimately reports what a verse permits,
# so these are not refused outright: the caller keeps one only when the
# cited evidence states it (see find_verdicts / grounding.verdict_supported).
_PERMISSIVE_VERDICTS = tuple(re.compile(p, re.IGNORECASE) for p in (
    r"\b(?P<subj>[A-Za-z][\w'’-]*(?:\s+[A-Za-z][\w'’-]*){0,3}?)\s+(is|are)\s+(now\s+|therefore\s+|also\s+|"
    r"thus\s+|then\s+|completely\s+|totally\s+|fully\s+|clearly\s+|perfectly\s+)?"
    r"(permissible|halal|lawful|permitted(?!\s+to\b)|allowed(?!\s+to\b)|"
    r"not\s+(haram|forbidden|prohibited|sinful|a\s+sin))\b",
    r"(?<![ء-ي])(?P<subj>[وف]?ال[ء-ي]{2,})\s+(?:(هو|هي)\s+)?(حلال|مباح|مباحة|جائز|جائزة|ليس\s+بحرام|غير\s+محرم)"
    r"(?![ء-ي])",
    r"(?<![ء-ي])(حلال|مباح|مباحة)\s+(لل[ء-ي]+|لكم|لك|لنا|للناس)(?![ء-ي])",
))

# Ruling vocabulary: an answer that survives the checks above but still
# speaks of rulings carries the fiqh disclaimer, whatever the intent.
_RULING_VOCABULARY = re.compile(
    r"\b(haram|halal|permissible|impermissible|forbidden|prohibited|obligatory|mandatory|makruh|"
    r"lawful|unlawful|ruling|fiqh|sinful)\b"
    r"|(?<![ء-ي])(حرام|حلال|محرم|محرمة|مباح|مباحة|واجب|واجبة|فرض|مكروه|مكروهة|يجوز|لا\s+يجوز|"
    r"جائز|حكم\s+شرعي|الحكم\s+الشرعي|الفقه|فقهي|فقهية)(?![ء-ي])",
    re.IGNORECASE,
)

VERDICT_PERSONAL = "personal_ruling"
VERDICT_PERMISSIVE = "permissibility_claim"
VERDICT_REPORTED = "reported_ruling"

# Keywords that indicate a scientific miracle claim
_SCIENTIFIC_MIRACLE_KEYWORDS = frozenset({
    "scientific miracle", "science proves", "quran predicted", "modern science",
    "big bang", "embryology", "astronomy", "expanding universe",
    "mountains as pegs", "إعجاز علمي", "العلم يثبت", "أثبت العلم",
    "الإعجاز العلمي", "النظرية العلمية", "علميًا", "توسع الكون",
    "الجبال أوتاد", "علم الأجنة",
    "scientifically proven", "scientific proof", "science confirms",
})

# Phrases that assert a definitive link between a verse and a modern theory.
# Any answer containing these in a scientific context must be hard-blocked.
_DEFINITIVE_SCIENTIFIC_CLAIM_PHRASES = frozenset({
    "this verse proves modern science",
    "the quran definitively refers to",
    "the quran definitively means",
    "science has confirmed the tafsir",
    "proves the big bang",
    "proves the theory",
    "definitively proves",
    "quran has proven",
    "proves modern",
    # Arabic equivalents
    "تثبت هذه الآية نظرية",
    "يثبت القرآن نظرية",
    "أثبت العلم صحة تفسير",
    "هذه الآية تثبت",
    "القرآن يثبت نظرية",
})

# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class AyahRef:
    """A parsed surah:ayah reference."""
    surah: int
    ayah_start: int
    ayah_end: Optional[int] = None  # None means single ayah
    raw: str = ""

    @property
    def is_valid(self) -> bool:
        if not (1 <= self.surah <= TOTAL_SURAHS):
            return False
        max_ayah = SURAH_AYAH_COUNTS[self.surah - 1]
        if not (1 <= self.ayah_start <= max_ayah):
            return False
        if self.ayah_end is not None:
            if self.ayah_end < self.ayah_start or self.ayah_end > max_ayah:
                return False
        return True


@dataclass
class GuardResult:
    """Result of QuranAnswerGuard validation."""
    passed: bool
    # Hard-block reason — if set, the caller must replace the answer
    hard_block_reason: Optional[str] = None
    # Non-fatal warnings to append to the response
    warnings: List[str] = field(default_factory=list)
    # Labels the caller must attach to the answer card
    required_labels: List[str] = field(default_factory=list)
    # Refs that were found invalid
    invalid_refs: List[str] = field(default_factory=list)
    # Source IDs that were found invalid
    invalid_source_ids: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Guard
# ---------------------------------------------------------------------------

class QuranAnswerGuard:
    """
    Validates AI-assisted Quranic answers before they reach users.

    Usage:
        guard = QuranAnswerGuard()
        result = guard.validate(
            answer_text="...",
            source_ids=["ibn_kathir_ar"],
            intent="tafsir_summary",
            is_translation=False,
        )
        if not result.passed:
            return safe_refusal_response(result.hard_block_reason)
        # attach result.warnings and result.required_labels to response
    """

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def validate(
        self,
        answer_text: str,
        source_ids: List[str],
        intent: str,
        *,
        is_translation: bool = False,
        generated: bool = False,
    ) -> GuardResult:
        """
        Run all guard checks on an answer before it is returned to the user.

        Args:
            answer_text: The full text of the AI-generated answer.
            source_ids: Source IDs cited in this answer.
            intent: Question intent (tafsir_summary, fatwa_like, scientific_miracle_claim, etc.)
            is_translation: True if this answer is a translation, not tafsir.
            generated: True for model output (the RAG pipeline). Fatwa content is
                then detected by ruling ASSERTIONS ("it is haram", "يجوز لك")
                rather than by bare keywords that also occur in tafsir prose.

        Returns:
            GuardResult. If passed=False, the caller must substitute the safe refusal.
        """
        warnings: List[str] = []
        labels: List[str] = []

        # Rule 1: fatwa-like intent or content → hard block
        fatwa_block = self._check_fatwa(answer_text, intent, generated=generated)
        if fatwa_block:
            return GuardResult(
                passed=False,
                hard_block_reason=fatwa_block,
            )

        # Rule 2: no source citations → hard block
        if not source_ids:
            return GuardResult(
                passed=False,
                hard_block_reason=(
                    "Answer has no source citations — cannot verify provenance. "
                    "No verified source available."
                ),
            )

        # Rule 3: unknown source IDs → hard block
        invalid_sources = [sid for sid in source_ids if sid not in TRUSTED_SOURCE_IDS]
        if invalid_sources:
            return GuardResult(
                passed=False,
                hard_block_reason=(
                    f"Answer cites unknown source IDs: {invalid_sources}. "
                    "Only registered trusted sources are allowed."
                ),
                invalid_source_ids=invalid_sources,
            )

        # Rule 4: validate all ayah references found in the answer text
        invalid_refs = self._check_ayah_refs(answer_text)
        if invalid_refs:
            return GuardResult(
                passed=False,
                hard_block_reason=(
                    f"Answer contains invalid ayah references: "
                    f"{[r.raw for r in invalid_refs]}. "
                    "These verse references do not exist in the Quran."
                ),
                invalid_refs=[r.raw for r in invalid_refs],
            )

        # Rule 5: scientific miracle claims → mandatory caution label + warning
        if self._is_scientific_miracle(answer_text, intent):
            # 5a. Hard-block if answer makes a definitive scientific claim
            definitive_block = self._check_definitive_scientific_claim(answer_text)
            if definitive_block:
                return GuardResult(
                    passed=False,
                    hard_block_reason=definitive_block,
                )
            caution_en = (
                "Connecting an ayah to scientific theories requires specialized "
                "scholarly and scientific review. This is presented as a "
                "contemporary reflection, not a definitive tafsir position."
            )
            caution_ar = (
                "الربط بين الآية والنظريات العلمية يحتاج إلى مراجعة علمية وشرعية متخصصة. "
                "هذا الطرح تأمل معاصر وليس موقفًا تفسيريًا قطعيًا."
            )
            warnings.append(caution_en)
            warnings.append(caution_ar)
            labels.append("scientific_reflection_needs_review")
            labels.append("needs_scholarly_and_scientific_review")
            labels.append("contemporary_reflection_not_tafsir")

        # Rule 6: translation must carry a label
        if is_translation:
            labels.append("translation_not_quran_text")

        return GuardResult(
            passed=True,
            warnings=warnings,
            required_labels=labels,
        )

    # -------------------------------------------------------------------------
    # Ayah reference validation
    # -------------------------------------------------------------------------

    def parse_ayah_refs(self, text: str) -> List[AyahRef]:
        """Extract all surah:ayah references from text."""
        refs: List[AyahRef] = []
        for match in _VERSE_REF_PATTERN.finditer(text):
            surah = int(match.group(1))
            ayah_start = int(match.group(2))
            ayah_end = int(match.group(3)) if match.group(3) else None
            refs.append(AyahRef(
                surah=surah,
                ayah_start=ayah_start,
                ayah_end=ayah_end,
                raw=match.group(0).strip(),
            ))
        return refs

    def is_valid_ayah_ref(self, surah: int, ayah: int) -> bool:
        """Return True if surah:ayah exists in the canonical corpus."""
        if not (1 <= surah <= TOTAL_SURAHS):
            return False
        return 1 <= ayah <= SURAH_AYAH_COUNTS[surah - 1]

    # -------------------------------------------------------------------------
    # Internal checks
    # -------------------------------------------------------------------------

    def _check_ayah_refs(self, text: str) -> List[AyahRef]:
        """Return list of invalid AyahRef objects found in text."""
        return [ref for ref in self.parse_ayah_refs(text) if not ref.is_valid]

    def _check_fatwa(self, text: str, intent: str, generated: bool = False) -> Optional[str]:
        """Return a hard-block reason if fatwa-like content is detected."""
        if intent == "fatwa_like":
            return (
                "This platform does not issue religious rulings (fatwas). "
                "Please consult a qualified Islamic scholar. — "
                "هذه المنصة لا تُصدر فتاوى دينية. يُرجى الرجوع إلى عالم إسلامي مؤهل."
            )
        text_lower = text.lower()
        if generated:
            hits = any(p.search(text) for p in _RULING_ASSERTIONS) or any(
                kind == VERDICT_PERSONAL for kind, _s, _subj in self.find_verdicts(text)
            )
        else:
            hits = any(kw.lower() in text_lower for kw in _FATWA_KEYWORDS)
        if hits:
            return (
                "Answer contains fatwa-like content. "
                "This platform provides informational tafsir only, not religious rulings. "
                "— هذه المنصة تقدم معلومات تفسيرية فقط، ولا تُصدر أحكامًا دينية."
            )
        return None

    # -------------------------------------------------------------------------
    # Verdicts in generated answers
    # -------------------------------------------------------------------------

    def find_verdicts(self, text: str) -> List[Tuple[str, str, str]]:
        """
        Rulings stated by a generated answer, sentence by sentence.

        Returns (kind, sentence, subject) triples. ``kind`` is
        VERDICT_PERSONAL (a ruling addressed to the reader, the validity of
        their worship, takfir: never allowed, cited or not),
        VERDICT_REPORTED (a verse's command paraphrased in the second person,
        or a general statement of a rule: allowed only when the cited
        evidence states it) or VERDICT_PERMISSIVE (a permissibility claim
        about ``subject``, allowed only when the cited evidence states it).
        Pass the answer with its verbatim quotations removed.
        """
        out: List[Tuple[str, str, str]] = []
        for sentence in _split_sentences(text):
            if any(p.search(sentence) for p in _PERSONAL_VERDICTS):
                out.append((VERDICT_PERSONAL, sentence, ""))
                continue
            m = _YOU_MUST.search(sentence)
            if m:
                frame = REPORTING_FRAME.search(sentence, 0, m.start())
                out.append((VERDICT_REPORTED if frame else VERDICT_PERSONAL, sentence, ""))
                continue
            if any(p.search(sentence) for p in _GENERAL_RULINGS):
                out.append((VERDICT_REPORTED, sentence, ""))
                continue
            for p in _PERMISSIVE_VERDICTS:
                m = p.search(sentence)
                if m:
                    subject = (m.groupdict().get("subj") or "").strip()
                    out.append((VERDICT_PERMISSIVE, sentence, subject))
                    break
        return out

    @staticmethod
    def has_ruling_vocabulary(text: str) -> bool:
        """True when the answer speaks of rulings (it then carries the fiqh disclaimer)."""
        return bool(_RULING_VOCABULARY.search(text or ""))

    def _is_scientific_miracle(self, text: str, intent: str) -> bool:
        """Return True if the answer relates to a scientific miracle claim."""
        if intent == "scientific_miracle_claim":
            return True
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in _SCIENTIFIC_MIRACLE_KEYWORDS)

    def _check_definitive_scientific_claim(self, text: str) -> Optional[str]:
        """
        Return a hard-block reason if the answer asserts a definitive link
        between a Quranic verse and a modern scientific theory.

        Per the scientific-miracle-claims-policy.md: phrases like
        "this verse proves modern science" or "science has confirmed the tafsir"
        present a scientific theory as definitive tafsir, which is prohibited
        without specialized scholarly and scientific review.
        """
        text_lower = text.lower()
        for phrase in _DEFINITIVE_SCIENTIFIC_CLAIM_PHRASES:
            if phrase.lower() in text_lower:
                return (
                    f"Answer contains a definitive scientific claim: '{phrase}'. "
                    "Scientific theories must not be presented as definitive tafsir. "
                    "Per the platform's scientific-miracle-claims-policy: this requires "
                    "specialized scholarly and scientific review before display. "
                    "— الربط القطعي بين الآيات والنظريات العلمية ممنوع بدون مراجعة علمية وشرعية متخصصة."
                )
        return None


_SENTENCES = re.compile(r"(?<=[.!?؟۔;؛])\s+|\n+")


def _split_sentences(text: str) -> List[str]:
    return [s for s in _SENTENCES.split(text or "") if s and s.strip()]


# Module-level singleton
quran_answer_guard = QuranAnswerGuard()
