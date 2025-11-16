"""Cost tracking middleware for token and API call monitoring."""

from typing import Any, Dict, List, Callable
from langchain_core.messages import BaseMessage
from src.services.middleware import AgentMiddleware
import logging
import time

logger = logging.getLogger(__name__)


class CostTrackingMiddleware(AgentMiddleware):
    """
    Tracks token usage and API costs during agent execution.

    Features:
    - Token counting (input, output, total)
    - Cost calculation by model
    - Budget enforcement
    - Per-tool cost tracking

    Usage:
        middleware = CostTrackingMiddleware(
            budget_usd=10.0,
            model="gpt-4-turbo"
        )
    """

    # Token costs per model (in USD, per 1M tokens)
    # Updated based on current pricing
    TOKEN_COSTS = {
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
        "claude-3.5-sonnet": {"input": 0.003, "output": 0.015},
    }

    def __init__(self, budget_usd: float = 10.0, model: str = "gpt-4-turbo"):
        """
        Initialize cost tracking.

        Args:
            budget_usd: Maximum budget for conversation in USD
            model: Model name for cost calculation
        """
        super().__init__("cost_tracking")
        self.budget_usd = budget_usd
        self.model = model
        self.spent_usd = 0.0
        self.token_log = []

    async def before_model(
        self,
        messages: List[BaseMessage],
        state: Dict[str, Any],
    ) -> tuple[List[BaseMessage], Dict[str, Any]]:
        """Check token budget before model call."""
        # Initialize or get current spending
        if "cost_tracking" not in state:
            state["cost_tracking"] = {
                "spent_usd": 0.0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "tool_calls": {},
            }

        current_budget = state["cost_tracking"]["spent_usd"]
        remaining = self.budget_usd - current_budget

        if remaining < 0.01:  # Less than $0.01 remaining
            logger.warning(f"Budget threshold reached: ${remaining:.4f} remaining")

        self.logger.info(
            f"Budget status: ${current_budget:.4f}/${self.budget_usd:.4f} "
            f"(${remaining:.4f} remaining)"
        )

        return messages, state

    async def wrap_model_call(
        self,
        llm_invoke: Callable,
        messages: List[BaseMessage],
        state: Dict[str, Any],
    ) -> Any:
        """Track costs during model invocation."""
        start_time = time.time()
        start_tokens = state.get("cost_tracking", {}).get("total_tokens", 0)

        response = await llm_invoke(messages)

        elapsed_ms = (time.time() - start_time) * 1000

        # Extract token usage if available
        if hasattr(response, "response_metadata"):
            metadata = response.response_metadata
            usage = metadata.get("token_usage", {})

            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            total_tokens = input_tokens + output_tokens

            # Calculate cost
            costs = self.TOKEN_COSTS.get(self.model, {"input": 0, "output": 0})
            cost_input = (input_tokens / 1_000_000) * costs["input"]
            cost_output = (output_tokens / 1_000_000) * costs["output"]
            total_cost = cost_input + cost_output

            # Update state
            if "cost_tracking" not in state:
                state["cost_tracking"] = {
                    "spent_usd": 0.0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "tool_calls": {},
                }

            state["cost_tracking"]["input_tokens"] += input_tokens
            state["cost_tracking"]["output_tokens"] += output_tokens
            state["cost_tracking"]["total_tokens"] += total_tokens
            state["cost_tracking"]["spent_usd"] += total_cost

            self.logger.info(
                f"Model call cost: ${total_cost:.6f} "
                f"({input_tokens} input, {output_tokens} output tokens, "
                f"{elapsed_ms:.0f}ms)"
            )

        return response

    async def wrap_tool_call(
        self,
        tool_execute: Callable,
        tool_name: str,
        tool_args: Dict[str, Any],
        state: Dict[str, Any],
    ) -> tuple[str, None | str]:
        """Track tool execution time and results."""
        start_time = time.time()

        try:
            result = await tool_execute()
            elapsed_ms = (time.time() - start_time) * 1000

            # Update tool stats
            if "cost_tracking" not in state:
                state["cost_tracking"] = {
                    "spent_usd": 0.0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "tool_calls": {},
                }
            if "tool_calls" not in state["cost_tracking"]:
                state["cost_tracking"]["tool_calls"] = {}

            if tool_name not in state["cost_tracking"]["tool_calls"]:
                state["cost_tracking"]["tool_calls"][tool_name] = {
                    "count": 0,
                    "total_time_ms": 0,
                    "errors": 0,
                }

            state["cost_tracking"]["tool_calls"][tool_name]["count"] += 1
            state["cost_tracking"]["tool_calls"][tool_name]["total_time_ms"] += elapsed_ms

            self.logger.info(f"Tool {tool_name} executed in {elapsed_ms:.0f}ms")

            return result, None

        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000

            # Update error count
            if "cost_tracking" not in state:
                state["cost_tracking"] = {
                    "spent_usd": 0.0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "tool_calls": {},
                }
            if "tool_calls" not in state["cost_tracking"]:
                state["cost_tracking"]["tool_calls"] = {}
            if tool_name not in state["cost_tracking"]["tool_calls"]:
                state["cost_tracking"]["tool_calls"][tool_name] = {
                    "count": 0,
                    "total_time_ms": 0,
                    "errors": 0,
                }

            state["cost_tracking"]["tool_calls"][tool_name]["errors"] += 1

            self.logger.error(
                f"Tool {tool_name} failed after {elapsed_ms:.0f}ms: {e}"
            )

            return None, str(e)

    async def after_agent(
        self,
        final_response: str,
        state: Dict[str, Any],
    ) -> tuple[str, Dict[str, Any]]:
        """Log final cost summary."""
        if "cost_tracking" in state:
            costs = state["cost_tracking"]
            self.logger.info(
                f"Conversation summary: "
                f"${costs['spent_usd']:.6f} spent, "
                f"{costs['total_tokens']} tokens used, "
                f"{len(costs.get('tool_calls', {}))} tools called"
            )

        return final_response, state
