"""
Deontic language: ruling requests in questions, ruling claims in answers.

One bilingual model of how a religious ruling is expressed, used on both
sides of generation:

* questions — ``ruling_request()`` decides whether the user asks for a
  verdict (fatwa) in any person or register: "can I…", "is it allowed for me",
  "am I sinning", "do I have to", "what do I owe", "is X a kafir", "are we
  still married", "هل يجوز لي/لنا", "يلزمني", "أفتني", "هل أنا مسلم",
  "هل يكفر من…", MSA or dialect. Such questions are routed to the
  consult-a-scholar response with sourced context only.
* answers — ``ruling_claims()`` finds sentences that state a ruling: who it is
  addressed to (the reader / the speaker / people in general), its deontic
  class (permitted, forbidden, obligatory, valid/invalid, takfir) and its
  subject, so the caller can refuse personal verdicts and takfir outright and
  keep a general ruling only when the cited evidence states it.

Arabic is matched on normalised tokens with clitics segmented (و/ف/ب/ل/ك/
س/ال/أ before, pronoun suffixes after), so "أيجوز", "فيجوز", "يجوزلي",
"يلزمني", "صلاتي" need no phrase list of their own.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Sequence, Set, Tuple

from app.safety.grounding import normalize_arabic

# ------------------------------------------------------------ deontic classes

PERMIT = "permit"
FORBID = "forbid"
OBLIGE = "oblige"
VALIDITY = "validity"
STATUS = "status"        # takfir / religious status of a person

# Person the ruling is addressed to / asked about.
SECOND = "second"        # the reader ("you", "لك")
FIRST = "first"          # the speaker ("I", "we", "لي", "صلاتي")
GENERAL = "general"      # people in general / a category ("whoever", "a Muslim")

# ------------------------------------------------------------------ Arabic

_PROCLITICS = ("وال", "فال", "بال", "كال", "لل", "ال", "و", "ف", "ب", "ل", "ك", "س", "ا")
_ENCLITICS = ("كما", "هما", "كم", "كن", "هم", "هن", "نا", "ني", "ها", "ه", "ك", "ي")


def ar_tokens(text: str) -> List[str]:
    return normalize_arabic(text).split()


def segment(tok: str) -> Set[str]:
    """Candidate stems of an Arabic token with up to two proclitics and one
    enclitic removed (all candidates, the caller matches against a lexicon)."""
    out = {tok}
    heads = {tok}
    for _ in range(2):
        nxt = set()
        for h in heads:
            for p in _PROCLITICS:
                if h.startswith(p) and len(h) - len(p) >= 2:
                    nxt.add(h[len(p):])
        out |= nxt
        heads = nxt
    for h in list(out):
        for s in _ENCLITICS:
            if h.endswith(s) and len(h) - len(s) >= 2:
                base = h[: -len(s)]
                out.add(base)
                if base.endswith("ت"):
                    out.add(base[:-1] + "ه")  # صلاتك -> صلاه
    return out


def _ar_set(words: str) -> frozenset:
    return frozenset(normalize_arabic(w) for w in words.split())


# Deontic predicates (normalised forms; hamza folded to alef, ة to ه, ى to ي).
_AR_PERMIT = _ar_set(
    "يجوز تجوز جائز جائزه الجواز يحل تحل حلال مباح مباحه يباح تباح ابيح اباح مسموح مسموحه رخصه "
    "رخص يرخص بأس باس حرج جناح عادي عادى ينفع يصير مانع مشكله"
)
_AR_FORBID = _ar_set(
    "يحرم تحرم حرام محرم محرمه محرما محرمه ممنوع ممنوعه منهي ياثم تاثم اثمت اثم"
)
_AR_OBLIGE = _ar_set(
    "يجب تجب وجب واجب واجبه الوجوب فرض فريضه مفروض مفروضه يلزم تلزم يلزمك لازم لازمه يتوجب يتعين "
    "ملزم ملزمه مطالب"
)
_AR_VALIDITY = _ar_set(
    "يصح تصح صحيح صحيحه باطل باطله يبطل تبطل بطلت بطل يفسد تفسد فاسد فاسده ينقض تنقض ينتقض تنتقض "
    "مقبول مقبوله تقبل يقبل يقع تقع وقع واقع نافذ يحتسب تحتسب تجزئ يجزئ يجزي تجزي"
)
_AR_STATUS = _ar_set("كافر كافره كفار يكفر مرتد مرتده مشرك مشركه الكافر المرتد")
_AR_RULING_NOUN = _ar_set("حكم الحكم فتوي فتاوي افتني افتوني افتونا استفتاء")

# Acts whose validity / obligations are asked about.
_AR_ACTS = _ar_set(
    "صلاه صلاتي صلاتنا الصلاه صوم صيام الصوم الصيام وضوء الوضوء غسل الغسل زواج الزواج نكاح النكاح "
    "طلاق الطلاق طالق طلقه زكاه الزكاه حج الحج عمره العمره يمين كفاره الكفاره فديه الفديه قضاء "
    "متزوجين متزوجون متزوج متزوجه زوجتي زوجي مسلم مسلمه مسلما"
)
# Personal markers: first-person pronouns / suffixed forms.
_AR_FIRST_WORDS = _ar_set("لي لنا علي علينا انا نحن عندي عندنا مني منا ني")
_AR_SECOND_WORDS = _ar_set("لك لكي عليك عليكي انت انتي وعليك فعليك")
_AR_INTERROGATIVE = _ar_set("هل ما ماذا كيف متي كم ايش شو وش ليش")
# Words that make a deontic token part of a name, not a ruling.
_AR_SACRED_HEADS = _ar_set("المسجد مسجد البيت بيت الشهر شهر المشعر الاشهر البلد بلد حرم")
_ALLAH_AGENT = _ar_set("الله تعالي سبحانه ربنا ربكم الرب")
# Verb forms reporting what Allah legislated ("حرّم الله…", "أحلّ الله…").
_AR_LEGISLATE = _ar_set("حرم احل فرض اوجب كتب نهي امر شرع اباح")
# Tafsir framing of a question: meaning, wisdom, explanation, occasion.
_AR_STATUS_SUBJECT = _ar_set("من ومن فمن كل وكل تارك وتارك الذي التي الذين فهو فهي فانه فانها هو هي فقد يعتبر يعد "
                             "انت وانت فانت انه انها")
_AR_NEGATORS = _ar_set("لا ولا فلا ليس ليست غير لم لن")
_AR_TAFSIR_FRAME = _ar_set("معني تفسير الحكمه حكمه لماذا لم سبب مراد تاويل دلاله يفسر فسر اشرح")


def _ar_classes(tok: str) -> Set[str]:
    cands = segment(tok)
    out = set()
    if cands & _AR_PERMIT:
        out.add(PERMIT)
    if cands & _AR_FORBID:
        out.add(FORBID)
    if cands & _AR_OBLIGE:
        out.add(OBLIGE)
    if cands & _AR_VALIDITY:
        out.add(VALIDITY)
    if cands & _AR_STATUS:
        out.add(STATUS)
    return out


def _ar_first_person(tokens: Sequence[str], raw: str = "") -> bool:
    raw_words = set(re.findall(r"[\u0621-\u064a]+", re.sub(r"[\u064b-\u0652\u0670]", "", raw))) if raw else set()
    for t in tokens:
        if t in ("علي",) and raw and "علي" not in raw_words and "وعلي" not in raw_words and "فعلي" not in raw_words:
            continue  # the preposition "على", not "عليّ"
        if t in _AR_FIRST_WORDS:
            return True
        # Suffixed first person on a deontic verb or act noun: "يلزمني",
        # "صلاتي", "زوجي", "علينا".
        if len(t) > 3 and (t.endswith("ني") or t.endswith("تي") or t.endswith("نا")):
            base = t[:-2]
            if segment(base) & (_AR_OBLIGE | _AR_PERMIT | _AR_ACTS | _AR_VALIDITY | _AR_FORBID) or \
                    segment(t) & _AR_ACTS:
                return True
        if t.endswith("ي") and segment(t) & _AR_ACTS and t not in ("مسلمي",):
            return True
    return False


def _ar_second_person(tokens: Sequence[str]) -> bool:
    for t in tokens:
        if t in _AR_SECOND_WORDS:
            return True
        # "صلاتك", "يلزمك", "طلاقك": a deontic word or act noun with the
        # second-person suffix.
        if len(t) > 3 and t.endswith(("ك", "كم", "كي")) and \
                segment(t) & (_AR_OBLIGE | _AR_PERMIT | _AR_ACTS | _AR_VALIDITY):
            return True
    return False


def _ar_deontic_hits(tokens: Sequence[str]) -> List[Tuple[int, Set[str]]]:
    hits = []
    for i, t in enumerate(tokens):
        cls = _ar_classes(t)
        if not cls:
            continue
        prev = tokens[i - 1] if i else ""
        nxt = tokens[i + 1] if i + 1 < len(tokens) else ""
        # "المسجد الحرام", "الشهر الحرام", "حرم مكة": names.
        if (FORBID in cls or PERMIT in cls) and prev in _AR_SACRED_HEADS:
            continue
        if t in ("محرم",) and prev in ("شهر",):
            continue
        # "لا بأس / لا حرج / لا جناح / ما في مانع" are permissions only when negated.
        if segment(t) & _ar_set("بأس باس حرج جناح مانع مشكله") and prev not in (
                "لا", "ولا", "فلا", "ليس", "غير", "ما", "مافي", "في", "مافيه", "بدون"):
            continue
        # Dialect "عادي" / "ينفع" / "يصير" are a permission only with an act
        # addressed to someone ("عادي تسمع…", "ينفع أصلي…").
        if segment(t) & _ar_set("عادي عادى ينفع يصير") and not (
                i + 1 < len(tokens) and tokens[i + 1][:1] in "تاين" and not tokens[i + 1].startswith("ال")):
            continue
        # Negation flips permission and prohibition: "لا يجوز", "لا يحل",
        # "ليس بحرام", "غير محرم".
        if prev in _AR_NEGATORS or (i >= 2 and tokens[i - 2] in _AR_NEGATORS and prev in ("ب", "من")):
            flipped = set()
            for c in cls:
                flipped.add({PERMIT: FORBID, FORBID: PERMIT, OBLIGE: PERMIT}.get(c, c))
            if segment(t) & _ar_set("بأس باس حرج جناح"):
                flipped = {PERMIT}
            cls = flipped
        # "حرّم الله" / "أحلّ الله": the verse's legislation, reported.
        if nxt in _ALLAH_AGENT or prev in _ALLAH_AGENT:
            cls = {c + ":reported" for c in cls}
        hits.append((i, cls))
    return hits


# ------------------------------------------------------------------ English

_EN = re.compile(r"[a-z]+(?:'[a-z]+)?")


def _en_tokens(text: str) -> List[str]:
    t = unicodedata.normalize("NFKC", text or "").lower().replace("’", "'").replace("‘", "'")
    return _EN.findall(t)


_EN_PERMIT_WORDS = {"permissible", "permitted", "allowed", "lawful", "halal", "acceptable", "fine", "ok",
                    "okay", "alright", "legitimate", "allowable"}
_EN_FORBID_WORDS = {"forbidden", "prohibited", "haram", "unlawful", "impermissible", "sinful", "sin",
                    "sins", "sinning", "sinner", "makruh", "disliked", "wrong"}
_EN_OBLIGE_WORDS = {"obligatory", "mandatory", "compulsory", "required", "obliged", "obligated", "obligation",
                    "duty", "owe", "owes", "wajib", "fard", "binding"}
_EN_VALIDITY_WORDS = {"valid", "invalid", "void", "nullified", "nullifies", "invalidates", "invalidated",
                      "binding"}
_EN_STATUS_WORDS = {"kafir", "kafirs", "kaafir", "kuffar", "disbeliever", "disbelievers", "apostate",
                    "apostates", "murtad", "murtads", "infidel", "infidels"}
_EN_FIRST = {"i", "me", "my", "myself", "we", "us", "our", "ourselves", "i'm", "i've", "we're"}
_EN_SECOND = {"you", "your", "yours", "yourself", "yourselves", "you're", "you've", "u"}
_EN_ACTS = {"prayer", "prayers", "pray", "salah", "salat", "fast", "fasts", "fasting", "sawm", "wudu",
            "wudhu", "ablution", "ghusl", "marriage", "married", "nikah", "divorce", "divorced", "talaq",
            "hajj", "umrah", "zakat", "zakah", "oath", "kaffara", "fidya", "fidyah", "hijab", "muslim"}
# Modal frames that ask permission/obligation for the speaker.
_EN_ASK_FIRST = re.compile(
    r"\b(can|may|could|should|must|shall)\s+(i|we)\b"
    r"|\b(do|does|did|will|would)\s+(i|we)\s+(have|need|got)\s+to\b"
    r"|\b(am\s+i|are\s+we|was\s+i|were\s+we|will\s+i|would\s+i|will\s+we)\b"
    r"|\b(is|was|would|will)\s+it\s+(be\s+)?(ok|okay|fine|alright|allowed|permissible|permitted|halal|haram|"
    r"forbidden|wrong|a\s+sin|sinful|obligatory|required|acceptable|lawful)\s+(for\s+(me|us)|if\s+(i|we)|to)\b"
    r"|\bwhat\s+(do|should|must)\s+(i|we)\s+(owe|pay|do|give|make\s+up)\b"
    r"|\bhow\s+(much|many)\b[^?]{0,40}\b(do|should|must)\s+(i|we)\s+(owe|pay|give|make\s+up|fast)\b"
    r"|\b(do|does)\s+(my|our)\b",
)
_EN_RETRIEVAL = re.compile(
    r"^(get|see|read|learn|know|find|understand|hear|ask|look|study|watch|explore|compare|search|view|"
    r"access|share|save|bookmark|use|reflect|begin|start|continue|listen|memori[sz]e|ponder|apply|"
    r"benefit|improve|draw|connect|relate|teach|explain|tell|cite|quote|summari[sz]e)\b"
)
_EN_TAFSIR_FRAME = re.compile(
    r"\b(what\s+does\s+(the\s+)?(verse|ayah|quran|surah|tafsir)|meaning\s+of|tafsir\s+of|why\s+did\s+"
    r"(allah|god)|why\s+does\s+(allah|god|the\s+quran)|how\s+do(es)?\s+(the\s+)?(scholars|commentators|"
    r"tafsir|mufassir)|according\s+to\s+(the\s+)?(verse|tafsir|ibn|al-)|in\s+(the\s+)?(verse|ayah|surah)\b|"
    r"\d{1,3}\s*:\s*\d{1,3})",
)


# The deontic word is the predicate asked about: "is my prayer valid",
# "would it be a sin", "is this allowed for us" (not "after a major sin").
_EN_ASKED_PREDICATE = re.compile(
    r"\b(is|are|am|was|were|would|will|does|do)\b(\s+\w+){0,5}?\s+(be\s+)?(considered\s+|counted\s+)?"
    r"(allowed|permissible|permitted|haram|halal|forbidden|prohibited|a\s+sin|sinful|sinning|obligatory|"
    r"required|mandatory|valid|invalid|void|wrong|makruh|lawful|unlawful|ok|okay|fine|acceptable|binding)\b"
)


@dataclass
class RulingRequest:
    person: str
    classes: Set[str] = field(default_factory=set)
    reason: str = ""


def ruling_request(question: str) -> Optional[RulingRequest]:
    """A request for a religious verdict, or None for an ordinary question."""
    q = (question or "").strip()
    if not q:
        return None
    if re.search(r"[؀-ۿ]", q):
        r = _ar_ruling_request(q)
        if r:
            return r
    return _en_ruling_request(q)


def _ar_ruling_request(q: str) -> Optional[RulingRequest]:
    toks = ar_tokens(q)
    if not toks:
        return None
    seg = [segment(t) for t in toks]
    raw = unicodedata.normalize("NFKC", q)
    hukm = re.search(
        r"(?<![ء-ي])[وف]?(ما|وما|ماهو|ما\s+هو|عن|اعرف|أعرف|معرفة|بين\s+لي|أخبرني\s+عن|اخبرني\s+عن|شو|ايش|إيش|"
        r"وش|ويش|شنو|شنهو|ايه|إيه|يعني\s+ايش)\s+(ال)?حكم"
        r"(ه|ها|هما|هم)?(?![ء-ي\u064b-\u0652])"
        r"|^\s*(ال)?حكم\s+(?!الله\s|داود|سليمان|بين)"
        r"|(?<![ء-ي])(ال)?حكم\s+(الشرع|الشريعة|الإسلام|الاسلام|الدين|الفقه)(?![ء-ي])"
        r"|(?<![ء-ي])(الحكم|حكمه|حكمها)\s+(الشرعي|الفقهي)(?![ء-ي])", raw)
    fatwa = any(s & _ar_set("فتوي فتاوي افتني افتوني افتونا استفتاء") for s in seg)
    if hukm or fatwa:
        # "ما حكم…", "أفتني", "فتوى" — not "حكمة" (wisdom), not "ما معنى
        # الحكم في قوله…".
        before = normalize_arabic(raw[:hukm.start()]).split()[-2:] if hukm else []
        if fatwa or not any(t in _AR_TAFSIR_FRAME for t in before):
            return RulingRequest(GENERAL, set(), "ruling_noun")
    first = _ar_first_person(toks, q)
    second = _ar_second_person(toks)
    asks = bool(set(toks) & _AR_INTERROGATIVE) or "؟" in q or "?" in q or toks[0].startswith("ا") and \
        bool(segment(toks[0][1:]) & (_AR_PERMIT | _AR_FORBID | _AR_OBLIGE | _AR_VALIDITY))
    hits = []
    for i, cls in _ar_deontic_hits(toks):
        t = toks[i]
        # "للحلال والحرام", "الكفار": nouns naming a category, not a predicate.
        if t.startswith(("ال", "لل", "وال", "فال", "بال", "كال")) and not (segment(t) & _AR_LEGISLATE):
            continue
        # Acceptance (of repentance, of a sacrifice) is hope, not a verdict.
        if segment(t) & _ar_set("تقبل يقبل مقبول مقبوله تقبلت"):
            continue
        hits.append((i, cls))
    own = [c for _, cls in hits for c in cls if not c.endswith(":reported")]
    framed = any(t in _AR_TAFSIR_FRAME for t in toks)
    story = bool(re.search(r"في\s+(القرآن|الآية|الاية|السورة|سورة|قصة|القصة)", q))
    if STATUS in own and not (first or second or any(t in _AR_STATUS_SUBJECT for t in toks)) or story:
        own = [c for c in own if c != STATUS]
    acts = any(s & _AR_ACTS for s in seg)
    person = FIRST if first else (SECOND if second else GENERAL)
    if own and asks:
        if first or second:
            return RulingRequest(person, set(own), "personal_deontic")
        if not framed:
            return RulingRequest(GENERAL, set(own), "general_deontic")
    # "ماذا علي؟", "كم يجب علي", "هل علي قضاء" — obligations of the speaker.
    if asks and first and (acts or re.search(r"(?<![ء-ي])[وف]?(علي|عليّ|علينا)(?![ء-ي\u064b-\u0652])", q)) \
            and not framed:
        return RulingRequest(FIRST, {OBLIGE}, "personal_act")
    # "هل أنا مسلم؟", "هل ما زلنا متزوجين؟" — the speaker's status.
    if asks and first and acts:
        return RulingRequest(FIRST, {STATUS}, "personal_status")
    return None


def _en_ruling_request(q: str) -> Optional[RulingRequest]:
    low = unicodedata.normalize("NFKC", q).lower().replace("’", "'")
    toks = _en_tokens(low)
    tset = set(toks)
    framed = bool(_EN_TAFSIR_FRAME.search(low))
    m = _EN_ASK_FIRST.search(low)
    if m:
        rest = low[m.end():].strip()
        if re.match(r"(can|may|could|should|must|shall)\s+(i|we)\b", m.group(0)):
            rest = re.sub(r"^(also|please|still|really|ever|just)\s+", "", rest)
            if _EN_RETRIEVAL.match(rest) and not (tset & (_EN_PERMIT_WORDS | _EN_FORBID_WORDS | _EN_OBLIGE_WORDS
                                                           | {"wudu", "ablution", "menstruating", "period",
                                                              "junub", "janabah"})):
                m = None
        elif re.match(r"(am\s+i|are\s+we|was\s+i|were\s+we|will\s+i|would\s+i|will\s+we)", m.group(0)):
            # "Am I allowed / sinning / still a Muslim / a kafir", "are we still married"
            words = set(_en_tokens(rest[:60]))
            if not words & (_EN_PERMIT_WORDS | _EN_FORBID_WORDS | _EN_OBLIGE_WORDS | _EN_VALIDITY_WORDS
                            | _EN_STATUS_WORDS | _EN_ACTS | {"punished", "accountable", "divorced", "allowed",
                                                             "permitted", "still"}):
                m = None
        elif m.group(0).startswith(("do my", "does my", "do our", "does our")):
            words = set(_en_tokens(rest[:60]))
            if not words & (_EN_ACTS | {"break", "breaks", "invalidate", "nullify", "count"}):
                m = None
        if m:
            return RulingRequest(FIRST, set(), "personal_modal")
    if tset & _EN_STATUS_WORDS and re.search(
            r"\b(is|are|am|was|were|becomes?|become)\s+(i|he|she|they|someone|somebody|anyone|anybody|a\s+person|"
            r"a\s+muslim|muslims|people|whoever|one|my\s+\w+|the\s+one|those)\b", low) and not framed:
        return RulingRequest(GENERAL, {STATUS}, "status")
    if re.search(r"\b(leave|leaves|left|exit|exits|exited|go|goes|out)\s+(out\s+of\s+)?(the\s+fold\s+of\s+)?"
                 r"(islam|the\s+religion|the\s+faith|the\s+deen)\b", low) and ("?" in q or toks[:1] and toks[0] in
                                                                                  {"does", "do", "is", "will", "would"}):
        return RulingRequest(FIRST if tset & _EN_FIRST else GENERAL, {STATUS}, "status")
    if re.search(r"\b(is|are|was|were|will|would)\b[^?]{0,60}\b(" + "|".join(sorted(_EN_ACTS)) + r")\b[^?]{0,50}"
                 r"\b(valid|invalid|void|binding|accepted\s+as\s+valid|nullified|sound)\b", low) and not framed:
        return RulingRequest(FIRST if tset & _EN_FIRST else GENERAL, {VALIDITY}, "validity")
    if re.search(r"\b(still|no\s+longer)\s+(a\s+)?(muslim|married|believer)\b", low):
        person = FIRST if tset & _EN_FIRST else GENERAL
        return RulingRequest(person, {STATUS}, "status")
    # Personal deontic / validity questions: "is my prayer valid", "is it a sin for me".
    if tset & _EN_FIRST and _EN_ASKED_PREDICATE.search(low):
        return RulingRequest(FIRST, set(), "personal_deontic")
    if tset & _EN_FIRST and tset & _EN_ACTS and re.search(r"\b(owe|make\s+up|missed|repay|expiat|break|broke)", low):
        return RulingRequest(FIRST, {OBLIGE}, "personal_act")
    return None


# ------------------------------------------------------------ answer claims

@dataclass
class RulingClaim:
    person: str              # SECOND / FIRST / GENERAL
    cls: str                 # PERMIT / FORBID / OBLIGE / VALIDITY / STATUS
    sentence: str
    subject: str             # the sentence with deontic words and framing removed
    reported: bool = False   # framed as what Allah / the verse legislates


_EN_CLAIM_PATTERNS: Tuple[Tuple[str, re.Pattern], ...] = tuple((cls, re.compile(p, re.IGNORECASE)) for cls, p in (
    (STATUS, r"\b(is|are|becomes?|became|has\s+become|have\s+become|will\s+become|would\s+be|remains?)\s+"
             r"(no\s+longer\s+|not\s+|now\s+|then\s+)?(a\s+|an\s+)?(muslims?|believers?|kafirs?|kaafirs?|kuffar|"
             r"disbelievers?|apostates?|murtads?|infidels?|non-?muslims?)\b"),
    (STATUS, r"\b(left|leaves|leave|exited|exits|exit|out\s+of|outside|expelled\s+from|outside\s+the\s+fold\s+of)\s+"
             r"(the\s+fold\s+of\s+)?(islam|the\s+religion|the\s+faith)\b"),
    (STATUS, r"\b(kafir|kaafir|apostate|murtad)\b"),
    (VALIDITY, r"\b(is|are|was|were|be|becomes?|remains?)\s+(still\s+|not\s+|now\s+)?(valid|invalid|void|"
               r"nullified|broken|sound|binding|effective)\b"),
    (VALIDITY, r"\b(does|do|did|will|would)\s*(not|n't)?\s+(count|take\s+effect|break|invalidate|nullify|"
               r"void)\b|\b(breaks|invalidates|nullifies|voids)\s+(the|your|his|her|their|a)\b"
               r"|\bdoes\s+not\s+count\b|\bdoesn't\s+count\b"),
    (OBLIGE, r"\b(is|are|was|were|be)\s+(also\s+|therefore\s+|thus\s+|then\s+|still\s+)?(obligatory|mandatory|"
             r"compulsory|required|obliged|obligated|wajib|fard|a\s+duty|an\s+obligation)\b"),
    (OBLIGE, r"\b(must(?!\s+not)|have\s+to|has\s+to|need\s+to|needs\s+to|ought\s+to|owe|owes)\b"),
    (FORBID, r"\b(is|are|was|were|be)\s+(also\s+|therefore\s+|thus\s+|then\s+|clearly\s+|strictly\s+)?"
             r"(haram|forbidden|prohibited|unlawful|impermissible|sinful|makruh|disliked|"
             r"a\s+(major\s+|grave\s+|minor\s+)?sin|wrong)\b"),
    (FORBID, r"\b(is|are|was|were|be)\s+not\s+(lawful|permissible|permitted|allowed|halal|acceptable)\b"),
    (FORBID, r"\b(must\s+not|may\s+not|cannot|can't|should\s+not|shouldn't|not\s+allowed\s+to|"
             r"not\s+permitted\s+to)\b"),
    (PERMIT, r"\b(is|are|was|were|be)\s+(now\s+|therefore\s+|thus\s+|then\s+|also\s+|completely\s+|totally\s+|"
             r"perfectly\s+|clearly\s+|fully\s+|quite\s+)?(permissible|permitted|allowed|lawful|halal|"
             r"acceptable|fine|ok|okay|alright|legitimate|no\s+sin|not\s+a\s+sin|not\s+haram|not\s+forbidden|"
             r"not\s+prohibited|not\s+sinful)\b"),
    (PERMIT, r"\b(no|nothing)\s+(harm|sin|blame|problem|issue|wrong)\s+(in|with|if|for)\b|\bnothing\s+wrong\b"
             r"|\b(you|one|anyone|anybody|a\s+(person|muslim|woman|man|believer|traveller|traveler)|muslims|"
             r"believers|women|men|people|someone|whoever)\s+(\w+\s+){0,2}?(may|can|is\s+free\s+to|are\s+free\s+to)\s+"
             r"(still\s+|also\s+|even\s+|safely\s+|freely\s+|simply\s+)?(?!(see|read|learn|reflect|ponder|find|notice|"
             r"understand|consult|ask|refer|recite\s+it\s+and\s+reflect|look|hope|trust|turn\s+to|seek\s+forgiveness|"
             r"repent|remember|thank|benefit)\b)[a-z]+\b"),
))
# Frames that report what Allah / the verse / a source says.
_EN_REPORT_FRAME = re.compile(
    r"\b(allah|god|the\s+lord|the\s+(verse|ayah|passage|surah|qur'?an|tafsir|commentary)|this\s+(verse|ayah|"
    r"passage)|these\s+verses|ibn\s+\w+|al-\w+|imam\s+\w+|[A-Z][a-z]+)\b[^.;\n]{0,60}?\b(explains?|notes?|"
    r"states?|says|said|mentions?|reports?|writes?|wrote|indicates?|clarifies?|holds?|permits?|permitted|"
    r"forbids?|forbade|prohibits?|prohibited|made\s+(lawful|permissible|unlawful)|tells?|told|commands?|"
    r"commanded|enjoins?|prescribes?|prescribed|declares?|declared|describes?|teach(es)?|adds?)\b",
    re.IGNORECASE,
)
_AR_REPORT_FRAME = re.compile(
    r"(?<![ء-ي])[وف]?(بين|بيّن|يبين|يبيّن|ذكر|يذكر|قال|يقول|أوضح|يوضح|أفاد|يفيد|نقل|ينقل|فسر|يفسر|أخبر|يخبر|"
    r"شرح|يشرح|أشار|يشير|حكى|روى|أورد|يورد|نص|ينص)(?![ء-ي])"
    r"|(?<![ء-ي])[وف]?(أحل|احل|حرم|حرّم|فرض|أوجب|كتب|أمر|نهى|أباح)\s+(الله|تعالى|سبحانه)"
    r"|(?<![ء-ي])(عند|بحسب|حسب|وفق|كما\s+في)\s",
)


def _en_person(sentence: str) -> str:
    toks = set(_en_tokens(sentence))
    if toks & _EN_SECOND:
        return SECOND
    # The model speaking as itself ("I rule", "we hold"). Quoted verse text
    # is removed by the caller, so a first person here is the answer's own.
    if re.search(r"\b(i|we)\s+(rule|declare|hold|believe|think|consider|say|advise|would\s+say|recommend)\b"
                 r"|\bmy\s+(ruling|fatwa|opinion|view|advice)\b|\bin\s+my\s+(opinion|view)\b", sentence, re.I):
        return FIRST
    return GENERAL


def _ar_person(tokens: Sequence[str]) -> str:
    if _ar_second_person(tokens):
        return SECOND
    if any(segment(t) & _ar_set("افتي نفتي فتواي رايي اري نري اعتقد") for t in tokens):
        return FIRST
    return GENERAL


def ruling_claims(sentence: str) -> List[RulingClaim]:
    """Rulings a sentence of a generated answer states (quoted text removed by the caller)."""
    out: List[RulingClaim] = []
    s = sentence or ""
    if re.search(r"[ء-ي]", s):
        toks = ar_tokens(s)
        person = _ar_person(toks)
        reported_frame = bool(_AR_REPORT_FRAME.search(s))
        for clause in _CLAUSES.split(s):
            ctoks = ar_tokens(clause)
            for i, cls in _ar_deontic_hits(ctoks):
                t = ctoks[i]
                # "بالحلال", "الحرام", "المحرمات": a category named, not a
                # ruling predicated ("فالبيع حلال", "الميتة محرمة", "حرّم الله").
                if t.startswith(("ال", "لل", "بال", "وال", "فال", "كال")) and not (segment(t) & _AR_LEGISLATE) \
                        and not any(c.endswith(":reported") for c in cls):
                    continue
                near = ctoks[max(0, i - 2): i + 3]
                for c in cls:
                    base = c.split(":")[0]
                    # Validity words ("صحيح" = correct/authentic) are a ruling
                    # only about an act of worship/contract or the reader's own.
                    if base == VALIDITY and not (any(segment(t) & _AR_ACTS for t in near)
                                                 or _ar_second_person(near)):
                        continue
                    # Takfir needs a predicate about a person or category
                    # ("من ترك… كافر", "فهو كافر"), not the word in a story.
                    if base == STATUS and not (person == SECOND or any(
                            t in _AR_STATUS_SUBJECT for t in ctoks[max(0, i - 8): i])):
                        continue
                    out.append(RulingClaim(person, base, s, _subject_ar(ctoks, i), reported=c.endswith(":reported")
                                           or reported_frame))
        # Rulings addressed to the reader without a deontic word: "ما عليك
        # شيء لو…" (no obligation on you), "عليك أن تعيد…", "لازم تعيد…".
        if re.search(r"(?<![ء-ي])[وف]?(ما|لا|ليس|مو|مش)\s+(عليك|عليكي|عليكم)\s+(شي|شيء|شيئا|حرج|إثم|اثم|بأس|ذنب)", s):
            out.append(RulingClaim(SECOND, PERMIT, s, s))
        elif re.search(r"(?<![ء-ي])[وف]?(عليك|عليكي)\s+(أن|ان)\s+ت|(?<![ء-ي])[وف]?(لازم|لازمك|يلزمك|واجب\s+عليك)\s+ت", s):
            out.append(RulingClaim(SECOND, OBLIGE, s, s))
        if re.search(r"(?<![ء-ي])(ليس|ليست|لم\s+يعد|لم\s+تعد|غير)\s+(ب)?(مسلم|مسلما|مسلمة|مؤمن|مؤمنا|من\s+المسلمين)"
                     r"(?![ء-ي])|(خرج|يخرج|خارج|تخرج|خرجت)\s+(عن|من)\s+(الملة|ملة|الإسلام|الاسلام|الدين)", s):
            out.append(RulingClaim(GENERAL, STATUS, s, s))
    low = s
    seen_cls: Set[str] = set()
    for cls, pat in _EN_CLAIM_PATTERNS:
        if cls in seen_cls:
            continue
        for m in pat.finditer(low):
            # "what is forbidden", "that which is lawful": a relative clause
            # naming a category, not a ruling about a subject.
            before = re.findall(r"[a-z']+", low[:m.start()].lower())[-2:]
            if before and (before[-1] in ("what", "whatever", "which", "whichever") or before == ["that", "which"]):
                continue
            if cls == OBLIGE and m.group(0).lower() in ("need to", "needs to") and _en_person(s) != SECOND:
                continue
            if cls == OBLIGE and re.search(r"\b(we|i|he|she|they|it)\s+(\w+\s+)?$", low[:m.start()], re.I) \
                    and _EN_REPORT_FRAME.search(s) and _en_person(s) != SECOND:
                # "…asked whether our Lord is near so that we must call out":
                # a narrative's own words, reported.
                continue
            if cls == FORBID and m.group(0).lower() in ("cannot", "can't", "should not", "shouldn't") \
                    and _en_person(s) != SECOND:
                continue
            if cls == STATUS and re.match(r"(is|are|becomes?|became|has|have|will|would|remains?)\b", m.group(0), re.I):
                tail = m.group(0).lower()
                if not re.search(r"no\s+longer|not\s|kafir|kaafir|kuffar|apostate|murtad|infidel|non-?muslim", tail) \
                        and not re.search(r"disbeliever", tail):
                    continue
                # "they are disbelievers who were warned" — the verse's own
                # subjects described — is not takfir; a rule about anyone who
                # does something is.
                if not re.search(r"\b(anyone|anybody|whoever|whosoever|someone|somebody|a\s+person|any\s+person|"
                                 r"a\s+muslim|any\s+muslim|muslims\s+who|one\s+who|he\s+who|she\s+who|those\s+who|"
                                 r"people\s+who|everyone\s+who|you|he|she|they)\b", s, re.I) or \
                        re.search(r"\b(the\s+verse|this\s+verse|the\s+ayah|in\s+the\s+verse|mentioned|described|"
                                  r"addressed|referred)\b", s, re.I) and not re.search(r"no\s+longer|not\s+a\s+muslim", tail):
                    continue
            clause = _clause_at(s, m.start())
            if re.match(r"(is|are|was|were|be)\b", m.group(0), re.I) and m.start() > 0:
                # "Zakah is obligatory and …": the subject precedes the predicate.
                cut = s[:m.start()]
                start = max(cut.rfind(","), cut.rfind(";"), cut.rfind(":"))
                head = re.split(r"\b(?:while|whereas|but|although)\b", cut[start + 1:])[-1]
                clause = head if xling_tokens(head) else clause
            out.append(RulingClaim(_en_person(s), cls, s, _subject_en(clause),
                                   reported=bool(_EN_REPORT_FRAME.search(s))))
            seen_cls.add(cls)
            break
    return out


_EN_DEONTIC_NOISE = re.compile(
    r"\b(is|are|was|were|be|been|it|its|this|that|so|thus|therefore|then|also|now|not|no|nothing|"
    r"permissible|permitted|allowed|lawful|halal|acceptable|fine|ok|okay|alright|legitimate|haram|forbidden|"
    r"prohibited|unlawful|impermissible|sinful|makruh|disliked|sin|wrong|harm|blame|problem|issue|obligatory|"
    r"mandatory|compulsory|required|obliged|obligated|duty|obligation|must|may|can|cannot|should|have|has|"
    r"need|needs|ought|owe|owes|valid|invalid|void|count|counts|you|your|yours|believers?|muslims?|for|to|"
    r"in|with|if|of|the|a|an|and|or)\b",
    re.IGNORECASE,
)


def xling_tokens(text: str) -> List[str]:
    from app.safety.xling import claim_tokens
    return claim_tokens(_EN_DEONTIC_NOISE.sub(" ", re.sub(
        r"^.*?\b(explains?|notes?|states?|says|said|mentions?|reports?|writes?|indicates?|clarifies?|holds?|"
        r"adds?)\s+(that\s+)?", "", text, flags=re.I)))[1]


_CLAUSES = re.compile(r"\s*[,;:،؛]\s*(?:and\s+|but\s+|while\s+|so\s+)?")


def _clause_at(sentence: str, pos: int) -> str:
    """The comma/semicolon clause of ``sentence`` that contains ``pos``."""
    start = 0
    for m in _CLAUSES.finditer(sentence):
        if m.start() >= pos:
            return sentence[start:m.start()]
        start = m.end()
    return sentence[start:]


def _subject_en(sentence: str) -> str:
    s = re.sub(r"\[[^\]]*\]", " ", sentence)
    s = re.sub(r"^.*?\b(explains?|notes?|states?|says|said|mentions?|reports?|writes?|indicates?|clarifies?|"
               r"holds?|adds?)\s+(that\s+)?", "", s, flags=re.I)
    return _EN_DEONTIC_NOISE.sub(" ", s)


def _subject_ar(tokens: Sequence[str], i: int) -> str:
    keep = []
    for j, t in enumerate(tokens):
        if j == i or _ar_classes(t) or t in _AR_FIRST_WORDS or t in _AR_SECOND_WORDS:
            continue
        keep.append(t)
    return " ".join(keep)


# --------------------------------------------------------- evidence markers

_EV_EN = {
    PERMIT: re.compile(r"\b(permissible|permitted|permits?|lawful|allowed|allows?|halal|no\s+(blame|sin|harm)|"
                       r"made\s+lawful|made\s+permissible|is\s+not\s+forbidden)\b", re.I),
    FORBID: re.compile(r"\b(forbid\w*|prohibit\w*|unlawful|haram|avoid|abomination|do\s+not|don't|never|"
                       r"must\s+not|may\s+not|should\s+not|shall\s+not|cannot|not\s+(lawful|permissible|"
                       r"permitted|allowed)|sinful|great\s+sin|sin|immorality|evil)\b", re.I),
    OBLIGE: re.compile(r"\b(prescribed|decreed|ordained|obligat\w*|enjoined|command\w*|must|should|have\s+to|"
                       r"has\s+to|duty|required|(are|is)\s+to\s+be\s+made\s+up|made\s+up|"
                       r"upon\s+(you|those|them))\b", re.I),
    VALIDITY: re.compile(r"\b(valid|invalid|void|nullif\w*|binding|takes?\s+effect|counts?|sound|broken)\b", re.I),
}


def _ar_ev_class_positions(text: str) -> List[Tuple[int, Set[str]]]:
    toks = ar_tokens(text)
    out = []
    for i, cls in _ar_deontic_hits(toks):
        out.append((i, {c.split(":")[0] for c in cls}))
    # Imperatives/prohibitions in verse style: "فاجتنبوه", "لا تقربوا", "كتب عليكم"
    for i, t in enumerate(toks):
        cands = segment(t)
        if cands & _ar_set("اجتنبوه فاجتنبوه اجتنبوا رجس نهي ينهي"):
            out.append((i, {FORBID}))
        if cands & _ar_set("كتب فرض امر اوجب عليكم عليه"):
            out.append((i, {OBLIGE}))
        if cands & _ar_set("احل اباح رخص رخصه"):
            out.append((i, {PERMIT}))
    return out


def evidence_states_class(cls: str, texts: Iterable[str]) -> List[Tuple[str, List[int]]]:
    """For each evidence text, the token positions where a ruling of ``cls`` is stated."""
    out = []
    for t in texts:
        if not t:
            continue
        if re.search(r"[ء-ي]", t) and len(re.findall(r"[ء-ي]", t)) > len(re.findall(r"[a-zA-Z]", t)):
            pos = [i for i, c in _ar_ev_class_positions(t) if cls in c]
        else:
            pat = _EV_EN.get(cls)
            pos = []
            if pat:
                words = _en_tokens(t)
                joined = " ".join(words)
                for m in pat.finditer(joined):
                    pos.append(joined[: m.start()].count(" "))
        out.append((t, pos))
    return out
