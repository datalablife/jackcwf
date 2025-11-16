"""Conversation service for managing conversations and messages."""

import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.models import ConversationORM, MessageORM
from src.repositories import ConversationRepository, MessageRepository

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for conversation management operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize conversation service.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session
        self.conv_repo = ConversationRepository(session)
        self.msg_repo = MessageRepository(session)

    async def create_conversation(
        self,
        user_id: str,
        title: str,
        system_prompt: str,
        model: str = "claude-sonnet-4-5-20250929",
        metadata: Optional[dict] = None,
    ) -> ConversationORM:
        """
        Create a new conversation.

        Args:
            user_id: User ID
            title: Conversation title
            system_prompt: System prompt for the conversation
            model: Model name (default: claude-sonnet-4-5-20250929)
            metadata: Additional metadata

        Returns:
            Created conversation
        """
        if metadata is None:
            metadata = {}

        conversation = await self.conv_repo.create(
            user_id=user_id,
            title=title,
            system_prompt=system_prompt,
            model=model,
            metadata=metadata,
        )

        logger.info(f"Created conversation {conversation.id} for user {user_id}")
        return conversation

    async def add_message(
        self,
        conversation_id: UUID,
        role: str,  # 'user', 'assistant', 'system'
        content: str,
        tool_calls: Optional[dict] = None,
        tool_results: Optional[dict] = None,
        tokens_used: Optional[int] = None,
    ) -> MessageORM:
        """
        Add a message to a conversation.

        Args:
            conversation_id: Conversation ID
            role: Message role
            content: Message content
            tool_calls: Tool calls made by assistant
            tool_results: Results from tool calls
            tokens_used: Number of tokens used

        Returns:
            Created message
        """
        message = await self.msg_repo.create(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
            tool_results=tool_results,
            tokens_used=tokens_used,
            metadata={},
        )

        logger.info(f"Added {role} message to conversation {conversation_id}")
        return message

    async def get_conversation_history(
        self,
        user_id: str,
        conversation_id: UUID,
        limit: int = 50,
    ) -> List[MessageORM]:
        """
        Get conversation history for a user.

        Args:
            user_id: User ID
            conversation_id: Conversation ID
            limit: Maximum number of messages

        Returns:
            List of messages in chronological order
        """
        # Verify conversation belongs to user
        conversation = await self.conv_repo.get_user_conversation(user_id, conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found for user {user_id}")

        return await self.msg_repo.get_conversation_messages(
            conversation_id=conversation_id,
            limit=limit,
        )

    async def get_conversation_context(
        self,
        user_id: str,
        conversation_id: UUID,
        max_messages: int = 10,
    ) -> dict:
        """
        Get conversation context for LangChain agent.

        Args:
            user_id: User ID
            conversation_id: Conversation ID
            max_messages: Maximum recent messages to include

        Returns:
            Conversation context dict with system prompt and recent messages
        """
        # Get conversation
        conversation = await self.conv_repo.get_user_conversation(user_id, conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found for user {user_id}")

        # Get recent messages
        messages = await self.msg_repo.get_conversation_messages_desc(
            conversation_id=conversation_id,
            limit=max_messages,
        )

        # Format messages for LangChain
        formatted_messages = [
            {
                "role": msg.role,
                "content": msg.content,
                "tool_calls": msg.tool_calls,
                "tool_results": msg.tool_results,
            }
            for msg in messages
        ]

        return {
            "conversation_id": str(conversation.id),
            "system_prompt": conversation.system_prompt,
            "model": conversation.model,
            "messages": formatted_messages,
            "message_count": await self.msg_repo.get_conversation_message_count(conversation_id),
        }

    async def delete_conversation(self, user_id: str, conversation_id: UUID) -> bool:
        """
        Delete a conversation (soft delete).

        Args:
            user_id: User ID
            conversation_id: Conversation ID

        Returns:
            True if deleted, False if not found
        """
        conversation = await self.conv_repo.get_user_conversation(user_id, conversation_id)
        if not conversation:
            return False

        # Delete all messages first
        await self.msg_repo.delete_conversation_messages(conversation_id)

        # Soft delete conversation
        await self.conv_repo.soft_delete(conversation_id)

        logger.info(f"Deleted conversation {conversation_id} for user {user_id}")
        return True

    async def update_conversation_summary(
        self,
        user_id: str,
        conversation_id: UUID,
        summary: str,
    ) -> Optional[ConversationORM]:
        """
        Update conversation summary (usually auto-generated).

        Args:
            user_id: User ID
            conversation_id: Conversation ID
            summary: Summary text

        Returns:
            Updated conversation or None
        """
        conversation = await self.conv_repo.get_user_conversation(user_id, conversation_id)
        if not conversation:
            return None

        return await self.conv_repo.update_title_and_summary(
            conversation_id=conversation_id,
            title=conversation.title,  # Keep existing title
            summary=summary,
        )

    async def list_conversations(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[List[ConversationORM], int]:
        """
        List conversations for a user with pagination.

        Args:
            user_id: User ID
            skip: Number of conversations to skip
            limit: Maximum number of conversations

        Returns:
            Tuple of (conversations list, total count)
        """
        conversations = await self.conv_repo.get_user_conversations(
            user_id=user_id,
            skip=skip,
            limit=limit,
        )

        total = await self.conv_repo.count_user_conversations(user_id)

        return conversations, total
