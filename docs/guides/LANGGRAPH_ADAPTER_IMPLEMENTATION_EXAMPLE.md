# LangGraph Adapter 实现示例

**仅当采用 Agent-Chat-UI 时使用此文档**

---

## 概述

本文档提供创建 LangGraph Adapter 层的完整实现示例，用于将您的 FastAPI 后端适配到 Agent-Chat-UI 期望的 LangGraph 协议。

---

## 1. 项目结构

```
src/
├── adapters/
│   ├── __init__.py
│   ├── langgraph_adapter.py          # 核心适配器
│   ├── protocol_translator.py         # 协议转换器
│   ├── state_converter.py             # 状态转换器
│   └── streaming_converter.py         # 流式格式转换
├── api/
│   ├── langgraph_compat_routes.py    # LangGraph 兼容端点
│   └── ...
├── services/
│   └── ...
└── ...
```

---

## 2. 核心适配器实现

### 文件: `/src/adapters/langgraph_adapter.py`

```python
"""
LangGraph Protocol Adapter

将 FastAPI 后端适配到 LangGraph 协议
- Protocol Translation (FastAPI ↔ LangGraph)
- State Conversion (DB Models ↔ MessagesState)
- Streaming Format Conversion
- Tool Execution Translation
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, AsyncIterator
from enum import Enum

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    ToolMessage,
    SystemMessage,
)

from src.models import Message as DBMessage, Conversation


class MessageRole(str, Enum):
    """Message roles."""
    HUMAN = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    SYSTEM = "system"


class LangGraphProtocolAdapter:
    """
    适配器层：FastAPI ↔ LangGraph Protocol

    职责:
    1. 将 LangGraph API 请求转换为内部格式
    2. 将内部状态转换为 LangGraph 格式
    3. 转换流式事件格式
    4. 管理工具执行的转换
    """

    # =========================================================================
    # 1. REQUEST TRANSLATION (LangGraph → FastAPI)
    # =========================================================================

    @staticmethod
    def translate_create_run_request(request: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换 LangGraph CreateRun 请求为内部格式

        Input (从 Agent-Chat-UI):
        {
          "assistant_id": "asst-123",
          "input": { "message": "Hello world" },
          "metadata": { "user_id": "user-123" }
        }

        Output (给 ConversationService):
        {
          "user_input": "Hello world",
          "conversation_id": "conv-123",
          "assistant_id": "asst-123",
          "metadata": { "user_id": "user-123" }
        }
        """
        return {
            "user_input": request.get("input", {}).get("message", ""),
            "assistant_id": request.get("assistant_id"),
            "metadata": request.get("metadata", {}),
            "thread_id": request.get("thread_id"),  # Maps to conversation_id
        }

    @staticmethod
    def translate_stream_request(
        request: Dict[str, Any],
    ) -> Dict[str, Any]:
        """转换流式请求参数。"""
        return {
            "conversation_id": request.get("thread_id"),
            "include_thinking": request.get("include_thinking", False),
            "context_window": request.get("context_window", 10),
        }

    # =========================================================================
    # 2. STATE CONVERSION (DB Models ↔ MessagesState)
    # =========================================================================

    @staticmethod
    def db_messages_to_langchain_messages(
        db_messages: List[DBMessage],
    ) -> List[BaseMessage]:
        """
        将数据库 Message 记录转换为 LangChain Message 对象。

        这是关键转换，因为 Agent-Chat-UI 期望 MessagesState 格式。

        Args:
            db_messages: 数据库中存储的消息列表

        Returns:
            LangChain BaseMessage 列表 (HumanMessage, AIMessage, ToolMessage, etc.)
        """
        messages: List[BaseMessage] = []

        for msg in db_messages:
            if msg.role == MessageRole.HUMAN.value:
                # 用户消息
                messages.append(
                    HumanMessage(
                        content=msg.content,
                        id=str(msg.id),
                    )
                )

            elif msg.role == MessageRole.ASSISTANT.value:
                # 助手消息 - 可能包含工具调用
                content = msg.content

                # 如果有工具调用，构建 content_blocks 格式
                if msg.tool_calls:
                    content = [
                        {
                            "type": "text",
                            "text": msg.content,
                        },
                        *[
                            {
                                "type": "tool_use",
                                "id": tc.get("id", str(uuid.uuid4())),
                                "name": tc.get("name"),
                                "input": tc.get("input", {}),
                            }
                            for tc in msg.tool_calls
                        ]
                    ]

                messages.append(
                    AIMessage(
                        content=content,
                        tool_calls=[
                            {
                                "id": tc.get("id", str(uuid.uuid4())),
                                "name": tc.get("name"),
                                "args": tc.get("input", {}),
                            }
                            for tc in (msg.tool_calls or [])
                        ],
                        id=str(msg.id),
                    )
                )

            elif msg.role == MessageRole.TOOL.value:
                # 工具结果消息
                messages.append(
                    ToolMessage(
                        content=msg.content,
                        tool_call_id=msg.metadata.get("tool_call_id"),
                        name=msg.metadata.get("tool_name"),
                        id=str(msg.id),
                    )
                )

            elif msg.role == MessageRole.SYSTEM.value:
                # 系统消息
                messages.append(
                    SystemMessage(
                        content=msg.content,
                        id=str(msg.id),
                    )
                )

        return messages

    @staticmethod
    def langchain_messages_to_db_messages(
        conversation_id: str,
        messages: List[BaseMessage],
        user_id: str,
    ) -> List[Dict[str, Any]]:
        """
        将 LangChain Message 对象转换为数据库格式。

        Used when saving messages back to database after Agent execution.
        """
        db_messages = []

        for msg in messages:
            # Determine role
            if isinstance(msg, HumanMessage):
                role = MessageRole.HUMAN.value
                tool_calls = None
            elif isinstance(msg, AIMessage):
                role = MessageRole.ASSISTANT.value
                # Extract tool_calls if present
                tool_calls = None
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    tool_calls = [
                        {
                            "id": tc.get("id"),
                            "name": tc.get("name"),
                            "input": tc.get("args", {}),
                        }
                        for tc in msg.tool_calls
                    ]
            elif isinstance(msg, ToolMessage):
                role = MessageRole.TOOL.value
                tool_calls = None
            elif isinstance(msg, SystemMessage):
                role = MessageRole.SYSTEM.value
                tool_calls = None
            else:
                continue

            # Extract content
            content = msg.content
            if isinstance(content, list):
                # Convert content_blocks to string
                text_parts = [
                    block.get("text")
                    for block in content
                    if isinstance(block, dict) and block.get("type") == "text"
                ]
                content = "".join(text_parts)

            db_messages.append({
                "conversation_id": conversation_id,
                "role": role,
                "content": str(content),
                "tool_calls": tool_calls,
                "user_id": user_id,
            })

        return db_messages

    # =========================================================================
    # 3. RESPONSE TRANSLATION (FastAPI → LangGraph)
    # =========================================================================

    @staticmethod
    def translate_create_run_response(
        message_id: str,
        conversation_id: str,
        thread_id: str,
    ) -> Dict[str, Any]:
        """
        转换创建 Run 的响应为 LangGraph 格式。

        Output (给 Agent-Chat-UI):
        {
          "run_id": "run-123",
          "thread_id": "thread-123",
          "status": "completed",
          "created_at": "2024-01-15T10:30:00Z"
        }
        """
        return {
            "run_id": message_id,
            "thread_id": thread_id,
            "status": "completed",
            "created_at": datetime.utcnow().isoformat() + "Z",
        }

    @staticmethod
    def translate_run_status_response(
        status: str,
        run_id: str,
        messages: List[BaseMessage],
    ) -> Dict[str, Any]:
        """获取 Run 状态响应。"""
        return {
            "run_id": run_id,
            "status": status,
            "messages": [
                {
                    "role": "user" if isinstance(m, HumanMessage) else "assistant",
                    "content": m.content,
                }
                for m in messages
            ],
        }

    # =========================================================================
    # 4. STREAMING FORMAT CONVERSION
    # =========================================================================

    @staticmethod
    def translate_to_content_blocks_event(
        chunk: str,
        index: int = 0,
    ) -> str:
        """
        将文本块转换为 LangGraph content_blocks 格式。

        Output (Server-Sent Events):
        event: content_blocks_delta
        data: {
          "type": "content_blocks_delta",
          "index": 0,
          "delta": {
            "type": "text_delta",
            "text": "Hello..."
          }
        }
        """
        event_data = {
            "type": "content_blocks_delta",
            "index": index,
            "delta": {
                "type": "text_delta",
                "text": chunk,
            }
        }
        return f"event: content_blocks_delta\ndata: {json.dumps(event_data)}\n\n"

    @staticmethod
    def translate_to_tool_call_event(
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_use_id: str,
    ) -> str:
        """
        将工具调用转换为 LangGraph 格式。

        Output (Server-Sent Events):
        event: content_blocks_delta
        data: {
          "type": "content_blocks_delta",
          "index": 0,
          "delta": {
            "type": "tool_use_delta",
            "id": "tool-123",
            "name": "search",
            "input": {...}
          }
        }
        """
        event_data = {
            "type": "content_blocks_delta",
            "index": 0,
            "delta": {
                "type": "tool_use_delta",
                "id": tool_use_id,
                "name": tool_name,
                "input": tool_input,
            }
        }
        return f"event: content_blocks_delta\ndata: {json.dumps(event_data)}\n\n"

    @staticmethod
    def translate_to_message_event(
        message_id: str,
        role: str,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        将完整消息转换为 LangGraph message 事件。

        Output (Server-Sent Events):
        event: message
        data: {
          "id": "msg-123",
          "type": "message",
          "role": "assistant",
          "content": [
            { "type": "text", "text": "Response..." },
            { "type": "tool_use", "id": "call-1", "name": "search", "input": {...} }
          ]
        }
        """
        content_blocks = [
            {
                "type": "text",
                "text": content,
            }
        ]

        if tool_calls:
            content_blocks.extend([
                {
                    "type": "tool_use",
                    "id": tc.get("id"),
                    "name": tc.get("name"),
                    "input": tc.get("input", {}),
                }
                for tc in tool_calls
            ])

        event_data = {
            "id": message_id,
            "type": "message",
            "role": role,
            "content": content_blocks,
        }
        return f"event: message\ndata: {json.dumps(event_data)}\n\n"

    # =========================================================================
    # 5. ERROR HANDLING
    # =========================================================================

    @staticmethod
    def translate_error(
        error_code: str,
        error_message: str,
        recoverable: bool = True,
    ) -> str:
        """
        转换错误为 LangGraph 兼容的错误事件。

        Output (Server-Sent Events):
        event: error
        data: {
          "type": "error",
          "code": "tool_execution_failed",
          "message": "...",
          "recoverable": true
        }
        """
        event_data = {
            "type": "error",
            "code": error_code,
            "message": error_message,
            "recoverable": recoverable,
        }
        return f"event: error\ndata: {json.dumps(event_data)}\n\n"
```

---

## 3. 兼容路由实现

### 文件: `/src/api/langgraph_compat_routes.py`

```python
"""
LangGraph Compatible Routes

提供与 LangGraph 部署 API 兼容的端点
"""

import asyncio
import logging
from typing import Dict, Any, AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.config import get_async_session
from src.adapters.langgraph_adapter import LangGraphProtocolAdapter
from src.services.conversation_service import ConversationService
from src.services.agent_service import AgentService
from src.repositories.message import MessageRepository
from src.middleware.auth_middleware import verify_jwt_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/threads", tags=["LangGraph Compat"])


# =========================================================================
# 1. CREATE RUN (创建执行)
# =========================================================================

@router.post("/{thread_id}/runs")
async def create_run(
    thread_id: str,
    request: Dict[str, Any],
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(verify_jwt_token),
):
    """
    创建 Run - LangGraph 兼容端点

    Maps to: POST /api/conversations/{conversation_id}/send

    Request:
    {
      "assistant_id": "asst-123",
      "input": { "message": "Hello" },
      "metadata": { ... }
    }

    Response:
    {
      "run_id": "run-123",
      "thread_id": "thread-123",
      "status": "completed"
    }
    """
    try:
        # 1. 转换请求
        internal_request = LangGraphProtocolAdapter.translate_create_run_request({
            **request,
            "thread_id": thread_id,
        })

        # 2. 获取或创建对话
        conv_service = ConversationService(session)
        conversation = await conv_service.get_conversation(UUID(thread_id), user_id)

        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )

        # 3. 调用 Agent
        agent_service = AgentService(session)
        response = await agent_service.invoke({
            "user_input": internal_request["user_input"],
            "conversation_id": str(conversation.id),
            "user_id": str(user_id),
        })

        # 4. 返回 LangGraph 格式响应
        return LangGraphProtocolAdapter.translate_create_run_response(
            message_id=response.get("message_id", ""),
            conversation_id=str(conversation.id),
            thread_id=thread_id,
        )

    except Exception as e:
        logger.error(f"Error creating run: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create run: {str(e)}"
        )


# =========================================================================
# 2. STREAM RUN (流式获取执行结果)
# =========================================================================

@router.get("/{thread_id}/runs/{run_id}/stream")
async def stream_run(
    thread_id: str,
    run_id: str,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(verify_jwt_token),
):
    """
    流式获取 Run 结果 - LangGraph 兼容

    Returns: Server-Sent Events 流，包含 content_blocks 格式

    Response Events:
    - content_blocks_delta: 文本增量
    - content_blocks_delta: 工具调用
    - message: 完整消息
    - error: 错误事件
    """

    async def event_generator() -> AsyncGenerator[str, None]:
        """生成流事件。"""
        try:
            # 1. 获取消息记录
            msg_repo = MessageRepository(session)
            messages = await msg_repo.get_conversation_messages(
                conversation_id=UUID(thread_id),
                limit=100,
            )

            # 2. 转换为 LangChain 格式
            adapter = LangGraphProtocolAdapter()
            langchain_messages = adapter.db_messages_to_langchain_messages(messages)

            # 3. 获取最后的助手消息
            if not langchain_messages:
                yield adapter.translate_error(
                    error_code="no_messages",
                    error_message="No messages found",
                )
                return

            last_message = langchain_messages[-1]

            # 4. 流式发送内容块
            content = last_message.content
            if isinstance(content, str):
                # 分块流式发送文本
                chunk_size = 20  # 字符
                for i in range(0, len(content), chunk_size):
                    chunk = content[i:i + chunk_size]
                    yield adapter.translate_to_content_blocks_event(chunk)
                    await asyncio.sleep(0.01)  # 模拟网络延迟

            elif isinstance(content, list):
                # 处理 content_blocks
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            text = block.get("text", "")
                            chunk_size = 20
                            for i in range(0, len(text), chunk_size):
                                chunk = text[i:i + chunk_size]
                                yield adapter.translate_to_content_blocks_event(chunk)
                                await asyncio.sleep(0.01)

                        elif block.get("type") == "tool_use":
                            yield adapter.translate_to_tool_call_event(
                                tool_name=block.get("name", "unknown"),
                                tool_input=block.get("input", {}),
                                tool_use_id=block.get("id", ""),
                            )

            # 5. 发送完整消息事件
            yield adapter.translate_to_message_event(
                message_id=run_id,
                role="assistant",
                content=content if isinstance(content, str) else "",
                tool_calls=getattr(last_message, "tool_calls", None),
            )

        except Exception as e:
            logger.error(f"Error streaming run: {str(e)}")
            adapter = LangGraphProtocolAdapter()
            yield adapter.translate_error(
                error_code="stream_error",
                error_message=str(e),
                recoverable=True,
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )


# =========================================================================
# 3. GET RUN STATUS (获取 Run 状态)
# =========================================================================

@router.get("/{thread_id}/runs/{run_id}")
async def get_run(
    thread_id: str,
    run_id: str,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(verify_jwt_token),
):
    """
    获取 Run 状态 - LangGraph 兼容

    Response:
    {
      "run_id": "run-123",
      "thread_id": "thread-123",
      "status": "completed",
      "messages": [...]
    }
    """
    try:
        # 1. 获取消息
        msg_repo = MessageRepository(session)
        messages = await msg_repo.get_conversation_messages(
            conversation_id=UUID(thread_id),
            limit=1,
        )

        if not messages:
            raise HTTPException(status_code=404, detail="Run not found")

        # 2. 转换为 LangChain 格式
        adapter = LangGraphProtocolAdapter()
        langchain_messages = adapter.db_messages_to_langchain_messages(messages)

        # 3. 返回 LangGraph 格式
        return adapter.translate_run_status_response(
            status="completed",
            run_id=run_id,
            messages=langchain_messages,
        )

    except Exception as e:
        logger.error(f"Error getting run: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================================
# 4. LIST RUNS (列出 Runs)
# =========================================================================

@router.get("/{thread_id}/runs")
async def list_runs(
    thread_id: str,
    limit: int = 10,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(verify_jwt_token),
):
    """
    列出线程的所有 Runs - LangGraph 兼容

    Response:
    {
      "runs": [
        {
          "run_id": "run-1",
          "created_at": "2024-01-15T10:30:00Z",
          "status": "completed"
        }
      ]
    }
    """
    try:
        msg_repo = MessageRepository(session)
        messages = await msg_repo.get_conversation_messages(
            conversation_id=UUID(thread_id),
            limit=limit,
        )

        return {
            "runs": [
                {
                    "run_id": str(msg.id),
                    "created_at": msg.created_at.isoformat() + "Z",
                    "status": "completed",
                }
                for msg in messages
            ]
        }

    except Exception as e:
        logger.error(f"Error listing runs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 4. 单元测试

### 文件: `/tests/test_langgraph_adapter.py`

```python
"""
Tests for LangGraph Adapter
"""

import pytest
from datetime import datetime
from uuid import UUID

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from src.adapters.langgraph_adapter import LangGraphProtocolAdapter
from src.models import Message as DBMessage


class TestLangGraphProtocolAdapter:
    """Test the LangGraph adapter."""

    def test_translate_create_run_request(self):
        """Test translating CreateRun request."""
        request = {
            "assistant_id": "asst-123",
            "input": {"message": "Hello world"},
            "metadata": {"user_id": "user-123"},
            "thread_id": "thread-456",
        }

        result = LangGraphProtocolAdapter.translate_create_run_request(request)

        assert result["user_input"] == "Hello world"
        assert result["assistant_id"] == "asst-123"
        assert result["thread_id"] == "thread-456"
        assert result["metadata"]["user_id"] == "user-123"

    def test_db_messages_to_langchain_messages(self):
        """Test converting DB messages to LangChain format."""
        db_messages = [
            DBMessage(
                id=UUID("12345678-1234-5678-1234-567812345678"),
                conversation_id=UUID("87654321-4321-8765-4321-876543218765"),
                role="user",
                content="Hello",
                tool_calls=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
            DBMessage(
                id=UUID("12345678-1234-5678-1234-567812345679"),
                conversation_id=UUID("87654321-4321-8765-4321-876543218765"),
                role="assistant",
                content="Hi there!",
                tool_calls=[
                    {
                        "id": "call-1",
                        "name": "search",
                        "input": {"query": "test"},
                    }
                ],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
        ]

        messages = LangGraphProtocolAdapter.db_messages_to_langchain_messages(db_messages)

        assert len(messages) == 2
        assert isinstance(messages[0], HumanMessage)
        assert messages[0].content == "Hello"
        assert isinstance(messages[1], AIMessage)
        assert "Hi there!" in str(messages[1].content)

    def test_translate_to_content_blocks_event(self):
        """Test converting text to content_blocks event."""
        event = LangGraphProtocolAdapter.translate_to_content_blocks_event(
            "Hello world"
        )

        assert "content_blocks_delta" in event
        assert "Hello world" in event
        assert "text_delta" in event

    def test_translate_to_tool_call_event(self):
        """Test converting tool call to content_blocks event."""
        event = LangGraphProtocolAdapter.translate_to_tool_call_event(
            tool_name="search",
            tool_input={"query": "test"},
            tool_use_id="call-1",
        )

        assert "content_blocks_delta" in event
        assert "tool_use_delta" in event
        assert "search" in event
        assert "call-1" in event

    def test_translate_to_message_event(self):
        """Test converting message to message event."""
        event = LangGraphProtocolAdapter.translate_to_message_event(
            message_id="msg-123",
            role="assistant",
            content="Hello",
            tool_calls=[
                {
                    "id": "call-1",
                    "name": "search",
                    "input": {"query": "test"},
                }
            ],
        )

        assert "event: message" in event
        assert "msg-123" in event
        assert "assistant" in event
        assert "Hello" in event
        assert "search" in event
```

---

## 5. 集成清单

### 实现顺序

```
Week 1: Protocol & State Conversion
├─ [ ] 实现 LangGraphProtocolAdapter (40h)
├─ [ ] 添加 langgraph_compat_routes.py 端点 (30h)
├─ [ ] 编写单元测试 (20h)
└─ [ ] 集成测试 (10h)

Week 2: Streaming & Tool Integration
├─ [ ] 实现 streaming format conversion (20h)
├─ [ ] 添加 tool execution translation (20h)
├─ [ ] 测试流式响应 (15h)
└─ [ ] 测试工具调用 (15h)

Week 3: Frontend Integration
├─ [ ] 集成 @langchain/langgraph-sdk (20h)
├─ [ ] 更新 Agent-Chat-UI 配置 (15h)
├─ [ ] 端到端集成测试 (20h)
└─ [ ] 性能优化 (15h)
```

### 部署检查清单

- [ ] 所有适配器端点测试通过
- [ ] 流式响应格式验证
- [ ] 工具执行兼容性验证
- [ ] RAG 集成测试
- [ ] 缓存系统集成测试
- [ ] 性能基准测试
- [ ] 安全审计
- [ ] 文档完成

---

## 6. 常见问题

### Q: 如何处理大型消息?
**A**: 在 `translate_to_content_blocks_event` 中添加分块逻辑，流式发送。

### Q: 如何处理并行工具执行?
**A**: 在 `wrap_tool_call` 中间件中使用 `asyncio.gather()`，然后逐个转换结果。

### Q: 如何处理错误恢复?
**A**: 使用 `translate_error` 方法，设置 `recoverable=True`，前端可以重试。

### Q: 与现有中间件冲突吗?
**A**: 不会。Adapter 层在 API 边界，中间件继续工作。

---

**提醒**: 这仅在采用 Agent-Chat-UI 时有用。**强烈建议继续使用 Vite 前端**。

