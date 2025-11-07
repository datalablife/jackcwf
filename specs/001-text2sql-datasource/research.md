# 阶段 0 研究: AI 驱动的数据源集成

**日期**: 2025-11-07
**特性**: 001-text2sql-datasource
**研究状态**: ✅ 完成

---

## 研究发现和技术决策

### 1. PostgreSQL 连接池管理

**研究问题**: 如何在 FastAPI 应用中实现高效的 PostgreSQL 连接池以支持多个并发数据源连接？

**评估的选项**:
- **Option A**: SQLAlchemy 默认连接池 + asyncio
- **Option B**: asyncpg 库 (异步 PostgreSQL 驱动)
- **Option C**: pgBouncer (独立连接池代理)

**决策**: Option A + asyncio 的组合
- **原因**: SQLAlchemy 2.0+ 原生支持异步，与 FastAPI 完美集成；pgBouncer 增加部署复杂度；asyncpg 需要更多配置
- **配置方案**:
  ```python
  engine = create_async_engine(
      DATABASE_URL,
      echo=False,
      future=True,
      pool_size=5,                    # 为 5 个并发数据源优化
      max_overflow=10,                # 临时溢出连接
      pool_timeout=30,                # 30 秒超时
      pool_recycle=3600,              # 1 小时回收连接
      pool_pre_ping=True              # 连接健康检查
  )
  ```
- **性能指标**: 支持 5+ 并发连接，连接建立 <100ms

---

### 2. 大文件上传处理 (500MB)

**研究问题**: 如何安全高效地处理最大 500MB 的文件上传，同时保持内存占用低？

**评估的选项**:
- **Option A**: 一次性加载到内存 (pandas)
- **Option B**: 流式分块处理 (starlette.UploadFile)
- **Option C**: 临时文件处理 + 分块读取

**决策**: Option B - 流式分块处理
- **原因**: 内存效率最高，支持大文件；与 FastAPI 原生集成；进度追踪能力强
- **实现细节**:
  ```python
  # 使用 UploadFile 和 shutil.copyfileobj
  # 分块大小: 1MB
  # 最大文件: 500MB
  # 内存占用: ~1-2MB (固定)
  ```
- **备选方案**: 如果需要文件永久存储，升级到 S3/MinIO
- **性能指标**: 500MB 文件处理 <30 秒，内存占用 <100MB

---

### 3. CSV/Excel 文件解析

**研究问题**: 选择最合适的 Python 库来解析 CSV 和 Excel 文件，同时保持高性能和准确的数据类型推断？

**评估的库**:
- **pandas**: 功能完整，但内存占用大
- **openpyxl**: Excel 专用，轻量级
- **csv 模块**: Python 标准库，仅支持 CSV
- **polars**: 高性能，但依赖较重

**决策**: pandas (仅用于元数据) + csv/openpyxl (用于数据处理)
- **原因**:
  - pandas: 快速开发，数据类型推断优秀
  - csv/openpyxl: 流式处理，内存高效
  - 组合方案平衡功能和性能
- **技术方案**:
  ```python
  # CSV: 使用 csv.DictReader + 类型推断函数
  # Excel: 使用 openpyxl + 迭代读取
  # 数据类型推断: 自定义函数检测 int/float/date/str
  ```
- **性能指标**: 100MB 文件解析 <10 秒

---

### 4. 凭据加密 (AES-256)

**研究问题**: 如何安全地存储和检索 PostgreSQL 数据库凭据，使用 AES-256 加密？

**评估的选项**:
- **Option A**: Python cryptography 库 (Fernet)
- **Option B**: Python cryptography 库 (AES-256)
- **Option C**: 外部密钥管理服务 (AWS KMS, HashiCorp Vault)

**决策**: Option B - cryptography 库的 AES-256
- **原因**:
  - 满足 AES-256 要求
  - 无外部依赖，部署简单
  - Fernet 自动处理 IV/盐，但限制性强
  - AES-256 提供更灵活的配置
- **实现方案**:
  ```python
  from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
  from cryptography.hazmat.backends import default_backend

  # 密钥生成: os.urandom(32) - 256 位
  # IV: os.urandom(16) - 128 位
  # 模式: CBC (标准，稳定)
  # 填充: PKCS7
  ```
- **密钥存储**: 环境变量 `ENCRYPTION_KEY` (生产环境升级到密钥管理系统)
- **安全性检查**:
  - 密钥绝不在日志中输出
  - 加密/解密功能单元测试覆盖
  - 凭据在数据库中始终加密存储

---

### 5. 前端状态管理 (Zustand)

**研究问题**: 如何使用 Zustand 设计数据源管理的状态结构，支持多个并发数据源？

**评估的方案**:
- **Option A**: 单个全局 store (useDataSourceStore)
- **Option B**: 多个专用 store (分离关注)
- **Option C**: Context API + Zustand 混合

**决策**: Option A + Option B 的混合方案
- **Store 1: `useDataSourceStore`**
  ```typescript
  {
    dataSources: DataSource[],
    selectedId: string | null,
    isLoading: boolean,
    error: string | null,
    actions: {
      fetchDataSources(),
      selectDataSource(id),
      addDataSource(config),
      removeDataSource(id),
      testConnection(config)
    }
  }
  ```
- **Store 2: `useSchemaStore`**
  ```typescript
  {
    schemas: Record<string, Schema>,
    isLoading: boolean,
    error: string | null,
    actions: {
      fetchSchema(dataSourceId),
      clearSchema(dataSourceId)
    }
  }
  ```
- **优势**:
  - 单一职责原则
  - 易于测试
  - 性能优化 (选择性订阅)
  - 缓存数据源和模式分离

---

### 6. 文件上传进度跟踪

**研究问题**: 如何在前端显示实时的文件上传进度，提供良好的用户体验？

**技术方案**:
- 后端: 返回 `Content-Length` 和流式响应
- 前端: 使用 XMLHttpRequest `progress` 事件或 fetch with ReadableStream
- 状态管理: Zustand store 中追踪上传进度

**推荐实现**:
```typescript
// 使用 XMLHttpRequest (最兼容)
const xhr = new XMLHttpRequest();
xhr.upload.addEventListener('progress', (e) => {
  const percent = (e.loaded / e.total) * 100;
  updateProgress(percent);
});
```

---

### 7. 数据库模式缓存策略

**研究问题**: 如何实现 5 分钟的模式缓存以优化性能，同时保持数据新鲜度？

**技术方案**:
- 缓存工具: Python 内置 functools.lru_cache 或 Redis
- MVP 方案: lru_cache (内存缓存，足够初期使用)
- 缓存键: `(data_source_id, timestamp_bucket)`
- 缓存失效: 时间或手动刷新

```python
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=10)
async def get_schema_cached(
    data_source_id: str,
    cache_time: int  # 时间戳分桶 (5分钟)
) -> Schema:
    return await fetch_schema_from_db(data_source_id)
```

---

## 技术栈确认

### 后端
- **框架**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0+ (异步)
- **数据库驱动**: asyncpg (PostgreSQL 异步驱动)
- **文件处理**: openpyxl, csv (标准库)
- **加密**: cryptography 41.0+
- **验证**: pydantic v2
- **测试**: pytest, pytest-asyncio

### 前端
- **框架**: React 18+
- **语言**: TypeScript 5.0+
- **状态管理**: Zustand 4.4+
- **HTTP 客户端**: React Query 5.0+ (TanStack Query)
- **UI 组件**: shadcn/ui, Tremor
- **样式**: Tailwind CSS 3.0+
- **表单**: React Hook Form 7.0+
- **测试**: Vitest, React Testing Library

---

## 已解决的技术不确定性

| 不确定性 | 决策 | 风险 | 缓解措施 |
|--------|------|-----|--------|
| 连接池策略 | SQLAlchemy 异步连接池 | 连接耗尽 | 配置 pool_size=5, max_overflow=10 |
| 大文件处理 | 流式分块处理 | 内存溢出 | 1MB 块大小，内存占用固定 |
| CSV/Excel 解析 | pandas + csv/openpyxl | 性能下降 | 流式处理，避免全文件加载 |
| 凭据加密 | cryptography AES-256 | 密钥泄露 | 环境变量管理，升级路线到密钥管理系统 |
| 前端状态 | Zustand 双 store 方案 | 状态不同步 | 单向数据流，明确的 action 定义 |
| 缓存策略 | lru_cache (MVP) | 内存占用 | 最大缓存 10 个数据源，5 分钟过期 |

---

## 性能和安全性目标

### 性能指标
- ✅ PostgreSQL 连接建立: <100ms
- ✅ 500MB 文件上传: <30 秒
- ✅ 100MB 文件解析: <10 秒
- ✅ 模式查询 (1000 表): <5 秒
- ✅ 仪表板加载: <1 秒

### 安全性指标
- ✅ 凭据加密: AES-256
- ✅ 密钥管理: 环境变量 (MVP) → 密钥管理系统 (生产)
- ✅ 日志安全: 凭据绝不记录
- ✅ SQL 注入防护: 参数化查询 (SQLAlchemy ORM)
- ✅ 文件验证: 类型和大小检查

---

## 后续步骤

1. **阶段 1**: 根据本研究创建数据模型和 API 契约
2. **阶段 2**: 生成具体的实现任务
3. **开发**: 按优先级实现后端服务和前端组件

**研究完成**: ✅
**所有 [NEEDS CLARIFICATION] 已解决**: ✅
**准备进入阶段 1 设计**: ✅
