"""
Round-5 answer-guard regressions over the REAL database.

* ar-canonical-quote-2:183 / ar-imlaei-quote-2:183: an answer quoting the
  opening of 2:183 (canonical Tanzil text from quran_verses) and then the
  first words of the Al-Muyassar chunk verbatim, which end on "فرض الله".
  A verbatim excerpt of the cited tafsir is the source's statement, never the
  model issuing a ruling.
* ar-2:187-rukhsa: Ibn Kathir's opening clause quoted after a reporting lead,
  then a paraphrase of the concession the chunk describes.
* invented promises put on the verse (2:153): "the verse promises… cured of
  every disease / never face illness, debt or sadness again" with a valid
  tafsir citation. The verse-reading path ("the verse promises…") must not
  admit an outcome or an absolute scope the evidence does not carry.

Answers are assembled at runtime from the stored rows; nothing here
hand-types Qur'an or tafsir text. Only the LLM is mocked.
"""
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import text

from app.rag.llm_provider import BaseLLM, LLMResponse
from app.rag.pipeline import RAGPipeline
from app.rag.types import RetrievedChunk

pytestmark = pytest.mark.requires_data("tafsir:2:153", "tafsir:2:183", "tafsir:2:187", "translations")

AR_DIG = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
SOURCES = ["muyassar_ar", "ibn_kathir_ar", "tabari_ar", "baghawi_ar", "qurtubi_ar"]


class _LLM(BaseLLM):
    model = "fake/r5"

    def __init__(self, answer):
        self.answer = answer

    async def generate(self, system_prompt, user_message, max_tokens=2000, temperature=0.3, json_mode=False):
        return LLMResponse(content=self.answer, model=self.model, tokens_used=1)

    async def health_check(self):
        return True


def _words(t, n, start=0):
    return " ".join((t or "").split()[start:start + n])


async def _chunks(session, sura, aya):
    names = {r[0]: (r[1] or "", r[2] or "") for r in (await session.execute(
        text("SELECT id, name_en, name_ar FROM tafseer_sources"))).all()}
    rows = (await session.execute(text(
        "SELECT chunk_id, source_id, sura_no, aya_start, aya_end, content_ar FROM tafseer_chunks "
        "WHERE sura_no = :s AND aya_start <= :a AND COALESCE(aya_end, aya_start) >= :a"), {"s": sura, "a": aya})).all()
    out = [RetrievedChunk(
        chunk_id=r[0], source_id=r[1], source_name=names[r[1]][0], source_name_ar=names[r[1]][1],
        verse_reference=f"{r[2]}:{r[3]}", sura_no=r[2], aya_start=r[3], aya_end=r[4] or r[3],
        content=r[5], content_ar=r[5], content_en=None, relevance_score=0.9)
        for r in rows if r[1] in SOURCES and r[1] in names and r[5]]
    out.sort(key=lambda c: SOURCES.index(c.source_id))
    return out


async def _run(session, question, answer, chunks):
    p = RAGPipeline(session, llm=_LLM(answer))
    p._try_fast_path_verse_query = AsyncMock(return_value=None)
    p._try_fast_path_thematic_query = AsyncMock(return_value=None)
    p.retriever.retrieve = AsyncMock(return_value=list(chunks))
    p._rerank_chunks = lambda c, q, m: c
    return await p.query(question=question, language="ar")


@pytest.fixture
async def session():
    from app.db import database

    async with database.AsyncSessionLocal() as s:
        yield s


def _pick(chunks, source):
    c = next((c for c in chunks if c.source_id == source), None)
    if c is None:
        pytest.skip(f"{source} not loaded")
    return c


async def _verse(session, s, a):
    row = (await session.execute(text(
        "SELECT text_uthmani, text_imlaei FROM quran_verses WHERE sura_no = :s AND aya_no = :a"),
        {"s": s, "a": a})).first()
    if not row or not row[0]:
        pytest.skip("quran_verses not loaded")
    return row


@pytest.mark.asyncio
async def test_ar_canonical_quote_2_183(session):
    chunks = await _chunks(session, 2, 183)
    my = _pick(chunks, "muyassar_ar")
    uth, _iml = await _verse(session, 2, 183)
    refa = "2:183".translate(AR_DIG)
    answer = (f"قال الله تعالى: ﴿{_words(uth, 4)}﴾ [القرآن، {refa}]، ومعناها كما في التفسير الميسر: "
              f"{_words(my.content_ar, 10)} [التفسير الميسر، {refa}].")
    assert _words(my.content_ar, 10).split()[-2:][0].endswith("فرض")  # the excerpt ends on the ruling verb
    r = await _run(session, f"ما تفسير الآية {refa}؟", answer, chunks)
    assert r.status == "answered" and r.answer_kind == "ai_synthesis", (r.status, r.warnings)
    assert "answer_withheld_by_guard" not in r.warnings


@pytest.mark.asyncio
async def test_ar_imlaei_quote_2_183(session):
    chunks = await _chunks(session, 2, 183)
    my = _pick(chunks, "muyassar_ar")
    _uth, iml = await _verse(session, 2, 183)
    refa = "2:183".translate(AR_DIG)
    answer = (f"في قوله «{_words(iml, 4)}» [القرآن، {refa}] بيّن الميسر: "
              f"{_words(my.content_ar, 10)} [الميسر، {refa}].")
    r = await _run(session, f"ما تفسير الآية {refa}؟", answer, chunks)
    assert r.status == "answered" and r.answer_kind == "ai_synthesis", (r.status, r.warnings)


@pytest.mark.asyncio
async def test_ar_2_187_rukhsa(session):
    chunks = await _chunks(session, 2, 187)
    ik = _pick(chunks, "ibn_kathir_ar")
    refa = "2:187".translate(AR_DIG)
    # Ibn Kathir's opening clause verbatim after a reporting lead, then the
    # concession it describes in the answer's own words.
    opening = _words(ik.content_ar.split("،")[0], 12)
    answer = (f"ذكر ابن كثير أن {opening}، فالجماع في ليالي رمضان مباح بعد أن كان محرما بعد النوم "
              f"في أول الإسلام [ابن كثير، {refa}].")
    r = await _run(session, f"ما معنى الآية {refa}؟", answer, chunks)
    assert r.status == "answered" and r.answer_kind == "ai_synthesis", (r.status, r.warnings)


@pytest.mark.asyncio
async def test_own_ruling_after_a_verbatim_excerpt_is_still_withheld(session):
    chunks = await _chunks(session, 2, 183)
    my = _pick(chunks, "muyassar_ar")
    refa = "2:183".translate(AR_DIG)
    answer = (f"ومعناها كما في التفسير الميسر: {_words(my.content_ar, 10)} [التفسير الميسر، {refa}]. "
              f"ويجب عليك أن تصوم ثلاثة أيام من كل شهر [التفسير الميسر، {refa}].")
    r = await _run(session, f"ما تفسير الآية {refa}؟", answer, chunks)
    assert r.status == "no_verified_source" and r.answer_kind == "refusal"


# ------------------------------------------ invented promises on the verse
# The cited chunks (2:153: Muyassar, Ibn Kathir, Tabari, Baghawi, Qurtubi)
# speak of seeking help through patience and prayer and of Allah being with
# the patient; none promises a cure, freedom from illness, debt or sadness.
INVENTED_PROMISES = [
    ("en", "The verse promises that believers who are patient and pray will be cured of every disease "
           "[Al-Tafsir Al-Muyassar, 2:153].", ["cured of every disease"]),
    ("en", "The verse promises that whoever is patient and prays will never face illness, debt or sadness again "
           "[Al-Tafsir Al-Muyassar, 2:153].", ["never face illness"]),
    ("en", "This verse promises that those who are patient and pray will always become wealthy "
           "[Al-Tafsir Al-Muyassar, 2:153].", ["become wealthy"]),
    ("ar", "تعد الآية الصابرين بأنهم يشفون من كل مرض [التفسير الميسر، ٢:١٥٣].", ["يشفون من كل مرض"]),
    ("ar", "تعد الآية من صبر وصلى بأنه لن يصيبه مرض ولا دين ولا حزن أبدا [التفسير الميسر، ٢:١٥٣].",
     ["لن يصيبه مرض"]),
    ("ar", "تبين الآية أن الصابرين المصلين يصبحون أغنياء ولا يفتقرون أبدا [التفسير الميسر، ٢:١٥٣].",
     ["يصبحون أغنياء"]),
]


def _flat_out(t):
    from app.safety.claim_guard import _flat
    return _flat(t)


@pytest.mark.asyncio
@pytest.mark.parametrize("lang,answer,markers", INVENTED_PROMISES)
async def test_invented_promise_on_the_verse_is_neutralised(session, lang, answer, markers):
    chunks = await _chunks(session, 2, 153)
    _pick(chunks, "muyassar_ar")
    q = "What does 2:153 promise?" if lang == "en" else "ماذا تعد الآية ٢:١٥٣؟"
    p = RAGPipeline(session, llm=_LLM(answer))
    p._try_fast_path_verse_query = AsyncMock(return_value=None)
    p._try_fast_path_thematic_query = AsyncMock(return_value=None)
    p.retriever.retrieve = AsyncMock(return_value=list(chunks))
    p._rerank_chunks = lambda c, q, m: c
    r = await p.query(question=q, language=lang)
    refused = r.status != "answered" or r.answer_kind in ("refusal", "notice")
    out = _flat_out(r.answer or "")
    leaked = [m for m in markers if _flat_out(m) in out]
    assert refused or not leaked, (r.status, r.answer_kind, r.warnings, (r.answer or "")[:300])
