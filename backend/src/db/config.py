"""
Database configuration and session management.

This module sets up the SQLAlchemy async engine and session factory
for the AI Data Analyzer application.
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import event
from sqlalchemy.pool import NullPool, QueuePool

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "")


def _get_engine():
    """Lazily create and return the database engine."""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set")

    # Create async engine with connection pooling
    engine = create_async_engine(
        DATABASE_URL,
        echo=os.getenv("DEBUG", "false").lower() == "true",
        future=True,
        pool_pre_ping=True,  # Test connections before using them
        pool_size=20,  # Number of connections to keep in the pool
        max_overflow=10,  # Maximum number of overflow connections
        connect_args={
            "timeout": 10,
            "command_timeout": 10,
            "server_settings": {"application_name": "text2sql_backend"},
        },
    )
    return engine


# Create a lazy engine and session factory
engine = None
async_session_maker = None


def _init_session_maker():
    """Initialize the async session maker."""
    global engine, async_session_maker

    if engine is None:
        engine = _get_engine()

    if async_session_maker is None:
        async_session_maker = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )


async def get_async_session() -> AsyncSession:
    """
    Dependency for FastAPI to get async database session.

    Usage in FastAPI route:
        @app.get("/")
        async def read_root(session: AsyncSession = Depends(get_async_session)):
            result = await session.execute(select(SomeModel))
            return result.scalars().all()

    Yields:
        AsyncSession: SQLAlchemy async session

    Raises:
        Exception: If database connection fails
    """
    _init_session_maker()

    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables by creating all tables defined in Base.metadata.

    This should be called once at application startup to ensure all tables exist.
    After this, use Alembic migrations for schema changes.
    """
    from .base import Base

    _init_session_maker()

    async with engine.begin() as conn:
        # Create all tables defined in models
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created successfully")


async def close_db() -> None:
    """
    Close database engine and all connections.

    This should be called at application shutdown.
    """
    global engine

    if engine:
        await engine.dispose()
        engine = None
        print("✅ Database connections closed")

