# Epic 1 - 实现指南（第2部分）

**文档版本**: 1.0 Part 2
**包含**: API框架、最佳实践、性能基准、风险缓解

---

## Story 1.3 - API 框架搭建

### Task 1.3.1: FastAPI 应用初始化

**当前状态评估**：

现有 `src/main.py` 已有基础框架，但需要增强：

```python
# 需要改进的方面：
# 1. 更细致的异常处理
# 2. 请求追踪（请求ID）
# 3. 速率限制
# 4. 依赖注入优化
# 5. 健康检查增强
# 6. 优雅关闭处理
```

**完整增强实现**：

```python
# src/main.py - 增强版本

import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.db.config import engine
from src.db.migrations import init_db
from src.utils.logging_config import setup_logging

# 配置日志
setup_logging(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 速率限制器
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    处理启动和关闭事件
    """
    # ============ 启动事件 ============
    logger.info("Starting LangChain AI Conversation backend...")

    try:
        # 初始化数据库
        await init_db(engine)
        logger.info("Database initialization completed")

        # 预热连接池
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        logger.info("Connection pool warmed up")

        # 加载配置
        logger.info(f"Environment: {os.getenv('ENV', 'development')}")
        logger.info(f"Debug mode: {os.getenv('DEBUG', 'false')}")

    except Exception as e:
        logger.error(f"Failed to initialize application: {e}", exc_info=True)
        raise

    logger.info("Application startup complete")

    yield

    # ============ 关闭事件 ============
    logger.info("Shutting down LangChain AI Conversation backend...")

    try:
        # 优雅关闭数据库连接
        await engine.dispose()
        logger.info("Database connections closed")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)

    logger.info("Shutdown completed")


# ============ FastAPI 应用初始化 ============

app = FastAPI(
    title="LangChain AI Conversation API",
    description="API for LangChain v1.0 AI Conversation with Agents and RAG",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# 添加速率限制器到应用
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, limiter.error_handler)

# ============ 中间件配置 ============

# 1. 可信主机中间件（安全性）
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "localhost",
        "127.0.0.1",
        "*.example.com",
    ] if os.getenv("ENV") == "production" else ["*"]
)

# 2. CORS 中间件
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:8000"
).split(",")
ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time"],
)

# 3. 请求追踪中间件
@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next: Callable):
    """为每个请求添加唯一 ID"""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response

# 4. 处理时间追踪中间件
@app.middleware("http")
async def add_process_time_middleware(request: Request, call_next: Callable):
    """记录请求处理时间"""
    import time

    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    response.headers["X-Process-Time"] = str(process_time)

    logger.info(
        f"[{request.state.request_id}] "
        f"{request.method} {request.url.path} - "
        f"{response.status_code} ({process_time:.3f}s)"
    )

    return response

# 5. 自定义应用中间件（业务逻辑）
from src.middleware.audit_logging_middleware import AuditLoggingMiddleware
from src.middleware.response_structuring_middleware import ResponseStructuringMiddleware
from src.middleware.content_moderation_middleware import ContentModerationMiddleware
from src.middleware.memory_injection_middleware import MemoryInjectionMiddleware
from src.middleware.auth_middleware import AuthenticationMiddleware

# 注意：中间件执行顺序是反向的（最后添加的最先执行）
app.add_middleware(AuditLoggingMiddleware)
app.add_middleware(ResponseStructuringMiddleware)
app.add_middleware(ContentModerationMiddleware)
app.add_middleware(MemoryInjectionMiddleware)
app.add_middleware(AuthenticationMiddleware)

# ============ 全局异常处理器 ============

class APIError(Exception):
    """API 级异常"""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: dict = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)

@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    """处理 API 错误"""
    logger.warning(
        f"[{request.state.request_id}] API Error: {exc.error_code} - {exc.message}",
        extra={"error_code": exc.error_code, "details": exc.details}
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "request_id": request.state.request_id,
                "details": exc.details if os.getenv("DEBUG") == "true" else {}
            }
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理验证错误"""
    logger.warning(
        f"[{request.state.request_id}] Validation error: {exc.errors()}",
        extra={"errors": exc.errors()}
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "request_id": request.state.request_id,
                "details": exc.errors() if os.getenv("DEBUG") == "true" else []
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理未捕获的异常"""
    logger.error(
        f"[{request.state.request_id}] Unhandled exception: {str(exc)}",
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred",
                "request_id": request.state.request_id,
                "details": str(exc) if os.getenv("DEBUG") == "true" else {}
            }
        }
    )

# ============ 健康检查端点 ============

@app.get("/health", tags=["Health"], status_code=status.HTTP_200_OK)
async def health_check(request: Request):
    """
    健康检查端点

    用于负载均衡器和监控系统
    """
    try:
        # 检查数据库连接
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")

        return {
            "status": "healthy",
            "service": "LangChain AI Conversation API",
            "version": "1.0.0",
            "request_id": request.state.request_id,
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "request_id": request.state.request_id,
            }
        )

@app.get("/ready", tags=["Health"], status_code=status.HTTP_200_OK)
async def readiness_check(request: Request):
    """
    就绪检查端点

    用于 Kubernetes 就绪探针
    """
    return {
        "ready": True,
        "version": "1.0.0",
        "request_id": request.state.request_id,
    }

# ============ 根端点 ============

@app.get("/", tags=["Root"])
async def root(request: Request):
    """根端点 - API 信息"""
    return {
        "message": "LangChain AI Conversation API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/health",
        "request_id": request.state.request_id,
        "endpoints": {
            "conversations": "/api/v1/conversations",
            "documents": "/api/v1/documents",
            "messages": "/api/v1/conversations/{id}/messages",
            "tools": "/api/v1/tools",
            "websocket": "/ws/v1/conversations/{id}",
        },
    }

# ============ 路由注册 ============

logger.info("Registering API routes...")

# API v1 路由组
from fastapi import APIRouter

api_router = APIRouter(prefix="/api/v1")

# 导入并注册路由
from src.api.conversation_routes import router as conversation_router
from src.api.message_routes import router as message_router
from src.api.document_routes import router as document_router
from src.api.tools_routes import router as tools_router
from src.api.websocket_routes import router as websocket_router

# 注册路由（去除前缀，因为已在 api_router 中定义）
api_router.include_router(
    conversation_router,
    tags=["Conversations"]
)
api_router.include_router(
    message_router,
    tags=["Messages"]
)
api_router.include_router(
    document_router,
    tags=["Documents"]
)
api_router.include_router(
    tools_router,
    tags=["Tools"]
)

app.include_router(api_router)
app.include_router(websocket_router)

logger.info("All routes registered successfully")

# ============ 应用入口 ============

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("ENV", "development") == "development",
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
        workers=int(os.getenv("WORKERS", "1")),
    )
```

### Task 1.3.2: 改进的依赖注入模式

**当前问题**：

```python
# 当前方式（重复太多）
@router.get("")
async def list_conversations(
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_user_id),
):
    pass
```

**改进方案 - 使用自定义依赖注入**：

```python
# src/api/dependencies.py

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.config import get_async_session
from src.repositories import ConversationRepository, MessageRepository
from src.services.conversation_service import ConversationService

# ============ 基础依赖 ============

async def get_request_id(request: Request) -> str:
    """从请求中获取请求 ID"""
    return getattr(request.state, "request_id", "unknown")

async def get_user_id(request: Request) -> str:
    """从请求中获取用户 ID"""
    # 实际应用中应从认证令牌或会话中获取
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing user ID"
        )
    return user_id

# ============ 服务依赖 ============

async def get_conversation_service(
    session: AsyncSession = Depends(get_async_session),
) -> ConversationService:
    """获取对话服务实例"""
    return ConversationService(session)

async def get_conversation_repository(
    session: AsyncSession = Depends(get_async_session),
) -> ConversationRepository:
    """获取对话存储库实例"""
    return ConversationRepository(session)

async def get_message_repository(
    session: AsyncSession = Depends(get_async_session),
) -> MessageRepository:
    """获取消息存储库实例"""
    return MessageRepository(session)

# ============ 注解式类型提示 ============

# 使用 Annotated 简化依赖注入
RequestIdType = Annotated[str, Depends(get_request_id)]
UserIdType = Annotated[str, Depends(get_user_id)]
ConversationServiceType = Annotated[
    ConversationService,
    Depends(get_conversation_service)
]
ConversationRepositoryType = Annotated[
    ConversationRepository,
    Depends(get_conversation_repository)
]

# ============ 路由中的用法 ============

# 改进前
@router.get("")
async def list_conversations(
    skip: int = 0,
    limit: int = 10,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_user_id),
):
    service = ConversationService(session)
    # ...

# 改进后
@router.get("")
async def list_conversations(
    skip: int = 0,
    limit: int = 10,
    request_id: RequestIdType,
    user_id: UserIdType,
    service: ConversationServiceType,
):
    """简洁清晰的签名，依赖通过类型注解自动注入"""
    # ...
```

**改进的对话路由**：

```python
# src/api/conversation_routes.py - 重构版本

import logging
import uuid
from typing import Optional, Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import (
    UserIdType,
    RequestIdType,
    ConversationServiceType,
    get_async_session,
)
from src.schemas.conversation_schema import (
    CreateConversationRequest,
    UpdateConversationRequest,
    ConversationResponse,
    ConversationListResponse,
)
from src.main import APIError, limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations")

# ============ 对话管理端点 ============

@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED
)
@limiter.limit("10/minute")
async def create_conversation(
    request_id: RequestIdType,
    user_id: UserIdType,
    service: ConversationServiceType,
    request_data: CreateConversationRequest,
):
    """
    创建新对话

    **参数**：
    - title: 对话标题
    - system_prompt: 系统提示
    - model: 使用的模型（可选）
    - metadata: 附加元数据（可选）

    **返回**：
    - 新创建的对话详情
    """
    try:
        logger.info(
            f"[{request_id}] Creating conversation for user {user_id}",
            extra={"user_id": user_id, "title": request_data.title}
        )

        conversation = await service.create_conversation(
            user_id=user_id,
            title=request_data.title,
            system_prompt=request_data.system_prompt,
            model=request_data.model,
            metadata=request_data.metadata,
        )

        return ConversationResponse(
            id=str(conversation.id),
            user_id=conversation.user_id,
            title=conversation.title,
            summary=conversation.summary,
            model=conversation.model,
            message_count=0,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )

    except Exception as e:
        logger.error(
            f"[{request_id}] Error creating conversation: {str(e)}",
            exc_info=True
        )
        raise APIError(
            message="Failed to create conversation",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="CREATE_CONVERSATION_ERROR",
        )

@router.get("", response_model=ConversationListResponse)
@limiter.limit("30/minute")
async def list_conversations(
    request_id: RequestIdType,
    user_id: UserIdType,
    service: ConversationServiceType,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    """
    列表查询用户的对话

    **参数**：
    - skip: 跳过的记录数（可选，默认0）
    - limit: 返回的记录数（可选，默认10，最多100）

    **返回**：
    - 对话列表与分页信息
    """
    try:
        logger.info(
            f"[{request_id}] Listing conversations for user {user_id}",
            extra={"skip": skip, "limit": limit}
        )

        conversations, total = await service.list_conversations(
            user_id=user_id,
            skip=skip,
            limit=limit,
        )

        items = [
            ConversationResponse(
                id=str(conv.id),
                user_id=conv.user_id,
                title=conv.title,
                summary=conv.summary,
                model=conv.model,
                message_count=await service.msg_repo.get_conversation_message_count(
                    conv.id
                ),
                created_at=conv.created_at,
                updated_at=conv.updated_at,
            )
            for conv in conversations
        ]

        return ConversationListResponse(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
        )

    except Exception as e:
        logger.error(
            f"[{request_id}] Error listing conversations: {str(e)}",
            exc_info=True
        )
        raise APIError(
            message="Failed to list conversations",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="LIST_CONVERSATIONS_ERROR",
        )

# ... 更多端点
```

### Task 1.3.3: 文档和 OpenAPI 配置

**增强的 OpenAPI 配置**：

```python
# src/api/openapi_config.py

def get_openapi_schema():
    """获取自定义 OpenAPI 架构"""

    return {
        "openapi": "3.0.0",
        "info": {
            "title": "LangChain AI Conversation API",
            "description": """
            LangChain 1.0 AI Conversation 系统的后端 API

            ## 特性
            - 基于 LangChain 1.0 的现代 AI 对话系统
            - RAG（检索增强生成）支持
            - 向量搜索和语义理解
            - 完整的对话历史管理
            - 工具调用和代理支持

            ## 认证
            所有 API 端点（除了 `/health`）都需要在请求头中提供用户 ID：

            ```
            X-User-ID: user123
            ```

            ## 限流
            - 创建操作：10/分钟
            - 读取操作：30/分钟
            - 默认：100/分钟

            ## 错误处理
            所有错误响应都遵循以下格式：

            ```json
            {
              "error": {
                "code": "ERROR_CODE",
                "message": "Human-readable error message",
                "request_id": "unique-request-id",
                "details": {}
              }
            }
            ```
            """,
            "version": "1.0.0",
            "contact": {
                "name": "API Support",
                "url": "https://example.com/support",
                "email": "api@example.com"
            },
            "license": {
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT"
            }
        },
        "servers": [
            {
                "url": "http://localhost:8000",
                "description": "Local development server"
            },
            {
                "url": "https://api.example.com",
                "description": "Production server"
            }
        ],
        "tags": [
            {
                "name": "Conversations",
                "description": "对话管理端点"
            },
            {
                "name": "Messages",
                "description": "消息管理端点"
            },
            {
                "name": "Documents",
                "description": "文档和 RAG 端点"
            },
            {
                "name": "Tools",
                "description": "工具和代理端点"
            },
            {
                "name": "Health",
                "description": "健康检查端点"
            }
        ]
    }

# 在 main.py 中使用
app.openapi_schema = get_openapi_schema()
```

---

## LangChain 1.0 最佳实践

### 1. 中间件集成

**推荐的中间件栈**：

```
请求 → 认证 → 审计日志 → 内容审核 → 记忆注入 → 响应结构化 → 业务逻辑
```

**每个中间件的职责**：

| 中间件 | 职责 | 优先级 | 性能影响 |
|-------|------|-------|---------|
| AuthenticationMiddleware | 用户验证和授权 | 1 (最高) | <5ms |
| AuditLoggingMiddleware | 请求/响应日志 | 2 | <10ms |
| ContentModerationMiddleware | 内容过滤和安全检查 | 3 | 10-50ms |
| MemoryInjectionMiddleware | 注入用户记忆/上下文 | 4 | 20-100ms |
| ResponseStructuringMiddleware | 响应格式标准化 | 5 (最低) | <5ms |

### 2. 内容块解析

**LangChain 1.0 内容块 API** 用于处理工具调用和响应：

```python
# src/services/content_blocks_parser.py

from langchain.messages import AIMessage, ToolCall

async def parse_ai_response_content_blocks(response):
    """
    解析 AI 响应中的内容块

    LangChain 1.0 统一了跨提供者的内容块表示
    """
    content_blocks = response.content

    tool_calls = []
    text_content = []
    reasoning_content = []

    for block in content_blocks:
        if isinstance(block, ToolCall):
            tool_calls.append({
                "id": block.id,
                "name": block.name,
                "arguments": block.arguments
            })
        elif isinstance(block, dict):
            if block.get("type") == "text":
                text_content.append(block.get("text", ""))
            elif block.get("type") == "reasoning":
                reasoning_content.append(block.get("thinking", ""))

    return {
        "text": "\n".join(text_content),
        "tool_calls": tool_calls,
        "reasoning": "\n".join(reasoning_content),
    }
```

### 3. 状态持久化（LangGraph 集成）

**建议的状态管理方案**：

```python
# 使用 LangGraph 管理对话状态
from langgraph.graph import StateGraph
from typing import TypedDict, Annotated

class ConversationState(TypedDict):
    """对话状态定义"""
    conversation_id: str
    user_id: str
    messages: Annotated[list, "Message history"]
    current_context: Annotated[dict, "Current execution context"]
    tokens_used: int
    memory_summary: str

# 使用 LangGraph 持久化
async def create_conversation_graph():
    """创建对话处理图"""
    graph = StateGraph(ConversationState)

    # 定义节点
    async def process_user_input(state: ConversationState):
        # 处理用户输入
        pass

    async def retrieve_context(state: ConversationState):
        # 从 RAG 检索上下文
        pass

    async def generate_response(state: ConversationState):
        # 使用 LangChain create_agent 生成响应
        pass

    # 连接节点
    graph.add_node("process_input", process_user_input)
    graph.add_node("retrieve_context", retrieve_context)
    graph.add_node("generate_response", generate_response)

    graph.add_edge("process_input", "retrieve_context")
    graph.add_edge("retrieve_context", "generate_response")

    return graph.compile()
```

### 4. 成本优化

**Token 优化策略**：

```python
# src/services/middleware/cost_tracking.py

class CostTracker:
    """追踪和优化 LLM 成本"""

    def __init__(self):
        self.pricing = {
            "claude-sonnet-4-5-20250929": {
                "input": 0.003,  # 每1M tokens $3
                "output": 0.015  # 每1M tokens $15
            }
        }

    async def estimate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """估计成本"""
        if model not in self.pricing:
            return 0

        pricing = self.pricing[model]
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    async def implement_cost_controls(
        self,
        conversation_id: str,
        max_tokens: int = 4000,
        max_cost: float = 1.0
    ):
        """
        实施成本控制

        - 限制上下文大小
        - 使用结构化输出减少重新生成
        - 缓存常见查询
        """
        pass
```

---

## 性能优化策略

### 1. 数据库性能基准

**目标 SLA**：

| 操作 | 目标延迟 | P99 | 索引覆盖 |
|------|---------|-----|---------|
| 获取对话 | 50ms | 100ms | Primary Key |
| 列表查询 (LIMIT 10) | 80ms | 150ms | Composite |
| 搜索对话 | 150ms | 300ms | Title Index |
| 向量搜索 (1K results) | 200ms | 400ms | HNSW |
| 批量插入 (1000) | 100ms | 150ms | Batch |

**测试和验证脚本**：

```python
# tests/test_performance.py

import pytest
import asyncio
import time
from uuid import uuid4

from src.db.config import AsyncSessionLocal
from src.repositories import ConversationRepository

@pytest.mark.asyncio
async def test_conversation_list_performance():
    """测试对话列表查询性能"""
    async with AsyncSessionLocal() as session:
        repo = ConversationRepository(session)

        # 预准备数据
        user_id = "test_user_123"

        # 创建100个对话
        for i in range(100):
            await repo.create(
                user_id=user_id,
                title=f"Conversation {i}",
                system_prompt="You are helpful",
            )

        # 测试性能
        start = time.time()
        conversations = await repo.get_user_conversations(
            user_id,
            skip=0,
            limit=10
        )
        elapsed_ms = (time.time() - start) * 1000

        assert len(conversations) == 10
        assert elapsed_ms < 100, f"Expected < 100ms, got {elapsed_ms:.2f}ms"

@pytest.mark.asyncio
async def test_vector_search_performance():
    """测试向量搜索性能"""
    from src.repositories import EmbeddingRepository
    import numpy as np

    async with AsyncSessionLocal() as session:
        repo = EmbeddingRepository(session)

        # 生成随机向量
        query_embedding = np.random.randn(1536).tolist()

        # 测试性能
        start = time.time()
        results = await repo.search_similar(
            query_embedding,
            user_id="test_user_123",
            limit=5,
            threshold=0.7
        )
        elapsed_ms = (time.time() - start) * 1000

        assert elapsed_ms < 200, f"Expected < 200ms, got {elapsed_ms:.2f}ms"
```

### 2. 缓存策略

**Redis 缓存集成**：

```python
# src/cache/redis_cache.py

import json
from redis import asyncio as aioredis
from typing import Optional, Any

class RedisCache:
    """Redis 缓存管理"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = None
        self.redis_url = redis_url

    async def connect(self):
        """连接到 Redis"""
        self.redis = await aioredis.from_url(self.redis_url)

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        value = await self.redis.get(key)
        return json.loads(value) if value else None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600
    ) -> bool:
        """设置缓存值（带 TTL）"""
        await self.redis.set(key, json.dumps(value), ex=ttl)
        return True

    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        await self.redis.delete(key)
        return True

    async def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的所有缓存"""
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
        return len(keys)

# 集成到存储库
class CachedConversationRepository(ConversationRepository):
    """带缓存的对话存储库"""

    def __init__(self, session, cache: RedisCache):
        super().__init__(session)
        self.cache = cache

    async def get_user_conversations(self, user_id: str, **kwargs):
        """带缓存的用户对话查询"""
        cache_key = f"conversations:{user_id}:{kwargs.get('skip', 0)}:{kwargs.get('limit', 10)}"

        # 尝试从缓存获取
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        # 从数据库获取
        results = await super().get_user_conversations(user_id, **kwargs)

        # 存储到缓存
        await self.cache.set(
            cache_key,
            [r.to_dict() for r in results],
            ttl=300  # 5分钟 TTL
        )

        return results
```

---

## 风险与缓解

### 1. 高风险项

| 风险 | 影响 | 可能性 | 缓解策略 |
|------|------|-------|---------|
| 数据库连接泄漏 | 连接池枯竭 | 中 | 显式资源管理，连接池监控 |
| N+1 查询问题 | 性能下降 | 高 | 使用 SQLAlchemy selectinload，查询审计 |
| 向量索引膨胀 | 搜索变慢 | 中 | 定期重建索引，分区管理 |
| 事务死锁 | 请求挂起 | 低 | 超时配置，死锁检测 |
| 缓存不一致 | 数据错误 | 中 | 缓存失效策略，版本控制 |

### 2. 缓解策略详解

**连接泄漏防护**：

```python
# src/db/connection_monitor.py

import logging
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

class ConnectionMonitor:
    """监控数据库连接池健康状况"""

    def __init__(self, engine):
        self.engine = engine

    async def check_pool_health(self):
        """检查连接池健康状况"""
        pool = self.engine.pool

        if not isinstance(pool, QueuePool):
            return

        logger.info(
            f"Connection pool status: "
            f"Size={pool.size()}, "
            f"Checked out={pool.checkedout()}, "
            f"Queue size={pool.queue.qsize()}"
        )

        # 告警条件
        if pool.checkedout() > pool.size() * 0.8:
            logger.warning(
                f"Connection pool utilization high: "
                f"{pool.checkedout()}/{pool.size()}"
            )
```

---

## 实现路线图

### Phase 1: 基础设施 (Week 1-2)

**任务**：
- [x] ORM 模型定义（已完成）
- [x] 数据库连接配置（已完成）
- [ ] 数据库迁移系统完善
- [ ] BaseRepository 增强实现
- [ ] 异常处理系统

**可交付物**：
- 完整的数据库架构
- 通用 Repository 框架
- 单元测试套件

### Phase 2: 存储库实现 (Week 2-3)

**任务**：
- [ ] ConversationRepository 完整实现
- [ ] MessageRepository 完整实现
- [ ] DocumentRepository 完整实现
- [ ] EmbeddingRepository 优化实现
- [ ] 集成测试

**可交付物**：
- 所有 Repository 类
- 集成测试用例
- 性能基准报告

### Phase 3: API 层 (Week 3-4)

**任务**：
- [ ] 改进 FastAPI 初始化
- [ ] 完整的 CRUD 路由
- [ ] 认证和授权
- [ ] 速率限制
- [ ] OpenAPI 文档

**可交付物**：
- 完整 API 实现
- API 文档
- 端到端测试

### Phase 4: 优化和监控 (Week 4-5)

**任务**：
- [ ] 性能优化
- [ ] 缓存集成
- [ ] 日志和监控
- [ ] 生产部署准备
- [ ] 压力测试

**可交付物**：
- 优化报告
- 监控仪表板
- 部署指南

---

## 检查清单

### 开发环境设置

- [ ] PostgreSQL 12+ 已安装
- [ ] pgvector 扩展已安装
- [ ] Python 3.12 已配置
- [ ] 依赖包已安装 (`uv install`)
- [ ] 环境变量已配置 (`.env` 文件)

### 数据库准备

- [ ] 创建了数据库
- [ ] 应用了所有迁移
- [ ] 创建了所有索引
- [ ] 测试了连接

### 代码质量

- [ ] 遵循 PEP 8 风格
- [ ] 所有函数都有文档字符串
- [ ] 错误处理完整
- [ ] 单元测试覆盖 > 80%
- [ ] 类型提示完整

### 性能验证

- [ ] 向量搜索 < 200ms P99
- [ ] 列表查询 < 100ms
- [ ] 批量插入正常工作
- [ ] 没有 N+1 查询问题
- [ ] 连接池正常工作

### 安全性

- [ ] 所有用户输入都已验证
- [ ] SQL 注入已防护（ORM）
- [ ] 认证已实施
- [ ] 速率限制已配置
- [ ] CORS 已正确配置

---

## 参考资源

1. **SQLAlchemy 异步文档**：https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
2. **PostgreSQL pgvector**：https://github.com/pgvector/pgvector
3. **FastAPI 最佳实践**：https://fastapi.tiangolo.com/
4. **LangChain 1.0**：https://python.langchain.com/
5. **Redis 缓存模式**：https://redis.io/docs/patterns/

---

**文档结束**
