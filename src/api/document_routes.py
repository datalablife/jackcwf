"""API routes for document management and RAG operations."""

import logging
import time
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.config import get_async_session
from src.services.document_service import DocumentService
from src.services.embedding_service import EmbeddingService
from src.schemas.document_schema import (
    DocumentSummary,
    DocumentListResponse,
    UploadDocumentResponse,
    SearchDocumentsRequest,
    SearchDocumentsResponse,
    SearchResult,
)
from src.utils.file_handler import FileHandler, validate_file_upload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["Documents"])


def get_user_id(request) -> str:
    """Extract user ID from request state."""
    return getattr(request.state, "user_id", "anonymous")


@router.post("", response_model=UploadDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_user_id),
):
    """
    Upload a document for RAG processing.

    **Parameters:**
    - **file**: Document file (PDF, TXT, DOCX, etc.)
    - **metadata**: Optional JSON metadata

    **Returns:**
    - Document ID and processing status

    **Performance Target:** ≤ 5000ms for processing
    """
    start_time = time.time()

    try:
        # Validate file upload
        validate_file_upload(file)

        # Parse metadata if provided
        import json
        metadata_dict = json.loads(metadata) if metadata else {}

        # Extract content from file
        file_handler = FileHandler()
        content = await file_handler.extract_text(file)

        if not content or len(content.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No text content could be extracted from the file",
            )

        # Create document service
        doc_service = DocumentService(session)

        # Create document record
        document = await doc_service.create_document(
            user_id=user_id,
            filename=file.filename,
            file_type=file_handler.detect_file_type(file.filename),
            content=content,
            metadata=metadata_dict,
        )

        # Chunk the content
        chunks = doc_service.chunker.chunk_text(content)
        logger.info(f"Created {len(chunks)} chunks from document {document.id}")

        # Generate embeddings
        embedding_service = EmbeddingService()
        embeddings = await embedding_service.embed_chunks(chunks)

        # Store chunks and embeddings
        chunk_count = await doc_service.chunk_and_store(
            document_id=document.id,
            content=content,
            embeddings=embeddings,
        )

        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(f"Document upload completed in {elapsed_ms:.2f}ms")

        # Check performance target
        if elapsed_ms > 5000:
            logger.warning(
                f"Document processing exceeded 5000ms target: {elapsed_ms:.2f}ms"
            )

        return UploadDocumentResponse(
            id=str(document.id),
            filename=document.filename,
            status="success",
            total_chunks=chunk_count,
            message=f"Document uploaded and processed successfully ({chunk_count} chunks created)",
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error uploading document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}",
        )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    skip: int = 0,
    limit: int = 10,
    file_type: Optional[str] = None,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_user_id),
):
    """
    List user's documents.

    **Parameters:**
    - **skip**: Number of documents to skip (default: 0)
    - **limit**: Maximum documents to return (default: 10)
    - **file_type**: Filter by file type (optional)

    **Returns:**
    - List of documents with pagination info
    """
    try:
        doc_service = DocumentService(session)

        # Get documents based on filter
        if file_type:
            documents = await doc_service.doc_repo.get_documents_by_type(
                user_id=user_id,
                file_type=file_type,
                skip=skip,
                limit=limit,
            )
        else:
            documents = await doc_service.doc_repo.get_user_documents(
                user_id=user_id,
                skip=skip,
                limit=limit,
            )

        # Get total count
        total = await doc_service.doc_repo.count_user_documents(user_id)

        # Build response items
        items = []
        for doc in documents:
            embedding_count = await doc_service.embedding_repo.count_document_embeddings(doc.id)
            items.append(
                DocumentSummary(
                    id=str(doc.id),
                    filename=doc.filename,
                    file_type=doc.file_type,
                    total_chunks=doc.total_chunks,
                    embedding_count=embedding_count,
                    created_at=doc.created_at,
                    metadata=doc.metadata,
                )
            )

        return DocumentListResponse(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
        )

    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list documents",
        )


@router.get("/{document_id}", response_model=DocumentSummary)
async def get_document(
    document_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_user_id),
):
    """
    Get a specific document.

    **Parameters:**
    - **document_id**: Document UUID

    **Returns:**
    - Document details with metadata
    """
    try:
        doc_service = DocumentService(session)

        summary = await doc_service.get_document_summary(user_id, document_id)

        if not summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        return DocumentSummary(**summary)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get document",
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_user_id),
):
    """
    Delete a document (soft delete).

    **Parameters:**
    - **document_id**: Document UUID

    **Note:** This soft deletes the document and all its embeddings.
    """
    try:
        doc_service = DocumentService(session)

        success = await doc_service.delete_document(user_id, document_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document",
        )


@router.post("/search", response_model=SearchDocumentsResponse)
async def search_documents(
    request_data: SearchDocumentsRequest,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_user_id),
):
    """
    Search documents using semantic similarity (RAG).

    **Parameters:**
    - **query**: Search query text
    - **limit**: Maximum results (default: 5, max: 20)
    - **threshold**: Similarity threshold (default: 0.7)

    **Returns:**
    - List of relevant document chunks with similarity scores

    **Performance Target:** ≤ 200ms P99
    """
    start_time = time.time()

    try:
        # Generate embedding for query
        embedding_service = EmbeddingService()
        query_embedding = await embedding_service.embed_text(request_data.query)

        # Search for similar embeddings
        doc_service = DocumentService(session)
        results = await doc_service.embedding_repo.search_similar(
            query_embedding=query_embedding,
            user_id=user_id,
            limit=request_data.limit,
            threshold=request_data.threshold,
        )

        # Calculate similarity scores
        similarities = embedding_service.batch_cosine_similarity(
            query_embedding=query_embedding,
            embeddings=[r.embedding for r in results],
        )

        # Build response
        search_results = []
        for embedding, similarity in zip(results, similarities):
            search_results.append(
                SearchResult(
                    document_id=str(embedding.document_id),
                    chunk_index=embedding.chunk_index,
                    chunk_text=embedding.chunk_text,
                    similarity=similarity,
                    metadata=embedding.metadata,
                )
            )

        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(f"Document search completed in {elapsed_ms:.2f}ms, found {len(search_results)} results")

        # Check performance target
        if elapsed_ms > 200:
            logger.warning(
                f"Document search exceeded 200ms target: {elapsed_ms:.2f}ms"
            )

        return SearchDocumentsResponse(
            query=request_data.query,
            results=search_results,
            total=len(search_results),
        )

    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search documents: {str(e)}",
        )


@router.get("/{document_id}/chunks", response_model=List[SearchResult])
async def get_document_chunks(
    document_id: UUID,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_user_id),
):
    """
    Get all chunks for a document.

    **Parameters:**
    - **document_id**: Document UUID
    - **skip**: Number of chunks to skip (default: 0)
    - **limit**: Maximum chunks to return (default: 100)

    **Returns:**
    - List of document chunks in order
    """
    try:
        doc_service = DocumentService(session)

        # Verify user owns the document
        document = await doc_service.doc_repo.get_user_document(user_id, document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        # Get embeddings for document
        embeddings = await doc_service.embedding_repo.search_by_document(
            document_id=document_id,
            skip=skip,
            limit=limit,
        )

        # Build response
        chunks = [
            SearchResult(
                document_id=str(embedding.document_id),
                chunk_index=embedding.chunk_index,
                chunk_text=embedding.chunk_text,
                similarity=1.0,  # Not a search result, so similarity is N/A
                metadata=embedding.metadata,
            )
            for embedding in embeddings
        ]

        return chunks

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document chunks: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get document chunks",
        )
