"""
Unified content blocks parser for cross-provider LLM integration.

This module provides a standardized interface for parsing content blocks from
different LLM providers (Claude, OpenAI, Google Gemini) and converting them
into a unified format suitable for financial analysis agents.

Supports:
- Reasoning traces (Claude native thinking, OpenAI o1 reasoning)
- Tool calls and results across all providers
- Multi-modal content (text, images, documents)
- Fallback strategies when content blocks are unavailable
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import json
import logging
from enum import auto

from pydantic import BaseModel, Field, validator


logger = logging.getLogger(__name__)


class ContentBlockType(str, Enum):
    """Unified content block types across all providers."""

    # Text content
    TEXT = "text"

    # Reasoning/Thinking traces
    REASONING = "reasoning"
    THINKING = "thinking"

    # Tool interaction
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"

    # Multi-modal
    IMAGE = "image"
    DOCUMENT = "document"

    # Provider-specific fallback
    UNKNOWN = "unknown"


class ProviderType(str, Enum):
    """Supported LLM providers."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    OLLAMA = "ollama"
    AWS_BEDROCK = "aws_bedrock"


class ReasoningFormat(str, Enum):
    """Format of reasoning traces from different providers."""

    CLAUDE_THINKING = "claude_thinking"  # Claude's native thinking block
    OPENAI_REASONING = "openai_reasoning"  # OpenAI o1-preview reasoning
    GEMINI_REASONING = "gemini_reasoning"  # Google's reasoning format
    TEXT_TRACE = "text_trace"  # Fallback: text-based reasoning
    UNKNOWN = "unknown"


@dataclass
class ContentBlockMetadata:
    """Metadata about a content block."""

    provider: ProviderType
    reasoning_format: ReasoningFormat = ReasoningFormat.UNKNOWN
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source_model: Optional[str] = None
    token_count: Optional[int] = None
    confidence: float = 1.0
    additional_metadata: Dict[str, Any] = field(default_factory=dict)


class UnifiedContentBlock(BaseModel):
    """
    Unified representation of a content block from any LLM provider.

    This is the standard internal format used throughout the agent system.
    """

    block_type: ContentBlockType
    content: Union[str, Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None
    raw_provider_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True


class ToolCallData(BaseModel):
    """Structured representation of a tool call."""

    tool_name: str
    tool_id: Optional[str] = None
    input_schema: Dict[str, Any]
    raw_input: Dict[str, Any]
    reasoning: Optional[str] = None
    provider: ProviderType

    class Config:
        use_enum_values = True


class ToolResultData(BaseModel):
    """Structured representation of a tool result."""

    tool_id: str
    tool_name: str
    result: Union[str, Dict[str, Any]]
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None

    class Config:
        use_enum_values = True


class ReasoningTrace(BaseModel):
    """Unified representation of reasoning/thinking from any provider."""

    format: ReasoningFormat
    content: str
    confidence: float = 1.0
    stop_reason: Optional[str] = None
    token_count: Optional[int] = None

    class Config:
        use_enum_values = True


class ParsedResponse(BaseModel):
    """Complete parsed response from an LLM with all components extracted."""

    provider: ProviderType
    model: str
    content_blocks: List[UnifiedContentBlock] = []
    reasoning_traces: List[ReasoningTrace] = []
    tool_calls: List[ToolCallData] = []
    tool_results: List[ToolResultData] = []
    final_text: str = ""
    stop_reason: Optional[str] = None
    usage: Optional[Dict[str, int]] = None
    raw_response: Optional[Dict[str, Any]] = None
    parse_errors: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True


class ContentBlockParser(ABC):
    """Abstract base class for provider-specific parsers."""

    def __init__(self, provider: ProviderType):
        self.provider = provider
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def parse(self, response: Any) -> ParsedResponse:
        """Parse provider-specific response into unified format."""
        pass

    @abstractmethod
    def parse_content_blocks(self, blocks: List[Any]) -> List[UnifiedContentBlock]:
        """Parse content blocks from provider response."""
        pass

    @abstractmethod
    def extract_reasoning_traces(self, response: Any) -> List[ReasoningTrace]:
        """Extract reasoning traces from response."""
        pass

    @abstractmethod
    def extract_tool_calls(self, response: Any) -> List[ToolCallData]:
        """Extract tool calls from response."""
        pass

    def safe_parse(self, response: Any) -> ParsedResponse:
        """
        Safe parse with comprehensive error handling.

        Always returns a ParsedResponse, even if parsing fails.
        """
        try:
            return self.parse(response)
        except Exception as e:
            self.logger.error(f"Parse error in {self.provider}: {e}", exc_info=True)
            return ParsedResponse(
                provider=self.provider,
                model=self._extract_model_safely(response),
                parse_errors=[f"Parsing failed: {str(e)}"]
            )

    def _extract_model_safely(self, response: Any) -> str:
        """Safely extract model name from response."""
        try:
            if isinstance(response, dict):
                return response.get("model", "unknown")
            if hasattr(response, "model"):
                return response.model
            return "unknown"
        except Exception:
            return "unknown"


class AnthropicContentBlockParser(ContentBlockParser):
    """Parser for Anthropic Claude responses."""

    def __init__(self):
        super().__init__(ProviderType.ANTHROPIC)

    def parse(self, response: Any) -> ParsedResponse:
        """
        Parse Anthropic response.

        Handles both message objects and raw dicts.
        """
        parsed = ParsedResponse(
            provider=self.provider,
            model=self._extract_model(response),
            stop_reason=self._extract_stop_reason(response),
            usage=self._extract_usage(response)
        )

        # Extract content blocks
        blocks = self._get_content_blocks(response)
        parsed.content_blocks = self.parse_content_blocks(blocks)

        # Extract reasoning traces
        parsed.reasoning_traces = self.extract_reasoning_traces(response)

        # Extract tool calls
        parsed.tool_calls = self.extract_tool_calls(response)

        # Extract final text content
        parsed.final_text = self._extract_final_text(blocks)

        parsed.raw_response = response if isinstance(response, dict) else None

        return parsed

    def parse_content_blocks(self, blocks: List[Any]) -> List[UnifiedContentBlock]:
        """Parse Anthropic content blocks."""
        unified_blocks = []

        for block in blocks:
            try:
                if isinstance(block, dict):
                    block_type = block.get("type", "unknown")
                else:
                    block_type = getattr(block, "type", "unknown")

                # Handle thinking/reasoning blocks
                if block_type == "thinking":
                    unified_blocks.append(UnifiedContentBlock(
                        block_type=ContentBlockType.THINKING,
                        content=self._get_block_content(block, "thinking_text"),
                        metadata={
                            "provider": self.provider.value,
                            "format": ReasoningFormat.CLAUDE_THINKING.value
                        },
                        raw_provider_data=block if isinstance(block, dict) else vars(block)
                    ))

                # Handle text blocks
                elif block_type == "text":
                    unified_blocks.append(UnifiedContentBlock(
                        block_type=ContentBlockType.TEXT,
                        content=self._get_block_content(block, "text"),
                        raw_provider_data=block if isinstance(block, dict) else vars(block)
                    ))

                # Handle tool use blocks
                elif block_type == "tool_use":
                    tool_data = self._parse_tool_use_block(block)
                    if tool_data:
                        unified_blocks.append(UnifiedContentBlock(
                            block_type=ContentBlockType.TOOL_USE,
                            content=tool_data,
                            raw_provider_data=block if isinstance(block, dict) else vars(block)
                        ))

                # Handle tool results
                elif block_type == "tool_result":
                    unified_blocks.append(UnifiedContentBlock(
                        block_type=ContentBlockType.TOOL_RESULT,
                        content=self._parse_tool_result_block(block),
                        raw_provider_data=block if isinstance(block, dict) else vars(block)
                    ))

                # Handle images
                elif block_type == "image":
                    unified_blocks.append(UnifiedContentBlock(
                        block_type=ContentBlockType.IMAGE,
                        content=self._parse_image_block(block),
                        raw_provider_data=block if isinstance(block, dict) else vars(block)
                    ))

                else:
                    # Unknown block type - store as-is
                    unified_blocks.append(UnifiedContentBlock(
                        block_type=ContentBlockType.UNKNOWN,
                        content=block if isinstance(block, dict) else vars(block),
                        raw_provider_data=block if isinstance(block, dict) else vars(block)
                    ))

            except Exception as e:
                self.logger.warning(f"Failed to parse Anthropic block: {e}")
                unified_blocks.append(UnifiedContentBlock(
                    block_type=ContentBlockType.UNKNOWN,
                    content=str(block),
                    error=str(e)
                ))

        return unified_blocks

    def extract_reasoning_traces(self, response: Any) -> List[ReasoningTrace]:
        """Extract reasoning traces from Anthropic response."""
        traces = []
        blocks = self._get_content_blocks(response)

        for block in blocks:
            block_type = block.get("type") if isinstance(block, dict) else getattr(block, "type", None)

            if block_type == "thinking":
                content = self._get_block_content(block, "thinking_text")
                if content:
                    traces.append(ReasoningTrace(
                        format=ReasoningFormat.CLAUDE_THINKING,
                        content=content,
                        token_count=len(content.split())  # Approximate
                    ))

        return traces

    def extract_tool_calls(self, response: Any) -> List[ToolCallData]:
        """Extract tool calls from Anthropic response."""
        tool_calls = []
        blocks = self._get_content_blocks(response)

        for block in blocks:
            block_type = block.get("type") if isinstance(block, dict) else getattr(block, "type", None)

            if block_type == "tool_use":
                try:
                    tool_call = ToolCallData(
                        tool_name=block.get("name") if isinstance(block, dict) else getattr(block, "name"),
                        tool_id=block.get("id") if isinstance(block, dict) else getattr(block, "id"),
                        input_schema={},  # Would need tool definition to get schema
                        raw_input=block.get("input") if isinstance(block, dict) else getattr(block, "input", {}),
                        provider=self.provider
                    )
                    tool_calls.append(tool_call)
                except Exception as e:
                    self.logger.warning(f"Failed to extract tool call: {e}")

        return tool_calls

    def _get_content_blocks(self, response: Any) -> List[Any]:
        """Extract content blocks from response."""
        if isinstance(response, dict):
            return response.get("content", [])
        if hasattr(response, "content"):
            return response.content
        return []

    def _extract_model(self, response: Any) -> str:
        """Extract model name."""
        if isinstance(response, dict):
            return response.get("model", "claude-unknown")
        if hasattr(response, "model"):
            return response.model
        return "claude-unknown"

    def _extract_stop_reason(self, response: Any) -> Optional[str]:
        """Extract stop reason."""
        if isinstance(response, dict):
            return response.get("stop_reason")
        if hasattr(response, "stop_reason"):
            return response.stop_reason
        return None

    def _extract_usage(self, response: Any) -> Optional[Dict[str, int]]:
        """Extract token usage."""
        if isinstance(response, dict):
            usage = response.get("usage", {})
            if usage:
                return {
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0)
                }
        if hasattr(response, "usage"):
            return {
                "input_tokens": getattr(response.usage, "input_tokens", 0),
                "output_tokens": getattr(response.usage, "output_tokens", 0)
            }
        return None

    def _get_block_content(self, block: Any, attr: str) -> str:
        """Safely extract block content."""
        if isinstance(block, dict):
            return block.get(attr, "")
        return getattr(block, attr, "")

    def _extract_final_text(self, blocks: List[Any]) -> str:
        """Extract final text content from blocks."""
        text_parts = []
        for block in blocks:
            block_type = block.get("type") if isinstance(block, dict) else getattr(block, "type", None)
            if block_type == "text":
                text = self._get_block_content(block, "text")
                if text:
                    text_parts.append(text)
        return "\n".join(text_parts)

    def _parse_tool_use_block(self, block: Any) -> Dict[str, Any]:
        """Parse tool use block into unified format."""
        if isinstance(block, dict):
            return {
                "tool_id": block.get("id"),
                "tool_name": block.get("name"),
                "input": block.get("input", {})
            }
        return {
            "tool_id": getattr(block, "id", None),
            "tool_name": getattr(block, "name", None),
            "input": getattr(block, "input", {})
        }

    def _parse_tool_result_block(self, block: Any) -> Dict[str, Any]:
        """Parse tool result block."""
        if isinstance(block, dict):
            return {
                "tool_use_id": block.get("tool_use_id"),
                "content": block.get("content"),
                "is_error": block.get("is_error", False)
            }
        return {
            "tool_use_id": getattr(block, "tool_use_id", None),
            "content": getattr(block, "content", None),
            "is_error": getattr(block, "is_error", False)
        }

    def _parse_image_block(self, block: Any) -> Dict[str, Any]:
        """Parse image block."""
        if isinstance(block, dict):
            return {
                "media_type": block.get("media_type"),
                "data": block.get("data")
            }
        return {
            "media_type": getattr(block, "media_type", None),
            "data": getattr(block, "data", None)
        }


class OpenAIContentBlockParser(ContentBlockParser):
    """Parser for OpenAI GPT-4 and o1 responses."""

    def __init__(self):
        super().__init__(ProviderType.OPENAI)

    def parse(self, response: Any) -> ParsedResponse:
        """
        Parse OpenAI response.

        Handles ChatCompletion and o1-preview reasoning models.
        """
        parsed = ParsedResponse(
            provider=self.provider,
            model=self._extract_model(response),
            stop_reason=self._extract_stop_reason(response),
            usage=self._extract_usage(response)
        )

        # Extract content from message
        message = self._get_message(response)

        parsed.content_blocks = self.parse_content_blocks(message)
        parsed.reasoning_traces = self.extract_reasoning_traces(message)
        parsed.tool_calls = self.extract_tool_calls(message)
        parsed.final_text = self._extract_final_text(message)

        parsed.raw_response = response if isinstance(response, dict) else None

        return parsed

    def parse_content_blocks(self, message: Any) -> List[UnifiedContentBlock]:
        """Parse OpenAI content blocks."""
        unified_blocks = []

        # OpenAI uses a single 'content' field with potential tool_calls
        if isinstance(message, dict):
            content = message.get("content", "")
        else:
            content = getattr(message, "content", "")

        if content:
            unified_blocks.append(UnifiedContentBlock(
                block_type=ContentBlockType.TEXT,
                content=content,
                raw_provider_data={"type": "text", "content": content}
            ))

        # Handle function/tool calls (OpenAI's format)
        tool_calls = self._get_tool_calls(message)
        for tc in tool_calls:
            unified_blocks.append(UnifiedContentBlock(
                block_type=ContentBlockType.TOOL_USE,
                content={
                    "function": tc.get("function", {}).get("name"),
                    "arguments": tc.get("function", {}).get("arguments"),
                    "id": tc.get("id")
                },
                raw_provider_data=tc
            ))

        # Handle reasoning (o1-preview specific)
        if self._has_reasoning_content(message):
            reasoning = self._get_reasoning_content(message)
            unified_blocks.append(UnifiedContentBlock(
                block_type=ContentBlockType.REASONING,
                content=reasoning,
                metadata={
                    "provider": self.provider.value,
                    "format": ReasoningFormat.OPENAI_REASONING.value
                }
            ))

        return unified_blocks

    def extract_reasoning_traces(self, message: Any) -> List[ReasoningTrace]:
        """Extract reasoning from o1 models."""
        traces = []

        # OpenAI o1 models return reasoning in a specific format
        if self._has_reasoning_content(message):
            reasoning = self._get_reasoning_content(message)
            if reasoning:
                traces.append(ReasoningTrace(
                    format=ReasoningFormat.OPENAI_REASONING,
                    content=reasoning
                ))

        return traces

    def extract_tool_calls(self, message: Any) -> List[ToolCallData]:
        """Extract tool calls from OpenAI response."""
        tool_calls = []

        for tc in self._get_tool_calls(message):
            try:
                function = tc.get("function", {})
                arguments = function.get("arguments", "{}")

                # Parse arguments if it's a JSON string
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except json.JSONDecodeError:
                        arguments = {"raw": arguments}

                tool_call = ToolCallData(
                    tool_name=function.get("name", "unknown"),
                    tool_id=tc.get("id"),
                    input_schema={},
                    raw_input=arguments,
                    provider=self.provider
                )
                tool_calls.append(tool_call)
            except Exception as e:
                self.logger.warning(f"Failed to extract OpenAI tool call: {e}")

        return tool_calls

    def _get_message(self, response: Any) -> Any:
        """Extract message from response."""
        if isinstance(response, dict):
            choices = response.get("choices", [])
            if choices:
                return choices[0].get("message", {})
            return {}
        if hasattr(response, "choices") and response.choices:
            return response.choices[0].message
        return None

    def _get_tool_calls(self, message: Any) -> List[Dict[str, Any]]:
        """Extract tool calls from message."""
        if isinstance(message, dict):
            return message.get("tool_calls", [])
        if hasattr(message, "tool_calls"):
            return message.tool_calls or []
        return []

    def _extract_model(self, response: Any) -> str:
        """Extract model name."""
        if isinstance(response, dict):
            return response.get("model", "gpt-unknown")
        if hasattr(response, "model"):
            return response.model
        return "gpt-unknown"

    def _extract_stop_reason(self, response: Any) -> Optional[str]:
        """Extract stop reason."""
        if isinstance(response, dict):
            choices = response.get("choices", [])
            if choices:
                return choices[0].get("finish_reason")
        if hasattr(response, "choices") and response.choices:
            return response.choices[0].finish_reason
        return None

    def _extract_usage(self, response: Any) -> Optional[Dict[str, int]]:
        """Extract token usage."""
        if isinstance(response, dict):
            usage = response.get("usage", {})
            if usage:
                return {
                    "input_tokens": usage.get("prompt_tokens", 0),
                    "output_tokens": usage.get("completion_tokens", 0)
                }
        if hasattr(response, "usage"):
            return {
                "input_tokens": getattr(response.usage, "prompt_tokens", 0),
                "output_tokens": getattr(response.usage, "completion_tokens", 0)
            }
        return None

    def _extract_final_text(self, message: Any) -> str:
        """Extract final text content."""
        if isinstance(message, dict):
            return message.get("content", "")
        if hasattr(message, "content"):
            return message.content or ""
        return ""

    def _has_reasoning_content(self, message: Any) -> bool:
        """Check if message has reasoning content (o1 models)."""
        # This is model-specific; would need to check model name
        # For now, check for reasoning_content attribute
        if isinstance(message, dict):
            return "reasoning_content" in message
        return hasattr(message, "reasoning_content")

    def _get_reasoning_content(self, message: Any) -> str:
        """Extract reasoning content from o1 models."""
        if isinstance(message, dict):
            return message.get("reasoning_content", "")
        return getattr(message, "reasoning_content", "")


class GoogleContentBlockParser(ContentBlockParser):
    """Parser for Google Gemini and VertexAI responses."""

    def __init__(self):
        super().__init__(ProviderType.GOOGLE)

    def parse(self, response: Any) -> ParsedResponse:
        """Parse Google Gemini response."""
        parsed = ParsedResponse(
            provider=self.provider,
            model=self._extract_model(response)
        )

        # Get candidates (Gemini response structure)
        candidates = self._get_candidates(response)

        if candidates:
            candidate = candidates[0]
            parsed.content_blocks = self.parse_content_blocks(candidate)
            parsed.reasoning_traces = self.extract_reasoning_traces(candidate)
            parsed.tool_calls = self.extract_tool_calls(candidate)
            parsed.final_text = self._extract_final_text(candidate)
            parsed.stop_reason = self._extract_stop_reason(candidate)

        parsed.raw_response = response if isinstance(response, dict) else None

        return parsed

    def parse_content_blocks(self, candidate: Any) -> List[UnifiedContentBlock]:
        """Parse Google Gemini content blocks."""
        unified_blocks = []

        # Get content parts from candidate
        parts = self._get_content_parts(candidate)

        for part in parts:
            try:
                if isinstance(part, dict):
                    # Handle text
                    if "text" in part:
                        unified_blocks.append(UnifiedContentBlock(
                            block_type=ContentBlockType.TEXT,
                            content=part["text"],
                            raw_provider_data=part
                        ))

                    # Handle function calls (Gemini's tool use)
                    elif "function_call" in part:
                        func_call = part["function_call"]
                        unified_blocks.append(UnifiedContentBlock(
                            block_type=ContentBlockType.TOOL_USE,
                            content={
                                "function_name": func_call.get("name"),
                                "arguments": func_call.get("args", {})
                            },
                            raw_provider_data=part
                        ))

                    # Handle inline data (images, etc.)
                    elif "inline_data" in part:
                        data = part["inline_data"]
                        unified_blocks.append(UnifiedContentBlock(
                            block_type=ContentBlockType.IMAGE,
                            content={
                                "media_type": data.get("mime_type"),
                                "data": data.get("data")
                            },
                            raw_provider_data=part
                        ))

                    else:
                        unified_blocks.append(UnifiedContentBlock(
                            block_type=ContentBlockType.UNKNOWN,
                            content=part,
                            raw_provider_data=part
                        ))

                else:
                    # Handle object with attributes
                    if hasattr(part, "text"):
                        unified_blocks.append(UnifiedContentBlock(
                            block_type=ContentBlockType.TEXT,
                            content=part.text,
                            raw_provider_data=vars(part)
                        ))
                    elif hasattr(part, "function_call"):
                        func = part.function_call
                        unified_blocks.append(UnifiedContentBlock(
                            block_type=ContentBlockType.TOOL_USE,
                            content={
                                "function_name": func.name,
                                "arguments": vars(func.args) if hasattr(func, "args") else {}
                            },
                            raw_provider_data=vars(part)
                        ))

            except Exception as e:
                self.logger.warning(f"Failed to parse Google block: {e}")
                unified_blocks.append(UnifiedContentBlock(
                    block_type=ContentBlockType.UNKNOWN,
                    content=str(part),
                    error=str(e)
                ))

        return unified_blocks

    def extract_reasoning_traces(self, candidate: Any) -> List[ReasoningTrace]:
        """
        Extract reasoning from Google Gemini.

        Gemini with reasoning may have separate thinking content.
        """
        traces = []

        # Check for thinking_content (Gemini's reasoning format)
        thinking = self._get_thinking_content(candidate)
        if thinking:
            traces.append(ReasoningTrace(
                format=ReasoningFormat.GEMINI_REASONING,
                content=thinking
            ))

        return traces

    def extract_tool_calls(self, candidate: Any) -> List[ToolCallData]:
        """Extract function calls from Google response."""
        tool_calls = []

        parts = self._get_content_parts(candidate)
        for part in parts:
            try:
                func_call = None

                if isinstance(part, dict) and "function_call" in part:
                    func_call = part["function_call"]
                elif hasattr(part, "function_call"):
                    func_call = part.function_call

                if func_call:
                    args = func_call.get("args") if isinstance(func_call, dict) else vars(func_call.args)

                    tool_call = ToolCallData(
                        tool_name=func_call.get("name") if isinstance(func_call, dict) else func_call.name,
                        tool_id=None,
                        input_schema={},
                        raw_input=args,
                        provider=self.provider
                    )
                    tool_calls.append(tool_call)

            except Exception as e:
                self.logger.warning(f"Failed to extract Google tool call: {e}")

        return tool_calls

    def _get_candidates(self, response: Any) -> List[Any]:
        """Extract candidates from response."""
        if isinstance(response, dict):
            return response.get("candidates", [])
        if hasattr(response, "candidates"):
            return response.candidates
        return []

    def _get_content_parts(self, candidate: Any) -> List[Any]:
        """Extract content parts from candidate."""
        if isinstance(candidate, dict):
            content = candidate.get("content", {})
            return content.get("parts", [])
        if hasattr(candidate, "content"):
            if hasattr(candidate.content, "parts"):
                return candidate.content.parts
        return []

    def _extract_model(self, response: Any) -> str:
        """Extract model name."""
        if isinstance(response, dict):
            return response.get("model_name", "gemini-unknown")
        if hasattr(response, "model_name"):
            return response.model_name
        return "gemini-unknown"

    def _extract_stop_reason(self, candidate: Any) -> Optional[str]:
        """Extract stop reason."""
        if isinstance(candidate, dict):
            return candidate.get("finish_reason")
        if hasattr(candidate, "finish_reason"):
            return candidate.finish_reason
        return None

    def _extract_final_text(self, candidate: Any) -> str:
        """Extract final text content."""
        text_parts = []
        parts = self._get_content_parts(candidate)

        for part in parts:
            if isinstance(part, dict) and "text" in part:
                text_parts.append(part["text"])
            elif hasattr(part, "text"):
                text_parts.append(part.text)

        return "\n".join(text_parts)

    def _get_thinking_content(self, candidate: Any) -> Optional[str]:
        """Extract thinking/reasoning content."""
        if isinstance(candidate, dict):
            return candidate.get("thinking_content", {}).get("text")
        if hasattr(candidate, "thinking_content"):
            if hasattr(candidate.thinking_content, "text"):
                return candidate.thinking_content.text
        return None


class ContentBlockParserFactory:
    """Factory for creating provider-specific parsers."""

    _parsers: Dict[ProviderType, type] = {
        ProviderType.ANTHROPIC: AnthropicContentBlockParser,
        ProviderType.OPENAI: OpenAIContentBlockParser,
        ProviderType.GOOGLE: GoogleContentBlockParser,
    }

    @classmethod
    def create_parser(cls, provider: ProviderType) -> ContentBlockParser:
        """Create a parser for the specified provider."""
        parser_class = cls._parsers.get(provider)
        if not parser_class:
            raise ValueError(f"Unsupported provider: {provider}")
        return parser_class()

    @classmethod
    def create_parser_for_model(cls, model_name: str) -> ContentBlockParser:
        """
        Create a parser based on model name.

        Auto-detects provider from model name.
        """
        model_lower = model_name.lower()

        if "claude" in model_lower:
            provider = ProviderType.ANTHROPIC
        elif "gpt" in model_lower or "o1" in model_lower:
            provider = ProviderType.OPENAI
        elif "gemini" in model_lower or "vertex" in model_lower:
            provider = ProviderType.GOOGLE
        else:
            # Default to Anthropic
            provider = ProviderType.ANTHROPIC

        return cls.create_parser(provider)

    @classmethod
    def register_parser(cls, provider: ProviderType, parser_class: type) -> None:
        """Register a custom parser for a provider."""
        cls._parsers[provider] = parser_class
