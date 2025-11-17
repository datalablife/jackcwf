"""Document service for document management and chunking."""

import logging
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

import tiktoken
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import DocumentORM, EmbeddingORM
from src.repositories import DocumentRepository, EmbeddingRepository

logger = logging.getLogger(__name__)


class DocumentChunker:
    """
    Service for chunking documents into processable pieces.

    Splits documents into overlapping chunks using token-based approach.
    Suitable for embedding with proper semantic boundaries.

    Tokenizer: tiktoken (GPT-3.5-turbo encoding)
    Chunk size: 1000 tokens (default)
    Overlap: 200 tokens (default)
    """

    DEFAULT_CHUNK_SIZE = 1000  # tokens
    DEFAULT_CHUNK_OVERLAP = 200  # tokens

    def __init__(self, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_CHUNK_OVERLAP):
        """
        Initialize document chunker.

        Args:
            chunk_size: Number of tokens per chunk (default 1000)
            overlap: Number of overlapping tokens between chunks (default 200)
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        # Use GPT-3.5-turbo encoding for consistency
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks with overlap using token-based approach.

        Args:
            text: Text to chunk

        Returns:
            List of text chunks

        Raises:
            ValueError: If text is empty or tokenization fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty for chunking")

        try:
            # Tokenize the text
            tokens = self.tokenizer.encode(text)
            logger.info(f"Tokenized text into {len(tokens)} tokens")

            if len(tokens) == 0:
                raise ValueError("Text produced no tokens after tokenization")

            chunks: List[str] = []
            step = self.chunk_size - self.overlap

            # Create chunks with overlap
            for i in range(0, len(tokens), step):
                chunk_tokens = tokens[i : i + self.chunk_size]

                # Decode tokens back to text
                chunk_text = self.tokenizer.decode(chunk_tokens)

                if chunk_text.strip():  # Skip empty chunks
                    chunks.append(chunk_text)

                # If this is the last chunk and it's smaller than chunk_size, break
                if i + self.chunk_size >= len(tokens):
                    break

            logger.info(f"Created {len(chunks)} chunks from text")
            return chunks

        except Exception as e:
            logger.error(f"Error chunking text: {str(e)}")
            raise

    def chunk_text_with_metadata(
        self,
        text: str,
        document_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Split text into chunks and include metadata for each chunk.

        Args:
            text: Text to chunk
            document_metadata: Metadata to include (e.g., page, section)

        Returns:
            List of (chunk_text, chunk_metadata) tuples

        Raises:
            ValueError: If text is empty
        """
        if document_metadata is None:
            document_metadata = {}

        chunks = self.chunk_text(text)
        chunks_with_metadata: List[Tuple[str, Dict[str, Any]]] = []

        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                **document_metadata,
                "chunk_index": i,
                "chunk_count": len(chunks),
                "tokens": len(self.tokenizer.encode(chunk)),
            }
            chunks_with_metadata.append((chunk, chunk_metadata))

        return chunks_with_metadata

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
            "meta": document.meta,
        }
