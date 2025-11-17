"""Pydantic schemas for message-related endpoints."""

from typing import Optional, List, Literal, Any
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MessageBase(BaseModel):
    """Base schema for messages."""

    content: str = Field(..., min_length=1, description="Message content")
    role: Literal["user", "assistant", "system"] = Field(
        ..., description="Message role: 'user', 'assistant', or 'system'"
    )


class MessageCreate(MessageBase):
    """Request to create a message."""

    pass


class MessageResponse(BaseModel):
    """Response with message data."""

    id: str = Field(..., description="Message ID")
    conversation_id: str = Field(..., description="Conversation ID")
    role: str = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    tool_calls: Optional[dict] = Field(None, description="Tool calls made by assistant")
    tool_results: Optional[dict] = Field(None, description="Results from tool calls")
    tokens_used: Optional[int] = Field(None, description="Number of tokens used")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "conversation_id": "e47ac10b-58cc-4372-a567-0e02b2c3d478",
                "role": "user",
                "content": "What is the weather like?",
                "tool_calls": None,
                "tool_results": None,
                "tokens_used": 10,
                "metadata": {},
                "created_at": "2025-11-18T10:30:00Z",
            }
        }


class MessageListResponse(BaseModel):
    """Response with list of messages."""

    items: List[MessageResponse] = Field(..., description="List of messages")
    total: int = Field(..., description="Total count")
    skip: int = Field(..., description="Number skipped")
    limit: int = Field(..., description="Limit applied")


class WebSocketMessage(BaseModel):
    """WebSocket message format for client->server communication."""

    type: Literal["message", "ping"] = Field(..., description="Message type")
    content: Optional[str] = Field(None, description="Message content (for type='message')")
    include_rag: bool = Field(default=True, description="Whether to include RAG context")
    user_id: Optional[str] = Field(None, description="User ID (required for first message)")


class ChatCompletionChunk(BaseModel):
    """Streaming response chunk for LLM output."""

    type: Literal[
        "message_chunk", "tool_call", "tool_result", "complete_state", "error", "heartbeat"
    ] = Field(..., description="Event type")
    content: Optional[str] = Field(None, description="Text content")
    tokens: Optional[int] = Field(None, description="Token count")
    tool_name: Optional[str] = Field(None, description="Tool name (for tool_call)")
    tool_input: Optional[dict] = Field(None, description="Tool input (for tool_call)")
    tool_result: Optional[Any] = Field(None, description="Tool result (for tool_result)")
    call_id: Optional[str] = Field(None, description="Tool call ID")
    final_message: Optional[str] = Field(None, description="Final message (for complete_state)")
    total_tokens: Optional[int] = Field(None, description="Total tokens (for complete_state)")
    error: Optional[str] = Field(None, description="Error message (for error type)")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "examples": [
                {
                    "type": "message_chunk",
                    "content": "Hello, I can help you with",
                    "tokens": 8,
                },
                {
                    "type": "tool_call",
                    "tool_name": "search_documents",
                    "tool_input": {"query": "Python"},
                    "call_id": "call_123",
                },
                {
                    "type": "tool_result",
                    "call_id": "call_123",
                    "tool_result": "Found 5 documents matching 'Python'",
                },
                {
                    "type": "complete_state",
                    "final_message": "I found some relevant documents for you.",
                    "total_tokens": 125,
                },
                {"type": "heartbeat"},
            ]
        }


class SendMessageSyncRequest(BaseModel):
    """Request to send a message synchronously."""

    content: str = Field(..., min_length=1, description="Message content")
    include_rag: bool = Field(
        default=True, description="Whether to include RAG search results"
    )


class SendMessageSyncResponse(BaseModel):
    """Response from synchronous message send."""

    message_id: str = Field(..., description="User message ID")
    response_id: str = Field(..., description="Assistant message ID")
    response: str = Field(..., description="Agent response content")
    tool_calls: Optional[dict] = Field(None, description="Tool calls made")
    tool_results: Optional[dict] = Field(None, description="Tool results")
    tokens_used: int = Field(..., description="Total tokens used")
    created_at: datetime = Field(..., description="Message creation time")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "message_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "response_id": "f47ac10b-58cc-4372-a567-0e02b2c3d480",
                "response": "The weather is sunny and warm.",
                "tool_calls": None,
                "tool_results": None,
                "tokens_used": 150,
                "created_at": "2025-11-18T10:30:00Z",
            }
        }
