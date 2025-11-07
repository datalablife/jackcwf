# Claude Code 配置文档

本目录包含 Claude Code 相关的配置和使用指南。

## 📑 文档索引

### 1. [QUICK_START.md](./QUICK_START.md)
**快速开始指南**

- 概述已配置的所有功能
- 立即使用 Claude Code 的方法
- 验证配置是否工作的步骤
- 常见问题解答

**适合场景**：刚开始使用或快速参考

---

### 2. [THINKING_CONFIG_GUIDE.md](./THINKING_CONFIG_GUIDE.md)
**Thinking 显示配置详细指南**

- 完整的配置文件说明
- Thinking 过程的显示规则
- 环境变量和高级配置
- 故障排除和最佳实践

**适合场景**：深入了解配置或自定义设置

---

### 3. [OUTPUT_RULES.md](./OUTPUT_RULES.md)
**文件输出优先级规则**

- 文件输出位置的优先级系统
- 报告、总结、指南、计划文件优先输出到根目录
- 详细的规则定义和关键词列表
- 实际场景示例和最佳实践

**适合场景**：了解文件生成位置规则，确保报告等文件输出到根目录

---

## 🎯 功能概览

本项目已配置了以下功能：

### ✨ 自动 Thinking 显示
- Claude Code 在复杂任务时自动显示思考过程
- 无需按 `Ctrl+O` 快捷键
- 包含问题分析、方案评估、选择理由、实施步骤

### 🌍 中文语言保持
- 即使在对话被压缩后也继续使用中文
- 所有输出（代码外的部分）都用中文
- 自动 hooks 监控和恢复

### 🔧 多层级配置保障
- `config.json` - 系统提示 + 语言设置
- `thinking-settings.json` - thinking 专用配置
- Hooks - 运行时环境监控
- Wrapper 脚本 - 启动时自动配置

---

## 🚀 快速开始

```bash
cd /path/to/project
claude
```

或使用 wrapper 脚本：
```bash
./claude-wrapper.sh
```

---

## 📂 项目文件结构

```
.claude/
├── config.json                      # 主配置
├── thinking-settings.json           # thinking配置
├── THINKING_CONFIG_GUIDE.md         # 详细指南
└── hooks/
    ├── user-prompt-submit-hook
    ├── conversation-compacted-hook
    └── thinking-display-hook

docs/guides/claude-code/
├── README.md                        # 本文件
├── QUICK_START.md                   # 快速开始
└── THINKING_CONFIG_GUIDE.md         # 详细指南

claude-wrapper.sh                    # 启动脚本
QUICK_START.md                       # 原始位置的快速开始（已归档）
```

---

## 💡 使用建议

1. **第一次使用**：阅读 `QUICK_START.md`
2. **需要自定义**：查看 `THINKING_CONFIG_GUIDE.md`
3. **遇到问题**：检查对应文档的故障排除部分

---

## 📝 文档维护

- 这些文档应与 `.claude/` 目录中的配置文件同步
- 如果修改了配置，请同时更新文档
- 原始文档位置在项目根目录和 `.claude/` 目录中作为备份

---

## 相关资源

- Claude Code 官方文档：https://code.claude.com/docs/
- 项目配置文件：`.claude/config.json`
- 启动脚本：`claude-wrapper.sh`

