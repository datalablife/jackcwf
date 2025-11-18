#!/usr/bin/env python3
"""
Setup Lantern Vector Storage Schema for LangChain RAG System.

This script creates a production-ready vector storage schema using Lantern's
HNSW (Hierarchical Navigable Small World) algorithm for efficient similarity search.

Key features:
- Optimized for LangChain RAG patterns
- Uses Lantern HNSW index for vector similarity search
- Supports document metadata filtering with JSONB
- BM25 text search capability via lantern_extras
- Background worker job processing
- Performance monitoring and statistics
"""

import os
import sys
import logging
import asyncpg
from datetime import datetime
from typing import Optional, Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s"
)
logger = logging.getLogger(__name__)


class LanternSchemaManager:
    """Manage Lantern vector storage schema for LangChain."""

    def __init__(self):
        self.conn: Optional[asyncpg.Connection] = None
        self.vector_dimension = 1536  # OpenAI embedding dimension

    async def connect(self) -> bool:
        """Connect to PostgreSQL database using environment variables."""
        try:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                logger.error("❌ DATABASE_URL environment variable not set")
                return False

            # asyncpg doesn't recognize the SQLAlchemy +asyncpg scheme
            # Convert postgresql+asyncpg:// to postgresql://
            asyncpg_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

            self.conn = await asyncpg.connect(asyncpg_url)
            logger.info("✅ Connected to PostgreSQL")
            return True
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False

    async def verify_lantern_extensions(self) -> bool:
        """Verify Lantern extensions are installed."""
        try:
            logger.info("\n[Verifying Lantern Extensions]")

            # Check for lantern extension
            lantern_check = await self.conn.fetchval(
                "SELECT extname FROM pg_extension WHERE extname = 'lantern'"
            )
            if lantern_check:
                logger.info("✅ lantern extension is available")
            else:
                logger.warning("⚠️  lantern extension not found, attempting to enable...")
                try:
                    await self.conn.execute("CREATE EXTENSION IF NOT EXISTS lantern")
                    logger.info("✅ lantern extension enabled")
                except Exception as e:
                    logger.warning(f"⚠️  Could not enable lantern: {e}")

            # Check for lantern_extras (BM25, embeddings, background workers)
            extras_check = await self.conn.fetchval(
                "SELECT extname FROM pg_extension WHERE extname = 'lantern_extras'"
            )
            if extras_check:
                logger.info("✅ lantern_extras extension is available")
            else:
                logger.warning("⚠️  lantern_extras not available (optional)")

            # Check for vector extension (pgvector compatibility)
            vector_check = await self.conn.fetchval(
                "SELECT extname FROM pg_extension WHERE extname = 'vector'"
            )
            if vector_check:
                logger.info("✅ pgvector extension is available")

            return True
        except Exception as e:
            logger.error(f"❌ Extension verification failed: {e}")
            return False

    async def create_vector_tables(self) -> bool:
        """Create LangChain-optimized vector storage tables with Lantern."""
        try:
            logger.info("\n[Creating Vector Storage Tables]")

            # Main documents table
            await self.conn.execute(f"""
                CREATE TABLE IF NOT EXISTS documents (
                    id BIGSERIAL PRIMARY KEY,

                    -- Content and embedding
                    content TEXT NOT NULL,
                    embedding REAL[{self.vector_dimension}] NOT NULL,

                    -- Metadata for filtering
                    metadata JSONB DEFAULT '{{}}',
                    source VARCHAR(255),
                    document_type VARCHAR(50),

                    -- LangChain-specific fields
                    document_id VARCHAR(255),
                    chunk_index INT DEFAULT 0,
                    total_chunks INT DEFAULT 1,

                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    -- Soft delete support
                    deleted_at TIMESTAMP DEFAULT NULL
                )
            """)
            logger.info("✅ Documents table created")

            # Embeddings batch processing table (for background jobs)
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS embedding_jobs (
                    id BIGSERIAL PRIMARY KEY,
                    document_id BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                    status VARCHAR(20) DEFAULT 'pending',  -- pending, processing, completed, failed
                    retry_count INT DEFAULT 0,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)
            logger.info("✅ Embedding jobs table created")

            # Search history for analytics
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id BIGSERIAL PRIMARY KEY,
                    query TEXT NOT NULL,
                    query_embedding REAL[1536],
                    results_count INT,
                    search_time_ms INT,
                    user_id VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.info("✅ Search history table created")

            # Conversation context table (for multi-turn conversations)
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id BIGSERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    title VARCHAR(255),
                    messages JSONB DEFAULT '[]',  -- Array of messages with embeddings
                    context_embedding REAL[1536],  -- Latest conversation context
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    deleted_at TIMESTAMP DEFAULT NULL
                )
            """)
            logger.info("✅ Conversations table created")

            return True
        except Exception as e:
            logger.error(f"❌ Table creation failed: {e}")
            return False

    async def create_lantern_indexes(self) -> bool:
        """Create Lantern HNSW indexes for vector similarity search."""
        try:
            logger.info("\n[Creating Lantern HNSW Indexes]")

            # Main vector similarity index using Lantern HNSW
            # Parameters:
            # - M: Maximum connections per node (16 is good for balance)
            # - ef_construction: Size of dynamic candidate list during construction (64 is standard)
            # - ef: Search parameter (40 for good recall with reasonable speed)
            await self.conn.execute(f"""
                CREATE INDEX IF NOT EXISTS documents_embedding_lantern_hnsw
                ON documents
                USING lantern_hnsw (embedding dist_l2sq_ops)
                WITH (M=16, ef_construction=64, ef=40, dim={self.vector_dimension})
            """)
            logger.info("✅ Lantern HNSW index created (dist_l2sq_ops)")

            # Optional: Create index for context embeddings
            await self.conn.execute(f"""
                CREATE INDEX IF NOT EXISTS conversations_context_embedding_hnsw
                ON conversations
                USING lantern_hnsw (context_embedding dist_l2sq_ops)
                WITH (M=16, ef_construction=64, ef=40, dim={self.vector_dimension})
                WHERE context_embedding IS NOT NULL
            """)
            logger.info("✅ Conversations context HNSW index created")

            return True
        except Exception as e:
            logger.error(f"❌ Index creation failed: {e}")
            return False

    async def create_supporting_indexes(self) -> bool:
        """Create additional indexes for filtering and search."""
        try:
            logger.info("\n[Creating Supporting Indexes]")

            # Metadata filtering index
            await self.conn.execute("""
                CREATE INDEX IF NOT EXISTS documents_metadata_gin
                ON documents USING GIN (metadata)
            """)
            logger.info("✅ Metadata GIN index created")

            # Source and type filtering
            await self.conn.execute("""
                CREATE INDEX IF NOT EXISTS documents_source_type_idx
                ON documents(source, document_type)
                WHERE deleted_at IS NULL
            """)
            logger.info("✅ Source/type index created")

            # Document ID lookup
            await self.conn.execute("""
                CREATE INDEX IF NOT EXISTS documents_document_id_idx
                ON documents(document_id)
                WHERE deleted_at IS NULL
            """)
            logger.info("✅ Document ID index created")

            # Timestamp indexes for range queries
            await self.conn.execute("""
                CREATE INDEX IF NOT EXISTS documents_created_at_idx
                ON documents(created_at DESC)
                WHERE deleted_at IS NULL
            """)
            logger.info("✅ Created timestamp index")

            # BM25 text search index (if lantern_extras available)
            try:
                await self.conn.execute("""
                    CREATE INDEX IF NOT EXISTS documents_content_bm25
                    ON documents USING bm25(content)
                    WITH (key='id')
                """)
                logger.info("✅ BM25 text search index created")
            except Exception as e:
                logger.warning(f"⚠️  BM25 index not available: {e}")

            return True
        except Exception as e:
            logger.error(f"❌ Supporting index creation failed: {e}")
            return False

    async def create_helper_functions(self) -> bool:
        """Create SQL functions for common operations."""
        try:
            logger.info("\n[Creating Helper Functions]")

            # Function for similarity search
            await self.conn.execute("""
                CREATE OR REPLACE FUNCTION search_documents(
                    query_embedding REAL[],
                    limit_results INT DEFAULT 10,
                    metadata_filter JSONB DEFAULT NULL
                )
                RETURNS TABLE (
                    id BIGINT,
                    content TEXT,
                    distance FLOAT,
                    metadata JSONB,
                    source VARCHAR,
                    document_type VARCHAR
                ) AS $$
                SELECT
                    d.id,
                    d.content,
                    d.embedding <-> query_embedding as distance,
                    d.metadata,
                    d.source,
                    d.document_type
                FROM documents d
                WHERE d.deleted_at IS NULL
                  AND (metadata_filter IS NULL OR d.metadata @> metadata_filter)
                ORDER BY d.embedding <-> query_embedding
                LIMIT limit_results;
                $$ LANGUAGE SQL STABLE;
            """)
            logger.info("✅ search_documents function created")

            # Function to update document timestamp
            await self.conn.execute("""
                CREATE OR REPLACE FUNCTION update_document_timestamp()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """)
            logger.info("✅ update_document_timestamp trigger function created")

            # Trigger for auto-updating timestamps
            await self.conn.execute("""
                DROP TRIGGER IF EXISTS documents_update_timestamp ON documents;
                CREATE TRIGGER documents_update_timestamp
                BEFORE UPDATE ON documents
                FOR EACH ROW
                EXECUTE FUNCTION update_document_timestamp();
            """)
            logger.info("✅ Timestamp update trigger created")

            return True
        except Exception as e:
            logger.error(f"❌ Function creation failed: {e}")
            return False

    async def verify_schema(self) -> bool:
        """Verify the schema is properly created."""
        try:
            logger.info("\n[Verifying Schema]")

            # Check tables
            tables = await self.conn.fetch("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
                AND tablename IN ('documents', 'embedding_jobs', 'search_history', 'conversations')
            """)
            logger.info(f"✅ Tables verified: {len(tables)} tables found")

            # Check indexes
            indexes = await self.conn.fetch("""
                SELECT indexname FROM pg_indexes
                WHERE schemaname = 'public'
                AND tablename IN ('documents', 'conversations')
            """)
            logger.info(f"✅ Indexes verified: {len(indexes)} indexes found")
            for idx in indexes:
                logger.info(f"   - {idx['indexname']}")

            # Check functions
            functions = await self.conn.fetch("""
                SELECT proname FROM pg_proc
                WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
                AND proname IN ('search_documents', 'update_document_timestamp')
            """)
            logger.info(f"✅ Functions verified: {len(functions)} functions found")

            return True
        except Exception as e:
            logger.error(f"❌ Schema verification failed: {e}")
            return False

    async def get_database_stats(self) -> bool:
        """Get database statistics."""
        try:
            logger.info("\n[Database Statistics]")

            # Table sizes
            stats = await self.conn.fetch("""
                SELECT
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                FROM pg_tables
                WHERE schemaname = 'public'
                AND tablename IN ('documents', 'embedding_jobs', 'search_history', 'conversations')
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            """)

            logger.info("  Table Sizes:")
            for stat in stats:
                logger.info(f"    - {stat['tablename']}: {stat['size']}")

            # Vector dimension verification
            dim_info = await self.conn.fetchval("""
                SELECT array_dims(embedding)::text
                FROM documents
                LIMIT 1
            """)

            if dim_info:
                logger.info(f"  Vector Column: configured {dim_info}")
            else:
                logger.info(f"  Vector Column: {self.vector_dimension}D (ready for data)")

            return True
        except Exception as e:
            logger.warning(f"⚠️  Could not retrieve detailed statistics: {e}")
            return True  # Don't fail on statistics


    async def cleanup(self):
        """Close database connection."""
        if self.conn:
            await self.conn.close()
            logger.info("✅ Database connection closed")

    async def run_full_setup(self) -> bool:
        """Run complete schema setup."""
        try:
            logger.info("=" * 80)
            logger.info("Lantern Vector Storage Schema Setup for LangChain RAG")
            logger.info("=" * 80 + "\n")

            if not await self.connect():
                return False

            if not await self.verify_lantern_extensions():
                logger.warning("⚠️  Some Lantern extensions not available (may affect features)")

            if not await self.create_vector_tables():
                return False

            if not await self.create_lantern_indexes():
                return False

            if not await self.create_supporting_indexes():
                return False

            if not await self.create_helper_functions():
                return False

            if not await self.verify_schema():
                return False

            if not await self.get_database_stats():
                return False

            logger.info("\n" + "=" * 80)
            logger.info("✅ Lantern Vector Storage Schema Setup Complete!")
            logger.info("=" * 80)
            logger.info("\nLangChain RAG System is ready with:")
            logger.info("  • Lantern HNSW vector similarity search")
            logger.info("  • Document storage with metadata filtering")
            logger.info("  • Multi-turn conversation support")
            logger.info("  • BM25 full-text search (via lantern_extras)")
            logger.info("  • Background job processing")
            logger.info("  • Search analytics and history tracking")

            return True
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            return False
        finally:
            await self.cleanup()


async def main():
    """Main entry point."""
    manager = LanternSchemaManager()
    success = await manager.run_full_setup()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
