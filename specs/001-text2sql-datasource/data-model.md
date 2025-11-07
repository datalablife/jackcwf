# 数据模型规范: 数据源集成

**特性**: 001-text2sql-datasource
**日期**: 2025-11-07
**版本**: 1.0

---

## 概述

本文档定义了数据源集成功能所需的所有数据模型、关系和约束。

---

## 核心实体

### 1. DataSource (数据源)

**用途**: 代表一个已连接的数据源 (PostgreSQL 或文件)

**表名**: `data_sources`

| 字段 | 类型 | 约束 | 说明 |
|------|------|-----|------|
| `id` | UUID | PK | 唯一标识符 |
| `user_id` | UUID | FK (users) | 所有者 |
| `name` | VARCHAR(255) | NOT NULL | 用户友好的名称 |
| `type` | ENUM | NOT NULL | 类型: 'postgresql', 'csv', 'excel' |
| `status` | ENUM | NOT NULL, DEFAULT: 'connected' | 状态: 'connected', 'disconnected', 'error' |
| `description` | TEXT | - | 可选描述 |
| `created_at` | TIMESTAMP | NOT NULL | 创建时间 |
| `updated_at` | TIMESTAMP | NOT NULL | 更新时间 |
| `last_tested_at` | TIMESTAMP | - | 最后测试时间 |
| `test_result` | BOOLEAN | - | 最后测试是否成功 |

**验证规则**:
- `name` 长度: 1-255 字符
- `type` 必须是允许的值之一
- 同一用户不允许重复的 `name`
- 创建时 `status` 默认为 'connected'

**索引**:
- `(user_id, created_at)` - 用户的数据源列表查询
- `(user_id, name)` - 数据源名称查询
- `(status)` - 连接状态过滤

---

### 2. DatabaseConnection (数据库连接)

**用途**: 存储 PostgreSQL 特定的连接信息

**表名**: `database_connections`

| 字段 | 类型 | 约束 | 说明 |
|------|------|-----|------|
| `id` | UUID | PK | 唯一标识符 |
| `data_source_id` | UUID | FK (data_sources), NOT NULL, UNIQUE | 关联的数据源 |
| `host` | VARCHAR(255) | NOT NULL | 主机地址 |
| `port` | INTEGER | NOT NULL, DEFAULT: 5432 | 端口号 |
| `database` | VARCHAR(255) | NOT NULL | 数据库名称 |
| `username` | VARCHAR(255) | NOT NULL | 用户名 (明文) |
| `password_encrypted` | BYTEA | NOT NULL | 加密的密码 (AES-256) |
| `ssl_enabled` | BOOLEAN | DEFAULT: false | 是否启用 SSL |
| `connection_timeout` | INTEGER | DEFAULT: 30 | 连接超时 (秒) |
| `last_connected_at` | TIMESTAMP | - | 最后成功连接时间 |
| `last_connection_error` | TEXT | - | 最后连接错误 |

**加密策略**:
- 密码使用 AES-256 加密，密钥来自 `ENCRYPTION_KEY` 环境变量
- 用户名以明文存储 (用于连接字符串生成)
- 所有加密/解密操作在应用层进行

**验证规则**:
- `host` 格式: 有效的域名或 IP 地址
- `port` 范围: 1-65535
- `database` 长度: 1-63 字符 (PostgreSQL 限制)
- `username` 长度: 1-63 字符
- `password_encrypted` 长度: >0

**关系**:
- 1:1 关系到 `DataSource`

---

### 3. FileUpload (文件上传)

**用途**: 存储上传文件的元数据

**表名**: `file_uploads`

| 字段 | 类型 | 约束 | 说明 |
|------|------|-----|------|
| `id` | UUID | PK | 唯一标识符 |
| `data_source_id` | UUID | FK (data_sources), NOT NULL, UNIQUE | 关联的数据源 |
| `original_filename` | VARCHAR(255) | NOT NULL | 原始文件名 |
| `file_type` | ENUM | NOT NULL | 类型: 'csv', 'excel' |
| `file_size` | BIGINT | NOT NULL | 文件大小 (字节) |
| `row_count` | INTEGER | - | 行数 (解析后) |
| `column_count` | INTEGER | - | 列数 |
| `uploaded_at` | TIMESTAMP | NOT NULL | 上传时间 |
| `expires_at` | TIMESTAMP | NOT NULL | 过期时间 (会话结束) |
| `content_hash` | VARCHAR(64) | - | SHA-256 哈希 (去重) |
| `temporary_path` | VARCHAR(255) | - | 临时文件路径 |

**验证规则**:
- `file_size` 范围: 1 - 536870912 字节 (500MB)
- `file_type` 必须是 'csv' 或 'excel'
- `row_count`, `column_count` 在解析后填充
- `expires_at` = 当前时间 + 会话持续时间

**关系**:
- 1:1 关系到 `DataSource`

---

### 4. Schema (数据库模式)

**用途**: 缓存数据库的表和列信息

**表名**: `schemas`

| 字段 | 类型 | 约束 | 说明 |
|------|------|-----|------|
| `id` | UUID | PK | 唯一标识符 |
| `data_source_id` | UUID | FK (data_sources), NOT NULL | 关联的数据源 |
| `table_name` | VARCHAR(255) | NOT NULL | 表名 |
| `columns` | JSONB | NOT NULL | 列定义 (JSON) |
| `primary_keys` | JSONB | - | 主键列表 (JSON) |
| `foreign_keys` | JSONB | - | 外键关系 (JSON) |
| `row_count` | BIGINT | - | 行数 (统计) |
| `created_at` | TIMESTAMP | NOT NULL | 缓存创建时间 |
| `expires_at` | TIMESTAMP | NOT NULL | 缓存过期时间 (创建时间 + 5 分钟) |

**列定义格式** (JSON):
```json
{
  "columns": [
    {
      "name": "id",
      "data_type": "integer",
      "nullable": false,
      "default": null
    },
    {
      "name": "email",
      "data_type": "varchar",
      "nullable": true,
      "default": null
    }
  ]
}
```

**主要数据类型映射**:
- PostgreSQL: integer → 'integer', varchar → 'text', timestamp → 'datetime', numeric → 'float'
- CSV/Excel: 自动推断为 'text', 'integer', 'float', 'datetime'

**缓存策略**:
- 过期时间: 创建时间 + 5 分钟
- 手动刷新: 调用 `GET /api/datasources/{id}/schema?refresh=true`
- 清理任务: 后台任务删除过期缓存

**关系**:
- N:1 关系到 `DataSource` (一个数据源可有多个表的缓存)

**索引**:
- `(data_source_id, table_name)` - 表查询
- `(expires_at)` - 缓存过期清理

---

### 5. DataSourceConfig (用户配置)

**用途**: 存储用户对数据源的偏好设置

**表名**: `data_source_configs`

| 字段 | 类型 | 约束 | 说明 |
|------|------|-----|------|
| `id` | UUID | PK | 唯一标识符 |
| `user_id` | UUID | FK (users), NOT NULL, UNIQUE | 用户 |
| `default_data_source_id` | UUID | FK (data_sources) | 默认数据源 |
| `last_selected_id` | UUID | FK (data_sources) | 最后选中的数据源 |
| `auto_refresh_schema` | BOOLEAN | DEFAULT: false | 是否自动刷新模式 |
| `schema_cache_ttl` | INTEGER | DEFAULT: 300 | 模式缓存 TTL (秒) |

**关系**:
- 1:1 关系到 `users` (未来的用户表)
- N:1 关系到 `DataSource` (通过外键)

---

## 关系图

```
users (假设存在)
  ↓
  ├→ data_sources (1:N)
  │   ├→ database_connections (1:1)
  │   ├→ file_uploads (1:1)
  │   └→ schemas (1:N)
  │
  └→ data_source_configs (1:1)
      ├→ default_data_source_id (FK)
      └→ last_selected_id (FK)
```

---

## 数据状态流

### DataSource 状态转换

```
           ┌─────────────────┐
           │    Created      │
           │  (connected)    │
           └────────┬────────┘
                    │
         ┌──────────┴──────────┐
         ↓                     ↓
    ┌─────────┐          ┌──────────┐
    │Connected│          │ Error    │
    └────┬────┘          └──────┬───┘
         │                      │
         └──────────┬───────────┘
                    ↓
             ┌────────────┐
             │Disconnected│
             └────────────┘
```

### 文件上传状态流

```
┌──────────┐    ┌──────────┐    ┌────────┐
│ Uploading│ →  │ Validating│ →  │ Ready  │
└──────────┘    └──────────┘    └────┬───┘
                                     ↓
                              ┌────────────┐
                              │ Expired    │
                              └────────────┘
```

---

## API 数据模型

### 请求模型

```typescript
// 创建 PostgreSQL 连接
interface CreatePostgresRequest {
  name: string;
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  ssl_enabled?: boolean;
}

// 上传文件
interface UploadFileRequest {
  name: string;
  file: File;
}

// 测试连接
interface TestConnectionRequest {
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
}
```

### 响应模型

```typescript
// 数据源响应
interface DataSourceResponse {
  id: string;
  name: string;
  type: 'postgresql' | 'csv' | 'excel';
  status: 'connected' | 'disconnected' | 'error';
  description?: string;
  created_at: string;
  last_tested_at?: string;
  test_result?: boolean;
}

// 模式响应
interface SchemaResponse {
  table_name: string;
  columns: Column[];
  primary_keys?: string[];
  foreign_keys?: ForeignKey[];
  row_count?: number;
}

interface Column {
  name: string;
  data_type: string;
  nullable: boolean;
  default?: any;
}
```

---

## 数据库迁移计划

### 初始迁移 (Migration 001)

创建以下表:
1. `data_sources`
2. `database_connections`
3. `file_uploads`
4. `schemas`
5. `data_source_configs`

工具: Alembic (SQLAlchemy 迁移)

### 索引和约束

```sql
-- 外键约束
ALTER TABLE database_connections
  ADD CONSTRAINT fk_database_connections_data_source_id
  FOREIGN KEY (data_source_id) REFERENCES data_sources(id) ON DELETE CASCADE;

-- 唯一约束
ALTER TABLE database_connections
  ADD CONSTRAINT uk_database_connections_data_source_id
  UNIQUE (data_source_id);

-- 复合索引
CREATE INDEX idx_data_sources_user_id_created_at
  ON data_sources(user_id, created_at);

CREATE INDEX idx_schemas_expires_at
  ON schemas(expires_at);
```

---

## 扩展点和注意事项

### MVP 阶段限制
- 文件存储在临时目录，会话结束后删除
- 不支持文件版本控制
- 不支持数据源权限管理（单用户假设）

### 未来升级路径
1. **持久文件存储**: 迁移到 S3/MinIO，添加 `file_storage_path` 字段
2. **权限管理**: 添加 `access_control` 表，支持共享和权限
3. **数据源变更历史**: 添加 `data_source_changelog` 表，审计所有连接变更
4. **更新通知**: 实现 WebSocket 支持，实时推送模式更新
5. **多租户支持**: 添加 `tenant_id` 字段，支持 SaaS 部署

---

## 性能考虑

### 查询优化
- 模式缓存: 避免频繁的数据库元信息查询
- 连接池: 避免连接建立开销
- 索引策略: 按查询模式优化索引

### 数据量估计
| 表 | 初期行数 | 增长率 | 1年预测 |
|----|---------|--------|--------|
| data_sources | 5-10 | 每月+10% | ~200 |
| schemas | 100 | 每月+5% | ~600 |
| file_uploads | 10 | 每月+20% | ~600 |

---

## 安全考虑

### 数据保护
- 密码加密: AES-256
- 传输加密: HTTPS (应用层强制)
- 访问控制: user_id 行级安全

### 审计日志
- 所有连接操作记录
- 文件上传路径记录
- 凭据修改不可追溯（设计要求）

---

## 测试数据

### 示例 PostgreSQL 连接
```json
{
  "name": "Coolify Production",
  "host": "host.docker.internal",
  "port": 5432,
  "database": "postgres",
  "username": "jackcwf888",
  "password": "encrypted_value",
  "ssl_enabled": false
}
```

### 示例 CSV 文件上传
```json
{
  "name": "User Analytics",
  "file_type": "csv",
  "file_size": 1024000,
  "row_count": 10000,
  "column_count": 5
}
```

---

**文档完成**: ✅
**模型验证**: ✅
**数据库设计就绪**: ✅
