"""Database migration and initialization script."""

import asyncio
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine

from src.models import (
    ConversationORM,
    MessageORM,
    DocumentORM,
    EmbeddingORM,
)
from src.db.config import engine
from src.db.base import Base


async def init_db(db_engine: Optional[AsyncEngine] = None) -> None:
    """
    Initialize database with all tables and extensions.

    This function:
    1. Enables pgvector extension
    2. Creates all tables
    3. Creates indices
    4. Sets up partitioning for embeddings table

    Args:
        db_engine: AsyncEngine instance (uses global engine if not provided)
    """
    if db_engine is None:
        db_engine = engine

    async with db_engine.begin() as conn:
        # Enable pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # Create all tables from models
        await conn.run_sync(Base.metadata.create_all)

        # Create additional indices (some might already exist from model definition)
        try:
            # Vector HNSW index for embeddings
            await conn.execute(
                text("""
                    CREATE INDEX IF NOT EXISTS idx_embeddings_vector_hnsw
                    ON embeddings USING hnsw (embedding vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64)
                """)
            )
        except Exception as e:
            print(f"Warning: Could not create HNSW index: {e}")

        # Set up partitioning for embeddings table (by month)
        try:
            await setup_embeddings_partitioning(conn)
        except Exception as e:
            print(f"Warning: Could not set up partitioning: {e}")

        print("Database initialization completed successfully")


async def setup_embeddings_partitioning(conn) -> None:
    """
    Set up time-based partitioning for embeddings table.

    Partitions by month for better performance with large datasets.
    """
    from datetime import datetime, timedelta

    # Check if table already exists and has partitions
    result = await conn.execute(
        text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'embeddings'
            )
        """)
    )
    if not result.scalar():
        print("Embeddings table does not exist yet, skipping partitioning setup")
        return

    # Get current month
    now = datetime.utcnow()
    current_month = now.strftime("%Y_%m")
    next_month = (now + timedelta(days=32)).replace(day=1).strftime("%Y_%m")

    # Create partitions for current and next month
    for month_str in [current_month, next_month]:
        year, month = month_str.split("_")
        partition_name = f"embeddings_{year}_{month}"

        # Check if partition already exists
        result = await conn.execute(
            text(f"""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name = '{partition_name}'
                )
            """)
        )

        if not result.scalar():
            # Create partition
            start_date = f"{year}-{month}-01"
            if month == "12":
                end_date = f"{int(year) + 1}-01-01"
            else:
                end_date = f"{year}-{int(month) + 1:02d}-01"

            try:
                await conn.execute(
                    text(f"""
                        CREATE TABLE IF NOT EXISTS {partition_name} PARTITION OF embeddings
                        FOR VALUES FROM ('{start_date}') TO ('{end_date}')
                    """)
                )
                print(f"Created partition: {partition_name}")
            except Exception as e:
                print(f"Warning: Could not create partition {partition_name}: {e}")


async def drop_all_tables(db_engine: Optional[AsyncEngine] = None) -> None:
    """
    Drop all tables (use with caution!).

    Args:
        db_engine: AsyncEngine instance (uses global engine if not provided)
    """
    if db_engine is None:
        db_engine = engine

    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        print("All tables dropped successfully")


if __name__ == "__main__":
    # Run initialization when script is executed directly
    asyncio.run(init_db())
