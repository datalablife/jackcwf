# LangChain v1.0 AI Conversation - Implementation Plan

**Feature**: LangChain v1.0 AI Conversation with Agents and RAG
**Version**: 1.0.0
**Plan Version**: 1.0.0
**Created**: 2025-11-16
**Status**: Ready for Implementation

---

## 🎯 Plan Overview

本计划基于 `.specify/memory/constitution.md` 的 8 个核心原则，为 LangChain v1.0 AI 对话功能提供详细的实现设计。

**依赖于**: `docs/features/langchain-ai-conversation-spec.md` (功能规范)

---

## 1️⃣ 系统整体架构

### 1.1 三层架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     前端层 (React 19)                        │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────┐         │
│  │ Chat UI    │  │ Doc Upload  │  │ Conversation │         │
│  │ (Tailark)  │  │   Manager   │  │   Browser    │         │
│  └────────┬───┘  └──────┬──────┘  └──────┬───────┘         │
│           │              │                 │                  │
│           └──────────────┼─────────────────┘                │
│                          │ WebSocket/HTTP                    │
└──────────────────────────┼──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              API Gateway (FastAPI)                           │
│  ┌────────────────────────────────────────────────────────┐│
│  │ Rate Limiting | JWT Authentication | CORS              ││
│  └────────────────────────────────────────────────────────┘│
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              中间件层 (Onion Pattern)                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. 认证中间件 (JWT Token Verification)             │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ 2. 记忆注入中间件 (Conversation History + RAG)     │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ 3. 内容审核中间件 (Safety Checks + Rate Limiting)  │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ 4. 响应结构化中间件 (JSON Formatting + Validation) │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ 5. 审计日志中间件 (Performance + Event Tracking)    │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│         LangChain v1.0 Agent 处理层                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Agent (create_agent)                               │  │
│  │  ┌─────────────┬─────────────┬────────────────────┐ │  │
│  │  │ Tool Select │ LLM Invoke  │ Response Generate  │ │  │
│  │  └─────────────┴─────────────┴────────────────────┘ │  │
│  │                                                      │  │
│  │  Tools:                                             │  │
│  │  ├─ search_documents() → pgvector RAG             │  │
│  │  ├─ query_database() → PostgreSQL SELECT          │  │
│  │  └─ web_search() → External API                   │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│         服务层 (业务逻辑)                                   │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐│
│  │ Conversation│  │ Embedding    │  │ Document          ││
│  │ Service     │  │ Service      │  │ Service           ││
│  └────────┬────┘  └────────┬─────┘  └────────┬───────────┘│
│           │                 │                  │             │
│           └─────────────────┼──────────────────┘            │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│         存储库层 (数据访问 - async)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐│
│  │ Conversation │  │ Message      │  │ Embedding         ││
│  │ Repository   │  │ Repository   │  │ Repository        ││
│  │ (asyncpg)    │  │ (asyncpg)    │  │ (asyncpg/pgvector)││
│  └────────┬─────┘  └────────┬─────┘  └────────┬───────────┘│
│           │                 │                  │             │
│           └─────────────────┼──────────────────┘            │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│           存储层 (PostgreSQL + Cache)                       │
│  ┌──────────────────┐    ┌──────────────────┐             │
│  │  PostgreSQL 15+  │    │   Redis 7.0+     │             │
│  │  ├─ conversations│    │ (Session & Cache)│             │
│  │  ├─ messages     │    │                  │             │
│  │  ├─ documents    │    │                  │             │
│  │  └─ embeddings   │    │                  │             │
│  │    (pgvector)    │    │                  │             │
│  └──────────────────┘    └──────────────────┘             │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  LLM APIs (Anthropic, OpenAI, Google, AWS)         │ │
│  └──────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 数据流设计

```
用户输入 ("What's in the document?")
    ↓
[WebSocket/HTTP 请求]
    ↓
FastAPI 路由 → /api/v1/conversations/{id}/messages
    ↓
┌────────────────────────────────────────────────────┐
│ 认证中间件                                          │
│ ✓ 验证 JWT token                                   │
│ ✓ 提取 user_id                                     │
│ ✓ 验证权限                                          │
└────┬───────────────────────────────────────────────┘
    ↓
┌────────────────────────────────────────────────────┐
│ 记忆注入中间件                                      │
│ ✓ 查询消息历史 (最近 5 条)                         │
│ ✓ 向量相似性搜索 (user query)                     │
│ ✓ 从 pgvector 检索相关文档 (≤ 200ms)            │
│ ✓ 注入到 request.state                             │
└────┬───────────────────────────────────────────────┘
    ↓
┌────────────────────────────────────────────────────┐
│ 内容审核中间件                                      │
│ ✓ 提示注入检测                                      │
│ ✓ 有害内容过滤                                      │
│ ✓ 速率限制检查                                      │
└────┬───────────────────────────────────────────────┘
    ↓
┌────────────────────────────────────────────────────┐
│ LangChain Agent 执行                               │
│ agent = create_agent(                              │
│     model="claude-sonnet-4-5-20250929",           │
│     tools=[search_documents, query_db, web_search]│
│     middleware=[...5 layers...]                    │
│ )                                                   │
│                                                     │
│ 执行步骤:                                           │
│ 1. 分析用户查询和历史                              │
│ 2. 选择合适的工具 (search_documents?)             │
│ 3. 并行执行工具 (asyncio.TaskGroup)               │
│    - 搜索相关文档                                  │
│    - 或查询数据库                                  │
│    - 或搜索网页                                    │
│ 4. 合并结果                                        │
│ 5. 生成自然语言响应                                │
└────┬───────────────────────────────────────────────┘
    ↓
┌────────────────────────────────────────────────────┐
│ 响应结构化中间件                                    │
│ ✓ 序列化响应为 JSON                                │
│ ✓ 添加元数据 (tokens_used, tool_calls)           │
│ ✓ 验证响应模式                                      │
└────┬───────────────────────────────────────────────┘
    ↓
┌────────────────────────────────────────────────────┐
│ 审计日志中间件                                      │
│ ✓ 记录消息和响应                                    │
│ ✓ 记录工具调用和结果                                │
│ ✓ 收集性能指标                                      │
│ ✓ 发送到日志聚合系统                                │
└────┬───────────────────────────────────────────────┘
    ↓
[WebSocket 流式响应] 或 [HTTP 响应]
    ↓
[前端实时更新聊天 UI]
```

---

## 2️⃣ 数据库设计

### 2.1 完整 ER 图

```
┌──────────────────────────┐
│       conversations      │
├──────────────────────────┤
│ id (UUID) [PK]          │
│ user_id (VARCHAR)        │
│ title (VARCHAR)          │
│ summary (TEXT)           │
│ model (VARCHAR)          │
│ system_prompt (TEXT)     │
│ metadata (JSONB)         │
│ is_deleted (BOOLEAN)     │
│ created_at (TIMESTAMP)   │
│ updated_at (TIMESTAMP)   │
└──────────────────────────┘
         │
         │ 1:N
         │
┌──────────────────────────┐
│       messages           │
├──────────────────────────┤
│ id (UUID) [PK]          │
│ conversation_id (FK)     │───────┐
│ role (VARCHAR)           │       │
│ content (TEXT)           │       │
│ tool_calls (JSONB)       │       │
│ tool_results (JSONB)     │       │
│ tokens_used (INTEGER)    │       │
│ metadata (JSONB)         │       │
│ created_at (TIMESTAMP)   │       │
└──────────────────────────┘       │
                                   │
                    ┌──────────────┴──────────┐
                    │                         │
        ┌───────────▼──────────┐  ┌──────────▼─────────┐
        │    documents         │  │   embeddings       │
        ├──────────────────────┤  ├────────────────────┤
        │ id (UUID) [PK]       │  │ id (UUID) [PK]     │
        │ user_id (VARCHAR)    │  │ document_id (FK)   │
        │ filename (VARCHAR)   │  │ chunk_text (TEXT)  │
        │ file_type (VARCHAR)  │  │ embedding (vector) │
        │ content (TEXT)       │  │ chunk_index (INT)  │
        │ total_chunks (INT)   │  │ metadata (JSONB)   │
        │ metadata (JSONB)     │  │ created_at (TS)    │
        │ is_deleted (BOOLEAN) │  │ is_deleted (BOOL)  │
        │ created_at (TS)      │  └────────────────────┘
        │ updated_at (TS)      │
        └──────────────────────┘
```

### 2.2 索引策略

```sql
-- conversations 表
CREATE INDEX idx_user_created ON conversations(user_id, created_at DESC);
CREATE INDEX idx_user_active ON conversations(user_id, is_deleted, created_at DESC);
CREATE INDEX idx_title_search ON conversations USING GIN(to_tsvector('english', title));

-- messages 表
CREATE INDEX idx_conversation ON messages(conversation_id, created_at);
CREATE INDEX idx_role ON messages(role);
CREATE INDEX idx_conversation_recent ON messages(conversation_id, created_at DESC)
  WHERE is_deleted = FALSE;

-- documents 表
CREATE INDEX idx_user_created ON documents(user_id, created_at DESC);
CREATE INDEX idx_user_active ON documents(user_id, is_deleted, created_at DESC);

-- embeddings 表 (关键性能指标)
CREATE INDEX idx_embedding USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_document ON embeddings(document_id);
CREATE INDEX idx_created ON embeddings(created_at DESC);
CREATE INDEX idx_document_chunk ON embeddings(document_id, chunk_index);
```

### 2.3 分区策略

```sql
-- embeddings 按时间分区 (>1M 记录时)
-- 理由: 向量表会持续增长，分区可以提高查询性能

CREATE TABLE embeddings_2025_11 PARTITION OF embeddings
  FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

CREATE TABLE embeddings_2025_12 PARTITION OF embeddings
  FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');

-- 自动分区创建触发器 (Python script)
-- 每月 1 号自动创建下一个月的分区
```

---

## 3️⃣ 中间件架构详设

### 3.1 认证中间件实现

```python
# backend/src/infrastructure/middleware/authentication.py

from fastapi import Request, HTTPException
from typing import Callable, Any
import jwt

class AuthenticationMiddleware:
    """认证中间件 - 验证 JWT token"""

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm

    async def __call__(
        self,
        request: Request,
        call_next: Callable
    ) -> Any:
        """
        验证流程:
        1. 从 Authorization header 提取 token
        2. 验证 JWT 签名和过期时间
        3. 提取 user_id 并存储在 request.state
        4. 继续处理
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing token")

        token = auth_header.split(" ")[1]

        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token")
            request.state.user_id = user_id
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

        response = await call_next(request)
        return response
```

### 3.2 记忆注入中间件实现

```python
# backend/src/infrastructure/middleware/memory_injection.py

from typing import Callable, Any
from fastapi import Request

class MemoryInjectionMiddleware:
    """记忆注入中间件 - 检索对话历史和 RAG 上下文"""

    def __init__(
        self,
        message_repo,
        embedding_repo,
        conversation_repo
    ):
        self.message_repo = message_repo
        self.embedding_repo = embedding_repo
        self.conversation_repo = conversation_repo

    async def __call__(
        self,
        request: Request,
        call_next: Callable
    ) -> Any:
        """
        记忆注入流程:
        1. 从请求中提取 conversation_id 和 message 内容
        2. 并行查询:
           a. 获取最近 5 条消息 (对话历史)
           b. 向量搜索相关文档 (RAG)
        3. 注入到 request.state
        4. 继续处理
        """
        user_id = request.state.user_id
        body = await request.json()
        conversation_id = body.get("conversation_id")
        user_message = body.get("message")

        if not conversation_id or not user_message:
            response = await call_next(request)
            return response

        # 并行执行两个查询
        import asyncio
        async with asyncio.TaskGroup() as tg:
            # 任务 1: 获取对话历史
            history_task = tg.create_task(
                self.message_repo.get_recent(conversation_id, limit=5)
            )

            # 任务 2: 向量搜索相关文档 (RAG)
            rag_task = tg.create_task(
                self.embedding_repo.search(
                    query=user_message,
                    user_id=user_id,
                    limit=5,
                    threshold=0.7
                )
            )

        # 结果已准备好
        conversation_history = await history_task
        rag_context = await rag_task

        # 注入到请求状态
        request.state.conversation_history = conversation_history
        request.state.rag_context = rag_context
        request.state.conversation_id = conversation_id

        response = await call_next(request)
        return response
```

### 3.3 审计日志中间件实现

```python
# backend/src/infrastructure/middleware/audit_logging.py

import time
import json
import structlog
from typing import Callable, Any
from fastapi import Request
from uuid import uuid4

logger = structlog.get_logger()

class AuditLoggingMiddleware:
    """审计日志中间件 - 记录所有操作和性能指标"""

    async def __call__(
        self,
        request: Request,
        call_next: Callable
    ) -> Any:
        """
        审计流程:
        1. 为请求分配唯一 ID
        2. 记录请求信息
        3. 测量执行时间
        4. 记录响应和性能指标
        """
        request_id = str(uuid4())
        request.state.request_id = request_id

        start_time = time.time()

        # 记录请求
        await logger.ainfo(
            "request_started",
            request_id=request_id,
            user_id=getattr(request.state, "user_id", "anonymous"),
            method=request.method,
            path=request.url.path,
            conversation_id=getattr(request.state, "conversation_id", None)
        )

        try:
            response = await call_next(request)
            elapsed_ms = (time.time() - start_time) * 1000

            # 记录响应
            await logger.ainfo(
                "request_completed",
                request_id=request_id,
                status_code=response.status_code,
                duration_ms=elapsed_ms,
                tokens_used=getattr(response.state, "tokens_used", 0),
                tools_called=getattr(response.state, "tools_called", [])
            )

            return response

        except Exception as exc:
            elapsed_ms = (time.time() - start_time) * 1000

            # 记录错误
            await logger.aerror(
                "request_failed",
                request_id=request_id,
                duration_ms=elapsed_ms,
                error=str(exc),
                error_type=type(exc).__name__
            )

            raise
```

---

## 4️⃣ 后端项目结构

### 4.1 目录树

```
backend/
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── conversations.py        # 对话端点
│   │   │   ├── messages.py             # 消息端点
│   │   │   ├── documents.py            # 文档上传端点
│   │   │   ├── embeddings.py           # RAG 搜索端点
│   │   │   └── health.py               # 健康检查
│   │   └── router.py                   # 路由注册
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── conversation_service.py     # 对话业务逻辑
│   │   ├── message_service.py          # 消息处理
│   │   ├── embedding_service.py        # 向量化服务
│   │   ├── document_service.py         # 文档处理
│   │   └── agent_service.py            # LangChain Agent
│   │
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base_repository.py          # 基础存储库
│   │   ├── conversation_repository.py  # 对话数据访问
│   │   ├── message_repository.py       # 消息数据访问
│   │   ├── document_repository.py      # 文档数据访问
│   │   └── embedding_repository.py     # 向量数据访问
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── domain.py                   # 业务领域模型
│   │   ├── dto.py                      # 数据传输对象 (Pydantic)
│   │   └── orm.py                      # SQLAlchemy ORM 模型
│   │
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── database.py                 # 数据库连接和会话
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   ├── authentication.py       # 认证中间件
│   │   │   ├── memory_injection.py     # 记忆注入中间件
│   │   │   ├── moderation.py           # 内容审核中间件
│   │   │   ├── response_structuring.py # 响应结构化中间件
│   │   │   └── audit_logging.py        # 审计日志中间件
│   │   ├── config.py                   # 配置管理
│   │   ├── logger.py                   # 日志配置
│   │   └── monitoring.py               # 监控和指标
│   │
│   └── main.py                         # 应用入口
│
├── tests/
│   ├── unit/
│   │   ├── services/
│   │   │   ├── test_conversation_service.py
│   │   │   ├── test_message_service.py
│   │   │   ├── test_embedding_service.py
│   │   │   └── test_agent_service.py
│   │   │
│   │   ├── repositories/
│   │   │   ├── test_conversation_repository.py
│   │   │   ├── test_message_repository.py
│   │   │   ├── test_document_repository.py
│   │   │   └── test_embedding_repository.py
│   │   │
│   │   └── middleware/
│   │       ├── test_authentication.py
│   │       ├── test_memory_injection.py
│   │       └── test_audit_logging.py
│   │
│   ├── integration/
│   │   ├── test_conversation_api.py
│   │   ├── test_message_api.py
│   │   ├── test_document_api.py
│   │   ├── test_rag_flow.py
│   │   └── test_agent_flow.py
│   │
│   ├── e2e/
│   │   └── test_conversation_e2e.py
│   │
│   ├── fixtures/
│   │   ├── conftest.py                 # pytest 配置
│   │   ├── mock_data.py                # 测试数据
│   │   └── mock_agent.py               # 模拟 Agent
│   │
│   └── __init__.py
│
├── pyproject.toml                      # 项目配置和依赖
├── pytest.ini                          # pytest 配置
├── .env.example                        # 环境变量示例
├── Dockerfile                          # Docker 镜像定义
└── README.md                           # 项目文档
```

### 4.2 API 路由定义

```python
# backend/src/api/v1/conversations.py

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/conversations", tags=["conversations"])

class CreateConversationRequest(BaseModel):
    title: str
    system_prompt: str
    model: str = "claude-sonnet-4-5-20250929"

class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: str

@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    request: Request,
    body: CreateConversationRequest
) -> ConversationResponse:
    """创建新对话"""
    user_id = request.state.user_id
    service = request.app.state.conversation_service

    conversation = await service.create(
        user_id=user_id,
        title=body.title,
        system_prompt=body.system_prompt,
        model=body.model
    )

    return conversation

@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    request: Request,
    conversation_id: str
) -> ConversationResponse:
    """获取对话详情"""
    user_id = request.state.user_id
    service = request.app.state.conversation_service

    conversation = await service.get(conversation_id, user_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation

class SendMessageRequest(BaseModel):
    conversation_id: str
    message: str

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    tokens_used: int
    tool_calls: Optional[list] = None

@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    request: Request,
    conversation_id: str,
    body: SendMessageRequest
) -> MessageResponse:
    """发送消息并获取 Agent 响应"""
    user_id = request.state.user_id
    conversation_history = request.state.conversation_history
    rag_context = request.state.rag_context

    service = request.app.state.message_service

    message = await service.send_message(
        conversation_id=conversation_id,
        user_id=user_id,
        content=body.message,
        conversation_history=conversation_history,
        rag_context=rag_context
    )

    return message

@router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    conversation_id: str,
    token: str
) -> None:
    """WebSocket 端点用于实时消息流"""
    # 认证
    user_id = verify_jwt(token)

    await websocket.accept()

    service = websocket.app.state.message_service

    try:
        while True:
            data = await websocket.receive_json()
            message_content = data.get("message")

            # 流式生成 Agent 响应
            async for chunk in service.send_message_stream(
                conversation_id=conversation_id,
                user_id=user_id,
                content=message_content
            ):
                await websocket.send_json({"chunk": chunk})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"error": str(e)})
        await websocket.close()
```

---

## 5️⃣ 前端项目结构

### 5.1 目录树

```
frontend/
├── src/
│   ├── components/
│   │   ├── Chat/
│   │   │   ├── ChatInterface.tsx       # 主聊天界面
│   │   │   ├── ChatMessage.tsx         # 单条消息
│   │   │   ├── ChatInput.tsx           # 输入框
│   │   │   ├── MessageList.tsx         # 消息列表
│   │   │   └── TypingIndicator.tsx     # 输入指示器
│   │   │
│   │   ├── DocumentUpload/
│   │   │   ├── DocumentUploadForm.tsx  # 上传表单
│   │   │   ├── FileDropZone.tsx        # 拖拽区域
│   │   │   ├── UploadProgress.tsx      # 进度条
│   │   │   └── DocumentList.tsx        # 文档列表
│   │   │
│   │   ├── Conversation/
│   │   │   ├── ConversationList.tsx    # 对话列表
│   │   │   ├── ConversationHeader.tsx  # 对话头部
│   │   │   └── ConversationSettings.tsx# 设置
│   │   │
│   │   ├── Layout/
│   │   │   ├── MainLayout.tsx          # 主布局
│   │   │   ├── Sidebar.tsx             # 侧边栏
│   │   │   └── Header.tsx              # 头部
│   │   │
│   │   └── Common/
│   │       ├── Button.tsx
│   │       ├── Input.tsx
│   │       ├── Modal.tsx
│   │       └── Toast.tsx
│   │
│   ├── hooks/
│   │   ├── useChat.ts                  # 聊天逻辑
│   │   ├── useConversation.ts          # 对话管理
│   │   ├── useDocuments.ts             # 文档管理
│   │   ├── useEmbeddings.ts            # RAG 搜索
│   │   ├── useWebSocket.ts             # WebSocket
│   │   └── useAuth.ts                  # 认证
│   │
│   ├── services/
│   │   ├── api.ts                      # API 客户端
│   │   ├── websocket.ts                # WebSocket 服务
│   │   ├── storage.ts                  # 本地存储
│   │   └── auth.ts                     # 认证服务
│   │
│   ├── stores/
│   │   ├── chatStore.ts                # 聊天状态 (Zustand)
│   │   ├── conversationStore.ts        # 对话状态
│   │   ├── documentStore.ts            # 文档状态
│   │   └── authStore.ts                # 认证状态
│   │
│   ├── pages/
│   │   ├── ChatPage.tsx                # 聊天页面
│   │   ├── DocumentsPage.tsx           # 文档页面
│   │   ├── ConversationsPage.tsx       # 对话列表页
│   │   ├── LoginPage.tsx               # 登录页
│   │   └── NotFoundPage.tsx            # 404 页
│   │
│   ├── types/
│   │   ├── api.ts                      # API 类型定义
│   │   ├── models.ts                   # 数据模型
│   │   └── index.ts                    # 导出
│   │
│   ├── utils/
│   │   ├── formatting.ts               # 格式化工具
│   │   ├── validation.ts               # 验证工具
│   │   ├── date.ts                     # 日期工具
│   │   └── error.ts                    # 错误处理
│   │
│   ├── styles/
│   │   ├── globals.css                 # 全局样式
│   │   ├── tailwind.config.js          # Tailwind 配置
│   │   └── theme.css                   # 主题样式
│   │
│   ├── App.tsx                         # 根组件
│   ├── main.tsx                        # 入口
│   └── router.tsx                      # 路由配置
│
├── tests/
│   ├── unit/
│   │   ├── hooks/
│   │   │   ├── useChat.test.ts
│   │   │   └── useConversation.test.ts
│   │   ├── utils/
│   │   │   └── formatting.test.ts
│   │   └── stores/
│   │       └── chatStore.test.ts
│   │
│   ├── integration/
│   │   ├── api.test.ts
│   │   └── websocket.test.ts
│   │
│   └── e2e/
│       ├── chat.spec.ts
│       ├── document-upload.spec.ts
│       └── conversation-management.spec.ts
│
├── public/
│   └── assets/
│       ├── icons/
│       ├── images/
│       └── fonts/
│
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── .env.example
└── README.md
```

### 5.2 关键组件实现

```typescript
// frontend/src/components/Chat/ChatInterface.tsx

import React, { useState, useEffect, useRef } from 'react'
import { useChat } from '@/hooks/useChat'
import { useConversation } from '@/hooks/useConversation'
import { useWebSocket } from '@/hooks/useWebSocket'
import { ChatMessage } from './ChatMessage'
import { ChatInput } from './ChatInput'
import { MessageList } from './MessageList'
import { TypingIndicator } from './TypingIndicator'

interface ChatInterfaceProps {
  conversationId: string
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  conversationId
}) => {
  const [messages, setMessages] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const { conversation, loading } = useConversation(conversationId)
  const { messages: wsMessages, sendMessage } = useWebSocket(conversationId)
  const { chat } = useChat()

  // WebSocket 消息处理
  useEffect(() => {
    if (wsMessages.length > 0) {
      setMessages(prev => [...prev, ...wsMessages])
      setIsLoading(false)
    }
  }, [wsMessages])

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSendMessage = async (content: string) => {
    setIsLoading(true)

    // 添加用户消息到 UI
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      role: 'user',
      content: content,
      createdAt: new Date().toISOString()
    }])

    // 通过 WebSocket 发送消息
    await sendMessage(content)
  }

  if (loading) {
    return <div className="flex items-center justify-center h-full">Loading...</div>
  }

  return (
    <div className="flex flex-col h-full bg-white">
      {/* 头部 */}
      <div className="border-b p-4">
        <h2 className="text-lg font-semibold">{conversation?.title}</h2>
      </div>

      {/* 消息列表 */}
      <MessageList messages={messages} isLoading={isLoading} />

      {/* 输入框 */}
      <ChatInput
        onSend={handleSendMessage}
        disabled={isLoading}
        placeholder="Ask me anything about your documents..."
      />

      <div ref={messagesEndRef} />
    </div>
  )
}
```

---

## 6️⃣ 监控和可观测性设计

### 6.1 关键指标和告警

```yaml
# prometheus/alerts.yml

groups:
  - name: langchain_conversation_alerts
    interval: 30s
    rules:
      # API 性能
      - alert: HighResponseTime
        expr: histogram_quantile(0.99, http_request_duration_seconds) > 1.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API response time P99 > 1s"

      - alert: VectorSearchSlow
        expr: histogram_quantile(0.99, vector_search_duration_seconds) > 0.2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Vector search latency P99 > 200ms"

      # 错误率
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Error rate > 1%"

      # 资源
      - alert: DatabaseConnectionPoolFull
        expr: db_connection_pool_used / db_connection_pool_size > 0.9
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "DB connection pool > 90% full"

      - alert: HighMemoryUsage
        expr: process_resident_memory_bytes / 1073741824 > 1.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Memory usage > 1GB"
```

### 6.2 仪表板设计

```
Grafana Dashboard: LangChain AI Conversation

Row 1: 系统概览
├─ Panel: 请求吞吐量 (req/s)
├─ Panel: 错误率 (%)
├─ Panel: API P99 延迟 (ms)
└─ Panel: 活跃用户数

Row 2: 对话分析
├─ Panel: 消息数/天
├─ Panel: 平均对话长度
├─ Panel: 工具使用率
└─ Panel: Agent 成功率

Row 3: 向量存储
├─ Panel: 向量搜索延迟 P99 (ms)
├─ Panel: 搜索命中率 (%)
├─ Panel: 向量表大小 (GB)
└─ Panel: 索引健康度

Row 4: 资源使用
├─ Panel: CPU 使用率 (%)
├─ Panel: 内存使用量 (GB)
├─ Panel: DB 连接池 (%)
└─ Panel: Redis 内存 (MB)

Row 5: 中间件性能
├─ Panel: 认证耗时 (ms)
├─ Panel: 记忆注入耗时 (ms)
├─ Panel: 审核耗时 (ms)
└─ Panel: 日志写入耗时 (ms)
```

---

## 7️⃣ 风险和缓解策略

| 风险 | 概率 | 影响 | 缓解策略 |
|------|------|------|---------|
| LLM API 限流/超时 | 高 | 高 | 实现请求队列 + 重试机制 + fallback 模型 |
| 向量搜索性能下降 | 中 | 高 | 索引优化 + 分区 + 缓存层 (Redis) |
| 数据库连接耗尽 | 中 | 高 | 连接池管理 + 监控告警 + 自动扩展 |
| token 成本过高 | 中 | 中 | 请求合批 + 缓存 + 成本监控 |
| 向量维度混乱 | 低 | 高 | 严格的单元测试 + 运行时验证 |
| WebSocket 连接泄漏 | 低 | 中 | 心跳检测 + 自动重连 + 连接监控 |
| RAG 上下文无关 | 中 | 中 | 相似度阈值调优 + 手动评估 |
| 中间件执行顺序错误 | 低 | 高 | 集成测试 + 文档清晰 + 代码审查 |

---

## 8️⃣ 实现时间表

### 第 1 周: 基础设施 (Week 1-2)

**目标**: 数据库和异步基础架构

- [ ] **Day 1-2**: 数据库设计和迁移脚本
  - 创建 4 个表 (conversations, messages, documents, embeddings)
  - 创建所有索引和约束
  - 测试分区策略

- [ ] **Day 3-4**: 异步存储库实现
  - ConversationRepository (async)
  - MessageRepository (async)
  - DocumentRepository (async)
  - EmbeddingRepository (async with pgvector search)

- [ ] **Day 5**: API 框架搭建
  - FastAPI 应用初始化
  - 路由注册
  - 错误处理中间件

**交付物**: 基础后端框架 + 存储库层

---

### 第 2-3 周: Agent 集成 (Week 2-3)

**目标**: LangChain Agent 和 RAG 管道

- [ ] **Day 6-8**: 向量化和 RAG 管道
  - 文档分块 (1000 tokens, 200 overlap)
  - OpenAI embedding API 集成
  - pgvector 向量存储和搜索实现

- [ ] **Day 9-10**: LangChain Agent 实现
  - 从 `langchain.agents import create_agent` 创建基础 Agent
  - 定义 3 个工具 (search_documents, query_database, web_search)
  - 测试工具调用和结果集成

- [ ] **Day 11-12**: 消息处理和对话管理
  - 对话创建和检索
  - 消息持久化
  - 上下文管理

**交付物**: 可工作的 AI Agent + RAG 搜索

---

### 第 3-4 周: 中间件和特性 (Week 3-4)

**目标**: 5 层中间件 + 完整功能

- [ ] **Day 13-14**: 中间件实现 (第 1-3 层)
  - AuthenticationMiddleware (JWT 验证)
  - MemoryInjectionMiddleware (历史 + RAG)
  - ContentModerationMiddleware (安全检查)

- [ ] **Day 15-16**: 中间件实现 (第 4-5 层)
  - ResponseStructuringMiddleware (JSON 格式化)
  - AuditLoggingMiddleware (结构化日志)

- [ ] **Day 17-18**: 特性完成
  - 文档上传端点
  - WebSocket 实时流
  - 错误处理和恢复

- [ ] **Day 19**: 集成测试
  - 端到端对话流程
  - 中间件堆栈验证
  - 工具执行测试

**交付物**: 完整后端功能 + 集成测试通过

---

### 第 4-5 周: 前端开发 (Week 4-5)

**目标**: React UI 和实时交互

- [ ] **Day 20-22**: 基础组件
  - 聊天界面 (Tailark 组件)
  - 消息列表和输入框
  - 对话管理界面

- [ ] **Day 23-24**: 高级特性
  - 文档上传和列表
  - WebSocket 集成
  - 实时消息更新

- [ ] **Day 25-26**: 状态管理和服务
  - Zustand store 实现
  - API 客户端
  - 错误处理和加载状态

- [ ] **Day 27**: 集成和联调
  - 前后端 API 联调
  - 端到端流程测试
  - UI/UX 优化

**交付物**: 完整前端应用 + 与后端集成

---

### 第 5-6 周: 测试和优化 (Week 5-6)

**目标**: 高质量代码和性能优化

- [ ] **Day 28-30**: 单元测试
  - Services 单元测试 (≥80%)
  - Repositories 单元测试
  - Utils 和 Hooks 单元测试

- [ ] **Day 31-32**: 性能优化
  - 数据库查询优化
  - 缓存策略 (Redis)
  - 向量搜索性能调优

- [ ] **Day 33-34**: 类型检查和 Linting
  - mypy --strict 通过
  - 代码格式化 (black, isort)
  - Linting (flake8, pylint)

- [ ] **Day 35**: 文档和部署准备
  - API 文档 (Swagger)
  - README 和开发指南
  - 部署检查清单

**交付物**: 生产就绪代码 + 完整文档

---

### 第 6-7 周: 部署 (Week 6-7)

**目标**: 生产部署和监控

- [ ] **Day 36-37**: 部署准备
  - Docker 镜像构建和测试
  - GitHub Actions CI/CD 配置
  - 环境变量和密钥管理

- [ ] **Day 38-39**: 监控和告警
  - Prometheus 指标配置
  - Grafana 仪表板创建
  - 告警规则配置

- [ ] **Day 40-41**: 测试环境部署
  - 通过 Coolify 部署到测试环境
  - 烟雾测试和功能验证
  - 性能基线测试

- [ ] **Day 42-43**: 生产部署
  - 金丝雀部署 (5% 流量)
  - 监控和日志收集验证
  - 全量部署

**交付物**: 生产部署 + 监控系统运行

---

## 9️⃣ 技术决策记录

### 决策 1: 为什么使用 LangChain v1.0 而不是 v0.x?

**选择**: LangChain v1.0 (create_agent + middleware)

**理由**:
- ✅ 简化的 API (create_agent)
- ✅ 官方中间件系统支持
- ✅ LangGraph 官方集成
- ✅ 多 LLM 提供商支持
- ✅ 更好的生产级特性

**替代方案**:
- ❌ LangChain v0.x - 复杂的链式 API，维护成本高
- ❌ Haystack - 功能过多，学习曲线陡峭
- ❌ 自研框架 - 时间成本高，可维护性低

---

### 决策 2: 为什么选择 PostgreSQL + pgvector?

**选择**: PostgreSQL 15+ + pgvector 扩展

**理由**:
- ✅ ACID 事务保证
- ✅ 强一致性 (RAG 数据可靠)
- ✅ 自托管 (降低成本)
- ✅ pgvector 成熟稳定
- ✅ HNSW 索引高性能

**替代方案**:
- ❌ Pinecone - 托管服务，成本高，供应商锁定
- ❌ Weaviate - 复杂部署，学习曲线陡峭
- ❌ Qdrant - 新兴，生态小，文档有限

---

### 决策 3: 为什么采用 5 层中间件?

**选择**: 5 层洋葱模式中间件 (认证→记忆→审核→结构→日志)

**理由**:
- ✅ 关注点分离 (SoC)
- ✅ 可测试性高
- ✅ 易于添加新功能
- ✅ 清晰的执行顺序
- ✅ 符合宪法原则 #2

**替代方案**:
- ❌ 单一巨大中间件 - 难以维护
- ❌ 无中间件 - 代码混乱
- ❌ 3 层中间件 - 功能不完整

---

## 🔟 部署和上线

### 部署前检查清单

**代码质量**:
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] mypy --strict 通过 (0 errors)
- [ ] pylint / flake8 无错误
- [ ] 代码审查通过

**功能完整性**:
- [ ] 所有 API 端点实现完成
- [ ] 所有中间件实现完成
- [ ] 所有工具实现完成
- [ ] WebSocket 流实现完成

**性能**:
- [ ] API 响应时间 P99 ≤ 1000ms
- [ ] 向量搜索 P99 ≤ 300ms
- [ ] 负载测试 (100 并发用户通过)

**安全**:
- [ ] 安全审计完成
- [ ] 所有敏感信息在环境变量中
- [ ] 无 SQL 注入漏洞
- [ ] 无 XSS 漏洞

**基础设施**:
- [ ] PostgreSQL 15+ 已配置
- [ ] pgvector 扩展已安装
- [ ] Redis 已配置
- [ ] Docker 镜像构建成功

### 部署后验证

- [ ] 应用正常启动
- [ ] 健康检查端点响应 ✓
- [ ] API 端点可访问
- [ ] 数据库连接成功
- [ ] 向量搜索工作正常
- [ ] WebSocket 连接成功
- [ ] 日志正确输出
- [ ] 监控指标收集

---

## 📚 参考资源

### 官方文档
- [LangChain v1.0 文档](https://docs.langchain.com/oss/python/releases/langchain-v1)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [FastAPI 文档](https://fastapi.tiangolo.com)

### 项目文档
- [项目宪法](../../.specify/memory/constitution.md)
- [功能规范](./langchain-ai-conversation-spec.md)
- [任务分解](./langchain-ai-conversation-tasks.md) (待创建)

---

**计划版本**: 1.0.0
**最后更新**: 2025-11-16
**状态**: 📋 Ready for Development
**下一步**: 创建任务分解 (langchain-ai-conversation-tasks.md)
