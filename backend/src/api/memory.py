"""Memory management API endpoints."""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Body

from src.memory.manager import get_memory_manager
from src.services.claude_integration import get_claude_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/memory", tags=["Memory Management"])


# Pydantic models for request/response
from pydantic import BaseModel, Field


class AddMemoryRequest(BaseModel):
    """Request model for adding memory."""

    content: str = Field(..., description="Memory content")
    memory_type: str = Field(
        default="long_term",
        description="Type of memory: short_term, long_term, rule, entity",
    )
    importance: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Importance score from 0.0 to 1.0",
    )
    tags: Optional[List[str]] = Field(default=None, description="Optional tags")
    metadata: Optional[dict] = Field(default=None, description="Optional metadata")


class SearchMemoryRequest(BaseModel):
    """Request model for searching memory."""

    query: str = Field(..., description="Search query")
    memory_type: Optional[str] = Field(default=None, description="Filter by memory type")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results")
    threshold: float = Field(default=0.0, ge=0.0, le=1.0, description="Relevance threshold")


class ClaudeMessageRequest(BaseModel):
    """Request model for Claude message with memory."""

    content: str = Field(..., description="User message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for memory tracking")
    use_memory: bool = Field(default=True, description="Use memory context")
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")


@router.post("/add", response_model=dict)
async def add_memory(request: AddMemoryRequest) -> dict:
    """Add a memory to the system.

    Args:
        request: AddMemoryRequest with memory content and metadata

    Returns:
        Result dictionary with success status
    """
    try:
        manager = get_memory_manager()
        success = await manager.add_memory(
            content=request.content,
            memory_type=request.memory_type,
            importance=request.importance,
            tags=request.tags,
            metadata=request.metadata,
        )

        if success:
            return {"success": True, "message": "Memory added successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to add memory")

    except Exception as e:
        logger.error(f"Error adding memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=dict)
async def search_memory(request: SearchMemoryRequest) -> dict:
    """Search memories by query.

    Args:
        request: SearchMemoryRequest with search parameters

    Returns:
        Dictionary with matching memories
    """
    try:
        manager = get_memory_manager()
        results = await manager.search_memory(
            query=request.query,
            memory_type=request.memory_type,
            limit=request.limit,
            threshold=request.threshold,
        )

        return {"success": True, "count": len(results), "memories": results}

    except Exception as e:
        logger.error(f"Error searching memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=dict)
async def search_memory_get(
    query: str = Query(..., description="Search query"),
    memory_type: Optional[str] = Query(None, description="Filter by type"),
    limit: int = Query(10, ge=1, le=100),
    threshold: float = Query(0.0, ge=0.0, le=1.0),
) -> dict:
    """Search memories by query (GET endpoint).

    Args:
        query: Search query
        memory_type: Optional filter by type
        limit: Maximum results
        threshold: Relevance threshold

    Returns:
        Dictionary with matching memories
    """
    try:
        manager = get_memory_manager()
        results = await manager.search_memory(
            query=query,
            memory_type=memory_type,
            limit=limit,
            threshold=threshold,
        )

        return {"success": True, "count": len(results), "memories": results}

    except Exception as e:
        logger.error(f"Error searching memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context/{conversation_id}", response_model=dict)
async def get_conversation_context(
    conversation_id: str,
    max_memories: int = Query(10, ge=1, le=50),
) -> dict:
    """Get memory context for a conversation.

    Args:
        conversation_id: Conversation ID
        max_memories: Maximum memories to retrieve

    Returns:
        Dictionary with relevant memories
    """
    try:
        manager = get_memory_manager()
        memories = await manager.get_conversation_context(
            conversation_id=conversation_id,
            max_memories=max_memories,
        )

        return {"success": True, "count": len(memories), "memories": memories}

    except Exception as e:
        logger.error(f"Error getting conversation context: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear", response_model=dict)
async def clear_memories(
    older_than_days: Optional[int] = Query(None, description="Clear memories older than N days"),
    memory_type: Optional[str] = Query(None, description="Only clear specific type"),
) -> dict:
    """Clear memories based on criteria.

    Args:
        older_than_days: Clear memories older than N days
        memory_type: Only clear specific memory type

    Returns:
        Result dictionary with count of cleared memories
    """
    try:
        manager = get_memory_manager()
        count = await manager.clear_memories(
            older_than_days=older_than_days,
            memory_type=memory_type,
        )

        return {"success": True, "cleared": count}

    except Exception as e:
        logger.error(f"Error clearing memories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=dict)
async def get_memory_stats() -> dict:
    """Get memory system statistics.

    Returns:
        Dictionary with memory statistics
    """
    try:
        manager = get_memory_manager()
        stats = await manager.get_memory_stats()
        return {"success": True, "stats": stats}

    except Exception as e:
        logger.error(f"Error getting memory stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/claude/message", response_model=dict)
async def claude_message(request: ClaudeMessageRequest) -> dict:
    """Send a message to Claude with memory context.

    Args:
        request: ClaudeMessageRequest with message and options

    Returns:
        Dictionary with Claude response
    """
    try:
        service = get_claude_service()

        messages = [{"role": "user", "content": request.content}]

        response = await service.chat(
            messages=messages,
            conversation_id=request.conversation_id,
            use_memory=request.use_memory,
            system_prompt=request.system_prompt,
        )

        return {
            "success": True,
            "response": response["content"],
            "usage": response["usage"],
            "conversation_id": request.conversation_id,
        }

    except Exception as e:
        logger.error(f"Error in Claude message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=dict)
async def memory_health() -> dict:
    """Health check for memory system.

    Returns:
        Health status dictionary
    """
    try:
        manager = get_memory_manager()
        stats = await manager.get_memory_stats()

        return {
            "success": True,
            "status": "healthy",
            "memory_initialized": stats.get("initialized", False),
        }

    except Exception as e:
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e),
        }
