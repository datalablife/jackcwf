"""
Financial analysis-specific content blocks handler.

Integrates parsed content blocks into financial agent workflows with
reasoning trace analysis, tool call validation, and financial insights extraction.
"""

import asyncio
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import json

from pydantic import BaseModel, Field

from content_blocks_parser import (
    ContentBlockParser,
    ContentBlockParserFactory,
    ParsedResponse,
    ProviderType,
    ContentBlockType,
    ReasoningFormat,
    ToolCallData,
    UnifiedContentBlock,
)


logger = logging.getLogger(__name__)


class FinancialInsightType(str, Enum):
    """Types of financial insights extracted."""

    VALUATION = "valuation"
    RISK = "risk"
    PERFORMANCE = "performance"
    FORECAST = "forecast"
    ANOMALY = "anomaly"
    UNKNOWN = "unknown"


@dataclass
class FinancialInsight:
    """Extracted financial insight from reasoning."""

    insight_type: FinancialInsightType
    content: str
    confidence: float
    source: str  # "reasoning" or "text"
    metrics: Optional[Dict[str, float]] = None


@dataclass
class ToolValidationResult:
    """Result of tool call validation."""

    is_valid: bool
    tool_name: str
    errors: List[str] = None
    warnings: List[str] = None
    estimated_cost: Optional[float] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class FinancialReasoningAnalyzer:
    """Analyzes reasoning traces for financial insights."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

        # Keywords for detecting financial insights
        self.insight_keywords = {
            FinancialInsightType.VALUATION: ["valuation", "fair value", "price target", "pe ratio", "intrinsic"],
            FinancialInsightType.RISK: ["risk", "volatility", "beta", "correlation", "drawdown"],
            FinancialInsightType.PERFORMANCE: ["return", "performance", "outperform", "underperform", "yield"],
            FinancialInsightType.FORECAST: ["forecast", "projection", "estimate", "guidance", "expect"],
            FinancialInsightType.ANOMALY: ["anomaly", "unusual", "exceptional", "outlier", "unexpected"],
        }

    def analyze_reasoning_traces(
        self,
        parsed: ParsedResponse,
    ) -> List[FinancialInsight]:
        """
        Extract financial insights from reasoning traces.

        Analyzes Claude thinking blocks or other reasoning formats.
        """
        insights = []

        for trace in parsed.reasoning_traces:
            # Analyze the reasoning content for financial insights
            extracted = self._extract_insights_from_text(trace.content, "reasoning")
            insights.extend(extracted)

        return insights

    def analyze_final_text(self, parsed: ParsedResponse) -> List[FinancialInsight]:
        """Extract financial insights from final text response."""
        insights = []

        if parsed.final_text:
            extracted = self._extract_insights_from_text(parsed.final_text, "text")
            insights.extend(extracted)

        return insights

    def _extract_insights_from_text(self, text: str, source: str) -> List[FinancialInsight]:
        """Extract insights from text content."""
        insights = []

        # Split into sentences
        sentences = [s.strip() for s in text.split(".") if s.strip()]

        for sentence in sentences:
            sentence_lower = sentence.lower()

            # Determine insight type by keyword matching
            insight_type = FinancialInsightType.UNKNOWN
            for itype, keywords in self.insight_keywords.items():
                if any(kw in sentence_lower for kw in keywords):
                    insight_type = itype
                    break

            if insight_type != FinancialInsightType.UNKNOWN:
                # Extract any numeric values mentioned
                metrics = self._extract_metrics(sentence)

                insights.append(FinancialInsight(
                    insight_type=insight_type,
                    content=sentence,
                    confidence=0.85,  # Base confidence
                    source=source,
                    metrics=metrics if metrics else None
                ))

        return insights

    def _extract_metrics(self, text: str) -> Optional[Dict[str, float]]:
        """Extract numeric metrics from text."""
        import re

        metrics = {}
        # Find percentage values
        percentages = re.findall(r'(\d+\.?\d*)\s*%', text)
        if percentages:
            metrics["percentage"] = float(percentages[0])

        # Find dollar amounts
        dollars = re.findall(r'\$\s*(\d+\.?\d*)\s*[BbMmKk]?', text)
        if dollars:
            metrics["amount"] = float(dollars[0])

        # Find ratios
        ratios = re.findall(r'(\d+\.?\d*)\s*x', text)
        if ratios:
            metrics["ratio"] = float(ratios[0])

        return metrics if metrics else None


class ToolCallValidator:
    """Validates tool calls for financial workflows."""

    # Tool cost estimates in API calls
    TOOL_COSTS = {
        "fetch_stock_data": 0.001,
        "fetch_financial_statements": 0.002,
        "calculate_ratios": 0.0005,
        "search_documents": 0.001,
        "query_database": 0.0008,
    }

    def __init__(self, max_budget: Optional[float] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.max_budget = max_budget

    def validate_tool_call(self, tool_call: ToolCallData) -> ToolValidationResult:
        """Validate a single tool call."""
        errors = []
        warnings = []

        # Check tool name validity
        if not self._is_valid_tool_name(tool_call.tool_name):
            errors.append(f"Unknown tool: {tool_call.tool_name}")

        # Check required inputs
        required_inputs = self._get_required_inputs(tool_call.tool_name)
        for required in required_inputs:
            if required not in tool_call.raw_input:
                errors.append(f"Missing required input: {required}")

        # Validate input types
        input_errors = self._validate_input_types(tool_call.tool_name, tool_call.raw_input)
        errors.extend(input_errors)

        # Estimate cost
        estimated_cost = self.TOOL_COSTS.get(tool_call.tool_name, 0.001)

        if self.max_budget and estimated_cost > self.max_budget:
            warnings.append(f"Tool cost ${estimated_cost} exceeds budget ${self.max_budget}")

        return ToolValidationResult(
            is_valid=len(errors) == 0,
            tool_name=tool_call.tool_name,
            errors=errors,
            warnings=warnings,
            estimated_cost=estimated_cost
        )

    def validate_tool_calls(self, tool_calls: List[ToolCallData]) -> List[ToolValidationResult]:
        """Validate multiple tool calls."""
        total_cost = 0.0
        results = []

        for tc in tool_calls:
            result = self.validate_tool_call(tc)
            results.append(result)

            if result.is_valid:
                total_cost += result.estimated_cost or 0

            if self.max_budget and total_cost > self.max_budget:
                # Add warning to remaining results
                for r in results[len(results) - 1:]:
                    if f"Total cost exceeds budget" not in r.warnings:
                        r.warnings.append(f"Total cost ${total_cost} exceeds budget ${self.max_budget}")

        return results

    def _is_valid_tool_name(self, name: str) -> bool:
        """Check if tool name is recognized."""
        return name in self.TOOL_COSTS

    def _get_required_inputs(self, tool_name: str) -> List[str]:
        """Get required inputs for a tool."""
        required_inputs_map = {
            "fetch_stock_data": ["ticker", "start_date"],
            "fetch_financial_statements": ["company_id", "period"],
            "calculate_ratios": ["financial_data"],
            "search_documents": ["query"],
            "query_database": ["sql"],
        }
        return required_inputs_map.get(tool_name, [])

    def _validate_input_types(self, tool_name: str, inputs: Dict[str, Any]) -> List[str]:
        """Validate input parameter types."""
        errors = []

        # Example type validation for specific tools
        if tool_name == "fetch_stock_data":
            if "ticker" in inputs and not isinstance(inputs["ticker"], str):
                errors.append("ticker must be a string")

        if tool_name == "calculate_ratios":
            if "financial_data" in inputs and not isinstance(inputs["financial_data"], dict):
                errors.append("financial_data must be a dictionary")

        return errors


class FinancialContentBlockHandler:
    """
    Main handler for processing LLM responses in financial workflows.

    Integrates parsing, validation, and analysis of content blocks.
    """

    def __init__(
        self,
        provider: Optional[ProviderType] = None,
        model_name: Optional[str] = None,
        max_tool_budget: Optional[float] = None,
    ):
        self.logger = logging.getLogger(self.__class__.__name__)

        # Initialize parser
        if model_name:
            self.parser = ContentBlockParserFactory.create_parser_for_model(model_name)
        elif provider:
            self.parser = ContentBlockParserFactory.create_parser(provider)
        else:
            raise ValueError("Either provider or model_name must be specified")

        # Initialize analyzers
        self.reasoning_analyzer = FinancialReasoningAnalyzer()
        self.tool_validator = ToolCallValidator(max_budget=max_tool_budget)

    def process_response(self, response: Any) -> "ProcessedFinancialResponse":
        """
        Process LLM response and extract all financial insights.

        This is the main entry point for the handler.
        """
        # Parse the response
        parsed = self.parser.safe_parse(response)

        if parsed.parse_errors:
            self.logger.warning(f"Parse errors: {parsed.parse_errors}")

        # Extract insights from reasoning
        reasoning_insights = self.reasoning_analyzer.analyze_reasoning_traces(parsed)

        # Extract insights from final text
        text_insights = self.reasoning_analyzer.analyze_final_text(parsed)

        # Validate tool calls
        tool_validations = self.tool_validator.validate_tool_calls(parsed.tool_calls)

        return ProcessedFinancialResponse(
            parsed_response=parsed,
            reasoning_insights=reasoning_insights,
            text_insights=text_insights,
            tool_validations=tool_validations,
            combined_insights=reasoning_insights + text_insights,
        )

    def extract_actionable_insights(self, response: Any) -> List[Dict[str, Any]]:
        """
        Extract actionable financial insights from response.

        Returns insights formatted for decision-making.
        """
        processed = self.process_response(response)

        actionable = []
        for insight in processed.combined_insights:
            actionable.append({
                "type": insight.insight_type.value,
                "content": insight.content,
                "confidence": insight.confidence,
                "source": insight.source,
                "metrics": insight.metrics or {}
            })

        return actionable

    async def process_response_streaming(
        self,
        response_stream,
    ) -> "ProcessedFinancialResponse":
        """
        Process streaming response from LLM.

        Accumulates blocks as they arrive.
        """
        accumulated_response = {
            "content": [],
            "model": "unknown"
        }

        async for chunk in response_stream:
            # Accumulate chunks
            if hasattr(chunk, "choices"):
                for choice in chunk.choices:
                    if hasattr(choice.delta, "content") and choice.delta.content:
                        accumulated_response["content"].append(choice.delta.content)

        # Parse accumulated response
        return self.process_response(accumulated_response)


class ProcessedFinancialResponse(BaseModel):
    """Complete processed response for financial workflows."""

    parsed_response: ParsedResponse
    reasoning_insights: List[FinancialInsight]
    text_insights: List[FinancialInsight]
    tool_validations: List[ToolValidationResult]
    combined_insights: List[FinancialInsight]

    class Config:
        arbitrary_types_allowed = True

    def get_high_confidence_insights(self, threshold: float = 0.8) -> List[FinancialInsight]:
        """Get insights above confidence threshold."""
        return [i for i in self.combined_insights if i.confidence >= threshold]

    def get_insights_by_type(self, insight_type: FinancialInsightType) -> List[FinancialInsight]:
        """Get insights of specific type."""
        return [i for i in self.combined_insights if i.insight_type == insight_type]

    def validate_all_tools(self) -> bool:
        """Check if all tools are valid."""
        return all(tv.is_valid for tv in self.tool_validations)

    def get_total_tool_cost(self) -> float:
        """Calculate total estimated tool execution cost."""
        return sum(tv.estimated_cost or 0 for tv in self.tool_validations)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for API responses."""
        return {
            "model": self.parsed_response.model,
            "insights": [
                {
                    "type": i.insight_type.value,
                    "content": i.content,
                    "confidence": i.confidence,
                    "source": i.source,
                    "metrics": i.metrics or {}
                }
                for i in self.combined_insights
            ],
            "reasoning_available": len(self.parsed_response.reasoning_traces) > 0,
            "tools_valid": self.validate_all_tools(),
            "total_tool_cost": self.get_total_tool_cost(),
            "tokens": self.parsed_response.usage or {},
        }
