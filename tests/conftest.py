"""Global pytest configuration and fixtures."""

import asyncio
import os
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from httpx import AsyncClient

from src.db.base import Base
from src.main import app
from src.models import ConversationORM, MessageORM, DocumentORM, EmbeddingORM


# Test database URL (in-memory SQLite for speed)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite+aiosqlite:///:memory:"
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create an instance of the default event loop for the test session.

    This fixture is required for pytest-asyncio to work properly.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def async_engine():
    """
    Create async database engine for testing.

    Uses in-memory SQLite for fast tests.
    Each test gets a fresh database.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create async database session for testing.

    Each test gets its own session that is rolled back after completion.
    """
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def client(async_session) -> AsyncGenerator[AsyncClient, None]:
    """
    Create FastAPI test client.

    Overrides database dependency to use test database.
    """
    from src.db.config import get_session

    async def override_get_session():
        yield async_session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ============================================================================
# Authentication Fixtures
# ============================================================================

@pytest.fixture
def test_user_id() -> str:
    """Test user ID."""
    return "test_user_123"


@pytest.fixture
def test_user_2_id() -> str:
    """Second test user ID for authorization tests."""
    return "test_user_456"


@pytest.fixture
def auth_headers(test_user_id) -> dict:
    """
    Authentication headers for test requests.

    In production, this would include JWT token.
    For tests, we use a simple user_id header.
    """
    return {
        "X-User-ID": test_user_id,
        "Content-Type": "application/json",
    }


@pytest.fixture
def auth_headers_user2(test_user_2_id) -> dict:
    """Authentication headers for second user."""
    return {
        "X-User-ID": test_user_2_id,
        "Content-Type": "application/json",
    }


# ============================================================================
# Model Fixtures - Conversation
# ============================================================================

@pytest.fixture
async def test_conversation(
    async_session: AsyncSession,
    test_user_id: str,
) -> ConversationORM:
    """Create a test conversation."""
    conversation = ConversationORM(
        user_id=test_user_id,
        title="Test Conversation",
        system_prompt="You are a helpful assistant.",
        model="claude-sonnet-4-5-20250929",
        metadata={},
    )
    async_session.add(conversation)
    await async_session.commit()
    await async_session.refresh(conversation)
    return conversation


@pytest.fixture
async def test_conversation_2(
    async_session: AsyncSession,
    test_user_2_id: str,
) -> ConversationORM:
    """Create a test conversation for second user."""
    conversation = ConversationORM(
        user_id=test_user_2_id,
        title="User 2 Conversation",
        system_prompt="You are a helpful assistant.",
        model="claude-sonnet-4-5-20250929",
        metadata={},
    )
    async_session.add(conversation)
    await async_session.commit()
    await async_session.refresh(conversation)
    return conversation


# ============================================================================
# Model Fixtures - Message
# ============================================================================

@pytest.fixture
async def test_message(
    async_session: AsyncSession,
    test_conversation: ConversationORM,
) -> MessageORM:
    """Create a test message."""
    message = MessageORM(
        conversation_id=test_conversation.id,
        role="user",
        content="Hello, how are you?",
        tokens_used=10,
        metadata={},
    )
    async_session.add(message)
    await async_session.commit()
    await async_session.refresh(message)
    return message


@pytest.fixture
async def test_messages(
    async_session: AsyncSession,
    test_conversation: ConversationORM,
) -> list[MessageORM]:
    """Create multiple test messages for a conversation."""
    messages = [
        MessageORM(
            conversation_id=test_conversation.id,
            role="user",
            content="What is Python?",
            tokens_used=5,
            metadata={},
        ),
        MessageORM(
            conversation_id=test_conversation.id,
            role="assistant",
            content="Python is a programming language.",
            tokens_used=15,
            metadata={},
        ),
        MessageORM(
            conversation_id=test_conversation.id,
            role="user",
            content="Tell me more.",
            tokens_used=5,
            metadata={},
        ),
    ]
    async_session.add_all(messages)
    await async_session.commit()
    for msg in messages:
        await async_session.refresh(msg)
    return messages


# ============================================================================
# Model Fixtures - Document
# ============================================================================

@pytest.fixture
async def test_document(
    async_session: AsyncSession,
    test_conversation: ConversationORM,
) -> DocumentORM:
    """Create a test document."""
    document = DocumentORM(
        conversation_id=test_conversation.id,
        title="Test Document",
        content="This is a test document for RAG.",
        source="test.txt",
        metadata={"type": "text"},
    )
    async_session.add(document)
    await async_session.commit()
    await async_session.refresh(document)
    return document


@pytest.fixture
async def test_documents(
    async_session: AsyncSession,
    test_conversation: ConversationORM,
) -> list[DocumentORM]:
    """Create multiple test documents."""
    documents = [
        DocumentORM(
            conversation_id=test_conversation.id,
            title="Document 1",
            content="Content about Python programming.",
            source="doc1.txt",
            metadata={},
        ),
        DocumentORM(
            conversation_id=test_conversation.id,
            title="Document 2",
            content="Content about FastAPI framework.",
            source="doc2.txt",
            metadata={},
        ),
        DocumentORM(
            conversation_id=test_conversation.id,
            title="Document 3",
            content="Content about LangChain library.",
            source="doc3.txt",
            metadata={},
        ),
    ]
    async_session.add_all(documents)
    await async_session.commit()
    for doc in documents:
        await async_session.refresh(doc)
    return documents


# ============================================================================
# Model Fixtures - Embedding
# ============================================================================

@pytest.fixture
async def test_embedding(
    async_session: AsyncSession,
    test_document: DocumentORM,
) -> EmbeddingORM:
    """Create a test embedding."""
    # Create a simple test embedding vector (1536 dimensions for OpenAI)
    test_vector = [0.1] * 1536

    embedding = EmbeddingORM(
        document_id=test_document.id,
        chunk_index=0,
        chunk_text="This is a test document for RAG.",
        embedding=test_vector,
        metadata={},
    )
    async_session.add(embedding)
    await async_session.commit()
    await async_session.refresh(embedding)
    return embedding


# ============================================================================
# Mock Fixtures - External Services
# ============================================================================

@pytest.fixture
def mock_openai_client() -> Mock:
    """
    Mock OpenAI client for embedding tests.

    Returns deterministic embeddings without API calls.
    """
    mock_client = Mock()
    mock_response = Mock()
    mock_response.data = [Mock(embedding=[0.1] * 1536)]
    mock_client.embeddings.create = AsyncMock(return_value=mock_response)
    return mock_client


@pytest.fixture
def mock_langchain_agent() -> Mock:
    """
    Mock LangChain agent for agent tests.

    Returns canned responses without LLM API calls.
    """
    mock_agent = Mock()
    mock_agent.invoke = AsyncMock(
        return_value={"output": "This is a test response from the agent."}
    )
    return mock_agent


@pytest.fixture
def mock_redis_client() -> Mock:
    """
    Mock Redis client for caching tests.

    Uses in-memory dict instead of Redis.
    """
    storage = {}

    mock_redis = Mock()
    mock_redis.get = AsyncMock(side_effect=lambda k: storage.get(k))
    mock_redis.set = AsyncMock(side_effect=lambda k, v, **kwargs: storage.update({k: v}))
    mock_redis.delete = AsyncMock(side_effect=lambda k: storage.pop(k, None))
    mock_redis.exists = AsyncMock(side_effect=lambda k: k in storage)

    return mock_redis


# ============================================================================
# Performance Testing Fixtures
# ============================================================================

@pytest.fixture
def performance_threshold():
    """Performance thresholds for tests."""
    return {
        "vector_search_ms": 200,  # Vector search should complete in <200ms
        "document_processing_ms": 5000,  # Document processing <5s
        "websocket_latency_ms": 100,  # WebSocket <100ms latency
        "api_response_ms": 1000,  # API responses <1s
    }


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def temp_upload_file(tmp_path):
    """Create a temporary upload file for testing."""
    file_path = tmp_path / "test_upload.txt"
    file_path.write_text("This is a test upload file for document processing.")
    return file_path


@pytest.fixture
def sample_conversation_data():
    """Sample conversation data for API tests."""
    return {
        "title": "API Test Conversation",
        "system_prompt": "You are a helpful AI assistant.",
        "model": "claude-sonnet-4-5-20250929",
        "metadata": {"source": "test"},
    }


@pytest.fixture
def sample_message_data():
    """Sample message data for API tests."""
    return {
        "role": "user",
        "content": "What is the meaning of life?",
    }


@pytest.fixture
def sample_document_data():
    """Sample document data for API tests."""
    return {
        "title": "Test Document",
        "content": "This is test content for RAG system.",
        "source": "test_api.txt",
        "metadata": {"category": "test"},
    }


# ============================================================================
# Markers
# ============================================================================

def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as a security test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running (>1s)"
    )
