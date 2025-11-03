# PostgreSQL 数据库连接指南

本文档说明如何连接到在 Coolify 中部署的 PostgreSQL 数据库实例。

## 部署信息

### 应用基本信息

| 项目 | 值 |
|------|-----|
| **应用名称** | docker-image-ok0s0cgw8ck0w8kgs8kk4kk8 |
| **应用 UUID** | ok0s0cgw8ck0w8kgs8kk4kk8 |
| **Docker 镜像** | lanterndata/lantern-suite:pg15-latest |
| **镜像类型** | PostgreSQL 15 + Lantern (pgvector 扩展) |
| **状态** | running:unhealthy |
| **FQDN** | https://pgvctor.jackcwf.com |
| **创建时间** | 2025-10-24 08:27:41 UTC |

### 数据库凭证

| 项目 | 值 |
|------|-----|
| **用户名** | `jackcwf888` |
| **密码** | `Jack_00492300` |
| **数据库** | `postgres` |

### 网络配置

| 项目 | 值 |
|------|-----|
| **端口** | 5432 (PostgreSQL 标准端口) |
| **Docker 网络** | coolify |
| **服务器** | localhost (Coolify 运行主机) |
| **IP 地址** | host.docker.internal |

## 连接方式

### 方式 1: 使用 psql 命令行客户端

```bash
# 使用环境变量
export PGHOST=host.docker.internal
export PGPORT=5432
export PGDATABASE=postgres
export PGUSER=jackcwf888
export PGPASSWORD=Jack_00492300

psql

# 或直接连接
psql -h host.docker.internal -p 5432 -U jackcwf888 -d postgres

# 输入密码: Jack_00492300
```

### 方式 2: 使用连接字符串 (Python)

```python
import psycopg2

connection_string = "postgresql://jackcwf888:Jack_00492300@host.docker.internal:5432/postgres"

# 使用 psycopg2
conn = psycopg2.connect(connection_string)

# 或分别指定参数
conn = psycopg2.connect(
    host="host.docker.internal",
    port=5432,
    database="postgres",
    user="jackcwf888",
    password="Jack_00492300"
)
```

### 方式 3: 使用 SQLAlchemy (Python)

```python
from sqlalchemy import create_engine

database_url = "postgresql://jackcwf888:Jack_00492300@host.docker.internal:5432/postgres"
engine = create_engine(database_url)

# 测试连接
with engine.connect() as connection:
    result = connection.execute("SELECT 1")
    print(result.fetchone())
```

### 方式 4: 使用 Node.js (pg 库)

```javascript
const { Client } = require('pg');

const client = new Client({
  user: 'jackcwf888',
  password: 'Jack_00492300',
  host: 'host.docker.internal',
  port: 5432,
  database: 'postgres',
});

client.connect((err) => {
  if (err) console.error(err);
  else console.log('Connected!');
});
```

### 方式 5: 使用 DBeaver (GUI 工具)

1. 新建数据库连接 → PostgreSQL
2. 配置连接参数：
   - **Server Host**: host.docker.internal
   - **Port**: 5432
   - **Database**: postgres
   - **Username**: jackcwf888
   - **Password**: Jack_00492300
3. 测试连接
4. 保存连接

### 方式 6: 使用 pgAdmin 4

1. 访问 pgAdmin 4 管理界面
2. 新建服务器：
   - **Name**: My PostgreSQL
   - **Host name/address**: host.docker.internal
   - **Port**: 5432
   - **Maintenance database**: postgres
   - **Username**: jackcwf888
   - **Password**: Jack_00492300
3. 保存

## 环境配置文件

项目根目录已创建 `.postgres_config` 文件，包含所有连接参数。

```bash
# 加载配置
source .postgres_config

# 使用环境变量连接
psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB
```

## 测试连接

### 使用 psql 测试

```bash
psql -h host.docker.internal -p 5432 -U jackcwf888 -d postgres -c "SELECT version();"
```

### 使用 Python 测试

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行测试脚本
python test_postgres_connection.py
```

### 使用 coolify-cli 查询应用状态

```bash
# 查看应用状态
coolify app get ok0s0cgw8ck0w8kgs8kk4kk8

# 查看应用日志
coolify app logs ok0s0cgw8ck0w8kgs8kk4kk8

# 查看环境变量
coolify app env list ok0s0cgw8ck0w8kgs8kk4kk8 --show-sensitive
```

## 关键信息

### ⚠️ 重要注意

1. **Lantern PostgreSQL**: 该实例运行的是 Lantern Suite，包含 pgvector 扩展用于向量相似度搜索

2. **默认 postgres 角色**: 日志显示默认的 `postgres` 角色不存在，请使用 `jackcwf888` 用户连接

3. **Docker 网络**:
   - 在 Coolify 容器内部访问：使用 `localhost:5432`
   - 从主机访问：使用 `host.docker.internal:5432`

4. **HTTPS FQDN**:
   - `https://pgvctor.jackcwf.com` 仅用于 HTTP Traefik 路由
   - **不是** PostgreSQL 连接地址

5. **健康检查**: 当前设置中未启用健康检查，这可能导致 unhealthy 状态

6. **端口映射**: Docker 容器的 5432 端口映射到主机的 5432 端口

### ✓ 已验证的信息

从 Coolify 获取的应用信息已保存到：
- 连接配置: `.postgres_config`
- 凭证安全性: 密码存储在本地文件中（不要提交到 Git）
- 应用 UUID: ok0s0cgw8ck0w8kgs8kk4kk8
- 环境变量: 已通过 `coolify app env list` 验证

## 故障排除

### 连接拒绝 (Connection refused)

**原因**: PostgreSQL 服务未运行或端口不可访问

**解决方案**:
```bash
# 1. 检查 Coolify 应用是否运行
coolify app list

# 2. 重启应用
coolify app restart ok0s0cgw8ck0w8kgs8kk4kk8

# 3. 查看应用日志
coolify app logs ok0s0cgw8ck0w8kgs8kk4kk8
```

### 认证失败

**原因**: 用户名或密码错误

**解决方案**:
```bash
# 1. 验证凭证
coolify app env list ok0s0cgw8ck0w8kgs8kk4kk8 --show-sensitive

# 2. 确保使用正确的用户: jackcwf888
# 3. 确保使用正确的密码: Jack_00492300
```

### 主机未找到 (Host not found)

**原因**: `host.docker.internal` 在你的环境中不可用

**解决方案**:
- 在 WSL 中，尝试使用 `172.17.0.1` (Docker 网关)
- 在 Docker 中，尝试使用 `docker host ip`
- 在本地开发中，尝试 `localhost` 或 `127.0.0.1`

### 状态显示 unhealthy

**原因**: 未启用健康检查或检查失败

**解决方案**:
```bash
# 1. 应用仍在运行且可连接
psql -h host.docker.internal -p 5432 -U jackcwf888 -d postgres -c "SELECT 1;"

# 2. 在 Coolify 面板配置健康检查
# Settings → Health Check → Enable
```

## 相关命令参考

```bash
# 列出所有应用
coolify app list

# 获取应用详情
coolify app get ok0s0cgw8ck0w8kgs8kk4kk8

# 查看应用日志（最近 100 行）
coolify app logs ok0s0cgw8ck0w8kgs8kk4kk8

# 查看环境变量
coolify app env list ok0s0cgw8ck0w8kgs8kk4kk8 --show-sensitive

# 重启应用
coolify app restart ok0s0cgw8ck0w8kgs8kk4kk8

# 停止应用
coolify app stop ok0s0cgw8ck0w8kgs8kk4kk8

# 启动应用
coolify app start ok0s0cgw8ck0w8kgs8kk4kk8
```

## 扩展功能

### 查询 Lantern 向量扩展

```sql
-- 检查 pgvector 扩展
SELECT * FROM pg_extension WHERE extname = 'vector';

-- 创建向量列示例
CREATE TABLE embeddings (
    id SERIAL PRIMARY KEY,
    text TEXT,
    embedding vector(1536)
);

-- 使用 Lantern 索引优化查询
CREATE INDEX ON embeddings USING lantern (embedding dist_l2_ops);
```

### 备份和恢复

```bash
# 备份数据库
pg_dump -h host.docker.internal -U jackcwf888 -d postgres > backup.sql

# 恢复数据库
psql -h host.docker.internal -U jackcwf888 -d postgres < backup.sql
```

## 安全建议

⚠️ **重要安全警告**:

1. 不要将凭证提交到 Git，确保 `.postgres_config` 在 `.gitignore` 中
2. 定期更改数据库密码
3. 限制数据库访问只到需要的 IP 地址
4. 在生产环境中使用环境变量或密钥管理系统
5. 启用 PostgreSQL 审计日志跟踪数据库活动

## 参考资源

- [PostgreSQL 官方文档](https://www.postgresql.org/docs/)
- [psycopg2 文档](https://www.psycopg.org/psycopg2/)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [Lantern 官方网站](https://lantern.dev/)
- [Coolify 文档](https://coolify.io/docs)

---

**最后更新**: 2025-10-27
**来源**: Coolify CLI v1.0.3 API 查询
