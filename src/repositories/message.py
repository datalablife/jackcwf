"""Message repository with conversation history management."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import MessageORM
from src.repositories.base import BaseRepository


class MessageRepository(BaseRepository[MessageORM]):
    """Repository for message management."""

    model_class = MessageORM

    def __init__(self, session: AsyncSession):
        """Initialize repository."""
        super().__init__(session)

    async def get_conversation_messages(
        self,
        conversation_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> List[MessageORM]:
        """
        Get messages from a conversation.

        Args:
            conversation_id: Conversation ID
            skip: Number of messages to skip
            limit: Maximum number of messages

        Returns:
            List of messages ordered chronologically
        """
        query = (
            select(MessageORM)
            .where(MessageORM.conversation_id == conversation_id)
            .order_by(MessageORM.created_at.asc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_conversation_messages_desc(
        self,
        conversation_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> List[MessageORM]:
        """
        Get messages from a conversation in reverse chronological order.

        Useful for getting recent messages first.

        Args:
            conversation_id: Conversation ID
            skip: Number of messages to skip
            limit: Maximum number of messages

        Returns:
            List of messages ordered by most recent first
        """
        query = (
            select(MessageORM)
            .where(MessageORM.conversation_id == conversation_id)
            .order_by(MessageORM.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(query)
        # Reverse to get chronological order
        return list(reversed(result.scalars().all()))

    async def get_conversation_message_count(self, conversation_id: UUID) -> int:
        """
        Count messages in a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            Number of messages
        """
        return await self.count(conversation_id=conversation_id)

    async def get_messages_by_role(
        self,
        conversation_id: UUID,
        role: str,  # 'user', 'assistant', 'system'
        skip: int = 0,
        limit: int = 50,
    ) -> List[MessageORM]:
        """
        Get messages from a conversation filtered by role.

        Args:
            conversation_id: Conversation ID
            role: Message role ('user', 'assistant', 'system')
            skip: Number of messages to skip
            limit: Maximum number of messages

        Returns:
            List of messages with specified role
        """
        query = (
            select(MessageORM)
            .where(
                and_(
                    MessageORM.conversation_id == conversation_id,
                    MessageORM.role == role,
                )
            )
            .order_by(MessageORM.created_at.asc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_last_user_message(
        self,
        conversation_id: UUID,
    ) -> Optional[MessageORM]:
        """
        Get the last user message in a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            Last user message or None
        """
        query = (
            select(MessageORM)
            .where(
                and_(
                    MessageORM.conversation_id == conversation_id,
                    MessageORM.role == "user",
                )
            )
            .order_by(MessageORM.created_at.desc())
            .limit(1)
        )

        result = await self.session.execute(query)
        return result.scalars().first()

    async def update_tool_results(
        self,
        message_id: UUID,
        tool_results: dict,
    ) -> Optional[MessageORM]:
        """
        Update tool results for an assistant message.

        Args:
            message_id: Message ID
            tool_results: Tool results dictionary

        Returns:
            Updated message or None
        """
        return await self.update(message_id, tool_results=tool_results)

    async def delete_conversation_messages(self, conversation_id: UUID) -> int:
        """
        Delete all messages from a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            Number of deleted messages
        """
        query = select(MessageORM).where(MessageORM.conversation_id == conversation_id)
        result = await self.session.execute(query)
        messages = result.scalars().all()

        for message in messages:
            await self.session.delete(message)

        await self.session.commit()
        return len(messages)

    async def get_messages_with_tokens(
        self,
        conversation_id: UUID,
    ) -> tuple[List[MessageORM], int]:
        """
        Get all messages from a conversation with total token count.

        Args:
            conversation_id: Conversation ID

        Returns:
            Tuple of (messages list, total tokens used)
        """
        messages = await self.get_conversation_messages(conversation_id, limit=1000)

        total_tokens = sum(msg.tokens_used or 0 for msg in messages)

        return messages, total_tokens
