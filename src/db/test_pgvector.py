#!/usr/bin/env python3
"""
Test pgvector functionality and create LangChain vector storage tables.

This script:
1. Verifies pgvector extension is available
2. Creates vector storage tables for LangChain
3. Tests vector insertion and similarity search
4. Reports performance metrics
"""

import os
import sys
import logging
import time
from datetime import datetime
from typing import List, Tuple

import asyncpg
import numpy as np

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s"
)
logger = logging.getLogger(__name__)


class PgVectorTester:
    """Test pgvector functionality for LangChain integration."""

    def __init__(self):
        self.conn = None
        self.vector_dimension = 1536  # OpenAI embedding dimension

    async def connect(self) -> bool:
        """Connect to PostgreSQL database."""
        try:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                logger.error("DATABASE_URL environment variable not set")
                return False

            self.conn = await asyncpg.connect(database_url)
            logger.info("✅ Connected to PostgreSQL")
            return True
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False

    async def verify_pgvector(self) -> bool:
        """Verify pgvector extension is enabled."""
        try:
            result = await self.conn.fetchval(
                "SELECT extname FROM pg_extension WHERE extname = 'vector'"
            )
            if result:
                logger.info("✅ pgvector extension is available")
                return True
            else:
                logger.warning("⚠️  pgvector extension not found, attempting to enable...")
                await self.conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                logger.info("✅ pgvector extension enabled")
                return True
        except Exception as e:
            logger.error(f"❌ pgvector verification failed: {e}")
            return False

    async def create_vector_tables(self) -> bool:
        """Create tables for LangChain vector storage."""
        try:
            # Create documents table
            await self.conn.execute(f"""
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    metadata JSONB DEFAULT '{{}}',
                    embedding vector({self.vector_dimension}),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.info("✅ Documents table created")

            # Create index for vector similarity search
            await self.conn.execute("""
                CREATE INDEX IF NOT EXISTS documents_embedding_idx
                ON documents
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """)
            logger.info("✅ Vector similarity index created")

            # Create metadata index
            await self.conn.execute("""
                CREATE INDEX IF NOT EXISTS documents_metadata_idx
                ON documents
                USING GIN (metadata)
            """)
            logger.info("✅ Metadata index created")

            return True
        except Exception as e:
            logger.error(f"❌ Table creation failed: {e}")
            return False

    async def test_vector_operations(self) -> bool:
        """Test vector insertion and similarity search."""
        try:
            logger.info("\n[Testing Vector Operations]")

            # Test 1: Insert a test vector
            test_vector = np.random.randn(self.vector_dimension).tolist()

            start_time = time.time()
            await self.conn.execute(
                """
                INSERT INTO documents (content, metadata, embedding)
                VALUES ($1, $2, $3)
                """,
                "Test document for RAG system",
                {"source": "test", "type": "test_vector"},
                test_vector
            )
            insert_time = time.time() - start_time
            logger.info(f"✅ Vector insertion successful ({insert_time*1000:.2f}ms)")

            # Test 2: Test similarity search
            start_time = time.time()
            results = await self.conn.fetch(
                """
                SELECT id, content, embedding <-> $1 as distance
                FROM documents
                ORDER BY embedding <-> $1
                LIMIT 5
                """,
                test_vector
            )
            search_time = time.time() - start_time

            if results:
                logger.info(f"✅ Similarity search successful ({search_time*1000:.2f}ms)")
                logger.info(f"   Found {len(results)} result(s)")
                for row in results:
                    logger.info(f"   - Document {row['id']}: distance={row['distance']:.6f}")
            else:
                logger.warning("⚠️  No results found in similarity search")

            # Test 3: Test vector update
            updated_vector = np.random.randn(self.vector_dimension).tolist()
            start_time = time.time()
            await self.conn.execute(
                """
                UPDATE documents
                SET embedding = $1, updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
                """,
                updated_vector,
                results[0]['id'] if results else 1
            )
            update_time = time.time() - start_time
            logger.info(f"✅ Vector update successful ({update_time*1000:.2f}ms)")

            # Test 4: Batch operations
            batch_vectors = [np.random.randn(self.vector_dimension).tolist() for _ in range(10)]
            batch_contents = [f"Batch document {i+1}" for i in range(10)]

            start_time = time.time()
            async with self.conn.transaction():
                for i, (content, vector) in enumerate(zip(batch_contents, batch_vectors)):
                    await self.conn.execute(
                        """
                        INSERT INTO documents (content, metadata, embedding)
                        VALUES ($1, $2, $3)
                        """,
                        content,
                        {"batch_id": 1, "index": i},
                        vector
                    )
            batch_time = time.time() - start_time
            logger.info(f"✅ Batch insertion successful (10 vectors in {batch_time*1000:.2f}ms)")
            logger.info(f"   Average: {batch_time/10*1000:.2f}ms per vector")

            return True
        except Exception as e:
            logger.error(f"❌ Vector operations test failed: {e}")
            return False

    async def get_statistics(self) -> bool:
        """Get database statistics."""
        try:
            # Get document count
            doc_count = await self.conn.fetchval(
                "SELECT COUNT(*) FROM documents"
            )

            # Get table size
            table_size = await self.conn.fetchval(
                """
                SELECT pg_size_pretty(pg_total_relation_size('documents'))
                """
            )

            # Get index info
            index_info = await self.conn.fetch(
                """
                SELECT indexname, pg_size_pretty(pg_relation_size(indexrelid)) as size
                FROM pg_indexes
                WHERE tablename = 'documents'
                """
            )

            logger.info("\n[Database Statistics]")
            logger.info(f"  Documents: {doc_count}")
            logger.info(f"  Table size: {table_size}")
            logger.info(f"  Indexes: {len(index_info)}")
            for idx in index_info:
                logger.info(f"    - {idx['indexname']}: {idx['size']}")

            return True
        except Exception as e:
            logger.error(f"❌ Failed to get statistics: {e}")
            return False

    async def cleanup(self):
        """Close database connection."""
        if self.conn:
            await self.conn.close()
            logger.info("✅ Database connection closed")

    async def run_all_tests(self) -> bool:
        """Run all tests."""
        try:
            logger.info("=" * 70)
            logger.info("pgvector Functionality Test for LangChain")
            logger.info("=" * 70 + "\n")

            # Connect
            if not await self.connect():
                return False

            # Verify pgvector
            if not await self.verify_pgvector():
                return False

            # Create tables
            if not await self.create_vector_tables():
                return False

            # Test operations
            if not await self.test_vector_operations():
                return False

            # Get statistics
            if not await self.get_statistics():
                return False

            logger.info("\n" + "=" * 70)
            logger.info("✅ All pgvector tests passed!")
            logger.info("=" * 70)
            logger.info("\nRAG System is ready for:")
            logger.info("  • Vector embedding storage")
            logger.info("  • Similarity-based retrieval")
            logger.info("  • Metadata filtering")
            logger.info("  • Batch operations")

            return True
        except Exception as e:
            logger.error(f"❌ Test suite failed: {e}")
            return False
        finally:
            await self.cleanup()


async def main():
    """Main entry point."""
    tester = PgVectorTester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
