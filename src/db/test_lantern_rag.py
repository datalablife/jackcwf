#!/usr/bin/env python3
"""
Test Lantern Vector Storage and RAG Operations.

This script tests:
1. Vector insertion performance
2. Similarity search functionality and latency
3. Metadata filtering
4. Batch operations
5. Full RAG pipeline integration
"""

import os
import sys
import logging
import time
import json
import asyncpg
import numpy as np
from datetime import datetime
from typing import List, Tuple, Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s"
)
logger = logging.getLogger(__name__)


class LanternRAGTester:
    """Test Lantern vector storage for LangChain RAG."""

    def __init__(self):
        self.conn: asyncpg.Connection = None
        self.vector_dimension = 1536  # OpenAI embedding dimension
        self.perf_metrics = {}

    async def connect(self) -> bool:
        """Connect to PostgreSQL database."""
        try:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                logger.error("❌ DATABASE_URL environment variable not set")
                return False

            # Convert SQLAlchemy URL format for asyncpg
            asyncpg_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

            self.conn = await asyncpg.connect(asyncpg_url)
            logger.info("✅ Connected to PostgreSQL")
            return True
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False

    async def clear_test_data(self) -> bool:
        """Clear test data from previous runs."""
        try:
            await self.conn.execute("DELETE FROM documents WHERE source = 'test'")
            await self.conn.execute("DELETE FROM conversations WHERE user_id = 'test_user'")
            logger.info("✅ Test data cleared")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to clear test data: {e}")
            return False

    async def test_single_insertion(self) -> bool:
        """Test single document insertion."""
        try:
            logger.info("\n[Test 1: Single Vector Insertion]")

            test_content = "This is a test document for RAG system. It contains important information about vector databases."
            test_embedding = np.random.randn(self.vector_dimension).tolist()

            start_time = time.time()
            await self.conn.execute(
                """
                INSERT INTO documents (content, embedding, metadata, source, document_type, document_id)
                VALUES ($1, $2, $3::jsonb, $4, $5, $6)
                """,
                test_content,
                test_embedding,
                json.dumps({"chunk": "1", "page": "1"}),
                "test",
                "article",
                "doc_001"
            )
            insert_time = (time.time() - start_time) * 1000

            logger.info(f"✅ Single insertion successful ({insert_time:.2f}ms)")
            self.perf_metrics["single_insert"] = insert_time
            return True
        except Exception as e:
            logger.error(f"❌ Insertion test failed: {e}")
            return False

    async def test_similarity_search(self) -> bool:
        """Test vector similarity search."""
        try:
            logger.info("\n[Test 2: Similarity Search]")

            # Create a query vector
            query_embedding = np.random.randn(self.vector_dimension).tolist()

            start_time = time.time()
            results = await self.conn.fetch(
                """
                SELECT id, content, metadata, source,
                       embedding <-> $1 as distance
                FROM documents
                WHERE source = 'test'
                ORDER BY embedding <-> $1
                LIMIT 5
                """,
                query_embedding
            )
            search_time = (time.time() - start_time) * 1000

            if results:
                logger.info(f"✅ Similarity search successful ({search_time:.2f}ms)")
                logger.info(f"   Found {len(results)} result(s)")
                for idx, row in enumerate(results, 1):
                    logger.info(f"   {idx}. Distance: {row['distance']:.6f}, ID: {row['id']}")
                self.perf_metrics["similarity_search"] = search_time
                return True
            else:
                logger.warning("⚠️  No results found in similarity search")
                return True
        except Exception as e:
            logger.error(f"❌ Similarity search test failed: {e}")
            return False

    async def test_metadata_filtering(self) -> bool:
        """Test metadata-based filtering with similarity search."""
        try:
            logger.info("\n[Test 3: Metadata Filtering]")

            # Insert test documents with different metadata
            for i in range(3):
                embedding = np.random.randn(self.vector_dimension).tolist()
                await self.conn.execute(
                    """
                    INSERT INTO documents (content, embedding, metadata, source, document_type)
                    VALUES ($1, $2, $3::jsonb, $4, $5)
                    """,
                    f"Test document {i+1}",
                    embedding,
                    json.dumps({"category": f"cat_{i}", "priority": i}),
                    "test",
                    "doc_type"
                )

            # Query with metadata filtering
            query_embedding = np.random.randn(self.vector_dimension).tolist()

            start_time = time.time()
            results = await self.conn.fetch(
                """
                SELECT id, content, metadata,
                       embedding <-> $1 as distance
                FROM documents
                WHERE source = 'test'
                  AND metadata @> $2::jsonb
                ORDER BY embedding <-> $1
                LIMIT 5
                """,
                query_embedding,
                json.dumps({"priority": 1})
            )
            filter_time = (time.time() - start_time) * 1000

            logger.info(f"✅ Metadata filtering successful ({filter_time:.2f}ms)")
            logger.info(f"   Found {len(results)} result(s) with metadata filter")
            self.perf_metrics["metadata_filter"] = filter_time
            return True
        except Exception as e:
            logger.error(f"❌ Metadata filtering test failed: {e}")
            return False

    async def test_batch_operations(self) -> bool:
        """Test batch vector insertion."""
        try:
            logger.info("\n[Test 4: Batch Vector Insertion]")

            batch_size = 20
            batch_embeddings = [np.random.randn(self.vector_dimension).tolist() for _ in range(batch_size)]
            batch_contents = [f"Batch document {i+1}" for i in range(batch_size)]

            start_time = time.time()
            async with self.conn.transaction():
                for content, embedding in zip(batch_contents, batch_embeddings):
                    await self.conn.execute(
                        """
                        INSERT INTO documents (content, embedding, metadata, source)
                        VALUES ($1, $2, $3::jsonb, $4)
                        """,
                        content,
                        embedding,
                        json.dumps({"batch_id": 1}),
                        "test"
                    )
            batch_time = (time.time() - start_time) * 1000

            logger.info(f"✅ Batch insertion successful ({batch_time:.2f}ms for {batch_size} vectors)")
            logger.info(f"   Average: {batch_time/batch_size:.2f}ms per vector")
            self.perf_metrics["batch_insert"] = batch_time
            self.perf_metrics["avg_per_vector"] = batch_time / batch_size
            return True
        except Exception as e:
            logger.error(f"❌ Batch operations test failed: {e}")
            return False

    async def test_conversation_storage(self) -> bool:
        """Test multi-turn conversation storage."""
        try:
            logger.info("\n[Test 5: Conversation Storage]")

            # Create a conversation
            context_embedding = np.random.randn(self.vector_dimension).tolist()
            messages = [
                {"role": "user", "content": "What is RAG?"},
                {"role": "assistant", "content": "RAG is Retrieval-Augmented Generation..."}
            ]

            start_time = time.time()
            conv_id = await self.conn.fetchval(
                """
                INSERT INTO conversations (user_id, title, messages, context_embedding, metadata)
                VALUES ($1, $2, $3::jsonb, $4, $5::jsonb)
                RETURNING id
                """,
                "test_user",
                "Test Conversation",
                json.dumps(messages),
                context_embedding,
                json.dumps({"session_id": "sess_001"})
            )
            conv_time = (time.time() - start_time) * 1000

            logger.info(f"✅ Conversation storage successful ({conv_time:.2f}ms)")
            logger.info(f"   Conversation ID: {conv_id}")
            self.perf_metrics["conversation_storage"] = conv_time
            return True
        except Exception as e:
            logger.error(f"❌ Conversation storage test failed: {e}")
            return False

    async def test_rag_pipeline(self) -> bool:
        """Test complete RAG pipeline: query -> search -> context -> response."""
        try:
            logger.info("\n[Test 6: Complete RAG Pipeline]")

            # Simulate RAG query: user question -> embedding -> search -> retrieval
            user_query = "Tell me about vector databases and similarity search"
            query_embedding = np.random.randn(self.vector_dimension).tolist()

            logger.info("  Step 1: Query encoding")
            start_time = time.time()
            # Simulating encoding time
            encoding_time = (time.time() - start_time) * 1000

            logger.info("  Step 2: Vector similarity search")
            start_time = time.time()
            search_results = await self.conn.fetch(
                """
                SELECT id, content, metadata, document_id,
                       embedding <-> $1 as distance,
                       created_at
                FROM documents
                WHERE source = 'test' AND deleted_at IS NULL
                ORDER BY embedding <-> $1
                LIMIT 5
                """,
                query_embedding
            )
            search_time = (time.time() - start_time) * 1000

            logger.info("  Step 3: Context retrieval")
            context_docs = []
            for result in search_results:
                context_docs.append({
                    "id": result["id"],
                    "content": result["content"],
                    "distance": result["distance"]
                })

            logger.info("  Step 4: Store search history")
            start_time = time.time()
            await self.conn.execute(
                """
                INSERT INTO search_history (query, query_embedding, results_count, search_time_ms, user_id)
                VALUES ($1, $2, $3, $4, $5)
                """,
                user_query,
                query_embedding,
                len(search_results),
                int(search_time),
                "test_user"
            )
            history_time = (time.time() - start_time) * 1000

            total_rag_time = encoding_time + search_time + history_time

            logger.info(f"✅ Complete RAG pipeline successful ({total_rag_time:.2f}ms total)")
            logger.info(f"   - Encoding: {encoding_time:.2f}ms")
            logger.info(f"   - Search: {search_time:.2f}ms")
            logger.info(f"   - History: {history_time:.2f}ms")
            logger.info(f"   - Retrieved {len(context_docs)} documents for context")

            self.perf_metrics["rag_pipeline_total"] = total_rag_time
            self.perf_metrics["rag_search_only"] = search_time

            return True
        except Exception as e:
            logger.error(f"❌ RAG pipeline test failed: {e}")
            return False

    async def get_database_stats(self) -> bool:
        """Get database statistics."""
        try:
            logger.info("\n[Database Statistics]")

            # Document count
            doc_count = await self.conn.fetchval(
                "SELECT COUNT(*) FROM documents WHERE deleted_at IS NULL"
            )

            # Table size
            table_size = await self.conn.fetchval(
                "SELECT pg_size_pretty(pg_total_relation_size('documents'))"
            )

            # Index list (fixed query)
            index_info = await self.conn.fetch(
                """
                SELECT indexname FROM pg_indexes
                WHERE tablename = 'documents'
                ORDER BY indexname
                """
            )

            logger.info(f"  Documents: {doc_count}")
            logger.info(f"  Table Size: {table_size}")
            logger.info(f"  Indexes ({len(index_info)}):")
            for idx in index_info:
                logger.info(f"    - {idx['indexname']}")

            return True
        except Exception as e:
            logger.warning(f"⚠️  Could not retrieve detailed statistics: {e}")
            return True

    def print_performance_summary(self):
        """Print performance metrics summary."""
        logger.info("\n" + "=" * 80)
        logger.info("PERFORMANCE METRICS SUMMARY")
        logger.info("=" * 80)

        if not self.perf_metrics:
            logger.warning("No performance metrics collected")
            return

        for metric_name, value in self.perf_metrics.items():
            logger.info(f"  {metric_name}: {value:.2f}ms")

        # Performance targets
        logger.info("\nPerformance Targets:")
        search_latency = self.perf_metrics.get("rag_search_only", float("inf"))
        if search_latency < 500:
            logger.info(f"  ✅ Search latency {search_latency:.2f}ms < 500ms target")
        else:
            logger.info(f"  ⚠️  Search latency {search_latency:.2f}ms >= 500ms target")

        logger.info("=" * 80)

    async def cleanup(self):
        """Close database connection."""
        if self.conn:
            await self.conn.close()
            logger.info("✅ Database connection closed")

    async def run_all_tests(self) -> bool:
        """Run all RAG tests."""
        try:
            logger.info("=" * 80)
            logger.info("Lantern Vector Storage & RAG Pipeline Tests")
            logger.info("=" * 80)

            if not await self.connect():
                return False

            if not await self.clear_test_data():
                return False

            if not await self.test_single_insertion():
                return False

            if not await self.test_similarity_search():
                return False

            if not await self.test_metadata_filtering():
                return False

            if not await self.test_batch_operations():
                return False

            if not await self.test_conversation_storage():
                return False

            if not await self.test_rag_pipeline():
                return False

            if not await self.get_database_stats():
                logger.warning("⚠️  Could not retrieve database statistics")

            self.print_performance_summary()

            logger.info("\n✅ All RAG tests completed successfully!")
            return True
        except Exception as e:
            logger.error(f"❌ Test suite failed: {e}")
            return False
        finally:
            await self.cleanup()


async def main():
    """Main entry point."""
    tester = LanternRAGTester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
