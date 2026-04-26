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

Running tests:
- pytest                       # Run all tests
- pytest tests/unit/           # Run only unit tests (fast)
- pytest tests/integration/    # Run integration tests
- pytest -m "unit"             # Run only unit-marked tests
- pytest -m "not slow"         # Skip slow tests
"""
import os
import pytest
from pathlib import Path


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


def pytest_collection_modifyitems(config, items):
    """Auto-mark tests based on their location."""
    for item in items:
        # Auto-mark tests in unit/ directory
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        # Auto-mark tests in integration/ directory
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)


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
