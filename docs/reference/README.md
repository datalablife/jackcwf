# 参考文档

欢迎来到参考文档！本目录包含快速参考、配置参考和文件组织系统相关的文档。

## 📚 文档导航

### 📋 快速参考
- [文档索引和快速导航](./DOCUMENTATION_INDEX.md) - 所有文档的导航中心
- [项目快速参考](./QUICK_REFERENCE.md) - 项目相关的快速参考
- [常用命令](./commands.md) - 常用的命令集合
- [配置参考](./configuration.md) - 全面的配置参考
- [依赖列表](./dependencies.md) - 所有依赖信息
- [术语表](./glossary.md) - 项目术语定义

### 📁 文件组织系统

**快速入门（推荐首先阅读）**
- [快速开始指南](./START_HERE.md) - 5分钟快速入门
- [快速参考](./FILE_ARCHIVE_QUICK_GUIDE.md) - 日常速查表

**详细规范**
- [完整的目录结构设计](./DIRECTORY_STRUCTURE.md) - 完整的目录规范和使用指南
- [目录树](./DIRECTORY_TREE.txt) - 可视化的目录结构

**实施指南**
- [实施总结](./IMPLEMENTATION_SUMMARY.md) - 项目成果和后续步骤
- [实施清单](./IMPLEMENTATION_CHECKLIST.md) - 分步实施指南
- [文件系统总结](./FILE_SYSTEM_SUMMARY.md) - 使用场景示例

**扩展资源**
- [文件组织系统](./FILE_ORGANIZATION_SYSTEM.md) - 详细的系统设计
- [文件系统总结](./FILE_ARCHIVE_SYSTEM_DELIVERABLES.md) - 交付资源清单

---

## 🎯 按用途查找文档

### 我想...

- **快速查看所有文档导航** → [文档索引和快速导航](./DOCUMENTATION_INDEX.md)
- **快速查看项目参考** → [项目快速参考](./QUICK_REFERENCE.md)
- **快速了解文件归档系统** → [快速开始指南](./START_HERE.md)
- **日常查询文件位置** → [快速参考](./FILE_ARCHIVE_QUICK_GUIDE.md)
- **了解完整规范** → [完整的目录结构](./DIRECTORY_STRUCTURE.md)
- **实施文件组织** → [实施清单](./IMPLEMENTATION_CHECKLIST.md)
- **查看目录可视化** → [目录树](./DIRECTORY_TREE.txt)
- **参考常用命令** → [常用命令](./commands.md)
- **查询配置参考** → [配置参考](./configuration.md)
- **了解项目术语** → [术语表](./glossary.md)

---

## 📖 文件说明

### 文件组织系统

| 文件 | 大小 | 用途 | 推荐阅读 |
|------|------|------|--------|
| **START_HERE.md** | 5分钟 | 快速入门 | ⭐⭐⭐⭐⭐ |
| **FILE_ARCHIVE_QUICK_GUIDE.md** | 10分钟 | 日常速查 | ⭐⭐⭐⭐⭐ |
| **DIRECTORY_STRUCTURE.md** | 30分钟 | 完整规范 | ⭐⭐⭐⭐ |
| **IMPLEMENTATION_SUMMARY.md** | 15分钟 | 实施总结 | ⭐⭐⭐ |
| **IMPLEMENTATION_CHECKLIST.md** | 30分钟 | 实施指南 | ⭐⭐⭐ |
| **DIRECTORY_TREE.txt** | 可视化 | 目录结构 | ⭐⭐ |
| **FILE_ORGANIZATION_SYSTEM.md** | 详细 | 系统设计 | ⭐⭐ |
| **FILE_SYSTEM_SUMMARY.md** | 详细 | 使用示例 | ⭐⭐ |
| **FILE_ARCHIVE_SYSTEM_DELIVERABLES.md** | 资源清单 | 交付成果 | ⭐ |

---

## 🚀 快速开始（5分钟）

### 1. 了解系统

```bash
# 阅读快速开始指南
cat START_HERE.md
```

### 2. 学习规范

```bash
# 查看日常速查表
cat FILE_ARCHIVE_QUICK_GUIDE.md
```

### 3. 深入学习

```bash
# 阅读完整规范
cat DIRECTORY_STRUCTURE.md
```

---

## 📋 文件归档规范概览

### 三大核心目录

- **docs/** - 所有文档（API、架构、指南、部署、集成、参考、变更日志、归档）
- **scripts/** - 所有脚本（开发、测试、部署、维护、工具、数据库、CI/CD、工具库）
- **tests/** - 所有测试（单元、集成、端到端、测试数据）

### 根目录允许的文件

- CLAUDE.md, README.md, pyproject.toml, uv.lock, rxconfig.py
- .gitignore, .env.example, Dockerfile, docker-compose.yml

### 命名规范

- 文件：小写 + 连字符（`setup-env.sh`, `api-docs.md`）
- 脚本：动词开头（`run-app.sh`, 不是 `app-run.sh`）
- 测试：test_ 前缀（`test_models.py`）

---

## 🔗 相关资源

### 项目文档
- [项目指导](../../CLAUDE.md) - 项目概览和规范
- [文档中心](../README.md) - 完整的文档导航
- [脚本中心](../../scripts/README.md) - 脚本使用指南
- [测试中心](../../tests/README.md) - 测试编写指南

### 开发指南
- [开发指南](../developer/) - 框架和工具
- [部署文档](../deployment/) - 应用部署
- [运维指南](../operations/) - 系统运维

### 其他参考
- [变更日志](../changelog/) - 版本历史
- [集成文档](../integrations/) - 数据库和 API 集成
- [架构设计](../architecture/) - 系统设计和决策

---

## ❓ 常见问题

**Q: 文件应该放在哪里？**
A: 参考 [快速参考](./FILE_ARCHIVE_QUICK_GUIDE.md) 中的快速判断树

**Q: 如何遵循命名规范？**
A: 查看 [完整规范](./DIRECTORY_STRUCTURE.md) 中的命名规范部分

**Q: 根目录能放什么文件？**
A: 只能放配置文件，参考 [快速参考](./FILE_ARCHIVE_QUICK_GUIDE.md)

**Q: 如何组织大型项目？**
A: 参考 [文件组织系统](./FILE_ORGANIZATION_SYSTEM.md)

**Q: 如何管理过期文档？**
A: 移至 `docs/archived/`，参考 [完整规范](./DIRECTORY_STRUCTURE.md)

---

## 📚 推荐阅读顺序

### 首次使用
1. **START_HERE.md** - 5分钟快速入门
2. **FILE_ARCHIVE_QUICK_GUIDE.md** - 日常速查
3. **DIRECTORY_STRUCTURE.md** - 完整规范

### 日常使用
1. **FILE_ARCHIVE_QUICK_GUIDE.md** - 打印贴墙
2. **commands.md** - 常用命令
3. **configuration.md** - 配置参考

### 深入学习
1. **DIRECTORY_STRUCTURE.md** - 完整设计
2. **FILE_ORGANIZATION_SYSTEM.md** - 系统设计
3. **IMPLEMENTATION_CHECKLIST.md** - 实施指南

---

## 📞 需要帮助？

1. **快速问题** → [快速参考](./FILE_ARCHIVE_QUICK_GUIDE.md)
2. **文件位置** → [快速开始](./START_HERE.md)
3. **完整规范** → [目录结构](./DIRECTORY_STRUCTURE.md)
4. **实施指导** → [实施清单](./IMPLEMENTATION_CHECKLIST.md)
5. **常用命令** → [常用命令](./commands.md)
6. **其他问题** → 查看相关文档

---

**最后更新**: 2025-10-27
**版本**: 1.0.0
**维护者**: 项目团队
