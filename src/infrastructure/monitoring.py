"""Monitoring and observability infrastructure for production deployment.

Provides comprehensive metrics, logging, and health checks for the LangChain
AI Conversation system.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from collections import defaultdict
import psutil
import os

logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: str
    checks: Dict[str, Any]
    errors: List[str]
    version: str = "1.0.0"


@dataclass
class SystemMetrics:
    """System resource metrics."""

    cpu_percent: float
    memory_percent: float
    memory_mb: float
    open_files: int
    timestamp: str


class MetricsCollector:
    """Collects and aggregates system metrics."""

    def __init__(self, window_size: int = 300):
        """
        Initialize metrics collector.

        Args:
            window_size: Time window for aggregation (seconds)
        """
        self.window_size = window_size
        self.metrics_history: List[SystemMetrics] = []
        self.request_durations: Dict[str, List[float]] = defaultdict(list)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.last_cleanup = datetime.now()

    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        process = psutil.Process(os.getpid())

        cpu_percent = process.cpu_percent(interval=0.1)
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        open_files = len(process.open_files())

        metrics = SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_mb=memory_info.rss / 1024 / 1024,
            open_files=open_files,
            timestamp=datetime.now().isoformat(),
        )

        self.metrics_history.append(metrics)

        # Cleanup old metrics
        await self._cleanup_old_metrics()

        return metrics

    async def record_request(
        self,
        endpoint: str,
        duration_ms: float,
        success: bool,
    ):
        """
        Record request metrics.

        Args:
            endpoint: API endpoint
            duration_ms: Request duration in milliseconds
            success: Whether request was successful
        """
        self.request_durations[endpoint].append(duration_ms)

        if not success:
            self.error_counts[endpoint] += 1

    async def _cleanup_old_metrics(self):
        """Remove metrics older than window size."""
        if (datetime.now() - self.last_cleanup).total_seconds() < 60:
            return  # Cleanup at most once per minute

        cutoff = datetime.now() - timedelta(seconds=self.window_size)
        cutoff_str = cutoff.isoformat()

        self.metrics_history = [
            m for m in self.metrics_history if m.timestamp > cutoff_str
        ]
        self.last_cleanup = datetime.now()

    def get_cpu_stats(self) -> Dict[str, float]:
        """Get CPU statistics for the window."""
        if not self.metrics_history:
            return {"current": 0, "avg": 0, "max": 0, "min": 0}

        values = [m.cpu_percent for m in self.metrics_history]
        return {
            "current": values[-1],
            "avg": sum(values) / len(values),
            "max": max(values),
            "min": min(values),
        }

    def get_memory_stats(self) -> Dict[str, float]:
        """Get memory statistics for the window."""
        if not self.metrics_history:
            return {
                "current_mb": 0,
                "avg_mb": 0,
                "max_mb": 0,
                "percent": 0,
            }

        values = [m.memory_mb for m in self.metrics_history]
        return {
            "current_mb": values[-1],
            "avg_mb": sum(values) / len(values),
            "max_mb": max(values),
            "percent": self.metrics_history[-1].memory_percent,
        }

    def get_endpoint_stats(
        self,
        endpoint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get request statistics for endpoints.

        Args:
            endpoint: Specific endpoint (all if None)

        Returns:
            Statistics dictionary
        """
        stats = {}

        if endpoint:
            durations = self.request_durations.get(endpoint, [])
            if durations:
                stats[endpoint] = {
                    "total_requests": len(durations),
                    "errors": self.error_counts.get(endpoint, 0),
                    "latency_ms": {
                        "p50": sorted(durations)[len(durations) // 2],
                        "p95": sorted(durations)[int(len(durations) * 0.95)],
                        "p99": sorted(durations)[int(len(durations) * 0.99)],
                        "avg": sum(durations) / len(durations),
                        "max": max(durations),
                    },
                }
        else:
            for ep, durations in self.request_durations.items():
                if durations:
                    stats[ep] = {
                        "total_requests": len(durations),
                        "errors": self.error_counts.get(ep, 0),
                        "latency_ms": {
                            "p50": sorted(durations)[len(durations) // 2],
                            "p95": sorted(durations)[int(len(durations) * 0.95)],
                            "p99": sorted(durations)[int(len(durations) * 0.99)],
                            "avg": sum(durations) / len(durations),
                            "max": max(durations),
                        },
                    }

        return stats


class HealthChecker:
    """Performs comprehensive health checks."""

    def __init__(self, metrics_collector: MetricsCollector):
        """
        Initialize health checker.

        Args:
            metrics_collector: MetricsCollector instance
        """
        self.metrics_collector = metrics_collector

    async def check_system_health(self) -> HealthCheckResult:
        """
        Perform comprehensive system health check.

        Returns:
            HealthCheckResult
        """
        checks = {}
        errors = []
        overall_status = "healthy"

        # CPU health
        cpu_stats = self.metrics_collector.get_cpu_stats()
        checks["cpu"] = {
            "status": "healthy" if cpu_stats["current"] < 80 else "degraded",
            "percent": cpu_stats["current"],
        }
        if cpu_stats["current"] >= 90:
            errors.append("CPU usage critical (>90%)")
            overall_status = "unhealthy"
        elif cpu_stats["current"] >= 80:
            overall_status = "degraded"

        # Memory health
        memory_stats = self.metrics_collector.get_memory_stats()
        checks["memory"] = {
            "status": "healthy" if memory_stats["percent"] < 80 else "degraded",
            "percent": memory_stats["percent"],
            "mb": memory_stats["current_mb"],
        }
        if memory_stats["percent"] >= 90:
            errors.append("Memory usage critical (>90%)")
            overall_status = "unhealthy"
        elif memory_stats["percent"] >= 80:
            overall_status = "degraded"

        # Database connectivity (can be enhanced with actual DB check)
        checks["database"] = {"status": "healthy"}

        # API endpoints
        endpoint_stats = self.metrics_collector.get_endpoint_stats()
        checks["endpoints"] = {
            "total_requests": sum(
                stats["total_requests"] for stats in endpoint_stats.values()
            ),
            "total_errors": sum(
                stats["errors"] for stats in endpoint_stats.values()
            ),
        }

        return HealthCheckResult(
            status=overall_status,
            timestamp=datetime.now().isoformat(),
            checks=checks,
            errors=errors,
        )

    async def check_liveness(self) -> HealthCheckResult:
        """Check if application is alive."""
        return HealthCheckResult(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            checks={"alive": True},
            errors=[],
        )

    async def check_readiness(self) -> HealthCheckResult:
        """Check if application is ready to serve traffic."""
        system_health = await self.check_system_health()

        # Ready if not critically unhealthy
        ready = system_health.status != "unhealthy"

        return HealthCheckResult(
            status="healthy" if ready else "unhealthy",
            timestamp=datetime.now().isoformat(),
            checks={
                "ready": ready,
                "system": system_health.checks,
            },
            errors=system_health.errors,
        )


class MonitoringManager:
    """Central monitoring manager."""

    def __init__(self):
        """Initialize monitoring manager."""
        self.metrics_collector = MetricsCollector()
        self.health_checker = HealthChecker(self.metrics_collector)
        self._monitoring_task: Optional[asyncio.Task] = None

    async def start_monitoring(self, interval_seconds: int = 10):
        """
        Start background monitoring task.

        Args:
            interval_seconds: Collection interval
        """
        if self._monitoring_task:
            return

        logger.info(f"Starting monitoring with {interval_seconds}s interval")

        async def monitor_loop():
            while True:
                try:
                    metrics = await self.metrics_collector.collect_system_metrics()
                    logger.debug(
                        f"Metrics - CPU: {metrics.cpu_percent}%, "
                        f"Memory: {metrics.memory_mb:.1f}MB, "
                        f"Files: {metrics.open_files}"
                    )
                    await asyncio.sleep(interval_seconds)
                except Exception as e:
                    logger.error(f"Monitoring error: {e}")
                    await asyncio.sleep(interval_seconds)

        self._monitoring_task = asyncio.create_task(monitor_loop())

    async def stop_monitoring(self):
        """Stop background monitoring task."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            logger.info("Monitoring stopped")

    async def get_full_status(self) -> Dict[str, Any]:
        """Get complete system status."""
        system_health = await self.health_checker.check_system_health()
        metrics = self.metrics_collector.get_cpu_stats()

        return {
            "health": asdict(system_health),
            "metrics": {
                "cpu": metrics,
                "memory": self.metrics_collector.get_memory_stats(),
                "endpoints": self.metrics_collector.get_endpoint_stats(),
            },
        }


# Global monitoring manager
_monitoring_manager: Optional[MonitoringManager] = None


def get_monitoring_manager() -> MonitoringManager:
    """Get global monitoring manager."""
    global _monitoring_manager
    if _monitoring_manager is None:
        _monitoring_manager = MonitoringManager()
    return _monitoring_manager
