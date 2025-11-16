"""Content moderation middleware for safety checks and rate limiting."""

import logging
import time
from typing import Dict

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class ContentModerationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for content moderation and rate limiting.

    Provides:
    - Rate limiting per user
    - Content safety checks
    - Request throttling
    """

    # Rate limit: requests per minute per user
    RATE_LIMIT = 60
    WINDOW_SIZE = 60  # seconds

    def __init__(self, app):
        """Initialize middleware."""
        super().__init__(app)
        # Store request timestamps per user: {user_id: [timestamps]}
        self.request_times: Dict[str, list] = {}

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request with content moderation.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response
        """
        # Get user_id from auth middleware (if available)
        user_id = getattr(request.state, "user_id", "anonymous")

        # Apply rate limiting for non-health endpoints
        if not request.url.path.startswith("/health"):
            if not self.check_rate_limit(user_id):
                logger.warning(f"Rate limit exceeded for user {user_id}")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Rate limit exceeded. Maximum 60 requests per minute."},
                )

        response = await call_next(request)
        return response

    def check_rate_limit(self, user_id: str) -> bool:
        """
        Check if user has exceeded rate limit.

        Args:
            user_id: User ID

        Returns:
            True if within limit, False if exceeded
        """
        current_time = time.time()

        # Initialize user if not exists
        if user_id not in self.request_times:
            self.request_times[user_id] = []

        # Remove old timestamps outside the window
        self.request_times[user_id] = [
            ts for ts in self.request_times[user_id]
            if current_time - ts < self.WINDOW_SIZE
        ]

        # Check if under limit
        if len(self.request_times[user_id]) >= self.RATE_LIMIT:
            return False

        # Add current timestamp
        self.request_times[user_id].append(current_time)
        return True

    def check_content_safety(self, content: str) -> bool:
        """
        Check if content passes safety checks.

        In production, integrate with:
        - OpenAI Moderation API
        - Google Safe Browsing
        - Perspective API
        - Custom filters

        Args:
            content: Content to check

        Returns:
            True if safe, False if potentially harmful
        """
        # Placeholder for content safety checks
        # In production: call moderation API

        # Basic checks
        if len(content) > 10000:
            return False

        # Check for common harmful patterns (simplified)
        harmful_patterns = ["malware", "exploit", "hack"]
        content_lower = content.lower()

        for pattern in harmful_patterns:
            if pattern in content_lower:
                logger.warning(f"Potentially harmful content detected: {pattern}")
                return False

        return True
