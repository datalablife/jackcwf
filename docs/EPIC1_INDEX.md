# Epic 1 - 文档导航与快速参考

**项目**: LangChain v1.0 AI Conversation System
**阶段**: Epic 1 - 后端基础设施（Story 1.1, 1.2, 1.3）
**状态**: 架构设计完成，待实现
**生成日期**: 2025-11-17

---

## 文档结构

### 核心设计文档

```
📚 Epic 1 文档体系
├── 📄 EPIC1_SUMMARY.md [✓ START HERE]
│   └── 项目概览、快速开始、时间线
│
├── 📋 EPIC1_ARCHITECTURE_DESIGN.md [详细设计]
│   ├── 执行摘要与架构审查
│   ├── Story 1.1: 数据库设计与迁移
│   ├── Story 1.2: 异步存储库实现
│   ├── Story 1.3: API 框架搭建
│   ├── LangChain 1.0 最佳实践
│   ├── 性能优化策略
│   └── 风险与缓解
│
├── 🛠️ EPIC1_IMPLEMENTATION_GUIDE.md [实现指南]
│   ├── Task 1.3.1: FastAPI 应用初始化
│   ├── Task 1.3.2: 改进的依赖注入
│   ├── Task 1.3.3: 文档和 OpenAPI 配置
│   ├── LangChain 集成
│   ├── 性能基准与测试
│   └── 风险缓解策略
│
└── 🚀 EPIC1_IMPLEMENTATION_ROADMAP.md [路线图]
    ├── Phase 1: 基础设施 (Week 1-2)
    ├── Phase 2: 存储库 (Week 2-3)
    ├── Phase 3: API 层 (Week 3-4)
    ├── Phase 4: 优化 (Week 4-5)
    ├── 代码参考实现
    └── 测试和部署清单
```

---

## 快速导航

### 按角色查找

#### 👤 项目经理 / 产品负责人

**推荐阅读**:
1. EPIC1_SUMMARY.md - 项目概览 (5分钟)
2. EPIC1_IMPLEMENTATION_ROADMAP.md - 时间线和里程碑 (10分钟)

**关键信息**:
- 估计工期: 5周
- 开发工作量: 3-4名工程师
- 关键风险: 数据库性能、连接泄漏
- 交付物: 完整后端基础设施

#### 👨‍💻 后端工程师 / 架构师

**推荐阅读** (按顺序):
1. EPIC1_SUMMARY.md - 快速了解 (10分钟)
2. EPIC1_ARCHITECTURE_DESIGN.md - 深入架构 (45分钟)
3. EPIC1_IMPLEMENTATION_GUIDE.md - 技术细节 (60分钟)
4. EPIC1_IMPLEMENTATION_ROADMAP.md - 实现计划 (30分钟)

**关键章节**:
- 架构审查 → 了解现状
- Story 1.1 → SQL Schema 设计
- Story 1.2 → Repository 框架
- BaseRepository 增强 → 事务管理
- LangChain 1.0 最佳实践 → 中间件集成

#### 🔧 DevOps / 基础设施

**推荐阅读**:
1. EPIC1_SUMMARY.md - 部署检查清单 (10分钟)
2. EPIC1_ARCHITECTURE_DESIGN.md - 性能优化章节 (20分钟)
3. EPIC1_IMPLEMENTATION_ROADMAP.md - Phase 4 优化章节 (15分钟)

**关键信息**:
- 数据库需求: PostgreSQL 12+, pgvector
- 应用需求: Python 3.12, AsyncIO
- 监控: 日志、指标、告警
- 部署: 容器化、健康检查、灰度发布

#### 🧪 QA / 测试工程师

**推荐阅读**:
1. EPIC1_IMPLEMENTATION_ROADMAP.md - 测试覆盖清单 (15分钟)
2. EPIC1_ARCHITECTURE_DESIGN.md - 性能基准 (20分钟)
3. 代码参考中的测试脚本 (30分钟)

**关键指标**:
- 单元测试覆盖: > 80%
- API 响应时间 P99: < 200ms
- 数据库查询 P99: < 100ms
- 向量搜索 P99: ≤ 200ms

---

## 关键文件清单

### 新增文件

| 文件路径 | 大小 | 优先级 | 说明 |
|---------|------|--------|------|
| `src/db/migrations_advanced.py` | 200行 | 高 | 高级迁移管理 |
| `src/exceptions.py` | 100行 | 高 | 异常分类系统 |
| `src/cache/redis_cache.py` | 150行 | 中 | 缓存集成 |
| `src/api/dependencies.py` | 100行 | 中 | 依赖注入 |
| `src/utils/logging_config.py` | 100行 | 中 | 日志配置 |

### 修改文件

| 文件路径 | 变更量 | 优先级 | 说明 |
|---------|--------|--------|------|
| `src/db/config.py` | +30 | 中 | 增强连接配置 |
| `src/db/base.py` | +20 | 低 | 事件监听器 |
| `src/repositories/base.py` | +200 | 高 | 事务和重试 |
| `src/repositories/conversation.py` | +50 | 中 | 统计分析 |
| `src/repositories/message.py` | +100 | 中 | Token 管理 |
| `src/main.py` | +100 | 中 | 应用增强 |
| `src/api/conversation_routes.py` | +50 | 低 | 依赖注入改进 |

---

## 实现路线图

### Timeline 概览

```
Week 1-2: 基础设施准备
  ├─ Day 1-2: 迁移系统完善 (BaselineR)
  ├─ Day 3-5: BaseRepository 增强
  ├─ Day 6-10: 异常处理系统
  └─ 交付: 完整数据库架构

Week 2-3: 存储库实现
  ├─ 完整 Repository 类集合
  ├─ 单元测试套件
  ├─ 性能基准报告
  └─ 交付: 经过充分测试的存储库

Week 3-4: API 层
  ├─ FastAPI 应用增强
  ├─ 依赖注入优化
  ├─ 完整路由实现
  └─ 交付: 完整 REST API

Week 4-5: 优化和监控
  ├─ 缓存集成
  ├─ 日志和监控
  ├─ 性能优化
  └─ 交付: 生产就绪系统
```

### 关键里程碑

| 里程碑 | 时间 | 条件 | 交付物 |
|--------|------|------|--------|
| M1: 基础设施就绪 | Week 2 | 所有DB迁移完成 | 数据库 + BaseRepo |
| M2: 存储库完成 | Week 3 | Test Coverage > 80% | 所有 Repository 类 |
| M3: API 就绪 | Week 4 | 所有端点测试通过 | 完整 REST API |
| M4: 生产就绪 | Week 5 | 性能基准达标 | 生产环境可部署 |

---

## 按照 Story 的文档映射

### Story 1.1: 数据库设计与迁移

**对应文档章节**:
- EPIC1_ARCHITECTURE_DESIGN.md → "Story 1.1 - 数据库设计与迁移"
  - Task 1.1.1: Conversations 表设计
  - Task 1.1.2: Messages 表设计
  - Task 1.1.3: Documents 和 Embeddings 表
  - Task 1.1.4: 索引优化策略
  - Task 1.1.5: 分区策略与维护

**关键代码**:
```python
# src/db/migrations_advanced.py
class AdvancedMigrationManager:
    async def run_all_migrations()
    async def _create_indices()
    async def _setup_embeddings_partitions()
```

**性能目标**:
| 操作 | 目标 | P99 |
|------|------|-----|
| 向量搜索 | ≤ 200ms | < 250ms |
| 批量插入 | ≤ 100ms | < 150ms |

---

### Story 1.2: 异步存储库实现

**对应文档章节**:
- EPIC1_ARCHITECTURE_DESIGN.md → "Story 1.2 - 异步存储库实现"
- EPIC1_IMPLEMENTATION_GUIDE.md → "LangChain 1.0 最佳实践"

**关键代码**:
```python
# src/repositories/base.py
class BaseRepository(Generic[T]):
    async def create()
    async def bulk_upsert()
    async def with_transaction()
    async def with_savepoint()

# src/repositories/conversation.py
class ConversationRepository(BaseRepository[ConversationORM]):
    async def get_user_conversations()
    async def search_by_title()
    async def soft_delete()

# 其他 Repository 类...
```

**测试覆盖**:
- ConversationRepository: CRUD + 搜索 + 软删除
- MessageRepository: 角色过滤 + Token 追踪
- EmbeddingRepository: 向量搜索 + 性能
- 性能基准: 所有操作

---

### Story 1.3: API 框架搭建

**对应文档章节**:
- EPIC1_IMPLEMENTATION_GUIDE.md → "Story 1.3 - API 框架搭建"
  - Task 1.3.1: FastAPI 应用初始化
  - Task 1.3.2: 依赖注入优化
  - Task 1.3.3: 文档配置

**关键代码**:
```python
# src/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动/关闭管理

@app.middleware("http")
async def add_request_id_middleware()

# src/api/dependencies.py
RequestIdType = Annotated[str, Depends(get_request_id)]
UserIdType = Annotated[str, Depends(get_user_id)]
ConversationServiceType = Annotated[ConversationService, ...]

# src/api/conversation_routes.py (改进)
@router.post("")
async def create_conversation(
    request_id: RequestIdType,
    user_id: UserIdType,
    service: ConversationServiceType,
    request_data: CreateConversationRequest,
):
    """简洁的函数签名"""
```

**API 端点清单**:
- POST /api/v1/conversations → 创建
- GET /api/v1/conversations → 列表
- GET /api/v1/conversations/{id} → 详情
- PUT /api/v1/conversations/{id} → 更新
- DELETE /api/v1/conversations/{id} → 删除
- GET /api/v1/conversations/{id}/messages → 消息历史

---

## 代码快速参考

### 1. 错误处理模式

```python
# src/exceptions.py
from src.exceptions import (
    RepositoryException,
    DuplicateRecordError,
    RecordNotFoundError,
    TransactionError,
)

try:
    await repository.create(...)
except IntegrityError as e:
    raise DuplicateRecordError() from e
except Exception as e:
    raise TransactionError("Failed to create") from e
```

### 2. 事务管理模式

```python
# 简单事务
async with session.begin():
    result = await repo.create(...)

# 嵌套事务（保存点）
async with session.begin_nested():
    result = await repo.create(...)
```

### 3. 批量操作模式

```python
# Bulk Create
instances = [ConversationORM(...), ...]
await repo.bulk_create(instances)

# Bulk Upsert
await repo.bulk_upsert(
    instances=[{...}, ...],
    index_elements=['id']
)
```

### 4. 查询模式

```python
# 简单查询
conversation = await repo.get_by(user_id=user_id, is_deleted=False)

# 列表查询
conversations = await repo.list(
    skip=0,
    limit=10,
    order_by="-created_at",
    user_id=user_id
)

# 搜索
results = await repo.search_by_title(user_id, "keyword")
```

### 5. 向量搜索模式

```python
# 生成查询向量
query_embedding = generate_embedding("query text")

# 搜索相似向量
results = await repo.search_similar(
    query_embedding,
    user_id=user_id,
    limit=5,
    threshold=0.7
)
```

---

## 常见问题 (FAQ)

### 架构相关

**Q: 为什么选择 PostgreSQL + pgvector？**
A: 参见 EPIC1_ARCHITECTURE_DESIGN.md 的架构审查章节。主要优点：
- ACID 事务保证
- pgvector 原生支持向量搜索
- HNSW 索引性能优异
- 完整的 JSON 支持

**Q: HNSW 参数应该如何调整？**
A: 参见 EPIC1_ARCHITECTURE_DESIGN.md 的"向量搜索查询示例"章节：
- m=16: 向量密度和搜索时间的权衡
- ef_construction=64: 构造质量参数
- 对于 1M+ 向量，考虑 m=8, ef_construction=32

---

### 实现相关

**Q: BaseRepository 的重试机制如何工作？**
A: 参见 EPIC1_IMPLEMENTATION_GUIDE.md 中的 @retry_on_operational_error 装饰器实现：
- 最多重试 3 次
- 指数退避策略
- 仅重试 OperationalError（临时性错误）

**Q: 如何处理数据库连接泄漏？**
A: 参见 EPIC1_ARCHITECTURE_DESIGN.md 的"风险缓解"章节：
- 使用 async with 上下文管理器
- 配置连接池超时
- 定期监控连接状态

---

### 性能相关

**Q: 如何优化向量搜索性能？**
A: 参见 EPIC1_ARCHITECTURE_DESIGN.md 的"性能优化"章节：
1. HNSW 索引参数调优
2. 分区策略（按月）
3. 定期重建索引
4. 查询缓存

**Q: 缓存应该如何集成？**
A: 参见 EPIC1_IMPLEMENTATION_GUIDE.md 的"缓存策略"章节：
- Redis 可选集成
- TTL 设置为 300s
- 分层缓存：应用层 + 数据库层

---

### 测试相关

**Q: 如何运行性能测试？**
A: 参见 EPIC1_IMPLEMENTATION_ROADMAP.md 的测试部分：
```bash
pytest tests/test_repository_performance.py -v
pytest tests/test_api_integration.py -v
```

**Q: 测试覆盖率应该达到多少？**
A: 参见 EPIC1_IMPLEMENTATION_ROADMAP.md 的测试覆盖清单：
- 总体: > 80%
- Repository: > 95%
- Service: > 85%
- API: > 75%

---

## 获取帮助

### 文档查阅

1. **架构问题** → EPIC1_ARCHITECTURE_DESIGN.md
2. **实现问题** → EPIC1_IMPLEMENTATION_GUIDE.md
3. **时间表问题** → EPIC1_IMPLEMENTATION_ROADMAP.md
4. **快速查询** → 本文档 (EPIC1_INDEX.md)

### 代码参考

- 所有代码示例都在对应文档章节中
- 关键代码在 EPIC1_IMPLEMENTATION_ROADMAP.md 的"代码参考实现"章节

### 性能基准

- 性能目标见 EPIC1_ARCHITECTURE_DESIGN.md 的"性能优化"章节
- 测试方法见 EPIC1_IMPLEMENTATION_ROADMAP.md

---

## 版本历史

| 版本 | 日期 | 作者 | 变更 |
|------|------|------|------|
| 1.0 | 2025-11-17 | LangChain Backend Architect | 初始版本 |

---

## 相关资源

- **项目根目录**: `/mnt/d/工作区/云开发/working/`
- **源代码**: `src/`
- **测试代码**: `tests/`
- **文档目录**: `docs/`

---

**最后更新**: 2025-11-17
**状态**: Epic 1 架构设计完成，准备开始实现
**下一步**: 按照 EPIC1_IMPLEMENTATION_ROADMAP.md 开始 Week 1 的工作

---

**提示**: 将本文档作为导航枢纽，根据需要跳转到相应的详细文档进行深入查阅。
