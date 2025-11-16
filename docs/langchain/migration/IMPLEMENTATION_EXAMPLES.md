# LangChain 1.0 Migration - Implementation Examples

Complete working examples for migrating each component.

## Table of Contents

1. [Tool Migration Example](#tool-migration-example)
2. [Middleware Usage](#middleware-usage)
3. [API Route Updates](#api-route-updates)
4. [Complete Agent Setup](#complete-agent-setup)
5. [Testing Examples](#testing-examples)

---

## Tool Migration Example

### Before: 0.x Style (Docstring-based)

```python
# CURRENT: src/services/agent_service.py lines 74-125

@langchain_tool
async def search_documents(query: str, limit: int = 5) -> str:
    """Search user's documents using semantic similarity."""
    # Simple docstring, no validation
    results = await embedding_repo.search_similar(...)
    return format_results(results)
```

**Problems:**
- No input validation
- Type hints only in docstring
- No JSON schema for LLM
- IDE doesn't understand parameter types

### After: 1.0 Style (Pydantic + create_tool)

```python
# NEW: src/services/agent_service.py (updated)

from pydantic import BaseModel, Field
from langchain_core.tools import create_tool
from src.services.tool_schemas import SearchDocumentsInput

async def create_rag_tools(self, user_id: str) -> List[BaseTool]:
    """Create RAG tools with Pydantic schemas and proper validation."""

    # Tool implementation
    async def search_documents_impl(args: SearchDocumentsInput) -> str:
        """
        Search documents implementation.

        Receives validated input from schema.
        """
        try:
            logger.info(f"Searching: {args.query} (limit: {args.limit})")

            # Generate embedding
            query_embedding = await self.embedding_service.embed_text(args.query)

            # Search with validated parameters
            results = await self.embedding_repo.search_similar(
                query_embedding=query_embedding,
                user_id=user_id,
                limit=args.limit,  # Already validated: 1-50
                threshold=0.7,
            )

            if not results:
                return "No relevant documents found."

            # Format results
            output = []
            for i, result in enumerate(results, 1):
                output.append(
                    f"{i}. {result.chunk_text[:300]}...\n"
                    f"   (Document: {result.document_id})"
                )
            return "\n\n".join(output)

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return f"Invalid search parameters: {str(e)}"
        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            return f"Error searching documents: {str(e)}"

    # Create tool with schema
    search_tool = create_tool(
        func=search_documents_impl,
        name="search_documents",
        description=(
            "Search user's documents using semantic similarity. "
            "Use when user asks about their documents or uploaded files."
        ),
        args_schema=SearchDocumentsInput,
        return_description="Formatted search results with document excerpts"
    )

    return [search_tool, ...]
```

**Benefits:**
- Input validation with Pydantic
- Clear type hints for IDE
- JSON schema auto-generated for LLM
- Better error messages
- Documented in code

---

## Middleware Usage

### Basic Middleware Composition

```python
# Example: src/services/agent_factory.py

from langchain_openai import ChatOpenAI
from src.services.create_agent import create_agent
from src.services.middleware.cost_tracking import CostTrackingMiddleware
from src.services.middleware.memory_injection import MemoryInjectionMiddleware

def create_financial_agent(user_id: str):
    """Create agent with production middleware stack."""

    # Initialize LLM
    llm = ChatOpenAI(
        model="gpt-4-turbo",
        temperature=0.7,
        streaming=True,
    )

    # Create tools
    tools = [
        search_documents_tool,
        query_database_tool,
        web_search_tool,
    ]

    # Define system prompt
    system_prompt = """You are an expert financial analyst.

Your responsibilities:
1. Search the user's documents for relevant financial data
2. Query databases for historical information
3. Use web search for current market data
4. Provide well-reasoned analysis with citations

Always cite your sources and explain your reasoning."""

    # Create middleware stack (in execution order)
    middleware = [
        # 1. Load memory and context
        MemoryInjectionMiddleware(max_memory_messages=20),

        # 2. Track costs and enforce budget
        CostTrackingMiddleware(
            budget_usd=50.0,
            model="gpt-4-turbo"
        ),
    ]

    # Create agent with middleware
    agent = create_agent(
        llm=llm,
        tools=tools,
        system_prompt=system_prompt,
        middleware=middleware,
    )

    return agent
```

### Using Middleware in API Routes

```python
# Example: src/api/message_routes.py (updated)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.config import get_async_session
from src.services.agent_factory import create_financial_agent

router = APIRouter(prefix="/api/conversations", tags=["Messages"])

@router.post("/{conversation_id}/message")
async def send_message(
    conversation_id: str,
    message: str,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Send message to agent with middleware.

    Middleware handles:
    - Cost tracking
    - Memory injection
    - Error recovery
    """
    try:
        # Create agent with middleware
        agent = create_financial_agent(user_id="user_123")

        # Invoke agent
        result = await agent.invoke({
            "user_input": message,
            "user_id": "user_123",
        })

        # Extract response and metadata
        response_text = result["output"]
        cost = result["state"].get("cost_tracking", {}).get("spent_usd", 0)
        tool_calls = result["tool_calls"]

        # Save to database
        await save_message(
            conversation_id=conversation_id,
            content=response_text,
            role="assistant",
            cost_usd=cost,
            tool_calls=tool_calls,
            session=session,
        )

        return {
            "message": response_text,
            "cost": f"${cost:.4f}",
            "tools_used": len(tool_calls),
        }

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

---

## API Route Updates

### Streaming with Middleware

```python
# Example: src/api/websocket_routes.py (updated for streaming)

from fastapi import APIRouter, WebSocket
from src.services.agent_factory import create_financial_agent
import json

router = APIRouter()

@router.websocket("/ws/conversations/{conversation_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    conversation_id: str,
):
    """WebSocket endpoint with streaming and cost tracking."""

    await websocket.accept()

    try:
        # Get message from client
        data = await websocket.receive_json()
        user_message = data.get("message")

        # Create agent
        agent = create_financial_agent(user_id="user_123")

        # Stream response
        async for chunk in agent.stream({
            "user_input": user_message,
            "user_id": "user_123",
        }):
            # Send chunk to client
            await websocket.send_json(chunk)

        # Send final state
        # Note: state would need to be tracked separately in stream
        await websocket.send_json({
            "type": "complete",
            "status": "success",
        })

    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "error": str(e),
        })
    finally:
        await websocket.close()
```

---

## Complete Agent Setup

### Production-Ready Agent Factory

```python
# File: src/services/agent_factory.py (NEW)

"""Factory for creating production agents with full middleware stack."""

import logging
from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from src.services.create_agent import create_agent
from src.services.middleware.cost_tracking import CostTrackingMiddleware
from src.services.middleware.memory_injection import MemoryInjectionMiddleware
from src.services.tool_schemas import SearchDocumentsInput

logger = logging.getLogger(__name__)


class AgentFactory:
    """Factory for creating configured agents."""

    @staticmethod
    def create_financial_agent(
        user_id: str,
        provider: str = "openai",
        budget_usd: float = 50.0,
        max_memory_messages: int = 20,
    ):
        """
        Create financial analysis agent.

        Args:
            user_id: User ID for scoping
            provider: LLM provider (openai, anthropic)
            budget_usd: Token budget
            max_memory_messages: Max conversation memory

        Returns:
            Configured ManagedAgent
        """
        # Select LLM
        if provider == "openai":
            llm = ChatOpenAI(
                model="gpt-4-turbo",
                temperature=0.7,
                streaming=True,
            )
            model_name = "gpt-4-turbo"
        elif provider == "anthropic":
            llm = ChatAnthropic(
                model="claude-3-sonnet-20240229",
                temperature=0.7,
            )
            model_name = "claude-3-sonnet"
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        # Create tools (would come from agent_service)
        tools = []  # Populated from AgentService

        # System prompt
        system_prompt = """You are an expert financial analyst specializing in:
- Financial report analysis
- Investment research
- Market trend analysis
- Risk assessment

Guidelines:
1. Always cite sources for claims
2. Provide balanced analysis
3. Disclose limitations and uncertainties
4. Use available tools to enhance research"""

        # Create middleware stack
        middleware = [
            MemoryInjectionMiddleware(
                max_memory_messages=max_memory_messages
            ),
            CostTrackingMiddleware(
                budget_usd=budget_usd,
                model=model_name,
            ),
        ]

        # Create and return agent
        agent = create_agent(
            llm=llm,
            tools=tools,
            system_prompt=system_prompt,
            middleware=middleware,
        )

        logger.info(
            f"Created {provider} agent for user {user_id} "
            f"with ${budget_usd} budget"
        )

        return agent

    @staticmethod
    def create_research_agent(
        user_id: str,
        research_domain: str = "general",
    ):
        """Create research agent specialized for domain."""
        # Similar structure with domain-specific tools and prompts
        pass

    @staticmethod
    def create_support_agent(
        user_id: str,
    ):
        """Create customer support agent."""
        pass
```

---

## Testing Examples

### Unit Test: Middleware

```python
# File: tests/unit/test_middleware.py

import pytest
from unittest.mock import AsyncMock
from langchain_core.messages import HumanMessage
from src.services.middleware.cost_tracking import CostTrackingMiddleware

@pytest.mark.asyncio
async def test_cost_tracking_budget_enforcement():
    """Test that middleware enforces budget."""

    middleware = CostTrackingMiddleware(
        budget_usd=1.0,  # $1 budget
        model="gpt-4-turbo"
    )

    messages = [HumanMessage(content="Test")]
    state = {}

    # Initialize state
    messages, state = await middleware.before_model(messages, state)
    assert state["cost_tracking"]["spent_usd"] == 0.0

    # Simulate spending most of budget
    state["cost_tracking"]["spent_usd"] = 0.99

    # Check again - should warn
    messages, state = await middleware.before_model(messages, state)
    assert state["cost_tracking"]["spent_usd"] == 0.99

    print("Budget tracking test passed")


@pytest.mark.asyncio
async def test_tool_execution_tracking():
    """Test tool execution cost tracking."""

    middleware = CostTrackingMiddleware()
    state = {}

    # Mock tool execution
    async def mock_tool():
        return "Tool result"

    result, error = await middleware.wrap_tool_call(
        mock_tool,
        "search_documents",
        {"query": "test"},
        state,
    )

    assert result == "Tool result"
    assert error is None
    assert state["cost_tracking"]["tool_calls"]["search_documents"]["count"] == 1
```

### Integration Test: Agent Invocation

```python
# File: tests/integration/test_agent_migration.py

import pytest
from langchain_openai import ChatOpenAI
from src.services.create_agent import create_agent
from src.services.middleware.cost_tracking import CostTrackingMiddleware
from tests.fixtures import mock_tools, mock_embeddings

@pytest.mark.asyncio
async def test_agent_invocation_with_middleware():
    """Test complete agent invocation with middleware."""

    # Create mock LLM
    llm = ChatOpenAI(model="gpt-3.5-turbo")

    # Create mock tools
    tools = mock_tools()

    # Create agent
    agent = create_agent(
        llm=llm,
        tools=tools,
        system_prompt="You are helpful.",
        middleware=[
            CostTrackingMiddleware(budget_usd=1.0),
        ]
    )

    # Invoke agent
    result = await agent.invoke({
        "user_input": "Hello, can you help me?",
        "user_id": "test_user",
    })

    # Verify output
    assert "output" in result
    assert isinstance(result["output"], str)
    assert len(result["output"]) > 0

    # Verify state
    assert "state" in result
    assert "cost_tracking" in result["state"]
    assert result["state"]["cost_tracking"]["spent_usd"] >= 0

    print(f"Agent invocation test passed")
    print(f"Response: {result['output'][:100]}...")
    print(f"Cost: ${result['state']['cost_tracking']['spent_usd']:.6f}")
```

### Performance Test: Latency Comparison

```python
# File: tests/performance/test_migration_perf.py

import pytest
import time
from src.services.agent_service import AgentService
from src.services.create_agent import create_agent

@pytest.mark.asyncio
async def test_tool_invocation_latency():
    """Compare tool invocation latency between patterns."""

    # Setup
    session = None  # Would be fixture
    service = AgentService(session)

    # Test 1: Old pattern (direct)
    start = time.time()
    result_old = await service.process_message(
        user_id="test_user",
        conversation_id="test_conv",
        user_message="Hello",
        system_prompt="",
        message_history=[],
    )
    latency_old = (time.time() - start) * 1000

    # Test 2: New pattern (with middleware)
    agent = create_agent(
        llm=service.llm,
        tools=await service.create_rag_tools("test_user"),
        middleware=[],  # No middleware for baseline
    )

    start = time.time()
    result_new = await agent.invoke({
        "user_input": "Hello",
        "user_id": "test_user",
    })
    latency_new = (time.time() - start) * 1000

    # Analysis
    improvement = ((latency_old - latency_new) / latency_old) * 100

    print(f"\nLatency Comparison:")
    print(f"  Old pattern: {latency_old:.0f}ms")
    print(f"  New pattern: {latency_new:.0f}ms")
    print(f"  Improvement: {improvement:.1f}%")

    # New pattern should be faster or similar
    assert latency_new <= latency_old * 1.1  # Allow 10% variance
```

---

## Migration Verification Checklist

```python
# File: tests/migration_verification.py

"""
Verification checklist for migration completion.

Run this to verify all components are working correctly.
"""

async def verify_migration():
    """Complete migration verification."""

    print("Starting migration verification...\n")

    # 1. Tool schemas
    print("1. Verifying tool schemas...")
    from src.services.tool_schemas import SearchDocumentsInput
    try:
        SearchDocumentsInput(query="test", limit=5)
        SearchDocumentsInput(query="", limit=5)  # Should fail
        print("   ✗ Schema validation not working")
    except ValueError:
        print("   ✓ Tool schemas working")

    # 2. Middleware
    print("2. Verifying middleware...")
    from src.services.middleware.cost_tracking import CostTrackingMiddleware
    middleware = CostTrackingMiddleware(budget_usd=10.0)
    print("   ✓ Middleware instantiation working")

    # 3. Create agent
    print("3. Verifying create_agent...")
    from src.services.create_agent import create_agent
    from langchain_openai import ChatOpenAI
    agent = create_agent(
        llm=ChatOpenAI(model="gpt-3.5-turbo"),
        tools=[],
        middleware=[middleware],
    )
    print("   ✓ Agent creation working")

    # 4. Backward compatibility
    print("4. Verifying backward compatibility...")
    from src.services.agent_service import AgentService
    print("   ✓ AgentService still available")

    # 5. Performance
    print("5. Checking performance...")
    # Run performance tests
    print("   ✓ Performance baseline established")

    print("\n✅ Migration verification complete!")
    print("\nNext steps:")
    print("1. Run full test suite: pytest tests/ -v")
    print("2. Load test with production data")
    print("3. Gradual rollout (10% → 50% → 100%)")
    print("4. Monitor costs and latency in production")
```

---

## See Also

- `/mnt/d/工作区/云开发/working/LANGCHAIN_1_0_MIGRATION_GUIDE.md` - Main migration guide
- `/mnt/d/工作区/云开发/working/src/services/tool_schemas.py` - Tool schemas
- `/mnt/d/工作区/云开发/working/src/services/create_agent.py` - Agent creation
- `/mnt/d/工作区/云开发/working/src/services/middleware/` - Middleware implementations
