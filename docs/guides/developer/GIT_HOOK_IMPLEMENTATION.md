# Claude Code 文件输出规则 - 真实可行版（Git Hook 实现）

## 概述

本项目使用 **Git Hooks** 自动强制执行文件输出优先级规则。这是一个真正可行的解决方案，不依赖 Claude Code 的内部机制，而是通过 Git 的 pre-commit hook 在提交时自动整理文件。

## 🎯 工作原理

### 简单来说

```
你生成文件 → 位置可以是任意地方
         ↓
用户执行 git commit
         ↓
Git Hook 自动触发
         ↓
Hook 检查文件名，发现优先级1文件在 docs/ 中
         ↓
自动移动到根目录
         ↓
commit 成功
```

### 详细流程

1. **文件生成阶段**
   - Claude Code 可以生成任何位置的文件
   - 不受任何约束

2. **Git 提交前阶段** ⚡ **关键！**
   - 用户执行 `git commit`
   - `.git/hooks/pre-commit` 自动触发
   - 脚本扫描并识别优先级1文件
   - 自动从 docs/ 移动到根目录
   - commit 继续进行

3. **提交完成**
   - 文件已经在正确位置
   - 提交成功

## 📋 优先级规则

### 优先级1（会被自动移到根目录）

| 类型 | 关键词 | 示例 |
|------|--------|------|
| 报告 | report, analysis, 分析, 报告 | ANALYSIS_REPORT.md |
| 总结 | summary, 总结, 摘要, 汇总 | PROJECT_SUMMARY.md |
| 指南 | guide, 指南, 手册, implementation | IMPLEMENTATION_GUIDE.md |
| 计划 | plan, roadmap, 路线图, 行动 | ACTION_PLAN.md |
| 清单 | maintenance, checklist, 维护, 清单 | deployment_checklist.md |

### 优先级2（留在 docs/ 子目录）

- `docs/reference/` - 参考文档、API 文档
- `docs/deployment/` - 部署指南、配置说明
- `docs/integrations/` - 集成文档
- `docs/guides/` - 其他开发指南

## 🚀 使用方法

### 正常工作流程

```bash
# 1. Claude Code 生成文件（任何位置）
claude
# 生成了 ANALYSIS_REPORT.md、docs/reference/API.md 等

# 2. 检查文件
ls *.md          # 可能只有一些文件
ls docs/**/*.md  # ANALYSIS_REPORT.md 可能在这里

# 3. 提交到 Git
git add .
git commit -m "docs: add analysis and api reference"

# 4. Git Hook 自动触发
# ℹ️  [INFO] 扫描 docs/ 目录中的优先级1文件...
# ✓ [SUCCESS] 移动: docs/guides/ANALYSIS_REPORT.md → ANALYSIS_REPORT.md
# 📊 统计：
#   - 找到的文件: 2
#   - 移动的文件: 1

# 5. commit 完成
# 所有文件现在在正确位置
```

### 立即整理已存在的文件

如果已经有一些文件在错误的位置，运行：

```bash
./cleanup-claude-files.sh
```

这个脚本会：
- 扫描 docs/ 中的所有文件
- 识别优先级1文件
- 自动移动到根目录
- 显示详细的移动统计

## 📂 实际示例

### 场景1：生成性能分析报告

```bash
# Claude 生成文件
claude

# 用户可能指定或 Claude 选择生成位置
# 生成了：docs/guides/performance_analysis.md

# 用户提交
git add .
git commit -m "docs: add performance analysis"

# Hook 自动执行
# 检测到 "analysis" 关键词
# 移动：docs/guides/performance_analysis.md → performance_analysis.md

# 最终位置：根目录中的 performance_analysis.md ✓
```

### 场景2：生成项目总结

```bash
# Claude 生成
claude

# 生成了：PROJECT_SUMMARY.md（已在根目录）

# 提交
git add .
git commit -m "docs: add project summary"

# Hook 检查
# 发现 PROJECT_SUMMARY.md 已在根目录
# 无需移动

# 最终位置：根目录中的 PROJECT_SUMMARY.md ✓
```

### 场景3：生成 API 参考（不需要移动）

```bash
# Claude 生成
claude

# 生成了：docs/reference/API_REFERENCE.md

# 提交
git add .
git commit -m "docs: add api reference"

# Hook 检查
# "reference" 不在优先级1关键词中
# 不需要移动

# 最终位置：docs/reference/API_REFERENCE.md ✓
```

## 🔧 Git Hook 详解

### Pre-commit Hook 位置

```
.git/hooks/pre-commit
```

### 工作流程

1. 用户执行 `git commit`
2. Git 自动运行 `.git/hooks/pre-commit`
3. Hook 调用 `.claude/reorganize-files.sh`
4. 脚本执行文件整理
5. 如果成功，commit 继续
6. 如果失败，commit 被阻止（用户需要修复）

### Hook 脚本

```bash
#!/bin/bash
# 位置：.git/hooks/pre-commit

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
CLAUDE_DIR="$PROJECT_ROOT/.claude"
REORGANIZE_SCRIPT="$CLAUDE_DIR/reorganize-files.sh"

if [ -f "$REORGANIZE_SCRIPT" ]; then
    bash "$REORGANIZE_SCRIPT"
fi

exit 0
```

## 🔍 文件整理脚本

### 位置

```
.claude/reorganize-files.sh
```

### 功能

1. 扫描 docs/ 目录中的所有 .md 和 .txt 文件
2. 对每个文件检查文件名
3. 如果包含优先级1关键词，移动到根目录
4. 输出彩色的统计信息

### 手动运行

```bash
bash .claude/reorganize-files.sh
```

### 输出示例

```
ℹ️  [INFO] 扫描 docs/ 目录中的优先级1文件...
✓ [SUCCESS] 移动: docs/guides/ANALYSIS_REPORT.md → ANALYSIS_REPORT.md
✓ [SUCCESS] 移动: docs/reference/PROJECT_SUMMARY.md → PROJECT_SUMMARY.md
📊 统计：
  - 找到的文件: 10
  - 移动的文件: 2
```

## 📝 快速整理脚本

### 位置

```
cleanup-claude-files.sh
```

### 使用方式

```bash
./cleanup-claude-files.sh
```

### 功能

- 检查项目是否在 Git 仓库中
- 扫描并整理所有优先级1文件
- 提示下一步操作

## 🎨 关键词完整列表

### 英文关键词（优先级1）

```
report, REPORT
analysis, ANALYSIS
summary, SUMMARY
guide, GUIDE
plan, PLAN
roadmap, ROADMAP
maintenance, MAINTENANCE
checklist, CHECKLIST
implementation, IMPLEMENTATION
```

### 中文关键词（优先级1）

```
报告, 分析, 总结, 摘要, 汇总
指南, 手册, 计划, 路线图, 行动
维护, 清单
```

## ⚙️ 配置位置

### 关键文件

```
.claude/
├── config.json                  - 系统提示（包含规则说明）
├── reorganize-files.sh          - 主整理脚本
└── OUTPUT_RULES.md             - 详细规则文档

.git/hooks/
└── pre-commit                   - Git Hook（自动触发）

cleanup-claude-files.sh          - 手动整理脚本
```

## 🚨 故障排除

### 问题1：Git Hook 没有执行

**症状**：提交时没有看到整理信息

**检查步骤**：
```bash
# 检查 hook 是否存在
ls -l .git/hooks/pre-commit

# 检查是否有执行权限
chmod +x .git/hooks/pre-commit

# 手动测试 hook
bash .git/hooks/pre-commit
```

### 问题2：Hook 执行但没有移动文件

**症状**：收到提示但文件还在 docs/ 中

**可能原因**：
- 文件名不包含优先级1关键词
- 关键词拼写错误
- 文件已经在根目录

**检查**：
```bash
# 查看文件位置
find docs -name "*.md" | grep -i "report\|analysis\|summary"

# 手动运行脚本测试
bash .claude/reorganize-files.sh
```

### 问题3：误操作导致文件被移动

**症状**：某些文件被意外移动到根目录

**解决**：
```bash
# 查看最近的 Git 操作
git log --oneline -5

# 恢复到上一个提交
git reset --soft HEAD~1

# 手动整理后重新提交
./cleanup-claude-files.sh
git add .
git commit -m "fix: revert file reorganization"
```

## 💡 最佳实践

### DO ✅

1. **定期整理**
   ```bash
   # 在提交前手动运行
   ./cleanup-claude-files.sh
   git add .
   git commit -m "docs: reorganize files"
   ```

2. **检查提交前的输出**
   - 查看 Hook 的输出信息
   - 确认移动的文件数量
   - 验证文件在正确位置

3. **使用明确的文件名**
   ```
   ✓ PERFORMANCE_ANALYSIS_REPORT.md
   ✓ PROJECT_QUARTERLY_SUMMARY.md
   ✓ ARCHITECTURE_IMPLEMENTATION_GUIDE.md
   ```

4. **为优先级2文件使用明确的路径**
   ```
   docs/reference/API_REFERENCE.md
   docs/deployment/DEPLOYMENT_GUIDE.md
   docs/integrations/SLACK_INTEGRATION.md
   ```

### DON'T ❌

1. **不要依赖手动整理**
   - Hook 会自动处理
   - 无需担心文件位置

2. **不要使用模糊的名称**
   ```
   ✗ guide.md（含义不清）
   ✓ IMPLEMENTATION_GUIDE.md（优先级1）
   ```

3. **不要在提交后移动文件**
   - 破坏 Git 历史
   - 使用 git mv 代替

4. **不要禁用 Hook**
   - 这样规则就失效了
   - 如有必要，先咨询团队

## 📚 相关文档

- `.claude/OUTPUT_RULES.md` - 详细的规则说明
- `docs/guides/claude-code/` - Claude Code 配置指南

## 🔗 相关命令

### Git 相关

```bash
# 查看 hook 状态
ls -la .git/hooks/pre-commit

# 手动运行 hook
bash .git/hooks/pre-commit

# 绕过 hook（不推荐）
git commit --no-verify
```

### 文件整理

```bash
# 手动整理
./cleanup-claude-files.sh

# 手动运行脚本
bash .claude/reorganize-files.sh

# 列出优先级1文件
find docs -name "*report*" -o -name "*summary*" -o -name "*guide*"
```

## ✨ 总结

这个系统的优势：

✅ **真正可行** - 使用 Git Hook，确保规则生效
✅ **自动化** - 每次提交时自动执行
✅ **无感知** - 用户无需额外操作
✅ **可恢复** - Git 历史完整，可以恢复
✅ **灵活** - 可以手动运行，也可以禁用

## 🎓 学习更多

要深入了解 Git Hooks，参考：
- `man githooks` - Git Hook 文档
- `https://git-scm.com/docs/githooks` - 官方文档

