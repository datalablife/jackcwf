# 实现任务清单: 数据源集成功能

**特性**: 001-text2sql-datasource - AI 驱动的数据源集成 (text2SQL MVP)
**日期**: 2025-11-07
**分支**: `001-text2sql-datasource`
**规范**: [spec.md](./spec.md) | **计划**: [plan.md](./plan.md)

---

## 📋 任务总览

**总任务数**: 82 个
**阶段数**: 6 个 (Setup + Foundational + 4 个用户故事 + Polish)
**并行机会**: 显著 (P1 和 P2 故事可部分并行)
**预计工作量**: 48 人·天 (5 人团队 = 10-15 工作日)

### 任务分布

| 阶段 | 故事 | 任务数 | 并行机会 |
|------|------|--------|--------|
| Phase 1 | Setup | 6 | 3/6 |
| Phase 2 | Foundational | 8 | 4/8 |
| Phase 3 | [US1] PostgreSQL 连接 | 10 | 5/10 |
| Phase 4 | [US2] 文件上传 | 9 | 4/9 |
| Phase 5 | [US3] 仪表板 | 7 | 3/7 |
| Phase 6 | [US4] 模式浏览 + [US5] 安全存储 | 8 | 3/8 |

---

## 🎯 MVP 范围建议

**最小可行产品** (首个 Sprint - 5-7 天):
- ✅ Phase 1: Setup (全部)
- ✅ Phase 2: Foundational (全部)
- ✅ Phase 3: [US1] PostgreSQL 连接 (全部)

**此范围覆盖**:
- 后端 ORM 模型和数据库迁移
- PostgreSQL 连接、测试、凭据存储
- 基础 API 端点
- 前端数据源列表和连接表单

---

## 🔗 依赖关系图

```
Phase 1: Setup
    ↓
Phase 2: Foundational (所有 Phase 3+ 的阻塞)
    ├─→ Phase 3: [US1] PostgreSQL 连接 (可独立完成)
    ├─→ Phase 4: [US2] 文件上传 (可独立完成)
    ├─→ Phase 5: [US3] 仪表板 (需要 US1 或 US2 完成)
    └─→ Phase 6: [US4] 模式浏览 (需要 US1 完成)
         Phase 6: [US5] 安全存储 (需要 US1 或 US2 完成)
```

---

# Phase 1: 项目初始化和设置

## 目标

建立后端和前端的项目基础结构，包括依赖管理、目录结构、开发环境配置。

---

## 任务列表

### 后端项目初始化

- [ ] T001 [P] 创建后端项目结构 backend/src/{models,services,api,db,migrations}
- [ ] T002 [P] 创建 backend/pyproject.toml 依赖声明 (FastAPI, SQLAlchemy, asyncpg, cryptography)
- [ ] T003 [P] 创建 backend/.env.example 环境变量文档
- [ ] T004 创建 backend/src/main.py FastAPI 应用入口，配置 CORS 和日志

### 前端项目初始化

- [ ] T005 [P] 创建 React 18 + TypeScript 项目 (frontend/)
- [ ] T006 [P] 安装前端依赖 (React 18, TypeScript, Zustand, @tanstack/react-query, shadcn/ui, Tremor, Tailwind, axios)
  - **关键**: Tremor 用于数据可视化图表（图表、仪表板统计）
  - **关键**: shadcn/ui 用于基础 UI 组件（表单、按钮、对话框等）
  - **关键**: Tailwind CSS 用于样式和响应式设计
- [ ] T007 [P] 创建 frontend/.env.example 环境变量文档
- [ ] T008 创建 frontend/src/main.tsx 入口和基础路由结构

### 数据库和开发环境

- [ ] T009 [P] 创建 .env 配置文件 (DATABASE_URL, ENCRYPTION_KEY 等)
- [ ] T010 [P] 验证到 Coolify PostgreSQL 连接
- [ ] T011 创建 Docker Compose 配置

### Git 配置

- [ ] T012 配置 backend/.gitignore (Python, venv, __pycache__ 等)
- [ ] T013 配置 frontend/.gitignore (node_modules, .env.local, dist/ 等)

---

# Phase 2: 基础设施和数据库

## 目标

建立数据库模式、ORM 模型、加密服务、连接管理等所有用户故事的共享基础。

---

## 任务列表

### 数据库和 ORM 模型

- [ ] T014 [P] 创建 backend/src/models/__init__.py 基础 Base 类
- [ ] T015 [P] 实现 backend/src/models/data_source.py (DataSource ORM 模型)
- [ ] T016 [P] 实现 backend/src/models/database_connection.py (DatabaseConnection ORM)
- [ ] T017 [P] 实现 backend/src/models/file_upload.py (FileUpload ORM)
- [ ] T018 [P] 实现 backend/src/models/schema.py (Schema ORM)
- [ ] T019 [P] 实现 backend/src/models/config.py (DataSourceConfig ORM)

### 数据库迁移

- [ ] T020 创建 Alembic 初始迁移脚本 backend/src/db/migrations/ (5 个表)
- [ ] T021 验证迁移脚本 (alembic upgrade head)

### 核心服务

- [ ] T022 [P] 实现 backend/src/services/encryption.py (AES-256 加密/解密)
- [ ] T023 [P] 实现 backend/src/db/session.py (SQLAlchemy 异步引擎和会话)

### 单元测试

- [ ] T024 创建 backend/tests/unit/test_models.py (所有 ORM 模型)
- [ ] T025 创建 backend/tests/unit/test_encryption.py (加密服务)

---

# Phase 3: User Story 1 - 连接到 PostgreSQL 数据库

## User Story 1: 数据工程师连接到远程 PostgreSQL 数据库

**优先级**: P1 | **故事点**: 13

---

## 后端任务

### PostgreSQL 服务

- [ ] T026 [P] 实现 backend/src/services/postgres.py:
  - async test_connection() - 测试连接
  - async get_database_schema() - 获取表和列
  - async query_database() - 执行查询

- [ ] T027 [P] 实现 backend/src/db/session.py 连接池配置
  - pool_size=5, max_overflow=10

### 数据源管理 API

- [ ] T028 创建 backend/src/api/datasources.py 路由:
  - POST /api/datasources/postgres
  - GET /api/datasources
  - GET /api/datasources/{id}
  - POST /api/datasources/{id}/test
  - DELETE /api/datasources/{id}

- [ ] T029 [P] 创建 backend/src/services/datasource_service.py
  - 处理数据源创建和验证

### 模式缓存

- [ ] T030 [P] 实现 backend/src/services/cache.py
  - 使用 lru_cache (5 分钟 TTL)

### 单元和集成测试

- [ ] T031 [P] 创建 backend/tests/unit/test_postgres.py
- [ ] T032 创建 backend/tests/integration/test_datasource_api.py

---

## 前端任务

### 状态管理

- [ ] T033 [P] 创建 frontend/src/stores/useDataSourceStore.ts
  - 状态: dataSources[], selectedId, isLoading, error
  - 操作: fetchDataSources, selectDataSource, addDataSource, removeDataSource

- [ ] T034 [P] 创建 frontend/src/stores/useSchemaStore.ts
  - 状态: schemas (缓存)

### API 服务

- [ ] T035 [P] 创建 frontend/src/services/datasource.api.ts
  - listDataSources(), createPostgresDataSource(), testConnection()

- [ ] T036 [P] 创建 frontend/src/services/schema.api.ts
  - getSchema()

### React 组件

- [ ] T037 创建 frontend/src/components/datasources/ConnectPostgres.tsx
  - 连接表单

- [ ] T038 [P] 创建 frontend/src/components/datasources/DataSourceList.tsx
  - 数据源列表

- [ ] T039 [P] 创建 frontend/src/components/common/StatusBadge.tsx
  - 连接状态徽章

### 页面

- [ ] T040 创建 frontend/src/pages/DataSourceSetup.tsx
  - 布局和集成

- [ ] T041 创建 frontend/src/components/schema/SchemaViewer.tsx
  - 模式显示

### 测试

- [ ] T042 [P] 创建 frontend/tests/unit/useDataSourceStore.test.ts
- [ ] T043 创建 frontend/tests/integration/datasource-setup.test.tsx

---

# Phase 4: User Story 2 - 上传本地 CSV/Excel 文件

## User Story 2: 数据分析师上传本地 CSV/Excel 文件

**优先级**: P1 | **故事点**: 13

---

## 后端任务

### 文件处理服务

- [ ] T044 [P] 实现 backend/src/services/file_handler.py:
  - async parse_csv() - 解析 CSV
  - async parse_excel() - 解析 Excel
  - async infer_columns() - 推断数据类型

- [ ] T045 [P] 创建文件存储管理 backend/tmp/uploads/

### 文件 API

- [ ] T046 创建 backend/src/api/files.py 路由:
  - POST /api/files/upload
  - GET /api/files/{id}/preview
  - DELETE /api/files/{id}

- [ ] T047 [P] 创建 backend/src/services/file_service.py

### 测试

- [ ] T048 [P] 创建 backend/tests/unit/test_file_handler.py
- [ ] T049 创建 backend/tests/integration/test_file_upload_api.py

---

## 前端任务

### API 服务

- [ ] T050 [P] 创建 frontend/src/services/file.api.ts
  - uploadFile(), getFilePreview(), deleteFile()

### React 组件

- [ ] T051 创建 frontend/src/components/datasources/FileUpload.tsx
  - 文件上传表单和拖放

- [ ] T052 [P] 创建 frontend/src/components/datasources/FilePreview.tsx
  - 文件数据预览和分页

- [ ] T053 [P] 创建 frontend/src/hooks/useFileUpload.ts
  - 上传状态管理

### 页面集成

- [ ] T054 更新 frontend/src/pages/DataSourceSetup.tsx
  - 添加文件上传功能

### 测试

- [ ] T055 [P] 创建 frontend/tests/unit/useFileUpload.test.ts
- [ ] T056 创建 frontend/tests/integration/file-upload.test.tsx

---

# Phase 5: User Story 3 - 仪表板显示数据源

## User Story 3: 用户在仪表板查看已连接的数据源

**优先级**: P1 | **故事点**: 8

---

## 前端任务

### 仪表板页面

- [ ] T057 创建 frontend/src/pages/Dashboard.tsx
  - 显示数据源列表（使用 shadcn/ui 组件）
  - **Tremor 统计信息**: 使用 Tremor KPIs 和 Stats 组件展示：
    - 数据源总数
    - 连接状态（已连接/断开）
    - 最近连接时间

### 数据源卡片

- [ ] T058 [P] 创建 frontend/src/components/datasources/DataSourceCard.tsx
  - 使用 shadcn/ui Card 组件构建
  - 卡片设计和操作（连接、删除、编辑）
  - **Tremor 状态指示**: 使用 Tremor Badge/Callout 显示连接状态

- [ ] T059 [P] 更新 frontend/src/components/datasources/DataSourceList.tsx
  - 使用 DataSourceCard
  - **Tremor 列表布局**: 如需大量数据展示，使用 Tremor Table 或 Grid

### 测试

- [ ] T060 [P] 创建 frontend/tests/unit/DataSourceCard.test.tsx
- [ ] T061 创建 frontend/tests/integration/dashboard.test.tsx

---

# Phase 6: User Story 4 & 5 - 模式浏览和安全存储

## User Story 4: 用户浏览数据库模式

**优先级**: P2 | **故事点**: 8

## User Story 5: 系统安全地存储数据源配置

**优先级**: P2 | **故事点**: 5

---

## 后端任务

### 模式 API

- [ ] T062 创建 backend/src/api/schemas.py 路由:
  - GET /api/datasources/{id}/schema
  - GET /api/datasources/{id}/schema/tables
  - GET /api/datasources/{id}/schema/tables/{table}

- [ ] T063 [P] 创建 backend/src/services/schema_service.py

### 配置管理

- [ ] T064 [P] 更新 backend/src/api/datasources.py
  - 添加配置管理端点

- [ ] T065 [P] 创建 backend/src/services/config_service.py

### 测试

- [ ] T066 创建 backend/tests/integration/test_schema_api.py

---

## 前端任务

### 模式浏览器

- [ ] T067 创建 frontend/src/pages/SchemaExplorer.tsx
- [ ] T068 [P] 更新 frontend/src/components/schema/SchemaViewer.tsx

### 设置页面

- [ ] T069 创建 frontend/src/pages/Settings.tsx
  - 管理数据源配置

### 测试

- [ ] T070 创建 frontend/tests/integration/schema-explorer.test.tsx
- [ ] T071 创建 frontend/tests/integration/settings.test.tsx

---

# Final Phase: 完善和交叉关注事项

## 任务列表

### 端到端测试

- [ ] T072 创建完整的 e2e 测试脚本 (使用 Playwright)
  - PostgreSQL 连接工作流
  - 文件上传工作流

### 性能测试

- [ ] T073 [P] 性能基准测试
  - 连接时间 <100ms
  - 文件上传 <30s for 500MB

- [ ] T074 [P] 缓存优化验证

### 文档完善

- [ ] T075 更新 quickstart.md
- [ ] T076 添加 API 使用示例

### 部署

- [ ] T077 [P] 创建生产 Docker 镜像
- [ ] T078 创建 docker-compose.yml
- [ ] T079 设置 GitHub Actions CI/CD

### 最终验证

- [ ] T080 代码审查和重构
- [ ] T081 [P] 最终集成测试运行
- [ ] T082 创建部署检查清单

---

## MVP 范围 (25 个任务)

```
T001-T013: Setup (13 任务) ✓
T014-T025: Foundational (12 任务) ✓
T026-T043: US1 PostgreSQL (18 任务) ✓

总计: 43 任务 (7-10 工作日)
```

---

## 工作量预估

| 阶段 | 人·天 | 5 人团队 |
|------|------|--------|
| Phase 1 (Setup) | 4 | 1 天 |
| Phase 2 (Foundational) | 6 | 1.5 天 |
| Phase 3 (US1) | 12 | 2.5 天 |
| Phase 4 (US2) | 10 | 2 天 |
| Phase 5 (US3) | 6 | 1.5 天 |
| Phase 6 (US4/5) | 8 | 2 天 |
| Final (Polish) | 8 | 1.5 天 |
| **总计** | **54** | **12 天** |

---

**任务清单生成**: ✅ 完成
**总任务**: 82 个
**状态**: 准备就绪，可以开始实现！
