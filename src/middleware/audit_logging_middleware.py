"""Audit logging middleware for tracking requests, performance, and events."""

import json
import logging
import os
import time
from typing import Optional, Dict, Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)
audit_logger = logging.getLogger("audit")


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for audit logging and comprehensive performance tracking.

    Logs:
    - Request details (method, path, user, timestamp, conversation_id)
    - Performance metrics (response time, status, middleware breakdowns)
    - Tool calls and parameters
    - Error details for debugging
    - Structured JSON format for log aggregation

    Configuration via environment variables:
    - AUDIT_LOGGING_ENABLED: Enable/disable audit logging
    - PERFORMANCE_WARNING_THRESHOLD_MS: Warn if request > N ms
    - PERFORMANCE_ERROR_THRESHOLD_MS: Error if request > N ms

    Performance target: <10ms logging overhead
    """

    def __init__(self, app):
        """Initialize middleware with performance configuration."""
        super().__init__(app)
        self.audit_enabled = os.getenv("AUDIT_LOGGING_ENABLED", "true").lower() == "true"
        self.performance_warning_ms = float(
            os.getenv("PERFORMANCE_WARNING_THRESHOLD_MS", "1000")
        )
        self.performance_error_ms = float(
            os.getenv("PERFORMANCE_ERROR_THRESHOLD_MS", "5000")
        )

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request with comprehensive audit logging.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response with logged metrics
        """
        if not self.audit_enabled:
            return await call_next(request)

        # Start timer
        start_time = time.time()

        # Get request info
        user_id = getattr(request.state, "user_id", "anonymous")
        request_id = getattr(request.state, "request_id", "unknown")
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)

        # Extract conversation ID from path
        conversation_id = self._extract_conversation_id(path)

        # Log request start
        self.log_request_start(
            request_id=request_id,
            user_id=user_id,
            method=method,
            path=path,
            conversation_id=conversation_id,
            query_params=query_params,
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate elapsed time and breakdowns
            elapsed_ms = (time.time() - start_time) * 1000

            # Extract middleware timings from request state
            performance_metrics = self._extract_performance_metrics(request, elapsed_ms)

            # Log request completion
            self.log_request_completion(
                request_id=request_id,
                user_id=user_id,
                method=method,
                path=path,
                conversation_id=conversation_id,
                status_code=response.status_code,
                elapsed_ms=elapsed_ms,
                metrics=performance_metrics,
            )

            # Check performance thresholds
            if elapsed_ms > self.performance_error_ms:
                logger.error(
                    f"Slow request (ERROR): {method} {path} took {elapsed_ms:.2f}ms "
                    f"(threshold: {self.performance_error_ms}ms)"
                )
            elif elapsed_ms > self.performance_warning_ms:
                logger.warning(
                    f"Slow request (WARN): {method} {path} took {elapsed_ms:.2f}ms "
                    f"(threshold: {self.performance_warning_ms}ms)"
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
                conversation_id=conversation_id,
                error=str(e),
                error_type=type(e).__name__,
                elapsed_ms=elapsed_ms,
            )

            raise

    def log_request_start(
        self,
        request_id: str,
        user_id: str,
        method: str,
        path: str,
        conversation_id: Optional[str] = None,
        query_params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log request start.

        Args:
            request_id: Unique request ID
            user_id: User ID
            method: HTTP method
            path: Request path
            conversation_id: Conversation ID (if applicable)
            query_params: Query parameters
        """
        log_data = {
            "event": "request_start",
            "request_id": request_id,
            "user_id": user_id,
            "method": method,
            "path": path,
        }

        if conversation_id:
            log_data["conversation_id"] = conversation_id

        if query_params:
            log_data["query_params"] = query_params

        audit_logger.info(json.dumps(log_data))

    def log_request_completion(
        self,
        request_id: str,
        user_id: str,
        method: str,
        path: str,
        status_code: int,
        elapsed_ms: float,
        conversation_id: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log request completion with performance metrics.

        Args:
            request_id: Unique request ID
            user_id: User ID
            method: HTTP method
            path: Request path
            status_code: HTTP status code
            elapsed_ms: Elapsed time in milliseconds
            conversation_id: Conversation ID (if applicable)
            metrics: Performance metrics breakdown
        """
        log_data = {
            "event": "request_complete",
            "request_id": request_id,
            "user_id": user_id,
            "method": method,
            "path": path,
            "status_code": status_code,
            "elapsed_ms": round(elapsed_ms, 2),
        }

        if conversation_id:
            log_data["conversation_id"] = conversation_id

        if metrics:
            log_data["metrics"] = metrics

        audit_logger.info(json.dumps(log_data))

    def log_request_error(
        self,
        request_id: str,
        user_id: str,
        method: str,
        path: str,
        error: str,
        error_type: str = "Unknown",
        elapsed_ms: float = 0.0,
        conversation_id: Optional[str] = None,
    ) -> None:
        """
        Log request error.

        Args:
            request_id: Unique request ID
            user_id: User ID
            method: HTTP method
            path: Request path
            error: Error message
            error_type: Exception type
            elapsed_ms: Elapsed time in milliseconds
            conversation_id: Conversation ID (if applicable)
        """
        log_data = {
            "event": "request_error",
            "level": "error",
            "request_id": request_id,
            "user_id": user_id,
            "method": method,
            "path": path,
            "error": error,
            "error_type": error_type,
            "elapsed_ms": round(elapsed_ms, 2),
        }

        if conversation_id:
            log_data["conversation_id"] = conversation_id

        audit_logger.error(json.dumps(log_data))

    def log_event(
        self,
        event_type: str,
        user_id: str,
        details: Dict[str, Any],
        request_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> None:
        """
        Log custom event.

        Args:
            event_type: Type of event
            user_id: User ID
            details: Event details
            request_id: Optional request ID for correlation
            conversation_id: Optional conversation ID
        """
        log_data = {
            "event": event_type,
            "user_id": user_id,
            "details": details,
        }

        if request_id:
            log_data["request_id"] = request_id

        if conversation_id:
            log_data["conversation_id"] = conversation_id

        audit_logger.info(json.dumps(log_data))

    def log_tool_call(
        self,
        tool_name: str,
        user_id: str,
        request_id: str,
        parameters: Dict[str, Any],
        result: Optional[str] = None,
        duration_ms: float = 0.0,
        conversation_id: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Log tool execution.

        Args:
            tool_name: Name of the tool
            user_id: User ID
            request_id: Request ID
            parameters: Tool parameters
            result: Tool result (if successful)
            duration_ms: Execution duration
            conversation_id: Conversation ID
            error: Error message (if failed)
        """
        log_data = {
            "event": "tool_call",
            "tool_name": tool_name,
            "user_id": user_id,
            "request_id": request_id,
            "duration_ms": round(duration_ms, 2),
        }

        if parameters:
            log_data["parameters"] = parameters

        if result:
            log_data["result"] = result

        if error:
            log_data["error"] = error
            log_data["status"] = "failed"
        else:
            log_data["status"] = "success"

        if conversation_id:
            log_data["conversation_id"] = conversation_id

        audit_logger.info(json.dumps(log_data))

    @staticmethod
    def _extract_conversation_id(path: str) -> Optional[str]:
        """
        Extract conversation ID from request path.

        Handles patterns like:
        - /api/v1/conversations/{id}
        - /api/v1/conversations/{id}/messages
        - /api/v1/conversations/{id}/stream

        Args:
            path: Request path

        Returns:
            Conversation ID or None
        """
        parts = path.split("/")
        try:
            idx = parts.index("conversations")
            if idx + 1 < len(parts):
                return parts[idx + 1]
        except (ValueError, IndexError):
            pass
        return None

    @staticmethod
    def _extract_performance_metrics(
        request: Request,
        total_ms: float,
    ) -> Dict[str, Any]:
        """
        Extract performance metrics from request state.

        Args:
            request: FastAPI request
            total_ms: Total request time

        Returns:
            Performance metrics dictionary
        """
        metrics = {
            "total_ms": round(total_ms, 2),
        }

        # Add middleware breakdowns
        if hasattr(request.state, "auth_time_ms"):
            metrics["auth_ms"] = round(request.state.auth_time_ms, 2)

        if hasattr(request.state, "memory_injection_time_ms"):
            metrics["memory_injection_ms"] = round(request.state.memory_injection_time_ms, 2)

        # Add tokens used
        if hasattr(request.state, "tokens_used"):
            metrics["tokens_used"] = request.state.tokens_used

        # Add tools called
        if hasattr(request.state, "tools_called"):
            metrics["tools_called"] = request.state.tools_called

        return metrics
