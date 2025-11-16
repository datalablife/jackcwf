"""
Unified Content Blocks - Getting Started in 5 Minutes

Copy-paste these examples to get started immediately.
"""

# EXAMPLE 1: Parse Claude Response
# ==================================

from src.services.content_blocks_parser import ContentBlockParserFactory, ProviderType
from src.services.financial_content_handler import FinancialContentBlockHandler

# Initialize
handler = FinancialContentBlockHandler(model_name="claude-3-5-sonnet-20241022")

# Claude response with reasoning
claude_response = {
    "id": "msg_123",
    "model": "claude-3-5-sonnet-20241022",
    "content": [
        {
            "type": "thinking",
            "thinking": (
                "Let me analyze the P/E ratio. "
                "Company has earnings of $10M, market cap $200M. "
                "P/E = 20x, which is below sector average of 25x. "
                "This suggests the stock may be undervalued."
            )
        },
        {
            "type": "text",
            "text": "Based on my analysis, the stock appears undervalued with a P/E ratio of 20."
        },
        {
            "type": "tool_use",
            "id": "tooluse_123",
            "name": "fetch_financial_statements",
            "input": {"company_id": "AAPL", "period": "Q3_2024"}
        }
    ],
    "stop_reason": "tool_use",
    "usage": {"input_tokens": 200, "output_tokens": 75}
}

# Process
processed = handler.process_response(claude_response)

# Access results
print(f"Model: {processed.parsed_response.model}")
print(f"Reasoning: {processed.parsed_response.reasoning_traces[0].content}")
print(f"Main text: {processed.parsed_response.final_text}")
print(f"Tool calls: {len(processed.parsed_response.tool_calls)}")
print(f"Insights: {len(processed.combined_insights)}")

# Get valuation insights specifically
valuation = processed.get_insights_by_type(FinancialInsightType.VALUATION)
for insight in valuation:
    print(f"  - {insight.content} (confidence: {insight.confidence})")


# EXAMPLE 2: Parse OpenAI Response
# ================================

# OpenAI response with function calls
openai_response = {
    "id": "chatcmpl-123",
    "model": "gpt-4-turbo",
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": "The company shows strong fundamentals with consistent revenue growth.",
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "fetch_stock_data",
                            "arguments": '{"ticker": "AAPL", "start_date": "2024-01-01"}'
                        }
                    }
                ]
            },
            "finish_reason": "tool_calls"
        }
    ],
    "usage": {
        "prompt_tokens": 200,
        "completion_tokens": 50,
        "total_tokens": 250
    }
}

# Process (same API!)
handler = FinancialContentBlockHandler(model_name="gpt-4-turbo")
processed = handler.process_response(openai_response)

print(f"\nOpenAI Response:")
print(f"Model: {processed.parsed_response.model}")
print(f"Text: {processed.parsed_response.final_text}")
print(f"Tools: {[tc.tool_name for tc in processed.tool_calls]}")
print(f"Tool inputs: {processed.tool_calls[0].raw_input if processed.tool_calls else 'None'}")


# EXAMPLE 3: Parse Google Gemini Response
# =======================================

gemini_response = {
    "candidates": [
        {
            "content": {
                "parts": [
                    {
                        "text": "The financial metrics suggest strong growth potential."
                    },
                    {
                        "function_call": {
                            "name": "search_documents",
                            "args": {"query": "quarterly earnings report"}
                        }
                    }
                ]
            },
            "finish_reason": "STOP"
        }
    ],
    "model_name": "gemini-1.5-pro"
}

# Same API
handler = FinancialContentBlockHandler(model_name="gemini-1.5-pro")
processed = handler.process_response(gemini_response)

print(f"\nGemini Response:")
print(f"Model: {processed.parsed_response.model}")
print(f"Text: {processed.parsed_response.final_text}")
print(f"Tools: {[tc.tool_name for tc in processed.tool_calls]}")


# EXAMPLE 4: Compare Multiple Providers
# =====================================

def compare_providers():
    """Get same analysis from all 3 providers."""

    handlers = {
        "claude": FinancialContentBlockHandler(model_name="claude-3-5-sonnet-20241022"),
        "gpt": FinancialContentBlockHandler(model_name="gpt-4-turbo"),
        "gemini": FinancialContentBlockHandler(model_name="gemini-1.5-pro"),
    }

    # In real scenario, call each API
    responses = {
        "claude": claude_response,
        "gpt": openai_response,
        "gemini": gemini_response,
    }

    results = {}
    for provider, handler in handlers.items():
        processed = handler.process_response(responses[provider])

        results[provider] = {
            "model": processed.parsed_response.model,
            "insights": len(processed.combined_insights),
            "tools": len(processed.tool_calls),
            "reasoning": len(processed.reasoning_traces) > 0,
            "cost": processed.get_total_tool_cost(),
        }

    print("\nProvider Comparison:")
    for provider, data in results.items():
        print(f"\n{provider.upper()}:")
        print(f"  Model: {data['model']}")
        print(f"  Insights: {data['insights']}")
        print(f"  Tools: {data['tools']}")
        print(f"  Reasoning: {data['reasoning']}")
        print(f"  Cost: ${data['cost']}")

    return results


# EXAMPLE 5: Validate and Execute Tools
# ======================================

def execute_tools_safely(response):
    """Execute tools only if validated."""

    handler = FinancialContentBlockHandler(
        model_name="claude-3-5-sonnet-20241022",
        max_tool_budget=0.10  # $0.10 limit
    )

    processed = handler.process_response(response)

    # Check validation
    if not processed.validate_all_tools():
        print("Tool validation failed:")
        for v in processed.tool_validations:
            if not v.is_valid:
                print(f"  {v.tool_name}: {v.errors}")
        return None

    # Check budget
    total_cost = processed.get_total_tool_cost()
    if total_cost > 0.10:
        print(f"Cost ${total_cost} exceeds budget $0.10")
        return None

    # Execute tools
    results = []
    for tool_call in processed.tool_calls:
        result = {
            "tool": tool_call.tool_name,
            "input": tool_call.raw_input,
            "status": "executed"
        }
        results.append(result)

    return {
        "success": True,
        "tools_executed": len(results),
        "total_cost": total_cost,
        "results": results
    }


# EXAMPLE 6: Extract Financial Insights
# ======================================

def extract_insights(response):
    """Extract and categorize financial insights."""

    handler = FinancialContentBlockHandler(model_name="claude-3-5-sonnet-20241022")
    processed = handler.process_response(response)

    # Get high-confidence insights
    high_conf = processed.get_high_confidence_insights(threshold=0.9)

    # Organize by type
    by_type = {}
    for insight in high_conf:
        itype = insight.insight_type.value
        if itype not in by_type:
            by_type[itype] = []
        by_type[itype].append({
            "content": insight.content,
            "confidence": insight.confidence,
            "source": insight.source,
            "metrics": insight.metrics
        })

    return {
        "total": len(high_conf),
        "by_type": by_type
    }


# EXAMPLE 7: Streaming Response Handler
# ======================================

async def handle_streaming():
    """Handle streaming responses (async)."""

    handler = FinancialContentBlockHandler(model_name="gpt-4-turbo")

    # Simulate streaming chunks
    chunks = [
        {"choices": [{"delta": {"content": "The "}}]},
        {"choices": [{"delta": {"content": "stock "}}]},
        {"choices": [{"delta": {"content": "shows "}}]},
        {"choices": [{"delta": {"content": "strong "}}]},
        {"choices": [{"delta": {"content": "fundamentals."}}]},
    ]

    # In real scenario, accumulate from actual stream
    accumulated = "".join([
        chunk["choices"][0]["delta"].get("content", "")
        for chunk in chunks
    ])

    response = {
        "model": "gpt-4-turbo",
        "choices": [{
            "message": {"content": accumulated}
        }]
    }

    processed = handler.process_response(response)
    return processed


# EXAMPLE 8: Multi-Provider Consensus Analysis
# =============================================

def analyze_with_consensus(ticker: str):
    """Get consensus analysis from all providers."""

    handlers = {
        "claude": FinancialContentBlockHandler(model_name="claude-3-5-sonnet-20241022"),
        "gpt": FinancialContentBlockHandler(model_name="gpt-4-turbo"),
        "gemini": FinancialContentBlockHandler(model_name="gemini-1.5-pro"),
    }

    # Get responses from each (in real scenario)
    responses = {
        "claude": claude_response,
        "gpt": openai_response,
        "gemini": gemini_response,
    }

    all_insights = []
    for provider, handler in handlers.items():
        processed = handler.process_response(responses[provider])
        for insight in processed.combined_insights:
            all_insights.append({
                "provider": provider,
                "type": insight.insight_type.value,
                "content": insight.content,
                "confidence": insight.confidence,
            })

    # Find common themes
    themes = {}
    for insight in all_insights:
        key = f"{insight['type']}"
        if key not in themes:
            themes[key] = []
        themes[key].append(insight["provider"])

    common_themes = {
        theme: providers
        for theme, providers in themes.items()
        if len(set(providers)) > 1
    }

    return {
        "ticker": ticker,
        "providers": len(handlers),
        "total_insights": len(all_insights),
        "common_themes": common_themes,
        "insights": all_insights,
    }


# EXAMPLE 9: Cost Tracking
# =========================

def track_costs(responses):
    """Track costs across multiple requests."""

    handler = FinancialContentBlockHandler(
        model_name="claude-3-5-sonnet-20241022"
    )

    total_cost = 0
    tool_costs = {}

    for response in responses:
        processed = handler.process_response(response)

        cost = processed.get_total_tool_cost()
        total_cost += cost

        for tool_call in processed.tool_calls:
            if tool_call.tool_name not in tool_costs:
                tool_costs[tool_call.tool_name] = []
            # Find cost in validations
            for v in processed.tool_validations:
                if v.tool_name == tool_call.tool_name:
                    tool_costs[tool_call.tool_name].append(v.estimated_cost)

    return {
        "total_cost": total_cost,
        "tool_breakdown": {
            tool: sum(costs) for tool, costs in tool_costs.items()
        },
        "per_request_avg": total_cost / len(responses) if responses else 0,
    }


# EXAMPLE 10: Error Handling
# ==========================

def safe_parse_any_response(response):
    """Safely parse any response with error recovery."""

    handler = FinancialContentBlockHandler(model_name="claude-3-5-sonnet-20241022")

    # safe_parse never throws
    processed = handler.process_response(response)

    # Check for errors
    if processed.parsed_response.parse_errors:
        print(f"Parse warnings: {processed.parsed_response.parse_errors}")
        # Continue with what we have

    # Check tool validation
    invalid_tools = [
        v for v in processed.tool_validations
        if not v.is_valid
    ]
    if invalid_tools:
        print(f"Invalid tools: {[t.tool_name for t in invalid_tools]}")

    # Still usable
    return {
        "model": processed.parsed_response.model,
        "insights": len(processed.combined_insights),
        "usable": True if processed.content_blocks else False,
    }


# QUICK SETUP CHECKLIST
# ====================

"""
1. Copy this file to your project
2. Update imports:
   from src.services.content_blocks_parser import ...
   from src.services.financial_content_handler import ...

3. Pick an example and adapt:
   - Example 1 for single provider
   - Example 4 for multi-provider
   - Example 5 for tool execution
   - Example 8 for consensus

4. Test with your LLM responses

5. Integrate into your agent

6. Enable logging:
   import logging
   logging.basicConfig(level=logging.DEBUG)

7. Monitor costs with LangSmith (optional)
"""


if __name__ == "__main__":
    # Run examples
    print("=" * 70)
    print("UNIFIED CONTENT BLOCKS - EXAMPLES")
    print("=" * 70)

    # Example 1
    print("\n1. Claude Response Parsing:")
    # (run example 1 code here)

    # Example 4
    print("\n2. Provider Comparison:")
    compare_providers()

    # Example 5
    print("\n3. Tool Execution:")
    result = execute_tools_safely(claude_response)
    if result:
        print(f"Success: {result['success']}")
        print(f"Tools executed: {result['tools_executed']}")
        print(f"Cost: ${result['total_cost']}")

    # Example 6
    print("\n4. Financial Insights:")
    insights = extract_insights(claude_response)
    print(f"Total insights: {insights['total']}")
    print(f"By type: {list(insights['by_type'].keys())}")

    # Example 10
    print("\n5. Error Handling:")
    malformed = {"corrupted": "data"}
    result = safe_parse_any_response(malformed)
    print(f"Result: {result}")

    print("\n" + "=" * 70)
    print("Examples completed!")
    print("=" * 70)
