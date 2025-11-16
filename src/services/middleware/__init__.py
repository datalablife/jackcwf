"""Base middleware classes for LangChain agent customization."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from langchain_core.messages import BaseMessage
import logging
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class AgentMiddleware(ABC):
    """
    Base class for agent middleware.

    Middleware hooks are called at six execution points:

    User Input
        ↓
    before_agent (modify input, inject context)
        ↓
    before_model (modify prompt, add system context)
        ↓
    wrap_model_call (intercept LLM request/response)
        ↓
    after_model (process LLM output)
        ↓
    wrap_tool_call (execute tools, handle errors)
        ↓
    after_agent (log results, update state)
        ↓
    Agent Output
    """

    def __init__(self, name: str):
        """Initialize middleware."""
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def before_agent(
        self,
        messages: List[BaseMessage],
        state: Dict[str, Any],
    ) -> tuple[List[BaseMessage], Dict[str, Any]]:
        """
        Called before agent processes messages.

        Use for:
        - Loading conversation memory/context
        - Injecting user preferences
        - Pre-processing input

        Args:
            messages: Input messages to agent
            state: Agent state dictionary

        Returns:
            (modified_messages, modified_state)
        """
        return messages, state

    async def before_model(
        self,
        messages: List[BaseMessage],
        state: Dict[str, Any],
    ) -> tuple[List[BaseMessage], Dict[str, Any]]:
        """
        Called before LLM invocation.

        Use for:
        - Updating system prompt
        - Adding context/examples
        - Enforcing constraints
        - Token counting/budget checks

        Args:
            messages: Messages about to be sent to LLM
            state: Agent state

        Returns:
            (modified_messages, modified_state)
        """
        return messages, state

    async def wrap_model_call(
        self,
        llm_invoke: Callable,
        messages: List[BaseMessage],
        state: Dict[str, Any],
    ) -> Any:
        """
        Wraps the actual LLM invocation.

        Use for:
        - Request/response logging
        - Rate limiting
        - Cost tracking
        - Error recovery
        - Request/response modification

        Args:
            llm_invoke: Async function to invoke LLM
            messages: Messages to send
            state: Agent state

        Returns:
            LLM response
        """
        return await llm_invoke(messages)

    async def after_model(
        self,
        response: Any,
        messages: List[BaseMessage],
        state: Dict[str, Any],
    ) -> tuple[Any, List[BaseMessage], Dict[str, Any]]:
        """
        Called after LLM returns response.

        Use for:
        - Parsing content blocks
        - Validating response
        - Extracting metadata
        - Updating conversation state

        Args:
            response: LLM response
            messages: Original messages
            state: Agent state

        Returns:
            (modified_response, messages, modified_state)
        """
        return response, messages, state

    async def wrap_tool_call(
        self,
        tool_execute: Callable,
        tool_name: str,
        tool_args: Dict[str, Any],
        state: Dict[str, Any],
    ) -> tuple[str, Optional[str]]:
        """
        Wraps tool execution.

        Use for:
        - Tool error recovery
        - Tool input validation
        - Tool output formatting
        - Tool-specific error handling
        - Tool cost tracking

        Args:
            tool_execute: Async function to execute tool
            tool_name: Name of tool being called
            tool_args: Arguments passed to tool
            state: Agent state

        Returns:
            (result, error) - either result or error will be set
        """
        try:
            result = await tool_execute()
            return result, None
        except Exception as e:
            self.logger.error(f"Tool {tool_name} failed: {e}")
            return None, str(e)

    async def after_agent(
        self,
        final_response: str,
        state: Dict[str, Any],
    ) -> tuple[str, Dict[str, Any]]:
        """
        Called after agent completes processing.

        Use for:
        - Saving conversation to database
        - Updating metrics
        - Cleanup
        - State persistence

        Args:
            final_response: Final agent response
            state: Final agent state

        Returns:
            (modified_response, modified_state)
        """
        return final_response, state
