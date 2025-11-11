"""Memory manager for Memori integration with Claude."""

import logging
from typing import Optional, Dict, Any, List

from memori import Memori

from src.memory.config import MemoriConfig, memory_config

logger = logging.getLogger(__name__)


class MemoryManager:
    """Manages Memori instances and Claude API integration."""

    def __init__(self, config: MemoriConfig = memory_config):
        """Initialize MemoryManager.

        Args:
            config: MemoriConfig instance with settings
        """
        self.config = config
        self._memori: Optional[Memori] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize Memori instance.

        This sets up the database connection and enables memory tracking
        for Claude API calls.
        """
        if self._initialized:
            logger.warning("MemoryManager already initialized")
            return

        if not self.config.enabled:
            logger.info("Memori is disabled in configuration")
            return

        try:
            # Create Memori instance with configuration
            memori_config = self.config.get_memori_config_dict()

            self._memori = Memori(
                **memori_config,
                api_key=self.config.anthropic_api_key,
            )

            # Enable global Memori recording
            self._memori.enable()

            logger.info("Memori initialized successfully")
            self._initialized = True

        except Exception as e:
            logger.error(f"Failed to initialize Memori: {str(e)}")
            raise

    async def shutdown(self) -> None:
        """Shutdown Memori instance and cleanup resources."""
        if self._memori:
            try:
                # Memori cleanup if needed
                logger.info("Memori shutdown completed")
            except Exception as e:
                logger.error(f"Error during Memori shutdown: {str(e)}")

        self._initialized = False

    def get_memori(self) -> Optional[Memori]:
        """Get the current Memori instance.

        Returns:
            Memori instance or None if not initialized
        """
        return self._memori

    async def add_memory(
        self,
        content: str,
        memory_type: str = "long_term",
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Add a memory to the system.

        Args:
            content: Memory content
            memory_type: Type of memory (short_term, long_term, rule, entity)
            importance: Importance score (0.0-1.0)
            tags: Optional list of tags
            metadata: Optional metadata dictionary

        Returns:
            True if successful, False otherwise
        """
        if not self._memori:
            logger.warning("Memori not initialized")
            return False

        try:
            # Add memory through Memori's API
            self._memori.add_memory(
                content=content,
                memory_type=memory_type,
                importance=importance,
                tags=tags or [],
                metadata=metadata or {},
            )
            logger.debug(f"Memory added: {memory_type} - {content[:50]}")
            return True
        except Exception as e:
            logger.error(f"Error adding memory: {str(e)}")
            return False

    async def search_memory(
        self,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 10,
        threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """Search memory by query.

        Args:
            query: Search query
            memory_type: Optional filter by memory type
            limit: Maximum number of results
            threshold: Relevance threshold (0.0-1.0)

        Returns:
            List of matching memories
        """
        if not self._memori:
            logger.warning("Memori not initialized")
            return []

        try:
            results = self._memori.search_memory(
                query=query,
                memory_type=memory_type,
                limit=limit,
                threshold=threshold,
            )
            return results
        except Exception as e:
            logger.error(f"Error searching memory: {str(e)}")
            return []

    async def get_conversation_context(
        self,
        conversation_id: str,
        max_memories: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get memory context for a specific conversation.

        Args:
            conversation_id: ID of the conversation
            max_memories: Maximum memories to retrieve

        Returns:
            List of relevant memories for the conversation
        """
        if not self._memori:
            logger.warning("Memori not initialized")
            return []

        try:
            # Retrieve memories for the conversation
            memories = self._memori.get_context_for_conversation(
                conversation_id=conversation_id,
                max_memories=max_memories,
            )
            return memories
        except Exception as e:
            logger.error(f"Error retrieving conversation context: {str(e)}")
            return []

    async def clear_memories(
        self,
        older_than_days: Optional[int] = None,
        memory_type: Optional[str] = None,
    ) -> int:
        """Clear memories based on criteria.

        Args:
            older_than_days: Clear memories older than N days
            memory_type: Only clear specific memory type

        Returns:
            Number of memories cleared
        """
        if not self._memori:
            logger.warning("Memori not initialized")
            return 0

        try:
            count = self._memori.clear_memories(
                older_than_days=older_than_days,
                memory_type=memory_type,
            )
            logger.info(f"Cleared {count} memories")
            return count
        except Exception as e:
            logger.error(f"Error clearing memories: {str(e)}")
            return 0

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics.

        Returns:
            Dictionary with memory statistics
        """
        if not self._memori:
            return {"initialized": False}

        try:
            stats = {
                "initialized": self._initialized,
                "total_memories": self._memori.get_memory_count(),
                "memory_by_type": self._memori.get_memory_distribution(),
                "database_size": self._memori.get_database_size(),
            }
            return stats
        except Exception as e:
            logger.error(f"Error retrieving memory stats: {str(e)}")
            return {"initialized": self._initialized, "error": str(e)}


# Global memory manager instance
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """Get or create the global memory manager instance.

    Returns:
        MemoryManager instance
    """
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager


async def initialize_memory_manager() -> MemoryManager:
    """Initialize the global memory manager.

    Returns:
        Initialized MemoryManager instance
    """
    manager = get_memory_manager()
    await manager.initialize()
    return manager
