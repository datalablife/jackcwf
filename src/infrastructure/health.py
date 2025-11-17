"""Health check and service monitoring endpoints."""

import asyncio
import logging
import os
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional

from fastapi import APIRouter, status
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status enum."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    SHUTTING_DOWN = "shutting_down"
    UNHEALTHY = "unhealthy"


class HealthChecker:
    """Service health checker."""

    def __init__(self):
        """Initialize health checker."""
        self.health_timeout_ms = float(os.getenv("HEALTH_CHECK_TIMEOUT_MS", "2000"))
        self.is_shutting_down = False

    async def check_database(self) -> Dict[str, Any]:
        """
        Check database connection.

        Returns:
            Health check result
        """
        try:
            # Import database connection
            from src.db.config import engine

            # Test connection
            async with engine.begin() as conn:
                await conn.execute("SELECT 1")

            return {
                "status": "healthy",
                "service": "database",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "service": "database",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def check_vector_store(self) -> Dict[str, Any]:
        """
        Check vector store (pgvector) availability.

        Returns:
            Health check result
        """
        try:
            # Import database connection
            from src.db.config import engine

            # Check pgvector extension
            async with engine.begin() as conn:
                result = await conn.execute(
                    "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
                )
                has_vector = result.scalar()

            status_text = "healthy" if has_vector else "degraded"
            return {
                "status": status_text,
                "service": "vector_store",
                "has_pgvector": has_vector,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Vector store health check failed: {e}")
            return {
                "status": "unhealthy",
                "service": "vector_store",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def check_redis(self) -> Dict[str, Any]:
        """
        Check Redis connection (if configured).

        Returns:
            Health check result
        """
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            return {
                "status": "skipped",
                "service": "redis",
                "reason": "Redis not configured",
                "timestamp": datetime.utcnow().isoformat(),
            }

        try:
            # Import redis (optional dependency)
            try:
                import redis.asyncio as redis
            except ImportError:
                return {
                    "status": "skipped",
                    "service": "redis",
                    "reason": "redis-py not installed",
                    "timestamp": datetime.utcnow().isoformat(),
                }

            # Test connection
            client = redis.from_url(redis_url)
            await client.ping()
            await client.close()

            return {
                "status": "healthy",
                "service": "redis",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "service": "redis",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def check_llm_api(self) -> Dict[str, Any]:
        """
        Check LLM API availability (quick test).

        Returns:
            Health check result
        """
        try:
            from langchain_anthropic import ChatAnthropic

            llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")
            # Quick test - just invoke with minimal input
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    lambda: llm.invoke("Health check: respond with OK")
                ),
                timeout=5.0,
            )

            return {
                "status": "healthy",
                "service": "llm_api",
                "model": "claude-3-5-sonnet-20241022",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except asyncio.TimeoutError:
            logger.warning("LLM API health check timed out")
            return {
                "status": "degraded",
                "service": "llm_api",
                "error": "Request timeout",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"LLM API health check failed: {e}")
            return {
                "status": "unhealthy",
                "service": "llm_api",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def run_full_check(self) -> Dict[str, Any]:
        """
        Run full health check with all services.

        Returns:
            Complete health check result
        """
        try:
            # Run checks in parallel with timeout protection
            checks = await asyncio.wait_for(
                asyncio.gather(
                    self.check_database(),
                    self.check_vector_store(),
                    self.check_redis(),
                    # Skip LLM API check in full check for speed
                    # self.check_llm_api(),
                    return_exceptions=True,
                ),
                timeout=self.health_timeout_ms / 1000.0,
            )

            # Process results
            check_results = []
            overall_status = HealthStatus.HEALTHY

            for check in checks:
                if isinstance(check, Exception):
                    check_results.append({
                        "status": "error",
                        "error": str(check),
                    })
                    overall_status = HealthStatus.UNHEALTHY
                else:
                    check_results.append(check)
                    # Update overall status
                    if check.get("status") == "unhealthy":
                        overall_status = HealthStatus.UNHEALTHY
                    elif check.get("status") == "degraded" and overall_status == HealthStatus.HEALTHY:
                        overall_status = HealthStatus.DEGRADED

            # Override if shutting down
            if self.is_shutting_down:
                overall_status = HealthStatus.SHUTTING_DOWN

            return {
                "status": overall_status,
                "timestamp": datetime.utcnow().isoformat(),
                "checks": check_results,
            }

        except asyncio.TimeoutError:
            logger.warning("Full health check timed out")
            return {
                "status": HealthStatus.DEGRADED,
                "timestamp": datetime.utcnow().isoformat(),
                "error": "Health check timeout",
            }


def create_health_routes() -> APIRouter:
    """
    Create health check routes.

    Returns:
        FastAPI router with health endpoints
    """
    router = APIRouter()
    health_checker = HealthChecker()

    @router.get("/health", tags=["Health"])
    async def health_quick_check():
        """Quick health check (fast, <100ms)."""
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": HealthStatus.HEALTHY,
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Service is running",
            },
        )

    @router.get("/health/full", tags=["Health"])
    async def health_full_check():
        """Full health check with all services (<2000ms)."""
        result = await health_checker.run_full_check()

        # Determine HTTP status
        http_status = status.HTTP_200_OK
        if result.get("status") == HealthStatus.UNHEALTHY:
            http_status = status.HTTP_503_SERVICE_UNAVAILABLE
        elif result.get("status") == HealthStatus.DEGRADED:
            http_status = status.HTTP_200_OK  # Still return 200 but indicate degraded

        return JSONResponse(
            status_code=http_status,
            content=result,
        )

    return router
