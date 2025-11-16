"""Pydantic schemas for conversation-related endpoints."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field


class MessageSchema(BaseModel):
    """Schema for a message in a conversation."""

    role: str = Field(..., description="Message role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content")
    tool_calls: Optional[dict] = Field(None, description="Tool calls made by assistant")
    tool_results: Optional[dict] = Field(None, description="Results from tool calls")
    tokens_used: Optional[int] = Field(None, description="Number of tokens used")
    created_at: datetime = Field(..., description="Message creation timestamp")


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""

    title: str = Field(..., min_length=1, max_length=255, description="Conversation title")
    system_prompt: str = Field(
        ...,
        min_length=1,
        description="System prompt for the conversation",
    )
    model: str = Field(
        default="claude-sonnet-4-5-20250929",
        description="Model to use for responses",
    )
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")


class UpdateConversationRequest(BaseModel):
    """Request to update a conversation."""

    title: Optional[str] = Field(None, min_length=1, max_length=255, description="New title")
    summary: Optional[str] = Field(None, description="Conversation summary")


class ConversationResponse(BaseModel):
    """Response with conversation data."""

    id: str = Field(..., description="Conversation ID")
    user_id: str = Field(..., description="User ID")
    title: str = Field(..., description="Conversation title")
    summary: Optional[str] = Field(None, description="Conversation summary")
    model: str = Field(..., description="Model used")
    message_count: int = Field(default=0, description="Number of messages")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class ConversationListResponse(BaseModel):
    """Response with list of conversations."""

    items: List[ConversationResponse] = Field(..., description="List of conversations")
    total: int = Field(..., description="Total count")
    skip: int = Field(..., description="Number skipped")
    limit: int = Field(..., description="Limit applied")


class SendMessageRequest(BaseModel):
    """Request to send a message in a conversation."""

    content: str = Field(..., min_length=1, description="Message content")
    include_rag: bool = Field(
        default=True,
        description="Whether to include RAG search results",
    )


class ConversationHistoryResponse(BaseModel):
    """Response with conversation history."""

    conversation_id: str = Field(..., description="Conversation ID")
    messages: List[MessageSchema] = Field(..., description="List of messages")
    total_tokens: int = Field(default=0, description="Total tokens used")


class ConversationContextResponse(BaseModel):
    """Response with conversation context for agent."""

    conversation_id: str = Field(..., description="Conversation ID")
    system_prompt: str = Field(..., description="System prompt")
    model: str = Field(..., description="Model name")
    messages: List[dict] = Field(..., description="Recent messages")
    message_count: int = Field(..., description="Total messages in conversation")
