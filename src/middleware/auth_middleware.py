"""Authentication middleware for JWT token verification."""

import logging
import os
from typing import Optional, List

import jwt
from fastapi import HTTPException, Request, status
from jwt import ExpiredSignatureError, InvalidTokenError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for JWT authentication.

    Verifies JWT tokens in Authorization header.
    """

    # Public endpoints that don't require authentication
    PUBLIC_ENDPOINTS = {
        "/health",
        "/api/docs",
        "/api/openapi.json",
        "/api/redoc",
    }

    def __init__(self, app):
        """Initialize middleware."""
        super().__init__(app)
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithms: List[str] = [
            alg.strip()
            for alg in os.getenv("JWT_ALGORITHMS", "HS256").split(",")
            if alg.strip()
        ]
        self.expected_audience = os.getenv("JWT_AUDIENCE")
        self.expected_issuer = os.getenv("JWT_ISSUER")

    async def dispatch(self, request: Request, call_next):
        """
        Process request and verify authentication.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response
        """
        # Skip authentication for public endpoints
        if request.url.path in self.PUBLIC_ENDPOINTS or request.url.path.startswith("/api/docs"):
            return await call_next(request)

        # Skip authentication for health checks
        if request.url.path == "/health":
            return await call_next(request)

        # Get authorization header
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            logger.warning(f"Missing or invalid Authorization header for {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing or invalid authorization token"},
            )

        token = auth_header.split(" ")[1]

        # Verify token (simplified - in production use proper JWT verification)
        user_id = self.verify_token(token)
        if not user_id:
            logger.warning(f"Invalid token for {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token"},
            )

        # Add user_id to request state
        request.state.user_id = user_id

        response = await call_next(request)
        return response

    def verify_token(self, token: str) -> Optional[str]:
        """
        Verify JWT token and extract user ID.

        Args:
            token: JWT token

        Returns:
            User ID if valid, None otherwise
        """
        if not token:
            return None

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

            return str(user_id)

        except ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except InvalidTokenError as exc:
            logger.error(f"Invalid JWT token: {exc}")
            return None
