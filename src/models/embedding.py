"""Embedding ORM model for storing document chunk embeddings."""

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, JSON, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, VECTOR

from src.db.base import Base


class EmbeddingORM(Base):
    """
    ORM model for embeddings table.

    Stores vector embeddings of document chunks for RAG.
    Uses pgvector extension with HNSW index for efficient similarity search.

    Performance target: Vector search ≤ 200ms P99
    """

    __tablename__ = "embeddings"
    __table_args__ = (
        # Indices for efficient querying
        Index("idx_embeddings_document", "document_id"),
        Index("idx_embeddings_created", "created_at"),
        Index("idx_embeddings_document_chunk", "document_id", "chunk_index"),
        # Vector index using HNSW (Hierarchical Navigable Small World)
        Index(
            "idx_embeddings_vector_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Key to documents
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Chunk Content & Embedding
    chunk_text = Column(Text, nullable=False)
    # Vector embedding (1536-dimensional for OpenAI text-embedding-3-small)
    embedding = Column(VECTOR(1536), nullable=False)
    chunk_index = Column(Integer, nullable=False)  # Sequential index within document

    # Metadata
    metadata = Column(JSON, nullable=False, default={})

    # Soft Delete
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return f"<EmbeddingORM(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"

    def to_dict(self, include_embedding: bool = False) -> dict:
        """
        Convert to dictionary representation.

        Args:
            include_embedding: Whether to include the full embedding vector (can be large)
        """
        data = {
            "id": str(self.id),
            "document_id": str(self.document_id),
            "chunk_text": self.chunk_text[:100] + "..." if len(self.chunk_text) > 100 else self.chunk_text,
            "chunk_index": self.chunk_index,
            "metadata": self.metadata,
            "is_deleted": self.is_deleted,
            "created_at": self.created_at.isoformat(),
        }

        if include_embedding and self.embedding is not None:
            data["embedding"] = self.embedding

        return data
