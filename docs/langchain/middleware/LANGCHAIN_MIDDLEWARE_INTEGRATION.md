# Unified Content Blocks - LangChain 1.0 Middleware Integration Guide

## Integration Overview

This guide shows how to integrate the unified content blocks system with LangChain 1.0's middleware architecture for building production-grade financial analysis agents.

## Architecture Diagram

```
LangChain Agent Loop:
┌──────────────────────────────────────────────────────────┐
│ User Input                                               │
└────────────────┬─────────────────────────────────────────┘
                 │
        ┌────────▼────────┐
        │ before_agent    │ ◄── Load conversation state
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │ before_model    │ ◄── Add content blocks context
        └────────┬────────┘
                 │
        ┌────────▼──────────────┐
        │ wrap_model_call       │ ◄── Call LLM, capture response
        │ (LLM Invocation)      │
        └────────┬──────────────┘
                 │
        ┌────────▼────────┐
        │ after_model     │ ◄── Parse content blocks
        │ (Parse Response)│
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │ wrap_tool_call  │ ◄── Execute/validate tools
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │ after_agent     │ ◄── Save state, log metrics
        └────────┬────────┘
                 │
┌────────────────▼─────────────────────────────────────────┐
│ Agent Output (Text + Insights + Tool Results)           │
└──────────────────────────────────────────────────────────┘
```

## Core Middleware Components

### 1. ContentBlocksParsingMiddleware

Handles parsing of LLM responses into unified content blocks.

```python
from typing import Any, Dict
import logging

from content_blocks_parser import ContentBlockParserFactory, ProviderType
from financial_content_handler import FinancialContentBlockHandler


class ContentBlocksParsingMiddleware:
    """
    LangChain 1.0 middleware for parsing unified content blocks.

    Executes in the after_model hook to parse responses.
    """

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.handler = FinancialContentBlockHandler(model_name=model_name)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def after_model(self, response: Any, **kwargs) -> Any:
        """
        Parse response after model execution.

        Adds parsed content blocks to response metadata.
        """
        try:
            # Parse the response
            processed = self.handler.process_response(response)

            # Attach parsed data to response
            if not hasattr(response, "_parsed_content_blocks"):
                response._parsed_content_blocks = processed

            # Log parsing results
            self.logger.debug(
                f"Parsed response: {len(processed.content_blocks)} blocks, "
                f"{len(processed.reasoning_traces)} reasoning traces, "
                f"{len(processed.tool_calls)} tool calls"
            )

            return response

        except Exception as e:
            self.logger.error(f"Content blocks parsing failed: {e}", exc_info=True)
            # Don't interrupt agent flow on parsing error
            return response
```

### 2. FinancialInsightsExtractionMiddleware

Extracts and validates financial insights from parsed content.

```python
class FinancialInsightsExtractionMiddleware:
    """Extract financial insights from parsed content blocks."""

    def __init__(self, confidence_threshold: float = 0.8):
        self.confidence_threshold = confidence_threshold
        self.logger = logging.getLogger(self.__class__.__name__)

    async def after_model(self, response: Any, **kwargs) -> Any:
        """Extract insights from parsed response."""
        if not hasattr(response, "_parsed_content_blocks"):
            return response

        try:
            processed = response._parsed_content_blocks

            # Extract high-confidence insights
            high_conf = processed.get_high_confidence_insights(
                threshold=self.confidence_threshold
            )

            # Organize by type
            insights_by_type = {}
            for insight in high_conf:
                itype = insight.insight_type.value
                if itype not in insights_by_type:
                    insights_by_type[itype] = []
                insights_by_type[itype].append(insight.content)

            # Attach to response
            response._financial_insights = {
                "count": len(high_conf),
                "by_type": insights_by_type,
                "reasoning_based": len(processed.reasoning_insights),
                "text_based": len(processed.text_insights),
            }

            self.logger.info(
                f"Extracted {len(high_conf)} high-confidence insights"
            )

            return response

        except Exception as e:
            self.logger.error(f"Insight extraction failed: {e}")
            return response
```

### 3. ToolCallValidationMiddleware

Validates and costs all tool calls before execution.

```python
class ToolCallValidationMiddleware:
    """Validate and cost tool calls from content blocks."""

    def __init__(self, max_budget: float = 0.10):
        self.max_budget = max_budget
        self.logger = logging.getLogger(self.__class__.__name__)

    async def before_model(self, inputs: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Prepare context before model call.

        Stores budget info for downstream validation.
        """
        inputs["_tool_budget"] = self.max_budget
        return inputs

    async def after_model(self, response: Any, **kwargs) -> Any:
        """Validate tool calls after model execution."""
        if not hasattr(response, "_parsed_content_blocks"):
            return response

        try:
            processed = response._parsed_content_blocks

            # Validate all tools
            validations = processed.tool_validations

            invalid_count = sum(1 for v in validations if not v.is_valid)
            if invalid_count > 0:
                self.logger.warning(
                    f"Found {invalid_count} invalid tools"
                )

            # Check budget
            total_cost = processed.get_total_tool_cost()
            if total_cost > self.max_budget:
                self.logger.warning(
                    f"Tools cost ${total_cost} exceeds budget ${self.max_budget}"
                )

            # Attach validation results
            response._tool_validation = {
                "valid": all(v.is_valid for v in validations),
                "total_cost": total_cost,
                "tool_count": len(validations),
                "invalid_tools": [
                    {
                        "name": v.tool_name,
                        "errors": v.errors
                    }
                    for v in validations
                    if not v.is_valid
                ],
                "warnings": [
                    {
                        "name": v.tool_name,
                        "warnings": v.warnings
                    }
                    for v in validations
                    if v.warnings
                ]
            }

            return response

        except Exception as e:
            self.logger.error(f"Tool validation failed: {e}")
            return response
```

### 4. ReasoningTransparencyMiddleware

Preserves and exposes reasoning traces for transparency.

```python
class ReasoningTransparencyMiddleware:
    """Capture and expose reasoning traces for interpretability."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.reasoning_history = []

    async def after_model(self, response: Any, **kwargs) -> Any:
        """Capture reasoning traces."""
        if not hasattr(response, "_parsed_content_blocks"):
            return response

        try:
            processed = response._parsed_content_blocks

            # Extract reasoning
            reasoning = {
                "count": len(processed.reasoning_traces),
                "formats": list(set(
                    t.format.value for t in processed.reasoning_traces
                )),
                "traces": [
                    {
                        "format": t.format.value,
                        "preview": t.content[:500],  # First 500 chars
                        "full_length": len(t.content),
                        "tokens": t.token_count or 0,
                        "confidence": t.confidence,
                    }
                    for t in processed.reasoning_traces
                ]
            }

            # Store in response
            response._reasoning_traces = reasoning

            # Track for debugging
            self.reasoning_history.append(reasoning)

            self.logger.debug(
                f"Captured {reasoning['count']} reasoning traces "
                f"({reasoning['formats']})"
            )

            return response

        except Exception as e:
            self.logger.error(f"Reasoning capture failed: {e}")
            return response

    def get_reasoning_history(self):
        """Get all captured reasoning for debugging."""
        return self.reasoning_history
```

## Integration with create_agent()

### Example: Financial Analysis Agent

```python
from langchain.agents import create_agent
from langchain.chat_models import ChatAnthropic
from langchain.tools import tool
from pydantic import BaseModel, Field


class StockAnalysisInput(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol")
    analysis_type: str = Field(
        default="valuation",
        description="Type of analysis: valuation, risk, performance"
    )


# Define tools with proper schemas
@tool("fetch_stock_data")
def fetch_stock_data(ticker: str) -> dict:
    """Fetch current stock data for a given ticker."""
    return {
        "ticker": ticker,
        "price": 150.0,
        "pe_ratio": 18.5,
        "market_cap": 2.5e12
    }


@tool("fetch_financial_statements")
def fetch_financial_statements(ticker: str, period: str = "Q3_2024") -> dict:
    """Fetch financial statements for a company."""
    return {
        "ticker": ticker,
        "period": period,
        "revenue": 96.99e9,
        "net_income": 25.4e9,
        "assets": 377e9
    }


@tool("calculate_ratios")
def calculate_ratios(financial_data: dict) -> dict:
    """Calculate financial ratios."""
    return {
        "roe": 0.22,
        "debt_to_equity": 0.4,
        "current_ratio": 2.1,
        "profit_margin": 0.26
    }


# Create agent with middleware
def create_financial_agent(model: str = "claude-3-5-sonnet-20241022"):
    """Create financial analysis agent with content blocks middleware."""

    # Initialize LLM
    llm = ChatAnthropic(model=model)

    # Define middleware stack
    middlewares = [
        # Parse content blocks first
        ContentBlocksParsingMiddleware(model_name=model),

        # Extract insights
        FinancialInsightsExtractionMiddleware(confidence_threshold=0.85),

        # Validate tools
        ToolCallValidationMiddleware(max_budget=0.10),

        # Preserve reasoning
        ReasoningTransparencyMiddleware(),
    ]

    # Create agent
    agent = create_agent(
        llm=llm,
        tools=[
            fetch_stock_data,
            fetch_financial_statements,
            calculate_ratios
        ],
        system_message=(
            "You are a financial analysis expert. "
            "Provide detailed analysis with reasoning. "
            "For stock analysis, always fetch data before making recommendations."
        ),
        middleware=middlewares,
        verbose=True
    )

    return agent


# Usage
async def analyze_stock(ticker: str):
    """Analyze a stock."""
    agent = create_financial_agent()

    response = await agent.arun(
        f"Provide a detailed valuation analysis for {ticker}. "
        f"Consider current metrics and industry trends."
    )

    # Access parsed data from response
    if hasattr(response, "_financial_insights"):
        insights = response._financial_insights
        print(f"Insights extracted: {insights['count']}")
        print(f"By type: {insights['by_type']}")

    if hasattr(response, "_reasoning_traces"):
        reasoning = response._reasoning_traces
        print(f"Reasoning traces: {reasoning['count']}")

    return response
```

## State Management Pattern

### Maintaining Agent State with Content Blocks

```python
from typing import Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AgentState:
    """Track agent state across tool calls."""

    conversation_id: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    parsed_responses: List[Dict[str, Any]] = field(default_factory=list)
    tool_execution_log: List[Dict[str, Any]] = field(default_factory=list)
    extracted_insights: List[Dict[str, Any]] = field(default_factory=list)
    total_cost: float = 0.0
    reasoning_traces: List[str] = field(default_factory=list)

    def add_response(self, response: Any, parsed: Any):
        """Add parsed response to state."""
        self.parsed_responses.append({
            "timestamp": datetime.utcnow().isoformat(),
            "model": parsed.parsed_response.model,
            "blocks": len(parsed.content_blocks),
            "reasoning": len(parsed.reasoning_traces),
            "tools": len(parsed.tool_calls),
        })

        # Store reasoning
        for trace in parsed.reasoning_traces:
            self.reasoning_traces.append(trace.content)

        # Store insights
        for insight in parsed.combined_insights:
            self.extracted_insights.append({
                "type": insight.insight_type.value,
                "content": insight.content,
                "confidence": insight.confidence,
                "source": insight.source,
            })

        # Track cost
        self.total_cost += sum(
            tv.estimated_cost or 0
            for tv in parsed.tool_validations
        )

    def get_summary(self) -> Dict[str, Any]:
        """Get state summary for checkpointing."""
        return {
            "id": self.conversation_id,
            "responses": len(self.parsed_responses),
            "insights": len(self.extracted_insights),
            "total_cost": self.total_cost,
            "reasoning_count": len(self.reasoning_traces),
            "tools_executed": len(self.tool_execution_log),
        }


# Integration with LangGraph for persistence
from langgraph.graph import StateGraph
from langgraph.checkpoint import MemorySaver


def create_financial_graph():
    """Create LangGraph with persistent state."""

    # Create state manager
    state_graph = StateGraph(AgentState)

    # Define nodes
    async def analyze_node(state: AgentState):
        """Analyze step."""
        agent = create_financial_agent()
        response = await agent.arun(
            "Analyze the provided financial data"
        )

        # Parse and add to state
        if hasattr(response, "_parsed_content_blocks"):
            state.add_response(response, response._parsed_content_blocks)

        return state

    async def execute_tools_node(state: AgentState):
        """Execute tool calls from analysis."""
        for insight in state.extracted_insights:
            # Determine which tools to execute based on insights
            pass

        return state

    async def summarize_node(state: AgentState):
        """Summarize analysis."""
        return state

    # Add nodes
    state_graph.add_node("analyze", analyze_node)
    state_graph.add_node("execute_tools", execute_tools_node)
    state_graph.add_node("summarize", summarize_node)

    # Add edges
    state_graph.add_edge("analyze", "execute_tools")
    state_graph.add_edge("execute_tools", "summarize")

    # Compile with checkpointing
    memory = MemorySaver()
    graph = state_graph.compile(checkpointer=memory)

    return graph
```

## Error Recovery Middleware

```python
class ErrorRecoveryMiddleware:
    """Handle and recover from errors in agent loop."""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.logger = logging.getLogger(self.__class__.__name__)

    async def wrap_model_call(self, func, args, kwargs):
        """Wrap model call with retry logic."""
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)

            except Exception as e:
                if attempt < self.max_retries - 1:
                    self.logger.warning(
                        f"Model call failed (attempt {attempt + 1}), retrying: {e}"
                    )
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    self.logger.error(f"Model call failed after {self.max_retries} retries")
                    raise

    async def wrap_tool_call(self, func, args, kwargs):
        """Wrap tool execution with error handling."""
        try:
            return await func(*args, **kwargs)

        except Exception as e:
            self.logger.error(f"Tool execution failed: {e}")
            # Return error result instead of failing
            return {
                "error": str(e),
                "fallback": True
            }
```

## Deployment Checklist

- [ ] Content blocks parser tested with all 3 providers
- [ ] Middleware stack integrated with agent
- [ ] Error handling verified (safe_parse always works)
- [ ] Tool validation prevents invalid executions
- [ ] Reasoning traces captured and logged
- [ ] Financial insights extracted correctly
- [ ] Cost tracking functional
- [ ] State persistence working
- [ ] Streaming responses handled
- [ ] Multi-provider consensus implemented

## Next Steps

1. Integrate middleware into your LangChain 1.0 create_agent() setup
2. Test with all 3 providers (Claude, GPT-4, Gemini)
3. Implement LangGraph checkpointing for state persistence
4. Add custom middleware for domain-specific logic
5. Monitor with LangSmith for production insights

## References

- LangChain 1.0 Middleware: `langchain.agents.create_agent(middleware=...)`
- LangGraph State: `langgraph.graph.StateGraph`
- Content Blocks: `src/services/content_blocks_parser.py`
- Examples: `src/examples/financial_analysis_examples.py`
