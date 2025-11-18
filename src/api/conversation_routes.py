"""API routes for conversation management."""

import logging
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.config import get_async_session
from src.services.conversation_service import ConversationService
from src.services.cached_rag import get_rag_service
from src.schemas.conversation_schema import (
    CreateConversationRequest,
    UpdateConversationRequest,
    ConversationResponse,
    ConversationListResponse,
    SendMessageRequest,
    ConversationHistoryResponse,
    ConversationContextResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/conversations", tags=["Conversations"])


# ============================================================================
# Schemas for Cached RAG Endpoints
# ============================================================================

class ChatRequest(BaseModel):
    """Chat request with optional cache control."""
    message: str
    enable_cache: bool = True
    doc_ids: Optional[list[int]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "message": "What is RAG?",
                "enable_cache": True,
                "doc_ids": None
            }
        }


class ChatResponse(BaseModel):
    """Chat response with cache metadata."""
    response: str
    cached: bool
    latency_ms: float
    cache_distance: Optional[float] = None
    model: str = "claude-3-5-sonnet-20241022"

    class Config:
        json_schema_extra = {
            "example": {
                "response": "RAG (Retrieval-Augmented Generation) is...",
                "cached": False,
                "latency_ms": 850.5,
                "cache_distance": None,
                "model": "claude-3-5-sonnet-20241022"
            }
        }


async def get_current_user(request: Request) -> str:
    """Extract user ID from request via FastAPI dependency injection."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated",
        )
    return user_id


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request_data: CreateConversationRequest,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user),
):
    """
    Create a new conversation.

    **Parameters:**
    - **title**: Conversation title
    - **system_prompt**: System prompt for the AI
    - **model**: Model to use (optional, default: claude-sonnet-4-5-20250929)
    - **metadata**: Additional metadata (optional)

    **Returns:**
    - Conversation details with ID and timestamps
    """
    try:
        service = ConversationService(session)

        conversation = await service.create_conversation(
            user_id=user_id,
            title=request_data.title,
            system_prompt=request_data.system_prompt,
            model=request_data.model,
            metadata=request_data.metadata,
        )

        return ConversationResponse(
            id=str(conversation.id),
            user_id=conversation.user_id,
            title=conversation.title,
            summary=conversation.summary,
            model=conversation.model,
            message_count=0,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )

    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation",
        )


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    skip: int = 0,
    limit: int = 10,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user),
):
    """
    List conversations for the user.

    **Parameters:**
    - **skip**: Number of conversations to skip (default: 0)
    - **limit**: Maximum conversations to return (default: 10)

    **Returns:**
    - List of conversations with pagination info
    """
    try:
        service = ConversationService(session)

        conversations, total = await service.list_conversations(
            user_id=user_id,
            skip=skip,
            limit=limit,
        )

        items = [
            ConversationResponse(
                id=str(conv.id),
                user_id=conv.user_id,
                title=conv.title,
                summary=conv.summary,
                model=conv.model,
                message_count=await service.msg_repo.get_conversation_message_count(conv.id),
                created_at=conv.created_at,
                updated_at=conv.updated_at,
            )
            for conv in conversations
        ]

        return ConversationListResponse(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
        )

    except Exception as e:
        logger.error(f"Error listing conversations: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list conversations",
        )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user),
):
    """
    Get a specific conversation.

    **Parameters:**
    - **conversation_id**: Conversation UUID

    **Returns:**
    - Conversation details
    """
    try:
        service = ConversationService(session)

        conversation = await service.conv_repo.get_user_conversation(user_id, conversation_id)

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        message_count = await service.msg_repo.get_conversation_message_count(conversation_id)

        return ConversationResponse(
            id=str(conversation.id),
            user_id=conversation.user_id,
            title=conversation.title,
            summary=conversation.summary,
            model=conversation.model,
            message_count=message_count,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversation",
        )


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    request_data: UpdateConversationRequest,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user),
):
    """
    Update a conversation.

    **Parameters:**
    - **conversation_id**: Conversation UUID
    - **title**: New title (optional)
    - **summary**: New summary (optional)

    **Returns:**
    - Updated conversation details
    """
    try:
        service = ConversationService(session)

        conversation = await service.conv_repo.get_user_conversation(user_id, conversation_id)

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        # Update fields if provided
        if request_data.title:
            conversation.title = request_data.title

        if request_data.summary:
            conversation.summary = request_data.summary

        updated = await service.conv_repo.update(
            conversation_id,
            title=request_data.title or conversation.title,
            summary=request_data.summary or conversation.summary,
        )

        message_count = await service.msg_repo.get_conversation_message_count(conversation_id)

        return ConversationResponse(
            id=str(updated.id),
            user_id=updated.user_id,
            title=updated.title,
            summary=updated.summary,
            model=updated.model,
            message_count=message_count,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating conversation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update conversation",
        )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user),
):
    """
    Delete a conversation (soft delete).

    **Parameters:**
    - **conversation_id**: Conversation UUID
    """
    try:
        service = ConversationService(session)

        success = await service.delete_conversation(user_id, conversation_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation",
        )


@router.get("/{conversation_id}/messages", response_model=ConversationHistoryResponse)
async def get_conversation_messages(
    conversation_id: UUID,
    limit: int = 50,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user),
):
    """
    Get message history for a conversation.

    **Parameters:**
    - **conversation_id**: Conversation UUID
    - **limit**: Maximum messages to return (default: 50)

    **Returns:**
    - List of messages with token count
    """
    try:
        service = ConversationService(session)

        # Verify user owns the conversation
        conversation = await service.conv_repo.get_user_conversation(user_id, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        messages, total_tokens = await service.msg_repo.get_messages_with_tokens(conversation_id)

        from src.schemas.conversation_schema import MessageSchema

        formatted_messages = [
            MessageSchema(
                role=msg.role,
                content=msg.content,
                tool_calls=msg.tool_calls,
                tool_results=msg.tool_results,
                tokens_used=msg.tokens_used,
                created_at=msg.created_at,
            )
            for msg in messages[:limit]
        ]

        return ConversationHistoryResponse(
            conversation_id=str(conversation_id),
            messages=formatted_messages,
            total_tokens=total_tokens,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation messages: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversation messages",
        )


@router.post("/{conversation_id}/messages", status_code=status.HTTP_201_CREATED)
async def send_message(
    conversation_id: UUID,
    request_data: SendMessageRequest,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user),
):
    """
    Send a message to a conversation.

    **Parameters:**
    - **conversation_id**: Conversation UUID
    - **content**: Message content
    - **include_rag**: Whether to include RAG search (default: true)

    **Returns:**
    - Agent response with any tool results
    """
    try:
        service = ConversationService(session)

        # Verify user owns the conversation
        conversation = await service.conv_repo.get_user_conversation(user_id, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        # Add user message
        user_message = await service.add_message(
            conversation_id=conversation_id,
            role="user",
            content=request_data.content,
        )

        # TODO: Call agent service to process message
        # For now, just return the user message

        return {
            "message_id": str(user_message.id),
            "role": user_message.role,
            "content": user_message.content,
            "created_at": user_message.created_at,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message",
        )


# ============================================================================
# Cached RAG Endpoints (Phase 1 Optimization)
# ============================================================================

@router.post("/v1/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_with_cache(request: ChatRequest):
    """
    Chat endpoint with semantic caching for RAG queries.

    This endpoint uses the CachedRAGService to:
    1. Encode user queries with OpenAI embeddings
    2. Search similar documents using Lantern HNSW index
    3. Check semantic cache for similar historical queries
    4. Return cached responses (300ms) or generate new ones (850ms)
    5. Cache new responses for future queries

    **Performance:**
    - Cache hit: ~300ms (65% faster)
    - Cache miss: ~850ms (full RAG pipeline)
    - Expected hit rate: 30-50% in production

    **Parameters:**
    - **message**: User's query
    - **enable_cache**: Whether to use semantic cache (default: true)
    - **doc_ids**: Optional list of document IDs to limit search scope

    **Returns:**
    - response: Generated answer
    - cached: Whether response came from cache
    - latency_ms: Total processing time
    - cache_distance: Semantic similarity score (if cached)
    - model: Model used for generation

    **Example:**
    ```json
    {
        "message": "What is RAG?",
        "enable_cache": true
    }
    ```

    **Response:**
    ```json
    {
        "response": "RAG (Retrieval-Augmented Generation) is...",
        "cached": false,
        "latency_ms": 850.5,
        "cache_distance": null,
        "model": "claude-3-5-sonnet-20241022"
    }
    ```
    """
    try:
        # Get RAG service instance
        rag_service = get_rag_service()

        # Execute query with semantic caching
        rag_result = await rag_service.query(
            user_query=request.message,
            enable_cache=request.enable_cache,
            doc_ids=request.doc_ids
        )

        # Log performance metrics
        cache_status = "HIT" if rag_result.cached else "MISS"
        logger.info(
            f"RAG Query [{cache_status}] - "
            f"Latency: {rag_result.latency_ms:.2f}ms - "
            f"Query: {request.message[:50]}..."
        )

        return ChatResponse(
            response=rag_result.response_text,
            cached=rag_result.cached,
            latency_ms=rag_result.latency_ms,
            cache_distance=rag_result.cache_distance,
            model=rag_result.model_name
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat request: {str(e)[:100]}"
        )
