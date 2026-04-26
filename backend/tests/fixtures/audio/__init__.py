"""
Audio fixtures for Tasmeeʿ integration tests.

To download fixtures, run:
    python download_fixtures.py

Source: EveryAyah.com (Free Quran verse-by-verse audio)
"""

from pathlib import Path

FIXTURES_DIR = Path(__file__).parent


def is_downloaded() -> bool:
    """Check if audio fixtures have been downloaded."""
    return (FIXTURES_DIR / "001_001_bismillah.wav").exists()


def get_fixture_path(filename: str) -> Path:
    """Get full path to a fixture file."""
    return FIXTURES_DIR / filename
