"""
Thread API Routes for Epic 4 - LangGraph Integration
Provides endpoints for:
- Creating/retrieving threads (mapped to conversations)
- Getting thread state with agent checkpoints
- Submitting tool execution results (human-in-the-loop)
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional, Dict, Any
from uuid import UUID
import logging

from src.db.config import get_async_session
from src.models.conversation import ConversationORM
from src.models.epic4_models import AgentCheckpoint, ToolCall
from src.models.message import MessageORM

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["threads"])


# Pydantic Models for Request/Response
from pydantic import BaseModel, Field


class ThreadCreateRequest(BaseModel):
    """Request body for creating a thread."""
    title: Optional[str] = Field(default="New Conversation", description="Thread title")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Thread metadata")


class ThreadResponse(BaseModel):
    """Response model for thread creation/retrieval."""
    thread_id: str = Field(..., description="Thread ID (format: thread_<conversation_id>)")
    conversation_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int
    metadata: Dict[str, Any]

    class Config:
        from_attributes = True


class ToolResultRequest(BaseModel):
    """Request body for submitting tool execution results."""
    tool_id: str = Field(..., description="Unique tool invocation ID")
    tool_name: str = Field(..., description="Name of the tool (vector_search, query_database, web_search)")
    result: Any = Field(..., description="Tool execution result")
    result_data: Optional[Dict[str, Any]] = Field(None, description="Structured result data")
    execution_time_ms: Optional[float] = Field(None, description="Execution time in milliseconds")


class ToolCallDetail(BaseModel):
    """Tool call information."""
    tool_id: str
    tool_name: str
    tool_input: Dict[str, Any]
    status: str
    execution_time_ms: Optional[float]


class ThreadStateResponse(BaseModel):
    """Response model for thread state."""
    thread_id: str
    conversation_id: str
    messages: list = Field(default=[], description="Recent messages")
    pending_tools: list = Field(default=[], description="Pending tool calls")
    agent_checkpoint: Optional[Dict[str, Any]] = Field(None, description="Latest agent checkpoint")
    metadata: Dict[str, Any] = Field(default={})

    class Config:
        from_attributes = True


# API Endpoints

@router.post("/threads", response_model=ThreadResponse, status_code=201)
async def create_or_get_thread(
    request: ThreadCreateRequest,
    user_id: str = "default_user",  # In production, get from JWT token
    db: AsyncSession = Depends(get_async_session)
):
    """
    Create a new thread or get existing thread.
    Maps to creating/retrieving a conversation.
    """
    try:
        # Check if conversation with title exists
        stmt = select(ConversationORM).where(
            and_(
                ConversationORM.user_id == user_id,
                ConversationORM.title == request.title,
                ConversationORM.is_deleted == False
            )
        )
        result = await db.execute(stmt)
        conversation = result.scalars().first()

        # Create new conversation if not exists
        if not conversation:
            conversation = ConversationORM(
                user_id=user_id,
                title=request.title,
                system_prompt="You are a helpful AI assistant.",  # Default system prompt
                meta=request.metadata or {}
            )
            db.add(conversation)
            await db.commit()
            await db.refresh(conversation)

        # Count messages
        msg_stmt = select(MessageORM).where(MessageORM.conversation_id == conversation.id)
        msg_result = await db.execute(msg_stmt)
        message_count = len(msg_result.scalars().all())

        return ThreadResponse(
            thread_id=f"thread_{conversation.id}",
            conversation_id=str(conversation.id),
            title=conversation.title,
            created_at=conversation.created_at.isoformat(),
            updated_at=conversation.updated_at.isoformat(),
            message_count=message_count,
            metadata=conversation.meta
        )

    except Exception as e:
        logger.error(f"Error creating/getting thread: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create thread: {str(e)}")


@router.get("/threads/{thread_id}/state", response_model=ThreadStateResponse)
async def get_thread_state(
    thread_id: str,
    include_messages: bool = Query(True, description="Include messages in response"),
    message_limit: int = Query(10, ge=1, le=500, description="Max messages to return"),
    include_tools: bool = Query(False, description="Include tool call information"),
    use_cache: bool = Query(True, description="Use cached results if available"),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get the complete state of a thread.
    Returns messages, pending tools, and agent checkpoint.
    """
    try:
        # Parse thread_id to get conversation_id
        if not thread_id.startswith("thread_"):
            raise HTTPException(status_code=400, detail="Invalid thread_id format")

        conversation_id_str = thread_id.replace("thread_", "")
        try:
            conversation_id = UUID(conversation_id_str)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid conversation UUID")

        # Get conversation
        stmt = select(ConversationORM).where(ConversationORM.id == conversation_id)
        result = await db.execute(stmt)
        conversation = result.scalars().first()

        if not conversation or conversation.is_deleted:
            raise HTTPException(status_code=404, detail="Thread not found")

        # Get recent messages
        messages = []
        if include_messages:
            msg_stmt = (
                select(MessageORM)
                .where(MessageORM.conversation_id == conversation_id)
                .order_by(MessageORM.created_at.desc())
                .limit(message_limit)
            )
            msg_result = await db.execute(msg_stmt)
            messages = [
                {
                    "id": str(msg.id),
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                    "tool_calls": msg.tool_calls if include_tools else None,
                    "tool_results": msg.tool_results if include_tools else None,
                }
                for msg in msg_result.scalars().all()
            ]

        # Get pending tool calls
        pending_tools = []
        if include_tools:
            tool_stmt = (
                select(ToolCall)
                .where(
                    and_(
                        ToolCall.conversation_id == conversation_id,
                        ToolCall.status.in_(["pending", "executing"])
                    )
                )
                .order_by(ToolCall.created_at.desc())
            )
            tool_result = await db.execute(tool_stmt)
            pending_tools = [tool.to_dict() for tool in tool_result.scalars().all()]

        # Get latest agent checkpoint
        agent_checkpoint = None
        cp_stmt = (
            select(AgentCheckpoint)
            .where(AgentCheckpoint.conversation_id == conversation_id)
            .order_by(AgentCheckpoint.step.desc())
            .limit(1)
        )
        cp_result = await db.execute(cp_stmt)
        latest_cp = cp_result.scalars().first()
        if latest_cp:
            agent_checkpoint = latest_cp.state

        return ThreadStateResponse(
            thread_id=thread_id,
            conversation_id=str(conversation.id),
            messages=messages,
            pending_tools=pending_tools,
            agent_checkpoint=agent_checkpoint,
            metadata=conversation.meta
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting thread state: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get thread state: {str(e)}")


@router.post("/threads/{thread_id}/tool-result")
async def submit_tool_result(
    thread_id: str,
    request: ToolResultRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Submit the result of a tool execution (human-in-the-loop).
    Updates the tool_calls table and marks as completed.
    """
    try:
        # Parse thread_id to get conversation_id
        if not thread_id.startswith("thread_"):
            raise HTTPException(status_code=400, detail="Invalid thread_id format")

        conversation_id_str = thread_id.replace("thread_", "")
        try:
            conversation_id = UUID(conversation_id_str)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid conversation UUID")

        # Find the tool call
        stmt = select(ToolCall).where(
            and_(
                ToolCall.tool_id == request.tool_id,
                ToolCall.conversation_id == conversation_id
            )
        )
        result = await db.execute(stmt)
        tool_call = result.scalars().first()

        if not tool_call:
            raise HTTPException(status_code=404, detail="Tool call not found")

        # Update tool call with result
        tool_call.status = "completed"
        tool_call.result = str(request.result)
        tool_call.result_data = request.result_data
        tool_call.execution_time_ms = request.execution_time_ms
        tool_call.user_confirmed = True
        tool_call.completed_at = __import__('datetime').datetime.utcnow()

        await db.commit()

        # TODO: Resume agent execution with the tool result

        return {
            "status": "success",
            "tool_id": request.tool_id,
            "message": "Tool result submitted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting tool result: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to submit tool result: {str(e)}")


# Health check endpoint
@router.get("/threads/health", tags=["health"])
async def thread_health_check():
    """Health check for thread endpoints."""
    return {"status": "ok", "service": "threads-api"}
