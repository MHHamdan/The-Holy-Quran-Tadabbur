"""
Attribution claims: who an answer says said something.

An attribution is grounded only when the named person or work is present in
the retrieved evidence: the author/work of a cited chunk (source metadata),
or a name the cited text itself mentions. Names are compared through

* a bilingual registry derived from the tafsir source catalogue (work names,
  author names, their Ibn-/Abu-/nisba short forms, Arabic and Latin), and
* a transliteration skeleton for any other name, so "Ubayy ibn Ka'b",
  "Sa'id ibn Jubayr" or "al-Bukhari" in an English answer match
  "أبي بن كعب", "سعيد بن جبير", "البخاري" in Arabic evidence.

Name detection is generic, not a list of known names: honorifics and titles
(Shaykh, Imam, Dr., al-Hafiz, الشيخ, الإمام, الحافظ, شيخ الإسلام…),
kunya/nasab forms (Abu X, Ibn X, أبو/أبي/ابن…), "al-X" nisbas, and any name in
an attribution frame ("according to X", "in X's view", "X held/wrote/argued",
"عند X", "يرى X", "قال X", "ذهب X إلى"). Collective attributions ("all the
scholars agree", "no commentator disputes", "the majority hold",
"أجمع العلماء", "لم يختلف أحد") need the evidence to state that agreement
or disagreement.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from app.safety.grounding import normalize_arabic
from app.safety.xling import arabic_skeleton, latin_skeleton, en_fold, MIN_SKELETON

# --------------------------------------------------------------- registry

@dataclass
class RegistryEntry:
    key: str                         # source base id
    forms: Set[str] = field(default_factory=set)   # normalised name forms (both scripts)


def _norm_latin(name: str) -> str:
    s = en_fold(name)
    s = re.sub(r"[^a-z\s-]", " ", s).replace("-", " ")
    toks = [t for t in s.split() if t not in ("the", "of", "and")]
    return " ".join(toks)


def _norm_ar(name: str) -> str:
    return normalize_arabic(name)


def _short_forms(name: str) -> Set[str]:
    """'Muhammad ibn Jarir al-Tabari' -> {'tabari', 'ibn jarir', ...}; Arabic likewise."""
    out: Set[str] = set()
    if re.search(r"[ء-ي]", name):
        n = _norm_ar(name)
        if not n:
            return out
        out.add(n)
        toks = n.split()
        for i, t in enumerate(toks):
            if t in ("ابن", "بن", "ابو", "ابي", "ام") and i + 1 < len(toks):
                out.add(("ابن" if t in ("ابن", "بن") else t) + " " + toks[i + 1])
            if t.startswith("ال") and len(t) > 4:
                out.add(t)
        if toks:
            out.add(toks[-1])
    else:
        n = _norm_latin(name)
        if not n:
            return out
        out.add(n)
        toks = n.split()
        for i, t in enumerate(toks):
            if t in ("ibn", "bin", "abu", "abi", "umm") and i + 1 < len(toks):
                out.add(("ibn" if t in ("ibn", "bin") else t) + " " + toks[i + 1])
            if t in ("al", "as", "at", "ad", "ar", "az", "an", "ash", "el") and i + 1 < len(toks):
                out.add(toks[i + 1])
        if toks and toks[-1] not in ("tafsir", "quran", "al"):
            out.add(toks[-1])
    return {f for f in out if len(f.replace(" ", "")) >= 3}


def build_registry() -> Dict[str, RegistryEntry]:
    from app.services.tafsir_sources import SOURCE_CITATION_ALIASES, TAFSIR_CATALOG

    reg: Dict[str, RegistryEntry] = {}
    for key, entry in TAFSIR_CATALOG.items():
        e = reg.setdefault(key, RegistryEntry(key))
        for f in ("name_en", "name_ar", "author_en", "author_ar"):
            v = entry.get(f) or ""
            for part in re.split(r"\s+(?:and|و)\s+|[()]", v):
                if part.strip():
                    e.forms |= _short_forms(part)
    for key, names in SOURCE_CITATION_ALIASES.items():
        e = reg.setdefault(key, RegistryEntry(key))
        for n in names:
            e.forms |= _short_forms(n)
    # Generic work words are not names.
    for e in reg.values():
        e.forms -= {"tafsir", "quran", "تفسير", "القران", "التفسير", "الكريم"}
    return reg


_REGISTRY: Optional[Dict[str, RegistryEntry]] = None


def registry() -> Dict[str, RegistryEntry]:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = build_registry()
    return _REGISTRY


def registry_key(name: str) -> Optional[str]:
    """Catalogue source a name refers to (author or work), or None."""
    n = _norm_ar(name) if re.search(r"[ء-ي]", name) else _norm_latin(name)
    toks = n.split()
    cands = {n}
    # strip honorifics / leading article words
    cands |= {" ".join(toks[i:]) for i in range(len(toks))}
    if not re.search(r"[ء-ي]", name):
        cands |= {c.replace("al ", "").strip() for c in list(cands)}
    for key, e in registry().items():
        if cands & e.forms:
            return key
    return None


_REGISTRY_RE: Optional["re.Pattern"] = None


def strip_registry_names(text: str) -> str:
    """Remove catalogue work/author names (attribution, not content)."""
    global _REGISTRY_RE
    if _REGISTRY_RE is None:
        from app.services.tafsir_sources import SOURCE_CITATION_ALIASES, TAFSIR_CATALOG
        names: Set[str] = set()
        for entry in TAFSIR_CATALOG.values():
            for f in ("name_en", "name_ar", "author_en", "author_ar"):
                for part in re.split(r"\s+(?:and|و)\s+|[()]", entry.get(f) or ""):
                    if part.strip():
                        names.add(part.strip())
        for vals in SOURCE_CITATION_ALIASES.values():
            names.update(vals)
        pats = []
        for n in sorted(names, key=len, reverse=True):
            if re.search(r"[ء-ي]", n):
                body = re.escape(n).replace(r"\ ", r"\s+")
                pats.append(r"(?<![ء-ي])[وفبل]?" + body + r"(?![ء-ي])")
            else:
                body = re.escape(n).replace(r"\ ", r"[\s-]+").replace(r"\-", r"[\s-]+").replace("'", "['’]?")
                pats.append(r"\b(?:(?:the|al|el)[\s-]+)?" + body + r"(?:'s|’s)?\b")
        _REGISTRY_RE = re.compile("|".join(pats), re.IGNORECASE)
    return _REGISTRY_RE.sub(" ", text or "")


# ------------------------------------------------------------ name detection

_EN_TITLES = (
    r"(?:Shaykh\s+al-Islam|Shaykh|Sheikh|Shaikh|Imam|Al-Imam|al-Imam|Hafiz|Hafidh|al-Hafiz|al-Hafidh|"
    r"Allamah|'Allamah|Allama|Mufti|Qadi|Dr\.?|Doctor|Professor|Prof\.?|Mawlana|Maulana|Ustadh|Ustaz|"
    r"Sayyid|Sidi|Mulla|Hujjat\s+al-Islam|mufassir|exegete|jurist|scholar|commentator|historian|"
    r"traditionist|muhaddith|faqih|theologian|preacher|scholar\s+of\s+tafsir)"
)
_LATIN_NAME_TOKEN = r"(?:(?:al|el|ad|an|ar|as|at|az|ash|adh|ath)-)?[A-Z][\w'’`ʿ]+(?:-[A-Z][\w'’`ʿ]+)?"
_LATIN_NAME = rf"{_LATIN_NAME_TOKEN}(?:\s+(?:(?:ibn|bin|bint|Ibn|Bin|Abu|Abi|al|Al)[\s-]+)?{_LATIN_NAME_TOKEN}){{0,4}}"
_EN_SPEECH_VERBS = (
    r"(?:said|says|stated|states|wrote|writes|narrated|narrates|reported|reports|mentioned|mentions|"
    r"explained|explains|held|holds|argued|argues|commented|comments|opined|opines|ruled|rules|taught|"
    r"teaches|transmitted|transmits|related|relates|recorded|records|claimed|claims|noted|notes|"
    r"maintained|maintains|believed|believes|considered|considers|viewed|views|interpreted|interprets|"
    r"understood|understands|read|reads|recited|recites|adds|added|observed|observes|insisted|insists|"
    r"concluded|concludes|suggested|suggests|asserted|asserts|cited|cites|quoted|quotes|preferred|prefers|"
    r"emphasized|emphasised|emphasizes|emphasises|pointed\s+out|points\s+out)"
)
_EN_PATTERNS = (
    re.compile(rf"\b{_EN_TITLES}\s+(?P<name>{_LATIN_NAME})"),
    re.compile(rf"\b(?P<name>(?:Ibn|Abu|Abi|Umm|Bint)\s+{_LATIN_NAME})"),
    re.compile(rf"\b(?P<name>{_LATIN_NAME_TOKEN}\s+(?:ibn|bin|bint|Ibn|Bin)\s+{_LATIN_NAME})"),
    re.compile(rf"(?<![\w-])(?P<name>(?:al|el|ad|an|ar|as|at|az|ash|adh|ath)-[A-Z][\w'’`ʿ]+(?:\s+{_LATIN_NAME_TOKEN})?)"),
    re.compile(rf"\b(?:according\s+to|in\s+the\s+(?:view|opinion|words|reading|interpretation)\s+of|as\s+per|per|"
               rf"following|citing|quoting|after)\s+(?P<name>{_LATIN_NAME})"),
    re.compile(rf"\b(?:as\s+)?(?P<name>{_LATIN_NAME})(?:'s|’s)\s+(?:view|opinion|reading|interpretation|"
               rf"position|words|tafsir|commentary|explanation|understanding)\b"),
    re.compile(rf"\b(?P<name>{_LATIN_NAME})\s+(?:also\s+|further\s+|once\s+|famously\s+|rightly\s+)?{_EN_SPEECH_VERBS}\b"),
    re.compile(rf"\bas\s+(?P<name>{_LATIN_NAME})\s+(?:{_EN_SPEECH_VERBS}|puts\s+it|put\s+it)\b"),
)
# Capitalised words that are not person names in this domain: God, the
# Qur'an, prophets and angels, places, months, prayers, sentence starters.
_EN_NOT_NAMES = frozenset((
    "the this that these those in on at for from by to of and or but so as if when while after before then "
    "according also all some many one it its he she they we his her their our your you i a an there here "
    "allah god lord prophet messenger quran qur'an koran tafsir tafseer surah sura verse verses ayah ayat "
    "book scripture revelation almighty exalted most high sahih sunan musnad hadith hadiths muhammad jibril "
    "gabriel adam nuh noah ibrahim abraham musa moses isa jesus maryam mary yusuf joseph yaqub jacob dawud "
    "david sulayman solomon yunus jonah harun aaron ismail ishmael ishaq isaac lut lot hud salih shuayb "
    "ayyub job zakariyya zechariah yahya john idris ilyas elias luqman khidr khadir dhul qarnayn pharaoh "
    "firawn iblis satan shaytan muslims muslim believers believer people children israel companions sahabah "
    "ummah kursi throne paradise jannah hell fire hereafter islam iman ihsan salah salat zakah zakat sawm "
    "hajj umrah ramadan shawwal muharram makkah mecca madinah medina jerusalem quds kaaba ka'bah arabs arab "
    "jews christians quraysh ansar muhajirun aws khazraj badr uhud khandaq hudaybiyyah tabuk friday fajr "
    "dhuhr asr maghrib isha tahajjud witr eid sunnah shariah sharia fiqh qiyamah day judgement judgment "
    "resurrection night power qadr baqarah fatihah fatiha imran nisa maidah anam araf anfal tawbah yunus "
    "kahf taha anbiya hajj muminun nur furqan ahzab yasin saffat zumar fussilat shura zukhruf dukhan "
    "fath hujurat qaf rahman waqiah hadid mulk qalam muzzammil muddaththir insan naba asr ikhlas falaq nas "
    "kawthar duha sharh inshirah tin alaq qadr zalzalah adiyat takathur humazah fil quraish maun kafirun "
    "nasr masad lahab note however therefore thus moreover furthermore indeed truly reflection "
    "english arabic saheeh international muyassar jalalayn shade"
).split())
_EN_PARTICLES = frozenset("al el ad an ar as at az ash adh ath ibn bin bint abu abi umm".split())

_AR_TITLES = (
    r"(?:شيخ\s+الإسلام|شيخ\s+الاسلام|حجة\s+الإسلام|حجة\s+الاسلام|حبر\s+الأمة|ترجمان\s+القرآن|"
    r"الإمام\s+الأعظم|"
    r"ال?شيخ|ال?إمام|ال?امام|ال?حافظ|ال?علامة|ال?دكتور|د\.|ال?مفتي|ال?قاضي|ال?أستاذ|ال?استاذ|ال?فقيه|"
    r"ال?محدث|ال?مفسر|ال?مؤرخ|ال?داعية|سماحة|فضيلة)"
)
_LAQAB_ONLY = re.compile(
    r"(شيخ\s+الإسلام|شيخ\s+الاسلام|حجة\s+الإسلام|حجة\s+الاسلام|حبر\s+الأمة|ترجمان\s+القرآن|الإمام\s+الأعظم)"
    r"(?=\s*(?:$|[:،,.؛]|(?:إن|أن|ان|في|عن|على|رحمه|ذكر|قال|يرى|بأن)(?![ء-ي])))"
)
_AR_FRAME = re.compile(
    r"(?<![ء-ي])[وف]?(قال|يقول|ذكر|يذكر|روى|يروي|يرى|رأى|أورد|يورد|نقل|ينقل|حكى|يحكي|أكد|يؤكد|صرح|يصرح|"
    r"أشار|يشير|أفاد|يفيد|ذهب|يذهب|اختار|يختار|رجح|يرجح|فسر|يفسر|قرر|يقرر|عند|بحسب|حسب|وفق|وفقا\s+ل|"
    r"رأي|قول|مذهب|تفسير|اجتهاد|كلام|عن|رواية|روايه|حديث|أخرجه|اخرجه|رواه|خرجه|أثر|نقله)(?![ء-ي])\s+(?=(?P<rest>[^\[\].:؛،,؟!\n«»\"]{2,60}))"
)
# "قال مجاهد إن…", "وقال قتادة:" — a strong speech verb, one word, then the
# reported content: that word is a speaker.
_AR_SINGLE_NAME = re.compile(
    r"(?<![ء-ي])[وف]?(قال|يقول|روى|ذكر|نقل|حكى|فسرها|فسره)\s+(?P<name>[ء-ي]{3,})\s*(?=[:،,]|\s+(إن|أن|ان|في|عن)(?![ء-ي]))"
)
_WEAK_FRAMES = frozenset(normalize_arabic(w) for w in "عن رواية روايه حديث أثر تفسير قول كلام رأي مذهب".split())
_AR_KUNYA = re.compile(r"(?<![ء-ي])[وفبل]?(?P<name>(?:أبو|أبي|أبا|ابو|ابي|ابا|ابن|بن|أم|ام)\s+[ء-ي]{2,}(?:\s+ال[ء-ي]{2,})?)")
_AR_TITLED = re.compile(rf"(?<![ء-ي])[وفبل]?{_AR_TITLES}\s+(?P<name>[ء-ي]{{2,}}(?:\s+(?:بن|ابن|أبو|أبي|ال[ء-ي]+|[ء-ي]{{2,}})){{0,3}})")
_AR_NOT_NAMES = frozenset(normalize_arabic(w) for w in (
    "الله النبي الرسول رسول تعالى سبحانه القرآن القران الآية الاية الآيات السورة المفسرون المفسرين العلماء "
    "أهل التأويل التفسير الميسر هذا هذه ذلك أن إن ان الذي التي الذين في من على عن إلى الى كل بعض أحد "
    "الجمهور المسلمين المسلمون الصحابة السلف الأئمة الفقهاء المؤمنين المؤمنون الناس العرب ربك ربنا ربكم "
    "معنى المعنى قوله تعالى جل وعلا عز وجل الحق النبيين الأنبياء جبريل موسى عيسى إبراهيم محمد نوح "
    "الصلاة الزكاة الصيام الحج هو هي هم أنه أنها انه انها بأن بان ما لا قد كان كانت يكون"
).split())
_AR_PARTICLES = frozenset(normalize_arabic(w) for w in "ابن بن أبو أبي أبا ابو ابي ابا أم ام".split())
_AR_NAME_STOP = frozenset(normalize_arabic(w) for w in (
    "أن إن ان أنه إنه أنها إنها في عن بأن بان رحمه رضي قال يقول ذكر هذه هذا الآية على من إلى الى عند لأن "
    "حيث وهو وهي هو هي ما لا قد كما تعالى معنى المراد المقصود رحمهما وغيره وغيرهم وجماعة"
).split())


# An honorific title (laqab) used as a name, with no proper-name token:
# "the Proof of Islam", "the Sultan of the Scholars", "Fakhr al-Din",
# "Shaykh al-Mufassirin", "حجة الإسلام", "سلطان العلماء", "شيخ المفسرين".
# A title-noun in construct with a community, discipline or the religion is
# a person's epithet; the Prophet's titles (…of the Messengers / Prophets)
# are not matched.
_LAQAB_HEADS_EN = (r"(?:Proof|Sultan|Shaykh|Sheikh|Imam|Seal|Pride|Lamp|Sun|Ornament|Pillar|Crown|Chief|Master|Leader|"
                   r"Ocean|Sea|Ink|Interpreter|Hafiz|Hujjat|Hujja|Sayyid|Mujaddid|Reviver|Teacher|Elder|Glory|Light|"
                   r"Star|Sword|Moon|Beauty|Support)")
_LAQAB_TAILS_EN = (r"(?:Islam|the\s+Religion|the\s+Faith|the\s+Ummah|the\s+Community|the\s+Scholars|the\s+Exegetes|"
                   r"the\s+Commentators|the\s+Interpreters|the\s+Jurists|the\s+Traditionists|the\s+Hadith\s+Scholars|"
                   r"the\s+Muslims|the\s+Believers|the\s+Sunnah|the\s+Qur'?an|the\s+Imams|the\s+Age|the\s+Era|"
                   r"(?:His|Their)\s+Time|the\s+Mufassirin|the\s+Muhaddithin)")
_LAQAB_EN = re.compile(
    rf"\b(?:the\s+)?{_LAQAB_HEADS_EN}\s+of\s+{_LAQAB_TAILS_EN}\b"
    r"|\b(?:Shaykh|Sheikh|Imam|Hujjat|Sultan|Taj|Shams|Fakhr|Badr|Sayf|Jamal|Izz|Najm|Muhyi|Taqi|Sharaf|Nur|Qutb|Zayn|"
    r"Burhan|Sadr|Imad|Jalal|Kamal|Rukn|Shihab|Siraj|Ala|Ala'|Nasir|Sa'd|Shaikh)[\s-]+(?:al|ad|ud|ul|an|ash|as|ar)[\s-]+"
    r"(?:Islam|Din|Deen|Dien|Ummah|Mufassirin|Muhaddithin|Ulama|Sunnah)\b",
    re.IGNORECASE,
)
_LAQAB_AR = re.compile(
    r"(?<![ء-ي])[وفل]?(?:ال)?(?:شيخ|إمام|امام|حجة|حبر|ترجمان|سلطان|تاج|شمس|فخر|بدر|سيف|جمال|عز|نجم|محيي|محيى|تقي|"
    r"شرف|نور|عمدة|خاتمة|رئيس|قطب|زين|برهان|صدر|عماد|جلال|كمال|ركن|شهاب|سراج|علاء|ناصر|مجدد|بحر|فقيه|محدث|مفسر)\s+"
    r"(?:ال)?(?:إسلام|اسلام|دين|أمة|امة|مفسرين|محدثين|علماء|قرآن|قران|سنة|حفاظ|فقهاء|أئمة|ائمة|مسلمين|عصر|زمان|"
    r"دنيا|مشرق|مغرب|شام|عراق|حجاز|يمن|حرمين|هدى|مذهب|ملة|حق|عارفين|زاهدين|قراء|نحاة|لغة)(?![ء-ي])"
)
_LAQAB_NOT = re.compile(r"المرسلين|النبيين|الأنبياء|الانبياء|Messengers|Prophets", re.IGNORECASE)


def _clean_latin(name: str) -> Optional[str]:
    name = re.sub(r"(?:'s|’s)$", "", name.strip())
    toks = [t.strip(" '’`-") for t in re.split(r"\s+", name.strip()) if t.strip(" '’`-")]
    while toks and toks[0].lower().replace("al-", "") in _EN_NOT_NAMES and toks[0].lower() not in _EN_PARTICLES:
        toks.pop(0)
    while toks and toks[-1].lower() in _EN_NOT_NAMES:
        toks.pop()
    distinctive = [t for t in toks if t.lower() not in _EN_PARTICLES and
                   re.sub(r"^(al|el|ad|an|ar|as|at|az|ash|adh|ath)-", "", t.lower()) not in _EN_NOT_NAMES]
    if not distinctive:
        return None
    return " ".join(toks)


def _clean_arabic(rest: str, max_words: int = 5) -> Optional[str]:
    """The name at the start of ``rest``: kunya/nasab chains (أبو X، X بن Y، عبد X)
    and "ال…ي" nisbas; None when ``rest`` does not start with a name."""
    raw = rest.split()
    norm = [normalize_arabic(w) for w in raw]
    out: List[str] = []
    i = 0
    while i < len(norm) and len(out) < max_words:
        w = norm[i]
        nxt = norm[i + 1] if i + 1 < len(norm) else ""
        if not w or w in _AR_NAME_STOP:
            break
        if w in _AR_PARTICLES and nxt and nxt not in _AR_NAME_STOP:
            out += raw[i:i + 2]
            i += 2
            continue
        if w == "عبد" and nxt:
            out += raw[i:i + 2]
            i += 2
            continue
        if w.startswith("ال") and w.endswith("ي") and len(w) >= 5 and w not in _AR_NOT_NAMES:
            out.append(raw[i])
            i += 1
            continue
        if nxt in ("بن", "ابن") and w not in _AR_NOT_NAMES:
            out.append(raw[i])
            i += 1
            continue
        if out and w not in _AR_NOT_NAMES and not w.startswith("ال") and len(out) < 3 and nxt in _AR_PARTICLES:
            out.append(raw[i])
            i += 1
            continue
        break
    if not out:
        return None
    distinctive = [w for w in (normalize_arabic(x) for x in out) if w not in _AR_PARTICLES and w not in _AR_NOT_NAMES]
    return " ".join(out) if distinctive else None


def find_person_names(sentence: str) -> List[str]:
    """Person (or work) names a sentence attributes something to, or mentions by kunya/title."""
    out: List[str] = []

    def add(n: Optional[str]):
        if n and n not in out:
            out.append(n)

    for pat in _EN_PATTERNS:
        for m in pat.finditer(sentence):
            add(_clean_latin(m.group("name")))
    for m in _LAQAB_ONLY.finditer(sentence):
        add(m.group(1))
    for pat in (_LAQAB_EN, _LAQAB_AR):
        for m in pat.finditer(sentence):
            if not _LAQAB_NOT.search(m.group(0)):
                add(m.group(0).strip())
    for m in _AR_TITLED.finditer(sentence):
        first = m.group("name").split()[0]
        add(_clean_arabic(m.group("name")) or (first if normalize_arabic(first) not in _AR_NOT_NAMES
                                               and normalize_arabic(first) not in _AR_NAME_STOP else None))
    for m in _AR_KUNYA.finditer(sentence):
        add(_clean_arabic(m.group("name")))
    for m in _AR_SINGLE_NAME.finditer(sentence):
        w = normalize_arabic(m.group("name"))
        if w not in _AR_NOT_NAMES and w not in _AR_NAME_STOP and not w.startswith("ال") and len(w) >= 3:
            add(m.group("name"))
    for m in _AR_FRAME.finditer(sentence):
        name = _clean_arabic(m.group("rest"))
        verb = normalize_arabic(m.group(0).split()[0]).lstrip("وف")
        if name and verb in _WEAK_FRAMES and not re.search(r"(^| )(ابن|بن|ابو|ابي|ابا|ام|عبد) ",
                                                            normalize_arabic(name) + " "):
            continue  # "عن المشي", "حديث النفس": a noun, not a person
        add(name)
    # Drop names contained in a longer one already found.
    return [n for n in out if not any(n != o and n in o for o in out)]


# -------------------------------------------------------------- support

_PARTICLE_SKELETON = {"ibn": "bn", "bin": "bn", "bint": "bnt", "abu": "b", "abi": "b", "aba": "b", "umm": "m",
                      "ابن": "bn", "بن": "bn", "ابو": "b", "ابي": "b", "ابا": "b", "ام": "m"}


def _skeleton_sequence_in(name: str, text_skeletons: Sequence[str]) -> bool:
    """Whole-name match on consonant skeletons ("Ubayy ibn Ka'b" = "أبي بن كعب"),
    for names whose parts are too short to match one by one."""
    toks = [t for t in _norm_latin(name).split() if t not in ("al", "el")]
    seq = [_PARTICLE_SKELETON.get(t, latin_skeleton(t)) for t in toks]
    seq = [x for x in seq if x]
    if len(seq) < 2 or sum(len(x) for x in seq) < 4:
        return False
    n = len(seq)
    for i in range(len(text_skeletons) - n + 1):
        if list(text_skeletons[i:i + n]) == seq:
            return True
    return False


def _latin_variants(word: str) -> Set[str]:
    """Consonant skeletons of a Latin name word, read with and without a
    leading article and with a final "-ah"/"-at" as tā' marbūṭa."""
    w = re.sub(r"[^a-z]", "", en_fold(word))
    forms = {w, re.sub(r"(?<=[aiu])[ht]$", "", w)}
    out = set()
    for f in forms:
        out.add(latin_skeleton(f))
        sk = re.sub(r"[aeiouwy]", "", f)
        for a, b in (("th", "t"), ("dh", "d"), ("sh", "s"), ("kh", "h"), ("gh", "g"), ("q", "k")):
            sk = sk.replace(a, b)
        out.add(re.sub(r"(.)\1+", r"\1", sk))
    return {x for x in out if x}


def _kunya_in(name: str, words: Sequence[str]) -> bool:
    """"Abu al-Aliyah" / "Umm Salamah" = "أبو العالية" / "أم سلمة": a kunya whose
    second word is too short in consonants to match alone is matched as the
    adjacent pair (the Latin word must be four letters or more)."""
    toks = [t for t in _norm_latin(name).split() if t not in ("al", "el")]
    for i, t in enumerate(toks[:-1]):
        if t not in ("abu", "abi", "aba", "umm") or len(toks[i + 1]) < 4:
            continue
        variants = _latin_variants(toks[i + 1])
        for j, w in enumerate(words[:-1]):
            nxt = words[j + 1][2:] if words[j + 1].startswith("ال") else words[j + 1]
            if w in ("ابو", "ابي", "ابا", "ام", "وابو", "وابي", "فابو") and arabic_skeleton(words[j + 1]) in variants \
                    and len(nxt) >= 0.6 * len(toks[i + 1]):
                return True
    return False


def _evidence_meta(chunk: object) -> str:
    return " ".join(filter(None, (str(getattr(chunk, f, "") or "") for f in
                                   ("source_name", "source_name_ar", "author", "author_name", "author_name_ar"))))


def name_in_text(name: str, text: str) -> bool:
    """Does ``text`` mention the person ``name`` (any script)?"""
    if not text:
        return False
    if re.search(r"[ء-ي]", name):
        parts = [w for w in normalize_arabic(name).split() if w not in _AR_PARTICLES and w not in _AR_NOT_NAMES]
        if not parts:
            return False
        words = normalize_arabic(text).split()
        stems = {w for w in words} | {w[1:] for w in words if w[:1] in "وفبل"} | \
                {w[2:] for w in words if w.startswith("ال")} | {"ال" + w for w in words}
        return all(p in stems or (p.startswith("ال") and p[2:] in stems) for p in parts)
    parts = [t for t in _norm_latin(name).split() if t not in _EN_PARTICLES and len(t) > 1]
    if not parts:
        return False
    if re.search(r"[a-zA-Z]", text):
        hay = f" {_norm_latin(text)} "
        if all(f" {p} " in hay for p in parts):
            return True
    if re.search(r"[ء-ي]", text):
        sk_words = [_PARTICLE_SKELETON.get(w, arabic_skeleton(w)) for w in normalize_arabic(text).split()]
        skset = set(sk_words)
        sks = [latin_skeleton(p) for p in parts]
        long = [s for s in sks if len(s) >= MIN_SKELETON]
        short = [s for s in sks if len(s) < MIN_SKELETON]
        if not long or short:
            return _skeleton_sequence_in(name, sk_words) or _kunya_in(name, normalize_arabic(text).split())
        if not all(s in skset for s in long):
            return False
        # A nisba ("al-Fahdawi", "al-Qurashi") is matched only by a nisba
        # (a word ending in ي): a three-consonant skeleton alone matches
        # ordinary words ("فهد").
        nisba_sk = {latin_skeleton(p) for p in parts if re.search(r"(?:i|iy|iyy|ee)$", p) and len(p) > 4}
        if nisba_sk:
            words = normalize_arabic(text).split()
            nisba_words = {arabic_skeleton(w) for w in words if w.endswith("ي") and len(w) >= 4}
            if not all(s in nisba_words for s in nisba_sk if len(s) <= 3):
                return False
        if short:
            # short parts must appear next to a long part
            for i, s in enumerate(sk_words):
                if s in long:
                    window = set(sk_words[max(0, i - 4): i + 5])
                    if all(x in window for x in short):
                        return True
            return False
        return True
    return False


def name_supported(name: str, chunks: Sequence[object], texts: Sequence[str]) -> bool:
    """The named person/work is the author/work of a cited chunk, or is named in its text."""
    from app.services.tafsir_sources import source_base_id

    key = registry_key(name)
    cited_keys = {source_base_id(getattr(c, "source_id", "") or "") for c in chunks}
    if key is not None and key in cited_keys:
        return True
    for c in chunks:
        if name_in_text(name, _evidence_meta(c)):
            return True
    return any(name_in_text(name, t) for t in texts)


# ----------------------------------------------------- collective claims

CONSENSUS = "consensus"
DISPUTE = "dispute"
MAJORITY = "majority"

_COLLECTIVE_EN = (r"(scholars|commentators|exegetes|mufassirun|mufassirin|jurists|imams|ulama|'ulama|"
                  r"companions|salaf|authorities|interpreters|muslims|ummah|schools)")
_CLAIM_PATTERNS: Tuple[Tuple[str, re.Pattern], ...] = tuple((k, re.compile(p, re.IGNORECASE)) for k, p in (
    (CONSENSUS, rf"\b(all|every|the)\s+(of\s+the\s+)?(\w+\s+){{0,2}}{_COLLECTIVE_EN}\s+(\w+\s+){{0,2}}"
                r"(agree|agreed|are\s+unanimous|were\s+unanimous|concur|concurred|accept|accepted)\b"),
    (CONSENSUS, r"\b(unanimous(ly)?|consensus|ijma['’]?|undisputed|uncontested|without\s+(any\s+)?"
                r"(disagreement|dispute|exception))\b"),
    (CONSENSUS, rf"\b(no|not\s+a\s+single|none\s+of\s+the)\s+(\w+\s+){{0,2}}({_COLLECTIVE_EN[1:-1]}|scholar|"
                r"commentator|exegete|jurist|one)\s+(\w+\s+){0,3}(disputes?|disputed|differs?|differed|disagrees?|"
                r"disagreed|denies|denied|objects?|objected)\b"),
    (MAJORITY, rf"\b(the\s+)?(majority|most|jumhur|bulk)\s+of\s+(the\s+)?(\w+\s+){{0,2}}{_COLLECTIVE_EN}\b"
               r"|\bjumhur\b"),
    (DISPUTE, rf"\b{_COLLECTIVE_EN}\s+(\w+\s+){{0,3}}(differ|differed|disagree|disagreed|are\s+divided|were\s+divided|"
              r"hold\s+different|have\s+different|gave\s+different|offered\s+different|used\s+different)\b"
              r"|\b(difference|differences|disagreement)\s+(of\s+opinion|among|between)\b"
              r"|\b(two|three|several|various|different)\s+(views|opinions|interpretations|positions)\b"),
    (CONSENSUS, r"(?<![ء-ي])[وف]?(أجمع|اجمع|أجمعت|اجمعت|اتفق|اتفقت|أطبق)\s+(العلماء|الأمة|الامة|المفسرون|المسلمون|"
                r"أهل|السلف|الفقهاء|الأئمة|الصحابة|جميع|كل)"
                r"|(?<![ء-ي])(بالإجماع|بالاجماع|إجماع|اجماع)(?![ء-ي])|لا\s+خلاف|بلا\s+خلاف|دون\s+خلاف"
                r"|(لم|ما)\s+(يختلف|يخالف|ينازع|ينكر)\s+(أحد|احد|فيه\s+أحد)|ليس\s+(بين|فيه)\s+\S+\s+خلاف"
                r"|(?<![ء-ي])(كل|جميع)\s+(العلماء|المفسرين|الفقهاء|الأئمة)\s+(على|يرون|متفقون|اتفقوا)"),
    (MAJORITY, r"(?<![ء-ي])(جمهور|الجمهور|أكثر\s+(العلماء|المفسرين|الفقهاء|أهل)|عامة\s+(العلماء|المفسرين|أهل))"),
    (DISPUTE, r"(?<![ء-ي])[وف]?(اختلف|اختلفت|اختلفوا|يختلف|تختلف|خلاف|الخلاف|قولان|أقوال|اقوال|القولين)(?![ء-ي])"),
))
_EVIDENCE_MARKERS = {
    CONSENSUS: re.compile(r"\b(consensus|unanimous\w*|agree\w*|ijma\w*|no\s+(disagreement|difference))\b"
                          r"|أجمع|اجمع|إجماع|اجماع|اتفق|لا\s+خلاف|بلا\s+خلاف|لا\s+يختلف", re.IGNORECASE),
    MAJORITY: re.compile(r"\b(majority|most\s+of\s+the|jumhur)\b|جمهور|الجمهور|أكثر\s+(أهل|العلماء|المفسرين)|"
                         r"أكثرهم|عامة\s+(أهل|العلماء|المفسرين)", re.IGNORECASE),
    DISPUTE: re.compile(r"\b(differ\w*|disagree\w*|dispute\w*|another\s+view|others\s+said|some\s+said|it\s+is\s+"
                        r"said|opinions)\b|اختلف|خلاف|قولان|أقوال|اقوال|وقيل|وقال\s+آخرون|وقال\s+بعضهم|فقال\s+"
                        r"بعضهم|وقال\s+غيره|القول\s+الثاني", re.IGNORECASE),
}


def collective_claims(sentence: str) -> List[str]:
    kinds = []
    for kind, pat in _CLAIM_PATTERNS:
        if pat.search(sentence) and kind not in kinds:
            kinds.append(kind)
    return kinds


_SPEAKER_AR = re.compile(r"(?<![ء-ي])[وف]?(?:قال|وقال|قاله|روي\s+عن|عن)\s+((?:ابن|أبو|ابو|أبي|ابي)?\s*[ء-ي]{3,})")
_SPEAKER_EN = re.compile(r"\b([A-Z][\w'`-]+(?:\s+(?:ibn|bin|bint|Ibn|Abu|al-\w+|Al-\w+))?(?:\s+[A-Z][\w'`-]+)?)\s+said\b")


def _several_speakers(text: str) -> bool:
    """The text reports the words of several different authorities on the
    point ("قال مجاهد… وقال الحسن…"): a difference of views laid out."""
    speakers = {normalize_arabic(m.group(1)) for m in _SPEAKER_AR.finditer(text or "")}
    speakers -= {normalize_arabic(w) for w in ("تعالى", "الله", "رسول", "النبي", "رسول الله", "لهم", "له")}
    if len(speakers) >= 3:
        return True
    return len({m.group(1) for m in _SPEAKER_EN.finditer(text or "")} - {"Allah", "He", "The"}) >= 3


def collective_supported(kind: str, texts: Iterable[str]) -> bool:
    pat = _EVIDENCE_MARKERS[kind]
    texts = list(texts)
    if any(pat.search(t or "") for t in texts):
        return True
    return kind == DISPUTE and any(_several_speakers(t) for t in texts)
