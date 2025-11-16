# Unified Content Blocks - Quick Reference Guide

## Overview

A standardized parsing system for LLM responses across Claude, OpenAI (GPT-4/o1), and Google Gemini that extracts reasoning traces, tool calls, and financial insights.

## Quick Start

### Basic Usage

```python
from financial_content_handler import FinancialContentBlockHandler

# Initialize with auto-detection
handler = FinancialContentBlockHandler(model_name="claude-3-5-sonnet-20241022")

# Process any LLM response
response = client.messages.create(...)
processed = handler.process_response(response)

# Access results
print(f"Model: {processed.parsed_response.model}")
print(f"Reasoning: {processed.parsed_response.reasoning_traces}")
print(f"Tools: {processed.parsed_response.tool_calls}")
print(f"Insights: {processed.combined_insights}")
```

## Core Components

### 1. ContentBlockParser (Unified Interface)

```python
from content_blocks_parser import ContentBlockParserFactory, ProviderType

# Create parser for provider
parser = ContentBlockParserFactory.create_parser(ProviderType.ANTHROPIC)

# Or auto-detect from model name
parser = ContentBlockParserFactory.create_parser_for_model("gpt-4-turbo")

# Parse response
parsed = parser.safe_parse(response)  # Never throws
```

### 2. ParsedResponse (Main Output)

```python
ParsedResponse(
    provider: ProviderType,           # anthropic, openai, google
    model: str,                       # Model name used
    content_blocks: List[UnifiedContentBlock],  # Normalized blocks
    reasoning_traces: List[ReasoningTrace],     # Extracted reasoning
    tool_calls: List[ToolCallData],   # Validated tool calls
    final_text: str,                  # Main response text
    stop_reason: Optional[str],       # "end_turn", "tool_use", etc
    usage: Optional[Dict[str, int]],  # Token counts
    parse_errors: List[str]           # Any parsing issues
)
```

### 3. UnifiedContentBlock (Standardized Block)

```python
UnifiedContentBlock(
    block_type: ContentBlockType,     # TEXT, REASONING, TOOL_USE, IMAGE, etc
    content: Union[str, Dict],        # Block content
    metadata: Optional[Dict],         # Provider-specific metadata
    raw_provider_data: Optional[Dict],# Original provider format
    error: Optional[str]              # Parse errors for this block
)
```

### 4. ReasoningTrace (Extracted Reasoning)

```python
ReasoningTrace(
    format: ReasoningFormat,  # CLAUDE_THINKING, OPENAI_REASONING, GEMINI_REASONING
    content: str,             # The reasoning text
    confidence: float,        # 0.0-1.0
    token_count: Optional[int]
)
```

## Content Block Types

| Type | Description | Providers |
|------|-------------|-----------|
| TEXT | Main response text | All |
| REASONING | Model's thinking process | All (format varies) |
| THINKING | Claude's native thinking blocks | Claude |
| TOOL_USE | Tool call request | All |
| TOOL_RESULT | Tool execution result | All |
| IMAGE | Image/document content | All |

## Reasoning Formats

| Format | Provider | Details |
|--------|----------|---------|
| CLAUDE_THINKING | Claude 3.5 w/ extended thinking | Native thinking blocks, non-streamed |
| OPENAI_REASONING | o1-preview, o1 | Via reasoning_content field |
| GEMINI_REASONING | Gemini w/ reasoning | Via thinking_content field |
| TEXT_TRACE | Any provider | Fallback: reasoning in text content |

## Provider Response Mapping

### Claude (Anthropic)

```python
response = {
    "content": [
        {"type": "thinking", "thinking": "..."},    # Reasoning
        {"type": "text", "text": "..."},           # Main response
        {"type": "tool_use", "id": "X", "name": "fetch_data", "input": {...}},
        {"type": "tool_result", "tool_use_id": "X", "content": "..."},
        {"type": "image", "source": {...}}
    ]
}
```

### OpenAI (GPT-4/o1)

```python
response = {
    "choices": [{
        "message": {
            "content": "...",                    # Main response
            "reasoning_content": "...",          # o1 models only
            "tool_calls": [                      # Tool calls
                {
                    "id": "call_X",
                    "function": {
                        "name": "fetch_data",
                        "arguments": '{"key": "value"}'  # JSON string
                    }
                }
            ]
        }
    }]
}
```

### Google (Gemini)

```python
response = {
    "candidates": [{
        "thinking_content": {"text": "..."},     # Reasoning
        "content": {
            "parts": [
                {"text": "..."},                 # Main response
                {
                    "function_call": {
                        "name": "fetch_data",
                        "args": {"key": "value"}  # Direct dict
                    }
                },
                {"inline_data": {"mime_type": "image/png", "data": "..."}}
            ]
        }
    }]
}
```

## Common Patterns

### Pattern 1: Extract Insights Only

```python
handler = FinancialContentBlockHandler(model_name="claude-3-5-sonnet-20241022")
processed = handler.process_response(response)

# High-confidence insights
high_conf = processed.get_high_confidence_insights(threshold=0.9)

# By type
valuations = processed.get_insights_by_type(FinancialInsightType.VALUATION)
risks = processed.get_insights_by_type(FinancialInsightType.RISK)
```

### Pattern 2: Execute Tools Safely

```python
handler = FinancialContentBlockHandler(
    model_name="claude-3-5-sonnet-20241022",
    max_tool_budget=0.10  # $0.10 per request
)
processed = handler.process_response(response)

if processed.validate_all_tools():
    for tool_call in processed.parsed_response.tool_calls:
        result = execute_tool(tool_call.tool_name, tool_call.raw_input)
        # Feed result back to agent
else:
    print("Invalid tools, skipping execution")

print(f"Total cost: ${processed.get_total_tool_cost()}")
```

### Pattern 3: Multi-Provider Consensus

```python
handlers = {
    "claude": FinancialContentBlockHandler(model_name="claude-3-5-sonnet-20241022"),
    "gpt": FinancialContentBlockHandler(model_name="gpt-4-turbo"),
    "gemini": FinancialContentBlockHandler(model_name="gemini-1.5-pro"),
}

for provider, handler in handlers.items():
    response = get_response_from_provider(provider)
    processed = handler.process_response(response)

    # Compare insights
    valuations = processed.get_insights_by_type(FinancialInsightType.VALUATION)
    print(f"{provider}: {len(valuations)} valuation insights")
```

### Pattern 4: Analyze Reasoning

```python
handler = FinancialContentBlockHandler(model_name="claude-3-5-sonnet-20241022")
processed = handler.process_response(response)

# Access reasoning traces
for trace in processed.parsed_response.reasoning_traces:
    print(f"Format: {trace.format.value}")
    print(f"Content: {trace.content}")
    print(f"Tokens: {trace.token_count}")

# Get insights extracted FROM reasoning
reasoning_insights = processed.reasoning_insights
text_insights = processed.text_insights
```

## Error Handling

### Safe Parsing (Never Throws)

```python
# safe_parse always returns ParsedResponse, even if it fails
parsed = parser.safe_parse(malformed_response)

# Check for errors
if parsed.parse_errors:
    print(f"Parsing errors: {parsed.parse_errors}")
    # Can still access parsed.content_blocks, etc
```

### Tool Validation

```python
# Validates all tools before execution
validations = processed.tool_validations

for validation in validations:
    if not validation.is_valid:
        print(f"Tool {validation.tool_name} errors: {validation.errors}")

    if validation.warnings:
        print(f"Tool {validation.tool_name} warnings: {validation.warnings}")
```

### Handling Missing Content

```python
# Graceful degradation if content missing
reasoning = processed.parsed_response.reasoning_traces
if not reasoning:
    print("No reasoning available, using text only")
    insights = processed.text_insights
else:
    insights = processed.reasoning_insights + processed.text_insights
```

## Insight Types

```python
from financial_content_handler import FinancialInsightType

insights_by_type = {
    FinancialInsightType.VALUATION: [...],   # PE, fair value, etc
    FinancialInsightType.RISK: [...],        # Volatility, drawdown, etc
    FinancialInsightType.PERFORMANCE: [...], # Returns, yield, etc
    FinancialInsightType.FORECAST: [...],    # Projections, estimates
    FinancialInsightType.ANOMALY: [...],     # Unusual patterns
}
```

## Configuration Examples

### Production Setup

```python
# Fast, reliable execution
default_handler = FinancialContentBlockHandler(
    model_name="gpt-4-turbo",
    max_tool_budget=5.0
)

# Deep reasoning for complex analysis
reasoning_handler = FinancialContentBlockHandler(
    model_name="claude-3-5-sonnet-20241022",
    max_tool_budget=10.0
)

# Multi-modal analysis
vision_handler = FinancialContentBlockHandler(
    model_name="gemini-1.5-pro",
    max_tool_budget=3.0
)
```

### Development Setup

```python
# Extensive logging
import logging
logging.basicConfig(level=logging.DEBUG)

# No budget constraints
handler = FinancialContentBlockHandler(
    model_name="claude-3-5-sonnet-20241022",
    max_tool_budget=None  # Unlimited
)
```

## File Locations

| File | Purpose |
|------|---------|
| `src/services/content_blocks_parser.py` | Core parsing logic & interfaces |
| `src/services/financial_content_handler.py` | Financial analysis integration |
| `src/examples/financial_analysis_examples.py` | Real-world usage examples |
| `tests/test_content_blocks.py` | Comprehensive test suite |

## API Reference

### FinancialContentBlockHandler

```python
handler = FinancialContentBlockHandler(
    provider: Optional[ProviderType] = None,
    model_name: Optional[str] = None,
    max_tool_budget: Optional[float] = None
)

# Process response
processed = handler.process_response(response: Any) -> ProcessedFinancialResponse

# Extract actionable insights
insights = handler.extract_actionable_insights(response: Any) -> List[Dict]

# Stream processing
async processed = handler.process_response_streaming(response_stream)
```

### ProcessedFinancialResponse

```python
# Get insights
high_conf = processed.get_high_confidence_insights(threshold: float = 0.8)
typed = processed.get_insights_by_type(insight_type: FinancialInsightType)

# Validation
is_valid = processed.validate_all_tools() -> bool
cost = processed.get_total_tool_cost() -> float

# Export
dict_form = processed.to_dict() -> Dict[str, Any]
```

### ContentBlockParserFactory

```python
# Create by provider
parser = ContentBlockParserFactory.create_parser(
    provider: ProviderType
) -> ContentBlockParser

# Create by model name (auto-detect)
parser = ContentBlockParserFactory.create_parser_for_model(
    model_name: str
) -> ContentBlockParser

# Register custom parser
ContentBlockParserFactory.register_parser(
    provider: ProviderType,
    parser_class: type
)
```

## Troubleshooting

### Issue: No reasoning traces extracted

**Solution**: Not all models include reasoning. Check:
- Using extended thinking model (Claude 3.5)?
- Using o1-preview/o1 for OpenAI?
- Use text_insights as fallback

### Issue: Tool calls not validating

**Solution**: Check validation errors:
```python
for v in processed.tool_validations:
    if not v.is_valid:
        print(v.errors)  # Missing inputs, unknown tool, etc
```

### Issue: JSON parsing fails for OpenAI arguments

**Solution**: Already handled. Arguments are parsed with fallback:
```python
# Malformed JSON is stored as:
tool_call.raw_input = {"raw": original_string}
```

### Issue: Different insights from different providers

**Solution**: This is expected. Compare consensus:
```python
# Get common themes across providers
consensus = portfolio_analyzer.get_consensus_analysis([...])
print(consensus["common_themes"])
```

## Performance Tips

1. **Token counting**: Use `processed.parsed_response.usage` for accurate counts
2. **Streaming**: Accumulate chunks once, parse final response
3. **Tool validation**: Cache results if running same tools repeatedly
4. **Insight extraction**: Process high-confidence insights first
5. **Provider selection**:
   - Claude: Best reasoning, slower
   - GPT-4: Fast and reliable
   - Gemini: Good multi-modal support

## Next Steps

1. **Read**: `UNIFIED_CONTENT_BLOCKS_ARCHITECTURE.md` for deep dive
2. **Review**: `src/examples/financial_analysis_examples.py` for patterns
3. **Test**: `tests/test_content_blocks.py` for edge cases
4. **Integrate**: Use in your agent with examples as templates

## Support

- **Bug**: Check parsing errors in `processed.parse_errors`
- **Custom provider**: Use `ContentBlockParserFactory.register_parser()`
- **Tool validation**: Check `processed.tool_validations` for details
- **Logging**: Enable debug logging for transformation steps
