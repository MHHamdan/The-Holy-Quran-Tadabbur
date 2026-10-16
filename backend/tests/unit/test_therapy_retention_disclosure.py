"""
The retention periods stated to users match the code.

/privacy (PrivacyPage.tsx) and the store draft (docs/store/data-safety.md)
quote each server-side retention limit; when a constant changes, both must
change with it.
"""
from pathlib import Path

import pytest

from app.api.routes import adhkar, tasmee, therapy
from app.services import search_history

ROOT = Path(__file__).resolve().parents[3]
PRIVACY_PAGE = ROOT / "frontend" / "src" / "pages" / "PrivacyPage.tsx"
DATA_SAFETY = ROOT / "docs" / "store" / "data-safety.md"
DHIKR_PAGE = ROOT / "frontend" / "src" / "pages" / "DhikrPage.tsx"

AR_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")

pytestmark = pytest.mark.skipif(not PRIVACY_PAGE.exists(), reason="frontend not present")


@pytest.mark.parametrize("days, en_phrase", [
    (therapy.THERAPY_RETENTION_DAYS, "for up to {d} days"),
    (tasmee.TASMEE_RETENTION_DAYS, "for up to {d} days"),
    (search_history.SEARCH_HISTORY_TTL_DAYS, "after {d} days"),
    (adhkar.DHIKR_RETENTION_DAYS, "deleted after {d} days"),
])
def test_privacy_page_states_each_retention_limit(days, en_phrase):
    page = PRIVACY_PAGE.read_text(encoding="utf-8")
    assert en_phrase.format(d=days) in page
    assert str(days).translate(AR_DIGITS) in page  # the Arabic text says the same


@pytest.mark.parametrize("days, constant", [
    (therapy.THERAPY_RETENTION_DAYS, "THERAPY_RETENTION_DAYS"),
    (tasmee.TASMEE_RETENTION_DAYS, "TASMEE_RETENTION_DAYS"),
    (search_history.SEARCH_HISTORY_TTL_DAYS, "SEARCH_HISTORY_TTL_DAYS"),
    (adhkar.DHIKR_RETENTION_DAYS, "DHIKR_RETENTION_DAYS"),
])
def test_store_draft_states_each_retention_limit(days, constant):
    doc = DATA_SAFETY.read_text(encoding="utf-8")
    row = next(line for line in doc.splitlines() if constant in line)
    assert f"{days} days" in row


def test_dhikr_page_sends_nothing_to_the_server():
    page = DHIKR_PAGE.read_text(encoding="utf-8")
    assert "/dhikr/sessions" not in page
    assert "fetch(" not in page
