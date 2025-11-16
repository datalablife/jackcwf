"""
Unified Content Blocks Architecture Guide for Financial Analysis Agent

OVERVIEW
========

This document describes the unified content blocks parsing strategy for cross-provider
LLM integration. It standardizes how to extract and process responses from Claude,
OpenAI GPT-4/o1, and Google Gemini within financial analysis workflows.

ARCHITECTURE
============

1. PROVIDER-SPECIFIC PARSING LAYER
   |
   |-- AnthropicContentBlockParser (Claude)
   |   |-- Handles thinking/reasoning blocks
   |   |-- Extracts native tool_use format
   |   |-- Processes images/documents
   |
   |-- OpenAIContentBlockParser (GPT-4/o1)
   |   |-- Handles function_call format
   |   |-- Extracts reasoning_content (o1 models)
   |   |-- Parses JSON arguments
   |
   |-- GoogleContentBlockParser (Gemini)
   |   |-- Handles function_call format
   |   |-- Extracts thinking_content
   |   |-- Processes inline_data (images)
   |
   --> Unified Interface: ContentBlockParser (Abstract)

2. UNIFIED REPRESENTATION LAYER
   |
   |-- ParsedResponse (main output type)
   |-- UnifiedContentBlock (normalized blocks)
   |-- ReasoningTrace (normalized reasoning)
   |-- ToolCallData (normalized tool calls)

3. FINANCIAL ANALYSIS LAYER
   |
   |-- FinancialContentBlockHandler (main entry point)
   |-- FinancialReasoningAnalyzer (extracts insights)
   |-- ToolCallValidator (validates & costs)

4. FACTORY PATTERN
   |
   |-- ContentBlockParserFactory
   |   |-- create_parser(provider: ProviderType)
   |   |-- create_parser_for_model(model_name: str)
   |   |-- register_parser(custom provider)


KEY CONCEPTS
============

CONTENT BLOCKS
--------------
- Unified representation of response components
- Types: TEXT, REASONING, THINKING, TOOL_USE, TOOL_RESULT, IMAGE, DOCUMENT
- Each provider maps to standard types

REASONING FORMATS
-----------------
- CLAUDE_THINKING: Claude's native thinking blocks (non-streamed, available at end)
- OPENAI_REASONING: o1-preview/o1 reasoning_content (alternative models)
- GEMINI_REASONING: Gemini's thinking_content (when available)
- TEXT_TRACE: Fallback text-based reasoning (when native not available)

TOOL CALL NORMALIZATION
------------------------
Claude:
  {
    "type": "tool_use",
    "id": "tooluse_123",
    "name": "fetch_data",
    "input": {"param": "value"}
  }

OpenAI:
  {
    "type": "function",
    "id": "call_123",
    "function": {
      "name": "fetch_data",
      "arguments": '{"param": "value"}'
    }
  }

Google:
  {
    "function_call": {
      "name": "fetch_data",
      "args": {"param": "value"}
    }
  }

All normalized to: ToolCallData with tool_name, tool_id, raw_input


IMPLEMENTATION PATTERNS
=======================

PATTERN 1: Basic Response Processing
-----------------------------------

from financial_content_handler import FinancialContentBlockHandler

# Initialize with auto-detection
handler = FinancialContentBlockHandler(model_name="claude-3-5-sonnet-20241022")

# Process response (any provider)
response = client.messages.create(...)
processed = handler.process_response(response)

# Access components
insights = processed.combined_insights
reasoning = processed.parsed_response.reasoning_traces
tool_calls = processed.parsed_response.tool_calls


PATTERN 2: Multi-Provider Consensus
-----------------------------------

handlers = {
    "claude": FinancialContentBlockHandler(model_name="claude-3-5-sonnet-20241022"),
    "gpt": FinancialContentBlockHandler(model_name="gpt-4-turbo"),
    "gemini": FinancialContentBlockHandler(model_name="gemini-1.5-pro"),
}

responses = {
    "claude": claude_client.messages.create(...),
    "gpt": openai_client.chat.completions.create(...),
    "gemini": gemini_client.generate_content(...),
}

for provider, handler in handlers.items():
    processed = handler.process_response(responses[provider])
    # Compare insights across providers
    valuation = processed.get_insights_by_type(FinancialInsightType.VALUATION)


PATTERN 3: Tool Call Execution Pipeline
--------------------------------------

# Handler validates and costs all tools
handler = FinancialContentBlockHandler(
    model_name="claude-3-5-sonnet-20241022",
    max_tool_budget=0.10  # $0.10 per request
)

processed = handler.process_response(response)

# Check validation before execution
if processed.validate_all_tools():
    for tool_call in processed.parsed_response.tool_calls:
        result = execute_tool(tool_call.tool_name, tool_call.raw_input)
        # Feed result back to agent

# Track costs
total_cost = processed.get_total_tool_cost()


PATTERN 4: Streaming Responses
-----------------------------

async def process_streaming():
    handler = FinancialContentBlockHandler(model_name="gpt-4-turbo")

    # Stream from OpenAI
    async with client.messages.stream(...) as stream:
        async for chunk in stream:
            # Handler processes chunks as they arrive
            pass

    # Process accumulated response
    processed = handler.process_response(accumulated)


PATTERN 5: Reasoning Analysis
----------------------------

handler = FinancialContentBlockHandler(model_name="claude-3-5-sonnet-20241022")
processed = handler.process_response(response)

# Access reasoning traces
for trace in processed.parsed_response.reasoning_traces:
    print(f"Format: {trace.format.value}")  # claude_thinking
    print(f"Content: {trace.content}")
    print(f"Tokens: {trace.token_count}")

# Extract financial insights FROM reasoning
insights = processed.reasoning_insights  # Parsed insights
high_conf = processed.get_high_confidence_insights(threshold=0.9)


EDGE CASES & HANDLING
====================

EDGE CASE 1: Malformed JSON in Function Arguments
-------------------------------------------------
OpenAI sometimes returns invalid JSON in function arguments.

HANDLED BY: OpenAIContentBlockParser._extract_tool_calls()
- Attempts json.loads()
- Falls back to {"raw": argument_string}
- Logs warning but continues processing

EDGE CASE 2: Missing Reasoning Content
--------------------------------------
Not all models provide reasoning (e.g., standard GPT-4 without o1).

HANDLED BY:
- reasoning_traces will be empty list
- safe_parse() always returns valid ParsedResponse
- Graceful degradation to text_insights only

EDGE CASE 3: Streaming Interruption
-----------------------------------
User cancels streaming response mid-generation.

HANDLED BY:
- process_response_streaming() accumulates what was received
- parse_errors captured if response incomplete
- Partial analysis still available

EDGE CASE 4: Tool Cost Exceeds Budget
------------------------------------
Computed total tool cost > max_tool_budget

HANDLED BY:
- ToolValidationResult.warnings populated
- Agent can choose to:
  a) Proceed anyway
  b) Skip expensive tools
  c) Request user approval

EDGE CASE 5: Provider Response Format Changes
---------------------------------------------
API changes structure of response (provider upgrade).

HANDLED BY:
- Custom parser registration via ContentBlockParserFactory.register_parser()
- Non-breaking updates to parser logic
- Falls back to UNKNOWN block types for unrecognized content

EDGE CASE 6: Multi-modal Content
-------------------------------
Response contains images, PDFs, or other documents.

HANDLED BY:
- Separate IMAGE and DOCUMENT block types
- raw_provider_data preserved for later processing
- Handler can delegate to specialized processors:

image_blocks = [b for b in parsed.content_blocks
                if b.block_type == ContentBlockType.IMAGE]
document_blocks = [b for b in parsed.content_blocks
                   if b.block_type == ContentBlockType.DOCUMENT]


PERFORMANCE CONSIDERATIONS
==========================

PARSING OVERHEAD
----------------
- Anthropic: ~1-2ms (simple object navigation)
- OpenAI: ~2-3ms (JSON parsing for function args)
- Google: ~1-2ms (parts iteration)
- Total: < 5ms for typical responses

MEMORY FOOTPRINT
---------------
- ParsedResponse + components: ~5-10KB per response
- Raw response kept in raw_provider_data
- Consider clearing if processing large batches

TOKEN COUNTING
--------------
- From response.usage when available
- Fallback to approximate (split length) for reasoning
- Use LangSmith for authoritative counts

REASONING TRACE ANALYSIS
------------------------
- Financial keyword extraction: O(n) where n = trace length
- Typically 100-300 tokens per trace
- Fast (~1ms) for reasonable trace lengths

STREAMING EFFICIENCY
-------------------
- Accumulate chunks without re-parsing
- Only parse final accumulated response
- Incremental insights extracted on-demand


COST OPTIMIZATION
=================

1. STRUCTURED OUTPUT GENERATION
   - Generate JSON/structured data in main loop
   - Avoid extra LLM call for parsing
   - Implemented in ToolCallData schema validation

2. TOKEN COUNTING
   - Built-in via response.usage
   - Enables cost tracking per insight type
   - Profile expensive insight types

3. TOOL COST CACHING
   - Cache tool costs in TOOL_COSTS dict
   - Avoids recalculation
   - Update when APIs change pricing

4. REASONING SELECTIVE EXECUTION
   - Use Claude thinking selectively
   - ~2-3x token cost vs standard Claude
   - Worth it for high-stakes decisions

5. PROVIDER SELECTION STRATEGY
   - Claude: Best reasoning, use for complex analysis
   - GPT-4: Fastest, use for quick turnaround
   - Gemini: Good balance, use for multi-modal

EXAMPLE: Cost Optimization Middleware
from financial_content_handler import FinancialContentBlockHandler

class CostTrackingMiddleware:
    def __init__(self, max_cost_per_run: float = 0.50):
        self.max_cost = max_cost_per_run
        self.total_cost = 0.0

    def should_process_response(self, handler, response):
        # Pre-check: would this exceed budget?
        estimated = self._estimate_cost(response)
        return (self.total_cost + estimated) <= self.max_cost

    def process_response(self, handler, response):
        processed = handler.process_response(response)
        self.total_cost += processed.get_total_tool_cost()
        return processed


ERROR HANDLING STRATEGY
======================

DESIGN PRINCIPLE: Always return valid ParsedResponse

1. PARSING ERRORS
   - safe_parse() catches all exceptions
   - Stores errors in parse_errors list
   - Returns minimal ParsedResponse

2. TOOL VALIDATION ERRORS
   - Collected in ToolValidationResult
   - Agent can decide to proceed or skip
   - No exception thrown

3. INSIGHT EXTRACTION ERRORS
   - Individual insights skipped on error
   - Collected insights still returned
   - Partial results better than none

4. LOGGING STRATEGY
   - CRITICAL: Parse failures affecting all blocks
   - WARNING: Individual block/tool parse failures
   - DEBUG: Content block transformation steps

TESTING STRATEGY
===============

TEST COVERAGE AREAS:

1. Provider-Specific Parsing (Unit)
   - Claude thinking + text blocks
   - OpenAI function calls + reasoning
   - Google function calls + thinking
   - Image/document handling
   - Error recovery

2. Cross-Provider Consistency (Integration)
   - Same analysis from each provider
   - Consistent insight extraction
   - Unified representation verified

3. Financial Insight Analysis (Unit)
   - Keyword detection accuracy
   - Metric extraction from text
   - Confidence scoring
   - Insight type classification

4. Tool Validation (Unit)
   - Valid tool detection
   - Cost calculation
   - Budget enforcement
   - Error message quality

5. End-to-End Workflows (Integration)
   - Stock analysis agent
   - Portfolio consensus
   - Tool execution pipeline
   - Streaming responses


MIGRATION GUIDE (from legacy LangChain)
======================================

BEFORE (Legacy):
```
from langchain.agents import initialize_agent
from langchain.chat_models import ChatAnthropic

agent = initialize_agent(
    tools=[my_tools],
    llm=ChatAnthropic(),
    agent="chat-zero-shot-react-description"
)
response = agent.run("Analyze AAPL")

# Parsing was custom, non-standard
```

AFTER (LangChain 1.0):
```
from financial_content_handler import FinancialContentBlockHandler

handler = FinancialContentBlockHandler(model_name="claude-3-5-sonnet")
response = client.messages.create(...)
processed = handler.process_response(response)

# Standard parsing, works across providers
insights = processed.combined_insights
```

MIGRATION STEPS:
1. Update model initialization (use official client, not LangChain wrapper)
2. Replace custom response parsing with handler
3. Update tool calling to use content blocks
4. Test with multiple providers
5. Migrate agents to use new middleware hooks


DEPLOYMENT RECOMMENDATIONS
==========================

DEVELOPMENT ENVIRONMENT:
- Use fast models (gpt-4-turbo, claude-opus)
- Enable reasoning for accuracy
- Extensive logging
- No budget constraints

STAGING ENVIRONMENT:
- Mix of models for testing
- Budget constraints: $10/day
- Structured logging
- Performance profiling

PRODUCTION ENVIRONMENT:
- Balanced model selection:
  - 80% GPT-4 (fast, reliable)
  - 15% Claude Sonnet (reasoning on demand)
  - 5% Gemini (multi-modal)
- Budget constraints: $1000/month
- Error alerting
- Cost dashboards
- LangSmith tracing


CONFIGURATION EXAMPLE:
```python
# prod_handler.py

from financial_content_handler import FinancialContentBlockHandler

def create_production_handler():
    return FinancialContentBlockHandler(
        model_name="gpt-4-turbo",  # Default: fast & reliable
        max_tool_budget=5.0  # Per request
    )

def create_reasoning_handler():
    """For complex financial analysis requiring extended thinking"""
    return FinancialContentBlockHandler(
        model_name="claude-3-5-sonnet-20241022",
        max_tool_budget=10.0
    )
```
"""

# This docstring serves as the architecture guide
# Below is implementation summary

print(__doc__)
