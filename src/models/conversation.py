"""Conversation ORM model for storing user conversations."""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON, Index
from sqlalchemy.dialects.postgresql import UUID

from src.db.base import Base


class ConversationORM(Base):
    """
    ORM model for conversations table.

    Stores metadata about AI conversations including user,
    title, system prompt, and model information.
    """

    __tablename__ = "conversations"
    __table_args__ = (
        Index("idx_conversations_user_created", "user_id", "created_at", postgresql_where="is_deleted = false"),
        Index("idx_conversations_user_active", "user_id", postgresql_where="is_deleted = false"),
        Index("idx_conversations_title_search", "title"),
    )

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys & User Info
    user_id = Column(String(255), nullable=False, index=True)

    # Conversation Metadata
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)
    model = Column(String(100), nullable=False, default="claude-sonnet-4-5-20250929")
    system_prompt = Column(Text, nullable=False)

    # Additional Data
    meta = Column(JSON, nullable=False, default={})

    # Soft Delete
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<ConversationORM(id={self.id}, user_id={self.user_id}, title={self.title})>"

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "title": self.title,
            "summary": self.summary,
            "model": self.model,
            "system_prompt": self.system_prompt,
            "meta": self.meta,
            "is_deleted": self.is_deleted,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
