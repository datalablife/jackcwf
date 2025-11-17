"""Conversation summarization service for managing long conversations."""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

import tiktoken
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories import ConversationRepository

logger = logging.getLogger(__name__)


class ConversationSummarizationService:
    """
    Service for handling long conversation context compression.

    Automatically summarizes older messages to prevent token overflow
    while maintaining context and semantic meaning.

    Configuration:
    - Token threshold: 6000 tokens
    - Keep recent: 10 most recent messages
    - Summarize: older messages
    """

    # Configuration constants
    CONVERSATION_SUMMARY_TOKEN_THRESHOLD = 6000
    RECENT_MESSAGES_TO_KEEP = 10
    TOKENIZER_ENCODING = "cl100k_base"  # GPT-3.5-turbo encoding

    def __init__(self, session: AsyncSession, api_key: Optional[str] = None):
        """
        Initialize conversation summarization service.

        Args:
            session: SQLAlchemy async session
            api_key: Anthropic API key (uses ANTHROPIC_API_KEY env var if not provided)
        """
        self.session = session
        self.conversation_repo = ConversationRepository(session)
        self.tokenizer = tiktoken.get_encoding(self.TOKENIZER_ENCODING)

        # Initialize Claude for summarization (Sonnet 4.5 for optimal speed/quality)
        self.llm = ChatAnthropic(
            api_key=api_key,
            model="claude-sonnet-4-5-20250929",
            temperature=0.3,  # Lower temperature for consistent summaries
        )

    def _count_message_tokens(self, messages: List[dict]) -> int:
        """
        Count total tokens in message list.

        Args:
            messages: List of messages in format [{"role": "...", "content": "..."}]

        Returns:
            Total token count
        """
        total_tokens = 0
        for msg in messages:
            content = msg.get("content", "")
            tokens = len(self.tokenizer.encode(content))
            total_tokens += tokens
        return total_tokens

    async def check_and_summarize(
        self,
        conversation_id: UUID,
        messages: List[dict],
        force_summarize: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Check if conversation needs summarization and perform if needed.

        Args:
            conversation_id: Conversation ID
            messages: List of messages [{"role": "...", "content": "..."}]
            force_summarize: Force summarization regardless of token count

        Returns:
            Summary dict if created, None otherwise
            Format: {
                "id": str,
                "conversation_id": str,
                "summary": str,
                "original_token_count": int,
                "messages_summarized_count": int,
                "created_at": datetime
            }
        """
        try:
            # Count tokens in conversation
            token_count = self._count_message_tokens(messages)

            logger.info(
                f"Checking conversation {conversation_id}: "
                f"{token_count} tokens, threshold: {self.CONVERSATION_SUMMARY_TOKEN_THRESHOLD}"
            )

            # Check if summarization is needed
            if not force_summarize and token_count < self.CONVERSATION_SUMMARY_TOKEN_THRESHOLD:
                logger.info(f"Conversation {conversation_id} does not exceed token threshold")
                return None

            logger.info(f"Summarizing conversation {conversation_id} ({token_count} tokens)")

            # Check if we have enough messages to summarize
            if len(messages) <= self.RECENT_MESSAGES_TO_KEEP:
                logger.info(f"Conversation has only {len(messages)} messages, no summarization needed")
                return None

            # Generate summary
            summary_dict = await self._generate_summary(conversation_id, messages, token_count)

            return summary_dict

        except Exception as e:
            logger.error(f"Error checking conversation {conversation_id}: {str(e)}", exc_info=True)
            return None

    async def _generate_summary(
        self,
        conversation_id: UUID,
        messages: List[dict],
        token_count: int,
    ) -> Dict[str, Any]:
        """
        Generate summary of conversation using Claude.

        Args:
            conversation_id: Conversation ID
            messages: List of messages
            token_count: Total tokens in messages

        Returns:
            Summary dict with metadata

        Raises:
            Exception: If summary generation fails
        """
        try:
            # Separate recent messages from older ones
            recent_messages = messages[-self.RECENT_MESSAGES_TO_KEEP :]
            older_messages = messages[: -self.RECENT_MESSAGES_TO_KEEP]

            # Format older messages for summarization
            older_messages_text = "\n".join(
                [f"{msg['role']}: {msg['content']}" for msg in older_messages]
            )

            # Create summarization prompt
            summary_prompt = f"""Please provide a concise 2-3 sentence summary of the following conversation,
            focusing on main topics discussed and key decisions or outcomes. Be factual and preserve important details.

Conversation Messages:
{older_messages_text}

Summary:"""

            # Generate summary using Claude
            messages_for_llm = [
                SystemMessage(
                    content="You are a helpful assistant that summarizes conversations concisely and accurately."
                ),
                HumanMessage(content=summary_prompt),
            ]

            response = await self.llm.ainvoke(messages_for_llm)
            summary_text = response.content.strip()

            logger.info(f"Generated summary for conversation {conversation_id}: {len(summary_text)} chars")

            # Create summary record
            summary_dict = {
                "id": None,  # Will be set by repository
                "conversation_id": str(conversation_id),
                "summary": summary_text,
                "original_token_count": token_count,
                "messages_summarized_count": len(older_messages),
                "created_at": datetime.utcnow(),
            }

            return summary_dict

        except Exception as e:
            logger.error(f"Error generating summary for {conversation_id}: {str(e)}", exc_info=True)
            raise

    async def inject_summary_into_context(
        self,
        conversation_id: UUID,
        recent_messages: List[dict],
    ) -> List[dict]:
        """
        Inject previous summary into recent message context if available.

        Args:
            conversation_id: Conversation ID
            recent_messages: List of recent messages

        Returns:
            Messages with summary injected if available, otherwise original messages
        """
        try:
            # Check if conversation has a summary
            conversation = await self.conversation_repo.get(conversation_id)
            if not conversation:
                logger.warning(f"Conversation {conversation_id} not found")
                return recent_messages

            # Check if conversation has summary info (would need to add to model)
            # For now, return recent messages as-is
            # In production, fetch summary from conversation_summaries table and prepend

            logger.debug(f"No previous summary to inject for conversation {conversation_id}")
            return recent_messages

        except Exception as e:
            logger.error(f"Error injecting summary for {conversation_id}: {str(e)}", exc_info=True)
            return recent_messages

    async def get_conversation_summary(
        self,
        conversation_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """
        Get the most recent summary for a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            Summary dict or None if not found
        """
        try:
            # Query conversation_summaries table for latest summary
            # This would be implemented with the repository once table is created
            logger.debug(f"Fetching summary for conversation {conversation_id}")
            return None  # TODO: Implement after adding conversation_summaries table

        except Exception as e:
            logger.error(f"Error fetching summary for {conversation_id}: {str(e)}", exc_info=True)
            return None

    async def should_summarize_conversation(
        self,
        messages: List[dict],
    ) -> bool:
        """
        Determine if conversation should be summarized.

        Args:
            messages: List of messages

        Returns:
            True if should summarize, False otherwise
        """
        # Check if we have enough messages
        if len(messages) <= self.RECENT_MESSAGES_TO_KEEP:
            return False

        # Check token count
        token_count = self._count_message_tokens(messages)
        if token_count >= self.CONVERSATION_SUMMARY_TOKEN_THRESHOLD:
            return True

        return False
