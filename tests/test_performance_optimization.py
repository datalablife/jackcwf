#!/usr/bin/env python3
"""
Performance Testing Suite for Redis Cache and Database Optimizations.

This module provides comprehensive performance tests to measure:
- Cache hit/miss latency
- Database query performance
- N+1 query detection
- Overall API response times

Run with:
    pytest tests/test_performance_optimization.py -v
"""

import pytest
import asyncio
import time
from typing import List
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload

from src.models import ConversationORM, MessageORM, DocumentORM
from src.infrastructure.redis_cache import RedisCache
from src.infrastructure.query_optimization import (
    get_conversations_with_messages_optimized,
    get_conversations_paginated,
    bulk_insert_messages,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
async def redis_cache():
    """Create Redis cache instance for testing."""
    cache = RedisCache(
        host="localhost",
        port=6379,
        db=15,  # Use separate DB for tests
    )
    await cache.initialize()
    yield cache
    await cache.flush_db()  # Clean up
    await cache.close()


@pytest.fixture
async def db_session():
    """Create test database session."""
    # Use test database
    from src.db.config import get_async_session

    async for session in get_async_session():
        yield session


# ============================================================================
# Redis Cache Performance Tests
# ============================================================================

class TestRedisCachePerformance:
    """Test Redis cache performance characteristics."""

    @pytest.mark.asyncio
    async def test_cache_write_latency(self, redis_cache: RedisCache):
        """Test cache write latency (should be <5ms)."""
        test_data = {
            "id": str(uuid4()),
            "title": "Test Conversation",
            "user_id": "test_user",
            "messages": [{"role": "user", "content": "Hello"}] * 10
        }

        latencies = []
        for _ in range(100):
            start = time.time()
            await redis_cache.set_conversation(test_data["id"], test_data)
            latency_ms = (time.time() - start) * 1000
            latencies.append(latency_ms)

        avg_latency = sum(latencies) / len(latencies)
        p95_latency = sorted(latencies)[94]  # 95th percentile

        print(f"\nCache WRITE Performance:")
        print(f"  Average: {avg_latency:.2f}ms")
        print(f"  P95: {p95_latency:.2f}ms")
        print(f"  Min: {min(latencies):.2f}ms")
        print(f"  Max: {max(latencies):.2f}ms")

        # Assert performance targets
        assert avg_latency < 5, f"Average latency {avg_latency}ms exceeds 5ms target"
        assert p95_latency < 10, f"P95 latency {p95_latency}ms exceeds 10ms target"

    @pytest.mark.asyncio
    async def test_cache_read_latency(self, redis_cache: RedisCache):
        """Test cache read latency (should be <5ms)."""
        test_id = str(uuid4())
        test_data = {
            "id": test_id,
            "title": "Test Conversation",
            "user_id": "test_user",
        }

        # Write data first
        await redis_cache.set_conversation(test_id, test_data)

        # Measure read latency
        latencies = []
        for _ in range(100):
            start = time.time()
            result = await redis_cache.get_conversation(test_id)
            latency_ms = (time.time() - start) * 1000
            latencies.append(latency_ms)

        avg_latency = sum(latencies) / len(latencies)
        p95_latency = sorted(latencies)[94]

        print(f"\nCache READ Performance:")
        print(f"  Average: {avg_latency:.2f}ms")
        print(f"  P95: {p95_latency:.2f}ms")
        print(f"  Min: {min(latencies):.2f}ms")
        print(f"  Max: {max(latencies):.2f}ms")

        # Assert performance targets
        assert avg_latency < 5, f"Average latency {avg_latency}ms exceeds 5ms target"
        assert p95_latency < 10, f"P95 latency {p95_latency}ms exceeds 10ms target"

    @pytest.mark.asyncio
    async def test_cache_hit_rate(self, redis_cache: RedisCache):
        """Test cache hit rate with realistic access patterns."""
        # Create 100 conversations
        conv_ids = [str(uuid4()) for _ in range(100)]
        for conv_id in conv_ids:
            await redis_cache.set_conversation(
                conv_id,
                {"id": conv_id, "title": f"Conv {conv_id}"},
                ttl=60
            )

        # Simulate realistic access pattern (Zipf distribution)
        # 20% of conversations get 80% of traffic
        import random
        hot_ids = conv_ids[:20]  # Hot data
        cold_ids = conv_ids[20:]  # Cold data

        hits = 0
        misses = 0
        total_requests = 1000

        for _ in range(total_requests):
            # 80% chance to access hot data
            if random.random() < 0.8:
                conv_id = random.choice(hot_ids)
            else:
                conv_id = random.choice(cold_ids)

            result = await redis_cache.get_conversation(conv_id)
            if result:
                hits += 1
            else:
                misses += 1

        hit_rate = hits / total_requests

        print(f"\nCache Hit Rate Analysis:")
        print(f"  Hits: {hits}")
        print(f"  Misses: {misses}")
        print(f"  Hit Rate: {hit_rate:.1%}")

        # We expect >90% hit rate with this access pattern
        assert hit_rate > 0.9, f"Hit rate {hit_rate:.1%} below 90% target"

    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(self, redis_cache: RedisCache):
        """Test cache TTL expiration behavior."""
        test_id = str(uuid4())
        test_data = {"id": test_id, "title": "Test"}

        # Set with short TTL
        await redis_cache.set_conversation(test_id, test_data, ttl=2)

        # Should exist immediately
        result = await redis_cache.get_conversation(test_id)
        assert result is not None, "Data should exist immediately after caching"

        # Should exist after 1 second
        await asyncio.sleep(1)
        result = await redis_cache.get_conversation(test_id)
        assert result is not None, "Data should exist after 1 second"

        # Should be expired after 3 seconds
        await asyncio.sleep(2)
        result = await redis_cache.get_conversation(test_id)
        assert result is None, "Data should be expired after 3 seconds"

        print("\nCache TTL Expiration: PASS")


# ============================================================================
# Database Query Performance Tests
# ============================================================================

class TestDatabaseQueryPerformance:
    """Test database query optimizations."""

    @pytest.mark.asyncio
    async def test_n_plus_1_prevention(self, db_session: AsyncSession):
        """Verify N+1 queries are eliminated."""
        # This test requires actual data in the database
        # Skip if no data exists
        result = await db_session.execute(
            select(ConversationORM).limit(1)
        )
        if not result.scalars().first():
            pytest.skip("No test data available")

        # Measure queries with eager loading
        from sqlalchemy import event
        from sqlalchemy.engine import Engine

        query_count = 0

        @event.listens_for(Engine, "before_cursor_execute", named=True)
        def receive_before_cursor_execute(**kw):
            nonlocal query_count
            query_count += 1

        # Execute optimized query
        query_count = 0
        result = await db_session.execute(
            select(ConversationORM)
            .options(selectinload(ConversationORM.messages))
            .limit(10)
        )
        conversations = result.scalars().all()

        # Access messages (should not trigger additional queries)
        for conv in conversations:
            _ = conv.messages

        print(f"\nN+1 Query Test:")
        print(f"  Conversations loaded: {len(conversations)}")
        print(f"  Total queries: {query_count}")

        # Should be 2 queries max: 1 for conversations + 1 for all messages
        assert query_count <= 2, f"Expected <=2 queries, got {query_count} (N+1 detected!)"

    @pytest.mark.asyncio
    async def test_bulk_insert_performance(self, db_session: AsyncSession):
        """Test bulk insert performance vs individual inserts."""
        conv_id = uuid4()

        # Create test conversation
        conv = ConversationORM(
            id=conv_id,
            user_id="test_user",
            title="Test",
            system_prompt="You are helpful",
        )
        db_session.add(conv)
        await db_session.commit()

        # Test individual inserts (SLOW)
        messages_individual = [
            {
                "conversation_id": conv_id,
                "role": "user",
                "content": f"Message {i}",
            }
            for i in range(100)
        ]

        start = time.time()
        for msg in messages_individual[:10]:  # Only 10 for time constraint
            message = MessageORM(**msg)
            db_session.add(message)
            await db_session.commit()
        individual_time = time.time() - start

        # Test bulk insert (FAST)
        messages_bulk = [
            {
                "conversation_id": conv_id,
                "role": "user",
                "content": f"Bulk Message {i}",
            }
            for i in range(100)
        ]

        start = time.time()
        await bulk_insert_messages(db_session, messages_bulk)
        bulk_time = time.time() - start

        speedup = individual_time / bulk_time

        print(f"\nBulk Insert Performance:")
        print(f"  Individual (10 msgs): {individual_time*1000:.2f}ms")
        print(f"  Bulk (100 msgs): {bulk_time*1000:.2f}ms")
        print(f"  Speedup: {speedup:.1f}x")

        # Bulk should be significantly faster
        assert speedup > 5, f"Bulk insert should be >5x faster, got {speedup:.1f}x"

        # Cleanup
        await db_session.rollback()

    @pytest.mark.asyncio
    async def test_pagination_performance(self, db_session: AsyncSession):
        """Test cursor-based pagination performance."""
        # This test requires actual data
        result = await db_session.execute(
            select(ConversationORM).limit(1)
        )
        if not result.scalars().first():
            pytest.skip("No test data available")

        # Test first page
        start = time.time()
        page1 = await get_conversations_paginated(
            db_session,
            user_id="test_user",
            cursor=None,
            limit=20
        )
        first_page_time = (time.time() - start) * 1000

        # Test deep page (if available)
        cursor = page1.get("next_cursor")
        if cursor:
            start = time.time()
            page2 = await get_conversations_paginated(
                db_session,
                user_id="test_user",
                cursor=cursor,
                limit=20
            )
            second_page_time = (time.time() - start) * 1000

            print(f"\nPagination Performance:")
            print(f"  Page 1: {first_page_time:.2f}ms")
            print(f"  Page 2: {second_page_time:.2f}ms")
            print(f"  Difference: {abs(second_page_time - first_page_time):.2f}ms")

            # Cursor pagination should have consistent performance
            assert abs(second_page_time - first_page_time) < 50, \
                "Pagination performance should be consistent"


# ============================================================================
# Integration Performance Tests
# ============================================================================

class TestIntegrationPerformance:
    """Test end-to-end performance with cache + DB."""

    @pytest.mark.asyncio
    async def test_cache_vs_db_latency(
        self,
        redis_cache: RedisCache,
        db_session: AsyncSession
    ):
        """Compare cache hit vs DB query latency."""
        # Skip if no data
        result = await db_session.execute(
            select(ConversationORM).limit(1)
        )
        conv = result.scalars().first()
        if not conv:
            pytest.skip("No test data available")

        conv_id = str(conv.id)

        # Measure DB query latency (cold)
        start = time.time()
        db_result = await db_session.execute(
            select(ConversationORM).where(ConversationORM.id == conv.id)
        )
        _ = db_result.scalars().first()
        db_latency = (time.time() - start) * 1000

        # Cache the conversation
        await redis_cache.set_conversation(conv_id, conv.to_dict())

        # Measure cache latency (hot)
        start = time.time()
        _ = await redis_cache.get_conversation(conv_id)
        cache_latency = (time.time() - start) * 1000

        speedup = db_latency / cache_latency

        print(f"\nCache vs DB Latency:")
        print(f"  DB Query: {db_latency:.2f}ms")
        print(f"  Cache Hit: {cache_latency:.2f}ms")
        print(f"  Speedup: {speedup:.1f}x")

        # Cache should be at least 5x faster
        assert speedup > 5, f"Cache should be >5x faster than DB, got {speedup:.1f}x"


# ============================================================================
# Benchmark Summary
# ============================================================================

@pytest.mark.asyncio
async def test_performance_summary(redis_cache: RedisCache):
    """Generate performance benchmark summary."""
    print("\n" + "="*80)
    print("PERFORMANCE OPTIMIZATION SUMMARY")
    print("="*80)

    # Redis health check
    health = await redis_cache.health_check()
    print(f"\nRedis Status: {health['status']}")
    print(f"  Latency: {health.get('latency_ms', 'N/A')}ms")
    print(f"  Memory: {health.get('used_memory', 'N/A')}")

    print("\nExpected Performance Improvements:")
    print("  Cache Hit Latency: 5ms (vs 50-200ms DB query)")
    print("  Cache Hit Rate: 60-80% for hot data")
    print("  N+1 Query Elimination: 50-100x faster")
    print("  Bulk Operations: 100x faster")
    print("  API Response (cached): 70% latency reduction")

    print("\nRecommendations:")
    print("  1. Enable Redis caching in production")
    print("  2. Apply database index migration")
    print("  3. Use eager loading for related data")
    print("  4. Implement cache warmup on startup")
    print("  5. Monitor cache hit rates with Prometheus")

    print("\n" + "="*80)
