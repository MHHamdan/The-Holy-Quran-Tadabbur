"""
AI-powered quiz question generator — grounded in tafsir text.

Retrieves tafseer_chunks for the requested surah, then asks the LLM
to produce MCQ questions whose answers are derived ONLY from that text.
This prevents hallucination: every question must be answerable from the
supplied context, not from general training knowledge.
"""
import json
import logging
import re
import time
from typing import Any  # used in _parse_llm_output return type

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import get_async_session
from app.models.tafseer import TafseerChunk
from app.rag.llm_provider import get_llm
from app.services.tafseer_api import get_tafseer_client

logger = logging.getLogger(__name__)
router = APIRouter()

# Maximum combined tafsir context fed to the LLM (chars)
_MAX_CONTEXT_CHARS = 6000
# Maximum questions per request
_MAX_QUESTIONS = 5


# ─── Request / Response models ─────────────────────────────────────────────────

class GenerateQuestionsRequest(BaseModel):
    surah: int = Field(..., ge=1, le=114, description="Surah number (1-114)")
    count: int = Field(3, ge=1, le=_MAX_QUESTIONS, description="How many questions to generate")
    lang: str = Field("ar", description="Language for questions: 'ar' or 'en'")

    @field_validator("lang")
    @classmethod
    def validate_lang(cls, v: str) -> str:
        if v not in ("ar", "en"):
            raise ValueError("lang must be 'ar' or 'en'")
        return v


class GeneratedOption(BaseModel):
    text: str
    isCorrect: bool


class GeneratedQuestion(BaseModel):
    id: str
    question: str
    options: list[GeneratedOption]
    explanation: str
    surahRef: int
    difficulty: str = "medium"
    category: str = "tafsir_ai"
    isAI: bool = True


class GenerateQuestionsResponse(BaseModel):
    questions: list[GeneratedQuestion]
    surah: int
    sourceChunks: int
    latency_ms: int


# ─── MCQ Generation Prompt ────────────────────────────────────────────────────

_SYSTEM_PROMPT_AR = """أنت معلم متخصص في علوم القرآن الكريم. مهمتك إنشاء أسئلة اختيار من متعدد (MCQ) تعليمية.

قواعد صارمة:
1. أنشئ الأسئلة فقط من النص الموفّر — لا تستخدم معلوماتك العامة.
2. لكل سؤال 4 خيارات، إجابة صحيحة واحدة فقط.
3. اجعل الخيارات الخاطئة معقولة (وليست مضللة بشكل واضح).
4. أضف شرحاً موجزاً للإجابة الصحيحة.
5. أخرج JSON صحيحاً فقط — بدون أي نص إضافي.

صيغة الإخراج (JSON فقط):
{
  "questions": [
    {
      "question": "نص السؤال",
      "options": ["الخيار أ", "الخيار ب", "الخيار ج", "الخيار د"],
      "correct": 0,
      "explanation": "شرح موجز للإجابة الصحيحة"
    }
  ]
}"""

_SYSTEM_PROMPT_EN = """You are a Quranic studies educator. Your task is to generate educational MCQ quiz questions.

Strict rules:
1. Generate questions ONLY from the provided text — do not use general knowledge.
2. Each question has exactly 4 options, only one correct answer.
3. Make wrong options plausible (not obviously misleading).
4. Include a brief explanation of the correct answer.
5. Output valid JSON only — no additional text.

Output format (JSON only):
{
  "questions": [
    {
      "question": "Question text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct": 0,
      "explanation": "Brief explanation of the correct answer"
    }
  ]
}"""


def _build_user_message(context: str, surah: int, count: int, lang: str) -> str:
    if lang == "ar":
        return (
            f"بناءً على تفسير سورة رقم {surah} التالي، أنشئ {count} أسئلة اختيار متعدد:\n\n"
            f"--- النص ---\n{context}\n--- نهاية النص ---\n\n"
            f"أنشئ {count} أسئلة من هذا النص فقط."
        )
    return (
        f"Based on the following tafsir of Surah {surah}, generate {count} MCQ questions:\n\n"
        f"--- TEXT ---\n{context}\n--- END TEXT ---\n\n"
        f"Generate {count} questions from this text only."
    )


# ─── Helper: fetch & truncate tafsir context for a surah ──────────────────────

async def _fetch_surah_context(
    session: AsyncSession,
    surah: int,
    lang: str,
    max_chars: int = _MAX_CONTEXT_CHARS,
) -> tuple[str, int]:
    """Return (context_text, num_chunks).
    Tries DB-seeded chunks first; falls back to alquran.cloud external API."""
    primary_field = "content_ar" if lang == "ar" else "content_en"
    fallback_field = "content_en" if lang == "ar" else "content_ar"

    stmt = (
        select(TafseerChunk)
        .where(TafseerChunk.sura_no == surah)
        .order_by(TafseerChunk.aya_start)
        .limit(40)
    )
    result = await session.execute(stmt)
    db_chunks = result.scalars().all()

    parts: list[str] = []
    total = 0

    if db_chunks:
        for chunk in db_chunks:
            text = getattr(chunk, primary_field, None) or getattr(chunk, fallback_field, None) or ""
            if not text.strip():
                continue
            ref = f"{chunk.sura_no}:{chunk.aya_start}"
            if chunk.aya_start != chunk.aya_end:
                ref += f"-{chunk.aya_end}"
            snippet = f"[{ref}] {text.strip()}"
            if total + len(snippet) > max_chars:
                remaining = max_chars - total
                if remaining > 80:
                    parts.append(snippet[:remaining])
                break
            parts.append(snippet)
            total += len(snippet) + 1
    else:
        # Fall back to alquran.cloud — ar.muyassar for Arabic, en.sahih for English
        edition = "ar.muyassar" if lang == "ar" else "en.sahih"
        client = get_tafseer_client()
        verses = await client.get_surah_tafseer(surah, edition)
        for v in verses:
            if not v.text.strip():
                continue
            snippet = f"[{surah}:{v.ayah}] {v.text.strip()}"
            if total + len(snippet) > max_chars:
                remaining = max_chars - total
                if remaining > 80:
                    parts.append(snippet[:remaining])
                break
            parts.append(snippet)
            total += len(snippet) + 1

    return "\n\n".join(parts), len(parts)


# ─── Helper: parse LLM JSON output ───────────────────────────────────────────

def _parse_llm_output(raw: str, surah: int, count: int) -> list[dict[str, Any]]:
    """Extract JSON from LLM output even if it contains extra text."""
    # Strip markdown code fences
    cleaned = re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()
    # Find first { to last }
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON object found in LLM output")
    json_str = cleaned[start:end]
    data = json.loads(json_str)
    raw_questions = data.get("questions", [])
    if not isinstance(raw_questions, list):
        raise ValueError("'questions' is not a list")

    result = []
    for i, q in enumerate(raw_questions[:count]):
        question = q.get("question", "").strip()
        options_raw = q.get("options", [])
        correct_idx = int(q.get("correct", 0))
        explanation = q.get("explanation", "").strip()

        if not question or len(options_raw) < 2:
            continue
        if correct_idx >= len(options_raw):
            correct_idx = 0

        options = [
            {"text": str(opt).strip(), "isCorrect": (j == correct_idx)}
            for j, opt in enumerate(options_raw[:4])
        ]

        result.append({
            "id": f"ai_{surah}_{int(time.time())}_{i}",
            "question": question,
            "options": options,
            "explanation": explanation,
            "surahRef": surah,
            "difficulty": "medium",
            "category": "tafsir_ai",
            "isAI": True,
        })

    return result


# ─── Endpoint ─────────────────────────────────────────────────────────────────

@router.post(
    "/generate-questions",
    response_model=GenerateQuestionsResponse,
    summary="Generate AI quiz questions grounded in tafsir for a given surah",
)
async def generate_questions(
    req: GenerateQuestionsRequest,
    session: AsyncSession = Depends(get_async_session),
) -> GenerateQuestionsResponse:
    t0 = time.monotonic()

    # 1. Fetch tafsir context
    context, num_chunks = await _fetch_surah_context(session, req.surah, req.lang)
    if not context:
        raise HTTPException(
            status_code=503,
            detail=f"Could not retrieve tafsir text for surah {req.surah}. Check external API availability.",
        )

    # 2. Build prompt
    system = _SYSTEM_PROMPT_AR if req.lang == "ar" else _SYSTEM_PROMPT_EN
    user_msg = _build_user_message(context, req.surah, req.count, req.lang)

    # 3. Call LLM — use fast model (14b) for quiz generation, lower latency
    fast_model = getattr(settings, "ollama_model_fast", "qwen2.5:14b")
    llm = get_llm(ollama_model=fast_model)
    try:
        llm_resp = await llm.generate(
            system_prompt=system,
            user_message=user_msg,
            max_tokens=1500,
            temperature=0.4,
        )
    except Exception as exc:
        logger.error("LLM generation failed for surah %d: %s", req.surah, exc)
        raise HTTPException(status_code=503, detail="AI generation temporarily unavailable")

    # 4. Parse output
    try:
        questions = _parse_llm_output(llm_resp.content, req.surah, req.count)
    except Exception as exc:
        logger.error("Failed to parse LLM output for surah %d: %s\nRaw: %s", req.surah, exc, llm_resp.content[:500])
        raise HTTPException(status_code=502, detail="AI returned an unexpected format. Please try again.")

    if not questions:
        raise HTTPException(status_code=502, detail="AI could not generate questions for this surah. Please try again.")

    latency = int((time.monotonic() - t0) * 1000)
    logger.info("Generated %d AI questions for surah %d in %dms", len(questions), req.surah, latency)

    return GenerateQuestionsResponse(
        questions=[GeneratedQuestion(**q) for q in questions],
        surah=req.surah,
        sourceChunks=num_chunks,
        latency_ms=latency,
    )
