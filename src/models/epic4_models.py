"""
ORM Models for Epic 4 Thread Support
Defines tool_calls, agent_checkpoints tables and enhancements to existing models
"""

from sqlalchemy import Column, Integer, String, Float, JSON, Text, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from uuid import uuid4
from src.db.base import Base


class ToolCall(Base):
    """
    Stores tool invocation records for tracking tool execution and results.
    Used for:
    - Human-in-the-loop: Tracking tool executions that require user confirmation
    - Tool execution history: Maintaining complete audit trail of tool calls
    - Error tracking: Tracking failed tool executions
    """

    __tablename__ = "tool_calls"
    __table_args__ = (
        Index("idx_tool_calls_tool_id", "tool_id", unique=True),
        Index("idx_tool_calls_status", "status"),
        Index("idx_tool_calls_message_id", "message_id"),
        Index("idx_tool_calls_conversation_id", "conversation_id"),
    )

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Unique tool invocation ID (e.g., "tool_abc123")
    tool_id = Column(String(255), unique=True, nullable=False, index=True)

    # Foreign Keys (using UUID since messages and conversations use UUID)
    message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Tool Information
    tool_name = Column(String(255), nullable=False)  # "vector_search", "query_database", "web_search"
    tool_input = Column(JSON, default={})  # {"query": "LangChain", "limit": 5}

    # Execution Status
    status = Column(String(50), default="pending", index=True)  # pending|executing|completed|failed
    result = Column(Text)  # Text representation of result
    result_data = Column(JSON)  # Structured result data

    # Error Information
    is_error = Column(Boolean, default=False)
    error_message = Column(Text)  # Error message if execution failed

    # Performance Metrics
    execution_time_ms = Column(Float)  # Execution time in milliseconds

    # Human-in-the-Loop
    user_confirmed = Column(Boolean, default=False)  # Whether user confirmed the result

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True))

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "tool_id": self.tool_id,
            "tool_name": self.tool_name,
            "tool_input": self.tool_input,
            "status": self.status,
            "result": self.result,
            "result_data": self.result_data,
            "is_error": self.is_error,
            "error_message": self.error_message,
            "execution_time_ms": self.execution_time_ms,
            "user_confirmed": self.user_confirmed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class AgentCheckpoint(Base):
    """
    Stores LangGraph agent state checkpoints for resumable agent execution.
    Used for:
    - Agent state persistence: Save/restore agent execution state
    - Resumable conversations: Resume conversations from saved checkpoint
    - Multi-turn conversations: Track agent state across turns
    - Debugging: Analyze agent behavior at each step
    """

    __tablename__ = "agent_checkpoints"
    __table_args__ = (
        Index("idx_agent_checkpoints_checkpoint_id", "checkpoint_id", unique=True),
        Index("idx_agent_checkpoints_thread_id", "thread_id"),
        Index("idx_agent_checkpoints_conversation_id", "conversation_id"),
    )

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Unique checkpoint ID (e.g., "ckpt_abc123")
    checkpoint_id = Column(String(255), unique=True, nullable=False, index=True)

    # Foreign Key (using UUID since conversations use UUID)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Thread/Conversation Reference
    thread_id = Column(String(255), nullable=False, index=True)  # Format: "thread_<conversation_id>"

    # Checkpoint Information
    step = Column(Integer, nullable=False)  # Execution step number (0, 1, 2, ...)
    state = Column(JSON, nullable=False)  # Complete LangGraph checkpoint state
    checkpoint_metadata = Column(JSON, default={})  # Additional metadata (model config, etc.)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "checkpoint_id": self.checkpoint_id,
            "conversation_id": str(self.conversation_id),
            "thread_id": self.thread_id,
            "step": self.step,
            "state": self.state,
            "metadata": self.checkpoint_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# Enhanced existing models (fields to add)
# =====================================

class MessageEnhanced:
    """
    Fields to add to existing Message model:

    metadata: JSON = Column(JSON, default={})
        Contains:
        - token_usage: Number of tokens used (input + output)
        - is_streaming: Boolean indicating if message is streaming
        - stream_completed: Boolean indicating if streaming completed
        - tool_calls: List of ToolCall references
        - tool_results: List of ToolResult references
    """
    pass


class ConversationEnhanced:
    """
    Fields to add to existing Conversation model:

    metadata: JSON = Column(JSON, default={})
        Contains:
        - model_config: LLM model configuration (model name, temperature, etc.)
        - user_preferences: User preferences for this conversation
        - agent_state: Current agent execution state
        - custom_fields: Any custom fields specific to this conversation
    """
    pass
