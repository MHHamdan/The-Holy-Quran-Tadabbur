"""
Phase C — Quran Question Classifier Tests

Tests for QuranQuestionClassifier: intent detection, language detection,
routing decisions, risk levels, and pipeline integration (pre-generation gate).

Reference: "تجربة تفسير القرآن الكريم بالذكاء الاصطناعي"
           Prof. Dr. Abdulrahman Al-Shehri
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.safety.quran_question_classifier import (
    QuranQuestionClassifier,
    QuestionClassification,
    quran_question_classifier,
    classifier_intent_to_query_intent,
    INTENT_FATWA_LIKE,
    INTENT_SCIENTIFIC_MIRACLE,
    INTENT_QIRAAT,
    INTENT_MORPHOLOGY,
    INTENT_IRAB,
    INTENT_VOCABULARY,
    INTENT_MUNASABAH,
    INTENT_SIMILARITY,
    INTENT_STORY,
    INTENT_THEMATIC_TAFSIR,
    INTENT_TAFSIR_SUMMARY,
    INTENT_GENERAL,
    INTENT_NEEDS_CLARIFICATION,
    INTENT_UNSUPPORTED,
    ROUTE_REFUSAL,
    ROUTE_RAG,
    ROUTE_STORIES,
    ROUTE_SIMILARITY,
    ROUTE_CLARIFICATION,
    RISK_HIGH,
    RISK_MEDIUM,
    RISK_LOW,
    FATWA_REFUSAL_EN,
    FATWA_REFUSAL_AR,
    SCIENTIFIC_CAUTION_EN,
    SCIENTIFIC_CAUTION_AR,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def clf() -> QuranQuestionClassifier:
    return QuranQuestionClassifier()


# ---------------------------------------------------------------------------
# 1. Fatwa-like detection (Arabic)
# ---------------------------------------------------------------------------

class TestFatwaArabic:
    def test_ma_hukm_arabic(self, clf):
        result = clf.classify("ما حكم الغيبة في الإسلام؟")
        assert result.intent == INTENT_FATWA_LIKE

    def test_hal_yajuz_arabic(self, clf):
        result = clf.classify("هل يجوز الاستثمار في البنوك؟")
        assert result.intent == INTENT_FATWA_LIKE

    def test_aftini_arabic(self, clf):
        result = clf.classify("أفتني في مسألة الصيام")
        assert result.intent == INTENT_FATWA_LIKE

    def test_halal_haram_arabic(self, clf):
        result = clf.classify("حلال أم حرام تناول هذا الطعام؟")
        assert result.intent == INTENT_FATWA_LIKE

    def test_fatwa_blocks_generation_arabic(self, clf):
        result = clf.classify("ما حكم هذا الفعل؟")
        assert result.allowed_to_generate is False
        assert result.route_to == ROUTE_REFUSAL
        assert result.risk_level == RISK_HIGH

    def test_fatwa_arabic_includes_bilingual_warning(self, clf):
        result = clf.classify("هل يجوز لي ذلك؟")
        assert FATWA_REFUSAL_EN in result.warnings
        assert FATWA_REFUSAL_AR in result.warnings


# ---------------------------------------------------------------------------
# 2. Fatwa-like detection (English)
# ---------------------------------------------------------------------------

class TestFatwaEnglish:
    def test_is_it_permissible(self, clf):
        result = clf.classify("Is it permissible to invest in cryptocurrency?")
        assert result.intent == INTENT_FATWA_LIKE

    def test_is_it_haram(self, clf):
        result = clf.classify("Is it haram to listen to music?")
        assert result.intent == INTENT_FATWA_LIKE

    def test_is_it_halal(self, clf):
        result = clf.classify("Is it halal to eat this type of food?")
        assert result.intent == INTENT_FATWA_LIKE

    def test_give_me_a_fatwa(self, clf):
        result = clf.classify("Give me a fatwa about working in finance.")
        assert result.intent == INTENT_FATWA_LIKE

    def test_what_is_the_ruling(self, clf):
        result = clf.classify("What is the ruling on fasting on Saturdays?")
        assert result.intent == INTENT_FATWA_LIKE

    def test_fatwa_blocks_generation_english(self, clf):
        result = clf.classify("Is it forbidden to miss Friday prayer?")
        assert result.allowed_to_generate is False
        assert result.route_to == ROUTE_REFUSAL
        assert result.risk_level == RISK_HIGH


# ---------------------------------------------------------------------------
# 3. Scientific miracle claim detection
# ---------------------------------------------------------------------------

class TestScientificMiracle:
    def test_arabic_scientific_miracle_keyword(self, clf):
        result = clf.classify("ما الإعجاز العلمي في سورة الذاريات؟")
        assert result.intent == INTENT_SCIENTIFIC_MIRACLE

    def test_english_big_bang(self, clf):
        result = clf.classify("Does 51:47 prove the Big Bang theory?")
        assert result.intent == INTENT_SCIENTIFIC_MIRACLE

    def test_english_scientific_miracle(self, clf):
        result = clf.classify("Explain the scientific miracle in Surah 21.")
        assert result.intent == INTENT_SCIENTIFIC_MIRACLE

    def test_scientific_miracle_requires_scholar_review(self, clf):
        result = clf.classify("Does the Quran mention embryology?")
        assert result.intent == INTENT_SCIENTIFIC_MIRACLE
        assert result.requires_scholar_review is True

    def test_scientific_miracle_allowed_to_generate(self, clf):
        # Not blocked — but carries caution warnings
        result = clf.classify("Science proves what this ayah mentioned.")
        assert result.allowed_to_generate is True

    def test_scientific_miracle_has_caution_warnings(self, clf):
        result = clf.classify("The Quran predicted modern astronomy.")
        assert SCIENTIFIC_CAUTION_EN in result.warnings
        assert SCIENTIFIC_CAUTION_AR in result.warnings

    def test_scientific_miracle_risk_is_high(self, clf):
        result = clf.classify("Scientifically proven facts in Quran.")
        assert result.risk_level == RISK_HIGH


# ---------------------------------------------------------------------------
# 4. Tafsir summary detection
# ---------------------------------------------------------------------------

class TestTafsirSummary:
    def test_arabic_tafsir_keyword(self, clf):
        result = clf.classify("ما تفسير سورة الفاتحة؟")
        assert result.intent == INTENT_TAFSIR_SUMMARY

    def test_arabic_sharh_keyword(self, clf):
        result = clf.classify("اشرح لي الآية الخامسة من سورة الكهف")
        assert result.intent == INTENT_TAFSIR_SUMMARY

    def test_english_tafsir_keyword(self, clf):
        result = clf.classify("What is the tafsir of 2:255?")
        assert result.intent == INTENT_TAFSIR_SUMMARY

    def test_english_explain_ayah(self, clf):
        result = clf.classify("Please explain this ayah for me.")
        assert result.intent == INTENT_TAFSIR_SUMMARY

    def test_english_meaning_of_verse(self, clf):
        result = clf.classify("What does this verse mean?")
        assert result.intent == INTENT_TAFSIR_SUMMARY

    def test_tafsir_allowed_to_generate(self, clf):
        result = clf.classify("Explain the meaning of the opening chapter.")
        assert result.allowed_to_generate is True
        assert result.route_to == ROUTE_RAG


# ---------------------------------------------------------------------------
# 5. Vocabulary meaning detection
# ---------------------------------------------------------------------------

class TestVocabularyMeaning:
    def test_arabic_vocabulary_keyword(self, clf):
        result = clf.classify("ما معنى كلمة التقوى في القرآن؟")
        assert result.intent == INTENT_VOCABULARY

    def test_arabic_gharib_quran(self, clf):
        result = clf.classify("ما غريب القرآن في هذه الآية؟")
        assert result.intent == INTENT_VOCABULARY

    def test_english_meaning_of_word(self, clf):
        result = clf.classify("What is the meaning of the word 'ghayb' in Quranic Arabic?")
        assert result.intent == INTENT_VOCABULARY

    def test_english_quranic_word(self, clf):
        result = clf.classify("Explain this difficult quranic word.")
        assert result.intent == INTENT_VOCABULARY


# ---------------------------------------------------------------------------
# 6. I'rab detection
# ---------------------------------------------------------------------------

class TestIrab:
    def test_arabic_irab_keyword(self, clf):
        result = clf.classify("ما إعراب كلمة الرحمن في الآية الأولى؟")
        assert result.intent == INTENT_IRAB

    def test_arabic_arib_keyword(self, clf):
        result = clf.classify("أعرب الجملة الأولى من سورة البقرة")
        assert result.intent == INTENT_IRAB

    def test_english_irab_keyword(self, clf):
        result = clf.classify("Show me the i'rab for this verse.")
        assert result.intent == INTENT_IRAB

    def test_english_parse_word(self, clf):
        result = clf.classify("Can you parse this word from the Quran?")
        assert result.intent == INTENT_IRAB

    def test_irab_does_not_invent_parsing(self, clf):
        # i'rab queries are routed to RAG (no dedicated source yet) with warning
        result = clf.classify("أعرب سورة الفاتحة كاملة")
        assert result.intent == INTENT_IRAB
        assert result.allowed_to_generate is True
        assert len(result.warnings) > 0


# ---------------------------------------------------------------------------
# 7. Morphology detection
# ---------------------------------------------------------------------------

class TestMorphology:
    def test_arabic_tasreef(self, clf):
        result = clf.classify("ما تصريف كلمة يعلمون؟")
        assert result.intent == INTENT_MORPHOLOGY

    def test_arabic_root(self, clf):
        result = clf.classify("ما الجذر اللغوي لكلمة مؤمنين؟")
        assert result.intent == INTENT_MORPHOLOGY

    def test_english_morphology(self, clf):
        result = clf.classify("What is the morphology of this Quranic word?")
        assert result.intent == INTENT_MORPHOLOGY

    def test_english_word_root(self, clf):
        result = clf.classify("What is the word root of 'rahman'?")
        assert result.intent == INTENT_MORPHOLOGY


# ---------------------------------------------------------------------------
# 8. Qira'at detection
# ---------------------------------------------------------------------------

class TestQiraat:
    def test_arabic_qiraat(self, clf):
        result = clf.classify("ما القراءات المتواترة لهذه الآية؟")
        assert result.intent == INTENT_QIRAAT

    def test_english_qiraat(self, clf):
        result = clf.classify("What are the qiraat variants for this verse?")
        assert result.intent == INTENT_QIRAAT

    def test_qiraat_risk_medium(self, clf):
        result = clf.classify("Tell me about the recitation variants of Surah Al-Fatiha.")
        assert result.intent == INTENT_QIRAAT
        assert result.risk_level == RISK_MEDIUM


# ---------------------------------------------------------------------------
# 9. Thematic tafsir detection
# ---------------------------------------------------------------------------

class TestThematicTafsir:
    def test_arabic_thematic(self, clf):
        result = clf.classify("ما آيات الصبر في القرآن الكريم؟")
        assert result.intent == INTENT_THEMATIC_TAFSIR

    def test_arabic_tafsir_mawdui(self, clf):
        result = clf.classify("كيف تناول القرآن موضوع الرحمة؟")
        assert result.intent == INTENT_THEMATIC_TAFSIR

    def test_english_verses_about(self, clf):
        result = clf.classify("Show me verses about patience in the Quran.")
        assert result.intent == INTENT_THEMATIC_TAFSIR

    def test_english_what_does_quran_say_about(self, clf):
        result = clf.classify("What does the Quran say about prayer?")
        assert result.intent == INTENT_THEMATIC_TAFSIR


# ---------------------------------------------------------------------------
# 10. Munasabah detection
# ---------------------------------------------------------------------------

class TestMunasabah:
    def test_arabic_munasabah(self, clf):
        result = clf.classify("ما المناسبة بين أول سورة البقرة وآخرها؟")
        assert result.intent == INTENT_MUNASABAH

    def test_arabic_relationship(self, clf):
        result = clf.classify("ما العلاقة بين الآيات في هذه السورة؟")
        assert result.intent == INTENT_MUNASABAH

    def test_english_relationship_between_ayahs(self, clf):
        result = clf.classify("What is the relationship between these ayahs?")
        assert result.intent == INTENT_MUNASABAH

    def test_munasabah_requires_scholar_review(self, clf):
        result = clf.classify("What is the contextual relationship between Surah 1 and 2?")
        assert result.intent == INTENT_MUNASABAH
        assert result.requires_scholar_review is True


# ---------------------------------------------------------------------------
# 11. Story detection
# ---------------------------------------------------------------------------

class TestStory:
    def test_arabic_qissa(self, clf):
        result = clf.classify("ما قصة سيدنا موسى في القرآن؟")
        assert result.intent == INTENT_STORY

    def test_arabic_people_of(self, clf):
        result = clf.classify("من هم قوم عاد في القرآن؟")
        assert result.intent == INTENT_STORY

    def test_english_story_of(self, clf):
        result = clf.classify("Tell me the story of Prophet Yusuf.")
        assert result.intent == INTENT_STORY

    def test_story_routes_to_stories(self, clf):
        result = clf.classify("What is the Quran story about the companions of the cave?")
        assert result.intent == INTENT_STORY
        assert result.route_to == ROUTE_STORIES


# ---------------------------------------------------------------------------
# 12. Similarity detection
# ---------------------------------------------------------------------------

class TestSimilarity:
    def test_arabic_similar_verses(self, clf):
        result = clf.classify("ما الآيات المشابهة لهذه الآية؟")
        assert result.intent == INTENT_SIMILARITY

    def test_english_similar_verses(self, clf):
        result = clf.classify("Show me similar verses to 2:255.")
        assert result.intent == INTENT_SIMILARITY

    def test_similarity_routes_to_similarity(self, clf):
        result = clf.classify("Find related ayahs for this verse.")
        assert result.intent == INTENT_SIMILARITY
        assert result.route_to == ROUTE_SIMILARITY


# ---------------------------------------------------------------------------
# 13. Needs clarification
# ---------------------------------------------------------------------------

class TestNeedsClarification:
    def test_single_word(self, clf):
        result = clf.classify("explain")
        assert result.intent == INTENT_NEEDS_CLARIFICATION

    def test_two_words(self, clf):
        result = clf.classify("quran meaning")
        assert result.intent == INTENT_NEEDS_CLARIFICATION

    def test_clarification_blocks_generation(self, clf):
        result = clf.classify("help me")
        assert result.allowed_to_generate is False
        assert result.route_to == ROUTE_CLARIFICATION


# ---------------------------------------------------------------------------
# 14. Unsupported / off-topic
# ---------------------------------------------------------------------------

class TestUnsupported:
    def test_stock_market_query(self, clf):
        result = clf.classify("What is the stock market forecast for today?")
        assert result.intent == INTENT_UNSUPPORTED
        assert result.allowed_to_generate is False

    def test_recipe_query(self, clf):
        result = clf.classify("Give me a recipe for chocolate cake.")
        assert result.intent == INTENT_UNSUPPORTED

    def test_unsupported_routes_to_refusal(self, clf):
        result = clf.classify("Tell me about the latest bitcoin price.")
        assert result.intent == INTENT_UNSUPPORTED
        assert result.route_to == ROUTE_REFUSAL


# ---------------------------------------------------------------------------
# 15. Language detection
# ---------------------------------------------------------------------------

class TestLanguageDetection:
    def test_arabic_only(self, clf):
        result = clf.classify("ما تفسير سورة الإخلاص؟")
        assert result.language == "ar"

    def test_english_only(self, clf):
        result = clf.classify("What is the meaning of Surah Al-Ikhlas?")
        assert result.language == "en"

    def test_mixed_arabic_english(self, clf):
        result = clf.classify("ما معنى Surah Al-Fatiha?")
        assert result.language in ("ar", "mixed")


# ---------------------------------------------------------------------------
# 16. classifier_intent_to_query_intent mapping
# ---------------------------------------------------------------------------

class TestIntentMapping:
    def test_fatwa_maps_to_ruling(self):
        assert classifier_intent_to_query_intent(INTENT_FATWA_LIKE) == "ruling"

    def test_scientific_miracle_maps_to_verse_meaning(self):
        assert classifier_intent_to_query_intent(INTENT_SCIENTIFIC_MIRACLE) == "verse_meaning"

    def test_story_maps_to_story_exploration(self):
        assert classifier_intent_to_query_intent(INTENT_STORY) == "story_exploration"

    def test_thematic_maps_to_theme_search(self):
        assert classifier_intent_to_query_intent(INTENT_THEMATIC_TAFSIR) == "theme_search"

    def test_irab_maps_to_linguistic(self):
        assert classifier_intent_to_query_intent(INTENT_IRAB) == "linguistic"

    def test_morphology_maps_to_linguistic(self):
        assert classifier_intent_to_query_intent(INTENT_MORPHOLOGY) == "linguistic"

    def test_unsupported_maps_to_unknown(self):
        assert classifier_intent_to_query_intent(INTENT_UNSUPPORTED) == "unknown"

    def test_unknown_intent_maps_to_verse_meaning_default(self):
        assert classifier_intent_to_query_intent("not_a_real_intent") == "verse_meaning"


# ---------------------------------------------------------------------------
# 17. Module-level singleton
# ---------------------------------------------------------------------------

class TestSingleton:
    def test_singleton_importable(self):
        assert quran_question_classifier is not None

    def test_singleton_is_classifier(self):
        assert isinstance(quran_question_classifier, QuranQuestionClassifier)


# ---------------------------------------------------------------------------
# 18. Result schema validation
# ---------------------------------------------------------------------------

class TestResultSchema:
    def test_result_is_dataclass(self, clf):
        result = clf.classify("What is tafsir of Al-Fatiha?")
        assert isinstance(result, QuestionClassification)

    def test_result_has_all_fields(self, clf):
        result = clf.classify("Explain this verse.")
        assert hasattr(result, "intent")
        assert hasattr(result, "language")
        assert hasattr(result, "risk_level")
        assert hasattr(result, "requires_source")
        assert hasattr(result, "requires_scholar_review")
        assert hasattr(result, "allowed_to_generate")
        assert hasattr(result, "route_to")
        assert hasattr(result, "warnings")

    def test_fatwa_requires_source(self, clf):
        result = clf.classify("Is it halal to do this?")
        assert result.requires_source is True

    def test_scientific_miracle_requires_source(self, clf):
        result = clf.classify("Does this verse prove the Big Bang?")
        assert result.requires_source is True


# ---------------------------------------------------------------------------
# 19. Pipeline integration — fatwa never reaches LLM (unit-level)
# ---------------------------------------------------------------------------

class TestPipelinePreClassify:
    """
    Verify that _pre_classify() in the pipeline returns a safe refusal for
    fatwa queries without calling the LLM or retriever.
    """

    def _make_pipeline(self):
        from app.rag.pipeline import RAGPipeline
        mock_session = MagicMock()
        pipeline = RAGPipeline.__new__(RAGPipeline)
        pipeline.session = mock_session
        # Patch retriever and validator so we don't need a DB
        pipeline.retriever = MagicMock()
        pipeline.validator = MagicMock()
        from app.core.config import settings
        pipeline.settings = settings
        return pipeline

    def test_fatwa_en_returns_refusal(self):
        from app.rag.pipeline import RAGPipeline
        pipeline = self._make_pipeline()
        result = pipeline._pre_classify(
            question="Is it haram to invest in bonds?",
            language="en",
            session_id=None,
        )
        assert result is not None
        assert result.status == "no_verified_source"
        assert result.confidence == 0.0
        assert result.intent == INTENT_FATWA_LIKE

    def test_fatwa_ar_returns_refusal(self):
        from app.rag.pipeline import RAGPipeline
        pipeline = self._make_pipeline()
        result = pipeline._pre_classify(
            question="ما حكم الاستثمار في الأسهم؟",
            language="ar",
            session_id=None,
        )
        assert result is not None
        assert result.status == "no_verified_source"
        assert result.intent == INTENT_FATWA_LIKE

    def test_scientific_miracle_passes_through(self):
        from app.rag.pipeline import RAGPipeline
        pipeline = self._make_pipeline()
        result = pipeline._pre_classify(
            question="Does this verse prove the Big Bang?",
            language="en",
            session_id=None,
        )
        # Allowed to generate — _pre_classify returns None (pipeline continues)
        assert result is None

    def test_normal_tafsir_passes_through(self):
        from app.rag.pipeline import RAGPipeline
        pipeline = self._make_pipeline()
        result = pipeline._pre_classify(
            question="Explain the meaning of Surah Al-Fatiha.",
            language="en",
            session_id=None,
        )
        assert result is None

    def test_clarification_returns_needs_clarification_status(self):
        from app.rag.pipeline import RAGPipeline
        pipeline = self._make_pipeline()
        result = pipeline._pre_classify(
            question="help",
            language="en",
            session_id=None,
        )
        assert result is not None
        assert result.status == "needs_clarification"

    def test_unsupported_returns_no_verified_source(self):
        from app.rag.pipeline import RAGPipeline
        pipeline = self._make_pipeline()
        result = pipeline._pre_classify(
            question="Give me a recipe for chocolate cake.",
            language="en",
            session_id=None,
        )
        assert result is not None
        assert result.status == "no_verified_source"
