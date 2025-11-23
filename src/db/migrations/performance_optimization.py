#!/usr/bin/env python3
"""
Database Performance Optimization Migration.

This migration adds strategic indexes to improve query performance
and eliminate common bottlenecks.

Run with:
    python -m src.db.migrations.performance_optimization
"""

import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Migration SQL
MIGRATION_SQL = """
-- ============================================================================
-- Performance Optimization Migration
-- Date: 2024
-- Description: Add strategic indexes for query optimization
-- ============================================================================

-- Track migration
CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(255) UNIQUE NOT NULL,
    applied_at TIMESTAMP DEFAULT NOW()
);

-- Check if this migration was already applied
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM schema_migrations WHERE migration_name = 'performance_optimization_v1'
    ) THEN
        -- ========================================================================
        -- 1. Conversation Indexes
        -- ========================================================================

        -- Index for recent conversations query (user + updated_at)
        CREATE INDEX IF NOT EXISTS idx_conv_user_updated
        ON conversations (user_id, updated_at DESC)
        WHERE is_deleted = false;

        -- Partial index for active conversations only
        CREATE INDEX IF NOT EXISTS idx_conv_active_user
        ON conversations (user_id, created_at DESC)
        WHERE is_deleted = false;

        -- Full-text search on conversation title (PostgreSQL)
        CREATE INDEX IF NOT EXISTS idx_conv_title_fulltext
        ON conversations USING gin(to_tsvector('english', title))
        WHERE is_deleted = false;

        -- Composite index for conversation search with filters
        CREATE INDEX IF NOT EXISTS idx_conv_user_model
        ON conversations (user_id, model, created_at DESC)
        WHERE is_deleted = false;

        -- ========================================================================
        -- 2. Message Indexes
        -- ========================================================================

        -- Index for message pagination (conversation + created_at)
        CREATE INDEX IF NOT EXISTS idx_msg_conv_created
        ON messages (conversation_id, created_at DESC);

        -- Index for role-based message filtering
        CREATE INDEX IF NOT EXISTS idx_msg_role_conv
        ON messages (role, conversation_id, created_at DESC);

        -- Index for token usage queries (analytics)
        CREATE INDEX IF NOT EXISTS idx_msg_tokens
        ON messages (conversation_id, tokens_used)
        WHERE tokens_used IS NOT NULL;

        -- ========================================================================
        -- 3. Document Indexes
        -- ========================================================================

        -- Index for document type filtering per user
        CREATE INDEX IF NOT EXISTS idx_doc_user_type_created
        ON documents (user_id, file_type, created_at DESC)
        WHERE is_deleted = false;

        -- Index for document size queries
        CREATE INDEX IF NOT EXISTS idx_doc_user_size
        ON documents (user_id, file_size)
        WHERE is_deleted = false;

        -- Full-text search on document filename
        CREATE INDEX IF NOT EXISTS idx_doc_filename_fulltext
        ON documents USING gin(to_tsvector('english', filename))
        WHERE is_deleted = false;

        -- ========================================================================
        -- 4. Optimize Existing Indexes (if needed)
        -- ========================================================================

        -- Analyze tables to update statistics
        ANALYZE conversations;
        ANALYZE messages;
        ANALYZE documents;

        -- Record migration
        INSERT INTO schema_migrations (migration_name)
        VALUES ('performance_optimization_v1');

        RAISE NOTICE 'Migration performance_optimization_v1 applied successfully';
    ELSE
        RAISE NOTICE 'Migration performance_optimization_v1 already applied, skipping';
    END IF;
END $$;
"""

# Rollback SQL (for development)
ROLLBACK_SQL = """
-- Rollback Performance Optimization Migration
DROP INDEX IF EXISTS idx_conv_user_updated;
DROP INDEX IF EXISTS idx_conv_active_user;
DROP INDEX IF EXISTS idx_conv_title_fulltext;
DROP INDEX IF EXISTS idx_conv_user_model;
DROP INDEX IF EXISTS idx_msg_conv_created;
DROP INDEX IF EXISTS idx_msg_role_conv;
DROP INDEX IF EXISTS idx_msg_tokens;
DROP INDEX IF EXISTS idx_doc_user_type_created;
DROP INDEX IF EXISTS idx_doc_user_size;
DROP INDEX IF EXISTS idx_doc_filename_fulltext;
DELETE FROM schema_migrations WHERE migration_name = 'performance_optimization_v1';
"""


async def apply_migration():
    """Apply performance optimization migration."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")

    engine = create_async_engine(database_url, echo=True)

    try:
        async with engine.begin() as conn:
            logger.info("Applying performance optimization migration...")

            # Execute migration
            await conn.execute(text(MIGRATION_SQL))

            logger.info("Migration applied successfully!")

            # Show created indexes
            result = await conn.execute(text("""
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                  AND indexname LIKE 'idx_%'
                ORDER BY tablename, indexname;
            """))

            logger.info("\n" + "="*80)
            logger.info("CREATED INDEXES:")
            logger.info("="*80)

            for row in result:
                logger.info(f"\nTable: {row[1]}")
                logger.info(f"Index: {row[2]}")
                logger.info(f"Definition: {row[3]}")

    finally:
        await engine.dispose()


async def rollback_migration():
    """Rollback performance optimization migration (development only)."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")

    # Safety check
    if os.getenv("ENVIRONMENT") == "production":
        logger.error("Cannot rollback migrations in production!")
        return

    engine = create_async_engine(database_url, echo=True)

    try:
        async with engine.begin() as conn:
            logger.warning("Rolling back performance optimization migration...")
            await conn.execute(text(ROLLBACK_SQL))
            logger.info("Rollback completed")

    finally:
        await engine.dispose()


async def analyze_query_performance():
    """Analyze current query performance and index usage."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")

    engine = create_async_engine(database_url)

    try:
        async with engine.begin() as conn:
            # Check index usage statistics
            logger.info("\n" + "="*80)
            logger.info("INDEX USAGE STATISTICS:")
            logger.info("="*80)

            result = await conn.execute(text("""
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan as index_scans,
                    idx_tup_read as tuples_read,
                    idx_tup_fetch as tuples_fetched
                FROM pg_stat_user_indexes
                WHERE schemaname = 'public'
                ORDER BY idx_scan DESC;
            """))

            for row in result:
                logger.info(
                    f"{row[1]}.{row[2]}: "
                    f"scans={row[3]}, read={row[4]}, fetched={row[5]}"
                )

            # Check table sizes
            logger.info("\n" + "="*80)
            logger.info("TABLE SIZES:")
            logger.info("="*80)

            result = await conn.execute(text("""
                SELECT
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
                    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as data_size,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as index_size
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
            """))

            for row in result:
                logger.info(
                    f"{row[1]}: total={row[2]}, data={row[3]}, indexes={row[4]}"
                )

    finally:
        await engine.dispose()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "apply":
            asyncio.run(apply_migration())
        elif command == "rollback":
            asyncio.run(rollback_migration())
        elif command == "analyze":
            asyncio.run(analyze_query_performance())
        else:
            print(f"Unknown command: {command}")
            print("Usage: python performance_optimization.py [apply|rollback|analyze]")
    else:
        # Default: apply migration
        asyncio.run(apply_migration())
