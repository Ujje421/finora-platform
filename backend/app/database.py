"""
Financial Intelligence Platform — Database Connection

Async SQLAlchemy engine with connection pooling.
Uses asyncpg driver for PostgreSQL with pgvector extension.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings
from app.utils.logging import get_logger

log = get_logger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


# Engine and session factory (initialized lazily)
_engine = None
_session_factory = None


def get_engine():
    """Get or create the async SQLAlchemy engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_pre_ping=True,  # Verify connections before use
            echo=settings.app_debug,  # SQL logging in dev
        )
        log.info(
            "Database engine created",
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the async session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def get_db() -> AsyncSession:
    """
    FastAPI dependency: yields an async database session.

    Usage:
        @router.get("/companies")
        async def list_companies(db: AsyncSession = Depends(get_db)):
            ...
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database connection and verify connectivity.
    Called during application startup.
    """
    engine = get_engine()
    async with engine.begin() as conn:
        # Verify connection works
        result = await conn.execute(
            __import__("sqlalchemy").text("SELECT 1")
        )
        assert result.scalar() == 1

        # Ensure pgvector extension exists
        await conn.execute(
            __import__("sqlalchemy").text("CREATE EXTENSION IF NOT EXISTS vector")
        )

    log.info("Database initialized successfully — pgvector extension enabled")


async def close_db() -> None:
    """Close database connections. Called during application shutdown."""
    global _engine, _session_factory
    if _engine:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        log.info("Database connections closed")
