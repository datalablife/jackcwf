"""Tests for Story 3.2.1 - Conversation CRUD endpoints."""

import pytest
import asyncio
from uuid import uuid4
from datetime import datetime
from typing import AsyncGenerator

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.main import app
from src.db.config import Base, get_async_session
from src.models import ConversationORM, MessageORM
from src.schemas.conversation_schema import (
    CreateConversationRequest,
    UpdateConversationRequest,
    ConversationResponse,
    ConversationListResponse,
)


# Test database setup (using in-memory SQLite)
@pytest.fixture
async def test_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    # Use in-memory SQLite for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_session():
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_async_session] = override_get_session

    async with async_session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def client(test_db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Set up auth in request state
        client.headers["Authorization"] = "Bearer test_token"
        yield client


@pytest.fixture
async def test_user_id() -> str:
    """Get test user ID."""
    return str(uuid4())


@pytest.fixture
async def test_conversation(
    test_db_session: AsyncSession, test_user_id: str
) -> ConversationORM:
    """Create a test conversation."""
    conversation = ConversationORM(
        id=uuid4(),
        user_id=test_user_id,
        title="Test Conversation",
        system_prompt="You are a helpful assistant.",
        model="claude-sonnet-4-5-20250929",
        meta={},
    )
    test_db_session.add(conversation)
    await test_db_session.commit()
    await test_db_session.refresh(conversation)
    return conversation


class TestConversationCRUD:
    """Test cases for conversation CRUD endpoints."""

    @pytest.mark.asyncio
    async def test_create_conversation(self, client: AsyncClient, test_user_id: str):
        """Test creating a new conversation."""
        request_data = {
            "title": "New Conversation",
            "system_prompt": "You are a helpful AI assistant.",
            "model": "claude-sonnet-4-5-20250929",
            "metadata": {"source": "test"},
        }

        # Mock the auth middleware
        with client.app.middleware_stack:
            response = await client.post(
                "/api/conversations",
                json=request_data,
                headers={"X-User-ID": test_user_id},
            )

        assert response.status_code in [200, 201], f"Response: {response.text}"
        data = response.json()
        assert data["title"] == "New Conversation"
        assert data["user_id"] == test_user_id
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_list_conversations(
        self, client: AsyncClient, test_user_id: str, test_conversation: ConversationORM
    ):
        """Test listing conversations with pagination."""
        response = await client.get(
            "/api/conversations?skip=0&limit=10",
            headers={"X-User-ID": test_user_id},
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_get_conversation(
        self, client: AsyncClient, test_user_id: str, test_conversation: ConversationORM
    ):
        """Test getting a specific conversation."""
        response = await client.get(
            f"/api/conversations/{test_conversation.id}",
            headers={"X-User-ID": test_user_id},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_conversation.id)
        assert data["title"] == test_conversation.title
        assert data["user_id"] == test_user_id

    @pytest.mark.asyncio
    async def test_update_conversation(
        self, client: AsyncClient, test_user_id: str, test_conversation: ConversationORM
    ):
        """Test updating a conversation."""
        update_data = {
            "title": "Updated Title",
            "summary": "This is a summary",
        }

        response = await client.put(
            f"/api/conversations/{test_conversation.id}",
            json=update_data,
            headers={"X-User-ID": test_user_id},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["summary"] == "This is a summary"

    @pytest.mark.asyncio
    async def test_delete_conversation(
        self, client: AsyncClient, test_user_id: str, test_conversation: ConversationORM
    ):
        """Test deleting a conversation."""
        response = await client.delete(
            f"/api/conversations/{test_conversation.id}",
            headers={"X-User-ID": test_user_id},
        )

        assert response.status_code == 204

        # Verify conversation is deleted
        response = await client.get(
            f"/api/conversations/{test_conversation.id}",
            headers={"X-User-ID": test_user_id},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_conversation_messages(
        self, client: AsyncClient, test_user_id: str, test_conversation: ConversationORM,
        test_db_session: AsyncSession
    ):
        """Test getting conversation message history."""
        # Add test messages
        msg1 = MessageORM(
            id=uuid4(),
            conversation_id=test_conversation.id,
            role="user",
            content="Hello",
            tokens_used=5,
        )
        msg2 = MessageORM(
            id=uuid4(),
            conversation_id=test_conversation.id,
            role="assistant",
            content="Hi there!",
            tokens_used=3,
        )
        test_db_session.add(msg1)
        test_db_session.add(msg2)
        await test_db_session.commit()

        response = await client.get(
            f"/api/conversations/{test_conversation.id}/messages?limit=50",
            headers={"X-User-ID": test_user_id},
        )

        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert "total_tokens" in data
        assert data["conversation_id"] == str(test_conversation.id)

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client: AsyncClient):
        """Test that unauthorized users cannot access conversations."""
        response = await client.get("/api/conversations")
        # Should fail without auth header
        assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_not_found_conversation(self, client: AsyncClient, test_user_id: str):
        """Test getting non-existent conversation."""
        fake_id = uuid4()
        response = await client.get(
            f"/api/conversations/{fake_id}",
            headers={"X-User-ID": test_user_id},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_conversation_response_schema(
        self, client: AsyncClient, test_user_id: str, test_conversation: ConversationORM
    ):
        """Test that response matches ConversationResponse schema."""
        response = await client.get(
            f"/api/conversations/{test_conversation.id}",
            headers={"X-User-ID": test_user_id},
        )

        assert response.status_code == 200
        data = response.json()

        # Validate schema
        conv = ConversationResponse(**data)
        assert conv.id == str(test_conversation.id)
        assert conv.title == test_conversation.title
        assert conv.user_id == test_user_id


class TestConversationPerformance:
    """Performance tests for conversation endpoints."""

    @pytest.mark.asyncio
    async def test_create_conversation_performance(
        self, client: AsyncClient, test_user_id: str
    ):
        """Test that conversation creation completes within <200ms."""
        import time

        request_data = {
            "title": "Performance Test",
            "system_prompt": "Test prompt",
        }

        start = time.time()
        response = await client.post(
            "/api/conversations",
            json=request_data,
            headers={"X-User-ID": test_user_id},
        )
        elapsed = (time.time() - start) * 1000  # Convert to ms

        assert response.status_code in [200, 201]
        assert elapsed < 200, f"Create conversation took {elapsed:.2f}ms (target: <200ms)"

    @pytest.mark.asyncio
    async def test_list_conversations_performance(
        self, client: AsyncClient, test_user_id: str
    ):
        """Test that listing conversations completes within <200ms."""
        import time

        start = time.time()
        response = await client.get(
            "/api/conversations?skip=0&limit=10",
            headers={"X-User-ID": test_user_id},
        )
        elapsed = (time.time() - start) * 1000  # Convert to ms

        assert response.status_code == 200
        assert elapsed < 200, f"List conversations took {elapsed:.2f}ms (target: <200ms)"

    @pytest.mark.asyncio
    async def test_get_conversation_performance(
        self, client: AsyncClient, test_user_id: str, test_conversation: ConversationORM
    ):
        """Test that getting a conversation completes within <200ms."""
        import time

        start = time.time()
        response = await client.get(
            f"/api/conversations/{test_conversation.id}",
            headers={"X-User-ID": test_user_id},
        )
        elapsed = (time.time() - start) * 1000  # Convert to ms

        assert response.status_code == 200
        assert elapsed < 200, f"Get conversation took {elapsed:.2f}ms (target: <200ms)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
