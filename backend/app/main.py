"""
Tadabbur-AI FastAPI Application

RAG-grounded Quranic knowledge platform with story connections.
"""
import time
import uuid
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

import os

from app.core.config import settings


def _cors_origins() -> list[str]:
    """CORS origins from env (CORS_ORIGINS=url1,url2) with localhost fallback."""
    env = os.getenv("CORS_ORIGINS", "")
    if env.strip():
        return [o.strip() for o in env.split(",") if o.strip()]
    return [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:8002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]
from app.core.responses import APIError, ErrorCode, error_response, ErrorDetail
from app.api.routes import quran, stories, rag, rag_verse, health, translation, story_atlas, story_atlas_registry, concepts, grammar, kg, tafseer, search, admin, graph, streaming, performance, rhetoric, themes, tasmee, review_tasks, vocabulary, feedback, therapy, asma, prophets, entities, topics, surah_atlas_intelligence, memorization, mushaf, adhkar, duas, asbab, quiz

# Configure structured logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan handler.
    Runs on startup and shutdown.
    """
    # Startup
    print(f"Starting {settings.app_name}...")
    print(f"Environment: {settings.environment}")
    print(f"Debug: {settings.debug}")

    # Initialize fast similarity service in background
    from app.services.fast_similarity import get_fast_similarity_service
    from app.db.database import get_async_session

    async def init_fast_similarity():
        try:
            async for session in get_async_session():
                service = get_fast_similarity_service()
                await service.initialize(session)
                print("FastSimilarityService initialized successfully")
                break
        except Exception as e:
            print(f"Warning: FastSimilarityService initialization failed: {e}")

    # Run initialization in background task
    import asyncio
    asyncio.create_task(init_fast_similarity())

    # Warm up the NLI emotion classifier in a background thread so the first
    # HTTP request does not pay the model-loading latency (~5–30 s on first run).
    if settings.emotion_classifier_enabled:
        from app.services.emotion_classifier import get_classifier

        async def _warmup_emotion_classifier() -> None:
            try:
                clf = get_classifier(
                    model_name=settings.emotion_model_name,
                    confidence_threshold=settings.emotion_confidence_threshold,
                )
                ok = await asyncio.to_thread(clf.warmup)
                status_str = "ready" if ok else "keyword-fallback (model unavailable)"
                print(f"Emotion classifier: {status_str}")
            except Exception as exc:
                print(f"Warning: Emotion classifier warmup failed: {exc}")

        asyncio.create_task(_warmup_emotion_classifier())

    # Pre-warm the Asmā' Allah atlas so the first /api/v1/quran/asma request
    # doesn't pay the ~700ms cold parse latency on a user's first navigation.
    # Cheap (one-shot file read + JSON parse), so we do it inline at startup
    # rather than as a background task — gives a deterministic hit on boot.
    try:
        from app.api.routes.asma import _load_atlas
        _load_atlas()  # populates the lru_cache
        print("Asmā' atlas: pre-warmed")
    except Exception as exc:
        print(f"Warning: Asmā' atlas pre-warm skipped ({exc})")

    yield

    # Shutdown
    print(f"Shutting down {settings.app_name}...")


app = FastAPI(
    title=settings.app_name,
    description="RAG-grounded Quranic knowledge platform with story connections",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Compress JSON responses >= 1KB (verse lists, tafseer chunks, search results)
app.add_middleware(GZipMiddleware, minimum_size=1024)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


MAX_REQUEST_BODY = 512_000  # 512 KB

@app.middleware("http")
async def enforce_body_size(request: Request, call_next):
    """Reject requests whose body exceeds MAX_REQUEST_BODY."""
    if request.method in ("POST", "PUT", "PATCH"):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_REQUEST_BODY:
            return JSONResponse(
                status_code=413,
                content={"ok": False, "error_code": "PAYLOAD_TOO_LARGE",
                         "message_en": "Request body exceeds 512 KB limit.",
                         "message_ar": "حجم الطلب يتجاوز الحد المسموح به (512 كيلوبايت)."},
            )
    return await call_next(request)


@app.middleware("http")
async def add_request_headers(request: Request, call_next):
    """Add request-id and processing time to response headers."""
    # Generate or extract request ID
    request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))

    # Store in request state for access in handlers
    request.state.request_id = request_id

    start_time = time.time()

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # Add headers
        response.headers["X-Request-Id"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Log request completion
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"-> {response.status_code} ({process_time:.3f}s)"
        )

        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"[{request_id}] {request.method} {request.url.path} "
            f"-> ERROR ({process_time:.3f}s): {str(e)}"
        )
        raise


@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    """Handle custom API errors with standardized envelope."""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    exc.request_id = request_id
    logger.warning(
        f"[{request_id}] API Error: {exc.error_code.value} - {exc.message_en}",
        extra={"error_code": exc.error_code.value, "request_id": request_id}
    )
    return exc.to_response()


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with standardized envelope."""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))

    details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error.get("loc", []))
        details.append(ErrorDetail(
            field=field,
            message=error.get("msg", "Validation error"),
            message_ar="خطأ في التحقق"
        ))

    logger.warning(
        f"[{request_id}] Validation Error: {len(details)} field errors",
        extra={"request_id": request_id, "errors": [d.model_dump() for d in details]}
    )

    return error_response(
        code=ErrorCode.VALIDATION_ERROR,
        message_en=f"Validation failed: {len(details)} error(s)",
        message_ar=f"فشل التحقق: {len(details)} خطأ",
        request_id=request_id,
        status_code=422,
        details=details
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with standardized error envelope."""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    logger.error(f"[{request_id}] Unhandled exception: {str(exc)}", exc_info=True)

    # In production, hide internal details
    message_en = str(exc) if settings.debug else "An internal error occurred"

    return error_response(
        code=ErrorCode.INTERNAL_ERROR,
        message_en=message_en,
        message_ar="حدث خطأ داخلي. تم تسجيل المشكلة.",
        request_id=request_id,
        status_code=500
    )


# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(quran.router, prefix="/api/v1/quran", tags=["Quran"])
app.include_router(stories.router, prefix="/api/v1/stories", tags=["Stories"])
app.include_router(rag.router, prefix="/api/v1/rag", tags=["RAG"])
app.include_router(rag_verse.router, prefix="/api/v1/rag", tags=["RAG Verse (Phase Y)"])
app.include_router(translation.router, prefix="/api/v1", tags=["Translation"])
app.include_router(story_atlas.router, prefix="/api/v1/story-atlas", tags=["Story Atlas"])
app.include_router(concepts.router, prefix="/api/v1/concepts", tags=["Concepts"])
app.include_router(grammar.router, prefix="/api/v1/grammar", tags=["Grammar"])
app.include_router(kg.router, prefix="/api/v1/kg", tags=["Knowledge Graph"])
app.include_router(tafseer.router, prefix="/api/v1", tags=["Tafseer"])
app.include_router(search.router, prefix="/api/v1/search", tags=["Search"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(graph.router, prefix="/api/v1/graph", tags=["Graph & Semantic"])
app.include_router(streaming.router, prefix="/api/v1", tags=["Streaming"])
app.include_router(performance.router, prefix="/api/v1", tags=["Performance"])
app.include_router(rhetoric.router, prefix="/api/v1/rhetoric", tags=["Rhetoric"])
app.include_router(themes.router, prefix="/api/v1/themes", tags=["Quranic Themes"])
app.include_router(tasmee.router, prefix="/api/v1/tasmee", tags=["Tasmee (Memorization)"])
app.include_router(review_tasks.router, prefix="/api/v1/admin", tags=["Review Workflow (Phase 6)"])
app.include_router(vocabulary.router, prefix="/api/v1/vocabulary", tags=["Vocabulary (Phase F)"])
app.include_router(feedback.router, prefix="/api/v1/feedback", tags=["User Feedback (Phase G)"])
app.include_router(therapy.router, prefix="/api/v1/therapy", tags=["Spiritual Guidance (Phase T)"])
app.include_router(asma.router, prefix="/api/v1/quran", tags=["Asmā' Allah Atlas (Phase W)"])
app.include_router(entities.router, prefix="/api/v1/quran", tags=["Entities (Phase T)"])
app.include_router(topics.router, prefix="/api/v1/quran", tags=["Topics (Phase V)"])
app.include_router(prophets.router, prefix="/api/v1/quran", tags=["Prophets Atlas (Phase X)"])
app.include_router(story_atlas_registry.router, prefix="/api/v1/quran", tags=["Story Atlas Registry"])
app.include_router(surah_atlas_intelligence.router, prefix="/api/v1/surah-atlas", tags=["Surah Atlas Intelligence"])
app.include_router(memorization.router, prefix="/api/v1/memorization", tags=["Memorization Intelligence"])
app.include_router(mushaf.router, prefix="/api/v1/mushaf", tags=["Mushaf Layout"])
app.include_router(adhkar.router, prefix="/api/v1/dhikr", tags=["Dhikr Sessions (Phase D)"])
app.include_router(duas.router, prefix="/api/v1/duas", tags=["Quranic Duas"])
app.include_router(asbab.router, prefix="/api/v1/quran", tags=["Asbab al-Nuzul"])
app.include_router(quiz.router, prefix="/api/v1/quiz", tags=["AI Quiz Generator"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs" if settings.debug else "disabled",
    }
