"""Circuit breaker pattern implementation for fault tolerance.

Provides robust circuit breaker implementation for protecting against cascading
failures in external service calls (LLM API, vector search, database queries).
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Optional, Callable, Any, TypeVar, Coroutine
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitBreakerState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking calls
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5
    """Number of failures before opening circuit"""

    recovery_timeout: float = 60
    """Seconds to wait before attempting recovery (half-open)"""

    success_threshold: int = 2
    """Number of successes in half-open state before closing"""

    timeout: float = 30
    """Timeout for individual function calls (seconds)"""

    exponential_backoff: bool = True
    """Use exponential backoff for recovery timeout"""

    max_timeout: float = 300
    """Maximum timeout value when using exponential backoff"""


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker monitoring."""

    total_calls: int = 0
    """Total number of calls made"""

    successful_calls: int = 0
    """Total successful calls"""

    failed_calls: int = 0
    """Total failed calls"""

    rejected_calls: int = 0
    """Total calls rejected while open"""

    consecutive_failures: int = 0
    """Current consecutive failures"""

    consecutive_successes: int = 0
    """Current consecutive successes in half-open state"""

    last_failure_time: Optional[datetime] = None
    """Timestamp of last failure"""

    last_success_time: Optional[datetime] = None
    """Timestamp of last success"""

    state_changes: list[tuple[datetime, CircuitBreakerState]] = field(default_factory=list)
    """History of state changes"""


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""

    def __init__(self, message: str = "Circuit breaker is open"):
        super().__init__(message)
        self.message = message


class CircuitBreakerTimeoutError(Exception):
    """Raised when circuit breaker call times out."""

    def __init__(self, message: str = "Circuit breaker call timed out"):
        super().__init__(message)
        self.message = message


class CircuitBreaker:
    """
    Circuit breaker for protecting against cascading failures.

    The circuit breaker has three states:
    - CLOSED: Normal operation, all calls pass through
    - OPEN: After too many failures, all calls are blocked immediately
    - HALF_OPEN: Testing if service recovered, limited calls allowed
    """

    def __init__(
        self,
        name: str = "default",
        config: Optional[CircuitBreakerConfig] = None,
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Name for identification in logs
            config: CircuitBreakerConfig (uses defaults if not provided)
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitBreakerState.CLOSED
        self.metrics = CircuitBreakerMetrics()
        self._state_lock = asyncio.Lock()
        self._last_recovery_attempt: Optional[datetime] = None
        self._current_recovery_timeout = self.config.recovery_timeout

        logger.info(
            f"CircuitBreaker '{name}' initialized: "
            f"failure_threshold={self.config.failure_threshold}, "
            f"recovery_timeout={self.config.recovery_timeout}s"
        )

    async def call(
        self,
        func: Callable[..., Coroutine[Any, Any, T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Async function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: If circuit is open
            CircuitBreakerTimeoutError: If call times out
        """
        self.metrics.total_calls += 1

        # Check if circuit is open
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_recovery():
                await self._transition_to_half_open()
            else:
                self.metrics.rejected_calls += 1
                logger.warning(
                    f"CircuitBreaker '{self.name}' OPEN: Rejecting call "
                    f"(rejected: {self.metrics.rejected_calls})"
                )
                raise CircuitBreakerOpenError(
                    f"CircuitBreaker '{self.name}' is open. "
                    f"Retry after {self._seconds_until_recovery():.1f}s"
                )

        # Execute function with timeout
        try:
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout,
            )
            await self._on_success()
            return result

        except asyncio.TimeoutError:
            await self._on_failure()
            logger.error(
                f"CircuitBreaker '{self.name}': Call timed out after "
                f"{self.config.timeout}s"
            )
            raise CircuitBreakerTimeoutError(
                f"Call timed out after {self.config.timeout}s"
            )
        except Exception as e:
            await self._on_failure()
            logger.error(
                f"CircuitBreaker '{self.name}': Call failed - {type(e).__name__}: {str(e)}"
            )
            raise

    async def call_sync(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """
        Execute synchronous function with circuit breaker protection.

        Args:
            func: Sync function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result
        """

        async def async_wrapper():
            return func(*args, **kwargs)

        return await self.call(async_wrapper)

    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self._last_recovery_attempt is None:
            return True

        elapsed = (datetime.now() - self._last_recovery_attempt).total_seconds()
        return elapsed >= self._current_recovery_timeout

    def _seconds_until_recovery(self) -> float:
        """Get seconds until next recovery attempt."""
        if self._last_recovery_attempt is None:
            return 0

        elapsed = (datetime.now() - self._last_recovery_attempt).total_seconds()
        remaining = max(0, self._current_recovery_timeout - elapsed)
        return remaining

    async def _transition_to_half_open(self):
        """Transition from OPEN to HALF_OPEN state."""
        async with self._state_lock:
            self.state = CircuitBreakerState.HALF_OPEN
            self.metrics.consecutive_successes = 0
            self._last_recovery_attempt = datetime.now()

            logger.info(
                f"CircuitBreaker '{self.name}' transitioning to HALF_OPEN: "
                f"attempting recovery"
            )

    async def _on_success(self):
        """Handle successful call."""
        async with self._state_lock:
            self.metrics.successful_calls += 1
            self.metrics.consecutive_failures = 0
            self.metrics.last_success_time = datetime.now()

            if self.state == CircuitBreakerState.HALF_OPEN:
                self.metrics.consecutive_successes += 1

                if self.metrics.consecutive_successes >= self.config.success_threshold:
                    # Reset to CLOSED state
                    self.state = CircuitBreakerState.CLOSED
                    self._current_recovery_timeout = self.config.recovery_timeout
                    self.metrics.state_changes.append(
                        (datetime.now(), CircuitBreakerState.CLOSED)
                    )

                    logger.info(
                        f"CircuitBreaker '{self.name}' recovered: "
                        f"HALF_OPEN -> CLOSED ({self.metrics.consecutive_successes} successes)"
                    )

    async def _on_failure(self):
        """Handle failed call."""
        async with self._state_lock:
            self.metrics.failed_calls += 1
            self.metrics.consecutive_failures += 1
            self.metrics.consecutive_successes = 0
            self.metrics.last_failure_time = datetime.now()

            if self.state == CircuitBreakerState.HALF_OPEN:
                # Back to OPEN if any failure in half-open
                self.state = CircuitBreakerState.OPEN
                self._increase_recovery_timeout()
                self.metrics.state_changes.append(
                    (datetime.now(), CircuitBreakerState.OPEN)
                )

                logger.warning(
                    f"CircuitBreaker '{self.name}' opened again: "
                    f"failure in HALF_OPEN state, "
                    f"new recovery timeout: {self._current_recovery_timeout}s"
                )

            elif (
                self.state == CircuitBreakerState.CLOSED
                and self.metrics.consecutive_failures >= self.config.failure_threshold
            ):
                # Open if too many consecutive failures
                self.state = CircuitBreakerState.OPEN
                self.metrics.state_changes.append(
                    (datetime.now(), CircuitBreakerState.OPEN)
                )

                logger.error(
                    f"CircuitBreaker '{self.name}' opened: "
                    f"{self.metrics.consecutive_failures} consecutive failures"
                )

    def _increase_recovery_timeout(self):
        """Increase recovery timeout with exponential backoff."""
        if self.config.exponential_backoff:
            # Double the timeout, up to max
            self._current_recovery_timeout = min(
                self._current_recovery_timeout * 2,
                self.config.max_timeout,
            )
        # Otherwise keep the same timeout

    def get_state(self) -> CircuitBreakerState:
        """Get current circuit breaker state."""
        return self.state

    def get_metrics(self) -> CircuitBreakerMetrics:
        """Get circuit breaker metrics."""
        return self.metrics

    def reset(self):
        """Reset circuit breaker to CLOSED state."""
        self.state = CircuitBreakerState.CLOSED
        self.metrics = CircuitBreakerMetrics()
        self._last_recovery_attempt = None
        self._current_recovery_timeout = self.config.recovery_timeout
        logger.info(f"CircuitBreaker '{self.name}' reset to CLOSED state")

    def __repr__(self) -> str:
        """String representation of circuit breaker."""
        return (
            f"CircuitBreaker(name='{self.name}', state={self.state.value}, "
            f"calls={self.metrics.total_calls}, "
            f"failures={self.metrics.failed_calls})"
        )


class CircuitBreakerManager:
    """Manages multiple circuit breakers."""

    def __init__(self):
        """Initialize circuit breaker manager."""
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()

    async def get_breaker(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ) -> CircuitBreaker:
        """
        Get or create a circuit breaker.

        Args:
            name: Name of circuit breaker
            config: Configuration (only used if creating new breaker)

        Returns:
            CircuitBreaker instance
        """
        async with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(name, config)
            return self._breakers[name]

    def get_breaker_sync(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ) -> CircuitBreaker:
        """
        Get or create a circuit breaker (synchronously).

        Args:
            name: Name of circuit breaker
            config: Configuration (only used if creating new breaker)

        Returns:
            CircuitBreaker instance
        """
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name, config)
        return self._breakers[name]

    def get_metrics(self) -> dict[str, CircuitBreakerMetrics]:
        """Get metrics for all circuit breakers."""
        return {name: breaker.get_metrics() for name, breaker in self._breakers.items()}

    def reset_all(self):
        """Reset all circuit breakers."""
        for breaker in self._breakers.values():
            breaker.reset()
        logger.info("All circuit breakers reset")


# Global circuit breaker manager
_breaker_manager: Optional[CircuitBreakerManager] = None


def get_breaker_manager() -> CircuitBreakerManager:
    """Get global circuit breaker manager."""
    global _breaker_manager
    if _breaker_manager is None:
        _breaker_manager = CircuitBreakerManager()
    return _breaker_manager


async def get_circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None,
) -> CircuitBreaker:
    """Get circuit breaker from global manager."""
    manager = get_breaker_manager()
    return await manager.get_breaker(name, config)
