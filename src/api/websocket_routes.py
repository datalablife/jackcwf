"""WebSocket routes for real-time AI conversations."""

import asyncio
import json
import logging
from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.config import get_async_session
from src.services.conversation_service import ConversationService
from src.services.agent_service import AgentService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """
    Manages WebSocket connections for real-time communication.

    Handles connection lifecycle, message broadcasting, and cleanup.
    """

    def __init__(self):
        """Initialize connection manager."""
        # Active connections: {conversation_id: {user_id: websocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, conversation_id: str, user_id: str):
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: WebSocket connection
            conversation_id: Conversation ID
            user_id: User ID
        """
        await websocket.accept()

        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = {}

        self.active_connections[conversation_id][user_id] = websocket

        logger.info(f"WebSocket connected: user={user_id}, conversation={conversation_id}")

    def disconnect(self, conversation_id: str, user_id: str):
        """
        Remove a WebSocket connection.

        Args:
            conversation_id: Conversation ID
            user_id: User ID
        """
        if conversation_id in self.active_connections:
            if user_id in self.active_connections[conversation_id]:
                del self.active_connections[conversation_id][user_id]

            # Clean up empty conversation
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]

        logger.info(f"WebSocket disconnected: user={user_id}, conversation={conversation_id}")

    async def send_message(self, websocket: WebSocket, message: dict):
        """
        Send a message to a specific WebSocket.

        Args:
            websocket: WebSocket connection
            message: Message dict to send
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {str(e)}")

    async def broadcast_to_conversation(self, conversation_id: str, message: dict):
        """
        Broadcast a message to all connections in a conversation.

        Args:
            conversation_id: Conversation ID
            message: Message dict to broadcast
        """
        if conversation_id not in self.active_connections:
            return

        for user_id, websocket in self.active_connections[conversation_id].items():
            await self.send_message(websocket, message)


# Global connection manager
manager = ConnectionManager()


async def get_session() -> AsyncSession:
    """Get database session for WebSocket handlers."""
    async for session in get_async_session():
        return session


@router.websocket("/ws/conversations/{conversation_id}")
async def websocket_conversation(
    websocket: WebSocket,
    conversation_id: UUID,
):
    """
    WebSocket endpoint for real-time conversation with AI agent.

    **Connection Flow:**
    1. Client connects to WebSocket
    2. Server validates conversation ownership
    3. Server loads conversation context
    4. Server sends ready message
    5. Client sends user messages
    6. Server streams agent responses

    **Message Formats:**

    **Client -> Server:**
    ```json
    {
        "type": "message",
        "content": "User message text",
        "include_rag": true,
        "user_id": "user123"
    }
    ```

    **Client -> Server (ping):**
    ```json
    {
        "type": "ping"
    }
    ```

    **Server -> Client (ready):**
    ```json
    {
        "type": "ready",
        "conversation_id": "uuid",
        "message": "Connected to conversation"
    }
    ```

    **Server -> Client (thinking):**
    ```json
    {
        "type": "agent_thinking",
        "content": "Partial thinking content...",
        "done": false
    }
    ```

    **Server -> Client (tool call):**
    ```json
    {
        "type": "tool_call",
        "tool_name": "search_documents",
        "tool_input": {"query": "..."},
        "call_id": "call_123"
    }
    ```

    **Server -> Client (tool result):**
    ```json
    {
        "type": "tool_result",
        "call_id": "call_123",
        "result": "Tool output..."
    }
    ```

    **Server -> Client (response):**
    ```json
    {
        "type": "response",
        "content": "Agent response text",
        "done": false
    }
    ```

    **Server -> Client (complete):**
    ```json
    {
        "type": "complete",
        "message_id": "uuid",
        "tokens_used": 150
    }
    ```

    **Server -> Client (error):**
    ```json
    {
        "type": "error",
        "error": "Error message"
    }
    ```

    **Server -> Client (pong):**
    ```json
    {
        "type": "pong"
    }
    ```

    **Performance:**
    - Streaming responses for better UX
    - Heartbeat every 30 seconds
    - Auto-reconnect on disconnect

    **Security:**
    - User ownership verified before connection
    - User ID extracted from message (in production, use JWT)
    """
    session = None
    user_id = None

    try:
        # Accept connection first
        await websocket.accept()

        # Wait for initial message with user_id
        initial_data = await websocket.receive_json()

        if "user_id" not in initial_data:
            await websocket.send_json({
                "type": "error",
                "error": "user_id required in first message",
            })
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        user_id = initial_data["user_id"]

        # Get database session
        session = await anext(get_async_session())

        # Verify user owns the conversation
        conv_service = ConversationService(session)
        conversation = await conv_service.conv_repo.get_user_conversation(
            user_id,
            conversation_id
        )

        if not conversation:
            await websocket.send_json({
                "type": "error",
                "error": "Conversation not found or access denied",
            })
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Register connection
        await manager.connect(websocket, str(conversation_id), user_id)

        # Load conversation context
        messages, total_tokens = await conv_service.msg_repo.get_messages_with_tokens(
            conversation_id
        )

        # Format message history for agent
        message_history = [
            {
                "role": msg.role,
                "content": msg.content,
            }
            for msg in messages[-20:]  # Last 20 messages for context
        ]

        # Send ready message
        await websocket.send_json({
            "type": "ready",
            "conversation_id": str(conversation_id),
            "message": "Connected to conversation",
            "message_count": len(messages),
            "total_tokens": total_tokens,
        })

        # Start heartbeat task
        heartbeat_task = asyncio.create_task(
            heartbeat_loop(websocket, str(conversation_id), user_id)
        )

        # Handle messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_json()

                message_type = data.get("type")

                if message_type == "ping":
                    # Respond to ping
                    await websocket.send_json({"type": "pong"})
                    continue

                elif message_type == "message":
                    # Process user message
                    await process_user_message(
                        websocket=websocket,
                        conversation_id=conversation_id,
                        user_id=user_id,
                        session=session,
                        user_message=data.get("content", ""),
                        include_rag=data.get("include_rag", True),
                        conversation=conversation,
                        message_history=message_history,
                    )

                    # Reload message history after processing
                    messages, total_tokens = await conv_service.msg_repo.get_messages_with_tokens(
                        conversation_id
                    )
                    message_history = [
                        {"role": msg.role, "content": msg.content}
                        for msg in messages[-20:]
                    ]

                else:
                    await websocket.send_json({
                        "type": "error",
                        "error": f"Unknown message type: {message_type}",
                    })

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for conversation {conversation_id}")
                break

        # Cancel heartbeat
        heartbeat_task.cancel()

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for conversation {conversation_id}")

    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "error": f"Internal error: {str(e)}",
            })
        except:
            pass

    finally:
        # Clean up
        if user_id:
            manager.disconnect(str(conversation_id), user_id)

        if session:
            await session.close()


async def process_user_message(
    websocket: WebSocket,
    conversation_id: UUID,
    user_id: str,
    session: AsyncSession,
    user_message: str,
    include_rag: bool,
    conversation: Any,
    message_history: list,
):
    """
    Process a user message and stream agent response.

    Args:
        websocket: WebSocket connection
        conversation_id: Conversation ID
        user_id: User ID
        session: Database session
        user_message: User's message content
        include_rag: Whether to include RAG search
        conversation: Conversation object
        message_history: Recent message history
    """
    try:
        conv_service = ConversationService(session)
        agent_service = AgentService(session)

        # Save user message
        user_msg = await conv_service.add_message(
            conversation_id=conversation_id,
            role="user",
            content=user_message,
        )

        logger.info(f"Saved user message {user_msg.id} in conversation {conversation_id}")

        # Send acknowledgment
        await websocket.send_json({
            "type": "message_received",
            "message_id": str(user_msg.id),
        })

        # Send agent thinking indicator
        await websocket.send_json({
            "type": "agent_thinking",
            "content": "Processing your message...",
            "done": False,
        })

        final_state = None

        async for event in agent_service.stream_message(
            user_id=user_id,
            conversation_id=str(conversation_id),
            user_message=user_message,
            system_prompt=conversation.system_prompt,
            message_history=message_history,
        ):
            event_type = event.get("type")

            if event_type == "content":
                await websocket.send_json({
                    "type": "response",
                    "content": event.get("content", ""),
                    "done": False,
                })
            elif event_type == "tool_call":
                await websocket.send_json({
                    "type": "tool_call",
                    "tool_name": event.get("tool_name"),
                    "tool_input": event.get("tool_input"),
                    "call_id": event.get("call_id"),
                })
            elif event_type == "tool_result":
                await websocket.send_json({
                    "type": "tool_result",
                    "call_id": event.get("call_id"),
                    "result": event.get("result"),
                })
            elif event_type == "complete_state":
                final_state = event
            elif event_type == "error":
                await websocket.send_json(event)

        await websocket.send_json({
            "type": "agent_thinking",
            "content": "Generating response...",
            "done": True,
        })

        if not final_state:
            raise RuntimeError("Agent stream did not provide completion data")

        # Save assistant message
        assistant_msg = await conv_service.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=final_state.get("response", "I processed your message."),
            tool_calls=final_state.get("tool_calls"),
            tool_results=final_state.get("tool_results"),
            tokens_used=final_state.get("tokens_used"),
        )

        # Send completion
        await websocket.send_json({
            "type": "complete",
            "message_id": str(assistant_msg.id),
            "tokens_used": final_state.get("tokens_used", 0),
        })

        logger.info(f"Completed processing message in conversation {conversation_id}")

    except Exception as e:
        logger.error(f"Error processing user message: {str(e)}", exc_info=True)
        await websocket.send_json({
            "type": "error",
            "error": f"Failed to process message: {str(e)}",
        })


async def heartbeat_loop(websocket: WebSocket, conversation_id: str, user_id: str):
    """
    Send periodic heartbeat messages to keep connection alive.

    Args:
        websocket: WebSocket connection
        conversation_id: Conversation ID
        user_id: User ID
    """
    try:
        while True:
            await asyncio.sleep(30)  # Send heartbeat every 30 seconds

            try:
                await websocket.send_json({"type": "heartbeat"})
            except:
                # Connection closed
                logger.info(f"Heartbeat failed for conversation {conversation_id}, closing")
                manager.disconnect(conversation_id, user_id)
                break

    except asyncio.CancelledError:
        logger.info(f"Heartbeat loop cancelled for conversation {conversation_id}")
