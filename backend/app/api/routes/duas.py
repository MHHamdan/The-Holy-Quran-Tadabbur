"""
Quranic Duʿā API — serves the static dua catalogue with server-side filtering.

All data is derived from exact Quranic references (Hafs ʿan ʿĀṣim).
No AI-generated content. Source: frontend/src/data/quranicDuas.ts (same dataset).

Rate-limited to 30 requests/min per IP.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.rate_limit import InMemoryRateLimiter, _get_client_ip, _make_429_response

logger = logging.getLogger(__name__)

router = APIRouter()

_duas_limiter = InMemoryRateLimiter(max_requests=30, window_seconds=60)


async def _rate_limit(request: Request) -> None:
    ip = _get_client_ip(request)
    allowed, retry_after = _duas_limiter.is_allowed(ip)
    if not allowed:
        logger.warning("Duas rate limit exceeded for IP %s", ip)
        raise _make_429_response(request)


# ── Static catalogue ──────────────────────────────────────────────────────────
# Sourced 1-to-1 from quranicDuas.ts; kept in sync manually.
# Arabic text is the Uthmani rasm — do NOT edit without human review.

_DUAS: list[dict] = [
    # Category: prophets (أدعية الأنبياء)
    {"id": "ibrahim-01", "surah": 2, "ayah": 127, "ayahEnd": 128, "category": "prophets", "prophet": "Ibrahim",
     "titleEn": "Ibrahim's Duʿā while building the Kaʿba", "titleAr": "دعاء إبراهيم عند بناء الكعبة",
     "surahNameEn": "Al-Baqarah", "surahNameAr": "البقرة",
     "meaningEn": "Our Lord! Accept [this] from us. Indeed, You are the Hearing, the Knowing.",
     "meaningAr": "رَبَّنَا تَقَبَّلْ مِنَّا ۖ إِنَّكَ أَنتَ السَّمِيعُ الْعَلِيمُ",
     "occasions": ["after_prayer", "seeking_guidance"],
     "tags": ["kaaba", "prophets", "acceptance"]},
    {"id": "ibrahim-02", "surah": 2, "ayah": 286, "ayahEnd": None, "category": "protection", "prophet": "Ibrahim",
     "titleEn": "Do not burden us beyond our capacity", "titleAr": "ربنا لا تحملنا ما لا طاقة لنا به",
     "surahNameEn": "Al-Baqarah", "surahNameAr": "البقرة",
     "meaningEn": "Our Lord, do not impose on us what we cannot bear, pardon us, forgive us, and have mercy on us.",
     "meaningAr": "رَبَّنَا وَلَا تُحَمِّلْنَا مَا لَا طَاقَةَ لَنَا بِهِ ۖ وَاعْفُ عَنَّا وَاغْفِرْ لَنَا وَارْحَمْنَا",
     "occasions": ["hardship", "seeking_forgiveness", "after_prayer"],
     "tags": ["forgiveness", "hardship", "mercy"]},
    {"id": "anbiya-yusuf-01", "surah": 12, "ayah": 101, "ayahEnd": None, "category": "prophets", "prophet": "Yusuf",
     "titleEn": "Yusuf's Duʿā after reunion", "titleAr": "دعاء يوسف بعد لقاء أهله",
     "surahNameEn": "Yusuf", "surahNameAr": "يوسف",
     "meaningEn": "My Lord, You have given me of sovereignty and taught me the interpretation of dreams. Creator of the heavens and earth, You are my protector in this world and the Hereafter. Cause me to die a Muslim and join me with the righteous.",
     "meaningAr": "رَبِّ قَدْ آتَيْتَنِي مِنَ الْمُلْكِ وَعَلَّمْتَنِي مِن تَأْوِيلِ الْأَحَادِيثِ ۚ فَاطِرَ السَّمَاوَاتِ وَالْأَرْضِ أَنتَ وَلِيِّي فِي الدُّنْيَا وَالْآخِرَةِ ۖ تَوَفَّنِي مُسْلِمًا وَأَلْحِقْنِي بِالصَّالِحِينَ",
     "occasions": ["seeking_guidance", "gratitude_moment"],
     "tags": ["prophets", "death", "righteous"]},
    {"id": "musa-01", "surah": 20, "ayah": 25, "ayahEnd": 28, "category": "prophets", "prophet": "Musa",
     "titleEn": "Musa's Duʿā before Pharaoh", "titleAr": "دعاء موسى قبل مواجهة فرعون",
     "surahNameEn": "Ta-Ha", "surahNameAr": "طه",
     "meaningEn": "My Lord, relieve my heart, ease my task for me, untie the knot from my tongue, that they may understand my speech.",
     "meaningAr": "رَبِّ اشْرَحْ لِي صَدْرِي ۝ وَيَسِّرْ لِي أَمْرِي ۝ وَاحْلُلْ عُقْدَةً مِّن لِّسَانِي ۝ يَفْقَهُوا قَوْلِي",
     "occasions": ["hardship", "studying", "seeking_guidance"],
     "tags": ["prophets", "speech", "ease"]},
    {"id": "sulayman-01", "surah": 27, "ayah": 19, "ayahEnd": None, "category": "gratitude", "prophet": "Sulayman",
     "titleEn": "Sulayman's Duʿā of gratitude", "titleAr": "دعاء سليمان شكراً",
     "surahNameEn": "An-Naml", "surahNameAr": "النمل",
     "meaningEn": "My Lord, enable me to be grateful for Your favor which You have bestowed upon me and upon my parents and to do righteousness of which You approve. And admit me by Your mercy into [the ranks of] Your righteous servants.",
     "meaningAr": "رَبِّ أَوْزِعْنِي أَنْ أَشْكُرَ نِعْمَتَكَ الَّتِي أَنْعَمْتَ عَلَيَّ وَعَلَىٰ وَالِدَيَّ وَأَنْ أَعْمَلَ صَالِحًا تَرْضَاهُ وَأَدْخِلْنِي بِرَحْمَتِكَ فِي عِبَادِكَ الصَّالِحِينَ",
     "occasions": ["gratitude_moment", "after_prayer", "morning"],
     "tags": ["prophets", "gratitude", "righteous"]},
    {"id": "ayyub-01", "surah": 21, "ayah": 83, "ayahEnd": None, "category": "prophets", "prophet": "Ayyub",
     "titleEn": "Ayyub's Duʿā in affliction", "titleAr": "دعاء أيوب في الضر",
     "surahNameEn": "Al-Anbiya", "surahNameAr": "الأنبياء",
     "meaningEn": "Indeed, adversity has touched me, and you are the Most Merciful of the merciful.",
     "meaningAr": "رَّبِّ أَنِّي مَسَّنِيَ الضُّرُّ وَأَنتَ أَرْحَمُ الرَّاحِمِينَ",
     "occasions": ["hardship", "health", "anxiety"],
     "tags": ["prophets", "patience", "healing"]},
    {"id": "yunus-01", "surah": 21, "ayah": 87, "ayahEnd": None, "category": "prophets", "prophet": "Yunus",
     "titleEn": "Yunus's Duʿā in the darkness", "titleAr": "دعاء يونس في الظلمات",
     "surahNameEn": "Al-Anbiya", "surahNameAr": "الأنبياء",
     "meaningEn": "There is no god except You; exalted are You. Indeed, I have been of the wrongdoers.",
     "meaningAr": "لَّا إِلَٰهَ إِلَّا أَنتَ سُبْحَانَكَ إِنِّي كُنتُ مِنَ الظَّالِمِينَ",
     "occasions": ["seeking_forgiveness", "hardship", "anxiety"],
     "tags": ["prophets", "tawbah", "tasbih"]},
    {"id": "zakariyya-01", "surah": 21, "ayah": 89, "ayahEnd": None, "category": "prophets", "prophet": "Zakariyya",
     "titleEn": "Zakariyya's Duʿā for an heir", "titleAr": "دعاء زكريا طلباً للذرية",
     "surahNameEn": "Al-Anbiya", "surahNameAr": "الأنبياء",
     "meaningEn": "My Lord, do not leave me alone [with no heir], and you are the best of inheritors.",
     "meaningAr": "رَّبِّ لَا تَذَرْنِي فَرْدًا وَأَنتَ خَيْرُ الْوَارِثِينَ",
     "occasions": ["for_children", "seeking_guidance"],
     "tags": ["prophets", "children", "family"]},
    # Category: forgiveness
    {"id": "adam-01", "surah": 7, "ayah": 23, "ayahEnd": None, "category": "forgiveness", "prophet": "Adam",
     "titleEn": "Adam & Hawwa's Duʿā of repentance", "titleAr": "دعاء آدم وحواء في التوبة",
     "surahNameEn": "Al-Aʿraf", "surahNameAr": "الأعراف",
     "meaningEn": "Our Lord, we have wronged ourselves, and if You do not forgive us and have mercy upon us, we will surely be among the losers.",
     "meaningAr": "رَبَّنَا ظَلَمْنَا أَنفُسَنَا وَإِن لَّمْ تَغْفِرْ لَنَا وَتَرْحَمْنَا لَنَكُونَنَّ مِنَ الْخَاسِرِينَ",
     "occasions": ["seeking_forgiveness", "after_prayer"],
     "tags": ["tawbah", "forgiveness", "adam"]},
    {"id": "istighfar-01", "surah": 3, "ayah": 16, "ayahEnd": None, "category": "forgiveness", "prophet": None,
     "titleEn": "Duʿā of the firm in faith", "titleAr": "دعاء الراسخين في الإيمان",
     "surahNameEn": "Ali-ʿImran", "surahNameAr": "آل عمران",
     "meaningEn": "Our Lord, indeed we have believed, so forgive us our sins and protect us from the punishment of the Fire.",
     "meaningAr": "رَبَّنَا إِنَّنَا آمَنَّا فَاغْفِرْ لَنَا ذُنُوبَنَا وَقِنَا عَذَابَ النَّارِ",
     "occasions": ["seeking_forgiveness", "after_prayer", "before_sleep"],
     "tags": ["forgiveness", "faith", "fire"]},
    # Category: guidance
    {"id": "fatiha-01", "surah": 1, "ayah": 5, "ayahEnd": 7, "category": "guidance", "prophet": None,
     "titleEn": "Al-Fatiha — Guide us to the straight path", "titleAr": "الفاتحة — اهدنا الصراط المستقيم",
     "surahNameEn": "Al-Fatihah", "surahNameAr": "الفاتحة",
     "meaningEn": "It is You we worship and You we ask for help. Guide us to the straight path — the path of those upon whom You have bestowed favor, not of those who have evoked anger or of those who are astray.",
     "meaningAr": "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ ۝ اهْدِنَا الصِّرَاطَ الْمُسْتَقِيمَ ۝ صِرَاطَ الَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ الْمَغْضُوبِ عَلَيْهِمْ وَلَا الضَّالِّينَ",
     "occasions": ["after_prayer", "morning", "evening", "seeking_guidance"],
     "tags": ["fatiha", "guidance", "prayer"]},
    {"id": "istikhara-01", "surah": 18, "ayah": 10, "ayahEnd": None, "category": "guidance", "prophet": None,
     "titleEn": "Duʿā of the Companions of the Cave", "titleAr": "دعاء أصحاب الكهف",
     "surahNameEn": "Al-Kahf", "surahNameAr": "الكهف",
     "meaningEn": "Our Lord, grant us from Yourself mercy and prepare for us from our affair right guidance.",
     "meaningAr": "رَبَّنَا آتِنَا مِن لَّدُنكَ رَحْمَةً وَهَيِّئْ لَنَا مِنْ أَمْرِنَا رَشَدًا",
     "occasions": ["seeking_guidance", "hardship"],
     "tags": ["guidance", "mercy", "cave"]},
    # Category: protection
    {"id": "ayat-kursi-01", "surah": 2, "ayah": 255, "ayahEnd": None, "category": "protection", "prophet": None,
     "titleEn": "Ayat al-Kursi — the Throne verse", "titleAr": "آية الكرسي",
     "surahNameEn": "Al-Baqarah", "surahNameAr": "البقرة",
     "meaningEn": "Allah — there is no deity except Him, the Ever-Living, the Sustainer of existence. Neither drowsiness overtakes Him nor sleep. To Him belongs whatever is in the heavens and whatever is on the earth.",
     "meaningAr": "اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ ۚ لَا تَأْخُذُهُ سِنَةٌ وَلَا نَوْمٌ",
     "occasions": ["morning", "evening", "before_sleep", "after_prayer"],
     "tags": ["protection", "throne", "morning", "sleep"]},
    {"id": "kaafiroon-01", "surah": 2, "ayah": 201, "ayahEnd": None, "category": "balance", "prophet": None,
     "titleEn": "Duʿā for good in this life and the Hereafter", "titleAr": "دعاء الخير في الدنيا والآخرة",
     "surahNameEn": "Al-Baqarah", "surahNameAr": "البقرة",
     "meaningEn": "Our Lord, give us in this world [that which is] good and in the Hereafter [that which is] good and protect us from the punishment of the Fire.",
     "meaningAr": "رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ",
     "occasions": ["after_prayer", "morning", "evening"],
     "tags": ["dunya", "akhirah", "balance"]},
    # Category: gratitude
    {"id": "shukr-01", "surah": 14, "ayah": 7, "ayahEnd": None, "category": "gratitude", "prophet": None,
     "titleEn": "If you are grateful, I will increase you", "titleAr": "لَئِن شَكَرْتُمْ لَأَزِيدَنَّكُمْ",
     "surahNameEn": "Ibrahim", "surahNameAr": "إبراهيم",
     "meaningEn": "If you are grateful, I will surely increase you [in favor]; but if you deny, indeed, My punishment is severe.",
     "meaningAr": "لَئِن شَكَرْتُمْ لَأَزِيدَنَّكُمْ ۖ وَلَئِن كَفَرْتُمْ إِنَّ عَذَابِي لَشَدِيدٌ",
     "occasions": ["gratitude_moment", "morning"],
     "tags": ["gratitude", "increase", "blessings"]},
    # Category: family
    {"id": "parents-01", "surah": 17, "ayah": 24, "ayahEnd": None, "category": "family", "prophet": None,
     "titleEn": "Duʿā for parents' mercy", "titleAr": "دعاء الرحمة للوالدين",
     "surahNameEn": "Al-Isra", "surahNameAr": "الإسراء",
     "meaningEn": "My Lord, have mercy upon them as they brought me up [when I was] small.",
     "meaningAr": "رَّبِّ ارْحَمْهُمَا كَمَا رَبَّيَانِي صَغِيرًا",
     "occasions": ["for_parents", "after_prayer"],
     "tags": ["parents", "mercy", "family"]},
    {"id": "children-01", "surah": 25, "ayah": 74, "ayahEnd": None, "category": "family", "prophet": None,
     "titleEn": "Our Lord, grant us good spouses and offspring", "titleAr": "ربنا هب لنا من أزواجنا وذرياتنا",
     "surahNameEn": "Al-Furqan", "surahNameAr": "الفرقان",
     "meaningEn": "Our Lord, grant us from among our wives and offspring comfort to our eyes and make us an example for the righteous.",
     "meaningAr": "رَبَّنَا هَبْ لَنَا مِنْ أَزْوَاجِنَا وَذُرِّيَّاتِنَا قُرَّةَ أَعْيُنٍ وَاجْعَلْنَا لِلْمُتَّقِينَ إِمَامًا",
     "occasions": ["for_children", "for_parents", "after_prayer"],
     "tags": ["family", "spouse", "children"]},
    # Category: healing
    {"id": "shifa-01", "surah": 26, "ayah": 80, "ayahEnd": None, "category": "healing", "prophet": "Ibrahim",
     "titleEn": "Ibrahim — When I am ill, He cures me", "titleAr": "إبراهيم — وإذا مرضت فهو يشفين",
     "surahNameEn": "Ash-Shuʿara", "surahNameAr": "الشعراء",
     "meaningEn": "And when I am ill, it is He who cures me.",
     "meaningAr": "وَإِذَا مَرِضْتُ فَهُوَ يَشْفِينِ",
     "occasions": ["health", "hardship"],
     "tags": ["healing", "prophets", "illness"]},
    # Category: knowledge
    {"id": "ilm-01", "surah": 20, "ayah": 114, "ayahEnd": None, "category": "knowledge", "prophet": None,
     "titleEn": "My Lord, increase me in knowledge", "titleAr": "رب زدني علما",
     "surahNameEn": "Ta-Ha", "surahNameAr": "طه",
     "meaningEn": "My Lord, increase me in knowledge.",
     "meaningAr": "رَّبِّ زِدْنِي عِلْمًا",
     "occasions": ["studying", "morning"],
     "tags": ["knowledge", "learning", "ilm"]},
    # Category: tawakkul
    {"id": "tawakkul-01", "surah": 9, "ayah": 129, "ayahEnd": None, "category": "tawakkul", "prophet": None,
     "titleEn": "He is sufficient for me — Hasbunallah", "titleAr": "حسبي الله لا إله إلا هو",
     "surahNameEn": "At-Tawbah", "surahNameAr": "التوبة",
     "meaningEn": "He is sufficient for me; there is no deity except Him. On Him I have relied, and He is the Lord of the great throne.",
     "meaningAr": "حَسْبِيَ اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ ۖ عَلَيْهِ تَوَكَّلْتُ ۖ وَهُوَ رَبُّ الْعَرْشِ الْعَظِيمِ",
     "occasions": ["anxiety", "hardship", "seeking_guidance"],
     "tags": ["tawakkul", "reliance", "throne"]},
    # Category: balance
    {"id": "steadfastness-01", "surah": 3, "ayah": 8, "ayahEnd": None, "category": "balance", "prophet": None,
     "titleEn": "Our Lord, do not let our hearts deviate", "titleAr": "ربنا لا تزغ قلوبنا",
     "surahNameEn": "Ali-ʿImran", "surahNameAr": "آل عمران",
     "meaningEn": "Our Lord, let not our hearts deviate after You have guided us and grant us from Yourself mercy. Indeed, You are the Bestower.",
     "meaningAr": "رَبَّنَا لَا تُزِغْ قُلُوبَنَا بَعْدَ إِذْ هَدَيْتَنَا وَهَبْ لَنَا مِن لَّدُنكَ رَحْمَةً ۚ إِنَّكَ أَنتَ الْوَهَّابُ",
     "occasions": ["doubt", "seeking_guidance", "after_prayer"],
     "tags": ["steadfastness", "guidance", "heart"]},
]

# ── Pydantic schema ───────────────────────────────────────────────────────────

class DuaOut(BaseModel):
    id: str
    surah: int
    ayah: int
    ayahEnd: Optional[int] = None
    category: str
    prophet: Optional[str] = None
    titleEn: str
    titleAr: str
    surahNameEn: str
    surahNameAr: str
    meaningEn: str
    meaningAr: str
    occasions: list[str]
    tags: list[str]


class DuaListOut(BaseModel):
    count: int
    duas: list[DuaOut]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get('', response_model=DuaListOut, dependencies=[Depends(_rate_limit)])
async def list_duas(
    category: Optional[str] = Query(None, description="Filter by category slug"),
    prophet:  Optional[str] = Query(None, description="Filter by prophet name"),
    occasion: Optional[str] = Query(None, description="Filter by occasion slug"),
    q:        Optional[str] = Query(None, max_length=120, description="Full-text search (English + Arabic)"),
) -> DuaListOut:
    """Return the full Quranic Duʿā catalogue with optional server-side filtering."""
    results = _DUAS

    if category:
        cat = category.lower().strip()
        results = [d for d in results if d['category'] == cat]

    if prophet:
        proph = prophet.strip()
        results = [d for d in results if (d.get('prophet') or '').lower() == proph.lower()]

    if occasion:
        occ = occasion.lower().strip()
        results = [d for d in results if occ in d.get('occasions', [])]

    if q:
        needle = q.lower()
        results = [
            d for d in results
            if (needle in d['titleEn'].lower()
                or needle in d['titleAr']
                or needle in d['meaningEn'].lower()
                or needle in d['meaningAr']
                or any(needle in t for t in d.get('tags', []))
                or needle in d['surahNameEn'].lower()
                or needle in (d.get('prophet') or '').lower())
        ]

    return DuaListOut(count=len(results), duas=[DuaOut(**d) for d in results])
