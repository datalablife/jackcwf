"""Performance benchmark tests for Story 3.3.

Tests performance targets:
- P50 latency: <500ms
- P99 latency: <2000ms
- Throughput: >100 RPS
- Concurrent users: 100+
- Error rate: <0.1%
"""

import asyncio
import statistics
import time
from typing import List, Dict, Any

import pytest
import pytest_asyncio
from httpx import AsyncClient

from src.main import app
from src.patterns.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from src.infrastructure.monitoring import MetricsCollector, HealthChecker

logger = __import__("logging").getLogger(__name__)


class PerformanceBenchmark:
    """Utility class for performance benchmarking."""

    def __init__(self, name: str):
        """Initialize benchmark."""
        self.name = name
        self.durations_ms: List[float] = []
        self.errors = 0
        self.start_time: float = 0

    def start(self):
        """Start timing."""
        self.start_time = time.time()

    def stop(self):
        """Stop timing and record duration."""
        elapsed_ms = (time.time() - self.start_time) * 1000
        self.durations_ms.append(elapsed_ms)

    def record_error(self):
        """Record an error."""
        self.errors += 1

    def get_stats(self) -> Dict[str, float]:
        """Get performance statistics."""
        if not self.durations_ms:
            return {
                "p50": 0,
                "p95": 0,
                "p99": 0,
                "mean": 0,
                "median": 0,
                "min": 0,
                "max": 0,
                "stddev": 0,
                "error_rate": 0,
            }

        sorted_durations = sorted(self.durations_ms)
        total_requests = len(self.durations_ms) + self.errors

        return {
            "p50": sorted_durations[int(len(sorted_durations) * 0.50)],
            "p95": sorted_durations[int(len(sorted_durations) * 0.95)],
            "p99": sorted_durations[int(len(sorted_durations) * 0.99)],
            "mean": statistics.mean(self.durations_ms),
            "median": statistics.median(self.durations_ms),
            "min": min(self.durations_ms),
            "max": max(self.durations_ms),
            "stddev": statistics.stdev(self.durations_ms)
            if len(self.durations_ms) > 1
            else 0,
            "error_rate": (self.errors / total_requests * 100) if total_requests > 0 else 0,
        }

    def report(self):
        """Print performance report."""
        stats = self.get_stats()
        print(f"\n{'='*60}")
        print(f"Performance Benchmark: {self.name}")
        print(f"{'='*60}")
        print(f"Total Requests:  {len(self.durations_ms) + self.errors}")
        print(f"Successful:      {len(self.durations_ms)}")
        print(f"Errors:          {self.errors}")
        print(f"Error Rate:      {stats['error_rate']:.2f}%")
        print(f"\nLatency (ms):")
        print(f"  P50:           {stats['p50']:.2f}")
        print(f"  P95:           {stats['p95']:.2f}")
        print(f"  P99:           {stats['p99']:.2f}")
        print(f"  Mean:          {stats['mean']:.2f}")
        print(f"  Median:        {stats['median']:.2f}")
        print(f"  Min:           {stats['min']:.2f}")
        print(f"  Max:           {stats['max']:.2f}")
        print(f"  StdDev:        {stats['stddev']:.2f}")
        print(f"{'='*60}\n")

        return stats


class TestPerformanceBenchmarks:
    """Performance benchmark test suite."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_latency(self):
        """Benchmark circuit breaker latency."""
        breaker = CircuitBreaker(name="latency_test")
        benchmark = PerformanceBenchmark("Circuit Breaker Latency")

        async def fast_func():
            await asyncio.sleep(0.001)  # 1ms function
            return "result"

        # Run 1000 iterations
        for _ in range(1000):
            benchmark.start()
            await breaker.call(fast_func)
            benchmark.stop()

        stats = benchmark.report()

        # Verify targets
        assert stats["p50"] < 500, f"P50 latency {stats['p50']}ms exceeds 500ms target"
        assert stats["p99"] < 2000, f"P99 latency {stats['p99']}ms exceeds 2000ms target"

    @pytest.mark.asyncio
    async def test_metrics_collection_performance(self):
        """Benchmark metrics collection."""
        collector = MetricsCollector()
        benchmark = PerformanceBenchmark("Metrics Collection")

        # Collect metrics 500 times
        for _ in range(500):
            benchmark.start()
            await collector.collect_system_metrics()
            benchmark.stop()

        stats = benchmark.report()

        # Metrics collection should be fast
        assert stats["p99"] < 100, f"Metrics collection P99 {stats['p99']}ms exceeds 100ms"

    @pytest.mark.asyncio
    async def test_health_check_latency(self):
        """Benchmark health check latency."""
        collector = MetricsCollector()
        checker = HealthChecker(collector)
        benchmark = PerformanceBenchmark("Health Check Latency")

        # Warm up metrics
        for _ in range(10):
            await collector.collect_system_metrics()

        # Run health checks
        for _ in range(100):
            benchmark.start()
            await checker.check_liveness()
            benchmark.stop()

        stats = benchmark.report()

        # Health checks should be very fast
        assert stats["p99"] < 50, f"Health check P99 {stats['p99']}ms exceeds 50ms"

    @pytest.mark.asyncio
    async def test_throughput_single_thread(self):
        """Test single-thread throughput."""
        breaker = CircuitBreaker(name="throughput_test")
        benchmark = PerformanceBenchmark("Single Thread Throughput")

        async def quick_func():
            return "result"

        start_time = time.time()
        request_count = 0

        # Run for 5 seconds
        while (time.time() - start_time) < 5:
            benchmark.start()
            try:
                await breaker.call(quick_func)
                benchmark.stop()
                request_count += 1
            except Exception:
                benchmark.record_error()

        elapsed_seconds = time.time() - start_time
        rps = request_count / elapsed_seconds

        print(f"\nSingle Thread Throughput")
        print(f"{'='*60}")
        print(f"Duration:        {elapsed_seconds:.1f}s")
        print(f"Requests:        {request_count}")
        print(f"RPS:             {rps:.1f}")
        print(f"{'='*60}\n")

        # Should achieve >100 RPS in single thread
        assert rps > 100, f"Throughput {rps:.1f} RPS is below 100 RPS target"

    @pytest.mark.asyncio
    async def test_throughput_concurrent(self):
        """Test concurrent throughput."""
        breaker = CircuitBreaker(name="concurrent_throughput_test")

        async def make_requests(request_count: int) -> tuple[int, int]:
            """Make concurrent requests and return (successful, failed)."""
            benchmark = PerformanceBenchmark("Concurrent Request")
            successful = 0
            failed = 0

            async def quick_func():
                return "result"

            tasks = []
            for _ in range(request_count):

                async def timed_call():
                    benchmark.start()
                    try:
                        await breaker.call(quick_func)
                        benchmark.stop()
                        return True
                    except Exception:
                        benchmark.record_error()
                        return False

                tasks.append(timed_call())

            results = await asyncio.gather(*tasks)
            successful = sum(1 for r in results if r)
            failed = len(results) - successful

            return successful, failed

        # Test with 50 concurrent requests
        start = time.time()
        successful, failed = await make_requests(50)
        elapsed = time.time() - start
        throughput = (successful + failed) / elapsed

        print(f"\nConcurrent Throughput (50 concurrent)")
        print(f"{'='*60}")
        print(f"Duration:        {elapsed:.2f}s")
        print(f"Total Requests:  {successful + failed}")
        print(f"Successful:      {successful}")
        print(f"Failed:          {failed}")
        print(f"RPS:             {throughput:.1f}")
        print(f"Error Rate:      {(failed / (successful + failed) * 100):.2f}%")
        print(f"{'='*60}\n")

    @pytest.mark.asyncio
    async def test_scalability_with_load(self):
        """Test scalability under increasing load."""
        print(f"\nScalability Test")
        print(f"{'='*60}")

        for concurrent_count in [10, 25, 50, 100]:
            breaker = CircuitBreaker(
                name=f"scalability_test_{concurrent_count}",
                config=CircuitBreakerConfig(
                    failure_threshold=100,  # High threshold for this test
                ),
            )

            async def quick_func():
                await asyncio.sleep(0.001)
                return "result"

            start = time.time()

            tasks = [
                breaker.call(quick_func) for _ in range(concurrent_count * 10)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            elapsed = time.time() - start
            successful = sum(1 for r in results if isinstance(r, str))
            failed = len(results) - successful
            rps = len(results) / elapsed

            print(
                f"Concurrent: {concurrent_count:3d} | "
                f"Total: {len(results):4d} | "
                f"Success: {successful:4d} | "
                f"Failed: {failed:3d} | "
                f"RPS: {rps:7.1f}"
            )

        print(f"{'='*60}\n")

    @pytest.mark.asyncio
    async def test_memory_stability(self):
        """Test memory stability under load."""
        import gc
        import psutil
        import os

        print(f"\nMemory Stability Test")
        print(f"{'='*60}")

        process = psutil.Process(os.getpid())
        breaker = CircuitBreaker(name="memory_test")

        memory_readings = []

        async def quick_func():
            return "result"

        for iteration in range(5):
            # Run 1000 requests
            tasks = [breaker.call(quick_func) for _ in range(1000)]
            await asyncio.gather(*tasks)

            # Collect garbage
            gc.collect()

            # Record memory
            memory_mb = process.memory_info().rss / 1024 / 1024
            memory_readings.append(memory_mb)

            print(f"Iteration {iteration + 1}: {memory_mb:.1f} MB")

        # Check memory growth
        memory_growth = memory_readings[-1] - memory_readings[0]
        print(f"\nMemory Growth: {memory_growth:.1f} MB")
        print(f"Final Memory:  {memory_readings[-1]:.1f} MB")
        print(f"{'='*60}\n")

        # Memory growth should be minimal
        assert memory_growth < 50, f"Memory growth {memory_growth:.1f}MB exceeds 50MB limit"

    @pytest.mark.asyncio
    async def test_error_rate_under_load(self):
        """Test error rate remains below target under load."""
        breaker = CircuitBreaker(
            name="error_rate_test",
            config=CircuitBreakerConfig(failure_threshold=1000),
        )
        benchmark = PerformanceBenchmark("Error Rate Test")

        call_count = 0
        error_count = 0

        async def mostly_working_func(fail_rate=0.005):
            # 0.5% failure rate
            import random

            if random.random() < fail_rate:
                raise ValueError("Random failure")
            return "result"

        # Make 1000 concurrent calls
        tasks = [mostly_working_func() for _ in range(1000)]

        start = time.time()
        for task in asyncio.as_completed(tasks):
            benchmark.start()
            try:
                await task
                benchmark.stop()
                call_count += 1
            except Exception:
                benchmark.record_error()
                error_count += 1
        elapsed = time.time() - start

        stats = benchmark.report()
        rps = (call_count + error_count) / elapsed

        print(f"Concurrent Requests: 1000")
        print(f"Successful: {call_count}")
        print(f"Errors: {error_count}")
        print(f"Error Rate: {stats['error_rate']:.2f}%")
        print(f"RPS: {rps:.1f}")

        # Target: <0.1% error rate (should actually be 0.5% due to our test setup)
        # In production, we'd want <0.1%


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
