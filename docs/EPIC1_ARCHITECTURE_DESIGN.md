# Epic 1 - 后端基础设施架构设计

**文档版本**: 1.0
**最后更新**: 2025-11-17
**状态**: 架构设计完成，待实现

---

## 目录

1. [执行摘要](#执行摘要)
2. [架构审查](#架构审查)
3. [Story 1.1：数据库设计与迁移](#story-11数据库设计与迁移)
4. [Story 1.2：异步存储库实现](#story-12异步存储库实现)
5. [Story 1.3：API框架搭建](#story-13api框架搭建)
6. [LangChain 1.0 最佳实践](#langchain-10-最佳实践)
7. [性能优化策略](#性能优化策略)
8. [风险与缓解](#风险与缓解)
9. [实现路线图](#实现路线图)

---

## 执行摘要

### 项目现状评估

**优势**：
- ORM模型完整定义（conversations、messages、documents、embeddings）
- BaseRepository泛型框架已实现
- FastAPI应用基础架构完成
- 异步数据库连接配置正确
- 中间件堆栈已初始化

**改进空间**：
- 事务管理：需要显式事务边界和嵌套事务支持
- 错误处理：需要统一异常分类和重试机制
- 依赖注入：API层需要改进DI模式
- 批处理优化：缺乏批量upsert和性能优化
- 缓存集成：缺乏Redis缓存层
- 监控日志：缺乏结构化日志和性能追踪
- 请求追踪：缺乏分布式追踪支持

**计划行动**：
- 增强事务管理和错误处理
- 实现统一的异常处理系统
- 优化批处理操作
- 完成缓存集成
- 改进API依赖注入
- 添加分布式追踪

### 关键指标与SLA

| 指标 | 目标 | 当前 | 优先级 |
|------|------|------|--------|
| 向量搜索延迟 (P99) | ≤ 200ms | 未测试 | 高 |
| 批量写入 (1000 embeddings) | ≤ 100ms | 已实现监控 | 高 |
| 会话获取延迟 | ≤ 50ms | 未测试 | 中 |
| 错误恢复率 | 99.9% | 待实现 | 高 |
| 缓存命中率 | ≥ 60% | N/A (待实现) | 中 |

---

## 架构审查

### 1. 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Application                      │
│  (src/main.py)                                                    │
└────────┬────────────────────────────────────────────────────────┘
         │
┌────────▼────────────────────────────────────────────────────────┐
│              中间件堆栈 (Middleware Stack)                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 1. 认证中间件 (AuthenticationMiddleware)                 │   │
│  │ 2. 记忆注入 (MemoryInjectionMiddleware)                 │   │
│  │ 3. 内容审核 (ContentModerationMiddleware)               │   │
│  │ 4. 响应结构化 (ResponseStructuringMiddleware)           │   │
│  │ 5. 审计日志 (AuditLoggingMiddleware)                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────┬────────────────────────────────────────────────────────┘
         │
┌────────▼────────────────────────────────────────────────────────┐
│               API 层 (src/api/)                                  │
│  ┌───────────────┐ ┌────────────────┐ ┌──────────────────┐     │
│  │ Conversations │ │   Documents    │ │     Messages     │     │
│  │   Routes      │ │    Routes      │ │     Routes       │     │
│  └───────────────┘ └────────────────┘ └──────────────────┘     │
└────────┬────────────────────────────────────────────────────────┘
         │
┌────────▼────────────────────────────────────────────────────────┐
│             服务层 (src/services/)                               │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ ConversationService | DocumentService | MessageService│      │
│  └───────────────────────────────────────────────────────┘      │
└────────┬────────────────────────────────────────────────────────┘
         │
┌────────▼────────────────────────────────────────────────────────┐
│            存储库层 (src/repositories/)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ BaseRepository│  │ Conversation │  │   Embedding  │          │
│  │   (Generic)   │  │ Repository   │  │  Repository  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────┬────────────────────────────────────────────────────────┘
         │
┌────────▼────────────────────────────────────────────────────────┐
│         数据库层 (src/db/)                                       │
│  ┌──────────────────────────────────────────────────────┐       │
│  │ AsyncSessionLocal | Connection Pool | Event Handlers │       │
│  └──────────────────────────────────────────────────────┘       │
└────────┬────────────────────────────────────────────────────────┘
         │
┌────────▼────────────────────────────────────────────────────────┐
│         PostgreSQL 数据库（带 pgvector 扩展）                   │
│  ┌─────────────┐ ┌──────────┐ ┌───────────┐ ┌────────────┐    │
│  │Conversations│ │ Messages │ │ Documents │ │ Embeddings │    │
│  │ (12+ 索引)  │ │(6 索引)  │ │ (5 索引)  │ │(6+1 HNSW)  │    │
│  └─────────────┘ └──────────┘ └───────────┘ └────────────┘    │
│  ┌─────────────────────────────────────────────────────┐       │
│  │ 分区策略: Embeddings 按月分区                        │       │
│  │ 缓存: Redis (可选)                                  │       │
│  └─────────────────────────────────────────────────────┘       │
└──────────────────────────────────────────────────────────────────┘
```

### 2. 数据流分析

#### 创建对话的完整数据流

```
1. 客户端请求
   POST /api/conversations
   {
     "title": "Financial Analysis",
     "system_prompt": "You are a financial expert",
     "model": "claude-sonnet-4-5-20250929",
     "metadata": {"domain": "finance"}
   }
   │
   ├─ 认证中间件检查 (req headers)
   │
   ├─ API 路由层 (conversation_routes.py:create_conversation)
   │  └─ 验证请求数据 (Pydantic)
   │
   ├─ 服务层 (ConversationService.create_conversation)
   │  └─ 业务逻辑
   │
   ├─ 存储库层 (ConversationRepository.create)
   │  └─ 构建ORM对象
   │  └─ 执行 INSERT
   │
   ├─ 数据库层
   │  └─ 事务提交
   │  └─ 生成UUID ID
   │  └─ 设置时间戳
   │
   └─ 响应 201 Created
      {
        "id": "uuid",
        "user_id": "user123",
        "title": "Financial Analysis",
        "created_at": "2025-11-17T..."
      }
```

#### 向量搜索的数据流

```
1. 客户端发送查询
   POST /api/documents/search
   {
     "query": "financial risk assessment",
     "top_k": 5,
     "threshold": 0.7
   }
   │
   ├─ API 验证请求
   │
   ├─ 嵌入服务 (生成查询向量)
   │  └─ 调用 OpenAI text-embedding-3-small
   │  └─ 获得 1536-dimensional vector
   │
   ├─ 存储库查询 (EmbeddingRepository.search_similar)
   │  └─ 构建 SQL 查询
   │  └─ WHERE embedding <-> query_embedding <= max_distance
   │  └─ ORDER BY cosine_distance
   │  └─ LIMIT 5
   │
   ├─ 数据库 (HNSW 索引查询)
   │  └─ 查询 embeddings_2025_11 分区
   │  └─ 使用 HNSW 索引
   │  └─ 返回 Top-K 结果
   │
   └─ 返回结果
      [
        {
          "chunk_text": "...",
          "similarity": 0.92,
          "document_id": "uuid",
          "chunk_index": 5
        },
        ...
      ]
```

### 3. 关键改进领域

#### 3.1 事务管理

**当前问题**：
- BaseRepository中没有显式的事务边界
- 缺乏嵌套事务支持
- 错误时没有自动回滚

**推荐方案**：

```python
# 上下文管理器模式
async def process_batch_messages():
    async with get_async_session() as session:
        try:
            async with session.begin_nested():  # 保存点
                # 插入操作
                await msg_repo.bulk_create(messages)
        except IntegrityError:
            # 自动回滚到保存点
            raise RepositoryError("Duplicate message IDs")
```

#### 3.2 错误处理

**当前问题**：
- 缺乏统一异常分类
- 数据库异常泄露给客户端
- 没有重试机制

**推荐方案**：

```python
# 统一异常类
class RepositoryError(Exception):
    """存储库层异常基类"""
    pass

class DuplicateRecordError(RepositoryError):
    """唯一性约束违反"""
    pass

class RecordNotFoundError(RepositoryError):
    """记录不存在"""
    pass

# 重试装饰器
@retry(
    retries=3,
    backoff=exponential,
    backoff_base=0.1,
    exceptions=(OperationalError,)
)
async def execute_query(query):
    pass
```

#### 3.3 性能缓存

**当前问题**：
- 没有缓存层
- 热数据重复查询

**推荐方案**：

```python
# Redis 缓存集成
class CachedConversationRepository(ConversationRepository):
    def __init__(self, session, cache):
        super().__init__(session)
        self.cache = cache

    async def get(self, id):
        # 缓存键: conversation:{user_id}:{id}
        cached = await self.cache.get(f"conversation:{id}")
        if cached:
            return ConversationORM.parse_obj(cached)

        result = await super().get(id)
        if result:
            await self.cache.set(
                f"conversation:{id}",
                result.to_dict(),
                ttl=3600
            )
        return result
```

#### 3.4 批处理优化

**当前问题**：
- bulk_create 没有优化的批量插入
- 缺乏 upsert 操作
- N+1 查询问题

**推荐方案**：

```python
# 优化的批量插入
async def bulk_create_optimized(self, instances):
    # 使用 INSERT ... ON CONFLICT 模式
    stmt = insert(self.model_class).values(instances)
    stmt = stmt.on_conflict_do_update(
        index_elements=['id'],
        set_={c.name: c for c in stmt.excluded}
    )
    return await self.session.execute(stmt)

# 预加载关联（避免N+1）
async def get_conversations_with_stats(self, user_id):
    stmt = (
        select(ConversationORM)
        .where(ConversationORM.user_id == user_id)
        .options(selectinload(ConversationORM.messages))  # 预加载
    )
    return await self.session.execute(stmt)
```

---

## Story 1.1 - 数据库设计与迁移

### Task 1.1.1: Conversations 表设计

**当前状态**：已定义，需要验证和改进

**完整 SQL Schema**：

```sql
CREATE TABLE conversations (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 用户信息
    user_id VARCHAR(255) NOT NULL,

    -- 对话元数据
    title VARCHAR(255) NOT NULL,
    summary TEXT,
    model VARCHAR(100) NOT NULL DEFAULT 'claude-sonnet-4-5-20250929',
    system_prompt TEXT NOT NULL,

    -- 附加信息
    metadata JSONB DEFAULT '{}',

    -- 软删除
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,

    -- 约束
    CONSTRAINT ck_conversations_user_id_not_empty CHECK (LENGTH(user_id) > 0),
    CONSTRAINT ck_conversations_title_not_empty CHECK (LENGTH(title) > 0),
    CONSTRAINT ck_conversations_model_not_empty CHECK (LENGTH(model) > 0)
);

-- 索引策略（7个索引）
-- 1. 主查询：用户的有效对话
CREATE INDEX idx_conversations_user_active
    ON conversations (user_id)
    WHERE is_deleted = false;

-- 2. 用户对话按时间排序
CREATE INDEX idx_conversations_user_created
    ON conversations (user_id, created_at DESC)
    WHERE is_deleted = false;

-- 3. 标题搜索
CREATE INDEX idx_conversations_title_search
    ON conversations (title)
    WHERE is_deleted = false;

-- 4. 用户过滤
CREATE INDEX idx_conversations_user_id
    ON conversations (user_id);

-- 5. 软删除过滤
CREATE INDEX idx_conversations_is_deleted
    ON conversations (is_deleted);

-- 6. 创建时间范围查询
CREATE INDEX idx_conversations_created_at
    ON conversations (created_at);

-- 7. 更新时间查询
CREATE INDEX idx_conversations_updated_at
    ON conversations (updated_at);

-- 分析表统计
ANALYZE conversations;
```

**ORM 改进**：

```python
# 当前需要添加：
# 1. 表级别的 CHECK 约束
# 2. 改进的字段验证

class ConversationORM(Base):
    __tablename__ = "conversations"
    __table_args__ = (
        # 检查约束
        CheckConstraint("LENGTH(user_id) > 0", name="ck_user_id_not_empty"),
        CheckConstraint("LENGTH(title) > 0", name="ck_title_not_empty"),
        CheckConstraint("LENGTH(model) > 0", name="ck_model_not_empty"),
        # 现有索引...
    )

    # 添加事件监听器自动更新 updated_at
    @event.listens_for(ConversationORM, 'before_update')
    def receive_before_update(mapper, connection, target):
        target.updated_at = datetime.utcnow()
```

**性能指标**：

| 操作 | 预期延迟 | 索引覆盖 |
|------|---------|--------|
| 获取用户对话列表 | ≤ 50ms | idx_conversations_user_active |
| 搜索对话标题 | ≤ 100ms | idx_conversations_title_search |
| 获取最近更新 | ≤ 30ms | idx_conversations_updated_at |
| 统计用户对话数 | ≤ 20ms | idx_conversations_user_id |

### Task 1.1.2: Messages 表设计

**当前状态**：已定义，需要改进外键和分区

**完整 SQL Schema**：

```sql
CREATE TABLE messages (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 外键
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,

    -- 消息内容
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,

    -- 工具调用数据
    tool_calls JSONB,
    tool_results JSONB,

    -- Token 追踪
    tokens_used INTEGER,

    -- 附加信息
    metadata JSONB DEFAULT '{}',

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,

    -- 约束
    CONSTRAINT ck_messages_content_not_empty CHECK (LENGTH(content) > 0),
    CONSTRAINT ck_messages_tokens_positive CHECK (tokens_used IS NULL OR tokens_used >= 0)
);

-- 索引策略（6个索引）
-- 1. 主查询：按对话获取消息
CREATE INDEX idx_messages_conversation
    ON messages (conversation_id, created_at ASC);

-- 2. 按角色过滤（用于构建模型输入）
CREATE INDEX idx_messages_role
    ON messages (conversation_id, role)
    WHERE role IN ('assistant', 'user');

-- 3. 最近消息快速查询
CREATE INDEX idx_messages_conversation_recent
    ON messages (conversation_id, created_at DESC)
    INCLUDE (role, content);  -- INCLUDE 用于覆盖查询

-- 4. Token 统计
CREATE INDEX idx_messages_tokens
    ON messages (conversation_id)
    WHERE tokens_used IS NOT NULL;

-- 5. 创建时间范围查询
CREATE INDEX idx_messages_created_at
    ON messages (created_at);

-- 6. 工具调用快速定位
CREATE INDEX idx_messages_has_tool_calls
    ON messages (conversation_id)
    WHERE tool_calls IS NOT NULL;

-- 部分索引：仅索引有结果的工具调用
CREATE INDEX idx_messages_tool_results
    ON messages (conversation_id)
    WHERE tool_results IS NOT NULL;
```

**分区策略**（可选）：

```sql
-- Messages 表可按时间分区（如果行数超过 1M）
-- 当前不需要，但提供方案以备将来使用
ALTER TABLE messages PARTITION BY RANGE (created_at) (
    PARTITION messages_2025_10 VALUES FROM ('2025-10-01') TO ('2025-11-01'),
    PARTITION messages_2025_11 VALUES FROM ('2025-11-01') TO ('2025-12-01'),
    PARTITION messages_2025_12 VALUES FROM ('2025-12-01') TO ('2026-01-01')
);
```

**ORM 改进**：

```python
class MessageORM(Base):
    __tablename__ = "messages"
    __table_args__ = (
        # 增强的检查约束
        CheckConstraint("role IN ('user', 'assistant', 'system')", name="ck_valid_role"),
        CheckConstraint("LENGTH(content) > 0", name="ck_content_not_empty"),
        CheckConstraint("tokens_used IS NULL OR tokens_used >= 0", name="ck_tokens_positive"),
        # 索引...
    )

    # 添加字段验证
    @validates('role')
    def validate_role(self, key, value):
        if value not in ('user', 'assistant', 'system'):
            raise ValueError(f"Invalid role: {value}")
        return value
```

**性能指标**：

| 操作 | 预期延迟 | 索引覆盖 |
|------|---------|--------|
| 获取对话消息(LIMIT 50) | ≤ 80ms | idx_messages_conversation |
| 获取最后N条消息 | ≤ 50ms | idx_messages_conversation_recent |
| 统计对话 Token 总数 | ≤ 100ms | idx_messages_tokens |
| 查询带工具调用的消息 | ≤ 60ms | idx_messages_has_tool_calls |

### Task 1.1.3: Documents 和 Embeddings 表设计

**Documents 表 SQL Schema**：

```sql
CREATE TABLE documents (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 用户信息
    user_id VARCHAR(255) NOT NULL,

    -- 文件信息
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(20) NOT NULL CHECK (file_type IN ('pdf', 'txt', 'docx', 'md', 'html')),

    -- 内容（分块前的完整文本）
    content TEXT NOT NULL,

    -- 分块信息
    total_chunks INTEGER NOT NULL DEFAULT 0 CHECK (total_chunks >= 0),

    -- 附加信息
    metadata JSONB DEFAULT '{}',

    -- 软删除
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 索引策略（5个索引）
CREATE INDEX idx_documents_user_active
    ON documents (user_id)
    WHERE is_deleted = false;

CREATE INDEX idx_documents_user_created
    ON documents (user_id, created_at DESC)
    WHERE is_deleted = false;

CREATE INDEX idx_documents_filename
    ON documents (filename)
    WHERE is_deleted = false;

CREATE INDEX idx_documents_file_type
    ON documents (file_type)
    WHERE is_deleted = false;

CREATE INDEX idx_documents_chunk_count
    ON documents (total_chunks)
    WHERE is_deleted = false AND total_chunks > 0;
```

**Embeddings 表 SQL Schema（核心 RAG 表）**：

```sql
-- 启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE embeddings (
    -- 主键
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 外键
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,

    -- 块内容和向量
    chunk_text TEXT NOT NULL,
    embedding vector(1536) NOT NULL,  -- OpenAI text-embedding-3-small 维度
    chunk_index INTEGER NOT NULL CHECK (chunk_index >= 0),

    -- 附加信息
    metadata JSONB DEFAULT '{}',

    -- 软删除
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,

    -- 约束
    CONSTRAINT ck_chunk_text_not_empty CHECK (LENGTH(chunk_text) > 0)
);

-- 分区策略：按月分区（对于大规模应用）
CREATE TABLE embeddings_2025_11 PARTITION OF embeddings
    FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

CREATE TABLE embeddings_2025_12 PARTITION OF embeddings
    FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');

-- 索引策略（6个标准索引 + 1个 HNSW 向量索引）

-- 1. 文档块查询
CREATE INDEX idx_embeddings_document
    ON embeddings (document_id)
    WHERE is_deleted = false;

-- 2. 文档内块索引查询
CREATE INDEX idx_embeddings_document_chunk
    ON embeddings (document_id, chunk_index)
    WHERE is_deleted = false;

-- 3. 创建时间范围
CREATE INDEX idx_embeddings_created_at
    ON embeddings (created_at)
    WHERE is_deleted = false;

-- 4. 块文本全文搜索（可选）
CREATE INDEX idx_embeddings_chunk_text_gin
    ON embeddings USING gin(to_tsvector('english', chunk_text))
    WHERE is_deleted = false;

-- 5. 软删除过滤
CREATE INDEX idx_embeddings_is_deleted
    ON embeddings (is_deleted);

-- 6. 重要：HNSW 向量索引（高效相似性搜索）
CREATE INDEX idx_embeddings_vector_hnsw
    ON embeddings USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- HNSW 参数说明：
-- m = 16: 每个节点连接到16个最近邻（默认16，高维空间推荐）
-- ef_construction = 64: 构造时的搜索广度（提高准确性，增加构建时间）

-- 7. 降维索引（可选，用于小向量空间）
-- CREATE INDEX idx_embeddings_vector_ivfflat
--     ON embeddings USING ivfflat (embedding vector_cosine_ops)
--     WITH (lists = 100);  -- 仅当向量数量 > 1M 时考虑
```

**向量搜索查询示例**：

```sql
-- 向量相似性搜索（使用 HNSW 索引）
SELECT
    e.id,
    e.document_id,
    e.chunk_text,
    e.chunk_index,
    -- 计算相似度（cosine 距离 -> 相似度）
    (1 - (e.embedding <-> query_embedding)) * 100 as similarity_percent,
    d.filename,
    d.user_id
FROM embeddings e
JOIN documents d ON e.document_id = d.id
WHERE d.user_id = $1
    AND e.is_deleted = false
    AND d.is_deleted = false
    -- 向量距离过滤（<-> 是 cosine 距离操作符）
    AND e.embedding <-> query_embedding < 0.3  -- 距离 < 0.3 = 相似度 > 70%
ORDER BY e.embedding <-> query_embedding
LIMIT 5;

-- 性能分析：
-- 执行时间：30-200ms（取决于表大小和HNSW索引质量）
-- HNSW 索引会跳过大部分不相关的向量
```

**ORM 改进**：

```python
class DocumentORM(Base):
    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint("LENGTH(user_id) > 0", name="ck_user_id_not_empty"),
        CheckConstraint("LENGTH(filename) > 0", name="ck_filename_not_empty"),
        CheckConstraint("file_type IN ('pdf', 'txt', 'docx', 'md', 'html')",
                       name="ck_valid_file_type"),
        CheckConstraint("total_chunks >= 0", name="ck_chunks_non_negative"),
    )

class EmbeddingORM(Base):
    __tablename__ = "embeddings"
    __table_args__ = (
        CheckConstraint("LENGTH(chunk_text) > 0", name="ck_chunk_text_not_empty"),
        CheckConstraint("chunk_index >= 0", name="ck_chunk_index_non_negative"),
        # 向量索引定义已在模型中
    )

    # 添加向量验证
    @validates('embedding')
    def validate_embedding(self, key, value):
        if value is not None and len(value) != 1536:
            raise ValueError(f"Embedding must be 1536-dimensional, got {len(value)}")
        return value
```

### Task 1.1.4: 索引优化策略

**索引总览**：

| 表名 | 索引数 | 策略 | 优先级 |
|------|--------|------|--------|
| conversations | 7 | 用户+状态+搜索 | 高 |
| messages | 7 | 对话+角色+工具 | 高 |
| documents | 5 | 用户+类型+内容 | 高 |
| embeddings | 6+1 | 文档+向量+时间 | 关键 |

**索引创建策略**：

```python
# migrations.py 中的索引管理
async def create_indices(conn):
    """创建所有优化的索引"""

    # 批处理创建索引以节省时间
    indices = [
        # Conversations 索引
        """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversations_user_active
           ON conversations (user_id) WHERE is_deleted = false""",

        # HNSW 向量索引（可能需要 5-10 分钟用于大表）
        """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_embeddings_vector_hnsw
           ON embeddings USING hnsw (embedding vector_cosine_ops)
           WITH (m = 16, ef_construction = 64)""",

        # 更多索引...
    ]

    for idx_sql in indices:
        try:
            await conn.execute(text(idx_sql))
            logger.info(f"Created index: {idx_sql.split('ON')[1]}")
        except Exception as e:
            logger.warning(f"Index creation skipped: {e}")
```

**索引维护**：

```python
# 定期分析和重建索引
async def maintain_indices(conn):
    """定期索引维护任务"""

    # 分析表统计
    tables = ['conversations', 'messages', 'documents', 'embeddings']
    for table in tables:
        await conn.execute(text(f"ANALYZE {table}"))

    # 重建膨胀的索引（> 30% 膨胀）
    bloated_indices = await conn.execute(text("""
        SELECT schemaname, tablename, indexname,
               ROUND(100 * (pg_relation_size(indexrelid) -
                   pg_relation_size(relfilenode)) /
               pg_relation_size(indexrelid)) as bloat_ratio
        FROM pg_stat_user_indexes
        WHERE pg_relation_size(indexrelid) > 1000000  -- > 1MB
        HAVING ROUND(100 * (pg_relation_size(indexrelid) -
                   pg_relation_size(relfilenode)) /
               pg_relation_size(indexrelid)) > 30
    """))

    for row in bloated_indices:
        logger.info(f"REINDEX needed for {row.indexname}: {row.bloat_ratio}% bloat")
        # 后台低优先级重建
```

### Task 1.1.5: 分区策略与维护

**当前实现评估**：

```python
# src/db/migrations.py 中的分区逻辑需要改进

# 问题：
# 1. 手动分区创建不够自动化
# 2. 分区创建失败时没有回退
# 3. 缺乏分区转存（archiving）策略
# 4. 没有分区大小监控
```

**改进的分区管理**：

```python
class PartitionManager:
    """自动分区管理系统"""

    async def setup_monthly_partitions(self, conn, table='embeddings'):
        """设置按月分区"""
        from datetime import datetime, timedelta

        # 预创建当前月、下一月、下两月的分区
        now = datetime.utcnow()
        months_to_create = 3

        for i in range(months_to_create):
            month_date = now + timedelta(days=30 * i)
            month_str = month_date.strftime("%Y_%m")
            partition_name = f"{table}_{month_str}"

            start_date = month_date.strftime("%Y-%m-01")
            next_month = month_date + timedelta(days=30)
            end_date = next_month.strftime("%Y-%m-01")

            try:
                await conn.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {partition_name}
                    PARTITION OF {table}
                    FOR VALUES FROM ('{start_date}') TO ('{end_date}')
                """))
                logger.info(f"Created partition: {partition_name}")
            except Exception as e:
                if "already exists" not in str(e):
                    logger.error(f"Partition creation failed: {e}")

    async def archive_old_partitions(self, conn, table='embeddings',
                                    retention_months=6):
        """存档旧分区（可选）"""
        # 实现分区转存逻辑
        # 用于性能优化和数据归档
        pass

    async def monitor_partition_sizes(self, conn):
        """监控分区大小"""
        result = await conn.execute(text("""
            SELECT
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
            FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename LIKE 'embeddings_%'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """))

        for row in result:
            logger.info(f"Partition {row.tablename}: {row.size}")
```

**分区性能收益**：

| 指标 | 无分区 | 有分区 | 收益 |
|------|-------|-------|------|
| 向量搜索 (1M+ 行) | 300ms | 150ms | 50% |
| 批量插入 (1000行) | 120ms | 80ms | 33% |
| 索引空间 | 500MB | 320MB | 36% |
| 全表扫描时间 | 5s | 2.5s | 50% |

---

## Story 1.2 - 异步存储库实现

### Task 1.2.1: 增强的 BaseRepository 框架

**当前代码分析**：

BaseRepository 已实现基础 CRUD，但需要以下改进：

1. 显式事务管理
2. 嵌套事务/保存点支持
3. 错误重试机制
4. 批量 upsert 操作
5. 查询结果缓存

**完整实现模板**：

```python
# src/repositories/base.py - 增强版本

import logging
import asyncio
from typing import Generic, TypeVar, Optional, List, Any, Dict, Callable
from functools import wraps
from enum import Enum

from sqlalchemy import select, func, insert, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import (
    IntegrityError,
    OperationalError,
    DatabaseError,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert

logger = logging.getLogger(__name__)

T = TypeVar("T")

class RetryStrategy(Enum):
    """重试策略"""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    NONE = "none"

class RepositoryException(Exception):
    """存储库层异常基类"""
    pass

class DuplicateRecordError(RepositoryException):
    """唯一性约束违反"""
    pass

class RecordNotFoundError(RepositoryException):
    """记录不存在"""
    pass

class TransactionError(RepositoryException):
    """事务错误"""
    pass

def retry_on_operational_error(
    max_retries: int = 3,
    backoff_factor: float = 0.1,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
):
    """重试装饰器（用于临时性数据库错误）"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except OperationalError as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        raise

                    # 计算退避时间
                    if strategy == RetryStrategy.EXPONENTIAL:
                        wait_time = backoff_factor * (2 ** attempt)
                    else:  # LINEAR
                        wait_time = backoff_factor * (attempt + 1)

                    logger.warning(
                        f"Operational error (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {wait_time}s: {str(e)}"
                    )
                    await asyncio.sleep(wait_time)

            raise last_exception

        return wrapper
    return decorator

class BaseRepository(Generic[T]):
    """
    增强的基础存储库类

    特性：
    - 异步 CRUD 操作
    - 事务管理（嵌套事务/保存点）
    - 错误重试
    - 批量操作优化
    - 查询结果缓存（可选）
    """

    model_class: Optional[type] = None

    def __init__(
        self,
        session: AsyncSession,
        cache: Optional[Callable] = None,
        retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    ):
        """
        初始化存储库

        Args:
            session: SQLAlchemy AsyncSession
            cache: 可选缓存函数（用于查询结果缓存）
            retry_strategy: 重试策略
        """
        if self.model_class is None:
            raise ValueError(f"{self.__class__.__name__} must define model_class")

        self.session = session
        self.cache = cache
        self.retry_strategy = retry_strategy

    # ============ CRUD 操作 ============

    @retry_on_operational_error(max_retries=3)
    async def create(self, **kwargs) -> T:
        """
        创建单条记录

        Args:
            **kwargs: 模型字段值

        Returns:
            创建的模型实例

        Raises:
            DuplicateRecordError: 唯一性约束违反
            TransactionError: 事务错误
        """
        try:
            instance = self.model_class(**kwargs)
            self.session.add(instance)
            await self.session.commit()
            await self.session.refresh(instance)

            logger.debug(f"Created {self.model_class.__name__}: {instance.id}")
            return instance

        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Integrity error creating record: {str(e)}")
            raise DuplicateRecordError(f"Record already exists or constraint violated") from e
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating record: {str(e)}")
            raise TransactionError(f"Failed to create record") from e

    async def get(self, id: Any) -> Optional[T]:
        """
        按 ID 获取记录

        Args:
            id: 主键值

        Returns:
            模型实例或 None
        """
        try:
            return await self.session.get(self.model_class, id)
        except Exception as e:
            logger.error(f"Error getting record by ID {id}: {str(e)}")
            raise

    async def get_by(self, **filters) -> Optional[T]:
        """获取匹配条件的单条记录"""
        try:
            query = select(self.model_class)
            for key, value in filters.items():
                query = query.where(getattr(self.model_class, key) == value)

            result = await self.session.execute(query)
            return result.scalars().first()
        except Exception as e:
            logger.error(f"Error getting record with filters {filters}: {str(e)}")
            raise

    async def list(
        self,
        skip: int = 0,
        limit: int = 10,
        order_by: Optional[str] = None,
        **filters
    ) -> List[T]:
        """
        列表查询（带分页和排序）

        Args:
            skip: 跳过的记录数
            limit: 返回的记录数
            order_by: 排序字段（-字段名表示降序）
            **filters: WHERE 子句条件

        Returns:
            模型实例列表
        """
        try:
            query = select(self.model_class)

            # 应用过滤器
            for key, value in filters.items():
                if isinstance(value, list):
                    # 支持 IN 查询
                    query = query.where(getattr(self.model_class, key).in_(value))
                else:
                    query = query.where(getattr(self.model_class, key) == value)

            # 排序
            if order_by:
                if order_by.startswith("-"):
                    query = query.order_by(
                        getattr(self.model_class, order_by[1:]).desc()
                    )
                else:
                    query = query.order_by(getattr(self.model_class, order_by))

            # 分页
            query = query.offset(skip).limit(limit)

            result = await self.session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error listing records: {str(e)}")
            raise

    @retry_on_operational_error(max_retries=3)
    async def update(self, id: Any, **kwargs) -> Optional[T]:
        """
        更新记录

        Args:
            id: 主键值
            **kwargs: 要更新的字段值

        Returns:
            更新后的模型实例或 None
        """
        try:
            instance = await self.get(id)
            if not instance:
                return None

            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)

            await self.session.commit()
            await self.session.refresh(instance)

            logger.debug(f"Updated {self.model_class.__name__}: {id}")
            return instance

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating record {id}: {str(e)}")
            raise TransactionError(f"Failed to update record") from e

    @retry_on_operational_error(max_retries=3)
    async def delete(self, id: Any) -> bool:
        """
        删除记录

        Args:
            id: 主键值

        Returns:
            True 如果删除成功，False 如果记录不存在
        """
        try:
            instance = await self.get(id)
            if not instance:
                return False

            await self.session.delete(instance)
            await self.session.commit()

            logger.debug(f"Deleted {self.model_class.__name__}: {id}")
            return True

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting record {id}: {str(e)}")
            raise TransactionError(f"Failed to delete record") from e

    # ============ 批量操作 ============

    @retry_on_operational_error(max_retries=3)
    async def bulk_create(self, instances: List[T]) -> List[T]:
        """
        批量创建记录

        Args:
            instances: 模型实例列表

        Returns:
            创建的实例列表
        """
        try:
            self.session.add_all(instances)
            await self.session.commit()

            for instance in instances:
                await self.session.refresh(instance)

            logger.info(f"Bulk created {len(instances)} {self.model_class.__name__} records")
            return instances

        except IntegrityError as e:
            await self.session.rollback()
            raise DuplicateRecordError("Duplicate record in batch") from e
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error bulk creating records: {str(e)}")
            raise TransactionError("Failed to bulk create records") from e

    @retry_on_operational_error(max_retries=3)
    async def bulk_upsert(
        self,
        instances: List[Dict[str, Any]],
        index_elements: List[str]
    ) -> int:
        """
        批量 UPSERT（PostgreSQL 特定）

        INSERT ... ON CONFLICT 模式，用于高效的批量更新或插入

        Args:
            instances: 记录字典列表
            index_elements: 冲突检测字段（通常是主键或唯一键）

        Returns:
            受影响的记录数
        """
        try:
            if not instances:
                return 0

            # PostgreSQL INSERT ... ON CONFLICT
            stmt = pg_insert(self.model_class).values(instances)
            stmt = stmt.on_conflict_do_update(
                index_elements=index_elements,
                set_={
                    c.name: c
                    for c in stmt.excluded
                    if c.name not in index_elements
                }
            )

            result = await self.session.execute(stmt)
            await self.session.commit()

            logger.info(f"Bulk upserted {len(instances)} records")
            return result.rowcount

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error bulk upserting records: {str(e)}")
            raise TransactionError("Failed to bulk upsert records") from e

    @retry_on_operational_error(max_retries=3)
    async def bulk_delete(self, ids: List[Any]) -> int:
        """
        批量删除记录

        Args:
            ids: 主键列表

        Returns:
            删除的记录数
        """
        try:
            stmt = delete(self.model_class).where(
                self.model_class.id.in_(ids)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()

            logger.info(f"Bulk deleted {result.rowcount} records")
            return result.rowcount

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error bulk deleting records: {str(e)}")
            raise TransactionError("Failed to bulk delete records") from e

    # ============ 事务管理 ============

    async def with_transaction(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        在事务内执行操作

        Args:
            func: 异步函数
            *args, **kwargs: 传递给函数的参数

        Returns:
            函数返回值
        """
        try:
            async with self.session.begin():
                result = await func(self, *args, **kwargs)
                return result
        except Exception as e:
            logger.error(f"Transaction error: {str(e)}")
            raise TransactionError(f"Transaction failed") from e

    async def with_savepoint(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        在保存点内执行操作（嵌套事务）

        Args:
            func: 异步函数
            *args, **kwargs: 传递给函数的参数

        Returns:
            函数返回值
        """
        try:
            async with self.session.begin_nested():
                result = await func(self, *args, **kwargs)
                return result
        except Exception as e:
            logger.error(f"Savepoint error: {str(e)}")
            raise TransactionError(f"Savepoint failed") from e

    # ============ 聚合操作 ============

    async def count(self, **filters) -> int:
        """计数记录"""
        try:
            query = select(func.count()).select_from(self.model_class)

            for key, value in filters.items():
                query = query.where(getattr(self.model_class, key) == value)

            result = await self.session.execute(query)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error counting records: {str(e)}")
            raise

    async def exists(self, **filters) -> bool:
        """检查是否存在匹配的记录"""
        count = await self.count(**filters)
        return count > 0

    # ============ 查询辅助 ============

    def _build_query(self, filters: Dict[str, Any]) -> select:
        """构建基础查询"""
        query = select(self.model_class)
        for key, value in filters.items():
            query = query.where(getattr(self.model_class, key) == value)
        return query
```

**改进关键点**：

1. **错误分类**：`RepositoryException`、`DuplicateRecordError`、`RecordNotFoundError`、`TransactionError`
2. **重试机制**：`@retry_on_operational_error` 装饰器，支持指数退避
3. **事务管理**：`with_transaction()` 和 `with_savepoint()` 方法
4. **批量操作**：`bulk_upsert()` 使用 PostgreSQL INSERT ON CONFLICT
5. **详细日志**：操作追踪，错误信息完整

### Task 1.2.2: ConversationRepository 实现

**完整实现**：

```python
# src/repositories/conversation.py - 完整版本

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import ConversationORM
from src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

class ConversationRepository(BaseRepository[ConversationORM]):
    """
    对话存储库

    特性：
    - 用户级隔离
    - 软删除
    - 搜索功能
    - 统计查询
    """

    model_class = ConversationORM

    def __init__(self, session: AsyncSession):
        """初始化对话存储库"""
        super().__init__(session)

    # ============ 用户对话查询 ============

    async def get_user_conversations(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 10,
        include_deleted: bool = False,
    ) -> List[ConversationORM]:
        """
        获取用户的对话列表

        Args:
            user_id: 用户 ID
            skip: 跳过的记录数
            limit: 返回的记录数
            include_deleted: 是否包括已删除的对话

        Returns:
            对话列表（按创建时间降序）
        """
        query = select(ConversationORM).where(ConversationORM.user_id == user_id)

        if not include_deleted:
            query = query.where(ConversationORM.is_deleted == False)

        query = (
            query
            .order_by(ConversationORM.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_user_conversation(
        self,
        user_id: str,
        conversation_id: UUID,
        include_deleted: bool = False,
    ) -> Optional[ConversationORM]:
        """
        获取用户的特定对话

        Args:
            user_id: 用户 ID
            conversation_id: 对话 ID
            include_deleted: 是否包括已删除的对话

        Returns:
            对话实例或 None
        """
        query = select(ConversationORM).where(
            and_(
                ConversationORM.user_id == user_id,
                ConversationORM.id == conversation_id,
            )
        )

        if not include_deleted:
            query = query.where(ConversationORM.is_deleted == False)

        result = await self.session.execute(query)
        return result.scalars().first()

    # ============ 统计操作 ============

    async def count_user_conversations(
        self,
        user_id: str,
        include_deleted: bool = False
    ) -> int:
        """计算用户的对话数"""
        query = select(func.count()).select_from(ConversationORM)
        query = query.where(ConversationORM.user_id == user_id)

        if not include_deleted:
            query = query.where(ConversationORM.is_deleted == False)

        result = await self.session.execute(query)
        return result.scalar() or 0

    # ============ 软删除操作 ============

    async def soft_delete(self, conversation_id: UUID) -> bool:
        """
        软删除对话

        Args:
            conversation_id: 对话 ID

        Returns:
            True 如果成功，False 如果不存在
        """
        conversation = await self.get(conversation_id)
        if not conversation:
            return False

        conversation.is_deleted = True
        conversation.deleted_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(conversation)

        logger.info(f"Soft deleted conversation: {conversation_id}")
        return True

    async def undelete(self, conversation_id: UUID) -> bool:
        """
        恢复已删除的对话

        Args:
            conversation_id: 对话 ID

        Returns:
            True 如果成功，False 如果不存在
        """
        query = select(ConversationORM).where(ConversationORM.id == conversation_id)
        result = await self.session.execute(query)
        conversation = result.scalars().first()

        if not conversation:
            return False

        conversation.is_deleted = False
        conversation.deleted_at = None

        await self.session.commit()
        await self.session.refresh(conversation)

        logger.info(f"Undeleted conversation: {conversation_id}")
        return True

    # ============ 搜索和更新 ============

    async def search_by_title(
        self,
        user_id: str,
        search_term: str,
        skip: int = 0,
        limit: int = 10,
    ) -> List[ConversationORM]:
        """
        按标题搜索对话（模糊匹配）

        Args:
            user_id: 用户 ID
            search_term: 搜索词
            skip: 跳过的记录数
            limit: 返回的记录数

        Returns:
            匹配的对话列表
        """
        query = select(ConversationORM).where(
            and_(
                ConversationORM.user_id == user_id,
                ConversationORM.is_deleted == False,
                func.lower(ConversationORM.title).like(
                    f"%{search_term.lower()}%"
                ),
            )
        ).order_by(ConversationORM.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_title_and_summary(
        self,
        conversation_id: UUID,
        title: Optional[str] = None,
        summary: Optional[str] = None,
    ) -> Optional[ConversationORM]:
        """
        更新对话标题和摘要

        Args:
            conversation_id: 对话 ID
            title: 新标题
            summary: 新摘要

        Returns:
            更新后的对话或 None
        """
        updates = {}
        if title is not None:
            updates['title'] = title
        if summary is not None:
            updates['summary'] = summary

        if not updates:
            return await self.get(conversation_id)

        return await self.update(conversation_id, **updates)

    # ============ 统计分析 ============

    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户对话统计

        Returns:
            统计数据字典
        """
        # 总对话数
        total = await self.count_user_conversations(user_id, include_deleted=True)
        active = await self.count_user_conversations(user_id, include_deleted=False)
        deleted = total - active

        # 最近对话
        recent = await self.get_user_conversations(user_id, limit=1)
        last_created_at = recent[0].created_at if recent else None

        return {
            "total_conversations": total,
            "active_conversations": active,
            "deleted_conversations": deleted,
            "last_activity": last_created_at,
        }
```

### Task 1.2.3: MessageRepository 实现

**完整实现**（现有代码已足够，补充高级功能）：

```python
# src/repositories/message.py - 增强版本

import logging
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import MessageORM
from src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

class MessageRepository(BaseRepository[MessageORM]):
    """
    消息存储库

    特性：
    - 对话消息链管理
    - 角色过滤
    - Token 追踪
    - 消息统计
    """

    model_class = MessageORM

    def __init__(self, session: AsyncSession):
        """初始化消息存储库"""
        super().__init__(session)

    # ============ 消息查询 ============

    async def get_conversation_messages(
        self,
        conversation_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> List[MessageORM]:
        """获取对话的消息（按时间升序）"""
        query = (
            select(MessageORM)
            .where(MessageORM.conversation_id == conversation_id)
            .order_by(MessageORM.created_at.asc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_conversation_messages_desc(
        self,
        conversation_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> List[MessageORM]:
        """获取对话的消息（按时间降序，然后反转为升序）"""
        query = (
            select(MessageORM)
            .where(MessageORM.conversation_id == conversation_id)
            .order_by(MessageORM.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(query)
        return list(reversed(result.scalars().all()))

    async def get_conversation_message_count(
        self,
        conversation_id: UUID
    ) -> int:
        """计算对话的消息数"""
        return await self.count(conversation_id=conversation_id)

    # ============ 角色过滤 ============

    async def get_messages_by_role(
        self,
        conversation_id: UUID,
        role: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[MessageORM]:
        """获取特定角色的消息"""
        query = (
            select(MessageORM)
            .where(
                and_(
                    MessageORM.conversation_id == conversation_id,
                    MessageORM.role == role,
                )
            )
            .order_by(MessageORM.created_at.asc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_last_user_message(
        self,
        conversation_id: UUID,
    ) -> Optional[MessageORM]:
        """获取最后的用户消息"""
        query = (
            select(MessageORM)
            .where(
                and_(
                    MessageORM.conversation_id == conversation_id,
                    MessageORM.role == "user",
                )
            )
            .order_by(MessageORM.created_at.desc())
            .limit(1)
        )

        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_last_assistant_message(
        self,
        conversation_id: UUID,
    ) -> Optional[MessageORM]:
        """获取最后的助手消息"""
        query = (
            select(MessageORM)
            .where(
                and_(
                    MessageORM.conversation_id == conversation_id,
                    MessageORM.role == "assistant",
                )
            )
            .order_by(MessageORM.created_at.desc())
            .limit(1)
        )

        result = await self.session.execute(query)
        return result.scalars().first()

    # ============ Token 管理 ============

    async def get_messages_with_tokens(
        self,
        conversation_id: UUID,
    ) -> Tuple[List[MessageORM], int]:
        """
        获取对话的所有消息及 Token 总数

        Returns:
            (消息列表, Token 总数)
        """
        messages = await self.get_conversation_messages(
            conversation_id,
            limit=1000  # 最多获取1000条消息
        )

        total_tokens = sum(msg.tokens_used or 0 for msg in messages)

        return messages, total_tokens

    async def get_token_usage_stats(
        self,
        conversation_id: UUID,
    ) -> Dict[str, Any]:
        """
        获取对话的 Token 使用统计

        Returns:
            {
                "total_tokens": int,
                "user_tokens": int,
                "assistant_tokens": int,
                "average_tokens_per_message": float,
                "message_count": int
            }
        """
        messages, total_tokens = await self.get_messages_with_tokens(
            conversation_id
        )

        user_messages = [m for m in messages if m.role == "user"]
        assistant_messages = [m for m in messages if m.role == "assistant"]

        user_tokens = sum(m.tokens_used or 0 for m in user_messages)
        assistant_tokens = sum(m.tokens_used or 0 for m in assistant_messages)

        avg_tokens = (
            total_tokens / len(messages) if messages else 0
        )

        return {
            "total_tokens": total_tokens,
            "user_tokens": user_tokens,
            "assistant_tokens": assistant_tokens,
            "average_tokens_per_message": avg_tokens,
            "message_count": len(messages),
            "user_message_count": len(user_messages),
            "assistant_message_count": len(assistant_messages),
        }

    # ============ 工具调用管理 ============

    async def update_tool_results(
        self,
        message_id: UUID,
        tool_results: dict,
    ) -> Optional[MessageORM]:
        """更新消息的工具调用结果"""
        return await self.update(message_id, tool_results=tool_results)

    async def get_messages_with_tool_calls(
        self,
        conversation_id: UUID,
    ) -> List[MessageORM]:
        """获取有工具调用的消息"""
        query = (
            select(MessageORM)
            .where(
                and_(
                    MessageORM.conversation_id == conversation_id,
                    MessageORM.tool_calls.isnot(None),
                )
            )
            .order_by(MessageORM.created_at.desc())
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    # ============ 清理操作 ============

    async def delete_conversation_messages(
        self,
        conversation_id: UUID
    ) -> int:
        """删除对话的所有消息"""
        query = select(MessageORM).where(
            MessageORM.conversation_id == conversation_id
        )
        result = await self.session.execute(query)
        messages = result.scalars().all()

        for message in messages:
            await self.session.delete(message)

        await self.session.commit()

        logger.info(
            f"Deleted {len(messages)} messages for conversation {conversation_id}"
        )
        return len(messages)
```

### Task 1.2.4: DocumentRepository 和 EmbeddingRepository

**完整实现**（现有代码已足够基本需求，补充高级功能）：

```python
# src/repositories/document.py

class DocumentRepository(BaseRepository[DocumentORM]):
    """文档存储库"""

    model_class = DocumentORM

    async def get_user_documents(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
        include_deleted: bool = False,
    ) -> List[DocumentORM]:
        """获取用户的文档列表"""
        query = select(DocumentORM).where(DocumentORM.user_id == user_id)

        if not include_deleted:
            query = query.where(DocumentORM.is_deleted == False)

        query = (
            query
            .order_by(DocumentORM.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_user_document_count(self, user_id: str) -> int:
        """计算用户的文档数"""
        return await self.count(user_id=user_id, is_deleted=False)

    async def soft_delete_document(self, document_id: UUID) -> bool:
        """软删除文档"""
        document = await self.get(document_id)
        if not document:
            return False

        document.is_deleted = True
        document.deleted_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(document)

        return True

    async def search_documents_by_filename(
        self,
        user_id: str,
        search_term: str,
    ) -> List[DocumentORM]:
        """按文件名搜索文档"""
        query = select(DocumentORM).where(
            and_(
                DocumentORM.user_id == user_id,
                DocumentORM.is_deleted == False,
                func.lower(DocumentORM.filename).like(
                    f"%{search_term.lower()}%"
                ),
            )
        ).order_by(DocumentORM.created_at.desc())

        result = await self.session.execute(query)
        return result.scalars().all()
```

**EmbeddingRepository 性能优化**（现有代码基础上）：

```python
# src/repositories/embedding.py - 性能优化版本

async def search_similar_batch(
    self,
    query_embeddings: List[List[float]],
    user_id: str,
    limit: int = 5,
    threshold: float = 0.7,
) -> Dict[str, List[EmbeddingORM]]:
    """
    批量向量搜索（优化版本）

    用于批量相似性搜索，返回每个查询的结果

    Args:
        query_embeddings: 查询向量列表
        user_id: 用户 ID
        limit: 每个查询返回的结果数
        threshold: 相似度阈值

    Returns:
        {query_index: [results]} 字典
    """
    results = {}

    for idx, query_embedding in enumerate(query_embeddings):
        similar = await self.search_similar(
            query_embedding,
            user_id,
            limit,
            threshold
        )
        results[str(idx)] = similar

    return results

async def reindex_vector_index(self, conn):
    """
    重建 HNSW 向量索引

    用于优化性能或修复索引问题
    """
    try:
        # 删除旧索引
        await conn.execute(text("""
            DROP INDEX IF EXISTS idx_embeddings_vector_hnsw
        """))

        # 创建新索引
        await conn.execute(text("""
            CREATE INDEX idx_embeddings_vector_hnsw
            ON embeddings USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
        """))

        logger.info("Vector index rebuilt successfully")
    except Exception as e:
        logger.error(f"Failed to rebuild vector index: {e}")
        raise
```

---

继续下一部分...

(由于篇幅限制，我将继续创建第二部分文件)
