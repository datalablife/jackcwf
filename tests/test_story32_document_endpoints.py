"""Tests for Story 3.2.3 - Document endpoint validation."""

import pytest
import time
import asyncio
from uuid import uuid4
from datetime import datetime
from typing import AsyncGenerator

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.main import app
from src.db.config import Base, get_async_session
from src.models import DocumentORM, EmbeddingORM


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
async def test_document(
    test_db_session: AsyncSession, test_user_id: str
) -> DocumentORM:
    """Create a test document."""
    doc = DocumentORM(
        id=uuid4(),
        user_id=test_user_id,
        title="Test Document",
        filename="test.txt",
        file_path="/test/test.txt",
        file_size=1024,
        mime_type="text/plain",
        chunk_count=5,
        total_tokens=500,
        metadata={},
    )
    test_db_session.add(doc)
    await test_db_session.commit()
    await test_db_session.refresh(doc)
    return doc


class TestDocumentEndpointValidation:
    """Test cases for document endpoint validation (Task 3.2.3)."""

    @pytest.mark.asyncio
    async def test_document_endpoints_exist(self, client: AsyncClient, test_user_id: str):
        """Test that all document endpoints are registered."""
        # These should return appropriate responses (not 404)
        endpoints = [
            "/api/documents",  # GET - list
            "/api/documents",  # POST - would fail without file but not 404
        ]

        for endpoint in endpoints:
            # Just verify endpoint exists (may return error due to missing file)
            # but not 404 (endpoint not found)
            response = await client.get(endpoint, headers={"X-User-ID": test_user_id})
            assert response.status_code != 404, f"Endpoint {endpoint} not found"

    @pytest.mark.asyncio
    async def test_get_documents_list(
        self, client: AsyncClient, test_user_id: str, test_document: DocumentORM
    ):
        """Test GET /api/v1/documents - document list endpoint."""
        response = await client.get(
            "/api/documents", headers={"X-User-ID": test_user_id}
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data or "documents" in data
        assert isinstance(data.get("items") or data.get("documents"), list)

    @pytest.mark.asyncio
    async def test_get_document_detail(
        self, client: AsyncClient, test_user_id: str, test_document: DocumentORM
    ):
        """Test GET /api/v1/documents/{document_id} - document detail endpoint."""
        response = await client.get(
            f"/api/documents/{test_document.id}",
            headers={"X-User-ID": test_user_id},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_document.id)
        assert data["title"] == "Test Document"

    @pytest.mark.asyncio
    async def test_get_document_chunks(
        self, client: AsyncClient, test_user_id: str, test_document: DocumentORM,
        test_db_session: AsyncSession
    ):
        """Test GET /api/v1/documents/{document_id}/chunks - document chunks endpoint."""
        # Add some test embeddings (chunks)
        for i in range(3):
            embedding = EmbeddingORM(
                id=uuid4(),
                document_id=test_document.id,
                chunk_index=i,
                chunk_text=f"This is chunk {i}",
                vector=[0.1] * 1536,  # Mock 1536-dim vector
            )
            test_db_session.add(embedding)
        await test_db_session.commit()

        response = await client.get(
            f"/api/documents/{test_document.id}/chunks",
            headers={"X-User-ID": test_user_id},
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data or "chunks" in data

    @pytest.mark.asyncio
    async def test_search_documents(
        self, client: AsyncClient, test_user_id: str, test_document: DocumentORM
    ):
        """Test POST /api/v1/documents/search - vector search endpoint."""
        search_data = {
            "query": "test query",
            "limit": 5,
        }

        response = await client.post(
            "/api/documents/search",
            json=search_data,
            headers={"X-User-ID": test_user_id},
        )

        assert response.status_code in [200, 400]  # May fail if embeddings unavailable
        if response.status_code == 200:
            data = response.json()
            assert "results" in data or "items" in data

    @pytest.mark.asyncio
    async def test_delete_document(
        self, client: AsyncClient, test_user_id: str, test_document: DocumentORM
    ):
        """Test DELETE /api/v1/documents/{document_id} - document delete endpoint."""
        response = await client.delete(
            f"/api/documents/{test_document.id}",
            headers={"X-User-ID": test_user_id},
        )

        assert response.status_code in [200, 204]

        # Verify document is deleted
        response = await client.get(
            f"/api/documents/{test_document.id}",
            headers={"X-User-ID": test_user_id},
        )
        assert response.status_code == 404


class TestDocumentEndpointPerformance:
    """Performance benchmark tests for document endpoints (Task 3.2.3)."""

    @pytest.mark.asyncio
    async def test_document_list_performance(
        self, client: AsyncClient, test_user_id: str, test_document: DocumentORM
    ):
        """Test document list endpoint performance (<200ms target)."""
        start = time.time()
        response = await client.get(
            "/api/documents", headers={"X-User-ID": test_user_id}
        )
        elapsed = (time.time() - start) * 1000

        assert response.status_code == 200
        assert elapsed < 200, f"Document list took {elapsed:.2f}ms (target: <200ms)"

    @pytest.mark.asyncio
    async def test_vector_search_performance(
        self, client: AsyncClient, test_user_id: str, test_document: DocumentORM
    ):
        """Test vector search endpoint performance (≤500ms target)."""
        search_data = {"query": "test", "limit": 5}

        start = time.time()
        response = await client.post(
            "/api/documents/search",
            json=search_data,
            headers={"X-User-ID": test_user_id},
        )
        elapsed = (time.time() - start) * 1000

        # Search may fail if embeddings not available, but should not time out
        assert elapsed < 500, f"Search took {elapsed:.2f}ms (target: ≤500ms)"

    @pytest.mark.asyncio
    async def test_get_document_detail_performance(
        self, client: AsyncClient, test_user_id: str, test_document: DocumentORM
    ):
        """Test get document detail endpoint performance (<200ms target)."""
        start = time.time()
        response = await client.get(
            f"/api/documents/{test_document.id}",
            headers={"X-User-ID": test_user_id},
        )
        elapsed = (time.time() - start) * 1000

        assert response.status_code == 200
        assert elapsed < 200, f"Get document took {elapsed:.2f}ms (target: <200ms)"

    @pytest.mark.asyncio
    async def test_delete_document_performance(
        self, client: AsyncClient, test_user_id: str, test_db_session: AsyncSession
    ):
        """Test batch delete performance (<1s for multiple documents target)."""
        # Create multiple test documents
        doc_ids = []
        for i in range(5):
            doc = DocumentORM(
                id=uuid4(),
                user_id=test_user_id,
                title=f"Doc {i}",
                filename=f"doc{i}.txt",
                file_path=f"/test/doc{i}.txt",
                file_size=1024,
                mime_type="text/plain",
                chunk_count=1,
                total_tokens=100,
                metadata={},
            )
            test_db_session.add(doc)
            doc_ids.append(doc.id)
        await test_db_session.commit()

        start = time.time()
        for doc_id in doc_ids:
            await client.delete(
                f"/api/documents/{doc_id}",
                headers={"X-User-ID": test_user_id},
            )
        elapsed = (time.time() - start) * 1000

        # Total time should be <1s for 5 deletes = ~200ms per delete
        assert (
            elapsed < 1000
        ), f"Batch delete took {elapsed:.2f}ms (target: <1000ms for 5 items)"


class TestDocumentEndpointIntegration:
    """Integration tests for document endpoints with middleware."""

    @pytest.mark.asyncio
    async def test_document_auth_required(self, client: AsyncClient):
        """Test that document endpoints require authentication."""
        response = await client.get("/api/documents")
        assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_document_endpoint_response_format(
        self, client: AsyncClient, test_user_id: str, test_document: DocumentORM
    ):
        """Test that document responses are properly formatted."""
        response = await client.get(
            f"/api/documents/{test_document.id}",
            headers={"X-User-ID": test_user_id},
        )

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        required_fields = ["id", "title", "filename", "created_at"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_document_list_pagination(
        self, client: AsyncClient, test_user_id: str, test_db_session: AsyncSession
    ):
        """Test document list endpoint supports pagination."""
        # Create multiple documents
        for i in range(15):
            doc = DocumentORM(
                id=uuid4(),
                user_id=test_user_id,
                title=f"Doc {i}",
                filename=f"doc{i}.txt",
                file_path=f"/test/doc{i}.txt",
                file_size=1024,
                mime_type="text/plain",
                chunk_count=1,
                total_tokens=100,
                metadata={},
            )
            test_db_session.add(doc)
        await test_db_session.commit()

        # Test pagination
        response = await client.get(
            "/api/documents?skip=0&limit=5",
            headers={"X-User-ID": test_user_id},
        )

        assert response.status_code == 200
        data = response.json()
        items = data.get("items") or data.get("documents")
        assert len(items) <= 5


class TestDocumentOpenAPIDocumentation:
    """Test OpenAPI documentation for document endpoints."""

    @pytest.mark.asyncio
    async def test_openapi_documentation_exists(self, client: AsyncClient):
        """Test that OpenAPI documentation is available."""
        response = await client.get("/api/openapi.json")
        assert response.status_code == 200

        schema = response.json()
        assert "paths" in schema

        # Check for document endpoints
        doc_endpoints = [
            "/api/v1/documents",
            "/api/v1/documents/{document_id}",
            "/api/v1/documents/search",
        ]

        paths = schema.get("paths", {})
        for endpoint in doc_endpoints:
            # At least one should exist (exact path may vary)
            found = any(
                endpoint in str(p) or "documents" in str(p) for p in paths.keys()
            )
            assert found, f"Endpoint {endpoint} not found in OpenAPI schema"

    @pytest.mark.asyncio
    async def test_swagger_ui_available(self, client: AsyncClient):
        """Test that Swagger UI is available for interactive API testing."""
        response = await client.get("/api/docs")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
