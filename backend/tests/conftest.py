"""
Pytest configuration and fixtures for backend tests.

Test Structure:
- tests/unit/         Fast unit tests (no external deps, run in CI)
- tests/integration/  Integration tests (may need DB/Qdrant)

Markers:
- @pytest.mark.unit: Fast unit tests (no external dependencies)
- @pytest.mark.integration: Tests that may require database/services
- @pytest.mark.slow: Slow tests (e.g., LLM calls, vectorization)

Running tests:
- pytest                       # Run all tests
- pytest tests/unit/           # Run only unit tests (fast)
- pytest tests/integration/    # Run integration tests
- pytest -m "unit"             # Run only unit-marked tests
- pytest -m "not slow"         # Skip slow tests
"""
import pytest


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


def pytest_collection_modifyitems(config, items):
    """Auto-mark tests based on their location."""
    for item in items:
        # Auto-mark tests in unit/ directory
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        # Auto-mark tests in integration/ directory
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
