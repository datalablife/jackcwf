"""
Practical examples of using unified content blocks in financial analysis agent.

Demonstrates real-world integration patterns with different LLM providers.
"""

import asyncio
from typing import Optional
import logging

from content_blocks_parser import (
    ProviderType,
    ContentBlockType,
)
from financial_content_handler import (
    FinancialContentBlockHandler,
    FinancialInsightType,
)


logger = logging.getLogger(__name__)


# Example 1: Stock Analysis Agent Using Claude
# =============================================

class StockAnalysisAgent:
    """Financial analysis agent for stock evaluation."""

    def __init__(self, model: str = "claude-3-5-sonnet-20241022"):
        self.model = model
        self.handler = FinancialContentBlockHandler(model_name=model)

    def analyze_stock(self, ticker: str, financial_data: dict) -> dict:
        """
        Analyze a stock using Claude with reasoning traces.

        This example shows how Claude's thinking blocks provide
        transparency into the analysis process.
        """
        # In real scenario, this would call the actual Claude API
        # For demo, we show the expected response structure
        llm_response = {
            "id": "msg_abc123",
            "model": self.model,
            "content": [
                {
                    "type": "thinking",
                    "thinking": (
                        "Let me analyze this company:\n"
                        "1. Revenue growth: The company shows 15% YoY growth\n"
                        "2. P/E ratio calculation: Market cap $50B, earnings $2B = 25x\n"
                        "3. Sector median P/E: 22x - suggesting slight premium\n"
                        "4. Debt/EBITDA: 2.5x, which is healthy\n"
                        "5. ROE trending up: 18% vs 15% last year\n"
                        "6. Risk factors: Competitive pressure in segment"
                    )
                },
                {
                    "type": "text",
                    "text": (
                        f"Stock {ticker} Analysis:\n\n"
                        "Valuation: Fair with slight premium to sector (P/E 25 vs median 22)\n"
                        "Momentum: Positive with consistent revenue growth (15% YoY)\n"
                        "Financial Health: Strong (D/E 2.5x, ROE improving)\n"
                        "Risk: Moderate competitive pressure\n"
                        "Recommendation: HOLD - Fair value, watch for growth acceleration"
                    )
                }
            ],
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": 450,
                "output_tokens": 280
            }
        }

        # Process the response
        processed = self.handler.process_response(llm_response)

        # Extract actionable insights
        return self._format_analysis(processed, ticker)

    def _format_analysis(self, processed, ticker: str) -> dict:
        """Format processed analysis for presentation."""
        insights = processed.combined_insights

        return {
            "ticker": ticker,
            "model": processed.parsed_response.model,

            # Reasoning transparency
            "reasoning_available": len(processed.parsed_response.reasoning_traces) > 0,
            "reasoning_summary": (
                processed.parsed_response.reasoning_traces[0].content
                if processed.parsed_response.reasoning_traces
                else None
            ),

            # Extracted insights
            "valuation_insights": [
                i.content for i in insights
                if i.insight_type == FinancialInsightType.VALUATION
            ],
            "risk_insights": [
                i.content for i in insights
                if i.insight_type == FinancialInsightType.RISK
            ],
            "performance_insights": [
                i.content for i in insights
                if i.insight_type == FinancialInsightType.PERFORMANCE
            ],

            # High-confidence insights only
            "high_confidence_insights": [
                {
                    "type": i.insight_type.value,
                    "content": i.content,
                    "confidence": i.confidence
                }
                for i in processed.get_high_confidence_insights(threshold=0.9)
            ],

            # Token usage tracking
            "tokens_used": processed.parsed_response.usage or {},
        }


# Example 2: Multi-Provider Portfolio Analysis
# ============================================

class PortfolioAnalyzer:
    """Analyze portfolio using multiple LLM providers for consensus."""

    def __init__(self):
        self.claude_handler = FinancialContentBlockHandler(
            model_name="claude-3-5-sonnet-20241022"
        )
        self.gpt_handler = FinancialContentBlockHandler(
            model_name="gpt-4-turbo"
        )
        self.gemini_handler = FinancialContentBlockHandler(
            model_name="gemini-1.5-pro"
        )

    def get_consensus_analysis(self, portfolio: list) -> dict:
        """
        Get consensus analysis from multiple providers.

        Each provider sees the same portfolio and provides insights.
        """
        analyses = {}

        # Claude's perspective (with reasoning)
        claude_response = self._get_claude_analysis(portfolio)
        analyses["claude"] = self.claude_handler.process_response(claude_response)

        # GPT-4's perspective
        gpt_response = self._get_gpt_analysis(portfolio)
        analyses["gpt"] = self.gpt_handler.process_response(gpt_response)

        # Gemini's perspective
        gemini_response = self._get_gemini_analysis(portfolio)
        analyses["gemini"] = self.gemini_handler.process_response(gemini_response)

        return self._aggregate_consensus(analyses, portfolio)

    def _get_claude_analysis(self, portfolio: list) -> dict:
        """Simulate Claude analysis response."""
        # Real implementation would call Claude API
        return {
            "model": "claude-3-5-sonnet-20241022",
            "content": [
                {
                    "type": "thinking",
                    "thinking": (
                        "Analyzing portfolio composition:\n"
                        "- Tech: 35% (higher than typical 20% benchmark)\n"
                        "- Finance: 25% (in line with benchmark)\n"
                        "- Healthcare: 20% (below 25% benchmark)\n"
                        "- Industrials: 15% (appropriate diversification)\n"
                        "- Energy: 5% (underweight, but acceptable)\n"
                        "Sector concentration risk is moderate."
                    )
                },
                {
                    "type": "text",
                    "text": (
                        "Portfolio is reasonably diversified with slight overweight to tech. "
                        "Recommend rebalancing toward healthcare for sector balance."
                    )
                }
            ]
        }

    def _get_gpt_analysis(self, portfolio: list) -> dict:
        """Simulate GPT-4 analysis response."""
        return {
            "model": "gpt-4-turbo",
            "choices": [{
                "message": {
                    "content": (
                        "Portfolio allocation shows tech overconcentration at 35%. "
                        "Consider reducing to 25-28% for better diversification."
                    )
                }
            }]
        }

    def _get_gemini_analysis(self, portfolio: list) -> dict:
        """Simulate Gemini analysis response."""
        return {
            "model": "gemini-1.5-pro",
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": (
                            "Tech sector at 35% creates concentration risk. "
                            "Recommend gradual rebalancing toward Healthcare (20->25%)."
                        )
                    }]
                }
            }]
        }

    def _aggregate_consensus(self, analyses: dict, portfolio: list) -> dict:
        """Aggregate insights from all providers."""
        all_insights = []

        for provider, processed in analyses.items():
            all_insights.extend([
                {
                    "provider": provider,
                    "type": i.insight_type.value,
                    "content": i.content,
                    "confidence": i.confidence,
                    "source": i.source
                }
                for i in processed.combined_insights
            ])

        return {
            "portfolio": portfolio,
            "provider_count": len(analyses),
            "consensus_insights": all_insights,

            # Find common themes across providers
            "common_themes": self._find_common_themes(all_insights),

            # Provider disagreements
            "disagreements": self._find_disagreements(analyses),
        }

    def _find_common_themes(self, insights: list) -> list:
        """Find insights mentioned by multiple providers."""
        # Simplified: group by insight type
        by_type = {}
        for insight in insights:
            itype = insight["type"]
            if itype not in by_type:
                by_type[itype] = []
            by_type[itype].append(insight)

        # Filter to themes mentioned by multiple providers
        return [
            {
                "theme": itype,
                "provider_count": len(items),
                "examples": [i["content"][:100] + "..." for i in items[:2]]
            }
            for itype, items in by_type.items()
            if len(items) > 1
        ]

    def _find_disagreements(self, analyses: dict) -> list:
        """Identify where providers disagree."""
        # Simplified disagreement detection
        disagreements = []

        if analyses["claude"] and analyses["gpt"]:
            # Compare risk insights
            claude_risks = analyses["claude"].get_insights_by_type(FinancialInsightType.RISK)
            gpt_risks = analyses["gpt"].get_insights_by_type(FinancialInsightType.RISK)

            if len(claude_risks) != len(gpt_risks):
                disagreements.append({
                    "category": "risk_assessment",
                    "claude_count": len(claude_risks),
                    "gpt_count": len(gpt_risks),
                    "note": "Different risk emphasis"
                })

        return disagreements


# Example 3: Tool Call Execution Pipeline
# ======================================

class ToolExecutionPipeline:
    """
    Execute tool calls extracted from LLM responses.

    Validates tools before execution and tracks costs.
    """

    def __init__(self, max_budget: float = 0.10):
        self.handler = FinancialContentBlockHandler(
            provider=ProviderType.ANTHROPIC,
            max_tool_budget=max_budget
        )
        self.executed_tools = []

    def execute_with_tools(self, llm_response: dict) -> dict:
        """
        Execute any tool calls in the LLM response.

        Returns results that can be fed back to the LLM.
        """
        # Process the response
        processed = self.handler.process_response(llm_response)

        # Validate all tools before execution
        if not processed.validate_all_tools():
            return {
                "success": False,
                "error": "Tool validation failed",
                "validation_errors": [
                    {
                        "tool": tv.tool_name,
                        "errors": tv.errors
                    }
                    for tv in processed.tool_validations
                    if not tv.is_valid
                ]
            }

        # Check budget
        total_cost = processed.get_total_tool_cost()
        if total_cost > self.handler.tool_validator.max_budget:
            return {
                "success": False,
                "error": f"Total tool cost ${total_cost} exceeds budget",
                "estimated_cost": total_cost
            }

        # Execute tools
        results = []
        for tool_call in processed.parsed_response.tool_calls:
            result = self._execute_tool(tool_call)
            results.append(result)
            self.executed_tools.append({
                "tool": tool_call.tool_name,
                "status": "executed" if result["success"] else "failed",
                "cost": processed.tool_validations[0].estimated_cost if results else 0
            })

        return {
            "success": True,
            "tool_results": results,
            "total_cost": total_cost,
            "reasoning_available": len(processed.parsed_response.reasoning_traces) > 0,
            "main_response": processed.parsed_response.final_text,
        }

    def _execute_tool(self, tool_call) -> dict:
        """Execute individual tool."""
        tool_name = tool_call.tool_name

        try:
            if tool_name == "fetch_financial_statements":
                return self._fetch_financial_statements(tool_call.raw_input)
            elif tool_name == "fetch_stock_data":
                return self._fetch_stock_data(tool_call.raw_input)
            elif tool_name == "calculate_ratios":
                return self._calculate_ratios(tool_call.raw_input)
            elif tool_name == "search_documents":
                return self._search_documents(tool_call.raw_input)
            else:
                return {
                    "success": False,
                    "tool": tool_name,
                    "error": "Unknown tool"
                }
        except Exception as e:
            return {
                "success": False,
                "tool": tool_name,
                "error": str(e)
            }

    def _fetch_financial_statements(self, inputs: dict) -> dict:
        """Simulate fetching financial statements."""
        return {
            "success": True,
            "tool": "fetch_financial_statements",
            "data": {
                "company_id": inputs.get("company_id"),
                "period": inputs.get("period"),
                "revenue": 1000000,
                "net_income": 250000,
                "assets": 5000000
            }
        }

    def _fetch_stock_data(self, inputs: dict) -> dict:
        """Simulate fetching stock data."""
        return {
            "success": True,
            "tool": "fetch_stock_data",
            "data": {
                "ticker": inputs.get("ticker"),
                "start_date": inputs.get("start_date"),
                "prices": [150.0, 151.5, 149.8, 152.3],
                "volumes": [1000000, 1100000, 950000, 1050000]
            }
        }

    def _calculate_ratios(self, inputs: dict) -> dict:
        """Simulate ratio calculation."""
        return {
            "success": True,
            "tool": "calculate_ratios",
            "data": {
                "pe_ratio": 18.5,
                "debt_to_equity": 0.4,
                "roe": 0.22,
                "current_ratio": 2.1
            }
        }

    def _search_documents(self, inputs: dict) -> dict:
        """Simulate document search."""
        return {
            "success": True,
            "tool": "search_documents",
            "data": {
                "query": inputs.get("query"),
                "results": [
                    "Document 1: Q3 earnings show strong growth",
                    "Document 2: Management discusses market opportunities",
                    "Document 3: Risk factors updated in latest filing"
                ]
            }
        }


# Example 4: Streaming Response Handler
# =====================================

class StreamingAnalysisHandler:
    """Handle streaming LLM responses."""

    def __init__(self, model: str = "claude-3-5-sonnet-20241022"):
        self.handler = FinancialContentBlockHandler(model_name=model)
        self.accumulated_response = {"content": [], "model": model}

    async def handle_streaming_analysis(self, stream) -> dict:
        """
        Process streaming response in real-time.

        Accumulates chunks and provides incremental insights.
        """
        async for chunk in stream:
            self._accumulate_chunk(chunk)

            # Provide incremental feedback
            if self._should_process_incrementally():
                yield self._get_incremental_insights()

        # Final processing
        final = self.handler.process_response(self.accumulated_response)
        yield {
            "type": "final",
            "insights": final.to_dict(),
            "complete": True
        }

    def _accumulate_chunk(self, chunk):
        """Accumulate streaming chunk."""
        if hasattr(chunk, "choices"):
            for choice in chunk.choices:
                if hasattr(choice.delta, "content") and choice.delta.content:
                    self.accumulated_response["content"].append(choice.delta.content)

    def _should_process_incrementally(self) -> bool:
        """Determine if we have enough to process."""
        accumulated = "".join(self.accumulated_response["content"])
        return len(accumulated.split()) > 20  # Every 20 words

    def _get_incremental_insights(self) -> dict:
        """Extract incremental insights."""
        accumulated = "".join(self.accumulated_response["content"])
        return {
            "type": "incremental",
            "partial_text": accumulated[-100:],  # Last 100 chars
            "tokens_so_far": len(accumulated.split())
        }


# Example 5: Multi-step Financial Analysis Workflow
# ================================================

class FinancialAnalysisWorkflow:
    """
    Complete workflow for financial analysis.

    Coordinates between multiple agents and tools.
    """

    def __init__(self):
        self.stock_agent = StockAnalysisAgent()
        self.portfolio_analyzer = PortfolioAnalyzer()
        self.tool_pipeline = ToolExecutionPipeline(max_budget=0.50)

    def analyze_portfolio_with_tools(self, portfolio: list) -> dict:
        """
        Complete portfolio analysis with tool usage.

        Step 1: Get consensus analysis from multiple providers
        Step 2: Execute recommended data gathering tools
        Step 3: Refine analysis with tool results
        """
        # Step 1: Initial analysis
        consensus = self.portfolio_analyzer.get_consensus_analysis(portfolio)

        # Step 2: Identify required data gathering
        required_data = self._identify_required_data(consensus)

        # Step 3: Execute data gathering (simulated)
        gathered_data = self._gather_data(required_data)

        # Step 4: Refine analysis
        refined_analysis = self._refine_analysis(consensus, gathered_data)

        return {
            "initial_consensus": consensus,
            "required_data": required_data,
            "gathered_data": gathered_data,
            "refined_analysis": refined_analysis,
            "status": "complete"
        }

    def _identify_required_data(self, consensus: dict) -> list:
        """Identify what data is needed."""
        return [
            "fetch_financial_statements",
            "fetch_stock_data",
            "calculate_ratios"
        ]

    def _gather_data(self, required_tools: list) -> dict:
        """Gather required data (simulated)."""
        return {
            "financial_statements": {
                "revenue_growth": 0.15,
                "profit_margin": 0.25
            },
            "stock_data": {
                "current_price": 150.0,
                "52_week_high": 165.0,
                "52_week_low": 120.0
            },
            "ratios": {
                "pe_ratio": 18.5,
                "roe": 0.22
            }
        }

    def _refine_analysis(self, consensus: dict, data: dict) -> dict:
        """Refine initial consensus with gathered data."""
        return {
            "initial_insights": consensus["consensus_insights"][:3],
            "data_confirms": "High confidence in initial assessment",
            "additional_findings": [
                "ROE of 22% indicates strong management execution",
                "52-week performance within expected range",
                "PE multiple reasonable for growth rate"
            ]
        }


# Main execution example
def main():
    """Demonstrate the unified content blocks system."""

    print("=" * 70)
    print("UNIFIED CONTENT BLOCKS SYSTEM FOR FINANCIAL ANALYSIS")
    print("=" * 70)

    # Example 1: Stock Analysis
    print("\n1. STOCK ANALYSIS WITH REASONING TRANSPARENCY")
    print("-" * 70)
    agent = StockAnalysisAgent()
    analysis = agent.analyze_stock("AAPL", {})
    print(f"Model: {analysis['model']}")
    print(f"Reasoning Available: {analysis['reasoning_available']}")
    print(f"High Confidence Insights: {len(analysis['high_confidence_insights'])}")

    # Example 2: Multi-Provider Consensus
    print("\n2. MULTI-PROVIDER CONSENSUS ANALYSIS")
    print("-" * 70)
    analyzer = PortfolioAnalyzer()
    portfolio = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
    consensus = analyzer.get_consensus_analysis(portfolio)
    print(f"Providers: {consensus['provider_count']}")
    print(f"Common Themes: {len(consensus['common_themes'])}")
    print(f"Disagreements: {len(consensus['disagreements'])}")

    # Example 3: Tool Execution
    print("\n3. TOOL EXECUTION WITH VALIDATION")
    print("-" * 70)
    pipeline = ToolExecutionPipeline(max_budget=0.10)
    tool_response = {
        "model": "claude-3-5-sonnet-20241022",
        "content": [{
            "type": "tool_use",
            "id": "tool_123",
            "name": "fetch_financial_statements",
            "input": {"company_id": "AAPL", "period": "Q3_2024"}
        }]
    }
    execution_result = pipeline.execute_with_tools(tool_response)
    print(f"Success: {execution_result['success']}")
    print(f"Tools Executed: {len(execution_result.get('tool_results', []))}")

    # Example 4: Complete Workflow
    print("\n4. COMPLETE FINANCIAL ANALYSIS WORKFLOW")
    print("-" * 70)
    workflow = FinancialAnalysisWorkflow()
    portfolio_analysis = workflow.analyze_portfolio_with_tools(["AAPL", "MSFT"])
    print(f"Status: {portfolio_analysis['status']}")
    print(f"Consensus Insights: {len(portfolio_analysis['initial_consensus']['consensus_insights'])}")

    print("\n" + "=" * 70)
    print("Examples completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
