"""
API Contract Tests

Validates that API responses match expected schemas.
Ensures no breaking changes to frontend contracts.
"""
import pytest
import sys
sys.path.insert(0, '/home/mhamdan/tadabbur/backend')

from pydantic import ValidationError
from app.api.schemas import (
    Madhab,
    ConceptType,
    DataStatus,
    VerificationStatus,
    ConceptSummary,
    ConceptListResponse,
    ConceptDetailResponse,
    OccurrenceDetail,
    TafsirEvidence,
    VerseReference,
    MiracleSummary,
    MiracleListResponse,
    TafsirEvidenceResponse,
)


class TestMadhabValidation:
    """Test strict madhab validation."""

    def test_valid_madhabs(self):
        """All 4 Sunni madhabs should be valid."""
        valid = ['hanafi', 'maliki', 'shafii', 'hanbali']
        for m in valid:
            assert Madhab(m).value == m

    def test_invalid_madhab_rejected(self):
        """Non-Sunni madhabs should be rejected."""
        invalid = ['jaafari', 'zaidi', 'ibadi', 'salafi', 'unknown']
        for m in invalid:
            with pytest.raises(ValueError):
                Madhab(m)

    def test_tafsir_evidence_madhab_validation(self):
        """TafsirEvidence should reject invalid madhabs."""
        with pytest.raises(ValidationError):
            TafsirEvidence(
                id="test",
                source_id="test_source",
                source_name_ar="تفسير",
                madhab="jaafari",  # Invalid
                verse_ref=VerseReference(sura_no=1, ayah_no=1),
                excerpt_ar="نص التفسير"
            )

    def test_tafsir_evidence_valid_madhab(self):
        """TafsirEvidence should accept valid madhabs."""
        evidence = TafsirEvidence(
            id="test",
            source_id="ibn_kathir_ar",
            source_name_ar="تفسير ابن كثير",
            madhab="shafii",
            verse_ref=VerseReference(sura_no=2, ayah_no=255),
            excerpt_ar="آية الكرسي..."
        )
        assert evidence.madhab == Madhab.SHAFII


class TestConceptSchemas:
    """Test concept response schemas."""

    def test_concept_summary_required_fields(self):
        """ConceptSummary must have all required fields."""
        # Missing label_ar should fail
        with pytest.raises(ValidationError):
            ConceptSummary(
                id="test",
                slug="test-slug",
                label_en="Test",
                type="person"
            )

    def test_concept_summary_valid(self):
        """Valid ConceptSummary should pass."""
        summary = ConceptSummary(
            id="person_musa",
            slug="musa",
            label_ar="موسى",
            label_en="Moses",
            type="person",
            is_curated=True,
            occurrence_count=50
        )
        assert summary.id == "person_musa"
        assert summary.type == ConceptType.PERSON

    def test_concept_list_response(self):
        """ConceptListResponse structure."""
        response = ConceptListResponse(
            concepts=[
                ConceptSummary(
                    id="test",
                    slug="test",
                    label_ar="اختبار",
                    label_en="Test",
                    type="theme"
                )
            ],
            total=1,
            offset=0,
            limit=50
        )
        assert response.ok is True
        assert len(response.concepts) == 1
        assert response.data_status == DataStatus.COMPLETE

    def test_concept_detail_with_occurrences(self):
        """ConceptDetailResponse with occurrences."""
        response = ConceptDetailResponse(
            id="person_musa",
            slug="musa",
            label_ar="موسى عليه السلام",
            label_en="Prophet Moses",
            type="person",
            occurrences=[
                OccurrenceDetail(
                    id=1,
                    concept_id="person_musa",
                    ref_type="ayah",
                    sura_no=2,
                    ayah_start=51,
                    verse_reference="2:51",
                    has_evidence=True,
                    is_verified=True
                )
            ]
        )
        assert response.ok is True
        assert len(response.occurrences) == 1
        assert response.verification_status == VerificationStatus.APPROVED


class TestMiracleSchemas:
    """Test miracle response schemas."""

    def test_miracle_summary(self):
        """MiracleSummary structure."""
        summary = MiracleSummary(
            id="miracle_musa_staff",
            slug="musa-staff",
            label_ar="تحول العصا إلى ثعبان",
            label_en="Staff Turning into Serpent",
            related_persons=[
                ConceptSummary(
                    id="person_musa",
                    slug="musa",
                    label_ar="موسى",
                    label_en="Moses",
                    type="person"
                )
            ],
            occurrence_count=5
        )
        assert len(summary.related_persons) == 1

    def test_miracle_list_response(self):
        """MiracleListResponse structure."""
        response = MiracleListResponse(
            data=[
                MiracleSummary(
                    id="miracle_musa_staff",
                    slug="musa-staff",
                    label_ar="عصا موسى",
                    label_en="Moses Staff"
                )
            ],
            total=1
        )
        assert response.ok is True
        assert response.data_status == DataStatus.COMPLETE


class TestTafsirEvidenceResponse:
    """Test tafsir evidence response schemas."""

    def test_tafsir_evidence_response(self):
        """TafsirEvidenceResponse structure."""
        response = TafsirEvidenceResponse(
            occurrence_id=1,
            concept_id="person_musa",
            verse_ref=VerseReference(sura_no=7, ayah_no=107),
            evidence=[
                TafsirEvidence(
                    id="chunk_1",
                    source_id="ibn_kathir_ar",
                    source_name_ar="تفسير ابن كثير",
                    madhab="shafii",
                    verse_ref=VerseReference(sura_no=7, ayah_no=107),
                    excerpt_ar="فألقى عصاه فإذا هي ثعبان مبين..."
                )
            ],
            madhabs_present=[Madhab.SHAFII],
            madhabs_missing=[Madhab.HANAFI, Madhab.MALIKI, Madhab.HANBALI]
        )
        assert len(response.evidence) == 1
        assert Madhab.SHAFII in response.madhabs_present

    def test_evidence_response_rejects_invalid_madhab(self):
        """Evidence with invalid madhab should fail validation."""
        with pytest.raises(ValidationError):
            TafsirEvidenceResponse(
                occurrence_id=1,
                concept_id="test",
                verse_ref=VerseReference(sura_no=1, ayah_no=1),
                evidence=[
                    TafsirEvidence(
                        id="chunk_1",
                        source_id="invalid",
                        source_name_ar="مصدر غير صحيح",
                        madhab="invalid_madhab",  # Should fail
                        verse_ref=VerseReference(sura_no=1, ayah_no=1),
                        excerpt_ar="text"
                    )
                ]
            )


class TestDataStatusHandling:
    """Test data completeness status."""

    def test_incomplete_data_status(self):
        """Incomplete data should be flagged."""
        response = ConceptDetailResponse(
            id="test",
            slug="test",
            label_ar="اختبار",
            label_en="Test",
            type="theme",
            data_status=DataStatus.INCOMPLETE,
            missing_fields=["description_ar", "tafsir_evidence"]
        )
        assert response.data_status == DataStatus.INCOMPLETE
        assert "description_ar" in response.missing_fields


class TestVerseReferenceValidation:
    """Test verse reference validation."""

    def test_valid_verse_reference(self):
        """Valid verse references should pass."""
        ref = VerseReference(sura_no=2, ayah_no=255)
        assert ref.reference == "2:255"

    def test_invalid_sura_number(self):
        """Sura number must be 1-114."""
        with pytest.raises(ValidationError):
            VerseReference(sura_no=115, ayah_no=1)  # Invalid

        with pytest.raises(ValidationError):
            VerseReference(sura_no=0, ayah_no=1)  # Invalid

    def test_invalid_ayah_number(self):
        """Ayah number must be >= 1."""
        with pytest.raises(ValidationError):
            VerseReference(sura_no=1, ayah_no=0)


def run_tests():
    """Run all contract tests."""
    pytest.main([__file__, '-v', '--tb=short'])


if __name__ == "__main__":
    run_tests()
