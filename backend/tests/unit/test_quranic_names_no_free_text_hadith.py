"""
QuranicNamesPage must not show free-text hadith.

The names data carried hadith wording with collection numbers that nobody had
verified (one, 'Sahih Bukhari 3350', was Qur'an 4:125). Those notes now sit in
data/manifests/review/quranic_names_hadith.json for scholar review and are not rendered.
A hadith may only come back as a structured, verified source, so the data file
and the page must not carry hadith fields at all.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
NAMES = ROOT / "frontend" / "src" / "data" / "quranicNames.ts"
PAGE = ROOT / "frontend" / "src" / "pages" / "QuranicNamesPage.tsx"
QUEUE = ROOT / "data" / "manifests" / "review" / "quranic_names_hadith.json"

_HADITH_FIELD = re.compile(r"\bhadith\w*\s*[?]?:", re.IGNORECASE)
_COLLECTION_NUMBER = re.compile(
    r"(Bukhari|Muslim|Tirmidhi|Abu Dawud|Nasa'?i|Ibn Majah|Ahmad|البخاري|مسلم|الترمذي|أبو داود|النسائي|ابن ماجه|أحمد)\s*\d+"
)


def test_names_data_has_no_hadith_fields():
    src = NAMES.read_text(encoding="utf-8")
    assert not _HADITH_FIELD.search(src)


def test_names_data_has_no_collection_numbers():
    src = NAMES.read_text(encoding="utf-8")
    assert not _COLLECTION_NUMBER.search(src), _COLLECTION_NUMBER.search(src).group(0)


def test_names_page_renders_no_hadith():
    src = PAGE.read_text(encoding="utf-8")
    assert "hadith" not in src.lower()


def test_removed_notes_are_queued_for_review_not_published():
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    assert queue["count"] == len(queue["entries"]) > 0
    statuses = {e["status"] for e in queue["entries"]}
    assert statuses <= {"needs_scholar_review", "rejected"}
    ibrahim = next(e for e in queue["entries"] if e["nameId"] == "ibrahim")
    # The 'Bukhari 3350' note quoted Qur'an 4:125; it must never be restored.
    assert ibrahim["status"] == "rejected"
    assert "hadithAr" not in ibrahim
