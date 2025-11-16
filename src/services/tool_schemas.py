"""Pydantic schemas for LangChain tools with validation."""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class SearchDocumentsInput(BaseModel):
    """Input schema for search_documents tool."""

    query: str = Field(
        description="Search query - what to look for in documents",
        min_length=1,
        max_length=500
    )
    limit: int = Field(
        default=5,
        description="Maximum number of results to return",
        ge=1,
        le=50
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "financial analysis 2024",
                "limit": 10
            }
        }


class QueryDatabaseInput(BaseModel):
    """Input schema for query_database tool."""

    natural_language_query: str = Field(
        description="What data the user wants to retrieve",
        min_length=5,
        max_length=1000
    )
    table_filter: Optional[str] = Field(
        default=None,
        description="Optional table name to limit search scope"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "natural_language_query": "Show me all transactions from Q1 2024",
                "table_filter": "transactions"
            }
        }


class WebSearchInput(BaseModel):
    """Input schema for web_search tool."""

    query: str = Field(
        description="What to search for on the web",
        min_length=1,
        max_length=500
    )
    limit: int = Field(
        default=5,
        description="Maximum number of results",
        ge=1,
        le=20
    )
    search_type: str = Field(
        default="general",
        description="Type of search: general, news, scholar",
        pattern="^(general|news|scholar)$"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "artificial intelligence trends 2024",
                "limit": 5,
                "search_type": "general"
            }
        }


# Tool response schemas (optional but recommended)

class SearchResult(BaseModel):
    """Single search result."""

    rank: int = Field(description="Result rank")
    content: str = Field(description="Result excerpt")
    similarity_score: float = Field(
        description="Similarity score (0-1)",
        ge=0,
        le=1
    )
    source_id: str = Field(description="Document ID or source")
    metadata: dict = Field(
        default_factory=dict,
        description="Additional metadata"
    )


class SearchResults(BaseModel):
    """Aggregated search results."""

    total_results: int = Field(description="Total results found")
    results: List[SearchResult] = Field(description="Search results")
    search_time_ms: float = Field(description="Search execution time")


class DatabaseQueryResult(BaseModel):
    """Result from database query."""

    query: str = Field(description="Executed query")
    row_count: int = Field(description="Number of rows returned")
    columns: List[str] = Field(description="Column names")
    sample_rows: List[dict] = Field(description="Sample of returned rows")
    execution_time_ms: float = Field(description="Query execution time")


class WebSearchResult(BaseModel):
    """Single web search result."""

    rank: int = Field(description="Result rank")
    title: str = Field(description="Result title")
    url: str = Field(description="Result URL")
    snippet: str = Field(description="Result snippet/summary")
    relevance_score: Optional[float] = Field(
        default=None,
        description="Relevance score 0-1"
    )


class WebSearchResults(BaseModel):
    """Aggregated web search results."""

    query: str = Field(description="Original search query")
    results: List[WebSearchResult] = Field(description="Search results")
    total_found: int = Field(description="Total results found")
    search_time_ms: float = Field(description="Search execution time")
