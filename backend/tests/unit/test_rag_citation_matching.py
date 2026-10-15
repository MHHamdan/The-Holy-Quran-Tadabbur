"""Hardened citation matching (validators/citation_validator.py)."""
from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

from app.validators.citation_validator import (
    CITATION_MARKER_RE,
    build_surah_name_index,
    chunk_aliases,
    match_citations,
    normalize_source_alias,
    parse_cited_reference,
)

SURAHS = build_surah_name_index([
    (1, "سورة الفاتحة", "Al-Faatiha"), (2, "سورة البقرة", "Al-Baqara"),
    (3, "سورة آل عمران", "Aal-i-Imraan"), (7, "سورة الأعراف", "Al-A'raaf"),
    (20, "سورة طه", "Taa-Haa"), (36, "سورة يس", "Yaseen"), (112, "سورة الإخلاص", "Al-Ikhlaas"),
])


def _chunk(source_id="ibn_kathir_ar", name="Tafsir Ibn Kathir (Arabic)", name_ar="تفسير ابن كثير",
           sura=2, start=255, end=255):
    return SimpleNamespace(chunk_id=f"{source_id}:{sura}:{start}", source_id=source_id, source_name=name,
                           source_name_ar=name_ar, sura_no=sura, aya_start=start, aya_end=end)


@pytest.mark.parametrize("ref,expected", [
    ("2:255", (2, 255, 255)), ("٢:٢٥٥", (2, 255, 255)), ("2:255-257", (2, 255, 257)),
    ("Al-Baqarah:255", (2, 255, 255)), ("Al-Baqara:45", (2, 45, 45)), ("البقرة:٤٥", (2, 45, 45)),
    ("سورة البقرة:٤٥", (2, 45, 45)), ("Surah 2:255", (2, 255, 255)), ("Ali Imran:7", (3, 7, 7)),
    ("Ya-Sin:1", (36, 1, 1)), ("Ta-Ha:5", (20, 5, 5)), ("Al-A'raf:3", (7, 3, 3)),
    ("0:0", None), ("2:300", None), ("115:1", None), ("2:10-5", None), ("Unknown:2", None),
])
def test_reference_parsing(ref, expected):
    assert parse_cited_reference(ref, SURAHS) == expected


def test_markers_with_blank_or_tiny_names_are_detected():
    found = [m.group(1) for m in CITATION_MARKER_RE.finditer("a [I, 2:255] b [ , 2:255] c [i.e., the angels]")]
    assert found == ["I", ""]


def test_aliases_are_exact_and_long_enough():
    aliases = chunk_aliases(_chunk())
    assert {"ibnkathir", normalize_source_alias("ابن كثير")} <= aliases
    assert all(len(a) >= 3 for a in aliases)
    assert normalize_source_alias("I") not in aliases


@pytest.mark.parametrize("marker,ok", [
    ("[Ibn Kathir, 2:255]", True),
    ("[Ibn Kathir, Al-Baqarah:255]", True),
    ("[ابن كثير، ٢:٢٥٥]", True),
    ("[Ismail ibn Umar ibn Kathir, 2:255]", True),
    ("[Kathir, 2:255]", False),          # partial name
    ("[I, 2:255]", False),
    ("[ , 2:255]", False),
    ("[Ibn Kathir, 0:0]", False),
    ("[Ibn Kathir, 2:1-286]", False),    # range wider than the chunk
    ("[Ibn Kathir, 2:254]", False),
    ("[Al-Tabari, 2:255]", False),       # source not retrieved
])
def test_match_rules(marker, ok):
    result = match_citations(f"Claim {marker}.", [_chunk()], SURAHS)
    assert (len(result.valid) == 1) is ok
    assert (marker in result.invalid_markers) is (not ok)


def test_quran_self_reference_valid_only_for_existing_ayat():
    result = match_citations("A [Quran, 2:255]. B [Quran, 2:300].", [_chunk()], SURAHS)
    assert [m.is_quran for m in result.valid] == [True]
    assert result.invalid_markers == ["[Quran, 2:300]"]


def test_range_inside_chunk_range_matches():
    chunk = _chunk(start=255, end=257)
    assert match_citations("x [Ibn Kathir, 2:256-257]", [chunk], SURAHS).valid


async def test_validate_citations_endpoint_caps_chunk_ids():
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/v1/rag/validate-citations", json={
            "answer": "x [Ibn Kathir, 2:255]", "retrieved_chunk_ids": [f"id{i}" for i in range(51)],
        })
    assert r.status_code == 422
