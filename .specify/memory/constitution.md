<!--
SYNC IMPACT REPORT
==================
Version Change: v0.0.0 → v1.0.0 (MAJOR: Initial constitution ratified)
Ratification Date: 2025-11-16
Last Amendment: 2025-11-16

New Principles Added:
- AI-First Architecture (LangChain v1.0 Foundation)
- Modular Middleware Framework
- Vector Storage Excellence (PostgreSQL + pgvector)
- Type Safety and Validation
- Async-First Implementation
- Semantic Code Organization
- Production Readiness
- Observability and Monitoring

Templates Requiring Update:
- ✅ .specify/templates/plan-template.md (PENDING)
- ✅ .specify/templates/spec-template.md (PENDING)
- ✅ .specify/templates/tasks-template.md (PENDING)
- ✅ .specify/templates/commands/*.md (PENDING)

Follow-up Actions:
- Create template files (.specify/templates/*.md)
- Configure command shortcuts (.specify/templates/commands/*.md)
- Establish monitoring dashboards and KPI tracking
- Set up CI/CD pipeline validation
-->

# 云开发 LangChain v1.0 RAG AI Agent 项目宪法

## 项目概览

**项目名称**: LangChain v1.0 RAG AI Agent 对话系统
**版本**: v1.0.0
**状态**: 生产开发中
**生效日期**: 2025-11-16

本宪法定义了项目的核心原则、技术约束、开发工作流和治理规则，确保项目在高可用性、可维护性和性能的指导下快速迭代。

## 核心原则

### 1. AI-First 架构（基于 LangChain v1.0）

**非协商规则**:
- 所有 AI 功能必须使用 LangChain v1.0 的 `create_agent()` API 作为基础，不使用 v0.x 模式
- 必须实现中间件系统（Middleware）支持动态提示、上下文工程和应答守卫
- 必须支持 LangGraph 框架提供的持久化对话、实时流和人类介入工作流
- 所有 LLM 调用必须使用统一的 `content_blocks` 属性支持多个提供商（Anthropic、OpenAI、Google、AWS、Ollama）

**设计原则**:
- Agent 模式是解决所有多步骤 AI 问题的首选方案
- 结构化输出优于多轮推理，以降低成本并提高确定性
- 工具定义必须清晰、原子性和可重用

**执行清单**:
- [ ] 所有对话功能使用 `create_agent()` 初始化
- [ ] 中间件在关键点实现（认证、日志、速率限制）
- [ ] LangGraph 用于复杂工作流（RAG、审批流、重新生成）

---

### 2. 模块化中间件框架

**非协商规则**:
- 中间件必须遵循洋葱模型（Onion Pattern），按顺序：请求验证 → 上下文注入 → 业务逻辑 → 输出转换 → 监控日志
- 每个中间件层必须实现 `async def __call__(request, call_next)` 签名
- 中间件必须支持条件启用（通过环境变量或功能标志控制）
- 错误必须优雅地传播，不得吞掉异常

**关键中间件**:
1. **认证中间件** - 验证 API 密钥和用户身份
2. **记忆注入中间件** - 从向量数据库检索相关上下文
3. **内容审核中间件** - 防止有害输入（安全第一）
4. **响应结构化中间件** - 统一 JSON 响应格式
5. **审计日志中间件** - 记录所有对话和决策

**执行清单**:
- [ ] 中间件按优先级排序
- [ ] 所有异常类型都被记录和恢复
- [ ] 中间件测试覆盖率 ≥ 90%

---

### 3. 向量存储卓越性（PostgreSQL + pgvector）

**非协商规则**:
- 向量存储必须使用 PostgreSQL 15+ 的 pgvector 扩展（Lantern Suite）
- 所有向量必须规范化为 L2 距离，维度统一为 1536（OpenAI Ada-003 标准）
- 必须为以下字段建立索引：`content`、`metadata`、`created_at`、`source`，使用 HNSW 算法优化距离查询
- 向量搜索超时必须 ≤ 200ms（P99）；批量插入 ≤ 100ms per 1000 vectors
- 必须实现软删除（使用 `is_deleted` 标志），保留审计追踪

**数据库约束**:
- 向量表架构必须包括：`id (UUID)`、`content (TEXT)`、`embedding (vector[1536])`、`metadata (JSONB)`、`source (VARCHAR)`、`created_at (TIMESTAMP)`、`updated_at (TIMESTAMP)`、`is_deleted (BOOLEAN)`
- 必须实现分区策略，按 `created_at` 按月分区（>1M 记录时）
- 必须为每个表配置备份和 WAL 归档

**执行清单**:
- [ ] pgvector 扩展已安装并配置
- [ ] 所有向量维度统一为 1536
- [ ] 距离查询性能监控每日进行
- [ ] 月度备份验证和恢复演练
- [ ] 向量表已按时间分区

---

### 4. 类型安全和验证

**非协商规则**:
- 所有 Python 代码必须使用 Python 3.14+ 并启用 `from __future__ import annotations`
- 所有函数参数和返回值必须有完整的类型注解（使用 Pydantic v2 模型）
- 必须在运行时验证所有外部输入（使用 Pydantic 的 `.model_validate()`）
- 禁止使用 `typing.Any`；使用具体的 Union 或 Generic 类型
- 禁止使用字符串形式的类型注解（延迟评估）；使用 `from __future__ import annotations`

**Pydantic 模型规则**:
- 所有数据传输对象（DTO）必须继承 `BaseModel`
- 必须使用 `ConfigDict(json_schema_extra=...)` 生成 OpenAPI 文档
- 必须为字段使用描述字符串（用于文档和验证错误消息）
- 必须为敏感字段使用 `Field(exclude=True)` 或 `SecretStr`

**执行清单**:
- [ ] 所有文件顶部包含 `from __future__ import annotations`
- [ ] 运行 `mypy --strict` 通过率 = 100%
- [ ] 所有 API 端点返回值包含 OpenAPI 类型声明

---

### 5. 异步优先实现

**非协商规则**:
- 所有 I/O 操作（数据库、API、文件）必须使用 `async/await` 语法
- 禁止在异步函数中使用同步库（使用 `asyncio.to_thread()` 包装同步调用）
- 所有数据库连接必须使用 `asyncpg`（异步 PostgreSQL 驱动）或 `SQLAlchemy async`
- 并发限制必须通过 `asyncio.Semaphore` 实现（max_concurrent = 10 by default）
- 必须使用 `asyncio.TaskGroup` 管理多个并发任务，确保异常传播

**性能约束**:
- 单次请求不超过 100 个未解析的任务（防止内存泄漏）
- 所有任务必须有明确的超时（MAX_TIMEOUT = 30 秒）
- 后台任务必须使用消息队列（Celery + Redis）处理，不阻塞 HTTP 响应

**执行清单**:
- [ ] 所有数据库调用使用 `async` 函数
- [ ] 并发测试覆盖 ≥ 100 个并发请求
- [ ] 超时错误被正确捕获和记录

---

### 6. 语义代码组织

**非协商规则**:
- 代码必须按功能域分层：`api` → `services` → `repositories` → `models` → `infrastructure`
- 每层的职责清晰划分，不允许跨越（逐层依赖，禁止循环依赖）
- 命名必须反映意图（方法名 = 动词 + 名词，如 `fetch_embeddings_by_query` ）
- 禁止使用通用命名（`data`、`result`、`temp`）；必须使用特定域术语

**文件组织**:
```
src/
├── api/              # FastAPI 路由（RESTful 端点）
│   ├── v1/
│   │   ├── conversations.py
│   │   ├── embeddings.py
│   │   ├── agents.py
│   │   └── documents.py
├── services/         # 业务逻辑（无框架依赖）
│   ├── agent_service.py
│   ├── embedding_service.py
│   ├── conversation_service.py
│   └── rag_service.py
├── repositories/     # 数据访问层（数据库交互）
│   ├── vector_repository.py
│   ├── conversation_repository.py
│   └── document_repository.py
├── models/           # Pydantic 数据模型和 ORM
│   ├── domain.py     # 业务领域模型
│   ├── dto.py        # 数据传输对象
│   └── orm.py        # SQLAlchemy ORM 模型
└── infrastructure/   # 系统层（配置、日志、监控）
    ├── database.py
    ├── config.py
    ├── logger.py
    └── monitoring.py
```

**执行清单**:
- [ ] 所有文件按层级组织，无循环依赖
- [ ] 每个模块有明确的 `__init__.py` 定义公共 API

---

### 7. 生产就绪性

**非协商规则**:
- 所有新代码必须伴随单元测试（测试覆盖率 ≥ 80%），并通过集成测试
- 必须实现优雅关闭（Graceful Shutdown）：在收到 SIGTERM 时，完成当前请求后关闭（超时 30 秒）
- 必须实现健康检查端点 (`GET /health`)，检查数据库连接、向量存储和外部 API
- 必须实现限流（Rate Limiting）：API 端点 ≤ 100 req/min per IP；并发任务 ≤ 10
- 所有密钥和敏感信息必须从环境变量加载（使用 `python-dotenv`），禁止硬编码

**部署约束**:
- 容器镜像必须使用 `python:3.14-slim` 作为基础镜像（最小化攻击面）
- 必须实现蓝绿部署或金丝雀部署，零停机时间升级
- 所有环境（开发、测试、生产）必须相同的依赖版本（使用 uv.lock）
- 生产环境必须启用所有监控、日志和告警

**执行清单**:
- [ ] 单元测试覆盖率报告每次提交
- [ ] 健康检查端点响应 ≤ 500ms
- [ ] 部署前通过自动化测试（单元、集成、端到端）
- [ ] 环境变量文档完整，包括所有密钥

---

### 8. 可观测性和监控

**非协商规则**:
- 所有关键操作必须记录日志（DEBUG、INFO、WARNING、ERROR 四个级别）
- 日志必须结构化为 JSON 格式，包含：`timestamp`、`level`、`module`、`function`、`message`、`context`（用户 ID、请求 ID 等）
- 必须追踪每个请求的唯一 ID（`X-Request-ID` header），贯穿整个调用链
- 必须实现分布式追踪（Distributed Tracing），使用 OpenTelemetry 标准
- 必须收集 4 个黄金指标：延迟、流量、错误率、饱和度

**监控指标**:
1. **API 性能**: 平均响应时间、P95/P99 延迟、吞吐量（req/s）
2. **向量搜索**: 查询延迟、索引大小、缓存命中率
3. **AI 质量**: 平均回复时间、用户满意度评分、错误率（无效响应）
4. **系统**: CPU/内存使用率、数据库连接池状态、错误日志频率

**告警规则**:
- 响应时间 P99 > 1000ms → 警告
- 错误率 > 1% → 严重告警
- 数据库连接池已满 → 严重告警
- 向量搜索超时 > 5% → 警告

**执行清单**:
- [ ] 日志库已配置（如 structlog 或 python-json-logger）
- [ ] 所有请求包含唯一追踪 ID
- [ ] OpenTelemetry SDK 已集成到 FastAPI
- [ ] 监控仪表板已配置（Grafana 或 Datadog）

---

## 技术栈约束

### 后端
- **框架**: FastAPI (最新版本，支持 Python 3.14)
- **数据库**: PostgreSQL 15+ 主副本复制
- **向量存储**: pgvector (Lanterns Suite)
- **ORM**: SQLAlchemy 2.0+ (async 支持)
- **AI 框架**: LangChain v1.0 (create_agent, LangGraph)
- **LLM 提供商**: OpenAI API (GPT-4o)、Anthropic Claude 3.5 Sonnet、Google Gemini、AWS Bedrock、本地 Ollama
- **缓存**: Redis (对话、嵌入缓存)
- **任务队列**: Celery + Redis (后台任务)
- **依赖管理**: uv (快速 Python 包管理)

### 前端
- **框架**: React 19 + TypeScript 5.7
- **构建工具**: Vite
- **UI 库**: Tailark (Tailwind CSS 组件)
- **状态管理**: TanStack Query (数据获取) + Zustand (全局状态)
- **表单**: React Hook Form + Zod (客户端验证)
- **实时通信**: WebSocket (基于 Socket.IO)

### DevOps
- **容器化**: Docker
- **部署平台**: Coolify (自托管)
- **CI/CD**: GitHub Actions
- **监控**: Prometheus + Grafana 或 Datadog
- **日志**: ELK Stack 或 Grafana Loki
- **备份**: PostgreSQL pg_dump (每日)

---

## 开发工作流

### 功能开发流程

1. **需求分析** - 使用 `/speckit.specify` 命令生成规范（spec.md）
2. **实现规划** - 使用 `/speckit.plan` 命令生成设计文档（plan.md）
3. **任务分解** - 使用 `/speckit.tasks` 命令生成待办事项（tasks.md）
4. **代码实现** - 按优先级依次完成任务，遵循类型安全和异步优先原则
5. **测试验证** - 单元测试 ≥ 80%，集成测试 ≥ 60%
6. **代码审查** - 使用 CrewAI 系统自动审查（参见 `code_review_crew/main.py`）
7. **性能优化** - 基于监控数据优化关键路径（向量搜索、API 响应）
8. **发布部署** - 通过 CI/CD 流程自动化部署到 Coolify

### Git 工作流

**分支策略**:
- `main` - 生产就绪代码，受保护，仅接受 PR
- `develop` - 集成分支，接受功能和修复 PR
- `feature/*` - 功能分支（从 `develop` 创建）
- `bugfix/*` - 修复分支（从 `develop` 创建）
- `hotfix/*` - 紧急修复（从 `main` 创建）

**提交规范** (Conventional Commits):
- `feat: 添加新功能`
- `fix: 修复 bug`
- `docs: 文档更新`
- `refactor: 代码重构`
- `perf: 性能优化`
- `test: 测试相关`
- `chore: 构建、依赖等`

**审查标准**:
- 至少一个 maintainer 同意
- CI/CD 所有检查通过（测试、linting、安全扫描）
- 代码覆盖率不降低

---

## 治理规则

### 版本管理

**语义版本号** (SemVer):
- MAJOR (X.0.0): 不兼容的 API 变更、原则移除/重新定义
- MINOR (X.Y.0): 新功能、新原则、向后兼容的增强
- PATCH (X.Y.Z): 错误修复、文档更新、非功能改进

**发布周期**:
- 新功能和修复在 `develop` 分支上积累
- 每周五进行一次 release 审查，确定是否发布新版本
- 紧急修复（P1 bug）直接发布为 patch 版本

### 原则修订流程

1. **提案阶段** - 在 GitHub Issues 中提出原则修改建议
2. **讨论阶段** - 邀请 maintainers 和贡献者评审（最少 3 天）
3. **投票阶段** - 超过 50% 的 maintainers 同意
4. **文档阶段** - 更新宪法、相关模板和运行指南
5. **公告阶段** - 在项目 README 和发布日志中公告

### 合规审查

- **频率**: 每月进行一次
- **范围**: 检查所有代码是否遵守宪法原则
- **工具**: 使用 `/speckit.analyze` 命令进行自动一致性检查
- **报告**: 生成合规报告，列出偏差和改进建议
- **处理**: 偏差必须在下一个迭代周期内修复

---

## 常见场景指南

### 场景 1: 实现新的 RAG 功能

**步骤**:
1. 使用 `/speckit.specify` 编写 RAG 功能规范
2. 确保遵守"向量存储卓越性"原则（pgvector、1536 维、HNSW 索引）
3. 使用 LangChain v1.0 的 `create_agent()` 构建 agent
4. 在中间件中注入记忆上下文（第 2 原则）
5. 添加监控指标（向量搜索延迟、缓存命中率）

**关键检查点**:
- [ ] 向量维度 = 1536
- [ ] 搜索延迟 ≤ 200ms (P99)
- [ ] 测试覆盖率 ≥ 80%
- [ ] 类型注解完整（mypy --strict 通过）

### 场景 2: 优化 API 性能

**步骤**:
1. 从监控数据识别瓶颈（Grafana 仪表板）
2. 根据"异步优先"原则（第 5 原则）进行异步化
3. 使用数据库索引优化查询
4. 实现缓存（Redis）减少重复查询
5. 通过 A/B 测试验证改进

**关键指标**:
- 响应时间 P99 从 X ms 降至 Y ms
- 吞吐量从 A req/s 提升至 B req/s
- 错误率 ≤ 1%

### 场景 3: 部署到生产环境

**步骤**:
1. 所有测试通过（单元、集成、端到端）
2. 环境变量配置完成（安全敏感信息）
3. 健康检查端点验证通过
4. 灾难恢复计划已审查
5. 通过金丝雀部署验证（5% 流量）
6. 全量部署

**生产检查清单**:
- [ ] 监控和告警已配置
- [ ] 日志收集和聚合正常
- [ ] 备份和恢复流程已验证
- [ ] 负载均衡和故障转移已测试
- [ ] 安全审计已完成

---

## 决策记录

### 为什么选择 LangChain v1.0?
- **优势**: 简化的 API (create_agent)、中间件系统、官方的 LangGraph 支持、多提供商兼容
- **替代方案**: Haystack (更复杂)、AutoGPT (实验性)、Langsmith (监控工具)
- **决策**: LangChain v1.0 是最成熟和灵活的框架

### 为什么使用 PostgreSQL + pgvector?
- **优势**: ACID 事务、强一致性、成熟的向量扩展、自托管（降低成本）
- **替代方案**: Pinecone (托管，高成本)、Weaviate (复杂)、Qdrant (较新，生态小)
- **决策**: 自托管 PostgreSQL 满足性能和成本的平衡

### 为什么采用异步优先架构?
- **优势**: 高并发支持、更少的内存开销、更好的响应时间
- **替代方案**: 同步 Flask (简单但不可扩展)、异步 Quart (相似)
- **决策**: FastAPI + asyncpg 是现代 Python 开发的标准

---

## 附录

### 附录 A: 环境变量参考

```bash
# LangChain 和 LLM 提供商
LANGCHAIN_API_KEY=sk-...
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...
GOOGLE_API_KEY=...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
OLLAMA_BASE_URL=http://localhost:11434

# 数据库
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/langchain_db
REDIS_URL=redis://localhost:6379/0

# 应用配置
ENVIRONMENT=production
LOG_LEVEL=INFO
MAX_CONCURRENT_TASKS=10
REQUEST_TIMEOUT_SECONDS=30

# 监控和日志
PROMETHEUS_ENABLED=true
OTEL_ENABLED=true
SENTRY_DSN=https://...
ELK_ENABLED=true
```

### 附录 B: 快速命令参考

```bash
# 开发
uv run reflex run                    # 启动开发服务器
uv run pytest                        # 运行测试
uv run mypy --strict src/            # 类型检查

# 部署
git push origin feature/branch        # 推送到 GitHub
# CI/CD 自动触发，部署到 Coolify

# 监控
# 访问 Grafana: https://monitoring.yourdomain.com
# 查看日志: ELK 或 Loki UI
```

---

**宪法版本**: v1.0.0
**生效日期**: 2025-11-16
**维护者**: 云开发团队
**最后修订**: 2025-11-16
**状态**: 生产就绪 ✅
