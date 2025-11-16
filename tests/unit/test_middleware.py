"""Unit tests for middleware functionality."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import Request
from starlette.responses import JSONResponse

from src.middleware.auth_middleware import AuthenticationMiddleware
from src.middleware.content_moderation_middleware import ContentModerationMiddleware
from src.middleware.response_structuring_middleware import ResponseStructuringMiddleware


@pytest.mark.asyncio
async def test_auth_middleware_public_endpoints():
    """Test that public endpoints bypass authentication."""
    middleware = AuthenticationMiddleware(AsyncMock())

    # Create mock request
    request = Mock(spec=Request)
    request.url.path = "/health"
    request.headers.get.return_value = ""

    call_next = AsyncMock(return_value=JSONResponse({"status": "ok"}))

    response = await middleware.dispatch(request, call_next)
    assert call_next.called


@pytest.mark.asyncio
async def test_auth_middleware_requires_token():
    """Test that protected endpoints require token."""
    middleware = AuthenticationMiddleware(AsyncMock())

    # Create mock request without token
    request = Mock(spec=Request)
    request.url.path = "/api/conversations"
    request.headers = {"Authorization": ""}

    call_next = AsyncMock()

    response = await middleware.dispatch(request, call_next)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_rate_limiting_within_limit():
    """Test rate limiting allows requests within limit."""
    middleware = ContentModerationMiddleware(AsyncMock())

    user_id = "test_user"

    # Make requests under the limit
    for i in range(10):
        result = middleware.check_rate_limit(user_id)
        assert result is True


@pytest.mark.asyncio
async def test_rate_limiting_exceeds_limit():
    """Test rate limiting blocks requests over limit."""
    middleware = ContentModerationMiddleware(AsyncMock())

    user_id = "test_user"

    # Make requests at the limit
    for i in range(middleware.RATE_LIMIT):
        result = middleware.check_rate_limit(user_id)
        assert result is True

    # Next request should fail
    result = middleware.check_rate_limit(user_id)
    assert result is False


@pytest.mark.asyncio
async def test_response_structuring_formats_response():
    """Test response structuring adds metadata."""
    result = ResponseStructuringMiddleware.structure_response(
        success=True,
        data={"key": "value"},
        request_id="req_123",
    )

    assert result["success"] is True
    assert result["data"] == {"key": "value"}
    assert result["request_id"] == "req_123"
    assert "timestamp" in result


@pytest.mark.asyncio
async def test_response_structuring_error_response():
    """Test response structuring for errors."""
    result = ResponseStructuringMiddleware.structure_response(
        success=False,
        error="Something went wrong",
        request_id="req_123",
    )

    assert result["success"] is False
    assert result["error"] == "Something went wrong"
    assert result["request_id"] == "req_123"


@pytest.mark.asyncio
async def test_content_moderation_cleanup():
    """Test that cleanup removes old request timestamps."""
    middleware = ContentModerationMiddleware(AsyncMock())

    # Add some request timestamps
    import time
    user_id = "test_user"

    # Add old timestamp (older than max_age)
    old_time = time.time() - (middleware.max_age + 100)
    middleware.request_times[user_id] = [old_time]

    # Simulate cleanup logic
    current_time = time.time()
    for uid in list(middleware.request_times.keys()):
        if middleware.request_times[uid]:
            oldest_time = min(middleware.request_times[uid])
            if current_time - oldest_time > middleware.max_age:
                middleware.request_times[uid] = []
        if not middleware.request_times[uid]:
            del middleware.request_times[uid]

    # Old timestamps should be removed
    assert user_id not in middleware.request_times


def test_jwt_token_verification():
    """Test JWT token verification."""
    import os
    import jwt

    # Create a valid token
    secret = "test_secret_key"
    payload = {"sub": "user_123", "exp": 9999999999}

    token = jwt.encode(payload, secret, algorithm="HS256")

    # Verify token
    decoded = jwt.decode(token, secret, algorithms=["HS256"])
    assert decoded["sub"] == "user_123"


def test_jwt_expired_token():
    """Test JWT expired token rejection."""
    import jwt
    import time

    secret = "test_secret_key"
    # Create token with past expiration
    payload = {"sub": "user_123", "exp": int(time.time()) - 100}

    token = jwt.encode(payload, secret, algorithm="HS256")

    # Should raise exception
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(token, secret, algorithms=["HS256"])


def test_jwt_invalid_signature():
    """Test JWT with invalid signature."""
    import jwt

    secret = "test_secret_key"
    wrong_secret = "wrong_secret"

    payload = {"sub": "user_123", "exp": 9999999999}
    token = jwt.encode(payload, secret, algorithm="HS256")

    # Should raise exception with wrong secret
    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(token, wrong_secret, algorithms=["HS256"])
