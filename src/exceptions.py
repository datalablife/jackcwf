"""Global exception definitions for LangChain AI Conversation system."""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class APIException(Exception):
    """Base API exception."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize API exception.

        Args:
            message: Error message
            status_code: HTTP status code
            error_code: Error code for classification
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response."""
        return {
            "success": False,
            "error": self.message,
            "error_code": self.error_code,
            "details": self.details,
        }


class ValidationException(APIException):
    """Raised when input validation fails (400)."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize validation exception."""
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class UnauthorizedException(APIException):
    """Raised when authentication fails (401)."""

    def __init__(self, message: str = "Unauthorized", details: Optional[Dict[str, Any]] = None):
        """Initialize unauthorized exception."""
        super().__init__(
            message=message,
            status_code=401,
            error_code="UNAUTHORIZED",
            details=details,
        )


class ForbiddenException(APIException):
    """Raised when user lacks permission (403)."""

    def __init__(self, message: str = "Forbidden", details: Optional[Dict[str, Any]] = None):
        """Initialize forbidden exception."""
        super().__init__(
            message=message,
            status_code=403,
            error_code="FORBIDDEN",
            details=details,
        )


class NotFoundException(APIException):
    """Raised when resource not found (404)."""

    def __init__(self, resource: str = "Resource", details: Optional[Dict[str, Any]] = None):
        """Initialize not found exception."""
        super().__init__(
            message=f"{resource} not found",
            status_code=404,
            error_code="NOT_FOUND",
            details=details,
        )


class RateLimitException(APIException):
    """Raised when rate limit exceeded (429)."""

    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        """Initialize rate limit exception."""
        super().__init__(
            message=message,
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details,
        )


class ConversationException(APIException):
    """Raised for conversation-related errors (400)."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize conversation exception."""
        super().__init__(
            message=message,
            status_code=400,
            error_code="CONVERSATION_ERROR",
            details=details,
        )


class AgentException(APIException):
    """Raised for agent execution errors (500)."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize agent exception."""
        super().__init__(
            message=message,
            status_code=500,
            error_code="AGENT_ERROR",
            details=details,
        )


class VectorSearchException(APIException):
    """Raised for vector search errors (500)."""

    def __init__(self, message: str = "Vector search failed", details: Optional[Dict[str, Any]] = None):
        """Initialize vector search exception."""
        super().__init__(
            message=message,
            status_code=500,
            error_code="VECTOR_SEARCH_ERROR",
            details=details,
        )


class DatabaseException(APIException):
    """Raised for database errors (500)."""

    def __init__(self, message: str = "Database error", details: Optional[Dict[str, Any]] = None):
        """Initialize database exception."""
        super().__init__(
            message=message,
            status_code=500,
            error_code="DATABASE_ERROR",
            details=details,
        )


class TimeoutException(APIException):
    """Raised when operation times out (504)."""

    def __init__(self, operation: str = "Operation", details: Optional[Dict[str, Any]] = None):
        """Initialize timeout exception."""
        super().__init__(
            message=f"{operation} timed out",
            status_code=504,
            error_code="TIMEOUT",
            details=details,
        )


class ContentModerationException(APIException):
    """Raised when content violates moderation policy (400)."""

    def __init__(self, violation_type: str = "Content violation", details: Optional[Dict[str, Any]] = None):
        """Initialize content moderation exception."""
        super().__init__(
            message=f"Content violates policy: {violation_type}",
            status_code=400,
            error_code="CONTENT_VIOLATION",
            details=details,
        )


async def call_with_retry(
    func,
    *args,
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    timeout_seconds: Optional[float] = None,
    **kwargs
):
    """
    Call async function with exponential backoff retry.

    Args:
        func: Async function to call
        *args: Positional arguments
        max_retries: Maximum retry attempts
        backoff_factor: Exponential backoff multiplier
        timeout_seconds: Optional timeout for each attempt
        **kwargs: Keyword arguments

    Returns:
        Function result

    Raises:
        Exception: If all retries exhausted
    """
    import asyncio
    import time

    last_error = None

    for attempt in range(max_retries + 1):
        try:
            if timeout_seconds:
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout_seconds,
                )
            else:
                result = await func(*args, **kwargs)

            return result

        except asyncio.TimeoutError as e:
            last_error = TimeoutException(operation=func.__name__)
            logger.warning(f"Attempt {attempt + 1} timeout: {func.__name__}")

        except Exception as e:
            last_error = e
            logger.warning(f"Attempt {attempt + 1} failed: {func.__name__} - {e}")

        # Exponential backoff
        if attempt < max_retries:
            delay = (backoff_factor ** attempt)
            await asyncio.sleep(delay)

    # All retries exhausted
    logger.error(f"All retries exhausted for {func.__name__}: {last_error}")
    raise last_error or Exception(f"Failed to call {func.__name__}")
