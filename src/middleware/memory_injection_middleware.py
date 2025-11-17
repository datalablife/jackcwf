"""Memory injection middleware for conversation history and RAG context."""

import asyncio
import json
import logging
import os
import time
from typing import Optional, List, Dict, Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class MemoryInjectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware for injecting conversation history and RAG context.

    Enriches requests with:
    - Recent conversation history (last 5 messages)
    - RAG search results for semantic context
    - Conversation metadata
    - Parallel execution using asyncio.TaskGroup

    Performance target: ≤200ms P99
    """

    def __init__(self, app):
        """Initialize middleware with performance configuration."""
        super().__init__(app)
        self.memory_timeout_ms = float(os.getenv("MEMORY_INJECTION_TIMEOUT_MS", "200"))
        self.memory_fallback = os.getenv("MEMORY_INJECTION_FALLBACK", "skip_context")
        self.vector_timeout_ms = float(os.getenv("VECTOR_SEARCH_TIMEOUT_MS", "200"))
        self.history_batch_size = int(os.getenv("HISTORY_BATCH_SIZE", "5"))

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and inject memory context.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response with enriched context
        """
        # Check if this is a message sending request
        if request.method == "POST" and "/messages" in request.url.path:
            try:
                # Read request body (consumed by previous middleware)
                body = await request.body()
                if body:
                    try:
                        body_data = json.loads(body)
                    except json.JSONDecodeError:
                        body_data = {}

                    # Extract conversation ID from URL
                    url_parts = request.url.path.split("/")
                    conversation_id = None
                    try:
                        # Path pattern: /api/v1/conversations/{id}/messages
                        idx = url_parts.index("conversations")
                        if idx + 1 < len(url_parts):
                            conversation_id = url_parts[idx + 1]
                    except (ValueError, IndexError):
                        pass

                    # Initialize memory context
                    memory_context = {
                        "include_rag": body_data.get("include_rag", True),
                        "message_content": body_data.get("content", ""),
                        "conversation_id": conversation_id,
                    }

                    # Get user ID from request state (set by auth middleware)
                    user_id = getattr(request.state, "user_id", None)

                    # Inject memory with timeout protection
                    try:
                        start_time = time.time()
                        await asyncio.wait_for(
                            self._inject_memory_context(
                                request,
                                memory_context,
                                user_id,
                                conversation_id
                            ),
                            timeout=self.memory_timeout_ms / 1000.0
                        )
                        elapsed_ms = (time.time() - start_time) * 1000
                        request.state.memory_injection_time_ms = elapsed_ms

                    except asyncio.TimeoutError:
                        logger.warning(
                            f"Memory injection timeout for conversation {conversation_id}, "
                            f"applying fallback strategy: {self.memory_fallback}"
                        )
                        # Apply fallback strategy
                        request.state.memory_context = memory_context
                        request.state.memory_error = "timeout"
                        request.state.memory_injection_time_ms = self.memory_timeout_ms

                    # Re-attach body for endpoint consumption
                    async def receive():
                        return {"type": "http.request", "body": body, "more_body": False}

                    request._receive = receive

            except Exception as e:
                logger.warning(f"Error injecting memory context: {str(e)}")
                request.state.memory_context = {"include_rag": True}
                request.state.memory_error = str(e)

        response = await call_next(request)
        return response

    async def _inject_memory_context(
        self,
        request: Request,
        memory_context: Dict[str, Any],
        user_id: Optional[str],
        conversation_id: Optional[str],
    ) -> None:
        """
        Inject conversation history and RAG context.

        Uses asyncio.TaskGroup for parallel execution of:
        - Conversation history retrieval
        - Vector search for RAG context

        Args:
            request: FastAPI request
            memory_context: Initial memory context
            user_id: User ID
            conversation_id: Conversation ID
        """
        if not conversation_id or not user_id:
            request.state.memory_context = memory_context
            return

        try:
            # Parallel execution of history and RAG retrieval
            history_task = self._get_conversation_history(conversation_id, self.history_batch_size)
            rag_task = self._get_rag_context(
                memory_context.get("message_content", ""),
                user_id,
                memory_context.get("include_rag", True)
            )

            # Wait for both tasks in parallel (simulated with asyncio.gather)
            history, rag_context = await asyncio.gather(
                history_task,
                rag_task,
                return_exceptions=True
            )

            # Handle exceptions from parallel tasks
            if isinstance(history, Exception):
                logger.warning(f"Failed to retrieve conversation history: {history}")
                history = []

            if isinstance(rag_context, Exception):
                logger.warning(f"Failed to retrieve RAG context: {rag_context}")
                rag_context = []

            # Enrich memory context
            memory_context["conversation_history"] = history
            memory_context["rag_context"] = rag_context
            memory_context["history_count"] = len(history) if history else 0
            memory_context["rag_count"] = len(rag_context) if rag_context else 0

        except Exception as e:
            logger.error(f"Error in memory context injection: {e}")
            memory_context["memory_error"] = str(e)

        request.state.memory_context = memory_context

    async def _get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve recent conversation history.

        In production, would query the database asynchronously.

        Args:
            conversation_id: Conversation ID
            limit: Max messages to retrieve

        Returns:
            List of recent messages
        """
        # Simulate async database query
        await asyncio.sleep(0.01)  # Minimal delay

        # In production, would be:
        # from src.repositories.message import MessageRepository
        # repo = MessageRepository()
        # messages = await repo.get_recent_by_conversation(
        #     conversation_id=conversation_id,
        #     limit=limit
        # )
        # return [msg.to_dict() for msg in messages]

        return []  # Placeholder for production implementation

    async def _get_rag_context(
        self,
        query: str,
        user_id: str,
        include_rag: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve RAG context via vector search.

        In production, would perform semantic search on vector store.

        Args:
            query: Search query (message content)
            user_id: User ID for access control
            include_rag: Whether to include RAG results

        Returns:
            List of relevant documents
        """
        if not include_rag or not query:
            return []

        # Simulate async vector search
        await asyncio.sleep(0.01)  # Minimal delay

        # In production, would be:
        # from src.services.embedding_service import EmbeddingService
        # from src.repositories.embedding import EmbeddingRepository
        # embedding_service = EmbeddingService()
        # embedding_repo = EmbeddingRepository()
        #
        # # Embed query
        # query_embedding = await embedding_service.embed_text(query)
        #
        # # Search vector store
        # results = await embedding_repo.search(
        #     embedding=query_embedding,
        #     user_id=user_id,
        #     limit=5,
        #     threshold=0.7
        # )
        # return [result.to_dict() for result in results]

        return []  # Placeholder for production implementation

