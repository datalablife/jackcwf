"""Document ORM model for storing uploaded documents."""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON, Index
from sqlalchemy.dialects.postgresql import UUID

from src.db.base import Base


class DocumentORM(Base):
    """
    ORM model for documents table.

    Stores metadata about uploaded documents including
    file information and chunk tracking for RAG.
    """

    __tablename__ = "documents"
    __table_args__ = (
        Index("idx_documents_user_created", "user_id", "created_at", postgresql_where="is_deleted = false"),
        Index("idx_documents_user_active", "user_id", postgresql_where="is_deleted = false"),
    )

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # User & File Info
    user_id = Column(String(255), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)  # 'pdf', 'txt', 'docx', etc.

    # Document Content
    content = Column(Text, nullable=False)

    # Chunking Info
    total_chunks = Column(int, nullable=False, default=0)

    # Additional Metadata
    metadata = Column(JSON, nullable=False, default={})

    # Soft Delete
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<DocumentORM(id={self.id}, filename={self.filename}, chunks={self.total_chunks})>"

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "filename": self.filename,
            "file_type": self.file_type,
            "content": self.content[:100] + "..." if len(self.content) > 100 else self.content,
            "total_chunks": self.total_chunks,
            "metadata": self.metadata,
            "is_deleted": self.is_deleted,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
