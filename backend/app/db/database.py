"""
Database connection and session management.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# Convert sync URL to async
DATABASE_URL_ASYNC = settings.database_url.replace(
    "postgresql://", "postgresql+asyncpg://"
)

# Async engine for FastAPI - optimized for performance
async_engine = create_async_engine(
    DATABASE_URL_ASYNC,
    echo=False,  # Disable SQL logging in production for performance
    pool_pre_ping=True,
    pool_size=25,  # Increased from 10 for higher concurrency
    max_overflow=50,  # Increased from 20 for burst traffic
    pool_recycle=3600,  # Recycle connections every hour to prevent stale connections
    pool_timeout=30,  # Wait up to 30s for a connection
)

# Sync engine for Alembic migrations and scripts
sync_engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)

# Session factories
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


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
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
