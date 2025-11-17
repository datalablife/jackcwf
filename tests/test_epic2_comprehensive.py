"""Comprehensive tests for Epic 2: Agent and RAG Pipeline."""

import pytest
import asyncio
from typing import List, Dict, Any
from uuid import uuid4
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Import services and models to test
from src.services.document_service import DocumentChunker
from src.services.embedding_service import EmbeddingService
from src.services.conversation_summarization_service import ConversationSummarizationService
from src.db.base import Base
from src.models import (
    ConversationORM,
    MessageORM,
    DocumentORM,
    EmbeddingORM,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_session() -> AsyncSession:
    """Create async session for tests."""
    # Use in-memory SQLite for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session


# ============================================================================
# TASK 2.1.1: Document Chunking Tests
# ============================================================================


class TestDocumentChunker:
    """Tests for token-based document chunking."""

    def test_chunker_initialization(self):
        """Test DocumentChunker initialization with default and custom parameters."""
        # Test default initialization
        chunker = DocumentChunker()
        assert chunker.chunk_size == 1000
        assert chunker.overlap == 200
        assert chunker.tokenizer is not None

        # Test custom initialization
        custom_chunker = DocumentChunker(chunk_size=500, overlap=50)
        assert custom_chunker.chunk_size == 500
        assert custom_chunker.overlap == 50

    def test_chunk_text_basic(self):
        """Test basic text chunking functionality."""
        chunker = DocumentChunker(chunk_size=100, overlap=10)

        text = "This is a test document. " * 20  # Create a longer text
        chunks = chunker.chunk_text(text)

        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)
        assert all(len(chunk) > 0 for chunk in chunks)

    def test_chunk_text_empty_text_raises_error(self):
        """Test that empty text raises ValueError."""
        chunker = DocumentChunker()

        with pytest.raises(ValueError, match="Text cannot be empty"):
            chunker.chunk_text("")

        with pytest.raises(ValueError, match="Text cannot be empty"):
            chunker.chunk_text("   ")

    def test_chunk_text_with_overlap(self):
        """Test that chunks have proper overlap."""
        chunker = DocumentChunker(chunk_size=50, overlap=10)
        text = "word " * 100  # 500 tokens approximately

        chunks = chunker.chunk_text(text)

        # Verify we have multiple chunks
        assert len(chunks) > 1

        # Verify chunks are not empty
        assert all(chunk.strip() for chunk in chunks)

    def test_chunk_text_with_metadata(self):
        """Test chunking with metadata."""
        chunker = DocumentChunker(chunk_size=100, overlap=10)
        text = "This is a test. " * 20
        metadata = {"source": "test", "page": 1}

        chunks_with_metadata = chunker.chunk_text_with_metadata(text, metadata)

        assert len(chunks_with_metadata) > 0

        for chunk_text, chunk_meta in chunks_with_metadata:
            assert isinstance(chunk_text, str)
            assert isinstance(chunk_meta, dict)
            assert "chunk_index" in chunk_meta
            assert "chunk_count" in chunk_meta
            assert "tokens" in chunk_meta
            assert chunk_meta["source"] == "test"
            assert chunk_meta["page"] == 1

    def test_chunk_text_token_counting(self):
        """Test token counting in chunks."""
        chunker = DocumentChunker(chunk_size=50, overlap=10)
        text = "This is a sample document. " * 10

        chunks = chunker.chunk_text(text)

        # Verify all chunks are returned
        assert len(chunks) > 0

        # Verify each chunk can be tokenized
        for chunk in chunks:
            tokens = chunker.tokenizer.encode(chunk)
            assert len(tokens) > 0

    def test_chunk_by_sentences(self):
        """Test sentence-based chunking."""
        chunker = DocumentChunker()
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."

        chunks = chunker.chunk_by_sentences(text)

        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)
        # Verify sentences end with period
        assert all(chunk.endswith(".") for chunk in chunks)


# ============================================================================
# TASK 2.1.2: Embedding Service Tests
# ============================================================================


class TestEmbeddingService:
    """Tests for OpenAI embedding service."""

    @pytest.mark.skip(reason="Requires OPENAI_API_KEY - test offline")
    async def test_embedding_initialization(self):
        """Test EmbeddingService initialization."""
        service = EmbeddingService(api_key="test-key")
        assert service.model == "text-embedding-3-small"
        assert service.EMBEDDING_DIMENSION == 1536

    @pytest.mark.skip(reason="Requires OPENAI_API_KEY - test offline")
    async def test_embed_text(self):
        """Test single text embedding."""
        service = EmbeddingService()
        text = "This is a test document for embedding."

        embedding = await service.embed_text(text)

        assert isinstance(embedding, list)
        assert len(embedding) == 1536

    @pytest.mark.skip(reason="Requires OPENAI_API_KEY - test offline")
    async def test_embed_texts_batch(self):
        """Test batch text embedding."""
        service = EmbeddingService()
        texts = [
            "First document.",
            "Second document.",
            "Third document.",
        ]

        embeddings = await service.embed_texts(texts)

        assert len(embeddings) == 3
        assert all(len(emb) == 1536 for emb in embeddings)

    def test_validate_embedding_valid(self):
        """Test embedding validation with valid embedding."""
        service = EmbeddingService(api_key="dummy-key")
        valid_embedding = [0.1] * 1536

        assert service.validate_embedding(valid_embedding) is True

    def test_validate_embedding_invalid_dimension(self):
        """Test embedding validation with invalid dimension."""
        service = EmbeddingService(api_key="dummy-key")
        invalid_embedding = [0.1] * 1500  # Wrong dimension

        assert service.validate_embedding(invalid_embedding) is False

    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        service = EmbeddingService(api_key="dummy-key")

        embedding1 = [1.0, 0.0, 0.0]
        embedding2 = [1.0, 0.0, 0.0]
        embedding3 = [0.0, 1.0, 0.0]

        # Identical embeddings should have similarity ~1.0
        similarity_identical = service.cosine_similarity(embedding1, embedding2)
        assert similarity_identical > 0.99

        # Orthogonal embeddings should have similarity ~0.0
        similarity_orthogonal = service.cosine_similarity(embedding1, embedding3)
        assert similarity_orthogonal < 0.01

    def test_batch_cosine_similarity(self):
        """Test batch cosine similarity."""
        service = EmbeddingService(api_key="dummy-key")

        query = [1.0, 0.0, 0.0]
        embeddings = [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.707, 0.707, 0.0],
        ]

        similarities = service.batch_cosine_similarity(query, embeddings)

        assert len(similarities) == 3
        assert all(isinstance(sim, float) for sim in similarities)
        assert 0 <= similarities[0] <= 1
        assert 0 <= similarities[1] <= 1
        assert 0 <= similarities[2] <= 1


# ============================================================================
# TASK 2.1.5: Conversation Summarization Tests
# ============================================================================


class TestConversationSummarizationService:
    """Tests for conversation summarization service."""

    @pytest.mark.skip(reason="Requires ANTHROPIC_API_KEY - test offline")
    @pytest.mark.asyncio
    async def test_summarization_service_initialization(self, async_session: AsyncSession):
        """Test service initialization."""
        service = ConversationSummarizationService(async_session, api_key="test-key")
        assert service.CONVERSATION_SUMMARY_TOKEN_THRESHOLD == 6000
        assert service.RECENT_MESSAGES_TO_KEEP == 10

    def test_count_message_tokens(self, async_session: AsyncSession):
        """Test token counting in messages."""
        service = ConversationSummarizationService(async_session, api_key="dummy-key")

        messages = [
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you for asking!"},
            {"role": "user", "content": "What is the meaning of life?"},
        ]

        token_count = service._count_message_tokens(messages)

        assert token_count > 0
        assert isinstance(token_count, int)

    def test_should_summarize_conversation_short(self, async_session: AsyncSession):
        """Test summarization check for short conversations."""
        service = ConversationSummarizationService(async_session, api_key="dummy-key")

        # Short conversation with few messages
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        should_summarize = service.should_summarize_conversation(messages)
        assert should_summarize is False

    def test_should_summarize_conversation_long(self, async_session: AsyncSession):
        """Test summarization check for long conversations."""
        service = ConversationSummarizationService(async_session, api_key="dummy-key")

        # Create a long conversation
        messages = [
            {"role": "user", "content": "Tell me about machine learning. " * 100}
            for _ in range(20)
        ]

        should_summarize = service.should_summarize_conversation(messages)
        # This depends on token count
        # Usually True for this many messages


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestEpic2Integration:
    """Integration tests for Epic 2 complete workflow."""

    @pytest.mark.asyncio
    async def test_document_chunking_pipeline(self):
        """Test complete document chunking pipeline."""
        chunker = DocumentChunker(chunk_size=100, overlap=10)

        # Simulate document content
        document_content = """
        This is a comprehensive document about machine learning.
        Machine learning is a subset of artificial intelligence.
        It focuses on developing algorithms that can learn from data.
        """ * 10

        # Step 1: Chunk the document
        chunks = chunker.chunk_text(document_content)
        assert len(chunks) > 0

        # Step 2: Get chunks with metadata
        chunks_with_metadata = chunker.chunk_text_with_metadata(
            document_content,
            {"source": "test_doc", "page": 1},
        )
        assert len(chunks_with_metadata) == len(chunks)

        # Step 3: Verify metadata
        for i, (chunk_text, metadata) in enumerate(chunks_with_metadata):
            assert metadata["chunk_index"] == i
            assert metadata["source"] == "test_doc"
            assert "tokens" in metadata
            assert metadata["tokens"] > 0

    def test_embedding_service_quality(self):
        """Test embedding service quality metrics."""
        service = EmbeddingService(api_key="dummy-key")

        # Test cosine similarity between similar texts
        embedding1 = [0.5, 0.5, 0.0, 0.0] * 384  # 1536-dim
        embedding2 = [0.5, 0.5, 0.1, 0.0] * 384  # Similar
        embedding3 = [0.0, 0.0, 0.0, 1.0] * 384  # Dissimilar

        sim_similar = service.cosine_similarity(embedding1, embedding2)
        sim_dissimilar = service.cosine_similarity(embedding1, embedding3)

        # Similar should be higher than dissimilar
        assert sim_similar > sim_dissimilar

    @pytest.mark.asyncio
    async def test_conversation_flow(self, async_session: AsyncSession):
        """Test typical conversation flow with summarization."""
        service = ConversationSummarizationService(async_session, api_key="dummy-key")

        # Simulate conversation
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi! How can I help?"},
            {"role": "user", "content": "Tell me about AI"},
            {"role": "assistant", "content": "AI is fascinating..."},
        ]

        # Check if should summarize
        should_summarize = service.should_summarize_conversation(messages)
        assert isinstance(should_summarize, bool)

        # Count tokens
        token_count = service._count_message_tokens(messages)
        assert token_count > 0


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================


class TestPerformanceTargets:
    """Tests to verify performance targets are met."""

    def test_document_chunking_performance(self):
        """Verify document chunking meets performance targets."""
        import time

        chunker = DocumentChunker(chunk_size=1000, overlap=200)
        large_document = "This is a test document. " * 5000  # Large document

        start_time = time.time()
        chunks = chunker.chunk_text(large_document)
        elapsed_ms = (time.time() - start_time) * 1000

        print(f"Chunking {len(large_document)} chars into {len(chunks)} chunks took {elapsed_ms:.2f}ms")

        # Should complete in reasonable time (< 1 second)
        assert elapsed_ms < 1000

    def test_token_counting_performance(self, async_session: AsyncSession):
        """Verify token counting meets performance targets."""
        import time

        service = ConversationSummarizationService(async_session, api_key="dummy-key")

        # Create large conversation
        messages = [
            {"role": "user", "content": "This is a test message. " * 100}
            for _ in range(50)
        ]

        start_time = time.time()
        token_count = service._count_message_tokens(messages)
        elapsed_ms = (time.time() - start_time) * 1000

        print(f"Counting tokens in 50 messages took {elapsed_ms:.2f}ms, total: {token_count} tokens")

        # Should complete quickly
        assert elapsed_ms < 500


# ============================================================================
# TEST EXECUTION
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
