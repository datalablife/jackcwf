# 运维和操作指南

欢迎来到运维指南！本目录包含系统部署、监控、维护和故障排除的文档。

## 📚 指南导航

### 🚀 快速开始
- [部署指南](../../deployment/) - 应用部署文档
- [监控和告警](./monitoring.md) - 系统监控配置

### 🗄️ 数据库管理
- [PostgreSQL 快速开始](./POSTGRESQL_QUICK_START.md) - PostgreSQL 快速上手
- [详细连接指南](../../integrations/POSTGRESQL_CONNECTION.md) - 全面的连接配置

### 💾 备份和迁移
- [数据备份](./backup.md) - 备份策略和实施
- [数据库迁移](../../changelog/migrations/) - DB 迁移记录

### 🔧 故障排除
- [故障排查](./troubleshooting.md) - 常见问题解决
- [监控告警](./monitoring.md) - 性能监控

---

## 🎯 按任务查找指南

### 我想...

- **快速部署应用** → [部署指南](../../deployment/)
- **配置 PostgreSQL** → [PostgreSQL 快速开始](./POSTGRESQL_QUICK_START.md)
- **连接数据库** → [PostgreSQL 连接指南](../../integrations/POSTGRESQL_CONNECTION.md)
- **设置监控** → [监控和告警](./monitoring.md)
- **备份数据** → [数据备份](./backup.md)
- **解决问题** → [故障排查](./troubleshooting.md)
- **查看迁移历史** → [数据库迁移](../../changelog/migrations/)

---

## 📖 文件说明

| 文件 | 用途 | 主要内容 |
|------|------|--------|
| **POSTGRESQL_QUICK_START.md** | PostgreSQL 快速指南 | 安装、初始化、基本命令 |
| **monitoring.md** | 监控配置 | 性能监控、告警设置 |
| **backup.md** | 数据备份 | 备份策略、恢复流程 |
| **troubleshooting.md** | 故障排除 | 常见问题和解决方案 |

---

## 🚀 快速开始（10分钟）

### 1. 部署应用

```bash
# 查看部署指南
cat ../../deployment/docker.md

# 或选择特定部署方式
cat ../../deployment/coolify.md
```

### 2. 配置数据库

```bash
# 快速 PostgreSQL 指南
cat POSTGRESQL_QUICK_START.md

# 详细连接配置
cat ../../integrations/POSTGRESQL_CONNECTION.md
```

### 3. 设置监控

```bash
# 监控和告警
cat monitoring.md
```

---

## 📊 常见运维任务

### 应用部署
1. 选择部署方式（Docker / Kubernetes / Coolify）
2. 阅读对应的部署指南
3. 准备环境变量和配置
4. 执行部署流程
5. 验证部署成功

**参考**: [部署文档](../../deployment/)

### 数据库管理
1. **初始化**: 按 [PostgreSQL 快速开始](./POSTGRESQL_QUICK_START.md)
2. **连接**: 参考 [连接指南](../../integrations/POSTGRESQL_CONNECTION.md)
3. **备份**: 定期执行备份，参考 [备份指南](./backup.md)
4. **监控**: 设置监控告警，参考 [监控配置](./monitoring.md)
5. **迁移**: 记录 DB 迁移，参考 [迁移记录](../../changelog/migrations/)

### 系统监控
1. 配置监控指标
2. 设置告警阈值
3. 建立告警通知
4. 定期审查监控数据

**参考**: [监控配置](./monitoring.md)

### 故障排除
1. 收集错误信息
2. 查看故障排查指南
3. 执行诊断步骤
4. 应用解决方案
5. 验证问题已解决

**参考**: [故障排查](./troubleshooting.md)

---

## 🔗 相关资源

### 内部文档
- [部署指南](../../deployment/) - 应用部署
- [PostgreSQL 集成](../../integrations/) - 数据库集成
- [参考文档](../../reference/) - 配置参考
- [变更日志](../../changelog/) - 版本历史

### 外部资源
- [PostgreSQL 官方文档](https://www.postgresql.org/docs/)
- [Docker 官方文档](https://docs.docker.com/)
- [Kubernetes 文档](https://kubernetes.io/docs/)
- [Coolify 文档](https://coolify.io/docs)

### 项目资源
- [项目指导](../../../CLAUDE.md) - 项目概览
- [脚本中心](../../../scripts/) - 自动化脚本
- [API 文档](../../api/) - API 参考

---

## ❓ 常见问题

**Q: PostgreSQL 如何快速开始？**
A: 参考 [PostgreSQL 快速开始](./POSTGRESQL_QUICK_START.md)

**Q: 如何连接到数据库？**
A: 参考 [PostgreSQL 连接指南](../../integrations/POSTGRESQL_CONNECTION.md)

**Q: 数据备份频率是多少？**
A: 参考 [备份指南](./backup.md) 中的建议

**Q: 系统出现问题怎么办？**
A: 参考 [故障排查](./troubleshooting.md)

**Q: 如何设置监控告警？**
A: 参考 [监控配置](./monitoring.md)

---

## 📞 需要帮助？

1. **部署问题** → [部署文档](../../deployment/)
2. **数据库问题** → [PostgreSQL 指南](./POSTGRESQL_QUICK_START.md)
3. **连接问题** → [连接指南](../../integrations/POSTGRESQL_CONNECTION.md)
4. **监控问题** → [监控配置](./monitoring.md)
5. **故障排除** → [故障排查](./troubleshooting.md)
6. **其他问题** → 查看相关指南文档

---

**最后更新**: 2025-10-27
**版本**: 1.0.0
**维护者**: 项目团队
