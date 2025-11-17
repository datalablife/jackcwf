# Epic 3: 中间件系统与特性完成 - 实现规范

**版本**: 1.0.0
**创建日期**: 2025-11-17
**状态**: 待实现
**总故事点**: 26 story points
**预期交付**: Week 3-4 (10 工作日)

---

## 📋 Executive Summary

Epic 3 实现后端中间件架构、API 端点、流式处理和生产就绪特性。此 Epic 建立在 Epic 1（基础设施）和 Epic 2（RAG + Agent）之上，完成完整的 AI 对话系统后端。

### 核心交付物

| 模块 | 文件 | 完成标准 |
|------|------|--------|
| 5层中间件 | `src/middleware/*.py` | 5个middleware + 错误处理 |
| API端点 | `src/api/routes/*.py` | 对话/消息/文档/WebSocket |
| 健康检查 | `src/infrastructure/health.py` | 4个服务检查 + 优雅关闭 |
| 测试套件 | `tests/test_epic3_*.py` | 100+ 测试用例，>80% 覆盖率 |
| 文档 | `docs/guides/EPIC3_*.md` | API文档、部署指南 |

---

## Story 3.1: 5层中间件实现 + 错误处理 (16 pts)

### 3.1.1 认证和记忆注入中间件 (4 pts)

#### 文件位置
- `src/middleware/authentication_middleware.py`
- `src/middleware/memory_injection_middleware.py`
- `src/middleware/__init__.py`

#### 实现要求

**AuthenticationMiddleware:**
```python
# 功能需求:
- JWT token 验证 (Bearer scheme)
- 多算法支持 (HS256, RS256)
- Token 过期检查
- user_id 提取和注入到 request.state
- JWT_AUDIENCE / JWT_ISSUER 约束检查
- 特殊端点白名单 (/health, /docs)

# 性能目标:
- 认证耗时: <10ms
- 缓存失效: 5分钟
```

**MemoryInjectionMiddleware:**
```python
# 功能需求:
- 异步提取最近 5 条消息
- 向量化查询并搜索相关文档 (RAG)
- 并行执行（asyncio.TaskGroup）
- 注入到 request.state:
  - conversation_history: List[dict]
  - rag_context: List[dict]
  - memory_error: Optional[str]

# 性能目标:
- 总耗时: ≤200ms (99%ile)
- 向量搜索: ≤150ms
- 消息查询: ≤50ms
```

#### 集成点
- 中间件栈顺序: Authentication → MemoryInjection → ContentModeration → ...
- 异常处理: 认证失败返回 401, 记忆注入失败应用降级策略

#### 单元测试
```python
# test_authentication_middleware.py
- test_valid_jwt_token()
- test_expired_token()
- test_invalid_signature()
- test_missing_token()
- test_special_endpoints_bypass()

# test_memory_injection_middleware.py
- test_parallel_execution()
- test_rag_context_injection()
- test_conversation_history_retrieval()
- test_timeout_handling()
```

---

### 3.1.2 内容审核和响应结构化中间件 (4 pts)

#### 文件位置
- `src/middleware/content_moderation_middleware.py`
- `src/middleware/response_structuring_middleware.py`

#### 实现要求

**ContentModerationMiddleware:**
```python
# 功能需求:
- 提示注入检测 (检查 SQL 关键字, 越狱尝试)
- 有害内容过滤 (调用外部API或本地模型)
- 速率限制:
  - 用户级: 100 req/min
  - IP级: 1000 req/min
  - 触发限制返回 429 Too Many Requests
- 内容长度验证:
  - 请求: ≤10000 字符
  - 响应: ≤50000 字符

# 配置:
- MODERATION_ENABLED: bool
- RATE_LIMIT_ENABLED: bool
- RATE_LIMIT_WINDOW_SECONDS: 60
```

**ResponseStructuringMiddleware:**
```python
# 功能需求:
- 统一响应格式:
  {
    "success": bool,
    "data": Optional[Any],
    "error": Optional[str],
    "error_code": Optional[str],
    "timestamp": str (ISO8601),
    "request_id": str,
    "metadata": {
      "tokens_used": int,
      "tools_called": List[str],
      "duration_ms": float
    }
  }
- 状态码规范化
- 错误消息统一
- 元数据注入
- 响应验证 (Pydantic schema)

# 性能目标:
- 结构化耗时: <5ms
```

#### 集成点
- 与 AuditLoggingMiddleware 配合记录结构化响应
- 错误处理: 确保异常被正确捕获和格式化

#### 单元测试
```python
# test_content_moderation_middleware.py
- test_sql_injection_detection()
- test_harmful_content_filtering()
- test_rate_limit_enforcement()
- test_content_length_validation()

# test_response_structuring_middleware.py
- test_response_format()
- test_error_responses()
- test_metadata_injection()
- test_status_code_mapping()
```

---

### 3.1.3 审计日志中间件和集成 (5 pts)

#### 文件位置
- `src/middleware/audit_logging_middleware.py`
- `src/infrastructure/logging_config.py`

#### 实现要求

**AuditLoggingMiddleware:**
```python
# 功能需求:
- 为每个请求分配唯一 request_id (X-Request-ID header)
- 记录请求信息:
  - request_id, user_id, method, path, query_params
  - conversation_id (if present)
  - 请求体摘要 (敏感字段脱敏)

- 测量执行时间并分解:
  - total_duration_ms
  - auth_middleware_ms
  - memory_injection_ms
  - agent_execution_ms
  - response_structuring_ms

- 记录响应信息:
  - status_code, response_size
  - tokens_used, tools_called
  - error (if any)

- 性能指标:
  - >1s 请求发出 WARN 日志
  - >5s 请求发出 ERROR 日志

- 日志格式: 结构化 JSON (structlog)
  {
    "timestamp": "2025-11-17T10:30:45.123Z",
    "level": "INFO",
    "event": "request_completed",
    "request_id": "...",
    "user_id": "...",
    "method": "POST",
    "path": "/api/v1/conversations/123/messages",
    "status_code": 200,
    "duration_ms": 345,
    "tokens_used": 150,
    "tools_called": ["search_documents"]
  }

# 日志输出:
- 同步写入: stdout (JSON)
- 异步写入: 日志聚合系统 (DataDog/CloudWatch)
```

**集成要求:**
```python
# 中间件栈顺序验证:
1. AuthenticationMiddleware (extracts user_id)
2. MemoryInjectionMiddleware (adds context)
3. ContentModerationMiddleware (validates input)
4. ResponseStructuringMiddleware (formats response)
5. AuditLoggingMiddleware (logs everything)

# 执行顺序: 请求 → 1 → 2 → 3 → 4 → 处理 → 4 → 3 → 2 → 1 → 5 → 响应
```

#### 单元测试
```python
# test_audit_logging_middleware.py
- test_request_id_generation()
- test_request_logging()
- test_response_logging()
- test_performance_metrics()
- test_slow_request_warning()
- test_middleware_order()
- test_json_log_format()
```

---

### 3.1.4 中间件错误处理和容错机制 (3 pts)

#### 文件位置
- `src/middleware/error_handling.py`
- `src/middleware/base_middleware.py`

#### 实现要求

**ErrorHandlingStrategy:**
```python
# 定义降级策略:
class FallbackStrategy(Enum):
    RETURN_PARTIAL = "return_partial"      # 返回部分结果
    RETRY_ONCE = "retry_once"              # 单次重试 (延迟100ms)
    SKIP_CONTEXT = "skip_context"          # 跳过该上下文，继续处理
    RETURN_ERROR = "return_error"           # 返回错误 (fail-fast)

# 各中间件的超时和降级策略:
- AuthenticationMiddleware:
  - Timeout: 50ms
  - Strategy: RETURN_ERROR (认证失败)

- MemoryInjectionMiddleware:
  - Timeout: 200ms
  - Strategy: SKIP_CONTEXT (返回空历史和RAG)

- ContentModerationMiddleware:
  - Timeout: 100ms
  - Strategy: RETURN_PARTIAL (返回请求，跳过审核)

- ResponseStructuringMiddleware:
  - Timeout: 20ms
  - Strategy: RETURN_ERROR (结构化失败是致命的)
```

**实现细节:**
```python
# 超时保护:
async with asyncio.timeout(timeout_ms / 1000):
    # 执行中间件逻辑
    pass

# 错误恢复:
try:
    # 尝试主流程
except asyncio.TimeoutError:
    # 应用降级策略
    await logger.aerror("middleware_timeout", ...)
    await apply_fallback_strategy(request, strategy)

except Exception as exc:
    # 记录并传播
    await logger.aerror("middleware_error", ...)
    if strategy == FallbackStrategy.RETURN_ERROR:
        raise
    else:
        # 应用降级，继续处理

# 重试逻辑:
async def retry_with_backoff(func, max_retries=2, delay_ms=50):
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(delay_ms / 1000 * (2 ** attempt))
```

**监控和告警:**
```python
# 中间件错误率监控:
- memory_injection_errors / memory_injection_calls > 5% → WARN
- rag_context_skipped_count > 10% of calls → ALERT
- middleware_timeout_count > 1% of calls → ALERT

# 性能监控:
- P50, P95, P99 延迟分别监控
- 单个中间件不应超过其超时配置 90%ile
```

#### 环境配置
```env
# .env
MEMORY_INJECTION_TIMEOUT_MS=200
MEMORY_INJECTION_FALLBACK=skip_context
VECTOR_SEARCH_TIMEOUT_MS=200
VECTOR_SEARCH_RETRY_COUNT=1
CONTENT_MODERATION_TIMEOUT_MS=100
CONTENT_MODERATION_FALLBACK=return_partial
AUTH_TIMEOUT_MS=50
AUTH_FALLBACK=return_error
RESPONSE_STRUCT_TIMEOUT_MS=20
RESPONSE_STRUCT_FALLBACK=return_error
```

#### 单元测试
```python
# test_error_handling.py
- test_timeout_handling()
- test_fallback_strategies()
- test_retry_logic()
- test_error_propagation()
- test_memory_injection_degradation()
- test_concurrent_middleware_errors()
```

---

## Story 3.2: API 端点实现 (8 pts)

### 3.2.1 对话端点实现 (3 pts)

#### 文件位置
- `src/api/conversation_routes.py` (增强)
- `src/schemas/conversation_schema.py` (新)

#### 端点列表

**POST /api/v1/conversations**
```python
# 创建新对话
Request:
{
  "title": str,
  "system_prompt": Optional[str],
  "model": Optional[str],  # default: "claude-sonnet-4-5-20250929"
  "metadata": Optional[dict]
}

Response (201):
{
  "success": true,
  "data": {
    "id": UUID,
    "user_id": str,
    "title": str,
    "model": str,
    "created_at": ISO8601,
    "system_prompt": str,
    "metadata": dict
  },
  "request_id": str,
  "timestamp": ISO8601
}

Errors:
- 400: Invalid input (missing title, etc.)
- 401: Unauthorized
- 500: Server error
```

**GET /api/v1/conversations**
```python
# 列出用户对话 (分页)
Query Parameters:
- page: int = 1
- page_size: int = 20 (max 100)
- sort_by: Literal["created_at", "updated_at"] = "created_at"
- sort_order: Literal["asc", "desc"] = "desc"

Response (200):
{
  "success": true,
  "data": {
    "items": [
      {
        "id": UUID,
        "title": str,
        "model": str,
        "created_at": ISO8601,
        "message_count": int,
        "last_message_at": ISO8601
      },
      ...
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": int,
      "pages": int
    }
  },
  "request_id": str,
  "timestamp": ISO8601
}

Errors:
- 401: Unauthorized
- 422: Invalid pagination params
```

**GET /api/v1/conversations/{conversation_id}**
```python
# 获取对话详情
Response (200):
{
  "success": true,
  "data": {
    "id": UUID,
    "user_id": str,
    "title": str,
    "model": str,
    "system_prompt": str,
    "created_at": ISO8601,
    "updated_at": ISO8601,
    "message_count": int,
    "metadata": dict
  },
  "request_id": str,
  "timestamp": ISO8601
}

Errors:
- 404: Conversation not found
- 401: Unauthorized (not owner)
```

**PUT /api/v1/conversations/{conversation_id}**
```python
# 更新对话
Request:
{
  "title": Optional[str],
  "metadata": Optional[dict]
}

Response (200): Updated conversation object
```

**DELETE /api/v1/conversations/{conversation_id}**
```python
# 软删除对话
Response (204): No content

Errors:
- 404: Not found
- 401: Unauthorized
```

#### 验证和安全
- 所有输入用 Pydantic schema 验证
- SQL 注入防护 (SQLAlchemy parameterized queries)
- 所有者验证 (user_id 必须匹配)
- 分页限制: max 100 items/page

#### 集成
- 与 ConversationRepository 交互
- 与 ConversationSummarizationService 交互 (检查是否需要总结)
- 中间件堆栈: 所有中间件应用

#### 单元测试
```python
# test_conversation_endpoints.py
- test_create_conversation()
- test_list_conversations_pagination()
- test_get_conversation_detail()
- test_update_conversation()
- test_delete_conversation()
- test_unauthorized_access()
- test_input_validation()
- test_not_found_error()
```

---

### 3.2.2 消息端点和 WebSocket (3 pts)

#### 文件位置
- `src/api/message_routes.py` (增强)
- `src/api/websocket_routes.py` (增强)
- `src/schemas/message_schema.py`

#### 端点列表

**GET /api/v1/conversations/{conversation_id}/messages**
```python
# 获取对话消息列表
Query Parameters:
- page: int = 1
- page_size: int = 50
- role: Optional[Literal["user", "assistant", "system"]]

Response (200):
{
  "success": true,
  "data": {
    "items": [
      {
        "id": UUID,
        "conversation_id": UUID,
        "role": str,
        "content": str,
        "tool_calls": Optional[List[dict]],
        "tool_results": Optional[List[dict]],
        "tokens_used": int,
        "created_at": ISO8601
      },
      ...
    ],
    "pagination": { ... }
  },
  "request_id": str
}
```

**POST /api/v1/conversations/{conversation_id}/messages**
```python
# 发送消息 (同步)
Request:
{
  "content": str (≤10000 chars),
  "metadata": Optional[dict]
}

Response (200):
{
  "success": true,
  "data": {
    "id": UUID,
    "content": str,
    "role": "assistant",
    "tool_calls": List[dict],
    "tokens_used": int,
    "created_at": ISO8601
  },
  "metadata": {
    "tokens_used": int,
    "tools_called": List[str],
    "duration_ms": float,
    "summary_triggered": bool
  },
  "request_id": str
}

Errors:
- 400: Empty content
- 404: Conversation not found
- 429: Rate limit exceeded
- 500: Agent execution error
```

**WebSocket /api/v1/ws/{conversation_id}**
```python
# 流式消息处理
# 连接建立:
1. WebSocket 连接建立
2. 认证检查 (token from query param or header)
3. 对话验证 (conversation_id 属于 user)
4. 加载上下文 (消息历史、文档、总结)

# 客户端发送格式:
{
  "type": "message",
  "content": str,
  "metadata": Optional[dict]
}

# 服务器推送事件:

Event 1: message_start
{
  "type": "message_start",
  "message_id": UUID,
  "timestamp": ISO8601
}

Event 2: message_chunk (repeating)
{
  "type": "message_chunk",
  "chunk": str,
  "delta": str
}

Event 3: tool_call (if applicable)
{
  "type": "tool_call",
  "tool_name": str,
  "tool_input": dict,
  "tool_id": str
}

Event 4: tool_result (if applicable)
{
  "type": "tool_result",
  "tool_id": str,
  "tool_result": str,
  "error": Optional[str]
}

Event 5: complete_state
{
  "type": "complete_state",
  "message_id": UUID,
  "role": "assistant",
  "content": str,
  "tool_calls": List[dict],
  "tokens_used": int,
  "created_at": ISO8601
}

# 心跳机制:
- 服务器每 30s 发送 heartbeat 事件
- 客户端未发送数据 5 分钟后关闭连接

# 错误处理:
{
  "type": "error",
  "error_code": str,
  "error_message": str
}
```

#### 实现细节
```python
# WebSocket 生命周期:
1. 连接建立 (on_connect)
   - 验证用户和对话
   - 加载消息历史
   - 加载 RAG 上下文
   - 检查是否需要总结

2. 消息接收 (on_message)
   - 验证内容
   - 调用 AgentService.stream_message()
   - 流式推送事件

3. 错误处理 (on_error)
   - 捕获异常
   - 发送错误事件
   - 记录到审计日志

4. 连接关闭 (on_disconnect)
   - 清理资源
   - 记录连接统计

# 性能要求:
- 消息处理延迟: <2000ms (平均)
- 流式推送延迟: <100ms per chunk
- 最大连接数: 1000 并发
- 消息队列大小: 100 events
```

#### 单元测试
```python
# test_message_endpoints.py
- test_get_messages_pagination()
- test_send_message_sync()
- test_unauthorized_access()

# test_websocket_routes.py
- test_websocket_connection()
- test_websocket_message_stream()
- test_tool_calls_streaming()
- test_tool_results_streaming()
- test_websocket_disconnection()
- test_websocket_timeout()
- test_concurrent_websocket_connections()
- test_heartbeat_mechanism()
- test_error_handling_in_websocket()
```

---

### 3.2.3 文档上传和搜索端点 (2 pts)

#### 文件位置
- `src/api/document_routes.py` (已存在，需增强)
- `src/api/embedding_routes.py` (可选，可并入 document_routes)

#### 端点列表 (已在 Epic 2 中实现，此处验证完成度)

**POST /api/v1/documents/upload**
- 验证文件大小 ≤50MB
- 验证文件类型 (PDF, TXT, MD)
- 异步处理 (返回 202 accepted)
- 后台任务: 分块 → 向量化 → 存储
- 返回 document_id 和 status

**GET /api/v1/documents**
- 分页列表用户文档
- 按 created_at 排序

**GET /api/v1/documents/{document_id}**
- 获取文档详情 (chunks count, size, etc.)

**GET /api/v1/documents/{document_id}/chunks**
- 获取文档分块列表 (分页)
- 返回 chunk_text, metadata, chunk_index

**POST /api/v1/documents/search**
- 语义搜索查询
- 请求: { "query": str, "limit": int }
- 返回: [{ "document_id", "chunk_text", "score" }]
- 性能: ≤500ms

**DELETE /api/v1/documents/{document_id}**
- 软删除文档及其 embeddings

#### 验证清单
- ✅ 文件上传处理
- ✅ Token-based 分块
- ✅ OpenAI embeddings 集成
- ✅ pgvector 存储和搜索
- ✅ 异步后台处理
- ✅ 错误处理和重试
- ✅ 单元和集成测试

---

## Story 3.3: 特性完成和生产就绪性 (8 pts)

### 3.3.1 流式响应实现 (2 pts)

#### 实现需求

**Server-Sent Events (SSE) 支持:**
```python
# 端点: GET /api/v1/conversations/{id}/stream
# 用途: 某些前端可能更偏好 SSE 而不是 WebSocket
# 实现:
- 单向服务器到客户端流
- 自动重连
- 事件格式同 WebSocket

# 示例:
data: {"type":"message_chunk","chunk":"Hello"}

data: {"type":"tool_call","tool_name":"search_documents"}

data: {"type":"complete_state","content":"..."}
```

**WebSocket 流实现:**
```python
# 已在 3.2.2 中定义
# 验证清单:
- ✅ 分块流式推送
- ✅ 工具调用事件
- ✅ 工具结果聚合
- ✅ 心跳机制
- ✅ 错误处理
- ✅ 并发连接管理
- ✅ 自动重连支持
```

**Agent 流式推理:**
```python
# AgentService.stream_message() 返回 AsyncIterator
# 实现细节:
- 使用 LangChain StreamingCallbackHandler
- 逐块收集 content
- 工具调用时发出 tool_call 事件
- 工具结果后发出 tool_result 事件
- 完成时发出 complete_state 事件
```

#### 单元测试
```python
# test_streaming.py
- test_sse_stream()
- test_websocket_stream()
- test_agent_streaming()
- test_stream_error_handling()
- test_concurrent_streams()
```

---

### 3.3.2 错误处理和恢复 (2 pts)

#### 全局异常处理器

**文件位置:**
- `src/exceptions.py`
- `src/main.py` (exception handlers)

**异常类型:**
```python
# 定义异常体系
class AppException(Exception):
    """基础应用异常"""
    error_code: str
    status_code: int
    detail: str

class ValidationException(AppException):
    status_code = 400
    error_code = "VALIDATION_ERROR"

class UnauthorizedException(AppException):
    status_code = 401
    error_code = "UNAUTHORIZED"

class ForbiddenException(AppException):
    status_code = 403
    error_code = "FORBIDDEN"

class NotFoundException(AppException):
    status_code = 404
    error_code = "NOT_FOUND"

class RateLimitException(AppException):
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"

class ConversationException(AppException):
    status_code = 400
    error_code = "CONVERSATION_ERROR"

class AgentException(AppException):
    status_code = 500
    error_code = "AGENT_ERROR"

class VectorSearchException(AppException):
    status_code = 500
    error_code = "VECTOR_SEARCH_ERROR"

class DatabaseException(AppException):
    status_code = 500
    error_code = "DATABASE_ERROR"
```

**异常处理器:**
```python
# src/main.py
@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "error_code": exc.error_code,
            "request_id": request.state.request_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # 记录未预期的异常
    await logger.aerror(
        "unhandled_exception",
        error=str(exc),
        error_type=type(exc).__name__,
        request_id=request.state.request_id
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "error_code": "INTERNAL_SERVER_ERROR",
            "request_id": request.state.request_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

**重试机制:**
```python
# 用于调用外部 API
async def call_with_retry(
    func: Callable,
    max_retries: int = 3,
    backoff_factor: float = 2,
    initial_delay_ms: int = 100
) -> Any:
    """带指数退避的重试"""
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as exc:
            if attempt == max_retries - 1:
                raise

            delay = (initial_delay_ms * (backoff_factor ** attempt)) / 1000
            await logger.ainfo(
                "retry_attempt",
                attempt=attempt + 1,
                delay_seconds=delay,
                error=str(exc)
            )
            await asyncio.sleep(delay)
```

**优雅降级:**
```python
# 当关键服务不可用时的处理
- 向量搜索超时 → 返回空 RAG 上下文
- 数据库超时 → 返回部分对话历史 (如果可用)
- LLM API 失败 → 返回错误消息 (让前端重试)
- 内容审核失败 → 跳过审核，继续处理
```

#### 单元测试
```python
# test_error_handling.py
- test_validation_exception()
- test_unauthorized_exception()
- test_not_found_exception()
- test_rate_limit_exception()
- test_agent_exception()
- test_database_exception()
- test_retry_logic()
- test_graceful_degradation()
- test_error_logging()
```

---

### 3.3.3 后端集成测试 (1 pt)

#### 测试场景

**场景 1: 完整对话流程**
```python
# test_integration_conversation_flow.py
1. 创建新对话
2. 上传文档到对话
3. 发送消息 (WebSocket)
4. 验证 Agent 调用了 search_documents
5. 验证响应包含相关信息
6. 验证对话历史已保存
7. 验证中间件都执行了
```

**场景 2: RAG 集成**
```python
# test_integration_rag_flow.py
1. 上传 PDF 文档
2. 等待后台向量化完成
3. 发送查询消息
4. 验证相关文档被检索到
5. 验证向量搜索性能 ≤200ms
6. 验证结果排名正确
```

**场景 3: 中间件堆栈**
```python
# test_integration_middleware_stack.py
1. 发送请求
2. 验证 request_id 被注入
3. 验证用户认证
4. 验证内容审核
5. 验证响应被结构化
6. 验证审计日志被记录
```

**场景 4: 错误恢复**
```python
# test_integration_error_recovery.py
1. 模拟向量搜索超时
2. 验证系统应用降级策略
3. 验证仍能返回部分结果
4. 验证错误被正确记录
```

**性能基准测试:**
```python
# test_performance_benchmarks.py
- 对话创建: <50ms
- 消息发送 (无工具): <500ms
- 消息发送 (含工具): <2000ms
- 向量搜索: ≤200ms P99
- 批量向量化 (100): ≤500ms
- 文档分块: <1s
- 中间件总开销: <300ms
```

#### 测试基础设施
```python
# tests/conftest.py
- 提供 async fixture
- 创建临时数据库
- 模拟外部 API (LLM, vector store)
- 清理测试数据

# tests/mock_data.py
- 示例对话、消息、文档
- 示例向量、embeddings

# tests/fixtures/
- mock_agent.py
- mock_rag.py
```

---

### 3.3.4 健康检查和优雅关闭 (3 pts)

#### 文件位置
- `src/infrastructure/health.py`
- `src/infrastructure/shutdown.py`

#### 健康检查实现

**GET /health 端点:**
```python
# 快速健康检查
Response (200):
{
  "status": "healthy" | "degraded" | "shutting_down",
  "timestamp": ISO8601
}

# 快速检查时间: <100ms
```

**GET /health/full 端点:**
```python
# 完整健康检查 (所有依赖)
Response (200):
{
  "status": "healthy" | "degraded",
  "timestamp": ISO8601,
  "checks": {
    "database": {
      "status": "healthy" | "unhealthy",
      "latency_ms": int,
      "error": Optional[str]
    },
    "vector_store": {
      "status": "healthy" | "unhealthy",
      "extension": "pgvector",
      "latency_ms": int
    },
    "redis": {
      "status": "healthy" | "unhealthy",
      "latency_ms": int
    },
    "llm_api": {
      "status": "healthy" | "unhealthy",
      "model": "claude-sonnet-4-5-20250929",
      "latency_ms": int
    }
  }
}

# 完整检查时间: <2000ms
```

**检查细节:**
```python
# Database check
- 执行 SELECT 1
- 测量延迟
- 验证连接池状态

# Vector Store check
- 查询 pgvector 扩展
- 验证 HNSW 索引存在
- 可选: 执行模型向量查询

# Redis check
- PING 操作
- 验证连接

# LLM API check
- 调用 API (max_tokens=10, quick=true)
- 验证认证和连接
- 可选: 验证模型列表
```

#### 优雅关闭实现

**信号处理:**
```python
# 捕获 SIGTERM 和 SIGINT
signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

# 关闭流程:
1. 收到 SIGTERM
2. 将健康状态设置为 "shutting_down"
3. 新连接返回 503
4. 等待活跃请求完成 (最多 30 秒)
5. 关闭资源 (DB, Redis, etc.)
6. 记录关闭完成
```

**活跃请求追踪:**
```python
class RequestTracker:
    def __init__(self):
        self.active_requests = 0
        self.lock = asyncio.Lock()

    async def track_request_start(self):
        async with self.lock:
            self.active_requests += 1

    async def track_request_end(self):
        async with self.lock:
            self.active_requests -= 1

    async def wait_for_completion(self, timeout_seconds=30):
        """等待所有请求完成"""
        start = time.time()
        while self.active_requests > 0:
            if time.time() - start > timeout_seconds:
                logger.warn(
                    "shutdown_timeout",
                    active_requests=self.active_requests
                )
                break
            await asyncio.sleep(0.1)
```

**资源清理:**
```python
async def cleanup_resources():
    """清理所有资源"""
    try:
        # 关闭数据库引擎
        if engine:
            await engine.dispose()

        # 关闭 Redis
        if redis_client:
            await redis_client.close()

        # 关闭其他连接
        # ...

        logger.info("all_resources_cleaned_up")
    except Exception as e:
        logger.error("resource_cleanup_error", error=str(e))
```

**集成到 FastAPI:**
```python
# src/main.py
@app.on_event("startup")
async def startup():
    logger.info("app_starting")
    # 初始化资源

@app.on_event("shutdown")
async def shutdown():
    logger.info("app_shutdown")
    # 关闭资源

# 或使用 lifespan context manager (FastAPI 0.93+)
@contextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("app_starting")
    yield
    # Shutdown
    logger.info("app_shutdown")

app = FastAPI(lifespan=lifespan)
```

#### 单元测试
```python
# test_health_checks.py
- test_health_endpoint()
- test_full_health_check()
- test_health_status_degraded()
- test_health_check_timeout()

# test_graceful_shutdown.py
- test_sigterm_handling()
- test_active_request_tracking()
- test_resource_cleanup()
- test_shutdown_timeout()
- test_shutdown_logging()
```

---

## 测试策略

### 测试覆盖目标
- 单元测试: >85% 行覆盖率
- 集成测试: 关键路径 100% 覆盖
- E2E 测试: 主要用户场景

### 测试框架
- 单元测试: pytest + pytest-asyncio
- Mock: unittest.mock + pytest fixtures
- 性能: pytest-benchmark
- 异步: pytest-asyncio

### 测试文件组织
```
tests/
├── unit/
│   ├── middleware/
│   │   ├── test_authentication.py
│   │   ├── test_memory_injection.py
│   │   ├── test_content_moderation.py
│   │   ├── test_response_structuring.py
│   │   └── test_audit_logging.py
│   ├── routes/
│   │   ├── test_conversation_routes.py
│   │   ├── test_message_routes.py
│   │   ├── test_document_routes.py
│   │   └── test_websocket_routes.py
│   └── error_handling/
│       ├── test_error_handlers.py
│       ├── test_retry_logic.py
│       └── test_graceful_degradation.py
├── integration/
│   ├── test_conversation_flow.py
│   ├── test_rag_flow.py
│   ├── test_middleware_stack.py
│   └── test_error_recovery.py
├── performance/
│   ├── test_benchmarks.py
│   └── test_load.py (可选)
└── fixtures/
    ├── conftest.py
    ├── mock_data.py
    └── mock_services.py
```

---

## 文档和交付物

### 需要编写的文档
1. **API 文档** (Swagger/OpenAPI)
   - 所有端点的完整 API spec
   - 请求/响应示例
   - 错误代码列表

2. **部署指南**
   - 环境配置
   - Docker 构建
   - 健康检查验证

3. **故障排查指南**
   - 常见问题
   - 日志分析
   - 性能调优

4. **中间件文档**
   - 执行顺序
   - 配置选项
   - 扩展指南

### 代码质量要求
- mypy --strict 通过
- black 格式化
- pylint score > 8.0
- docstring 完整

---

## 验收标准

### 功能完成
- [ ] 5层中间件全部实现
- [ ] 所有 API 端点实现
- [ ] WebSocket 流式处理完工
- [ ] 健康检查和优雅关闭
- [ ] 全局异常处理

### 质量指标
- [ ] 代码行覆盖率 ≥85%
- [ ] 所有单元测试通过
- [ ] 集成测试通过 (关键路径)
- [ ] 无 mypy --strict 错误
- [ ] 无 pylint 严重警告 (score > 8.0)

### 性能指标
- [ ] API 响应 <2000ms (含 RAG)
- [ ] 向量搜索 P99 ≤200ms
- [ ] 中间件开销 <300ms
- [ ] 消息发送端到端 <2000ms

### 文档完整性
- [ ] API 文档完整
- [ ] 部署指南完整
- [ ] 源代码注释完整 (docstring)
- [ ] 故障排查指南完整

### 安全检查
- [ ] SQL 注入防护通过
- [ ] XSS 防护通过
- [ ] 认证检查通过
- [ ] 权限检查通过

---

## 实现时间表

| 阶段 | 任务 | 天数 | 完成日期 |
|------|------|------|--------|
| 1 | Story 3.1.1 & 3.1.2 | 2-3 | Day 2-3 |
| 2 | Story 3.1.3 & 3.1.4 | 2 | Day 4-5 |
| 3 | Story 3.2 | 2 | Day 6-7 |
| 4 | Story 3.3 | 2 | Day 8-9 |
| 5 | 测试和文档 | 1-2 | Day 9-10 |

---

**版本**: 1.0.0
**最后更新**: 2025-11-17
**维护者**: LangChain Backend Architecture Team
