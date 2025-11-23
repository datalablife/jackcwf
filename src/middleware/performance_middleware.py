#!/usr/bin/env python3
"""
Performance Monitoring Middleware.

Tracks request latency, database query times, and cache performance.
Exposes metrics for Prometheus.
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, Gauge

logger = logging.getLogger(__name__)

# Prometheus metrics
request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint', 'status']
)

request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

active_requests = Gauge(
    'http_requests_active',
    'Number of active HTTP requests'
)

cache_hits = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query latency',
    ['query_type']
)


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track performance metrics.

    Measures:
    - Request duration
    - Active requests
    - Response status codes
    - Slow requests (>1s)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect metrics."""
        start_time = time.time()
        active_requests.inc()

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Record metrics
            endpoint = request.url.path
            method = request.method
            status = response.status_code

            request_duration.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).observe(duration)

            request_count.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).inc()

            # Log slow requests
            if duration > 1.0:
                logger.warning(
                    f"SLOW REQUEST: {method} {endpoint} "
                    f"took {duration*1000:.2f}ms (status={status})"
                )
            else:
                logger.debug(
                    f"{method} {endpoint}: {duration*1000:.2f}ms (status={status})"
                )

            # Add performance headers
            response.headers["X-Response-Time"] = f"{duration*1000:.2f}ms"

            return response

        finally:
            active_requests.dec()
