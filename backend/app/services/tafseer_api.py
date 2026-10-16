"""
Tafseer client behind /api/v1/tafseer/{surah}/{ayah} and /tafseer/surah.

Every edition is answered from the app's own licensed library; nothing is
proxied from alquran.cloud any more (its edition catalogue is only used by the
health check):

- Arabic tafsir editions (ar.*) read tafseer_chunks of the matching
  tafseer_sources row, and only while that row is enabled AND
  licence-verified. A source whose licence is not verified (al-Muyassar, whose
  King Fahd Complex terms await owner confirmation) is refused like an
  unlisted edition.
- English editions read the QuranEnc translations table (LICENSED_DB_EDITIONS).

API Documentation (catalogue only): https://alquran.cloud/api
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
    EN_SAHIH = "en.sahih"                # Saheeh International (served from the licensed DB copy)
    EN_HILALI = "en.hilali"              # Hilali & Khan (served from the licensed DB copy)


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
        "name_ar": "ترجمة صحيح إنترناشيونال",
        "name_en": "Saheeh International (QuranEnc.com)",
        "author_ar": "صحيح إنترناشيونال — مركز نور الدولي",
        "author_en": "Saheeh International — Noor International Center",
    },
    "en.hilali": {
        "name_ar": "ترجمة الهلالي وخان",
        "name_en": "Hilali & Khan",
        "author_ar": "تقي الدين الهلالي ومحسن خان",
        "author_en": "Hilali & Muhsin Khan",
    },
}


# English translations are no longer fetched from alquran.cloud: its copies come
# from Tanzil, whose translation terms are non-commercial only. These two are
# answered from the QuranEnc editions in the translations table, which carry a
# republication grant (data/manifests/translation_sources.json). Any other
# English edition is refused rather than silently fetched.
LICENSED_DB_EDITIONS: Dict[str, str] = {
    "en.sahih": "english_saheeh",
    "en.hilali": "english_hilali_khan",
}


# Arabic tafsir editions -> their tafseer_sources id. Served from tafseer_chunks
# only while that source is enabled and licence-verified (_licensed_tafsir_ids),
# so the licence decision lives in one place: the database row, which follows
# data/manifests/tafseer_sources.json.
LICENSED_DB_TAFSIR: Dict[str, str] = {
    "ar.baghawi": "baghawi_ar",
    "ar.tabari": "tabari_ar",
    "ar.qurtubi": "qurtubi_ar",
    "ar.ibnkathir": "ibn_kathir_ar",
    # Licence pending owner confirmation: refused while license_verified=0.
    "ar.muyassar": "muyassar_ar",
}

# Default editions when a request names none: a cleared Arabic tafsir and the
# licensed English translation of the meanings.
DEFAULT_TAFSIR_EDITION = "ar.baghawi"
DEFAULT_EDITIONS: List[str] = [DEFAULT_TAFSIR_EDITION, "en.sahih"]

# Only editions whose provenance and terms are recorded can be served. alquran.cloud
# lists ~130 editions, many without an author, and at least one is mislabelled
# (its "ar.miqbas" returns Ibn Ashur's al-Tahrir wa al-Tanwir under the title of
# Tanwir al-Miqbas), so nothing outside this allowlist is considered, and an
# Arabic edition on it is still refused while its source is not licence-verified.
ALLOWED_EDITIONS: frozenset = frozenset(set(LICENSED_DB_TAFSIR) | set(LICENSED_DB_EDITIONS))


def is_allowed_edition(edition: str) -> bool:
    return edition in ALLOWED_EDITIONS


async def _licensed_tafsir_ids() -> frozenset:
    """tafseer_sources ids that are enabled and licence-verified right now."""
    from sqlalchemy import select
    from app.db.database import AsyncSessionLocal
    from app.models.tafseer import TafseerSource

    async with AsyncSessionLocal() as session:
        rows = await session.execute(
            select(TafseerSource.id).where(
                TafseerSource.id.in_(list(LICENSED_DB_TAFSIR.values())),
                TafseerSource.is_enabled == 1,
                TafseerSource.license_verified == 1,
            )
        )
        return frozenset(r[0] for r in rows)


async def servable_editions() -> List[str]:
    """Allowlisted editions this installation will actually serve now."""
    licensed = await _licensed_tafsir_ids()
    return sorted(
        e for e in ALLOWED_EDITIONS
        if e in LICENSED_DB_EDITIONS or LICENSED_DB_TAFSIR.get(e) in licensed
    )


async def _db_tafsir(surah: int, ayah: Optional[int], source_id: str) -> Optional[List[tuple]]:
    """(ayah, text) rows of one licensed tafsir source, or None when the source
    is not enabled and licence-verified (the edition must then be refused).
    A range passage is reported at its first ayah; upstream placeholders
    ("no tafsir for this verse") are never returned."""
    from sqlalchemy import select
    from app.db.database import AsyncSessionLocal
    from app.models.tafseer import TafseerChunk, TafseerSource
    from app.services.tafsir_sources import is_tafsir_placeholder

    async with AsyncSessionLocal() as session:
        servable = (
            await session.execute(
                select(TafseerSource.id).where(
                    TafseerSource.id == source_id,
                    TafseerSource.is_enabled == 1,
                    TafseerSource.license_verified == 1,
                )
            )
        ).scalar_one_or_none()
        if servable is None:
            return None
        query = (
            select(TafseerChunk.aya_start, TafseerChunk.content_ar, TafseerChunk.content_en)
            .where(TafseerChunk.source_id == source_id, TafseerChunk.sura_no == surah)
            .order_by(TafseerChunk.aya_start, TafseerChunk.chunk_order)
        )
        if ayah is not None:
            query = query.where(TafseerChunk.aya_start <= ayah, TafseerChunk.aya_end >= ayah)
        rows = (await session.execute(query)).all()
    out: List[tuple] = []
    for aya_start, content_ar, content_en in rows:
        text = (content_ar or content_en or "").strip()
        if is_tafsir_placeholder(text):
            continue
        out.append((ayah if ayah is not None else aya_start, text))
    return out


# TafseerResponse.error value when every requested edition was refused.
EDITION_NOT_LICENSED = "EDITION_NOT_LICENSED"


async def _db_translation(surah: int, ayah: Optional[int], key: str) -> List[tuple]:
    """(ayah, text, version) rows for one edition from the translations table."""
    from sqlalchemy import select
    from app.db.database import AsyncSessionLocal
    from app.models.quran import QuranVerse, Translation

    query = (
        select(QuranVerse.aya_no, Translation.text, Translation.edition_version)
        .join(Translation, Translation.verse_id == QuranVerse.id)
        .where(QuranVerse.sura_no == surah, Translation.translator == key)
        .order_by(QuranVerse.aya_no)
    )
    if ayah is not None:
        query = query.where(QuranVerse.aya_no == ayah)
    async with AsyncSessionLocal() as session:
        return list((await session.execute(query)).all())


class AlQuranCloudClient:
    """
    Tafseer and translation client.

    Verse and surah text comes from the licensed library only (tafseer_chunks
    of enabled, licence-verified sources; QuranEnc translations). The
    alquran.cloud API is called only for its edition catalogue and the health
    check, cached in the hybrid L1/L2 cache (in-memory + Redis).
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
            editions = DEFAULT_EDITIONS

        # Validate surah/ayah
        if not 1 <= surah <= 114:
            return TafseerResponse(
                surah=surah,
                ayah=ayah,
                success=False,
                error="Invalid surah number (must be 1-114)",
            )

        tafasir = []
        requested = [e.strip() for e in editions if e.strip()]
        refused: List[str] = []

        for edition in requested:
            if not is_allowed_edition(edition):
                logger.warning(f"Edition {edition} refused: not on the licensed allowlist")
                refused.append(edition)
                continue
            if edition in LICENSED_DB_EDITIONS:
                rows = await _db_translation(surah, ayah, LICENSED_DB_EDITIONS[edition])
                if rows:
                    _, text, version = rows[0]
                    tafasir.append(TafseerVerse(
                        surah=surah, ayah=ayah, text=text, edition=edition,
                        edition_name=f"{EDITION_METADATA[edition]['name_en']} v{version}",
                        language="en",
                    ))
                continue
            rows = await _db_tafsir(surah, ayah, LICENSED_DB_TAFSIR[edition])
            if rows is None:
                logger.info(f"Edition {edition} refused: its source is not licence-verified")
                refused.append(edition)
                continue
            for _, text in rows[:1]:
                tafasir.append(TafseerVerse(
                    surah=surah, ayah=ayah, text=text, edition=edition,
                    edition_name=EDITION_METADATA[edition]["name_ar"], language="ar",
                ))

        latency = int((time.perf_counter() - start) * 1000)

        return TafseerResponse(
            surah=surah,
            ayah=ayah,
            tafasir=tafasir,
            success=len(tafasir) > 0,
            error=None if tafasir else (
                EDITION_NOT_LICENSED if requested and len(refused) == len(requested)
                else "No tafseer found"
            ),
            latency_ms=latency,
        )

    async def get_surah_tafseer(
        self,
        surah: int,
        edition: str = DEFAULT_TAFSIR_EDITION,
    ) -> List[TafseerVerse]:
        """
        Get tafseer for an entire surah from the licensed library.

        Args:
            surah: Surah number (1-114)
            edition: Edition identifier

        Returns:
            List of TafseerVerse for the ayahs the source has a passage for;
            empty when the edition is not on the allowlist or its source is
            not licence-verified.
        """
        if not is_allowed_edition(edition):
            logger.warning(f"Edition {edition} refused: not on the licensed allowlist")
            return []
        if edition in LICENSED_DB_EDITIONS:
            name = EDITION_METADATA[edition]["name_en"]
            return [
                TafseerVerse(surah=surah, ayah=a, text=text, edition=edition,
                             edition_name=f"{name} v{version}", language="en")
                for a, text, version in await _db_translation(surah, None, LICENSED_DB_EDITIONS[edition])
            ]
        rows = await _db_tafsir(surah, None, LICENSED_DB_TAFSIR[edition])
        if rows is None:
            logger.info(f"Edition {edition} refused: its source is not licence-verified")
            return []
        name = EDITION_METADATA[edition]["name_ar"]
        return [
            TafseerVerse(surah=surah, ayah=a, text=text, edition=edition,
                         edition_name=name, language="ar")
            for a, text in rows
        ]

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
        response = await client.get_tafseer(2, 255, DEFAULT_EDITIONS)
        result["tafseer_test"] = {
            "success": response.success,
            "tafasir_count": len(response.tafasir),
            "latency_ms": response.latency_ms,
            "sample": response.tafasir[0].text[:200] if response.tafasir else None,
        }

    return result
