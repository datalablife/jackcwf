# Memori & Claude 快速开始指南

## 5 分钟快速开始

### 1. 环境设置

```bash
# 进入后端目录
cd backend

# 复制环境配置
cp .env.example .env

# 编辑 .env，设置必要的变量
# 最重要的是：
# ANTHROPIC_API_KEY=sk-...
# MEMORI_DB_TYPE=sqlite (用于开发)
# MEMORI_SQLITE_PATH=./memori.db
```

### 2. 安装依赖

```bash
poetry install
```

### 3. 运行数据库迁移

```bash
# 创建 Memori 所需的表
alembic upgrade head
```

### 4. 启动应用

```bash
python -m src.main
# 或使用 uvicorn
uvicorn src.main:app --reload
```

### 5. 测试 API

```bash
# 添加记忆
curl -X POST http://localhost:8000/api/memory/add \
  -H "Content-Type: application/json" \
  -d '{
    "content": "User prefers SQL queries over ORM",
    "memory_type": "entity",
    "importance": 0.8,
    "tags": ["user_preference"]
  }'

# 搜索记忆
curl "http://localhost:8000/api/memory/search?query=SQL&limit=5"

# 获取统计信息
curl "http://localhost:8000/api/memory/stats"

# 发送消息给 Claude（需要 ANTHROPIC_API_KEY）
curl -X POST http://localhost:8000/api/memory/claude/message \
  -H "Content-Type: application/json" \
  -d '{
    "content": "How do I optimize SQL queries?",
    "conversation_id": "conv_123",
    "use_memory": true
  }'
```

---

## 核心概念速览

### 记忆类型

```python
# 短期记忆（本会话）
await manager.add_memory(
    content="User just mentioned PostgreSQL",
    memory_type="short_term",
    importance=0.5
)

# 长期记忆（跨会话）
await manager.add_memory(
    content="User prefers window functions",
    memory_type="long_term",
    importance=0.8
)

# 规则（系统约束）
await manager.add_memory(
    content="Always validate SQL queries for safety",
    memory_type="rule",
    importance=0.9
)

# 实体（引用数据）
await manager.add_memory(
    content="Main database: production_db",
    memory_type="entity",
    importance=0.7
)
```

### 重要性评分

```
1.0  ████ 关键规则、安全约束
0.8  ███  用户偏好、重要信息
0.5  ██   标准上下文
0.3  █    临时信息
```

---

## 常见任务

### 添加用户偏好

```python
from src.memory.manager import get_memory_manager

manager = get_memory_manager()

# 记住用户偏好
await manager.add_memory(
    content="User prefers concise responses with code examples",
    memory_type="entity",
    importance=0.8,
    tags=["user_preference", "communication_style"]
)
```

### 搜索相关信息

```python
# 找出关于性能优化的所有信息
results = await manager.search_memory(
    query="performance optimization",
    limit=10
)

for memory in results:
    print(f"[{memory['type']}] {memory['content']}")
```

### 使用 Claude 并注入上下文

```python
from src.services.claude_integration import get_claude_service

service = get_claude_service()

# Claude 会自动获得相关的记忆作为上下文
response = await service.chat(
    messages=[
        {"role": "user", "content": "Help me write a complex query"}
    ],
    conversation_id="conv_123",
    use_memory=True  # 启用记忆上下文注入
)

print(response["content"])
```

### 跟踪对话

```python
# 同一对话中的多次交互
messages = [
    {"role": "user", "content": "Setup PostgreSQL database"}
]

# 第一条消息
response1 = await service.chat(
    messages=messages,
    conversation_id="conv_123",
    use_memory=True
)

# 继续对话
messages.append({"role": "assistant", "content": response1["content"]})
messages.append({"role": "user", "content": "How do I add indexes?"})

response2 = await service.chat(
    messages=messages,
    conversation_id="conv_123",
    use_memory=True
)
# Claude 理解上下文（仍在讨论之前设置的 PostgreSQL）
```

### 获取系统统计

```python
stats = await manager.get_memory_stats()

print(f"Total Memories: {stats['total_memories']}")
print(f"Memory Types:")
for type_name, count in stats['memory_by_type'].items():
    print(f"  {type_name}: {count}")
```

### 清理旧记忆

```python
# 删除 30 天前的短期记忆
count = await manager.clear_memories(
    older_than_days=30,
    memory_type="short_term"
)
print(f"Cleared {count} old memories")
```

---

## 项目结构

```
backend/
├── src/
│   ├── memory/                    # 内存管理模块
│   │   ├── __init__.py
│   │   ├── config.py             # Memori 配置
│   │   └── manager.py            # 内存管理器
│   ├── services/
│   │   └── claude_integration.py # Claude 集成服务
│   ├── api/
│   │   └── memory.py             # 内存管理 API 端点
│   └── main.py                   # FastAPI 应用入口
├── migrations/versions/
│   └── 002_add_memori_memory_tables.py  # 数据库迁移
├── examples/
│   └── memori_integration_example.py    # 完整示例
├── tests/
│   └── test_memory_integration.py       # 集成测试
├── pyproject.toml                # Poetry 依赖配置
└── .env.example                  # 环境变量示例
```

---

## API 端点速查

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/memory/add` | 添加记忆 |
| POST | `/api/memory/search` | 搜索记忆 |
| GET | `/api/memory/search?query=...` | 搜索（GET） |
| GET | `/api/memory/context/{id}` | 获取对话上下文 |
| GET | `/api/memory/stats` | 获取系统统计 |
| DELETE | `/api/memory/clear` | 清理记忆 |
| POST | `/api/memory/claude/message` | 发送 Claude 消息 |
| GET | `/api/memory/health` | 健康检查 |

---

## 运行示例

```bash
# 进入后端目录
cd backend

# 运行完整示例
python examples/memori_integration_example.py
```

示例会：
1. 添加各种类型的记忆
2. 演示搜索功能
3. 展示与 Claude 的交互
4. 显示 API 使用方式
5. 提供最佳实践建议

---

## 环境变量参考

### 必需变量
```env
ANTHROPIC_API_KEY=sk-...              # Claude API 密钥
```

### 可选但推荐
```env
MEMORI_DB_TYPE=sqlite                 # 数据库类型（开发用 sqlite）
MEMORI_SQLITE_PATH=./memori.db        # SQLite 文件路径
MEMORI_CONSCIOUS_INGEST=true          # 启用持久化上下文
MEMORI_AUTO_INGEST=true               # 启用动态上下文注入
```

### 生产环境（PostgreSQL）
```env
MEMORI_DB_TYPE=postgresql
MEMORI_DB_HOST=localhost
MEMORI_DB_PORT=5432
MEMORI_DB_NAME=memori_memory
MEMORI_DB_USER=postgres
MEMORI_DB_PASSWORD=...
```

---

## 调试技巧

### 启用详细日志

```env
MEMORI_LOG_LEVEL=DEBUG
LOG_LEVEL=DEBUG
```

### 检查内存内容

```python
# 获取所有长期记忆
results = await manager.search_memory(
    query="",  # 空查询返回所有
    memory_type="long_term",
    limit=100
)

for r in results:
    print(f"{r['id']}: {r['content']}")
```

### 检查数据库

```bash
# SQLite 查询
sqlite3 memori.db "SELECT count(*) FROM memories;"
sqlite3 memori.db "SELECT * FROM memories LIMIT 5;"

# PostgreSQL 查询
psql -h localhost -U postgres -d memori_memory \
  -c "SELECT count(*) FROM memories;"
```

---

## 常见问题

**Q: Memori 需要额外的外部服务吗？**
A: 不需要。它使用标准 SQL 数据库（SQLite、PostgreSQL 等）存储。

**Q: 记忆会自动过期吗？**
A: 可以配置 `MEMORI_MEMORY_RETENTION_DAYS` 或使用 `clear_memories()` 手动清理。

**Q: Claude 集成需要什么？**
A: 只需设置 `ANTHROPIC_API_KEY` 环境变量。

**Q: 可以在多个应用实例间共享记忆吗？**
A: 可以，如果它们使用同一个 PostgreSQL 数据库。SQLite 不适合共享。

**Q: 如何处理隐私问题？**
A: 不要在记忆中存储 PII，使用 `clear_memories()` 定期清理，启用多租户隔离。

---

## 后续步骤

1. **运行示例** - 执行 `python examples/memori_integration_example.py` 了解全部功能
2. **阅读完整指南** - 查看 `MEMORI_INTEGRATION_GUIDE.md` 获取详细信息
3. **编写测试** - 参考 `tests/test_memory_integration.py` 编写自己的测试
4. **集成到应用** - 在你的业务逻辑中使用记忆管理和 Claude 集成
5. **监控** - 定期检查 `/api/memory/stats` 确保系统健康

---

## 获取帮助

- 查看 `MEMORI_INTEGRATION_GUIDE.md` 获取完整文档
- 检查 `tests/` 目录中的测试示例
- 查看 `examples/` 目录中的使用示例
- 参考 [Memori 官方文档](https://memori.readthedocs.io/)
- 参考 [Anthropic 文档](https://docs.anthropic.com/)

---

**祝你编码愉快！🚀**
