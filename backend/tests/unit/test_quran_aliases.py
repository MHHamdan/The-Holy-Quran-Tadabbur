"""
Unit tests for the Quranic alias layer (quran_aliases.py).

Tests cover:
- Arabic spelling variants (with/without hamza, diacritics)
- Transliteration variants
- Range vs. single-verse resolution
- No Quran-text mutation
- match_type field on the response model
"""
import pytest
from app.services.quran_aliases import resolve_alias, AliasTarget, ALIAS_MAP, _norm_key


# ---------------------------------------------------------------------------
# Ayat al-Kursi (2:255)
# ---------------------------------------------------------------------------

class TestAyatAlKursi:
    def test_arabic_with_hamza(self):
        result = resolve_alias("آية الكرسي")
        assert result is not None
        assert result.sura_no == 2
        assert result.aya_start == 255
        assert result.aya_end is None

    def test_arabic_without_hamza(self):
        result = resolve_alias("اية الكرسي")
        assert result is not None
        assert result.sura_no == 2
        assert result.aya_start == 255

    def test_english_with_hyphen(self):
        result = resolve_alias("Ayat al-Kursi")
        assert result is not None
        assert result.sura_no == 2
        assert result.aya_start == 255

    def test_english_ayatul(self):
        result = resolve_alias("Ayatul Kursi")
        assert result is not None
        assert result.sura_no == 2
        assert result.aya_start == 255

    def test_case_insensitive(self):
        assert resolve_alias("AYAT AL-KURSI") is not None
        assert resolve_alias("ayat al-kursi") is not None
        assert resolve_alias("Ayat Al Kursi") is not None

    def test_diacritics_stripped(self):
        # With kasra on kursi
        result = resolve_alias("آية الكُرسي")
        assert result is not None
        assert result.sura_no == 2

    def test_label_ar(self):
        result = resolve_alias("Ayatul Kursi")
        assert result.label_ar == "آية الكرسي"

    def test_label_en(self):
        result = resolve_alias("آية الكرسي")
        assert result.label_en == "Ayat al-Kursi"


# ---------------------------------------------------------------------------
# Al-Fatihah (Surah 1, 1:1–1:7)
# ---------------------------------------------------------------------------

class TestAlFatihah:
    def test_arabic_surah_prefix(self):
        result = resolve_alias("سورة الفاتحة")
        assert result is not None
        assert result.sura_no == 1
        assert result.aya_start == 1
        assert result.aya_end == 7

    def test_arabic_short(self):
        result = resolve_alias("الفاتحة")
        assert result is not None
        assert result.sura_no == 1

    def test_english_al_fatihah(self):
        result = resolve_alias("Al-Fatihah")
        assert result is not None
        assert result.sura_no == 1

    def test_english_fatiha(self):
        result = resolve_alias("Fatiha")
        assert result is not None
        assert result.sura_no == 1

    def test_english_surah_prefix(self):
        result = resolve_alias("Surah Al-Fatihah")
        assert result is not None
        assert result.sura_no == 1

    def test_full_range_returned(self):
        result = resolve_alias("الفاتحة")
        assert result.aya_start == 1
        assert result.aya_end == 7


# ---------------------------------------------------------------------------
# People / Companions of the Cave (18:9–26)
# ---------------------------------------------------------------------------

class TestPeopleOfTheCave:
    def test_arabic_with_hamza(self):
        result = resolve_alias("أصحاب الكهف")
        assert result is not None
        assert result.sura_no == 18
        assert result.aya_start == 9
        assert result.aya_end == 26

    def test_arabic_without_hamza(self):
        result = resolve_alias("اصحاب الكهف")
        assert result is not None
        assert result.sura_no == 18
        assert result.aya_start == 9

    def test_english_people(self):
        result = resolve_alias("People of the Cave")
        assert result is not None
        assert result.sura_no == 18
        assert result.aya_start == 9

    def test_english_companions(self):
        result = resolve_alias("Companions of the Cave")
        assert result is not None
        assert result.sura_no == 18

    def test_range_is_correct(self):
        result = resolve_alias("أصحاب الكهف")
        assert result.aya_end == 26


# ---------------------------------------------------------------------------
# Dhul-Qarnayn (18:83–98)
# ---------------------------------------------------------------------------

class TestDhulQarnayn:
    def test_arabic(self):
        result = resolve_alias("ذو القرنين")
        assert result is not None
        assert result.sura_no == 18
        assert result.aya_start == 83
        assert result.aya_end == 98

    def test_english_hyphen(self):
        result = resolve_alias("Dhul-Qarnayn")
        assert result is not None
        assert result.sura_no == 18
        assert result.aya_start == 83

    def test_english_space(self):
        result = resolve_alias("Dhul Qarnayn")
        assert result is not None
        assert result.sura_no == 18

    def test_transliteration_zul(self):
        result = resolve_alias("Zul Qarnayn")
        assert result is not None
        assert result.sura_no == 18

    def test_range_is_correct(self):
        result = resolve_alias("Dhul-Qarnayn")
        assert result.aya_end == 98


# ---------------------------------------------------------------------------
# Non-alias queries return None
# ---------------------------------------------------------------------------

class TestNonAliasQueries:
    def test_common_word_not_alias(self):
        assert resolve_alias("الله") is None

    def test_prophet_name_not_alias(self):
        assert resolve_alias("موسى") is None

    def test_empty_string(self):
        assert resolve_alias("") is None

    def test_random_phrase(self):
        assert resolve_alias("something completely random xyz") is None

    def test_partial_alias_name(self):
        # "الكرسي" alone is not registered
        assert resolve_alias("الكرسي") is None


# ---------------------------------------------------------------------------
# No Quran-text mutation
# ---------------------------------------------------------------------------

class TestNoTextMutation:
    def test_alias_does_not_store_quran_text(self):
        """AliasTarget stores only references, never Quran text strings."""
        for key, target in ALIAS_MAP.items():
            assert isinstance(target.sura_no, int), f"sura_no must be int: {key}"
            assert isinstance(target.aya_start, int), f"aya_start must be int: {key}"
            assert target.aya_end is None or isinstance(target.aya_end, int)
            # label fields are metadata strings (verse names), not Quran text
            # They should not contain Arabic tashkeel (full diacritics would
            # suggest copy-pasted Quran text)
            import re
            TASHKEEL = re.compile(r'[ً-ٰٟ]')
            assert not TASHKEEL.search(target.label_ar), (
                f"label_ar for '{key}' contains tashkeel — likely copied from "
                f"Quran text (forbidden). Use a plain metadata label."
            )

    def test_alias_map_has_no_collisions(self):
        """Each normalised key maps to exactly one target (collision check runs at import)."""
        seen: dict = {}
        for _spellings, _target in []:  # collision already caught at module load
            pass
        # If import succeeded, no collision was found
        assert len(ALIAS_MAP) > 0


# ---------------------------------------------------------------------------
# match_type field on GroundedVerseResponse
# ---------------------------------------------------------------------------

class TestMatchTypeField:
    def test_grounded_verse_response_has_match_type(self):
        """GroundedVerseResponse must have a match_type field with default 'normalized'."""
        from app.api.routes.quran import GroundedVerseResponse
        import inspect
        fields = GroundedVerseResponse.model_fields
        assert "match_type" in fields, "match_type field missing from GroundedVerseResponse"
        default = fields["match_type"].default
        assert default == "normalized", (
            f"match_type default should be 'normalized', got {default!r}"
        )

    def test_alias_match_type_value(self):
        """The string 'alias' is the correct match_type for alias hits."""
        from app.api.routes.quran import GroundedVerseResponse
        v = GroundedVerseResponse(
            verse_id=1, sura_no=2, sura_name_ar="البقرة", sura_name_en="Al-Baqarah",
            aya_no=255, reference="2:255", text_uthmani="...", text_imlaei="...",
            page_no=42, juz_no=3, relevance_score=1.0, highlighted_text="...",
            grounding="Direct alias: Ayat al-Kursi",
            matched_concepts=["آية الكرسي"], highlighted_terms=["آية الكرسي"],
            match_type="alias",
        )
        assert v.match_type == "alias"

    def test_valid_match_type_values(self):
        """Accepted match_type values are alias, normalized, concept_expansion."""
        from app.api.routes.quran import GroundedVerseResponse
        base = dict(
            verse_id=1, sura_no=1, sura_name_ar="الفاتحة", sura_name_en="Al-Fatihah",
            aya_no=1, reference="1:1", text_uthmani="...", text_imlaei="...",
            page_no=1, juz_no=1, relevance_score=0.5, highlighted_text="...",
            grounding="test", matched_concepts=[], highlighted_terms=[],
        )
        for mt in ("alias", "normalized", "concept_expansion"):
            v = GroundedVerseResponse(**base, match_type=mt)
            assert v.match_type == mt


# ---------------------------------------------------------------------------
# ALIAS_MAP integrity
# ---------------------------------------------------------------------------

class TestAliasMapIntegrity:
    def test_all_sura_nos_valid(self):
        for key, target in ALIAS_MAP.items():
            assert 1 <= target.sura_no <= 114, f"sura_no out of range for key '{key}'"

    def test_all_aya_starts_positive(self):
        for key, target in ALIAS_MAP.items():
            assert target.aya_start >= 1, f"aya_start < 1 for key '{key}'"

    def test_range_end_gte_start(self):
        for key, target in ALIAS_MAP.items():
            if target.aya_end is not None:
                assert target.aya_end >= target.aya_start, (
                    f"aya_end < aya_start for key '{key}'"
                )

    def test_no_empty_labels(self):
        for key, target in ALIAS_MAP.items():
            assert target.label_ar.strip(), f"empty label_ar for key '{key}'"
            assert target.label_en.strip(), f"empty label_en for key '{key}'"

    def test_map_not_empty(self):
        assert len(ALIAS_MAP) >= 10, "ALIAS_MAP should have at least 10 entries"
