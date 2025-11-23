#!/usr/bin/env python3
"""
4GB Deployment Performance Stress Test
=======================================
Simulates realistic production load to validate 4GB memory configuration.

Test Scenarios:
1. Normal Load: 100 req/s
2. Peak Load: 200 req/s
3. Spike Load: 500 req/s
4. Sustained Load: 150 req/s for 10 minutes

Metrics Collected:
- API response times (P50, P95, P99)
- Memory usage per container
- Database connection count
- Cache hit rate
- Error rate

Usage:
    python scripts/infrastructure/stress-test-4gb.py --duration 300 --output results/
"""

import asyncio
import aiohttp
import time
import json
import argparse
from typing import List, Dict
from datetime import datetime
from dataclasses import dataclass, asdict
import statistics
import subprocess

@dataclass
class StressTestResult:
    timestamp: str
    scenario: str
    duration_seconds: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    requests_per_second: float
    error_rate: float
    memory_usage_mb: Dict[str, float]
    database_connections: int
    cache_hit_rate: float


class StressTest:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.latencies: List[float] = []
        self.errors: int = 0
        self.success: int = 0

    async def make_request(self, session: aiohttp.ClientSession, endpoint: str = "/health"):
        """Make a single HTTP request and measure latency."""
        start = time.time()
        try:
            async with session.get(f"{self.base_url}{endpoint}", timeout=10) as response:
                await response.text()
                latency = (time.time() - start) * 1000  # Convert to ms
                self.latencies.append(latency)
                if response.status == 200:
                    self.success += 1
                else:
                    self.errors += 1
                return latency
        except Exception as e:
            self.errors += 1
            latency = (time.time() - start) * 1000
            self.latencies.append(latency)
            print(f"Request failed: {e}")
            return latency

    async def run_load_test(self, requests_per_second: int, duration_seconds: int):
        """Generate load at specified rate for given duration."""
        connector = aiohttp.TCPConnector(limit=200, limit_per_host=200)
        timeout = aiohttp.ClientTimeout(total=30)

        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            start_time = time.time()
            tasks = []

            while time.time() - start_time < duration_seconds:
                # Create burst of requests
                for _ in range(requests_per_second):
                    task = asyncio.create_task(self.make_request(session))
                    tasks.append(task)

                # Wait 1 second before next batch
                await asyncio.sleep(1)

                # Periodically collect completed tasks to prevent memory buildup
                if len(tasks) > 1000:
                    await asyncio.gather(*tasks, return_exceptions=True)
                    tasks.clear()

            # Wait for remaining tasks
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    def get_docker_stats(self) -> Dict[str, float]:
        """Get current memory usage of all containers."""
        try:
            result = subprocess.run(
                ["docker", "stats", "--no-stream", "--format", "{{.Container}}\t{{.MemUsage}}"],
                capture_output=True,
                text=True,
                timeout=5
            )

            memory_usage = {}
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split("\t")
                    if len(parts) == 2:
                        container, mem = parts
                        # Extract MB value (e.g., "500MiB / 800MiB" -> 500)
                        mem_mb = float(mem.split()[0].replace("MiB", "").replace("GiB", "000"))
                        memory_usage[container] = mem_mb

            return memory_usage
        except Exception as e:
            print(f"Failed to get docker stats: {e}")
            return {}

    def get_database_connections(self) -> int:
        """Get current PostgreSQL connection count."""
        try:
            result = subprocess.run(
                [
                    "docker", "exec", "postgres",
                    "psql", "-U", "langchain", "-d", "langchain_db", "-t",
                    "-c", "SELECT count(*) FROM pg_stat_activity;"
                ],
                capture_output=True,
                text=True,
                timeout=5
            )
            return int(result.stdout.strip())
        except Exception as e:
            print(f"Failed to get DB connections: {e}")
            return -1

    def get_cache_hit_rate(self) -> float:
        """Get Redis cache hit rate."""
        try:
            result = subprocess.run(
                ["docker", "exec", "redis-cache", "redis-cli", "INFO", "stats"],
                capture_output=True,
                text=True,
                timeout=5
            )

            hits, misses = 0, 0
            for line in result.stdout.split("\n"):
                if "keyspace_hits:" in line:
                    hits = int(line.split(":")[1].strip())
                elif "keyspace_misses:" in line:
                    misses = int(line.split(":")[1].strip())

            if hits + misses > 0:
                return (hits / (hits + misses)) * 100
            return 0.0
        except Exception as e:
            print(f"Failed to get cache hit rate: {e}")
            return -1.0

    def calculate_metrics(self, scenario: str, duration: int) -> StressTestResult:
        """Calculate performance metrics from collected data."""
        total = len(self.latencies)

        if total == 0:
            print("WARNING: No successful requests!")
            return StressTestResult(
                timestamp=datetime.now().isoformat(),
                scenario=scenario,
                duration_seconds=duration,
                total_requests=0,
                successful_requests=0,
                failed_requests=self.errors,
                avg_latency_ms=0,
                p50_latency_ms=0,
                p95_latency_ms=0,
                p99_latency_ms=0,
                min_latency_ms=0,
                max_latency_ms=0,
                requests_per_second=0,
                error_rate=100.0,
                memory_usage_mb={},
                database_connections=0,
                cache_hit_rate=0
            )

        sorted_latencies = sorted(self.latencies)

        return StressTestResult(
            timestamp=datetime.now().isoformat(),
            scenario=scenario,
            duration_seconds=duration,
            total_requests=total + self.errors,
            successful_requests=self.success,
            failed_requests=self.errors,
            avg_latency_ms=statistics.mean(self.latencies),
            p50_latency_ms=sorted_latencies[int(len(sorted_latencies) * 0.50)],
            p95_latency_ms=sorted_latencies[int(len(sorted_latencies) * 0.95)],
            p99_latency_ms=sorted_latencies[int(len(sorted_latencies) * 0.99)],
            min_latency_ms=min(self.latencies),
            max_latency_ms=max(self.latencies),
            requests_per_second=(total + self.errors) / duration,
            error_rate=(self.errors / (total + self.errors)) * 100 if (total + self.errors) > 0 else 0,
            memory_usage_mb=self.get_docker_stats(),
            database_connections=self.get_database_connections(),
            cache_hit_rate=self.get_cache_hit_rate()
        )

    def reset_metrics(self):
        """Reset metrics for next test."""
        self.latencies.clear()
        self.errors = 0
        self.success = 0


async def run_stress_test_suite(base_url: str, output_dir: str):
    """Run complete stress test suite with multiple scenarios."""

    test = StressTest(base_url)
    results = []

    print("\n" + "="*60)
    print("4GB Deployment Stress Test Suite")
    print("="*60)
    print(f"Target: {base_url}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")

    # Scenario 1: Normal Load
    print("[1/4] Running Normal Load Test (100 req/s for 60s)...")
    test.reset_metrics()
    await test.run_load_test(requests_per_second=100, duration_seconds=60)
    result1 = test.calculate_metrics("Normal Load", 60)
    results.append(result1)
    print(f"  ✓ Completed: {result1.successful_requests} requests, "
          f"P95: {result1.p95_latency_ms:.1f}ms, "
          f"Errors: {result1.error_rate:.1f}%\n")

    # Wait between tests
    print("  Cooling down for 30 seconds...")
    await asyncio.sleep(30)

    # Scenario 2: Peak Load
    print("[2/4] Running Peak Load Test (200 req/s for 60s)...")
    test.reset_metrics()
    await test.run_load_test(requests_per_second=200, duration_seconds=60)
    result2 = test.calculate_metrics("Peak Load", 60)
    results.append(result2)
    print(f"  ✓ Completed: {result2.successful_requests} requests, "
          f"P95: {result2.p95_latency_ms:.1f}ms, "
          f"Errors: {result2.error_rate:.1f}%\n")

    await asyncio.sleep(30)

    # Scenario 3: Spike Load
    print("[3/4] Running Spike Load Test (500 req/s for 30s)...")
    test.reset_metrics()
    await test.run_load_test(requests_per_second=500, duration_seconds=30)
    result3 = test.calculate_metrics("Spike Load", 30)
    results.append(result3)
    print(f"  ✓ Completed: {result3.successful_requests} requests, "
          f"P95: {result3.p95_latency_ms:.1f}ms, "
          f"Errors: {result3.error_rate:.1f}%\n")

    await asyncio.sleep(30)

    # Scenario 4: Sustained Load
    print("[4/4] Running Sustained Load Test (150 req/s for 300s)...")
    test.reset_metrics()
    await test.run_load_test(requests_per_second=150, duration_seconds=300)
    result4 = test.calculate_metrics("Sustained Load", 300)
    results.append(result4)
    print(f"  ✓ Completed: {result4.successful_requests} requests, "
          f"P95: {result4.p95_latency_ms:.1f}ms, "
          f"Errors: {result4.error_rate:.1f}%\n")

    # Generate report
    print("\n" + "="*60)
    print("STRESS TEST RESULTS SUMMARY")
    print("="*60 + "\n")

    for result in results:
        print(f"Scenario: {result.scenario}")
        print(f"  Total Requests: {result.total_requests}")
        print(f"  Success Rate: {(result.successful_requests/result.total_requests)*100:.1f}%")
        print(f"  Avg Latency: {result.avg_latency_ms:.1f}ms")
        print(f"  P50 Latency: {result.p50_latency_ms:.1f}ms")
        print(f"  P95 Latency: {result.p95_latency_ms:.1f}ms")
        print(f"  P99 Latency: {result.p99_latency_ms:.1f}ms")
        print(f"  Throughput: {result.requests_per_second:.1f} req/s")
        print(f"  Error Rate: {result.error_rate:.2f}%")
        print(f"  DB Connections: {result.database_connections}")
        print(f"  Cache Hit Rate: {result.cache_hit_rate:.1f}%")
        print(f"  Memory Usage:")
        for container, mem in result.memory_usage_mb.items():
            print(f"    {container}: {mem:.1f}MB")
        print()

    # Save results to JSON
    output_file = f"{output_dir}/stress_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump([asdict(r) for r in results], f, indent=2)

    print(f"Results saved to: {output_file}")
    print("\n" + "="*60)
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")

    # Generate performance verdict
    print("PERFORMANCE VERDICT:")
    print("-" * 60)

    # Check if meets criteria
    passed_normal = result1.p95_latency_ms < 500 and result1.error_rate < 1.0
    passed_peak = result2.p95_latency_ms < 1000 and result2.error_rate < 5.0
    passed_spike = result3.error_rate < 10.0
    passed_sustained = result4.p95_latency_ms < 800 and result4.error_rate < 2.0

    print(f"Normal Load (100 req/s):  {'✓ PASS' if passed_normal else '✗ FAIL'}")
    print(f"Peak Load (200 req/s):    {'✓ PASS' if passed_peak else '✗ FAIL'}")
    print(f"Spike Load (500 req/s):   {'✓ PASS' if passed_spike else '✗ FAIL'}")
    print(f"Sustained Load (150/s):   {'✓ PASS' if passed_sustained else '✗ FAIL'}")

    all_passed = passed_normal and passed_peak and passed_spike and passed_sustained
    print("\n" + "="*60)
    if all_passed:
        print("OVERALL STATUS: ✓ READY FOR PRODUCTION")
    else:
        print("OVERALL STATUS: ✗ NEEDS OPTIMIZATION")
    print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="4GB Deployment Stress Test")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of API")
    parser.add_argument("--output", default="./results", help="Output directory for results")
    args = parser.parse_args()

    # Create output directory
    import os
    os.makedirs(args.output, exist_ok=True)

    # Run stress test
    asyncio.run(run_stress_test_suite(args.url, args.output))


if __name__ == "__main__":
    main()
