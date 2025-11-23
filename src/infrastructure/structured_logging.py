"""Enhanced structured logging for LangChain AI application.

Provides JSON-formatted logs compatible with Logstash and ELK stack.
Includes request tracing, performance metrics, and contextual information.
"""

import json
import logging
import sys
import time
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

# Context variables for request tracking
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")
user_id_ctx: ContextVar[str] = ContextVar("user_id", default="")


class StructuredLogger:
    """Structured JSON logger for centralized logging."""

    def __init__(self, name: str, level: int = logging.INFO):
        """
        Initialize structured logger.

        Args:
            name: Logger name (typically __name__)
            level: Logging level (default: INFO)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Remove existing handlers
        self.logger.handlers.clear()

        # Create console handler with JSON formatter
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)

        # Prevent propagation to avoid duplicate logs
        self.logger.propagate = False

    def _build_log_entry(
        self,
        message: str,
        level: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Build structured log entry.

        Args:
            message: Log message
            level: Log level
            extra: Additional fields

        Returns:
            Structured log dictionary
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "logger": self.logger.name,
            "request_id": request_id_ctx.get() or "N/A",
            "user_id": user_id_ctx.get() or "N/A",
        }

        if extra:
            log_entry.update(extra)

        return log_entry

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        log_entry = self._build_log_entry(message, "DEBUG", kwargs)
        self.logger.debug(json.dumps(log_entry))

    def info(self, message: str, **kwargs):
        """Log info message."""
        log_entry = self._build_log_entry(message, "INFO", kwargs)
        self.logger.info(json.dumps(log_entry))

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        log_entry = self._build_log_entry(message, "WARNING", kwargs)
        self.logger.warning(json.dumps(log_entry))

    def error(self, message: str, exc_info: Optional[Exception] = None, **kwargs):
        """
        Log error message.

        Args:
            message: Error message
            exc_info: Exception object
            **kwargs: Additional fields
        """
        log_entry = self._build_log_entry(message, "ERROR", kwargs)

        if exc_info:
            log_entry["exception"] = {
                "type": type(exc_info).__name__,
                "message": str(exc_info),
                "traceback": traceback.format_exc(),
            }

        self.logger.error(json.dumps(log_entry))

    def critical(self, message: str, exc_info: Optional[Exception] = None, **kwargs):
        """
        Log critical message.

        Args:
            message: Critical message
            exc_info: Exception object
            **kwargs: Additional fields
        """
        log_entry = self._build_log_entry(message, "CRITICAL", kwargs)

        if exc_info:
            log_entry["exception"] = {
                "type": type(exc_info).__name__,
                "message": str(exc_info),
                "traceback": traceback.format_exc(),
            }

        self.logger.critical(json.dumps(log_entry))


class JSONFormatter(logging.Formatter):
    """JSON log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record

        Returns:
            JSON-formatted log string
        """
        # If message is already JSON, return as-is
        try:
            json.loads(record.getMessage())
            return record.getMessage()
        except (json.JSONDecodeError, TypeError):
            pass

        # Build structured log
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        return json.dumps(log_entry)


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured request/response logging.

    Logs all HTTP requests with timing, status codes, and contextual information.
    """

    def __init__(self, app, logger: Optional[StructuredLogger] = None):
        """
        Initialize middleware.

        Args:
            app: FastAPI application
            logger: Structured logger instance
        """
        super().__init__(app)
        self.logger = logger or StructuredLogger(__name__)

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """
        Process request and log details.

        Args:
            request: Incoming request
            call_next: Next middleware/endpoint

        Returns:
            Response
        """
        # Generate request ID
        req_id = str(uuid4())
        request_id_ctx.set(req_id)

        # Extract user ID if available
        user_id = request.headers.get("X-User-ID", "anonymous")
        user_id_ctx.set(user_id)

        # Start timing
        start_time = time.time()

        # Log request
        self.logger.info(
            "Incoming request",
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params),
            client_ip=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log response
            self.logger.info(
                "Request completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = req_id

            return response

        except Exception as exc:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log error
            self.logger.error(
                "Request failed",
                exc_info=exc,
                method=request.method,
                path=request.url.path,
                duration_ms=round(duration_ms, 2),
            )

            raise


# Global logger instance
def get_logger(name: str) -> StructuredLogger:
    """
    Get or create structured logger.

    Args:
        name: Logger name

    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name)


# Helper function for performance logging
def log_performance(
    logger: StructuredLogger,
    operation: str,
    duration_ms: float,
    **kwargs,
):
    """
    Log performance metric.

    Args:
        logger: Logger instance
        operation: Operation name
        duration_ms: Duration in milliseconds
        **kwargs: Additional fields
    """
    logger.info(
        f"Performance: {operation}",
        operation=operation,
        duration_ms=round(duration_ms, 2),
        **kwargs,
    )


# Helper function for cache logging
def log_cache_operation(
    logger: StructuredLogger,
    operation: str,
    hit: bool,
    model: str,
    latency_ms: float,
    distance: Optional[float] = None,
):
    """
    Log cache operation.

    Args:
        logger: Logger instance
        operation: Operation type (hit/miss)
        hit: Whether cache hit
        model: Model name
        latency_ms: Operation latency
        distance: Semantic distance (if applicable)
    """
    log_data = {
        "operation": operation,
        "cache_hit": hit,
        "model": model,
        "latency_ms": round(latency_ms, 2),
    }

    if distance is not None:
        log_data["distance"] = round(distance, 4)

    logger.info(f"Cache operation: {operation}", **log_data)


# Helper function for RAG logging
def log_rag_query(
    logger: StructuredLogger,
    query: str,
    model: str,
    cache_hit: bool,
    latency_ms: float,
    chunks_retrieved: int,
    total_tokens: Optional[int] = None,
):
    """
    Log RAG query.

    Args:
        logger: Logger instance
        query: Query text
        model: Model name
        cache_hit: Whether cache hit
        latency_ms: Total latency
        chunks_retrieved: Number of chunks retrieved
        total_tokens: Total tokens used (if applicable)
    """
    log_data = {
        "query_length": len(query),
        "model": model,
        "cache_hit": cache_hit,
        "latency_ms": round(latency_ms, 2),
        "chunks_retrieved": chunks_retrieved,
    }

    if total_tokens:
        log_data["total_tokens"] = total_tokens

    logger.info("RAG query processed", **log_data)
