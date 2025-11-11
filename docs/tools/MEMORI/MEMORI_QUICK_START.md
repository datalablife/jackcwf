# Memori快速开始指南

本文档提供快速集成Memori到Text2SQL项目的步骤。

## 前置条件

```bash
# 1. 安装依赖
cd /mnt/d/工作区/云开发/working/backend
poetry add anthropic memori-ai tiktoken

# 2. 设置环境变量
echo "MEMORI_ANTHROPIC_API_KEY=your-api-key-here" >> .env
```

## 5分钟快速集成

### 步骤1: 创建服务文件

已创建以下核心文件：
- `/backend/src/services/memori_service.py` - Memori服务管理器
- `/backend/src/services/token_manager.py` - Token管理
- `/backend/src/services/claude_retry.py` - 重试策略
- `/backend/src/api/text2sql.py` - Text2SQL API端点

### 步骤2: 在main.py中注册路由

```python
# backend/src/main.py
from src.api import text2sql, monitoring

app.include_router(text2sql.router)
app.include_router(monitoring.router)
```

### 步骤3: 创建数据库表（如需要）

```python
# backend/migrations/versions/00X_add_sessions_table.py
"""添加会话表"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

def upgrade():
    op.create_table(
        'user_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('last_activity', sa.DateTime, nullable=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('ended_at', sa.DateTime, nullable=True),
        sa.Column('metadata', JSONB, nullable=True)
    )

    op.create_index('idx_user_sessions_user_id', 'user_sessions', ['user_id'])
    op.create_index('idx_user_sessions_active', 'user_sessions', ['is_active'])

def downgrade():
    op.drop_table('user_sessions')
```

### 步骤4: 测试集成

```bash
# 启动服务
poetry run uvicorn src.main:app --reload

# 测试API
curl -X POST http://localhost:8000/api/text2sql/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "session_id": "test_session",
    "datasource_id": 1,
    "query": "查询所有用户"
  }'
```

## 配置说明

### 基础配置

在 `.env` 文件中添加：

```bash
# Anthropic API
MEMORI_ANTHROPIC_API_KEY=sk-ant-your-key

# 模型选择
MEMORI_CLAUDE_MODEL=claude-sonnet-4-5-20250929

# 记忆配置
MEMORI_CONSCIOUS_INGEST=true
MEMORI_AUTO_INGEST=true
MEMORI_MAX_MEMORY_TOKENS=100000

# Token预算
MEMORI_DAILY_TOKEN_LIMIT=1000000
MEMORI_PER_REQUEST_TOKEN_LIMIT=8000

# 并发控制
MEMORI_MAX_CONCURRENT_REQUESTS=10
MEMORI_MAX_REQUESTS_PER_USER=3
```

### 高级配置

对于生产环境，参考 `.env.memori` 中的完整配置。

## 使用示例

### 示例1: 基本对话

```python
from src.services.memori_service import get_memori_service

memori_service = get_memori_service()

# 创建对话
response = await memori_service.create_message(
    user_id="user_123",
    session_id="session_456",
    messages=[
        {"role": "user", "content": "生成查询所有用户的SQL"}
    ],
    system="You are a SQL expert."
)

print(response["content"])  # 生成的SQL
```

### 示例2: 添加显式记忆

```python
# 保存数据库schema到记忆
await memori_service.add_conscious_memory(
    user_id="user_123",
    session_id="session_456",
    content="Table: users (id INT, name VARCHAR, email VARCHAR)",
    metadata={"type": "schema", "table": "users"},
    importance=0.9,
    namespace="schema:1"
)
```

### 示例3: 搜索相关记忆

```python
# 搜索相关的schema信息
memories = await memori_service.search_memories(
    user_id="user_123",
    session_id="session_456",
    query="用户表结构",
    limit=5
)

for memory in memories:
    print(f"Content: {memory['content']}")
    print(f"Importance: {memory['importance']}")
```

### 示例4: 监控使用情况

```python
from src.services.token_manager import get_token_manager

token_manager = get_token_manager()

# 获取用户使用统计
stats = await token_manager.get_usage_stats(
    user_id="user_123",
    days=7
)

print(f"Total tokens: {stats['total_tokens']}")
print(f"Estimated cost: ${stats['estimated_cost']:.2f}")
```

## 常见使用场景

### 场景1: Text2SQL生成

```python
@router.post("/text2sql/generate")
async def generate_sql(request: Text2SQLRequest):
    # 1. 构建包含schema的上下文
    context_builder = ContextBuilder()
    context = await context_builder.build_context(
        user_id=request.user_id,
        session_id=request.session_id,
        user_query=request.query,
        datasource_id=request.datasource_id
    )

    # 2. 调用Claude（自动注入相关记忆）
    response = await memori_service.create_message(
        user_id=request.user_id,
        session_id=request.session_id,
        messages=[{"role": "user", "content": request.query}],
        system=f"You are a SQL expert.\n\n{context}",
        namespace=f"datasource:{request.datasource_id}"
    )

    return {"sql": response["content"]}
```

### 场景2: 多轮对话优化

```python
# 用户第一次查询
response1 = await memori_service.create_message(
    user_id="user_123",
    session_id="session_456",
    messages=[
        {"role": "user", "content": "查询用户表"}
    ]
)

# 用户第二次查询（Memori自动记住第一次的上下文）
response2 = await memori_service.create_message(
    user_id="user_123",
    session_id="session_456",
    messages=[
        {"role": "user", "content": "查询用户表"},
        {"role": "assistant", "content": response1["content"]},
        {"role": "user", "content": "加上年龄筛选"}
    ]
)
```

### 场景3: Schema记忆管理

```python
async def cache_datasource_schema(datasource_id: int):
    """将数据源schema缓存到Memori"""
    # 获取schema
    schema = await get_datasource_schema(datasource_id)

    # 为每个表创建记忆
    for table in schema.tables:
        content = f"Table: {table.name}\n"
        content += f"Columns: {', '.join(f'{c.name} ({c.type})' for c in table.columns)}"

        await memori_service.add_conscious_memory(
            user_id="system",
            session_id="schema_cache",
            content=content,
            metadata={
                "type": "schema",
                "datasource_id": datasource_id,
                "table_name": table.name
            },
            importance=0.95,
            namespace=f"schema:{datasource_id}"
        )
```

## 性能优化建议

### 1. 减少Token使用

```python
# 使用更小的上下文窗口
from src.services.optimization_strategies import CostOptimizer, OptimizationStrategy

optimizer = CostOptimizer(strategy=OptimizationStrategy.AGGRESSIVE)
optimized_messages = optimizer.optimize_context(messages, max_tokens=4096)
```

### 2. 实施缓存

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_schema(datasource_id: int):
    """缓存schema查询结果"""
    return fetch_schema_from_db(datasource_id)
```

### 3. 异步批处理

```python
import asyncio

# 批量处理多个请求
async def batch_generate_sql(requests: List[Text2SQLRequest]):
    tasks = [
        generate_sql(request)
        for request in requests
    ]
    return await asyncio.gather(*tasks)
```

## 监控和调试

### 启用调试日志

```python
# backend/src/main.py
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 只为Memori启用DEBUG
logging.getLogger('src.services.memori_service').setLevel(logging.DEBUG)
```

### 查看监控指标

```bash
# 获取系统统计
curl http://localhost:8000/api/monitoring/stats/hourly?hours=24

# 获取用户统计
curl http://localhost:8000/api/monitoring/stats/user/user_123?days=7

# 获取记忆增长趋势
curl http://localhost:8000/api/monitoring/memory/growth/user_123/session_456
```

## 故障排查

### 问题1: "ANTHROPIC_API_KEY not found"

**解决方案**:
```bash
# 确保环境变量已设置
export MEMORI_ANTHROPIC_API_KEY=your-key

# 或在.env文件中添加
echo "MEMORI_ANTHROPIC_API_KEY=your-key" >> .env
```

### 问题2: Token限制错误

**解决方案**:
```python
# 增加token预算
MEMORI_DAILY_TOKEN_LIMIT=5000000

# 或减少单次请求的token
MEMORI_PER_REQUEST_TOKEN_LIMIT=4000
```

### 问题3: 高延迟

**解决方案**:
```python
# 1. 减少检索的记忆数量
MEMORI_RETRIEVAL_LIMIT=5

# 2. 使用更快的模型
MEMORI_CLAUDE_MODEL=claude-3-haiku-20240307

# 3. 启用缓存
MEMORI_ENABLE_CACHING=true
```

### 问题4: 记忆隔离失败

**检查**:
```python
# 验证session key唯一性
async def test_isolation():
    service = get_memori_service()

    # 为两个不同会话添加记忆
    await service.add_conscious_memory(
        user_id="user1",
        session_id="session1",
        content="Session 1 memory"
    )

    await service.add_conscious_memory(
        user_id="user1",
        session_id="session2",
        content="Session 2 memory"
    )

    # 搜索，确保隔离
    s1_memories = await service.search_memories(
        user_id="user1",
        session_id="session1",
        query="memory"
    )

    # Session 2的记忆不应出现在Session 1的搜索结果中
    assert all("Session 1" in m["content"] for m in s1_memories)
```

## 下一步

1. 阅读完整的集成指南: `/mnt/d/工作区/云开发/working/MEMORI_CLAUDE_INTEGRATION_GUIDE.md`
2. 查看API文档: `http://localhost:8000/docs`
3. 运行集成测试: `poetry run pytest tests/integration/test_memori.py`
4. 配置生产环境: 参考部署清单

## 支持

遇到问题？
- 查看详细文档: `MEMORI_CLAUDE_INTEGRATION_GUIDE.md`
- 检查日志: `/tmp/backend.log`
- 查看监控: `http://localhost:8000/api/monitoring/stats/hourly`

---

**最后更新**: 2025-11-11
