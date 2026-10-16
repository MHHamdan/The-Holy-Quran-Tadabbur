"""
Cross-lingual evidence view (English claims <-> Arabic evidence and back).

The production corpus is Arabic tafsir; answers are written in Arabic or
English. A claim can only be checked against evidence in a script it shares,
so this module gives every evidence text a view in the other language:

1. A bilingual lexicon learned deterministically from the canonical parallel
   corpus (each Qur'an verse paired with its stored English translations):
   Dice co-occurrence between Arabic light stems and English stems. It is
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
    "although though however therefore thus hence indeed namely e g i e etc s t one ones"
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
    return re.sub(r"'s\b", "", text).replace("'", "")


def en_stem(word: str) -> str:
    """Porter stem (irregular plurals folded first)."""
    return porter(_IRREGULAR.get(word, word))


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
    "يبين بين يوضح أوضح وضح يذكر ذكر نقل ينقل أورد يورد أفاد يفيد أشار يشير معناه ومعناه والمعنى المراد "
    "المقصود يقصد أي يعني تفسير التفسير تفسيره المفسر المفسرون قوله وقوله الآية الاية آية كما وكما "
    "يقرر ذكره ونقل وذكر وبين وأوضح ويذكر ويبين ويوضح حديث الحديث رواية روايه روى وروى"
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
    """Arabic stem <-> English stem translation candidates (Dice-ranked)."""

    def __init__(self, ar2en: Optional[Dict[str, Tuple[str, ...]]] = None,
                 en2ar: Optional[Dict[str, Tuple[str, ...]]] = None,
                 vocab: Optional[FrozenSet[str]] = None, names: Optional[FrozenSet[str]] = None):
        self.ar2en = ar2en or {}
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

    @classmethod
    def build(cls, pairs: Iterable[Tuple[str, str]], top_k: int = 6, min_dice: float = 0.08,
              min_pair: int = 2) -> "Lexicon":
        """Learn the lexicon from (Arabic verse, English translation) pairs."""
        ca: Counter = Counter()
        ce: Counter = Counter()
        cae: Counter = Counter()
        names: Set[str] = set()
        for ar, en in pairs:
            for m in re.finditer(r"(?<=[a-z,;\]\)]\s)([A-Z][A-Za-z’'`ʿāīūĀĪŪâêîôû-]+)", en or ""):
                names.add(en_fold(m.group(1)).strip("-"))
            a_set = set(ar_content(ar))
            e_set = set(en_content(en, drop_meta=False))
            if not a_set or not e_set:
                continue
            ca.update(a_set)
            ce.update(e_set)
            for a in a_set:
                for e in e_set:
                    cae[(a, e)] += 1
        ar_best: Dict[str, List[Tuple[float, str]]] = defaultdict(list)
        en_best: Dict[str, List[Tuple[float, str]]] = defaultdict(list)
        for (a, e), n in cae.items():
            if n < min_pair:
                continue
            dice = 2.0 * n / (ca[a] + ce[e])
            if dice < min_dice:
                continue
            ar_best[a].append((dice, e))
            en_best[e].append((dice, a))
        # Candidates are kept in Dice order (best first).
        ar2en = {a: tuple(e for _, e in sorted(v, reverse=True)[:top_k]) for a, v in ar_best.items()}
        en2ar = {e: tuple(a for _, a in sorted(v, reverse=True)[:top_k]) for e, v in en_best.items()}
        return cls(ar2en, en2ar, frozenset(ca) | frozenset(ce), frozenset(names))


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
        elif w == "لا" and i + 1 < len(words) and words[i + 1][:1] == "ت" and words[i + 1].endswith(("وا", "وه")):
            out.append((i, "§forbid"))  # "لا تقربوا", "لا تأكلوا"
    return out


# ------------------------------------------------------------ evidence view

@dataclass
class _Text:
    script: str                          # "en" | "ar"
    tokens: List[str]                    # content stems in order (with deontic class tokens)
    skeletons: List[str] = field(default_factory=list)  # aligned with tokens ("" for class tokens)


def _analyse(text: str, script: Optional[str] = None) -> _Text:
    """Content stems of ``text`` with aligned transliteration skeletons."""
    ar_n = len(re.findall(r"[ء-ي]", text or ""))
    en_n = len(re.findall(r"[A-Za-z]", text or ""))
    script = script or ("ar" if ar_n > en_n else "en")
    toks: List[str] = []
    sks: List[str] = []
    if script == "ar":
        words = ar_words(text)
        deon = dict(_ar_deontic(words))
        for i, w in enumerate(words):
            if i in deon:
                toks.append(deon[i])
                sks.append("")
                continue
            if len(w) <= 2 or w in _AR_STOP or w in AR_META:
                continue
            st = _stem_ar(w)
            if st in _AR_STOP or st in AR_META:
                continue
            toks.append(st)
            sks.append(arabic_skeleton(w))
    else:
        words = en_words(text)
        deon = dict(_en_deontic(words))
        for i, w in enumerate(words):
            if i in deon:
                toks.append(deon[i])
                sks.append("")
                continue
            if len(w) < 3 or w in EN_STOP or w in EN_META:
                continue
            toks.append(en_stem(w))
            sks.append(latin_skeleton(w))
    return _Text(script, toks, sks)


@dataclass
class EvidenceView:
    texts: List[_Text] = field(default_factory=list)
    lexicon: Lexicon = field(default_factory=lambda: _EMPTY)

    @classmethod
    def of(cls, texts: Iterable[str], lexicon: Optional[Lexicon] = None) -> "EvidenceView":
        view = cls(lexicon=lexicon or _EMPTY)
        for t in texts:
            if t:
                a = _analyse(t)
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


# Best Dice candidates used across scripts: 3 for reading tafsir prose,
# 2 (strict) where one verse must carry a claim on its own.
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
            if not t.startswith("§"):
                # Mutual best alignments only: t's top translations whose
                # own top translations include t, and their top renderings.
                for pivot in fwd.get(t, ())[:2]:
                    back_list = back.get(pivot, ())[:3]
                    if t not in back_list:
                        continue
                    for syn in back_list:
                        if syn != t:
                            match[syn].append(t)
        for i, tok in enumerate(text.tokens):
            for ct in match.get(tok, ()):
                where[ct].append(i)
        return where
    trans = lex.en2ar if script == "en" else lex.ar2en
    inv: Dict[str, List[str]] = defaultdict(list)
    for t in need:
        if t.startswith("§"):
            inv[t].append(t)
            continue
        back = lex.ar2en if script == "en" else lex.en2ar
        for c in trans.get(t, ())[:per_word]:
            # Mutual alignment only (each among the other's best renderings):
            # "consume" is not a translation of "ربا" just because the two
            # co-occur in "those who consume riba".
            if t in back.get(c, ())[:per_word]:
                inv[c].append(t)
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
        if k and len(k) >= MIN_SKELETON:
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
        best = min(((abs(p - i), cls) for p in ps for i, cls in marks), default=None)
        if best:
            votes[best[1]] += 1
    return votes


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
