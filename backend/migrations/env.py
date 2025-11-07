"""
Alembic migration environment configuration.

This module sets up the Alembic environment for database migrations.
It configures the SQLAlchemy models metadata for auto-migration detection
and handles both offline and online migration modes.
"""

import os
import sys
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Add backend src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the models' metadata for auto-migration detection
from src.db.base import Base
from src.models import *  # noqa

# Get Alembic configuration object
config = context.config

# Configure logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the target metadata for auto-migration detection
# This allows Alembic to detect schema changes in ORM models
target_metadata = Base.metadata


def get_db_url() -> str:
    """
    Get database URL from environment variable.

    Returns:
        str: DATABASE_URL from environment

    Raises:
        RuntimeError: If DATABASE_URL is not set
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set. "
            "Please configure it in .env file."
        )
    return db_url


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_db_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # Get database URL from environment
    url = get_db_url()

    # Create engine configuration
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# Determine whether to run migrations in offline or online mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
