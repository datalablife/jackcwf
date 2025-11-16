"""Document service for document management and chunking."""

import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.models import DocumentORM, EmbeddingORM
from src.repositories import DocumentRepository, EmbeddingRepository

logger = logging.getLogger(__name__)


class DocumentChunker:
    """
    Service for chunking documents into processable pieces.

    Splits documents into overlapping chunks suitable for embedding.
    """

    DEFAULT_CHUNK_SIZE = 1000  # characters
    DEFAULT_CHUNK_OVERLAP = 200  # characters

    def __init__(self, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_CHUNK_OVERLAP):
        """
        Initialize document chunker.

        Args:
            chunk_size: Number of characters per chunk
            overlap: Number of overlapping characters between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks with overlap.

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        chunks = []
        step = self.chunk_size - self.overlap

        for i in range(0, len(text), step):
            chunk = text[i : i + self.chunk_size]
            if chunk.strip():  # Skip empty chunks
                chunks.append(chunk)

            # If this is the last chunk and it's smaller than chunk_size, break
            if i + self.chunk_size >= len(text):
                break

        return chunks

    def chunk_by_sentences(self, text: str) -> List[str]:
        """
        Split text into chunks by sentences.

        More semantic than character-based chunking.

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        sentences = text.split(".")
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Add period back
            sentence_with_period = sentence + "."

            if len(current_chunk) + len(sentence_with_period) <= self.chunk_size:
                current_chunk += " " + sentence_with_period if current_chunk else sentence_with_period
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence_with_period

        if current_chunk:
            chunks.append(current_chunk)

        return chunks


class DocumentService:
    """Service for document management operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize document service.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session
        self.doc_repo = DocumentRepository(session)
        self.embedding_repo = EmbeddingRepository(session)
        self.chunker = DocumentChunker()

    async def create_document(
        self,
        user_id: str,
        filename: str,
        file_type: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> DocumentORM:
        """
        Create a new document.

        Args:
            user_id: User ID
            filename: Document filename
            file_type: File type (pdf, txt, docx, etc.)
            content: Document content
            metadata: Additional metadata

        Returns:
            Created document
        """
        if metadata is None:
            metadata = {}

        document = await self.doc_repo.create(
            user_id=user_id,
            filename=filename,
            file_type=file_type,
            content=content,
            total_chunks=0,
            metadata=metadata,
        )

        logger.info(f"Created document {document.id} for user {user_id}")
        return document

    async def chunk_and_store(
        self,
        document_id: UUID,
        content: str,
        embeddings: List[List[float]],
    ) -> int:
        """
        Chunk document content and store embeddings.

        Args:
            document_id: Document ID
            content: Document content
            embeddings: List of embedding vectors (must match chunks)

        Returns:
            Number of chunks created

        Raises:
            ValueError: If embeddings count doesn't match chunks count
        """
        # Chunk the content
        chunks = self.chunker.chunk_text(content)

        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Embeddings count ({len(embeddings)}) must match chunks count ({len(chunks)})"
            )

        # Create embedding objects
        embedding_objs = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            embedding_obj = EmbeddingORM(
                document_id=document_id,
                chunk_text=chunk,
                embedding=embedding,
                chunk_index=i,
                metadata={"source": "document", "chunk": i},
            )
            embedding_objs.append(embedding_obj)

        # Bulk create embeddings
        count = await self.embedding_repo.bulk_create_embeddings(embedding_objs)

        # Update document chunk count
        await self.doc_repo.update_chunk_count(document_id, count)

        logger.info(f"Created {count} embeddings for document {document_id}")
        return count

    async def delete_document(self, user_id: str, document_id: UUID) -> bool:
        """
        Delete a document (soft delete).

        Args:
            user_id: User ID
            document_id: Document ID

        Returns:
            True if deleted, False if not found
        """
        document = await self.doc_repo.get_user_document(user_id, document_id)
        if not document:
            return False

        # Soft delete document
        await self.doc_repo.soft_delete(document_id)

        # Soft delete embeddings
        await self.embedding_repo.soft_delete_document_embeddings(document_id)

        logger.info(f"Deleted document {document_id} for user {user_id}")
        return True

    async def get_document_summary(self, user_id: str, document_id: UUID) -> Optional[dict]:
        """
        Get document summary with chunk information.

        Args:
            user_id: User ID
            document_id: Document ID

        Returns:
            Document summary dict or None
        """
        document = await self.doc_repo.get_user_document(user_id, document_id)
        if not document:
            return None

        embedding_count = await self.embedding_repo.count_document_embeddings(document_id)

        return {
            "id": str(document.id),
            "filename": document.filename,
            "file_type": document.file_type,
            "total_chunks": document.total_chunks,
            "embedding_count": embedding_count,
            "created_at": document.created_at.isoformat(),
            "metadata": document.metadata,
        }
