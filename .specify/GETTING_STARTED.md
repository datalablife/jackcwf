# 快速入门指南：项目宪法和规范系统

欢迎来到 **LangChain v1.0 RAG AI Agent 项目**。本指南将帮助您快速了解项目的治理框架和工作流程。

---

## 📖 5 分钟快速概览

### 项目宪法是什么?

项目宪法是一份正式文件，定义了 **8 个核心原则**，所有开发工作都必须遵守这些原则。它确保：
- ✅ 代码质量一致
- ✅ 架构清晰合理
- ✅ 性能目标明确
- ✅ 可观测性完善

### 8 个核心原则一览

| # | 原则 | 关键要求 |
|---|------|---------|
| 1 | 🤖 AI-First 架构 | LangChain v1.0 `create_agent()` + 中间件系统 |
| 2 | 🔧 模块化中间件 | 5 层中间件：认证、记忆、审核、结构化、日志 |
| 3 | 📊 向量存储卓越 | PostgreSQL + pgvector，维度 1536，搜索 ≤ 200ms |
| 4 | 🔒 类型安全 | Python 3.14 + Pydantic v2 + mypy --strict |
| 5 | ⚡ 异步优先 | 所有 I/O 使用 async/await，无阻塞操作 |
| 6 | 📚 语义组织 | 分层架构：api → services → repositories → models |
| 7 | 🚀 生产就绪 | 测试 ≥ 80%，优雅关闭，健康检查 |
| 8 | 📈 可观测性 | 结构化日志，分布式追踪，4 个黄金指标 |

---

## 🚀 开始你的第一个功能

### Step 1: 理解需求 (30 分钟)

阅读以下文件了解项目背景：

```bash
# 核心文件
cat .specify/memory/constitution.md          # 项目宪法（必读！）
cat .specify/README.md                       # 规范系统概览
```

### Step 2: 创建功能规范 (1 小时)

为新功能创建详细规范：

```bash
# 复制规范模板
cp .specify/templates/spec-template.md docs/features/my-feature-spec.md

# 编辑并填充内容（使用你喜欢的编辑器）
vim docs/features/my-feature-spec.md
```

**规范应该包含**:
- 用户故事和接受标准
- 数据模型 (Pydantic v2)
- API 端点定义
- 数据库架构 (PostgreSQL)
- 向量存储需求 (维度、索引、超时)
- 中间件需求 (认证、记忆注入等)
- 监控指标和告警
- 测试策略

### Step 3: 设计实现方案 (1.5 小时)

根据规范设计系统架构：

```bash
# 复制计划模板
cp .specify/templates/plan-template.md docs/features/my-feature-plan.md

# 编辑并创建架构文档
vim docs/features/my-feature-plan.md
```

**计划应该包含**:
- 系统整体架构图
- 中间件架构设计
- 数据库设计 (表、分区、索引)
- 后端项目结构和模块
- 前端项目结构
- 监控和可观测性设计
- 测试策略
- 部署计划

### Step 4: 分解为任务 (1 小时)

将计划分解为可执行的故事和任务：

```bash
# 复制任务模板
cp .specify/templates/tasks-template.md docs/features/my-feature-tasks.md

# 编辑并分解为故事和任务
vim docs/features/my-feature-tasks.md
```

**任务应该包含**:
- 按优先级分类的故事 (P0-P2)
- 具体任务和完成标准
- 技术约束和代码示例
- 依赖关系图
- 时间估算

### Step 5: 实现并审查 (开发周期)

根据任务列表实现代码：

```bash
# 遵守这些原则开发：
# 1. 所有函数都有类型注解 (mypy --strict 必须通过)
# 2. 所有 I/O 都使用 async/await
# 3. 所有 API 都有监控和日志记录
# 4. 所有功能都有单元测试 (≥ 80%)

# 实现后检查宪法合规性
/speckit.constitution-check backend/src/your_module.py

# 运行自动化测试
uv run pytest tests/

# 通过类型检查
uv run mypy --strict backend/src/
```

### Step 6: 部署到生产 (部署流程)

部署前的最终检查：

```bash
# 运行所有检查
uv run pytest                              # 测试通过
uv run mypy --strict backend/src/         # 类型检查通过
/speckit.constitution-check --detailed    # 宪法合规

# 提交代码
git add .
git commit -m "feat: add my-feature implementation"
git push origin feature/my-feature

# 通过 GitHub PR，等待 CI/CD 自动部署到 Coolify
```

---

## 📋 常见场景解答

### 场景 1: 我需要添加一个新的 API 端点

**步骤**:
1. 在规范中定义 API 契约 (spec-template.md)
2. 创建 Pydantic DTO 模型
3. 实现服务层和存储库层
4. 添加中间件拦截 (认证、日志)
5. 编写单元测试 (≥ 80% 覆盖)
6. 添加监控指标

**关键检查**:
- [ ] 所有参数都有类型注解
- [ ] 所有数据库操作都是异步的
- [ ] 关键操作都有日志记录
- [ ] mypy --strict 通过

### 场景 2: 我需要优化 API 性能

**步骤**:
1. 使用 Grafana 确认瓶颈
2. 检查数据库查询和索引
3. 实现缓存 (Redis) 或异步化
4. 添加性能监控
5. A/B 测试验证改进

**性能目标**:
- API 响应时间 P99 ≤ 500ms
- 向量搜索延迟 ≤ 200ms
- 错误率 ≤ 1%

### 场景 3: 我需要与向量数据库交互

**步骤**:
1. 使用 1536 维向量 (OpenAI Ada 标准)
2. 使用 HNSW 索引优化搜索
3. 搜索超时设定为 ≤ 200ms
4. 实现软删除机制
5. 添加审计追踪

**技术约束**:
- 维度必须 = 1536
- 距离指标 = cosine (L2 也可以)
- 索引类型 = HNSW
- 搜索必须异步

### 场景 4: 部署到生产失败

**故障排查**:
1. 检查所有环境变量是否已配置
2. 验证数据库连接是否正常
3. 确认向量索引已创建
4. 检查 Docker 镜像是否成功构建
5. 查看 Coolify 部署日志

**常见问题**:
- ❌ "ModuleNotFoundError" → 检查依赖是否安装 (`uv sync`)
- ❌ "Database connection failed" → 检查 DATABASE_URL 环境变量
- ❌ "Health check failed" → 增加初始延迟到 60 秒
- ❌ "pgvector not found" → 确保在 PostgreSQL 中运行 `CREATE EXTENSION pgvector`

---

## 📚 完整文档导航

### 必读文档

| 文档 | 用途 | 阅读时间 |
|------|------|---------|
| `.specify/memory/constitution.md` | 8 个核心原则和治理规则 | 45 分钟 |
| `.specify/README.md` | 规范系统快速参考 | 15 分钟 |
| `.specify/GETTING_STARTED.md` | 本文件 - 快速入门 | 10 分钟 |

### 参考模板

| 模板 | 何时使用 | 包含内容 |
|------|----------|---------|
| `spec-template.md` | 创建新功能规范 | 需求、模型、API、数据库 |
| `plan-template.md` | 设计实现方案 | 架构、中间件、监控设计 |
| `tasks-template.md` | 分解为任务 | 故事、任务、时间估算 |

### 外部参考

| 资源 | 链接 | 用途 |
|------|------|------|
| LangChain v1.0 | https://docs.langchain.com/oss/python/releases/langchain-v1 | Agent 和工具定义 |
| pgvector | https://github.com/pgvector/pgvector | 向量存储配置 |
| Tailark UI | https://tailark.com | 前端 UI 组件 |
| FastAPI | https://fastapi.tiangolo.com | API 框架文档 |
| SQLAlchemy Async | https://docs.sqlalchemy.org/en/20/ | 异步数据库操作 |

---

## 🔧 开发环境快速设置

### 1. 安装依赖

```bash
# 同步虚拟环境和依赖
uv sync

# 激活虚拟环境（可选）
source .venv/bin/activate
```

### 2. 配置数据库

```bash
# 加载 PostgreSQL 配置
source .postgres_config

# 测试连接
psql -h host.docker.internal -p 5432 -U jackcwf888 -d postgres
```

### 3. 启动开发服务器

```bash
# 运行前后端
uv run reflex run

# 或仅运行后端
uv run reflex run --backend-only
```

### 4. 运行测试

```bash
# 所有测试
uv run pytest

# 特定测试文件
uv run pytest tests/unit/test_my_feature.py

# 生成覆盖率报告
uv run pytest --cov=src tests/
```

### 5. 类型检查

```bash
# 运行 mypy
uv run mypy --strict backend/src/

# 检查特定文件
uv run mypy --strict backend/src/services/agent_service.py
```

---

## ✅ 开发检查清单

在提交代码前，确保通过以下检查：

### 代码质量
- [ ] 所有函数都有完整的类型注解
- [ ] mypy --strict 通过 (0 errors)
- [ ] pylint/flake8 无警告
- [ ] 代码格式化 (black 或 yapf)

### 测试
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 所有测试通过 (pytest)
- [ ] 集成测试覆盖关键路径
- [ ] E2E 测试通过 (Playwright)

### 功能完整性
- [ ] 所有异步操作使用 async/await
- [ ] 所有数据库操作都有索引优化
- [ ] 关键操作都有监控指标
- [ ] 错误处理完善

### 宪法合规
- [ ] 代码遵守 8 个核心原则
- [ ] 中间件都已实现
- [ ] 监控和日志都已配置
- [ ] /speckit.constitution-check 通过

### 文档和部署
- [ ] 规范、计划、任务文件已完成
- [ ] README 和内联注释已更新
- [ ] 数据库迁移已应用
- [ ] 部署前健康检查通过

---

## 🆘 常见问题解答

**Q: 我可以修改宪法吗?**
A: 可以，但必须遵循[治理规则](./memory/constitution.md#治理规则)中的修订流程。所有修改都需要 maintainer 投票同意。

**Q: 如果我的代码不符合宪法怎么办?**
A: 在代码审查中会被指出。修改代码以遵守宪法，而不是修改宪法以适应代码。

**Q: 类型检查失败怎么办?**
A: 添加适当的类型注解或使用 `typing.cast()` 和 `# type: ignore` (仅在必要时)。避免使用 `Any`。

**Q: 异步操作太复杂，可以用同步吗?**
A: 不可以。使用 `asyncio.to_thread()` 包装同步调用，或重构为异步。

**Q: 性能目标无法达到怎么办?**
A: 在计划中文档化限制，与 maintainers 讨论替代方案，获得明确批准后再继续。

---

## 📞 获取帮助

### 遇到问题？

1. **查看宪法** - 大多数答案都在 [constitution.md](./memory/constitution.md)
2. **查看示例** - 模板中包含代码示例
3. **查看外部文档** - LangChain、FastAPI、PostgreSQL 官方文档
4. **提问** - 在项目 GitHub Issues 中提出问题

### 宪法修改建议？

在 GitHub Issues 中创建"Constitution Enhancement"主题，描述：
- 建议的原则修改
- 修改的理由
- 受影响的代码/流程
- 提议的实现

---

## 🎯 接下来的步骤

### 如果你是新开发者

1. ✅ 完成本快速入门 (30 分钟)
2. ✅ 阅读完整宪法 (45 分钟)
3. ✅ 审查一个已实现的功能 (1 小时)
4. ✅ 为第一个简单功能创建规范 (1 小时)
5. ✅ 提交 PR 并获得代码审查反馈

### 如果你是项目 Lead

1. ✅ 审查并批准宪法
2. ✅ 向团队宣布宪法
3. ✅ 设置 CI/CD 宪法检查
4. ✅ 创建 Grafana 监控仪表板
5. ✅ 安排月度合规审查会议

---

## 📈 成功标志

当你看到以下情况，说明项目运行良好：

✅ 所有 PR 的类型检查都通过 (mypy --strict)
✅ 所有新功能都有 ≥ 80% 的测试覆盖
✅ API 响应时间 P99 ≤ 500ms
✅ 向量搜索延迟 ≤ 200ms
✅ 错误率 ≤ 1%
✅ 所有中间件都正确运行
✅ 监控指标数据完整
✅ 月度宪法审查无重大问题

---

## 祝贺！🎉

你现在已经理解了项目的宪法和规范系统。是时候开始你的第一个功能了！

**建议顺序**:

1. 阅读完整宪法 (45 分钟)
2. 创建功能规范 (1 小时)
3. 设计实现方案 (1.5 小时)
4. 分解为任务 (1 小时)
5. 开始编码！

---

**最后更新**: 2025-11-16
**文档版本**: v1.0.0
**维护者**: 云开发团队
