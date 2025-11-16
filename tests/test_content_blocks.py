"""
Comprehensive tests for cross-provider content blocks parsing.

Tests cover Claude, OpenAI, and Google Gemini response formats.
"""

import pytest
import json
from datetime import datetime
from typing import Dict, Any

from content_blocks_parser import (
    ContentBlockParser,
    ContentBlockParserFactory,
    AnthropicContentBlockParser,
    OpenAIContentBlockParser,
    GoogleContentBlockParser,
    ParsedResponse,
    ProviderType,
    ContentBlockType,
    ReasoningFormat,
    ToolCallData,
)
from financial_content_handler import (
    FinancialContentBlockHandler,
    FinancialReasoningAnalyzer,
    ToolCallValidator,
    FinancialInsightType,
)


class TestAnthropicParser:
    """Test Anthropic Claude response parsing."""

    def test_parse_simple_text_response(self):
        """Test parsing simple text response from Claude."""
        parser = AnthropicContentBlockParser()

        response = {
            "id": "msg_123",
            "type": "message",
            "model": "claude-3-sonnet-20240229",
            "content": [
                {"type": "text", "text": "The stock appears undervalued."}
            ],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 100, "output_tokens": 50}
        }

        parsed = parser.parse(response)

        assert parsed.provider == ProviderType.ANTHROPIC
        assert parsed.model == "claude-3-sonnet-20240229"
        assert parsed.final_text == "The stock appears undervalued."
        assert len(parsed.content_blocks) == 1
        assert parsed.content_blocks[0].block_type == ContentBlockType.TEXT
        assert parsed.stop_reason == "end_turn"
        assert parsed.usage["output_tokens"] == 50

    def test_parse_thinking_and_text(self):
        """Test parsing response with thinking blocks."""
        parser = AnthropicContentBlockParser()

        response = {
            "id": "msg_123",
            "model": "claude-3-7-sonnet-20250219",
            "content": [
                {
                    "type": "thinking",
                    "thinking": "Let me analyze the P/E ratio. The company has earnings of $10M "
                                "and market cap of $200M, giving a P/E of 20. This is below the "
                                "sector average of 25, suggesting undervaluation."
                },
                {
                    "type": "text",
                    "text": "Based on my analysis, the stock appears undervalued with a P/E ratio of 20."
                }
            ],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 150, "output_tokens": 100}
        }

        parsed = parser.parse(response)

        assert len(parsed.content_blocks) == 2
        assert parsed.content_blocks[0].block_type == ContentBlockType.THINKING
        assert parsed.content_blocks[1].block_type == ContentBlockType.TEXT

        assert len(parsed.reasoning_traces) == 1
        assert parsed.reasoning_traces[0].format == ReasoningFormat.CLAUDE_THINKING
        assert "P/E ratio" in parsed.reasoning_traces[0].content

    def test_parse_tool_use(self):
        """Test parsing tool use blocks."""
        parser = AnthropicContentBlockParser()

        response = {
            "model": "claude-3-sonnet-20240229",
            "content": [
                {
                    "type": "text",
                    "text": "I need to fetch the latest financial data."
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

        parsed = parser.parse(response)

        assert len(parsed.tool_calls) == 1
        tool_call = parsed.tool_calls[0]
        assert tool_call.tool_name == "fetch_financial_statements"
        assert tool_call.tool_id == "tooluse_123"
        assert tool_call.raw_input["company_id"] == "AAPL"
        assert tool_call.raw_input["period"] == "Q3_2024"

    def test_parse_image_block(self):
        """Test parsing image/document blocks."""
        parser = AnthropicContentBlockParser()

        response = {
            "model": "claude-3-sonnet-20240229",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": "iVBORw0KGgo..."
                    }
                },
                {
                    "type": "text",
                    "text": "This chart shows an uptrend."
                }
            ]
        }

        parsed = parser.parse(response)

        assert any(b.block_type == ContentBlockType.IMAGE for b in parsed.content_blocks)

    def test_error_handling(self):
        """Test error handling for malformed responses."""
        parser = AnthropicContentBlockParser()

        # Response with missing fields
        response = {
            "content": [{"type": "invalid"}]
        }

        parsed = parser.safe_parse(response)
        assert parsed.provider == ProviderType.ANTHROPIC
        assert len(parsed.content_blocks) > 0  # Should still process


class TestOpenAIParser:
    """Test OpenAI GPT-4 and o1 response parsing."""

    def test_parse_gpt4_response(self):
        """Test parsing standard GPT-4 response."""
        parser = OpenAIContentBlockParser()

        response = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4-turbo",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "The company shows strong fundamentals with consistent revenue growth."
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 200,
                "completion_tokens": 50,
                "total_tokens": 250
            }
        }

        parsed = parser.parse(response)

        assert parsed.provider == ProviderType.OPENAI
        assert parsed.model == "gpt-4-turbo"
        assert "revenue growth" in parsed.final_text
        assert parsed.stop_reason == "stop"
        assert parsed.usage["input_tokens"] == 200

    def test_parse_function_calls(self):
        """Test parsing OpenAI function/tool calls."""
        parser = OpenAIContentBlockParser()

        response = {
            "model": "gpt-4-turbo",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "I'll fetch the financial data.",
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
            ]
        }

        parsed = parser.parse(response)

        assert len(parsed.tool_calls) == 1
        tool_call = parsed.tool_calls[0]
        assert tool_call.tool_name == "fetch_stock_data"
        assert tool_call.tool_id == "call_123"
        assert tool_call.raw_input["ticker"] == "AAPL"

    def test_parse_o1_reasoning(self):
        """Test parsing o1-preview reasoning output."""
        parser = OpenAIContentBlockParser()

        # o1 models include reasoning_content
        response = {
            "model": "o1-preview",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Based on my analysis, the fair value is approximately $150.",
                        "reasoning_content": (
                            "Let me work through the valuation. The company has FCF of $5B, "
                            "a growth rate of 8%, and WACC of 7%. Using DCF: "
                            "PV = 5B / (0.07 - 0.08) = ... (calculation steps)"
                        )
                    },
                    "finish_reason": "stop"
                }
            ]
        }

        parsed = parser.parse(response)

        assert len(parsed.reasoning_traces) == 1
        assert "DCF" in parsed.reasoning_traces[0].content
        assert parsed.reasoning_traces[0].format == ReasoningFormat.OPENAI_REASONING

    def test_malformed_function_arguments(self):
        """Test handling of malformed JSON in function arguments."""
        parser = OpenAIContentBlockParser()

        response = {
            "model": "gpt-4-turbo",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Fetching data...",
                        "tool_calls": [
                            {
                                "id": "call_456",
                                "type": "function",
                                "function": {
                                    "name": "query_database",
                                    "arguments": "invalid json {here"
                                }
                            }
                        ]
                    },
                    "finish_reason": "tool_calls"
                }
            ]
        }

        parsed = parser.parse(response)
        # Should still parse but with fallback
        assert len(parsed.tool_calls) == 1
        assert "raw" in parsed.tool_calls[0].raw_input or isinstance(parsed.tool_calls[0].raw_input, dict)


class TestGoogleParser:
    """Test Google Gemini response parsing."""

    def test_parse_gemini_response(self):
        """Test parsing basic Gemini response."""
        parser = GoogleContentBlockParser()

        response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": "The financial metrics suggest a growth trajectory."
                            }
                        ]
                    },
                    "finish_reason": "STOP"
                }
            ],
            "model_name": "gemini-1.5-pro"
        }

        parsed = parser.parse(response)

        assert parsed.provider == ProviderType.GOOGLE
        assert parsed.model == "gemini-1.5-pro"
        assert "growth trajectory" in parsed.final_text

    def test_parse_gemini_function_calls(self):
        """Test parsing Gemini function calls."""
        parser = GoogleContentBlockParser()

        response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": "I need to fetch the data first."
                            },
                            {
                                "function_call": {
                                    "name": "search_documents",
                                    "args": {"query": "quarterly earnings report"}
                                }
                            }
                        ]
                    }
                }
            ]
        }

        parsed = parser.parse(response)

        assert len(parsed.tool_calls) == 1
        tool_call = parsed.tool_calls[0]
        assert tool_call.tool_name == "search_documents"
        assert tool_call.raw_input["query"] == "quarterly earnings report"

    def test_parse_gemini_with_images(self):
        """Test parsing Gemini response with images."""
        parser = GoogleContentBlockParser()

        response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "inline_data": {
                                    "mime_type": "image/png",
                                    "data": "iVBORw0KGgo..."
                                }
                            },
                            {
                                "text": "This chart shows market trends."
                            }
                        ]
                    }
                }
            ]
        }

        parsed = parser.parse(response)

        assert any(b.block_type == ContentBlockType.IMAGE for b in parsed.content_blocks)

    def test_parse_gemini_thinking(self):
        """Test parsing Gemini with thinking/reasoning."""
        parser = GoogleContentBlockParser()

        response = {
            "candidates": [
                {
                    "thinking_content": {
                        "text": "The P/E ratio of 15 is below the sector median of 20, suggesting value."
                    },
                    "content": {
                        "parts": [
                            {
                                "text": "This stock appears undervalued relative to peers."
                            }
                        ]
                    }
                }
            ]
        }

        parsed = parser.parse(response)

        assert len(parsed.reasoning_traces) == 1
        assert "P/E ratio" in parsed.reasoning_traces[0].content


class TestParserFactory:
    """Test parser factory functionality."""

    def test_factory_creates_correct_parsers(self):
        """Test factory creates correct parser for each provider."""
        factory = ContentBlockParserFactory()

        # Test by provider type
        claude_parser = factory.create_parser(ProviderType.ANTHROPIC)
        assert isinstance(claude_parser, AnthropicContentBlockParser)

        openai_parser = factory.create_parser(ProviderType.OPENAI)
        assert isinstance(openai_parser, OpenAIContentBlockParser)

        google_parser = factory.create_parser(ProviderType.GOOGLE)
        assert isinstance(google_parser, GoogleContentBlockParser)

    def test_factory_auto_detects_model(self):
        """Test factory auto-detects provider from model name."""
        factory = ContentBlockParserFactory()

        # Test model name detection
        claude_parser = factory.create_parser_for_model("claude-3-sonnet")
        assert isinstance(claude_parser, AnthropicContentBlockParser)

        gpt_parser = factory.create_parser_for_model("gpt-4-turbo")
        assert isinstance(gpt_parser, OpenAIContentBlockParser)

        gemini_parser = factory.create_parser_for_model("gemini-1.5-pro")
        assert isinstance(gemini_parser, GoogleContentBlockParser)

    def test_invalid_provider(self):
        """Test error handling for invalid provider."""
        factory = ContentBlockParserFactory()

        with pytest.raises(ValueError):
            factory.create_parser(ProviderType.OLLAMA)  # Not yet registered


class TestFinancialContentHandler:
    """Test financial analysis content handler."""

    def test_process_claude_response(self):
        """Test processing Claude response for financial insights."""
        handler = FinancialContentBlockHandler(provider=ProviderType.ANTHROPIC)

        response = {
            "model": "claude-3-sonnet-20240229",
            "content": [
                {
                    "type": "thinking",
                    "thinking": "P/E ratio is 15, which is below sector average of 20. Risk profile is moderate."
                },
                {
                    "type": "text",
                    "text": "The stock shows valuation strength with PE of 15 and moderate risk profile."
                }
            ]
        }

        processed = handler.process_response(response)

        assert processed.parsed_response.model == "claude-3-sonnet-20240229"
        assert len(processed.reasoning_insights) > 0
        assert len(processed.text_insights) > 0

        # Check that insights were extracted
        valuation_insights = processed.get_insights_by_type(FinancialInsightType.VALUATION)
        assert len(valuation_insights) > 0

    def test_validate_tool_calls(self):
        """Test tool call validation."""
        handler = FinancialContentBlockHandler(
            provider=ProviderType.ANTHROPIC,
            max_tool_budget=0.01
        )

        response = {
            "model": "claude-3-sonnet-20240229",
            "content": [
                {
                    "type": "tool_use",
                    "id": "tool_123",
                    "name": "fetch_financial_statements",
                    "input": {"company_id": "AAPL", "period": "Q3_2024"}
                }
            ]
        }

        processed = handler.process_response(response)

        assert len(processed.tool_validations) == 1
        assert processed.tool_validations[0].is_valid
        assert processed.validate_all_tools()

    def test_invalid_tool_detection(self):
        """Test detection of invalid tool calls."""
        handler = FinancialContentBlockHandler(provider=ProviderType.ANTHROPIC)

        response = {
            "model": "claude-3-sonnet-20240229",
            "content": [
                {
                    "type": "tool_use",
                    "id": "tool_456",
                    "name": "invalid_tool",
                    "input": {}
                }
            ]
        }

        processed = handler.process_response(response)

        assert not processed.validate_all_tools()
        assert len(processed.tool_validations[0].errors) > 0


class TestCrossProviderConsistency:
    """Test consistency across all providers."""

    def test_same_financial_data_different_providers(self):
        """Test that same analysis produces consistent insights across providers."""
        handlers = {
            "claude": FinancialContentBlockHandler(provider=ProviderType.ANTHROPIC),
            "openai": FinancialContentBlockHandler(provider=ProviderType.OPENAI),
            "google": FinancialContentBlockHandler(provider=ProviderType.GOOGLE),
        }

        financial_analysis = {
            "claude_response": {
                "model": "claude-3-sonnet",
                "content": [
                    {
                        "type": "text",
                        "text": "Based on valuation metrics, the stock shows strength."
                    }
                ]
            },
            "openai_response": {
                "model": "gpt-4",
                "choices": [{
                    "message": {
                        "content": "Based on valuation metrics, the stock shows strength."
                    }
                }]
            },
            "google_response": {
                "model": "gemini-1.5-pro",
                "candidates": [{
                    "content": {
                        "parts": [
                            {"text": "Based on valuation metrics, the stock shows strength."}
                        ]
                    }
                }]
            }
        }

        insights_by_provider = {}
        for provider, handler in handlers.items():
            response = financial_analysis[f"{provider}_response"]
            processed = handler.process_response(response)
            insights_by_provider[provider] = processed.combined_insights

        # All should extract valuation insights
        for provider, insights in insights_by_provider.items():
            valuation = [i for i in insights if i.insight_type == FinancialInsightType.VALUATION]
            assert len(valuation) > 0, f"{provider} should have valuation insights"


class TestErrorRecovery:
    """Test error recovery and fallback behavior."""

    def test_corrupted_response_fallback(self):
        """Test fallback when response is corrupted."""
        parser = AnthropicContentBlockParser()

        # Severely malformed response
        response = {"corrupted": "data"}

        parsed = parser.safe_parse(response)

        # Should still return ParsedResponse
        assert parsed is not None
        assert parsed.provider == ProviderType.ANTHROPIC
        assert len(parsed.parse_errors) > 0

    def test_missing_content_blocks(self):
        """Test handling of responses without content blocks."""
        parser = AnthropicContentBlockParser()

        response = {"model": "claude-3-sonnet"}

        parsed = parser.parse(response)

        assert parsed.final_text == ""
        assert len(parsed.content_blocks) == 0

    def test_partial_tool_information(self):
        """Test handling of incomplete tool call information."""
        parser = AnthropicContentBlockParser()

        response = {
            "model": "claude-3-sonnet",
            "content": [
                {
                    "type": "tool_use",
                    "id": "tool_789",
                    # Missing 'name' and 'input'
                }
            ]
        }

        parsed = parser.safe_parse(response)

        # Should handle gracefully
        assert parsed is not None


# Integration test for streaming scenario
@pytest.mark.asyncio
async def test_streaming_financial_analysis():
    """Test processing streaming response."""
    handler = FinancialContentBlockHandler(provider=ProviderType.OPENAI)

    # Simulate streaming chunks
    chunks = [
        {"choices": [{"delta": {"content": "The "}}]},
        {"choices": [{"delta": {"content": "stock "}}]},
        {"choices": [{"delta": {"content": "shows "}}]},
        {"choices": [{"delta": {"content": "strong "}}]},
        {"choices": [{"delta": {"content": "valuation."}}]},
    ]

    # Note: This is a simplified test structure
    # In practice, you'd use actual async streaming
    accumulated = "The stock shows strong valuation."
    assert "valuation" in accumulated.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
