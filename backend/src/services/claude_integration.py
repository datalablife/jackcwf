"""Claude API integration service with Memori context injection."""

import json
import logging
from typing import Optional, List, Dict, Any

from anthropic import Anthropic

from src.memory.config import memory_config
from src.memory.manager import get_memory_manager

logger = logging.getLogger(__name__)


class ClaudeIntegrationService:
    """Service for Claude API integration with Memori context."""

    def __init__(self):
        """Initialize Claude integration service."""
        self.client: Optional[Anthropic] = None
        self.memory_manager = get_memory_manager()
        self.model = memory_config.claude_model
        self.max_tokens = memory_config.max_tokens

    async def initialize(self) -> None:
        """Initialize Anthropic client."""
        try:
            self.client = Anthropic(api_key=memory_config.anthropic_api_key)
            logger.info("Claude integration service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Claude client: {str(e)}")
            raise

    async def chat(
        self,
        messages: List[Dict[str, str]],
        conversation_id: Optional[str] = None,
        use_memory: bool = True,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a message to Claude with optional Memori context.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            conversation_id: Optional conversation ID for memory tracking
            use_memory: Whether to inject memory context
            system_prompt: Optional custom system prompt

        Returns:
            Response dictionary with 'content', 'usage', and 'stop_reason'
        """
        if not self.client:
            raise RuntimeError("Claude client not initialized. Call initialize() first.")

        # Build system prompt with memory context if enabled
        system_content = system_prompt or self._get_default_system_prompt()

        if use_memory and conversation_id:
            # Get relevant memories for this conversation
            memories = await self.memory_manager.search_memory(
                query=messages[-1]["content"] if messages else "",
                limit=5,
            )

            if memories:
                context = self._format_memory_context(memories)
                system_content += f"\n\n## Relevant Context:\n{context}"

        try:
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_content,
                messages=messages,
            )

            # Extract response data
            assistant_message = response.content[0].text if response.content else ""

            # Store interaction in memory if conversation_id provided
            if conversation_id:
                last_user_message = next(
                    (m["content"] for m in reversed(messages) if m["role"] == "user"),
                    "",
                )
                await self._store_interaction_in_memory(
                    conversation_id=conversation_id,
                    user_message=last_user_message,
                    assistant_message=assistant_message,
                )

            result = {
                "content": assistant_message,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
                "stop_reason": response.stop_reason,
                "model": response.model,
            }

            logger.debug(f"Claude response generated for conversation: {conversation_id}")
            return result

        except Exception as e:
            logger.error(f"Error calling Claude API: {str(e)}")
            raise

    async def chat_streaming(
        self,
        messages: List[Dict[str, str]],
        conversation_id: Optional[str] = None,
        use_memory: bool = True,
        system_prompt: Optional[str] = None,
    ):
        """Stream messages from Claude with optional Memori context.

        Args:
            messages: List of message dictionaries
            conversation_id: Optional conversation ID
            use_memory: Whether to inject memory context
            system_prompt: Optional custom system prompt

        Yields:
            Streamed text chunks from Claude
        """
        if not self.client:
            raise RuntimeError("Claude client not initialized. Call initialize() first.")

        # Build system prompt
        system_content = system_prompt or self._get_default_system_prompt()

        if use_memory and conversation_id:
            memories = await self.memory_manager.search_memory(
                query=messages[-1]["content"] if messages else "",
                limit=5,
            )

            if memories:
                context = self._format_memory_context(memories)
                system_content += f"\n\n## Relevant Context:\n{context}"

        try:
            full_response = ""

            with self.client.messages.stream(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_content,
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    full_response += text
                    yield text

            # Store in memory after streaming completes
            if conversation_id:
                last_user_message = next(
                    (m["content"] for m in reversed(messages) if m["role"] == "user"),
                    "",
                )
                await self._store_interaction_in_memory(
                    conversation_id=conversation_id,
                    user_message=last_user_message,
                    assistant_message=full_response,
                )

        except Exception as e:
            logger.error(f"Error in streaming response: {str(e)}")
            raise

    @staticmethod
    def _get_default_system_prompt() -> str:
        """Get default system prompt for Claude.

        Returns:
            Default system prompt
        """
        return (
            "You are a helpful AI assistant. You provide accurate, thoughtful, and "
            "well-reasoned responses. When relevant context is available, you use it "
            "to provide more personalized and accurate responses."
        )

    @staticmethod
    def _format_memory_context(memories: List[Dict[str, Any]]) -> str:
        """Format memories into context string.

        Args:
            memories: List of memory dictionaries

        Returns:
            Formatted context string
        """
        if not memories:
            return ""

        context_parts = []
        for i, memory in enumerate(memories, 1):
            content = memory.get("content", "")
            memory_type = memory.get("type", "unknown")
            importance = memory.get("importance", 0)
            context_parts.append(
                f"{i}. [{memory_type}] {content} (importance: {importance:.2f})"
            )

        return "\n".join(context_parts)

    async def _store_interaction_in_memory(
        self,
        conversation_id: str,
        user_message: str,
        assistant_message: str,
    ) -> None:
        """Store interaction in Memori for future context.

        Args:
            conversation_id: Conversation ID
            user_message: User's message
            assistant_message: Assistant's response
        """
        try:
            # Store as a conversation memory
            memory_content = (
                f"Conversation {conversation_id}:\n"
                f"User: {user_message[:200]}...\n"
                f"Assistant: {assistant_message[:200]}..."
            )

            await self.memory_manager.add_memory(
                content=memory_content,
                memory_type="long_term",
                importance=0.7,
                tags=["conversation", conversation_id],
                metadata={
                    "conversation_id": conversation_id,
                    "type": "interaction",
                },
            )
        except Exception as e:
            logger.warning(f"Failed to store interaction in memory: {str(e)}")


# Global Claude integration service instance
_claude_service: Optional[ClaudeIntegrationService] = None


def get_claude_service() -> ClaudeIntegrationService:
    """Get or create global Claude integration service.

    Returns:
        ClaudeIntegrationService instance
    """
    global _claude_service
    if _claude_service is None:
        _claude_service = ClaudeIntegrationService()
    return _claude_service


async def initialize_claude_service() -> ClaudeIntegrationService:
    """Initialize global Claude integration service.

    Returns:
        Initialized ClaudeIntegrationService instance
    """
    service = get_claude_service()
    await service.initialize()
    return service
