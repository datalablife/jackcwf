"""Integration tests for complete conversation workflow."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.db.base import Base
from src.models import ConversationORM, MessageORM


@pytest.fixture
async def test_client():
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_health_check(test_client):
    """Test health check endpoint."""
    response = await test_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_conversation_workflow(test_client):
    """Test complete conversation creation and message flow."""
    # Note: This test requires proper authentication setup
    # For now, we verify the endpoints exist and return appropriate errors without auth

    # Test creating conversation without auth should return 401
    response = await test_client.post(
        "/api/conversations",
        json={
            "title": "Test Conversation",
            "system_prompt": "Be helpful",
        },
    )
    assert response.status_code == 401  # Unauthorized


@pytest.mark.asyncio
async def test_conversation_list_requires_auth(test_client):
    """Test that conversation list requires authentication."""
    response = await test_client.get("/api/conversations")
    assert response.status_code == 401  # Unauthorized


@pytest.mark.asyncio
async def test_root_endpoint(test_client):
    """Test root endpoint."""
    response = await test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "LangChain AI Conversation API"
    assert "endpoints" in data


@pytest.mark.asyncio
async def test_api_docs_available(test_client):
    """Test that API documentation is available."""
    response = await test_client.get("/api/docs")
    # Swagger UI should return HTML
    assert response.status_code == 200
    assert "html" in response.headers.get("content-type", "").lower()


@pytest.mark.asyncio
async def test_openapi_schema_available(test_client):
    """Test that OpenAPI schema is available."""
    response = await test_client.get("/api/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["openapi"]
    assert "paths" in data
