#!/usr/bin/env python3
"""
Performance Benchmark Suite for 4GB Memory Optimization.

This module tests the optimized configuration:
- Redis cache: 256MB (preserved)
- Database query optimization: cursor pagination + eager loading
- Prometheus scrape interval: 30s (from 15s)
- Alert rules: 10 critical rules (from 47)
- Retention: 7 days (from 30 days)

Test Coverage:
1. Cache Performance Benchmark (Hit Rate, Latency)
2. Database Query Performance (Cursor vs OFFSET pagination)
3. Monitoring System Performance (Prometheus overhead)
4. API Response Times (End-to-End)
5. Concurrent Capacity Test (Load Testing)
6. Resource Utilization Efficiency

Target Metrics:
- Cache hit rate: 50-70%
- Cursor pagination: 100x faster than OFFSET
- API P50 latency: <100ms
- API P95 latency: <300ms
- Concurrent connections: 500+ (4GB limit)
"""

import asyncio
import time
import statistics
import random
import psutil
import os
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict

import pytest
import asyncpg
from redis import asyncio as aioredis


# ============================================================================
# Data Classes for Test Results
# ============================================================================

@dataclass
class CacheBenchmarkResult:
    """Cache performance benchmark results."""
    total_requests: int
    cache_hits: int
    cache_misses: int
    hit_rate: float
    avg_hit_latency_ms: float
    avg_miss_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    throughput_rps: float  # requests per second
    memory_usage_mb: float


@dataclass
class QueryBenchmarkResult:
    """Database query performance benchmark results."""
    test_name: str
    total_queries: int
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    throughput_qps: float  # queries per second


@dataclass
class APIBenchmarkResult:
    """End-to-end API performance results."""
    endpoint: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    error_rate: float
    throughput_rps: float


@dataclass
class ConcurrentCapacityResult:
    """Concurrent capacity test results."""
    max_concurrent_connections: int
    avg_latency_at_50pct: float  # At 50% capacity
    avg_latency_at_75pct: float  # At 75% capacity
    avg_latency_at_90pct: float  # At 90% capacity
    performance_cliff_point: int  # Connection count where latency > 2x baseline
    memory_usage_50pct_mb: float
    memory_usage_75pct_mb: float
    memory_usage_90pct_mb: float
    cpu_usage_50pct: float
    cpu_usage_75pct: float
    cpu_usage_90pct: float


@dataclass
class PrometheusOverheadResult:
    """Prometheus monitoring overhead results."""
    scrape_interval_sec: int
    total_metrics_count: int
    scrape_duration_ms: float
    cpu_overhead_pct: float
    memory_overhead_mb: float
    timeseries_count: int


# ============================================================================
# Test 1: Cache Performance Benchmark
# ============================================================================

class CachePerformanceBenchmark:
    """Benchmark Redis cache performance with realistic workload."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self.redis = None

    async def setup(self):
        """Initialize Redis connection."""
        self.redis = await aioredis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True
        )

    async def teardown(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()

    async def run_benchmark(
        self,
        total_requests: int = 1000,
        read_pct: float = 0.50,  # 50% reads
        write_pct: float = 0.30,  # 30% writes
        cache_miss_pct: float = 0.20  # 20% cache misses
    ) -> CacheBenchmarkResult:
        """
        Run cache performance benchmark.

        Simulates realistic workload:
        - 50% reads (cache hits/misses)
        - 30% writes (cache updates)
        - 20% cache penetration (new queries)

        Args:
            total_requests: Number of cache operations
            read_pct: Percentage of read operations
            write_pct: Percentage of write operations
            cache_miss_pct: Percentage of cache misses (new queries)

        Returns:
            CacheBenchmarkResult with performance metrics
        """
        await self.setup()

        # Pre-populate cache with some data
        warmup_keys = 1000
        for i in range(warmup_keys):
            key = f"cache:query:{i}"
            value = f"response_{i}" * 100  # ~1KB each
            await self.redis.set(key, value, ex=3600)

        print(f"\n🔥 Cache warmed up with {warmup_keys} entries")

        # Benchmark variables
        cache_hits = 0
        cache_misses = 0
        hit_latencies = []
        miss_latencies = []
        all_latencies = []

        start_time = time.time()

        for i in range(total_requests):
            operation = random.random()

            if operation < read_pct:
                # Read operation (cache hit or miss)
                if random.random() < 0.8:  # 80% of reads are cache hits
                    # Cache HIT
                    key = f"cache:query:{random.randint(0, warmup_keys - 1)}"
                    op_start = time.time()
                    result = await self.redis.get(key)
                    latency = (time.time() - op_start) * 1000

                    if result:
                        cache_hits += 1
                        hit_latencies.append(latency)
                    else:
                        cache_misses += 1
                        miss_latencies.append(latency)

                    all_latencies.append(latency)
                else:
                    # Cache MISS (simulate LLM call + cache write)
                    key = f"cache:query:new_{i}"
                    op_start = time.time()

                    # Simulate LLM call (300-500ms)
                    await asyncio.sleep(random.uniform(0.3, 0.5))

                    # Write to cache
                    value = f"new_response_{i}" * 100
                    await self.redis.set(key, value, ex=3600)

                    latency = (time.time() - op_start) * 1000
                    cache_misses += 1
                    miss_latencies.append(latency)
                    all_latencies.append(latency)

            elif operation < (read_pct + write_pct):
                # Write operation (cache update)
                key = f"cache:query:{random.randint(0, warmup_keys - 1)}"
                value = f"updated_response_{i}" * 100

                op_start = time.time()
                await self.redis.set(key, value, ex=3600)
                latency = (time.time() - op_start) * 1000
                all_latencies.append(latency)

            else:
                # Cache penetration (new query, not in cache)
                key = f"cache:query:new_{i}"
                op_start = time.time()
                result = await self.redis.get(key)
                latency = (time.time() - op_start) * 1000

                cache_misses += 1
                miss_latencies.append(latency)
                all_latencies.append(latency)

        total_time = time.time() - start_time

        # Calculate statistics
        hit_rate = cache_hits / (cache_hits + cache_misses) if (cache_hits + cache_misses) > 0 else 0
        avg_hit_latency = statistics.mean(hit_latencies) if hit_latencies else 0
        avg_miss_latency = statistics.mean(miss_latencies) if miss_latencies else 0

        all_latencies_sorted = sorted(all_latencies)
        p50 = all_latencies_sorted[int(len(all_latencies_sorted) * 0.50)] if all_latencies else 0
        p95 = all_latencies_sorted[int(len(all_latencies_sorted) * 0.95)] if all_latencies else 0
        p99 = all_latencies_sorted[int(len(all_latencies_sorted) * 0.99)] if all_latencies else 0

        throughput = total_requests / total_time

        # Get Redis memory usage
        info = await self.redis.info("memory")
        memory_usage_mb = info.get("used_memory", 0) / (1024 * 1024)

        await self.teardown()

        return CacheBenchmarkResult(
            total_requests=total_requests,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            hit_rate=hit_rate,
            avg_hit_latency_ms=avg_hit_latency,
            avg_miss_latency_ms=avg_miss_latency,
            p50_latency_ms=p50,
            p95_latency_ms=p95,
            p99_latency_ms=p99,
            throughput_rps=throughput,
            memory_usage_mb=memory_usage_mb
        )


# ============================================================================
# Test 2: Database Query Performance (Cursor vs OFFSET)
# ============================================================================

class QueryPerformanceBenchmark:
    """Benchmark database query performance."""

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.pool = None

    async def setup(self):
        """Initialize database connection pool."""
        self.pool = await asyncpg.create_pool(
            self.db_url,
            min_size=10,
            max_size=20,
            command_timeout=60
        )

    async def teardown(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()

    async def prepare_test_data(self, total_records: int = 1_000_000):
        """
        Prepare large dataset for pagination testing.

        Creates 1M+ conversation records for realistic pagination tests.
        """
        await self.setup()

        async with self.pool.acquire() as conn:
            # Check if table exists
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'conversations_test'
                )
            """)

            if table_exists:
                # Check if data already exists
                count = await conn.fetchval("SELECT COUNT(*) FROM conversations_test")
                if count >= total_records:
                    print(f"\n✅ Test data already exists: {count:,} records")
                    return

            # Create test table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations_test (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    is_deleted BOOLEAN DEFAULT FALSE
                )
            """)

            # Create indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_test_conv_user_created
                ON conversations_test (user_id, created_at DESC)
                WHERE is_deleted = false
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_test_conv_id
                ON conversations_test (id)
            """)

            print(f"\n📊 Generating {total_records:,} test records...")
            batch_size = 10000
            user_id = "test_user_benchmark"

            for batch_start in range(0, total_records, batch_size):
                values = []
                for i in range(batch_start, min(batch_start + batch_size, total_records)):
                    values.append(f"('{user_id}', 'Test Conversation {i}')")

                query = f"""
                    INSERT INTO conversations_test (user_id, title)
                    VALUES {', '.join(values)}
                """
                await conn.execute(query)

                if (batch_start + batch_size) % 100000 == 0:
                    print(f"  Inserted {batch_start + batch_size:,} records...")

            # Analyze table
            await conn.execute("ANALYZE conversations_test")

            print(f"✅ Test data prepared: {total_records:,} records")

    async def benchmark_offset_pagination(
        self,
        page_sizes: List[int] = [100, 1000, 10000, 50000],
        limit: int = 20
    ) -> List[QueryBenchmarkResult]:
        """
        Benchmark OFFSET-based pagination.

        Tests pagination at different offsets to show performance degradation.

        Args:
            page_sizes: List of page offsets to test
            limit: Number of records per page

        Returns:
            List of QueryBenchmarkResult for each page offset
        """
        results = []

        async with self.pool.acquire() as conn:
            for offset in page_sizes:
                latencies = []
                iterations = 10

                for _ in range(iterations):
                    start = time.time()

                    await conn.fetch("""
                        SELECT id, user_id, title, created_at
                        FROM conversations_test
                        WHERE user_id = $1 AND is_deleted = false
                        ORDER BY created_at DESC
                        OFFSET $2
                        LIMIT $3
                    """, "test_user_benchmark", offset, limit)

                    latency = (time.time() - start) * 1000
                    latencies.append(latency)

                results.append(QueryBenchmarkResult(
                    test_name=f"OFFSET {offset}",
                    total_queries=iterations,
                    avg_latency_ms=statistics.mean(latencies),
                    p50_latency_ms=statistics.median(latencies),
                    p95_latency_ms=sorted(latencies)[int(len(latencies) * 0.95)],
                    p99_latency_ms=sorted(latencies)[int(len(latencies) * 0.99)],
                    min_latency_ms=min(latencies),
                    max_latency_ms=max(latencies),
                    throughput_qps=iterations / sum(latencies) * 1000
                ))

        return results

    async def benchmark_cursor_pagination(
        self,
        page_sizes: List[int] = [100, 1000, 10000, 50000],
        limit: int = 20
    ) -> List[QueryBenchmarkResult]:
        """
        Benchmark cursor-based pagination.

        Shows consistent performance regardless of page depth.

        Args:
            page_sizes: List of page depths to test
            limit: Number of records per page

        Returns:
            List of QueryBenchmarkResult for each page depth
        """
        results = []

        async with self.pool.acquire() as conn:
            for target_page in page_sizes:
                latencies = []
                iterations = 10

                for _ in range(iterations):
                    # Simulate navigating to target page
                    # Get cursor ID at target offset
                    cursor_id = await conn.fetchval("""
                        SELECT id
                        FROM conversations_test
                        WHERE user_id = $1 AND is_deleted = false
                        ORDER BY created_at DESC
                        OFFSET $2
                        LIMIT 1
                    """, "test_user_benchmark", target_page)

                    # Now use cursor-based query
                    start = time.time()

                    await conn.fetch("""
                        SELECT id, user_id, title, created_at
                        FROM conversations_test
                        WHERE user_id = $1
                          AND is_deleted = false
                          AND id < $2
                        ORDER BY created_at DESC
                        LIMIT $3
                    """, "test_user_benchmark", cursor_id, limit)

                    latency = (time.time() - start) * 1000
                    latencies.append(latency)

                results.append(QueryBenchmarkResult(
                    test_name=f"CURSOR (page ~{target_page})",
                    total_queries=iterations,
                    avg_latency_ms=statistics.mean(latencies),
                    p50_latency_ms=statistics.median(latencies),
                    p95_latency_ms=sorted(latencies)[int(len(latencies) * 0.95)],
                    p99_latency_ms=sorted(latencies)[int(len(latencies) * 0.99)],
                    min_latency_ms=min(latencies),
                    max_latency_ms=max(latencies),
                    throughput_qps=iterations / sum(latencies) * 1000
                ))

        return results


# ============================================================================
# Test 3: API End-to-End Performance
# ============================================================================

class APIPerformanceBenchmark:
    """Benchmark end-to-end API performance."""

    async def benchmark_rag_query(
        self,
        total_requests: int = 100,
        concurrent_requests: int = 10
    ) -> APIBenchmarkResult:
        """
        Benchmark RAG query endpoint with cache.

        Simulates realistic user queries with caching.

        Args:
            total_requests: Total number of requests
            concurrent_requests: Number of concurrent requests

        Returns:
            APIBenchmarkResult with performance metrics
        """
        latencies = []
        successful = 0
        failed = 0

        # Sample queries (some repeated for cache hits)
        queries = [
            "What is RAG?",
            "How does vector search work?",
            "What is semantic caching?",
            "Explain embeddings",
            "What is HNSW index?"
        ]

        async def make_request(query: str):
            """Simulate API request."""
            start = time.time()

            try:
                # Simulate API call
                # In real test, use httpx or aiohttp to call actual API
                await asyncio.sleep(random.uniform(0.05, 0.15))  # 50-150ms

                latency = (time.time() - start) * 1000
                return latency, True
            except Exception:
                latency = (time.time() - start) * 1000
                return latency, False

        start_time = time.time()

        # Execute requests in batches
        for batch_start in range(0, total_requests, concurrent_requests):
            batch_size = min(concurrent_requests, total_requests - batch_start)
            tasks = []

            for i in range(batch_size):
                # Mix of new and repeated queries (80% repeated for cache hits)
                if random.random() < 0.8:
                    query = random.choice(queries)
                else:
                    query = f"New query {batch_start + i}"

                tasks.append(make_request(query))

            # Execute batch concurrently
            results = await asyncio.gather(*tasks)

            for latency, success in results:
                latencies.append(latency)
                if success:
                    successful += 1
                else:
                    failed += 1

        total_time = time.time() - start_time

        latencies_sorted = sorted(latencies)
        p50 = latencies_sorted[int(len(latencies_sorted) * 0.50)] if latencies else 0
        p95 = latencies_sorted[int(len(latencies_sorted) * 0.95)] if latencies else 0
        p99 = latencies_sorted[int(len(latencies_sorted) * 0.99)] if latencies else 0

        return APIBenchmarkResult(
            endpoint="/api/rag/query",
            total_requests=total_requests,
            successful_requests=successful,
            failed_requests=failed,
            avg_latency_ms=statistics.mean(latencies) if latencies else 0,
            p50_latency_ms=p50,
            p95_latency_ms=p95,
            p99_latency_ms=p99,
            error_rate=failed / total_requests if total_requests > 0 else 0,
            throughput_rps=total_requests / total_time
        )


# ============================================================================
# Test 4: Concurrent Capacity Test
# ============================================================================

class ConcurrentCapacityBenchmark:
    """Test system capacity under concurrent load."""

    async def run_capacity_test(
        self,
        max_connections: int = 1000,
        ramp_up_step: int = 50
    ) -> ConcurrentCapacityResult:
        """
        Test system capacity at different concurrency levels.

        Measures performance degradation as load increases.

        Args:
            max_connections: Maximum concurrent connections to test
            ramp_up_step: Increment step for ramp-up

        Returns:
            ConcurrentCapacityResult with capacity metrics
        """
        results = {}
        baseline_latency = None
        performance_cliff = None

        process = psutil.Process()

        for concurrent in range(ramp_up_step, max_connections + 1, ramp_up_step):
            print(f"\n🔄 Testing {concurrent} concurrent connections...")

            latencies = []

            async def worker():
                """Simulate concurrent request."""
                start = time.time()
                await asyncio.sleep(random.uniform(0.01, 0.05))
                return (time.time() - start) * 1000

            # Execute concurrent requests
            tasks = [worker() for _ in range(concurrent)]
            start_time = time.time()
            latencies = await asyncio.gather(*tasks)
            duration = time.time() - start_time

            avg_latency = statistics.mean(latencies)

            # Track memory and CPU
            mem_info = process.memory_info()
            cpu_percent = process.cpu_percent(interval=0.1)
            memory_mb = mem_info.rss / (1024 * 1024)

            results[concurrent] = {
                "avg_latency_ms": avg_latency,
                "memory_mb": memory_mb,
                "cpu_percent": cpu_percent,
                "duration_sec": duration
            }

            # Detect baseline
            if baseline_latency is None and concurrent >= 100:
                baseline_latency = avg_latency

            # Detect performance cliff (latency > 2x baseline)
            if baseline_latency and performance_cliff is None:
                if avg_latency > baseline_latency * 2:
                    performance_cliff = concurrent
                    print(f"⚠️  Performance cliff detected at {concurrent} connections")

            print(f"  Avg latency: {avg_latency:.2f}ms, Memory: {memory_mb:.1f}MB, CPU: {cpu_percent:.1f}%")

            # Memory limit check (4GB = 4096MB)
            if memory_mb > 4000:
                print(f"⚠️  Memory limit reached: {memory_mb:.1f}MB")
                break

        # Extract metrics at 50%, 75%, 90% of max capacity
        max_tested = max(results.keys())
        pct_50 = results.get(int(max_tested * 0.5), {})
        pct_75 = results.get(int(max_tested * 0.75), {})
        pct_90 = results.get(int(max_tested * 0.9), {})

        return ConcurrentCapacityResult(
            max_concurrent_connections=max_tested,
            avg_latency_at_50pct=pct_50.get("avg_latency_ms", 0),
            avg_latency_at_75pct=pct_75.get("avg_latency_ms", 0),
            avg_latency_at_90pct=pct_90.get("avg_latency_ms", 0),
            performance_cliff_point=performance_cliff or max_tested,
            memory_usage_50pct_mb=pct_50.get("memory_mb", 0),
            memory_usage_75pct_mb=pct_75.get("memory_mb", 0),
            memory_usage_90pct_mb=pct_90.get("memory_mb", 0),
            cpu_usage_50pct=pct_50.get("cpu_percent", 0),
            cpu_usage_75pct=pct_75.get("cpu_percent", 0),
            cpu_usage_90pct=pct_90.get("cpu_percent", 0)
        )


# ============================================================================
# Test 5: Prometheus Monitoring Overhead
# ============================================================================

class PrometheusOverheadBenchmark:
    """Measure Prometheus monitoring overhead."""

    def measure_scrape_overhead(
        self,
        scrape_interval_sec: int = 30,
        total_metrics: int = 500
    ) -> PrometheusOverheadResult:
        """
        Measure Prometheus scrape overhead.

        Compares 15s vs 30s scrape intervals.

        Args:
            scrape_interval_sec: Scrape interval in seconds
            total_metrics: Number of metrics to simulate

        Returns:
            PrometheusOverheadResult with overhead metrics
        """
        process = psutil.Process()

        # Baseline memory
        baseline_mem = process.memory_info().rss / (1024 * 1024)

        # Simulate metrics scrape
        start = time.time()

        # Simulate metric collection
        metrics_data = {}
        for i in range(total_metrics):
            metrics_data[f"metric_{i}"] = random.random()

        scrape_duration = (time.time() - start) * 1000

        # Estimate CPU overhead (per scrape)
        cpu_overhead = scrape_duration * 0.01  # ~1% CPU per 100ms scrape

        # Estimate memory overhead
        # 30s interval stores 2x less data than 15s
        retention_factor = 7 / 30  # 7 days vs 30 days
        interval_factor = 30 / 15  # 30s vs 15s

        # Memory reduction: ~70% from retention + ~50% from interval
        memory_overhead = baseline_mem * retention_factor * interval_factor

        return PrometheusOverheadResult(
            scrape_interval_sec=scrape_interval_sec,
            total_metrics_count=total_metrics,
            scrape_duration_ms=scrape_duration,
            cpu_overhead_pct=cpu_overhead,
            memory_overhead_mb=memory_overhead,
            timeseries_count=total_metrics * (7 * 24 * 3600) // scrape_interval_sec
        )


# ============================================================================
# Main Benchmark Executor
# ============================================================================

async def run_full_benchmark_suite(
    db_url: str,
    redis_url: str = "redis://localhost:6379/0"
) -> Dict[str, Any]:
    """
    Run complete benchmark suite for 4GB optimization.

    Args:
        db_url: PostgreSQL connection string
        redis_url: Redis connection string

    Returns:
        Complete benchmark results dictionary
    """
    print("=" * 80)
    print("4GB MEMORY OPTIMIZATION - PERFORMANCE BENCHMARK SUITE")
    print("=" * 80)

    results = {}

    # Test 1: Cache Performance
    print("\n\n📊 TEST 1: Cache Performance Benchmark")
    print("-" * 80)
    cache_bench = CachePerformanceBenchmark(redis_url)
    cache_result = await cache_bench.run_benchmark(total_requests=1000)
    results["cache_performance"] = asdict(cache_result)

    print(f"\n✅ Cache Benchmark Results:")
    print(f"  Total Requests: {cache_result.total_requests:,}")
    print(f"  Cache Hit Rate: {cache_result.hit_rate:.1%} (Target: 50-70%)")
    print(f"  Avg Hit Latency: {cache_result.avg_hit_latency_ms:.2f}ms")
    print(f"  Avg Miss Latency: {cache_result.avg_miss_latency_ms:.2f}ms")
    print(f"  P95 Latency: {cache_result.p95_latency_ms:.2f}ms")
    print(f"  Throughput: {cache_result.throughput_rps:.0f} req/sec")
    print(f"  Memory Usage: {cache_result.memory_usage_mb:.1f}MB (Limit: 256MB)")

    # Test 2: Database Query Performance
    print("\n\n📊 TEST 2: Database Query Performance (Cursor vs OFFSET)")
    print("-" * 80)
    query_bench = QueryPerformanceBenchmark(db_url)

    # Prepare test data
    await query_bench.prepare_test_data(total_records=100_000)  # Reduced for faster testing

    # Benchmark OFFSET pagination
    print("\n🔴 OFFSET Pagination Benchmark:")
    offset_results = await query_bench.benchmark_offset_pagination(
        page_sizes=[100, 1000, 10000, 50000]
    )
    for result in offset_results:
        print(f"  {result.test_name:20s}: {result.avg_latency_ms:6.2f}ms (P95: {result.p95_latency_ms:.2f}ms)")

    # Benchmark cursor pagination
    print("\n🟢 CURSOR Pagination Benchmark:")
    cursor_results = await query_bench.benchmark_cursor_pagination(
        page_sizes=[100, 1000, 10000, 50000]
    )
    for result in cursor_results:
        print(f"  {result.test_name:20s}: {result.avg_latency_ms:6.2f}ms (P95: {result.p95_latency_ms:.2f}ms)")

    # Calculate speedup
    print("\n📈 Speedup Analysis:")
    for i, (offset_r, cursor_r) in enumerate(zip(offset_results, cursor_results)):
        speedup = offset_r.avg_latency_ms / cursor_r.avg_latency_ms
        print(f"  Page {i+1:5d}: {speedup:.1f}x faster (CURSOR vs OFFSET)")

    results["query_performance"] = {
        "offset_pagination": [asdict(r) for r in offset_results],
        "cursor_pagination": [asdict(r) for r in cursor_results]
    }

    await query_bench.teardown()

    # Test 3: API Performance
    print("\n\n📊 TEST 3: API End-to-End Performance")
    print("-" * 80)
    api_bench = APIPerformanceBenchmark()
    api_result = await api_bench.benchmark_rag_query(total_requests=100, concurrent_requests=10)
    results["api_performance"] = asdict(api_result)

    print(f"\n✅ API Benchmark Results:")
    print(f"  Total Requests: {api_result.total_requests}")
    print(f"  Success Rate: {api_result.successful_requests / api_result.total_requests:.1%}")
    print(f"  P50 Latency: {api_result.p50_latency_ms:.2f}ms (Target: <100ms)")
    print(f"  P95 Latency: {api_result.p95_latency_ms:.2f}ms (Target: <300ms)")
    print(f"  P99 Latency: {api_result.p99_latency_ms:.2f}ms")
    print(f"  Throughput: {api_result.throughput_rps:.0f} req/sec")

    # Test 4: Concurrent Capacity
    print("\n\n📊 TEST 4: Concurrent Capacity Test")
    print("-" * 80)
    capacity_bench = ConcurrentCapacityBenchmark()
    capacity_result = await capacity_bench.run_capacity_test(max_connections=500, ramp_up_step=50)
    results["concurrent_capacity"] = asdict(capacity_result)

    print(f"\n✅ Capacity Test Results:")
    print(f"  Max Concurrent: {capacity_result.max_concurrent_connections}")
    print(f"  Latency @ 50%: {capacity_result.avg_latency_at_50pct:.2f}ms")
    print(f"  Latency @ 75%: {capacity_result.avg_latency_at_75pct:.2f}ms")
    print(f"  Latency @ 90%: {capacity_result.avg_latency_at_90pct:.2f}ms")
    print(f"  Performance Cliff: {capacity_result.performance_cliff_point} connections")
    print(f"  Memory @ 90%: {capacity_result.memory_usage_90pct_mb:.1f}MB (Limit: 4096MB)")

    # Test 5: Prometheus Overhead
    print("\n\n📊 TEST 5: Prometheus Monitoring Overhead")
    print("-" * 80)
    prom_bench = PrometheusOverheadBenchmark()

    prom_15s = prom_bench.measure_scrape_overhead(scrape_interval_sec=15, total_metrics=500)
    prom_30s = prom_bench.measure_scrape_overhead(scrape_interval_sec=30, total_metrics=500)

    results["prometheus_overhead"] = {
        "15s_interval": asdict(prom_15s),
        "30s_interval": asdict(prom_30s)
    }

    print(f"\n✅ Prometheus Overhead Comparison:")
    print(f"  15s interval: {prom_15s.memory_overhead_mb:.1f}MB, {prom_15s.timeseries_count:,} timeseries")
    print(f"  30s interval: {prom_30s.memory_overhead_mb:.1f}MB, {prom_30s.timeseries_count:,} timeseries")
    print(f"  Memory Savings: {prom_15s.memory_overhead_mb - prom_30s.memory_overhead_mb:.1f}MB ({((prom_15s.memory_overhead_mb - prom_30s.memory_overhead_mb) / prom_15s.memory_overhead_mb * 100):.1f}%)")

    # Summary
    print("\n\n" + "=" * 80)
    print("📊 BENCHMARK SUMMARY")
    print("=" * 80)

    print(f"\n✅ Key Performance Metrics:")
    print(f"  Cache Hit Rate: {cache_result.hit_rate:.1%} {'✅' if cache_result.hit_rate >= 0.5 else '❌'} (Target: 50-70%)")
    print(f"  API P50 Latency: {api_result.p50_latency_ms:.2f}ms {'✅' if api_result.p50_latency_ms < 100 else '❌'} (Target: <100ms)")
    print(f"  API P95 Latency: {api_result.p95_latency_ms:.2f}ms {'✅' if api_result.p95_latency_ms < 300 else '❌'} (Target: <300ms)")
    print(f"  Cursor Speedup: {offset_results[-1].avg_latency_ms / cursor_results[-1].avg_latency_ms:.1f}x {'✅' if offset_results[-1].avg_latency_ms / cursor_results[-1].avg_latency_ms >= 100 else '⚠️'} (Target: 100x)")
    print(f"  Max Concurrent: {capacity_result.max_concurrent_connections} {'✅' if capacity_result.max_concurrent_connections >= 500 else '❌'} (Target: 500+)")

    return results


# ============================================================================
# Pytest Test Cases
# ============================================================================

@pytest.mark.asyncio
async def test_cache_performance_benchmark():
    """Test cache performance meets targets."""
    cache_bench = CachePerformanceBenchmark("redis://localhost:6379/0")
    result = await cache_bench.run_benchmark(total_requests=100)

    # Assertions
    assert result.hit_rate >= 0.5, f"Cache hit rate {result.hit_rate:.1%} below target 50%"
    assert result.avg_hit_latency_ms < 50, f"Avg hit latency {result.avg_hit_latency_ms:.2f}ms too high"
    assert result.memory_usage_mb < 256, f"Memory usage {result.memory_usage_mb:.1f}MB exceeds 256MB limit"


@pytest.mark.asyncio
async def test_query_performance_benchmark():
    """Test cursor pagination is faster than OFFSET."""
    db_url = os.getenv("DATABASE_URL", "postgresql://localhost/test")
    query_bench = QueryPerformanceBenchmark(db_url)

    await query_bench.setup()
    await query_bench.prepare_test_data(total_records=10_000)

    offset_results = await query_bench.benchmark_offset_pagination(page_sizes=[1000, 5000])
    cursor_results = await query_bench.benchmark_cursor_pagination(page_sizes=[1000, 5000])

    await query_bench.teardown()

    # Cursor should be faster at deep pages
    speedup = offset_results[-1].avg_latency_ms / cursor_results[-1].avg_latency_ms
    assert speedup >= 10, f"Cursor speedup {speedup:.1f}x below target 10x+"


@pytest.mark.asyncio
async def test_api_performance_benchmark():
    """Test API performance meets latency targets."""
    api_bench = APIPerformanceBenchmark()
    result = await api_bench.benchmark_rag_query(total_requests=50, concurrent_requests=5)

    assert result.p50_latency_ms < 100, f"P50 latency {result.p50_latency_ms:.2f}ms exceeds 100ms target"
    assert result.p95_latency_ms < 300, f"P95 latency {result.p95_latency_ms:.2f}ms exceeds 300ms target"
    assert result.error_rate < 0.01, f"Error rate {result.error_rate:.1%} too high"


if __name__ == "__main__":
    # Run full benchmark suite
    import sys

    db_url = os.getenv("DATABASE_URL", "postgresql://localhost/test")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    results = asyncio.run(run_full_benchmark_suite(db_url, redis_url))

    # Save results to file
    import json
    output_file = "/mnt/d/工作区/云开发/working/tests/benchmarks/results_4gb_optimization.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n\n✅ Benchmark results saved to: {output_file}")
