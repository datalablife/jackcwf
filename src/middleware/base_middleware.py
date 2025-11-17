"""Base middleware class with common error handling and utilities."""

import asyncio
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse

logger = logging.getLogger(__name__)


class FallbackStrategy(str, Enum):
    """Fallback strategy when middleware operation fails."""

    RETURN_PARTIAL = "return_partial"  # Return partial data if available
    RETRY_ONCE = "retry_once"  # Retry operation once
    SKIP_CONTEXT = "skip_context"  # Skip enrichment, continue with minimal context
    RETURN_ERROR = "return_error"  # Return 400/500 error


class BaseMiddleware(BaseHTTPMiddleware, ABC):
    """
    Base middleware class with common error handling patterns.

    Provides:
    - Timeout protection with asyncio.wait_for
    - Fallback strategies for failures
    - Retry logic with exponential backoff
    - Structured error responses
    - Performance tracking
    """

    def __init__(
        self,
        app,
        timeout_ms: float = 5000,
        fallback_strategy: FallbackStrategy = FallbackStrategy.RETURN_ERROR,
        max_retries: int = 1,
        backoff_factor: float = 2.0,
    ):
        """
        Initialize base middleware.

        Args:
            app: FastAPI application
            timeout_ms: Operation timeout in milliseconds
            fallback_strategy: Strategy when operation fails
            max_retries: Maximum retry attempts
            backoff_factor: Exponential backoff multiplier
        """
        super().__init__(app)
        self.timeout_ms = timeout_ms
        self.fallback_strategy = fallback_strategy
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.logger = logging.getLogger(self.__class__.__name__)

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Dispatch request with error handling.

        Subclasses should override this method.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response
        """
        return await call_next(request)

    async def execute_with_timeout(
        self,
        coro,
        operation_name: str = "operation",
        fallback_value: Any = None,
    ) -> Any:
        """
        Execute async operation with timeout protection.

        Args:
            coro: Coroutine to execute
            operation_name: Name of operation for logging
            fallback_value: Value to return on timeout

        Returns:
            Operation result or fallback value
        """
        try:
            result = await asyncio.wait_for(
                coro,
                timeout=self.timeout_ms / 1000.0
            )
            return result
        except asyncio.TimeoutError:
            self.logger.warning(
                f"Operation timeout: {operation_name} "
                f"(timeout: {self.timeout_ms}ms)"
            )
            return fallback_value
        except Exception as exc:
            self.logger.error(f"Operation error: {operation_name} - {exc}")
            return fallback_value

    async def execute_with_retry(
        self,
        coro_func,
        operation_name: str = "operation",
        fallback_value: Any = None,
    ) -> Any:
        """
        Execute async operation with exponential backoff retry.

        Args:
            coro_func: Async function to execute (not coroutine, function that returns coroutine)
            operation_name: Name of operation for logging
            fallback_value: Value to return after all retries exhausted

        Returns:
            Operation result or fallback value
        """
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                result = await self.execute_with_timeout(
                    coro_func(),
                    operation_name=f"{operation_name} (attempt {attempt + 1})",
                    fallback_value=None,
                )

                if result is not None:
                    return result

            except Exception as exc:
                last_error = exc
                if attempt < self.max_retries:
                    # Exponential backoff
                    delay = (self.backoff_factor ** attempt) / 1000  # Convert to seconds
                    self.logger.debug(
                        f"Retry {operation_name} after {delay}s "
                        f"(error: {exc})"
                    )
                    await asyncio.sleep(delay)

        if last_error:
            self.logger.error(
                f"Operation exhausted retries: {operation_name} - {last_error}"
            )

        return fallback_value

    @staticmethod
    def create_error_response(
        status_code: int,
        error: str,
        error_code: str = "ERROR",
        details: Optional[Dict[str, Any]] = None,
    ) -> JSONResponse:
        """
        Create structured error response.

        Args:
            status_code: HTTP status code
            error: Error message
            error_code: Error code for classification
            details: Additional details

        Returns:
            JSONResponse with structured error format
        """
        content = {
            "success": False,
            "error": error,
            "error_code": error_code,
        }

        if details:
            content["details"] = details

        return JSONResponse(
            status_code=status_code,
            content=content,
        )

    def apply_fallback_strategy(
        self,
        strategy: Optional[FallbackStrategy] = None,
        operation_name: str = "operation",
    ) -> Dict[str, Any]:
        """
        Get fallback strategy and return appropriate response structure.

        Args:
            strategy: Fallback strategy to apply (uses default if None)
            operation_name: Name of operation for logging

        Returns:
            Dictionary with fallback action and data

        Raises:
            ValueError: If strategy is RETURN_ERROR
        """
        strategy = strategy or self.fallback_strategy

        self.logger.warning(
            f"Applying fallback strategy: {strategy} for {operation_name}"
        )

        if strategy == FallbackStrategy.RETURN_ERROR:
            return {
                "action": "error",
                "status_code": 500,
                "message": f"Failed to {operation_name}",
            }
        elif strategy == FallbackStrategy.RETURN_PARTIAL:
            return {
                "action": "partial",
                "data": {},
            }
        elif strategy == FallbackStrategy.SKIP_CONTEXT:
            return {
                "action": "skip",
                "data": None,
            }
        elif strategy == FallbackStrategy.RETRY_ONCE:
            return {
                "action": "retry",
                "max_attempts": 1,
            }
        else:
            raise ValueError(f"Unknown fallback strategy: {strategy}")
