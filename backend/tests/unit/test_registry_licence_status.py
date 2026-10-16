"""
Every source registry entry states its licence clearance, truthfully.

The final release audit found 14 entries in frontend/src/data/sourceRegistry.ts
without licenseStatus (the classical lexicons, two audio hosts, the internal
editorial datasets and the Tirmidhi list), so the gate fell back to a notes
marker. licenseStatus is now a required field, and these checks keep it
honest against data/manifests/tafseer_sources.json:

- every entry has one of cleared / restricted / unverified / blocked;
- 'cleared' on third-party content needs a lastVerifiedAt date;
- a tafsir source served from the library (manifest enabled_ids, not on
  licence hold) is cleared or restricted; one on licence hold or with a
  pending manifest licence is never cleared or restricted.
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
REGISTRY = (ROOT / "frontend" / "src" / "data" / "sourceRegistry.ts").read_text(encoding="utf-8")
MANIFEST = json.loads((ROOT / "data" / "manifests" / "tafseer_sources.json").read_text(encoding="utf-8"))

STATUSES = {"cleared", "restricted", "unverified", "blocked"}
# Content the project itself wrote or curated (no third-party licence involved).
OWN_TYPES = {"internal_mapping", "metadata"}


def _entries() -> dict:
    body = REGISTRY[REGISTRY.index("export const SOURCE_REGISTRY"):]
    out = {}
    for block in re.split(r"\n  \{\n", body)[1:]:
        block = block.split("\n  },")[0]
        sid = re.search(r"sourceId:\s*'([^']+)'", block)
        if not sid:
            continue

        def field(name, block=block):
            m = re.search(name + r":\s*'((?:\\'|[^'])*)'", block)
            return m.group(1) if m else None

        out[sid.group(1)] = {k: field(k) for k in ("licenseStatus", "type", "lastVerifiedAt", "author")}
    return out


ENTRIES = _entries()


def test_registry_parsed():
    assert len(ENTRIES) > 40
    assert "muyassar_ar" in ENTRIES and "lanes_lexicon" in ENTRIES


def test_licence_status_is_required_in_the_type():
    assert re.search(r"\n  licenseStatus: LicenseStatus;", REGISTRY)
    assert "licenseStatus?:" not in REGISTRY


@pytest.mark.parametrize("source_id", sorted(ENTRIES))
def test_every_entry_has_a_licence_status(source_id):
    assert ENTRIES[source_id]["licenseStatus"] in STATUSES, source_id


@pytest.mark.parametrize("source_id", sorted(ENTRIES))
def test_cleared_third_party_content_was_verified(source_id):
    e = ENTRIES[source_id]
    if e["licenseStatus"] == "cleared" and e["type"] not in OWN_TYPES:
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", e["lastVerifiedAt"] or ""), source_id


def test_previously_unset_entries_are_not_invented_as_cleared():
    # Classical works whose digital edition is unverified, and hosts whose
    # terms are not recorded: unknown means 'unverified', never 'cleared'.
    for sid in (
        "al_nihaya_ibn_al_athir", "gharib_al_quran_ibn_qutaybah", "lanes_lexicon",
        "lisan_al_arab", "mufradat_al_raghib", "qamus_al_muhit",
        "quran_audio_cdn", "quran_com_verse_audio", "tirmidhi_asma_husna_list",
    ):
        assert ENTRIES[sid]["licenseStatus"] == "unverified", sid


def test_tafsir_registry_agrees_with_manifest():
    hold = set(MANIFEST.get("licence_hold_ids", []))
    by_id = {s["id"]: s for s in MANIFEST["sources"]}
    for sid in MANIFEST["enabled_ids"]:
        status = ENTRIES[sid]["licenseStatus"]
        if sid in hold:
            assert status in {"unverified", "blocked"}, sid
        else:
            assert status in {"cleared", "restricted"}, sid
    for sid, src in by_id.items():
        lic = src.get("license") or {}
        pending = str(lic.get("type", "")).startswith("pending") or not lic.get("verified_date")
        if sid in ENTRIES and pending:
            assert ENTRIES[sid]["licenseStatus"] not in {"cleared", "restricted"}, sid
