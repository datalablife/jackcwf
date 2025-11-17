"""
Remote PostgreSQL Database Setup and Verification Script
For Coolify PostgreSQL instance with pgvector support

SECURITY: This script reads all credentials from environment variables.
No hardcoded passwords, usernames, or connection details are allowed.
"""

import asyncio
import os
import sys
from typing import Optional
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool

# Setup logging with security in mind
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConfigError(Exception):
    """Raised when database configuration is invalid or missing."""

    pass


def _get_required_env(var_name: str, description: str) -> str:
    """
    Get a required environment variable with proper error handling.

    Args:
        var_name: Name of the environment variable
        description: Human-readable description

    Returns:
        The environment variable value

    Raises:
        DatabaseConfigError: If the variable is not set

    Security Note:
        - Never includes the variable value in error messages
        - Provides clear guidance on how to fix
    """
    value = os.getenv(var_name)

    if not value or not value.strip():
        raise DatabaseConfigError(
            f"\nMissing required environment variable: {var_name}\n"
            f"Description: {description}\n"
            f"\nHow to fix:\n"
            f"  1. Ensure .env file is created from .env.example\n"
            f"  2. Set {var_name}=<your-actual-value> in .env\n"
            f"  3. Make sure .env is in .gitignore\n"
            f"\nFor detailed instructions: docs/SECURE_DATABASE_SETUP.md\n"
        )

    return value.strip()


class RemotePostgresSetup:
    """Setup and verify remote PostgreSQL database connection."""

    def __init__(self):
        """
        Initialize with database configuration from environment variables.

        SECURITY: All credentials come from environment variables, not defaults.
        Fails immediately if required configuration is missing.
        """
        try:
            # Get DATABASE_URL from environment
            # This is the primary configuration method
            self.database_url = _get_required_env(
                "DATABASE_URL",
                "PostgreSQL async connection string "
                "(postgresql+asyncpg://user:password@host:port/db)"
            )

            # Also get individual components from environment for verification
            self.host = _get_required_env(
                "POSTGRES_HOST",
                "PostgreSQL host/server address"
            )
            self.port = int(
                _get_required_env(
                    "POSTGRES_PORT",
                    "PostgreSQL port number (default: 5432)"
                )
            )
            self.user = _get_required_env(
                "POSTGRES_USER",
                "PostgreSQL username"
            )
            self.db = _get_required_env(
                "POSTGRES_DB",
                "PostgreSQL database name"
            )

            self.engine = None
            self.session_maker = None

        except DatabaseConfigError as e:
            logger.error(str(e))
            raise

    async def connect(self) -> bool:
        """
        Test database connection.

        Returns:
            bool: True if connection successful, False otherwise

        Security Note:
            - Doesn't expose connection details in error messages
            - Logs only that connection was attempted, not details
        """
        try:
            logger.info(f"Connecting to PostgreSQL at {self.host}:{self.port}...")
            self.engine = create_async_engine(
                self.database_url,
                echo=False,  # Never echo SQL - might contain credentials
                poolclass=NullPool,
                connect_args={
                    "timeout": 30,
                    "command_timeout": 60,
                    "server_settings": {
                        "application_name": "langchain_ai_setup",
                        "jit": "off",
                    }
                },
            )
            self.session_maker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

            # Test connection
            async with self.engine.connect() as conn:
                result = await conn.execute(text("SELECT version();"))
                version = result.scalar()
                logger.info(f"✅ Connected to PostgreSQL: {version}")
                return True

        except Exception as e:
            # Log error without exposing credentials
            logger.error(
                f"❌ Connection failed: {type(e).__name__}\n"
                f"   Please verify your DATABASE_URL is correct.\n"
                f"   See: docs/SECURE_DATABASE_SETUP.md"
            )
            return False

    async def check_pgvector_extension(self) -> bool:
        """
        Check if pgvector extension is installed.

        Returns:
            bool: True if pgvector is available, False otherwise
        """
        if not self.session_maker:
            logger.warning("⚠️  Session maker not initialized")
            return False

        try:
            async with self.session_maker() as session:
                result = await session.execute(
                    text("SELECT version FROM pg_extension WHERE extname = 'vector';")
                )
                version = result.scalar()
                if version:
                    logger.info(f"✅ pgvector extension found: version {version}")
                    return True
                else:
                    logger.warning("⚠️  pgvector extension not installed")
                    return False
        except Exception as e:
            logger.warning(f"⚠️  pgvector check failed: {type(e).__name__}")
            return False

    async def enable_pgvector_extension(self) -> bool:
        """
        Enable pgvector extension if not already enabled.

        Returns:
            bool: True if extension enabled/already exists, False otherwise
        """
        if not self.session_maker:
            logger.warning("⚠️  Session maker not initialized")
            return False

        try:
            async with self.session_maker() as session:
                try:
                    await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                    await session.commit()
                    logger.info("✅ pgvector extension enabled")
                    return True
                except Exception as e:
                    logger.warning(
                        f"⚠️  Could not enable pgvector: {type(e).__name__}\n"
                        f"   This might be due to permissions."
                    )
                    # Check if it's already enabled anyway
                    return await self.check_pgvector_extension()
        except Exception as e:
            logger.error(f"❌ Extension setup failed: {type(e).__name__}")
            return False

    async def check_database_permissions(self) -> bool:
        """
        Check database permissions and capabilities.

        Returns:
            bool: True if permissions are adequate, False otherwise
        """
        if not self.session_maker:
            logger.warning("⚠️  Session maker not initialized")
            return False

        try:
            async with self.session_maker() as session:
                # Check if we can create tables
                await session.execute(text("CREATE TEMPORARY TABLE perm_test (id SERIAL);"))
                await session.execute(text("DROP TABLE perm_test;"))
                logger.info("✅ Database permissions are adequate")
                return True
        except Exception as e:
            logger.warning(f"⚠️  Permission check: {type(e).__name__}")
            return False

    async def get_database_stats(self) -> dict:
        """
        Get useful database statistics.

        Returns:
            dict: Database statistics

        Security Note:
            - Only returns non-sensitive statistics
            - Doesn't expose user information or credentials
        """
        if not self.session_maker:
            logger.warning("⚠️  Session maker not initialized")
            return {}

        try:
            stats = {}
            async with self.session_maker() as session:
                # Get database size
                result = await session.execute(
                    text(
                        "SELECT pg_database.datname, "
                        "pg_size_pretty(pg_database_size(pg_database.datname)) "
                        "FROM pg_database WHERE datname = current_database();"
                    )
                )
                db_size = result.fetchone()
                if db_size:
                    stats['database_size'] = db_size[1]

                # Get table count
                result = await session.execute(
                    text(
                        "SELECT count(*) FROM information_schema.tables "
                        "WHERE table_schema = 'public';"
                    )
                )
                stats['table_count'] = result.scalar()

                # Get installed extensions
                result = await session.execute(
                    text("SELECT extname FROM pg_extension;")
                )
                stats['extensions'] = [row[0] for row in result.fetchall()]

                # Get PostgreSQL version
                result = await session.execute(text("SELECT version();"))
                stats['postgres_version'] = result.scalar()

                return stats
        except Exception as e:
            logger.error(f"❌ Failed to get stats: {type(e).__name__}")
            return {}

    async def run_full_setup(self) -> bool:
        """
        Run full setup and verification.

        Returns:
            bool: True if all checks passed, False otherwise
        """
        logger.info("=" * 70)
        logger.info("Remote PostgreSQL Database Setup and Verification")
        logger.info("=" * 70)

        # Step 1: Connect
        logger.info("\n[1/5] Testing database connection...")
        if not await self.connect():
            return False

        # Step 2: Check pgvector
        logger.info("\n[2/5] Checking pgvector extension...")
        if not await self.check_pgvector_extension():
            logger.info("Attempting to enable pgvector...")
            if not await self.enable_pgvector_extension():
                logger.warning("⚠️  pgvector not available - vector search will not work")

        # Step 3: Check permissions
        logger.info("\n[3/5] Checking database permissions...")
        if not await self.check_database_permissions():
            logger.error("❌ Insufficient permissions")
            return False

        # Step 4: Get statistics
        logger.info("\n[4/5] Gathering database statistics...")
        stats = await self.get_database_stats()
        if stats:
            logger.info("Database Statistics:")
            for key, value in stats.items():
                logger.info(f"  • {key}: {value}")

        # Step 5: Summary
        logger.info("\n[5/5] Setup Summary:")
        logger.info("=" * 70)
        logger.info("✅ PostgreSQL Setup Complete!")
        # Only log non-sensitive information
        logger.info(f"   Host: {self.host}:{self.port}")
        logger.info(f"   Database: {self.db}")
        logger.info("=" * 70)
        logger.info("\nFor security best practices, see: docs/SECURE_DATABASE_SETUP.md")

        if self.engine:
            await self.engine.dispose()
        return True


async def main():
    """
    Main entry point.

    Exits with:
        0 if setup successful
        1 if setup failed
    """
    try:
        setup = RemotePostgresSetup()
        success = await setup.run_full_setup()
        sys.exit(0 if success else 1)
    except DatabaseConfigError as e:
        # Configuration error - already logged
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {type(e).__name__}")
        logger.error("For help, see: docs/SECURE_DATABASE_SETUP.md")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
