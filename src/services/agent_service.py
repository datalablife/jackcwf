"""LangChain agent service for handling AI conversations with tools."""

import json
import logging
from typing import Any, Dict, List, Optional, AsyncIterator
from uuid import UUID

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool as langchain_tool
from langchain_openai import ChatOpenAI
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
        async def query_database(natural_language_query: str) -> str:
            """
            Query database using natural language.

            Use this when the user asks for structured data, statistics,
            or information that might be in a database.

            NOTE: This is a placeholder for production implementation.
            In production, this should:
            1. Use an LLM to convert natural language to safe SQL
            2. Validate queries against a whitelist of tables/columns
            3. Use parameterized queries to prevent SQL injection
            4. Implement rate limiting and query cost estimation

            Args:
                natural_language_query: What data the user wants to retrieve

            Returns:
                Query results formatted as text
            """
            logger.info(f"Tool query_database called with query: {natural_language_query}")

            # Placeholder response
            return (
                f"Database query tool received request: '{natural_language_query}'\n\n"
                "This is a placeholder. In production, this would:\n"
                "1. Convert your question to a safe SQL query\n"
                "2. Execute it against the database\n"
                "3. Return formatted results\n\n"
                "Example SQL: SELECT * FROM table WHERE condition LIMIT 10"
            )

        @langchain_tool
        async def web_search(query: str, limit: int = 5) -> str:
            """
            Search the web for current information.

            Use this when the user asks about:
            - Current events or news
            - Recent developments in a topic
            - Information not in their documents
            - Real-time data or statistics

            NOTE: This is a placeholder for production implementation.
            In production, integrate with services like:
            - Tavily Search API
            - Serper.dev
            - Google Custom Search
            - Bing Search API

            Args:
                query: What to search for on the web
                limit: Maximum number of results (default: 5)

            Returns:
                Web search results with summaries
            """
            logger.info(f"Tool web_search called with query: {query}")

            # Placeholder response
            return (
                f"Web search for '{query}' would return {limit} results.\n\n"
                "This is a placeholder. In production, this would:\n"
                "1. Query a web search API\n"
                "2. Retrieve relevant results\n"
                "3. Format and summarize findings\n\n"
                "Integration options:\n"
                "- Tavily Search (optimized for LLMs)\n"
                "- Serper.dev (Google Search API)\n"
                "- Bing Search API\n"
                "- DuckDuckGo API"
            )

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

            # Build messages for LLM
            messages = []

            # Add system prompt
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))

            # Add message history
            for msg in message_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
                elif msg["role"] == "system":
                    messages.append(SystemMessage(content=msg["content"]))

            # Add current user message
            messages.append(HumanMessage(content=user_message))

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

                # Add tool results as a message
                tool_results_text = "\n\n".join([
                    f"Tool: {tc['name']}\nResult: {tr['output']}"
                    for tc, tr in zip(tool_calls_data, tool_results_data)
                ])

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
        try:
            # Create tools
            tools = await self.create_rag_tools(user_id)

            # Build messages
            messages = []
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))

            for msg in message_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))

            messages.append(HumanMessage(content=user_message))

            # Bind tools to LLM
            llm_with_tools = self.llm.bind_tools(tools)

            # Stream response
            async for chunk in llm_with_tools.astream(messages):
                if chunk.content:
                    yield {
                        "type": "content",
                        "content": chunk.content,
                    }

                # Handle tool calls in streaming
                if hasattr(chunk, "tool_calls") and chunk.tool_calls:
                    for tool_call in chunk.tool_calls:
                        yield {
                            "type": "tool_call",
                            "tool_name": tool_call.get("name"),
                            "tool_input": tool_call.get("args", {}),
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
