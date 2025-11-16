# LangChain 1.0 Multi-Model Agent Middleware Stack Design

## Executive Summary

This document provides a production-ready middleware stack architecture for complex multi-model agents with PII validation, dynamic model routing, token budget management, cost tracking, reasoning trace handling, and human-in-the-loop approval.

---

## Architecture Overview

### Middleware Execution Flow

```
User Input
    ↓
[before_agent] ← Load session state, validate PII, check budgets
    ↓
Agent Router (Tool Selection)
    ↓
[before_model] ← Route model based on complexity, add context, approval check
    ↓
[wrap_model_call] ← Count tokens, validate budget, execute model call
    ↓
Model Response (with content_blocks)
    ↓
[after_model] ← Parse reasoning traces, validate outputs, update costs
    ↓
Tool Execution
    ↓
[wrap_tool_call] ← Cost tracking for tool execution
    ↓
[after_agent] ← Persist costs, save checkpoints, summarize context
    ↓
User Output
```

### Key Design Principles

1. **Separation of Concerns**: Each middleware handles one aspect (PII, routing, budgets, costs, reasoning, approval, context)
2. **State Persistence**: Session state (budgets, costs, context) persisted in LangGraph checkpoints
3. **Non-blocking Validation**: PII and approval checks happen early; failures handled gracefully
4. **Cost Transparency**: All LLM calls tracked with token counting and cost estimation
5. **Content Block Awareness**: Middleware understands provider-specific reasoning traces and tool calls
6. **Human Interruption**: Approval middleware can pause execution at before_model hook
7. **Progressive Degradation**: If budget exceeded, fallback to cheaper models or sync mode

---

## 1. Session State Management

### SessionBudget Data Model

```python
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Dict, Optional

class TokenUsage(BaseModel):
    """Track token usage per model and overall"""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    @property
    def cost(self, provider: str, model: str) -> float:
        # Pricing varies by provider/model
        pricing = {
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4o": {"input": 0.005, "output": 0.015},
        }
        rate = pricing.get(model, {"input": 0.001, "output": 0.002})
        return (self.input_tokens * rate["input"] +
                self.output_tokens * rate["output"]) / 1000

class SessionBudget(BaseModel):
    """Per-user session budget tracking"""
    user_id: str
    session_id: str

    # Budget allocation
    max_tokens_per_session: int = 50000  # Hard limit
    max_cost_per_session: float = 10.0   # USD
    max_requests_per_session: int = 100

    # Current usage
    used_tokens: int = 0
    used_cost: float = 0.0
    request_count: int = 0

    # Per-model tracking
    model_usage: Dict[str, TokenUsage] = {}

    # Session metadata
    started_at: datetime = None
    expires_at: datetime = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.started_at is None:
            self.started_at = datetime.utcnow()
        if self.expires_at is None:
            self.expires_at = datetime.utcnow() + timedelta(hours=24)

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    @property
    def tokens_remaining(self) -> int:
        return max(0, self.max_tokens_per_session - self.used_tokens)

    @property
    def budget_remaining(self) -> float:
        return max(0.0, self.max_cost_per_session - self.used_cost)

    @property
    def can_proceed(self) -> bool:
        """Check if session can proceed with new request"""
        return (
            not self.is_expired and
            self.tokens_remaining > 1000 and  # Minimum 1k tokens
            self.budget_remaining > 0.01 and  # Minimum $0.01
            self.request_count < self.max_requests_per_session
        )

    def update_usage(self, model: str, tokens_in: int, tokens_out: int, cost: float):
        """Record token and cost usage"""
        self.used_tokens += tokens_in + tokens_out
        self.used_cost += cost
        self.request_count += 1

        if model not in self.model_usage:
            self.model_usage[model] = TokenUsage()

        usage = self.model_usage[model]
        usage.input_tokens += tokens_in
        usage.output_tokens += tokens_out
        usage.total_tokens += tokens_in + tokens_out

class SessionStateManager:
    """Manages persistent session state with LangGraph checkpoints"""

    def __init__(self, langgraph_checkpoint_storage):
        self.storage = langgraph_checkpoint_storage

    async def load_or_create(self, user_id: str, session_id: str) -> SessionBudget:
        """Load session budget from checkpoint or create new"""
        checkpoint_id = f"session:{user_id}:{session_id}"

        try:
            checkpoint = await self.storage.get_checkpoint(checkpoint_id)
            return SessionBudget.model_validate_json(checkpoint.values)
        except:
            # Create new session
            budget = SessionBudget(user_id=user_id, session_id=session_id)
            await self.persist(budget)
            return budget

    async def persist(self, budget: SessionBudget):
        """Save session budget to checkpoint"""
        checkpoint_id = f"session:{budget.user_id}:{budget.session_id}"
        await self.storage.put_checkpoint(
            checkpoint_id,
            values=budget.model_dump_json()
        )

    async def get_budget_summary(self, user_id: str, session_id: str) -> Dict:
        """Get human-readable budget summary"""
        budget = await self.load_or_create(user_id, session_id)
        return {
            "tokens_used": budget.used_tokens,
            "tokens_remaining": budget.tokens_remaining,
            "cost_used": round(budget.used_cost, 4),
            "budget_remaining": round(budget.budget_remaining, 4),
            "requests_used": budget.request_count,
            "is_expired": budget.is_expired,
            "can_proceed": budget.can_proceed,
            "per_model": {
                model: {
                    "tokens": usage.total_tokens,
                    "cost": usage.cost
                }
                for model, usage in budget.model_usage.items()
            }
        }
```

---

## 2. Middleware Components

### 2.1 PII Validation Middleware (before_agent)

```python
from typing import Any, Dict
import re
from enum import Enum

class PIIType(str, Enum):
    """PII categories"""
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"
    API_KEY = "api_key"
    DATABASE_PASSWORD = "database_password"

class PIIDetector:
    """Detect and redact PII in user input"""

    PATTERNS = {
        PIIType.SSN: r'\b\d{3}-\d{2}-\d{4}\b',
        PIIType.CREDIT_CARD: r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
        PIIType.EMAIL: r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        PIIType.PHONE: r'\b(?:\+?1[-.\s]?)?\(?[2-9]\d{2}\)?[-.\s]?[2-9]\d{2}[-.\s]?\d{4}\b',
        PIIType.API_KEY: r'(?:api[_-]?)?key[_-]?[a-zA-Z0-9]{32,}',
        PIIType.DATABASE_PASSWORD: r'password\s*=\s*["\']?[^"\'\s]+["\']?',
    }

    def __init__(self, strict_mode: bool = False):
        """
        strict_mode=True: Block any message with PII
        strict_mode=False: Redact PII and continue
        """
        self.strict_mode = strict_mode

    def detect(self, text: str) -> Dict[PIIType, list]:
        """Find PII in text"""
        findings = {}
        for pii_type, pattern in self.PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                findings[pii_type] = matches
        return findings

    def redact(self, text: str) -> tuple[str, Dict[PIIType, list]]:
        """Redact PII and return clean text + findings"""
        findings = self.detect(text)
        redacted = text

        for pii_type, pattern in self.PATTERNS.items():
            placeholder = f"[REDACTED_{pii_type.upper()}]"
            redacted = re.sub(pattern, placeholder, redacted, flags=re.IGNORECASE)

        return redacted, findings

class PIIValidationMiddleware:
    """Middleware to validate and redact PII before agent processing"""

    def __init__(self, pii_detector: PIIDetector, strict_mode: bool = False):
        self.detector = pii_detector
        self.strict_mode = strict_mode

    async def before_agent(
        self,
        agent_input: Dict[str, Any],
        agent_state: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Hook executed before agent processes input.

        Returns:
            - Modified agent_input with redacted content
            - Raises exception if strict_mode and PII found
        """
        user_message = agent_input.get("input", "")

        # Detect PII
        findings = self.detector.detect(user_message)

        if findings:
            # Log for audit trail
            audit_log = {
                "timestamp": datetime.utcnow(),
                "user_id": agent_state.get("user_id"),
                "pii_types_found": list(findings.keys()),
                "pii_count": sum(len(v) for v in findings.values())
            }

            if self.strict_mode:
                # Reject message with PII
                raise ValueError(
                    f"Input contains sensitive information: "
                    f"{', '.join(str(k) for k in findings.keys())}. "
                    f"Please remove and try again."
                )
            else:
                # Redact and continue
                clean_input, _ = self.detector.redact(user_message)
                agent_input["input"] = clean_input
                agent_state["pii_audit"] = audit_log
                agent_state["pii_was_redacted"] = True

        return agent_input
```

### 2.2 Query Complexity Router Middleware (before_agent)

```python
from enum import Enum

class QueryComplexity(str, Enum):
    """Query complexity levels"""
    SIMPLE = "simple"          # Use Claude-Haiku or GPT-4o
    MODERATE = "moderate"      # Use Claude-Sonnet or GPT-4
    COMPLEX = "complex"        # Use Claude-Opus or GPT-4 Turbo
    REQUIRES_REASONING = "reasoning"  # Extended thinking mode

class ComplexityAnalyzer:
    """Analyze query complexity to route to appropriate model"""

    # Complexity indicators
    SIMPLE_KEYWORDS = {
        "what", "who", "when", "where", "how many",
        "summarize", "list", "define"
    }

    COMPLEX_KEYWORDS = {
        "analyze", "compare", "contrast", "evaluate",
        "design", "architecture", "tradeoffs", "optimization",
        "debug", "troubleshoot", "root cause", "edge case"
    }

    REASONING_KEYWORDS = {
        "prove", "theorem", "proof", "mathematical",
        "logic", "constraint", "satisfaction", "reasoning"
    }

    def analyze(self, query: str) -> QueryComplexity:
        """Determine query complexity"""
        lower_query = query.lower()

        # Check for reasoning requirements
        if any(kw in lower_query for kw in self.REASONING_KEYWORDS):
            return QueryComplexity.REQUIRES_REASONING

        # Check for complex patterns
        complexity_score = 0

        # Factors that increase complexity
        if any(kw in lower_query for kw in self.COMPLEX_KEYWORDS):
            complexity_score += 3

        # Code analysis or technical depth
        if "```" in query or "code" in lower_query:
            complexity_score += 2

        # Length heuristic (long queries often more complex)
        if len(query) > 500:
            complexity_score += 2

        # Multiple sub-questions
        if query.count("?") > 2:
            complexity_score += 2

        # Domain-specific terminology
        technical_terms = ["algorithm", "architecture", "api", "database", "distributed"]
        if any(term in lower_query for term in technical_terms):
            complexity_score += 1

        # Determine complexity level
        if complexity_score >= 6:
            return QueryComplexity.COMPLEX
        elif complexity_score >= 3:
            return QueryComplexity.MODERATE
        elif any(kw in lower_query for kw in self.SIMPLE_KEYWORDS):
            return QueryComplexity.SIMPLE
        else:
            return QueryComplexity.MODERATE

class ModelRouter:
    """Route queries to appropriate models based on complexity"""

    ROUTING_TABLE = {
        QueryComplexity.SIMPLE: {
            "primary": "claude-3-haiku-20240307",
            "fallback": "gpt-4o",
            "max_tokens": 2000,
            "cost_budget_multiplier": 1.0,
        },
        QueryComplexity.MODERATE: {
            "primary": "claude-3-5-sonnet-20241022",
            "fallback": "gpt-4",
            "max_tokens": 4000,
            "cost_budget_multiplier": 2.0,
        },
        QueryComplexity.COMPLEX: {
            "primary": "claude-3-opus-20240229",
            "fallback": "gpt-4-turbo",
            "max_tokens": 8000,
            "cost_budget_multiplier": 4.0,
        },
        QueryComplexity.REQUIRES_REASONING: {
            "primary": "claude-3-opus-20240229",
            "fallback": "gpt-4-turbo",
            "max_tokens": 16000,
            "cost_budget_multiplier": 8.0,
            "enable_thinking": True,
        },
    }

    def __init__(self, budget_manager: SessionStateManager):
        self.budget = budget_manager
        self.complexity = ComplexityAnalyzer()

    async def route(
        self,
        query: str,
        session_budget: SessionBudget,
        user_preferences: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Route to appropriate model based on complexity and budget"""

        # Analyze complexity
        complexity = self.complexity.analyze(query)
        config = self.ROUTING_TABLE[complexity]

        # Check if preferred provider specified
        preferred_provider = (user_preferences or {}).get("preferred_provider")

        # Determine model to use
        model = config["primary"]
        if preferred_provider == "openai":
            model = config["fallback"]

        # Check if budget allows for this complexity
        estimated_cost = config["cost_budget_multiplier"] * 0.01  # Rough estimate
        if session_budget.budget_remaining < estimated_cost:
            # Downgrade to cheaper model
            if complexity == QueryComplexity.COMPLEX:
                model = self.ROUTING_TABLE[QueryComplexity.MODERATE]["primary"]
            elif complexity in [QueryComplexity.MODERATE, QueryComplexity.REQUIRES_REASONING]:
                model = self.ROUTING_TABLE[QueryComplexity.SIMPLE]["primary"]
            else:
                raise ValueError("Insufficient budget to process query")

        return {
            "complexity": complexity,
            "model": model,
            "max_tokens": config["max_tokens"],
            "enable_thinking": config.get("enable_thinking", False),
            "estimated_cost_multiplier": config["cost_budget_multiplier"],
        }

class ComplexityRoutingMiddleware:
    """Route queries to appropriate models based on complexity"""

    def __init__(self, router: ModelRouter):
        self.router = router

    async def before_agent(
        self,
        agent_input: Dict[str, Any],
        agent_state: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Determine model routing before agent starts"""

        session_budget: SessionBudget = agent_state.get("session_budget")
        query = agent_input.get("input", "")

        # Route query
        routing = await self.router.route(
            query,
            session_budget,
            agent_state.get("user_preferences", {})
        )

        # Store routing decision in state for use by before_model
        agent_state["query_routing"] = routing
        agent_state["target_model"] = routing["model"]
        agent_state["target_max_tokens"] = routing["max_tokens"]

        return agent_input
```

### 2.3 Budget & Cost Management Middleware

```python
from typing import Awaitable, Callable

class TokenCounter:
    """Count tokens using LangSmith integration"""

    def __init__(self, langsmith_client):
        self.langsmith = langsmith_client

    async def count_tokens(
        self,
        text: str,
        model: str
    ) -> Dict[str, int]:
        """Count tokens using model-specific tokenizer"""
        # Use LangSmith's token counting
        result = await self.langsmith.count_tokens(text, model=model)
        return {
            "input_tokens": result.get("total_tokens", 0),
            "output_tokens": 0  # To be filled after response
        }

class BudgetValidationMiddleware:
    """Validate token budget before making model calls"""

    def __init__(self, state_manager: SessionStateManager, token_counter: TokenCounter):
        self.state = state_manager
        self.counter = token_counter

    async def before_model(
        self,
        model_input: Dict[str, Any],
        agent_state: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Validate budget before sending to model"""

        session_budget: SessionBudget = agent_state.get("session_budget")
        routing = agent_state.get("query_routing", {})
        model = routing.get("model", "claude-3-5-sonnet-20241022")

        # Check session-level budget
        if not session_budget.can_proceed:
            budget_summary = {
                "tokens_remaining": session_budget.tokens_remaining,
                "budget_remaining": session_budget.budget_remaining,
                "is_expired": session_budget.is_expired,
            }
            raise ValueError(
                f"Budget exceeded. Summary: {budget_summary}"
            )

        # Estimate input tokens
        prompt_text = str(model_input.get("messages", []))
        token_estimate = await self.counter.count_tokens(prompt_text, model)

        # Check if we have enough tokens for input + estimated output
        estimated_total = (
            token_estimate["input_tokens"] +
            routing.get("max_tokens", 2000)
        )

        if estimated_total > session_budget.tokens_remaining:
            raise ValueError(
                f"Insufficient tokens. Needed: {estimated_total}, "
                f"Remaining: {session_budget.tokens_remaining}"
            )

        # Store estimate in state for later cost calculation
        agent_state["token_estimate"] = {
            "input_tokens": token_estimate["input_tokens"],
            "estimated_output_tokens": routing.get("max_tokens", 2000),
            "model": model,
        }

        return model_input

class CostTrackingMiddleware:
    """Track costs and implement safeguards"""

    PROVIDER_PRICING = {
        "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
        "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
        "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4": {"input": 0.03, "output": 0.06},
    }

    def __init__(self, state_manager: SessionStateManager):
        self.state = state_manager

    async def wrap_model_call(
        self,
        call_fn: Callable,
        agent_state: Dict[str, Any],
        **kwargs
    ) -> Awaitable[Any]:
        """
        Wrap model call to track costs and validate budget.

        This is the actual point where the LLM is called.
        We can intercept before and after the call.
        """

        session_budget: SessionBudget = agent_state.get("session_budget")
        estimate = agent_state.get("token_estimate", {})
        model = estimate.get("model", "unknown")

        # Call the actual model
        response = await call_fn()

        # Extract actual token usage from response
        # Content blocks include usage information
        actual_input_tokens = 0
        actual_output_tokens = 0

        if hasattr(response, "usage"):
            actual_input_tokens = response.usage.input_tokens
            actual_output_tokens = response.usage.output_tokens

        # Calculate actual cost
        pricing = self.PROVIDER_PRICING.get(model, {"input": 0.001, "output": 0.002})
        actual_cost = (
            actual_input_tokens * pricing["input"] +
            actual_output_tokens * pricing["output"]
        ) / 1000

        # Update session budget
        session_budget.update_usage(
            model,
            actual_input_tokens,
            actual_output_tokens,
            actual_cost
        )

        # Persist updated budget
        await self.state.persist(session_budget)

        # Store for audit
        agent_state["last_call_cost"] = {
            "model": model,
            "input_tokens": actual_input_tokens,
            "output_tokens": actual_output_tokens,
            "cost": actual_cost,
        }

        return response
```

### 2.4 Reasoning Trace Parsing Middleware (after_model)

```python
from typing import List, Optional

class ReasoningTrace:
    """Structured reasoning trace from model"""

    def __init__(
        self,
        provider: str,
        thinking_content: str = None,
        tool_calls: List[Dict] = None,
        text_content: str = None,
    ):
        self.provider = provider
        self.thinking_content = thinking_content
        self.tool_calls = tool_calls or []
        self.text_content = text_content

    def to_dict(self) -> Dict:
        return {
            "provider": self.provider,
            "thinking": self.thinking_content[:500] if self.thinking_content else None,
            "tool_calls_count": len(self.tool_calls),
            "response_preview": self.text_content[:200] if self.text_content else None,
        }

class ContentBlockParser:
    """Parse content_blocks from different LLM providers"""

    async def parse_anthropic(self, response: Any) -> ReasoningTrace:
        """
        Parse Anthropic Claude response with content_blocks.

        Anthropic content_blocks structure:
        [
            {"type": "thinking", "thinking": "..."},
            {"type": "tool_use", "id": "...", "name": "...", "input": {...}},
            {"type": "text", "text": "..."}
        ]
        """
        thinking = None
        tool_calls = []
        text = None

        for block in response.content:
            if block.type == "thinking":
                thinking = block.thinking
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                    "type": "tool_use",
                })
            elif block.type == "text":
                text = block.text

        return ReasoningTrace(
            provider="anthropic",
            thinking_content=thinking,
            tool_calls=tool_calls,
            text_content=text,
        )

    async def parse_openai(self, response: Any) -> ReasoningTrace:
        """
        Parse OpenAI response with structured outputs.

        OpenAI structure (with reasoning model):
        {
            "choices": [{
                "message": {
                    "content": "...",
                    "reasoning": "..." (if reasoning model)
                }
            }]
        }
        """
        thinking = None
        tool_calls = []
        text = None

        message = response.choices[0].message

        # OpenAI reasoning (if available)
        if hasattr(message, "reasoning"):
            thinking = message.reasoning

        # Tool calls
        if hasattr(message, "tool_calls") and message.tool_calls:
            tool_calls = [
                {
                    "id": tool.id,
                    "name": tool.function.name,
                    "input": json.loads(tool.function.arguments),
                    "type": "tool_call",
                }
                for tool in message.tool_calls
            ]

        # Text content
        text = message.content

        return ReasoningTrace(
            provider="openai",
            thinking_content=thinking,
            tool_calls=tool_calls,
            text_content=text,
        )

    async def parse_google(self, response: Any) -> ReasoningTrace:
        """Parse Google GenAI response"""
        thinking = None
        tool_calls = []
        text = None

        # Google uses similar structure to OpenAI
        content = response.candidates[0].content

        text_parts = []
        for part in content.parts:
            if hasattr(part, "text"):
                text_parts.append(part.text)
            elif hasattr(part, "function_call"):
                tool_calls.append({
                    "name": part.function_call.name,
                    "input": dict(part.function_call.args),
                    "type": "function_call",
                })

        text = " ".join(text_parts)

        return ReasoningTrace(
            provider="google",
            thinking_content=thinking,
            tool_calls=tool_calls,
            text_content=text,
        )

class ReasoningTraceMiddleware:
    """Parse and store reasoning traces from model responses"""

    def __init__(self, parser: ContentBlockParser):
        self.parser = parser

    async def after_model(
        self,
        model_response: Any,
        agent_state: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Parse reasoning traces from model response.

        This runs after model returns, before tools execute.
        Extracts structured insights from model reasoning.
        """

        target_model = agent_state.get("target_model", "")

        # Determine provider from model name
        if "claude" in target_model:
            trace = await self.parser.parse_anthropic(model_response)
        elif "gpt" in target_model:
            trace = await self.parser.parse_openai(model_response)
        else:
            trace = await self.parser.parse_google(model_response)

        # Store structured trace in state
        agent_state["reasoning_trace"] = trace.to_dict()

        # If reasoning enabled, extract key insights
        if trace.thinking_content:
            insights = await self._extract_insights(trace.thinking_content)
            agent_state["reasoning_insights"] = insights

        return model_response

    async def _extract_insights(self, thinking_content: str) -> List[str]:
        """Extract key insights from reasoning content"""
        # Simple heuristic: break into sentences that contain key patterns
        insights = []
        sentences = thinking_content.split(".")

        key_patterns = [
            "important", "key", "critical", "issue", "problem",
            "solution", "approach", "consideration", "constraint"
        ]

        for sentence in sentences:
            if any(pattern in sentence.lower() for pattern in key_patterns):
                insights.append(sentence.strip())

        return insights[:5]  # Top 5 insights
```

### 2.5 Human-in-the-Loop Approval Middleware (before_model)

```python
from enum import Enum
from datetime import datetime

class ApprovalLevel(str, Enum):
    """Risk levels for approval"""
    LOW = "low"           # Auto-approve
    MEDIUM = "medium"     # Ask human for approval
    HIGH = "high"         # Require explicit approval
    CRITICAL = "critical" # Require multi-factor confirmation

class OperationRiskAssessor:
    """Assess risk level of agent operations"""

    HIGH_RISK_OPERATIONS = {
        "database_write", "delete_data", "modify_user",
        "deploy_code", "modify_permissions", "financial_transaction",
    }

    HIGH_RISK_KEYWORDS = {
        "delete", "drop", "remove", "destroy",
        "modify user", "change permission", "transfer",
        "deploy", "production", "critical"
    }

    def assess_risk(self, agent_input: str, tools_to_use: List[str] = None) -> ApprovalLevel:
        """Assess operation risk level"""

        risk_score = 0

        # Check for high-risk operations in tool list
        if tools_to_use:
            for tool in tools_to_use:
                if any(op in tool.lower() for op in self.HIGH_RISK_OPERATIONS):
                    risk_score += 3

        # Check for high-risk keywords in input
        lower_input = agent_input.lower()
        for keyword in self.HIGH_RISK_KEYWORDS:
            if keyword in lower_input:
                risk_score += 2

        # Determine level
        if risk_score >= 5:
            return ApprovalLevel.CRITICAL
        elif risk_score >= 3:
            return ApprovalLevel.HIGH
        elif risk_score >= 1:
            return ApprovalLevel.MEDIUM
        else:
            return ApprovalLevel.LOW

class ApprovalStore:
    """Store and retrieve user approvals"""

    def __init__(self, storage):
        self.storage = storage

    async def request_approval(
        self,
        user_id: str,
        session_id: str,
        operation: str,
        risk_level: ApprovalLevel,
        timeout_seconds: int = 300,
    ) -> Dict[str, Any]:
        """
        Request human approval for operation.

        This would integrate with:
        - WebSocket channel back to user
        - Notification system
        - Admin approval interface
        """

        approval_request = {
            "request_id": f"apr_{datetime.utcnow().timestamp()}",
            "user_id": user_id,
            "session_id": session_id,
            "operation": operation,
            "risk_level": risk_level,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(seconds=timeout_seconds),
            "approved": None,
            "approved_by": None,
            "approved_at": None,
        }

        # Store request
        await self.storage.save(f"approval:{approval_request['request_id']}", approval_request)

        # Send notification to user (WebSocket, email, etc.)
        await self._notify_user(approval_request)

        # Wait for approval (with timeout)
        result = await self._wait_for_approval(
            approval_request["request_id"],
            timeout_seconds
        )

        return result

    async def approve(
        self,
        request_id: str,
        approved_by: str,
    ) -> bool:
        """Approve a pending request"""
        request = await self.storage.get(f"approval:{request_id}")
        if request and request["approved"] is None:
            request["approved"] = True
            request["approved_by"] = approved_by
            request["approved_at"] = datetime.utcnow()
            await self.storage.save(f"approval:{request_id}", request)
            return True
        return False

    async def deny(
        self,
        request_id: str,
        denied_by: str,
        reason: str = None,
    ) -> bool:
        """Deny a pending request"""
        request = await self.storage.get(f"approval:{request_id}")
        if request and request["approved"] is None:
            request["approved"] = False
            request["approved_by"] = denied_by
            request["denial_reason"] = reason
            request["approved_at"] = datetime.utcnow()
            await self.storage.save(f"approval:{request_id}", request)
            return True
        return False

    async def _notify_user(self, approval_request: Dict):
        """Send notification to user (implement based on your stack)"""
        pass

    async def _wait_for_approval(self, request_id: str, timeout_seconds: int) -> Dict:
        """Poll/wait for approval response"""
        pass

class HumanInTheLoopMiddleware:
    """Middleware to gate operations requiring human approval"""

    def __init__(
        self,
        risk_assessor: OperationRiskAssessor,
        approval_store: ApprovalStore,
        auto_approve_low_risk: bool = True,
    ):
        self.assessor = risk_assessor
        self.approvals = approval_store
        self.auto_approve_low_risk = auto_approve_low_risk

    async def before_model(
        self,
        model_input: Dict[str, Any],
        agent_state: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Check if operation requires human approval before proceeding.

        This middleware PAUSES execution if high-risk operation detected.
        The agent will resume when approval is granted.
        """

        user_input = agent_state.get("original_input", "")
        tools_to_use = model_input.get("tools", [])

        # Assess risk
        risk_level = self.assessor.assess_risk(user_input, tools_to_use)

        if risk_level == ApprovalLevel.LOW and self.auto_approve_low_risk:
            # Auto-approve, continue
            agent_state["approval_level"] = ApprovalLevel.LOW
            agent_state["approval_required"] = False
            return model_input

        if risk_level in [ApprovalLevel.MEDIUM, ApprovalLevel.HIGH, ApprovalLevel.CRITICAL]:
            # Request approval
            user_id = agent_state.get("user_id")
            session_id = agent_state.get("session_id")

            approval_result = await self.approvals.request_approval(
                user_id=user_id,
                session_id=session_id,
                operation=user_input[:100],
                risk_level=risk_level,
                timeout_seconds=300 if risk_level == ApprovalLevel.CRITICAL else 120,
            )

            if not approval_result.get("approved"):
                # Approval denied or timeout
                raise Exception(
                    f"Operation requires approval but was "
                    f"{approval_result.get('status', 'denied')}"
                )

            # Approval granted, continue
            agent_state["approval_level"] = risk_level
            agent_state["approval_required"] = True
            agent_state["approval_granted_by"] = approval_result.get("approved_by")

        return model_input
```

### 2.6 Context Summarization Middleware (before_model & after_agent)

```python
class ContextSummarizer:
    """Summarize conversation context to manage token limits"""

    def __init__(self, llm_client):
        self.llm = llm_client

    async def should_summarize(
        self,
        conversation_history: List[Dict],
        max_tokens: int = 4000,
    ) -> bool:
        """Check if conversation needs summarization"""

        # Count tokens in history
        total_tokens = sum(
            len(msg.get("content", "").split()) * 1.3  # Rough estimate
            for msg in conversation_history
        )

        # Summarize if approaching 70% of max
        return total_tokens > (max_tokens * 0.7)

    async def summarize_conversation(
        self,
        conversation_history: List[Dict],
        focus_on: str = None,
    ) -> str:
        """
        Summarize conversation history to condense context.

        Keeps recent messages, summarizes older ones.
        """

        if len(conversation_history) <= 3:
            return None  # Not enough to summarize

        # Split into recent (keep) and old (summarize)
        recent_count = 3  # Keep last 3 messages
        recent = conversation_history[-recent_count:]
        old = conversation_history[:-recent_count]

        # Build summarization prompt
        old_messages = "\n".join([
            f"{msg.get('role', 'unknown')}: {msg.get('content', '')[:200]}"
            for msg in old
        ])

        focus_instruction = f"\nKeep focus on: {focus_on}" if focus_on else ""

        summary_prompt = f"""Summarize this conversation history in 2-3 sentences.
Keep key decisions, important data, and context.{focus_instruction}

History:
{old_messages}

Summary:"""

        # Use smaller model for speed (don't consume budget)
        # In practice, you might use a fast local model or cache
        summary = await self.llm.generate(
            summary_prompt,
            model="claude-3-haiku-20240307",  # Fast summarization
            max_tokens=300,
        )

        return summary

class ContextManagementMiddleware:
    """Manage conversation context to stay within token limits"""

    def __init__(self, summarizer: ContextSummarizer):
        self.summarizer = summarizer

    async def before_model(
        self,
        model_input: Dict[str, Any],
        agent_state: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Check conversation history size and summarize if needed.

        This prevents token limit exceeded errors.
        """

        messages = model_input.get("messages", [])
        max_tokens = agent_state.get("target_max_tokens", 4000)

        # Check if summarization needed
        should_summarize = await self.summarizer.should_summarize(
            messages,
            max_tokens=max_tokens
        )

        if should_summarize:
            # Get user's main focus if available
            focus = agent_state.get("primary_goal")

            # Summarize old messages
            summary = await self.summarizer.summarize_conversation(
                messages,
                focus_on=focus
            )

            if summary:
                # Replace old messages with summary message
                recent_messages = messages[-3:]
                summarized_messages = [
                    {
                        "role": "system",
                        "content": f"Context summary: {summary}"
                    },
                    *recent_messages
                ]

                model_input["messages"] = summarized_messages
                agent_state["context_was_summarized"] = True
                agent_state["summary_created_at"] = datetime.utcnow()

        return model_input

    async def after_agent(
        self,
        agent_output: Dict[str, Any],
        agent_state: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Check if context should be archived or pruned after completion.
        """

        # Archive old checkpoints if conversation getting too long
        conversation_length = len(agent_state.get("messages", []))
        if conversation_length > 50:
            # Mark old checkpoints for archival
            agent_state["checkpoint_pruning_needed"] = True

        return agent_output
```

### 2.7 Tool Execution Cost Tracking (wrap_tool_call)

```python
class ToolCallCostTracker:
    """Track costs of tool execution"""

    TOOL_COSTS = {
        "database_query": 0.001,
        "api_call": 0.002,
        "file_read": 0.0001,
        "file_write": 0.0001,
        "search": 0.0005,
    }

    def __init__(self, state_manager: SessionStateManager):
        self.state = state_manager

    async def wrap_tool_call(
        self,
        call_fn: Callable,
        tool_name: str,
        tool_input: Dict,
        agent_state: Dict[str, Any],
        **kwargs
    ) -> Awaitable[Any]:
        """
        Wrap tool execution to track costs.

        Tools are less expensive than LLM calls but still need tracking.
        """

        start_time = datetime.utcnow()

        # Execute tool
        result = await call_fn()

        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()

        # Estimate cost (varies by tool type)
        base_cost = self.TOOL_COSTS.get(
            tool_name,
            0.0001  # Default small cost
        )

        # Time-based multiplier (10s = 10x cost)
        time_multiplier = max(1.0, execution_time / 10.0)
        tool_cost = base_cost * time_multiplier

        # Update session budget
        session_budget: SessionBudget = agent_state.get("session_budget")
        session_budget.used_cost += tool_cost
        await self.state.persist(session_budget)

        # Log tool execution
        if "tool_executions" not in agent_state:
            agent_state["tool_executions"] = []

        agent_state["tool_executions"].append({
            "tool_name": tool_name,
            "execution_time": execution_time,
            "cost": tool_cost,
            "input": str(tool_input)[:100],
            "timestamp": start_time,
        })

        return result
```

---

## 3. Middleware Execution Order & State Flow

### Execution Sequence

```
USER INPUT
    ↓
[1. before_agent]
    ├─ PIIValidationMiddleware: Detect & redact sensitive info
    ├─ ComplexityRoutingMiddleware: Analyze query, determine model
    └─ Output: agent_state enriched with routing, budgets validated
    ↓
[2. Agent Tool Selection]
    (Agent decides which tools to invoke)
    ↓
[3. before_model]
    ├─ HumanInTheLoopMiddleware: Check approval if high-risk
    ├─ ContextManagementMiddleware: Summarize if needed
    ├─ BudgetValidationMiddleware: Final budget check
    └─ Output: model_input ready for LLM, approval granted if needed
    ↓
[4. wrap_model_call]
    ├─ Entry: Count tokens, validate budget one more time
    ├─ Call: Execute LLM model with cost tracking
    └─ Exit: Update session budget with actual usage
    ↓
[5. after_model]
    ├─ ReasoningTraceMiddleware: Parse content_blocks, extract insights
    └─ Output: model_response with reasoning traces extracted
    ↓
[6. Tool Execution]
    └─ wrap_tool_call: Track tool costs
    ↓
[7. after_agent]
    ├─ ContextManagementMiddleware: Check for archival/pruning
    ├─ Persist: Save costs and state to checkpoint
    └─ Output: Final result with full cost accounting
    ↓
USER OUTPUT with Summary
```

### State Object Structure

```python
# agent_state structure maintained throughout execution
agent_state = {
    # User & Session Info
    "user_id": str,
    "session_id": str,
    "original_input": str,

    # Budget & Cost Tracking (from SessionBudget)
    "session_budget": SessionBudget,
    "token_estimate": {
        "input_tokens": int,
        "estimated_output_tokens": int,
        "model": str,
    },
    "last_call_cost": {
        "model": str,
        "input_tokens": int,
        "output_tokens": int,
        "cost": float,
    },

    # Routing & Model Selection
    "query_routing": {
        "complexity": QueryComplexity,
        "model": str,
        "max_tokens": int,
        "enable_thinking": bool,
    },
    "target_model": str,
    "target_max_tokens": int,

    # PII & Security
    "pii_was_redacted": bool,
    "pii_audit": {
        "timestamp": datetime,
        "pii_types_found": List[PIIType],
        "pii_count": int,
    },

    # Approval Status
    "approval_level": ApprovalLevel,
    "approval_required": bool,
    "approval_granted_by": str,

    # Reasoning & Content Blocks
    "reasoning_trace": {
        "provider": str,
        "thinking": str,
        "tool_calls_count": int,
        "response_preview": str,
    },
    "reasoning_insights": List[str],

    # Context Management
    "context_was_summarized": bool,
    "summary_created_at": datetime,
    "checkpoint_pruning_needed": bool,

    # Tool Execution
    "tool_executions": [
        {
            "tool_name": str,
            "execution_time": float,
            "cost": float,
            "timestamp": datetime,
        }
    ],

    # User Preferences
    "user_preferences": {
        "preferred_provider": str,  # "anthropic" | "openai" | "google"
        "budget_alerts": bool,
    },
}
```

---

## 4. Checkpoint Strategy for State Persistence

### Checkpoint Design

```python
class CheckpointStrategy:
    """Strategy for persisting agent state to checkpoints"""

    # Checkpoint frequency levels
    CHECKPOINT_AFTER_EVERY_MODEL = 1      # Most frequent, highest overhead
    CHECKPOINT_AFTER_TOOL_CALL = 2        # Moderate frequency
    CHECKPOINT_AFTER_AGENT_TURN = 3       # Standard (recommended)
    CHECKPOINT_AFTER_SUMMARIZATION = 4    # Less frequent, larger summaries

    def __init__(self, storage, strategy_level: int = 3):
        self.storage = storage
        self.strategy = strategy_level

    async def should_checkpoint(
        self,
        event_type: str,  # "model_call", "tool_call", "agent_turn"
        agent_state: Dict,
    ) -> bool:
        """Determine if checkpoint should be created"""

        if event_type == "model_call":
            return self.strategy <= self.CHECKPOINT_AFTER_EVERY_MODEL
        elif event_type == "tool_call":
            return self.strategy <= self.CHECKPOINT_AFTER_TOOL_CALL
        elif event_type == "agent_turn":
            return self.strategy <= self.CHECKPOINT_AFTER_AGENT_TURN
        elif event_type == "summarization":
            return self.strategy <= self.CHECKPOINT_AFTER_SUMMARIZATION

        return False

    async def create_checkpoint(
        self,
        user_id: str,
        session_id: str,
        turn_number: int,
        agent_state: Dict,
        event_type: str,
    ) -> str:
        """
        Create a checkpoint for recovery and debugging.

        Returns: checkpoint_id for time-travel debugging
        """

        checkpoint_id = f"{user_id}:{session_id}:turn{turn_number}:{event_type}"

        checkpoint = {
            "checkpoint_id": checkpoint_id,
            "timestamp": datetime.utcnow(),
            "user_id": user_id,
            "session_id": session_id,
            "turn_number": turn_number,
            "event_type": event_type,

            # Full state for recovery
            "state": agent_state.copy(),

            # Metadata for cleanup
            "size_bytes": len(str(agent_state)),
            "tokens_used_so_far": agent_state.get("session_budget", {}).get("used_tokens", 0),
        }

        # Compress for storage
        await self.storage.put_checkpoint(checkpoint_id, checkpoint)

        return checkpoint_id

    async def recover_from_checkpoint(
        self,
        checkpoint_id: str,
    ) -> Dict:
        """Recover agent state from checkpoint"""

        checkpoint = await self.storage.get_checkpoint(checkpoint_id)
        return checkpoint["state"]

    async def cleanup_old_checkpoints(
        self,
        user_id: str,
        session_id: str,
        keep_count: int = 10,
    ):
        """
        Clean up old checkpoints to save storage.

        Keep most recent N checkpoints per session.
        """

        pattern = f"{user_id}:{session_id}:*"
        checkpoints = await self.storage.list_checkpoints(pattern)

        # Sort by timestamp, keep recent ones
        checkpoints_sorted = sorted(
            checkpoints,
            key=lambda x: x.get("timestamp"),
            reverse=True
        )

        for checkpoint in checkpoints_sorted[keep_count:]:
            await self.storage.delete_checkpoint(checkpoint["checkpoint_id"])
```

### Checkpoint Persistence in LangGraph

```python
from langgraph.checkpoint.base import BaseCheckpointStorage
from langgraph.checkpoint.postgres import PostgresCheckpointStorage

async def setup_langgraph_checkpoints(postgres_url: str):
    """
    Set up LangGraph checkpoint storage using PostgreSQL.

    This enables:
    - Automatic conversation state persistence
    - Time-travel debugging (replay from any checkpoint)
    - Multi-turn conversation recovery
    """

    # Use PostgreSQL for production
    checkpoint_storage = PostgresCheckpointStorage(
        connection_string=postgres_url,
        table_name="langgraph_checkpoints",
    )

    return checkpoint_storage

async def create_agent_with_checkpoints(
    llm_client,
    tools: List,
    checkpoint_storage,
    middleware_stack: List,
):
    """
    Create agent with checkpoint support.

    LangGraph automatically saves checkpoints after each step.
    """

    from langchain.agents import create_agent

    agent = create_agent(
        llm=llm_client,
        tools=tools,
        system_prompt="You are a helpful assistant.",

        # Middleware stack
        middleware=middleware_stack,

        # Checkpointing configuration
        checkpointer=checkpoint_storage,

        # Save state after each step
        checkpoint_at="end",

        # Fallback recovery
        on_failure="restore_from_checkpoint",
    )

    return agent
```

---

## 5. Error Handling & Rollback Strategies

### Comprehensive Error Recovery

```python
class MiddlewareErrorHandler:
    """Handle errors in middleware with rollback strategies"""

    class ErrorSeverity(Enum):
        RECOVERABLE = 1      # Can retry
        DEGRADABLE = 2       # Fallback available
        FATAL = 3            # Must abort

    def __init__(self, checkpoint_manager: CheckpointStrategy):
        self.checkpoints = checkpoint_manager

    async def handle_middleware_error(
        self,
        error: Exception,
        middleware_name: str,
        stage: str,  # before_agent, before_model, wrap_model_call, etc.
        agent_state: Dict,
        agent_input: Dict,
    ) -> Dict[str, Any]:
        """
        Handle middleware error with appropriate strategy.

        Returns: recovery_action
        """

        severity = self._assess_severity(error, middleware_name)

        if severity == self.ErrorSeverity.RECOVERABLE:
            return await self._retry_with_backoff(
                error, middleware_name, agent_state
            )
        elif severity == self.ErrorSeverity.DEGRADABLE:
            return await self._apply_fallback(
                error, middleware_name, agent_state
            )
        else:  # FATAL
            return await self._abort_and_rollback(
                error, middleware_name, agent_state
            )

    def _assess_severity(self, error: Exception, middleware_name: str) -> ErrorSeverity:
        """Determine error severity"""

        # PII validation failure: fatal (security)
        if "PIIValidationMiddleware" in middleware_name:
            return self.ErrorSeverity.FATAL

        # Budget validation failure: degradable (use cheaper model)
        if "BudgetValidationMiddleware" in middleware_name:
            return self.ErrorSeverity.DEGRADABLE

        # Approval timeout: fatal (security)
        if "HumanInTheLoopMiddleware" in middleware_name:
            return self.ErrorSeverity.FATAL

        # Model call failure: recoverable (retry)
        if "wrap_model_call" in middleware_name:
            return self.ErrorSeverity.RECOVERABLE

        # Tool failure: degradable (skip tool)
        if "wrap_tool_call" in middleware_name:
            return self.ErrorSeverity.DEGRADABLE

        # Context summarization failure: degradable (truncate)
        if "ContextManagementMiddleware" in middleware_name:
            return self.ErrorSeverity.DEGRADABLE

        return self.ErrorSeverity.DEGRADABLE

    async def _retry_with_backoff(
        self,
        error: Exception,
        middleware_name: str,
        agent_state: Dict,
    ) -> Dict[str, Any]:
        """Retry operation with exponential backoff"""

        retry_count = agent_state.get(f"{middleware_name}_retries", 0)
        max_retries = 3

        if retry_count >= max_retries:
            raise error

        # Exponential backoff: 1s, 2s, 4s
        wait_time = 2 ** retry_count
        await asyncio.sleep(wait_time)

        agent_state[f"{middleware_name}_retries"] = retry_count + 1

        return {
            "action": "retry",
            "retry_count": retry_count + 1,
            "wait_time": wait_time,
        }

    async def _apply_fallback(
        self,
        error: Exception,
        middleware_name: str,
        agent_state: Dict,
    ) -> Dict[str, Any]:
        """Apply fallback strategy"""

        if "BudgetValidationMiddleware" in middleware_name:
            # Fallback: use cheaper model
            return {
                "action": "downgrade_model",
                "from_model": agent_state.get("target_model"),
                "to_model": "claude-3-haiku-20240307",
            }

        elif "ContextManagementMiddleware" in middleware_name:
            # Fallback: truncate instead of summarize
            return {
                "action": "truncate_context",
                "keep_last_n_messages": 5,
            }

        elif "wrap_tool_call" in middleware_name:
            # Fallback: skip tool, continue with LLM response
            return {
                "action": "skip_tool",
                "continue_with": "llm_response",
            }

        return {
            "action": "continue_with_warnings",
            "warning": str(error),
        }

    async def _abort_and_rollback(
        self,
        error: Exception,
        middleware_name: str,
        agent_state: Dict,
    ) -> Dict[str, Any]:
        """Abort operation and rollback to last checkpoint"""

        session_id = agent_state.get("session_id")
        user_id = agent_state.get("user_id")

        # Find last successful checkpoint
        last_checkpoint = await self.checkpoints.storage.list_checkpoints(
            f"{user_id}:{session_id}:*"
        )

        if last_checkpoint:
            checkpoint_id = last_checkpoint[0]["checkpoint_id"]
            restored_state = await self.checkpoints.recover_from_checkpoint(checkpoint_id)

            return {
                "action": "rollback",
                "recovered_from": checkpoint_id,
                "restored_state": restored_state,
            }
        else:
            return {
                "action": "abort_session",
                "error": str(error),
            }
```

---

## 6. Complete Integration Example

### Assembling the Middleware Stack

```python
async def build_middleware_stack(
    llm_client,
    langsmith_client,
    postgres_url: str,
    redis_client,
):
    """
    Build complete middleware stack for multi-model agent.

    Returns: List of middleware instances in execution order
    """

    # 1. Set up storage and managers
    checkpoint_storage = await setup_langgraph_checkpoints(postgres_url)
    state_manager = SessionStateManager(checkpoint_storage)

    # 2. PII Validation
    pii_detector = PIIDetector(strict_mode=False)
    pii_middleware = PIIValidationMiddleware(pii_detector)

    # 3. Complexity Routing
    token_counter = TokenCounter(langsmith_client)
    model_router = ModelRouter(state_manager)
    routing_middleware = ComplexityRoutingMiddleware(model_router)

    # 4. Budget Management
    budget_middleware = BudgetValidationMiddleware(state_manager, token_counter)
    cost_tracking_middleware = CostTrackingMiddleware(state_manager)

    # 5. Reasoning Trace Parsing
    content_parser = ContentBlockParser()
    reasoning_middleware = ReasoningTraceMiddleware(content_parser)

    # 6. Human-in-the-Loop
    risk_assessor = OperationRiskAssessor()
    approval_store = ApprovalStore(redis_client)
    approval_middleware = HumanInTheLoopMiddleware(risk_assessor, approval_store)

    # 7. Context Management
    context_summarizer = ContextSummarizer(llm_client)
    context_middleware = ContextManagementMiddleware(context_summarizer)

    # 8. Tool Cost Tracking
    tool_cost_middleware = ToolCallCostTracker(state_manager)

    # Build middleware stack in execution order
    middleware_stack = [
        # before_agent hooks
        {
            "name": "pii_validation",
            "hook": "before_agent",
            "middleware": pii_middleware,
        },
        {
            "name": "complexity_routing",
            "hook": "before_agent",
            "middleware": routing_middleware,
        },

        # before_model hooks
        {
            "name": "human_approval",
            "hook": "before_model",
            "middleware": approval_middleware,
        },
        {
            "name": "context_management",
            "hook": "before_model",
            "middleware": context_middleware,
        },
        {
            "name": "budget_validation",
            "hook": "before_model",
            "middleware": budget_middleware,
        },

        # wrap_model_call hook
        {
            "name": "cost_tracking",
            "hook": "wrap_model_call",
            "middleware": cost_tracking_middleware,
        },

        # after_model hooks
        {
            "name": "reasoning_parsing",
            "hook": "after_model",
            "middleware": reasoning_middleware,
        },

        # wrap_tool_call hook
        {
            "name": "tool_cost_tracking",
            "hook": "wrap_tool_call",
            "middleware": tool_cost_middleware,
        },

        # after_agent hooks (empty, but context_middleware handles it)
    ]

    return middleware_stack

# Usage in agent creation
async def create_multi_model_agent(llm_client, tools, config):
    """
    Create the final agent with complete middleware stack.
    """

    from langchain.agents import create_agent

    middleware_stack = await build_middleware_stack(
        llm_client=llm_client,
        langsmith_client=config["langsmith_client"],
        postgres_url=config["postgres_url"],
        redis_client=config["redis_client"],
    )

    agent = create_agent(
        llm=llm_client,
        tools=tools,
        system_prompt="""You are a helpful multi-model AI assistant.

        You have access to tools for various tasks.
        Always follow security guidelines and budget constraints.
        """,

        # Register middleware
        middleware=middleware_stack,

        # Checkpoint for state persistence
        checkpointer=await setup_langgraph_checkpoints(config["postgres_url"]),
    )

    return agent
```

### Using the Agent

```python
async def run_agent(agent, user_id: str, session_id: str, user_input: str):
    """
    Execute agent with full middleware stack.

    The middleware stack handles:
    - PII redaction
    - Model routing based on complexity
    - Budget validation
    - Cost tracking
    - Reasoning trace extraction
    - Approval workflows
    - Context management
    - State persistence
    """

    # Initialize session budget
    state_manager = SessionStateManager(agent.checkpointer)
    session_budget = await state_manager.load_or_create(user_id, session_id)

    # Prepare agent state
    agent_state = {
        "user_id": user_id,
        "session_id": session_id,
        "original_input": user_input,
        "session_budget": session_budget,
        "user_preferences": {
            "preferred_provider": "anthropic",  # Claude by default
        },
    }

    # Run agent (middleware stack executes automatically)
    try:
        result = await agent.ainvoke(
            input={"input": user_input},
            config={
                "configurable": {"user_id": user_id, "session_id": session_id},
            },
            state=agent_state,  # State passed through all middleware
        )

        # Get final budget summary
        budget_summary = await state_manager.get_budget_summary(user_id, session_id)

        return {
            "response": result.get("output"),
            "reasoning_insights": agent_state.get("reasoning_insights", []),
            "cost_summary": {
                "tokens_used": budget_summary["tokens_used"],
                "cost_used": budget_summary["cost_used"],
                "remaining_budget": budget_summary["budget_remaining"],
            },
            "metadata": {
                "approval_required": agent_state.get("approval_required", False),
                "pii_redacted": agent_state.get("pii_was_redacted", False),
                "context_summarized": agent_state.get("context_was_summarized", False),
            },
        }

    except Exception as e:
        # Error handler provides recovery strategy
        error_handler = MiddlewareErrorHandler(CheckpointStrategy(agent.checkpointer))
        recovery = await error_handler.handle_middleware_error(
            e,
            middleware_name=getattr(e, "middleware_name", "unknown"),
            stage="execution",
            agent_state=agent_state,
            agent_input={"input": user_input},
        )

        return {
            "error": str(e),
            "recovery_action": recovery.get("action"),
            "budget_summary": await state_manager.get_budget_summary(user_id, session_id),
        }
```

---

## 7. Monitoring & Observability

### LangSmith Integration for Cost Analysis

```python
from langsmith import Client as LangSmithClient

class CostAnalyzer:
    """Analyze costs and performance using LangSmith"""

    def __init__(self, langsmith_api_key: str):
        self.client = LangSmithClient(api_key=langsmith_api_key)

    async def get_session_analytics(
        self,
        user_id: str,
        session_id: str,
    ) -> Dict[str, Any]:
        """Get cost and performance analytics for session"""

        runs = self.client.list_runs(
            filter=f'and(eq(metadata_key:"user_id", "{user_id}"), '
                  f'eq(metadata_key:"session_id", "{session_id}"))',
        )

        total_cost = 0.0
        model_breakdown = {}

        for run in runs:
            cost = self._estimate_cost_from_run(run)
            total_cost += cost

            model = run.extra.get("model", "unknown")
            if model not in model_breakdown:
                model_breakdown[model] = {"cost": 0.0, "calls": 0}

            model_breakdown[model]["cost"] += cost
            model_breakdown[model]["calls"] += 1

        return {
            "total_cost": total_cost,
            "per_model": model_breakdown,
            "run_count": len(runs),
        }

    def _estimate_cost_from_run(self, run) -> float:
        """Estimate cost from a run using token counts"""

        tokens_in = run.extra.get("tokens_in", 0)
        tokens_out = run.extra.get("tokens_out", 0)
        model = run.extra.get("model", "")

        pricing = {
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
            "gpt-4": {"input": 0.03, "output": 0.06},
        }

        rates = pricing.get(model, {"input": 0.001, "output": 0.002})
        return (tokens_in * rates["input"] + tokens_out * rates["output"]) / 1000
```

---

## Summary

This middleware stack provides:

✓ **Layered Security**: PII validation before any model interaction
✓ **Smart Model Routing**: Dynamic selection based on query complexity and budget
✓ **Cost Control**: Token budgets, cost tracking, and safeguards
✓ **Reasoning Extraction**: Parse content_blocks from all providers
✓ **Human Approval**: Gated operations with approval workflows
✓ **Context Management**: Automatic summarization for token limits
✓ **Persistence**: LangGraph checkpoints for recovery and debugging
✓ **Error Recovery**: Graceful degradation with fallback strategies
✓ **Observability**: LangSmith integration for cost analysis

Each middleware is independent, composable, and can be enabled/disabled based on your needs.
