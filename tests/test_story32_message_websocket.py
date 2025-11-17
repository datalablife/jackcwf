"""Tests for Story 3.2.2 - Message and WebSocket endpoints."""

import pytest
import json
import asyncio
from uuid import uuid4
from datetime import datetime
from typing import AsyncGenerator

from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.main import app
from src.db.config import Base, get_async_session
from src.models import ConversationORM, MessageORM
from src.schemas.message_schema import (
    MessageResponse,
    SendMessageSyncRequest,
    SendMessageSyncResponse,
    ChatCompletionChunk,
)


# Test database setup
@pytest.fixture
async def test_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
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


@pytest.fixture
async def test_messages(
    test_db_session: AsyncSession, test_conversation: ConversationORM
) -> list[MessageORM]:
    """Create test messages."""
    messages = [
        MessageORM(
            id=uuid4(),
            conversation_id=test_conversation.id,
            role="user",
            content="What is Python?",
            tokens_used=5,
        ),
        MessageORM(
            id=uuid4(),
            conversation_id=test_conversation.id,
            role="assistant",
            content="Python is a programming language.",
            tokens_used=8,
        ),
    ]
    for msg in messages:
        test_db_session.add(msg)
    await test_db_session.commit()
    for msg in messages:
        await test_db_session.refresh(msg)
    return messages


class TestMessageEndpoints:
    """Test cases for message endpoints."""

    @pytest.mark.asyncio
    async def test_get_messages_list(
        self,
        client: AsyncClient,
        test_user_id: str,
        test_conversation: ConversationORM,
        test_messages: list[MessageORM],
    ):
        """Test getting list of messages from a conversation."""
        response = await client.get(
            f"/api/conversations/{test_conversation.id}/messages",
            headers={"X-User-ID": test_user_id},
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data or "messages" in data
        assert isinstance(data.get("items") or data.get("messages"), list)

    @pytest.mark.asyncio
    async def test_get_message_detail(
        self,
        client: AsyncClient,
        test_user_id: str,
        test_conversation: ConversationORM,
        test_messages: list[MessageORM],
    ):
        """Test getting a specific message detail."""
        message = test_messages[0]
        response = await client.get(
            f"/api/conversations/{test_conversation.id}/messages/{message.id}",
            headers={"X-User-ID": test_user_id},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(message.id)
        assert data["role"] == "user"
        assert data["content"] == "What is Python?"

    @pytest.mark.asyncio
    async def test_update_message(
        self,
        client: AsyncClient,
        test_user_id: str,
        test_conversation: ConversationORM,
        test_messages: list[MessageORM],
    ):
        """Test updating a message's metadata or token count."""
        message = test_messages[0]
        update_data = {
            "tokens_used": 10,
            "metadata": {"flagged": True},
        }

        response = await client.put(
            f"/api/conversations/{test_conversation.id}/messages/{message.id}",
            json=update_data,
            headers={"X-User-ID": test_user_id},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tokens_used"] == 10

    @pytest.mark.asyncio
    async def test_delete_message(
        self,
        client: AsyncClient,
        test_user_id: str,
        test_conversation: ConversationORM,
        test_messages: list[MessageORM],
    ):
        """Test deleting a message."""
        message = test_messages[0]
        response = await client.delete(
            f"/api/conversations/{test_conversation.id}/messages/{message.id}",
            headers={"X-User-ID": test_user_id},
        )

        assert response.status_code == 204

        # Verify message is deleted
        response = await client.get(
            f"/api/conversations/{test_conversation.id}/messages/{message.id}",
            headers={"X-User-ID": test_user_id},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_send_message_sync(
        self,
        client: AsyncClient,
        test_user_id: str,
        test_conversation: ConversationORM,
    ):
        """Test sending a message synchronously."""
        request_data = {
            "content": "What is the weather?",
            "include_rag": True,
        }

        response = await client.post(
            f"/api/conversations/{test_conversation.id}/messages",
            json=request_data,
            headers={"X-User-ID": test_user_id},
        )

        # Should return user message at minimum
        assert response.status_code in [200, 201]
        data = response.json()
        assert "message_id" in data or "id" in data

    @pytest.mark.asyncio
    async def test_message_response_schema(
        self,
        client: AsyncClient,
        test_user_id: str,
        test_conversation: ConversationORM,
        test_messages: list[MessageORM],
    ):
        """Test that message response matches schema."""
        message = test_messages[0]
        response = await client.get(
            f"/api/conversations/{test_conversation.id}/messages/{message.id}",
            headers={"X-User-ID": test_user_id},
        )

        assert response.status_code == 200
        data = response.json()
        msg = MessageResponse(**data)
        assert msg.id == str(message.id)
        assert msg.role == "user"

    @pytest.mark.asyncio
    async def test_unauthorized_message_access(
        self, client: AsyncClient, test_conversation: ConversationORM
    ):
        """Test that unauthorized users cannot access messages."""
        response = await client.get(
            f"/api/conversations/{test_conversation.id}/messages"
        )
        assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_message_list_pagination(
        self,
        client: AsyncClient,
        test_user_id: str,
        test_conversation: ConversationORM,
        test_db_session: AsyncSession,
    ):
        """Test message list pagination."""
        # Add multiple messages
        for i in range(15):
            msg = MessageORM(
                id=uuid4(),
                conversation_id=test_conversation.id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}",
                tokens_used=5,
            )
            test_db_session.add(msg)
        await test_db_session.commit()

        response = await client.get(
            f"/api/conversations/{test_conversation.id}/messages?limit=10",
            headers={"X-User-ID": test_user_id},
        )

        assert response.status_code == 200
        data = response.json()
        messages = data.get("items") or data.get("messages")
        assert len(messages) <= 10

    @pytest.mark.asyncio
    async def test_message_performance(
        self,
        client: AsyncClient,
        test_user_id: str,
        test_conversation: ConversationORM,
        test_messages: list[MessageORM],
    ):
        """Test message endpoint performance (<500ms target)."""
        import time

        message = test_messages[0]
        start = time.time()
        response = await client.get(
            f"/api/conversations/{test_conversation.id}/messages/{message.id}",
            headers={"X-User-ID": test_user_id},
        )
        elapsed = (time.time() - start) * 1000  # Convert to ms

        assert response.status_code == 200
        assert elapsed < 500, f"Message endpoint took {elapsed:.2f}ms (target: <500ms)"


class TestWebSocketMessageFormat:
    """Test WebSocket message format validation."""

    def test_websocket_message_format(self):
        """Test WebSocket message format validation."""
        from src.schemas.message_schema import WebSocketMessage

        # Valid message
        msg = WebSocketMessage(
            type="message",
            content="Hello",
            include_rag=True,
            user_id="user123",
        )
        assert msg.type == "message"

        # Valid ping
        msg = WebSocketMessage(type="ping")
        assert msg.type == "ping"

    def test_chat_completion_chunk_format(self):
        """Test ChatCompletionChunk format validation."""
        from src.schemas.message_schema import ChatCompletionChunk

        # Message chunk
        chunk = ChatCompletionChunk(
            type="message_chunk",
            content="Hello",
            tokens=2,
        )
        assert chunk.type == "message_chunk"

        # Tool call
        chunk = ChatCompletionChunk(
            type="tool_call",
            tool_name="search",
            tool_input={"q": "test"},
            call_id="call_1",
        )
        assert chunk.type == "tool_call"

        # Tool result
        chunk = ChatCompletionChunk(
            type="tool_result",
            call_id="call_1",
            tool_result="Found 5 results",
        )
        assert chunk.type == "tool_result"

        # Complete state
        chunk = ChatCompletionChunk(
            type="complete_state",
            final_message="Done",
            total_tokens=150,
        )
        assert chunk.type == "complete_state"

        # Heartbeat
        chunk = ChatCompletionChunk(type="heartbeat")
        assert chunk.type == "heartbeat"

    def test_websocket_message_serialization(self):
        """Test WebSocket message serialization."""
        from src.schemas.message_schema import ChatCompletionChunk

        chunk = ChatCompletionChunk(
            type="message_chunk",
            content="Hello",
            tokens=2,
        )

        # Should be JSON serializable
        json_str = chunk.model_dump_json()
        assert json_str is not None
        data = json.loads(json_str)
        assert data["type"] == "message_chunk"


class TestWebSocketEventTypes:
    """Test WebSocket event type definitions."""

    def test_all_event_types_supported(self):
        """Test that all required event types are supported."""
        from src.schemas.message_schema import ChatCompletionChunk

        event_types = [
            "message_chunk",
            "tool_call",
            "tool_result",
            "complete_state",
            "error",
            "heartbeat",
        ]

        for event_type in event_types:
            # Should not raise validation error
            chunk = ChatCompletionChunk(type=event_type)
            assert chunk.type == event_type

    def test_tool_call_event_structure(self):
        """Test tool_call event structure."""
        from src.schemas.message_schema import ChatCompletionChunk

        chunk = ChatCompletionChunk(
            type="tool_call",
            tool_name="search_documents",
            tool_input={"query": "Python", "limit": 5},
            call_id="call_abc123",
        )

        assert chunk.type == "tool_call"
        assert chunk.tool_name == "search_documents"
        assert chunk.tool_input["query"] == "Python"
        assert chunk.call_id == "call_abc123"

    def test_tool_result_event_structure(self):
        """Test tool_result event structure."""
        from src.schemas.message_schema import ChatCompletionChunk

        result = {
            "count": 5,
            "documents": ["doc1", "doc2", "doc3", "doc4", "doc5"],
        }

        chunk = ChatCompletionChunk(
            type="tool_result",
            call_id="call_abc123",
            tool_result=result,
        )

        assert chunk.type == "tool_result"
        assert chunk.call_id == "call_abc123"
        assert chunk.tool_result["count"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
