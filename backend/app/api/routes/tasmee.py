"""
API Routes for Tasmeeʿ (Memorization) feature.

This module provides endpoints for:
1. Session management (create, read, complete, delete)
2. Audio transcription (single upload and WebSocket streaming)
3. Word-by-word alignment with possible-slip detection
4. Progress statistics

Speech-to-text runs on Hugging Face Inference Providers (hosted Whisper,
HF_STT_MODEL) from the backend; the HF token never reaches the client.

Access model: sessions are addressed by an unguessable ``public_id`` and every
call after creation must present the per-session client token returned once
by ``POST /sessions`` (``X-Tasmee-Token`` header, or the first WebSocket
frame ``{"type": "auth", "token": ...}``). STT-consuming calls are rate
limited per client IP, uploads and per-session audio are capped, and rows
expire after ``TASMEE_RETENTION_DAYS`` (default 90).

Recordings are streamed for recognition only and never written to disk; only
the recognised words of possible slips are stored.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import math
import os
import re
import secrets
from datetime import datetime, timedelta
from typing import List, Optional

import numpy as np
from fastapi import (
    APIRouter,
    Depends,
    File,
    Header,
    HTTPException,
    Query,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel, Field
from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.hf_client import HFErrorKind, HFInferenceError
from app.core.config import settings
from app.core.rate_limit import _stt_limiter, check as rate_limit_check, stt_rate_limit
from app.db.database import get_async_session
from app.models.quran import QuranVerse
from app.models.tasmee import (
    EventType,
    MistakeTypeEnum,
    SessionStatus,
    TasmeeEvent,
    TasmeeMistake,
    TasmeeSession,
)
from app.services.quran_text_utils import is_first_verse_with_bismillah, remove_bismillah
from app.stt import get_stt_provider
from app.stt.alignment import Mistake, MistakeType, RecitationAligner
from app.stt.arabic_normalizer import tokenize_with_positions

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Limits, retention and access control
# ============================================================================

TASMEE_RETENTION_DAYS = int(os.getenv("TASMEE_RETENTION_DAYS", "90"))

SAMPLE_RATE = 16000
BYTES_PER_SAMPLE = 2  # 16-bit PCM
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # POST /transcribe
MAX_SESSION_AUDIO_SECONDS = 600  # 10 minutes of streamed audio per session
MAX_SESSION_AUDIO_BYTES = SAMPLE_RATE * BYTES_PER_SAMPLE * MAX_SESSION_AUDIO_SECONDS
MAX_WS_TEXT_FRAME = 4096
WS_AUTH_TIMEOUT_SECONDS = 10.0

# Streaming windows: non-overlapping 3 s windows. Overlapping windows re-fed
# already matched words to the aligner and produced false slip alerts on a
# correct recitation; a slip is only reported after the same expected word
# fails in 2 consecutive windows.
WS_WINDOW_SECONDS = 3.0
WS_MISMATCH_WINDOW_PATIENCE = 2

TOKEN_HEADER = "X-Tasmee-Token"

# WebSocket close codes (4xxx = application specific)
WS_CLOSE_UNAUTHORIZED = 4001
WS_CLOSE_STT_UNAVAILABLE = 4003
WS_CLOSE_NOT_FOUND = 4004
WS_CLOSE_SESSION_LIMIT = 4008
WS_CLOSE_NOT_ACTIVE = 4009
WS_CLOSE_RATE_LIMITED = 4029

_ALLOWED_WS_MESSAGES = {"reveal_request", "config_update", "reset", "auth"}
_REVEAL_MODES = {"auto", "smart_tap", "hybrid"}
_TAP_COUNTS = {1, 3}
_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

# Every call that can reach the paid speech-to-text service (session create,
# WebSocket connect, single-file transcribe) shares the app-wide STT budget
# (app.core.rate_limit.stt_rate_limit / _stt_limiter: 10 per minute per
# client, Redis-shared when RATE_LIMIT_BACKEND=redis).


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _token_matches(tasmee_session: TasmeeSession, token: Optional[str]) -> bool:
    if not token or not isinstance(token, str) or not tasmee_session.client_token_hash:
        return False
    return hmac.compare_digest(_hash_token(token), tasmee_session.client_token_hash)


async def _load_session(db: AsyncSession, public_id: str) -> Optional[TasmeeSession]:
    if not isinstance(public_id, str) or not _UUID_RE.match(public_id):
        return None
    result = await db.execute(select(TasmeeSession).where(TasmeeSession.public_id == public_id))
    return result.scalar_one_or_none()


async def _get_owned_session(
    db: AsyncSession, public_id: str, token: Optional[str]
) -> TasmeeSession:
    """Load a session the caller holds the token for (401 without a token, else 404)."""
    if not token:
        raise HTTPException(status_code=401, detail="Missing session token")
    tasmee_session = await _load_session(db, public_id)
    # A wrong token and an unknown id look the same, so ids cannot be probed.
    if not tasmee_session or not _token_matches(tasmee_session, token):
        raise HTTPException(status_code=404, detail="Session not found")
    return tasmee_session


async def _purge_expired_sessions(db: AsyncSession) -> None:
    """Delete sessions (and, by FK cascade, their events/slips) past retention."""
    cutoff = datetime.utcnow() - timedelta(days=TASMEE_RETENTION_DAYS)
    await db.execute(sa_delete(TasmeeSession).where(TasmeeSession.created_at < cutoff))


# ============================================================================
# Pydantic Models
# ============================================================================


class SessionCreateRequest(BaseModel):
    """Request to create a new Tasmee session."""

    sura_no: int = Field(..., ge=1, le=114, description="Surah number (1-114)")
    aya_start: int = Field(..., ge=1, le=286, description="Starting ayah number")
    aya_end: int = Field(..., ge=1, le=286, description="Ending ayah number")
    user_id: Optional[str] = Field(None, max_length=255, description="Optional user identifier")
    device_id: Optional[str] = Field(None, max_length=255, description="Optional device identifier")
    stt_model: str = Field("base", pattern=r"^[A-Za-z0-9._-]{1,32}$", description="STT model size")


class SessionResponse(BaseModel):
    """Response with session details. ``id`` is the public (UUID) id."""

    id: str
    status: str
    created_at: str
    sura_no: int
    sura_name_ar: Optional[str]
    sura_name_en: Optional[str]
    aya_start: int
    aya_end: int
    total_verses: int
    total_words: int
    words_completed: int
    words_correct: int
    mistakes_count: int
    accuracy_score: Optional[float]
    completion_percentage: float
    expected_text: Optional[str] = None
    highlighted_words: Optional[List[dict]] = None
    # Returned only by POST /sessions; the server keeps only its hash.
    client_token: Optional[str] = None


class TranscriptionResponse(BaseModel):
    """Response from transcription."""

    text: str
    words: List[dict]
    alignment: dict
    mistakes: List[dict]
    is_complete: bool


class SessionCredential(BaseModel):
    id: str = Field(..., max_length=64)
    token: str = Field(..., min_length=8, max_length=128)


class DeleteSessionsRequest(BaseModel):
    sessions: List[SessionCredential] = Field(..., min_length=1, max_length=200)


class DeleteSessionsResponse(BaseModel):
    deleted: int


# ============================================================================
# Helpers
# ============================================================================


def _recitable_text(verse) -> str:
    """Ayah text as recited: no Basmala prefix except for Al-Fatiha 1:1."""
    if verse.sura_no != 1 and is_first_verse_with_bismillah(verse.sura_no, verse.aya_no):
        return remove_bismillah(verse.text_uthmani)
    return verse.text_uthmani


_POSITIONAL_MISTAKES = {
    MistakeType.SUBSTITUTION,
    MistakeType.DELETION,
    MistakeType.MISPRONUNCIATION,
}


def _words_correct(aligner: RecitationAligner) -> int:
    """Words followed without a flagged slip, up to the current pointer.

    Insertions/repetitions do not consume an expected word, so only slips
    tied to an expected position count against it.
    """
    position = aligner.state.current_position
    flagged = {
        m.position
        for m in aligner.state.mistakes
        if m.type in _POSITIONAL_MISTAKES and m.position < position
    }
    return max(0, position - len(flagged))


def _aya_for_position(tasmee_session: TasmeeSession, position: int) -> int:
    """Map a word position to its ayah using the per-ayah word counts."""
    counts = (tasmee_session.extra_data or {}).get("verse_word_counts") or []
    seen = 0
    for aya_no, count in counts:
        seen += count
        if position < seen:
            return aya_no
    return tasmee_session.aya_end if counts else tasmee_session.aya_start


def _mistake_row(
    tasmee_session: TasmeeSession, mistake: Mistake, timestamp_offset: float = 0.0
) -> TasmeeMistake:
    return TasmeeMistake(
        session_id=tasmee_session.id,
        mistake_type=MistakeTypeEnum(mistake.type.value),
        severity=mistake.severity.value,
        word_position=mistake.position,
        verse_sura_no=tasmee_session.sura_no,
        verse_aya_no=_aya_for_position(tasmee_session, mistake.position),
        expected_word=(mistake.expected_word or "")[:200],
        expected_normalized=(mistake.expected_normalized or "")[:200],
        actual_word=mistake.actual_word[:200] if mistake.actual_word else None,
        actual_normalized=mistake.actual_normalized[:200] if mistake.actual_normalized else None,
        timestamp=timestamp_offset + mistake.timestamp,
        confidence=mistake.confidence,
        context_before=mistake.context_before,
        context_after=mistake.context_after,
    )


def _session_response(tasmee_session: TasmeeSession, **extra) -> SessionResponse:
    return SessionResponse(
        id=tasmee_session.public_id,
        status=tasmee_session.status.value,
        created_at=tasmee_session.created_at.isoformat(),
        sura_no=tasmee_session.sura_no,
        sura_name_ar=tasmee_session.sura_name_ar,
        sura_name_en=tasmee_session.sura_name_en,
        aya_start=tasmee_session.aya_start,
        aya_end=tasmee_session.aya_end,
        total_verses=tasmee_session.total_verses,
        total_words=tasmee_session.total_words,
        words_completed=tasmee_session.words_completed or 0,
        words_correct=tasmee_session.words_correct or 0,
        mistakes_count=tasmee_session.mistakes_count or 0,
        accuracy_score=tasmee_session.accuracy_score,
        completion_percentage=tasmee_session.completion_percentage or 0.0,
        **extra,
    )


def _clamp_count(value, default: int) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return default
    if isinstance(value, float) and not math.isfinite(value):
        return default
    return max(1, min(10, int(value)))


# ============================================================================
# Session Management Endpoints
# ============================================================================


@router.post(
    "/sessions",
    response_model=SessionResponse,
    tags=["Sessions"],
    dependencies=[Depends(stt_rate_limit)],
)
async def create_session(
    request: SessionCreateRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Create a new Tasmee memorization session.

    Returns the session (with its public id and expected text) and a client
    token that must accompany every later call for this session.
    """
    if request.aya_end < request.aya_start:
        raise HTTPException(status_code=400, detail="aya_end must be >= aya_start")

    # Lazy retention purge (mirrors therapy sessions).
    await _purge_expired_sessions(session)

    query = (
        select(QuranVerse)
        .where(QuranVerse.sura_no == request.sura_no)
        .where(QuranVerse.aya_no >= request.aya_start)
        .where(QuranVerse.aya_no <= request.aya_end)
        .order_by(QuranVerse.aya_no)
    )
    result = await session.execute(query)
    verses = result.scalars().all()

    if not verses:
        await session.commit()
        raise HTTPException(
            status_code=404,
            detail=f"No verses found for surah {request.sura_no}, "
            f"ayat {request.aya_start}-{request.aya_end}",
        )

    # The canonical store prefixes the Basmala to ayah 1 of every surah except
    # Al-Fatiha (where it IS ayah 1) and At-Tawbah; it is not part of that
    # ayah, so it must not be graded as missing words.
    recitable = [(v.aya_no, _recitable_text(v)) for v in verses]
    expected_text = " ".join(text for _, text in recitable)
    words = tokenize_with_positions(expected_text)
    verse_word_counts = [[aya_no, len(tokenize_with_positions(text))] for aya_no, text in recitable]

    client_token = secrets.token_urlsafe(24)

    tasmee_session = TasmeeSession(
        user_id=request.user_id,
        device_id=request.device_id,
        status=SessionStatus.ACTIVE,
        sura_no=request.sura_no,
        sura_name_ar=verses[0].sura_name_ar,
        sura_name_en=verses[0].sura_name_en,
        aya_start=request.aya_start,
        aya_end=request.aya_end,
        total_verses=len(verses),
        total_words=len(words),
        stt_model=request.stt_model,
        client_token_hash=_hash_token(client_token),
        extra_data={
            "expected_text": expected_text,
            "verse_ids": [v.id for v in verses],
            "verse_word_counts": verse_word_counts,
        },
    )
    session.add(tasmee_session)
    await session.commit()
    await session.refresh(tasmee_session)

    session.add(
        TasmeeEvent(
            session_id=tasmee_session.id,
            event_type=EventType.SESSION_START,
            timestamp=0.0,
            data={"aya_range": f"{request.aya_start}-{request.aya_end}"},
        )
    )
    await session.commit()

    highlighted_words = [
        {
            "word": w.original,
            "normalized": w.normalized,
            "position": w.position,
            "status": "pending" if i > 0 else "current",
            "mistake_type": None,
        }
        for i, w in enumerate(words)
    ]

    return _session_response(
        tasmee_session,
        expected_text=expected_text,
        highlighted_words=highlighted_words,
        client_token=client_token,
    )


@router.post("/sessions/delete", response_model=DeleteSessionsResponse, tags=["Sessions"])
async def delete_sessions(
    request: DeleteSessionsRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Delete the caller's sessions (and their events and slips).

    Each entry must carry the session's client token; entries that are
    unknown or whose token does not match are skipped silently.
    """
    deleted = 0
    for cred in request.sessions:
        tasmee_session = await _load_session(session, cred.id)
        if tasmee_session and _token_matches(tasmee_session, cred.token):
            await session.execute(
                sa_delete(TasmeeSession).where(TasmeeSession.id == tasmee_session.id)
            )
            deleted += 1
    await session.commit()
    return DeleteSessionsResponse(deleted=deleted)


@router.get("/sessions/{session_id}", response_model=SessionResponse, tags=["Sessions"])
async def get_session(
    session_id: str,
    x_tasmee_token: Optional[str] = Header(None, alias=TOKEN_HEADER),
    session: AsyncSession = Depends(get_async_session),
):
    """Get session details (requires the session token)."""
    tasmee_session = await _get_owned_session(session, session_id, x_tasmee_token)
    return _session_response(
        tasmee_session,
        expected_text=(tasmee_session.extra_data or {}).get("expected_text"),
    )


@router.post("/sessions/{session_id}/complete", tags=["Sessions"])
async def complete_session(
    session_id: str,
    x_tasmee_token: Optional[str] = Header(None, alias=TOKEN_HEADER),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Mark a session as completed.

    ``accuracy_score`` is the share of followed words with no flagged slip
    (automatic word matching only; harakat and tajweed are not assessed).
    """
    tasmee_session = await _get_owned_session(session, session_id, x_tasmee_token)

    words_completed = tasmee_session.words_completed or 0
    words_correct = tasmee_session.words_correct or 0
    accuracy = (
        max(0.0, min(1.0, words_correct / words_completed)) if words_completed > 0 else 0.0
    )

    tasmee_session.status = SessionStatus.COMPLETED
    tasmee_session.completed_at = datetime.utcnow()
    tasmee_session.accuracy_score = accuracy
    tasmee_session.completion_percentage = (
        words_completed / tasmee_session.total_words * 100
        if tasmee_session.total_words > 0
        else 0.0
    )

    session.add(
        TasmeeEvent(
            session_id=tasmee_session.id,
            event_type=EventType.SESSION_END,
            timestamp=tasmee_session.active_duration_seconds or 0.0,
            data={"accuracy": accuracy, "mistakes": tasmee_session.mistakes_count},
        )
    )
    await session.commit()

    return {
        "status": "completed",
        "accuracy_score": accuracy,
        "words_completed": words_completed,
        "words_correct": words_correct,
        "total_words": tasmee_session.total_words,
        "completion_percentage": tasmee_session.completion_percentage,
        "total_mistakes": tasmee_session.mistakes_count,
    }


# ============================================================================
# Audio Transcription Endpoints
# ============================================================================


@router.post(
    "/transcribe",
    response_model=TranscriptionResponse,
    tags=["Transcription"],
    dependencies=[Depends(stt_rate_limit)],
)
async def transcribe_audio(
    session_id: str,
    audio: UploadFile = File(...),
    timestamp: float = Query(0.0, ge=0.0, le=86400.0, description="Current timestamp"),
    x_tasmee_token: Optional[str] = Header(None, alias=TOKEN_HEADER),
    db_session: AsyncSession = Depends(get_async_session),
):
    """
    Transcribe uploaded audio (16 kHz mono 16-bit PCM, at most 5 MB) and
    align it with the expected text.
    """
    tasmee_session = await _get_owned_session(db_session, session_id, x_tasmee_token)

    if tasmee_session.status != SessionStatus.ACTIVE:
        raise HTTPException(
            status_code=409,
            detail=f"Session is {tasmee_session.status.value}, not active",
        )

    audio_data = await audio.read(MAX_UPLOAD_BYTES + 1)
    if len(audio_data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Audio upload is larger than 5 MB")
    if len(audio_data) % BYTES_PER_SAMPLE:
        audio_data = audio_data[:-1]

    used = (tasmee_session.audio_duration_seconds or 0.0) + len(audio_data) / (
        SAMPLE_RATE * BYTES_PER_SAMPLE
    )
    if used > MAX_SESSION_AUDIO_SECONDS:
        raise HTTPException(status_code=413, detail="Session audio limit (10 minutes) reached")

    audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

    stt_provider = get_stt_provider(model_size=tasmee_session.stt_model, language="ar")

    try:
        stt_result = await asyncio.to_thread(
            stt_provider.transcribe, audio_array, word_timestamps=True
        )
    except HFInferenceError as e:
        logger.error("Transcription failed: %s", e)
        if e.kind == HFErrorKind.QUOTA:
            raise HTTPException(
                status_code=429,
                detail="Speech recognition usage limit reached. Please try again later.",
            )
        raise HTTPException(status_code=503, detail="Speech recognition is temporarily unavailable.")
    except Exception as e:  # noqa: BLE001
        logger.error("Transcription failed: %s", type(e).__name__)
        raise HTTPException(status_code=500, detail="Transcription failed.")

    expected_text = (tasmee_session.extra_data or {}).get("expected_text", "")
    aligner = RecitationAligner(expected_text)
    aligner.state.current_position = tasmee_session.words_completed or 0

    mistakes: List[Mistake] = []
    for segment in stt_result.segments:
        mistakes.extend(aligner.process_segment(segment).mistakes)

    tasmee_session.words_completed = aligner.state.current_position
    tasmee_session.words_correct = _words_correct(aligner)
    tasmee_session.mistakes_count = (tasmee_session.mistakes_count or 0) + len(mistakes)
    tasmee_session.active_duration_seconds = (
        tasmee_session.active_duration_seconds or 0.0
    ) + stt_result.duration
    tasmee_session.audio_duration_seconds = used

    for mistake in mistakes:
        db_session.add(_mistake_row(tasmee_session, mistake, timestamp))

    db_session.add(
        TasmeeEvent(
            session_id=tasmee_session.id,
            event_type=EventType.WORD_MATCHED,
            timestamp=timestamp,
            expected_word_index=aligner.state.current_position,
            confidence=stt_result.segments[0].confidence if stt_result.segments else 0.0,
            data={
                "words_in_segment": stt_result.word_count,
                "mistakes_in_segment": len(mistakes),
            },
        )
    )
    await db_session.commit()

    return TranscriptionResponse(
        text=stt_result.full_text,
        words=[w.__dict__ for s in stt_result.segments for w in s.words],
        alignment=aligner.get_state(),
        mistakes=[m.to_dict() for m in mistakes],
        is_complete=aligner.state.is_complete,
    )


# ============================================================================
# WebSocket for Real-time Transcription
# ============================================================================


async def _ws_close(websocket: WebSocket, code: int, reason: str) -> None:
    try:
        await websocket.close(code=code, reason=reason)
    except RuntimeError:
        pass  # already closed


async def _ws_receive_auth(websocket: WebSocket) -> Optional[str]:
    """Wait for the first frame ``{"type": "auth", "token": "..."}``."""
    try:
        message = await asyncio.wait_for(websocket.receive(), timeout=WS_AUTH_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        return None
    text = message.get("text")
    if not isinstance(text, str) or len(text) > MAX_WS_TEXT_FRAME:
        return None
    try:
        data = json.loads(text)
    except ValueError:
        return None
    if not isinstance(data, dict) or data.get("type") != "auth":
        return None
    token = data.get("token")
    return token if isinstance(token, str) else None


@router.websocket("/ws/{session_id}")
async def websocket_transcription(
    websocket: WebSocket,
    session_id: str,
):
    """
    WebSocket endpoint for real-time word-by-word follow-along.

    Protocol:
    - Client → Server:
      - first frame (required): {"type": "auth", "token": "<client_token>"}
      - Binary: raw 16 kHz mono PCM Int16 audio
      - JSON: {"type": "reveal_request", "count": 1..10}
      - JSON: {"type": "config_update", "reveal_mode": "auto|smart_tap|hybrid",
               "tap_reveal_count": 1|3, "hybrid_threshold": 0..1}
      - JSON: {"type": "reset"}

    - Server → Client: init, pointer_update, reveal_words, mistake_alert,
      config_updated, reset_complete, stt_unavailable, session_limit.

    Close codes: 4001 unauthorized, 4003 STT unavailable, 4004 not found,
    4008 session audio limit, 4009 session not active, 4029 rate limited.
    """
    await websocket.accept()

    if not await rate_limit_check(_stt_limiter, websocket, "STT"):
        await _ws_close(websocket, WS_CLOSE_RATE_LIMITED, "rate_limited")
        return

    token = await _ws_receive_auth(websocket)
    if not token:
        await _ws_close(websocket, WS_CLOSE_UNAUTHORIZED, "unauthorized")
        return

    from app.db.database import AsyncSessionLocal
    from app.stt.audio_buffer import RollingAudioBuffer

    async with AsyncSessionLocal() as db_session:
        tasmee_session = await _load_session(db_session, session_id)
        if not tasmee_session or not _token_matches(tasmee_session, token):
            await _ws_close(websocket, WS_CLOSE_NOT_FOUND, "session_not_found")
            return
        if tasmee_session.status != SessionStatus.ACTIVE:
            await _ws_close(websocket, WS_CLOSE_NOT_ACTIVE, "session_not_active")
            return

        expected_text = (tasmee_session.extra_data or {}).get("expected_text", "")

        stt_provider = get_stt_provider(model_size=tasmee_session.stt_model, language="ar")
        try:
            stt_provider.load_model()
        except HFInferenceError as e:
            logger.error("STT unavailable for a Tasmee session: %s", e)
            await _ws_close(websocket, WS_CLOSE_STT_UNAVAILABLE, "stt_unavailable")
            return
        stt_failures = 0

        aligner = RecitationAligner(
            expected_text, mismatch_window_patience=WS_MISMATCH_WINDOW_PATIENCE
        )
        aligner.state.current_position = tasmee_session.words_completed or 0

        words = tokenize_with_positions(expected_text)
        total_words = len(words)

        reveal_state = {
            "pointer": tasmee_session.words_completed or 0,
            "revealed_up_to": tasmee_session.words_completed or 0,
            "reveal_mode": "auto",
            "tap_reveal_count": 1,
            "hybrid_threshold": 0.7,
        }

        audio_buffer = RollingAudioBuffer(
            window_duration=WS_WINDOW_SECONDS,
            step_duration=WS_WINDOW_SECONDS,
            sample_rate=SAMPLE_RATE,
        )

        await websocket.send_json({
            "type": "init",
            "total_words": total_words,
            "pointer": reveal_state["pointer"],
            "revealed_up_to": reveal_state["revealed_up_to"],
            "reveal_mode": reveal_state["reveal_mode"],
            "words": [
                {"word": w.original, "position": w.position, "is_revealed": i < reveal_state["revealed_up_to"]}
                for i, w in enumerate(words)
            ],
        })

        async def handle_pointer_advance(new_position: int) -> None:
            old_pointer = reveal_state["pointer"]
            reveal_state["pointer"] = new_position
            progress = new_position / total_words if total_words > 0 else 1.0

            new_revealed = reveal_state["revealed_up_to"]
            if reveal_state["reveal_mode"] == "auto":
                new_revealed = max(reveal_state["revealed_up_to"], new_position)
            elif reveal_state["reveal_mode"] == "hybrid" and progress < reveal_state["hybrid_threshold"]:
                new_revealed = max(reveal_state["revealed_up_to"], new_position)
            # smart_tap: never auto-reveal

            await websocket.send_json({
                "type": "pointer_update",
                "position": new_position,
                "previous_position": old_pointer,
                "progress": progress,
                "revealed_up_to": new_revealed,
                "is_complete": new_position >= total_words,
            })

            if new_revealed > reveal_state["revealed_up_to"]:
                await websocket.send_json({
                    "type": "reveal_words",
                    "words": [
                        {"word": words[i].original, "position": i}
                        for i in range(reveal_state["revealed_up_to"], new_revealed)
                    ],
                    "reveal_source": "alignment",
                    "revealed_up_to": new_revealed,
                })
                reveal_state["revealed_up_to"] = new_revealed

        async def handle_reveal_request(count: int) -> None:
            new_revealed = min(reveal_state["revealed_up_to"] + count, total_words)
            if new_revealed > reveal_state["revealed_up_to"]:
                await websocket.send_json({
                    "type": "reveal_words",
                    "words": [
                        {"word": words[i].original, "position": i}
                        for i in range(reveal_state["revealed_up_to"], new_revealed)
                    ],
                    "reveal_source": "tap",
                    "revealed_up_to": new_revealed,
                })
                reveal_state["revealed_up_to"] = new_revealed

        async def handle_config_update(config: dict) -> None:
            mode = config.get("reveal_mode")
            if isinstance(mode, str) and mode in _REVEAL_MODES:
                reveal_state["reveal_mode"] = mode
            tap = config.get("tap_reveal_count")
            if not isinstance(tap, bool) and isinstance(tap, int) and tap in _TAP_COUNTS:
                reveal_state["tap_reveal_count"] = tap
            threshold = config.get("hybrid_threshold")
            if (
                not isinstance(threshold, bool)
                and isinstance(threshold, (int, float))
                and math.isfinite(threshold)
                and 0.0 <= threshold <= 1.0
            ):
                reveal_state["hybrid_threshold"] = float(threshold)

            await websocket.send_json({
                "type": "config_updated",
                "reveal_mode": reveal_state["reveal_mode"],
                "tap_reveal_count": reveal_state["tap_reveal_count"],
                "hybrid_threshold": reveal_state["hybrid_threshold"],
            })

        # The 10-minute cap spans reconnects to the same session.
        total_audio_bytes = int(
            (tasmee_session.audio_duration_seconds or 0.0) * SAMPLE_RATE * BYTES_PER_SAMPLE
        )

        try:
            while True:
                message = await websocket.receive()
                if message.get("type") == "websocket.disconnect":
                    break

                data = message.get("bytes")
                if data is not None:
                    total_audio_bytes += len(data)
                    if total_audio_bytes > MAX_SESSION_AUDIO_BYTES:
                        await websocket.send_json({"type": "session_limit", "max_seconds": MAX_SESSION_AUDIO_SECONDS})
                        await _ws_close(websocket, WS_CLOSE_SESSION_LIMIT, "session_limit")
                        return
                    if len(data) % BYTES_PER_SAMPLE:
                        data = data[:-1]

                    chunk = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                    window = audio_buffer.add_chunk(chunk)
                    if window is None:
                        continue

                    try:
                        stt_result = await asyncio.to_thread(
                            stt_provider.transcribe, window, word_timestamps=True
                        )
                        stt_failures = 0
                    except HFInferenceError as e:
                        stt_failures += 1
                        logger.warning("[TasmeeSTT] window failed (%d): %s", stt_failures, e)
                        await websocket.send_json({
                            "type": "stt_unavailable",
                            "reason": "ai_quota_exceeded" if e.kind == HFErrorKind.QUOTA else e.kind.value,
                        })
                        if stt_failures >= 3:
                            await _ws_close(websocket, WS_CLOSE_STT_UNAVAILABLE, "stt_unavailable")
                            return
                        continue

                    # Log counts only: never the recognised words.
                    logger.debug(
                        "[TasmeeSTT] window: %d segments, %d words",
                        len(stt_result.segments),
                        stt_result.word_count,
                    )
                    if not stt_result.segments:
                        continue

                    old_position = aligner.state.current_position
                    window_mistakes: List[Mistake] = []
                    for segment in stt_result.segments:
                        window_mistakes.extend(aligner.process_segment(segment).mistakes)

                    new_position = aligner.state.current_position

                    # Persist before notifying: the client may call /complete
                    # as soon as it sees is_complete.
                    for mistake in window_mistakes:
                        db_session.add(_mistake_row(tasmee_session, mistake))
                    tasmee_session.words_completed = new_position
                    tasmee_session.words_correct = _words_correct(aligner)
                    tasmee_session.mistakes_count = len(aligner.state.mistakes)
                    tasmee_session.audio_duration_seconds = total_audio_bytes / (
                        SAMPLE_RATE * BYTES_PER_SAMPLE
                    )
                    await db_session.commit()

                    if new_position > old_position:
                        await handle_pointer_advance(new_position)

                    for mistake in window_mistakes:
                        await websocket.send_json({
                            "type": "mistake_alert",
                            "position": mistake.position,
                            "mistake_type": mistake.type.value,
                            "severity": mistake.severity.value,
                            "expected_word": mistake.expected_word,
                            "actual_word": mistake.actual_word,
                            "timestamp": mistake.timestamp,
                            "is_skip": mistake.type == MistakeType.DELETION,
                        })
                    continue

                raw = message.get("text")
                if not isinstance(raw, str) or len(raw) > MAX_WS_TEXT_FRAME:
                    continue
                try:
                    msg_data = json.loads(raw)
                except ValueError:
                    continue
                if not isinstance(msg_data, dict):
                    continue
                msg_type = msg_data.get("type")
                if msg_type not in _ALLOWED_WS_MESSAGES:
                    continue
                logger.debug("[TasmeeWS] control message: %s", msg_type)

                if msg_type == "reveal_request":
                    count = _clamp_count(msg_data.get("count"), reveal_state["tap_reveal_count"])
                    await handle_reveal_request(count)
                elif msg_type == "config_update":
                    await handle_config_update(msg_data)
                elif msg_type == "reset":
                    aligner.reset()
                    audio_buffer.reset()
                    reveal_state["pointer"] = 0
                    reveal_state["revealed_up_to"] = 0
                    await websocket.send_json({
                        "type": "reset_complete",
                        "pointer": 0,
                        "revealed_up_to": 0,
                    })
                # "auth" after the handshake is ignored.

        except WebSocketDisconnect:
            logger.info("Tasmee WebSocket disconnected")
        except Exception as e:  # noqa: BLE001
            logger.error("Tasmee WebSocket error: %s", type(e).__name__)
            await _ws_close(websocket, 4000, "internal_error")
        finally:
            stt_provider.unload_model()
            await db_session.commit()


# ============================================================================
# Mistake and Statistics Endpoints
# ============================================================================


@router.get("/sessions/{session_id}/mistakes", tags=["Mistakes"])
async def get_session_mistakes(
    session_id: str,
    x_tasmee_token: Optional[str] = Header(None, alias=TOKEN_HEADER),
    session: AsyncSession = Depends(get_async_session),
):
    """Get the possible slips recorded for a session (requires the token)."""
    tasmee_session = await _get_owned_session(session, session_id, x_tasmee_token)
    result = await session.execute(
        select(TasmeeMistake)
        .where(TasmeeMistake.session_id == tasmee_session.id)
        .order_by(TasmeeMistake.timestamp)
    )
    mistakes = result.scalars().all()
    return {"mistakes": [m.to_dict() for m in mistakes], "count": len(mistakes)}


@router.get("/stats", tags=["Statistics"])
async def get_statistics(
    session: AsyncSession = Depends(get_async_session),
):
    """Aggregate, anonymous usage statistics (no per-user filtering)."""
    total_sessions = (await session.execute(select(func.count(TasmeeSession.id)))).scalar() or 0
    completed_sessions = (
        await session.execute(
            select(func.count(TasmeeSession.id)).where(
                TasmeeSession.status == SessionStatus.COMPLETED
            )
        )
    ).scalar() or 0
    avg_accuracy = (
        await session.execute(
            select(func.avg(TasmeeSession.accuracy_score)).where(
                TasmeeSession.accuracy_score.isnot(None)
            )
        )
    ).scalar() or 0.0
    total_words = (await session.execute(select(func.sum(TasmeeSession.words_completed)))).scalar() or 0
    total_mistakes = (await session.execute(select(func.count(TasmeeMistake.id)))).scalar() or 0

    return {
        "total_sessions": total_sessions,
        "completed_sessions": completed_sessions,
        "average_accuracy": round(avg_accuracy * 100, 2),
        "total_words_practiced": total_words,
        "total_mistakes": total_mistakes,
    }


# ============================================================================
# Health Check
# ============================================================================


@router.get("/health", tags=["Health"])
async def health_check():
    """Check if Tasmee service is healthy (no HF call is made)."""
    try:
        provider = get_stt_provider()
        provider.load_model()
        stt_available = True
        stt_error = None
    except HFInferenceError as e:
        stt_available = False
        stt_error = e.kind.value
    except Exception:  # noqa: BLE001
        stt_available = False
        stt_error = "provider_error"

    return {
        "status": "healthy" if stt_available else "degraded",
        "stt_provider": settings.stt_provider,
        "stt_model": settings.hf_stt_model if settings.stt_provider == "huggingface" else None,
        "stt_available": stt_available,
        "stt_error": stt_error,
        "max_session_audio_seconds": MAX_SESSION_AUDIO_SECONDS,
    }
