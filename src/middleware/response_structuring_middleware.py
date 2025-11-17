"""Response structuring middleware for JSON formatting and validation."""

import json
import logging
import time
import uuid
from datetime import datetime
from typing import Optional, Any, Dict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse

logger = logging.getLogger(__name__)


class ResponseStructuringMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structuring API responses in consistent format.

    Ensures all responses follow the standard format:
    ```json
    {
        "success": bool,
        "data": Optional[any],
        "error": Optional[str],
        "error_code": Optional[str],
        "timestamp": str (ISO 8601),
        "request_id": str,
        "metadata": {
            "tokens_used": Optional[int],
            "tools_called": Optional[List[str]],
            "duration_ms": float
        }
    }
    ```

    Performance target: <5ms overhead
    """

    # Response exempt paths (skip structuring)
    EXEMPT_PATHS = {
        "/health",
        "/health/full",
        "/api/docs",
        "/api/openapi.json",
        "/api/redoc",
    }

    def __init__(self, app):
        """Initialize middleware."""
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and structure response.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response with structured body
        """
        # Add request ID to state (for tracking and logging)
        request.state.request_id = str(uuid.uuid4())
        request.state.response_start_time = time.time()

        # Call next middleware/endpoint
        response = await call_next(request)

        # Skip structuring for exempt paths
        if self._is_exempt_path(request.url.path):
            return response

        # Skip structuring for non-JSON responses or no-content responses
        if response.status_code == 204:  # No content
            return response

        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response

        # Skip structuring if already structured (has "success" field)
        try:
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            if not body:
                return self._create_structured_response(
                    success=response.status_code < 400,
                    data=None,
                    error=None,
                    request_id=request.state.request_id,
                    status_code=response.status_code,
                    duration_ms=self._get_elapsed_ms(request),
                    metadata={},
                )

            try:
                original_data = json.loads(body)
            except json.JSONDecodeError:
                # Invalid JSON, return as-is
                return JSONResponse(
                    content={"error": "Invalid JSON response"},
                    status_code=500,
                    headers=dict(response.headers),
                )

            # Check if already structured
            if isinstance(original_data, dict) and "success" in original_data:
                # Already structured, just return with enhanced metadata
                return JSONResponse(
                    content=original_data,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                )

            # Structure the response
            duration_ms = self._get_elapsed_ms(request)
            structured = self._structure_response(
                success=response.status_code < 400,
                data=original_data if response.status_code < 400 else None,
                error=original_data if response.status_code >= 400 else None,
                request_id=request.state.request_id,
                duration_ms=duration_ms,
                metadata=self._extract_metadata(request),
            )

            # Return structured response
            return JSONResponse(
                content=structured,
                status_code=response.status_code,
                headers=dict(response.headers),
            )

        except Exception as e:
            logger.error(f"Error structuring response: {e}")
            # Return error response
            return JSONResponse(
                content={
                    "success": False,
                    "error": "Internal server error",
                    "error_code": "INTERNAL_ERROR",
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": request.state.request_id,
                },
                status_code=500,
            )

    @staticmethod
    def _structure_response(
        success: bool,
        data: Optional[Any] = None,
        error: Optional[Any] = None,
        request_id: Optional[str] = None,
        duration_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Structure response in consistent format.

        Args:
            success: Whether request was successful
            data: Response data (if successful)
            error: Error details (if failed)
            request_id: Request ID for tracking
            duration_ms: Request duration in milliseconds
            metadata: Additional metadata

        Returns:
            Structured response dict
        """
        structured = {
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if request_id:
            structured["request_id"] = request_id

        if data is not None:
            structured["data"] = data

        if error is not None:
            if isinstance(error, dict) and "detail" in error:
                structured["error"] = error.get("detail", str(error))
                structured["error_code"] = error.get("error_code", "ERROR")
            else:
                structured["error"] = str(error)
                structured["error_code"] = "ERROR"

        # Add metadata
        if metadata:
            structured["metadata"] = metadata
        else:
            structured["metadata"] = {}

        # Always include duration
        structured["metadata"]["duration_ms"] = round(duration_ms, 2)

        return structured

    @staticmethod
    def _create_structured_response(
        success: bool,
        data: Optional[Any] = None,
        error: Optional[Any] = None,
        request_id: Optional[str] = None,
        status_code: int = 200,
        duration_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> JSONResponse:
        """Create a structured JSON response."""
        content = ResponseStructuringMiddleware._structure_response(
            success=success,
            data=data,
            error=error,
            request_id=request_id,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )

        return JSONResponse(
            content=content,
            status_code=status_code,
        )

    @staticmethod
    def _extract_metadata(request: Request) -> Dict[str, Any]:
        """
        Extract metadata from request state.

        Args:
            request: FastAPI request

        Returns:
            Metadata dictionary
        """
        metadata = {}

        # Add token count if available
        if hasattr(request.state, "tokens_used"):
            metadata["tokens_used"] = request.state.tokens_used

        # Add tools called if available
        if hasattr(request.state, "tools_called"):
            metadata["tools_called"] = request.state.tools_called

        # Add memory injection time if available
        if hasattr(request.state, "memory_injection_time_ms"):
            metadata["memory_injection_ms"] = round(
                request.state.memory_injection_time_ms, 2
            )

        # Add auth time if available
        if hasattr(request.state, "auth_time_ms"):
            metadata["auth_ms"] = round(request.state.auth_time_ms, 2)

        return metadata

    @staticmethod
    def _get_elapsed_ms(request: Request) -> float:
        """
        Calculate elapsed time since request start.

        Args:
            request: FastAPI request

        Returns:
            Elapsed time in milliseconds
        """
        if hasattr(request.state, "response_start_time"):
            elapsed = time.time() - request.state.response_start_time
            return elapsed * 1000
        return 0.0

    @staticmethod
    def _is_exempt_path(path: str) -> bool:
        """Check if path is exempt from response structuring."""
        exempt_paths = {
            "/health",
            "/health/full",
            "/api/docs",
            "/api/openapi.json",
            "/api/redoc",
        }

        if path in exempt_paths:
            return True

        if path.startswith("/api/docs") or path.startswith("/api/openapi"):
            return True

        return False
