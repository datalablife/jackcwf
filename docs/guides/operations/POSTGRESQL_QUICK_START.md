# PostgreSQL 快速开始指南

快速连接和管理 Coolify 部署的 PostgreSQL 数据库。

## 数据库凭证

```
主机: host.docker.internal
端口: 5432
用户: jackcwf888
密码: Jack_00492300
数据库: postgres
```

## 快速连接

### 方式 1: 命令行（推荐）

```bash
psql -h host.docker.internal -p 5432 -U jackcwf888 -d postgres
```

输入密码: `Jack_00492330`

### 方式 2: 使用管理脚本

```bash
# 查看信息
./coolify_postgres_manage.sh info

# 查看应用状态
./coolify_postgres_manage.sh status

# 启动交互式客户端
./coolify_postgres_manage.sh psql

# 查看应用日志
./coolify_postgres_manage.sh logs

# 测试连接
./coolify_postgres_manage.sh test
```

### 方式 3: Python

```python
import psycopg2

conn = psycopg2.connect(
    host="host.docker.internal",
    port=5432,
    database="postgres",
    user="jackcwf888",
    password="Jack_00492300"
)

with conn.cursor() as cur:
    cur.execute("SELECT version();")
    print(cur.fetchone())
```

## 常用命令

```bash
# 加载环境变量
source .postgres_config

# 使用环境变量连接
psql

# 查看所有数据库
\l

# 连接到特定数据库
\c database_name

# 列出所有表
\dt

# 执行 SQL 文件
\i /path/to/file.sql

# 导出查询结果
psql -c "SELECT * FROM table_name;" > output.txt

# 备份数据库
pg_dump -h host.docker.internal -U jackcwf888 -d postgres > backup.sql

# 恢复数据库
psql -h host.docker.internal -U jackcwf888 -d postgres < backup.sql

# 显示帮助
\h

# 退出
\q
```

## Coolify 管理

```bash
# 查看应用状态
coolify app list

# 查看详细信息
coolify app get ok0s0cgw8ck0w8kgs8kk4kk8

# 查看日志
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

## 应用信息

| 属性 | 值 |
|------|-----|
| **应用 UUID** | ok0s0cgw8ck0w8kgs8kk4kk8 |
| **Docker 镜像** | lanterndata/lantern-suite:pg15-latest |
| **PostgreSQL 版本** | 15 |
| **特殊功能** | pgvector (向量相似度搜索) |
| **状态** | running:unhealthy |
| **FQDN** | https://pgvctor.jackcwf.com |

## 文件说明

- **`.postgres_config`** - 环境变量配置文件
- **`POSTGRESQL_CONNECTION.md`** - 详细连接指南
- **`coolify_postgres_manage.sh`** - 管理脚本
- **`test_postgres_connection.py`** - Python 连接测试脚本

## 故障排除

### 连接失败

```bash
# 1. 验证应用运行状态
coolify app get ok0s0cgw8ck0w8kgs8kk4kk8

# 2. 查看应用日志
coolify app logs ok0s0cgw8ck0w8kgs8kk4kk8

# 3. 重启应用
coolify app restart ok0s0cgw8ck0w8kgs8kk4kk8
```

### 使用不同的连接地址

```bash
# Docker 容器内部
psql -h localhost -p 5432 -U jackcwf888 -d postgres

# Docker 网关
psql -h 172.17.0.1 -p 5432 -U jackcwf888 -d postgres

# 主机
psql -h host.docker.internal -p 5432 -U jackcwf888 -d postgres
```

## 下一步

1. 阅读 `POSTGRESQL_CONNECTION.md` 了解更多连接方式
2. 查看应用日志：`coolify app logs ok0s0cgw8ck0w8kgs8kk4kk8`
3. 在 Coolify 面板配置健康检查
4. 设置数据库备份策略
5. 创建额外的数据库和用户账号

---

**获取帮助**: 查看 CLAUDE.md 中的 Coolify CLI 管理规则部分
