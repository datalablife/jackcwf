"""Pydantic schemas for document-related endpoints."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field


class DocumentSummary(BaseModel):
    """Summary of a document."""

    id: str = Field(..., description="Document ID")
    filename: str = Field(..., description="File name")
    file_type: str = Field(..., description="File type (pdf, txt, docx, etc.)")
    total_chunks: int = Field(..., description="Total chunks after splitting")
    embedding_count: int = Field(..., description="Number of embeddings")
    created_at: datetime = Field(..., description="Creation timestamp")
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")


class UploadDocumentRequest(BaseModel):
    """Request to upload a document."""

    filename: str = Field(..., min_length=1, description="Document filename")
    file_type: str = Field(
        ...,
        description="File type (pdf, txt, docx, etc.)",
    )
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")


class UploadDocumentResponse(BaseModel):
    """Response after uploading a document."""

    id: str = Field(..., description="Document ID")
    filename: str = Field(..., description="File name")
    status: str = Field(..., description="Upload status")
    total_chunks: int = Field(..., description="Total chunks created")
    message: str = Field(..., description="Status message")


class DocumentListResponse(BaseModel):
    """Response with list of documents."""

    items: List[DocumentSummary] = Field(..., description="List of documents")
    total: int = Field(..., description="Total count")
    skip: int = Field(..., description="Number skipped")
    limit: int = Field(..., description="Limit applied")


class SearchDocumentsRequest(BaseModel):
    """Request to search documents."""

    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(default=5, ge=1, le=20, description="Max results")
    threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Similarity threshold",
    )


class SearchResult(BaseModel):
    """Single search result."""

    document_id: str = Field(..., description="Document ID")
    chunk_index: int = Field(..., description="Chunk index in document")
    chunk_text: str = Field(..., description="Chunk text excerpt")
    similarity: float = Field(..., description="Similarity score (0-1)")
    metadata: Optional[dict] = Field(default=None, description="Chunk metadata")


class SearchDocumentsResponse(BaseModel):
    """Response with search results."""

    query: str = Field(..., description="Search query")
    results: List[SearchResult] = Field(..., description="Search results")
    total: int = Field(..., description="Total results found")
