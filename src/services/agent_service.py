"""LangChain agent service for handling AI conversations with tools."""

import asyncio
import logging
import os
import re
from typing import Any, AsyncIterator, Dict, List, Optional
from uuid import UUID

from duckduckgo_search import DDGS
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool as langchain_tool
from langchain_openai import ChatOpenAI
from sqlalchemy import text as sql_text
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories import EmbeddingRepository
from src.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class AgentService:
    """
    Service for LangChain agent operations.

    Uses LangChain v1.0 patterns with:
    - create_agent() for agent creation
    - Middleware hooks for customization
    - Content blocks for tool calls and reasoning
    - Streaming support for real-time responses
    - Cost tracking and token counting
    """

    def __init__(
        self,
        session: AsyncSession,
        openai_api_key: Optional[str] = None,
        model: str = "gpt-4-turbo",
    ):
        """
        Initialize agent service.

        Args:
            session: SQLAlchemy async session
            openai_api_key: OpenAI API key
            model: Model to use for agent
        """
        self.session = session
        self.embedding_repo = EmbeddingRepository(session)
        self.embedding_service = EmbeddingService(openai_api_key)
        self.model = model

        # Initialize LLM with streaming support
        self.llm = ChatOpenAI(
            model=model,
            openai_api_key=openai_api_key,
            temperature=0.7,
            streaming=True,  # Enable streaming
        )
        self.allowed_tables = set(
            filter(
                None,
                os.getenv("QUERY_TOOL_ALLOWED_TABLES", "conversations,messages,documents,embeddings").split(","),
            )
        )

    SQL_FORBIDDEN_KEYWORDS = {"insert", "update", "delete", "drop", "truncate", "alter", "create", ";"}

    def _build_messages(
        self,
        system_prompt: str,
        message_history: List[dict],
        user_message: str,
    ) -> List[Any]:
        """Create LangChain message sequence from stored history."""
        messages: List[Any] = []

        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))

        for msg in message_history:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
            elif role == "system":
                messages.append(SystemMessage(content=content))

        messages.append(HumanMessage(content=user_message))
        return messages

    @staticmethod
    def _extract_chunk_text(chunk: Any) -> str:
        """Convert AIMessageChunk content to plain text."""
        content = getattr(chunk, "content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    parts.append(item.get("text", ""))
                else:
                    parts.append(str(item))
            return "".join(parts)
        return ""

    @staticmethod
    def _format_tool_results(tool_calls: List[dict], tool_results: List[dict]) -> str:
        """Format tool call/results for follow-up prompting."""
        lines = []
        for call, result in zip(tool_calls, tool_results):
            lines.append(
                f"Tool {call['name']} (call_id={call['id']}):\n"
                f"Input: {call.get('input')}\n"
                f"Output: {result.get('output')}"
            )
        return "\n\n".join(lines)

    def _validate_sql_query(self, sql_query: str) -> str:
        """Ensure SQL query is read-only and targets allowlisted tables."""
        if not sql_query or not sql_query.strip():
            raise ValueError("SQL query cannot be empty")

        query = sql_query.strip().rstrip(";")
        lowered = query.lower()

        if not lowered.startswith("select"):
            raise ValueError("Only SELECT statements are allowed")

        for keyword in self.SQL_FORBIDDEN_KEYWORDS:
            if keyword in lowered:
                raise ValueError(f"Keyword '{keyword}' is not allowed in SQL queries")

        tables = re.findall(r"from\\s+([a-zA-Z_][\\w.]*)", lowered)
        if not tables:
            raise ValueError("SQL query must include a FROM clause")

        for table in tables:
            actual = table.split(".")[-1]
            if actual not in self.allowed_tables:
                raise ValueError(f"Table '{actual}' is not allowed for querying")

        if " limit " not in lowered:
            query += " LIMIT 100"

        return query

    async def _execute_safe_query(self, sanitized_query: str) -> List[Dict[str, Any]]:
        """Run validated SQL and return row dictionaries."""
        result = await self.session.execute(sql_text(sanitized_query))
        rows = result.mappings().all()
        return [dict(row) for row in rows]

    async def _perform_web_search(self, query: str, limit: int, search_type: str) -> List[dict]:
        """Execute DuckDuckGo search in a thread pool."""
        def _search():
            with DDGS() as ddgs:
                if search_type == "news":
                    return list(ddgs.news(query, max_results=limit))
                elif search_type == "scholar":
                    return list(ddgs.text(query, max_results=limit, backend="lite"))
                return list(ddgs.text(query, max_results=limit))

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _search)

    @staticmethod
    def _summarize_search_results(results: List[dict], limit: int) -> str:
        """Convert search results into formatted string."""
        if not results:
            return "No results found."

        lines = []
        for idx, item in enumerate(results, 1):
            title = item.get("title") or item.get("heading") or "Untitled result"
            url = item.get("url") or item.get("href") or item.get("image") or "N/A"
            snippet = item.get("body") or item.get("excerpt") or item.get("description") or ""
            lines.append(f"{idx}. {title}\n   URL: {url}\n   Snippet: {snippet}")
        return "\n\n".join(lines[:limit])

    async def create_rag_tools(self, user_id: str) -> List[Any]:
        """
        Create RAG-enabled tools for the agent.

        Uses Pydantic models for type safety and validation.

        Args:
            user_id: User ID for scoping tools

        Returns:
            List of LangChain Tool objects
        """
        embedding_repo = self.embedding_repo
        embedding_service = self.embedding_service
        user_id_str = user_id

        @langchain_tool
        async def search_documents(query: str, limit: int = 5) -> str:
            """
            Search user's documents using semantic similarity.

            Use this tool when the user asks about their documents,
            uploaded files, or previously shared information.

            Args:
                query: Search query - what to look for in documents
                limit: Maximum number of results to return (default: 5)

            Returns:
                Formatted search results with document excerpts
            """
            try:
                logger.info(f"Tool search_documents called with query: {query}")

                # Generate embedding for query
                query_embedding = await embedding_service.embed_text(query)

                # Search for similar embeddings
                results = await embedding_repo.search_similar(
                    query_embedding=query_embedding,
                    user_id=user_id_str,
                    limit=limit,
                    threshold=0.7,
                )

                if not results:
                    return "No relevant documents found for your query."

                # Calculate similarity scores
                similarities = embedding_service.batch_cosine_similarity(
                    query_embedding=query_embedding,
                    embeddings=[r.embedding for r in results],
                )

                # Format results
                formatted_results = []
                for i, (result, similarity) in enumerate(zip(results, similarities), 1):
                    formatted_results.append(
                        f"{i}. [Similarity: {similarity:.2%}]\n"
                        f"   {result.chunk_text[:300]}...\n"
                        f"   (Document ID: {result.document_id}, Chunk: {result.chunk_index})"
                    )

                return "\n\n".join(formatted_results)

            except Exception as e:
                logger.error(f"Error in search_documents: {str(e)}", exc_info=True)
                return f"Error searching documents: {str(e)}"

        @langchain_tool
        async def query_database(sql_query: str) -> str:
            """
            Execute a validated SQL query against the primary database.

            Only read-only SELECT statements targeting allowlisted tables
            are permitted. A LIMIT clause is enforced automatically if
            omitted to protect resources.
            """
            logger.info(f"Tool query_database called with query: {sql_query}")

            try:
                sanitized = self._validate_sql_query(sql_query)
                rows = await self._execute_safe_query(sanitized)
            except Exception as exc:
                logger.error(f"query_database validation failed: {exc}")
                return f"SQL query rejected: {exc}"

            if not rows:
                return "Query executed successfully but returned no rows."

            preview = rows[: min(20, len(rows))]
            columns = preview[0].keys()
            formatted_rows = "\n".join(
                f"- { {col: row[col] for col in columns} }"
                for row in preview
            )

            return (
                f"Executed query:\n{sanitized}\n\n"
                f"Columns: {', '.join(columns)}\n"
                f"Returned rows: {len(rows)} (showing {len(preview)})\n"
                f"{formatted_rows}"
            )

        @langchain_tool
        async def web_search(query: str, limit: int = 5, search_type: str = "general") -> str:
            """
            Search the web for current information.

            Use this when the user asks about:
            - Current events or news
            - Recent developments in a topic
            - Information not in their documents
            - Real-time data or statistics

            Args:
                query: What to search for on the web
                limit: Maximum number of results (default: 5)
                search_type: general/news/scholar

            Returns:
                Web search results with summaries from DuckDuckGo
            """
            logger.info(f"Tool web_search called with query: {query} ({search_type})")

            try:
                results = await self._perform_web_search(query, limit, search_type)
                return self._summarize_search_results(results, limit)
            except Exception as exc:
                logger.error(f"Web search failed: {exc}")
                return f"Web search failed: {exc}"

        return [search_documents, query_database, web_search]

    async def process_message(
        self,
        user_id: str,
        conversation_id: str,
        user_message: str,
        system_prompt: str,
        message_history: List[dict],
    ) -> dict:
        """
        Process a user message with the agent.

        Uses LangChain v1.0 patterns for:
        - Tool calling
        - Content blocks
        - Token tracking
        - Error handling

        Args:
            user_id: User ID
            conversation_id: Conversation ID
            user_message: User's message
            system_prompt: System prompt for the agent
            message_history: Previous messages in format [{"role": "...", "content": "..."}]

        Returns:
            Response dict with:
            - agent_response: Final response text
            - tool_calls: List of tool calls made (if any)
            - tool_results: List of tool results (if any)
            - tokens_used: Total tokens used
            - reasoning: Agent's reasoning process (if available)
        """
        try:
            logger.info(f"Processing message for conversation {conversation_id}")

            # Create RAG tools
            tools = await self.create_rag_tools(user_id)

            messages = self._build_messages(system_prompt, message_history, user_message)

            # Bind tools to LLM
            llm_with_tools = self.llm.bind_tools(tools)

            # Invoke LLM with tools
            logger.info(f"Invoking LLM with {len(tools)} tools")
            response = await llm_with_tools.ainvoke(messages)

            # Initialize response data
            tool_calls_data = []
            tool_results_data = []
            tokens_used = 0

            # Extract token usage if available
            if hasattr(response, "response_metadata"):
                usage = response.response_metadata.get("token_usage", {})
                tokens_used = usage.get("total_tokens", 0)

            # Check for tool calls in response
            if hasattr(response, "tool_calls") and response.tool_calls:
                logger.info(f"Agent made {len(response.tool_calls)} tool calls")

                # Process each tool call
                for tool_call in response.tool_calls:
                    tool_name = tool_call.get("name")
                    tool_input = tool_call.get("args", {})
                    call_id = tool_call.get("id", f"call_{len(tool_calls_data)}")

                    tool_calls_data.append({
                        "id": call_id,
                        "name": tool_name,
                        "input": tool_input,
                    })

                    # Execute the tool
                    try:
                        # Find the tool
                        tool = next((t for t in tools if t.name == tool_name), None)

                        if tool:
                            # Execute tool
                            result = await tool.ainvoke(tool_input)

                            tool_results_data.append({
                                "id": call_id,
                                "output": result,
                            })

                            logger.info(f"Tool {tool_name} executed successfully")
                        else:
                            logger.error(f"Tool {tool_name} not found")
                            tool_results_data.append({
                                "id": call_id,
                                "output": f"Error: Tool {tool_name} not found",
                            })

                    except Exception as e:
                        logger.error(f"Error executing tool {tool_name}: {str(e)}")
                        tool_results_data.append({
                            "id": call_id,
                            "output": f"Error executing tool: {str(e)}",
                        })

                # If tools were called, get final response from agent
                # Add tool results to messages
                messages.append(response)

                tool_results_text = self._format_tool_results(tool_calls_data, tool_results_data)

                messages.append(HumanMessage(
                    content=f"Here are the tool results:\n\n{tool_results_text}\n\n"
                            f"Please provide a final response to the user based on these results."
                ))

                # Get final response
                final_response = await self.llm.ainvoke(messages)
                agent_response = final_response.content

                # Add final response tokens
                if hasattr(final_response, "response_metadata"):
                    usage = final_response.response_metadata.get("token_usage", {})
                    tokens_used += usage.get("total_tokens", 0)

            else:
                # No tool calls, use direct response
                agent_response = response.content

            logger.info(
                f"Message processed successfully. "
                f"Tools called: {len(tool_calls_data)}, Tokens: {tokens_used}"
            )

            return {
                "agent_response": agent_response,
                "tool_calls": tool_calls_data if tool_calls_data else None,
                "tool_results": tool_results_data if tool_results_data else None,
                "tokens_used": tokens_used,
            }

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            return {
                "agent_response": f"I encountered an error while processing your message: {str(e)}",
                "error": True,
                "tool_calls": None,
                "tool_results": None,
                "tokens_used": 0,
            }

    async def stream_message(
        self,
        user_id: str,
        conversation_id: str,
        user_message: str,
        system_prompt: str,
        message_history: List[dict],
    ) -> AsyncIterator[dict]:
        """
        Stream a response from the agent.

        Yields chunks as they're generated for real-time UX.

        Args:
            user_id: User ID
            conversation_id: Conversation ID
            user_message: User's message
            system_prompt: System prompt
            message_history: Previous messages

        Yields:
            Response chunks with type and content
        """
        state = {
            "response": "",
            "tool_calls": [],
            "tool_results": [],
            "tokens_used": 0,
        }

        try:
            tools = await self.create_rag_tools(user_id)
            messages = self._build_messages(system_prompt, message_history, user_message)

            async for event in self._stream_with_tools(messages, tools, state):
                yield event

            yield {
                "type": "complete_state",
                "response": state["response"],
                "tool_calls": state["tool_calls"] or None,
                "tool_results": state["tool_results"] or None,
                "tokens_used": state["tokens_used"],
            }

        except Exception as e:
            logger.error(f"Error streaming message: {str(e)}", exc_info=True)
            yield {
                "type": "error",
                "error": str(e),
            }

    async def summarize_conversation(
        self,
        conversation_title: str,
        message_history: List[dict],
    ) -> str:
        """
        Generate a summary of the conversation.

        Args:
            conversation_title: Conversation title
            message_history: List of messages

        Returns:
            Generated summary (2-3 sentences)
        """
        try:
            # Build message text
            messages_text = "\n".join(
                [f"{msg['role']}: {msg['content']}" for msg in message_history[-10:]]
            )

            # Create summary prompt
            prompt = f"""
Please summarize the following conversation in 2-3 concise sentences.
Focus on the main topics discussed and any key outcomes or decisions.

Title: {conversation_title}

Recent Messages:
{messages_text}

Summary:"""

            # Get summary from LLM
            messages = [HumanMessage(content=prompt)]
            response = await self.llm.ainvoke(messages)

            summary = response.content.strip()

            logger.info(f"Generated summary for conversation '{conversation_title}'")

            return summary

        except Exception as e:
            logger.error(f"Error summarizing conversation: {str(e)}", exc_info=True)
            return f"Conversation about {conversation_title}"

    async def _stream_with_tools(
        self,
        messages: List[Any],
        tools: List[Any],
        state: Dict[str, Any],
    ) -> AsyncIterator[dict]:
        """Recursive helper that streams responses and handles tool invocations."""
        llm_with_tools = self.llm.bind_tools(tools)
        aggregated_chunk = None

        async for chunk in llm_with_tools.astream(messages):
            aggregated_chunk = chunk if aggregated_chunk is None else aggregated_chunk + chunk
            text = self._extract_chunk_text(chunk)
            if text:
                state["response"] += text
                yield {"type": "content", "content": text}

        if aggregated_chunk is None:
            return

        usage = getattr(aggregated_chunk, "response_metadata", {}).get("token_usage", {})
        state["tokens_used"] += usage.get("total_tokens", 0)

        ai_message = aggregated_chunk.to_message()
        tool_calls = getattr(ai_message, "tool_calls", None) or []
        updated_messages = messages + [ai_message]

        if tool_calls:
            recent_calls = []
            recent_results = []
            for tool_call in tool_calls:
                call_id = tool_call.get("id") or f"call_{len(state['tool_calls'])}"
                payload = {
                    "id": call_id,
                    "name": tool_call.get("name"),
                    "input": tool_call.get("args", {}),
                }
                state["tool_calls"].append(payload)
                recent_calls.append(payload)

                yield {
                    "type": "tool_call",
                    "tool_name": payload["name"],
                    "tool_input": payload["input"],
                    "call_id": call_id,
                }

                result_payload = await self._handle_tool_execution(tool_call, tools, call_id)
                state["tool_results"].append(result_payload)
                recent_results.append(result_payload)

                yield {
                    "type": "tool_result",
                    "call_id": call_id,
                    "result": result_payload["output"],
                }

            tool_results_text = self._format_tool_results(recent_calls, recent_results)
            follow_up_messages = updated_messages + [
                HumanMessage(
                    content="Here are the tool results:\n\n"
                    f"{tool_results_text}\n\nPlease provide a final response to the user based on these results."
                )
            ]

            async for event in self._stream_with_tools(follow_up_messages, tools, state):
                yield event

    async def _handle_tool_execution(self, tool_call: dict, tools: List[Any], call_id: str) -> dict:
        """Execute LangChain tool and capture output/errors."""
        tool_name = tool_call.get("name")
        tool_input = tool_call.get("args", {})

        tool = next((t for t in tools if t.name == tool_name), None)

        if not tool:
            output = f"Error: Tool {tool_name} not found"
        else:
            try:
                if hasattr(tool, "ainvoke"):
                    output = await tool.ainvoke(tool_input)
                else:
                    output = tool.invoke(tool_input)
            except Exception as exc:
                logger.error(f"Error executing tool {tool_name}: {exc}")
                output = f"Error executing tool {tool_name}: {exc}"

        return {"id": call_id, "output": output}
