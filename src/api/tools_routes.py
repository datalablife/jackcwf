"""API routes for tool management and execution."""

import logging
from typing import List, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from src.db.config import get_async_session
from src.services.agent_service import AgentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tools", tags=["Tools"])


class ToolSchema(BaseModel):
    """Schema for a tool definition."""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    parameters: dict = Field(..., description="Tool parameter schema (JSON Schema)")
    examples: Optional[List[dict]] = Field(None, description="Example usages")


class ToolListResponse(BaseModel):
    """Response with available tools."""

    tools: List[ToolSchema] = Field(..., description="List of available tools")
    count: int = Field(..., description="Number of tools")


class ExecuteToolRequest(BaseModel):
    """Request to execute a tool."""

    tool_name: str = Field(..., description="Name of tool to execute")
    input: dict = Field(..., description="Tool input parameters")
    conversation_id: Optional[str] = Field(None, description="Optional conversation context")


class ExecuteToolResponse(BaseModel):
    """Response from tool execution."""

    tool_name: str = Field(..., description="Name of executed tool")
    input: dict = Field(..., description="Tool input")
    output: Any = Field(..., description="Tool output")
    success: bool = Field(..., description="Whether execution succeeded")
    error: Optional[str] = Field(None, description="Error message if failed")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")


def get_user_id(request) -> str:
    """Extract user ID from request state."""
    return getattr(request.state, "user_id", "anonymous")


def verify_admin_access(x_admin_key: Optional[str] = Header(None)) -> bool:
    """
    Verify admin access for tool execution.

    In production, this should check against a secure admin key.

    Args:
        x_admin_key: Admin API key from header

    Raises:
        HTTPException: If admin access is denied
    """
    import os

    admin_key = os.getenv("ADMIN_API_KEY")

    if not admin_key:
        # If no admin key is set, allow in development only
        if os.getenv("ENV", "development") == "development":
            logger.warning("Admin key not set - allowing access in development mode")
            return True
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Admin API key not configured",
            )

    if x_admin_key != admin_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin credentials",
        )

    return True


@router.get("", response_model=ToolListResponse)
async def list_tools(
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_user_id),
):
    """
    List all available tools.

    **Returns:**
    - List of tool definitions with names, descriptions, and parameter schemas

    **Available Tools:**
    - **search_documents**: Search user's documents using semantic similarity (RAG)
    - **query_database**: Execute controlled database queries (placeholder)
    - **web_search**: Search the web for information (placeholder)

    **Note:** Tool availability may vary based on user permissions and configuration.
    """
    try:
        # Define available tools
        tools = [
            ToolSchema(
                name="search_documents",
                description="Search through user's uploaded documents using semantic similarity. "
                "Returns relevant document chunks that match the query.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query to find relevant documents",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 20,
                        },
                    },
                    "required": ["query"],
                },
                examples=[
                    {
                        "query": "What is the company's revenue?",
                        "limit": 5,
                    },
                    {
                        "query": "machine learning algorithms",
                        "limit": 10,
                    },
                ],
            ),
            ToolSchema(
                name="query_database",
                description="Execute safe, controlled database queries to retrieve structured data. "
                "Converts natural language to SQL (placeholder for future implementation).",
                parameters={
                    "type": "object",
                    "properties": {
                        "sql_query": {
                            "type": "string",
                            "description": "SQL SELECT query to execute",
                        },
                    },
                    "required": ["sql_query"],
                },
                examples=[
                    {
                        "sql_query": "SELECT * FROM users WHERE active = true LIMIT 10",
                    },
                ],
            ),
            ToolSchema(
                name="web_search",
                description="Search the web for current information and facts. "
                "Useful for questions requiring up-to-date data (placeholder for future implementation).",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Web search query",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 10,
                        },
                    },
                    "required": ["query"],
                },
                examples=[
                    {
                        "query": "latest AI developments 2024",
                        "limit": 5,
                    },
                ],
            ),
        ]

        return ToolListResponse(
            tools=tools,
            count=len(tools),
        )

    except Exception as e:
        logger.error(f"Error listing tools: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list tools",
        )


@router.post("/execute", response_model=ExecuteToolResponse)
async def execute_tool(
    request_data: ExecuteToolRequest,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_user_id),
    admin_verified: bool = Depends(verify_admin_access),
):
    """
    Execute a tool directly (requires admin access).

    **Parameters:**
    - **tool_name**: Name of the tool to execute
    - **input**: Tool input parameters as JSON
    - **conversation_id**: Optional conversation ID for context

    **Security:**
    - Requires admin API key in X-Admin-Key header
    - Should only be used for debugging and testing
    - Not recommended for production user-facing features

    **Headers:**
    - **X-Admin-Key**: Admin API key

    **Returns:**
    - Tool execution result with output and timing
    """
    import time

    start_time = time.time()

    try:
        # Create agent service to access tools
        agent_service = AgentService(session)

        # Get tools for the user
        tools = await agent_service.create_rag_tools(user_id)

        # Find the requested tool
        tool = None
        for t in tools:
            if t.name == request_data.tool_name:
                tool = t
                break

        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool '{request_data.tool_name}' not found",
            )

        # Execute the tool
        logger.info(f"Executing tool {request_data.tool_name} with input: {request_data.input}")

        try:
            # Tools are async, so await them
            result = await tool.ainvoke(request_data.input)
        except AttributeError:
            # Fallback to sync invoke if async not available
            result = tool.invoke(request_data.input)

        elapsed_ms = (time.time() - start_time) * 1000

        logger.info(f"Tool {request_data.tool_name} executed in {elapsed_ms:.2f}ms")

        return ExecuteToolResponse(
            tool_name=request_data.tool_name,
            input=request_data.input,
            output=result,
            success=True,
            error=None,
            execution_time_ms=elapsed_ms,
        )

    except HTTPException:
        raise
    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        logger.error(f"Error executing tool {request_data.tool_name}: {str(e)}", exc_info=True)

        return ExecuteToolResponse(
            tool_name=request_data.tool_name,
            input=request_data.input,
            output=None,
            success=False,
            error=str(e),
            execution_time_ms=elapsed_ms,
        )
