"""Graceful shutdown and resource cleanup utilities."""

import asyncio
import logging
import signal
from typing import Optional, Set

logger = logging.getLogger(__name__)


class GracefulShutdownManager:
    """Manages graceful shutdown of the application."""

    def __init__(self, timeout_seconds: int = 30):
        """
        Initialize graceful shutdown manager.

        Args:
            timeout_seconds: Maximum time to wait for active requests before forced shutdown
        """
        self.timeout_seconds = timeout_seconds
        self.is_shutting_down = False
        self.active_requests: Set[asyncio.Task] = set()
        self._signal_handlers = []

    async def setup_signal_handlers(self):
        """Setup OS signal handlers for graceful shutdown."""
        loop = asyncio.get_running_loop()

        def signal_handler(sig):
            logger.info(f"Received signal {sig}, initiating graceful shutdown...")
            asyncio.create_task(self.shutdown())

        # Register handlers for SIGTERM and SIGINT
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                signal_handler,
                sig,
            )
            self._signal_handlers.append((sig, signal_handler))

    async def shutdown(self):
        """
        Initiate graceful shutdown.

        1. Mark shutdown as in progress
        2. Stop accepting new requests
        3. Wait for active requests to complete (with timeout)
        4. Clean up resources
        5. Exit
        """
        logger.info("Starting graceful shutdown...")
        self.is_shutting_down = True

        # Wait for active requests to complete
        if self.active_requests:
            logger.info(f"Waiting for {len(self.active_requests)} active requests to complete...")
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self.active_requests, return_exceptions=True),
                    timeout=self.timeout_seconds,
                )
            except asyncio.TimeoutError:
                logger.warning(
                    f"Timeout waiting for active requests. "
                    f"Cancelling {len(self.active_requests)} tasks."
                )
                for task in self.active_requests:
                    task.cancel()

                # Give tasks time to cleanup after cancellation
                await asyncio.sleep(1)

        logger.info("Graceful shutdown completed")

    async def cleanup_resources(self):
        """Cleanup resources (database, redis, etc.)."""
        logger.info("Cleaning up resources...")

        try:
            # Close database connection
            from src.db.config import engine
            await engine.dispose()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")

        try:
            # Close Redis connection if configured
            redis_url = __import__("os").getenv("REDIS_URL")
            if redis_url:
                try:
                    import redis.asyncio as redis
                    client = redis.from_url(redis_url)
                    await client.close()
                    logger.info("Redis connection closed")
                except Exception as e:
                    logger.error(f"Error closing Redis connection: {e}")
        except Exception as e:
            logger.error(f"Error with Redis cleanup: {e}")

        logger.info("Resource cleanup completed")

    def register_request(self, task: asyncio.Task):
        """Register an active request task."""
        if not self.is_shutting_down:
            self.active_requests.add(task)
            task.add_done_callback(self.unregister_request)

    def unregister_request(self, task: asyncio.Task):
        """Unregister a completed request task."""
        self.active_requests.discard(task)


# Global shutdown manager instance
_shutdown_manager: Optional[GracefulShutdownManager] = None


def get_shutdown_manager() -> GracefulShutdownManager:
    """Get or create global shutdown manager."""
    global _shutdown_manager
    if _shutdown_manager is None:
        _shutdown_manager = GracefulShutdownManager()
    return _shutdown_manager


def is_shutting_down() -> bool:
    """Check if system is shutting down."""
    return get_shutdown_manager().is_shutting_down
