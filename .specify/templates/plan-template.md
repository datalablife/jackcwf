# Implementation Plan Template

## 项目宪法检查
- 此计划是否遵守所有 8 个核心原则? ✅
- 是否包含中间件架构设计? ✅
- 是否定义了数据库和向量存储设计? ✅
- 是否描述了类型安全的数据流? ✅
- 是否计划了异步和并发策略? ✅
- 代码组织是否遵守语义分层? ✅
- 是否包含部署和监控计划? ✅
- 是否包含测试和质量保证策略? ✅

---

## 设计概览

**功能**: [FEATURE_NAME]
**版本**: v[X.Y.Z]
**架构决策**: [简要说明关键设计选择]

---

## 架构设计

### 1. 系统整体架构

```
┌─────────────────────────────────────┐
│         Frontend (React 19)          │
│      + Tailark UI Components         │
└────────────────┬────────────────────┘
                 │ WebSocket/HTTP
┌────────────────▼────────────────────┐
│   FastAPI 应用 (异步优先)            │
│  ┌─────────────────────────────────┐│
│  │ 中间件层 (洋葱模型)              ││
│  │ 1. 认证                         ││
│  │ 2. 记忆注入                      ││
│  │ 3. 审核                         ││
│  │ 4. 响应结构化                    ││
│  │ 5. 审计日志                      ││
│  └────────────┬────────────────────┘│
│               │                      │
│  ┌────────────▼────────────────────┐│
│  │ LangChain v1.0 Agent            ││
│  │ + Middleware System             ││
│  │ + LangGraph (持久化/流)          ││
│  └────────────┬────────────────────┘│
│               │                      │
│  ┌────────────▼────────────────────┐│
│  │ 服务层 (业务逻辑)                ││
│  │ - agent_service                 ││
│  │ - embedding_service             ││
│  │ - conversation_service          ││
│  │ - rag_service                   ││
│  └────────────┬────────────────────┘│
│               │                      │
│  ┌────────────▼────────────────────┐│
│  │ 存储库层 (数据访问)              ││
│  │ - vector_repository             ││
│  │ - conversation_repository       ││
│  │ - document_repository           ││
│  └────────────┬────────────────────┘│
└────────────────┼────────────────────┘
                 │
    ┌────────────┼────────────────┐
    │            │                │
┌───▼───┐  ┌────▼────┐    ┌─────▼───┐
│ PgSQL │  │  Redis  │    │ LLM API │
│+pgvec │  │(缓存)   │    │(OpenAI) │
└───────┘  └─────────┘    └─────────┘
```

### 2. 中间件架构 (洋葱模型)

```python
# 执行顺序 (从外到内)
middleware_stack = [
    RequestValidationMiddleware,      # 请求验证
    MemoryInjectionMiddleware,        # 记忆上下文注入
    ContentModerationMiddleware,      # 内容审核
    ResponseStructuringMiddleware,    # 响应结构化
    AuditLoggingMiddleware,           # 审计日志
    # -> 业务逻辑处理 ->
]
```

### 3. 数据流设计

```
用户输入
  │
  ▼
[认证中间件] ──✅──▶ 提取 user_id、session_id
  │
  ▼
[记忆注入中间件] ──✅──▶ 向量数据库查询相关上下文
  │
  ▼
[审核中间件] ──✅──▶ 检查提示词安全性
  │
  ▼
LangChain Agent
  │
  ├──▶ 选择工具
  │    ├──▶ RAG 工具 (向量搜索)
  │    ├──▶ 数据库查询工具
  │    └──▶ 外部 API 工具
  │
  └──▶ 生成响应
  │
  ▼
[响应结构化] ──✅──▶ JSON 格式化
  │
  ▼
[审计日志] ──✅──▶ 记录交互历史
  │
  ▼
发送给用户
```

---

## 数据库设计 (PostgreSQL)

### 核心表结构

#### 1. documents 表 (文档存储)
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR NOT NULL,
    content TEXT NOT NULL,
    source VARCHAR NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,

    INDEX idx_source_created (source, created_at),
    INDEX idx_created (created_at DESC)
);
```

#### 2. embeddings 表 (向量存储)
```sql
CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id),
    chunk_text TEXT NOT NULL,
    embedding vector(1536) NOT NULL,  -- OpenAI Ada
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,

    INDEX idx_embedding USING hnsw (embedding vector_cosine_ops)
);
```

#### 3. conversations 表 (对话历史)
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR NOT NULL,
    title VARCHAR,
    summary TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,

    INDEX idx_user_created (user_id, created_at DESC)
);
```

#### 4. messages 表 (消息记录)
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    role VARCHAR(10) CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    usage JSONB,  -- token 使用统计
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_conversation_created (conversation_id, created_at)
);
```

### 分区策略
```sql
-- 按月分区 embeddings 表 (>1M 记录时)
CREATE TABLE embeddings_2025_11 PARTITION OF embeddings
  FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

CREATE TABLE embeddings_2025_12 PARTITION OF embeddings
  FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');
```

---

## 后端实现细节

### 1. 项目结构
```
backend/
├── src/
│   ├── api/
│   │   └── v1/
│   │       ├── conversations.py
│   │       ├── embeddings.py
│   │       ├── agents.py
│   │       └── documents.py
│   ├── services/
│   │   ├── agent_service.py
│   │   ├── embedding_service.py
│   │   ├── conversation_service.py
│   │   └── rag_service.py
│   ├── repositories/
│   │   ├── vector_repository.py
│   │   ├── conversation_repository.py
│   │   └── document_repository.py
│   ├── models/
│   │   ├── domain.py
│   │   ├── dto.py
│   │   └── orm.py
│   ├── infrastructure/
│   │   ├── database.py
│   │   ├── middleware.py
│   │   ├── config.py
│   │   ├── logger.py
│   │   └── monitoring.py
│   └── main.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
└── pyproject.toml
```

### 2. 关键模块设计

#### embedding_service.py
```python
from typing import List
from langchain_openai import OpenAIEmbeddings

class EmbeddingService:
    """向量化服务"""

    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    async def embed_text(self, text: str) -> List[float]:
        """异步生成向量"""
        # 异步调用，维度 = 1536
        pass

    async def semantic_search(
        self,
        query: str,
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[dict]:
        """向量相似性搜索 (≤ 200ms P99)"""
        pass
```

#### agent_service.py
```python
from langchain.agents import create_agent

class AgentService:
    """LangChain v1.0 Agent 服务"""

    def __init__(self, llm, tools, middleware):
        self.agent = create_agent(
            llm=llm,
            tools=tools,
            middleware=middleware  # 中间件系统
        )

    async def run_agent(
        self,
        input_text: str,
        conversation_id: str
    ) -> str:
        """运行 Agent (异步)"""
        # 使用 LangGraph 持久化对话
        # 支持流式响应
        pass
```

### 3. 中间件实现

```python
from typing import Callable, Any

class MemoryInjectionMiddleware:
    """记忆注入中间件"""

    async def __call__(self, request: Request, call_next: Callable) -> Any:
        # 1. 提取用户 ID 和对话 ID
        user_id = request.headers.get("X-User-ID")
        conversation_id = request.headers.get("X-Conversation-ID")

        # 2. 从向量数据库检索相关上下文
        context = await self.vector_repo.search(
            query=request.json().get("message"),
            user_id=user_id,
            limit=5
        )

        # 3. 注入到请求上下文
        request.state.memory_context = context

        # 4. 继续处理
        response = await call_next(request)
        return response
```

---

## 前端实现细节

### 1. 项目结构
```
frontend/
├── src/
│   ├── components/
│   │   ├── ChatInterface.tsx
│   │   ├── DocumentUpload.tsx
│   │   └── SearchResults.tsx
│   ├── hooks/
│   │   ├── useChat.ts
│   │   ├── useDocuments.ts
│   │   └── useSearch.ts
│   ├── stores/
│   │   ├── chatStore.ts
│   │   └── documentStore.ts
│   ├── pages/
│   │   ├── ChatPage.tsx
│   │   ├── UploadPage.tsx
│   │   └── SearchPage.tsx
│   ├── services/
│   │   ├── api.ts
│   │   └── websocket.ts
│   └── App.tsx
└── package.json
```

### 2. Tailark UI 集成

```typescript
// 使用 Tailark Hero 组件
import { HeroSection } from "@/components/ui/hero-section"

export const LandingPage: React.FC = () => {
  return (
    <HeroSection
      title="AI-Powered Document Search"
      subtitle="Ask questions about your documents using LangChain v1.0"
      cta={{ label: "Get Started", href: "/chat" }}
    />
  )
}
```

### 3. 实时通信 (WebSocket)

```typescript
// 使用 Socket.IO 进行实时消息流
import io from "socket.io-client"

const socket = io("ws://localhost:8000", {
  auth: { token: JWT_TOKEN }
})

socket.on("agent:response_chunk", (chunk: string) => {
  // 流式输出响应
  setChatMessages(prev => [...prev, chunk])
})
```

---

## 监控和可观测性设计

### 1. 关键指标

| 指标 | 来源 | 告警阈值 | 仪表板 |
|------|------|---------|--------|
| API 响应时间 P99 | FastAPI logs | > 1000ms | Grafana |
| 向量搜索延迟 P99 | Database logs | > 200ms | Grafana |
| 错误率 | Application logs | > 1% | Datadog |
| 缓存命中率 | Redis stats | < 70% | Prometheus |
| 向量索引大小 | PostgreSQL | > 100GB | Grafana |

### 2. 日志示例

```json
{
  "timestamp": "2025-11-16T10:30:45.123Z",
  "level": "INFO",
  "module": "services.agent_service",
  "function": "run_agent",
  "message": "Agent execution completed",
  "context": {
    "request_id": "req_abc123",
    "user_id": "user_123",
    "conversation_id": "conv_456",
    "duration_ms": 245,
    "tokens_used": 1250,
    "status": "success"
  }
}
```

### 3. 告警规则

```yaml
groups:
  - name: api_alerts
    rules:
      - alert: HighResponseTime
        expr: histogram_quantile(0.99, http_request_duration_seconds) > 1
        for: 5m
        annotations:
          summary: "API response time P99 > 1s"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
        for: 5m
        annotations:
          summary: "Error rate > 1%"
```

---

## 测试策略

### 1. 单元测试
```python
# tests/unit/services/test_embedding_service.py
@pytest.mark.asyncio
async def test_embed_text():
    service = EmbeddingService()
    result = await service.embed_text("Hello world")
    assert len(result) == 1536
    assert all(isinstance(x, float) for x in result)
```

### 2. 集成测试
```python
# tests/integration/api/test_chat_endpoint.py
@pytest.mark.asyncio
async def test_chat_endpoint(client: AsyncClient):
    response = await client.post(
        "/api/v1/conversations/chat",
        json={"message": "What is LangChain?"}
    )
    assert response.status_code == 200
    assert "response" in response.json()
```

### 3. E2E 测试 (Playwright)
```typescript
// frontend/tests/e2e/chat.spec.ts
test("user can send a message and receive response", async ({ page }) => {
  await page.goto("/chat")
  await page.fill("[data-testid=message-input]", "Hello")
  await page.click("[data-testid=send-button]")
  await expect(page.locator("[data-testid=agent-response]")).toBeVisible()
})
```

---

## 部署计划

### 1. 环境配置

```bash
# 开发环境
ENVIRONMENT=development
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql+asyncpg://localhost:5432/langchain_dev

# 测试环境
ENVIRONMENT=staging
LOG_LEVEL=INFO
DATABASE_URL=postgresql+asyncpg://pg-staging:5432/langchain_test

# 生产环境
ENVIRONMENT=production
LOG_LEVEL=WARNING
DATABASE_URL=postgresql+asyncpg://pg-prod:5432/langchain_prod
```

### 2. Coolify 部署步骤

1. 推送代码到 GitHub main 分支
2. CI/CD 自动触发 (GitHub Actions)
3. 构建 Docker 镜像 (python:3.14-slim)
4. 运行自动化测试 (单元、集成)
5. 部署到 Coolify (蓝绿部署)
6. 健康检查验证
7. 监控告警配置

### 3. 健康检查 (≤ 500ms)

```python
@app.get("/health")
async def health_check() -> dict:
    return {
        "status": "healthy",
        "database": await check_database(),
        "redis": await check_redis(),
        "llm_api": await check_llm_api(),
        "vector_store": await check_vector_store()
    }
```

---

## 性能目标

| 操作 | 当前 | 目标 | 时间表 |
|------|------|------|--------|
| API 响应时间 P99 | TBD | ≤ 500ms | Sprint 1 |
| 向量搜索延迟 P99 | TBD | ≤ 200ms | Sprint 1 |
| 吞吐量 | TBD | ≥ 100 req/s | Sprint 2 |
| 错误率 | TBD | ≤ 1% | Sprint 1 |

---

## 风险和缓解策略

| 风险 | 概率 | 影响 | 缓解策略 |
|------|------|------|---------|
| LLM API 限流 | 高 | 高 | 实现请求队列 + 重试机制 |
| 向量搜索性能下降 | 中 | 高 | 索引优化 + 分区策略 |
| 数据库连接耗尽 | 低 | 高 | 连接池管理 + 监控告警 |

---

## 时间表

- **第 1 周**: 环境搭建 + 数据库设计
- **第 2-3 周**: 后端服务开发 (Agent、嵌入、RAG)
- **第 4 周**: 前端开发 + 集成
- **第 5 周**: 测试 + 优化
- **第 6 周**: 部署到生产

---

## 参考资源

- LangChain v1.0: https://docs.langchain.com/oss/python/releases/langchain-v1
- PostgreSQL pgvector: https://github.com/pgvector/pgvector
- Tailark UI: https://tailark.com
- FastAPI: https://fastapi.tiangolo.com
- SQLAlchemy Async: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
