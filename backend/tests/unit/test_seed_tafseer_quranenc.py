"""
QuranEnc tafsir seeder: verbatim text, licence state from the manifest, flag.

The DB check writes inside a transaction that is rolled back, so the shared
database is not changed. It needs the cached download
(data/raw/tafsir/quranenc/english_mokhtasar.json, part of the data bundle) and
skips without it.
"""
import json
import sys
from pathlib import Path

import pytest
from sqlalchemy import text

BACKEND = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND / "scripts" / "ingest"))

import seed_tafsir_quranenc as seeder  # noqa: E402
from seed_tafseer import load_licence_state  # noqa: E402

CACHE = seeder.CACHE_DIR / "english_mokhtasar.json"


def test_quranenc_sources_are_pending_in_the_manifest():
    for key in ("english_mokhtasar", "arabic_mokhtasar"):
        state = load_licence_state(seeder.SOURCES[key]["id"])
        assert not state["verified"] and not state["enabled"], key


def test_stored_text_is_verbatim_with_footnotes_after():
    v = {"text": "255. Allah ...", "footnotes": None}
    assert seeder.stored_text(v) == "255. Allah ..."
    v = {"text": "1. Text", "footnotes": "[1] note"}
    assert seeder.stored_text(v) == "1. Text\n\n[1] note"


def test_verify_rejects_incomplete_downloads():
    data = {"key": "x", "verses": [{"sura": 1, "aya": 1, "text": "a", "footnotes": None}]}
    with pytest.raises(ValueError):
        seeder.verify(data)


def test_mukhtasar_en_is_behind_a_flag(monkeypatch):
    from app.services import tafsir_comparison as tc

    assert tc.FLAGGED_SOURCES["mukhtasar_en"] == "FEATURE_MUKHTASAR_EN"
    monkeypatch.delenv("FEATURE_MUKHTASAR_EN", raising=False)
    assert not tc._flag_on("FEATURE_MUKHTASAR_EN")
    monkeypatch.setenv("FEATURE_MUKHTASAR_EN", "1")
    assert tc._flag_on("FEATURE_MUKHTASAR_EN")


@pytest.mark.skipif(not CACHE.exists(), reason="QuranEnc cache not present (data bundle)")
def test_write_covers_every_ayah_disabled_and_rolls_back():
    from app.db.database import SyncSessionLocal

    data = json.loads(CACHE.read_text(encoding="utf-8"))
    seeder.verify(data)
    with SyncSessionLocal() as db:
        try:
            if db.execute(text("SELECT 1 FROM tafseer_chunks WHERE source_id='mukhtasar_en' LIMIT 1")).first():
                pytest.skip("mukhtasar_en already seeded in this database")
            seeder.write(db, "english_mokhtasar", data, replace=False)
            n, distinct = db.execute(text(
                "SELECT count(*), count(DISTINCT (sura_no, aya_start)) FROM tafseer_chunks WHERE source_id='mukhtasar_en'"
            )).one()
            assert n == distinct == 6236
            row = db.execute(text(
                "SELECT license_verified, is_enabled, translator, source_url FROM tafseer_sources WHERE id='mukhtasar_en'"
            )).one()
            assert row[0] == 0 and row[1] == 0 and row[2] and row[3] == "https://quranenc.com"
            stored = db.execute(text(
                "SELECT content_en FROM tafseer_chunks WHERE source_id='mukhtasar_en' AND sura_no=2 AND aya_start=255"
            )).scalar()
            cached = next(v for v in data["verses"] if (v["sura"], v["aya"]) == (2, 255))
            assert stored == seeder.stored_text(cached)
        finally:
            db.rollback()
        assert not db.execute(text("SELECT 1 FROM tafseer_sources WHERE id='mukhtasar_en'")).first()
