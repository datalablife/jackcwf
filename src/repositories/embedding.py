"""Embedding repository with vector similarity search."""

import logging
import time
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import EmbeddingORM, DocumentORM
from src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class EmbeddingRepository(BaseRepository[EmbeddingORM]):
    """
    Repository for embedding management with vector search.

    Uses pgvector HNSW index for efficient similarity search.
    Performance target: Vector search ≤ 200ms P99
    """

    model_class = EmbeddingORM

    def __init__(self, session: AsyncSession):
        """Initialize repository."""
        super().__init__(session)

    async def search_similar(
        self,
        query_embedding: List[float],
        user_id: str,
        limit: int = 5,
        threshold: float = 0.7,
    ) -> List[EmbeddingORM]:
        """
        Search for similar embeddings using cosine similarity.

        Uses pgvector cosine distance for efficient vector search.

        Args:
            query_embedding: Query embedding vector (1536-dimensional)
            user_id: User ID to scope search to user's documents
            limit: Maximum number of results
            threshold: Similarity threshold (0.0 to 1.0)

        Returns:
            List of similar embeddings, sorted by similarity (most similar first)

        Performance: Target ≤ 200ms P99
        """
        start_time = time.time()

        try:
            # Vector distance search using pgvector cosine distance
            # cosine_distance ranges from 0 (identical) to 2 (opposite)
            # We convert threshold (similarity 0-1) to distance (2-0)
            max_distance = 2 - (2 * threshold)

            query = (
                select(EmbeddingORM)
                .join(DocumentORM, EmbeddingORM.document_id == DocumentORM.id)
                .where(
                    and_(
                        DocumentORM.user_id == user_id,
                        EmbeddingORM.is_deleted == False,
                        DocumentORM.is_deleted == False,
                        # Use cosine distance: <-> operator
                        # Requires pgvector extension
                        EmbeddingORM.embedding.op("<->")(query_embedding) <= max_distance,
                    )
                )
                .order_by(EmbeddingORM.embedding.op("<->")(query_embedding))
                .limit(limit)
            )

            result = await self.session.execute(query)
            embeddings = result.scalars().all()

            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(f"Vector search completed in {elapsed_ms:.2f}ms, found {len(embeddings)} results")

            # Assert performance target
            if elapsed_ms > 200:
                logger.warning(
                    f"Vector search exceeded 200ms target: {elapsed_ms:.2f}ms. "
                    f"Consider optimizing indices or database performance."
                )

            return embeddings

        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(f"Vector search failed after {elapsed_ms:.2f}ms: {str(e)}")
            raise

    async def search_by_document(
        self,
        document_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[EmbeddingORM]:
        """
        Get all embeddings for a document.

        Args:
            document_id: Document ID
            skip: Number of embeddings to skip
            limit: Maximum number of embeddings

        Returns:
            List of embeddings ordered by chunk index
        """
        query = (
            select(EmbeddingORM)
            .where(
                and_(
                    EmbeddingORM.document_id == document_id,
                    EmbeddingORM.is_deleted == False,
                )
            )
            .order_by(EmbeddingORM.chunk_index.asc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def count_document_embeddings(self, document_id: UUID) -> int:
        """
        Count embeddings for a document.

        Args:
            document_id: Document ID

        Returns:
            Number of embeddings
        """
        return await self.count(document_id=document_id, is_deleted=False)

    async def bulk_create_embeddings(
        self,
        embeddings: List[EmbeddingORM],
    ) -> int:
        """
        Bulk create embeddings.

        Performance target: ≤ 100ms per 1000 vectors

        Args:
            embeddings: List of embedding instances

        Returns:
            Number of created embeddings
        """
        start_time = time.time()

        self.session.add_all(embeddings)
        await self.session.commit()

        elapsed_ms = (time.time() - start_time) * 1000
        count = len(embeddings)
        ms_per_1000 = (elapsed_ms / count) * 1000 if count > 0 else 0

        logger.info(
            f"Bulk created {count} embeddings in {elapsed_ms:.2f}ms "
            f"({ms_per_1000:.2f}ms per 1000 vectors)"
        )

        if ms_per_1000 > 100:
            logger.warning(
                f"Bulk insert exceeded 100ms per 1000 vectors target: {ms_per_1000:.2f}ms. "
                f"Consider database optimization."
            )

        return count

    async def soft_delete_document_embeddings(self, document_id: UUID) -> int:
        """
        Soft delete all embeddings for a document.

        Args:
            document_id: Document ID

        Returns:
            Number of deleted embeddings
        """
        query = select(EmbeddingORM).where(EmbeddingORM.document_id == document_id)
        result = await self.session.execute(query)
        embeddings = result.scalars().all()

        for embedding in embeddings:
            embedding.is_deleted = True

        await self.session.commit()
        return len(embeddings)

    async def get_user_embedding_count(self, user_id: str) -> int:
        """
        Count total embeddings for a user.

        Args:
            user_id: User ID

        Returns:
            Total number of embeddings
        """
        query = (
            select(func.count(EmbeddingORM.id))
            .select_from(EmbeddingORM)
            .join(DocumentORM, EmbeddingORM.document_id == DocumentORM.id)
            .where(
                and_(
                    DocumentORM.user_id == user_id,
                    EmbeddingORM.is_deleted == False,
                    DocumentORM.is_deleted == False,
                )
            )
        )

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def search_by_chunk_index(
        self,
        document_id: UUID,
        start_index: int,
        end_index: int,
    ) -> List[EmbeddingORM]:
        """
        Get embeddings within a chunk index range.

        Args:
            document_id: Document ID
            start_index: Starting chunk index (inclusive)
            end_index: Ending chunk index (inclusive)

        Returns:
            List of embeddings in the range
        """
        query = (
            select(EmbeddingORM)
            .where(
                and_(
                    EmbeddingORM.document_id == document_id,
                    EmbeddingORM.chunk_index >= start_index,
                    EmbeddingORM.chunk_index <= end_index,
                    EmbeddingORM.is_deleted == False,
                )
            )
            .order_by(EmbeddingORM.chunk_index.asc())
        )

        result = await self.session.execute(query)
        return result.scalars().all()
