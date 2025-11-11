"""Integration tests for Memori and Claude integration."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.memory.config import MemoriConfig
from src.memory.manager import MemoryManager, get_memory_manager
from src.services.claude_integration import ClaudeIntegrationService


@pytest.fixture
def memory_config():
    """Create test memory configuration."""
    return MemoriConfig(
        enabled=True,
        db_type="sqlite",
        sqlite_path=":memory:",  # Use in-memory SQLite for testing
        conscious_ingest=True,
        auto_ingest=True,
    )


@pytest.fixture
def memory_manager(memory_config):
    """Create memory manager for testing."""
    return MemoryManager(config=memory_config)


@pytest.fixture
def claude_service():
    """Create Claude service for testing."""
    return ClaudeIntegrationService()


@pytest.mark.asyncio
async def test_memory_manager_initialization(memory_manager):
    """Test MemoryManager initialization."""
    assert not memory_manager._initialized

    # Note: Actual initialization requires Memori library
    # This test checks the structure
    assert memory_manager.config.enabled
    assert memory_manager.config.db_type == "sqlite"


@pytest.mark.asyncio
async def test_memory_manager_add_memory(memory_manager):
    """Test adding memory through MemoryManager."""
    # Mock the Memori instance
    with patch.object(memory_manager, "_memori") as mock_memori:
        memory_manager._initialized = True
        mock_memori.add_memory.return_value = None

        success = await memory_manager.add_memory(
            content="Test memory content",
            memory_type="long_term",
            importance=0.8,
            tags=["test", "example"],
        )

        assert success
        mock_memori.add_memory.assert_called_once()


@pytest.mark.asyncio
async def test_memory_manager_search(memory_manager):
    """Test searching memory."""
    # Mock the Memori instance
    with patch.object(memory_manager, "_memori") as mock_memori:
        memory_manager._initialized = True
        mock_results = [
            {
                "id": "1",
                "content": "Test memory",
                "type": "long_term",
                "importance": 0.8,
            }
        ]
        mock_memori.search_memory.return_value = mock_results

        results = await memory_manager.search_memory(
            query="test",
            limit=10,
        )

        assert len(results) == 1
        assert results[0]["content"] == "Test memory"
        mock_memori.search_memory.assert_called_once()


@pytest.mark.asyncio
async def test_memory_manager_stats(memory_manager):
    """Test getting memory statistics."""
    # Mock the Memori instance
    with patch.object(memory_manager, "_memori") as mock_memori:
        memory_manager._initialized = True
        mock_memori.get_memory_count.return_value = 42
        mock_memori.get_memory_distribution.return_value = {
            "short_term": 10,
            "long_term": 32,
        }
        mock_memori.get_database_size.return_value = 1.5

        stats = await memory_manager.get_memory_stats()

        assert stats["initialized"]
        assert stats["total_memories"] == 42
        assert stats["memory_by_type"]["short_term"] == 10


@pytest.mark.asyncio
async def test_claude_service_initialization(claude_service):
    """Test Claude service initialization."""
    with patch("src.services.claude_integration.Anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        await claude_service.initialize()

        assert claude_service.client is not None
        mock_anthropic.assert_called_once()


@pytest.mark.asyncio
async def test_claude_service_chat(claude_service):
    """Test Claude chat with memory context."""
    # Setup mock client
    mock_client = MagicMock()
    claude_service.client = mock_client

    # Mock response
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Test response")]
    mock_response.usage.input_tokens = 10
    mock_response.usage.output_tokens = 5
    mock_response.stop_reason = "end_turn"
    mock_response.model = "claude-3-5-sonnet-20241022"
    mock_client.messages.create.return_value = mock_response

    # Mock memory manager
    with patch.object(claude_service.memory_manager, "search_memory") as mock_search:
        mock_search.return_value = [
            {
                "content": "Previous context",
                "type": "long_term",
                "importance": 0.9,
            }
        ]

        messages = [{"role": "user", "content": "Hello Claude"}]
        result = await claude_service.chat(
            messages=messages,
            conversation_id="conv_123",
            use_memory=True,
        )

        assert result["content"] == "Test response"
        assert result["usage"]["input_tokens"] == 10
        assert result["stop_reason"] == "end_turn"
        mock_client.messages.create.assert_called_once()


@pytest.mark.asyncio
async def test_claude_service_system_prompt_generation(claude_service):
    """Test system prompt generation for Claude."""
    prompt = claude_service._get_default_system_prompt()

    assert isinstance(prompt, str)
    assert "helpful" in prompt.lower()
    assert "context" in prompt.lower()


@pytest.mark.asyncio
async def test_memory_context_formatting(claude_service):
    """Test memory context formatting."""
    memories = [
        {
            "content": "First memory",
            "type": "long_term",
            "importance": 0.9,
        },
        {
            "content": "Second memory",
            "type": "short_term",
            "importance": 0.5,
        },
    ]

    context = claude_service._format_memory_context(memories)

    assert "First memory" in context
    assert "Second memory" in context
    assert "long_term" in context
    assert "short_term" in context
    assert "0.90" in context or "0.9" in context


def test_config_db_connection_strings():
    """Test database connection string generation."""
    # PostgreSQL config
    pg_config = MemoriConfig(
        db_type="postgresql",
        db_host="localhost",
        db_port=5432,
        db_name="memori_db",
        db_user="postgres",
        db_password="password",
    )
    pg_conn = pg_config.db_connection_string
    assert "postgresql" in pg_conn
    assert "localhost:5432" in pg_conn
    assert "memori_db" in pg_conn

    # SQLite config
    sqlite_config = MemoriConfig(
        db_type="sqlite",
        sqlite_path="/tmp/memori.db",
    )
    sqlite_conn = sqlite_config.db_connection_string
    assert "sqlite" in sqlite_conn
    assert "/tmp/memori.db" in sqlite_conn


def test_config_get_memori_config_dict():
    """Test getting Memori configuration dictionary."""
    config = MemoriConfig(
        conscious_ingest=True,
        auto_ingest=True,
        enable_semantic_search=True,
    )

    memori_dict = config.get_memori_config_dict()

    assert memori_dict["conscious_ingest"] is True
    assert memori_dict["auto_ingest"] is True
    assert memori_dict["enable_semantic_search"] is True


@pytest.mark.asyncio
async def test_get_memory_manager_singleton():
    """Test that get_memory_manager returns singleton."""
    manager1 = get_memory_manager()
    manager2 = get_memory_manager()

    assert manager1 is manager2
