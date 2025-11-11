# Memori 与 Claude 集成指南

## 概述

本指南描述了如何在 Text2SQL 后端应用中集成 **Memori** - 一个为 AI 代理提供持久化、可查询内存的开源系统，以及 **Anthropic Claude API** 的上下文记忆管理。

### 关键特性

- **通用 LLM 集成**: 通过 `memori.enable()` 自动拦截并记录 Claude API 调用
- **SQL 原生存储**: 支持 PostgreSQL、MySQL、SQLite 等标准 SQL 数据库
- **智能记忆处理**: 自动进行实体提取、关系映射、重要性评分
- **双重记忆模式**:
  - **Conscious Ingest**: 在会话开始时注入持久化上下文
  - **Auto Ingest**: 在每次 LLM 调用时动态注入最相关的记忆
- **多种记忆类型**: 短期、长期、规则、实体

---

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │  Claude Chat     │  │ Memory API       │               │
│  │  Endpoints       │  │ Endpoints        │               │
│  └────────┬─────────┘  └────────┬─────────┘               │
│           │                      │                          │
│  ┌────────▼──────────────────────▼──────────┐              │
│  │  Claude Integration Service               │              │
│  │  - Message routing                       │              │
│  │  - Memory context injection              │              │
│  │  - Conversation management               │              │
│  └────────┬───────────────────────┬─────────┘              │
│           │                       │                         │
│  ┌────────▼──────────┐  ┌────────▼─────────┐              │
│  │ Anthropic Claude  │  │ Memory Manager   │              │
│  │ API Client        │  │ (Memori wrapper) │              │
│  └────────┬──────────┘  └────────┬─────────┘              │
│           │                      │                         │
└───────────┼──────────────────────┼──────────────────────────┘
            │                      │
┌───────────▼──────────────────────▼──────────────────────────┐
│                     Database Layer                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────┐      ┌──────────────────────┐   │
│  │  Main Database       │      │  Memory Database     │   │
│  │  (PostgreSQL)        │      │  (PostgreSQL/SQLite) │   │
│  │  - Data sources      │      │  - Memories table    │   │
│  │  - Files             │      │  - Relationships     │   │
│  │  - Users             │      │  - Conversations     │   │
│  └──────────────────────┘      │  - Statistics        │   │
│                                 └──────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 安装和配置

### 1. 更新依赖

项目的 `pyproject.toml` 已更新，包含必要的包：

```toml
[tool.poetry.dependencies]
memori = "^0.3.0"
anthropic = "^0.28.0"
litellm = "^1.45.0"
httpx = "^0.27.0"
```

安装依赖：
```bash
cd backend
poetry install
```

### 2. 环境变量配置

复制 `.env.example` 到 `.env` 并配置：

```bash
cp .env.example .env
```

关键环境变量：

```env
# Anthropic Claude
ANTHROPIC_API_KEY=sk-...
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Memori 配置
MEMORI_ENABLED=true
MEMORI_DB_TYPE=postgresql  # 或 sqlite
MEMORI_DB_HOST=localhost
MEMORI_DB_PORT=5432
MEMORI_DB_NAME=memori_memory
MEMORI_DB_USER=postgres
MEMORI_DB_PASSWORD=your_password

# 或使用 SQLite（开发环境推荐）
MEMORI_SQLITE_PATH=./memori.db

# 记忆模式
MEMORI_CONSCIOUS_INGEST=true
MEMORI_AUTO_INGEST=true
MEMORI_ENABLE_SEMANTIC_SEARCH=true
```

### 3. 数据库迁移

运行迁移脚本以创建 Memori 所需的表：

```bash
# 使用 Alembic 迁移
alembic upgrade head
```

迁移将创建以下表：
- `memories` - 核心记忆存储
- `memory_relationships` - 记忆之间的关系
- `conversations` - 对话跟踪
- `memory_search_index` - 快速搜索索引
- `memory_stats` - 系统统计

---

## 核心模块说明

### 1. MemoriConfig (`src/memory/config.py`)

配置类，管理 Memori 的所有设置。

```python
from src.memory.config import MemoriConfig, memory_config

# 自定义配置
config = MemoriConfig(
    enabled=True,
    db_type="postgresql",
    conscious_ingest=True,
    auto_ingest=True,
)

# 获取数据库连接字符串
conn_str = config.db_connection_string
```

**关键属性**:
- `enabled`: 启用/禁用 Memori
- `db_type`: 数据库类型 (sqlite, postgresql, mysql)
- `conscious_ingest`: 启用持久化上下文注入
- `auto_ingest`: 启用实时动态注入
- `enable_semantic_search`: 启用语义搜索
- `memory_retention_days`: 记忆保留天数

### 2. MemoryManager (`src/memory/manager.py`)

管理 Memori 实例的生命周期和操作。

```python
from src.memory.manager import get_memory_manager

# 获取全局单例
manager = get_memory_manager()

# 初始化（在 FastAPI lifespan 中自动调用）
await manager.initialize()

# 添加记忆
await manager.add_memory(
    content="User prefers concise responses",
    memory_type="entity",
    importance=0.8,
    tags=["user_preference"],
    metadata={"user_id": "123"}
)

# 搜索记忆
results = await manager.search_memory(
    query="database optimization",
    memory_type="long_term",
    limit=10,
    threshold=0.0
)

# 获取对话上下文
memories = await manager.get_conversation_context(
    conversation_id="conv_123",
    max_memories=10
)

# 获取统计信息
stats = await manager.get_memory_stats()
```

**可用方法**:
- `add_memory()` - 添加记忆
- `search_memory()` - 搜索记忆
- `get_conversation_context()` - 获取对话上下文
- `clear_memories()` - 清理过期记忆
- `get_memory_stats()` - 获取系统统计

### 3. ClaudeIntegrationService (`src/services/claude_integration.py`)

处理 Claude API 调用并注入记忆上下文。

```python
from src.services.claude_integration import get_claude_service

# 获取全局单例
service = get_claude_service()

# 初始化（在 FastAPI lifespan 中自动调用）
await service.initialize()

# 发送消息（带记忆注入）
response = await service.chat(
    messages=[
        {"role": "user", "content": "How do I optimize my SQL queries?"}
    ],
    conversation_id="conv_123",
    use_memory=True,  # 注入相关记忆作为上下文
    system_prompt=None  # 使用默认系统提示
)

# 返回结构
{
    "content": "Assistant response...",
    "usage": {
        "input_tokens": 150,
        "output_tokens": 200
    },
    "stop_reason": "end_turn",
    "model": "claude-3-5-sonnet-20241022"
}

# 流式响应
async for chunk in service.chat_streaming(
    messages=messages,
    conversation_id="conv_123",
    use_memory=True
):
    print(chunk, end="", flush=True)
```

---

## API 端点

### 内存管理 API (`/api/memory`)

#### 1. 添加记忆
```
POST /api/memory/add

{
    "content": "User prefers PostgreSQL",
    "memory_type": "entity",  // short_term, long_term, rule, entity
    "importance": 0.8,        // 0.0 - 1.0
    "tags": ["database", "preference"],
    "metadata": {"source": "user_input"}
}

Response:
{
    "success": true,
    "message": "Memory added successfully"
}
```

#### 2. 搜索记忆
```
POST /api/memory/search

{
    "query": "database optimization",
    "memory_type": "long_term",    // optional
    "limit": 10,
    "threshold": 0.0
}

Response:
{
    "success": true,
    "count": 3,
    "memories": [
        {
            "id": "mem_123",
            "content": "...",
            "type": "long_term",
            "importance": 0.8
        }
    ]
}
```

#### 3. 获取对话上下文
```
GET /api/memory/context/{conversation_id}?max_memories=10

Response:
{
    "success": true,
    "count": 5,
    "memories": [...]
}
```

#### 4. 获取系统统计
```
GET /api/memory/stats

Response:
{
    "success": true,
    "stats": {
        "initialized": true,
        "total_memories": 42,
        "memory_by_type": {
            "short_term": 10,
            "long_term": 25,
            "rules": 5,
            "entities": 2
        },
        "database_size": 2.5
    }
}
```

#### 5. 清理记忆
```
DELETE /api/memory/clear?older_than_days=30&memory_type=short_term

Response:
{
    "success": true,
    "cleared": 15
}
```

### Claude 集成 API

#### 发送消息
```
POST /api/memory/claude/message

{
    "content": "How do I create indexes in PostgreSQL?",
    "conversation_id": "conv_123",
    "use_memory": true,
    "system_prompt": null  // optional custom system prompt
}

Response:
{
    "success": true,
    "response": "To create indexes in PostgreSQL...",
    "usage": {
        "input_tokens": 150,
        "output_tokens": 200
    },
    "conversation_id": "conv_123"
}
```

#### 健康检查
```
GET /api/memory/health

Response:
{
    "success": true,
    "status": "healthy",
    "memory_initialized": true
}
```

---

## 使用场景

### 场景 1: 用户特定的 SQL 优化建议

```python
# 添加用户偏好到记忆
await manager.add_memory(
    content="User prefers window functions for complex aggregations",
    memory_type="entity",
    importance=0.8,
    tags=["user_preference", "sql_optimization"]
)

# 后续查询时自动注入这个偏好
response = await claude_service.chat(
    messages=[{"role": "user", "content": "How do I calculate running totals?"}],
    use_memory=True
)
# Claude 的回复会考虑用户对 window functions 的偏好
```

### 场景 2: 系统规则和约束

```python
# 添加安全规则
await manager.add_memory(
    content="Always validate and sanitize user input before SQL execution",
    memory_type="rule",
    importance=0.95,
    tags=["security", "sql_safety"]
)

# 添加性能约束
await manager.add_memory(
    content="Queries must complete in under 5 seconds for user-facing operations",
    memory_type="rule",
    importance=0.9,
    tags=["performance", "constraint"]
)
```

### 场景 3: 对话历史管理

```python
# 第一条消息
response1 = await claude_service.chat(
    messages=[{"role": "user", "content": "Set up a PostgreSQL database"}],
    conversation_id="conv_123",
    use_memory=True
)

# 后续消息将从记忆中检索前一条的上下文
response2 = await claude_service.chat(
    messages=[
        {"role": "user", "content": "Set up a PostgreSQL database"},
        {"role": "assistant", "content": response1["content"]},
        {"role": "user", "content": "How do I add indexes?"}
    ],
    conversation_id="conv_123",
    use_memory=True
)
# Claude 能够理解这是关于之前创建的 PostgreSQL 数据库的后续问题
```

### 场景 4: 实体和关系管理

```python
# 添加实体记忆
await manager.add_memory(
    content="Database: customer_db, Tables: users, orders, products",
    memory_type="entity",
    importance=0.7,
    tags=["database_schema", "customer_db"],
    metadata={"database": "customer_db"}
)

# 搜索特定数据库的信息
results = await manager.search_memory(
    query="customer_db schema",
    limit=5
)
```

---

## 记忆类型和重要性评分指南

### 记忆类型

| 类型 | 描述 | 典型重要性 | 使用场景 |
|------|------|----------|--------|
| **short_term** | 当前会话的临时信息 | 0.3-0.6 | 当前任务、临时笔记、会话特定上下文 |
| **long_term** | 跨会话的持久化信息 | 0.5-0.9 | 用户偏好、学习的事实、历史交互 |
| **rule** | 系统约束和准则 | 0.7-1.0 | 安全策略、业务规则、最佳实践 |
| **entity** | 命名实体和引用数据 | 0.4-0.8 | 用户、数据库、API、关系 |

### 重要性评分

```
1.0:    ████████████████ 关键安全规则、系统约束
0.9:    ████████████████ 重要规则、关键偏好
0.8:    ███████████████  用户偏好、重要事实
0.7:    ███████████████  常用指南、模式
0.6:    ██████████████   一般上下文、常见知识
0.5:    █████████████    标准内存、中等重要性
0.4:    ████████████     参考数据、补充信息
0.3:    ███████████      临时信息、低优先级
0.0:    ░░░░░░░░░░░░░░░░ 已弃用或存档的信息
```

---

## 性能优化建议

### 1. 记忆检索优化

```python
# 为常见查询添加标签
await manager.add_memory(
    content="...",
    tags=["frequent_query", "sql_optimization"]
)

# 按标签搜索（更快）
results = await manager.search_memory(
    query="",  # 可选
    limit=10
)
```

### 2. 批量操作

```python
# 批量添加记忆
memories = [...]  # 准备好的记忆列表
for memory in memories:
    await manager.add_memory(**memory)
```

### 3. 缓存策略

Memori 配置中启用缓存：
```env
MEMORI_ENABLE_CACHING=true
MEMORI_CACHE_TTL_SECONDS=300  # 5 分钟缓存
```

### 4. 定期清理

设置定期清理任务：
```python
# 清理 30 天前的短期记忆
await manager.clear_memories(
    older_than_days=30,
    memory_type="short_term"
)
```

---

## 监控和调试

### 获取系统统计

```python
stats = await manager.get_memory_stats()

print(f"Total Memories: {stats['total_memories']}")
print(f"Distribution: {stats['memory_by_type']}")
print(f"Database Size: {stats['database_size']} MB")
```

### 日志记录

查看应用日志以追踪 Memori 操作：

```bash
# 设置日志级别
MEMORI_LOG_LEVEL=DEBUG

# 查看日志
tail -f backend/app.log | grep memory
```

### 性能监控

从 `/api/memory/stats` 端点监控：
- 总记忆数
- 内存分布
- 数据库大小
- 平均重要性分数

---

## 故障排除

### 问题 1: "Memori not initialized"

**原因**: 应用启动时初始化失败

**解决方案**:
1. 检查 `ANTHROPIC_API_KEY` 是否设置
2. 验证数据库连接
3. 查看应用启动日志

### 问题 2: 内存搜索结果为空

**原因**: 没有相关的记忆或搜索查询不匹配

**解决方案**:
1. 确保先添加了记忆
2. 使用更通用的搜索查询
3. 检查记忆是否已过期

### 问题 3: Claude API 超时

**原因**: 记忆检索或上下文注入耗时过长

**解决方案**:
1. 减少 `MEMORI_CACHE_TTL_SECONDS`
2. 限制搜索结果数（`limit=5`）
3. 使用更高的重要性阈值

### 问题 4: 数据库磁盘空间不足

**原因**: 记忆数据库增长过快

**解决方案**:
```python
# 定期清理过期记忆
await manager.clear_memories(older_than_days=30)

# 或只清理特定类型
await manager.clear_memories(
    older_than_days=7,
    memory_type="short_term"
)
```

---

## 最佳实践

### 1. 记忆组织

- 使用描述性标签组织相关记忆
- 将相关的记忆链接在一起
- 定期审查和更新记忆重要性

### 2. 隐私和安全

- 不要在记忆中存储敏感的 API 密钥
- 对个人数据应用适当的过期策略
- 利用多租户隔离功能

### 3. 性能

- 为高频查询优化记忆结构
- 使用合适的记忆类型和重要性分数
- 实施定期的清理和维护策略

### 4. 监控

- 定期检查内存统计
- 追踪记忆检索性能
- 监控数据库大小增长

---

## 后续开发计划

### 短期
- [ ] 实现 WebSocket 支持实时记忆更新
- [ ] 添加记忆版本控制
- [ ] 实现批量 API 端点

### 中期
- [ ] 集成向量数据库用于更好的语义搜索
- [ ] 实现记忆可视化仪表板
- [ ] 添加记忆导入/导出功能

### 长期
- [ ] 实现分布式记忆存储
- [ ] 添加多 LLM 提供商支持
- [ ] 实现高级分析和洞察功能

---

## 参考资源

- [Memori GitHub](https://github.com/GibsonAI/Memori)
- [Memori 文档](https://memori.readthedocs.io/)
- [Anthropic Claude API 文档](https://docs.anthropic.com/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)

---

## 支持和反馈

如有任何问题或建议，请提交 Issue 或 Pull Request 到项目仓库。

**最后更新**: 2024-11-12
