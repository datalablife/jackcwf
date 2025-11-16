"""Unit tests for BaseRepository CRUD operations."""

import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker

from src.db.base import Base
from src.models import ConversationORM
from src.repositories.base import BaseRepository


class TestRepository(BaseRepository[ConversationORM]):
    """Test repository for testing."""
    model_class = ConversationORM


@pytest.fixture
async def test_db() -> AsyncEngine:
    """Create test database."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def test_session(test_db) -> AsyncSession:
    """Create test session."""
    async_session = sessionmaker(test_db, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.mark.asyncio
async def test_create(test_session):
    """Test create operation."""
    repo = TestRepository(test_session)

    conv = await repo.create(
        user_id="user_1",
        title="Test Conversation",
        system_prompt="Be helpful",
        model="claude-sonnet",
    )

    assert conv.id is not None
    assert conv.user_id == "user_1"
    assert conv.title == "Test Conversation"


@pytest.mark.asyncio
async def test_get(test_session):
    """Test get operation."""
    repo = TestRepository(test_session)

    conv = await repo.create(
        user_id="user_1",
        title="Test",
        system_prompt="test",
        model="claude",
    )

    retrieved = await repo.get(conv.id)
    assert retrieved is not None
    assert retrieved.id == conv.id
    assert retrieved.user_id == "user_1"


@pytest.mark.asyncio
async def test_get_nonexistent(test_session):
    """Test get with nonexistent ID."""
    repo = TestRepository(test_session)

    result = await repo.get(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_update(test_session):
    """Test update operation."""
    repo = TestRepository(test_session)

    conv = await repo.create(
        user_id="user_1",
        title="Original",
        system_prompt="test",
        model="claude",
    )

    updated = await repo.update(conv.id, title="Updated")
    assert updated is not None
    assert updated.title == "Updated"


@pytest.mark.asyncio
async def test_delete(test_session):
    """Test delete operation."""
    repo = TestRepository(test_session)

    conv = await repo.create(
        user_id="user_1",
        title="Test",
        system_prompt="test",
        model="claude",
    )

    deleted = await repo.delete(conv.id)
    assert deleted is True

    retrieved = await repo.get(conv.id)
    assert retrieved is None


@pytest.mark.asyncio
async def test_list(test_session):
    """Test list operation."""
    repo = TestRepository(test_session)

    # Create multiple conversations
    for i in range(5):
        await repo.create(
            user_id=f"user_{i}",
            title=f"Conv {i}",
            system_prompt="test",
            model="claude",
        )

    # List with limit
    items = await repo.list(limit=3)
    assert len(items) == 3

    # List with skip
    items = await repo.list(skip=2, limit=3)
    assert len(items) == 3


@pytest.mark.asyncio
async def test_count(test_session):
    """Test count operation."""
    repo = TestRepository(test_session)

    # Create conversations
    for i in range(5):
        await repo.create(
            user_id="user_1",
            title=f"Conv {i}",
            system_prompt="test",
            model="claude",
        )

    count = await repo.count(user_id="user_1")
    assert count == 5


@pytest.mark.asyncio
async def test_exists(test_session):
    """Test exists operation."""
    repo = TestRepository(test_session)

    conv = await repo.create(
        user_id="user_1",
        title="Test",
        system_prompt="test",
        model="claude",
    )

    exists = await repo.exists(id=conv.id)
    assert exists is True

    exists = await repo.exists(id=uuid4())
    assert exists is False


@pytest.mark.asyncio
async def test_bulk_create(test_session):
    """Test bulk create operation."""
    repo = TestRepository(test_session)

    # Create instances
    instances = [
        ConversationORM(
            user_id="user_1",
            title=f"Conv {i}",
            system_prompt="test",
            model="claude",
        )
        for i in range(10)
    ]

    created = await repo.bulk_create(instances)
    assert len(created) == 10
    assert all(inst.id is not None for inst in created)


@pytest.mark.asyncio
async def test_bulk_delete(test_session):
    """Test bulk delete operation."""
    repo = TestRepository(test_session)

    # Create instances
    instances = [
        ConversationORM(
            user_id="user_1",
            title=f"Conv {i}",
            system_prompt="test",
            model="claude",
        )
        for i in range(5)
    ]

    created = await repo.bulk_create(instances)
    ids = [inst.id for inst in created]

    # Delete
    deleted_count = await repo.bulk_delete(ids)
    assert deleted_count == 5


@pytest.mark.asyncio
async def test_transaction_rollback_on_create_error(test_session):
    """Test transaction rollback on create error."""
    repo = TestRepository(test_session)

    # Try to create with invalid data (missing required field)
    with pytest.raises(Exception):
        await repo.create(
            user_id="user_1",
            # Missing title
            system_prompt="test",
            model="claude",
        )

    # Verify session is still usable
    count = await repo.count()
    assert count == 0
