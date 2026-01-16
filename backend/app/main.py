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
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.core.config import settings
from app.core.responses import APIError, ErrorCode, error_response, ErrorDetail
from app.api.routes import quran, stories, rag, health, translation, story_atlas, concepts, grammar, kg, tafseer, search, admin, graph, streaming, performance, rhetoric, themes

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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://172.24.50.21:3000",
        "http://172.24.50.21:5173",  # Vite dev server
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs" if settings.debug else "disabled",
    }
