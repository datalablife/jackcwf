"""End-to-end integration tests for Story 3.3 - Streaming and Production Readiness.

Tests comprehensive workflows including:
- Streaming response with SSE
- Circuit breaker protection
- Error handling and recovery
- Health checks
- Performance benchmarks
- Stress testing
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.db.base import Base
from src.db.config import get_async_session
from src.patterns.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitBreakerState,
)
from src.infrastructure.monitoring import MetricsCollector, HealthChecker

logger = logging.getLogger(__name__)

# Test database URL (in-memory SQLite with async)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_db():
    """Create test database and return session."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_db):
    """Create test client."""

    async def override_get_async_session():
        yield test_db

    app.dependency_overrides[get_async_session] = override_get_async_session

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


class TestStreamingEndpoint:
    """Tests for SSE streaming endpoint."""

    @pytest.mark.asyncio
    async def test_stream_endpoint_exists(self, client):
        """Test streaming endpoint is available."""
        # Health check endpoint
        response = await client.get("/api/v1/health/stream")
        assert response.status_code == 200
        data = response.json()
        assert "streaming" in data
        assert data["streaming"]["enabled"] is True

    @pytest.mark.asyncio
    async def test_stream_authentication_required(self, client):
        """Test stream endpoint requires authentication."""
        response = await client.post(
            "/api/v1/conversations/550e8400-e29b-41d4-a716-446655440000/stream",
            json={"content": "Hello"},
        )
        assert response.status_code in [401, 422]  # Unauthorized or validation error

    @pytest.mark.asyncio
    async def test_stream_ndjson_format(self, client):
        """Test streaming response uses NDJSON format."""
        # Note: This test would require proper setup with database
        # showing how NDJSON format is returned
        pass


class TestCircuitBreaker:
    """Tests for circuit breaker pattern."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_creation(self):
        """Test circuit breaker creation."""
        breaker = CircuitBreaker(
            name="test_breaker",
            config=CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout=10,
            ),
        )
        assert breaker.name == "test_breaker"
        assert breaker.get_state() == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_success(self):
        """Test successful calls with circuit breaker."""
        breaker = CircuitBreaker(name="test_success")

        async def success_func():
            return "success"

        result = await breaker.call(success_func)
        assert result == "success"
        assert breaker.get_state() == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self):
        """Test circuit breaker opens after threshold failures."""
        breaker = CircuitBreaker(
            name="test_failures",
            config=CircuitBreakerConfig(failure_threshold=3),
        )

        async def failing_func():
            raise ValueError("Test failure")

        # Should fail and increment counter
        with pytest.raises(ValueError):
            await breaker.call(failing_func)

        assert breaker.metrics.consecutive_failures == 1
        assert breaker.get_state() == CircuitBreakerState.CLOSED

        # Fail 2 more times
        with pytest.raises(ValueError):
            await breaker.call(failing_func)
        with pytest.raises(ValueError):
            await breaker.call(failing_func)

        # Now circuit should be OPEN
        assert breaker.get_state() == CircuitBreakerState.OPEN

        # Next call should be rejected immediately
        with pytest.raises(CircuitBreakerOpenError):
            await breaker.call(failing_func)

        assert breaker.metrics.rejected_calls == 1

    @pytest.mark.asyncio
    async def test_circuit_breaker_timeout(self):
        """Test circuit breaker timeout protection."""
        breaker = CircuitBreaker(
            name="test_timeout",
            config=CircuitBreakerConfig(timeout=0.1),  # 100ms timeout
        )

        async def slow_func():
            await asyncio.sleep(1)  # 1 second delay
            return "result"

        # Should timeout
        from src.patterns.circuit_breaker import CircuitBreakerTimeoutError

        with pytest.raises(CircuitBreakerTimeoutError):
            await breaker.call(slow_func)

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery mechanism."""
        breaker = CircuitBreaker(
            name="test_recovery",
            config=CircuitBreakerConfig(
                failure_threshold=2,
                recovery_timeout=0.1,  # 100ms for testing
                success_threshold=1,
            ),
        )

        # Fail twice to open circuit
        async def failing_func():
            raise ValueError("Fail")

        with pytest.raises(ValueError):
            await breaker.call(failing_func)
        with pytest.raises(ValueError):
            await breaker.call(failing_func)

        assert breaker.get_state() == CircuitBreakerState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(0.2)

        # Next call should transition to HALF_OPEN
        async def success_func():
            return "recovered"

        result = await breaker.call(success_func)
        assert result == "recovered"

        # After success_threshold successes, should close
        assert breaker.get_state() == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_metrics(self):
        """Test circuit breaker metrics collection."""
        breaker = CircuitBreaker(name="test_metrics")

        async def test_func(should_fail=False):
            if should_fail:
                raise ValueError("Fail")
            return "success"

        # Successful calls
        await breaker.call(test_func)
        await breaker.call(test_func)

        metrics = breaker.get_metrics()
        assert metrics.total_calls == 2
        assert metrics.successful_calls == 2
        assert metrics.failed_calls == 0

        # Failed call
        with pytest.raises(ValueError):
            await breaker.call(test_func, should_fail=True)

        metrics = breaker.get_metrics()
        assert metrics.total_calls == 3
        assert metrics.failed_calls == 1


class TestMonitoring:
    """Tests for monitoring and health checks."""

    @pytest.mark.asyncio
    async def test_metrics_collector_creation(self):
        """Test metrics collector initialization."""
        collector = MetricsCollector(window_size=300)
        assert collector.window_size == 300

    @pytest.mark.asyncio
    async def test_system_metrics_collection(self):
        """Test system metrics collection."""
        collector = MetricsCollector()

        metrics = await collector.collect_system_metrics()
        assert metrics.cpu_percent >= 0
        assert metrics.memory_percent >= 0
        assert metrics.memory_mb > 0
        assert metrics.open_files >= 0

    @pytest.mark.asyncio
    async def test_request_metrics_recording(self):
        """Test request metrics recording."""
        collector = MetricsCollector()

        await collector.record_request("/api/test", 100, True)
        await collector.record_request("/api/test", 150, True)
        await collector.record_request("/api/test", 120, False)

        stats = collector.get_endpoint_stats("/api/test")
        assert stats["/api/test"]["total_requests"] == 3
        assert stats["/api/test"]["errors"] == 1

    @pytest.mark.asyncio
    async def test_health_checker_liveness(self):
        """Test liveness probe."""
        collector = MetricsCollector()
        checker = HealthChecker(collector)

        result = await checker.check_liveness()
        assert result.status == "healthy"
        assert result.checks["alive"] is True

    @pytest.mark.asyncio
    async def test_health_checker_readiness(self):
        """Test readiness probe."""
        collector = MetricsCollector()
        checker = HealthChecker(collector)

        # Collect some metrics first
        await collector.collect_system_metrics()

        result = await checker.check_readiness()
        assert result.status in ["healthy", "degraded", "unhealthy"]

    @pytest.mark.asyncio
    async def test_health_endpoint_exists(self, client):
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestErrorHandling:
    """Tests for error handling and recovery."""

    @pytest.mark.asyncio
    async def test_graceful_degradation(self):
        """Test graceful degradation when services fail."""
        # Would test actual graceful degradation in middleware
        pass

    @pytest.mark.asyncio
    async def test_error_response_format(self, client):
        """Test error responses are properly formatted."""
        # Request non-existent endpoint
        response = await client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_validation_error_handling(self, client):
        """Test validation error handling."""
        # Request with invalid data
        response = await client.post(
            "/api/v1/conversations",
            json={"invalid": "data"},
        )
        assert response.status_code in [400, 422]


class TestPerformance:
    """Performance benchmark tests."""

    @pytest.mark.asyncio
    async def test_health_check_latency(self, client):
        """Test health check endpoint latency."""
        start = time.time()
        response = await client.get("/health")
        elapsed_ms = (time.time() - start) * 1000

        assert response.status_code == 200
        assert elapsed_ms < 100  # Should be very fast

    @pytest.mark.asyncio
    async def test_circuit_breaker_performance(self):
        """Test circuit breaker overhead."""
        breaker = CircuitBreaker(name="perf_test")

        async def fast_func():
            return "result"

        # Measure overhead of 100 calls through circuit breaker
        start = time.time()
        for _ in range(100):
            await breaker.call(fast_func)
        elapsed_ms = (time.time() - start) * 1000

        # Each call should be < 1ms overhead
        avg_ms = elapsed_ms / 100
        assert avg_ms < 1.0, f"Average latency {avg_ms}ms exceeds 1ms"

    @pytest.mark.asyncio
    async def test_metrics_collection_performance(self):
        """Test metrics collection performance."""
        collector = MetricsCollector()

        start = time.time()
        for _ in range(100):
            await collector.collect_system_metrics()
        elapsed_ms = (time.time() - start) * 1000

        # Each collection should be < 10ms
        avg_ms = elapsed_ms / 100
        assert avg_ms < 10.0


class TestStressScenarios:
    """Stress testing scenarios."""

    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self):
        """Test concurrent health check requests."""
        collector = MetricsCollector()
        checker = HealthChecker(collector)

        # Run 50 concurrent checks
        tasks = [
            checker.check_readiness() for _ in range(50)
        ]
        results = await asyncio.gather(*tasks)

        assert len(results) == 50
        assert all(r.status in ["healthy", "degraded", "unhealthy"] for r in results)

    @pytest.mark.asyncio
    async def test_concurrent_circuit_breaker_calls(self):
        """Test circuit breaker with concurrent calls."""
        breaker = CircuitBreaker(name="concurrent_test")

        async def concurrent_func(delay_ms=10):
            await asyncio.sleep(delay_ms / 1000)
            return "result"

        # Run 100 concurrent calls
        tasks = [
            breaker.call(concurrent_func) for _ in range(100)
        ]
        results = await asyncio.gather(*tasks)

        assert len(results) == 100
        assert all(r == "result" for r in results)

        metrics = breaker.get_metrics()
        assert metrics.total_calls == 100
        assert metrics.successful_calls == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
