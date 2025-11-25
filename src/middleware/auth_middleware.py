"""Authentication middleware for JWT token verification."""

import asyncio
import logging
import os
import time
from typing import Optional, List
from functools import lru_cache

import jwt
from fastapi import HTTPException, Request, status, Depends
from jwt import ExpiredSignatureError, InvalidTokenError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for JWT authentication with performance optimization.

    Verifies JWT tokens in Authorization header with caching and timeouts.
    Performance target: <10ms per auth check
    """

    # Public endpoints that don't require authentication
    PUBLIC_ENDPOINTS = {
        "/health",
        "/health/full",
        "/api/docs",
        "/api/openapi.json",
        "/api/redoc",
        "/api/v1/docs",
        "/ws",  # WebSocket endpoint - has its own authentication via user_id
    }

    def __init__(self, app):
        """Initialize middleware with configuration."""
        super().__init__(app)
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithms: List[str] = [
            alg.strip()
            for alg in os.getenv("JWT_ALGORITHMS", "HS256").split(",")
            if alg.strip()
        ]
        self.expected_audience = os.getenv("JWT_AUDIENCE")
        self.expected_issuer = os.getenv("JWT_ISSUER")
        self.auth_timeout_ms = float(os.getenv("AUTH_TIMEOUT_MS", "50"))

        # Token cache: {token_hash: (user_id, expiry_time)}
        self._token_cache = {}
        self._cache_ttl = 300  # 5 minutes cache validity
        self._cache_cleanup_interval = 300  # Cleanup every 5 minutes
        self._last_cleanup = time.time()

    async def dispatch(self, request: Request, call_next):
        """
        Process request and verify authentication with timeout protection.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response

        Raises:
            JSONResponse: 401 for authentication failures
        """
        # Skip authentication for public endpoints
        if self._is_public_endpoint(request.url.path):
            return await call_next(request)

        # Get authorization header
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            logger.warning(f"Missing or invalid Authorization header for {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "success": False,
                    "error": "Missing or invalid authorization token",
                    "error_code": "UNAUTHORIZED",
                },
            )

        token = auth_header.split(" ", 1)[1] if " " in auth_header else ""

        # Verify token with timeout
        try:
            start_time = time.time()
            user_id = await asyncio.wait_for(
                self._async_verify_token(token),
                timeout=self.auth_timeout_ms / 1000.0
            )
            elapsed_ms = (time.time() - start_time) * 1000

            if not user_id:
                logger.warning(f"Invalid token for {request.url.path}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "success": False,
                        "error": "Invalid token",
                        "error_code": "INVALID_TOKEN",
                    },
                )

            # Add user_id to request state for downstream middleware
            request.state.user_id = user_id
            request.state.auth_time_ms = elapsed_ms

            response = await call_next(request)
            return response

        except asyncio.TimeoutError:
            logger.error(f"Authentication timeout for {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "success": False,
                    "error": "Authentication timeout",
                    "error_code": "AUTH_TIMEOUT",
                },
            )

    async def _async_verify_token(self, token: str) -> Optional[str]:
        """
        Async wrapper for token verification.

        Args:
            token: JWT token

        Returns:
            User ID if valid, None otherwise
        """
        return self.verify_token(token)

    def verify_token(self, token: str) -> Optional[str]:
        """
        Verify JWT token and extract user ID with caching.

        Performance optimizations:
        - Token cache to avoid repeated verification
        - Cache cleanup to prevent memory leaks
        - Fast path for cached tokens

        Args:
            token: JWT token

        Returns:
            User ID if valid, None otherwise
        """
        if not token:
            return None

        # Check cache first
        token_hash = hash(token)
        if token_hash in self._token_cache:
            user_id, expiry_time = self._token_cache[token_hash]
            if time.time() < expiry_time:
                return user_id
            else:
                # Cache expired, remove it
                del self._token_cache[token_hash]

        # Periodic cache cleanup
        if time.time() - self._last_cleanup > self._cache_cleanup_interval:
            self._cleanup_token_cache()

        try:
            decode_kwargs = {
                "algorithms": self.algorithms,
                "options": {"require": ["exp", "sub"]},
            }
            if self.expected_audience:
                decode_kwargs["audience"] = self.expected_audience
            if self.expected_issuer:
                decode_kwargs["issuer"] = self.expected_issuer

            payload = jwt.decode(token, self.secret_key, **decode_kwargs)
            user_id = payload.get("sub")
            if not user_id:
                logger.error("JWT missing subject claim")
                return None

            # Cache the result
            token_hash = hash(token)
            cache_expiry = time.time() + self._cache_ttl
            self._token_cache[token_hash] = (str(user_id), cache_expiry)

            return str(user_id)

        except ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except InvalidTokenError as exc:
            logger.error(f"Invalid JWT token: {exc}")
            return None
        except Exception as exc:
            logger.error(f"Token verification error: {exc}")
            return None

    def _cleanup_token_cache(self) -> None:
        """Remove expired entries from token cache."""
        current_time = time.time()
        expired_tokens = [
            token_hash
            for token_hash, (_, expiry_time) in self._token_cache.items()
            if current_time >= expiry_time
        ]
        for token_hash in expired_tokens:
            del self._token_cache[token_hash]
        self._last_cleanup = time.time()
        if expired_tokens:
            logger.debug(f"Cleaned up {len(expired_tokens)} expired tokens from cache")

    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public (no auth required)."""
        public_paths = {
            "/health",
            "/health/full",
            "/api/docs",
            "/api/openapi.json",
            "/api/redoc",
            "/api/v1/docs",
            "/metrics",  # Prometheus metrics endpoint
        }

        if path in public_paths:
            return True

        # Check path prefixes
        if path.startswith("/api/docs") or path.startswith("/api/openapi"):
            return True

        # WebSocket endpoints - authenticated by the websocket handler itself
        if path.startswith("/ws"):
            return True

        return False


_auth_helper_instance: Optional[AuthenticationMiddleware] = None


async def _noop_app(scope, receive, send):
    """Minimal ASGI callable used solely for token verification helper."""
    return None


def _get_auth_helper() -> AuthenticationMiddleware:
    """Lazily construct AuthenticationMiddleware for token verification reuse."""
    global _auth_helper_instance
    if _auth_helper_instance is None:
        _auth_helper_instance = AuthenticationMiddleware(_noop_app)
    return _auth_helper_instance


def verify_jwt_token(token: str) -> Optional[str]:
    """Expose JWT verification for dependencies that can't run the middleware."""
    helper = _get_auth_helper()
    return helper.verify_token(token)


async def get_current_user(request: Request) -> str:
    """
    FastAPI dependency to extract authenticated user ID from request.

    This function is used as a Depends() parameter in route handlers to
    automatically extract and validate the user_id from the request state.

    The AuthenticationMiddleware must be registered to populate request.state.user_id.

    Args:
        request: FastAPI request object with state populated by AuthenticationMiddleware

    Returns:
        user_id: The authenticated user's ID string

    Raises:
        HTTPException: 401 Unauthorized if user is not authenticated
    """
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated",
        )
    return user_id
