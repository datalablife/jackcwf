"""Audit logging middleware for tracking requests, performance, and events."""

import json
import logging
import time
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for audit logging and performance tracking.

    Logs:
    - Request details (method, path, user, timestamp)
    - Performance metrics (response time, status)
    - Event tracking for important operations
    - Error details for debugging
    """

    def __init__(self, app):
        """Initialize middleware."""
        super().__init__(app)
        self.logger = logging.getLogger("audit")

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request with audit logging.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response
        """
        # Start timer
        start_time = time.time()

        # Get request info
        user_id = getattr(request.state, "user_id", "anonymous")
        request_id = getattr(request.state, "request_id", "unknown")
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)

        # Log request start
        self.log_request_start(
            request_id=request_id,
            user_id=user_id,
            method=method,
            path=path,
            query_params=query_params,
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate elapsed time
            elapsed_ms = (time.time() - start_time) * 1000

            # Log request completion
            self.log_request_completion(
                request_id=request_id,
                user_id=user_id,
                method=method,
                path=path,
                status_code=response.status_code,
                elapsed_ms=elapsed_ms,
            )

            # Warn if slow
            if elapsed_ms > 1000:
                logger.warning(
                    f"Slow request detected: {method} {path} took {elapsed_ms:.2f}ms"
                )

            return response

        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000

            # Log error
            self.log_request_error(
                request_id=request_id,
                user_id=user_id,
                method=method,
                path=path,
                error=str(e),
                elapsed_ms=elapsed_ms,
            )

            raise

    def log_request_start(
        self,
        request_id: str,
        user_id: str,
        method: str,
        path: str,
        query_params: Optional[dict] = None,
    ) -> None:
        """
        Log request start.

        Args:
            request_id: Unique request ID
            user_id: User ID
            method: HTTP method
            path: Request path
            query_params: Query parameters
        """
        self.logger.info(
            json.dumps(
                {
                    "event": "request_start",
                    "request_id": request_id,
                    "user_id": user_id,
                    "method": method,
                    "path": path,
                    "query_params": query_params,
                }
            )
        )

    def log_request_completion(
        self,
        request_id: str,
        user_id: str,
        method: str,
        path: str,
        status_code: int,
        elapsed_ms: float,
    ) -> None:
        """
        Log request completion.

        Args:
            request_id: Unique request ID
            user_id: User ID
            method: HTTP method
            path: Request path
            status_code: HTTP status code
            elapsed_ms: Elapsed time in milliseconds
        """
        self.logger.info(
            json.dumps(
                {
                    "event": "request_complete",
                    "request_id": request_id,
                    "user_id": user_id,
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "elapsed_ms": round(elapsed_ms, 2),
                }
            )
        )

    def log_request_error(
        self,
        request_id: str,
        user_id: str,
        method: str,
        path: str,
        error: str,
        elapsed_ms: float,
    ) -> None:
        """
        Log request error.

        Args:
            request_id: Unique request ID
            user_id: User ID
            method: HTTP method
            path: Request path
            error: Error message
            elapsed_ms: Elapsed time in milliseconds
        """
        self.logger.error(
            json.dumps(
                {
                    "event": "request_error",
                    "request_id": request_id,
                    "user_id": user_id,
                    "method": method,
                    "path": path,
                    "error": error,
                    "elapsed_ms": round(elapsed_ms, 2),
                }
            )
        )

    def log_event(
        self,
        event_type: str,
        user_id: str,
        details: dict,
        request_id: Optional[str] = None,
    ) -> None:
        """
        Log custom event.

        Args:
            event_type: Type of event
            user_id: User ID
            details: Event details
            request_id: Optional request ID for correlation
        """
        self.logger.info(
            json.dumps(
                {
                    "event": event_type,
                    "user_id": user_id,
                    "request_id": request_id,
                    "details": details,
                }
            )
        )
