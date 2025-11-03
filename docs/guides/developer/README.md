# 开发者指南

欢迎来到开发者指南！本目录包含所有与项目开发相关的文档。

## 📚 指南导航

### 🚀 快速开始
- [开发环境完整设置总结](./DEVELOPMENT_ENVIRONMENT_SUMMARY.md) - 开发环境配置完整总结
- [开发环境设置](./setup.md) - 本地开发环境配置

### 🛠️ 框架和工具
- **Reflex 框架**
  - [Reflex + uv 开发指南](./REFLEX_WITH_UV.md) - 使用 uv 运行 Reflex
  - [Reflex 故障排除指南](./REFLEX_TROUBLESHOOTING.md) - 常见问题解决
  - 包含：快速启动、常用命令、端口配置、故障排除

- **包管理工具**
  - [uv 包管理器指南](./UV_GUIDE.md) - uv 的详细使用说明
  - 包含：安装、虚拟环境、依赖管理、最佳实践

### 💻 代码开发
- [代码风格规范](./code-style.md) - 代码编写标准
- [测试指南](./testing.md) - 测试编写规范
- [调试指南](./debugging.md) - 常见问题调试

### 🤝 协作
- [贡献指南](./contributing.md) - 如何贡献代码
- [代码审查](../../../code_review_crew/) - CrewAI 代码审查系统

---

## 🎯 按任务查找指南

### 我想...

- **完整了解开发环境** → [开发环境完整设置总结](./DEVELOPMENT_ENVIRONMENT_SUMMARY.md)
- **设置开发环境** → [开发环境设置](./setup.md)
- **学习 Reflex 框架** → [Reflex + uv 指南](./REFLEX_WITH_UV.md)
- **解决 Reflex 问题** → [Reflex 故障排除指南](./REFLEX_TROUBLESHOOTING.md)
- **管理项目依赖** → [uv 包管理器](./UV_GUIDE.md)
- **编写规范代码** → [代码风格规范](./code-style.md)
- **编写测试** → [测试指南](./testing.md)
- **调试问题** → [调试指南](./debugging.md)
- **提交代码** → [贡献指南](./contributing.md)

---

## 📖 文件说明

| 文件 | 用途 | 主要内容 |
|------|------|--------|
| **DEVELOPMENT_ENVIRONMENT_SUMMARY.md** | 开发环境总结 | 技术栈、配置项、工作流程 |
| **REFLEX_WITH_UV.md** | Reflex 快速开发 | 启动、命令、端口、故障排除 |
| **REFLEX_TROUBLESHOOTING.md** | Reflex 故障排除 | 常见问题、解决方案、优化建议 |
| **UV_GUIDE.md** | 包管理工具详解 | 安装、虚拟环境、依赖、工作流 |
| **setup.md** | 环境配置 | 开发环境初始化 |
| **code-style.md** | 代码规范 | Python 和 TypeScript 编码标准 |
| **testing.md** | 测试指南 | 单元测试、集成测试编写 |
| **debugging.md** | 调试技巧 | 问题诊断和解决 |
| **contributing.md** | 贡献规范 | 代码提交流程 |

---

## 🚀 快速开始（5分钟）

### 1. 设置环境

```bash
# 阅读开发环境设置
cat setup.md

# 或使用 Reflex + uv 快速指南
cat REFLEX_WITH_UV.md
```

### 2. 启动开发

```bash
# 使用 uv 启动 Reflex
uv run reflex run

# 应用将在 http://localhost:3000 运行
```

### 3. 了解工具

- **框架**: Reflex（全栈 Python 框架）
- **包管理**: uv（快速包管理器）
- **前端**: React + TypeScript（自动生成）
- **后端**: FastAPI（自动生成）
- **样式**: Tailwind CSS（集成）

---

## 💡 推荐学习路径

### 初学者
1. [Reflex + uv 开发指南](./REFLEX_WITH_UV.md) - 10分钟快速开始
2. [开发环境设置](./setup.md) - 5分钟环境配置
3. [代码风格规范](./code-style.md) - 了解编码标准

### 有经验的开发者
1. [uv 包管理器指南](./UV_GUIDE.md) - 深入理解依赖管理
2. [代码风格规范](./code-style.md) - 团队编码标准
3. [贡献指南](./contributing.md) - 代码提交流程

### 高级用户
1. [测试指南](./testing.md) - 编写高质量测试
2. [调试指南](./debugging.md) - 高效问题诊断
3. [架构设计](../architecture/) - 系统设计决策

---

## 🔗 相关资源

### 官方文档
- [Reflex 官方文档](https://reflex.dev/docs)
- [Reflex UI 组件库](https://reflex.dev/docs/library)
- [uv 官方文档](https://docs.astral.sh/uv/)

### 项目文档
- [项目指导](../../CLAUDE.md) - 项目概览和规范
- [代码审查](../../../code_review_crew/) - 代码质量保证
- [测试指南](../../../tests/README.md) - 测试编写
- [API 文档](../api/) - API 设计和文档

### 工具和配置
- [Python 项目配置](../../../pyproject.toml)
- [Reflex 配置](../../../rxconfig.py)
- [开发脚本](../../../scripts/dev/) - 开发辅助工具

---

## ❓ 常见问题

**Q: Reflex 和 uv 分别是什么？**
A: Reflex 是全栈 Python 框架，自动生成 React 和 FastAPI。uv 是快速的包管理工具。

**Q: 如何启动开发服务器？**
A: 运行 `uv run reflex run`，前端在 3000，后端在 8000。

**Q: 代码风格有什么要求？**
A: 参考 [code-style.md](./code-style.md)，包含 Python 和 TypeScript 规范。

**Q: 如何编写测试？**
A: 参考 [testing.md](./testing.md) 和 [tests/ 指南](../../../tests/README.md)。

**Q: 如何提交代码？**
A: 参考 [contributing.md](./contributing.md) 和 [贡献指南](../../../docs/guides/developer/contributing.md)。

---

## 📞 需要帮助？

1. **快速问题** → 查看本 README 的常见问题
2. **环境问题** → [开发环境设置](./setup.md)
3. **框架问题** → [Reflex + uv 指南](./REFLEX_WITH_UV.md)
4. **工具问题** → [uv 包管理器](./UV_GUIDE.md)
5. **其他问题** → 查看对应的指南文档

---

**最后更新**: 2025-10-27
**版本**: 1.0.0
**维护者**: 项目团队
