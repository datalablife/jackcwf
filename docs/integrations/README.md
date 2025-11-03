# 集成文档

欢迎来到集成文档！本目录包含与第三方服务、数据库和 API 的集成指南。

## 📚 文档导航

### 🗄️ 数据库集成
- [PostgreSQL 集成指南](./postgresql.md) - 数据库集成
- [PostgreSQL 详细连接](./POSTGRESQL_CONNECTION.md) - 全面的连接和配置指南
  - 包含：连接方式、驱动程序、工具、故障排除

### ⚡ 缓存和消息
- [Redis 集成](./redis.md) - 缓存服务集成

### 🔌 外部服务
- [外部 API 集成](./external-apis.md) - 第三方 API 集成指南
- [Webhook 配置](./webhooks.md) - Webhook 实现指南

---

## 🎯 按数据库/服务查找

### PostgreSQL

**快速开始**
→ [PostgreSQL 快速开始](../guides/operations/POSTGRESQL_QUICK_START.md)
- 5分钟快速上手
- 包含：安装、初始化、基本命令

**详细配置**
→ [PostgreSQL 连接指南](./POSTGRESQL_CONNECTION.md)
- 详细的连接配置
- 包含：驱动程序、工具、常见问题

**集成指南**
→ [PostgreSQL 集成](./postgresql.md)
- 在项目中集成 PostgreSQL
- 最佳实践

### Redis
→ [Redis 集成](./redis.md) - 缓存服务集成

### 外部 API
→ [外部 API 集成](./external-apis.md) - 第三方 API 调用

---

## 📖 文件说明

| 文件 | 用途 | 主要内容 |
|------|------|--------|
| **postgresql.md** | PostgreSQL 集成 | 项目中的 DB 集成方案 |
| **POSTGRESQL_CONNECTION.md** | 连接详解 | 连接参数、工具、故障排除 |
| **redis.md** | Redis 集成 | 缓存服务集成 |
| **external-apis.md** | 外部 API | 调用第三方 API |
| **webhooks.md** | Webhook | Webhook 实现 |

---

## 🚀 快速开始

### PostgreSQL 开发环境

```bash
# 1. 快速了解（5分钟）
cat ../guides/operations/POSTGRESQL_QUICK_START.md

# 2. 学习连接（10分钟）
cat POSTGRESQL_CONNECTION.md

# 3. 项目集成
cat postgresql.md
```

### Redis 缓存

```bash
# 集成 Redis
cat redis.md
```

### 外部 API

```bash
# 调用第三方 API
cat external-apis.md
```

---

## 📊 常见集成任务

### PostgreSQL 集成

**步骤**:
1. 参考 [快速开始](../guides/operations/POSTGRESQL_QUICK_START.md) 安装
2. 参考 [连接指南](./POSTGRESQL_CONNECTION.md) 配置连接
3. 参考 [集成指南](./postgresql.md) 在项目中使用
4. 设置监控和备份（参考[运维指南](../guides/operations/)）

**相关文档**:
- [PostgreSQL 快速开始](../guides/operations/POSTGRESQL_QUICK_START.md)
- [PostgreSQL 连接指南](./POSTGRESQL_CONNECTION.md)
- [运维指南](../guides/operations/README.md)

### 其他服务集成

**Redis**
→ [Redis 集成](./redis.md)

**外部 API**
→ [外部 API 集成](./external-apis.md)

**Webhook**
→ [Webhook 配置](./webhooks.md)

---

## 🔗 相关资源

### 内部文档
- [运维指南](../guides/operations/) - 数据库管理和维护
- [部署文档](../deployment/) - 应用部署配置
- [开发指南](../developer/) - 框架和工具
- [API 文档](../api/) - API 设计和文档

### 外部资源
- [PostgreSQL 官方文档](https://www.postgresql.org/docs/)
- [Redis 官方文档](https://redis.io/docs/)
- [PostgreSQL Python 驱动](https://www.psycopg.org/)
- [SQLAlchemy ORM](https://www.sqlalchemy.org/)

### 项目资源
- [脚本中心](../../scripts/) - 自动化脚本
- [数据库脚本](../../scripts/database/) - DB 管理脚本
- [参考文档](../reference/) - 快速参考

---

## ❓ 常见问题

**Q: 如何快速启动 PostgreSQL？**
A: 参考 [PostgreSQL 快速开始](../guides/operations/POSTGRESQL_QUICK_START.md)

**Q: PostgreSQL 连接参数是什么？**
A: 参考 [PostgreSQL 连接指南](./POSTGRESQL_CONNECTION.md)

**Q: 如何在项目中使用 PostgreSQL？**
A: 参考 [PostgreSQL 集成](./postgresql.md)

**Q: 如何集成 Redis？**
A: 参考 [Redis 集成](./redis.md)

**Q: 如何调用外部 API？**
A: 参考 [外部 API 集成](./external-apis.md)

**Q: 如何实现 Webhook？**
A: 参考 [Webhook 配置](./webhooks.md)

---

## 📞 需要帮助？

1. **快速 PostgreSQL** → [快速开始](../guides/operations/POSTGRESQL_QUICK_START.md)
2. **PostgreSQL 连接** → [连接指南](./POSTGRESQL_CONNECTION.md)
3. **项目集成** → [集成指南](./postgresql.md)
4. **Redis 集成** → [Redis 集成](./redis.md)
5. **API 集成** → [API 集成](./external-apis.md)
6. **运维问题** → [运维指南](../guides/operations/README.md)

---

**最后更新**: 2025-10-27
**版本**: 1.0.0
**维护者**: 项目团队
