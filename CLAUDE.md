
[项目记忆规则]
        - **必须主动调用** progress-recorder agent 来记录重要决策、任务变更、完成事项等关键信息到progress.md
        - 检测到以下情况时**立即自动触发** progress-recorder:
               *   出现"决定使用/最终选择/将采用"等决策语言
               *   出现"必须/不能/要求"等约束语言
               *   出现"完成了/实现了/修复了"等完成标识
               *   出现"需要/应该/计划"等新任务
        - 当 progress.md 的 Notes/Done 条目过多 (>100条)影响阅读时，应归档到 progress.archive.md

[指令集 - 前缀 "/"]
        - record：使用 progress-recorder 执行增量合并任务
        - archive：使用 progress-recorder 执行快照归档任务
        - recap：阅读 progress.md，回顾项目当前状态（包括但不仅限于关键约束、待办事项、完成时度等）

# Claude 上下文记忆管理系统完全指南

## 📑 目录概览

本文档是 Claude API 与 Memori 内存管理系统集成的完整索引和导航指南。

---

## 🎯 核心模块

### 🧠 Memori 记忆系统集成

Memori 是一个为 AI 代理提供持久化、可查询内存的开源系统。已完整集成到本项目中，为 Claude API 提供上下文记忆能力。

#### 快速导航

| 资源 | 位置 | 描述 |
|------|------|------|
| **快速开始** | [docs/tools/MEMORI/MEMORI_QUICKSTART.md](./docs/tools/MEMORI/MEMORI_QUICKSTART.md) | 5分钟快速上手指南 |
| **完整指南** | [docs/tools/MEMORI/MEMORI_INTEGRATION_GUIDE.md](./docs/tools/MEMORI/MEMORI_INTEGRATION_GUIDE.md) | 1200+ 行详细集成指南 |
| **实现总结** | [docs/tools/MEMORI/MEMORI_IMPLEMENTATION_SUMMARY.md](./docs/tools/MEMORI/MEMORI_IMPLEMENTATION_SUMMARY.md) | 功能总结和部署清单 |
| **代码示例** | [backend/examples/memori_integration_example.py](./backend/examples/memori_integration_example.py) | 6 个可运行的示例场景 |
| **集成测试** | [backend/tests/test_memory_integration.py](./backend/tests/test_memory_integration.py) | 综合测试用例 |

---

## 📦 实现清单

### ✅ 后端集成完成

#### 核心模块（已实现）
- ✅ `src/memory/config.py` - Memori 和 Claude 配置管理
- ✅ `src/memory/manager.py` - 内存管理器（CRUD、搜索、统计）
- ✅ `src/services/claude_integration.py` - Claude API 集成服务
- ✅ `src/api/memory.py` - 8 个 RESTful API 端点

#### 数据库支持（已实现）
- ✅ `migrations/versions/002_add_memori_memory_tables.py` - 数据库迁移脚本
  - `memories` 表 - 核心记忆存储
  - `memory_relationships` 表 - 记忆关系图
  - `conversations` 表 - 对话追踪
  - `memory_search_index` 表 - 搜索索引
  - `memory_stats` 表 - 系统统计

#### 配置和依赖（已实现）
- ✅ `backend/pyproject.toml` - 更新依赖（memori、anthropic、litellm）
- ✅ `backend/.env.example` - 环境变量配置示例

---

## 🔌 API 端点速查

### 内存管理 API 端点（`/api/memory`）

#### 添加记忆
```
POST /api/memory/add
请求体: { content, memory_type, importance, tags, metadata }
响应: { success, message }
```
📖 详细说明：[集成指南 - API 部分](./docs/tools/MEMORI/MEMORI_INTEGRATION_GUIDE.md#api-端点)

#### 搜索记忆
```
POST /api/memory/search
GET  /api/memory/search?query=...
请求体: { query, memory_type, limit, threshold }
响应: { success, count, memories }
```

#### 获取对话上下文
```
GET /api/memory/context/{conversation_id}?max_memories=10
响应: { success, count, memories }
```

#### 系统统计
```
GET /api/memory/stats
响应: { success, stats }
```

#### 清理记忆
```
DELETE /api/memory/clear?older_than_days=30&memory_type=short_term
响应: { success, cleared }
```

#### Claude 消息发送
```
POST /api/memory/claude/message
请求体: { content, conversation_id, use_memory, system_prompt }
响应: { success, response, usage, conversation_id }
```

#### 健康检查
```
GET /api/memory/health
响应: { success, status, memory_initialized }
```

---

## 🚀 快速开始 (5 分钟)

### 1. 环境设置
```bash
cd backend
cp .env.example .env
# 编辑 .env 设置 ANTHROPIC_API_KEY=sk-...
```

### 2. 安装依赖
```bash
poetry install
```

### 3. 数据库迁移
```bash
alembic upgrade head
```

### 4. 启动应用
```bash
python -m src.main
```

### 5. 测试 API
```bash
# 添加记忆
curl -X POST http://localhost:8000/api/memory/add \
  -H "Content-Type: application/json" \
  -d '{"content":"test memory","memory_type":"long_term","importance":0.8}'

# 发送 Claude 消息
curl -X POST http://localhost:8000/api/memory/claude/message \
  -H "Content-Type: application/json" \
  -d '{"content":"Hello","conversation_id":"conv_1","use_memory":true}'
```

详见：[MEMORI_QUICKSTART.md](./docs/tools/MEMORI/MEMORI_QUICKSTART.md)

---

## 💡 核心概念

### 记忆类型（4 种）

| 类型 | 描述 | 重要性 | 用途 |
|------|------|--------|------|
| **short_term** | 当前会话临时信息 | 0.3-0.6 | 临时笔记、任务上下文 |
| **long_term** | 跨会话持久化信息 | 0.5-0.9 | 用户偏好、学习事实 |
| **rule** | 系统约束和准则 | 0.7-1.0 | 安全规则、业务约束 |
| **entity** | 命名实体和引用 | 0.4-0.8 | 用户、数据库、关系 |

### 重要性评分

```
1.0  ████ 关键安全规则、系统约束
0.9  ███  重要规则、关键偏好
0.8  ███  用户偏好、重要信息
0.5  ██   标准内存、中等重要性
0.3  █    临时信息、低优先级
```

### 双重记忆模式

| 模式 | 说明 | 特点 |
|------|------|------|
| **Conscious Ingest** | 会话开始时注入 | 持久化、全局上下文、性能好 |
| **Auto Ingest** | 每次调用时注入 | 动态、相关性高、实时性好 |
| **Combined** | 同时启用 | 最佳效果，兼顾性能和相关性 |

---

## 📚 完整文档导引

### 对于新手
1. 开始：[MEMORI_QUICKSTART.md](./docs/tools/MEMORI/MEMORI_QUICKSTART.md) - 5分钟快速开始
2. 学习：[MEMORI_INTEGRATION_GUIDE.md](./docs/tools/MEMORI/MEMORI_INTEGRATION_GUIDE.md) - 完整学习指南
3. 实践：[backend/examples/memori_integration_example.py](./backend/examples/memori_integration_example.py) - 代码示例

### 对于开发者
1. 架构：[MEMORI_INTEGRATION_GUIDE.md - 架构概览](./docs/tools/MEMORI/MEMORI_INTEGRATION_GUIDE.md#架构概览)
2. 模块：[MEMORI_INTEGRATION_GUIDE.md - 核心模块说明](./docs/tools/MEMORI/MEMORI_INTEGRATION_GUIDE.md#核心模块说明)
3. 代码：[backend/src/memory/](./backend/src/memory/) 和 [backend/src/services/claude_integration.py](./backend/src/services/claude_integration.py)
4. 测试：[backend/tests/test_memory_integration.py](./backend/tests/test_memory_integration.py)

### 对于运维
1. 部署：[MEMORI_IMPLEMENTATION_SUMMARY.md - 部署检查清单](./docs/tools/MEMORI/MEMORI_IMPLEMENTATION_SUMMARY.md#部署检查清单)
2. 监控：[MEMORI_INTEGRATION_GUIDE.md - 监控和调试](./docs/tools/MEMORI/MEMORI_INTEGRATION_GUIDE.md#监控和调试)
3. 性能：[MEMORI_INTEGRATION_GUIDE.md - 性能优化](./docs/tools/MEMORI/MEMORI_INTEGRATION_GUIDE.md#性能优化建议)
4. 故障排查：[MEMORI_INTEGRATION_GUIDE.md - 故障排除](./docs/tools/MEMORI/MEMORI_INTEGRATION_GUIDE.md#故障排除)

---

## 🎯 使用场景

### 场景 1：保存用户偏好
```python
await manager.add_memory(
    content="User prefers window functions for aggregations",
    memory_type="entity",
    importance=0.8,
    tags=["user_preference", "sql"]
)
```

### 场景 2：系统规则约束
```python
await manager.add_memory(
    content="Always validate SQL queries before execution",
    memory_type="rule",
    importance=0.95,
    tags=["security"]
)
```

### 场景 3：对话上下文追踪
```python
response = await claude_service.chat(
    messages=[{"role": "user", "content": "..."}],
    conversation_id="conv_123",
    use_memory=True  # 自动注入相关记忆
)
```

详见：[MEMORI_INTEGRATION_GUIDE.md - 使用场景](./docs/tools/MEMORI/MEMORI_INTEGRATION_GUIDE.md#使用场景)

---

## 🔍 代码位置快速导引

### 配置管理
- **文件**: `backend/src/memory/config.py`
- **类**: `MemoriConfig`
- **全局实例**: `memory_config`
- **说明**: 管理 Memori 和 Claude 的所有配置参数

### 内存管理
- **文件**: `backend/src/memory/manager.py`
- **类**: `MemoryManager`
- **全局方法**: `get_memory_manager()`
- **功能**: 记忆 CRUD、搜索、统计、清理

### Claude 集成
- **文件**: `backend/src/services/claude_integration.py`
- **类**: `ClaudeIntegrationService`
- **全局方法**: `get_claude_service()`
- **功能**: Claude 调用、记忆注入、对话追踪

### API 端点
- **文件**: `backend/src/api/memory.py`
- **路由**: `router` (前缀: `/api/memory`)
- **端点**: 8 个完整的 CRUD + Claude 端点
- **验证**: 使用 Pydantic 模型

### 主应用入口
- **文件**: `backend/src/main.py`
- **更新内容**: 在 lifespan 中初始化 Memori 和 Claude 服务
- **路由集成**: 包含 `memory.router`

### 数据库迁移
- **文件**: `backend/migrations/versions/002_add_memori_memory_tables.py`
- **表**: memories, memory_relationships, conversations, memory_search_index, memory_stats
- **索引**: 完整的查询优化索引

---

## 📊 系统架构图

```
┌─────────────────────────────────────────┐
│         FastAPI Application             │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────┐  ┌─────────────────┐ │
│  │ Memory API   │  │ Claude Endpoints│ │
│  │ /api/memory  │  │ /api/memory/... │ │
│  └──────┬───────┘  └────────┬────────┘ │
│         │                   │           │
│  ┌──────▼───────────────────▼────────┐  │
│  │  Claude Integration Service       │  │
│  │  - Message routing                │  │
│  │  - Memory context injection       │  │
│  │  - Conversation management        │  │
│  └──────┬─────────────────┬──────────┘  │
│         │                 │              │
│  ┌──────▼───┐  ┌─────────▼────────────┐ │
│  │ Anthropic │  │  Memory Manager      │ │
│  │  Claude   │  │  (Memori wrapper)    │ │
│  │   API     │  │  - CRUD operations   │ │
│  │           │  │  - Search & retrieve │ │
│  │           │  │  - Statistics        │ │
│  └──────┬────┘  └─────────┬────────────┘ │
└─────────┼──────────────────┼──────────────┘
          │                  │
┌─────────▼──────────────────▼──────────────┐
│         Database Layer                    │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────────┐                  │
│  │ Memory Database  │                  │
│  │ PostgreSQL/SQLite                  │
│  │                  │                  │
│  │ - memories       │                  │
│  │ - relationships  │                  │
│  │ - conversations  │                  │
│  │ - search_index   │                  │
│  │ - stats          │                  │
│  └──────────────────┘                  │
│                                         │
└─────────────────────────────────────────┘
```

---

## 🛠️ 环境变量参考

### 必需变量
```env
ANTHROPIC_API_KEY=sk-...              # Claude API 密钥（必需）
```

### Memori 配置
```env
MEMORI_ENABLED=true                   # 启用/禁用
MEMORI_DB_TYPE=sqlite                 # sqlite / postgresql / mysql
MEMORI_SQLITE_PATH=./memori.db        # SQLite 文件路径
MEMORI_CONSCIOUS_INGEST=true          # 持久化上下文注入
MEMORI_AUTO_INGEST=true               # 动态上下文注入
MEMORI_ENABLE_SEMANTIC_SEARCH=true    # 语义搜索
MEMORI_MAX_MEMORY_ITEMS=1000          # 最大记忆数
MEMORI_MEMORY_RETENTION_DAYS=90       # 保留天数
```

### PostgreSQL 配置（生产推荐）
```env
MEMORI_DB_HOST=localhost
MEMORI_DB_PORT=5432
MEMORI_DB_NAME=memori_memory
MEMORI_DB_USER=postgres
MEMORI_DB_PASSWORD=...
```

### 性能和监控
```env
MEMORI_CACHE_TTL_SECONDS=300          # 缓存时间
MEMORI_ENABLE_CACHING=true            # 启用缓存
MEMORI_BATCH_SIZE=32                  # 批处理大小
MEMORI_ENABLE_MONITORING=true         # 启用监控
MEMORI_LOG_LEVEL=INFO                 # 日志级别
```

详见：[MEMORI_QUICKSTART.md - 环境变量参考](./docs/tools/MEMORI/MEMORI_QUICKSTART.md#环境变量参考)

---

## 📈 监控 KPI

定期监控以下指标：

| 指标 | 来源 | 说明 |
|------|------|------|
| **总记忆数** | `/api/memory/stats` | 应稳定增长，不无限增长 |
| **数据库大小** | `/api/memory/stats` | 监控磁盘使用情况 |
| **搜索延迟** | 日志/监控 | 应 < 100ms |
| **Claude 响应时间** | 日志/监控 | 含记忆注入应 < 500ms |
| **缓存命中率** | 监控 | 更高更好 |

---

## ❓ 常见问题

**Q: Memori 需要额外的外部服务吗？**
A: 不需要。使用标准 SQL 数据库（SQLite、PostgreSQL）存储。

**Q: 如何在开发和生产环境间切换存储？**
A: 修改 `.env` 中的 `MEMORI_DB_TYPE` 即可。

**Q: 记忆会自动过期吗？**
A: 可以配置 `MEMORI_MEMORY_RETENTION_DAYS` 或手动调用 `clear_memories()`。

**Q: 如何处理多个应用实例的记忆共享？**
A: 使用 PostgreSQL 作为共享存储，不要使用 SQLite。

**Q: 记忆数据有隐私风险吗？**
A: 不要存储 PII 数据，定期清理，启用多租户隔离。

详见：[MEMORI_QUICKSTART.md - 常见问题](./docs/tools/MEMORI/MEMORI_QUICKSTART.md#常见问题)

---

## 🧪 测试和示例

### 运行完整示例
```bash
cd backend
python examples/memori_integration_example.py
```

### 运行单元测试
```bash
cd backend
pytest tests/test_memory_integration.py -v
```

### 获取测试覆盖率
```bash
pytest tests/test_memory_integration.py --cov=src
```

---

## 📋 部署清单

### ✅ 开发环境
- [ ] 配置 `.env` 文件
- [ ] 运行 `poetry install`
- [ ] 运行 `alembic upgrade head`
- [ ] 启动应用 `python -m src.main`
- [ ] 测试 API 端点

### ⏳ 测试环境
- [ ] 设置 PostgreSQL
- [ ] 运行完整测试套件
- [ ] 验证 Claude API 集成
- [ ] 检查错误处理

### 🚀 生产环境
- [ ] 使用 PostgreSQL
- [ ] 启用监控和日志
- [ ] 实施备份策略
- [ ] 设置内存清理任务
- [ ] 配置性能指标收集

详见：[MEMORI_IMPLEMENTATION_SUMMARY.md - 部署检查清单](./docs/tools/MEMORI/MEMORI_IMPLEMENTATION_SUMMARY.md#部署检查清单)

---

## 📞 支持和资源

### 内部文档
- [快速开始指南](./docs/tools/MEMORI/MEMORI_QUICKSTART.md)
- [完整集成指南](./docs/tools/MEMORI/MEMORI_INTEGRATION_GUIDE.md)
- [实现总结和检查清单](./docs/tools/MEMORI/MEMORI_IMPLEMENTATION_SUMMARY.md)
- [代码示例](./backend/examples/memori_integration_example.py)
- [集成测试](./backend/tests/test_memory_integration.py)

### 外部资源
- [Memori GitHub](https://github.com/GibsonAI/Memori)
- [Memori 文档](https://memori.readthedocs.io/)
- [Anthropic Claude 文档](https://docs.anthropic.com/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)

---

## 📝 更新日志

### v1.0.0 (2024-11-12)
✅ Memori 与 Claude API 完整集成
- 4 个核心模块实现
- 8 个 API 端点
- 完整数据库支持
- 3000+ 行文档
- 生产级代码质量

---

## 🎓 推荐学习路径

### 🟢 初级（1-2 小时）
1. 阅读 [MEMORI_QUICKSTART.md](./docs/tools/MEMORI/MEMORI_QUICKSTART.md)
2. 运行示例代码 `examples/memori_integration_example.py`
3. 尝试 API 端点 (curl 命令)

### 🟡 中级（2-4 小时）
1. 阅读 [MEMORI_INTEGRATION_GUIDE.md](./docs/tools/MEMORI/MEMORI_INTEGRATION_GUIDE.md)
2. 研究核心模块源代码
3. 编写自己的测试
4. 集成到业务逻辑

### 🔴 高级（4+ 小时）
1. 深入学习架构设计
2. 优化性能和监控
3. 扩展功能（如向量搜索）
4. 实施生产级部署

---

**最后更新**: 2024-11-12
**状态**: 生产就绪 ✅
**维护者**: 云开发团队
