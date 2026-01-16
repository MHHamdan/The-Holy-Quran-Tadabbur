"""
AlQuran.Cloud API Client for Tafseer Integration.

Provides access to multiple Quranic translations and tafsir
from the free alquran.cloud API.

API Documentation: https://alquran.cloud/api

Features:
- Multiple tafsir editions (Ibn Kathir, Jalalayn, Al-Muyassar)
- Bilingual support (Arabic and English)
- Automatic caching with configurable TTL
- Graceful error handling with retries
"""
import time
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class TafseerLanguage(str, Enum):
    """Supported tafseer languages."""
    ARABIC = "ar"
    ENGLISH = "en"


class TafseerEdition(str, Enum):
    """Available tafseer editions from alquran.cloud."""
    # Arabic Tafsir
    AR_MUYASSAR = "ar.muyassar"          # التفسير الميسر
    AR_JALALAYN = "ar.jalalayn"          # تفسير الجلالين
    AR_BAGHAWY = "ar.baghawi"            # تفسير البغوي
    AR_QURTUBI = "ar.qurtubi"            # تفسير القرطبي
    AR_TABARI = "ar.tabari"              # تفسير الطبري
    AR_IBN_KATHIR = "ar.ibnkathir"       # تفسير ابن كثير

    # English Translations/Tafsir
    EN_SAHIH = "en.sahih"                # Sahih International
    EN_PICKTHALL = "en.pickthall"        # Pickthall
    EN_YUSUFALI = "en.yusufali"          # Yusuf Ali
    EN_HILALI = "en.hilali"              # Hilali & Khan
    EN_TRANSLITERATION = "en.transliteration"  # Transliteration


@dataclass
class TafseerEditionInfo:
    """Information about a tafseer edition."""
    identifier: str
    language: str
    name: str
    english_name: str
    format: str = "text"
    type: str = "tafsir"
    direction: str = "rtl"


@dataclass
class TafseerVerse:
    """Tafseer content for a single verse."""
    surah: int
    ayah: int
    text: str
    edition: str
    edition_name: str
    language: str


@dataclass
class TafseerResponse:
    """Response from tafseer API."""
    surah: int
    ayah: int
    tafasir: List[TafseerVerse] = field(default_factory=list)
    success: bool = True
    error: Optional[str] = None
    cached: bool = False
    latency_ms: int = 0


# Edition metadata for display
EDITION_METADATA: Dict[str, Dict[str, str]] = {
    "ar.muyassar": {
        "name_ar": "التفسير الميسر",
        "name_en": "Al-Muyassar (Simplified)",
        "author_ar": "مجمع الملك فهد",
        "author_en": "King Fahd Complex",
    },
    "ar.jalalayn": {
        "name_ar": "تفسير الجلالين",
        "name_en": "Tafsir Al-Jalalayn",
        "author_ar": "جلال الدين المحلي وجلال الدين السيوطي",
        "author_en": "Al-Mahalli & As-Suyuti",
    },
    "ar.ibnkathir": {
        "name_ar": "تفسير ابن كثير",
        "name_en": "Tafsir Ibn Kathir",
        "author_ar": "ابن كثير",
        "author_en": "Ibn Kathir",
    },
    "ar.qurtubi": {
        "name_ar": "تفسير القرطبي",
        "name_en": "Tafsir Al-Qurtubi",
        "author_ar": "القرطبي",
        "author_en": "Al-Qurtubi",
    },
    "ar.tabari": {
        "name_ar": "تفسير الطبري",
        "name_en": "Tafsir At-Tabari",
        "author_ar": "الطبري",
        "author_en": "At-Tabari",
    },
    "ar.baghawi": {
        "name_ar": "تفسير البغوي",
        "name_en": "Tafsir Al-Baghawi",
        "author_ar": "البغوي",
        "author_en": "Al-Baghawi",
    },
    "en.sahih": {
        "name_ar": "الترجمة الصحيحة",
        "name_en": "Sahih International",
        "author_ar": "صحيح انترناشيونال",
        "author_en": "Sahih International",
    },
    "en.pickthall": {
        "name_ar": "ترجمة بيكثال",
        "name_en": "Pickthall Translation",
        "author_ar": "محمد مارمادوك بيكثال",
        "author_en": "Muhammad M. Pickthall",
    },
    "en.yusufali": {
        "name_ar": "ترجمة يوسف علي",
        "name_en": "Yusuf Ali Translation",
        "author_ar": "عبد الله يوسف علي",
        "author_en": "Abdullah Yusuf Ali",
    },
    "en.hilali": {
        "name_ar": "ترجمة الهلالي وخان",
        "name_en": "Hilali & Khan",
        "author_ar": "تقي الدين الهلالي ومحسن خان",
        "author_en": "Hilali & Muhsin Khan",
    },
}


class AlQuranCloudClient:
    """
    Client for the alquran.cloud API.

    Provides access to Quranic tafsir and translations
    with hybrid L1/L2 caching (in-memory + Redis).
    """

    def __init__(
        self,
        base_url: str = None,
        timeout: float = None,
        cache_ttl: int = None,
        use_hybrid_cache: bool = True,
    ):
        self.base_url = base_url or settings.alquran_cloud_base_url
        self.timeout = timeout or settings.alquran_cloud_timeout
        self.cache_ttl = cache_ttl or settings.alquran_cloud_cache_ttl
        self.use_hybrid_cache = use_hybrid_cache

        # Hybrid cache (L1 in-memory + L2 Redis)
        self._hybrid_cache = None
        if use_hybrid_cache:
            try:
                from app.services.redis_cache import get_hybrid_cache
                self._hybrid_cache = get_hybrid_cache()
            except Exception as e:
                logger.warning(f"Failed to initialize hybrid cache: {e}")

        # Fallback simple in-memory cache
        self._cache: Dict[str, tuple] = {}

    def _get_cache_key(self, surah: int, ayah: int, edition: str) -> str:
        """Generate cache key."""
        return f"tafseer:{edition}:{surah}:{ayah}"

    async def _get_cached(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached value (hybrid cache first, then fallback)."""
        # Try hybrid cache first
        if self._hybrid_cache:
            try:
                value = await self._hybrid_cache.get(key)
                if value is not None:
                    return value
            except Exception as e:
                logger.debug(f"Hybrid cache get failed: {e}")

        # Fallback to simple cache
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self.cache_ttl:
                return value
            else:
                del self._cache[key]
        return None

    async def _set_cached(self, key: str, value: Dict[str, Any]):
        """Cache a value (to both hybrid and fallback)."""
        # Set in hybrid cache
        if self._hybrid_cache:
            try:
                await self._hybrid_cache.set(
                    key, value,
                    l1_ttl=300,  # 5 min L1
                    l2_ttl=self.cache_ttl,  # Configured TTL for L2
                )
            except Exception as e:
                logger.debug(f"Hybrid cache set failed: {e}")

        # Always set in fallback cache
        self._cache[key] = (value, time.time())

    async def get_editions(self) -> List[TafseerEditionInfo]:
        """
        Get list of available tafseer/translation editions.

        Returns:
            List of TafseerEditionInfo objects
        """
        cache_key = "tafseer:editions"
        cached = await self._get_cached(cache_key)
        if cached:
            return [TafseerEditionInfo(**e) for e in cached]

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/edition")
                response.raise_for_status()
                data = response.json()

            editions = []
            for ed in data.get("data", []):
                # Filter to tafsir and translation types
                if ed.get("type") in ["tafsir", "translation"]:
                    editions.append(TafseerEditionInfo(
                        identifier=ed.get("identifier"),
                        language=ed.get("language"),
                        name=ed.get("name"),
                        english_name=ed.get("englishName"),
                        format=ed.get("format", "text"),
                        type=ed.get("type"),
                        direction=ed.get("direction", "rtl"),
                    ))

            # Cache the result (editions rarely change, longer TTL)
            await self._set_cached(cache_key, [vars(e) for e in editions])
            return editions

        except Exception as e:
            logger.error(f"Failed to fetch editions: {e}")
            return []

    async def get_tafseer(
        self,
        surah: int,
        ayah: int,
        editions: List[str] = None,
    ) -> TafseerResponse:
        """
        Get tafseer/translation for a specific verse.

        Args:
            surah: Surah number (1-114)
            ayah: Ayah number
            editions: List of edition identifiers (default: from settings)

        Returns:
            TafseerResponse with content from all requested editions
        """
        start = time.perf_counter()

        if editions is None:
            editions = settings.tafseer_default_editions.split(",")

        # Validate surah/ayah
        if not 1 <= surah <= 114:
            return TafseerResponse(
                surah=surah,
                ayah=ayah,
                success=False,
                error="Invalid surah number (must be 1-114)",
            )

        tafasir = []

        for edition in editions:
            edition = edition.strip()
            cache_key = self._get_cache_key(surah, ayah, edition)

            # Check cache
            cached = await self._get_cached(cache_key)
            if cached:
                tafasir.append(TafseerVerse(**cached))
                continue

            # Fetch from API
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(
                        f"{self.base_url}/ayah/{surah}:{ayah}/{edition}"
                    )

                    if response.status_code == 404:
                        logger.warning(f"Verse {surah}:{ayah} not found for edition {edition}")
                        continue

                    response.raise_for_status()
                    data = response.json()

                ayah_data = data.get("data", {})
                edition_info = ayah_data.get("edition", {})

                verse = TafseerVerse(
                    surah=surah,
                    ayah=ayah,
                    text=ayah_data.get("text", ""),
                    edition=edition,
                    edition_name=edition_info.get("name", edition),
                    language=edition_info.get("language", "ar"),
                )

                # Cache the result
                await self._set_cached(cache_key, vars(verse))
                tafasir.append(verse)

            except httpx.TimeoutException:
                logger.error(f"Timeout fetching tafseer for {surah}:{ayah} edition {edition}")
            except Exception as e:
                logger.error(f"Error fetching tafseer: {e}")

        latency = int((time.perf_counter() - start) * 1000)

        return TafseerResponse(
            surah=surah,
            ayah=ayah,
            tafasir=tafasir,
            success=len(tafasir) > 0,
            error=None if tafasir else "No tafseer found",
            latency_ms=latency,
        )

    async def get_surah_tafseer(
        self,
        surah: int,
        edition: str = "ar.muyassar",
    ) -> List[TafseerVerse]:
        """
        Get tafseer for an entire surah.

        Args:
            surah: Surah number (1-114)
            edition: Edition identifier

        Returns:
            List of TafseerVerse for all ayahs in the surah
        """
        cache_key = f"tafseer:surah:{edition}:{surah}"
        cached = await self._get_cached(cache_key)
        if cached:
            return [TafseerVerse(**v) for v in cached]

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/surah/{surah}/{edition}"
                )
                response.raise_for_status()
                data = response.json()

            verses = []
            surah_data = data.get("data", {})
            edition_info = surah_data.get("edition", {})

            for ayah_data in surah_data.get("ayahs", []):
                verses.append(TafseerVerse(
                    surah=surah,
                    ayah=ayah_data.get("numberInSurah"),
                    text=ayah_data.get("text", ""),
                    edition=edition,
                    edition_name=edition_info.get("name", edition),
                    language=edition_info.get("language", "ar"),
                ))

            # Cache the result
            await self._set_cached(cache_key, [vars(v) for v in verses])
            return verses

        except Exception as e:
            logger.error(f"Failed to fetch surah tafseer: {e}")
            return []

    async def health_check(self) -> bool:
        """Check if the API is accessible."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/edition")
                return response.status_code == 200
        except Exception:
            return False

    def get_edition_metadata(self, edition: str) -> Dict[str, str]:
        """Get metadata for an edition."""
        return EDITION_METADATA.get(edition, {
            "name_ar": edition,
            "name_en": edition,
            "author_ar": "",
            "author_en": "",
        })


# Singleton instance
_client_instance: Optional[AlQuranCloudClient] = None


def get_tafseer_client() -> AlQuranCloudClient:
    """Get the tafseer API client instance."""
    global _client_instance
    if _client_instance is None:
        _client_instance = AlQuranCloudClient()
    return _client_instance


async def test_tafseer_api() -> Dict[str, Any]:
    """
    Test the tafseer API with a sample verse.

    Returns diagnostic information.
    """
    client = get_tafseer_client()

    result = {
        "api_available": await client.health_check(),
        "test_verse": "2:255",
        "editions_count": 0,
        "tafseer_test": None,
    }

    if result["api_available"]:
        editions = await client.get_editions()
        result["editions_count"] = len(editions)

        # Test fetching tafseer for Ayat al-Kursi
        response = await client.get_tafseer(2, 255, ["ar.muyassar", "en.sahih"])
        result["tafseer_test"] = {
            "success": response.success,
            "tafasir_count": len(response.tafasir),
            "latency_ms": response.latency_ms,
            "sample": response.tafasir[0].text[:200] if response.tafasir else None,
        }

    return result
