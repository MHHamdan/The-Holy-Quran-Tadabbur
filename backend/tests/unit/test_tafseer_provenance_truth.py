"""
The tafsir footer credits where the stored text really came from.

The reader footer shows the registry's licenseOrTerms and sourceUrl next to
"Copy stored in the Tadabbur library". For tabari_ar, qurtubi_ar and
ibn_kathir_ar it credited the Apache-2.0 riotu-lab/Quran-Tafseers dataset
while the stored passages were seeded from the spa5k tafsir_api CDN (only
3215/6236, 3116/6176 and 560/6197 passages identical). The registry now names
the spa5k edition with licence status "unverified" (owner review), and these
checks keep the registry, the manifest's stored_copy record and the database
row's source_url in agreement, so a later reseed from the dataset
(seed_tafseer.py --replace) has to update all three together.
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = json.loads((ROOT / "data" / "manifests" / "tafseer_sources.json").read_text(encoding="utf-8"))
REGISTRY_SRC = (ROOT / "frontend" / "src" / "data" / "sourceRegistry.ts").read_text(encoding="utf-8")
HF_DATASET = "riotu-lab/Quran-Tafseers"
SPA5K = "cdn.jsdelivr.net/gh/spa5k/tafsir_api"
STORED_ELSEWHERE = ("ibn_kathir_ar", "tabari_ar", "qurtubi_ar")


def _registry(source_id: str) -> dict:
    m = re.search(r"\{\s*sourceId:\s*'" + re.escape(source_id) + r"'(.*?)\n  \},", REGISTRY_SRC, re.S)
    assert m, source_id
    block = m.group(1)

    def field(name):
        f = re.search(name + r":\s*'((?:\\'|[^'])*)'", block)
        return f.group(1).replace("\\'", "'") if f else None

    return {k: field(k) for k in ("licenseOrTerms", "sourceUrl", "licenseStatus", "notes")}


def _manifest(source_id: str) -> dict:
    return next(s for s in MANIFEST["sources"] if s["id"] == source_id)


@pytest.mark.parametrize("source_id", STORED_ELSEWHERE)
def test_registry_names_the_stored_copy_origin_not_the_dataset(source_id):
    reg = _registry(source_id)
    sc = _manifest(source_id)["stored_copy"]
    assert HF_DATASET not in reg["licenseOrTerms"]
    assert HF_DATASET not in reg["sourceUrl"]
    assert reg["sourceUrl"] == sc["seeded_from"]
    assert SPA5K in reg["sourceUrl"]
    assert "spa5k" in reg["licenseOrTerms"] and "unverified" in reg["licenseOrTerms"]
    assert reg["licenseStatus"] == "unverified" == sc["registry_status"]
    assert sc["owner_review"] is True
    assert "seed_tafseer.py --replace" in sc["note"]
    assert "Seeded from the Apache-2.0 HF dataset" not in _manifest(source_id)["license"]["notes"]


def test_baghawi_really_is_from_the_dataset():
    reg = _registry("baghawi_ar")
    assert HF_DATASET in reg["sourceUrl"]
    assert "stored_copy" not in _manifest("baghawi_ar")


@pytest.mark.asyncio
async def test_registry_agrees_with_the_database_origin():
    """A registry entry may credit the dataset only if the row's text came from it."""
    from sqlalchemy import text

    from app.db import database

    async with database.AsyncSessionLocal() as session:
        try:
            rows = (await session.execute(text(
                "SELECT id, source_url FROM tafseer_sources WHERE is_enabled = 1"
            ))).all()
        except Exception as e:  # pragma: no cover
            pytest.skip(f"database unavailable: {type(e).__name__}")
    if not rows:
        pytest.skip("no tafsir sources seeded")
    for sid, source_url in rows:
        reg = _registry(sid)
        credits_dataset = HF_DATASET in (reg["licenseOrTerms"] or "") or HF_DATASET in (reg["sourceUrl"] or "")
        from_dataset = HF_DATASET in (source_url or "")
        if credits_dataset:
            assert from_dataset, f"{sid}: registry credits {HF_DATASET} but the stored text came from {source_url}"
        sc = _manifest(sid).get("stored_copy")
        if sc and sid in STORED_ELSEWHERE:
            assert source_url == sc["seeded_from"], (
                f"{sid}: database source_url {source_url} differs from manifest stored_copy; "
                "after a reseed update the registry entry and the manifest together"
            )


def test_replace_plan_keeps_ids_and_diffs_by_verse():
    import sys

    sys.path.insert(0, str(ROOT / "backend" / "scripts" / "ingest"))
    import seed_tafseer

    stored = {(1, 1): "a", (2, 1): "b", (2, 2): "c"}
    new = {(2, 1): "b", (2, 2): "C", (2, 3): "d"}
    plan = seed_tafseer.plan_replacement(new, stored)
    assert plan == {"update": [(2, 2)], "insert": [(2, 3)], "delete": [(1, 1)], "unchanged": 1}
    # chunk ids depend only on source and verse, so an update keeps the id
    assert seed_tafseer.generate_chunk_id("tabari_ar", 2, 2) == seed_tafseer.generate_chunk_id("tabari_ar", 2, 2)
    entries = [
        {"surah": 2, "ayah": 1, "text": "  نص  "},
        {"surah": 2, "ayah": 2, "text": "لا يوجد تفسير لهذه الأية"},
        {"surah": 2, "ayah": 3, "text": ""},
    ]
    assert seed_tafseer.clean_entries(entries, "ar") == {(2, 1): "نص"}


def test_replace_requires_pinned_provenance(tmp_path, monkeypatch):
    import sys

    sys.path.insert(0, str(ROOT / "backend" / "scripts" / "ingest"))
    import seed_tafseer

    monkeypatch.setattr(seed_tafseer, "RAW_DIR", tmp_path)
    (tmp_path / "tabari_ar.json").write_text("[]", encoding="utf-8")
    with pytest.raises(SystemExit, match="provenance.json"):
        seed_tafseer.replace_source(session=None, source_id="tabari_ar", qdrant=False)
