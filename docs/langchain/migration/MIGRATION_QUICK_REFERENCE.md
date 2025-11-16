# LangChain 1.0 Migration - Quick Reference

Fast lookup guide for migration decisions and patterns.

## Decision Trees

### Should I Migrate Now?

```
┌─ Is your system in production? ─────┐
│                                     │
├─ Yes: Need migration? (Y/N)         │
│    ├─ No: Skip for now             │
│    └─ Yes: Use compatibility layer │
│           (gradual migration)       │
│                                     │
└─ No: Start with 1.0 patterns       │
    (new development)                 │
```

### Which Middleware Do I Need?

```
Do you need:
├─ Cost tracking?
│  └─ Yes → CostTrackingMiddleware
├─ Context window management?
│  └─ Yes → MemoryInjectionMiddleware
├─ Error recovery?
│  └─ Yes → ErrorRecoveryMiddleware (custom)
├─ PII protection?
│  └─ Yes → PIIProtectionMiddleware (custom)
└─ All above?
   └─ Use full production stack
```

## Code Migration Cheat Sheet

### Tool Definition

**Pattern: Before (0.x)**
```python
@langchain_tool
async def search(query: str, limit: int = 5) -> str:
    """Search documents."""
    # Implementation
```

**Pattern: After (1.0)**
```python
from pydantic import BaseModel, Field
from langchain_core.tools import create_tool

class SearchInput(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    limit: int = Field(default=5, ge=1, le=50)

async def search_impl(args: SearchInput) -> str:
    # Implementation

tool = create_tool(
    func=search_impl,
    name="search",
    args_schema=SearchInput,
)
```

### Agent Creation

**Pattern: Before (0.x)**
```python
# Manual tool binding and message handling
llm_with_tools = llm.bind_tools(tools)
response = await llm_with_tools.ainvoke(messages)
# Manual tool execution and error handling
```

**Pattern: After (1.0)**
```python
from src.services.create_agent import create_agent

agent = create_agent(
    llm=llm,
    tools=tools,
    system_prompt="...",
    middleware=[...],
)

result = await agent.invoke({
    "user_input": "...",
    "user_id": "user_123",
})
```

### Middleware Usage

**Pattern: Composition**
```python
# Middleware executes in order
middleware = [
    # 1. Load context first
    MemoryInjectionMiddleware(),
    # 2. Then track costs
    CostTrackingMiddleware(),
    # 3. Finally handle errors
    ErrorRecoveryMiddleware(),
]

agent = create_agent(
    llm=llm,
    tools=tools,
    middleware=middleware,
)
```

## Common Patterns

### Pattern 1: Basic Agent with Cost Tracking

```python
from src.services.create_agent import create_agent
from src.services.middleware.cost_tracking import CostTrackingMiddleware

agent = create_agent(
    llm=ChatOpenAI(model="gpt-4-turbo"),
    tools=tools,
    middleware=[
        CostTrackingMiddleware(budget_usd=50.0),
    ]
)
```

**Use When:** Need to monitor or limit API costs

### Pattern 2: Agent with Memory Management

```python
from src.services.middleware.memory_injection import MemoryInjectionMiddleware

agent = create_agent(
    llm=llm,
    tools=tools,
    middleware=[
        MemoryInjectionMiddleware(max_memory_messages=30),
    ]
)
```

**Use When:** Have long conversations that exceed token limits

### Pattern 3: Production Stack

```python
agent = create_agent(
    llm=llm,
    tools=tools,
    system_prompt="You are...",
    middleware=[
        MemoryInjectionMiddleware(max_memory_messages=20),
        CostTrackingMiddleware(budget_usd=100.0),
        # Add custom middleware as needed
    ]
)
```

**Use When:** Full production deployment with all safeguards

### Pattern 4: Custom Middleware

```python
from src.services.middleware import AgentMiddleware

class MyCustomMiddleware(AgentMiddleware):
    async def before_agent(self, messages, state):
        # Custom logic
        return messages, state

    async def wrap_tool_call(self, tool_execute, tool_name, args, state):
        # Custom tool logic
        result, error = await super().wrap_tool_call(...)
        return result, error

# Use it
agent = create_agent(
    llm=llm,
    tools=tools,
    middleware=[MyCustomMiddleware()],
)
```

**Use When:** Need specialized behavior not in standard middleware

## File Structure

```
src/
├── services/
│   ├── agent_service.py          # KEEP: Original service
│   ├── create_agent.py           # NEW: 1.0 agent creation
│   ├── tool_schemas.py           # NEW: Pydantic schemas
│   ├── middleware/
│   │   ├── __init__.py          # NEW: Base middleware
│   │   ├── cost_tracking.py      # NEW: Cost tracking
│   │   └── memory_injection.py   # NEW: Memory management
│   ├── langgraph_state.py         # NEW: LangGraph state (future)
│   └── conversation_graph.py      # NEW: Graph definition (future)
│
├── api/
│   ├── message_routes.py         # UPDATE: Use new patterns
│   └── ...
│
└── ...

tests/
├── unit/
│   ├── test_middleware.py        # NEW: Middleware tests
│   ├── test_tool_schemas.py      # NEW: Schema tests
│   └── ...
│
├── integration/
│   ├── test_agent_migration.py   # NEW: Integration tests
│   └── ...
│
├── performance/
│   ├── test_migration_perf.py    # NEW: Performance tests
│   └── ...
│
└── fixtures/
    └── ...
```

## Migration Path Decision

### Small System (< 10 endpoints)
```
Timeline: 1-2 weeks
Approach: Full rewrite to 1.0
Risk: Low
```

### Medium System (10-50 endpoints)
```
Timeline: 2-3 weeks
Approach: Gradual migration with compatibility layer
Risk: Low-Medium
Process:
  Week 1: Update tools with schemas
  Week 2: Implement middleware
  Week 3: Gradual traffic shift
```

### Large System (50+ endpoints)
```
Timeline: 3-4 weeks
Approach: Feature-flag based gradual migration
Risk: Medium
Process:
  Week 1: Create parallel implementation
  Week 2: Add feature flags and routing
  Week 3: Gradual traffic shift (10% → 50% → 100%)
  Week 4: Cleanup and monitoring
```

## Performance Targets

| Metric | Target | Acceptable |
|--------|--------|-----------|
| Tool latency | < 600ms | < 800ms |
| Agent init | < 150ms | < 200ms |
| Token overhead | < 500 | < 1000 |
| Memory per conv | < 3MB | < 5MB |

## Deployment Checklist

- [ ] All tests passing
- [ ] No performance regression
- [ ] Cost tracking accurate
- [ ] Backward compatibility verified
- [ ] Documentation updated
- [ ] Team trained on new patterns
- [ ] Monitoring/alerts configured
- [ ] Rollback plan in place

## Troubleshooting

### Issue: Tests fail with "Tool X not found"
**Solution:** Check tool names match between schema and registration

### Issue: High token usage after migration
**Solution:** Implement MemoryInjectionMiddleware with summarization

### Issue: Cost tracking not accurate
**Solution:** Ensure CostTrackingMiddleware wraps all LLM calls

### Issue: Middleware execution order wrong
**Solution:** Reorder middleware list; earlier ones execute first

### Issue: Type hints not working in IDE
**Solution:** Use Pydantic models in tool input schemas

## Quick Links

- **Main Guide:** `/mnt/d/工作区/云开发/working/LANGCHAIN_1_0_MIGRATION_GUIDE.md`
- **Implementation Examples:** `/mnt/d/工作区/云开发/working/IMPLEMENTATION_EXAMPLES.md`
- **Tool Schemas:** `/mnt/d/工作区/云开发/working/src/services/tool_schemas.py`
- **Agent Creation:** `/mnt/d/工作区/云开发/working/src/services/create_agent.py`
- **Middleware Base:** `/mnt/d/工作区/云开发/working/src/services/middleware/__init__.py`
- **Cost Tracking:** `/mnt/d/工作区/云开发/working/src/services/middleware/cost_tracking.py`
- **Testing Guide:** `/mnt/d/工作区/云开发/working/TESTING_GUIDE.md`

## Key Principles

1. **Middleware Composition** - Use hooks instead of large classes
2. **Type Safety** - Always use Pydantic for validation
3. **Gradual Migration** - Keep old patterns working during transition
4. **Cost Awareness** - Track and limit token usage
5. **Streaming Support** - Design for real-time UX
6. **Error Recovery** - Implement graceful failure handling

## Learning Path

1. Read migration guide overview (30 min)
2. Review implementation examples (30 min)
3. Run existing tests (15 min)
4. Implement one tool with new schema (1 hour)
5. Create agent with middleware (1 hour)
6. Write tests for changes (1-2 hours)
7. Performance testing (1 hour)

**Total: ~5-6 hours for understanding → implementation**
