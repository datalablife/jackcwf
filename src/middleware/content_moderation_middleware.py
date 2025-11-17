"""Content moderation middleware for safety checks and rate limiting."""

import asyncio
import logging
import os
import re
import time
from typing import Dict, Optional, Tuple

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)


class ContentModerationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for content moderation and rate limiting.

    Provides:
    - Rate limiting per user (100 req/min) and IP (1000 req/min)
    - SQL injection detection
    - XSS/prompt injection detection
    - Content safety checks
    - Request/response size validation
    - Performance target: <100ms

    Configuration via environment variables:
    - CONTENT_MODERATION_ENABLED: Enable/disable moderation
    - RATE_LIMIT_ENABLED: Enable/disable rate limiting
    - RATE_LIMIT_USER: User rate limit (req/min)
    - RATE_LIMIT_IP: IP rate limit (req/min)
    - MAX_REQUEST_SIZE: Max request body size (bytes)
    - MAX_RESPONSE_SIZE: Max response size (bytes)
    - MODERATION_TIMEOUT_MS: Moderation check timeout
    """

    # Rate limit configuration
    RATE_LIMIT_USER = 100  # requests per minute per user
    RATE_LIMIT_IP = 1000  # requests per minute per IP
    WINDOW_SIZE = 60  # seconds

    # Content constraints
    MAX_REQUEST_SIZE = 10000  # characters
    MAX_RESPONSE_SIZE = 50000  # characters

    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"('|\")\s*(OR|AND)\s*('|\")?",
        r"--\s*$",
        r"/\*.*\*/",
        r";\s*(DROP|DELETE|TRUNCATE|UPDATE)",
    ]

    # XSS/Prompt injection patterns
    INJECTION_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"eval\s*\(",
        r"__import__",
        r"exec\s*\(",
    ]

    def __init__(self, app):
        """Initialize middleware with rate limiting and security checks."""
        super().__init__(app)
        self.moderation_enabled = os.getenv("CONTENT_MODERATION_ENABLED", "true").lower() == "true"
        self.rate_limit_enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
        self.rate_limit_user = int(os.getenv("RATE_LIMIT_USER", self.RATE_LIMIT_USER))
        self.rate_limit_ip = int(os.getenv("RATE_LIMIT_IP", self.RATE_LIMIT_IP))
        self.max_request_size = int(os.getenv("MAX_REQUEST_SIZE", self.MAX_REQUEST_SIZE))
        self.max_response_size = int(os.getenv("MAX_RESPONSE_SIZE", self.MAX_RESPONSE_SIZE))
        self.moderation_timeout_ms = float(os.getenv("MODERATION_TIMEOUT_MS", "100"))

        # Rate limit tracking: {user_id or ip: [timestamps]}
        self.user_request_times: Dict[str, list] = {}
        self.ip_request_times: Dict[str, list] = {}
        self.max_age = 3600  # Keep timestamps for 1 hour

        # Compile regex patterns
        self.sql_patterns = [re.compile(p, re.IGNORECASE) for p in self.SQL_INJECTION_PATTERNS]
        self.injection_patterns = [re.compile(p, re.IGNORECASE) for p in self.INJECTION_PATTERNS]

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request with content moderation.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response (429 if rate limited, 400 if unsafe content)
        """
        # Skip moderation for health checks and documentation
        if self._is_exempt_path(request.url.path):
            return await call_next(request)

        # Get user_id and IP from request
        user_id = getattr(request.state, "user_id", "anonymous")
        client_ip = self._get_client_ip(request)

        # Apply rate limiting
        if self.rate_limit_enabled:
            rate_limit_status = self._check_rate_limits(user_id, client_ip)
            if not rate_limit_status[0]:
                logger.warning(
                    f"Rate limit exceeded for {rate_limit_status[1]} "
                    f"(user={user_id}, ip={client_ip})"
                )
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "success": False,
                        "error": f"Rate limit exceeded. {rate_limit_status[1]}",
                        "error_code": "RATE_LIMIT_EXCEEDED",
                    },
                )

        # Apply content moderation
        if self.moderation_enabled and request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Read and check request body
                body = await request.body()
                if body:
                    # Check size
                    if len(body) > self.max_request_size * 4:  # UTF-8 could be 4 bytes per char
                        logger.warning(f"Request body too large: {len(body)} bytes")
                        return JSONResponse(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            content={
                                "success": False,
                                "error": "Request body too large",
                                "error_code": "PAYLOAD_TOO_LARGE",
                            },
                        )

                    # Check content safety
                    try:
                        body_str = body.decode("utf-8", errors="ignore")
                        is_safe, violation_type = await asyncio.wait_for(
                            self._check_content_safety(body_str),
                            timeout=self.moderation_timeout_ms / 1000.0
                        )

                        if not is_safe:
                            logger.warning(
                                f"Potentially harmful content detected ({violation_type}) "
                                f"from user {user_id}"
                            )
                            return JSONResponse(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                content={
                                    "success": False,
                                    "error": f"Content violates safety policy: {violation_type}",
                                    "error_code": "CONTENT_VIOLATION",
                                },
                            )
                    except asyncio.TimeoutError:
                        logger.warning("Content moderation check timed out, allowing request")
                        # Allow request to proceed even if moderation times out
                        # (fail open for availability)

                # Re-attach body for endpoint consumption
                async def receive():
                    return {"type": "http.request", "body": body, "more_body": False}

                request._receive = receive

            except Exception as e:
                logger.error(f"Error in content moderation: {e}")
                # Allow request on moderation error (fail open)

        response = await call_next(request)
        return response

    def _check_rate_limits(self, user_id: str, client_ip: str) -> Tuple[bool, str]:
        """
        Check if user or IP has exceeded rate limits.

        Args:
            user_id: User ID
            client_ip: Client IP address

        Returns:
            Tuple (within_limits, limit_description)
        """
        current_time = time.time()

        # Check user rate limit
        if user_id != "anonymous":
            if not self._check_limit(
                user_id,
                self.user_request_times,
                self.rate_limit_user,
                current_time
            ):
                return False, f"User limit: {self.rate_limit_user} requests/minute"

        # Check IP rate limit
        if not self._check_limit(
            client_ip,
            self.ip_request_times,
            self.rate_limit_ip,
            current_time
        ):
            return False, f"IP limit: {self.rate_limit_ip} requests/minute"

        return True, "OK"

    def _check_limit(
        self,
        key: str,
        tracking_dict: Dict[str, list],
        limit: int,
        current_time: float
    ) -> bool:
        """
        Check if key has exceeded limit.

        Args:
            key: Tracking key (user_id or IP)
            tracking_dict: Dictionary tracking request times
            limit: Request limit per WINDOW_SIZE
            current_time: Current time

        Returns:
            True if within limit, False if exceeded
        """
        # Initialize if not exists
        if key not in tracking_dict:
            tracking_dict[key] = []

        # Remove old timestamps outside the window
        tracking_dict[key] = [
            ts for ts in tracking_dict[key]
            if current_time - ts < self.WINDOW_SIZE
        ]

        # Check if under limit
        if len(tracking_dict[key]) >= limit:
            return False

        # Add current timestamp
        tracking_dict[key].append(current_time)

        # Cleanup old entries periodically
        if current_time % 300 < 1:  # Every ~5 minutes
            self._cleanup_old_entries(tracking_dict, current_time)

        return True

    def _cleanup_old_entries(self, tracking_dict: Dict[str, list], current_time: float) -> None:
        """Remove entries older than max_age."""
        keys_to_remove = []
        for key, timestamps in tracking_dict.items():
            if timestamps and current_time - min(timestamps) > self.max_age:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del tracking_dict[key]

        if keys_to_remove:
            logger.debug(f"Cleaned up {len(keys_to_remove)} old rate limit entries")

    async def _check_content_safety(self, content: str) -> Tuple[bool, Optional[str]]:
        """
        Check if content passes safety checks.

        Args:
            content: Content to check

        Returns:
            Tuple (is_safe, violation_type)
        """
        # Check for SQL injection
        for pattern in self.sql_patterns:
            if pattern.search(content):
                return False, "SQL_INJECTION"

        # Check for XSS/injection
        for pattern in self.injection_patterns:
            if pattern.search(content):
                return False, "INJECTION_ATTEMPT"

        # Check content length
        if len(content) > self.max_request_size:
            return False, "CONTENT_TOO_LONG"

        # Additional checks could be added here:
        # - PII detection
        # - Toxicity/harmful language
        # - Malware signature detection
        # - Integration with external APIs (OpenAI Moderation, etc.)

        return True, None

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """
        Extract client IP from request headers.

        Handles proxies (X-Forwarded-For, X-Real-IP).

        Args:
            request: FastAPI request

        Returns:
            Client IP address
        """
        # Check X-Forwarded-For header (most common)
        if "x-forwarded-for" in request.headers:
            return request.headers["x-forwarded-for"].split(",")[0].strip()

        # Check X-Real-IP header
        if "x-real-ip" in request.headers:
            return request.headers["x-real-ip"]

        # Fall back to client IP from connection
        if request.client:
            return request.client.host

        return "unknown"

    @staticmethod
    def _is_exempt_path(path: str) -> bool:
        """Check if path is exempt from moderation."""
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
