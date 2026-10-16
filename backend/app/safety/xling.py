"""
Cross-lingual evidence view (English claims <-> Arabic evidence and back).

The production corpus is Arabic tafsir; answers are written in Arabic or
English. A claim can only be checked against evidence in a script it shares,
so this module gives every evidence text a view in the other language:

1. A bilingual lexicon learned deterministically from the canonical parallel
   corpus (each Qur'an verse paired with its stored English translations):
   log-likelihood (G²) co-occurrence between Arabic and English stems. It is
   data-derived, never hand-tuned to particular answers.
2. A transliteration skeleton for names and terms ("Ubayy ibn Ka'b" vs
   "أبي بن كعب", "rafath" vs "الرفث"): consonant classes only, compared on
   skeletons long enough not to collide with ordinary words.

``support()`` scores how much of a claim's content is carried by one place in
the evidence (local window), across scripts, and lists what is not carried.
Pure functions, no I/O: the pipeline builds the lexicon once per process from
the database (see ``Lexicon.build``); without it only same-script evidence
and transliteration count.
"""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Iterable, List, Optional, Sequence, Set, Tuple

from app.safety.grounding import normalize_arabic, _AR_STOP
from app.safety.stemming import arabic_stem as _stem_ar, porter

# ------------------------------------------------------------------ English

EN_STOP = frozenset((
    "a an the and or but if then than so as of to in on at by for with from into onto upon about over "
    "under after before during between through without within among against toward towards this that "
    "these those there here it its it's is are was were be been being am do does did done have has had "
    "having i me my mine we us our ours you your yours he him his she her hers they them their theirs "
    "who whom whose which what when where why how not no nor all any each every both either neither "
    "some such own same other another more most very can could will would shall should may might must "
    "also just only even still yet too again ever never once whether while until unless because since "
    "although though however therefore thus hence indeed namely e g i e etc s t one ones "
    "become becomes became get gets got come comes came go goes went make makes made let lets"
).split())

# Report verbs and discourse words: framing, not content.
EN_META = frozenset((
    "explain explains explained explaining note notes noted noting mention mentions mentioned state states "
    "stated stating write writes wrote written say says said tell tells told report reports reported "
    "describe describes described highlight highlights emphasize emphasizes emphasise emphasises point "
    "points pointed indicate indicates indicated clarify clarifies clarified add adds added comment "
    "comments commented observe observes observed interpret interprets interpreted interpretation mean "
    "means meant meaning meanings refer refers referring discuss discusses discussed according "
    "commentary commentator commentators exegete exegetes exegesis tafsir tafseer verse verses ayah ayat "
    "ayahs surah sura passage quran qur'an quranic text phrase word words statement context sense "
    "regarding concerning related relating summary summarize summarizes summarised summarized "
    "teach teaches taught show shows shown lesson lessons understood understand understanding "
    "imam shaykh sheikh scholar scholars author book work ibn bin abu al el thing things kind "
    "cite cites cited citing quote quotes quoted quoting hadith hadiths narration narrations narrated "
    "report reports reported tradition traditions also further adds added allah god"
).split())

_EN_WORD = re.compile(r"[a-z]+")
_IRREGULAR = {
    "wives": "wife", "women": "woman", "men": "man", "children": "child", "people": "person",
    "lives": "life", "feet": "foot", "teeth": "tooth", "mice": "mouse", "geese": "goose",
}


def en_fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    text = text.replace("’", "'").replace("‘", "'").replace("ʿ", "").replace("ʾ", "")
    text = re.sub(r"\bnon[-\s]+(?=[a-z])", "non", text)  # "non-Muslim" is not "Muslim"
    return re.sub(r"'s\b", "", text).replace("'", "")


def en_stem(word: str) -> str:
    """Porter stem (irregular plurals folded first, British "-our" read as "-or")."""
    w = _IRREGULAR.get(word, word)
    if len(w) > 5 and re.search(r"[^aeiou]our(s|ed|ing|able|ite)?$", w):
        w = re.sub(r"our(s|ed|ing|able|ite)?$", r"or\1", w)
    return porter(w)


def en_words(text: str) -> List[str]:
    return _EN_WORD.findall(en_fold(text))


def en_content(text: str, drop_meta: bool = True) -> List[str]:
    """Content stems of English text, in order."""
    out = []
    for w in en_words(text):
        if len(w) < 3 or w in EN_STOP or (drop_meta and w in EN_META):
            continue
        out.append(en_stem(w))
    return out


# ------------------------------------------------------------------- Arabic

# Report verbs and discourse words in Arabic (framing, not content).
AR_META = frozenset(normalize_arabic(w) for w in (
    "منهم منكم منهن لهم لكم لهن بهم بكم فيهم فيكم عنهم عنكم اليهم اليكم بينهم بينكم عليهم عليكم معهم "
    "يبين بين يوضح أوضح وضح نقل ينقل أورد يورد أفاد يفيد أشار يشير معناه ومعناه والمعنى المراد "
    "المقصود يقصد أي يعني تفسير التفسير تفسيره المفسر المفسرون قوله وقوله الآية الاية آية كما وكما "
    "يقرر ونقل وبين وأوضح ويبين ويوضح حديث الحديث رواية روايه روى وروى"
).split())

def ar_content(text: str) -> List[str]:
    """Content stems of Arabic text, in order (light stemming, stop words out)."""
    out = []
    for t in normalize_arabic(text).split():
        if len(t) <= 2 or t in _AR_STOP:
            continue
        st = _stem_ar(t)
        if st not in _AR_STOP:
            out.append(st)
    return out


def ar_words(text: str) -> List[str]:
    return [t for t in normalize_arabic(text).split() if t]


# ---------------------------------------------------------- transliteration

# Consonant classes shared by Arabic letters and their usual Latin spellings.
# Vowels, alef, waw/ya (long vowels or semivowels), hamza and ayn are dropped:
# they are the letters Latin spellings render least consistently.
_AR_CLASS = {
    "ب": "b", "ت": "t", "ث": "t", "ج": "j", "ح": "h", "خ": "h", "د": "d", "ذ": "d", "ر": "r", "ز": "z",
    "س": "s", "ش": "s", "ص": "s", "ض": "d", "ط": "t", "ظ": "z", "غ": "g", "ف": "f", "ق": "k", "ك": "k",
    "ل": "l", "م": "m", "ن": "n", "ه": "h", "ة": "",
}
_LATIN_DIGRAPHS = (("th", "t"), ("dh", "d"), ("sh", "s"), ("kh", "h"), ("gh", "g"), ("ch", "s"),
                   ("ph", "f"), ("q", "k"), ("c", "k"), ("x", "ks"), ("v", "f"), ("p", "b"))


def latin_skeleton(word: str) -> str:
    w = re.sub(r"[^a-z]", "", en_fold(word))
    if w.startswith(("al", "el")) and len(w) > 4:
        w = w[2:]
    for a, b in _LATIN_DIGRAPHS:
        w = w.replace(a, b)
    sk = re.sub(r"[aeiouwy]", "", w)
    return re.sub(r"(.)\1+", r"\1", sk)


def arabic_skeleton(word: str) -> str:
    w = normalize_arabic(word).replace(" ", "")
    if w.startswith("ال") and len(w) > 3:
        w = w[2:]
    sk = "".join(_AR_CLASS.get(ch, "") for ch in w)
    return re.sub(r"(.)\1+", r"\1", sk)


MIN_SKELETON = 3


# ------------------------------------------------------------------ lexicon

class Lexicon:
    """Arabic stem <-> English stem translation candidates (G²-ranked; used mutually)."""

    def __init__(self, ar2en: Optional[Dict[str, Tuple[str, ...]]] = None,
                 en2ar: Optional[Dict[str, Tuple[str, ...]]] = None,
                 vocab: Optional[FrozenSet[str]] = None, names: Optional[FrozenSet[str]] = None,
                 ar_freq: Optional[Dict[str, int]] = None):
        self.ar2en = ar2en or {}
        # Arabic stem -> number of parallel texts using it. A transliterated
        # name may only match a rare Arabic word ("البصرة"), never a common
        # one that shares its consonants ("بصر", sight).
        self.ar_freq = ar_freq or {}
        self.en2ar = en2ar or {}
        # Every stem the parallel corpus uses (both scripts).
        self.vocab = vocab or frozenset()
        # Words the translations capitalise mid-sentence: the Qur'an's own
        # proper names and divine names ("Pharaoh", "Ever-Living", "Kursi").
        self.names = names or frozenset()

    def __bool__(self) -> bool:
        return bool(self.ar2en)

    def __len__(self) -> int:
        return len(self.ar2en)

    def with_domain_words(self, words: Iterable[str]) -> "Lexicon":
        """Add words the English tafsir literature uses to the domain
        vocabulary (no translations: they only mark a term as in-domain)."""
        extra = {en_stem(w) for w in words if w and len(w) > 2}
        return Lexicon(self.ar2en, self.en2ar, self.vocab | frozenset(extra), self.names, self.ar_freq)

    @classmethod
    def build(cls, pairs: Iterable[Tuple[str, str]], top_k: int = 6, min_g2: float = 10.83,
              min_pair: int = 2) -> "Lexicon":
        """
        Learn the lexicon from (Arabic verse, English translation) pairs.

        Word pairs are ranked by Dunning's log-likelihood ratio (G²) of their
        co-occurrence, keeping positive associations significant at p < 0.001.
        Unlike Dice it does not let two rare words that happen to share one
        verse outrank a word and its usual translation.
        """
        ca: Counter = Counter()
        ce: Counter = Counter()
        cae: Counter = Counter()
        names: Set[str] = set()
        n_pairs = [0]
        for ar, en in pairs:
            for m in re.finditer(r"(?<=[a-z,;\]\)]\s)([A-Z][A-Za-z’'`ʿāīūĀĪŪâêîôû-]+)", en or ""):
                names.add(en_fold(m.group(1)).strip("-"))
            a_set = set(ar_content(ar))
            e_set = set(en_content(en, drop_meta=False))
            if not a_set or not e_set:
                continue
            n_pairs[0] += 1
            ca.update(a_set)
            ce.update(e_set)
            for a in a_set:
                for e in e_set:
                    cae[(a, e)] += 1
        total = max(n_pairs[0], 1)
        ar_best: Dict[str, List[Tuple[float, str]]] = defaultdict(list)
        en_best: Dict[str, List[Tuple[float, str]]] = defaultdict(list)
        for (a, e), n in cae.items():
            if n < min_pair:
                continue
            g2 = _g2(n, ca[a], ce[e], total)
            if g2 < min_g2:
                continue
            ar_best[a].append((g2, e))
            en_best[e].append((g2, a))
        # Candidates are kept in G² order (best first).
        ar2en = {a: tuple(e for _, e in sorted(v, reverse=True)[:top_k]) for a, v in ar_best.items()}
        en2ar = {e: tuple(a for _, a in sorted(v, reverse=True)[:top_k]) for e, v in en_best.items()}
        return cls(ar2en, en2ar, frozenset(ca) | frozenset(ce), frozenset(names), dict(ca))


def _xlogx(k: float, n: float) -> float:
    return k * math.log(k / n) if k > 0 else 0.0


def _g2(k11: int, ka: int, ke: int, n: int) -> float:
    """Dunning's G² for a positive association (0 when the pair is under-represented)."""
    k12, k21 = ka - k11, ke - k11
    k22 = n - k11 - k12 - k21
    if k22 < 0 or k11 * n <= ka * ke:
        return 0.0
    rows = (k11 + k12, k21 + k22)
    cols = (k11 + k21, k12 + k22)
    return 2.0 * (_xlogx(k11, rows[0] * cols[0] / n) + _xlogx(k12, rows[0] * cols[1] / n)
                  + _xlogx(k21, rows[1] * cols[0] / n) + _xlogx(k22, rows[1] * cols[1] / n))


_EMPTY = Lexicon()


# ---------------------------------------------------------- deontic tokens

# Rulings are expressed with different parts of speech in each language
# ("forbidden", "do not approach", "حرّم", "لا تقربوا"). Each deontic word
# is also emitted as a class token so the class itself can be matched across
# scripts.
_EN_DEONTIC = {
    "§forbid": ("forbid", "forbids", "forbidden", "forbade", "prohibit", "prohibits", "prohibited", "prohibition",
                "unlawful", "haram", "impermissible", "sin", "sins", "sinful", "abomination"),
    "§permit": ("permit", "permits", "permitted", "permissible", "permission", "lawful", "halal", "allow",
                "allowed", "allows"),
    "§oblige": ("obligatory", "obligation", "obligated", "mandatory", "compulsory", "prescribed", "decreed",
                "ordained", "enjoined", "duty", "required", "commanded", "command"),
}
_EN_DEONTIC_STEMS = {porter(w): cls for cls, ws in _EN_DEONTIC.items() for w in ws}
_AR_DEONTIC = {
    "§forbid": ("حرم", "محرم", "محرمة", "تحريم", "نهى", "ينهى", "نهي", "إثم", "رجس", "اجتنبوا", "فاجتنبوه",
                "منهي", "حرام"),
    "§permit": ("أحل", "يحل", "حلال", "مباح", "أباح", "يجوز", "جائز", "رخص", "رخصة"),
    "§oblige": ("فرض", "مفروض", "مفروضة", "فريضة", "واجب", "وجب", "أوجب", "كتب", "أمر", "ألزم", "يلزم"),
}
_AR_DEONTIC_STEMS = {_stem_ar(normalize_arabic(w)): cls for cls, ws in _AR_DEONTIC.items() for w in ws}


_FLIP = {"§permit": "§forbid", "§forbid": "§permit", "§oblige": "§permit"}
_EN_NEGATORS = frozenset("not no never nor isnt arent wasnt werent".split())
_AR_NEGATORS = frozenset(normalize_arabic(w) for w in "لا ولا فلا ليس ليست غير لم لن".split())


def _en_deontic(words: Sequence[str]) -> List[Tuple[int, str]]:
    out = []
    for i, w in enumerate(words):
        cls = _EN_DEONTIC_STEMS.get(en_stem(w)) or _EN_DEONTIC_STEMS.get(w)
        if cls:
            # "not lawful", "is not permitted" state the opposite ruling.
            if any(x in _EN_NEGATORS for x in words[max(0, i - 2):i]):
                cls = _FLIP[cls]
            out.append((i, cls))
        elif w in ("not", "never") and i and words[i - 1] in ("do", "does", "did", "must", "should", "may"):
            out.append((i, "§forbid"))
        elif w == "dont":
            out.append((i, "§forbid"))
    return out


def _ar_deontic(words: Sequence[str]) -> List[Tuple[int, str]]:
    out = []
    for i, w in enumerate(words):
        st = _stem_ar(w)
        cls = _AR_DEONTIC_STEMS.get(st) or _AR_DEONTIC_STEMS.get(w)
        if cls:
            # "لا يحل", "ليس بحرام", "غير محرم" state the opposite ruling.
            if i and words[i - 1] in _AR_NEGATORS:
                cls = _FLIP[cls]
            out.append((i, cls))
        elif w in ("لا", "ولا", "فلا") and i + 1 < len(words) and words[i + 1][:1] == "ت" and words[i + 1].endswith(("وا", "وه")):
            out.append((i, "§forbid"))  # "لا تقربوا", "لا تأكلوا"
        else:
            # Second-person plural imperative ("فأصلحوا", "أقيموا"): a command.
            bare = w[1:] if w[:1] in "وف" and len(w) > 5 else w
            if bare[:1] == "ا" and bare.endswith("وا") and len(bare) >= 5 and not (i and words[i - 1] in _AR_NEGATORS):
                out.append((i, "§oblige"))
    return out


# ------------------------------------------------------------ evidence view

@dataclass
class _Text:
    script: str                          # "en" | "ar"
    tokens: List[str]                    # content stems in order (with deontic class tokens)
    skeletons: List[str] = field(default_factory=list)  # aligned with tokens ("" for class tokens)
    groups: List[int] = field(default_factory=list)     # conjunct index of each token ("X و Y", "X and Y")


def _analyse(text: str, script: Optional[str] = None, deontic_content: bool = False) -> _Text:
    """Content stems of ``text`` with aligned transliteration skeletons.

    Deontic words become class tokens; with ``deontic_content`` (evidence
    side) their stem is kept as content too ("فأصلحوا" is a command and also
    says what is commanded)."""
    ar_n = len(re.findall(r"[ء-ي]", text or ""))
    en_n = len(re.findall(r"[A-Za-z]", text or ""))
    script = script or ("ar" if ar_n > en_n else "en")
    toks: List[str] = []
    sks: List[str] = []
    grp: List[int] = []
    g = 0
    if script == "ar":
        words = ar_words(text)
        deon = dict(_ar_deontic(words))
        for i, w in enumerate(words):
            if i and w[:1] in "وف" and len(w) > 3:
                g += 1
            if i in deon:
                toks.append(deon[i])
                sks.append("")
                grp.append(g)
                if not deontic_content:
                    continue
            if len(w) <= 2 or w in _AR_STOP or w in AR_META:
                continue
            st = _stem_ar(w)
            if st in _AR_STOP or st in AR_META:
                continue
            toks.append(st)
            sks.append(arabic_skeleton(w))
            grp.append(g)
    else:
        words = en_words(text)
        deon = dict(_en_deontic(words))
        for i, w in enumerate(words):
            if w in ("and", "but", "while", "whereas"):
                g += 1
            if i in deon:
                toks.append(deon[i])
                sks.append("")
                grp.append(g)
                if not deontic_content:
                    continue
            if len(w) < 3 or w in EN_STOP or w in EN_META:
                continue
            toks.append(en_stem(w))
            sks.append(latin_skeleton(w))
            grp.append(g)
    return _Text(script, toks, sks, grp)


@dataclass
class EvidenceView:
    texts: List[_Text] = field(default_factory=list)
    lexicon: Lexicon = field(default_factory=lambda: _EMPTY)

    @classmethod
    def of(cls, texts: Iterable[str], lexicon: Optional[Lexicon] = None) -> "EvidenceView":
        view = cls(lexicon=lexicon or _EMPTY)
        for t in texts:
            if t:
                a = _analyse(t, deontic_content=True)
                if a.tokens:
                    view.texts.append(a)
        return view

    def __bool__(self) -> bool:
        return bool(self.texts)


@dataclass
class Support:
    tokens: int = 0
    found: int = 0
    local: int = 0
    unsupported: List[str] = field(default_factory=list)
    comparable: bool = False

    @property
    def coverage(self) -> float:
        return self.found / self.tokens if self.tokens else 1.0

    @property
    def local_coverage(self) -> float:
        return self.local / self.tokens if self.tokens else 1.0


def claim_tokens(claim: str) -> Tuple[str, List[str], List[str]]:
    """(script, distinct content stems, aligned skeletons) of a claim (class tokens excluded)."""
    a = _analyse(claim)
    toks, sks = [], []
    for t, k in zip(a.tokens, a.skeletons):
        # Deontic class tokens mark rulings in evidence; as claim content they
        # would let any sentence with "must"/"sin" match any command.
        if t in toks or t.startswith("§"):
            continue
        toks.append(t)
        sks.append(k)
    return a.script, toks, sks


def deontic_classes(text: str) -> List[str]:
    """Deontic class tokens ("§forbid", "§permit", "§oblige") a text expresses."""
    return list(dict.fromkeys(t for t in _analyse(text).tokens if t.startswith("§")))


# Best-ranked candidates used across scripts: 3 for reading tafsir prose,
# 2 (strict) where one verse must carry a claim on its own.
RARE_WORD = 40             # parallel texts: above this an Arabic word is common vocabulary
TRANSLATIONS_PER_WORD = 3
STRICT_TRANSLATIONS_PER_WORD = 2
SHORT_TEXT = 150   # tokens: verse translations and short tafsir are read whole


def _positions(script: str, need: Sequence[str], skel: Dict[str, str], text: _Text,
               lex: Lexicon, per_word: int = TRANSLATIONS_PER_WORD) -> Dict[str, List[int]]:
    """Token positions in ``text`` that carry each claim token."""
    where: Dict[str, List[int]] = defaultdict(list)
    if text.script == script:
        # Same script: identical stem, or a synonym through the other language
        # ("path" ~ "way" through سبيل; "تسكن" ~ "تطمئن" through "rest").
        fwd, back = (lex.en2ar, lex.ar2en) if script == "en" else (lex.ar2en, lex.en2ar)
        match: Dict[str, List[str]] = defaultdict(list)
        for t in need:
            match[t].append(t)
            # Strict reading (one verse carrying a claim): exact stems only.
            if not t.startswith("§") and per_word >= TRANSLATIONS_PER_WORD:
                # Mutual best alignments only: t's top translations whose
                # own top translations include t, and their top renderings.
                for pivot in fwd.get(t, ())[:1]:
                    back_list = back.get(pivot, ())[:3]
                    if t not in back_list:
                        continue
                    for syn in back_list:
                        if syn != t:
                            match[syn].append(t)
        weak = {}
        if script == "ar":
            for t in need:
                k = _consonants(t)
                if len(k) >= 3:
                    weak.setdefault(k, []).append(t)
        for i, tok in enumerate(text.tokens):
            for ct in match.get(tok, ()):
                where[ct].append(i)
            if weak and not tok.startswith("§"):
                for ct in weak.get(_consonants(tok), ()):
                    if ct != tok:
                        where[ct].append(i)
        return where
    trans = lex.en2ar if script == "en" else lex.ar2en
    inv: Dict[str, List[str]] = defaultdict(list)
    for t in need:
        if t.startswith("§"):
            inv[t].append(t)
            continue
        back = lex.ar2en if script == "en" else lex.en2ar
        for rank, c in enumerate(trans.get(t, ())[:per_word]):
            # Mutual alignment only (each among the other's best renderings):
            # "consume" is not a translation of "ربا" just because the two
            # co-occur in "those who consume riba". A word's single best
            # rendering counts when the word is among that rendering's kept
            # candidates at all ("riba" -> "ربا", whose own list is led by
            # "usury" and "interest").
            if t in back.get(c, ())[:per_word] or (rank == 0 and t in back.get(c, ())):
                inv[c].append(t)
    # Arabic renderings are also matched on their consonants, so a light
    # stem's morphological variants carry the same translation ("استماع" /
    # "استمع", "الحضور" / "حضر").
    inv_cons: Dict[str, List[str]] = defaultdict(list)
    if script == "en" and text.script == "ar":
        for c, cts in list(inv.items()):
            k = _consonants(c)
            if len(k) >= 3:
                inv_cons[k].extend(cts)
    sk_inv: Dict[str, List[str]] = defaultdict(list)
    short_sk: Dict[str, List[str]] = defaultdict(list)
    for t in need:
        k = skel.get(t, "")
        if len(k) >= MIN_SKELETON:
            sk_inv[k].append(t)
        elif len(k) == 2 and script == "en" and lex.vocab and t not in lex.vocab:
            # A transliterated Arabic term the English corpus never uses
            # ("zina", "riba"): its short skeleton may match a short word.
            short_sk[k].append(t)
    for i, (tok, k) in enumerate(zip(text.tokens, text.skeletons)):
        for ct in inv.get(tok, ()):
            where[ct].append(i)
        if inv_cons and tok not in inv and not tok.startswith("§"):
            for ct in inv_cons.get(_consonants(tok), ()):
                where[ct].append(i)
        if k and len(k) >= MIN_SKELETON and (text.script != "ar" or lex.ar_freq.get(tok, 0) <= RARE_WORD):
            for ct in sk_inv.get(k, ()):
                where[ct].append(i)
        elif k and short_sk.get(k) and len(tok) <= 4:
            for ct in short_sk[k]:
                where[ct].append(i)
    return where


def nearest_class(claim: str, text: str, lexicon: Optional[Lexicon] = None) -> Dict[str, int]:
    """
    For each deontic class stated in ``text``, how many of the claim's
    content words found in ``text`` sit nearest to that class's marker
    ("Allah has permitted trade and forbidden interest": "trade" is nearest
    the permission, "interest" the prohibition).
    """
    lex = lexicon or _EMPTY
    script, need, sks = claim_tokens(claim)
    t = _analyse(text)
    marks = [(i, tok) for i, tok in enumerate(t.tokens) if tok.startswith("§")]
    votes: Dict[str, int] = defaultdict(int)
    if not marks or not need:
        return votes
    where = _positions(script, need, dict(zip(need, sks)), t, lex)
    for tok, ps in where.items():
        if tok.startswith("§") or not ps:
            continue
        # Nearest marker, preferring one in the same conjunct ("أحل البيع
        # وحرم الربا": البيع goes with أحل, not with the equally near حرم).
        gr = t.groups
        best = min(((abs(p - i) + (0 if (p < len(gr) and i < len(gr) and gr[p] == gr[i]) else 0.5), cls)
                    for p in ps for i, cls in marks), default=None)
        if best:
            votes[best[1]] += 1
    return votes


def _consonants(stem: str) -> str:
    """An Arabic stem without its long vowels/weak letters (ا و ي ى ء)."""
    return re.sub(r"[اويىءئؤ]", "", stem)


def _best_window(where: Dict[str, List[int]], window: int) -> Set[str]:
    hits = sorted((p, t) for t, ps in where.items() for p in ps)
    best: Set[str] = set()
    counts: Dict[str, int] = {}
    j = 0
    for pos, tok in hits:
        counts[tok] = counts.get(tok, 0) + 1
        while hits[j][0] < pos - window:
            old = hits[j][1]
            counts[old] -= 1
            if not counts[old]:
                del counts[old]
            j += 1
        if len(counts) > len(best):
            best = set(counts)
    return best


def support(claim: str, view: EvidenceView, window: int = 60, per_word: int = TRANSLATIONS_PER_WORD) -> Support:
    """
    How much of ``claim`` the evidence carries, across scripts. A claim
    token is carried by an evidence token when they are the same stem, a
    synonym through the other language, lexicon translations of each other,
    or share a transliteration skeleton of 3+ consonants.

    Short texts (verse translations, short tafsir) are read whole and pooled;
    a long text counts only inside one window, so a long chunk that contains
    every common word somewhere does not carry an invented claim.
    """
    script, need, sks = claim_tokens(claim)
    best = Support(tokens=len(need), unsupported=list(need))
    if not need or not view:
        return best
    lex = view.lexicon
    skel = dict(zip(need, sks))
    short_found: Set[str] = set()
    longs: List[Set[str]] = []
    comparable = False
    for text in view.texts:
        # Another script is comparable only through the lexicon
        # (transliteration alone matches names, not statements).
        if text.script != script and not lex:
            continue
        comparable = True
        where = _positions(script, need, skel, text, lex, per_word)
        if len(text.tokens) <= SHORT_TEXT:
            short_found |= {t for t, ps in where.items() if ps}
        else:
            longs.append(_best_window(where, window))
    if not comparable:
        return best
    candidates = [short_found | w for w in longs] or [short_found]
    found = max(candidates, key=len)
    any_found = short_found.union(*longs) if longs else short_found
    return Support(tokens=len(need), found=len(any_found), local=len(found),
                   unsupported=[t for t in need if t not in found], comparable=True)


# ------------------------------------------------------- polarity and scope
#
# Lexical coverage cannot tell "Allah forgives whoever repents" from "Allah
# forgives even without repentance": both share every content word. Two
# checks read what coverage ignores:
#
# * polarity: a content word the claim negates or cancels as a condition
#   ("without repentance", "no need to repent", "regardless of whether they
#   turn back", "not prohibited") that the evidence only ever states
#   affirmatively, or the reverse;
# * absolute scope: "guaranteed", "permanently", "never again",
#   "automatically", "unconditionally", "أبدا", "حتما", "مضمون". The claim
#   asserts a scope the evidence must state too (same class of marker).

_EN_NEG_SPLIT = re.compile(
    r"(\b(?:not|no|never|nor|neither|without|cannot|cant|dont|doesnt|didnt|isnt|arent|wasnt|werent|wont|"
    r"regardless\s+of(?:\s+whether)?|irrespective\s+of|no\s+matter(?:\s+whether|\s+if)?|need\s+not|neednt|"
    r"no\s+need\s+(?:to|for)|instead\s+of|rather\s+than|free\s+from|free\s+of|exempt\s+from)\b|[,;:.!?])"
)
_EN_SCOPE_RESET = frozenset("but except only unless while whereas until till so".split())
# On the claim side only cancelled conditions count ("without repentance",
# "no need to repent"): a plain "not" is too often a prohibition paraphrased
# ("do not approach" = "forbids approaching").
_EN_CANCEL = re.compile(
    r"(\b(?:without|regardless\s+of(?:\s+whether)?|irrespective\s+of|no\s+matter(?:\s+whether|\s+if)?|need\s+not|"
    r"neednt|no\s+need\s+(?:to|for)|not\s+need(?:ed)?\s+to|dont\s+need\s+to|doesnt\s+need\s+to|"
    r"not\s+(?:required|necessary)\s+to|instead\s+of|free\s+from|free\s+of|exempt\s+from|beyond|exceeding|in\s+excess\s+of)\b|[,;:.!?])"
)
_AR_CANCEL = frozenset(normalize_arabic(w) for w in "بلا دون بدون بغير".split())
_AR_CANCEL_PHRASE = re.compile(r"(?<![ء-ي])(?:من\s+غير|بغض\s+النظر\s+عن|لا\s+حاجة\s+(?:إلى|الى|ل)|"
                               r"لا\s+يشترط|لا\s+يلزم|ليس\s+بحاجة\s+(?:إلى|الى))(?![ء-ي])")
_AR_NEG_WORDS = frozenset(normalize_arabic(w) for w in
                          "لا ولا فلا ليس ليست غير بغير لم ولم فلم لن ولن بلا دون بدون عدم".split())
_AR_SCOPE_RESET = frozenset(normalize_arabic(w) for w in "إلا الا لكن ولكن بل حتى".split())
NEG_SCOPE_EN = 3
NEG_SCOPE_AR = 2

ABSOLUTE_CLASSES = {
    # (claim marker, evidence marker)
    "temporal": (
        re.compile(r"\b(?:forever|permanent(?:ly)?|for\s+life|for\s+ever|(?:never|not)\s+(?:\w+\s+){0,4}?again|"
                   r"ever\s+again|eternal(?:ly)?|perpetual(?:ly)?|always|at\s+all\s+times)\b"
                   r"|(?<![ء-ي])[وف]?(?:أبدا|ابدا|دائما|للأبد|للابد|مدى\s+الحياة|بعد\s+اليوم)(?![ء-ي])", re.I),
        re.compile(r"\b(?:forever|for\s+ever|eternal\w*|perpetual\w*|always|everlasting|abid\w+)\b"
                   r"|(?<![ء-ي])[وف]?(?:أبدا|ابدا|أبد|ابد|دائما|دائم|خالد|خالدا|خالدين|خالدون|الخلود|مؤبد|"
                   r"لا\s+يزال|كل\s+حين|كل\s+وقت)(?![ء-ي])", re.I),
    ),
    "guarantee": (
        re.compile(r"\b(?:guarante\w+|assured(?:ly)?|automatic(?:ally)?|certain\s+to|sure\s+to|bound\s+to|"
                   r"inevitabl[ey]|definitely|without\s+fail|instant(?:ly)?|immediate(?:ly)?)\b"
                   r"|(?<![ء-ي])[وفب]?(?:مضمون|مضمونة|يضمن|تضمن|ضمان|حتما|لا\s+محالة|قطعا|تلقائيا|فورا|"
                   r"على\s+الفور)(?![ء-ي])", re.I),
        re.compile(r"\b(?:guarante\w+|assur\w+|certain\w*|surely|inevitabl\w+|undoubted\w*|"
                   r"immediate\w*|instant\w*)\b"
                   r"|(?<![ء-ي])[وفب]?(?:ضمن|يضمن|مضمون|ضمان|حتما|لا\s+محالة|قطعا|عاجل|عاجلا|فورا)(?![ء-ي])", re.I),
    ),
    "unconditional": (
        re.compile(r"\b(?:regardless|irrespective|no\s+matter|unconditional(?:ly)?|without\s+(?:any\s+)?"
                   r"(?:condition|conditions|exception|need)|even\s+without|whatever\s+(?:he|she|they|one|you)\s+"
                   r"(?:does|do|did))\b"
                   r"|(?<![ء-ي])(?:بغض\s+النظر|بلا\s+شرط|دون\s+شرط|بدون\s+شرط|من\s+غير\s+شرط|دون\s+حاجة|بلا\s+حاجة|"
                   r"مهما\s+(?:فعل|عمل|فعلوا|عملوا))(?![ء-ي])", re.I),
        re.compile(r"\b(?:regardless|irrespective|unconditional\w*|without\s+exception)\b"
                   r"|(?<![ء-ي])(?:بغض\s+النظر|بلا\s+شرط|دون\s+شرط|على\s+كل\s+حال|في\s+كل\s+حال)", re.I),
    ),
}


def absolute_scope(claim: str) -> List[str]:
    """Classes of absolute scope the claim asserts."""
    return [k for k, (pat, _) in ABSOLUTE_CLASSES.items() if pat.search(claim or "")]


def scope_supported(cls: str, texts: Iterable[str]) -> bool:
    pat = ABSOLUTE_CLASSES[cls][1]
    return any(pat.search(t or "") for t in texts)


def _polar_tokens(text: str, claim: bool = False) -> Tuple[_Text, List[bool]]:
    """Content tokens of ``text`` (as the evidence view reads them) and, for
    each, whether it sits in the scope of a negation (evidence) or of a
    cancelled condition (``claim``)."""
    if claim and re.search(r"[ء-ي]", text or ""):
        text = _AR_CANCEL_PHRASE.sub(" بدون ", text)
    ar_n = len(re.findall(r"[ء-ي]", text or ""))
    en_n = len(re.findall(r"[A-Za-z]", text or ""))
    toks: List[str] = []
    sks: List[str] = []
    negs: List[bool] = []
    if ar_n > en_n:
        scope = 0
        for r in re.findall(r"[ء-يً-ْ]+|[,;:،؛.!?؟]", text or ""):
            if re.fullmatch(r"[,;:،؛.!?؟]", r):
                scope = 0
                continue
            w = normalize_arabic(r)
            if not w:
                continue
            if w in _AR_SCOPE_RESET:
                scope = 0
                continue
            if w in (_AR_CANCEL if claim else _AR_NEG_WORDS):
                scope = NEG_SCOPE_AR
                continue
            negated = scope > 0
            scope = max(0, scope - 1)
            if len(w) <= 2 or w in _AR_STOP or w in AR_META:
                continue
            st = _stem_ar(w)
            if st in _AR_STOP or st in AR_META:
                continue
            toks.append(st)
            sks.append(arabic_skeleton(w))
            negs.append(negated)
        return _Text("ar", toks, sks), negs
    scope = 0
    split = _EN_CANCEL if claim else _EN_NEG_SPLIT
    for p in split.split(en_fold(text)):
        if not p:
            continue
        if re.fullmatch(r"[,;:.!?]", p):
            scope = 0
            continue
        if split.fullmatch(p):
            scope = 2 if claim else NEG_SCOPE_EN
            continue
        for w in _EN_WORD.findall(p):
            if w in _EN_SCOPE_RESET:
                scope = 0
                continue
            if len(w) < 3 or w in EN_STOP or w in EN_META:
                continue
            toks.append(en_stem(w))
            sks.append(latin_skeleton(w))
            negs.append(scope > 0)
            scope = max(0, scope - 1)
    return _Text("en", toks, sks), negs


def polarity_conflicts(claim: str, texts: Sequence[str], lexicon: Optional[Lexicon] = None) -> List[str]:
    """
    Content words of ``claim`` whose polarity no evidence occurrence shares:
    negated / cancelled in the claim but stated only affirmatively in the
    evidence, or the reverse. Words the evidence does not carry at all are
    not polarity conflicts (coverage judges those).
    """
    lex = lexicon or _EMPTY
    c_text, c_negs = _polar_tokens(claim, claim=True)
    if not c_text.tokens:
        return []
    want: Dict[str, Set[bool]] = defaultdict(set)
    for tok, neg in zip(c_text.tokens, c_negs):
        want[tok].add(neg)
    need = list(want)
    skel = dict(zip(c_text.tokens, c_text.skeletons))
    seen: Dict[str, Set[bool]] = defaultdict(set)
    for t in texts:
        if not t:
            continue
        e_text, e_negs = _polar_tokens(t)
        if e_text.script != c_text.script and not lex:
            continue
        where = _positions(c_text.script, need, skel, e_text, lex)
        for tok, ps in where.items():
            for p in ps:
                if p < len(e_negs):
                    seen[tok].add(e_negs[p])
    # A condition the claim cancels that the evidence states; or what the
    # evidence only ever denies, asserted by a claim that is not itself a
    # prohibition ("forbids approaching" restates "do not approach").
    out = [tok for tok, pol in want.items() if pol == {True} and tok in seen and seen[tok] == {False}]
    if not _FORBID_PARAPHRASE.search(claim or ""):
        c_plain, _ = _polar_tokens(claim)
        out += [tok for tok, pol in want.items() if pol == {False} and seen.get(tok) == {True}
                and tok not in out and not _negated_in(tok, claim)]
    return out


_FORBID_PARAPHRASE = re.compile(
    r"\b(?:forbid\w*|forbade|prohibit\w*|avoid\w*|refrain\w*|abstain\w*|warn\w*|shun\w*|stay\s+away|keep\s+away|"
    r"bann?\w*|not\s+allowed|unlawful|haram|never|not|no|nor|neither|cannot|only|except)\b"
    r"|(?<![ء-ي])[وف]?(?:ينهى|نهى|ينهي|نهي|النهي|حرم|يحرم|تحريم|محرم|اجتناب|يجتنب|اجتنبوا|تجنب|يحذر|حذر|لا|ليس|لم|لن|"
    r"غير|إلا|الا|إنما|انما|عدم|دون)(?![ء-ي])", re.IGNORECASE)


def _negated_in(tok: str, claim: str) -> bool:
    text, negs = _polar_tokens(claim)
    return any(t == tok and n for t, n in zip(text.tokens, negs))
