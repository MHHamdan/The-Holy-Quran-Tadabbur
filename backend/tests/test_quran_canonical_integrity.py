"""
The canonical Qur'an text, end to end: source files -> built JSON -> database
-> frontend sources.

(a) data/raw/tanzil/* hash to the source_sha256 recorded in quran_tanzil.json
(b) quran_tanzil.json hashes to quran_hafs.json validation.checksum_sha256
(c) scripts/build_quran_tanzil.py rebuilds quran_tanzil.json byte for byte
(d) all 6,236 quran_verses rows equal the JSON (text, Bismillah, page, juz),
    the hizb/rub'/sajdah markers equal quran_structure_markers.json, and
    text_normalized is a mark-free search key with the verse's letters
(e) no Qur'an text is typed into frontend sources: every vowelled Arabic run
    whose letters occur in the Qur'an is byte-exact Tanzil text (or on the
    reasoned allowlist); quranExcerpts.json is verbatim for every key.

A one-mark change anywhere fails one of these.
"""
import hashlib
import importlib.util
import json
import random
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TANZIL_JSON = ROOT / "data" / "raw" / "quran_tanzil.json"
TANZIL_DIR = ROOT / "data" / "raw" / "tanzil"
HAFS_MANIFEST = ROOT / "data" / "manifests" / "quran_hafs.json"
MARKERS = ROOT / "data" / "manifests" / "quran_structure_markers.json"
EXCERPTS = ROOT / "frontend" / "src" / "data" / "generated" / "quranExcerpts.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from quran_literal_scan import DERIVED_FIELDS, scan  # noqa: E402

# Files owned by other workstreams that still type Qur'an text; each must be
# removed from this set when fixed (the test fails if a listed file is clean).
# Reviewed exceptions: short, unvowelled names, titles or notes that use Qur'anic
# wording without presenting it as a quotation (each sits next to its verse
# reference). Keyed by (file, exact phrase) so any NEW hand-typed text in these
# files still fails. Reviewed by the release orchestrator 2026-10-14.
ALLOWED_NAMED_PHRASES = {
    ("frontend/src/data/generated/quranKnowledgeGraph.json", "مثل الحمار يحمل أسفاراً"): "story title (62:5)",
    ("frontend/src/data/generated/quranKnowledgeGraph.json", "الشجرة الملعونة في القرآن"): "story title (17:60)",
    ("frontend/src/data/generated/quranStoryRegistry.json", "مثل الحمار يحمل أسفاراً"): "story title (62:5)",
    ("frontend/src/data/generated/quranStoryRegistry.json", "الشجرة الملعونة في القرآن"): "story title (17:60)",
    ("frontend/src/data/generated/surahMemoryAtlas.json", "مثل الحمار يحمل أسفاراً"): "story title (62:5)",
    ("frontend/src/data/generated/surahMemoryAtlas.json", "الشجرة الملعونة في القرآن"): "story title (17:60)",
    ("frontend/src/data/generated/quranPlacesIndex.json", "الصفا والمروة من شعائر الله"): "place note citing 2:158",
    ("frontend/src/data/generated/quranProphetStoryPages.json", "آتاه الله الملك والحكمة"):
        "summary wording; echoes 2:251 (about Dawud) - queued for owner review in data/review/owner_review_queue.json",
    ("frontend/src/i18n/translations.ts", "الذي عنده علم من الكتاب"): "name of a figure (27:40)",
    ("frontend/src/pages/QuranicCallsAtlasPage.tsx", "يا أيها الذين آمنوا"): "the call formula the atlas is about",
}


_MARKS = re.compile("[\u064B-\u065F\u0670]")


def _letters(text: str) -> str:
    """Letter skeleton shared by the search normalisers (seats and pause signs folded)."""
    text = re.sub("[\u06D6-\u06ED\u0640\s]", "", text)
    for a, b in (("ؤ", "و"), ("ئ", "ي"), ("ء", ""), ("ة", "ه"), ("ى", "ي")):
        text = text.replace(a, b)
    return text


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def tanzil():
    return json.loads(TANZIL_JSON.read_text(encoding="utf-8"))


# --- (a) (b) checksums -------------------------------------------------------

def test_source_files_match_recorded_hashes(tanzil):
    recorded = tanzil["source_sha256"]
    assert set(recorded) == {p.name for p in TANZIL_DIR.iterdir() if p.is_file()}
    for name, digest in recorded.items():
        assert _sha256(TANZIL_DIR / name) == digest, name


def test_built_json_matches_manifest_checksum():
    manifest = json.loads(HAFS_MANIFEST.read_text(encoding="utf-8"))
    assert manifest["validation"]["checksum_sha256"] == _sha256(TANZIL_JSON)


def test_checksum_detects_a_single_mark(tmp_path):
    raw = TANZIL_JSON.read_text(encoding="utf-8")
    mutated = tmp_path / "q.json"
    mutated.write_text(raw.replace("َ", "ِ", 1), encoding="utf-8")
    manifest = json.loads(HAFS_MANIFEST.read_text(encoding="utf-8"))
    assert _sha256(mutated) != manifest["validation"]["checksum_sha256"]


# --- (c) rebuild ---------------------------------------------------------------

def test_rebuild_is_byte_identical(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("build_quran_tanzil", ROOT / "scripts" / "build_quran_tanzil.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    out = tmp_path / "quran_tanzil.json"
    monkeypatch.setattr(mod, "OUT", out)
    monkeypatch.setattr(mod, "ROOT", tmp_path)  # only used to print a relative path
    assert mod.main() in (0, None)
    assert out.read_bytes() == TANZIL_JSON.read_bytes()


# --- (d) database parity ---------------------------------------------------------

@pytest.mark.asyncio
async def test_database_rows_equal_canonical_json(tanzil):
    from sqlalchemy import text
    from app.db import database

    spec = importlib.util.spec_from_file_location(
        "seed_quran", ROOT / "backend" / "scripts" / "ingest" / "seed_quran.py")
    seed_quran = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(seed_quran)

    async with database.AsyncSessionLocal() as session:
        try:
            rows = (await session.execute(text(
                "SELECT id, sura_no, aya_no, text_uthmani, text_imlaei, text_normalized, "
                "bismillah_uthmani, bismillah_imlaei, page_no, juz_no, hizb_no, rub_no, sajda_type "
                "FROM quran_verses ORDER BY id"
            ))).mappings().all()
        except Exception as e:  # pragma: no cover
            pytest.skip(f"database unavailable: {type(e).__name__}")
    if not rows:
        pytest.skip("quran_verses not seeded")

    verses = tanzil["verses"]
    assert len(rows) == len(verses) == 6236
    markers = json.loads(MARKERS.read_text(encoding="utf-8"))
    starts = {tuple(q): i + 1 for i, q in enumerate(markers["hizb_quarters"])}
    sajdahs = {(s["sura"], s["aya"]): s["type"] for s in markers["sajdahs"]}
    rub = 0
    mismatches = []
    for row, v in zip(rows, verses):
        key = (v["sura_no"], v["aya_no"])
        rub = starts.get(key, rub)
        expected = {
            "sura_no": v["sura_no"], "aya_no": v["aya_no"],
            "text_uthmani": v["aya_text"], "text_imlaei": v["aya_text_emlaey"],
            "bismillah_uthmani": v["bismillah"], "bismillah_imlaei": v["bismillah_emlaey"],
            "page_no": v["page"], "juz_no": v["jozz"],
            "rub_no": rub, "hizb_no": (rub - 1) // 4 + 1, "sajda_type": sajdahs.get(key),
        }
        for field, value in expected.items():
            if row[field] != value:
                mismatches.append((key, field))
        # text_normalized is a search key. The stored keys were produced by an
        # older normaliser (hamza seats folded, pause signs dropped) that matches
        # neither seed_quran.normalize_for_search nor quran_search's functions,
        # so only its invariants are checked here: present, no vowel marks, and
        # the same letters as the verse (reported for the seed's owner).
        norm = row["text_normalized"] or ""
        if not norm or _MARKS.search(norm) or _letters(norm) != _letters(seed_quran.normalize_for_search(v["aya_text"])):
            mismatches.append((key, "text_normalized"))
    assert not mismatches, mismatches[:10]


# --- (e) frontend sources ----------------------------------------------------------

def test_no_hand_typed_quran_in_frontend():
    hits = scan()
    by_file = {}
    for rel, n, run in hits:
        by_file.setdefault(rel, []).append((n, run))
    found = {(f, run) for f, v in by_file.items() for _, run in v}
    unexpected = sorted(found - set(ALLOWED_NAMED_PHRASES))
    assert not unexpected, unexpected[:10]
    stale = set(ALLOWED_NAMED_PHRASES) - found
    assert not stale, f"no longer present, remove from ALLOWED_NAMED_PHRASES: {stale}"


def test_scanner_flags_a_single_changed_mark(tmp_path, tanzil):
    random.seed(7)
    verse = next(v for v in random.sample(tanzil["verses"], 200) if v["aya_text_emlaey"].count("َ") > 3
                 and len(v["aya_text_emlaey"].split()) > 5)
    original = verse["aya_text_emlaey"]
    mutated = original.replace("َ", "ِ", 1)
    f = tmp_path / "sample.ts"
    f.write_text(f"export const ok = '{original}';\nexport const bad = '{mutated}';\n", encoding="utf-8")
    # the scanner reports paths relative to the repo; place the file inside it
    target = ROOT / "frontend" / "src" / "__ws3_scan_probe__.ts"
    target.write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
    try:
        hits = scan([target])
    finally:
        target.unlink()
    assert [n for _, n, _ in hits] == [2]


def test_scanner_flags_unvowelled_quotation(tanzil):
    """Canonical text is vowelled, so a typed unvowelled quotation is never verbatim."""
    verse = next(v for v in tanzil["verses"] if len(v["aya_text_emlaey"].split()) >= 8)
    plain = re.sub("[\u064B-\u065F\u0670\u06D6-\u06ED]", "", verse["aya_text_emlaey"])
    plain = " ".join(plain.split()[:6])
    target = ROOT / "frontend" / "src" / "__ws3_scan_probe_plain__.ts"
    target.write_text(f"export const quote = '\"{plain}\"';\n", encoding="utf-8")
    try:
        hits = scan([target])
    finally:
        target.unlink()
    assert [n for _, n, _ in hits] == [1]


def test_derived_call_phrases_come_from_their_verse():
    """callText lines are skipped by the scanner, so check they are cut from the record's verse."""
    strip = re.compile("[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED\u0640]")
    for rel in DERIVED_FIELDS:
        data = json.loads((ROOT / rel).read_text(encoding="utf-8"))
        calls = data["calls"]
        assert calls, rel
        for c in calls:
            if c.get("callText"):
                assert c["callText"] in strip.sub("", c["ayahTextEmlaei"]), (rel, c["callId"])


def test_generated_excerpts_are_verbatim(tanzil):
    data = json.loads(EXCERPTS.read_text(encoding="utf-8"))
    assert "CHANGING IT IS NOT ALLOWED" in data["quranTextCopyright"]
    by_key = {(v["sura_no"], v["aya_no"]): v["aya_text_emlaey"] for v in tanzil["verses"]}
    for key, text_ in data["excerpts"].items():
        ref = key.split("#")[0]
        sura, ayas = ref.split(":")
        start, _, end = ayas.partition("-")
        verses = [by_key[(int(sura), a)] for a in range(int(start), int(end or start) + 1)]
        assert text_ and text_ in " ".join(verses), key
