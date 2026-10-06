"""Tasmee must not grade the editorial Basmala prefix as missing words."""
from types import SimpleNamespace

from app.api.routes.tasmee import _recitable_text

BASMALA = "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ"


def _v(sura, aya, text):
    return SimpleNamespace(sura_no=sura, aya_no=aya, text_uthmani=text)


def test_basmala_prefix_removed_from_first_ayah():
    assert _recitable_text(_v(112, 1, f"{BASMALA} قُلْ هُوَ ٱللَّهُ أَحَدٌ")) == "قُلْ هُوَ ٱللَّهُ أَحَدٌ"


def test_fatiha_basmala_is_an_ayah_and_kept():
    assert _recitable_text(_v(1, 1, BASMALA)) == BASMALA


def test_other_ayat_untouched():
    text = "ٱللَّهُ ٱلصَّمَدُ"
    assert _recitable_text(_v(112, 2, text)) == text
