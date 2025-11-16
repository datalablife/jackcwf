"""Memory injection middleware for conversation history and RAG context."""

import logging
import json

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class MemoryInjectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware for injecting conversation history and RAG context.

    Enriches requests with:
    - Recent conversation history
    - RAG search results
    - Conversation metadata
    """

    def __init__(self, app):
        """Initialize middleware."""
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and inject memory context.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response
        """
        # Check if this is a message sending request
        if request.method == "POST" and "/messages" in request.url.path:
            try:
                # Read request body
                body = await request.body()
                if body:
                    body_data = json.loads(body)

                    # Store in request state for later use in handlers
                    request.state.memory_context = {
                        "include_rag": body_data.get("include_rag", True),
                        "message_content": body_data.get("content", ""),
                    }

                    # Create new request with consumed body
                    async def receive():
                        return {"type": "http.request", "body": body, "more_body": False}

                    request._receive = receive

            except Exception as e:
                logger.warning(f"Error injecting memory context: {str(e)}")

        response = await call_next(request)
        return response
