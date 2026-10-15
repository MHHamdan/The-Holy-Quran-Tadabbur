"""
Database connection and session management.

Connection budget: every uvicorn worker owns one async pool of
DB_POOL_SIZE + DB_MAX_OVERFLOW connections, so keep

    WORKERS * (DB_POOL_SIZE + DB_MAX_OVERFLOW) <= max_connections - 10

(Postgres default max_connections is 100; the margin covers migrations,
scripts, backups and psql). Requests that find the pool exhausted wait up to
DB_POOL_TIMEOUT seconds instead of failing with "too many clients".
"""
import os
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


DB_POOL_SIZE = _env_int("DB_POOL_SIZE", 10)
DB_MAX_OVERFLOW = _env_int("DB_MAX_OVERFLOW", 10)
DB_POOL_TIMEOUT = _env_int("DB_POOL_TIMEOUT", 10)

# Convert sync URL to async
DATABASE_URL_ASYNC = settings.database_url.replace(
    "postgresql://", "postgresql+asyncpg://"
)

# Async engine for FastAPI
async_engine = create_async_engine(
    DATABASE_URL_ASYNC,
    echo=False,  # Disable SQL logging in production for performance
    pool_pre_ping=True,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_recycle=3600,  # Recycle connections every hour to prevent stale connections
    pool_timeout=DB_POOL_TIMEOUT,
)

# Session factories
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()


@lru_cache(maxsize=1)
def get_sync_engine():
    """Sync engine for scripts, created on first use (the API never needs it,
    so API workers do not hold a second connection pool)."""
    return create_engine(
        settings.database_url,
        echo=settings.debug,
        pool_pre_ping=True,
    )


@lru_cache(maxsize=1)
def _sync_session_factory():
    return sessionmaker(bind=get_sync_engine(), autocommit=False, autoflush=False)


def __getattr__(name: str):
    # Lazy module attributes kept for scripts: `from app.db.database import
    # SyncSessionLocal` / `sync_engine` build the sync engine only when used.
    if name == "sync_engine":
        return get_sync_engine()
    if name == "SyncSessionLocal":
        return _sync_session_factory()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_async_session_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_session():
    """Get sync session for scripts."""
    session = _sync_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
