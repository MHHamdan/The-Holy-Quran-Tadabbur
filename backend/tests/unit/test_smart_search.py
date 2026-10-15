"""
Smart search parsing: references, surah names, aliases (no DB).
"""
import pytest

from app.services.quran_aliases import resolve_alias
from app.services.smart_search import (
    ParsedReference,
    arabic_surah_key,
    latin_key,
    match_surahs,
    parse_reference,
)


@pytest.mark.parametrize("q", [
    "2:255", "٢:٢٥٥", "۲:۲۵۵", "2 255", "2.255", "2-255", "2/255",
    "سورة 2:255", "surah 2:255", " 2 : 255 ", "2：255",
])
def test_reference_forms(q):
    assert parse_reference(q) == ParsedReference(2, 255, None)


def test_reference_range():
    assert parse_reference("2:255-257") == ParsedReference(2, 255, 257)
    assert parse_reference("٢:٢٥٥–٢٥٧") == ParsedReference(2, 255, 257)


def test_bare_number_is_surah():
    assert parse_reference("18") == ParsedReference(18, None)
    assert parse_reference("سورة ١٨") == ParsedReference(18, None)


@pytest.mark.parametrize("q", ["patience", "الصبر", "2:255 mercy", "1234:1", ""])
def test_not_a_reference(q):
    assert parse_reference(q) is None


@pytest.mark.parametrize("name", ["Al-Baqarah", "al-baqara", "Al Baqarah", "Baqarah", "BAQARA", "Surah Al-Baqarah", "Albaqara"])
def test_latin_surah_names(name):
    assert 2 in match_surahs(name)


@pytest.mark.parametrize("name", [
    "البقرة",                      # البقرة
    "سورة البقرة",  # سورة البقرة
    "البقره",                      # البقره
    "بقرة",                                  # بقرة
])
def test_arabic_surah_names(name):
    assert 2 in match_surahs(name)


def test_latin_key_folds():
    assert latin_key("Al-Baqarah") == latin_key("baqara") == "baqara"
    assert latin_key("Aal-Imran") == latin_key("Al Imran")


def test_arabic_key_strips_surah_word():
    assert arabic_surah_key("سورة الكهف") == "الكهف"


def test_word_that_is_not_a_surah():
    assert match_surahs("patience") == []
    assert match_surahs("الصبر") == []


@pytest.mark.parametrize("q", ["آية الكرسي", "ayat al kursi", "Ayat al-Kursi"])
def test_ayat_al_kursi_alias(q):
    t = resolve_alias(q)
    assert (t.sura_no, t.aya_start, t.kind) == (2, 255, "verse")
