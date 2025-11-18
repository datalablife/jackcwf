"""
Load testing script for semantic cache performance validation.

Tests the RAG query pipeline with semantic caching to validate:
- Cache hit rate (target: 40-60%)
- Latency improvement (target: 850ms → 400ms, 53% improvement)
- Cache efficiency
"""

import time
import random
import statistics
from typing import Dict, List
from locust import HttpUser, task, between, events
from locust.contrib.fasthttp import FastHttpUser


# Test queries for cache validation
TEST_QUERIES = [
    "What is retrieval-augmented generation (RAG)?",
    "How does semantic caching improve LLM performance?",
    "Explain the HNSW index algorithm",
    "What are the benefits of vector similarity search?",
    "How does Lantern PostgreSQL extension work?",
    "What is Claude 3.5 Sonnet model?",
    "Explain embedding models and their use cases",
    "What is the difference between L2 and cosine distance?",
    "How does the cache invalidation work?",
    "What are the performance metrics for cache hit vs miss?",
    # Repeated queries to generate cache hits
    "What is retrieval-augmented generation (RAG)?",
    "How does semantic caching improve LLM performance?",
    "Explain the HNSW index algorithm",
    "What are the benefits of vector similarity search?",
]


class CachePerformanceMetrics:
    """Track cache performance metrics."""

    def __init__(self):
        self.cache_hits = 0
        self.cache_misses = 0
        self.hit_latencies: List[float] = []
        self.miss_latencies: List[float] = []

    def record_hit(self, latency_ms: float):
        """Record a cache hit."""
        self.cache_hits += 1
        self.hit_latencies.append(latency_ms)

    def record_miss(self, latency_ms: float):
        """Record a cache miss."""
        self.cache_misses += 1
        self.miss_latencies.append(latency_ms)

    def get_summary(self) -> Dict:
        """Get performance summary."""
        total = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total * 100) if total > 0 else 0

        def stats(latencies):
            if not latencies:
                return {}
            return {
                "min": min(latencies),
                "max": max(latencies),
                "avg": statistics.mean(latencies),
                "median": statistics.median(latencies),
                "p95": sorted(latencies)[int(len(latencies) * 0.95)],
                "p99": sorted(latencies)[int(len(latencies) * 0.99)],
            }

        return {
            "total_queries": total,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate_percent": hit_rate,
            "hit_latencies": stats(self.hit_latencies),
            "miss_latencies": stats(self.miss_latencies),
        }


# Global metrics tracker
metrics = CachePerformanceMetrics()


class CacheLoadTest(FastHttpUser):
    """Load test user for semantic cache performance validation."""

    wait_time = between(0.5, 2.0)  # Wait between requests
    host = "http://localhost:8000"  # Default host

    def on_start(self):
        """Called when a simulated user starts."""
        self.query_count = 0

    @task(weight=100)
    def test_chat_with_cache(self):
        """Test the chat endpoint with caching enabled."""
        query = random.choice(TEST_QUERIES)
        self.query_count += 1

        start_time = time.time()

        try:
            response = self.client.post(
                "/api/conversations/v1/chat",
                json={"message": query, "enable_cache": True, "doc_ids": None},
                name="/api/conversations/v1/chat (cached)",
            )

            if response.status_code == 200:
                end_time = time.time()
                latency_ms = (end_time - start_time) * 1000

                data = response.json()
                is_cached = data.get("cached", False)

                if is_cached:
                    metrics.record_hit(latency_ms)
                else:
                    metrics.record_miss(latency_ms)

                # Print progress
                if self.query_count % 10 == 0:
                    summary = metrics.get_summary()
                    print(
                        f"\n[Query {self.query_count}] "
                        f"Hit Rate: {summary['hit_rate_percent']:.1f}% | "
                        f"Hits: {summary['cache_hits']} | "
                        f"Misses: {summary['cache_misses']} | "
                        f"Latency: {latency_ms:.0f}ms {'(HIT)' if is_cached else '(MISS)'}"
                    )
            else:
                self.environment.runner.stop()
                print(f"Error: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"Request failed: {e}")


class CacheLoadTestWithoutCache(FastHttpUser):
    """Load test user without caching for performance comparison."""

    wait_time = between(0.5, 2.0)
    host = "http://localhost:8000"
    weight = 10  # 10% of users don't use cache

    @task(weight=100)
    def test_chat_without_cache(self):
        """Test the chat endpoint with caching disabled."""
        query = random.choice(TEST_QUERIES[:5])  # Use subset of queries

        start_time = time.time()

        try:
            response = self.client.post(
                "/api/conversations/v1/chat",
                json={"message": query, "enable_cache": False, "doc_ids": None},
                name="/api/conversations/v1/chat (no-cache)",
            )

            if response.status_code == 200:
                end_time = time.time()
                latency_ms = (end_time - start_time) * 1000
                metrics.record_miss(latency_ms)
        except Exception as e:
            print(f"Request failed: {e}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the load test stops."""
    summary = metrics.get_summary()

    print("\n" + "=" * 80)
    print("CACHE PERFORMANCE TEST RESULTS")
    print("=" * 80)
    print(f"Total Queries: {summary['total_queries']}")
    print(f"Cache Hits: {summary['cache_hits']}")
    print(f"Cache Misses: {summary['cache_misses']}")
    print(f"Hit Rate: {summary['hit_rate_percent']:.1f}%")
    print(f"Target Hit Rate: 40-60%")
    print(
        f"Target Status: {'✅ PASS' if 40 <= summary['hit_rate_percent'] <= 60 else '❌ FAIL'}"
    )
    print()
    print("CACHE HIT LATENCIES (ms):")
    if summary["hit_latencies"]:
        for key, value in summary["hit_latencies"].items():
            print(f"  {key}: {value:.1f}ms")
        target_hit = 300
        avg_hit = summary["hit_latencies"]["avg"]
        print(f"  Target: {target_hit}ms")
        print(f"  Status: {'✅ PASS' if avg_hit <= target_hit else '❌ FAIL'}")
    else:
        print("  No cache hits recorded")
    print()
    print("CACHE MISS LATENCIES (ms):")
    if summary["miss_latencies"]:
        for key, value in summary["miss_latencies"].items():
            print(f"  {key}: {value:.1f}ms")
        target_miss = 850
        avg_miss = summary["miss_latencies"]["avg"]
        print(f"  Target: {target_miss}ms")
        print(f"  Status: {'✅ PASS' if avg_miss <= target_miss else '❌ FAIL'}")
    else:
        print("  No cache misses recorded")
    print()
    print("LATENCY IMPROVEMENT:")
    if summary["hit_latencies"] and summary["miss_latencies"]:
        avg_hit = summary["hit_latencies"]["avg"]
        avg_miss = summary["miss_latencies"]["avg"]
        improvement = ((avg_miss - avg_hit) / avg_miss) * 100
        print(f"  Improvement: {improvement:.1f}% ({avg_miss:.1f}ms → {avg_hit:.1f}ms)")
        print(f"  Target: 53% improvement")
        print(f"  Status: {'✅ PASS' if improvement >= 50 else '❌ FAIL'}")
    print("=" * 80)


if __name__ == "__main__":
    import os

    # Print instructions
    print("Load Test Configuration:")
    print("  - Users: 10 (default)")
    print("  - Spawn Rate: 1 user/s (default)")
    print("  - Duration: Run via 'locust' CLI")
    print("  - Host: http://localhost:8000 (set LOCUST_HOST env var to change)")
    print()
    print("Run with:")
    print("  locust -f tests/load_test_cache.py --host=http://localhost:8000")
    print()
    print("Or with custom settings:")
    print("  locust -f tests/load_test_cache.py --host=http://localhost:8000 -u 50 -r 5 -t 5m")
    print()
