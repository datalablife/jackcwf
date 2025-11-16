# Production-Grade Financial RAG System Architecture
## LangChain 1.0 Backend Design

**Last Updated:** 2025-11-16
**Status:** Design Complete
**Implementation Pattern:** LangChain 1.0 create_agent + LangGraph + Middleware

---

## 1. HIGH-LEVEL ARCHITECTURE OVERVIEW

### System Component Stack

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                    │
│  (Web UI → WebSocket → Streaming Responses with Token Counts)          │
└─────────────────────┬───────────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────────────┐
│                   API GATEWAY LAYER                                     │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Authentication │ Rate Limiting │ Request Validation              │  │
│  │ Cost Tracking  │ Session Management                              │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────────────┐
│              AGENT ORCHESTRATION LAYER (LangGraph)                      │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                    Financial RAG Agent                             │ │
│  │  ┌────────────────────────────────────────────────────────────┐  │ │
│  │  │ MIDDLEWARE EXECUTION HOOKS (Six-Point Stack)              │  │ │
│  │  │                                                            │  │ │
│  │  │  1. before_agent: Load user session, check token budget  │  │ │
│  │  │     └─ Load conversation checkpoint                      │  │ │
│  │  │     └─ Initialize cost tracker                          │  │ │
│  │  │     └─ Extract user context (role, data access)        │  │ │
│  │  │                                                          │  │ │
│  │  │  2. before_model: Prepare prompt, mask PII             │  │ │
│  │  │     └─ Apply PII detection middleware                  │  │ │
│  │  │     └─ Build context from retrieved documents          │  │ │
│  │  │     └─ Truncate context if token budget tight         │  │ │
│  │  │     └─ Inject conversation memory summary             │  │ │
│  │  │                                                          │  │ │
│  │  │  3. wrap_model_call: Intercept LLM request/response    │  │ │
│  │  │     └─ Count tokens (input/output)                     │  │ │
│  │  │     └─ Track provider costs (Claude vs GPT-4)         │  │ │
│  │  │     └─ Handle streaming with buffer management         │  │ │
│  │  │     └─ Parse content blocks for reasoning traces      │  │ │
│  │  │                                                          │  │ │
│  │  │  4. wrap_tool_call: Execute retrieval/analysis tools   │  │ │
│  │  │     └─ Vector search with timeout                      │  │ │
│  │  │     └─ Rate limit tool execution                       │  │ │
│  │  │     └─ Track tool metrics (latency, errors)           │  │ │
│  │  │     └─ Error recovery for failed searches             │  │ │
│  │  │                                                          │  │ │
│  │  │  5. after_model: Process LLM output                    │  │ │
│  │  │     └─ Validate structured outputs                    │  │ │
│  │  │     └─ Extract tool calls and reasoning               │  │ │
│  │  │     └─ PII masking on output                          │  │ │
│  │  │                                                          │  │ │
│  │  │  6. after_agent: Save state and finalize              │  │ │
│  │  │     └─ Save conversation to LangGraph checkpoint      │  │ │
│  │  │     └─ Write cost records to database                 │  │ │
│  │  │     └─ Update user token budget                       │  │ │
│  │  │     └─ Emit analytics events                          │  │ │
│  │  │                                                            │  │ │
│  │  └────────────────────────────────────────────────────────────┘  │ │
│  │                                                                    │ │
│  │  ┌─ Agent State Machine ──────────────────────────────────────┐  │ │
│  │  │ Pending → Retrieving → Analyzing → Responding → Complete  │  │ │
│  │  └────────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────┬───────────────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┬──────────────┐
        │             │             │              │
┌───────▼──┐  ┌──────▼──┐  ┌──────▼──┐  ┌──────▼────┐
│ RETRIEVAL │  │ ANALYSIS │  │  STATE  │  │OBSERVABILITY
│ LAYER     │  │ LAYER    │  │ LAYER   │  │ LAYER
└───────────┘  └──────────┘  └─────────┘  └────────────┘
```

---

## 2. DETAILED MIDDLEWARE STACK

### Middleware Execution Flow

```
USER INPUT
    │
    ▼
┌─────────────────────────────────────────┐
│  before_agent Hook                      │
│  • Load session from LangGraph          │
│  • Initialize cost tracking             │
│  • Extract user context                 │
│  • Check rate limits                    │
│  • Validate query (length, sensitivity) │
└──────────┬──────────────────────────────┘
           │
    ▼──────────────────────────▼
┌─────────────────────────────────────────┐
│  Tool Invocation: semantic_search()     │
│  • Vector similarity (Pinecone/Weaviate)│
│  • Metadata filtering by user role      │
│  • Top-K retrieval with scores          │
│  • PII detection on retrieved docs      │
└──────────┬──────────────────────────────┘
           │
    ▼──────────────────────────▼
┌─────────────────────────────────────────┐
│  before_model Hook                      │
│  • Build RAG prompt from docs           │
│  • Mask PII in context                  │
│  • Summarize long conversations         │
│  • Calculate token budget               │
│  • Inject few-shot examples             │
│  • Set temperature based on task        │
└──────────┬──────────────────────────────┘
           │
    ▼──────────────────────────▼
┌─────────────────────────────────────────┐
│  wrap_model_call Hook                   │
│  • Intercept LLM request                │
│  • Start token counting                 │
│  • Handle streaming with buffer         │
│  • Parse content blocks on response     │
│  • Collect reasoning traces             │
│  • Track provider-specific metrics      │
└──────────┬──────────────────────────────┘
           │
    ▼──────────────────────────▼
┌─────────────────────────────────────────┐
│  LLM Processing                         │
│  (Claude 3.5 Sonnet / GPT-4o)           │
│  • Streaming token output               │
│  • Native tool use if available         │
│  • Structured output generation         │
└──────────┬──────────────────────────────┘
           │
    ▼──────────────────────────▼
┌─────────────────────────────────────────┐
│  after_model Hook                       │
│  • Validate output structure            │
│  • Extract tool calls from response     │
│  • Count output tokens                  │
│  • Calculate costs                      │
│  • Mask PII in output                   │
│  • Store tokens for budget tracking     │
└──────────┬──────────────────────────────┘
           │
    ▼──────────────────────────▼
┌─────────────────────────────────────────┐
│  after_agent Hook                       │
│  • Save to LangGraph checkpoint         │
│  • Write cost records                   │
│  • Update user token budget             │
│  • Emit to LangSmith                    │
│  • Send analytics events                │
└──────────┬──────────────────────────────┘
           │
    ▼──────────────────────────▼
        STREAM TO CLIENT
        with token counts & costs
```

### Middleware Priority & Execution Order

```
PRIORITY LEVELS (Execution Order):

1. CRITICAL (Pre-LLM):
   ├─ AuthenticationMiddleware (before_agent)
   ├─ RateLimitMiddleware (before_agent)
   ├─ TokenBudgetMiddleware (before_agent)
   └─ QueryValidationMiddleware (before_agent)

2. CONTEXT (Pre-Prompt):
   ├─ PIIDetectionMiddleware (before_model)
   ├─ ConversationSummarizationMiddleware (before_model)
   ├─ ContextWindowMiddleware (before_model)
   └─ RetrieverMiddleware (tool execution)

3. OBSERVATION (Wrapping):
   ├─ TokenCountingMiddleware (wrap_model_call)
   ├─ CostTrackingMiddleware (wrap_model_call)
   ├─ ContentBlockParserMiddleware (wrap_model_call)
   └─ StreamingBufferMiddleware (wrap_model_call)

4. FINALIZATION (Post-LLM):
   ├─ OutputValidationMiddleware (after_model)
   ├─ PIIMaskingMiddleware (after_model)
   ├─ PersistenceMiddleware (after_agent)
   └─ AnalyticsMiddleware (after_agent)
```

---

## 3. TOOL DEFINITIONS (Semantic Layer)

### Tool 1: Semantic Document Search

**Purpose:** Retrieve financially relevant documents using vector similarity
**Vector DB:** Pinecone or Weaviate with 1536-dim embeddings
**Metadata Filtering:** By company, ticker, document type, date range

```
Tool: semantic_search
├─ Input Schema (Pydantic):
│  ├─ query: str (financial research question)
│  ├─ top_k: int = 5 (documents to retrieve)
│  ├─ company_filter: Optional[str] (ticker or name)
│  ├─ date_range: Optional[tuple[str, str]] (ISO dates)
│  ├─ document_types: List[str] (10-K, earnings call, analyst report)
│  ├─ min_score: float = 0.7 (relevance threshold)
│  └─ user_id: str (for access control)
│
├─ Execution Flow:
│  1. Validate query (PII check, length limits)
│  2. Generate embedding for query
│  3. Execute vector search with metadata filtering
│  4. Apply user role-based access control
│  5. Mask PII in retrieved content
│  6. Return docs with relevance scores
│
├─ Output Schema:
│  ├─ documents: List[dict]
│  │  ├─ content: str (document text)
│  │  ├─ metadata: dict
│  │  │  ├─ source: str
│  │  │  ├─ company: str
│  │  │  ├─ ticker: str
│  │  │  ├─ doc_type: str
│  │  │  ├─ date: str
│  │  │  └─ relevance_score: float
│  │  └─ pii_masked: bool
│  ├─ search_time_ms: int
│  └─ error: Optional[str]
│
├─ Error Handling:
│  • Vector DB timeout → Return cached fallback results
│  • Query parse error → Return graceful error message
│  • No results found → Suggest broader search
│  • Access denied → Return empty with authorization error
│
└─ Middleware Hooks:
   • wrap_tool_call: Timeout enforcement (5s max)
   • wrap_tool_call: Rate limiting per user
   • wrap_tool_call: Latency tracking for optimization
   • after_tool: PII mask on output
```

### Tool 2: Financial Data Analysis

**Purpose:** Perform numerical analysis on retrieved financial data
**Capabilities:** Time-series analysis, ratio calculations, benchmarking

```
Tool: financial_analysis
├─ Input Schema (Pydantic):
│  ├─ documents: List[str] (financial text to analyze)
│  ├─ analysis_type: str (enum: ratio, trend, benchmark, anomaly)
│  ├─ metrics: List[str] (P/E ratio, ROE, debt-to-equity, etc.)
│  ├─ comparison_company: Optional[str] (for benchmarking)
│  ├─ period: str (quarterly or annual)
│  └─ user_id: str
│
├─ Execution Flow:
│  1. Parse financial statements from text
│  2. Extract numerical values with confidence scoring
│  3. Validate calculations (sanity checks)
│  4. Generate analysis based on type
│  5. Format output for presentation
│
├─ Output Schema:
│  ├─ analysis_type: str
│  ├─ metrics_calculated: dict
│  │  ├─ metric_name: float (value)
│  │  └─ confidence: float (0-1)
│  ├─ trends: List[dict]
│  │  ├─ metric: str
│  │  ├─ direction: str (up/down/stable)
│  │  └─ magnitude: float
│  ├─ benchmarks: Optional[dict]
│  │  ├─ company_metric: float
│  │  ├─ industry_median: float
│  │  └─ percentile: float
│  ├─ insights: List[str]
│  └─ confidence_score: float
│
└─ Error Handling:
   • Parse error → Return partial analysis with error flag
   • Missing data → Use available metrics, mark as incomplete
   • Outlier detected → Flag for manual review
```

### Tool 3: Historical Context Retrieval

**Purpose:** Retrieve conversation history summaries for context
**Storage:** LangGraph checkpoints with automatic summarization

```
Tool: get_conversation_history
├─ Input Schema:
│  ├─ conversation_id: str
│  ├─ num_turns: int = 5 (recent turns)
│  ├─ summarize: bool = True (use summary if available)
│  └─ include_metadata: bool = True
│
├─ Execution Flow:
│  1. Load checkpoint from LangGraph
│  2. Extract conversation state
│  3. Optionally summarize if > 10K tokens
│  4. Filter by access control
│
├─ Output Schema:
│  ├─ history: List[dict]
│  │  ├─ turn: int
│  │  ├─ query: str
│  │  ├─ response_summary: str
│  │  ├─ documents_used: List[str]
│  │  ├─ timestamp: str
│  │  └─ costs: dict (tokens, dollars)
│  ├─ total_tokens_used: int
│  ├─ conversation_summary: Optional[str]
│  └─ checkpoint_id: str
│
└─ Caching:
   • Summary cached for 1 hour
   • Recent turns cached for 10 minutes
   • Invalidated on new query
```

---

## 4. STATE MANAGEMENT & PERSISTENCE

### State Structure (LangGraph Checkpoint Format)

```python
ConversationState = {
    # Identity & Context
    "user_id": str,
    "conversation_id": str,
    "session_id": str,

    # Conversation Content
    "messages": List[BaseMessage],  # Full conversation history
    "last_query": str,
    "last_response": str,

    # Token & Budget Tracking
    "tokens_used": {
        "input_tokens": int,
        "output_tokens": int,
        "total_tokens": int,
        "by_provider": {
            "claude": int,
            "gpt4": int
        }
    },
    "cost_tracking": {
        "total_cost_usd": float,
        "by_provider": {
            "claude": float,
            "gpt4": float
        },
        "by_query": List[{
            "query": str,
            "cost": float,
            "tokens": int,
            "timestamp": str
        }]
    },

    # Agent State
    "agent_state": str,  # pending, retrieving, analyzing, responding, complete
    "retrieved_documents": List[dict],
    "tool_calls": List[dict],

    # User Budget & Rate Limiting
    "monthly_budget": {
        "tokens_allocated": int,
        "tokens_remaining": int,
        "cost_limit_usd": float,
        "cost_remaining_usd": float,
        "reset_date": str
    },

    # Metadata
    "created_at": str,
    "updated_at": str,
    "checkpoint_version": int,
}
```

### Checkpoint Persistence Strategy

```
TIER 1 (Hot Cache - In-Memory):
├─ Active conversation (last 5 turns)
├─ TTL: 1 hour
└─ Size: ~50KB per conversation

TIER 2 (Warm Storage - Database):
├─ LangGraph PostgreSQL checkpoints
├─ Stored after each turn
├─ Retention: 90 days
└─ Automatic pruning of old turns

TIER 3 (Summarized Archive - Cold Storage):
├─ Triggered when conversation > 30 turns or 50K tokens
├─ Generate summary of entire conversation
├─ Store summary + metadata in archive table
├─ Delete original detailed checkpoint
└─ Retention: 365 days

CHECKPOINT TRIGGERS:
├─ After each successful LLM response
├─ Before tool execution (for rollback)
├─ On user logout
└─ On budget alert threshold
```

### Token Budget Management

```
BUDGET ALLOCATION MODEL:

┌─────────────────────────────────────┐
│  User Tier Configuration            │
├─────────────────────────────────────┤
│ Free Tier:    100K tokens/month      │
│ Pro Tier:     1M tokens/month        │
│ Enterprise:   Unlimited             │
└─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│  Real-Time Budget Tracking          │
├─────────────────────────────────────┤
│ • Decrement on LLM usage            │
│ • Warn at 75% utilization          │
│ • Block at 100% utilization        │
│ • Prioritize cheaper provider      │
└─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│  Provider Selection Strategy        │
├─────────────────────────────────────┤
│ Query Type: Simple retrieval        │
│   → Use GPT-4o (cheaper)           │
│                                     │
│ Query Type: Complex reasoning      │
│   → Use Claude 3.5 Sonnet         │
│                                     │
│ Query Type: Multi-step analysis   │
│   → Provider with most budget left │
└─────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│  Token Optimization                 │
├─────────────────────────────────────┤
│ • Structured output (main loop)    │
│ • Context window truncation        │
│ • Conversation summarization       │
│ • Aggressive caching              │
└─────────────────────────────────────┘
```

---

## 5. COST OPTIMIZATION APPROACH

### Multi-Provider Strategy

```
PROVIDER SELECTION ENGINE:

┌──────────────────────┐
│   Incoming Query     │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  Classify Query Complexity               │
├──────────────────────────────────────────┤
│ • Simple (document search only)          │
│ • Moderate (single retrieval + analyze)  │
│ • Complex (multi-step reasoning)         │
│ • Urgent (low latency required)          │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  Candidate Provider Matrix               │
├──────────────────────────────────────────┤
│ Provider  │ Simple │ Moderate│ Complex   │
│-----------|--------|---------|-----------|
│ GPT-4o    │  $$$   │  $$$$   │  $$$$$    │
│ Claude 3.5│  $$    │  $$$    │  $$$$     │
│ Mixtral   │  $     │  $$     │  N/A      │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  Select Provider                         │
├──────────────────────────────────────────┤
│ • Check budget remaining                 │
│ • Check rate limits                      │
│ • Verify capability match                │
│ • Estimate token cost                    │
└──────────────────────────────────────────┘
```

### Cost-Saving Techniques

```
TECHNIQUE 1: Structured Output Generation
─────────────────────────────────────────
• Generate JSON schemas in main model loop
• Eliminate extra LLM calls for formatting
• Use tool_choice="required" for deterministic output
• Savings: 30-40% reduction in token usage

Example:
  Query: "Analyze P/E ratio trends"
  ├─ Retrieve documents (1 call)
  ├─ Generate structured output directly (no reformatting LLM call)
  └─ Stream JSON to client

  Cost: ~500 tokens vs ~700 tokens (old approach)

────────────────────────────────────────────────────

TECHNIQUE 2: Aggressive Caching
────────────────────────────────
• Cache retrieval results for identical queries
• Cache analysis results for same documents
• TTL: 24 hours for documents, 1 hour for analyses
• Key: hash(query, user_role, date_filter)
• Savings: 60-80% for repeated queries

────────────────────────────────────────────────────

TECHNIQUE 3: Context Compression
────────────────────────────────
• Summarize long conversations after 20 turns
• Compress retrieved documents (top 3 instead of 5)
• Use extractive summarization (no extra LLM call)
• Implement token budget warnings at 50%, 75%, 90%
• Savings: 25-35% on context tokens

────────────────────────────────────────────────────

TECHNIQUE 4: Provider Routing
─────────────────────────────
Decision Tree:
  if query_complexity == "simple":
    use GPT-4o (cheaper for simple tasks)
  elif query_complexity == "complex":
    use Claude (better at reasoning)
  elif budget_remaining < 0.5 * monthly_allocation:
    use cheapest available provider
  else:
    use provider with best capability match

Savings: 20-30% through smart provider selection

────────────────────────────────────────────────────

TECHNIQUE 5: Asynchronous Tool Batching
───────────────────────────────────────
• Group multiple retrieval requests in parallel
• Batch financial calculations
• Combine tool results before LLM processing
• Savings: 15-20% through reduced context building

────────────────────────────────────────────────────

TOKEN BUDGET ESTIMATION:

Typical Query Breakdown (500 tokens):
├─ Query input: 50 tokens
├─ Retrieved context: 300 tokens
├─ System prompt: 80 tokens
├─ Conversation history: 40 tokens
└─ Response output: 100 tokens

After Optimization (350 tokens):
├─ Query input: 50 tokens
├─ Summarized context: 150 tokens (compression)
├─ System prompt: 80 tokens
├─ Conversation summary: 20 tokens (summarization)
└─ Response output: 50 tokens (structured output)

Monthly Cost Estimation (10K queries):
├─ Without optimization: 5M tokens = $50
├─ With optimization: 3.5M tokens = $35
└─ Savings: 30% or $15/user/month
```

### Cost Tracking Implementation

```python
CostTrackingSchema = {
    "query_id": str,
    "user_id": str,
    "timestamp": str,
    "provider": str,  # "claude" or "gpt4"
    "input_tokens": int,
    "output_tokens": int,
    "total_tokens": int,
    "cost_usd": float,
    "query_type": str,  # "retrieval", "analysis", "reasoning"
    "tools_used": List[str],
    "cache_hit": bool,
    "latency_ms": int,
    "user_tier": str,
}

Cost Calculation:
├─ Claude 3.5 Sonnet:
│  ├─ Input: $3 per 1M tokens
│  └─ Output: $15 per 1M tokens
│
├─ GPT-4o:
│  ├─ Input: $5 per 1M tokens
│  └─ Output: $15 per 1M tokens
│
└─ Calculation:
   cost = (input_tokens * provider_input_rate) +
          (output_tokens * provider_output_rate)
```

---

## 6. OBSERVABILITY & MONITORING PLAN

### LangSmith Integration Strategy

```
TRACING HIERARCHY:

Project Level:
└─ financial-rag-production
   │
   ├─ Conversation Level (Tag: user_id, conversation_id)
   │  └─ Turn-based tracing
   │     ├─ Query execution (start → end)
   │     ├─ Tool calls (retrieval, analysis)
   │     ├─ LLM invocation
   │     ├─ Middleware hooks
   │     └─ Cost tracking
   │
   ├─ Middleware Tracing (Tag: middleware_name, hook_type)
   │  ├─ before_agent: Session load time
   │  ├─ before_model: Prompt construction time
   │  ├─ wrap_model_call: Token counting, streaming
   │  ├─ after_model: Validation time
   │  └─ after_agent: Persistence time
   │
   └─ Tool Tracing (Tag: tool_name)
      ├─ semantic_search: Vector DB latency
      ├─ financial_analysis: Parsing time
      └─ get_conversation_history: Checkpoint retrieval time

METRICS TO CAPTURE:

Latency Metrics:
├─ Total query latency (p50, p95, p99)
├─ Tool execution latency per tool
├─ LLM response latency by provider
├─ Middleware hook latency by type
└─ Token streaming latency

Cost Metrics:
├─ Cost per query (by provider, by user tier)
├─ Total monthly cost by provider
├─ Cost per user (aggregated)
├─ Tokens used per provider
└─ Cache hit rate (cost savings)

Quality Metrics:
├─ Document relevance score (user feedback)
├─ Analysis accuracy (validated against known values)
├─ User satisfaction (NPS score)
├─ Error rate per tool
└─ PII detection accuracy

Business Metrics:
├─ Queries per user per day
├─ Average tokens per query
├─ User retention rate
├─ Budget overage rate
└─ Provider preference (auto-selected vs manual)

DASHBOARD DEFINITION:

Dashboard: Financial RAG Overview
├─ KPI Cards:
│  ├─ Total Queries (24h): 1,234
│  ├─ Average Latency: 2.3s
│  ├─ Cost (24h): $45.23
│  └─ Error Rate: 0.2%
│
├─ Charts:
│  ├─ Query volume over time (by provider)
│  ├─ Latency distribution (p50/p95/p99)
│  ├─ Cost breakdown (by provider, by user tier)
│  ├─ Tool performance (latency, error rate)
│  └─ Token usage trend
│
├─ Tables:
│  ├─ Top users by queries
│  ├─ Slowest queries (with details)
│  ├─ Most expensive queries
│  └─ Tools with highest error rate
│
└─ Alerts:
   ├─ Error rate > 1%
   ├─ P95 latency > 5s
   ├─ Daily cost > $100
   ├─ Vector DB latency > 2s
   └─ Token budget utilization > 90%
```

### Custom Observability Implementation

```python
class FinancialRAGObserver:
    """
    Comprehensive observability for RAG system
    """

    def __init__(self, langsmith_client, metrics_backend):
        self.langsmith = langsmith_client
        self.metrics = metrics_backend

    # Middleware Hook Tracing
    def trace_before_agent(self, context):
        """Track session load, budget check, rate limits"""
        with self.langsmith.trace("before_agent"):
            metrics = {
                "session_load_ms": ...,
                "budget_check_ms": ...,
                "user_tier": context.user.tier,
                "budget_remaining": context.budget.remaining,
            }
            self.metrics.emit("middleware.before_agent", metrics)

    # Token Counting
    def count_tokens(self, provider, message):
        """Accurate token counting per provider"""
        if provider == "claude":
            return self._count_claude_tokens(message)
        elif provider == "gpt4":
            return self._count_openai_tokens(message)

    # Cost Calculation
    def calculate_cost(self, provider, tokens):
        """Real-time cost calculation"""
        rates = {
            "claude": {"input": 0.003, "output": 0.015},
            "gpt4": {"input": 0.005, "output": 0.015},
        }
        return sum(tokens.values()) * rates[provider]["average"]

    # Error Tracking
    def track_error(self, error_type, context):
        """Categorize and track errors"""
        self.metrics.emit("errors", {
            "type": error_type,
            "severity": self._classify_severity(error_type),
            "context": context,
            "timestamp": now(),
        })

    # Performance Profiling
    def profile_tool(self, tool_name, duration_ms):
        """Track tool performance over time"""
        self.metrics.emit("tool_performance", {
            "tool": tool_name,
            "latency_ms": duration_ms,
            "status": "success",
        })
```

### Monitoring & Alerting Rules

```
ALERT RULES:

1. Error Rate Spike
   Condition: error_rate > 0.01 for 5 minutes
   Severity: High
   Action: Page on-call engineer

2. Latency Degradation
   Condition: p95_latency > 5.0s for 10 minutes
   Severity: Medium
   Action: Check vector DB, LLM provider status

3. Vector DB Overload
   Condition: vector_search_latency > 2.0s for 3 minutes
   Severity: Medium
   Action: Scale vector DB, enable caching

4. Budget Overage
   Condition: daily_cost > monthly_budget / 30 * 1.5
   Severity: Low
   Action: Notify product team, review queries

5. Token Budget Alert
   Condition: user_token_utilization > 0.9
   Severity: Low
   Action: Suggest upgrade, enable caching

6. Provider Outage
   Condition: provider_error_rate > 0.05
   Severity: Critical
   Action: Failover to backup provider

7. PII Detection Failure
   Condition: pii_detection_confidence < 0.8
   Severity: Critical
   Action: Fallback to conservative masking
```

---

## 7. IMPLEMENTATION ROADMAP

### Phase 1: Foundation (Weeks 1-2)
- LangChain 1.0 agent scaffolding with create_agent()
- LangGraph checkpoint setup with PostgreSQL
- Basic retrieval tool with Pinecone
- Token counting integration
- Cost tracking database schema

### Phase 2: Middleware Stack (Weeks 3-4)
- Implement 6 middleware hooks
- PII detection and masking
- Token budget enforcement
- Conversation summarization
- Basic monitoring setup

### Phase 3: Advanced Features (Weeks 5-6)
- Multi-provider routing (Claude + GPT-4)
- Financial analysis tools
- Caching layer
- LangSmith dashboard
- Advanced streaming support

### Phase 4: Production Hardening (Weeks 7-8)
- Load testing (100K+ documents)
- Error recovery mechanisms
- Rate limiting refinement
- Security audit (API keys, encryption)
- Performance optimization

### Phase 5: Monitoring & Ops (Weeks 9+)
- Production observability
- Cost optimization fine-tuning
- User analytics dashboards
- On-call documentation
- Runbook creation

---

## 8. TECHNOLOGY STACK

```
Core Framework:
├─ LangChain 1.0 (agents, tools, runnable)
├─ LangGraph (conversation persistence, time-travel)
└─ Anthropic SDK (Claude integration)

LLM Providers:
├─ Anthropic Claude 3.5 Sonnet (primary)
├─ OpenAI GPT-4o (secondary, cost optimization)
└─ Mixtura 8x7B (fallback, cheaper)

Vector Database:
├─ Pinecone (primary, managed)
└─ Weaviate (backup, self-hosted option)

Persistence:
├─ PostgreSQL (LangGraph checkpoints)
├─ Redis (caching)
└─ S3 (conversation archives)

Observability:
├─ LangSmith (tracing, debugging, cost analysis)
├─ Prometheus (metrics)
├─ Grafana (dashboards)
└─ CloudWatch (logs)

Infrastructure:
├─ FastAPI (API server)
├─ Uvicorn (ASGI server)
├─ Docker (containerization)
└─ Kubernetes (orchestration)
```

---

## 9. KEY DESIGN DECISIONS & RATIONALE

```
DECISION 1: LangChain 1.0 create_agent() over custom LangGraph
├─ Rationale: Cleaner interface, automatic LangGraph integration,
│             built-in middleware support, faster development
├─ Trade-off: Less flexibility than custom graphs (acceptable trade)
└─ Impact: 40% reduction in boilerplate code

DECISION 2: Multi-Provider Strategy (Claude + GPT-4)
├─ Rationale: Claude better at reasoning, GPT-4o cheaper for simple tasks,
│             redundancy for production stability
├─ Trade-off: Increased complexity in provider routing logic
└─ Impact: 30% average cost reduction, improved reliability

DECISION 3: In-Loop Structured Output Generation
├─ Rationale: Eliminate extra LLM calls for output formatting
├─ Trade-off: Requires upfront schema definition
└─ Impact: 30-40% token savings per query

DECISION 4: Tiered Checkpoint Strategy
├─ Rationale: Hot cache for active conversations, archived summaries for cold storage
├─ Trade-off: Increased storage complexity
└─ Impact: Fast active conversation recovery, cost-effective archival

DECISION 5: PII Detection in Middleware Hooks
├─ Rationale: Consistent masking across retrieval and generation
├─ Trade-off: Slight performance overhead
└─ Impact: Compliance with financial regulations (GDPR, SOX)
```

---

## 10. RISK MITIGATION

```
RISK 1: Vector DB Latency at Scale (100K+ documents)
├─ Mitigation:
│  ├─ Implement hierarchical indexing
│  ├─ Use hybrid search (keyword + vector)
│  ├─ Enable result caching
│  ├─ Add read replicas
│  └─ Monitoring with alerts at 2s latency
│
└─ Fallback: Keyword search if vector search fails

RISK 2: Token Budget Overage
├─ Mitigation:
│  ├─ Enforce hard token budget limits
│  ├─ Implement context window truncation
│  ├─ Aggressive conversation summarization
│  ├─ Real-time budget warnings
│  └─ Monthly alerts on utilization
│
└─ Fallback: Automatic prompt compression at 80% budget

RISK 3: LLM Provider Outage
├─ Mitigation:
│  ├─ Multi-provider redundancy
│  ├─ Circuit breaker pattern
│  ├─ Graceful degradation to keyword search
│  ├─ Pre-cached popular queries
│  └─ Client-side fallback UI
│
└─ Fallback: Return cached results or error message

RISK 4: PII Leakage in Financial Data
├─ Mitigation:
│  ├─ Multi-stage PII detection (retrieval + generation)
│  ├─ User role-based access control
│  ├─ Audit logging of all data access
│  ├─ Regular compliance scans
│  └─ Automated testing on synthetic PII
│
└─ Fallback: Conservative masking (over-mask rather than under-mask)

RISK 5: Conversation State Corruption
├─ Mitigation:
│  ├─ Immutable checkpoints (append-only)
│  ├─ Versioning on each checkpoint
│  ├─ Automatic backup before state mutation
│  ├─ Checksum validation on load
│  └─ Time-travel debugging with LangGraph
│
└─ Fallback: Automatic rollback to last known good state
```

---

## 11. SUCCESS METRICS

```
Performance SLOs:
├─ P50 Latency: < 2.0 seconds
├─ P95 Latency: < 5.0 seconds
├─ P99 Latency: < 10.0 seconds
└─ Uptime: 99.9% (43 minutes downtime/month)

Cost SLOs:
├─ Average cost per query: < $0.05
├─ Tokens per query: < 500 (optimized)
├─ Cache hit rate: > 40%
└─ Provider cost efficiency: 30% reduction YoY

Quality SLOs:
├─ Error rate: < 0.5%
├─ Document relevance: > 0.75 (user feedback)
├─ PII detection accuracy: > 99%
└─ Analysis accuracy: > 95% (validated)

User Experience SLOs:
├─ First response time: < 1.0 second
├─ Streaming throughput: > 50 tokens/sec
├─ Query success rate: > 99%
└─ User satisfaction: > 4.0/5.0 stars
```

---

## CONCLUSION

This production-grade RAG system leverages LangChain 1.0's streamlined APIs, middleware system, and LangGraph integration to build a scalable, cost-efficient financial research platform. The architecture prioritizes:

1. **Performance**: Real-time streaming, <2s P50 latency
2. **Cost**: 30-40% reduction through structured outputs and smart routing
3. **Compliance**: PII detection and masking in all data flows
4. **Reliability**: Multi-provider redundancy, graceful degradation
5. **Observability**: Comprehensive LangSmith tracing, cost tracking
6. **Scalability**: Handles 100K+ documents with efficient retrieval

The modular middleware design enables rapid feature addition and A/B testing, while LangGraph checkpoints provide automatic conversation persistence and time-travel debugging for production troubleshooting.
