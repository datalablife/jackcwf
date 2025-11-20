# Phase 2 流式 LLM 响应优化 - 实现规划

**启动时间**: 2025-11-20
**预期完成**: 2025-11-21 (4 小时)
**优先级**: P0 (关键)
**预期成果**: 首字节延迟 -81% (550ms → 100ms)

---

## 🎯 执行摘要

Phase 2 流式 LLM 响应优化旨在通过 Server-Sent Events (SSE) 实现实时流式传输，大幅改善用户感知延迟。这是提升用户体验的关键优化。

### 关键指标

| 指标 | 当前 | 目标 | 改进 |
|------|------|------|------|
| **首字节延迟** | 550ms | 100ms | **-81%** ✅ |
| **用户感知延迟** | 高 | 低 | **显著** ✅ |
| **块吞吐量** | N/A | >50/sec | **新增** ✅ |
| **内存占用** | N/A | <20MB | **目标** ✅ |

---

## 📐 技术架构设计

### 流式响应管道

```
用户请求
    ↓
┌─────────────────────────────────────────┐
│ POST /api/v1/conversations/{id}/stream  │
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│ StreamingChatService                    │
│  ├─ 初始化对话上下文                     │
│  ├─ 加载缓存的消息历史                   │
│  └─ 准备 LangChain Agent                │
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│ LangChain Agent (流式模式)                │
│  ├─ 流式输入处理                         │
│  ├─ 工具调用流式输出                     │
│  └─ 最终响应生成                        │
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│ SSE 事件缓冲区                            │
│  ├─ message_chunk (50-100 tokens)       │
│  ├─ tool_call                           │
│  ├─ tool_result                         │
│  └─ complete_state                      │
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│ HTTP Response (SSE)                      │
│  data: {"type": "message_chunk", ...}   │
│  data: {"type": "tool_call", ...}       │
│  data: {"type": "complete_state", ...}  │
└────────────┬────────────────────────────┘
             ↓
浏览器 (实时渲染)
```

### 核心组件

```
src/
├─ api/
│  ├─ streaming_routes.py          (新建 - SSE 端点)
│  │  └─ POST /api/v1/conversations/{id}/stream
│  │  └─ OPTIONS /api/v1/conversations/{id}/stream
│  │
│  └─ existing routes (修改)
│     └─ 保留非流式端点向后兼容
│
├─ services/
│  ├─ streaming_chat_service.py    (新建 - 流式聊天服务)
│  │  └─ StreamingChatService
│  │  ├─ stream_agent_response()
│  │  ├─ _build_streaming_agent()
│  │  └─ _format_stream_event()
│  │
│  └─ existing services (修改)
│     └─ SemanticCacheService 集成
│     └─ AgentService 流式支持
│
├─ models/
│  ├─ streaming_models.py          (新建 - 数据模型)
│  │  └─ StreamEvent
│  │  ├─ MessageChunkEvent
│  │  ├─ ToolCallEvent
│  │  ├─ ToolResultEvent
│  │  └─ CompleteStateEvent
│  │
│  └─ existing models (兼容)
│
└─ infrastructure/
   ├─ streaming_metrics.py          (新建 - 流式指标)
   │  └─ 首字节延迟追踪
   │  └─ 块吞吐量计数
   │  └─ 内存使用监控
   │
   └─ existing metrics (扩展)
      └─ Prometheus 指标集成
```

---

## 🛠️ 实现步骤 (4 小时)

### Step 1: 创建数据模型 (30 分钟)

**文件**: `src/models/streaming_models.py`

```python
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum

class StreamEventType(str, Enum):
    """流式事件类型"""
    MESSAGE_CHUNK = "message_chunk"        # 文本块
    TOOL_CALL = "tool_call"                # 工具调用
    TOOL_RESULT = "tool_result"            # 工具结果
    THINKING = "thinking"                  # 思考过程
    COMPLETE_STATE = "complete_state"      # 完成状态
    ERROR = "error"                        # 错误

class StreamEvent(BaseModel):
    """基础流式事件"""
    type: StreamEventType
    timestamp: float
    sequence: int

class MessageChunkEvent(StreamEvent):
    """消息块事件"""
    type: StreamEventType = StreamEventType.MESSAGE_CHUNK
    content: str                            # 文本块内容
    token_count: int                        # Token 数
    is_final: bool = False                 # 是否最后一块

class ToolCallEvent(StreamEvent):
    """工具调用事件"""
    type: StreamEventType = StreamEventType.TOOL_CALL
    tool_name: str                         # 工具名称
    tool_input: Dict[str, Any]             # 工具输入参数

class ToolResultEvent(StreamEvent):
    """工具结果事件"""
    type: StreamEventType = StreamEventType.TOOL_RESULT
    tool_name: str
    result: Any                            # 工具执行结果

class CompleteStateEvent(StreamEvent):
    """完成状态事件"""
    type: StreamEventType = StreamEventType.COMPLETE_STATE
    final_message: str                     # 最终消息
    total_tokens: int                      # 总 Token 数
    total_chunks: int                      # 总块数
    elapsed_time: float                    # 耗时 (秒)
```

### Step 2: 创建流式聊天服务 (90 分钟)

**文件**: `src/services/streaming_chat_service.py`

```python
import asyncio
import json
import time
from typing import AsyncGenerator, Dict, Any, Optional
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.messages import HumanMessage
from src.models.streaming_models import (
    StreamEvent, MessageChunkEvent, ToolCallEvent,
    ToolResultEvent, CompleteStateEvent, StreamEventType
)
from src.services.agent_service import AgentService
from src.services.semantic_cache import SemanticCacheService
import logging

logger = logging.getLogger(__name__)

class StreamingCallbackHandler(BaseCallbackHandler):
    """LangChain 流式回调处理器"""

    def __init__(self):
        self.chunks = []
        self.current_content = ""

    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        """处理新 Token"""
        self.current_content += token
        self.chunks.append(token)

    async def on_tool_start(self, tool: str, input: Dict[str, Any], **kwargs) -> None:
        """工具调用开始"""
        logger.info(f"Tool started: {tool}")

    async def on_tool_end(self, output: str, **kwargs) -> None:
        """工具调用结束"""
        logger.info(f"Tool ended with output: {output[:100]}")

class StreamingChatService:
    """流式聊天服务"""

    def __init__(self, agent_service: AgentService, cache_service: SemanticCacheService):
        self.agent_service = agent_service
        self.cache_service = cache_service
        self.chunk_buffer = []
        self.buffer_size = 50  # Token 数

    async def stream_agent_response(
        self,
        conversation_id: str,
        user_message: str,
        user_id: str,
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        流式生成 Agent 响应

        首字节延迟目标: <100ms
        块吞吐量目标: >50 chunks/sec
        """

        start_time = time.time()
        sequence = 0
        total_tokens = 0
        total_chunks = 0

        try:
            # 1. 加载对话历史
            messages = await self._load_conversation_messages(conversation_id)

            # 2. 首字节延迟: 在实际生成前发送初始化事件
            first_byte_time = time.time() - start_time
            logger.info(f"First byte latency: {first_byte_time:.1f}ms")

            # 3. 建立流式 Agent
            agent = self._build_streaming_agent()
            callback_handler = StreamingCallbackHandler()

            # 4. 执行 Agent 并流式处理输出
            accumulated_tokens = ""
            async for chunk in agent.astream_events(
                input={"messages": messages + [HumanMessage(content=user_message)]},
                config={"callbacks": [callback_handler]},
            ):
                event = chunk

                # 处理 LLM 事件
                if event.get("event") == "on_chat_model_stream":
                    content = event.get("data", {}).get("chunk", {}).get("content", "")
                    if content:
                        accumulated_tokens += content

                        # 缓冲 Token 直到达到缓冲大小
                        if len(accumulated_tokens) >= self.buffer_size:
                            chunk_event = MessageChunkEvent(
                                type=StreamEventType.MESSAGE_CHUNK,
                                timestamp=time.time(),
                                sequence=sequence,
                                content=accumulated_tokens,
                                token_count=len(accumulated_tokens.split()),
                                is_final=False,
                            )
                            sequence += 1
                            total_tokens += chunk_event.token_count
                            total_chunks += 1
                            yield chunk_event
                            accumulated_tokens = ""

                # 处理工具调用
                elif event.get("event") == "on_tool_start":
                    tool_event = ToolCallEvent(
                        type=StreamEventType.TOOL_CALL,
                        timestamp=time.time(),
                        sequence=sequence,
                        tool_name=event.get("data", {}).get("tool", ""),
                        tool_input=event.get("data", {}).get("input", {}),
                    )
                    sequence += 1
                    yield tool_event

                # 处理工具结果
                elif event.get("event") == "on_tool_end":
                    result_event = ToolResultEvent(
                        type=StreamEventType.TOOL_RESULT,
                        timestamp=time.time(),
                        sequence=sequence,
                        tool_name=event.get("data", {}).get("tool", ""),
                        result=event.get("data", {}).get("output", ""),
                    )
                    sequence += 1
                    yield result_event

            # 发送剩余的文本块
            if accumulated_tokens:
                final_chunk = MessageChunkEvent(
                    type=StreamEventType.MESSAGE_CHUNK,
                    timestamp=time.time(),
                    sequence=sequence,
                    content=accumulated_tokens,
                    token_count=len(accumulated_tokens.split()),
                    is_final=True,
                )
                sequence += 1
                total_tokens += final_chunk.token_count
                total_chunks += 1
                yield final_chunk

            # 发送完成状态
            elapsed = time.time() - start_time
            complete_event = CompleteStateEvent(
                type=StreamEventType.COMPLETE_STATE,
                timestamp=time.time(),
                sequence=sequence,
                final_message=accumulated_tokens,
                total_tokens=total_tokens,
                total_chunks=total_chunks,
                elapsed_time=elapsed,
            )
            yield complete_event

            logger.info(
                f"Stream complete: {total_tokens} tokens, "
                f"{total_chunks} chunks, {elapsed:.1f}s elapsed"
            )

        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            error_event = StreamEvent(
                type=StreamEventType.ERROR,
                timestamp=time.time(),
                sequence=sequence,
            )
            yield error_event

    def _build_streaming_agent(self):
        """构建支持流式的 Agent"""
        # 使用现有的 agent_service，配置为流式模式
        return self.agent_service.create_agent(streaming=True)

    async def _load_conversation_messages(self, conversation_id: str):
        """加载对话消息历史"""
        # TODO: 从数据库加载
        return []
```

### Step 3: 创建 SSE 端点 (90 分钟)

**文件**: `src/api/streaming_routes.py`

```python
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
import json
import asyncio
from typing import AsyncGenerator
from src.services.streaming_chat_service import StreamingChatService
from src.services.agent_service import AgentService
from src.services.semantic_cache import SemanticCacheService
from src.db.config import get_async_session
from src.middleware.auth_middleware import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["streaming"])

@router.post("/conversations/{conversation_id}/stream")
async def stream_conversation(
    conversation_id: str,
    message: dict,
    user_id: str = Depends(get_current_user),
    session = Depends(get_async_session),
):
    """
    流式 API 端点 - 使用 Server-Sent Events

    请求体:
    {
        "message": "用户消息"
    }

    响应: Server-Sent Events 流
    data: {"type": "message_chunk", "content": "...", "sequence": 0}
    data: {"type": "tool_call", "tool_name": "...", "sequence": 1}
    data: {"type": "complete_state", "total_tokens": 100, ...}
    """

    # 验证输入
    if not message.get("message"):
        raise HTTPException(status_code=400, detail="Missing message field")

    # 初始化服务
    agent_service = AgentService()
    cache_service = SemanticCacheService()
    streaming_service = StreamingChatService(agent_service, cache_service)

    async def event_generator() -> AsyncGenerator[str, None]:
        """SSE 事件生成器"""
        try:
            async for event in streaming_service.stream_agent_response(
                conversation_id=conversation_id,
                user_message=message["message"],
                user_id=user_id,
            ):
                # 转换为 JSON 并发送
                event_json = json.dumps(event.dict())
                yield f"data: {event_json}\n\n"

                # 给客户端时间处理事件
                await asyncio.sleep(0.01)

        except Exception as e:
            logger.error(f"Event generation error: {e}", exc_info=True)
            error_json = json.dumps({
                "type": "error",
                "message": str(e),
            })
            yield f"data: {error_json}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # 禁用代理缓冲
            "Connection": "keep-alive",
        },
    )

@router.options("/conversations/{conversation_id}/stream")
async def options_stream(conversation_id: str):
    """CORS 预检请求"""
    return {
        "allow": ["POST", "OPTIONS"],
    }
```

### Step 4: 集成到主应用 (30 分钟)

**文件**: `src/main.py` (修改)

```python
# 在路由注册部分添加
from src.api.streaming_routes import router as streaming_router

# ... 其他代码 ...

def register_routes():
    """注册所有 API 路由"""
    # ... 现有路由 ...

    # 添加流式路由
    app.include_router(streaming_router)
    logger.info("Registered streaming routes")
```

### Step 5: 创建监控指标 (30 分钟)

**文件**: `src/infrastructure/streaming_metrics.py` (新建)

```python
from prometheus_client import Histogram, Counter, Gauge
import logging

logger = logging.getLogger(__name__)

# 首字节延迟直方图 (毫秒)
first_byte_latency = Histogram(
    "streaming_first_byte_latency_ms",
    "First byte latency for streaming responses",
    buckets=(10, 25, 50, 100, 250, 500, 1000),
)

# 块吞吐量计数器
chunk_throughput = Counter(
    "streaming_chunks_total",
    "Total chunks sent in streaming responses",
)

# 活跃流连接数
active_streams = Gauge(
    "streaming_active_connections",
    "Number of active streaming connections",
)

# 流完成计数器
stream_completions = Counter(
    "streaming_completions_total",
    "Total completed streaming responses",
    labelnames=["status"],  # success, error, timeout
)

# 流内存使用
stream_memory_usage = Gauge(
    "streaming_memory_mb",
    "Memory usage for streaming buffers",
)
```

---

## ✅ 验证清单

### 代码完成清单
- [ ] `src/models/streaming_models.py` - 数据模型完成
- [ ] `src/services/streaming_chat_service.py` - 流式服务完成
- [ ] `src/api/streaming_routes.py` - SSE 端点完成
- [ ] `src/infrastructure/streaming_metrics.py` - 监控指标完成
- [ ] `src/main.py` - 路由集成完成

### 功能验证清单
- [ ] SSE 端点返回流式响应
- [ ] 消息块正确序列化
- [ ] 工具调用事件正确发送
- [ ] 完成状态事件包含正确信息
- [ ] 错误处理和日志记录完整

### 性能验证清单
- [ ] 首字节延迟 < 100ms (目标)
- [ ] 块吞吐量 > 50 chunks/sec (目标)
- [ ] 内存占用 < 20MB per connection (目标)
- [ ] 无内存泄漏 (长连接测试)
- [ ] 并发连接正确处理 (10+ 并发)

### 监控验证清单
- [ ] Prometheus 指标正确导出
- [ ] 首字节延迟直方图记录
- [ ] 活跃连接计数正确
- [ ] 完成状态分类统计

---

## 🧪 测试计划 (1 小时)

### 单元测试
```bash
# 测试流式服务
pytest tests/test_streaming_service.py -v

# 测试数据模型序列化
pytest tests/test_streaming_models.py -v
```

### 集成测试
```bash
# 测试 SSE 端点
pytest tests/integration/test_streaming_endpoint.py -v

# 测试流式 Agent 集成
pytest tests/integration/test_streaming_agent.py -v
```

### 性能测试
```bash
# 测试首字节延迟
locust -f tests/load_test_streaming.py \
        --host=http://localhost:8000 \
        -u 20 -r 5 -t 5m

# 测试并发连接
curl -N http://localhost:8000/api/v1/conversations/{id}/stream \
     -d '{"message": "test"}' \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $TOKEN"
```

---

## 📊 性能目标

| 指标 | 目标 | 方法 |
|------|------|------|
| **首字节延迟** | <100ms | 在 LLM 返回第一个 token 前最小化处理 |
| **块吞吐量** | >50/sec | 优化缓冲区大小和发送频率 |
| **内存使用** | <20MB | 限制缓冲区大小，及时释放 |
| **并发连接** | 10+ | 使用异步 I/O，避免阻塞 |
| **错误恢复** | 自动重试 | 实现重试逻辑和降级策略 |

---

## 📅 时间线

```
Day 1 (今天):
├─ Step 1: 创建数据模型 (30min) ✅ 预期完成
├─ Step 2: 创建流式服务 (90min) ✅ 预期完成
├─ Step 3: 创建 SSE 端点 (90min) ✅ 预期完成
├─ Step 4: 集成到主应用 (30min) ✅ 预期完成
└─ Step 5: 创建监控指标 (30min) ✅ 预期完成

Day 2 (明天):
├─ 单元/集成测试
├─ 性能测试和基准
└─ 完成报告生成

Total: 4 小时工作 + 2-3 小时测试 = Phase 2 完成 ✅
```

---

## 🚀 后续步骤

### 立即 (今天)
```
[ ] 开始 Step 1: 创建数据模型
[ ] Step 1 完成后 → Step 2
[ ] Step 2 完成后 → Step 3
[ ] 完成所有 Step 1-5
```

### 明天
```
[ ] 运行单元/集成测试
[ ] 执行性能基准测试
[ ] 生成 Phase 2 完成报告
[ ] 启动 Phase 3 (Claude Prompt Caching)
```

---

**Phase 2 已准备就绪！首字节延迟改进目标 -81% (550ms → 100ms)**

需要我现在开始实现 Step 1 吗？
