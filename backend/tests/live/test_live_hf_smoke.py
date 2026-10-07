"""
Live Hugging Face smoke tests — spend a small amount of HF credit.

Run only when explicitly requested:

    HF_TOKEN=hf_... pytest -m live_hf tests/live -v

Every call is minimal (few tokens / one short batch). If the account's
credits are exhausted the test is skipped with that reason rather than
failing, since that is an account state, not a code defect. All other upstream
errors fail the test.
"""

import asyncio
from pathlib import Path

import pytest

from app.ai.hf_client import HFErrorKind, HFInferenceError, hf_configured

pytestmark = pytest.mark.live_hf

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "audio"
ARABIC = __import__("re").compile(r"[؀-ۿ]")
LATIN = __import__("re").compile(r"[A-Za-z]")


@pytest.fixture(autouse=True)
def _require_token():
    if not hf_configured():
        pytest.skip("HF_TOKEN not configured")


def _call(fn):
    """Run fn(); skip on exhausted credits, re-raise anything else."""
    try:
        return fn()
    except HFInferenceError as err:
        if err.kind == HFErrorKind.QUOTA:
            pytest.skip(f"HF credits/rate limit: {err}")
        raise


def _run(coro_factory):
    return _call(lambda: asyncio.run(coro_factory()))


# ----------------------------------------------------------------------- chat


def test_chat_english():
    from app.rag.llm_provider import get_llm

    r = _run(
        lambda: get_llm().generate(
            system_prompt="Answer in one short English sentence.",
            user_message="What is the name of the first surah of the Quran?",
            max_tokens=40,
            temperature=0.0,
        )
    )
    assert r.content and len(LATIN.findall(r.content)) > len(ARABIC.findall(r.content))
    assert r.provider == "huggingface" and r.model


def test_chat_arabic():
    from app.rag.llm_provider import get_llm

    r = _run(
        lambda: get_llm().generate(
            system_prompt="أجب بجملة عربية قصيرة واحدة فقط.",
            user_message="ما اسم السورة الأولى في المصحف؟",
            max_tokens=40,
            temperature=0.0,
        )
    )
    assert len(ARABIC.findall(r.content)) > len(LATIN.findall(r.content))


def test_unknown_model_maps_to_model_unavailable():
    from app.rag.llm_provider import HuggingFaceLLM

    llm = HuggingFaceLLM(model="tadabbur-ci/this-model-does-not-exist")
    with pytest.raises(HFInferenceError) as info:
        asyncio.run(llm.generate("s", "u", max_tokens=1))
    if info.value.kind == HFErrorKind.QUOTA:
        pytest.skip("HF credits/rate limit")
    assert info.value.kind in (HFErrorKind.MODEL_UNAVAILABLE, HFErrorKind.BAD_REQUEST)


# ------------------------------------------------------- embeddings / rerank


def test_embeddings_match_index_dimension_and_rank_sensibly():
    from app.ai.embeddings import HFEmbeddingModel
    from app.core.config import settings

    vecs = _call(
        lambda: HFEmbeddingModel().encode(
            [
                "query: الصبر عند المصيبة",
                "passage: الصبر حبس النفس عن الجزع عند المصيبة",
                "passage: أحكام البيع والشراء في الأسواق",
            ]
        )
    )
    assert vecs.shape == (3, settings.embedding_dimension)
    assert float(vecs[0] @ vecs[1]) > float(vecs[0] @ vecs[2])


def test_reranker_orders_relevant_passage_first():
    from app.rag.reranker import _hf_rerank_scores

    scores = _call(
        lambda: _hf_rerank_scores(
            "ما معنى الصبر؟",
            [
                "الزكاة ركن من أركان الإسلام",
                "الصبر حبس النفس على طاعة الله وعن معصيته",
            ],
        )
    )
    assert scores[1] > scores[0]


def test_zero_shot_emotion():
    from app.services.emotion_classifier import NLIEmotionClassifier

    clf = NLIEmotionClassifier()
    scored = _call(lambda: clf._zero_shot("I lost my father last week and I miss him so much"))
    best = max(scored, key=lambda p: p[1])[0]
    assert best in ("grief", "sadness")


# --------------------------------------------------------------- speech-to-text


def test_speech_to_text_on_recitation_fixture():
    from app.stt.providers.huggingface import HuggingFaceSTTProvider

    audio = FIXTURES / "112_001_ikhlas_1.mp3"
    if not audio.exists():
        pytest.skip("audio fixture missing")
    result = _call(lambda: HuggingFaceSTTProvider().transcribe(str(audio)))
    assert "الله" in result.full_text
    assert result.get_all_words(), "word timestamps expected"


# ----------------------------------------------------------- grounded RAG (AR/EN)


async def _evidence_for(sura: int, ayat: range):
    """Real retrieved-evidence stand-in: stored tafsir chunks for these ayat."""
    from sqlalchemy import select
    from app.db.database import AsyncSessionLocal
    from app.models.tafseer import TafseerChunk, TafseerSource
    from app.rag.types import RetrievedChunk

    async with AsyncSessionLocal() as s:
        rows = (
            await s.execute(
                select(TafseerChunk, TafseerSource)
                .join(TafseerSource, TafseerChunk.source_id == TafseerSource.id)
                .where(TafseerChunk.sura_no == sura, TafseerChunk.aya_start.in_(list(ayat)))
                .limit(6)
            )
        ).all()
    return [
        RetrievedChunk(
            chunk_id=c.chunk_id,
            source_id=c.source_id,
            source_name=src.name_en,
            source_name_ar=src.name_ar,
            verse_reference=c.verse_reference,
            sura_no=c.sura_no,
            aya_start=c.aya_start,
            aya_end=c.aya_end,
            content=c.content_ar or c.content_en or "",
            content_ar=c.content_ar,
            content_en=c.content_en,
            relevance_score=0.9,
        )
        for c, src in rows
    ]


@pytest.mark.parametrize(
    "language,question",
    [
        ("en", "What does Surah Al-Ikhlas say about Allah?"),
        ("ar", "ماذا تقول سورة الإخلاص عن الله تعالى؟"),
    ],
)
def test_grounded_rag_answer_cites_only_retrieved_chunks(language, question):
    from unittest.mock import AsyncMock
    from app.db.database import AsyncSessionLocal
    from app.rag.pipeline import RAGPipeline

    async def run():
        chunks = await _evidence_for(112, range(1, 5))
        if len(chunks) < 2:
            pytest.skip("no seeded tafsir for 112:1-4")
        async with AsyncSessionLocal() as session:
            p = RAGPipeline(session)
            p.max_tokens = 400
            p._try_fast_path_verse_query = AsyncMock(return_value=None)
            p._try_fast_path_thematic_query = AsyncMock(return_value=None)
            p.retriever.retrieve = AsyncMock(return_value=chunks)
            p._rerank_chunks = lambda c, q, m: c
            return await p.query(question=question, language=language), chunks

    result, chunks = _run(run)
    if result.status == "ai_unavailable":
        pytest.skip(f"HF unavailable: {result.degradation_reasons}")
    evidence_ids = {c.chunk_id for c in chunks}
    assert {c.chunk_id for c in result.citations} <= evidence_ids
    if result.status == "answered":
        assert result.answer_kind == "ai_synthesis" and result.citations
        letters = ARABIC if language == "ar" else LATIN
        other = LATIN if language == "ar" else ARABIC
        assert len(letters.findall(result.answer)) > len(other.findall(result.answer))
    else:
        assert result.answer_kind == "refusal" and not result.citations
