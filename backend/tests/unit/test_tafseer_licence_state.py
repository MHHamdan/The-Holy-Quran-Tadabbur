"""
English tafsir translations are not public domain, and the seeder and DB say so.

ibn_kathir_en / jalalayn_en / ibn_abbas_en were seeded as
'public_domain_classical' with license_verified=1 because the Arabic authors
died centuries ago; the English texts are modern copyrighted translations.
The seeder now takes licence state from the manifest, and migration
ws3a1b2c3d4e5 disables the rows. The DB checks run the migration's SQL inside
a transaction that is rolled back, so the shared database is not changed.
"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND / "scripts" / "ingest"))

import seed_tafseer  # noqa: E402


def _migration():
    path = BACKEND / "alembic" / "versions" / "ws3a1b2c3d4e5_disable_unlicensed_english_tafsir.py"
    spec = importlib.util.spec_from_file_location("ws3a_migration", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ENGLISH = ("ibn_kathir_en", "jalalayn_en", "ibn_abbas_en")


def test_no_english_source_is_labelled_public_domain():
    for sid, meta in seed_tafseer.SOURCE_METADATA.items():
        if meta.get("language") == "en":
            assert meta["license_type"] == "pending_verification", sid
            assert "public domain" not in meta["license"].lower(), sid


@pytest.mark.parametrize("sid", ENGLISH)
def test_manifest_marks_english_unverified(sid):
    state = seed_tafseer.load_licence_state(sid)
    assert state == {**state, "verified": False, "enabled": False}


@pytest.mark.parametrize("sid", ["ibn_kathir_ar", "tabari_ar", "qurtubi_ar", "baghawi_ar", "muyassar_ar"])
def test_manifest_enables_verified_arabic(sid):
    state = seed_tafseer.load_licence_state(sid)
    assert state["verified"] and state["enabled"], state


def test_unknown_source_is_unverified(tmp_path):
    assert not seed_tafseer.load_licence_state("no_such_source")["verified"]
    bad = tmp_path / "m.json"
    bad.write_text("{not json")
    assert not seed_tafseer.load_licence_state("tabari_ar", bad)["verified"]


def test_seeder_skips_unverified_without_flag(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("must not load data for an unverified source")

    monkeypatch.setattr(seed_tafseer, "load_tafseer_data", boom)
    assert seed_tafseer.seed_source(session=None, source_id="ibn_kathir_en") == (0, 0, 0)


def test_manifest_enabled_ids_have_verified_licences():
    manifest = json.loads((ROOT / "data" / "manifests" / "tafseer_sources.json").read_text(encoding="utf-8"))
    by_id = {s["id"]: s for s in manifest["sources"]}
    for sid in manifest["enabled_ids"]:
        lic = by_id[sid]["license"]
        assert lic["verified_date"] and not lic["type"].startswith("pending"), sid
    assert not set(ENGLISH) & set(manifest["enabled_ids"])


@pytest.mark.asyncio
async def test_migration_removes_english_from_compare_and_rag_sources():
    from app.db import database
    from app.services.tafsir_comparison import tafsir_comparison_service

    mod = _migration()
    # The swarm migrations were linearised (ws2a -> ws3a -> ...); pin the
    # revision, not its parent.
    assert mod.revision == "ws3a1b2c3d4e5"
    async with database.AsyncSessionLocal() as session:
        try:
            await session.execute(text("SELECT 1 FROM tafseer_sources LIMIT 1"))
        except Exception as e:  # pragma: no cover
            pytest.skip(f"database unavailable: {type(e).__name__}")
        try:
            for sql in mod.UPGRADE_SQL:
                await session.execute(text(sql))
            rows = (await session.execute(text(
                "SELECT id, is_enabled, license_verified, license_type, license, translator "
                "FROM tafseer_sources WHERE id IN ('ibn_kathir_en','jalalayn_en')"
            ))).all()
            for sid, enabled, verified, ltype, lic, translator in rows:
                assert (enabled, verified, ltype) == (0, 0, "pending_verification"), sid
                assert "public domain" not in (lic or "").lower()
                assert translator
            result = await tafsir_comparison_service.compare_verse(session, surah=2, ayah=255)
            assert result["entries"], "expected Arabic tafsir for 2:255"
            assert not [e for e in result["entries"] if e["source_id"].endswith("_en")]
        finally:
            await session.rollback()
