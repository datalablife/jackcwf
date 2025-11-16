"""Conversation repository with business logic."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import ConversationORM
from src.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[ConversationORM]):
    """Repository for conversation management."""

    model_class = ConversationORM

    def __init__(self, session: AsyncSession):
        """Initialize repository."""
        super().__init__(session)

    async def get_user_conversations(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 10,
        include_deleted: bool = False,
    ) -> List[ConversationORM]:
        """
        Get all conversations for a user.

        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records
            include_deleted: Whether to include soft-deleted conversations

        Returns:
            List of conversations ordered by most recent first
        """
        query = select(ConversationORM).where(ConversationORM.user_id == user_id)

        if not include_deleted:
            query = query.where(ConversationORM.is_deleted == False)

        query = query.order_by(ConversationORM.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_user_conversation(
        self,
        user_id: str,
        conversation_id: UUID,
        include_deleted: bool = False,
    ) -> Optional[ConversationORM]:
        """
        Get a specific conversation for a user.

        Args:
            user_id: User ID
            conversation_id: Conversation ID
            include_deleted: Whether to include soft-deleted conversations

        Returns:
            Conversation instance or None
        """
        query = select(ConversationORM).where(
            and_(
                ConversationORM.user_id == user_id,
                ConversationORM.id == conversation_id,
            )
        )

        if not include_deleted:
            query = query.where(ConversationORM.is_deleted == False)

        result = await self.session.execute(query)
        return result.scalars().first()

    async def count_user_conversations(self, user_id: str) -> int:
        """
        Count active conversations for a user.

        Args:
            user_id: User ID

        Returns:
            Number of active conversations
        """
        return await self.count(user_id=user_id, is_deleted=False)

    async def soft_delete(self, conversation_id: UUID) -> bool:
        """
        Soft delete a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            True if deleted, False if not found
        """
        conversation = await self.get(conversation_id)
        if not conversation:
            return False

        conversation.is_deleted = True
        conversation.deleted_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(conversation)
        return True

    async def undelete(self, conversation_id: UUID) -> bool:
        """
        Restore a soft-deleted conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            True if restored, False if not found
        """
        query = select(ConversationORM).where(ConversationORM.id == conversation_id)
        result = await self.session.execute(query)
        conversation = result.scalars().first()

        if not conversation:
            return False

        conversation.is_deleted = False
        conversation.deleted_at = None

        await self.session.commit()
        await self.session.refresh(conversation)
        return True

    async def update_title_and_summary(
        self,
        conversation_id: UUID,
        title: str,
        summary: Optional[str] = None,
    ) -> Optional[ConversationORM]:
        """
        Update conversation title and summary.

        Args:
            conversation_id: Conversation ID
            title: New title
            summary: New summary (optional)

        Returns:
            Updated conversation or None
        """
        return await self.update(
            conversation_id,
            title=title,
            summary=summary,
        )

    async def search_by_title(
        self,
        user_id: str,
        search_term: str,
        skip: int = 0,
        limit: int = 10,
    ) -> List[ConversationORM]:
        """
        Search conversations by title.

        Args:
            user_id: User ID
            search_term: Search term
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of matching conversations
        """
        from sqlalchemy import func

        query = select(ConversationORM).where(
            and_(
                ConversationORM.user_id == user_id,
                ConversationORM.is_deleted == False,
                func.lower(ConversationORM.title).like(f"%{search_term.lower()}%"),
            )
        ).order_by(ConversationORM.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()
