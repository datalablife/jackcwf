# Hooks规则分析与根目录文档遗留情况

## 📋 问题描述

根目录仍有多个.md开发文档没有被归档到docs目录的相应子文件夹中。这是由于项目中的hooks规则系统与文档整理规则发生了冲突。

---

## 🔍 Hooks规则系统

### 规则文件位置
- **file-output-rule-hook**: `.claude/hooks/file-output-rule-hook`
- **output-rules.json**: `.claude/output-rules.json`

### 规则层级

#### Priority 1 (必须保留在根目录)
根据`output-rules.json`的定义：
- **CLAUDE.md** - 项目配置
- **progress.md** - 项目进度追踪
- **progress.archive.md** - 进度归档
- **README.md** - 项目根目录README

#### Priority 2 (应该被归档到docs)
根据`file-output-rule-hook`定义的关键词：
关键词列表：
- "report", "summary", "analysis", "guide", "plan", "roadmap", "maintenance", "checklist"
- 中文：分析报告、总结、摘要、汇总、指南、手册、实现、计划、路线图、维护、清单

---

## ⚠️ 当前根目录文件状态分析

### ✅ 正确保留在根目录的文件 (Priority 1)
1. **CLAUDE.md** - 基础设施文件
2. **progress.md** - 进度追踪
3. **progress.archive.md** - 进度归档
4. **README.md** - 项目根README

### ❌ 应该被归档但仍在根目录的文件 (Priority 2)

| 文件名 | 匹配关键词 | 应该归档到 | 理由 |
|-------|---------|---------|------|
| ANALYSIS_REMEDIATION_COMPLETE.md | analysis, ANALYSIS | docs/reference/ | 分析类文档 |
| BACKEND_IMPLEMENTATION_COMPLETE.md | implementation | docs/guides/developer/ | 项目里程碑标记 |
| DELIVERY_CHECKLIST.md | checklist | docs/architecture/ | 交付清单 |
| DELIVERY_SUMMARY.md | summary | docs/reference/ | 交付摘要 |
| FEATURE_SPECIFICATION_CREATED.md | specification | docs/features/ | 功能规范 |
| FINANCIAL_RAG_EXECUTIVE_SUMMARY.md | summary | docs/features/rag/ | RAG系统摘要 |
| FINANCIAL_RAG_IMPLEMENTATION.md | implementation | docs/features/rag/ | RAG实现指南 |
| IMPLEMENTATION_CHECKLIST.md | checklist | docs/architecture/ | 实现检查清单 |
| IMPLEMENTATION_EXAMPLES.md | implementation | docs/langchain/migration/ | 迁移示例代码 |
| IMPLEMENTATION_SUMMARY.md | summary | docs/architecture/ | 实现总结 |
| LANGCHAIN_1_0_MIGRATION_GUIDE.md | guide | docs/langchain/migration/ | 迁移指南 |
| MIDDLEWARE_IMPLEMENTATION.md | implementation | docs/langchain/middleware/ | 中间件实现 |
| QUICK_START_GUIDE.md | guide | docs/quickstart/ | 快速开始 |
| langchain-ai-conversation-plan.md | plan | docs/features/ | 功能计划 |

---

## 🎯 问题根源分析

### 1. Hooks规则的矛盾性

**file-output-rule-hook中的定义** (第8-10行):
```bash
PRIORITY1_KEYWORDS=("report" "summary" "analysis" "guide" "plan" "roadmap" ...
```

这些关键词被定义为"Priority 1"，意味着包含这些关键词的文件应该在根目录生成。

**output-rules.json中的定义** (Priority 2):
这些相同的关键词被定义为Priority 2，应该被输出到docs的子目录。

### 2. 命名约定的影响

当这些开发文档被生成时（特别是通过Agent和Task工具时）：
- 文件使用了包含这些关键词的名称
- hooks系统检测到关键词
- 根据file-output-rule-hook，这些文件被留在了根目录

### 3. 为什么没有自动归档

在您执行文档整理时：
- 您手动选择了33个文件进行迁移
- **但遗留的这14个文件包含Priority 1关键词**
- hooks系统会警告这些文件应该在根目录
- 因此在git commit时，Pre-commit钩子自动将这些文件从docs移回根目录

查看git log可以看到这个过程：
```
commit 45a3eae refactor: Move critical documentation to root directory per pre-commit rules
  - 12 files changed (12 个文件重命名回根目录)
```

---

## 🔧 规则冲突详解

### file-output-rule-hook 的作用机制

```bash
# 第13-31行的check_output_priority函数：
# 如果文件名包含Priority1关键词 && 文件不在根目录
# → 输出警告：文件应该在根目录
# → 返回错误代码
```

### output-rules.json 的作用机制

```json
// Priority 2规则定义了这些关键词应该输出到docs的子目录
// 但这与file-output-rule-hook的Priority 1定义冲突
```

### Pre-commit钩子的最终判定

在git提交时，Pre-commit钩子优先执行：
```json
// enforcementRules中的override_archive_rules:
"priority": 1,
"action": "apply_output_rules_first"
```

**效果**：file-output-rule-hook中的优先级规则优先级更高，所以这些文件被自动移回根目录。

---

## 📊 关键词分布统计

| 关键词 | 文件数 | 文件列表 |
|-------|--------|---------|
| summary | 3 | DELIVERY_SUMMARY.md, FINANCIAL_RAG_EXECUTIVE_SUMMARY.md, IMPLEMENTATION_SUMMARY.md |
| implementation | 5 | BACKEND_IMPLEMENTATION_COMPLETE.md, FINANCIAL_RAG_IMPLEMENTATION.md, IMPLEMENTATION_CHECKLIST.md, IMPLEMENTATION_EXAMPLES.md, MIDDLEWARE_IMPLEMENTATION.md |
| analysis | 1 | ANALYSIS_REMEDIATION_COMPLETE.md |
| guide | 2 | LANGCHAIN_1_0_MIGRATION_GUIDE.md, QUICK_START_GUIDE.md |
| checklist | 2 | DELIVERY_CHECKLIST.md, IMPLEMENTATION_CHECKLIST.md |
| plan | 1 | langchain-ai-conversation-plan.md |

---

## ✅ 建议的解决方案

### 方案1：修改hooks规则 (推荐)

**修改file-output-rule-hook:**
1. 将Priority 1关键词限制到真正需要在根目录的文件
2. 区分"标记文件"(如COMPLETED.md)和"内容文档"(如指南、实现等)

**修改output-rules.json:**
1. 添加新的优先级规则，区分标记文件和内容文档
2. 标记文件（如BACKEND_IMPLEMENTATION_COMPLETE.md）保留在根目录
3. 内容文档（如实现指南）必须归档到docs

### 方案2：统一命名约定

不再使用包含Priority 1关键词的名称：
- ✅ `BACKEND_IMPLEMENTATION_COMPLETE.md` (标记文件)
- ❌ `IMPLEMENTATION_EXAMPLES.md` → ✅ `example_code.md`

### 方案3：强制整理（立即执行）

1. 手动移动这14个文件到docs的相应目录
2. 更新hooks规则以允许这样的移动
3. 修改这些文件的命名以避免与Priority 1关键词冲突

---

## 🎓 Hook系统工作流总结

```
Agent生成文件
    ↓
agent指定输出位置(docs/xxx/)
    ↓
file-output-rule-hook检查文件名
    ↓
文件名匹配Priority1关键词?
    ├─ YES → 警告：应该在根目录 → 建议改为根目录
    └─ NO → 按指定位置输出到docs/
    ↓
git add (文件已在docs/)
    ↓
Pre-commit hook执行
    ↓
检查Priority1关键词 + 路径不在根目录?
    ├─ YES → 自动移动回根目录
    └─ NO → 保持原位置
    ↓
git commit
    ↓
"Move critical documentation to root directory per pre-commit rules"
```

---

## 💡 关键发现

1. **hooks规则存在优先级冲突**：
   - Priority 1关键词的定义过于宽泛
   - 许多开发文档实际上应该被归档

2. **Pre-commit钩子优先级更高**：
   - 即使手动移动文件到docs/，Pre-commit钩子也会自动移回根目录
   - 这导致文档组织工作被自动回滚

3. **需要区分文件类型**：
   - 项目状态标记（BACKEND_IMPLEMENTATION_COMPLETE）→ 根目录
   - 内容文档（实现指南、迁移指南）→ docs/
   - 当前hooks没有做这样的区分

---

## 🔐 规则优先级顺序

```
1. Pre-commit hook (file-output-rule-hook) ⭐ 最高优先级
   ↓
2. .claude/hooks/ 中的其他hook
   ↓
3. output-rules.json
   ↓
4. 手动指定的位置 ⬇️ 最低优先级
```

这意味着hooks规则几乎是"不可违抗的"，除非修改hook本身。

---

## 📝 总结

**根本原因**：file-output-rule-hook中的PRIORITY1_KEYWORDS定义过于宽泛，包含了许多应该被归档到docs的文档类型的关键词，导致Pre-commit钩子会自动将这些文件拉回到根目录。

**解决方向**：需要精化hooks规则，区分真正应该在根目录的文件类型（如项目状态标记）和应该被归档的内容文档。
