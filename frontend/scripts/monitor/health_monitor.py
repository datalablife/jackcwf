#!/usr/bin/env python3
"""
Production Health Monitor for Frontend/Backend Services

Features:
- HTTP health checks with configurable intervals
- Resource usage monitoring (CPU, Memory)
- Automatic restart via Supervisor
- Alert notifications (webhook, email)
- Graceful degradation handling
"""

import asyncio
import logging
import os
import signal
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

import httpx

# Optional: psutil for resource monitoring
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('health_monitor')


class ServiceStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class ServiceConfig:
    name: str
    health_url: str
    check_interval: int = 30  # seconds
    timeout: int = 10  # seconds
    unhealthy_threshold: int = 3  # consecutive failures before unhealthy
    recovery_threshold: int = 2  # consecutive successes before healthy


@dataclass
class ServiceState:
    status: ServiceStatus = ServiceStatus.UNKNOWN
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_check: Optional[datetime] = None
    last_healthy: Optional[datetime] = None
    last_error: Optional[str] = None
    response_time_ms: float = 0.0


@dataclass
class MonitorConfig:
    backend_url: str = field(default_factory=lambda: os.getenv('BACKEND_HEALTH_URL', 'http://localhost:8000/health'))
    frontend_url: str = field(default_factory=lambda: os.getenv('FRONTEND_HEALTH_URL', 'http://localhost:3000'))
    check_interval: int = field(default_factory=lambda: int(os.getenv('HEALTH_CHECK_INTERVAL', '30')))
    alert_webhook: Optional[str] = field(default_factory=lambda: os.getenv('ALERT_WEBHOOK_URL'))
    supervisor_sock: str = field(default_factory=lambda: os.getenv('SUPERVISOR_SOCK', '/var/run/supervisor.sock'))


class HealthMonitor:
    def __init__(self, config: MonitorConfig):
        self.config = config
        self.running = True
        self.services: dict[str, tuple[ServiceConfig, ServiceState]] = {}
        self._setup_services()
        self._setup_signal_handlers()

    def _setup_services(self):
        """Initialize service configurations."""
        self.services['backend'] = (
            ServiceConfig(
                name='backend',
                health_url=self.config.backend_url,
                check_interval=self.config.check_interval,
            ),
            ServiceState()
        )
        self.services['frontend'] = (
            ServiceConfig(
                name='frontend',
                health_url=self.config.frontend_url,
                check_interval=self.config.check_interval,
                timeout=5,  # Frontend can be slower
            ),
            ServiceState()
        )

    def _setup_signal_handlers(self):
        """Setup graceful shutdown handlers."""
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    async def check_service_health(self, service_name: str) -> ServiceStatus:
        """Check health of a single service."""
        config, state = self.services[service_name]

        try:
            async with httpx.AsyncClient(timeout=config.timeout) as client:
                start_time = time.monotonic()
                response = await client.get(config.health_url)
                elapsed_ms = (time.monotonic() - start_time) * 1000

                state.response_time_ms = elapsed_ms
                state.last_check = datetime.now()

                if response.status_code == 200:
                    state.consecutive_successes += 1
                    state.consecutive_failures = 0
                    state.last_healthy = datetime.now()
                    state.last_error = None

                    if state.consecutive_successes >= config.recovery_threshold:
                        state.status = ServiceStatus.HEALTHY

                    logger.info(
                        f"[{service_name}] Health check OK "
                        f"(status={response.status_code}, time={elapsed_ms:.1f}ms)"
                    )
                    return state.status
                else:
                    raise Exception(f"Unhealthy status code: {response.status_code}")

        except Exception as e:
            state.consecutive_failures += 1
            state.consecutive_successes = 0
            state.last_error = str(e)
            state.last_check = datetime.now()

            if state.consecutive_failures >= config.unhealthy_threshold:
                state.status = ServiceStatus.UNHEALTHY
                await self._handle_unhealthy_service(service_name)
            else:
                state.status = ServiceStatus.DEGRADED

            logger.warning(
                f"[{service_name}] Health check FAILED "
                f"(failures={state.consecutive_failures}, error={e})"
            )
            return state.status

    async def _handle_unhealthy_service(self, service_name: str):
        """Handle unhealthy service - trigger restart and alerts."""
        config, state = self.services[service_name]

        logger.error(f"[{service_name}] Service is UNHEALTHY, triggering recovery...")

        # Send alert
        await self._send_alert(
            title=f"Service Unhealthy: {service_name}",
            message=f"Service {service_name} has failed {state.consecutive_failures} consecutive health checks. "
                    f"Last error: {state.last_error}",
            severity="critical"
        )

        # Restart via supervisor
        await self._restart_service(service_name)

    async def _restart_service(self, service_name: str):
        """Restart service using supervisorctl."""
        try:
            proc = await asyncio.create_subprocess_exec(
                'supervisorctl', 'restart', service_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                logger.info(f"[{service_name}] Service restart triggered successfully")
                # Reset state after restart
                _, state = self.services[service_name]
                state.consecutive_failures = 0
                state.status = ServiceStatus.UNKNOWN
            else:
                logger.error(f"[{service_name}] Failed to restart: {stderr.decode()}")
        except Exception as e:
            logger.error(f"[{service_name}] Error restarting service: {e}")

    async def _send_alert(self, title: str, message: str, severity: str = "warning"):
        """Send alert notification via webhook."""
        if not self.config.alert_webhook:
            logger.info(f"Alert (no webhook): [{severity}] {title} - {message}")
            return

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(
                    self.config.alert_webhook,
                    json={
                        "title": title,
                        "message": message,
                        "severity": severity,
                        "timestamp": datetime.now().isoformat(),
                        "source": "health_monitor"
                    }
                )
                logger.info(f"Alert sent: [{severity}] {title}")
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")

    def _collect_resource_metrics(self) -> dict:
        """Collect system resource metrics."""
        if not HAS_PSUTIL:
            return {}

        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
            }
        except Exception as e:
            logger.warning(f"Failed to collect metrics: {e}")
            return {}

    async def run(self):
        """Main monitoring loop."""
        logger.info("Health Monitor started")
        logger.info(f"Backend URL: {self.config.backend_url}")
        logger.info(f"Frontend URL: {self.config.frontend_url}")
        logger.info(f"Check interval: {self.config.check_interval}s")

        # Initial delay to allow services to start
        await asyncio.sleep(10)

        while self.running:
            try:
                # Run health checks concurrently
                tasks = [
                    self.check_service_health(name)
                    for name in self.services.keys()
                ]
                await asyncio.gather(*tasks, return_exceptions=True)

                # Log resource metrics periodically
                metrics = self._collect_resource_metrics()
                if metrics:
                    logger.info(
                        f"System metrics: CPU={metrics.get('cpu_percent', 'N/A')}%, "
                        f"Memory={metrics.get('memory_percent', 'N/A')}%, "
                        f"Disk={metrics.get('disk_percent', 'N/A')}%"
                    )

                # Wait for next check
                await asyncio.sleep(self.config.check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                await asyncio.sleep(5)

        logger.info("Health Monitor stopped")


async def main():
    config = MonitorConfig()
    monitor = HealthMonitor(config)
    await monitor.run()


if __name__ == '__main__':
    asyncio.run(main())
