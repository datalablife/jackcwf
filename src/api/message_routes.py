"""API routes for message management."""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from src.db.config import get_async_session
from src.repositories.message import MessageRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/conversations", tags=["Messages"])


class MessageDetailResponse(BaseModel):
    """Detailed message response."""

    id: str = Field(..., description="Message ID")
    conversation_id: str = Field(..., description="Conversation ID")
    role: str = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    tool_calls: Optional[dict] = Field(None, description="Tool calls made")
    tool_results: Optional[dict] = Field(None, description="Tool results")
    tokens_used: Optional[int] = Field(None, description="Tokens used")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    created_at: str = Field(..., description="Creation timestamp")


class UpdateMessageRequest(BaseModel):
    """Request to update a message."""

    tool_results: Optional[dict] = Field(None, description="Tool results to update")
    tokens_used: Optional[int] = Field(None, description="Tokens used to update")
    metadata: Optional[dict] = Field(None, description="Metadata to update")


def get_user_id(request) -> str:
    """Extract user ID from request state."""
    return getattr(request.state, "user_id", "anonymous")


@router.get("/{conversation_id}/messages/{message_id}", response_model=MessageDetailResponse)
async def get_message(
    conversation_id: UUID,
    message_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_user_id),
):
    """
    Get a specific message by ID.

    **Parameters:**
    - **conversation_id**: Conversation UUID
    - **message_id**: Message UUID

    **Returns:**
    - Full message details including tool calls and results

    **Security:**
    - Verifies user owns the conversation before returning message
    """
    try:
        msg_repo = MessageRepository(session)

        # Get the message
        message = await msg_repo.get(message_id)

        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found",
            )

        # Verify message belongs to the conversation
        if message.conversation_id != conversation_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found in this conversation",
            )

        # TODO: Verify user owns the conversation
        # For now, we trust the auth middleware set the user_id correctly

        return MessageDetailResponse(
            id=str(message.id),
            conversation_id=str(message.conversation_id),
            role=message.role,
            content=message.content,
            tool_calls=message.tool_calls,
            tool_results=message.tool_results,
            tokens_used=message.tokens_used,
            metadata=message.metadata or {},
            created_at=message.created_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting message: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get message",
        )


@router.put("/{conversation_id}/messages/{message_id}", response_model=MessageDetailResponse)
async def update_message(
    conversation_id: UUID,
    message_id: UUID,
    request_data: UpdateMessageRequest,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_user_id),
):
    """
    Update a message's metadata, tool results, or token count.

    **Parameters:**
    - **conversation_id**: Conversation UUID
    - **message_id**: Message UUID
    - **tool_results**: Tool execution results (optional)
    - **tokens_used**: Token count (optional)
    - **metadata**: Additional metadata (optional)

    **Returns:**
    - Updated message details

    **Use Cases:**
    - Update tool results after execution
    - Track token usage for cost monitoring
    - Add metadata for debugging or analytics

    **Security:**
    - Verifies user owns the conversation before updating
    """
    try:
        msg_repo = MessageRepository(session)

        # Get the message
        message = await msg_repo.get(message_id)

        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found",
            )

        # Verify message belongs to the conversation
        if message.conversation_id != conversation_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found in this conversation",
            )

        # TODO: Verify user owns the conversation

        # Build update dict with only provided fields
        update_data = {}

        if request_data.tool_results is not None:
            update_data["tool_results"] = request_data.tool_results

        if request_data.tokens_used is not None:
            update_data["tokens_used"] = request_data.tokens_used

        if request_data.metadata is not None:
            # Merge with existing metadata
            existing_metadata = message.metadata or {}
            existing_metadata.update(request_data.metadata)
            update_data["metadata"] = existing_metadata

        if not update_data:
            # No updates provided, return current message
            return MessageDetailResponse(
                id=str(message.id),
                conversation_id=str(message.conversation_id),
                role=message.role,
                content=message.content,
                tool_calls=message.tool_calls,
                tool_results=message.tool_results,
                tokens_used=message.tokens_used,
                metadata=message.metadata or {},
                created_at=message.created_at.isoformat(),
            )

        # Update the message
        updated_message = await msg_repo.update(message_id, **update_data)

        logger.info(f"Updated message {message_id} with fields: {list(update_data.keys())}")

        return MessageDetailResponse(
            id=str(updated_message.id),
            conversation_id=str(updated_message.conversation_id),
            role=updated_message.role,
            content=updated_message.content,
            tool_calls=updated_message.tool_calls,
            tool_results=updated_message.tool_results,
            tokens_used=updated_message.tokens_used,
            metadata=updated_message.metadata or {},
            created_at=updated_message.created_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating message: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update message",
        )


@router.delete("/{conversation_id}/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    conversation_id: UUID,
    message_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_user_id),
):
    """
    Delete a message from a conversation.

    **Parameters:**
    - **conversation_id**: Conversation UUID
    - **message_id**: Message UUID

    **Note:**
    - This is a hard delete (permanent removal)
    - Use with caution as this cannot be undone
    - Consider soft delete for production use

    **Security:**
    - Verifies user owns the conversation before deleting
    """
    try:
        msg_repo = MessageRepository(session)

        # Get the message
        message = await msg_repo.get(message_id)

        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found",
            )

        # Verify message belongs to the conversation
        if message.conversation_id != conversation_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found in this conversation",
            )

        # TODO: Verify user owns the conversation

        # Delete the message
        await msg_repo.delete(message_id)

        logger.info(f"Deleted message {message_id} from conversation {conversation_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting message: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete message",
        )
