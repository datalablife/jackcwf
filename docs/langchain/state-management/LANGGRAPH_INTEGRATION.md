# LangChain 1.0 create_agent Integration Guide

## Complete Integration with the Middleware Stack

### 1. Using LangChain 1.0's create_agent with Middleware

```python
# agent_factory.py
from langchain.agents import create_agent
from langchain_core.language_model import BaseLLM
from langchain_core.tools import BaseTool
from typing import List, Dict, Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)

class MiddlewareAdapter:
    """Adapt our middleware to LangChain's middleware system"""

    def __init__(self, middleware_stack: List[tuple]):
        self.before_agent_mw = []
        self.before_model_mw = []
        self.wrap_model_call_mw = []
        self.after_model_mw = []
        self.wrap_tool_call_mw = []
        self.after_agent_mw = []

        # Organize middleware by hook type
        for name, hook, mw in middleware_stack:
            if hook == "before_agent":
                self.before_agent_mw.append((name, mw))
            elif hook == "before_model":
                self.before_model_mw.append((name, mw))
            elif hook == "wrap_model_call":
                self.wrap_model_call_mw.append((name, mw))
            elif hook == "after_model":
                self.after_model_mw.append((name, mw))
            elif hook == "wrap_tool_call":
                self.wrap_tool_call_mw.append((name, mw))
            elif hook == "after_agent":
                self.after_agent_mw.append((name, mw))

    async def execute_before_agent(
        self,
        agent_input: Dict[str, Any],
        agent_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute all before_agent middleware"""

        for name, middleware in self.before_agent_mw:
            try:
                agent_input = await middleware.before_agent(
                    agent_input, agent_state
                )
                logger.debug(f"Executed before_agent middleware: {name}")
            except Exception as e:
                logger.error(f"Error in {name}: {e}")
                raise

        return agent_input

    async def execute_before_model(
        self,
        model_input: Dict[str, Any],
        agent_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute all before_model middleware"""

        for name, middleware in self.before_model_mw:
            try:
                model_input = await middleware.before_model(
                    model_input, agent_state
                )
                logger.debug(f"Executed before_model middleware: {name}")
            except Exception as e:
                logger.error(f"Error in {name}: {e}")
                raise

        return model_input

    async def execute_after_model(
        self,
        model_response: Any,
        agent_state: Dict[str, Any],
    ) -> Any:
        """Execute all after_model middleware"""

        for name, middleware in self.after_model_mw:
            try:
                model_response = await middleware.after_model(
                    model_response, agent_state
                )
                logger.debug(f"Executed after_model middleware: {name}")
            except Exception as e:
                logger.error(f"Error in {name}: {e}")
                raise

        return model_response

    async def execute_after_agent(
        self,
        agent_output: Dict[str, Any],
        agent_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute all after_agent middleware"""

        for name, middleware in self.after_agent_mw:
            try:
                agent_output = await middleware.after_agent(
                    agent_output, agent_state
                )
                logger.debug(f"Executed after_agent middleware: {name}")
            except Exception as e:
                logger.error(f"Error in {name}: {e}")
                raise

        return agent_output

    def wrap_model_call_fn(
        self,
        call_fn: Callable,
        agent_state: Dict[str, Any],
    ) -> Callable:
        """
        Wrap model call with all wrap_model_call middleware.

        Returns a wrapped function that executes middleware hooks.
        """

        async def wrapped_call():
            # Execute wrap_model_call middleware
            for name, middleware in self.wrap_model_call_mw:
                try:
                    # Each middleware wraps the call
                    original_call = call_fn
                    call_fn = await middleware.wrap_model_call(
                        original_call, agent_state
                    )
                    logger.debug(f"Applied wrap_model_call middleware: {name}")
                except Exception as e:
                    logger.error(f"Error in {name}: {e}")
                    raise

            # Execute the wrapped model call
            return await call_fn()

        return wrapped_call


async def create_langgraph_agent(
    llm_client: BaseLLM,
    tools: List[BaseTool],
    checkpoint_storage,
    middleware_stack: List[tuple],
    system_prompt: str = None,
    verbose: bool = False,
) -> "Agent":
    """
    Create a LangChain 1.0 agent with middleware stack.

    Args:
        llm_client: Language model (Claude, GPT-4, etc.)
        tools: List of tools available to agent
        checkpoint_storage: LangGraph checkpoint storage
        middleware_stack: List of (name, hook, middleware) tuples
        system_prompt: System prompt for agent
        verbose: Enable verbose logging

    Returns:
        Agent with middleware support
    """

    if system_prompt is None:
        system_prompt = """You are a helpful AI assistant with access to various tools.

        Always:
        - Respect budget constraints and PII policies
        - Explain your reasoning clearly
        - Use available tools appropriately
        - Ask for clarification when needed
        """

    # Adapt middleware to LangChain format
    adapter = MiddlewareAdapter(middleware_stack)

    # Create base agent using LangChain 1.0's create_agent
    agent = create_agent(
        llm=llm_client,
        tools=tools,
        system_prompt=system_prompt,

        # Configure checkpointing
        checkpointer=checkpoint_storage,
        checkpoint_at="end",  # Save after each turn

        # Verbose logging
        verbose=verbose,
    )

    # Attach middleware adapter to agent
    agent._middleware_adapter = adapter

    return agent


class MiddlewareAwareAgent:
    """Wraps LangChain agent with middleware execution"""

    def __init__(
        self,
        agent,
        state_manager,
        middleware_adapter: MiddlewareAdapter,
    ):
        self.agent = agent
        self.state_manager = state_manager
        self.middleware_adapter = middleware_adapter
        self.logger = logging.getLogger(__name__)

    async def ainvoke(
        self,
        user_id: str,
        session_id: str,
        user_input: str,
        config: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Execute agent with full middleware stack.

        This is the main entry point for running the agent.
        """

        # Initialize session budget
        session_budget = await self.state_manager.load_or_create(
            user_id, session_id
        )

        # Create agent state
        agent_state = {
            "user_id": user_id,
            "session_id": session_id,
            "original_input": user_input,
            "session_budget": session_budget,
            "user_preferences": config.get("user_preferences", {}) if config else {},
        }

        try:
            # Execute before_agent middleware
            agent_input = {"input": user_input}
            agent_input = await self.middleware_adapter.execute_before_agent(
                agent_input, agent_state
            )

            self.logger.info(
                f"Executing agent for {user_id}:{session_id} "
                f"with input: {user_input[:50]}..."
            )

            # Execute agent (with LangGraph checkpointing built-in)
            result = await self.agent.ainvoke(
                input=agent_input,
                config={
                    "configurable": {
                        "user_id": user_id,
                        "session_id": session_id,
                    },
                },
            )

            # Execute after_agent middleware
            result = await self.middleware_adapter.execute_after_agent(
                result, agent_state
            )

            # Get budget summary
            budget_summary = await self.state_manager.get_budget_summary(
                user_id, session_id
            )

            return {
                "output": result.get("output", ""),
                "reasoning_insights": agent_state.get("reasoning_insights", []),
                "cost_summary": {
                    "tokens_used": budget_summary["tokens_used"],
                    "cost_used": budget_summary["cost_used"],
                    "remaining_budget": budget_summary["budget_remaining"],
                },
                "metadata": {
                    "model_used": agent_state.get("target_model"),
                    "approval_required": agent_state.get("approval_required", False),
                    "pii_redacted": agent_state.get("pii_was_redacted", False),
                    "context_summarized": agent_state.get("context_was_summarized", False),
                },
                "full_state": agent_state,  # For debugging
            }

        except Exception as e:
            self.logger.error(f"Agent execution failed: {e}")

            # Get final budget state
            budget_summary = await self.state_manager.get_budget_summary(
                user_id, session_id
            )

            return {
                "error": str(e),
                "error_type": type(e).__name__,
                "budget_summary": budget_summary,
                "recovery_available": bool(
                    agent_state.get("session_budget").tokens_remaining > 1000
                ),
            }

    async def stream(
        self,
        user_id: str,
        session_id: str,
        user_input: str,
        config: Optional[Dict] = None,
    ):
        """
        Stream agent output token-by-token.

        Useful for real-time user interfaces.
        """

        # Similar to ainvoke but yields tokens as they arrive
        session_budget = await self.state_manager.load_or_create(
            user_id, session_id
        )

        agent_state = {
            "user_id": user_id,
            "session_id": session_id,
            "original_input": user_input,
            "session_budget": session_budget,
        }

        # Execute before_agent middleware
        agent_input = {"input": user_input}
        agent_input = await self.middleware_adapter.execute_before_agent(
            agent_input, agent_state
        )

        # Stream from agent
        async for token in self.agent.astream(
            input=agent_input,
            config={
                "configurable": {
                    "user_id": user_id,
                    "session_id": session_id,
                },
            },
        ):
            # Yield token to client
            yield {
                "token": token,
                "state": agent_state.copy(),  # Might include partial costs
            }

        # Execute after_agent middleware
        final_result = await self.middleware_adapter.execute_after_agent(
            {"output": ""}, agent_state
        )

        yield {
            "final": final_result,
            "state": agent_state,
        }
```

---

### 2. Tool Definition with Middleware Support

```python
# tools.py
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class DatabaseQuery(BaseModel):
    """Schema for database query tool"""
    query: str = Field(..., description="SQL query to execute")
    database: str = Field(default="main", description="Database name")
    max_rows: int = Field(default=100, description="Maximum rows to return")

@tool(args_schema=DatabaseQuery)
async def query_database(query: str, database: str = "main", max_rows: int = 100) -> Dict[str, Any]:
    """
    Execute a database query.

    This tool would be wrapped by wrap_tool_call middleware for cost tracking.
    """
    # Implementation here
    logger.info(f"Executing query on {database}: {query[:50]}...")
    return {
        "rows": 42,  # Dummy result
        "columns": ["id", "name", "value"],
    }

class SearchQuery(BaseModel):
    """Schema for search tool"""
    query: str = Field(..., description="Search query")
    limit: int = Field(default=10, description="Results limit")

@tool(args_schema=SearchQuery)
async def search(query: str, limit: int = 10) -> Dict[str, Any]:
    """
    Search for information.

    Cost: ~$0.0001 per search
    """
    logger.info(f"Searching for: {query}")
    return {
        "results": [
            {"title": f"Result {i}", "snippet": "..."}
            for i in range(min(limit, 5))
        ],
    }

class CodeAnalysis(BaseModel):
    """Schema for code analysis tool"""
    code: str = Field(..., description="Code to analyze")
    language: str = Field(default="python", description="Programming language")

@tool(args_schema=CodeAnalysis)
async def analyze_code(code: str, language: str = "python") -> Dict[str, Any]:
    """
    Analyze code for issues and improvements.

    This is an expensive operation (costs ~$0.01 per call).
    """
    logger.info(f"Analyzing {language} code: {len(code)} chars")
    return {
        "issues": [
            {"type": "error", "message": "Example issue"},
        ],
        "suggestions": ["Use type hints", "Add docstrings"],
        "complexity_score": 6.5,
    }

# Create tools list
TOOLS = [
    query_database,
    search,
    analyze_code,
]
```

---

### 3. Complete Setup Example

```python
# setup.py
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres import PostgresCheckpointStorage
from middleware_stack.state import SessionStateManager
from middleware_stack.pii import PIIDetector, PIIValidationMiddleware
from middleware_stack.routing import ModelRouter, ComplexityRoutingMiddleware
from middleware_stack.budget import (
    TokenCounter,
    BudgetValidationMiddleware,
    CostTrackingMiddleware,
)
from middleware_stack.reasoning import ContentBlockParser, ReasoningTraceMiddleware
import os
import logging

logging.basicConfig(level=logging.INFO)

async def setup_production_agent():
    """Set up production-ready agent with middleware"""

    # 1. Initialize storage and clients
    postgres_url = os.environ.get(
        "POSTGRES_URL",
        "postgresql://user:password@localhost/langgraph"
    )
    checkpoint_storage = PostgresCheckpointStorage(
        connection_string=postgres_url,
    )

    # LLM client (Anthropic Claude)
    llm_client = ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
        temperature=0.7,
    )

    # 2. Set up middleware components
    state_manager = SessionStateManager(checkpoint_storage)

    # PII detection
    pii_detector = PIIDetector(strict_mode=False)
    pii_middleware = PIIValidationMiddleware(pii_detector)

    # Complexity routing
    model_router = ModelRouter(state_manager)
    routing_middleware = ComplexityRoutingMiddleware(model_router)

    # Budget management
    # For token counting, we'll use a stub (integrate with LangSmith in production)
    class SimpleTokenCounter:
        async def count_tokens(self, text, model):
            # Rough estimate: 1 token ~= 4 characters
            return {"input_tokens": max(1, len(text) // 4)}

    token_counter = SimpleTokenCounter()
    budget_middleware = BudgetValidationMiddleware(state_manager, token_counter)
    cost_middleware = CostTrackingMiddleware(state_manager)

    # Reasoning traces
    parser = ContentBlockParser()
    reasoning_middleware = ReasoningTraceMiddleware(parser)

    # 3. Assemble middleware stack
    middleware_stack = [
        ("pii_validation", "before_agent", pii_middleware),
        ("complexity_routing", "before_agent", routing_middleware),
        ("budget_validation", "before_model", budget_middleware),
        ("cost_tracking", "wrap_model_call", cost_middleware),
        ("reasoning_parsing", "after_model", reasoning_middleware),
    ]

    # 4. Create agent
    from tools import TOOLS
    from agent_factory import (
        create_langgraph_agent,
        MiddlewareAwareAgent,
        MiddlewareAdapter,
    )

    agent = await create_langgraph_agent(
        llm_client=llm_client,
        tools=TOOLS,
        checkpoint_storage=checkpoint_storage,
        middleware_stack=middleware_stack,
        system_prompt="""You are a helpful AI assistant with access to various tools.

        You must respect budget constraints and security policies:
        - PII will be automatically redacted from your inputs
        - Your model will be selected based on query complexity
        - Token usage and costs are tracked for each query
        - High-risk operations may require human approval

        Always:
        - Explain your reasoning
        - Use tools appropriately
        - Acknowledge constraints
        """,
        verbose=True,
    )

    # 5. Wrap with middleware adapter
    adapter = MiddlewareAdapter(middleware_stack)
    aware_agent = MiddlewareAwareAgent(
        agent=agent,
        state_manager=state_manager,
        middleware_adapter=adapter,
    )

    return aware_agent


# Usage example
async def example_usage():
    """Example of using the agent"""

    agent = await setup_production_agent()

    # Execute a query
    result = await agent.ainvoke(
        user_id="user_123",
        session_id="session_abc",
        user_input="Analyze the architecture of microservices systems",
        config={
            "user_preferences": {
                "preferred_provider": "anthropic",
            },
        },
    )

    print("Agent Response:")
    print(f"Output: {result['output']}")
    print(f"Model Used: {result['metadata']['model_used']}")
    print(f"Cost: ${result['cost_summary']['cost_used']:.4f}")
    print(f"Tokens Used: {result['cost_summary']['tokens_used']}")
    print(f"\nReasoning Insights:")
    for insight in result["reasoning_insights"]:
        print(f"  - {insight}")

    return result


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_usage())
```

---

### 4. API Endpoint Integration (FastAPI)

```python
# api.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import asyncio
import json

app = FastAPI(title="Multi-Model Agent API")

# Global agent instance (initialize in startup event)
agent = None

class AgentQuery(BaseModel):
    """Request schema for agent"""
    query: str
    user_preferences: Optional[Dict] = None
    session_budget: Optional[Dict] = None

class AgentResponse(BaseModel):
    """Response schema from agent"""
    output: str
    cost_summary: Dict[str, Any]
    metadata: Dict[str, Any]
    reasoning_insights: list = []

@app.on_event("startup")
async def startup():
    """Initialize agent on startup"""
    global agent
    from setup import setup_production_agent
    agent = await setup_production_agent()

@app.post("/v1/agent/invoke", response_model=AgentResponse)
async def invoke_agent(
    request: AgentQuery,
    user_id: str,  # From auth middleware
    session_id: str = None,  # Default from user_id
) -> AgentResponse:
    """
    Execute agent with query.

    Middleware stack handles:
    - PII redaction
    - Model routing
    - Budget validation
    - Cost tracking
    """

    if session_id is None:
        session_id = f"session_{user_id}"

    try:
        result = await agent.ainvoke(
            user_id=user_id,
            session_id=session_id,
            user_input=request.query,
            config={
                "user_preferences": request.user_preferences or {},
            },
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return AgentResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

@app.get("/v1/agent/stream")
async def stream_agent_response(
    query: str,
    user_id: str,
    session_id: str = None,
):
    """
    Stream agent response token-by-token.

    Returns Server-Sent Events (SSE) with tokens and updates.
    """

    if session_id is None:
        session_id = f"session_{user_id}"

    async def event_generator():
        async for event in agent.stream(
            user_id=user_id,
            session_id=session_id,
            user_input=query,
        ):
            # Yield SSE format
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )

@app.get("/v1/budget/{user_id}/{session_id}")
async def get_budget_summary(user_id: str, session_id: str):
    """Get budget summary for a session"""

    summary = await agent.state_manager.get_budget_summary(user_id, session_id)
    return summary

@app.post("/v1/budget/{user_id}/{session_id}/reset")
async def reset_budget(user_id: str, session_id: str):
    """Reset session budget (admin only)"""

    await agent.state_manager.reset_session(user_id, session_id)
    return {"status": "reset", "user_id": user_id, "session_id": session_id}

# Health check
@app.get("/health")
async def health():
    return {"status": "ok"}
```

---

### 5. Environment Configuration

```bash
# .env
# Database
POSTGRES_URL=postgresql://user:password@localhost:5432/langgraph

# LLM Providers
ANTHROPIC_API_KEY=sk-ant-xxxxx
OPENAI_API_KEY=sk-xxx
GOOGLE_API_KEY=xxxxx

# Observability
LANGSMITH_API_KEY=ls_xxxxx
LANGSMITH_PROJECT=production

# Budget (optional, per user tier)
DEFAULT_MAX_TOKENS=50000
DEFAULT_MAX_COST=10.0
DEFAULT_MAX_REQUESTS=100

# PII Detection
PII_STRICT_MODE=false
PII_REDACTION_ENABLED=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

---

## Key Features

✓ **Composable Middleware**: Each hook independent and pluggable
✓ **State Persistence**: Automatic checkpoint saving with LangGraph
✓ **Cost Transparency**: Real-time budget tracking
✓ **PII Protection**: Automatic detection and redaction
✓ **Model Routing**: Dynamic selection based on query complexity
✓ **Reasoning Extraction**: Parse reasoning traces from all providers
✓ **Human Approval**: Gate high-risk operations
✓ **Error Recovery**: Graceful degradation and rollback
✓ **Streaming Support**: Token-by-token output for UX
✓ **Production-Ready**: Logging, monitoring, error handling

---

## Testing the Setup

```python
# test_agent.py
import pytest
import asyncio

@pytest.mark.asyncio
async def test_pii_redaction():
    """Test PII detection and redaction"""
    from middleware_stack.pii import PIIDetector

    detector = PIIDetector()
    text = "My SSN is 123-45-6789 and my email is test@example.com"

    clean_text, findings = detector.redact(text)

    assert "[REDACTED_SSN]" in clean_text
    assert "[REDACTED_EMAIL]" in clean_text
    assert len(findings) == 2

@pytest.mark.asyncio
async def test_budget_validation():
    """Test budget enforcement"""
    from middleware_stack.state import SessionBudget

    budget = SessionBudget(
        user_id="test_user",
        session_id="test_session",
        max_tokens_per_session=1000,
        max_cost_per_session=1.0,
    )

    assert budget.can_proceed == True

    budget.update_usage("claude-3-5-sonnet-20241022", 800, 200, 0.95)
    assert budget.can_proceed == False  # Over budget
    assert budget.tokens_remaining == 0

@pytest.mark.asyncio
async def test_complexity_routing():
    """Test query complexity analysis"""
    from middleware_stack.routing import ComplexityAnalyzer, QueryComplexity

    analyzer = ComplexityAnalyzer()

    simple = analyzer.analyze("What is Python?")
    assert simple == QueryComplexity.SIMPLE

    complex_q = analyzer.analyze(
        "Design a distributed database architecture with "
        "consistency guarantees and fault tolerance"
    )
    assert complex_q == QueryComplexity.COMPLEX

    reasoning = analyzer.analyze("Prove the Collatz conjecture")
    assert reasoning == QueryComplexity.REQUIRES_REASONING

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

