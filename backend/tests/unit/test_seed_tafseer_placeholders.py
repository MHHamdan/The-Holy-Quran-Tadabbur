"""
'لا يوجد تفسير لهذه الأية' rows are not tafsir and are never stored.

99 such rows (qurtubi_ar 60, ibn_kathir_ar 39) were shown under the scholar's
name and could be cited by RAG. The seeder now skips them and migration
ws3b2c3d4e5f6 deletes the stored ones; the DB check runs that SQL inside a
transaction that is rolled back.
"""
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import text

BACKEND = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND / "scripts" / "ingest"))

import seed_tafseer  # noqa: E402

PLACEHOLDER = "لا يوجد تفسير لهذه الأية"


@pytest.mark.parametrize("value", [PLACEHOLDER, f"  {PLACEHOLDER} ", f"{PLACEHOLDER}.", "لا يوجد تفسير لهذه الآية"])
def test_placeholder_detected(value):
    assert seed_tafseer.is_placeholder(value)


def test_real_text_is_not_a_placeholder():
    assert not seed_tafseer.is_placeholder("قال أبو جعفر: لا يوجد تفسير لهذه الأية عند فلان ثم ذكر")


class _Result:
    def __init__(self, rows=None):
        self._rows = rows or []

    def scalar_one_or_none(self):
        return None

    def all(self):
        return self._rows


class _Session:
    def __init__(self):
        self.added = []

    def execute(self, stmt):
        if "quran_verses" in str(stmt):
            return _Result([(1, 26, 33), (2, 26, 34), (3, 26, 35)])
        return _Result()

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        pass

    def commit(self):
        pass


def test_seeder_drops_placeholders(monkeypatch):
    data = [
        {"surah": 26, "ayah": 33, "text": "نص تفسير حقيقي"},
        {"surah": 26, "ayah": 34, "text": PLACEHOLDER},
        {"surah": 26, "ayah": 35, "text": PLACEHOLDER + " "},
    ]
    monkeypatch.setattr(seed_tafseer, "load_tafseer_data", lambda sid: (data, "hash"))
    monkeypatch.setattr(seed_tafseer, "load_licence_state",
                        lambda sid: {"verified": True, "enabled": True, "reason": "ok"})
    session = _Session()
    inserted, skipped, failed = seed_tafseer.seed_source(session, "qurtubi_ar")
    assert (inserted, skipped, failed) == (1, 2, 0)
    chunks = [o for o in session.added if type(o).__name__ == "TafseerChunk"]
    assert [c.aya_start for c in chunks] == [33]
    source = next(o for o in session.added if type(o).__name__ == "TafseerSource")
    assert source.license_verified == 1 and source.is_enabled == 1


def _migration():
    path = BACKEND / "alembic" / "versions" / "ws3b2c3d4e5f6_drop_tafsir_placeholders.py"
    spec = importlib.util.spec_from_file_location("ws3b_migration", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.asyncio
async def test_migration_deletes_placeholders_and_recounts():
    from app.db import database
    from app.services.tafsir_comparison import tafsir_comparison_service

    mod = _migration()
    assert mod.down_revision == "ws3a1b2c3d4e5"
    async with database.AsyncSessionLocal() as session:
        try:
            before = (await session.execute(text(
                "SELECT count(*) FROM tafseer_chunks WHERE btrim(content_ar) = :p"), {"p": PLACEHOLDER})).scalar()
        except Exception as e:  # pragma: no cover
            pytest.skip(f"database unavailable: {type(e).__name__}")
        if not before:
            pytest.skip("no placeholder rows in this database (already migrated or not seeded)")
        try:
            for sql in mod.UPGRADE_SQL:
                await session.execute(text(sql))
            after = (await session.execute(text(
                "SELECT count(*) FROM tafseer_chunks WHERE content_ar LIKE 'لا يوجد تفسير%'"))).scalar()
            assert after == 0
            counts = dict((await session.execute(text(
                "SELECT id, ayah_count FROM tafseer_sources WHERE id IN ('qurtubi_ar','ibn_kathir_ar')"))).all())
            assert counts == {"qurtubi_ar": 6176, "ibn_kathir_ar": 6197}
            result = await tafsir_comparison_service.compare_verse(session, surah=26, ayah=34)
            assert "qurtubi_ar" not in {e["source_id"] for e in result["entries"]}
        finally:
            await session.rollback()
