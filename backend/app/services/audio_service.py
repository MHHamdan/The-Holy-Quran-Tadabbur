"""
Quran Audio Service.

Provides audio URLs for Quran recitation from free public sources.
Supported reciters:
- Saud Al-Shuraim
- Maher Al-Muaiqly
- Mishary Al-Afasy
- Abdul Basit Abdul Samad
- Mahmoud Khalil Al-Husary
- Muhammad Siddiq Al-Minshawi

Audio sources (with fallback priority):
1. Primary: everyayah.com (per-verse audio, most reliable)
2. Fallback 1: cdn.islamic.network (alquran.cloud CDN)
3. Fallback 2: verses.quran.com (Quran.com CDN)

Arabic: خدمة صوت القرآن الكريم
"""

import logging
import httpx
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class Reciter(str, Enum):
    """Available reciters."""
    SAUD_SHURAIM = "saud_shuraim"
    MAHER_MUAIQLY = "maher_muaiqly"
    MISHARY_AFASY = "mishary_afasy"
    ABDUL_BASIT = "abdul_basit"
    HUSARY = "husary"
    MINSHAWI = "minshawi"


@dataclass
class ReciterInfo:
    """Information about a reciter."""
    id: str
    name_ar: str
    name_en: str
    style: str  # murattal, mujawwad
    # CDN subfolder for quranicaudio.com (surah-level)
    quranicaudio_folder: str
    # Subfolder for everyayah.com (verse-by-verse)
    everyayah_folder: str
    # alquran.cloud edition identifier
    alquran_cloud_id: str = ""
    # Quran.com recitation ID (for verses.quran.com)
    quran_com_id: int = 0


# Verse count per Surah (for calculating absolute ayah number)
SURAH_VERSE_COUNTS = [
    7, 286, 200, 176, 120, 165, 206, 75, 129, 109,  # 1-10
    123, 111, 43, 52, 99, 128, 111, 110, 98, 135,   # 11-20
    112, 78, 118, 64, 77, 227, 93, 88, 69, 60,      # 21-30
    34, 30, 73, 54, 45, 83, 182, 88, 75, 85,        # 31-40
    54, 53, 89, 59, 37, 35, 38, 29, 18, 45,         # 41-50
    60, 49, 62, 55, 78, 96, 29, 22, 24, 13,         # 51-60
    14, 11, 11, 18, 12, 12, 30, 52, 52, 44,         # 61-70
    28, 28, 20, 56, 40, 31, 50, 40, 46, 42,         # 71-80
    29, 19, 36, 25, 22, 17, 19, 26, 30, 20,         # 81-90
    15, 21, 11, 8, 8, 19, 5, 8, 8, 11,              # 91-100
    11, 8, 3, 9, 5, 4, 7, 3, 6, 3,                  # 101-110
    5, 4, 5, 6                                       # 111-114
]

# Pre-calculate cumulative verse counts for fast absolute ayah lookup
CUMULATIVE_VERSE_COUNTS = [0]
for count in SURAH_VERSE_COUNTS:
    CUMULATIVE_VERSE_COUNTS.append(CUMULATIVE_VERSE_COUNTS[-1] + count)


def get_absolute_ayah_number(sura_no: int, aya_no: int) -> int:
    """
    Convert sura:aya to absolute ayah number (1-6236).

    Example: 2:1 -> 8 (Al-Fatiha has 7 verses, so Al-Baqarah starts at 8)
    """
    if sura_no < 1 or sura_no > 114:
        return 0
    return CUMULATIVE_VERSE_COUNTS[sura_no - 1] + aya_no


# Reciter configurations with multiple source IDs
RECITERS: Dict[str, ReciterInfo] = {
    Reciter.SAUD_SHURAIM: ReciterInfo(
        id="saud_shuraim",
        name_ar="سعود الشريم",
        name_en="Saud Al-Shuraim",
        style="murattal",
        quranicaudio_folder="Saud_Ash-Shuraim_64kbps",
        everyayah_folder="Saood_ash-Shuraym_128kbps",
        alquran_cloud_id="ar.saudshuraim",
        quran_com_id=6,
    ),
    Reciter.MAHER_MUAIQLY: ReciterInfo(
        id="maher_muaiqly",
        name_ar="ماهر المعيقلي",
        name_en="Maher Al-Muaiqly",
        style="murattal",
        quranicaudio_folder="Maher_AlMuaiqly_64kbps",
        everyayah_folder="MaherAlMuaiqly128kbps",
        alquran_cloud_id="ar.mahermuaiqly",
        quran_com_id=7,
    ),
    Reciter.MISHARY_AFASY: ReciterInfo(
        id="mishary_afasy",
        name_ar="مشاري العفاسي",
        name_en="Mishary Al-Afasy",
        style="murattal",
        quranicaudio_folder="Alafasy_64kbps",
        everyayah_folder="Alafasy_128kbps",
        alquran_cloud_id="ar.alafasy",
        quran_com_id=7,
    ),
    Reciter.ABDUL_BASIT: ReciterInfo(
        id="abdul_basit",
        name_ar="عبد الباسط عبد الصمد",
        name_en="Abdul Basit Abdul Samad",
        style="mujawwad",
        quranicaudio_folder="Abdul_Basit_Mujawwad_128kbps",
        everyayah_folder="Abdul_Basit_Mujawwad_128kbps",
        alquran_cloud_id="ar.abdulbasitmurattal",
        quran_com_id=1,
    ),
    Reciter.HUSARY: ReciterInfo(
        id="husary",
        name_ar="محمود خليل الحصري",
        name_en="Mahmoud Khalil Al-Husary",
        style="murattal",
        quranicaudio_folder="Husary_64kbps",
        everyayah_folder="Husary_128kbps",
        alquran_cloud_id="ar.husary",
        quran_com_id=5,
    ),
    Reciter.MINSHAWI: ReciterInfo(
        id="minshawi",
        name_ar="محمد صديق المنشاوي",
        name_en="Muhammad Siddiq Al-Minshawi",
        style="mujawwad",
        quranicaudio_folder="Minshawy_Mujawwad_192kbps",
        everyayah_folder="Minshawy_Mujawwad_192kbps",
        alquran_cloud_id="ar.minshawi",
        quran_com_id=8,
    ),
}

# CDN base URLs (ordered by reliability)
EVERYAYAH_BASE = "https://everyayah.com/data"
ALQURAN_CLOUD_BASE = "https://cdn.islamic.network/quran/audio/128"
QURANICAUDIO_BASE = "https://download.quranicaudio.com/quran"


class QuranAudioService:
    """
    Service for getting Quran audio URLs with multi-fallback support.

    Priority order:
    1. everyayah.com (fastest, verse-level)
    2. cdn.islamic.network (alquran.cloud CDN)
    3. quranicaudio.com (surah-level fallback)

    Arabic: خدمة الحصول على روابط الصوت مع دعم البدائل المتعددة
    """

    def __init__(self):
        self._http_client: Optional[httpx.AsyncClient] = None
        # Cache for URL validation results: url -> (is_valid, timestamp)
        self._url_cache: Dict[str, Tuple[bool, float]] = {}
        self._cache_ttl = 3600  # 1 hour

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=10.0,
                follow_redirects=True,
            )
        return self._http_client

    async def validate_audio_url(self, url: str) -> bool:
        """
        Validate that an audio URL is accessible.

        Args:
            url: The URL to validate

        Returns:
            True if URL returns 200 status
        """
        import time

        # Check cache
        if url in self._url_cache:
            is_valid, timestamp = self._url_cache[url]
            if time.time() - timestamp < self._cache_ttl:
                return is_valid

        try:
            client = await self._get_client()
            response = await client.head(url)
            is_valid = response.status_code == 200
            self._url_cache[url] = (is_valid, time.time())
            return is_valid
        except Exception as e:
            logger.warning(f"URL validation failed for {url}: {e}")
            self._url_cache[url] = (False, time.time())
            return False

    def get_reciters(self) -> List[Dict]:
        """Get list of available reciters."""
        return [
            {
                "id": info.id,
                "name_ar": info.name_ar,
                "name_en": info.name_en,
                "style": info.style,
            }
            for info in RECITERS.values()
        ]

    def get_surah_audio_url(
        self,
        sura_no: int,
        reciter: str = "mishary_afasy",
    ) -> Optional[str]:
        """
        Get audio URL for a complete Surah.

        Args:
            sura_no: Surah number (1-114)
            reciter: Reciter ID

        Returns:
            Audio URL or None if not found
        """
        if sura_no < 1 or sura_no > 114:
            return None

        reciter_info = RECITERS.get(reciter)
        if not reciter_info:
            reciter_info = RECITERS[Reciter.MISHARY_AFASY]

        # Format: 001.mp3, 002.mp3, etc.
        sura_str = str(sura_no).zfill(3)
        return f"{QURANICAUDIO_BASE}/{reciter_info.quranicaudio_folder}/{sura_str}.mp3"

    def get_verse_audio_url(
        self,
        sura_no: int,
        aya_no: int,
        reciter: str = "mishary_afasy",
    ) -> Optional[str]:
        """
        Get audio URL for a single verse (primary source).

        Args:
            sura_no: Surah number (1-114)
            aya_no: Verse number
            reciter: Reciter ID

        Returns:
            Audio URL or None if not found
        """
        if sura_no < 1 or sura_no > 114:
            return None

        reciter_info = RECITERS.get(reciter)
        if not reciter_info:
            reciter_info = RECITERS[Reciter.MISHARY_AFASY]

        # Format: 001001.mp3 (sura 1, aya 1)
        sura_str = str(sura_no).zfill(3)
        aya_str = str(aya_no).zfill(3)
        return f"{EVERYAYAH_BASE}/{reciter_info.everyayah_folder}/{sura_str}{aya_str}.mp3"

    def get_verse_audio_urls_with_fallback(
        self,
        sura_no: int,
        aya_no: int,
        reciter: str = "mishary_afasy",
    ) -> Dict[str, str]:
        """
        Get multiple audio URLs for a verse with fallback options.

        Returns all available URLs so the frontend can try them in order.

        Args:
            sura_no: Surah number (1-114)
            aya_no: Verse number
            reciter: Reciter ID

        Returns:
            Dict with primary and multiple fallback URLs
        """
        if sura_no < 1 or sura_no > 114:
            return {}

        reciter_info = RECITERS.get(reciter)
        if not reciter_info:
            reciter_info = RECITERS[Reciter.MISHARY_AFASY]

        sura_str = str(sura_no).zfill(3)
        aya_str = str(aya_no).zfill(3)

        # Primary: everyayah.com
        urls = {
            "primary": f"{EVERYAYAH_BASE}/{reciter_info.everyayah_folder}/{sura_str}{aya_str}.mp3",
        }

        # Fallback 1: alquran.cloud CDN (uses absolute ayah number)
        if reciter_info.alquran_cloud_id:
            absolute_ayah = get_absolute_ayah_number(sura_no, aya_no)
            urls["fallback1"] = f"{ALQURAN_CLOUD_BASE}/{reciter_info.alquran_cloud_id}/{absolute_ayah}.mp3"

        # Fallback 2: Alternative everyayah folder (Mishary Afasy as universal fallback)
        if reciter != "mishary_afasy":
            urls["fallback2"] = f"{EVERYAYAH_BASE}/Alafasy_128kbps/{sura_str}{aya_str}.mp3"

        return urls

    def get_all_fallback_urls(
        self,
        sura_no: int,
        aya_no: int,
        reciter: str = "mishary_afasy",
    ) -> List[str]:
        """
        Get ordered list of all audio URLs to try for maximum reliability.

        Args:
            sura_no: Surah number (1-114)
            aya_no: Verse number
            reciter: Reciter ID

        Returns:
            List of URLs in priority order
        """
        urls = []

        if sura_no < 1 or sura_no > 114:
            return urls

        reciter_info = RECITERS.get(reciter)
        if not reciter_info:
            reciter_info = RECITERS[Reciter.MISHARY_AFASY]

        sura_str = str(sura_no).zfill(3)
        aya_str = str(aya_no).zfill(3)
        absolute_ayah = get_absolute_ayah_number(sura_no, aya_no)

        # 1. Primary: everyayah.com with requested reciter
        urls.append(f"{EVERYAYAH_BASE}/{reciter_info.everyayah_folder}/{sura_str}{aya_str}.mp3")

        # 2. alquran.cloud CDN
        if reciter_info.alquran_cloud_id:
            urls.append(f"{ALQURAN_CLOUD_BASE}/{reciter_info.alquran_cloud_id}/{absolute_ayah}.mp3")

        # 3. Mishary Afasy fallback (most reliable)
        if reciter != "mishary_afasy":
            urls.append(f"{EVERYAYAH_BASE}/Alafasy_128kbps/{sura_str}{aya_str}.mp3")
            urls.append(f"{ALQURAN_CLOUD_BASE}/ar.alafasy/{absolute_ayah}.mp3")

        # 4. Husary fallback (widely available)
        if reciter != "husary":
            urls.append(f"{EVERYAYAH_BASE}/Husary_128kbps/{sura_str}{aya_str}.mp3")

        return urls

    async def get_first_working_url(
        self,
        sura_no: int,
        aya_no: int,
        reciter: str = "mishary_afasy",
    ) -> Optional[str]:
        """
        Get the first working audio URL by testing each fallback.

        Args:
            sura_no: Surah number (1-114)
            aya_no: Verse number
            reciter: Reciter ID

        Returns:
            First working URL or None if all fail
        """
        urls = self.get_all_fallback_urls(sura_no, aya_no, reciter)

        for url in urls:
            if await self.validate_audio_url(url):
                return url

        logger.error(f"All audio URLs failed for {sura_no}:{aya_no}")
        return None

    def get_verse_range_audio_urls(
        self,
        sura_no: int,
        aya_start: int,
        aya_end: int,
        reciter: str = "mishary_afasy",
    ) -> List[Dict]:
        """
        Get audio URLs for a range of verses.

        Args:
            sura_no: Surah number (1-114)
            aya_start: Starting verse
            aya_end: Ending verse
            reciter: Reciter ID

        Returns:
            List of verse audio info with all fallback URLs
        """
        verses = []
        for aya_no in range(aya_start, aya_end + 1):
            urls = self.get_verse_audio_urls_with_fallback(sura_no, aya_no, reciter)
            if urls:
                verses.append({
                    "sura_no": sura_no,
                    "aya_no": aya_no,
                    "reference": f"{sura_no}:{aya_no}",
                    "url": urls.get("primary"),
                    "fallback_urls": [urls.get("fallback1"), urls.get("fallback2")],
                })
        return verses

    def get_page_audio_info(
        self,
        page_no: int,
        reciter: str = "mishary_afasy",
        verses: List[Dict] = None,
    ) -> Dict:
        """
        Get audio info for a Mushaf page.

        Since pages span multiple suras sometimes, this returns
        info needed to play all verses on a page.

        Args:
            page_no: Mushaf page number (1-604)
            reciter: Reciter ID
            verses: Optional list of verses on the page

        Returns:
            Audio info including URLs for each verse with fallbacks
        """
        if not verses:
            return {
                "page_no": page_no,
                "reciter": reciter,
                "verse_audios": [],
            }

        verse_audios = []
        for v in verses:
            sura_no = v.get("sura_no")
            aya_no = v.get("aya_no")
            urls = self.get_verse_audio_urls_with_fallback(sura_no, aya_no, reciter)

            if urls:
                verse_audios.append({
                    "sura_no": sura_no,
                    "aya_no": aya_no,
                    "reference": f"{sura_no}:{aya_no}",
                    "url": urls.get("primary"),
                    "fallback_urls": [
                        u for u in [urls.get("fallback1"), urls.get("fallback2")]
                        if u
                    ],
                })

        return {
            "page_no": page_no,
            "reciter": reciter,
            "verse_audios": verse_audios,
            "total_verses": len(verse_audios),
        }


# Singleton instance
_audio_service: Optional[QuranAudioService] = None


def get_audio_service() -> QuranAudioService:
    """Get audio service singleton."""
    global _audio_service
    if _audio_service is None:
        _audio_service = QuranAudioService()
    return _audio_service
