"""Response structuring middleware for JSON formatting and validation."""

import json
import logging
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse

logger = logging.getLogger(__name__)


class ResponseStructuringMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structuring API responses.

    Ensures consistent response format:
    {
        "success": bool,
        "data": any,
        "error": optional[str],
        "timestamp": str,
        "request_id": str
    }
    """

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
        # Add request ID to state (for tracking)
        import uuid
        request.state.request_id = str(uuid.uuid4())

        response = await call_next(request)

        # Skip structuring for non-JSON responses
        if response.status_code == 204:  # No content
            return response

        if "application/json" not in response.headers.get("content-type", ""):
            return response

        # Read and parse response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        try:
            original_data = json.loads(body) if body else None
        except json.JSONDecodeError:
            # If we can't parse it, return a new JSONResponse with the raw body
            return JSONResponse(
                content=original_data,
                status_code=response.status_code,
                headers=dict(response.headers),
            )

        # Structure the response
        structured = self.structure_response(
            success=response.status_code < 400,
            data=original_data if response.status_code < 400 else None,
            error=original_data if response.status_code >= 400 else None,
            request_id=request.state.request_id,
        )

        # Return NEW JSONResponse with structured body
        # This avoids consuming the original response iterator
        return JSONResponse(
            content=structured,
            status_code=response.status_code,
            headers=dict(response.headers),
        )

    @staticmethod
    def structure_response(
        success: bool,
        data: Optional[any] = None,
        error: Optional[any] = None,
        request_id: Optional[str] = None,
    ) -> dict:
        """
        Structure response in consistent format.

        Args:
            success: Whether request was successful
            data: Response data (if successful)
            error: Error details (if failed)
            request_id: Request ID for tracking

        Returns:
            Structured response dict
        """
        from datetime import datetime

        structured = {
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if request_id:
            structured["request_id"] = request_id

        if data is not None:
            structured["data"] = data

        if error is not None:
            structured["error"] = error

        return structured
