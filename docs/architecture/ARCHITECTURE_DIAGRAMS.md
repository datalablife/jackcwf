# Middleware Stack Architecture Diagrams & Decision Trees

## 1. Complete Execution Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         USER REQUEST LIFECYCLE                               │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │  User Input  │
                              │  (Raw Text)  │
                              └──────┬───────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │   [before_agent] PHASE          │
                    │   ═══════════════════════════   │
                    │   1. PII Validation             │
                    │      ├─ Detect PII              │
                    │      ├─ Redact if found         │
                    │      └─ Log for audit           │
                    │                                 │
                    │   2. Complexity Routing         │
                    │      ├─ Analyze query           │
                    │      ├─ Determine model         │
                    │      └─ Check budget sufficiency│
                    │                                 │
                    │   Output: Cleaned input +       │
                    │           Model selection       │
                    │           Budget estimate       │
                    └────────────────┬────────────────┘
                                     │
                                     ▼
                        ┌────────────────────────┐
                        │  Agent Tool Selection  │
                        │  (Which tools to use?) │
                        └────────────┬───────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │   [before_model] PHASE          │
                    │   ═══════════════════════════   │
                    │   1. Approval Check             │
                    │      ├─ Risk assessment         │
                    │      ├─ High-risk → Wait human │
                    │      └─ Low-risk → Auto approve │
                    │                                 │
                    │   2. Context Management         │
                    │      ├─ Check token count       │
                    │      ├─ Summarize if needed     │
                    │      └─ Manage history          │
                    │                                 │
                    │   3. Budget Validation          │
                    │      ├─ Token estimate          │
                    │      ├─ Cost check              │
                    │      └─ Fail if over budget     │
                    │                                 │
                    │   Output: Model-ready prompt    │
                    │            With context window  │
                    │            Approval granted     │
                    └────────────────┬────────────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │ [wrap_model_call] PHASE         │
                    │ ═══════════════════════════════ │
                    │                                 │
                    │ ┌─────────────────────────┐     │
                    │ │ PRE-CALL:               │     │
                    │ │ • Count input tokens    │     │
                    │ │ • Validate budget       │     │
                    │ │ • Prepare request       │     │
                    │ └─────────────────────────┘     │
                    │                                 │
                    │ ┌─────────────────────────┐     │
                    │ │ EXECUTE:                │     │
                    │ │ • Call LLM model        │     │
                    │ │ • Get response + usage  │     │
                    │ │ • Record token count    │     │
                    │ └─────────────────────────┘     │
                    │                                 │
                    │ ┌─────────────────────────┐     │
                    │ │ POST-CALL:              │     │
                    │ │ • Calculate cost        │     │
                    │ │ • Update session budget │     │
                    │ │ • Persist to checkpoint │     │
                    │ └─────────────────────────┘     │
                    │                                 │
                    │ Output: LLM response with       │
                    │         usage metadata          │
                    │         Costs updated           │
                    └────────────────┬────────────────┘
                                     │
                                     ▼
                        ┌────────────────────────┐
                        │  LLM Model Response    │
                        │  (With content_blocks) │
                        └────────────┬───────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │   [after_model] PHASE           │
                    │   ═════════════════════════════ │
                    │                                 │
                    │   1. Content Block Parsing      │
                    │      ├─ Parse thinking (if any) │
                    │      ├─ Extract tool calls      │
                    │      └─ Store reasoning trace   │
                    │                                 │
                    │   2. Insight Extraction         │
                    │      ├─ Find key points         │
                    │      ├─ Summarize reasoning     │
                    │      └─ Store for response      │
                    │                                 │
                    │   Output: Structured insights   │
                    │            Response ready for   │
                    │            tool execution       │
                    └────────────────┬────────────────┘
                                     │
                                     ▼
                        ┌────────────────────────┐
                        │  Tool Execution Phase  │
                        │  (If tools needed)     │
                        └────────────┬───────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │ [wrap_tool_call] PHASE          │
                    │ ════════════════════════════════│
                    │                                 │
                    │ For each tool:                  │
                    │  ├─ Track start time            │
                    │  ├─ Execute tool                │
                    │  ├─ Calculate tool cost         │
                    │  ├─ Update session budget       │
                    │  └─ Log execution               │
                    │                                 │
                    │ Output: Tool results            │
                    │         Tool costs tracked      │
                    └────────────────┬────────────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │   [after_agent] PHASE           │
                    │   ═════════════════════════════ │
                    │                                 │
                    │   1. Context Management         │
                    │      ├─ Check context size      │
                    │      ├─ Mark for archival       │
                    │      └─ Plan cleanup            │
                    │                                 │
                    │   2. Final Cost Accounting      │
                    │      ├─ Sum all costs           │
                    │      ├─ Update budget final     │
                    │      └─ Generate receipt        │
                    │                                 │
                    │   3. State Persistence          │
                    │      ├─ Persist checkpoint      │
                    │      ├─ Save session state      │
                    │      └─ Archive if needed       │
                    │                                 │
                    │   Output: Final result with     │
                    │            Costs & metadata     │
                    │            State persisted      │
                    └────────────────┬────────────────┘
                                     │
                                     ▼
                              ┌──────────────┐
                              │ User Output  │
                              │ + Metadata   │
                              │ + Costs      │
                              └──────────────┘
```

---

## 2. Middleware Execution Order Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                MIDDLEWARE EXECUTION SEQUENCE                     │
│               (Detailed Order & Data Flow)                       │
└─────────────────────────────────────────────────────────────────┘

STAGE 1: before_agent
──────────────────────────────────────────────────────────────────
  ┌──────────────────────────────────────────────────────────┐
  │ PIIValidationMiddleware (1st)                            │
  │ ────────────────────────────────────────────────────────│
  │ INPUT:  agent_input = {input: "raw user text"}          │
  │         agent_state = {user_id, session_id, budget}     │
  │                                                          │
  │ ACTION: • detect(agent_input["input"])                  │
  │         • if PII found:                                 │
  │           - redact(agent_input["input"])                │
  │           - set agent_state["pii_was_redacted"] = True  │
  │           - log audit event                             │
  │                                                          │
  │ OUTPUT: agent_input = {input: "cleaned text"}           │
  │         agent_state += {pii_audit, pii_was_redacted}    │
  └──────────────────────────────────────────────────────────┘
            ↓
  ┌──────────────────────────────────────────────────────────┐
  │ ComplexityRoutingMiddleware (2nd)                        │
  │ ────────────────────────────────────────────────────────│
  │ INPUT:  agent_input = {input: "cleaned text"}           │
  │         agent_state += {session_budget}                 │
  │                                                          │
  │ ACTION: • complexity = analyzer.analyze(input)          │
  │         • routing = router.route(input, budget)         │
  │         • agent_state["target_model"] = routing.model   │
  │         • agent_state["query_routing"] = routing        │
  │                                                          │
  │ OUTPUT: agent_state += {target_model, query_routing}    │
  └──────────────────────────────────────────────────────────┘
            ↓
        agent_state is now complete for before_agent phase


STAGE 2: before_model
──────────────────────────────────────────────────────────────────
  ┌──────────────────────────────────────────────────────────┐
  │ HumanInTheLoopMiddleware (3rd)                           │
  │ ────────────────────────────────────────────────────────│
  │ INPUT:  agent_state (with risk assessment info)         │
  │         model_input (messages to send)                  │
  │                                                          │
  │ ACTION: • risk_level = assessor.assess_risk()           │
  │         • if HIGH or CRITICAL:                          │
  │           - request_approval() [WAITS for human]        │
  │           - on denied: raise ValueError                 │
  │           - on approved: continue                       │
  │         • agent_state["approval_level"] = risk_level    │
  │                                                          │
  │ OUTPUT: model_input (unchanged if approved)             │
  │         agent_state += {approval_level, approved_by}    │
  └──────────────────────────────────────────────────────────┘
            ↓
  ┌──────────────────────────────────────────────────────────┐
  │ ContextManagementMiddleware (4th)                        │
  │ ────────────────────────────────────────────────────────│
  │ INPUT:  model_input = {messages: [...]}                 │
  │         agent_state += {target_max_tokens}              │
  │                                                          │
  │ ACTION: • should_summarize(messages) ?                  │
  │         • if yes:                                       │
  │           - summary = summarizer.summarize()            │
  │           - model_input["messages"] =                   │
  │             [{system: summary}, ...recent]              │
  │           - agent_state["context_summarized"] = True    │
  │                                                          │
  │ OUTPUT: model_input (possibly with summarized context)  │
  │         agent_state += {context_was_summarized}         │
  └──────────────────────────────────────────────────────────┘
            ↓
  ┌──────────────────────────────────────────────────────────┐
  │ BudgetValidationMiddleware (5th)                         │
  │ ────────────────────────────────────────────────────────│
  │ INPUT:  model_input (final messages)                    │
  │         agent_state += {query_routing}                  │
  │                                                          │
  │ ACTION: • if not session_budget.can_proceed:            │
  │           - raise ValueError(budget exceeded)           │
  │         • estimate = count_tokens(model_input)          │
  │         • if estimate > remaining_tokens:               │
  │           - raise ValueError(insufficient tokens)       │
  │         • agent_state["token_estimate"] = estimate      │
  │                                                          │
  │ OUTPUT: model_input (validated)                         │
  │         agent_state += {token_estimate}                 │
  └──────────────────────────────────────────────────────────┘
            ↓
        Ready for model call


STAGE 3: wrap_model_call
──────────────────────────────────────────────────────────────────
  ┌──────────────────────────────────────────────────────────┐
  │ CostTrackingMiddleware.wrap_model_call (6th)             │
  │ ────────────────────────────────────────────────────────│
  │ INPUT:  call_fn() = async function to LLM               │
  │         agent_state += {token_estimate}                 │
  │                                                          │
  │ ACTION: • response = await call_fn()                    │
  │         • usage = extract_usage(response)               │
  │         • cost = calculate_cost(usage, model)           │
  │         • session_budget.update_usage(...)              │
  │         • await state_manager.persist(budget)           │
  │         • agent_state["last_call_cost"] = {...}         │
  │                                                          │
  │ OUTPUT: response (from model)                           │
  │         agent_state += {last_call_cost}                 │
  │         budget persisted to checkpoint                  │
  └──────────────────────────────────────────────────────────┘
            ↓
        LLM call executed and costs tracked


STAGE 4: after_model
──────────────────────────────────────────────────────────────────
  ┌──────────────────────────────────────────────────────────┐
  │ ReasoningTraceMiddleware (7th)                           │
  │ ────────────────────────────────────────────────────────│
  │ INPUT:  model_response (from LLM)                       │
  │         agent_state += {target_model}                   │
  │                                                          │
  │ ACTION: • parser = select_parser(target_model)          │
  │         • trace = parser.parse(response)                │
  │         • agent_state["reasoning_trace"] = trace        │
  │         • if trace.thinking:                            │
  │           - insights = extract_insights(thinking)       │
  │           - agent_state["reasoning_insights"] = insights│
  │                                                          │
  │ OUTPUT: model_response (unchanged)                      │
  │         agent_state += {reasoning_trace, insights}      │
  └──────────────────────────────────────────────────────────┘
            ↓
        Reasoning parsed for user presentation


STAGE 5: wrap_tool_call (if tools invoked)
──────────────────────────────────────────────────────────────────
  ┌──────────────────────────────────────────────────────────┐
  │ ToolCallCostTracker (8th, repeated per tool)             │
  │ ────────────────────────────────────────────────────────│
  │ INPUT:  call_fn() = tool to execute                     │
  │         tool_name, tool_input                           │
  │         agent_state                                     │
  │                                                          │
  │ ACTION: • start_time = now()                            │
  │         • result = await call_fn()                      │
  │         • duration = now() - start_time                 │
  │         • tool_cost = TOOL_COSTS[name] * duration       │
  │         • session_budget.used_cost += tool_cost         │
  │         • await state_manager.persist(budget)           │
  │         • agent_state["tool_executions"].append({...})  │
  │                                                          │
  │ OUTPUT: result (from tool)                              │
  │         agent_state += {tool_executions}                │
  │         budget updated for tool execution               │
  └──────────────────────────────────────────────────────────┘
            ↓
        All tools executed with cost tracking


STAGE 6: after_agent
──────────────────────────────────────────────────────────────────
  ┌──────────────────────────────────────────────────────────┐
  │ ContextManagementMiddleware.after_agent (9th)            │
  │ ────────────────────────────────────────────────────────│
  │ INPUT:  agent_output (final result)                     │
  │         agent_state (complete state)                    │
  │                                                          │
  │ ACTION: • if len(messages) > 50:                        │
  │           - agent_state["checkpoint_pruning_needed"]    │
  │         • final_costs = sum all costs from session       │
  │         • agent_state["final_cost_summary"] = {...}     │
  │                                                          │
  │ OUTPUT: agent_output (unchanged)                        │
  │         agent_state += {final_cost_summary}             │
  └──────────────────────────────────────────────────────────┘
            ↓
  ┌──────────────────────────────────────────────────────────┐
  │ Final State Persistence                                  │
  │ ────────────────────────────────────────────────────────│
  │ ACTION: • Create final checkpoint                       │
  │         • Save session state to database                │
  │         • Mark turn as complete                         │
  │         • Schedule cleanup if needed                    │
  │                                                          │
  │ OUTPUT: Checkpoint saved                                │
  │         Session state persisted                         │
  └──────────────────────────────────────────────────────────┘
            ↓
        COMPLETE - Return to user with summary
```

---

## 3. State Flow Through Middleware

```
┌─────────────────────────────────────────────────────────────────┐
│            AGENT STATE EVOLUTION THROUGH PIPELINE                │
└─────────────────────────────────────────────────────────────────┘

START:
agent_state = {
  user_id: "user_123",
  session_id: "session_abc",
  original_input: "Analyze microservices",
  session_budget: SessionBudget(...),
  user_preferences: {...}
}

↓ AFTER PIIValidationMiddleware:
agent_state += {
  pii_was_redacted: False,  (or True if PII found)
  pii_audit: {...}          (only if PII found)
}

↓ AFTER ComplexityRoutingMiddleware:
agent_state += {
  query_routing: {
    complexity: "COMPLEX",
    model: "claude-3-opus-20240229",
    max_tokens: 8000,
    enable_thinking: False
  },
  target_model: "claude-3-opus-20240229",
  target_max_tokens: 8000
}

↓ AFTER HumanInTheLoopMiddleware:
agent_state += {
  approval_level: "MEDIUM",
  approval_required: True,
  approval_granted_by: "user_123"
}

↓ AFTER ContextManagementMiddleware (before_model):
agent_state += {
  context_was_summarized: False,  (or True)
  summary_created_at: datetime(...)
}

↓ AFTER BudgetValidationMiddleware:
agent_state += {
  token_estimate: {
    input_tokens: 245,
    estimated_output_tokens: 8000,
    model: "claude-3-opus-20240229"
  }
}

↓ AFTER wrap_model_call (Cost Tracking):
agent_state += {
  last_call_cost: {
    model: "claude-3-opus-20240229",
    input_tokens: 245,
    output_tokens: 1523,
    cost: 0.0247
  }
}
session_budget.update_usage(...)  # Budget updated

↓ AFTER ReasoningTraceMiddleware:
agent_state += {
  reasoning_trace: {
    provider: "anthropic",
    thinking: "Let me think about...",  (if thinking enabled)
    tool_calls_count: 2,
    response_preview: "The architecture consists of..."
  },
  reasoning_insights: [
    "Key insight 1",
    "Key insight 2",
    ...
  ]
}

↓ AFTER wrap_tool_call (if tools invoked):
agent_state += {
  tool_executions: [
    {
      tool_name: "search",
      execution_time: 1.23,
      cost: 0.0005,
      timestamp: datetime(...),
      input: "microservices patterns"
    },
    ...
  ]
}
session_budget.used_cost += 0.0005

↓ AFTER ContextManagementMiddleware (after_agent):
agent_state += {
  checkpoint_pruning_needed: False,  (or True)
  final_cost_summary: {
    model_cost: 0.0247,
    tool_cost: 0.0005,
    total_cost: 0.0252,
    tokens_used: 1768
  }
}

FINAL STATE STRUCTURE:
agent_state = {
  # User & Session
  user_id: "user_123",
  session_id: "session_abc",
  original_input: "...",
  session_budget: SessionBudget(...),

  # PII
  pii_was_redacted: False,

  # Routing
  query_routing: {...},
  target_model: "...",

  # Approval
  approval_level: "MEDIUM",
  approval_required: True,

  # Context
  context_was_summarized: False,

  # Tokens & Budget
  token_estimate: {...},
  last_call_cost: {...},

  # Reasoning
  reasoning_trace: {...},
  reasoning_insights: [...],

  # Tools
  tool_executions: [...],

  # Final Summary
  final_cost_summary: {...},
  checkpoint_pruning_needed: False
}

↓ RETURN TO USER:
response = {
  output: "The architecture consists of...",
  cost_summary: {
    tokens_used: 1768,
    cost_used: 0.0252,
    remaining_budget: 9.9748
  },
  metadata: {
    model_used: "claude-3-opus-20240229",
    approval_required: True,
    pii_redacted: False,
    context_summarized: False
  },
  reasoning_insights: [...]
}
```

---

## 4. Decision Tree: When to Use Which Middleware

```
┌─────────────────────────────────────────────────────────────────┐
│     MIDDLEWARE DECISION TREE: WHICH TO ENABLE?                   │
└─────────────────────────────────────────────────────────────────┘

START: Evaluating middleware requirements
    │
    ├─ Do you need PII protection?
    │  ├─ YES → Use PIIValidationMiddleware
    │  │        ├─ strict_mode=True:  Block on PII (recommended for healthcare/finance)
    │  │        └─ strict_mode=False: Redact silently (general use)
    │  │
    │  └─ NO → Skip PIIValidationMiddleware
    │
    ├─ Do you need dynamic model selection?
    │  ├─ YES → Use ComplexityRoutingMiddleware
    │  │        ├─ For cost optimization (route simple → cheap models)
    │  │        ├─ For quality optimization (route complex → capable models)
    │  │        └─ Recommended for most production systems
    │  │
    │  └─ NO → Skip (use fixed model)
    │
    ├─ Do you have budget constraints?
    │  ├─ YES → Use BudgetValidationMiddleware + CostTrackingMiddleware
    │  │        ├─ For SaaS with per-user budgets
    │  │        ├─ For enterprise with cost controls
    │  │        └─ ESSENTIAL for most systems
    │  │
    │  └─ NO → Skip (but still recommended for monitoring)
    │
    ├─ Do you need human approval for operations?
    │  ├─ YES → Use HumanInTheLoopMiddleware
    │  │        ├─ For high-risk operations (data deletion, permissions)
    │  │        ├─ For regulatory compliance (HIPAA, SOX, GDPR)
    │  │        ├─ For financial transactions
    │  │        └─ For security-sensitive systems
    │  │
    │  └─ NO → Skip
    │
    ├─ Do you need to extract reasoning from models?
    │  ├─ YES → Use ReasoningTraceMiddleware
    │  │        ├─ For transparency/explainability
    │  │        ├─ For debugging model decisions
    │  │        ├─ For audit trails
    │  │        └─ With Claude/GPT-4 models (extended thinking)
    │  │
    │  └─ NO → Skip
    │
    ├─ Do you have long conversations?
    │  ├─ YES → Use ContextManagementMiddleware
    │  │        ├─ For multi-turn conversations (>10 turns)
    │  │        ├─ For large context windows (>10k tokens)
    │  │        ├─ Prevents token limit exceeded errors
    │  │        └─ Recommended for chat applications
    │  │
    │  └─ NO → Skip (or keep for safety)
    │
    ├─ Do you have expensive external tools?
    │  ├─ YES → Use ToolCallCostTracker (wrap_tool_call)
    │  │        ├─ For database queries (cost to execute)
    │  │        ├─ For API calls (rate limiting, cost)
    │  │        ├─ For data processing pipelines
    │  │        └─ For financial/reporting operations
    │  │
    │  └─ NO → Skip (or keep for monitoring)
    │
    └─ RESULT: Minimal Stack vs. Full Stack


MINIMAL STACK (Basic Usage):
──────────────────────────
✓ ComplexityRoutingMiddleware    (model selection)
✓ BudgetValidationMiddleware     (basic protection)
✓ CostTrackingMiddleware         (cost awareness)
─────────────────────────────────
Total middleware: 3
Best for: Simple applications, prototypes

STANDARD STACK (Production):
────────────────────────────
✓ PIIValidationMiddleware
✓ ComplexityRoutingMiddleware
✓ BudgetValidationMiddleware
✓ CostTrackingMiddleware
✓ ReasoningTraceMiddleware
✓ ContextManagementMiddleware
─────────────────────────────
Total middleware: 6
Best for: Most production applications

FULL STACK (Enterprise):
────────────────────────
✓ PIIValidationMiddleware         (strict_mode=True)
✓ ComplexityRoutingMiddleware
✓ HumanInTheLoopMiddleware        (approval for high-risk)
✓ BudgetValidationMiddleware
✓ CostTrackingMiddleware
✓ ReasoningTraceMiddleware
✓ ContextManagementMiddleware
✓ ToolCallCostTracker
─────────────────────────────
Total middleware: 8
Best for: Enterprise, healthcare, finance, high-risk operations


RUNTIME CONFIGURATION BY USER TIER:
───────────────────────────────────
Free Tier:
  ├─ PIIValidationMiddleware (redact)
  ├─ ComplexityRoutingMiddleware (cost optimization)
  ├─ BudgetValidationMiddleware (strict: 10k tokens/month)
  └─ Budget: $0.50/month

Pro Tier:
  ├─ Full standard stack
  ├─ BudgetValidationMiddleware (100k tokens/month)
  └─ Budget: $10/month

Enterprise Tier:
  ├─ Full enterprise stack
  ├─ HumanInTheLoopMiddleware enabled
  ├─ Custom budget per department
  ├─ ToolCallCostTracker with detailed audit
  └─ Budget: Custom (typically $1000+/month)
```

---

## 5. Error Handling Decision Tree

```
┌─────────────────────────────────────────────────────────────────┐
│          MIDDLEWARE ERROR HANDLING DECISION FLOW                  │
└─────────────────────────────────────────────────────────────────┘

ERROR DETECTED
    │
    ├─ Which middleware raised the error?
    │
    ├─ PIIValidationMiddleware ERROR
    │  └─ Severity: FATAL (Security issue)
    │     ├─ Action: Block request
    │     ├─ Log: Security audit log
    │     ├─ Response: "Input contains sensitive information"
    │     └─ No recovery: User must resubmit without PII
    │
    ├─ ComplexityRoutingMiddleware ERROR
    │  └─ Severity: RECOVERABLE
    │     ├─ Action: Use default model (claude-3-5-sonnet)
    │     ├─ Log: Warning + details
    │     ├─ Response: Continue with safe model
    │     └─ Recovery: Automatic fallback
    │
    ├─ BudgetValidationMiddleware ERROR
    │  └─ Severity: DEGRADABLE
    │     ├─ Is token budget insufficient?
    │     │  ├─ YES → Try downgrade to cheaper model
    │     │  │        ├─ If SIMPLE complexity: Use Haiku
    │     │  │        ├─ If MODERATE: Use Sonnet
    │     │  │        └─ If COMPLEX: Insufficient budget, error
    │     │  │
    │     │  ├─ Is cost budget insufficient?
    │     │  │  ├─ YES → Downgrade model
    │     │  │  └─ If can't downgrade: Block with budget error
    │     │  │
    │     │  └─ If still insufficient → Error to user
    │     │
    │     ├─ Log: Budget constraint hit
    │     ├─ Response: "Budget exceeded" + summary
    │     └─ Recovery: Downgrade or fail
    │
    ├─ CostTrackingMiddleware ERROR (wrap_model_call)
    │  └─ Severity: RECOVERABLE (transient)
    │     ├─ If LLM timeout?
    │     │  ├─ Retry: exponential backoff (1s, 2s, 4s)
    │     │  ├─ Max retries: 3
    │     │  └─ On final failure: Return partial result
    │     │
    │     ├─ If usage parsing fails?
    │     │  ├─ Action: Estimate tokens
    │     │  ├─ Log: Warning
    │     │  └─ Continue with estimate
    │     │
    │     ├─ If cost calculation fails?
    │     │  ├─ Action: Use conservative estimate
    │     │  ├─ Log: Warning
    │     │  └─ Allow to proceed
    │     │
    │     └─ Recovery: Retry or estimate
    │
    ├─ HumanInTheLoopMiddleware ERROR
    │  └─ Severity: FATAL (Security/approval critical)
    │     ├─ If approval timeout?
    │     │  ├─ Action: Deny operation (secure default)
    │     │  ├─ Log: Approval timeout
    │     │  └─ Response: "Approval timeout, operation cancelled"
    │     │
    │     ├─ If user denies?
    │     │  ├─ Action: Block operation
    │     │  ├─ Log: Denied by user
    │     │  └─ Response: "Operation cancelled by user"
    │     │
    │     └─ No recovery: Must resubmit if approved
    │
    ├─ ReasoningTraceMiddleware ERROR
    │  └─ Severity: DEGRADABLE
    │     ├─ If parsing fails?
    │     │  ├─ Action: Skip reasoning extraction
    │     │  ├─ Log: Warning
    │     │  ├─ Response: Return without insights
    │     │  └─ Recovery: Continue with fallback
    │     │
    │     └─ Non-blocking: Always continue
    │
    ├─ ContextManagementMiddleware ERROR
    │  └─ Severity: DEGRADABLE
    │     ├─ If summarization fails?
    │     │  ├─ Action: Truncate context (keep last 5 messages)
    │     │  ├─ Log: Warning
    │     │  ├─ Response: Continue with truncated context
    │     │  └─ Note: Some context lost
    │     │
    │     └─ Recovery: Fallback truncation
    │
    └─ ToolCallCostTracker ERROR (wrap_tool_call)
       └─ Severity: DEGRADABLE
          ├─ If tool execution fails?
          │  ├─ Action: Skip tool, continue with LLM response
          │  ├─ Log: Tool failure
          │  ├─ Response: Continue without tool output
          │  └─ Recovery: Proceed without tool
          │
          ├─ If cost tracking fails?
          │  ├─ Action: Estimate tool cost
          │  ├─ Log: Warning
          │  └─ Continue with estimate
          │
          └─ Non-fatal: Always continue


ROLLBACK STRATEGY:
──────────────────

On FATAL errors (PII, Approval):
  ├─ Save current state to checkpoint
  ├─ Return error to user
  ├─ No recovery: Requires new request
  └─ Audit trail: Log security event

On RECOVERABLE errors (Model call, budget):
  ├─ Retry with backoff (exponential: 1s, 2s, 4s)
  ├─ If all retries fail:
  │  ├─ Restore from last checkpoint
  │  ├─ Return partial result if available
  │  └─ Log for investigation
  └─ Audit trail: Track retries

On DEGRADABLE errors (Tools, context, reasoning):
  ├─ Apply fallback strategy
  ├─ Continue execution
  ├─ Notify user of degradation
  ├─ Log warning
  └─ Audit trail: Record fallback used


EXAMPLE ERROR SCENARIOS:
────────────────────────

Scenario 1: Budget Exceeded with COMPLEX query
┌─────────────────────────────────────────────────┐
│ 1. User: "Analyze 100 GB dataset"               │
│ 2. ComplexityRoutingMiddleware → COMPLEX        │
│ 3. Model selected: claude-3-opus ($0.10 est)    │
│ 4. BudgetValidationMiddleware checks:           │
│    User budget: $0.50, Remaining: $0.02         │
│ 5. ERROR: Insufficient budget                   │
│ 6. Recovery:                                    │
│    - Downgrade to claude-3-haiku ($0.01)        │
│    - Inform user: "Using cheaper model"         │
│    - Continue execution                         │
│ 7. Result: SUCCESS with degraded quality        │
└─────────────────────────────────────────────────┘

Scenario 2: High-Risk Operation Without Approval
┌─────────────────────────────────────────────────┐
│ 1. User: "Delete all user records from table"   │
│ 2. HumanInTheLoopMiddleware → HIGH risk          │
│ 3. Send approval request to admin                │
│ 4. Wait 300 seconds for response                 │
│ 5. Admin denies approval                         │
│ 6. ERROR: Operation not approved                 │
│ 7. Recovery: NONE - operation blocked            │
│ 8. Response: "Operation cancelled by admin"      │
│ 9. User must resubmit with safe operation        │
└─────────────────────────────────────────────────┘

Scenario 3: LLM Timeout During Model Call
┌─────────────────────────────────────────────────┐
│ 1. Model call initiated                          │
│ 2. 30 seconds pass, no response                  │
│ 3. ERROR: Timeout                                │
│ 4. Recovery - Retry 1:                           │
│    - Wait 1 second, retry                        │
│    - Timeout again                               │
│ 5. Recovery - Retry 2:                           │
│    - Wait 2 seconds, retry                       │
│    - Timeout again                               │
│ 6. Recovery - Retry 3:                           │
│    - Wait 4 seconds, retry                       │
│    - Still timing out                            │
│ 7. ERROR: Max retries exceeded                   │
│ 8. Restore from checkpoint, return partial       │
│ 9. Response: "Timeout, partial result"           │
└─────────────────────────────────────────────────┘
```

---

## 6. Checkpoint Strategy Decision Matrix

```
┌──────────────────────────────────────────────────────────────────┐
│          CHECKPOINT STRATEGY: WHICH FREQUENCY?                    │
└──────────────────────────────────────────────────────────────────┘

Decision Factors:
  1. Conversation Length: Short (1-3 turns) vs. Long (10+ turns)
  2. Cost per Turn: Low ($0.01) vs. High ($1.00+)
  3. Recovery Criticality: Low vs. High (financial, medical)
  4. Storage Cost: Cheap ($0.01/GB/month) vs. Expensive
  5. Session Type: Stateless API vs. Stateful chat

┌─────────────────────────┬──────────────┬──────────────┬──────────────┐
│ Scenario                │ Checkpoint   │ Storage      │ Use Case     │
│                         │ Frequency    │ Cost         │              │
├─────────────────────────┼──────────────┼──────────────┼──────────────┤
│ Simple Q&A              │ After agent  │ Low          │ Most APIs    │
│ (1-2 turns, <$0.10)     │ turn only    │              │              │
│                         │              │              │              │
│ Moderate chat           │ After model  │ Medium       │ Chat apps    │
│ (5-20 turns, <$1)       │ + after tool │              │ Streaming    │
│                         │              │              │              │
│ Long conversation       │ Every step   │ High         │ Extended     │
│ (20+ turns, >$1)        │ (model +     │              │ conversations│
│                         │ tool calls)  │              │ Time-travel  │
│                         │              │              │              │
│ Financial transaction   │ Every step   │ High         │ Payments     │
│ (critical recovery)     │ + redundant  │              │ Healthcare   │
│                         │ backup       │              │ Legal        │
│                         │              │              │              │
│ Development/debugging   │ Every step   │ Very high    │ Testing      │
│ (need full replay)      │ + verbose    │              │ Debugging    │
│                         │ logging      │              │              │
└─────────────────────────┴──────────────┴──────────────┴──────────────┘


FREQUENCY LEVELS & TRADE-OFFS:
───────────────────────────────

Level 1: After Agent Turn Only
├─ Checkpoints: 1 per conversation turn
├─ Storage: ~100 KB per checkpoint
├─ Latency: 5-10ms overhead
├─ Recovery: Can recover complete turn
├─ Best for: Simple stateless queries
└─ Cost: $0.01/1000 checkpoints

Level 2: After Model + Tool Calls
├─ Checkpoints: 2-4 per turn
├─ Storage: ~50 KB per checkpoint
├─ Latency: 5-15ms overhead
├─ Recovery: Can recover partial execution
├─ Best for: Standard chat applications
└─ Cost: $0.02-0.04/turn

Level 3: Every Step (Maximum)
├─ Checkpoints: 5-10 per turn
├─ Storage: ~30 KB per checkpoint
├─ Latency: 10-20ms overhead
├─ Recovery: Can resume from any step
├─ Best for: Critical operations, debugging
├─ Time-travel: Full replay capability
└─ Cost: $0.05-0.10/turn


CHECKPOINT CLEANUP STRATEGY:
──────────────────────────────

After Conversation Complete:
  ├─ Keep last 5 checkpoints (recent history)
  ├─ Archive older than 30 days to cold storage
  ├─ Delete after 90 days (compliance)
  └─ Or keep indefinitely for audit

Automatic Pruning:
  ├─ Monitor checkpoint storage size
  ├─ If > 100MB per session: Purge old checkpoints
  ├─ Keep only necessary recovery points
  └─ Scheduled cleanup (daily, low traffic hours)

Manual Cleanup (Admin):
  ├─ Reset session: Delete all checkpoints
  ├─ Archive session: Move to cold storage
  ├─ Restore from backup: Recover deleted session
  └─ Audit trail: Log all cleanup operations


RECOMMENDED CONFIGURATIONS:
────────────────────────────

Development:
  checkpoint_frequency = EVERY_STEP
  keep_count = unlimited
  archive_days = never
  → Full debuggability

Staging:
  checkpoint_frequency = AFTER_TOOL_CALL
  keep_count = 50 per session
  archive_days = 30
  → Balance debuggability & cost

Production SaaS:
  checkpoint_frequency = AFTER_AGENT_TURN
  keep_count = 10 per session
  archive_days = 7
  → Minimize storage, fast recovery

Production Enterprise:
  checkpoint_frequency = AFTER_TOOL_CALL
  keep_count = 100 per session
  archive_days = 90
  backup_frequency = daily
  → Compliance & full recovery capability
```

---

## Summary: When to Deploy Each Middleware

```
For MVP/Prototype:
  ✓ ComplexityRoutingMiddleware
  ✓ BudgetValidationMiddleware
  ✓ CostTrackingMiddleware
  (3 middleware, ~2 hours to implement)

For Production SaaS:
  ✓ PIIValidationMiddleware (redact mode)
  ✓ ComplexityRoutingMiddleware
  ✓ BudgetValidationMiddleware
  ✓ CostTrackingMiddleware
  ✓ ReasoningTraceMiddleware
  ✓ ContextManagementMiddleware
  (6 middleware, ~1 day to implement)

For Enterprise/Healthcare:
  ✓ PIIValidationMiddleware (strict mode)
  ✓ ComplexityRoutingMiddleware
  ✓ HumanInTheLoopMiddleware
  ✓ BudgetValidationMiddleware
  ✓ CostTrackingMiddleware
  ✓ ReasoningTraceMiddleware
  ✓ ContextManagementMiddleware
  ✓ ToolCallCostTracker
  (8 middleware, ~2-3 days to implement)
```

