"""
API Routes for Tasmeeʿ (Memorization) feature.

This module provides endpoints for:
1. Session management (create, update, complete)
2. Audio transcription with streaming support
3. Alignment and mistake detection
4. Progress tracking
5. Session history

Speech-to-text runs on Hugging Face Inference Providers (hosted Whisper,
HF_STT_MODEL) from the backend; the HF token never reaches the client.
"""

import asyncio
import io
import json
import logging
import os
import tempfile
import time
import uuid
from datetime import datetime
from typing import List, Optional

import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_session
from app.models.quran import QuranVerse
from app.models.tasmee import (
    EventType,
    MistakeTypeEnum,
    SessionStatus,
    TasmeeEvent,
    TasmeeMistake,
    TasmeeProgress,
    TasmeeSession,
)
from app.ai.hf_client import HFErrorKind, HFInferenceError
from app.core.config import settings
from app.stt import get_stt_provider
from app.services.quran_text_utils import is_first_verse_with_bismillah, remove_bismillah
from app.stt.alignment import MistakeType, RecitationAligner
from app.stt.arabic_normalizer import tokenize_with_positions

logger = logging.getLogger(__name__)

router = APIRouter()

# Audio storage directory
AUDIO_STORAGE_DIR = os.environ.get(
    "TASMEE_AUDIO_DIR",
    os.path.join(tempfile.gettempdir(), "tasmee_audio"),
)
os.makedirs(AUDIO_STORAGE_DIR, exist_ok=True)


# ============================================================================
# Pydantic Models
# ============================================================================


class SessionCreateRequest(BaseModel):
    """Request to create a new Tasmee session."""

    sura_no: int = Field(..., ge=1, le=114, description="Surah number (1-114)")
    aya_start: int = Field(..., ge=1, description="Starting ayah number")
    aya_end: int = Field(..., ge=1, description="Ending ayah number")
    user_id: Optional[str] = Field(None, description="Optional user identifier")
    device_id: Optional[str] = Field(None, description="Optional device identifier")
    stt_model: str = Field("base", description="STT model size")


class SessionResponse(BaseModel):
    """Response with session details."""

    id: int
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


class TranscriptionRequest(BaseModel):
    """Request for transcription with optional session context."""

    session_id: int
    timestamp: float = Field(0.0, description="Current timestamp in seconds")


class TranscriptionResponse(BaseModel):
    """Response from transcription."""

    text: str
    words: List[dict]
    alignment: dict
    mistakes: List[dict]
    is_complete: bool


class MistakeResponse(BaseModel):
    """Response with mistake details."""

    id: int
    mistake_type: str
    severity: str
    word_position: int
    expected_word: str
    actual_word: Optional[str]
    timestamp: float
    confidence: float
    context_before: List[str]
    context_after: List[str]


class ProgressResponse(BaseModel):
    """Response with progress for a verse."""

    sura_no: int
    aya_no: int
    total_attempts: int
    successful_attempts: int
    best_accuracy: float
    average_accuracy: float
    is_memorized: bool


# ============================================================================
# Session Management Endpoints
# ============================================================================


@router.post("/sessions", response_model=SessionResponse, tags=["Sessions"])
async def create_session(
    request: SessionCreateRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Create a new Tasmee memorization session.

    Initializes a session for practicing recitation of the specified
    surah and ayah range. Returns session details including the expected
    text for recitation.
    """
    # Validate ayah range
    if request.aya_end < request.aya_start:
        raise HTTPException(
            status_code=400,
            detail="aya_end must be >= aya_start",
        )

    # Fetch verses from database
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
        raise HTTPException(
            status_code=404,
            detail=f"No verses found for surah {request.sura_no}, "
            f"ayat {request.aya_start}-{request.aya_end}",
        )

    # Combine verse texts. The canonical store prefixes the Basmala to ayah 1
    # of every surah except Al-Fatiha (where it IS ayah 1) and At-Tawbah; it is
    # not part of that ayah, so it must not be graded as missing words.
    expected_text = " ".join(_recitable_text(v) for v in verses)
    words = tokenize_with_positions(expected_text)

    # Get surah name from first verse
    sura_name_ar = verses[0].sura_name_ar
    sura_name_en = verses[0].sura_name_en

    # Create session
    tasmee_session = TasmeeSession(
        user_id=request.user_id,
        device_id=request.device_id,
        status=SessionStatus.ACTIVE,
        sura_no=request.sura_no,
        sura_name_ar=sura_name_ar,
        sura_name_en=sura_name_en,
        aya_start=request.aya_start,
        aya_end=request.aya_end,
        total_verses=len(verses),
        total_words=len(words),
        stt_model=request.stt_model,
        extra_data={
            "expected_text": expected_text,
            "verse_ids": [v.id for v in verses],
        },
    )
    session.add(tasmee_session)
    await session.commit()
    await session.refresh(tasmee_session)

    # Create start event
    start_event = TasmeeEvent(
        session_id=tasmee_session.id,
        event_type=EventType.SESSION_START,
        timestamp=0.0,
        data={"aya_range": f"{request.aya_start}-{request.aya_end}"},
    )
    session.add(start_event)
    await session.commit()

    # Prepare highlighted words
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

    return SessionResponse(
        id=tasmee_session.id,
        status=tasmee_session.status.value,
        created_at=tasmee_session.created_at.isoformat(),
        sura_no=tasmee_session.sura_no,
        sura_name_ar=sura_name_ar,
        sura_name_en=sura_name_en,
        aya_start=tasmee_session.aya_start,
        aya_end=tasmee_session.aya_end,
        total_verses=tasmee_session.total_verses,
        total_words=tasmee_session.total_words,
        words_completed=0,
        words_correct=0,
        mistakes_count=0,
        accuracy_score=None,
        completion_percentage=0.0,
        expected_text=expected_text,
        highlighted_words=highlighted_words,
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse, tags=["Sessions"])
async def get_session(
    session_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """Get session details by ID."""
    query = select(TasmeeSession).where(TasmeeSession.id == session_id)
    result = await session.execute(query)
    tasmee_session = result.scalar_one_or_none()

    if not tasmee_session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse(
        id=tasmee_session.id,
        status=tasmee_session.status.value,
        created_at=tasmee_session.created_at.isoformat(),
        sura_no=tasmee_session.sura_no,
        sura_name_ar=tasmee_session.sura_name_ar,
        sura_name_en=tasmee_session.sura_name_en,
        aya_start=tasmee_session.aya_start,
        aya_end=tasmee_session.aya_end,
        total_verses=tasmee_session.total_verses,
        total_words=tasmee_session.total_words,
        words_completed=tasmee_session.words_completed,
        words_correct=tasmee_session.words_correct,
        mistakes_count=tasmee_session.mistakes_count,
        accuracy_score=tasmee_session.accuracy_score,
        completion_percentage=tasmee_session.completion_percentage,
        expected_text=tasmee_session.extra_data.get("expected_text") if tasmee_session.extra_data else None,
    )


@router.post("/sessions/{session_id}/complete", tags=["Sessions"])
async def complete_session(
    session_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Mark a session as completed.

    Calculates final metrics and updates progress tracking.
    """
    query = select(TasmeeSession).where(TasmeeSession.id == session_id)
    result = await session.execute(query)
    tasmee_session = result.scalar_one_or_none()

    if not tasmee_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Calculate accuracy
    if tasmee_session.words_completed > 0:
        accuracy = tasmee_session.words_correct / tasmee_session.words_completed
    else:
        accuracy = 0.0

    # Update session
    tasmee_session.status = SessionStatus.COMPLETED
    tasmee_session.completed_at = datetime.utcnow()
    tasmee_session.accuracy_score = accuracy
    tasmee_session.completion_percentage = (
        tasmee_session.words_completed / tasmee_session.total_words * 100
        if tasmee_session.total_words > 0
        else 0.0
    )

    # Create end event
    end_event = TasmeeEvent(
        session_id=session_id,
        event_type=EventType.SESSION_END,
        timestamp=tasmee_session.active_duration_seconds,
        data={
            "accuracy": accuracy,
            "mistakes": tasmee_session.mistakes_count,
        },
    )
    session.add(end_event)

    await session.commit()

    return {
        "status": "completed",
        "accuracy_score": accuracy,
        "completion_percentage": tasmee_session.completion_percentage,
        "total_mistakes": tasmee_session.mistakes_count,
    }


@router.get("/sessions", tags=["Sessions"])
async def list_sessions(
    user_id: Optional[str] = None,
    sura_no: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
):
    """List Tasmee sessions with optional filtering."""
    query = select(TasmeeSession).order_by(TasmeeSession.created_at.desc())

    if user_id:
        query = query.where(TasmeeSession.user_id == user_id)
    if sura_no:
        query = query.where(TasmeeSession.sura_no == sura_no)
    if status:
        query = query.where(TasmeeSession.status == SessionStatus(status))

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    sessions = result.scalars().all()

    return {
        "sessions": [s.to_dict() for s in sessions],
        "count": len(sessions),
        "offset": offset,
        "limit": limit,
    }


def _recitable_text(verse) -> str:
    """Ayah text as recited: no Basmala prefix except for Al-Fatiha 1:1."""
    if verse.sura_no != 1 and is_first_verse_with_bismillah(verse.sura_no, verse.aya_no):
        return remove_bismillah(verse.text_uthmani)
    return verse.text_uthmani


# ============================================================================
# Audio Transcription Endpoints
# ============================================================================


@router.post("/transcribe", response_model=TranscriptionResponse, tags=["Transcription"])
async def transcribe_audio(
    session_id: int,
    audio: UploadFile = File(...),
    timestamp: float = Query(0.0, description="Current timestamp"),
    db_session: AsyncSession = Depends(get_async_session),
):
    """
    Transcribe uploaded audio and align with expected text.

    Accepts audio in WAV format (16kHz mono PCM recommended).
    Returns transcription with alignment status and any detected mistakes.
    """
    # Get session
    query = select(TasmeeSession).where(TasmeeSession.id == session_id)
    result = await db_session.execute(query)
    tasmee_session = result.scalar_one_or_none()

    if not tasmee_session:
        raise HTTPException(status_code=404, detail="Session not found")

    if tasmee_session.status != SessionStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail=f"Session is {tasmee_session.status.value}, not active",
        )

    # Read audio data
    audio_data = await audio.read()

    # Convert to numpy array (assuming 16-bit PCM)
    try:
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse audio data: {str(e)}",
        )

    # Get or create STT provider
    stt_provider = get_stt_provider(
        model_size=tasmee_session.stt_model,
        language="ar",
    )

    # Transcribe (HTTP call to HF — run off the event loop)
    try:
        stt_result = await asyncio.to_thread(
            stt_provider.transcribe, audio_array, word_timestamps=True
        )
    except HFInferenceError as e:
        logger.error(f"Transcription failed: {e}")
        if e.kind == HFErrorKind.QUOTA:
            raise HTTPException(status_code=429, detail="Speech recognition usage limit reached. Please try again later.")
        raise HTTPException(status_code=503, detail="Speech recognition is temporarily unavailable.")
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail="Transcription failed.")

    # Get expected text
    expected_text = tasmee_session.extra_data.get("expected_text", "") if tasmee_session.extra_data else ""

    # Create aligner and process
    aligner = RecitationAligner(expected_text)

    # Set initial position from session
    aligner.state.current_position = tasmee_session.words_completed

    # Process transcription segments
    mistakes = []
    for segment in stt_result.segments:
        alignment_result = aligner.process_segment(segment)
        mistakes.extend(alignment_result.mistakes)

    # Update session
    tasmee_session.words_completed = aligner.state.current_position
    tasmee_session.words_correct = (
        aligner.state.current_position - len(aligner.state.mistakes)
    )
    tasmee_session.mistakes_count = len(aligner.state.mistakes)
    tasmee_session.active_duration_seconds += stt_result.duration

    # Save mistakes to database
    for mistake in mistakes:
        db_mistake = TasmeeMistake(
            session_id=session_id,
            mistake_type=MistakeTypeEnum(mistake.type.value),
            severity=mistake.severity.value,
            word_position=mistake.position,
            verse_sura_no=tasmee_session.sura_no,
            verse_aya_no=tasmee_session.aya_start,  # Simplified
            expected_word=mistake.expected_word,
            expected_normalized=mistake.expected_normalized,
            actual_word=mistake.actual_word,
            actual_normalized=mistake.actual_normalized,
            timestamp=timestamp + mistake.timestamp,
            confidence=mistake.confidence,
            context_before=mistake.context_before,
            context_after=mistake.context_after,
        )
        db_session.add(db_mistake)

    # Create event for transcription
    event = TasmeeEvent(
        session_id=session_id,
        event_type=EventType.WORD_MATCHED,
        timestamp=timestamp,
        expected_word_index=aligner.state.current_position,
        recognized_word=stt_result.full_text[:100],  # Truncate
        confidence=stt_result.segments[0].confidence if stt_result.segments else 0.0,
        data={
            "words_in_segment": stt_result.word_count,
            "mistakes_in_segment": len(mistakes),
        },
    )
    db_session.add(event)

    await db_session.commit()

    return TranscriptionResponse(
        text=stt_result.full_text,
        words=[w.__dict__ for s in stt_result.segments for w in s.words],
        alignment=aligner.get_state(),
        mistakes=[m.to_dict() for m in mistakes],
        is_complete=aligner.state.is_complete,
    )


@router.post("/sessions/{session_id}/audio", tags=["Audio"])
async def upload_session_audio(
    session_id: int,
    audio: UploadFile = File(...),
    db_session: AsyncSession = Depends(get_async_session),
):
    """
    Upload and save the complete audio recording for a session.

    The audio is saved for later playback and review.
    """
    # Get session
    query = select(TasmeeSession).where(TasmeeSession.id == session_id)
    result = await db_session.execute(query)
    tasmee_session = result.scalar_one_or_none()

    if not tasmee_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Generate filename
    filename = f"session_{session_id}_{uuid.uuid4().hex[:8]}.wav"
    filepath = os.path.join(AUDIO_STORAGE_DIR, filename)

    # Save audio
    audio_data = await audio.read()
    with open(filepath, "wb") as f:
        f.write(audio_data)

    # Update session
    tasmee_session.audio_file_path = filepath
    tasmee_session.audio_duration_seconds = len(audio_data) / (16000 * 2)  # Assuming 16kHz 16-bit

    await db_session.commit()

    return {
        "status": "saved",
        "filename": filename,
        "size_bytes": len(audio_data),
    }


# ============================================================================
# WebSocket for Real-time Transcription
# ============================================================================


@router.websocket("/ws/{session_id}")
async def websocket_transcription(
    websocket: WebSocket,
    session_id: int,
):
    """
    WebSocket endpoint for real-time audio transcription with progressive reveal.

    Client sends audio chunks, server responds with pointer updates and word reveals.

    Protocol:
    - Client → Server:
      - Binary: Raw 16kHz mono PCM Int16 audio
      - JSON: {"type": "reveal_request", "count": 1|3} - tap to reveal words
      - JSON: {"type": "config_update", "reveal_mode": "auto|smart_tap|hybrid", ...}

    - Server → Client:
      - {"type": "pointer_update", "position": int, "progress": float, ...}
      - {"type": "reveal_words", "words": [...], "reveal_source": "alignment|tap"}
      - {"type": "highlight_word", "position": int, "status": str}
      - {"type": "mistake_alert", "position": int, "mistake_type": str, ...}
    """
    logger.info(f"[TasmeeWS] Connection attempt for session {session_id}")
    await websocket.accept()
    logger.info(f"[TasmeeWS] Connection accepted for session {session_id}")

    # Import audio buffer
    from app.stt.audio_buffer import RollingAudioBuffer

    # Get database session
    from app.db.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db_session:
        # Get Tasmee session
        query = select(TasmeeSession).where(TasmeeSession.id == session_id)
        result = await db_session.execute(query)
        tasmee_session = result.scalar_one_or_none()

        if not tasmee_session:
            await websocket.close(code=4004, reason="Session not found")
            return

        expected_text = tasmee_session.extra_data.get("expected_text", "") if tasmee_session.extra_data else ""

        # Initialize STT and aligner
        stt_provider = get_stt_provider(
            model_size=tasmee_session.stt_model,
            language="ar",
        )
        try:
            stt_provider.load_model()
        except HFInferenceError as e:
            logger.error(f"STT unavailable for session {session_id}: {e}")
            await websocket.close(code=4003, reason="stt_unavailable")
            return
        stt_failures = 0

        aligner = RecitationAligner(expected_text)
        aligner.state.current_position = tasmee_session.words_completed

        # Get word list for reveal tracking
        words = tokenize_with_positions(expected_text)
        total_words = len(words)

        # Progressive reveal state
        reveal_state = {
            "pointer": tasmee_session.words_completed,  # Voice-driven position
            "revealed_up_to": tasmee_session.words_completed,  # Highest revealed index
            "reveal_mode": "auto",  # auto | smart_tap | hybrid
            "tap_reveal_count": 1,  # Words to reveal per tap (1 or 3)
            "hybrid_threshold": 0.7,  # Switch to tap mode at 70%
        }

        # Rolling audio buffer (1.2s window, 0.4s step for low latency)
        audio_buffer = RollingAudioBuffer(
            window_duration=1.2,
            step_duration=0.4,
            sample_rate=16000,
        )

        # Send initial state
        logger.info(f"[TasmeeWS] Sending init message for session {session_id} with {total_words} words")
        await websocket.send_json({
            "type": "init",
            "total_words": total_words,
            "pointer": reveal_state["pointer"],
            "revealed_up_to": reveal_state["revealed_up_to"],
            "reveal_mode": reveal_state["reveal_mode"],
            "words": [{"word": w.original, "position": w.position, "is_revealed": i < reveal_state["revealed_up_to"]} for i, w in enumerate(words)],
        })
        logger.info(f"[TasmeeWS] Init message sent for session {session_id}")

        async def handle_pointer_advance(new_position: int) -> None:
            """Handle pointer advancement and reveal logic."""
            nonlocal reveal_state

            old_pointer = reveal_state["pointer"]
            reveal_state["pointer"] = new_position
            progress = new_position / total_words if total_words > 0 else 1.0

            # Determine what to reveal based on mode
            new_revealed = reveal_state["revealed_up_to"]

            logger.info(f"[TasmeeReveal] Mode={reveal_state['reveal_mode']}, progress={progress:.2f}, current_revealed={reveal_state['revealed_up_to']}")

            if reveal_state["reveal_mode"] == "auto":
                # Auto reveal: reveal all words up to pointer
                new_revealed = max(reveal_state["revealed_up_to"], new_position)
                logger.info(f"[TasmeeReveal] Auto mode: revealing up to {new_revealed}")
            elif reveal_state["reveal_mode"] == "hybrid":
                # Hybrid: auto until threshold, then require taps
                if progress < reveal_state["hybrid_threshold"]:
                    new_revealed = max(reveal_state["revealed_up_to"], new_position)
                    logger.info(f"[TasmeeReveal] Hybrid mode (below threshold): revealing up to {new_revealed}")
                else:
                    logger.info(f"[TasmeeReveal] Hybrid mode (above threshold): not auto-revealing")
            else:
                logger.info(f"[TasmeeReveal] Smart tap mode: not auto-revealing")
            # smart_tap: never auto-reveal

            # Send pointer update
            pointer_msg = {
                "type": "pointer_update",
                "position": new_position,
                "previous_position": old_pointer,
                "progress": progress,
                "revealed_up_to": new_revealed,
                "is_complete": new_position >= total_words,
            }
            logger.info(f"[TasmeeWS] Sending pointer_update: {pointer_msg}")
            await websocket.send_json(pointer_msg)

            # Send reveal_words if words were revealed
            if new_revealed > reveal_state["revealed_up_to"]:
                revealed_words = [
                    {"word": words[i].original, "position": i}
                    for i in range(reveal_state["revealed_up_to"], new_revealed)
                ]
                await websocket.send_json({
                    "type": "reveal_words",
                    "words": revealed_words,
                    "reveal_source": "alignment",
                    "revealed_up_to": new_revealed,
                })
                reveal_state["revealed_up_to"] = new_revealed

        async def handle_reveal_request(count: int) -> None:
            """Handle tap-to-reveal request."""
            nonlocal reveal_state

            logger.info(f"[TasmeeReveal] Tap reveal request: count={count}, current_revealed={reveal_state['revealed_up_to']}")

            # Reveal next N words (but not past total)
            new_revealed = min(
                reveal_state["revealed_up_to"] + count,
                total_words
            )

            if new_revealed > reveal_state["revealed_up_to"]:
                revealed_words = [
                    {"word": words[i].original, "position": i}
                    for i in range(reveal_state["revealed_up_to"], new_revealed)
                ]
                reveal_msg = {
                    "type": "reveal_words",
                    "words": revealed_words,
                    "reveal_source": "tap",
                    "revealed_up_to": new_revealed,
                }
                logger.info(f"[TasmeeWS] Sending reveal_words: {len(revealed_words)} words, new revealed_up_to={new_revealed}")
                await websocket.send_json(reveal_msg)
                reveal_state["revealed_up_to"] = new_revealed
            else:
                logger.info(f"[TasmeeReveal] No new words to reveal (already at {reveal_state['revealed_up_to']})")

        async def handle_config_update(config: dict) -> None:
            """Handle configuration updates."""
            nonlocal reveal_state

            if "reveal_mode" in config:
                reveal_state["reveal_mode"] = config["reveal_mode"]
            if "tap_reveal_count" in config:
                reveal_state["tap_reveal_count"] = config["tap_reveal_count"]
            if "hybrid_threshold" in config:
                reveal_state["hybrid_threshold"] = config["hybrid_threshold"]

            await websocket.send_json({
                "type": "config_updated",
                "reveal_mode": reveal_state["reveal_mode"],
                "tap_reveal_count": reveal_state["tap_reveal_count"],
                "hybrid_threshold": reveal_state["hybrid_threshold"],
            })

        # Audio logging state
        audio_chunk_count = 0
        total_audio_bytes = 0
        last_log_time = asyncio.get_event_loop().time()

        try:
            while True:
                # Receive data (can be binary audio or JSON message)
                message = await websocket.receive()

                if "bytes" in message:
                    # Binary audio data
                    data = message["bytes"]
                    audio_chunk_count += 1
                    total_audio_bytes += len(data)

                    # Log every 10th chunk
                    if audio_chunk_count % 10 == 1:
                        current_time = asyncio.get_event_loop().time()
                        elapsed = current_time - last_log_time
                        logger.info(f"[TasmeeAudio] Received chunk #{audio_chunk_count}: {len(data)} bytes, total: {total_audio_bytes} bytes")
                        last_log_time = current_time

                    # Convert to numpy float32
                    chunk = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

                    # Log buffer state
                    if audio_chunk_count % 10 == 1:
                        logger.info(f"[TasmeeAudio] Buffer state: {audio_buffer.buffer_duration:.2f}s / {audio_buffer.window_duration:.2f}s window, need {audio_buffer.step_samples} samples for step")

                    # Add to rolling buffer
                    window = audio_buffer.add_chunk(chunk)

                    if window is not None:
                        logger.info(f"[TasmeeAudio] Buffer ready for STT: {len(window)} samples ({len(window)/16000:.2f}s)")
                        # Transcribe the window (HTTP call to HF — off the event loop)
                        try:
                            stt_result = await asyncio.to_thread(
                                stt_provider.transcribe, window, word_timestamps=True
                            )
                            stt_failures = 0
                        except HFInferenceError as e:
                            stt_failures += 1
                            logger.warning(f"[TasmeeSTT] window failed ({stt_failures}): {e}")
                            await websocket.send_json({
                                "type": "stt_unavailable",
                                "reason": "ai_quota_exceeded" if e.kind == HFErrorKind.QUOTA else e.kind.value,
                            })
                            if stt_failures >= 3:
                                await websocket.close(code=4003, reason="stt_unavailable")
                                return
                            continue

                        if stt_result.segments:
                            # Log transcription result
                            transcript_text = " ".join(s.text for s in stt_result.segments)
                            logger.info(f"[TasmeeSTT] Transcribed: '{transcript_text[:100]}...' ({len(stt_result.segments)} segments)")
                        else:
                            logger.debug("[TasmeeSTT] No speech detected in window")

                        if stt_result.segments:
                            # Track position before processing
                            old_position = aligner.state.current_position

                            # Process segments through aligner
                            all_mistakes = []
                            for segment in stt_result.segments:
                                alignment_result = aligner.process_segment(segment)
                                all_mistakes.extend(alignment_result.mistakes)

                            # Check if pointer advanced
                            new_position = aligner.state.current_position
                            logger.info(f"[TasmeeAlign] Position: old={old_position}, new={new_position}")
                            if new_position > old_position:
                                logger.info(f"[TasmeeAlign] Pointer advanced! Sending pointer_update")
                                await handle_pointer_advance(new_position)

                            # Send mistake alerts
                            for mistake in all_mistakes:
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

                            # Update session in database
                            tasmee_session.words_completed = new_position
                            tasmee_session.mistakes_count = len(aligner.state.mistakes)
                            await db_session.commit()

                elif "text" in message:
                    # JSON message
                    logger.info(f"[TasmeeWS] Received text message: {message['text'][:200]}")
                    try:
                        msg_data = eval(message["text"]) if isinstance(message["text"], str) else message["text"]
                        if isinstance(msg_data, str):
                            import json
                            msg_data = json.loads(msg_data)

                        msg_type = msg_data.get("type")
                        logger.info(f"[TasmeeWS] Parsed message type: {msg_type}")

                        if msg_type == "reveal_request":
                            count = msg_data.get("count", reveal_state["tap_reveal_count"])
                            logger.info(f"[TasmeeWS] Handling reveal_request with count={count}")
                            await handle_reveal_request(count)

                        elif msg_type == "config_update":
                            logger.info(f"[TasmeeWS] Handling config_update: {msg_data}")
                            await handle_config_update(msg_data)

                        elif msg_type == "reset":
                            # Reset alignment state
                            aligner.reset()
                            audio_buffer.reset()
                            reveal_state["pointer"] = 0
                            reveal_state["revealed_up_to"] = 0
                            await websocket.send_json({
                                "type": "reset_complete",
                                "pointer": 0,
                                "revealed_up_to": 0,
                            })

                    except Exception as e:
                        logger.warning(f"Failed to parse JSON message: {e}")

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for session {session_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            try:
                await websocket.close(code=4000, reason="internal_error")
            except RuntimeError:
                pass  # Connection already closed
        finally:
            stt_provider.unload_model()
            await db_session.commit()


# ============================================================================
# Mistake and Progress Endpoints
# ============================================================================


@router.get("/sessions/{session_id}/mistakes", tags=["Mistakes"])
async def get_session_mistakes(
    session_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """Get all mistakes for a session."""
    query = (
        select(TasmeeMistake)
        .where(TasmeeMistake.session_id == session_id)
        .order_by(TasmeeMistake.timestamp)
    )
    result = await session.execute(query)
    mistakes = result.scalars().all()

    return {
        "mistakes": [m.to_dict() for m in mistakes],
        "count": len(mistakes),
    }


@router.get("/progress", tags=["Progress"])
async def get_progress(
    user_id: Optional[str] = None,
    device_id: Optional[str] = None,
    sura_no: Optional[int] = None,
    session: AsyncSession = Depends(get_async_session),
):
    """Get memorization progress."""
    query = select(TasmeeProgress)

    if user_id:
        query = query.where(TasmeeProgress.user_id == user_id)
    if device_id:
        query = query.where(TasmeeProgress.device_id == device_id)
    if sura_no:
        query = query.where(TasmeeProgress.sura_no == sura_no)

    query = query.order_by(TasmeeProgress.sura_no, TasmeeProgress.aya_no)
    result = await session.execute(query)
    progress_records = result.scalars().all()

    return {
        "progress": [p.to_dict() for p in progress_records],
        "count": len(progress_records),
    }


@router.get("/stats", tags=["Statistics"])
async def get_statistics(
    user_id: Optional[str] = None,
    session: AsyncSession = Depends(get_async_session),
):
    """Get overall memorization statistics."""
    # Total sessions
    sessions_query = select(func.count(TasmeeSession.id))
    if user_id:
        sessions_query = sessions_query.where(TasmeeSession.user_id == user_id)
    total_sessions = (await session.execute(sessions_query)).scalar() or 0

    # Completed sessions
    completed_query = sessions_query.where(
        TasmeeSession.status == SessionStatus.COMPLETED
    )
    completed_sessions = (await session.execute(completed_query)).scalar() or 0

    # Average accuracy
    accuracy_query = select(func.avg(TasmeeSession.accuracy_score)).where(
        TasmeeSession.accuracy_score.isnot(None)
    )
    if user_id:
        accuracy_query = accuracy_query.where(TasmeeSession.user_id == user_id)
    avg_accuracy = (await session.execute(accuracy_query)).scalar() or 0.0

    # Total words practiced
    words_query = select(func.sum(TasmeeSession.words_completed))
    if user_id:
        words_query = words_query.where(TasmeeSession.user_id == user_id)
    total_words = (await session.execute(words_query)).scalar() or 0

    # Total mistakes
    mistakes_query = select(func.count(TasmeeMistake.id))
    if user_id:
        mistakes_query = mistakes_query.join(TasmeeSession).where(
            TasmeeSession.user_id == user_id
        )
    total_mistakes = (await session.execute(mistakes_query)).scalar() or 0

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
    """Check if Tasmee service is healthy."""
    # STT runs on Hugging Face; availability = provider constructs and HF is configured.
    try:
        provider = get_stt_provider()
        provider.load_model()
        stt_available = True
        stt_error = None
    except HFInferenceError as e:
        stt_available = False
        stt_error = e.kind.value
    except Exception:
        stt_available = False
        stt_error = "provider_error"

    return {
        "status": "healthy" if stt_available else "degraded",
        "stt_provider": settings.stt_provider,
        "stt_model": settings.hf_stt_model if settings.stt_provider == "huggingface" else None,
        "stt_available": stt_available,
        "stt_error": stt_error,
        "audio_storage_dir": AUDIO_STORAGE_DIR,
        "audio_storage_writable": os.access(AUDIO_STORAGE_DIR, os.W_OK),
    }
