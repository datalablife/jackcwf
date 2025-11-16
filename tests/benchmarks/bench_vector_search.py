"""Performance benchmarks for vector search operations."""

import asyncio
import time
import logging
from typing import List
from uuid import uuid4
import numpy as np

from sqlalchemy.ext.asyncio import AsyncSession
from src.db.config import engine, get_async_session
from src.models import DocumentORM, EmbeddingORM
from src.repositories.embedding import EmbeddingRepository

logger = logging.getLogger(__name__)


async def benchmark_vector_search(num_vectors: int = 1000) -> dict:
    """
    Benchmark vector search performance.

    Target: Vector search should complete in ≤200ms P99

    Args:
        num_vectors: Number of vectors to insert for testing

    Returns:
        Benchmark results dict
    """
    async for session in get_async_session():
        try:
            # Setup: Create a test document
            doc = DocumentORM(
                user_id="test_user",
                filename="bench_test.txt",
                file_type="txt",
                content="Test document for benchmarking",
                total_chunks=num_vectors,
            )
            session.add(doc)
            await session.flush()

            # Create embeddings
            embeddings = []
            for i in range(num_vectors):
                # Generate random 1536-dimensional vectors
                embedding_vector = np.random.randn(1536).tolist()
                embedding = EmbeddingORM(
                    document_id=doc.id,
                    chunk_text=f"Chunk {i}: Sample text for benchmarking",
                    embedding=embedding_vector,
                    chunk_index=i,
                )
                embeddings.append(embedding)

            # Benchmark: Bulk insert
            repo = EmbeddingRepository(session)
            insert_start = time.time()
            await repo.bulk_create(embeddings)
            insert_time = time.time() - insert_start
            logger.info(f"Inserted {num_vectors} vectors in {insert_time:.2f}s")

            # Benchmark: Search operations
            query_vector = np.random.randn(1536).tolist()
            search_times = []

            for _ in range(10):  # 10 search iterations
                search_start = time.time()
                results = await repo.search_similar(
                    query_embedding=query_vector,
                    user_id="test_user",
                    limit=5,
                    threshold=0.7,
                )
                search_time = (time.time() - search_start) * 1000  # Convert to ms
                search_times.append(search_time)

            # Calculate percentiles
            search_times_sorted = sorted(search_times)
            p50 = search_times_sorted[int(len(search_times_sorted) * 0.5)]
            p95 = search_times_sorted[int(len(search_times_sorted) * 0.95)]
            p99 = search_times_sorted[int(len(search_times_sorted) * 0.99)]

            results_dict = {
                "num_vectors": num_vectors,
                "insert_time_seconds": insert_time,
                "insert_throughput_vectors_per_sec": num_vectors / insert_time,
                "search_p50_ms": p50,
                "search_p95_ms": p95,
                "search_p99_ms": p99,
                "target_p99_ms": 200,
                "passed": p99 <= 200,
            }

            logger.info(f"Vector search benchmark results: {results_dict}")
            return results_dict

        finally:
            # Cleanup
            await session.execute(
                "DELETE FROM embeddings WHERE document_id = %s",
                (doc.id,),
            )
            await session.execute(
                "DELETE FROM documents WHERE id = %s",
                (doc.id,),
            )
            await session.commit()


async def benchmark_bulk_operations() -> dict:
    """
    Benchmark bulk CRUD operations to ensure N+1 fix is working.

    Args:
        None

    Returns:
        Benchmark results dict
    """
    async for session in get_async_session():
        from src.repositories.document import DocumentRepository

        try:
            repo = DocumentRepository(session)

            # Benchmark: Bulk create
            documents = [
                DocumentORM(
                    user_id=f"user_{i % 10}",
                    filename=f"doc_{i}.txt",
                    file_type="txt",
                    content=f"Content of document {i}",
                    total_chunks=i,
                )
                for i in range(100)
            ]

            create_start = time.time()
            created = await repo.bulk_create(documents)
            create_time = time.time() - create_start

            # Benchmark: Bulk delete
            delete_ids = [doc.id for doc in created]
            delete_start = time.time()
            deleted_count = await repo.bulk_delete(delete_ids)
            delete_time = time.time() - delete_start

            results_dict = {
                "bulk_create_100_items_seconds": create_time,
                "bulk_create_throughput_items_per_sec": 100 / create_time,
                "bulk_delete_100_items_seconds": delete_time,
                "bulk_delete_throughput_items_per_sec": 100 / delete_time,
            }

            logger.info(f"Bulk operations benchmark: {results_dict}")
            return results_dict

        finally:
            await session.rollback()


async def verify_indices() -> dict:
    """
    Verify that all required indices exist in the database.

    Returns:
        Index verification results
    """
    async with engine.begin() as conn:
        from sqlalchemy import text

        required_indices = {
            "idx_conversations_user_created": "conversations",
            "idx_conversations_user_active": "conversations",
            "idx_messages_conversation": "messages",
            "idx_messages_conversation_recent": "messages",
            "idx_embeddings_vector_hnsw": "embeddings",
            "idx_embeddings_document": "embeddings",
            "idx_documents_user_created": "documents",
            "idx_documents_user_active": "documents",
        }

        results = {}
        for index_name, table_name in required_indices.items():
            result = await conn.execute(
                text("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_indexes
                        WHERE indexname = :index_name
                    )
                """),
                {"index_name": index_name},
            )
            exists = result.scalar()
            results[index_name] = {
                "table": table_name,
                "exists": exists,
            }
            if not exists:
                logger.warning(f"Index {index_name} missing on table {table_name}")

        all_exist = all(r["exists"] for r in results.values())
        results["all_indices_exist"] = all_exist

        logger.info(f"Index verification: {results}")
        return results


async def main():
    """Run all benchmarks."""
    logger.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("LangChain Backend Performance Benchmarks")
    print("=" * 60)

    # Verify indices
    print("\n1. Verifying database indices...")
    index_results = await verify_indices()
    print(f"All indices present: {index_results['all_indices_exist']}")

    # Benchmark bulk operations
    print("\n2. Benchmarking bulk CRUD operations...")
    bulk_results = await benchmark_bulk_operations()
    for key, value in bulk_results.items():
        print(f"   {key}: {value:.4f}")

    # Benchmark vector search
    print("\n3. Benchmarking vector search (1000 vectors)...")
    vector_results = await benchmark_vector_search(1000)
    print(f"   Vector search P99: {vector_results['search_p99_ms']:.2f}ms")
    print(f"   Target: {vector_results['target_p99_ms']}ms")
    print(f"   Passed: {vector_results['passed']}")

    print("\n" + "=" * 60)
    print("Benchmarks completed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
