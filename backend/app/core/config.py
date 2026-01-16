"""
Application configuration with Pydantic Settings.
"""
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
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
    database_url: str = "postgresql://tadabbur:tadabbur_dev@localhost:5432/tadabbur"

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_tafseer: str = "tafseer_chunks"
    qdrant_collection_verses: str = "quran_verses"

    # Redis Cache Configuration
    redis_url: str = "redis://localhost:6379/0"
    redis_key_prefix: str = "tadabbur:"  # Namespace prefix for all keys
    redis_max_connections: int = 10  # Connection pool size
    redis_socket_timeout: float = 5.0  # Socket timeout in seconds
    redis_default_ttl: int = 3600  # Default TTL for cached items (1 hour)
    redis_l1_max_size: int = 10000  # Max items in L1 in-memory cache
    redis_l1_ttl: int = 300  # L1 cache TTL (5 minutes)

    # SurrealDB Knowledge Graph
    surreal_host: str = "localhost"
    surreal_port: int = 8000
    surreal_user: str = "root"
    surreal_pass: str = "root"
    surreal_namespace: str = "tadabbur"
    surreal_database: str = "quran_kg"

    # Anthropic
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-sonnet-4-20250514"

    # LLM Provider Selection
    # Options: "ollama" (local, cost-free) or "claude" (API, paid)
    llm_provider: str = "ollama"

    # Ollama Configuration (for local LLM inference)
    ollama_model: str = "qwen2.5:32b"
    ollama_model_fast: str = "qwen2.5:14b"  # Faster model for RAG (half the size, 2x faster)
    ollama_base_url: str = "http://localhost:11434"
    ollama_rag_max_tokens: int = 1500  # Lower token limit for faster RAG responses
    ollama_rag_use_fast_model: bool = True  # Use fast model for RAG by default

    # Embedding Model
    embedding_model_multilingual: str = "intfloat/multilingual-e5-large"
    embedding_dimension: int = 1024

    # RAG Configuration
    rag_top_k: int = 10
    rag_min_confidence: float = 0.5
    rag_citation_required: bool = True

    # Safety
    max_query_length: int = 1000
    rate_limit_per_minute: int = 30

    # Admin
    admin_token: Optional[str] = None  # Set via ADMIN_TOKEN env var

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


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
