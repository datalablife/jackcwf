# 实现阶段行动计划

**项目**: 001-text2sql-datasource - AI 驱动的数据源集成
**日期**: 2025-11-08
**状态**: ✅ 规划完成，准备进入实现阶段
**分支**: main (3,158 行规划文档已合并)

---

## 📋 当前状态

✅ **规划阶段已完成**:
- 功能规范: spec.md (5 个用户故事)
- 技术规划: plan.md (8 个技术决策)
- 研究文档: research.md (技术方案确认)
- 数据模型: data-model.md (5 个 ORM 实体)
- API 规范: contracts/ (12 个端点)
- 任务清单: tasks.md (82 个任务)

✅ **分支状态**:
- Feature 分支已合并到 main
- 所有文件已在 GitHub 上可见
- 本地已同步最新状态

---

## 🚀 下一步行动 (6 个关键阶段)

### 1️⃣ 创建后端项目结构和初始化 (1-2 天)

**目标**: 建立 FastAPI 后端项目基础

**任务清单**:
- [ ] T001 创建 backend/ 目录结构
  ```
  backend/
  ├── src/
  │   ├── models/
  │   ├── services/
  │   ├── api/
  │   ├── db/
  │   └── main.py
  ├── tests/
  ├── pyproject.toml
  └── .env.example
  ```

- [ ] T002 创建 backend/pyproject.toml (依赖配置)
  ```toml
  [tool.poetry.dependencies]
  python = "^3.12"
  fastapi = "^0.104.0"
  sqlalchemy = "^2.0.23"
  asyncpg = "^0.29.0"
  cryptography = "^41.0.7"
  pydantic = "^2.5.0"
  pytest = "^7.4.0"
  pytest-asyncio = "^0.21.0"
  ```

- [ ] T003 创建 backend/.env.example (环境变量模板)
  ```env
  DATABASE_URL=postgresql+asyncpg://user:password@host:5432/database
  ENCRYPTION_KEY=your-256-bit-key-base64-encoded
  MAX_FILE_SIZE=536870912
  SCHEMA_CACHE_TTL=300
  LOG_LEVEL=INFO
  ```

- [ ] T004 创建 backend/src/main.py (FastAPI 应用入口)
  - 配置 CORS
  - 设置日志
  - 添加健康检查端点

**验收标准**:
- ✅ 可以运行 `uvicorn src.main:app --reload`
- ✅ http://localhost:8000/health 返回正常

---

### 2️⃣ 创建前端项目结构和初始化 (1-2 天)

**目标**: 建立 React 18 前端项目基础

**任务清单**:
- [ ] T005 初始化 Vite + React 18 + TypeScript 项目
  ```bash
  npm create vite@latest frontend -- --template react-ts
  cd frontend
  npm install
  ```

- [ ] T006 安装前端依赖
  ```bash
  # Core dependencies
  npm install zustand @tanstack/react-query axios react-router-dom

  # UI & Styling
  npm install tremor recharts        # Data visualization
  npm install -D tailwindcss@3 postcss autoprefixer

  # Testing
  npm install -D vitest @testing-library/react @testing-library/jest-dom

  # Development tools
  npm install -D @types/node typescript
  ```
  **Important**: Tremor for dashboard visualization, shadcn/ui (to be added via CLI) for base components

- [ ] T007 创建 frontend/.env.example
  ```env
  VITE_API_URL=http://localhost:8000/api
  VITE_APP_NAME=AI Data Analyzer
  ```

- [ ] T008 创建 frontend/src/main.tsx 和基础路由
  - 配置 React Router v6
  - 创建 Zustand store 目录结构
  - 设置 Tailwind CSS

**验收标准**:
- ✅ 可以运行 `npm run dev`
- ✅ http://localhost:5173 能访问

---

### 3️⃣ Phase 1 - Setup (配置和环境) (2-3 天)

**6 个任务** - 参考 tasks.md 的 T001-T013

**关键任务**:
- [ ] T009 创建 .env 配置文件 (使用 Coolify PostgreSQL 凭据)
- [ ] T010 验证到 Coolify PostgreSQL 的连接
  ```bash
  psql -h host.docker.internal -p 5432 -U jackcwf888 -d postgres
  ```
- [ ] T011 配置 Docker Compose (可选)
- [ ] T012-T013 配置 .gitignore

**验收标准**:
- ✅ 后端能运行 `uvicorn src.main:app --reload`
- ✅ 前端能运行 `npm run dev`
- ✅ PostgreSQL 连接测试成功

---

### 4️⃣ Phase 2 - Foundational (数据库和模型) (2-3 天)

**8 个任务** - 参考 tasks.md 的 T014-T025

**关键任务**:
- [ ] T014-T019 实现 5 个 ORM 模型
  - DataSource (数据源)
  - DatabaseConnection (PostgreSQL 连接)
  - FileUpload (文件上传)
  - Schema (模式缓存)
  - DataSourceConfig (用户配置)

- [ ] T020 创建 Alembic 数据库迁移脚本
  ```bash
  alembic init migrations
  alembic revision --autogenerate -m "Initial migration"
  alembic upgrade head
  ```

- [ ] T021-T022 实现加密和会话管理
  - AES-256 加密/解密服务
  - SQLAlchemy 异步连接池配置

- [ ] T023-T025 编写单元测试

**验收标准**:
- ✅ 数据库迁移成功运行
- ✅ 所有 ORM 模型可实例化
- ✅ 单元测试覆盖率 >80%

---

### 5️⃣ Phase 3 - PostgreSQL 连接功能 (3-4 天)

**18 个任务** - 参考 tasks.md 的 T026-T043

**后端部分** (T026-T032):
- [ ] T026 实现 PostgreSQL 连接服务
  ```python
  # backend/src/services/postgres.py
  async def test_connection(host, port, database, username, password)
  async def get_database_schema(session, data_source_id)
  ```

- [ ] T027 配置连接池
- [ ] T028 创建数据源 API 端点
  ```
  POST /api/datasources/postgres
  GET /api/datasources
  GET /api/datasources/{id}
  POST /api/datasources/{id}/test
  DELETE /api/datasources/{id}
  ```

- [ ] T029 实现数据源业务逻辑层
- [ ] T030 实现模式缓存
- [ ] T031-T032 编写集成测试

**前端部分** (T033-T043):
- [ ] T033-T034 创建 Zustand store
  ```typescript
  // frontend/src/stores/useDataSourceStore.ts
  // frontend/src/stores/useSchemaStore.ts
  ```

- [ ] T035-T036 创建 API 服务
- [ ] T037-T039 创建 React 组件
  - ConnectPostgres.tsx (连接表单)
  - DataSourceList.tsx (数据源列表)
  - StatusBadge.tsx (状态徽章)

- [ ] T040-T041 创建页面
- [ ] T042-T043 编写测试

**验收标准**:
- ✅ 可以连接到 Coolify PostgreSQL
- ✅ 连接成功时显示表列表
- ✅ 凭据被加密保存
- ✅ 刷新后连接仍然存在

---

### 6️⃣ 完成 MVP 验收和部署 (1-2 天)

**目标**: 验证 MVP 功能完整性，准备部署

**任务**:
- [ ] 运行完整的集成测试
- [ ] 验证性能指标
  - PostgreSQL 连接 <100ms ✅
  - 仪表板加载 <1s ✅
  - 凭据加密正确 ✅

- [ ] 代码审查和质量检查
- [ ] 文档更新

---

## 📊 工作量预估和时间表

### MVP 范围 (Phase 1-3)

| 阶段 | 任务数 | 人·天 | 预计天数 |
|------|--------|------|--------|
| Phase 1 (Setup) | 6 | 4 | 1 |
| Phase 2 (Foundational) | 8 | 6 | 1.5 |
| Phase 3 (US1 PostgreSQL) | 18 | 12 | 2.5 |
| 完成和部署 | - | 4 | 1 |
| **总计** | **32** | **26** | **6 天** |

### 5 人团队并行执行方案

**第 1-2 天**:
- 人 1: 后端初始化 (T001-T004) + Phase 1
- 人 2: 前端初始化 (T005-T008) + Phase 1
- 人 3-5: 平行做数据库迁移和配置

**第 3-4 天**:
- 人 1: PostgreSQL 服务 + API (T026-T029)
- 人 2: Zustand store + API 客户端 (T033-T036)
- 人 3: React 组件 (T037-T041)
- 人 4-5: 集成测试

**第 5-6 天**:
- 全员: 集成测试 + 部署

---

## 🎯 立即开始的步骤

### 第一步: 初始化后端项目

```bash
# 在项目根目录执行
mkdir -p backend/src/{models,services,api,db}
cd backend

# 创建 pyproject.toml
cat > pyproject.toml << 'EOF'
[tool.poetry]
name = "text2sql-backend"
version = "0.1.0"
description = "AI-powered data source integration backend"
authors = ["Your Team"]

[tool.poetry.dependencies]
python = "^3.12"
fastapi = "^0.104.0"
uvicorn = "^0.24.0"
sqlalchemy = "^2.0.23"
asyncpg = "^0.29.0"
alembic = "^1.13.0"
cryptography = "^41.0.7"
pydantic = "^2.5.0"
python-dotenv = "^1.0.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
pytest-cov = "^4.1.0"
black = "^23.12.0"
mypy = "^1.7.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
EOF

# 安装依赖
poetry install
```

### 第二步: 初始化前端项目

```bash
# 在项目根目录执行
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install zustand react-query axios
npm install -D tailwindcss postcss autoprefixer vitest @testing-library/react
npx tailwindcss init -p
```

### 第三步: 创建环境配置

```bash
# 在项目根目录
cat > .env.local << 'EOF'
DATABASE_URL=postgresql+asyncpg://jackcwf888:PASSWORD@host.docker.internal:5432/postgres
ENCRYPTION_KEY=your-256-bit-key-here
MAX_FILE_SIZE=536870912
EOF
```

### 第四步: 验证连接

```bash
# 测试 PostgreSQL 连接
psql -h host.docker.internal -p 5432 -U jackcwf888 -d postgres -c "SELECT version();"
```

---

## ✅ 检查清单

在开始编码前，请确保:

- [ ] GitHub 上的 main 分支已同步
- [ ] 本地已拉取最新代码
- [ ] 已阅读 specs/001-text2sql-datasource/quickstart.md
- [ ] 已准备好 Coolify PostgreSQL 凭据
- [ ] 后端和前端项目结构已创建
- [ ] 环境变量已配置
- [ ] PostgreSQL 连接已测试

---

## 📞 需要帮助？

- 查看 quickstart.md 获取详细代码示例
- 查看 tasks.md 获取完整任务清单
- 查看 contracts/ 获取 API 规范
- 查看 data-model.md 获取数据模型详情

---

**准备就绪！可以开始实现了！** 🚀
