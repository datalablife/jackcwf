# 实现计划：AI 驱动的数据源集成 (text2SQL MVP)

**分支**: `001-text2sql-datasource` | **日期**: 2025-11-07 | **规范**: [spec.md](./spec.md)
**输入**: 特性规范来自 `/specs/001-text2sql-datasource/spec.md`

**说明**: 此模板由 `/speckit.plan` 命令填充。

## 摘要

本功能是 AI 驱动数据分析平台的基础层，实现数据源集成能力。用户可以连接远程 PostgreSQL 数据库或上传本地 CSV/Excel 文件，系统通过 Coolify 托管的 PostgreSQL 数据库存储配置和元数据。

**核心需求**:
- 远程 PostgreSQL 连接与身份验证
- 本地文件上传（CSV/Excel，最大 500MB）
- 数据源仪表板和管理
- 安全凭据存储（AES-256 加密）
- 数据库模式探索和缓存

## 技术背景

**后端语言/版本**: Python 3.12
**前端语言/版本**: TypeScript + React 18
**主要后端依赖**: FastAPI, SQLAlchemy, psycopg2-binary, cryptography, pydantic
**主要前端依赖**: React 18, TypeScript, Zustand, React Query, shadcn/ui, Tremor
**存储**: PostgreSQL (Coolify 托管实例)
**后端测试**: pytest, pytest-asyncio
**前端测试**: Vitest, React Testing Library
**目标平台**: Web (浏览器 + 服务器)
**项目类型**: 全栈 Web 应用（前端 + 后端分离）
**性能目标**:
  - UI 操作: 3 秒内完成
  - 数据库操作: 5 秒内完成
  - 页面加载: 1 秒内显示数据源
  - 文件上传: 500MB 文件 30 秒内处理完成
**约束条件**:
  - MVP 阶段不支持文件永久存储（仅会话级）
  - 模式缓存: 5 分钟
  - 并发连接: 支持至少 5 个数据源
**规模/范围**:
  - 用户数: 初期 <100
  - 单库表数: 支持最多 1000 个表
  - 文件大小: 最大 500MB

## 宪法检查

*门控: 第 0 阶段研究前必须通过。第 1 阶段设计后重新检查。*

**当前状态**: 项目宪法模板尚未填充 - 此特性不受限制性约束的约束。

**推荐原则** (基于项目最佳实践):
1. **测试优先**: 为所有 API 端点编写单元和集成测试
2. **安全性**: 凭据必须加密（AES-256），绝不在日志中暴露
3. **文档**: 所有 API 端点和数据模型必须有完整文档
4. **可观察性**: 结构化日志记录，用于调试和监控

**通过状态**: ✅ 无宪法冲突

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### 源代码结构 (仓库根目录)

```text
# Web 应用结构
backend/
├── src/
│   ├── models/              # SQLAlchemy ORM 模型
│   │   ├── data_source.py   # DataSource, DatabaseConnection, FileUpload
│   │   └── schema.py        # Schema, Column 等
│   ├── services/            # 业务逻辑服务
│   │   ├── postgres.py      # PostgreSQL 连接和查询
│   │   ├── file_handler.py  # 文件解析和处理
│   │   ├── encryption.py    # 凭据加密/解密
│   │   └── cache.py         # 模式缓存
│   ├── api/                 # FastAPI 路由
│   │   ├── data_sources.py  # 数据源端点
│   │   ├── files.py         # 文件上传端点
│   │   └── schemas.py       # 模式端点
│   ├── db/                  # 数据库配置
│   │   ├── session.py       # SQLAlchemy 会话
│   │   └── migrations/      # Alembic 迁移
│   └── main.py              # FastAPI 应用入口
└── tests/
    ├── unit/                # 单元测试
    │   ├── test_postgres.py
    │   ├── test_file_handler.py
    │   └── test_encryption.py
    ├── integration/         # 集成测试
    │   ├── test_datasource_api.py
    │   └── test_file_upload_api.py
    └── fixtures/            # 测试数据

frontend/
├── src/
│   ├── components/
│   │   ├── datasources/     # 数据源管理组件 (shadcn/ui)
│   │   │   ├── DataSourceList.tsx
│   │   │   ├── DataSourceCard.tsx
│   │   │   ├── ConnectPostgres.tsx
│   │   │   └── FileUpload.tsx
│   │   ├── schema/          # 模式浏览器组件 (shadcn/ui)
│   │   │   ├── SchemaExplorer.tsx
│   │   │   └── TableViewer.tsx
│   │   ├── dashboard/       # 仪表板数据可视化 (Tremor)
│   │   │   ├── StatisticsCards.tsx    # Tremor KPI/Stats 组件
│   │   │   ├── DataSourceMetrics.tsx  # 数据源统计信息
│   │   │   └── ConnectionStatus.tsx   # 连接状态指示
│   │   └── common/          # 通用组件 (shadcn/ui)
│   │       ├── StatusBadge.tsx
│   │       └── ErrorAlert.tsx
│   ├── pages/
│   │   ├── Dashboard.tsx    # 主仪表板 (Tremor 统计 + shadcn/ui 列表)
│   │   ├── DataSourceSetup.tsx
│   │   └── SchemaExplorer.tsx
│   ├── stores/              # Zustand 状态管理
│   │   ├── useDataSourceStore.ts
│   │   └── useSchemaStore.ts
│   ├── hooks/               # 自定义 hooks
│   │   ├── useDataSources.ts
│   │   └── useFileUpload.ts
│   ├── services/            # API 调用
│   │   ├── datasource.api.ts
│   │   ├── file.api.ts
│   │   └── schema.api.ts
│   └── types/               # TypeScript 类型
│       └── datasource.ts
└── tests/
    ├── unit/                # 单元测试
    └── integration/         # 集成测试
```

**结构决策**: 采用选项 2（Web 应用）- 前后端分离，便于独立开发和部署。后端通过 FastAPI 提供 REST API，前端使用 React 18 + Zustand 构建交互式界面。

**前端架构决策 - Tremor + shadcn/ui 组合**:
- **shadcn/ui**: 用于基础 UI 组件（表单、按钮、卡片、对话框等）
  - 优势: 可定制、Tailwind CSS 集成、优秀的可访问性
  - 用途: 数据源管理、连接表单、模式浏览器
- **Tremor**: 用于数据可视化和仪表板组件
  - 优势: 专为数据应用设计、KPI 卡片、统计展示、图表库
  - 用途: Dashboard 统计信息、数据源指标、连接状态可视化、性能监控
- **整合方式**: Tremor 提供数据展示层，shadcn/ui 提供交互和管理层，Tailwind CSS 统一样式系统

## 复杂性跟踪

> **仅在宪法检查有需要证明的违规时填充**

**当前状态**: 无宪法违规，无复杂性权衡。

## 阶段 0: 研究与清晰化

### 研究任务

以下领域需要研究以解决技术不确定性:

1. **PostgreSQL 连接池**
   - 任务: 研究 SQLAlchemy 连接池最佳实践以支持多个并发连接
   - 输出: 连接池配置建议 (最大连接数, 超时设置, 重试逻辑)

2. **大文件上传处理**
   - 任务: 研究流式文件上传和处理大文件 (500MB) 的最佳实践
   - 输出: 流式处理实现指南

3. **CSV/Excel 解析**
   - 任务: 评估 Python CSV 和 Excel 库 (pandas, openpyxl, csvx)
   - 输出: 库选择建议和集成方案

4. **凭据加密**
   - 任务: 研究 Python cryptography 库 AES-256 实现
   - 输出: 加密/解密函数实现方案

5. **前端状态管理**
   - 任务: 评估 Zustand 在数据源管理中的实现模式
   - 输出: 状态结构设计建议

**输出文件**: `research.md` (包含所有研究发现和决策)

## 阶段 1: 设计与契约

### 数据模型设计

**关键实体**:
- `DataSource`: 代表一个已连接的数据源
- `DatabaseConnection`: PostgreSQL 特定的连接信息
- `FileUpload`: 上传的文件元数据
- `Schema`: 数据库模式信息
- `DataSourceConfig`: 用户偏好设置

### API 契约

**主要端点**:

1. **数据源管理**
   - `POST /api/datasources/postgres` - 创建 PostgreSQL 连接
   - `POST /api/datasources/file` - 上传文件
   - `GET /api/datasources` - 列出所有数据源
   - `GET /api/datasources/{id}` - 获取数据源详情
   - `DELETE /api/datasources/{id}` - 删除数据源
   - `POST /api/datasources/{id}/test` - 测试连接

2. **文件操作**
   - `POST /api/files/upload` - 上传文件
   - `GET /api/files/{id}/preview` - 预览文件数据
   - `DELETE /api/files/{id}` - 删除文件

3. **模式操作**
   - `GET /api/datasources/{id}/schema` - 获取数据源的完整模式
   - `GET /api/datasources/{id}/schema/tables` - 获取表列表
   - `GET /api/datasources/{id}/schema/tables/{table}/columns` - 获取列信息

### 输出文件

- `data-model.md` - 详细的数据模型规范
- `contracts/postgres.yaml` - PostgreSQL API OpenAPI 规范
- `contracts/files.yaml` - 文件上传 API OpenAPI 规范
- `contracts/schema.yaml` - 模式 API OpenAPI 规范
- `quickstart.md` - 集成快速开始指南
