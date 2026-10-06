"""
Application configuration with Pydantic Settings.
"""
from functools import lru_cache
from typing import Optional
from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Tadabbur-AI"
    # API Version follows Semantic Versioning (semver.org):
    # - MAJOR: Breaking changes (response shape changes, removed fields)
    # - MINOR: New features (new fields, new endpoints) - backwards compatible
    # - PATCH: Bug fixes, performance improvements - no API changes
    # Frontend should warn if MAJOR version differs from expected
    api_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True

    # Database
    database_url: str = "postgresql://tadabbur:tadabbur_dev@localhost:19432/tadabbur"

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 19633
    qdrant_collection_tafseer: str = "tafseer_chunks"
    qdrant_collection_verses: str = "quran_verses"

    # Redis Cache Configuration
    redis_url: str = "redis://localhost:19379/0"
    redis_key_prefix: str = "tadabbur:"  # Namespace prefix for all keys
    redis_max_connections: int = 10  # Connection pool size
    redis_socket_timeout: float = 5.0  # Socket timeout in seconds
    redis_default_ttl: int = 3600  # Default TTL for cached items (1 hour)
    redis_l1_max_size: int = 10000  # Max items in L1 in-memory cache
    redis_l1_ttl: int = 300  # L1 cache TTL (5 minutes)

    # SurrealDB Knowledge Graph
    surreal_host: str = "localhost"
    surreal_port: int = 8529  # Docker maps 8529:8000
    surreal_user: str = "root"
    surreal_pass: str = "root"
    surreal_namespace: str = "tadabbur"
    surreal_database: str = "quran_kg"

    # ------------------------------------------------------------------
    # Hugging Face — the ONLY AI/model platform (server side only)
    # ------------------------------------------------------------------
    # HF_TOKEN is the documented variable; HUGGINGFACE_TOKEN is accepted for
    # compatibility. It is never logged, returned by an endpoint, or exposed
    # to the frontend (no VITE_* variable may carry it).
    hf_token: Optional[SecretStr] = Field(
        default=None,
        validation_alias=AliasChoices("HF_TOKEN", "HUGGINGFACE_TOKEN"),
    )
    # OpenAI-compatible router used for chat completion.
    hf_router_url: str = "https://router.huggingface.co/v1"
    # Chat model for RAG synthesis, grammar, quiz, verification assistant.
    # Chosen by scripts/bench/bench_hf_llm.py — see docs/migration/HF_MODEL_SELECTION.md.
    hf_llm_model: str = "meta-llama/Llama-3.3-70B-Instruct"
    # Provider routing: "auto" (router default), a provider name
    # (e.g. "novita", "together"), or a policy ("cheapest", "fastest").
    hf_llm_provider: str = "auto"
    hf_llm_max_tokens: int = 1500
    hf_timeout_seconds: float = 60.0
    # Embeddings must match the vectors already stored in Qdrant
    # (multilingual-e5-large, 1024-d).
    hf_embedding_model: str = "intfloat/multilingual-e5-large"
    hf_reranker_model: str = "BAAI/bge-reranker-v2-m3"
    hf_stt_model: str = "openai/whisper-large-v3-turbo"
    hf_zero_shot_model: str = "facebook/bart-large-mnli"

    # Embedding dimension of hf_embedding_model (Qdrant collection size)
    embedding_dimension: int = 1024

    # RAG Configuration
    rag_top_k: int = 10
    rag_min_confidence: float = 0.5
    rag_citation_required: bool = True

    # Safety
    max_query_length: int = 1000
    rate_limit_per_minute: int = 30

    # Admin
    admin_token: Optional[str] = None   # Set via ADMIN_TOKEN env var (Bearer auth, auth.py)
    admin_api_key: Optional[str] = None  # Set via ADMIN_API_KEY env var (X-Admin-API-Key, admin_auth.py)

    # NLP Provider Configuration
    # Primary NLP provider for grammar analysis: farasa, camel, stanza, llm
    nlp_primary_provider: str = "farasa"
    nlp_enable_farasa: bool = True
    nlp_enable_camel: bool = True
    nlp_enable_stanza: bool = True
    nlp_enable_llm: bool = True
    nlp_farasa_use_api: bool = False  # Use local farasapy library by default
    nlp_farasa_api_url: str = "https://farasa.qcri.org/webapi"
    nlp_min_confidence: float = 0.6  # Minimum confidence to accept NLP result
    nlp_cache_ttl: int = 86400  # 24 hours cache for NLP results

    # Tafseer API Configuration
    alquran_cloud_base_url: str = "https://api.alquran.cloud/v1"
    alquran_cloud_timeout: float = 30.0
    alquran_cloud_cache_ttl: int = 86400  # 24 hours
    # Default tafseer editions (bilingual focus)
    tafseer_default_editions: str = "ar.muyassar,en.sahih"

    # Cache Warming Configuration
    cache_warm_on_startup: bool = False  # Auto-warm cache on startup
    cache_warm_interval: int = 3600  # Re-warm interval in seconds (1 hour)

    # Feature Flags
    feature_nlp_chain: bool = True  # Use multi-provider NLP chain
    feature_external_tafseer: bool = True  # Use alquran.cloud API
    feature_redis_cache: bool = True  # Use Redis (fallback to in-memory)
    feature_ai_verification: bool = True  # Enable AI verification assistant
    feature_cache_warming: bool = True  # Enable cache warming service

    # Emotion Classifier — Phase T4
    # Zero-shot NLI emotion classification (English) via HF (hf_zero_shot_model).
    # Set emotion_classifier_enabled=false to force keyword-only mode.
    emotion_classifier_enabled: bool = True
    # Minimum entailment probability to accept the NLI prediction.
    # Below this threshold the keyword classifier is used as fallback.
    emotion_confidence_threshold: float = 0.40

    @property
    def hf_llm_model_id(self) -> str:
        """Model id with the provider-routing suffix the HF router expects."""
        provider = (self.hf_llm_provider or "auto").strip()
        if provider == "auto" or ":" in self.hf_llm_model:
            return self.hf_llm_model
        return f"{self.hf_llm_model}:{provider}"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
