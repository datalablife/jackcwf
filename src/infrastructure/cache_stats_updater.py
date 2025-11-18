"""Background task to periodically update cache statistics in Prometheus."""

import asyncio
import logging
from typing import Optional
from datetime import datetime

from src.services.semantic_cache import get_cache_service
from src.infrastructure.cache_metrics import update_cache_stats

logger = logging.getLogger(__name__)


class CacheStatsUpdater:
    """Periodic updater for cache statistics."""

    def __init__(self, interval_seconds: int = 30):
        """
        Initialize cache stats updater.

        Args:
            interval_seconds: Interval between updates in seconds (default: 30s)
        """
        self.interval_seconds = interval_seconds
        self.is_running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the periodic update task."""
        if self.is_running:
            logger.warning("Cache stats updater is already running")
            return

        self.is_running = True
        self._task = asyncio.create_task(self._update_loop())
        logger.info(f"Cache stats updater started (interval: {self.interval_seconds}s)")

    async def stop(self):
        """Stop the periodic update task."""
        if not self.is_running:
            return

        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Cache stats updater stopped")

    async def _update_loop(self):
        """Main update loop."""
        while self.is_running:
            try:
                await self._update_stats()
                await asyncio.sleep(self.interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache stats update loop: {e}", exc_info=True)
                await asyncio.sleep(self.interval_seconds)

    async def _update_stats(self):
        """Update cache statistics from the database."""
        try:
            cache_service = get_cache_service()
            if not cache_service:
                logger.debug("Cache service not available, skipping stats update")
                return

            # Get cache statistics
            stats = await cache_service.get_cache_stats()

            # Extract statistics
            total_entries = stats.get("total_entries", 0)
            total_hits = stats.get("total_hits", 0)
            hit_percentage = stats.get("hit_percentage", 0) / 100  # Convert to ratio

            # Extract table size (convert from human-readable format if needed)
            table_size_str = stats.get("table_size", "0 MB")
            table_size_bytes = self._parse_size(table_size_str)

            # Update gauge metrics
            model_name = "claude-3-5-sonnet-20241022"  # Default model
            update_cache_stats(
                model_name=model_name,
                total_entries=total_entries,
                hit_rate=hit_percentage,
                table_size_bytes=table_size_bytes,
            )

            logger.debug(
                f"Cache stats updated: "
                f"entries={total_entries}, "
                f"hits={total_hits}, "
                f"hit_rate={hit_percentage*100:.1f}%, "
                f"size={table_size_str}"
            )

        except Exception as e:
            logger.error(f"Error updating cache statistics: {e}")

    @staticmethod
    def _parse_size(size_str: str) -> int:
        """
        Parse human-readable size string to bytes.

        Args:
            size_str: Size string like "256 MB" or "1.5 GB"

        Returns:
            Size in bytes
        """
        try:
            parts = size_str.strip().split()
            if len(parts) != 2:
                return 0

            value = float(parts[0])
            unit = parts[1].upper()

            multipliers = {
                "B": 1,
                "KB": 1024,
                "MB": 1024 ** 2,
                "GB": 1024 ** 3,
                "TB": 1024 ** 4,
            }

            return int(value * multipliers.get(unit, 1))
        except (ValueError, IndexError):
            logger.warning(f"Could not parse size string: {size_str}")
            return 0


# Global instance
_updater: Optional[CacheStatsUpdater] = None


def get_cache_stats_updater(interval_seconds: int = 30) -> CacheStatsUpdater:
    """Get or create the global cache stats updater."""
    global _updater
    if _updater is None:
        _updater = CacheStatsUpdater(interval_seconds=interval_seconds)
    return _updater


async def start_cache_stats_updater(interval_seconds: int = 30):
    """Start the cache stats updater."""
    updater = get_cache_stats_updater(interval_seconds)
    await updater.start()


async def stop_cache_stats_updater():
    """Stop the cache stats updater."""
    global _updater
    if _updater:
        await _updater.stop()
        _updater = None
