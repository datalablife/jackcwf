"""Memory injection middleware for conversation context management."""

from typing import Any, Dict, List
from langchain_core.messages import BaseMessage, SystemMessage
from src.services.middleware import AgentMiddleware
import logging

logger = logging.getLogger(__name__)


class MemoryInjectionMiddleware(AgentMiddleware):
    """
    Injects user context and conversation memory into agent state.

    Features:
    - Load user preferences
    - Inject previous conversation summaries
    - Add entity/topic memory
    - Maintain conversation context window

    Usage:
        middleware = MemoryInjectionMiddleware(
            max_memory_messages=20
        )
    """

    def __init__(self, max_memory_messages: int = 20):
        """
        Initialize memory injection.

        Args:
            max_memory_messages: Max messages to keep in context
        """
        super().__init__("memory_injection")
        self.max_memory_messages = max_memory_messages

    async def before_agent(
        self,
        messages: List[BaseMessage],
        state: Dict[str, Any],
    ) -> tuple[List[BaseMessage], Dict[str, Any]]:
        """
        Inject memory before processing.

        In production, would:
        1. Load user preferences from database
        2. Retrieve conversation summary
        3. Extract key entities from history
        4. Inject relevant context
        """
        if "memory" not in state:
            state["memory"] = {
                "conversation_summary": None,
                "key_entities": [],
                "user_preferences": {},
                "message_count": 0,
            }

        # Track message count
        state["memory"]["message_count"] = len(messages)

        # Trim message history if too long (keeping budget)
        if len(messages) > self.max_memory_messages:
            logger.info(
                f"Trimming message history from {len(messages)} to "
                f"{self.max_memory_messages} messages"
            )
            # Keep system message + recent messages
            system_msgs = [m for m in messages if isinstance(m, SystemMessage)]
            other_msgs = [m for m in messages if not isinstance(m, SystemMessage)]

            # Keep recent non-system messages
            kept_msgs = other_msgs[-(self.max_memory_messages - len(system_msgs)):]
            messages = system_msgs + kept_msgs

            # Note: in production, would summarize trimmed messages
            state["memory"]["conversation_summary"] = (
                "Previous context was summarized due to token limits."
            )

        return messages, state

    async def after_agent(
        self,
        final_response: str,
        state: Dict[str, Any],
    ) -> tuple[str, Dict[str, Any]]:
        """Save memory state after processing."""
        if "memory" in state:
            self.logger.info(
                f"Memory state: {state['memory']['message_count']} messages, "
                f"{len(state['memory']['key_entities'])} entities tracked"
            )

        return final_response, state
