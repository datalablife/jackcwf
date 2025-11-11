# 数据库配置指南 - Coolify PostgreSQL

**文档版本**: 1.0
**创建日期**: 2025-11-10
**用途**: 配置开发和生产环境的 PostgreSQL 数据库

---

## 📋 概述

本项目使用 Coolify 云部署平台托管的 PostgreSQL 数据库。已为开发环境和生产环境各创建一个数据库实例。

### 数据库信息

#### 开发环境 (Development)

| 属性 | 值 |
|------|-----|
| **UUID** | t8gkw0k8ko04s80kk884gsw4 |
| **数据库名** | data_management_dev |
| **用户名** | dev_user |
| **密码** | dev_password_123 |
| **主机** | host.docker.internal (Docker) / localhost (本地) |
| **端口** | 5432 (默认) |
| **服务器** | localhost (Coolify) |
| **状态** | running:starting ⏳ |

#### 生产环境 (Production)

| 属性 | 值 |
|------|-----|
| **UUID** | m8oss0o0448cgswsk4c8ck0g |
| **数据库名** | data_management_prod |
| **用户名** | prod_user |
| **密码** | prod_password_secure_123 |
| **主机** | host.docker.internal (Docker) / localhost (本地) |
| **端口** | 5432 (默认) |
| **服务器** | localhost (Coolify) |
| **状态** | running:starting ⏳ |

---

## 🔧 获取实际连接信息

由于 Coolify 会为每个数据库实例动态分配端口和地址，你需要通过 Coolify 面板获取实际的连接信息：

### 通过 Coolify 面板查看

1. 打开 Coolify 面板: https://coolpanel.jackcwf.com
2. 导航到 **Databases** → **PostgreSQL**
3. 选择对应的数据库实例：
   - `Data Management Dev` (开发)
   - `Data Management Prod` (生产)
4. 点击数据库信息，获取：
   - 实际主机名/IP
   - 实际端口号
   - 数据库名
   - 用户名
   - 密码 (显示敏感信息)

### 通过 Coolify CLI 查看

```bash
# 查看开发数据库详情
coolify --context myapp database get t8gkw0k8ko04s80kk884gsw4 -s

# 查看生产数据库详情
coolify --context myapp database get m8oss0o0448cgswsk4c8ck0g -s

# 列出所有数据库
coolify --context myapp database list
```

---

## 🔌 连接字符串

### 开发环境

基于 Coolify 分配的信息，连接字符串格式为：

```
postgresql://dev_user:dev_password_123@<HOST>:<PORT>/data_management_dev
```

**示例**:
```
postgresql://dev_user:dev_password_123@localhost:5432/data_management_dev
```

### 生产环境

```
postgresql://prod_user:prod_password_secure_123@<HOST>:<PORT>/data_management_prod
```

**示例**:
```
postgresql://prod_user:prod_password_secure_123@prod-db.example.com:5432/data_management_prod
```

---

## 🚀 配置文件

### 后端配置

#### 开发环境 (backend/.env)

```bash
# 从 Coolify 面板获取实际值后，更新以下内容
DATABASE_URL=postgresql://dev_user:dev_password_123@<实际主机>:<实际端口>/data_management_dev
```

#### 生产环境 (backend/.env.production)

```bash
# 从 Coolify 面板获取实际值后，更新以下内容
DATABASE_URL=postgresql://prod_user:prod_password_secure_123@<实际主机>:<实际端口>/data_management_prod
```

### 前端配置

#### 开发环境 (frontend/.env.development)

```bash
VITE_API_URL=http://localhost:8000
```

#### 生产环境 (frontend/.env.production)

```bash
VITE_API_URL=https://api.your-domain.com
```

---

## ✅ 测试连接

### 使用 psql 命令行工具

```bash
# 连接到开发数据库
psql postgresql://dev_user:dev_password_123@<HOST>:<PORT>/data_management_dev

# 连接到生产数据库
psql postgresql://prod_user:prod_password_secure_123@<HOST>:<PORT>/data_management_prod

# 执行测试查询
SELECT 1;  # 应返回 1
\dt         # 显示所有表
\q          # 退出
```

### 使用 Python

```python
import psycopg2

# 开发环境
conn = psycopg2.connect(
    host="<HOST>",
    port=<PORT>,
    database="data_management_dev",
    user="dev_user",
    password="dev_password_123"
)

cursor = conn.cursor()
cursor.execute("SELECT 1")
print(cursor.fetchone())  # 应输出 (1,)
conn.close()
```

### 使用 Node.js

```javascript
const { Client } = require('pg');

const client = new Client({
  host: '<HOST>',
  port: <PORT>,
  database: 'data_management_dev',
  user: 'dev_user',
  password: 'dev_password_123',
});

await client.connect();
const res = await client.query('SELECT 1');
console.log(res.rows); // [ { '?column?': 1 } ]
await client.end();
```

---

## 📊 管理数据库

### 查看数据库状态

```bash
# 检查开发数据库状态
coolify --context myapp database get t8gkw0k8ko04s80kk884gsw4

# 检查生产数据库状态
coolify --context myapp database get m8oss0o0448cgswsk4c8ck0g
```

### 重启数据库

```bash
# 重启开发数据库
coolify --context myapp database restart t8gkw0k8ko04s80kk884gsw4

# 重启生产数据库
coolify --context myapp database restart m8oss0o0448cgswsk4c8ck0g
```

### 停止数据库

```bash
# 停止开发数据库
coolify --context myapp database stop t8gkw0k8ko04s80kk884gsw4

# 停止生产数据库
coolify --context myapp database stop m8oss0o0448cgswsk4c8ck0g
```

### 启动数据库

```bash
# 启动开发数据库
coolify --context myapp database start t8gkw0k8ko04s80kk884gsw4

# 启动生产数据库
coolify --context myapp database start m8oss0o0448cgswsk4c8ck0g
```

---

## 🔒 安全建议

### 密码管理

**⚠️ 重要**: 当前使用的密码仅供开发使用

- 开发密码: `dev_password_123` (简单，仅用于开发)
- 生产密码: `prod_password_secure_123` (应使用更强密码)

**生产环境最佳实践**:
1. 使用强密码（至少 16 个字符，包含大小写、数字、符号）
2. 通过 Coolify 面板安全地存储和管理密码
3. 定期轮换密码
4. 不要在版本控制中提交实际密码

### 访问控制

```bash
# 查看所有用户
\du

# 修改密码
ALTER USER dev_user WITH PASSWORD 'new_password';

# 限制用户权限
GRANT CONNECT ON DATABASE data_management_dev TO dev_user;
REVOKE ALL PRIVILEGES ON DATABASE data_management_dev FROM public;
```

### 备份和恢复

```bash
# 备份数据库
pg_dump postgresql://dev_user:dev_password_123@<HOST>:<PORT>/data_management_dev > backup.sql

# 恢复数据库
psql postgresql://dev_user:dev_password_123@<HOST>:<PORT>/data_management_dev < backup.sql
```

---

## 🛠️ 故障排查

### 问题 1: 无法连接到数据库

**症状**: `connection refused` 或 `timeout`

**解决方案**:
1. 检查数据库状态: `coolify --context myapp database list`
2. 确保数据库状态为 `running` 而不是 `exited`
3. 验证主机名和端口是否正确
4. 检查防火墙规则是否允许连接
5. 确保用户名和密码正确

### 问题 2: 认证失败

**症状**: `FATAL: password authentication failed`

**解决方案**:
1. 验证用户名拼写正确
2. 确保密码正确（注意引号和特殊字符）
3. 如果密码包含特殊字符，使用 URL 编码
4. 通过 Coolify 面板重置用户密码

```bash
# URL 编码特殊字符（如果需要）
# 例如: password@123 → password%40123
postgresql://user:password%40123@host:5432/dbname
```

### 问题 3: 磁盘空间不足

**症状**: `disk space is low` 或 `no space left`

**解决方案**:
1. 清理旧数据或日志
2. 通过 Coolify 面板扩展存储空间
3. 检查并优化数据库大小:

```sql
-- 查看数据库大小
SELECT
  datname,
  pg_size_pretty(pg_database_size(datname))
FROM pg_database
ORDER BY pg_database_size(datname) DESC;

-- 查看表大小
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 问题 4: 连接过多

**症状**: `too many connections`

**解决方案**:
1. 检查活动连接:

```sql
SELECT pid, usename, application_name, state
FROM pg_stat_activity;

-- 终止特定连接
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE usename = 'dev_user' AND state != 'active';
```

2. 增加 max_connections 配置
3. 在应用中实现连接池

---

## 📚 数据库初始化

### 创建表结构

第一次连接时，需要创建应用所需的表。可以使用迁移工具：

```bash
# 使用 Alembic (FastAPI)
cd backend
alembic upgrade head

# 或使用 psycopg 直接执行脚本
psql postgresql://dev_user:dev_password_123@<HOST>:<PORT>/data_management_dev < schema.sql
```

### 导入初始数据

```bash
# 导入 SQL 数据
psql postgresql://dev_user:dev_password_123@<HOST>:<PORT>/data_management_dev < data.sql

# 或通过应用 API 导入
curl -X POST http://localhost:8000/api/seed-data
```

---

## 🔄 迁移到新环境

### 从开发迁移到生产

```bash
# 1. 备份开发数据库
pg_dump postgresql://dev_user:dev_password_123@dev-host:5432/data_management_dev > prod_data.sql

# 2. 恢复到生产数据库
psql postgresql://prod_user:prod_password_secure_123@prod-host:5432/data_management_prod < prod_data.sql

# 3. 验证数据
psql postgresql://prod_user:prod_password_secure_123@prod-host:5432/data_management_prod -c "SELECT COUNT(*) FROM your_table;"
```

---

## 📖 参考资源

- **PostgreSQL 官方文档**: https://www.postgresql.org/docs/
- **Coolify 文档**: https://coolify.io/docs
- **psycopg2 文档**: https://www.psycopg.org/
- **SQLAlchemy ORM**: https://docs.sqlalchemy.org/

---

## ✅ 配置检查清单

- [ ] 通过 Coolify 面板获取开发数据库的实际主机和端口
- [ ] 通过 Coolify 面板获取生产数据库的实际主机和端口
- [ ] 更新 `backend/.env` 中的 DATABASE_URL（开发）
- [ ] 更新 `backend/.env.production` 中的 DATABASE_URL（生产）
- [ ] 测试开发数据库连接
- [ ] 测试生产数据库连接
- [ ] 运行数据库迁移 (`alembic upgrade head`)
- [ ] 创建初始数据（如需要）
- [ ] 备份数据库配置和凭证到安全位置
- [ ] 在生产环境中使用强密码
- [ ] 配置定期备份任务

---

**最后更新**: 2025-11-10
**维护者**: Claude Code
**状态**: ✅ 完成
