"""
Database configuration for async SQLAlchemy with secure environment handling.

This module handles all database configuration and ensures all sensitive
information comes from environment variables, not hardcoded defaults.

Security principles:
- All credentials must come from environment variables
- No default values containing actual credentials
- Fail fast if required configuration is missing
- Don't expose sensitive information in logs or errors
"""

import os
from typing import AsyncGenerator, Optional

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.pool import NullPool


class DatabaseConfigError(Exception):
    """Raised when database configuration is invalid or missing."""

    pass


def _get_required_env(var_name: str, description: str) -> str:
    """
    Get a required environment variable with proper error handling.

    Args:
        var_name: Name of the environment variable
        description: Human-readable description of what this variable is for

    Returns:
        The environment variable value

    Raises:
        DatabaseConfigError: If the variable is not set

    Security Note:
        - Never includes the variable value in error messages
        - Provides clear guidance on how to fix the issue
    """
    value = os.getenv(var_name)

    if not value or not value.strip():
        raise DatabaseConfigError(
            f"\nMissing required environment variable: {var_name}\n"
            f"Description: {description}\n"
            f"\nHow to fix:\n"
            f"  1. Copy .env.example to .env (if you haven't already)\n"
            f"  2. Edit .env and set: {var_name}=<your-actual-value>\n"
            f"  3. Make sure .env is in .gitignore (prevent accidental commits)\n"
            f"\nFor detailed instructions, see: docs/SECURE_DATABASE_SETUP.md\n"
        )

    return value.strip()


def _get_optional_env(
    var_name: str, default: Optional[str] = None
) -> Optional[str]:
    """
    Get an optional environment variable.

    Args:
        var_name: Name of the environment variable
        default: Default value if not set (should be None or a safe value)

    Returns:
        The environment variable value or default

    Security Note:
        - Default values should never contain actual credentials
        - Only safe/placeholder values are allowed as defaults
    """
    value = os.getenv(var_name, default)
    return value.strip() if value else None


# Validate and load DATABASE_URL
# This is the primary configuration - it must be set
DATABASE_URL = _get_required_env(
    "DATABASE_URL",
    "PostgreSQL async connection string (postgresql+asyncpg://user:password@host:port/db)"
)

# Optional: override echo from environment
SQL_ECHO = _get_optional_env("SQL_ECHO", "false").lower() == "true"

# Optional: override connection timeout
CONNECTION_TIMEOUT = int(_get_optional_env("DB_CONNECTION_TIMEOUT", "10"))
COMMAND_TIMEOUT = int(_get_optional_env("DB_COMMAND_TIMEOUT", "60"))

# Optional: enable SQL query logging
DB_ECHO = SQL_ECHO

# Create async engine with optimized settings
# Use NullPool for async engines (QueuePool is not compatible with asyncio)
try:
    engine: AsyncEngine = create_async_engine(
        DATABASE_URL,
        echo=DB_ECHO,
        poolclass=NullPool,  # Use NullPool for async engines
        future=True,
        # Connection configuration
        connect_args={
            "timeout": CONNECTION_TIMEOUT,
            "command_timeout": COMMAND_TIMEOUT,
            "server_settings": {
                "application_name": _get_optional_env(
                    "DB_APPLICATION_NAME", "langchain_ai_app"
                ),
                "jit": "off",
            },
        },
    )
except Exception as e:
    raise DatabaseConfigError(
        f"\nFailed to create database engine: {type(e).__name__}\n"
        f"Please verify your DATABASE_URL is correct.\n"
        f"See: docs/SECURE_DATABASE_SETUP.md for more information.\n"
    )

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session.

    Usage in FastAPI:
        @app.get("/api/endpoint")
        async def my_endpoint(session: AsyncSession = Depends(get_async_session)):
            # Use session to query database
            ...

    This function ensures proper resource cleanup with try/finally pattern.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Event listeners for connection management
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """
    Set SQLite pragmas if using SQLite for testing.

    This is primarily for development/testing only.
    Production should use PostgreSQL.
    """
    if "sqlite" in str(dbapi_conn):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
