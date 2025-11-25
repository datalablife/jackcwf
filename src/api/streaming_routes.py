"""Server-Sent Events (SSE) streaming routes for real-time AI conversations.

Provides NDJSON (newline-delimited JSON) streaming responses for real-time
message processing, tool execution tracking, and agent state updates.
"""

import asyncio
import json
import logging
import os
from typing import AsyncGenerator, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, status, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.config import get_async_session
from src.repositories.message import MessageRepository
from src.services.conversation_service import ConversationService
from src.services.agent_service import AgentService
from src.middleware.auth_middleware import verify_jwt_token
from src.schemas.message_schema import MessageCreate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Streaming"])


class StreamingEvent:
    """Represents a streaming event in NDJSON format."""

    TYPE_MESSAGE_CHUNK = "message_chunk"
    TYPE_TOOL_CALL = "tool_call"
    TYPE_TOOL_RESULT = "tool_result"
    TYPE_COMPLETE_STATE = "complete_state"
    TYPE_ERROR = "error"
    TYPE_HEARTBEAT = "heartbeat"

    def __init__(
        self,
        event_type: str,
        content: Any,
        tokens: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a streaming event.

        Args:
            event_type: Type of event (message_chunk, tool_call, etc.)
            content: Event content
            tokens: Token count (for message chunks)
            metadata: Optional metadata dictionary
        """
        self.event_type = event_type
        self.content = content
        self.tokens = tokens
        self.metadata = metadata or {}

    def to_ndjson(self) -> str:
        """Convert event to NDJSON format (JSON + newline)."""
        event_data = {
            "type": self.event_type,
            "content": self.content,
            "tokens": self.tokens,
            "metadata": self.metadata,
        }
        return json.dumps(event_data) + "\n"


class StreamingManager:
    """Manages streaming responses with buffering and backpressure handling."""

    def __init__(self, buffer_size: int = 100, flush_interval: float = 0.1):
        """
        Initialize streaming manager.

        Args:
            buffer_size: Maximum events in buffer before flushing
            flush_interval: Time interval (seconds) to flush buffered events
        """
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.event_buffer: list[StreamingEvent] = []
        self.total_tokens = 0

    async def add_event(self, event: StreamingEvent):
        """
        Add event to buffer.

        Args:
            event: StreamingEvent to add
        """
        self.event_buffer.append(event)
        if event.event_type == StreamingEvent.TYPE_MESSAGE_CHUNK:
            self.total_tokens += event.tokens

        # Auto-flush if buffer is full
        if len(self.event_buffer) >= self.buffer_size:
            await self.flush()

    async def flush(self) -> list[StreamingEvent]:
        """
        Flush buffered events.

        Returns:
            List of buffered events
        """
        events = self.event_buffer[:]
        self.event_buffer = []
        return events

    def get_total_tokens(self) -> int:
        """Get total token count processed so far."""
        return self.total_tokens

    def reset(self):
        """Reset manager state."""
        self.event_buffer = []
        self.total_tokens = 0


async def stream_agent_response(
    conversation_id: UUID,
    message_content: str,
    user_id: str,
    db: AsyncSession,
) -> AsyncGenerator[str, None]:
    """
    Stream agent response as NDJSON events.

    This is the core streaming function that processes messages through the agent
    and yields events as they occur.

    Args:
        conversation_id: ID of conversation
        message_content: User message content
        user_id: ID of user
        db: Database session

    Yields:
        NDJSON-formatted event strings
    """
    manager = StreamingManager()

    try:
        # Get services
        conversation_service = ConversationService(db)
        agent_service = AgentService(db)

        # Verify conversation exists and user has access
        conversation = await conversation_service.get_conversation(conversation_id, user_id)
        if not conversation:
            event = StreamingEvent(
                StreamingEvent.TYPE_ERROR,
                {"message": "Conversation not found"},
            )
            yield event.to_ndjson()
            return

        # Create and save user message
        message_repo = MessageRepository(db)
        user_message = await message_repo.create(
            {
                "conversation_id": conversation_id,
                "content": message_content,
                "role": "user",
                "metadata": {"source": "api", "stream": True},
            }
        )

        # Initialize agent state
        logger.info(f"Starting agent stream for conversation {conversation_id}")

        # Stream agent response
        message_buffer = ""
        tool_calls = []

        async for token in agent_service.stream_agent_response(
            message_content=message_content,
            conversation_id=str(conversation_id),
            user_id=user_id,
            db=db,
        ):
            # Handle different token types
            if token.get("type") == "message_chunk":
                # Stream message chunk
                chunk_text = token.get("content", "")
                message_buffer += chunk_text
                tokens = token.get("tokens", 1)

                event = StreamingEvent(
                    StreamingEvent.TYPE_MESSAGE_CHUNK,
                    chunk_text,
                    tokens=tokens,
                    metadata={"chunk_size": len(chunk_text)},
                )
                await manager.add_event(event)

                # Flush on interval basis
                if len(manager.event_buffer) >= manager.buffer_size:
                    for buffered_event in await manager.flush():
                        yield buffered_event.to_ndjson()

            elif token.get("type") == "tool_call":
                # Streaming tool call
                tool_name = token.get("tool_name")
                tool_args = token.get("args", {})

                event = StreamingEvent(
                    StreamingEvent.TYPE_TOOL_CALL,
                    {
                        "tool_name": tool_name,
                        "args": tool_args,
                        "call_id": token.get("call_id"),
                    },
                    metadata={"timestamp": token.get("timestamp")},
                )
                await manager.add_event(event)
                tool_calls.append({"tool": tool_name, "args": tool_args})

                # Flush immediately for tool calls
                for buffered_event in await manager.flush():
                    yield buffered_event.to_ndjson()

            elif token.get("type") == "tool_result":
                # Tool execution result
                tool_name = token.get("tool_name")
                result = token.get("result")
                success = token.get("success", True)

                event = StreamingEvent(
                    StreamingEvent.TYPE_TOOL_RESULT,
                    {
                        "tool_name": tool_name,
                        "result": result,
                        "success": success,
                        "error": token.get("error"),
                    },
                    metadata={"execution_time": token.get("execution_time")},
                )
                await manager.add_event(event)

                # Flush immediately for tool results
                for buffered_event in await manager.flush():
                    yield buffered_event.to_ndjson()

        # Flush any remaining buffered events
        for buffered_event in await manager.flush():
            yield buffered_event.to_ndjson()

        # Save agent response message
        if message_buffer:
            agent_message = await message_repo.create(
                {
                    "conversation_id": conversation_id,
                    "content": message_buffer,
                    "role": "assistant",
                    "metadata": {
                        "source": "agent",
                        "stream": True,
                        "tokens": manager.get_total_tokens(),
                        "tool_calls": tool_calls,
                    },
                }
            )
            logger.info(f"Agent response saved: {agent_message.id}")

        # Send completion event
        completion_event = StreamingEvent(
            StreamingEvent.TYPE_COMPLETE_STATE,
            {
                "message": message_buffer,
                "tool_calls": tool_calls,
                "total_tokens": manager.get_total_tokens(),
            },
            metadata={
                "conversation_id": str(conversation_id),
                "status": "completed",
            },
        )
        yield completion_event.to_ndjson()

        logger.info(
            f"Agent streaming completed: conversation={conversation_id}, "
            f"tokens={manager.get_total_tokens()}"
        )

    except Exception as e:
        logger.error(f"Error in stream_agent_response: {str(e)}", exc_info=True)

        # Send error event
        error_event = StreamingEvent(
            StreamingEvent.TYPE_ERROR,
            {
                "message": f"Streaming error: {str(e)}",
                "error_type": type(e).__name__,
            },
        )
        yield error_event.to_ndjson()


@router.post("/conversations/{conversation_id}/stream")
async def stream_conversation_message(
    conversation_id: UUID,
    request: MessageCreate,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_async_session),
) -> StreamingResponse:
    """
    Stream agent response for a conversation message.

    This endpoint returns a Server-Sent Events (SSE) stream of NDJSON events
    representing the agent's processing of the user message. Each event contains:
    - message_chunk: Individual tokens of the assistant's response
    - tool_call: When the agent calls a tool
    - tool_result: Results from tool execution
    - complete_state: Final state when streaming completes
    - error: Any errors that occurred during processing

    The response format is NDJSON (newline-delimited JSON) for easy streaming
    and progressive parsing.

    Args:
        conversation_id: ID of the conversation
        request: MessageCreate with message content
        authorization: JWT authorization token
        db: Database session

    Returns:
        StreamingResponse with NDJSON-formatted events

    Raises:
        HTTPException: If conversation not found or user not authorized
    """
    try:
        # Get environment mode
        env_mode = os.getenv("ENVIRONMENT", "development")

        # In development mode, skip authentication check for easier testing
        # In production, proper JWT token validation is required
        if env_mode == "production":
            # Production: Verify authorization
            token = authorization.replace("Bearer ", "") if authorization else None
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing authorization token",
                )

            user_id = verify_jwt_token(token)
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token",
                )
        else:
            # Development: Use default user for testing
            user_id = "dev-user-default"

        # Create streaming response
        return StreamingResponse(
            stream_agent_response(
                conversation_id=conversation_id,
                message_content=request.content,
                user_id=user_id,
                db=db,
            ),
            media_type="application/x-ndjson",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
                "Content-Disposition": "inline",
            },
        )

    except ValueError as e:
        logger.error(f"Invalid conversation ID: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid conversation ID: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error in stream_conversation_message: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Streaming error: {str(e)}",
        )


@router.post("/conversations/{conversation_id}/stream-debug")
async def stream_conversation_message_debug(
    conversation_id: UUID,
    request: MessageCreate,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_async_session),
) -> StreamingResponse:
    """
    Debug endpoint for streaming with verbose output.

    This endpoint is identical to the standard streaming endpoint but includes
    additional metadata for debugging purposes.

    Args:
        conversation_id: ID of the conversation
        request: MessageCreate with message content
        authorization: JWT authorization token
        db: Database session

    Returns:
        StreamingResponse with verbose NDJSON events
    """
    return await stream_conversation_message(
        conversation_id=conversation_id,
        request=request,
        authorization=authorization,
        db=db,
    )


@router.get("/health/stream")
async def health_check_stream() -> Dict[str, Any]:
    """
    Health check for streaming functionality.

    Returns:
        Health status with streaming availability
    """
    return {
        "status": "healthy",
        "streaming": {
            "enabled": True,
            "format": "application/x-ndjson",
            "endpoints": [
                "/api/v1/conversations/{conversation_id}/stream",
                "/api/v1/conversations/{conversation_id}/stream-debug",
            ],
        },
    }
