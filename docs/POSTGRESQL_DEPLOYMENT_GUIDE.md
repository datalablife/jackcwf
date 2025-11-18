# PostgreSQL 远程数据库部署指南

**项目**: LangChain AI Conversation Backend  
**数据库**: Coolify 托管的 PostgreSQL + pgvector  
**创建日期**: 2025-11-18  
**状态**: ✅ 生产就绪

---

## 🔒 安全基础

本指南遵循以下安全原则：

```
✅ 所有凭证来自环境变量
✅ 代码中不包含敏感信息
✅ .env 文件不提交到 Git
✅ 清晰的错误消息，不暴露凭证
✅ 不同环境使用独立的凭证
```

---

## 📍 您的 Coolify PostgreSQL 信息

根据 `.env` 文件中的配置：

| 配置项 | 值 |
|--------|-----|
| **应用 UUID** | ok0s0cgw8ck0w8kgs8kk4kk8 |
| **应用名** | docker-image-ok0s0cgw8ck0w8kgs8kk4kk8 |
| **FQDN** | https://pgvctor.jackcwf.com |
| **用户名** | jackcwf888 |
| **端口** | 5432 |
| **数据库** | postgres |

⚠️ **重要**: 密码存储在 `.env` 文件中，不在本指南中显示

---

## 🚀 快速开始

### 第 1 步：配置环境变量

```bash
# 1. 如果还没有 .env 文件，从模板创建
cp .env.example .env

# 2. 编辑 .env 文件并设置正确的值
# 对于 Coolify 上的远程 PostgreSQL，您需要：
#
# DATABASE_URL=postgresql+asyncpg://jackcwf888:YOUR_PASSWORD@ACTUAL_HOST:5432/postgres
#
# 其中：
#   - YOUR_PASSWORD: 从 Coolify 控制面板获取
#   - ACTUAL_HOST: Coolify 提供的实际 IP 或域名（不是 host.docker.internal）
```

### 第 2 步：验证配置

```bash
# 验证所有必需的环境变量都已设置
python scripts/validate_env.py

# 输出应该显示：
# ✅ DATABASE_URL is configured
# ✅ POSTGRES_HOST is configured
# ✅ POSTGRES_PORT is configured
# ✅ POSTGRES_USER is configured
# ✅ POSTGRES_DB is configured
```

### 第 3 步：测试数据库连接

```bash
# 运行远程数据库设置脚本
python src/db/setup_remote_db.py

# 脚本会：
# 1. 测试与 PostgreSQL 的连接
# 2. 检查 pgvector 扩展
# 3. 验证数据库权限
# 4. 显示数据库统计信息
```

### 第 4 步：初始化数据库

```bash
# 运行数据库迁移
alembic upgrade head

# 或使用 Python
python src/db/migrations.py
```

---

## 🔌 连接配置详解

### 本地开发 (Docker)

如果您在 Docker 容器中运行 LangChain 应用，并且 PostgreSQL 在同一 Docker 网络中：

```env
DATABASE_URL=postgresql+asyncpg://jackcwf888:PASSWORD@host.docker.internal:5432/postgres
POSTGRES_HOST=host.docker.internal
POSTGRES_PORT=5432
POSTGRES_USER=jackcwf888
POSTGRES_DB=postgres
```

### 生产环境 (远程 Coolify)

对于 Coolify 上的远程 PostgreSQL 部署：

```env
# 首先，从 Coolify 控制面板获取实际的 PostgreSQL 主机信息
# https://coolpanel.jackcwf.com -> 应用详情 -> PostgreSQL 连接信息

DATABASE_URL=postgresql+asyncpg://jackcwf888:PASSWORD@ACTUAL_IP_OR_DOMAIN:5432/postgres
POSTGRES_HOST=ACTUAL_IP_OR_DOMAIN
POSTGRES_PORT=5432
POSTGRES_USER=jackcwf888
POSTGRES_DB=postgres
```

### 使用 SSH 隧道 (安全的远程访问)

对于更安全的远程连接：

```bash
# 1. 建立 SSH 隧道到 Coolify 服务器
ssh -L 5432:localhost:5432 user@coolify.server.com &

# 2. 在 .env 中使用本地连接
DATABASE_URL=postgresql+asyncpg://jackcwf888:PASSWORD@localhost:5432/postgres
POSTGRES_HOST=localhost
```

---

## 📋 获取实际的 PostgreSQL 连接信息

### 方法 1: 通过 Coolify 网页界面

```
1. 访问 https://coolpanel.jackcwf.com
2. 使用凭证登录
3. 导航到应用管理
4. 找到 PostgreSQL 应用 (ok0s0cgw8ck0w8kgs8kk4kk8)
5. 查看"连接信息"或"环境变量"
6. 复制 POSTGRES_HOST 的实际值（IP 地址或域名）
7. 确认端口（通常是 5432）
```

### 方法 2: 通过 Coolify CLI

```bash
# 获取应用详细信息（需要 Coolify CLI 配置）
coolify app show ok0s0cgw8ck0w8kgs8kk4kk8 --show-sensitive --format json

# 查找 POSTGRES_HOST 字段中的实际主机值
```

### 方法 3: 测试连接

```bash
# 使用 psql 测试连接（需要安装 PostgreSQL 客户端）
psql -h <POSTGRES_HOST> -U jackcwf888 -d postgres -c "SELECT version();"

# 系统会提示输入密码
# 如果连接成功，您将看到 PostgreSQL 版本信息
```

---

## ✅ 验证 pgvector 扩展

pgvector 是向量搜索所必需的：

```sql
-- 登录到 PostgreSQL
psql -h <POSTGRES_HOST> -U jackcwf888 -d postgres

-- 检查是否已安装
SELECT extname FROM pg_extension WHERE extname = 'vector';

-- 如果未安装，创建扩展（需要超级用户权限）
CREATE EXTENSION IF NOT EXISTS vector;

-- 验证
SELECT version FROM pg_extension WHERE extname = 'vector';
```

---

## 🛡️ 安全清单

### 开发环境

- [ ] `.env` 文件已创建（从 `.env.example`）
- [ ] `.env` 文件在 `.gitignore` 中
- [ ] 所有凭证已从 `.env` 中正确设置
- [ ] 运行 `python scripts/validate_env.py` 通过验证
- [ ] 运行 `python src/db/setup_remote_db.py` 成功连接

### 生产环境

- [ ] 从 Coolify 控制面板获得实际的 PostgreSQL 主机 IP
- [ ] 密码已从 Coolify 获取并设置在环境变量中
- [ ] 防火墙规则允许从应用服务器到 PostgreSQL 的连接
- [ ] 使用 SSH 隧道或 VPN 进行远程访问（推荐）
- [ ] 定期备份数据库（每天或每周）
- [ ] 监控数据库性能和连接数
- [ ] 设置告警（CPU、磁盘、连接数）

### 持续检查

- [ ] 定期审计 git 历史中是否有泄露的凭证
- [ ] 每 90 天轮换一次数据库密码
- [ ] 检查 PostgreSQL 日志中的异常活动
- [ ] 定期更新 PostgreSQL 和 pgvector 版本

---

## 🔧 常见问题

### Q: 如何获得实际的 PostgreSQL 主机地址？

**A**: 您需要从 Coolify 控制面板获取：
1. 访问 https://coolpanel.jackcwf.com
2. 进入应用详情
3. 查找 PostgreSQL 的"公共地址"或"连接信息"
4. 这通常是一个 IP 地址（如 `47.79.87.199`）或域名

### Q: 为什么连接超时？

**A**: 检查以下几点：
1. PostgreSQL 服务是否在运行？
2. 防火墙是否允许端口 5432 的连接？
3. 主机地址是否正确？
4. 端口是否正确（通常是 5432）？
5. 用户名和密码是否正确？

### Q: pgvector 扩展未找到

**A**: 
1. 确认 PostgreSQL 版本 ≥ 12
2. Coolify PostgreSQL 应该已预装 pgvector
3. 如果未安装，需要超级用户权限来创建扩展
4. 联系 Coolify 支持确保 pgvector 已启用

### Q: 如何安全地管理生产密码？

**A**: 对于生产环境，不要在 `.env` 文件中存储密码：
1. 使用 AWS Secrets Manager、Azure Key Vault 等
2. 使用 Coolify 的环境变量管理功能
3. 使用 SSH 隧道进行远程访问
4. 定期轮换密码

---

## 📚 相关文档

- **安全数据库设置**: `docs/SECURE_DATABASE_SETUP.md`
- **安全审计**: `scripts/git_security_audit.py`
- **环境验证**: `scripts/validate_env.py`
- **数据库设置**: `src/db/setup_remote_db.py`
- **数据库配置**: `src/db/config.py`

---

## 🚨 紧急情况

### 如果凭证被泄露：

```bash
# 1. 立即更改 Coolify PostgreSQL 密码
# (通过 Coolify 控制面板)

# 2. 更新本地 .env 文件
# 编辑 DATABASE_URL 中的密码

# 3. 审计 git 历史中是否有泄露
python scripts/git_security_audit.py --recent

# 4. 如果有泄露，使用 git-filter-branch 或 BFG 移除
# (需要谨慎操作)

# 5. 通知所有用户
# 重新生成 API 密钥和令牌
```

---

## 📞 获取帮助

1. **连接问题**: 
   - 检查 POSTGRES_HOST 是否正确
   - 使用 `psql` 命令行测试连接
   - 查看 firewall 和网络设置

2. **性能问题**:
   - 监控 PostgreSQL 进程
   - 检查 pgvector 索引
   - 查看慢查询日志

3. **pgvector 问题**:
   - 验证扩展已安装
   - 检查向量列的维度（应该是 1536）
   - 查看扩展版本

4. **Coolify 特定问题**:
   - 访问 https://coolpanel.jackcwf.com
   - 查看应用日志
   - 查看 PostgreSQL 容器的状态

---

**最后更新**: 2025-11-18  
**维护者**: Claude Code  
**版本**: 1.0 - 生产就绪
