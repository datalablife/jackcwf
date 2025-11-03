# 文档中心

欢迎来到项目文档中心！本目录包含所有项目文档的中央索引。

## 📑 文档分类导航

### 🚀 快速开始
- [用户入门指南](./guides/user/getting-started.md) - 新用户快速上手
- [开发环境设置](./guides/developer/setup.md) - 开发者环境配置
- [常见问题 (FAQ)](./guides/user/faq.md) - 常见问题解答

### 🏗️ 架构和设计
- [系统架构概览](./architecture/overview.md) - 整体架构设计
- [架构决策记录 (ADR)](./architecture/decisions/) - 重要架构决策
- [架构图](./architecture/diagrams/) - 系统交互图、数据流图等

### 🔌 API 文档
- [API 端点列表](./api/endpoints.md) - 所有 API 端点
- [数据模式定义](./api/schemas.md) - 请求/响应模式
- [认证和授权](./api/authentication.md) - 身份验证方式
- [错误代码参考](./api/errors.md) - 完整的错误代码列表

### 📚 开发指南
- [代码风格规范](./guides/developer/code-style.md) - 代码编写标准
- [测试指南](./guides/developer/testing.md) - 测试编写规范
- [贡献指南](./guides/developer/contributing.md) - 如何贡献代码
- [调试指南](./guides/developer/debugging.md) - 常见问题调试
- **框架和工具指南**
  - [Reflex + uv 开发指南](./guides/developer/REFLEX_WITH_UV.md) - 使用 uv 运行 Reflex
  - [uv 包管理器指南](./guides/developer/UV_GUIDE.md) - uv 的详细使用说明
  - [开发环境设置](./guides/developer/setup.md) - 本地开发环境配置

### 🚢 部署文档
- **[部署指南中心](./deployment/)** - 所有部署相关文档
  - [Coolify 部署检查清单](./deployment/coolify-deploy-checklist.md) - 快速部署指南和故障排查
  - [Granian PATH 问题修复](./deployment/granian-path-fix.md) - 解决生产环境 granian 找不到的问题
  - [Coolify Git 集成指南](./deployment/COOLIFY_GIT_INTEGRATION.md) - 使用 Coolify CLI 进行 Git 管理和自动部署
  - [Docker 部署](./deployment/docker.md) - Docker 容器部署
  - [Kubernetes 部署](./deployment/kubernetes.md) - K8s 部署指南
  - [CI/CD 流程](./deployment/ci-cd.md) - 自动化流程

### 🔧 运维和维护
- [运维指南](./guides/operations/README.md) - 系统运维
- [监控和告警](./guides/operations/monitoring.md) - 监控配置
- [数据备份](./guides/operations/backup.md) - 备份策略
- [故障排查](./guides/operations/troubleshooting.md) - 常见问题解决
- **数据库运维**
  - [PostgreSQL 快速开始](./guides/operations/POSTGRESQL_QUICK_START.md) - PostgreSQL 快速上手

### 🔌 集成文档
- [PostgreSQL 集成](./integrations/postgresql.md) - 数据库集成
- [PostgreSQL 连接指南](./integrations/POSTGRESQL_CONNECTION.md) - 详细的连接和配置
- [Redis 集成](./integrations/redis.md) - 缓存服务
- [外部 API 集成](./integrations/external-apis.md) - 第三方 API
- [Webhook 配置](./integrations/webhooks.md) - Webhook 实现

### 📖 参考文档
- [术语表](./reference/glossary.md) - 项目术语定义
- [依赖列表](./reference/dependencies.md) - 所有依赖信息
- [配置参考](./reference/configuration.md) - 全面的配置参考
- [常用命令](./reference/commands.md) - 常用的命令集合
- **文件归档系统**
  - [快速开始](./reference/START_HERE.md) - 5分钟快速入门
  - [快速参考](./reference/FILE_ARCHIVE_QUICK_GUIDE.md) - 日常速查表
  - [完整规范](./reference/DIRECTORY_STRUCTURE.md) - 目录结构完整设计
  - [实施总结](./reference/IMPLEMENTATION_SUMMARY.md) - 实施总结和后续步骤
  - [实施清单](./reference/IMPLEMENTATION_CHECKLIST.md) - 分步实施指南
  - [目录树](./reference/DIRECTORY_TREE.txt) - 可视化目录结构

### 📝 变更日志
- [变更日志](./changelog/CHANGELOG.md) - 项目版本历史
- [版本发布说明](./changelog/releases/) - 各版本详细说明
- [数据库迁移](./changelog/migrations/) - DB 迁移记录

### 📦 归档文档
- [归档文档](./archived/) - 过期但需要保留的文档

---

## 🎯 按用户角色查找文档

### 👤 对于最终用户
1. [用户入门指南](./guides/user/getting-started.md)
2. [产品功能介绍](./guides/user/features.md)
3. [常见问题](./guides/user/faq.md)
4. [API 错误代码](./api/errors.md)

### 👨‍💻 对于开发者
1. [开发环境设置](./guides/developer/setup.md)
2. [Reflex + uv 指南](./guides/developer/REFLEX_WITH_UV.md) - 快速上手框架开发
3. [系统架构概览](./architecture/overview.md)
4. [API 文档](./api/)
5. [代码风格规范](./guides/developer/code-style.md)
6. [测试指南](./guides/developer/testing.md)
7. [调试指南](./guides/developer/debugging.md)
8. [uv 包管理器](./guides/developer/UV_GUIDE.md)

### 🔧 对于运维人员
1. [部署指南](./deployment/) - 所有部署文档
2. [Coolify 部署检查清单](./deployment/coolify-deploy-checklist.md) - 快速部署和故障排查
3. [Granian PATH 修复](./deployment/granian-path-fix.md) - 生产环境问题解决
4. [Coolify Git 集成](./deployment/COOLIFY_GIT_INTEGRATION.md) - Git 仓库管理和自动部署
5. [运维指南](./guides/operations/)
6. [监控和告警](./guides/operations/monitoring.md)
7. [故障排查](./guides/operations/troubleshooting.md)
8. [数据备份](./guides/operations/backup.md)

### 🏢 对于项目经理
1. [项目概览](../README.md)
2. [变更日志](./changelog/CHANGELOG.md)
3. [架构决策](./architecture/decisions/)
4. [部署流程](./deployment/ci-cd.md)

---

## 📋 文档维护规范

### 创建新文档
1. 选择合适的分类目录
2. 使用清晰的文件名（小写 + 连字符）
3. 添加文件头和目录
4. 更新本 README.md 的相应链接
5. 更新 [变更日志](./changelog/CHANGELOG.md)

### 更新现有文档
1. 确保信息准确和最新
2. 保持格式一致
3. 记录重大变更到变更日志
4. 过期文档移至 [archived/](./archived/)

### 文档格式标准
- 使用 Markdown 格式
- 第一行为 H1 标题 (`# 标题`)
- 包含目录链接 (如文档较长)
- 底部包含"最后更新"日期
- 保持行长度在 100 字符以内（便于 diff）

---

## 🔍 搜索文档

### 按关键词搜索

- **Reflex**: [guides/developer/reflex-with-uv.md](./guides/developer/reflex-with-uv.md)
- **Python**: [guides/developer/code-style.md](./guides/developer/code-style.md)
- **PostgreSQL**: [integrations/postgresql.md](./integrations/postgresql.md)
- **Docker**: [deployment/docker.md](./deployment/docker.md)
- **API**: [api/endpoints.md](./api/endpoints.md)
- **Granian**: [deployment/granian-path-fix.md](./deployment/granian-path-fix.md)
- **Coolify**: [deployment/coolify-deploy-checklist.md](./deployment/coolify-deploy-checklist.md)

### 按任务搜索

- **如何部署应用**: [deployment/coolify-deploy-checklist.md](./deployment/coolify-deploy-checklist.md)
- **如何解决 granian 问题**: [deployment/granian-path-fix.md](./deployment/granian-path-fix.md)
- **如何使用 Coolify 和 Git 集成**: [deployment/COOLIFY_GIT_INTEGRATION.md](./deployment/COOLIFY_GIT_INTEGRATION.md)
- **如何写测试**: [guides/developer/testing.md](./guides/developer/testing.md)
- **如何调试问题**: [guides/developer/debugging.md](./guides/developer/debugging.md)
- **如何监控系统**: [guides/operations/monitoring.md](./guides/operations/monitoring.md)
- **如何备份数据**: [guides/operations/backup.md](./guides/operations/backup.md)

---

## 📞 需要帮助？

- 查看 [常见问题](./guides/user/faq.md)
- 参考 [故障排查](./guides/operations/troubleshooting.md)
- 查看 [调试指南](./guides/developer/debugging.md)
- 阅读 [贡献指南](./guides/developer/contributing.md)
- **部署问题**: [Coolify 部署检查清单](./deployment/coolify-deploy-checklist.md)

---

## 📊 文档统计

| 分类 | 文档数 | 状态 |
|------|--------|------|
| API | 4 | ✓ 完成 |
| 架构 | 2 | ✓ 完成 |
| 指南 | 10 | 🔄 进行中 |
| 部署 | 7 | ✓ 完成 |
| 集成 | 4 | 🔄 进行中 |
| 参考 | 4 | ✓ 完成 |
| 变更日志 | 1 | ✓ 完成 |

---

**最后更新**: 2025-11-03
**版本**: 1.1.0
**维护者**: 项目团队
