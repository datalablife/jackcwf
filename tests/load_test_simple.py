"""
Simplified load testing for API availability and performance.

Tests basic endpoint availability and response times.
"""

import time
import statistics
from typing import Dict, List
from locust import HttpUser, task, between, events


class SimpleLoadMetrics:
    """Track simple performance metrics."""

    def __init__(self):
        self.health_latencies: List[float] = []
        self.docs_latencies: List[float] = []
        self.api_errors = 0
        self.api_success = 0

    def record_health(self, latency_ms: float):
        """Record health check latency."""
        self.health_latencies.append(latency_ms)

    def record_docs(self, latency_ms: float):
        """Record API docs latency."""
        self.docs_latencies.append(latency_ms)

    def record_error(self):
        """Record an error."""
        self.api_errors += 1

    def record_success(self):
        """Record a success."""
        self.api_success += 1

    def get_summary(self) -> Dict:
        """Get performance summary."""
        def stats(latencies):
            if not latencies:
                return {}
            return {
                "min": min(latencies),
                "max": max(latencies),
                "avg": statistics.mean(latencies),
                "median": statistics.median(latencies),
                "p95": sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 0 else 0,
                "p99": sorted(latencies)[int(len(latencies) * 0.99)] if len(latencies) > 0 else 0,
            }

        return {
            "total_requests": self.api_success + self.api_errors,
            "success": self.api_success,
            "errors": self.api_errors,
            "error_rate_percent": (self.api_errors / (self.api_success + self.api_errors) * 100) if (self.api_success + self.api_errors) > 0 else 0,
            "health_latencies": stats(self.health_latencies),
            "docs_latencies": stats(self.docs_latencies),
        }


# Global metrics tracker
metrics = SimpleLoadMetrics()


class SimpleLoadTest(HttpUser):
    """Basic load test for API endpoints."""

    wait_time = between(0.5, 2.0)
    host = "http://localhost:8000"

    @task(weight=60)
    def test_health_endpoint(self):
        """Test health endpoint."""
        start_time = time.time()
        try:
            response = self.client.get("/health", name="/health")
            latency_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                metrics.record_health(latency_ms)
                metrics.record_success()
            else:
                metrics.record_error()
        except Exception as e:
            metrics.record_error()

    @task(weight=40)
    def test_api_docs(self):
        """Test API docs endpoint."""
        start_time = time.time()
        try:
            response = self.client.get("/api/docs", name="/api/docs")
            latency_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                metrics.record_docs(latency_ms)
                metrics.record_success()
            else:
                metrics.record_error()
        except Exception as e:
            metrics.record_error()


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops."""
    summary = metrics.get_summary()

    print("\n" + "=" * 80)
    print("API AVAILABILITY TEST RESULTS")
    print("=" * 80)
    print(f"Total Requests: {summary['total_requests']}")
    print(f"Success: {summary['success']}")
    print(f"Errors: {summary['errors']}")
    print(f"Error Rate: {summary['error_rate_percent']:.1f}%")
    print(f"Target Error Rate: < 5%")
    print(f"Status: {'✅ PASS' if summary['error_rate_percent'] < 5 else '❌ FAIL'}")
    print()

    print("HEALTH ENDPOINT LATENCIES (ms):")
    if summary["health_latencies"]:
        for key, value in summary["health_latencies"].items():
            print(f"  {key}: {value:.1f}ms")
        print(f"  Target: < 100ms")
        avg = summary["health_latencies"]["avg"]
        print(f"  Status: {'✅ PASS' if avg < 100 else '❌ FAIL'}")
    else:
        print("  No health endpoint requests recorded")
    print()

    print("API DOCS ENDPOINT LATENCIES (ms):")
    if summary["docs_latencies"]:
        for key, value in summary["docs_latencies"].items():
            print(f"  {key}: {value:.1f}ms")
        print(f"  Target: < 200ms")
        avg = summary["docs_latencies"]["avg"]
        print(f"  Status: {'✅ PASS' if avg < 200 else '❌ FAIL'}")
    else:
        print("  No API docs requests recorded")
    print("=" * 80)
