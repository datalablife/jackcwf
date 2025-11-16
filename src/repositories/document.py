"""Document repository with document management."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import DocumentORM
from src.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[DocumentORM]):
    """Repository for document management."""

    model_class = DocumentORM

    def __init__(self, session: AsyncSession):
        """Initialize repository."""
        super().__init__(session)

    async def get_user_documents(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 10,
        include_deleted: bool = False,
    ) -> List[DocumentORM]:
        """
        Get all documents for a user.

        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records
            include_deleted: Whether to include soft-deleted documents

        Returns:
            List of documents ordered by most recent first
        """
        query = select(DocumentORM).where(DocumentORM.user_id == user_id)

        if not include_deleted:
            query = query.where(DocumentORM.is_deleted == False)

        query = query.order_by(DocumentORM.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_user_document(
        self,
        user_id: str,
        document_id: UUID,
        include_deleted: bool = False,
    ) -> Optional[DocumentORM]:
        """
        Get a specific document for a user.

        Args:
            user_id: User ID
            document_id: Document ID
            include_deleted: Whether to include soft-deleted documents

        Returns:
            Document instance or None
        """
        query = select(DocumentORM).where(
            and_(
                DocumentORM.user_id == user_id,
                DocumentORM.id == document_id,
            )
        )

        if not include_deleted:
            query = query.where(DocumentORM.is_deleted == False)

        result = await self.session.execute(query)
        return result.scalars().first()

    async def count_user_documents(self, user_id: str) -> int:
        """
        Count active documents for a user.

        Args:
            user_id: User ID

        Returns:
            Number of active documents
        """
        return await self.count(user_id=user_id, is_deleted=False)

    async def soft_delete(self, document_id: UUID) -> bool:
        """
        Soft delete a document.

        Args:
            document_id: Document ID

        Returns:
            True if deleted, False if not found
        """
        document = await self.get(document_id)
        if not document:
            return False

        document.is_deleted = True
        document.deleted_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(document)
        return True

    async def update_chunk_count(
        self,
        document_id: UUID,
        chunk_count: int,
    ) -> Optional[DocumentORM]:
        """
        Update the total chunk count for a document.

        Args:
            document_id: Document ID
            chunk_count: Total number of chunks

        Returns:
            Updated document or None
        """
        return await self.update(document_id, total_chunks=chunk_count)

    async def search_by_filename(
        self,
        user_id: str,
        search_term: str,
        skip: int = 0,
        limit: int = 10,
    ) -> List[DocumentORM]:
        """
        Search documents by filename.

        Args:
            user_id: User ID
            search_term: Search term
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of matching documents
        """
        from sqlalchemy import func

        query = select(DocumentORM).where(
            and_(
                DocumentORM.user_id == user_id,
                DocumentORM.is_deleted == False,
                func.lower(DocumentORM.filename).like(f"%{search_term.lower()}%"),
            )
        ).order_by(DocumentORM.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_documents_by_type(
        self,
        user_id: str,
        file_type: str,  # 'pdf', 'txt', 'docx', etc.
        skip: int = 0,
        limit: int = 10,
    ) -> List[DocumentORM]:
        """
        Get documents filtered by file type.

        Args:
            user_id: User ID
            file_type: File type to filter
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of documents with specified type
        """
        query = (
            select(DocumentORM)
            .where(
                and_(
                    DocumentORM.user_id == user_id,
                    DocumentORM.file_type == file_type,
                    DocumentORM.is_deleted == False,
                )
            )
            .order_by(DocumentORM.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(query)
        return result.scalars().all()
