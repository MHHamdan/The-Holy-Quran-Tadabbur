"""
Pytest configuration and fixtures for backend tests.

Test Structure:
- tests/unit/         Fast unit tests (no external deps, run in CI)
- tests/integration/  Integration tests (may need DB/Qdrant)

Markers:
- @pytest.mark.unit: Fast unit tests (no external dependencies)
- @pytest.mark.integration: Tests that may require database/services
- @pytest.mark.slow: Slow tests (e.g., LLM calls, vectorization)
- @pytest.mark.requires_stt: Tests that require STT model
- @pytest.mark.requires_audio: Tests that require audio fixtures
- @pytest.mark.live_hf: Calls real Hugging Face Inference Providers (spends credit)

Running tests:
- pytest                       # Run all tests
- pytest tests/unit/           # Run only unit tests (fast)
- pytest tests/integration/    # Run integration tests
- pytest -m "unit"             # Run only unit-marked tests
- pytest -m "not slow"         # Skip slow tests
- pytest -m "not live_hf"      # Normal/CI run — never calls Hugging Face
- pytest -m live_hf            # Live HF smoke tests (needs HF_TOKEN + credit)

Every test NOT marked live_hf runs with the HF token cleared, so a missing
mock can never turn into a paid upstream call; HF code paths take their
"not configured" fallbacks instead.
"""
import os
import pytest
from pathlib import Path
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


# =============================================================================
# Path Configuration
# =============================================================================

TESTS_DIR = Path(__file__).parent
FIXTURES_DIR = TESTS_DIR / "fixtures"
AUDIO_FIXTURES_DIR = FIXTURES_DIR / "audio"


# =============================================================================
# Environment Configuration
# =============================================================================

STT_MODEL_SIZE = os.environ.get("STT_MODEL_SIZE", "base")
STT_DEVICE = os.environ.get("STT_DEVICE", "cpu")
STT_COMPUTE_TYPE = os.environ.get("STT_COMPUTE_TYPE", "int8")


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "unit: Fast unit tests with no external dependencies"
    )
    config.addinivalue_line(
        "markers",
        "integration: Tests that may require database or external services"
    )
    config.addinivalue_line(
        "markers",
        "slow: Slow tests (LLM calls, large data processing)"
    )
    config.addinivalue_line(
        "markers",
        "requires_stt: Tests that require faster-whisper STT model"
    )
    config.addinivalue_line(
        "markers",
        "requires_audio: Tests that require audio fixtures from EveryAyah.com"
    )
    config.addinivalue_line(
        "markers",
        "live_hf: calls real Hugging Face Inference Providers; run only with "
        "`pytest -m live_hf` (or RUN_LIVE_HF=1)"
    )


def _live_hf_enabled(config) -> bool:
    markexpr = (config.option.markexpr or "").strip()
    return os.environ.get("RUN_LIVE_HF") == "1" or markexpr == "live_hf"


def pytest_collection_modifyitems(config, items):
    """Auto-mark tests based on their location; gate live HF tests."""
    live = _live_hf_enabled(config)
    skip_live = pytest.mark.skip(reason="live_hf: run with `pytest -m live_hf` (spends HF credit)")
    for item in items:
        if "live_hf" in item.keywords and not live:
            item.add_marker(skip_live)
        # Auto-mark tests in unit/ directory
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        # Auto-mark tests in integration/ directory
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)


# =============================================================================
# NullPool DB Engine — prevents asyncpg "Future attached to different loop" errors
# =============================================================================
# Using NullPool means every DB request gets a fresh connection (no pooling).
# This eliminates event-loop binding issues that occur when connections created
# in one module's event loop are reused in another module's loop, or when
# synchronous TestClient requests share a pool with async AsyncClient requests.
#
# Recommendation from SQLAlchemy docs for testing: use NullPool or StaticPool.

@pytest.fixture(scope="session", autouse=True)
def _patch_db_nullpool():
    """Replace the async engine with NullPool for test isolation."""
    try:
        from app.db import database
        from app.core.config import settings

        db_url_async = settings.database_url.replace(
            "postgresql://", "postgresql+asyncpg://"
        )
        test_engine = create_async_engine(db_url_async, poolclass=NullPool)
        test_session_factory = async_sessionmaker(
            bind=test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        original_engine = database.async_engine
        original_session = database.AsyncSessionLocal
        database.async_engine = test_engine
        database.AsyncSessionLocal = test_session_factory

        yield

        database.async_engine = original_engine
        database.AsyncSessionLocal = original_session
    except Exception:
        yield


@pytest.fixture(autouse=True)
def _no_live_hf(request, monkeypatch):
    """Clear the HF token for every test that is not explicitly live_hf."""
    if request.node.get_closest_marker("live_hf"):
        yield
        return
    from app.core.config import settings
    monkeypatch.setattr(settings, "hf_token", None)
    yield


@pytest.fixture(scope="module", autouse=True)
def _reset_rate_limiters():
    """Reset in-memory rate limiters before each test module.

    Rate limiters are module-level singletons. Without reset, accumulated
    request counts from earlier modules can exhaust the limit for later tests.
    """
    try:
        from app.core.rate_limit import (
            _rag_limiter, _search_limiter, _vocab_limiter,
            _admin_decision_limiter, _feedback_limiter, _therapy_limiter,
        )
        for lim in (_rag_limiter, _search_limiter, _vocab_limiter,
                    _admin_decision_limiter, _feedback_limiter, _therapy_limiter):
            lim.reset()
    except Exception:
        pass
    yield


# =============================================================================
# Audio Fixtures for Tasmeeʿ Tests
# =============================================================================

@pytest.fixture(scope="session")
def audio_fixtures_dir():
    """Return path to audio fixtures directory."""
    return AUDIO_FIXTURES_DIR


@pytest.fixture(scope="session")
def audio_fixtures_available():
    """Check if audio fixtures are downloaded."""
    return (AUDIO_FIXTURES_DIR / "001_001_bismillah.wav").exists()


@pytest.fixture(scope="session")
def stt_config():
    """Return STT configuration from environment."""
    return {
        "model_size": STT_MODEL_SIZE,
        "device": STT_DEVICE,
        "compute_type": STT_COMPUTE_TYPE,
    }
