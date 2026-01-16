"""
Production-Grade Tafsir API Integration Service

Fetches tafsir text and audio from multiple external sources with:
- Multiple fallback sources (Quran.com API v4, quran-tafseer.com)
- Circuit breaker pattern for API resilience
- Intelligent caching with TTL
- LLM integration for summarization and explanations
- Comprehensive error handling

Sources:
- Primary: Quran.com API v4 (https://api.quran.com/api/v4)
- Secondary: quran-tafseer.com API
- Audio: read.tafsir.one

Following FANG best practices for reliability and performance.
"""

import httpx
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import asyncio
import logging
import re

logger = logging.getLogger(__name__)


# =============================================================================
# Circuit Breaker Pattern for API Resilience
# =============================================================================

@dataclass
class CircuitState:
    """Circuit breaker state tracking for API calls"""
    failures: int = 0
    last_failure: Optional[datetime] = None
    state: str = "closed"  # closed, open, half_open

    def record_failure(self):
        self.failures += 1
        self.last_failure = datetime.now()
        if self.failures >= 3:
            self.state = "open"
            logger.warning(f"Circuit breaker opened after {self.failures} failures")

    def record_success(self):
        self.failures = 0
        self.state = "closed"

    def should_attempt(self) -> bool:
        if self.state == "closed":
            return True
        if self.state == "open":
            # Check if cooldown period (30 seconds) has passed
            if self.last_failure and datetime.now() - self.last_failure > timedelta(seconds=30):
                self.state = "half_open"
                return True
            return False
        return True  # half_open


# =============================================================================
# In-Memory Cache with TTL
# =============================================================================

class TafsirCache:
    """High-performance cache for tafsir data with automatic expiration"""

    def __init__(self, ttl_seconds: int = 3600):
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
        self._ttl = timedelta(seconds=ttl_seconds)

    def _make_key(self, edition: str, sura: int, ayah: int) -> str:
        return f"tafsir:{edition}:{sura}:{ayah}"

    def get(self, edition: str, sura: int, ayah: int) -> Optional[Dict]:
        key = self._make_key(edition, sura, ayah)
        if key in self._cache:
            data, timestamp = self._cache[key]
            if datetime.now() - timestamp < self._ttl:
                logger.debug(f"Cache HIT: {key}")
                return data
            del self._cache[key]
        return None

    def set(self, edition: str, sura: int, ayah: int, data: Dict):
        key = self._make_key(edition, sura, ayah)
        self._cache[key] = (data, datetime.now())
        logger.debug(f"Cache SET: {key}")

    def clear_expired(self):
        now = datetime.now()
        expired = [k for k, (_, ts) in self._cache.items() if now - ts >= self._ttl]
        for k in expired:
            del self._cache[k]
        if expired:
            logger.info(f"Cleared {len(expired)} expired cache entries")


class TafsirSource(str, Enum):
    """External tafsir sources"""
    QURAN_COM = "quran_com"
    TAFSIR_ONE = "tafsir_one"
    SPA5K_CDN = "spa5k_cdn"


@dataclass
class TafsirEditionInfo:
    """Information about a tafsir edition"""
    id: str
    slug: str
    name_ar: str
    name_en: str
    author_ar: str
    author_en: str
    language: str
    source: TafsirSource
    has_audio: bool
    quran_com_id: Optional[int] = None  # ID for Quran.com API
    tafsir_one_slug: Optional[str] = None  # Slug for read.tafsir.one


# Available tafsir editions with metadata
TAFSIR_EDITIONS: Dict[str, TafsirEditionInfo] = {
    # Arabic Tafseers with Audio (from read.tafsir.one)
    "muyassar": TafsirEditionInfo(
        id="muyassar",
        slug="almuyassar",
        name_ar="التفسير الميسر",
        name_en="Al-Muyassar (Simplified)",
        author_ar="مجمع الملك فهد",
        author_en="King Fahd Complex",
        language="ar",
        source=TafsirSource.TAFSIR_ONE,
        has_audio=True,
        quran_com_id=16,
        tafsir_one_slug="almuyassar",
    ),
    "jalalayn": TafsirEditionInfo(
        id="jalalayn",
        slug="aljalalayn",
        name_ar="تفسير الجلالين",
        name_en="Tafsir Al-Jalalayn",
        author_ar="جلال الدين المحلي والسيوطي",
        author_en="Al-Mahalli & As-Suyuti",
        language="ar",
        source=TafsirSource.TAFSIR_ONE,
        has_audio=True,
        quran_com_id=None,
        tafsir_one_slug="aljalalayn",
    ),
    "saadi": TafsirEditionInfo(
        id="saadi",
        slug="alsaadi",
        name_ar="تفسير السعدي",
        name_en="Tafsir As-Saadi",
        author_ar="عبد الرحمن السعدي",
        author_en="Abdur-Rahman As-Saadi",
        language="ar",
        source=TafsirSource.TAFSIR_ONE,
        has_audio=True,
        quran_com_id=91,
        tafsir_one_slug="alsaadi",
    ),
    "ibn_juzayy": TafsirEditionInfo(
        id="ibn_juzayy",
        slug="ibn-juzay",
        name_ar="التسهيل لعلوم التنزيل",
        name_en="At-Tashil (Ibn Juzayy)",
        author_ar="ابن جزي الكلبي",
        author_en="Ibn Juzayy Al-Kalbi",
        language="ar",
        source=TafsirSource.TAFSIR_ONE,
        has_audio=True,
        quran_com_id=None,
        tafsir_one_slug="ibn-juzay",
    ),
    "ibn_ashoor": TafsirEditionInfo(
        id="ibn_ashoor",
        slug="ibn-ashoor",
        name_ar="التحرير والتنوير",
        name_en="At-Tahrir wat-Tanwir",
        author_ar="محمد الطاهر ابن عاشور",
        author_en="Ibn Ashoor",
        language="ar",
        source=TafsirSource.TAFSIR_ONE,
        has_audio=True,
        quran_com_id=None,
        tafsir_one_slug="ibn-ashoor",
    ),
    # Arabic Tafseers from Quran.com (text only)
    "ibn_kathir": TafsirEditionInfo(
        id="ibn_kathir",
        slug="ibn-kathir",
        name_ar="تفسير ابن كثير",
        name_en="Tafsir Ibn Kathir",
        author_ar="ابن كثير",
        author_en="Ibn Kathir",
        language="ar",
        source=TafsirSource.QURAN_COM,
        has_audio=False,
        quran_com_id=14,
    ),
    "tabari": TafsirEditionInfo(
        id="tabari",
        slug="tabari",
        name_ar="تفسير الطبري",
        name_en="Tafsir At-Tabari",
        author_ar="الإمام الطبري",
        author_en="Imam At-Tabari",
        language="ar",
        source=TafsirSource.QURAN_COM,
        has_audio=False,
        quran_com_id=15,
    ),
    "qurtubi": TafsirEditionInfo(
        id="qurtubi",
        slug="qurtubi",
        name_ar="الجامع لأحكام القرآن",
        name_en="Al-Jami li-Ahkam al-Quran",
        author_ar="الإمام القرطبي",
        author_en="Imam Al-Qurtubi",
        language="ar",
        source=TafsirSource.QURAN_COM,
        has_audio=False,
        quran_com_id=90,
    ),
    "baghawi": TafsirEditionInfo(
        id="baghawi",
        slug="baghawi",
        name_ar="معالم التنزيل",
        name_en="Ma'alim at-Tanzil",
        author_ar="الإمام البغوي",
        author_en="Imam Al-Baghawi",
        language="ar",
        source=TafsirSource.QURAN_COM,
        has_audio=False,
        quran_com_id=94,
    ),
    "wasit": TafsirEditionInfo(
        id="wasit",
        slug="wasit",
        name_ar="التفسير الوسيط",
        name_en="Al-Tafsir al-Wasit",
        author_ar="محمد سيد طنطاوي",
        author_en="Muhammad Sayyid Tantawi",
        language="ar",
        source=TafsirSource.QURAN_COM,
        has_audio=False,
        quran_com_id=93,
    ),
    # English Tafseers (from Quran.com API v4)
    "ibn_kathir_en": TafsirEditionInfo(
        id="ibn_kathir_en",
        slug="ibn-kathir-en",
        name_ar="تفسير ابن كثير (إنجليزي)",
        name_en="Tafsir Ibn Kathir (English)",
        author_ar="ابن كثير",
        author_en="Ibn Kathir",
        language="en",
        source=TafsirSource.QURAN_COM,
        has_audio=False,
        quran_com_id=169,
    ),
    "en_ibn_kathir": TafsirEditionInfo(
        id="en_ibn_kathir",
        slug="ibn-kathir-en",
        name_ar="تفسير ابن كثير (إنجليزي)",
        name_en="Ibn Kathir (English)",
        author_ar="ابن كثير",
        author_en="Ibn Kathir",
        language="en",
        source=TafsirSource.QURAN_COM,
        has_audio=False,
        quran_com_id=169,
    ),
    "en_maarif": TafsirEditionInfo(
        id="en_maarif",
        slug="maarif-al-quran",
        name_ar="معارف القرآن",
        name_en="Ma'arif al-Qur'an",
        author_ar="المفتي محمد شفيع",
        author_en="Mufti Muhammad Shafi",
        language="en",
        source=TafsirSource.QURAN_COM,
        has_audio=False,
        quran_com_id=168,
    ),
    "en_tazkirul": TafsirEditionInfo(
        id="en_tazkirul",
        slug="tazkirul-quran",
        name_ar="تذكير القرآن",
        name_en="Tazkirul Quran",
        author_ar="مولانا وحيد الدين خان",
        author_en="Maulana Wahiduddin Khan",
        language="en",
        source=TafsirSource.QURAN_COM,
        has_audio=False,
        quran_com_id=817,
    ),
}


class ExternalTafsirService:
    """
    Production-grade service for fetching tafsir from external APIs.

    Features:
    - Multiple fallback sources with automatic failover
    - Circuit breaker pattern for resilience
    - In-memory caching with TTL
    - Clean text processing
    """

    def __init__(self):
        self.quran_com_base = "https://api.quran.com/api/v4"
        self.quran_tafseer_base = "http://api.quran-tafseer.com"
        self.tafsir_one_base = "https://read.tafsir.one"
        self.timeout = 15.0

        # Circuit breakers for each source
        self._circuits: Dict[str, CircuitState] = {
            "quran_com": CircuitState(),
            "quran_tafseer": CircuitState(),
            "tafsir_one": CircuitState(),
        }

        # Cache with 1 hour TTL
        self._cache = TafsirCache(ttl_seconds=3600)

        # Reusable HTTP client
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={"User-Agent": "Tadabbur/1.0"}
            )
        return self._client

    def _clean_tafsir_text(self, text: str) -> str:
        """Clean HTML and format tafsir text for display"""
        if not text:
            return ""

        # Preserve semantic markers from Quran.com formatting
        # Convert <span class="blue"> to special markers for key terms
        text = re.sub(r'<span[^>]*class="blue"[^>]*>', '⟨', text)
        text = re.sub(r'<span[^>]*class="green"[^>]*>', '『', text)
        text = re.sub(r'</span>', '⟩', text)
        text = text.replace('⟩⟩', '⟩').replace('⟩『', '『')
        text = text.replace('』⟩', '』')

        # Remove remaining HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Clean up whitespace while preserving paragraph structure
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()

        return text

    def get_editions(self, language: Optional[str] = None, has_audio: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Get list of available tafsir editions with optional filtering"""
        editions = []
        for edition_id, info in TAFSIR_EDITIONS.items():
            if language and info.language != language:
                continue
            if has_audio is not None and info.has_audio != has_audio:
                continue
            editions.append({
                "id": info.id,
                "slug": info.slug,
                "name_ar": info.name_ar,
                "name_en": info.name_en,
                "author_ar": info.author_ar,
                "author_en": info.author_en,
                "language": info.language,
                "has_audio": info.has_audio,
                "source": info.source.value,
            })
        return editions

    def get_audio_url(self, edition_id: str, sura: int) -> Optional[str]:
        """
        Get audio URL for a tafsir edition and sura.
        Audio is available from read.tafsir.one for supported editions.
        """
        edition = TAFSIR_EDITIONS.get(edition_id)
        if not edition or not edition.has_audio or not edition.tafsir_one_slug:
            return None

        sura_padded = str(sura).zfill(3)
        return f"{self.tafsir_one_base}/audio/{edition.tafsir_one_slug}/{sura_padded}.mp3"

    async def fetch_from_quran_com(self, tafsir_id: int, sura: int, ayah: int) -> Optional[Dict[str, Any]]:
        """
        Fetch tafsir text from Quran.com API v4.
        Endpoint: /tafsirs/{tafsir_id}/by_ayah/{sura}:{ayah}
        """
        circuit = self._circuits["quran_com"]
        if not circuit.should_attempt():
            logger.debug("Circuit open for Quran.com, skipping")
            return None

        try:
            client = await self._get_client()
            # CORRECT endpoint format for Quran.com API v4
            url = f"{self.quran_com_base}/tafsirs/{tafsir_id}/by_ayah/{sura}:{ayah}"

            logger.debug(f"Fetching from Quran.com: {url}")
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            tafsir_data = data.get("tafsir", {})
            text = tafsir_data.get("text", "")

            if text:
                circuit.record_success()
                return {
                    "text": self._clean_tafsir_text(text),
                    "text_html": text,
                    "verse_key": f"{sura}:{ayah}",
                    "source": "quran_com",
                    "resource_name": tafsir_data.get("resource_name", ""),
                }

            logger.warning(f"Empty response from Quran.com for {sura}:{ayah}")
            return None

        except httpx.HTTPStatusError as e:
            logger.warning(f"Quran.com HTTP error {e.response.status_code}: {e}")
            circuit.record_failure()
            return None
        except Exception as e:
            logger.error(f"Quran.com API error: {e}")
            circuit.record_failure()
            return None

    async def fetch_from_quran_tafseer(self, tafsir_id: int, sura: int, ayah: int) -> Optional[Dict[str, Any]]:
        """
        Fetch tafsir text from quran-tafseer.com API (fallback source).
        Endpoint: /tafseer/{tafsir_id}/{sura}/{ayah}
        """
        circuit = self._circuits["quran_tafseer"]
        if not circuit.should_attempt():
            logger.debug("Circuit open for quran-tafseer.com, skipping")
            return None

        try:
            client = await self._get_client()
            url = f"{self.quran_tafseer_base}/tafseer/{tafsir_id}/{sura}/{ayah}"

            logger.debug(f"Fetching from quran-tafseer.com: {url}")
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            text = data.get("text", "")
            if text:
                circuit.record_success()
                return {
                    "text": self._clean_tafsir_text(text),
                    "text_html": text,
                    "verse_key": f"{sura}:{ayah}",
                    "source": "quran_tafseer",
                }

            return None

        except Exception as e:
            logger.warning(f"quran-tafseer.com API error: {e}")
            circuit.record_failure()
            return None

    async def fetch_from_tafsir_one(self, tafsir_slug: str, sura: int, ayah: int) -> Optional[Dict[str, Any]]:
        """Fetch tafsir text from read.tafsir.one"""
        circuit = self._circuits["tafsir_one"]
        if not circuit.should_attempt():
            logger.debug("Circuit open for tafsir.one, skipping")
            return None

        try:
            client = await self._get_client()
            url = f"{self.tafsir_one_base}/get.php"
            params = {
                "uth": "",
                "src": tafsir_slug,
                "s": str(sura),
                "a": str(ayah),
            }

            logger.debug(f"Fetching from tafsir.one: {url}")
            response = await client.get(url, params=params)
            response.raise_for_status()

            # Response might be plain text or JSON
            content_type = response.headers.get("content-type", "")
            if "json" in content_type:
                data = response.json()
                text = data.get("text", "") if isinstance(data, dict) else str(data)
            else:
                text = response.text

            if text and text.strip() and not text.startswith("<!DOCTYPE"):
                circuit.record_success()
                return {
                    "text": self._clean_tafsir_text(text),
                    "text_html": text,
                    "verse_key": f"{sura}:{ayah}",
                    "source": "tafsir_one",
                }

            return None

        except Exception as e:
            logger.warning(f"tafsir.one API error: {e}")
            circuit.record_failure()
            return None

    async def get_tafsir(self, edition_id: str, sura: int, ayah: int) -> Optional[Dict[str, Any]]:
        """
        Get tafsir text for a specific verse with automatic fallback.

        Tries sources in order of preference:
        1. Quran.com API v4 (most reliable, best formatting)
        2. quran-tafseer.com (fallback)
        3. read.tafsir.one (for editions with audio)
        """
        edition = TAFSIR_EDITIONS.get(edition_id)
        if not edition:
            logger.warning(f"Unknown tafsir edition: {edition_id}")
            return None

        # Check cache first
        cached = self._cache.get(edition_id, sura, ayah)
        if cached:
            return cached

        result = None

        # Tafsir ID mapping for quran-tafseer.com
        quran_tafseer_ids = {
            "muyassar": 1,
            "ibn_kathir": 2,
            "tabari": 3,
            "saadi": 4,
            "qurtubi": 5,
            "baghawi": 6,
            "wasit": 7,
            "jalalayn": 8,
        }

        # 1. Try Quran.com first if available (best source)
        if edition.quran_com_id:
            result = await self.fetch_from_quran_com(edition.quran_com_id, sura, ayah)

        # 2. Fallback to quran-tafseer.com
        if not result and edition_id in quran_tafseer_ids:
            result = await self.fetch_from_quran_tafseer(quran_tafseer_ids[edition_id], sura, ayah)

        # 3. Fallback to tafsir.one if available
        if not result and edition.tafsir_one_slug:
            result = await self.fetch_from_tafsir_one(edition.tafsir_one_slug, sura, ayah)

        if result:
            # Enrich with edition metadata
            result["edition"] = {
                "id": edition.id,
                "name_ar": edition.name_ar,
                "name_en": edition.name_en,
                "author_ar": edition.author_ar,
                "author_en": edition.author_en,
                "language": edition.language,
                "has_audio": edition.has_audio,
            }

            # Add audio URL if available
            if edition.has_audio:
                result["audio_url"] = self.get_audio_url(edition_id, sura)

            # Cache the result
            self._cache.set(edition_id, sura, ayah, result)

            return result

        logger.error(f"All sources failed for {edition_id}:{sura}:{ayah}")
        return None

    async def get_multiple_tafsirs(
        self,
        edition_ids: List[str],
        sura: int,
        ayah: int
    ) -> List[Dict[str, Any]]:
        """Get tafsir from multiple editions concurrently for comparison"""
        tasks = [self.get_tafsir(eid, sura, ayah) for eid in edition_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, dict)]

    async def get_sura_tafsir(
        self,
        edition_id: str,
        sura: int,
        start_ayah: int = 1,
        end_ayah: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get tafsir for a range of verses in a sura"""
        edition = TAFSIR_EDITIONS.get(edition_id)
        if not edition:
            return []

        # Default to reasonable range
        if end_ayah is None:
            end_ayah = start_ayah + 10

        # Fetch in batches of 5 for better performance
        results = []
        batch_size = 5
        for batch_start in range(start_ayah, end_ayah + 1, batch_size):
            batch_end = min(batch_start + batch_size, end_ayah + 1)
            tasks = [self.get_tafsir(edition_id, sura, ayah) for ayah in range(batch_start, batch_end)]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            results.extend([r for r in batch_results if isinstance(r, dict)])

        return results

    async def close(self):
        """Clean up resources"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# =============================================================================
# LLM Integration Service for Tafsir Enhancement
# =============================================================================

class TafsirLLMService:
    """
    LLM-powered tafsir enhancement service for:
    - Text summarization
    - Word/phrase explanations
    - Question answering about verses
    """

    def __init__(self, ollama_base: str = None):
        # For Docker: use OLLAMA_BASE_URL from environment
        import os
        default_ollama = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
        self.ollama_base = ollama_base or default_ollama
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5:32b")  # Use the model from docker-compose
        self.timeout = 60.0
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def _call_llm(self, prompt: str, system: str = "") -> Optional[str]:
        """Make LLM API call with error handling"""
        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.ollama_base}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "system": system,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "num_predict": 500,
                    }
                }
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return None

    async def summarize_tafsir(
        self,
        tafsir_text: str,
        verse_text: str,
        language: str = "ar"
    ) -> Optional[str]:
        """Generate a concise summary of tafsir text"""
        if language == "ar":
            system = """أنت عالم متخصص في تفسير القرآن الكريم. مهمتك تلخيص التفسير بشكل موجز ومفيد.
اكتب ملخصاً واضحاً في 2-3 جمل تشمل:
1. المعنى الرئيسي للآية
2. أهم الدروس المستفادة
لا تضف معلومات من خارج النص المعطى."""

            prompt = f"""الآية: {verse_text}

التفسير الكامل:
{tafsir_text[:2000]}

اكتب ملخصاً موجزاً:"""
        else:
            system = """You are a Quran tafsir expert. Summarize the tafsir concisely in 2-3 sentences covering:
1. Main meaning of the verse
2. Key lessons
Do not add information beyond what's provided."""

            prompt = f"""Verse: {verse_text}

Full Tafsir:
{tafsir_text[:2000]}

Write a concise summary:"""

        return await self._call_llm(prompt, system)

    async def explain_word(
        self,
        word: str,
        verse_text: str,
        context: str = "",
        language: str = "ar"
    ) -> Optional[str]:
        """Explain a specific word in the verse context"""
        if language == "ar":
            system = """أنت عالم متخصص في اللغة العربية وعلوم القرآن.
اشرح الكلمة المطلوبة بشكل واضح ومختصر.
اذكر: المعنى اللغوي، المعنى في السياق القرآني."""

            prompt = f"""الآية: {verse_text}

الكلمة المطلوب شرحها: {word}

{f'من التفسير: {context[:500]}' if context else ''}

اشرح هذه الكلمة في سياق الآية:"""
        else:
            system = """You are an Arabic language and Quranic sciences expert.
Explain the word clearly and concisely with linguistic and Quranic context meaning."""

            prompt = f"""Verse: {verse_text}

Word to explain: {word}

{f'From tafsir: {context[:500]}' if context else ''}

Explain this word in context:"""

        return await self._call_llm(prompt, system)

    async def answer_question(
        self,
        question: str,
        verse_text: str,
        tafsir_text: str,
        language: str = "ar"
    ) -> Optional[str]:
        """Answer a question about the verse based on tafsir"""
        if language == "ar":
            system = """أنت عالم متخصص في تفسير القرآن. أجب على السؤال بناءً على التفسير المعطى فقط.
إذا لم تجد الإجابة في التفسير، قل ذلك بوضوح.
كن موجزاً ودقيقاً."""

            prompt = f"""الآية: {verse_text}

التفسير:
{tafsir_text[:2000]}

السؤال: {question}

الإجابة:"""
        else:
            system = """You are a Quran tafsir expert. Answer based only on the provided tafsir.
If the answer isn't in the tafsir, say so clearly. Be concise and accurate."""

            prompt = f"""Verse: {verse_text}

Tafsir:
{tafsir_text[:2000]}

Question: {question}

Answer:"""

        return await self._call_llm(prompt, system)

    async def close(self):
        """Clean up resources"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# =============================================================================
# Singleton Instances
# =============================================================================

external_tafsir_service = ExternalTafsirService()
tafsir_llm_service = TafsirLLMService()
