"""
Example usage of Memori and Claude integration in Text2SQL backend.

This example demonstrates:
1. Initializing Memori memory management
2. Adding memories to the system
3. Searching for relevant memories
4. Using Claude with memory context injection
5. Managing conversation context
"""

import asyncio
import logging
from typing import Optional

from src.memory.config import MemoriConfig
from src.memory.manager import MemoryManager
from src.services.claude_integration import ClaudeIntegrationService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_basic_memory_operations():
    """Example 1: Basic memory operations."""
    logger.info("=" * 60)
    logger.info("Example 1: Basic Memory Operations")
    logger.info("=" * 60)

    # Create memory configuration
    config = MemoriConfig(
        enabled=True,
        db_type="sqlite",
        sqlite_path="./memori_example.db",
        conscious_ingest=True,
        auto_ingest=True,
    )

    # Create and initialize memory manager
    manager = MemoryManager(config=config)
    await manager.initialize()

    # Add various types of memories
    memories_to_add = [
        {
            "content": "User prefers concise responses with examples",
            "memory_type": "entity",
            "importance": 0.8,
            "tags": ["user_preference", "communication_style"],
        },
        {
            "content": "Always validate SQL queries before execution",
            "memory_type": "rule",
            "importance": 0.9,
            "tags": ["safety", "sql_handling"],
        },
        {
            "content": "Previously discussed integrating PostgreSQL with the system",
            "memory_type": "long_term",
            "importance": 0.7,
            "tags": ["database", "postgresql"],
        },
        {
            "content": "User mentioned timezone issues in last session",
            "memory_type": "short_term",
            "importance": 0.6,
            "tags": ["issue", "timezone"],
        },
    ]

    logger.info("\nAdding memories to system...")
    for memory in memories_to_add:
        success = await manager.add_memory(
            content=memory["content"],
            memory_type=memory["memory_type"],
            importance=memory["importance"],
            tags=memory["tags"],
        )
        logger.info(f"  ✓ Added {memory['memory_type']}: {memory['content'][:40]}...")

    # Get system statistics
    logger.info("\nMemory System Statistics:")
    stats = await manager.get_memory_stats()
    logger.info(f"  Total Memories: {stats.get('total_memories', 0)}")
    logger.info(f"  Memory by Type: {stats.get('memory_by_type', {})}")


async def example_memory_search():
    """Example 2: Searching memories."""
    logger.info("\n" + "=" * 60)
    logger.info("Example 2: Memory Search")
    logger.info("=" * 60)

    config = MemoriConfig(
        enabled=True,
        db_type="sqlite",
        sqlite_path="./memori_example.db",
    )

    manager = MemoryManager(config=config)
    await manager.initialize()

    # Search for relevant memories
    search_queries = [
        "database configuration",
        "SQL validation",
        "user preferences",
        "timezone issues",
    ]

    logger.info("\nSearching for relevant memories...\n")
    for query in search_queries:
        results = await manager.search_memory(
            query=query,
            limit=5,
            threshold=0.0,
        )

        logger.info(f"Query: '{query}'")
        if results:
            for i, memory in enumerate(results, 1):
                logger.info(
                    f"  {i}. [{memory.get('type', 'unknown')}] "
                    f"{memory.get('content', '')[:50]}..."
                )
        else:
            logger.info("  No matches found")


async def example_claude_with_memory():
    """Example 3: Claude chat with memory context."""
    logger.info("\n" + "=" * 60)
    logger.info("Example 3: Claude Chat with Memory Context")
    logger.info("=" * 60)

    # Initialize services
    claude_service = ClaudeIntegrationService()

    # Note: Requires ANTHROPIC_API_KEY environment variable
    try:
        await claude_service.initialize()
    except Exception as e:
        logger.warning(f"Claude service initialization skipped: {str(e)}")
        logger.info("Set ANTHROPIC_API_KEY environment variable to test Claude integration")
        return

    # Simulate a conversation with memory context
    conversation_id = "example_conv_001"

    logger.info("\nStarting conversation with Claude...\n")

    messages = [
        {
            "role": "user",
            "content": "How should I structure my database for the data source integration?",
        }
    ]

    try:
        response = await claude_service.chat(
            messages=messages,
            conversation_id=conversation_id,
            use_memory=True,
            system_prompt=None,  # Use default system prompt
        )

        logger.info("User: How should I structure my database for the data source integration?")
        logger.info(f"\nAssistant: {response['content'][:200]}...\n")
        logger.info(f"Tokens used - Input: {response['usage']['input_tokens']}, "
                    f"Output: {response['usage']['output_tokens']}")

    except Exception as e:
        logger.error(f"Error in Claude chat: {str(e)}")


async def example_conversation_context():
    """Example 4: Managing conversation context."""
    logger.info("\n" + "=" * 60)
    logger.info("Example 4: Conversation Context Management")
    logger.info("=" * 60)

    config = MemoriConfig(
        enabled=True,
        db_type="sqlite",
        sqlite_path="./memori_example.db",
    )

    manager = MemoryManager(config=config)
    await manager.initialize()

    conversation_id = "example_conv_002"

    logger.info(f"\nRetrieving context for conversation: {conversation_id}\n")

    memories = await manager.get_conversation_context(
        conversation_id=conversation_id,
        max_memories=5,
    )

    if memories:
        logger.info("Relevant memories for conversation:")
        for i, memory in enumerate(memories, 1):
            logger.info(
                f"  {i}. {memory.get('content', '')[:60]}... "
                f"(Type: {memory.get('type', 'unknown')})"
            )
    else:
        logger.info("No memories found for this conversation")


async def example_api_usage():
    """Example 5: API endpoint usage demonstration."""
    logger.info("\n" + "=" * 60)
    logger.info("Example 5: API Endpoint Usage")
    logger.info("=" * 60)

    logger.info("""
The following API endpoints are available:

Memory Management:
  POST   /api/memory/add
    - Add a new memory to the system

  POST   /api/memory/search
    - Search for memories by query

  GET    /api/memory/search?query=...
    - Search memories (GET variant)

  GET    /api/memory/context/{conversation_id}
    - Get memory context for a conversation

  GET    /api/memory/stats
    - Get memory system statistics

  DELETE /api/memory/clear
    - Clear old memories

Claude Integration:
  POST   /api/memory/claude/message
    - Send a message to Claude with memory context

  GET    /api/memory/health
    - Check memory system health

Example curl commands:

# Add a memory
curl -X POST http://localhost:8000/api/memory/add \\
  -H "Content-Type: application/json" \\
  -d '{
    "content": "User prefers SQL queries over ORM",
    "memory_type": "entity",
    "importance": 0.8,
    "tags": ["user_preference"]
  }'

# Search memories
curl "http://localhost:8000/api/memory/search?query=SQL&limit=5"

# Get memory stats
curl "http://localhost:8000/api/memory/stats"

# Send message to Claude with memory
curl -X POST http://localhost:8000/api/memory/claude/message \\
  -H "Content-Type: application/json" \\
  -d '{
    "content": "Help me optimize my database queries",
    "conversation_id": "conv_123",
    "use_memory": true
  }'
    """)


async def example_memory_organization():
    """Example 6: Memory organization and importance scoring."""
    logger.info("\n" + "=" * 60)
    logger.info("Example 6: Memory Organization Best Practices")
    logger.info("=" * 60)

    logger.info("""
Memory Types and Their Use Cases:

1. SHORT_TERM (importance: 0.3-0.6)
   - Recent conversation snippets
   - Current task context
   - Temporary notes
   - Usage: Quick recall within a session

2. LONG_TERM (importance: 0.5-0.9)
   - User preferences and patterns
   - Learned facts and knowledge
   - Historical interactions
   - Usage: Persistent context across sessions

3. RULES (importance: 0.7-1.0)
   - System constraints and requirements
   - Best practices and guidelines
   - Security policies
   - Usage: Always-applicable constraints

4. ENTITIES (importance: 0.4-0.8)
   - Named entities (users, databases, APIs)
   - Relationships and attributes
   - Metadata
   - Usage: Reference data for context

Importance Scoring Guide:
  0.9-1.0: Critical rules, security constraints
  0.7-0.8: User preferences, important facts
  0.5-0.6: General context, conversation history
  0.3-0.4: Low-priority notes
  0.0-0.2: Archived or deprecated info

Tags Strategy:
  - Use descriptive, lowercase tags
  - Link related memories with common tags
  - Examples: #database, #sql_validation, #user_preference
  - Helps in organization and discovery
    """)


async def main():
    """Run all examples."""
    logger.info("\n" + "=" * 80)
    logger.info("MEMORI & CLAUDE INTEGRATION EXAMPLES")
    logger.info("=" * 80)

    try:
        # Run examples
        await example_basic_memory_operations()
        await example_memory_search()
        await example_claude_with_memory()
        await example_conversation_context()
        await example_api_usage()
        await example_memory_organization()

        logger.info("\n" + "=" * 80)
        logger.info("Examples completed successfully!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Error running examples: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
