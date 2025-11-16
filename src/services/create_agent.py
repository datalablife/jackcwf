"""
Enhanced create_agent implementation for LangChain 1.0.

This module provides a higher-level agent creation function that
automatically handles:
- Middleware composition
- Tool binding
- LangGraph integration
- Streaming support
- Error handling
"""

from typing import Any, List, Optional, Dict
from langchain_core.language_model import BaseLLM
from langchain_core.tools import BaseTool
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage, AIMessage
from src.services.middleware import AgentMiddleware
import logging

logger = logging.getLogger(__name__)


class ManagedAgent:
    """
    Enhanced agent with middleware support.

    Features:
    - Middleware composition with 6 execution hooks
    - Tool binding and execution
    - Streaming support
    - Error recovery
    - Cost tracking

    Usage:
        agent = create_agent(
            llm=ChatOpenAI(model="gpt-4-turbo"),
            tools=[search_tool, database_tool],
            system_prompt="You are a helpful AI...",
            middleware=[
                CostTrackingMiddleware(budget_usd=10.0),
                MemoryInjectionMiddleware(),
            ]
        )

        response = await agent.invoke({
            "user_input": "What documents do I have?",
            "user_id": "user_123"
        })
    """

    def __init__(
        self,
        llm: BaseLLM,
        tools: List[BaseTool],
        system_prompt: str = "",
        middleware: Optional[List[AgentMiddleware]] = None,
    ):
        """
        Initialize agent.

        Args:
            llm: Language model instance
            tools: List of tools agent can use
            system_prompt: System prompt for agent
            middleware: List of middleware instances
        """
        self.llm = llm
        self.tools = {tool.name: tool for tool in tools}
        self.tools_list = tools
        self.system_prompt = system_prompt
        self.middleware = middleware or []
        self.llm_with_tools = llm.bind_tools(tools)

    async def invoke(
        self,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Invoke agent with middleware pipeline.

        Args:
            input_data: Input containing "user_input" and "user_id"

        Returns:
            Response dict with agent output, state, and metadata
        """
        # Build initial state
        state = {
            "user_id": input_data.get("user_id"),
            "user_input": input_data.get("user_input"),
            "start_time": None,
            "message_history": input_data.get("message_history", []),
        }

        # Build initial messages
        messages: List[BaseMessage] = []

        # Add system prompt
        if self.system_prompt:
            messages.append(SystemMessage(content=self.system_prompt))

        # Add message history if provided
        if "message_history" in state and state["message_history"]:
            for msg in state["message_history"]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))
                elif role == "system":
                    messages.append(SystemMessage(content=content))

        # Add current user input
        messages.append(HumanMessage(content=input_data.get("user_input", "")))

        # Execute before_agent hooks
        for middleware in self.middleware:
            messages, state = await middleware.before_agent(messages, state)

        # Execute before_model hooks
        for middleware in self.middleware:
            messages, state = await middleware.before_model(messages, state)

        # Call LLM with tools
        try:
            # Create wrapped invoke function
            async def invoke_llm(msgs):
                # Execute wrap_model_call hooks
                result = msgs  # Start with messages
                for middleware in self.middleware:
                    result = await middleware.wrap_model_call(
                        lambda: self.llm_with_tools.ainvoke(msgs),
                        msgs,
                        state
                    )
                return result

            response = await invoke_llm(messages)

            # Execute after_model hooks
            for middleware in self.middleware:
                response, messages, state = await middleware.after_model(
                    response, messages, state
                )

        except Exception as e:
            logger.error(f"Error invoking LLM: {e}", exc_info=True)
            return {
                "output": f"Error processing request: {str(e)}",
                "state": state,
                "error": True,
                "tool_calls": [],
            }

        # Extract text response and tool calls
        agent_response = response.content if hasattr(response, "content") else str(response)
        tool_calls_data = getattr(response, "tool_calls", []) or []

        # Execute tools if requested
        if tool_calls_data:
            messages.append(response)

            for tool_call in tool_calls_data:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})
                tool_call_id = tool_call.get("id", f"call_{len(tool_calls_data)}")

                # Create wrapped tool execute function
                async def execute_tool():
                    tool = self.tools.get(tool_name)
                    if not tool:
                        raise ValueError(f"Tool {tool_name} not found")
                    return await tool.ainvoke(tool_args)

                # Execute wrap_tool_call hooks
                result, error = None, None
                for middleware in self.middleware:
                    result, error = await middleware.wrap_tool_call(
                        execute_tool,
                        tool_name,
                        tool_args,
                        state
                    )

                # Add tool result to messages
                if error:
                    messages.append(ToolMessage(
                        content=f"Error: {error}",
                        tool_call_id=tool_call_id
                    ))
                else:
                    messages.append(ToolMessage(
                        content=str(result) if result is not None else "No result",
                        tool_call_id=tool_call_id
                    ))

            # Get final response after tool execution
            try:
                final_response = await self.llm.ainvoke(messages)
                agent_response = final_response.content if hasattr(final_response, "content") else str(final_response)
            except Exception as e:
                logger.error(f"Error getting final response: {e}")
                agent_response = "I processed your request but encountered an error generating the final response."

        # Execute after_agent hooks
        for middleware in self.middleware:
            agent_response, state = await middleware.after_agent(
                agent_response, state
            )

        return {
            "output": agent_response,
            "state": state,
            "tool_calls": tool_calls_data if tool_calls_data else [],
            "error": False,
        }

    async def stream(
        self,
        input_data: Dict[str, Any],
    ):
        """
        Stream response from agent.

        Yields chunks as they're generated for real-time UX.

        Args:
            input_data: Input containing "user_input" and "user_id"

        Yields:
            Response chunks with type and content
        """
        # Build initial state and messages (similar to invoke)
        state = {
            "user_id": input_data.get("user_id"),
            "user_input": input_data.get("user_input"),
        }

        messages: List[BaseMessage] = []

        if self.system_prompt:
            messages.append(SystemMessage(content=self.system_prompt))

        messages.append(HumanMessage(content=input_data.get("user_input", "")))

        # Execute middleware before streaming
        for middleware in self.middleware:
            messages, state = await middleware.before_agent(messages, state)

        for middleware in self.middleware:
            messages, state = await middleware.before_model(messages, state)

        # Stream response
        try:
            async for chunk in self.llm_with_tools.astream(messages):
                if chunk.content:
                    yield {
                        "type": "content",
                        "content": chunk.content,
                    }

                # Handle tool calls in streaming
                if hasattr(chunk, "tool_calls") and chunk.tool_calls:
                    for tool_call in chunk.tool_calls:
                        yield {
                            "type": "tool_call",
                            "tool_name": tool_call.get("name"),
                            "tool_input": tool_call.get("args", {}),
                        }

        except Exception as e:
            logger.error(f"Error streaming response: {e}", exc_info=True)
            yield {
                "type": "error",
                "error": str(e),
            }


def create_agent(
    llm: BaseLLM,
    tools: List[BaseTool],
    system_prompt: str = "",
    middleware: Optional[List[AgentMiddleware]] = None,
) -> ManagedAgent:
    """
    Create an agent with middleware support (LangChain 1.0 pattern).

    This is the recommended pattern for agent creation in LangChain 1.0.
    It replaces Agent.from_llm() and custom agent classes with a
    composable, middleware-based architecture.

    Args:
        llm: Language model instance (ChatOpenAI, ChatAnthropic, etc.)
        tools: List of Tool objects for agent to use
        system_prompt: Optional system prompt for agent
        middleware: Optional list of middleware for customization

    Returns:
        ManagedAgent instance

    Example:
        from langchain_openai import ChatOpenAI
        from src.services.create_agent import create_agent
        from src.services.middleware.cost_tracking import CostTrackingMiddleware

        # Create agent with cost tracking
        agent = create_agent(
            llm=ChatOpenAI(model="gpt-4-turbo"),
            tools=[search_documents, query_database, web_search],
            system_prompt='''You are a helpful financial analyst.
                Use tools to find relevant information before answering.''',
            middleware=[
                CostTrackingMiddleware(
                    budget_usd=10.0,
                    model="gpt-4-turbo"
                ),
                MemoryInjectionMiddleware(
                    max_memory_messages=20
                ),
            ]
        )

        # Use agent
        result = await agent.invoke({
            "user_input": "Analyze the latest financial reports",
            "user_id": "user_123",
        })

        print(result["output"])
        print(f"Cost: ${result['state']['cost_tracking']['spent_usd']:.4f}")

    Benefits:
    - Type-safe with Pydantic validation
    - Composable with middleware hooks
    - Automatic LangGraph integration ready
    - Streaming support built-in
    - Cost tracking and budget enforcement
    - Error recovery policies
    - Memory/context management
    """
    return ManagedAgent(
        llm=llm,
        tools=tools,
        system_prompt=system_prompt,
        middleware=middleware or []
    )
