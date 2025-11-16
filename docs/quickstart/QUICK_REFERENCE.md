# Quick Reference Guide: Middleware Stack

## 1. At-a-Glance Middleware Comparison

```
┌─────────────────────────┬──────────┬──────┬─────────────────────┐
│ Middleware              │ Hook     │ Risk │ Primary Purpose     │
├─────────────────────────┼──────────┼──────┼─────────────────────┤
│ PIIValidationMidd       │ before_a │ HIGH │ Redact sensitive    │
│                         │ gent     │      │ data                │
│                         │          │      │                     │
│ ComplexityRouting       │ before_a │ LOW  │ Route to right      │
│                         │ gent     │      │ model by complexity │
│                         │          │      │                     │
│ HumanInTheLoop          │ before_m │ HIGH │ Approval gate for   │
│                         │ odel     │      │ high-risk ops       │
│                         │          │      │                     │
│ ContextManagement       │ before_m │ LOW  │ Manage token budget │
│                         │ odel     │      │ with summarization  │
│                         │          │      │                     │
│ BudgetValidation        │ before_m │ MED  │ Validate budget     │
│                         │ odel     │      │ before LLM call     │
│                         │          │      │                     │
│ CostTracking            │ wrap_mod │ LOW  │ Track actual costs   │
│                         │ el_call  │      │ and usage           │
│                         │          │      │                     │
│ ReasoningTrace          │ after_mo │ LOW  │ Extract reasoning   │
│                         │ del      │      │ and insights        │
│                         │          │      │                     │
│ ToolCallCostTracker     │ wrap_too │ LOW  │ Track tool exec     │
│                         │ l_call   │      │ costs               │
└─────────────────────────┴──────────┴──────┴─────────────────────┘

ACRONYMS:
  before_agent = before_a
  before_model = before_m
  wrap_model_call = wrap_mod
  wrap_tool_call = wrap_too
  after_model = after_mo
```

## 2. Installation & Configuration

### Prerequisites
```bash
pip install langchain langchain-anthropic langchain-openai
pip install langgraph
pip install postgresql  # For checkpoints
```

### Minimal Setup (5 minutes)
```python
from middleware_stack.routing import ModelRouter, ComplexityRoutingMiddleware
from middleware_stack.budget import BudgetValidationMiddleware, CostTrackingMiddleware
from middleware_stack.state import SessionStateManager

# 1. Setup state manager
state_manager = SessionStateManager(checkpoint_storage)

# 2. Create minimal middleware
router = ModelRouter(state_manager)
routing_mw = ComplexityRoutingMiddleware(router)
budget_mw = BudgetValidationMiddleware(state_manager, token_counter)
cost_mw = CostTrackingMiddleware(state_manager)

# 3. Create agent with middleware
agent = await create_langgraph_agent(
    llm_client=llm,
    tools=tools,
    checkpoint_storage=checkpoint_storage,
    middleware_stack=[
        ("routing", "before_agent", routing_mw),
        ("budget", "before_model", budget_mw),
        ("cost", "wrap_model_call", cost_mw),
    ]
)
```

## 3. Common Patterns

### Pattern 1: Cost-Conscious SaaS
```python
middleware_stack = [
    ("pii", "before_agent", PIIValidationMiddleware(pii_detector)),
    ("routing", "before_agent", ComplexityRoutingMiddleware(router)),
    ("budget", "before_model", BudgetValidationMiddleware(...)),
    ("cost", "wrap_model_call", CostTrackingMiddleware(...)),
]

# Result: Routes cheap models for simple queries, expensive for complex
# Users see real costs in realtime
```

### Pattern 2: Healthcare/Finance (High Compliance)
```python
middleware_stack = [
    ("pii_strict", "before_agent",
     PIIValidationMiddleware(pii_detector, strict_mode=True)),
    ("approval", "before_model",
     HumanInTheLoopMiddleware(risk_assessor, approval_store)),
    ("budget", "before_model", BudgetValidationMiddleware(...)),
    ("cost", "wrap_model_call", CostTrackingMiddleware(...)),
    ("reasoning", "after_model", ReasoningTraceMiddleware(parser)),
]

# Result: Blocks any PII, requires approval for risky operations,
# tracks reasoning for audit trail, enforces budgets
```

### Pattern 3: Long Conversational Chat
```python
middleware_stack = [
    ("pii", "before_agent", PIIValidationMiddleware(pii_detector)),
    ("routing", "before_agent", ComplexityRoutingMiddleware(router)),
    ("context", "before_model", ContextManagementMiddleware(summarizer)),
    ("approval", "before_model", HumanInTheLoopMiddleware(...)),
    ("budget", "before_model", BudgetValidationMiddleware(...)),
    ("cost", "wrap_model_call", CostTrackingMiddleware(...)),
    ("reasoning", "after_model", ReasoningTraceMiddleware(parser)),
]

# Result: Handles long conversations with automatic summarization,
# prevents token limit errors, tracks costs per turn
```

## 4. Common Configuration Values

```python
# Budget Tiers (USD per month)
BUDGET_TIERS = {
    "free": 0.50,
    "pro": 10.0,
    "enterprise": None,  # Custom
}

# Token Limits
TOKEN_LIMITS = {
    "free": 10000,
    "pro": 100000,
    "enterprise": None,  # Unlimited
}

# Request Limits
REQUEST_LIMITS = {
    "free": 50,
    "pro": 1000,
    "enterprise": None,  # Unlimited
}

# Model Selection Rules
MODEL_RULES = {
    QueryComplexity.SIMPLE: "claude-3-haiku-20240307",
    QueryComplexity.MODERATE: "claude-3-5-sonnet-20241022",
    QueryComplexity.COMPLEX: "claude-3-opus-20240229",
}

# PII Detection
PII_CONFIG = {
    "healthcare": {
        "strict_mode": True,
        "detect_ssn": True,
        "detect_medical_id": True,
    },
    "finance": {
        "strict_mode": True,
        "detect_credit_card": True,
        "detect_account": True,
    },
    "general": {
        "strict_mode": False,
        "detect_email": True,
    },
}

# Checkpoint Strategy
CHECKPOINT_CONFIG = {
    "development": {
        "frequency": "every_step",
        "keep_days": 30,
        "enable_verbose_logging": True,
    },
    "production": {
        "frequency": "after_agent_turn",
        "keep_count": 10,
        "archive_days": 7,
    },
}
```

## 5. Debugging Checklist

### Issue: Budget exceeded unexpectedly
```
1. Check token estimates:
   - Count actual tokens used vs. estimate
   - Adjust routing thresholds if estimates off

2. Review tool costs:
   - Expensive tool calls during execution?
   - Wrap with timeout and fallback

3. Analyze model selection:
   - Is cheap model being used for complex queries?
   - Adjust complexity analyzer rules

4. Monitor conversation length:
   - Long histories not being summarized?
   - Lower summarization threshold
```

### Issue: Reasoning traces not captured
```
1. Check provider:
   - Anthropic Claude: Uses "thinking" block
   - OpenAI: Uses "reasoning" field
   - Google: Limited reasoning support

2. Enable thinking mode:
   - Set enable_thinking=True in routing
   - Requires claude-3-opus or gpt-4-turbo

3. Check content block parsing:
   - Verify parser for your provider
   - Add logging to parser.parse_*() methods
```

### Issue: PII not detected
```
1. Check detection mode:
   - Ensure PIIDetector(strict_mode=X) correct

2. Add custom patterns:
   - PII_PATTERNS dict extensible
   - Add company-specific PII (employee IDs, etc.)

3. Test regex patterns:
   - Use regex101.com to validate patterns
   - Test against real examples
```

### Issue: Human approval timing out
```
1. Check WebSocket connection:
   - Ensure notification system working
   - Check if approval request reaching user

2. Increase timeout:
   - Default 300 seconds
   - Adjust in request_approval() call

3. Add reminder notifications:
   - Notify user at 50%, 80%, 99% of timeout
   - Send multiple channels (email, SMS, etc.)
```

## 6. Monitoring Dashboard Queries

### Cost Analysis
```python
# Daily spend by user
SELECT
  user_id,
  DATE(created_at) as date,
  SUM(cost_usd) as total_cost,
  COUNT(*) as request_count,
  AVG(tokens_used) as avg_tokens
FROM agent_executions
GROUP BY user_id, DATE(created_at)
ORDER BY total_cost DESC;

# Model usage distribution
SELECT
  target_model,
  COUNT(*) as calls,
  SUM(tokens_used) as total_tokens,
  AVG(cost_usd) as avg_cost
FROM agent_executions
GROUP BY target_model;
```

### Error Analysis
```python
# Error rate by middleware
SELECT
  error_source,
  COUNT(*) as error_count,
  COUNT(*)::float / SUM(COUNT(*)) OVER () * 100 as pct
FROM agent_errors
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY error_source
ORDER BY error_count DESC;

# Recovery success rate
SELECT
  error_type,
  SUM(CASE WHEN recovered THEN 1 ELSE 0 END) as recovered_count,
  COUNT(*) as total_errors,
  100.0 * SUM(CASE WHEN recovered THEN 1 ELSE 0 END) / COUNT(*) as recovery_rate
FROM agent_errors
GROUP BY error_type;
```

### Performance Analysis
```python
# Middleware latency breakdown
SELECT
  middleware_name,
  COUNT(*) as executions,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_ms) as p50,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) as p95,
  PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_ms) as p99
FROM middleware_metrics
WHERE created_at > NOW() - INTERVAL '1 day'
GROUP BY middleware_name;
```

## 7. Deployment Checklist

### Pre-Production
- [ ] Load test middleware stack with 100 concurrent users
- [ ] Validate cost calculations against provider bills
- [ ] Test PII detection with real-world examples
- [ ] Verify checkpoint recovery works
- [ ] Check error handling for all failure modes
- [ ] Measure p99 latency overhead (<100ms)
- [ ] Test budget enforcement at limits
- [ ] Verify human approval workflow

### Production Rollout
- [ ] Migrate 10% traffic first
- [ ] Monitor error rates, costs, latency
- [ ] Collect user feedback on model quality
- [ ] Check that budgets are working
- [ ] Verify PII redaction success
- [ ] Migrate 50% traffic
- [ ] Migrate 100% traffic
- [ ] Archive old checkpoints

### Post-Deployment
- [ ] Monitor daily costs vs. budget
- [ ] Track error rates by middleware
- [ ] Analyze model selection decisions
- [ ] Adjust complexity thresholds if needed
- [ ] Review user feedback on quality
- [ ] Clean up old checkpoints weekly
- [ ] Generate weekly cost reports

## 8. File Structure

```
your-project/
├── middleware_stack/
│   ├── __init__.py
│   ├── state.py              # SessionBudget, StateManager
│   ├── pii.py                # PIIDetector, PIIValidationMiddleware
│   ├── routing.py            # ComplexityAnalyzer, ModelRouter
│   ├── budget.py             # TokenCounter, Budget/Cost Tracking
│   ├── reasoning.py          # ContentBlockParser, Reasoning Traces
│   ├── approval.py           # HumanInTheLoop, Approval gates
│   ├── context.py            # Context summarization
│   └── tools.py              # Tool cost tracking
│
├── agent_factory.py           # create_langgraph_agent()
├── setup.py                   # setup_production_agent()
├── api.py                     # FastAPI endpoints
├── requirements.txt           # Dependencies
├── .env                       # Configuration
└── tests/
    ├── test_pii.py
    ├── test_routing.py
    ├── test_budget.py
    └── test_integration.py
```

## 9. Troubleshooting Table

| Issue | Cause | Solution |
|-------|-------|----------|
| Tokens exceeding budget | Long context | Enable ContextManagementMiddleware |
| Slow responses | All requests using expensive model | Check ComplexityRoutingMiddleware thresholds |
| PII leaking | Detection disabled | Verify PIIValidationMiddleware enabled |
| High costs unexpectedly | Expensive tools being overused | Wrap tools, add timeout, fallback |
| Approvals timing out | WebSocket disconnect | Check notification system, increase timeout |
| Reasoning not captured | Wrong model or provider | Use Claude/GPT-4, set enable_thinking=True |
| Checkpoints too large | Saving every step | Use after_agent_turn frequency |
| Memory growing unbounded | No checkpoint cleanup | Enable automatic pruning, set keep_count |

## 10. Migration from Legacy LangChain

```python
# OLD (Legacy)
from langchain.agents import AgentType, initialize_agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
)

# NEW (LangChain 1.0 with Middleware)
from langchain.agents import create_agent
from middleware_stack.state import SessionStateManager

state_manager = SessionStateManager(checkpoint_storage)
middleware_stack = [
    ("routing", "before_agent", ComplexityRoutingMiddleware(router)),
    ("budget", "before_model", BudgetValidationMiddleware(...)),
    ("cost", "wrap_model_call", CostTrackingMiddleware(...)),
]

agent = await create_langgraph_agent(
    llm_client=llm,
    tools=tools,
    checkpoint_storage=checkpoint_storage,
    middleware_stack=middleware_stack,
)
```

## Quick Start Commands

```bash
# Install
pip install -r requirements.txt

# Setup database
psql -c "CREATE DATABASE langgraph"
python -c "from setup import setup_production_agent; await setup_production_agent()"

# Run tests
pytest tests/ -v

# Start API
uvicorn api:app --reload

# Monitor costs
python -c "from analytics import cost_dashboard; cost_dashboard()"

# Reset user budget
python -c "from middleware_stack.state import SessionStateManager; \
           await SessionStateManager(...).reset_session('user_id', 'session_id')"
```

---

**For detailed implementation, see:**
- MIDDLEWARE_STACK_DESIGN.md - Complete design
- MIDDLEWARE_IMPLEMENTATION.md - Production code
- LANGGRAPH_INTEGRATION.md - LangChain 1.0 integration
- ARCHITECTURE_DIAGRAMS.md - Visual diagrams
