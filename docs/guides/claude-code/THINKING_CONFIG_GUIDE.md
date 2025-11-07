# Claude Code Thinking 显示配置指南

## 概述

本配置确保 Claude Code 在进行复杂任务时自动显示完整的思考过程，无需用户按 `Ctrl+O` 快捷键。

## 配置文件结构

```
.claude/
├── config.json                          # 主配置文件（包含thinking显示设置）
├── thinking-settings.json               # thinking相关设置
└── hooks/
    ├── user-prompt-submit-hook         # 用户提示hook
    ├── conversation-compacted-hook     # 对话压缩hook
    └── thinking-display-hook           # thinking显示hook
```

## 如何使用

### 方法 1：直接运行 Claude Code（推荐）

在项目目录中直接运行：
```bash
claude
```

Claude Code 会自动加载 `.claude/config.json` 中的所有设置，包括 thinking 显示配置。

### 方法 2：使用 Wrapper 脚本

```bash
./claude-wrapper.sh
```

Wrapper 脚本会：
- 自动加载所有配置
- 合并 thinking 设置
- 设置环境变量
- 启动 Claude Code

### 方法 3：命令行指定

```bash
claude --settings '.claude/thinking-settings.json' --verbose
```

## 配置详解

### config.json 中的 Thinking 配置

| 配置项 | 值 | 说明 |
|------|-----|------|
| `showThinking` | `true` | 启用 thinking 显示 |
| `expandThinkingByDefault` | `true` | 默认展开 thinking 内容 |
| `verbose` | `true` | 启用详细输出模式 |
| `thinkingLevel` | `comprehensive` | thinking 详细级别为完整 |

### thinking-settings.json 中的配置

```json
{
  "thinkingSettings": {
    "enabled": true,              // thinking 总开关
    "displayMode": "auto",         // 自动显示模式
    "expandByDefault": true,       // 默认展开
    "showThinkingIndicator": true, // 显示thinking指示器
    "thinkingDisplayPosition": "top", // thinking显示位置：顶部
    "autoShowOnComplexTasks": true // 复杂任务时自动显示
  }
}
```

## Thinking 显示规则

Claude Code 会在以下情况显示 thinking 过程：

1. **代码分析与调试** - 分析复杂代码问题时
2. **系统设计** - 设计架构或功能时
3. **技术决策** - 在多个方案中做选择时
4. **问题排查** - 诊断和解决问题时
5. **复杂任务** - 需要多步骤推理的任务时

## Thinking 过程格式

Claude 会使用以下格式显示思考：

```
<thinking>
问题分析：理解用户的需求是什么
方案评估：列举可能的解决方案
方案选择：说明为什么选择某个方案
实施步骤：分步骤说明如何实现
风险考虑：列出可能的问题或边界情况
</thinking>

[实际的回复和代码]
```

## 验证配置是否生效

1. **启动 Claude Code**：`claude`
2. **提出一个复杂的编程问题**，例如：
   ```
   如何重构这个模块来提高性能？
   ```
3. **观察输出**：
   - ✅ 应该看到 `<thinking>` 部分在回复前
   - ✅ 思考过程应该包含完整的分析步骤
   - ✅ 不需要按 `Ctrl+O` 来查看思考

## 环境变量

以下环境变量用于控制 thinking 显示：

```bash
CLAUDE_SHOW_THINKING=true      # 启用thinking显示
CLAUDE_EXPAND_THINKING=true    # 默认展开thinking
CLAUDE_VERBOSE=true            # 启用详细输出
```

## 故障排除

### 问题：thinking 仍然不显示

**解决方案**：
1. 确保 `.claude/config.json` 中的 `showThinking` 为 `true`
2. 运行 `claude --verbose` 启用详细模式
3. 重启 Claude Code 会话

### 问题：thinking 显示被截断

**解决方案**：
1. 增加 `verbose` 输出级别
2. 使用 `--print` 模式查看完整输出：
   ```bash
   claude --print "你的问题" --verbose
   ```

### 问题：配置未被加载

**解决方案**：
1. 验证 config.json 在 `.claude/` 目录中
2. 确认 JSON 格式正确（使用 `jq . .claude/config.json` 验证）
3. 运行 `claude doctor` 检查配置状态

## 最佳实践

1. **复杂任务**：对于复杂的编程任务，thinking 过程会显示完整的推理步骤
2. **审核代码**：在代码审核时，thinking 会展示考虑的因素
3. **学习过程**：保存包含 thinking 的对话，可以学习解决问题的思路
4. **调试**：在调试时，thinking 过程有助于理解问题分析步骤

## 相关文件

- `.claude/config.json` - 主配置文件
- `.claude/thinking-settings.json` - thinking 专门配置
- `claude-wrapper.sh` - Wrapper 脚本
- `.claude/hooks/thinking-display-hook` - thinking 显示 hook

## 注意事项

- 配置在启动 Claude Code 时加载
- 修改配置后，需要重启 Claude Code 会话
- Thinking 显示不会影响性能，但会增加输出量
- 某些简单任务可能不会显示 thinking（这是正常的）
