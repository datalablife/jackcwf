"""Message ORM model for storing conversation messages."""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    DateTime,
    JSON,
    Index,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from src.db.base import Base


class MessageORM(Base):
    """
    ORM model for messages table.

    Stores individual messages within conversations,
    including role, content, tool calls, and results.
    """

    __tablename__ = "messages"
    __table_args__ = (
        # Foreign key constraint to conversations
        Index("idx_messages_conversation", "conversation_id"),
        Index("idx_messages_role", "role"),
        Index("idx_messages_conversation_recent", "conversation_id", "created_at"),
        # Check constraint for valid roles
        CheckConstraint("role IN ('user', 'assistant', 'system')", name="ck_valid_role"),
    )

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Key
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Message Content
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)

    # Tool Calling & Results
    tool_calls = Column(JSON, nullable=True)  # List of tool calls made by assistant
    tool_results = Column(JSON, nullable=True)  # Results from tool calls

    # Token Usage Tracking
    tokens_used = Column(Integer, nullable=True)

    # Additional Metadata
    metadata = Column(JSON, nullable=False, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return f"<MessageORM(id={self.id}, conversation_id={self.conversation_id}, role={self.role})>"

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "role": self.role,
            "content": self.content,
            "tool_calls": self.tool_calls,
            "tool_results": self.tool_results,
            "tokens_used": self.tokens_used,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }
