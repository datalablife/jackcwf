# Claude Code 文件输出优先级规则

## 概述

本文档定义了 Claude Code 在开发过程中生成各类文件的输出位置规则。主要目的是确保**报告、总结、指南、计划等重要文件优先输出到项目根目录**，而不是按照文档归档规范自动存放到 docs/ 子目录。

### 关键原则

**优先级规则 > 文档归档规范**

即使 docs/ 文件夹中存在明确的文档组织规范，文件输出优先级规则的优先级更高。

---

## 为什么需要这个规则？

### 问题背景

在开发过程中，Claude Code 可能会生成：
- 代码分析报告
- 项目总结
- 实现指南
- 行动计划
- 架构设计文档
- 性能评估

这些文件**需要立即被团队看到**，不应该被自动归档到嵌套的 docs/ 子目录中。

### 规则的价值

1. **可见性高** - 重要文件在根目录，团队一眼即见
2. **易于访问** - 无需查找，打开项目就能看到
3. **快速共享** - 便于版本控制和代码审查
4. **优先级清晰** - 根目录文件 > docs/ 文件

---

## 详细规则定义

### 优先级系统

#### 优先级 1（必须在根目录）

**这些文件类型无论如何都必须输出到项目根目录。**

##### 1. 报告类文件（Report Files）

**关键词**：report, REPORT, analysis, ANALYSIS, 分析报告, 评估

**用途**：分析、评估、诊断类文档

**示例**：
- `ANALYSIS_REPORT.md` - 分析报告
- `performance_report.md` - 性能报告
- `code_analysis.md` - 代码分析
- `security_evaluation.md` - 安全评估
- `performance_analysis.md` - 性能分析

**规则**：
- 必须在根目录生成
- 不能放入 `docs/` 任何子目录
- 用户应该在项目打开时就看到

##### 2. 总结类文件（Summary Files）

**关键词**：summary, SUMMARY, 总结, 摘要, 汇总, 概述

**用途**：项目总结、阶段总结、开发总结

**示例**：
- `PROJECT_SUMMARY.md` - 项目总结
- `sprint_summary.md` - 冲刺总结
- `development_summary.md` - 开发总结
- `release_summary.md` - 发布总结
- `quarter_summary.md` - 季度总结

**规则**：
- 必须在根目录生成
- 作为项目顶级文档
- 应该在 README.md 之前被查阅

##### 3. 指导类文件（Guidance Files）

**关键词**：guide, GUIDE, 指南, 手册, 实现, implementation

**用途**：实现指南、架构指南、开发指南

**示例**：
- `IMPLEMENTATION_GUIDE.md` - 实现指南
- `ARCHITECTURE_GUIDE.md` - 架构指南
- `setup_guide.md` - 设置指南
- `development_guide.md` - 开发指南
- `deployment_guide.md` - 部署指南

**规则**：
- 优先输出到根目录
- 新加入项目的开发者应该立即看到

##### 4. 计划类文件（Plan Files）

**关键词**：plan, PLAN, roadmap, ROADMAP, 路线图, 行动, 方案

**用途**：项目计划、实现计划、行动方案

**示例**：
- `IMPLEMENTATION_PLAN.md` - 实现计划
- `ACTION_PLAN.md` - 行动计划
- `roadmap.md` - 路线图
- `project_plan.md` - 项目计划
- `migration_plan.md` - 迁移计划

**规则**：
- 必须在根目录生成
- 用户可以立即了解项目方向

##### 5. 维护和检查清单（Maintenance Files）

**关键词**：maintenance, MAINTENANCE, checklist, CHECKLIST, 维护, 清单

**用途**：维护清单、发布检查清单、部署前检查

**示例**：
- `maintenance.md` - 维护指南
- `deployment_checklist.md` - 部署检查清单
- `release_checklist.md` - 发布检查清单
- `review_checklist.md` - 审查清单

**规则**：
- 必须在根目录生成
- 便于运维人员快速查阅

---

#### 优先级 2（可以输出到 docs/）

**这些文件类型可以遵循文档归档规范，输出到 docs/ 的相应子目录。**

##### 允许的文件类型

| 文件类型 | 位置 | 说明 |
|---------|------|------|
| 参考文档 | docs/reference | API 参考、技术参考 |
| 部署文档 | docs/deployment | 部署说明、配置指南 |
| 集成文档 | docs/integrations | 集成指南、第三方集成 |
| 其他指南 | docs/guides | 通用指南、最佳实践 |

---

### 强制执行规则

#### ✅ 必须做

1. **报告、总结、指南、计划文件只能在根目录生成**
   ```
   ✓ ANALYSIS_REPORT.md           (根目录)
   ✓ PROJECT_SUMMARY.md           (根目录)
   ✓ IMPLEMENTATION_GUIDE.md       (根目录)
   ✓ ACTION_PLAN.md               (根目录)
   ```

2. **不能将优先级1的文件放入任何子目录**
   ```
   ✗ docs/reference/analysis.md      (错误)
   ✗ docs/guides/guide.md            (错误)
   ✗ docs/deployment/plan.md         (错误)
   ```

3. **如果文件名同时符合多个规则，遵守最高优先级**
   ```
   IMPLEMENTATION_GUIDE.md
   ├─ 匹配"guide"规则 → 优先级1
   ├─ 匹配"implementation"规则 → 优先级1
   └─ 输出到：根目录 (优先级1最高)
   ```

#### ❌ 禁止做

1. **不要将报告文件放入子目录**
   ```
   ✗ docs/reference/performance_report.md
   ✗ docs/guides/analysis.md
   ```

2. **不要将计划文件放入子目录**
   ```
   ✗ docs/guides/implementation_plan.md
   ✗ docs/deployment/roadmap.md
   ```

3. **不要遵循文档归档规范来放置优先级1的文件**
   ```
   ✗ 忽视这个规则，按docs规范放置
   ✓ 遵循输出优先级规则
   ```

---

## 工作流程和验证

### 文件生成时的行为

#### 生成报告时

```
用户：请分析这个模块的性能问题

Claude:
1. 进行分析...
2. 生成报告...
3. 📝 我将生成 performance_report.md 到项目根目录，遵循文件输出优先级规则。
4. 创建 performance_report.md (在根目录)
```

#### 生成指南时

```
用户：为微服务架构生成实现指南

Claude:
1. 设计指南内容...
2. 📝 我将生成 ARCHITECTURE_GUIDE.md 到项目根目录，遵循文件输出优先级规则。
3. 创建 ARCHITECTURE_GUIDE.md (在根目录)
```

#### 生成参考文档时

```
用户：生成 API 参考文档

Claude:
1. 编写参考...
2. 📝 我将生成 API_REFERENCE.md 到 docs/reference/，遵循优先级2规则。
3. 创建 docs/reference/API_REFERENCE.md
```

### 验证规则是否生效

#### 方法1：查看文件位置

```bash
# 应该在根目录看到
ls -la *.md

# 应该包含
ANALYSIS_REPORT.md
PROJECT_SUMMARY.md
IMPLEMENTATION_GUIDE.md
ACTION_PLAN.md
```

#### 方法2：查看 Claude 的提示语句

当 Claude 生成文件时，应该看到类似：
```
📝 我将生成 [文件名] 到项目根目录，遵循文件输出优先级规则。
```

#### 方法3：检查日志

```bash
tail -f /tmp/claude_output_rules.log
```

---

## 实际场景示例

### 场景1：代码性能分析

**用户请求**：
```
请分析 data_processor.py 的性能问题
```

**预期行为**：
- 文件名：`data_processor_performance_analysis.md`
- 输出位置：项目根目录 ✓
- Claude 会说：`我将生成 data_processor_performance_analysis.md 到项目根目录...`

**不要做**：
```
❌ docs/reference/data_processor_analysis.md
❌ docs/guides/performance_analysis.md
```

### 场景2：项目实现指南

**用户请求**：
```
为新的认证系统生成实现指南
```

**预期行为**：
- 文件名：`AUTH_SYSTEM_IMPLEMENTATION_GUIDE.md`
- 输出位置：项目根目录 ✓
- 内容应该包含完整的实现步骤

**不要做**：
```
❌ docs/guides/developer/auth_guide.md
❌ docs/guides/implementation.md
```

### 场景3：部署说明

**用户请求**：
```
写部署说明
```

**预期行为**：
- 文件名：`deployment_guide.md` 或 `deployment.md`
- 输出位置：`docs/deployment/` ✓
- 因为不包含优先级1关键词，可以归档

**原因**：
- 关键词"deployment"本身不在优先级1列表中
- 需要加"guide"才能成为优先级1

### 场景4：项目总结

**用户请求**：
```
生成项目阶段总结
```

**预期行为**：
- 文件名：`PROJECT_PHASE_SUMMARY.md`
- 输出位置：项目根目录 ✓
- 应该在项目中最显眼的位置

**不要做**：
```
❌ docs/guides/summary.md
❌ docs/reference/project_summary.md
```

---

## 关键词参考表

### 优先级1 - 根目录

| 类型 | 英文关键词 | 中文关键词 |
|------|-----------|-----------|
| 报告 | report, analysis, evaluation | 分析, 报告, 评估 |
| 总结 | summary, overview, recap | 总结, 摘要, 汇总 |
| 指南 | guide, manual, implementation | 指南, 手册, 实现 |
| 计划 | plan, roadmap, strategy | 计划, 路线图, 方案 |
| 维护 | maintenance, checklist | 维护, 清单 |

### 优先级2 - docs/

| 类型 | 关键词 |
|------|--------|
| 参考 | reference, API, 参考 |
| 部署 | deployment, deploy, 部署 |
| 集成 | integration, integrate, 集成 |
| 开发 | development, developer, 开发 |

---

## 配置文件

### config.json 中的输出规则

```json
{
  "outputRules": {
    "enabled": true,
    "priority": "root-directory-first",
    "enforcementLevel": "strict"
  }
}
```

### output-rules.json

详细的规则定义文件，包含：
- 文件类型映射
- 优先级定义
- 强制执行规则
- 环境变量设置

---

## 常见问题

### Q1: 如果我想将某个文件放入 docs/ 目录怎么办？

**A**: 确保文件名不包含任何优先级1关键词。例如：
```
✓ deployment.md → docs/deployment/
✗ deployment_plan.md → 必须在根目录（包含"plan"关键词）
```

### Q2: 如何识别一个文件是优先级1还是优先级2？

**A**: 检查文件名是否包含任何这些关键词：
- 英文：report, analysis, summary, guide, plan, roadmap, maintenance, checklist
- 中文：分析, 报告, 总结, 摘要, 指南, 手册, 计划, 路线图, 维护, 清单

只要包含任何一个，就是优先级1。

### Q3: 同一个文件名包含两个优先级关键词怎么办？

**A**: 遵守最高优先级（优先级1）。例如：
```
deployment_guide.md
- 包含"deployment"（优先级2）
- 包含"guide"（优先级1）
→ 输出到：根目录（优先级1）
```

### Q4: 能修改规则吗？

**A**: 可以，修改以下文件：
1. `.claude/config.json` - 系统提示
2. `.claude/output-rules.json` - 详细规则定义
3. 确保修改后重启 Claude Code

### Q5: 为什么有优先级2的文件？

**A**: 并不是所有文件都需要在根目录。例如：
- API 参考文档 → docs/reference/ 是合理的
- 第三方集成说明 → docs/integrations/ 是合理的

优先级2是为了避免根目录过于拥挤。

---

## 故障排除

### 问题1：文件被放入了 docs/ 子目录

**症状**：
```
❌ docs/guides/ANALYSIS_REPORT.md (应该在根目录)
```

**解决方案**：
1. 检查 config.json 是否有 outputRules 配置
2. 确认 `"outputRules": {"enabled": true}`
3. 重启 Claude Code
4. 手动移动文件到根目录：`mv docs/guides/ANALYSIS_REPORT.md ./`

### 问题2：Claude 不遵循规则

**症状**：
```
用户：分析这个问题
Claude 在 docs/reference/ 中生成了 analysis.md
```

**解决方案**：
1. 检查系统提示是否包含输出规则部分
2. 显式提醒：`请按照文件输出优先级规则，报告应该在根目录`
3. 查看是否有多个配置文件冲突

### 问题3：找不到生成的文件

**症状**：
```
Claude 说生成了文件，但找不到
```

**解决方案**：
1. 搜索整个项目：`find . -name "*report*" -o -name "*analysis*"`
2. 查看临时目录：`/tmp/`
3. 检查是否需要刷新文件浏览器

---

## 最佳实践

### DO ✅

1. **优先级1文件立即在根目录查看**
   ```
   $ ls *.md
   ANALYSIS_REPORT.md
   PROJECT_SUMMARY.md
   IMPLEMENTATION_GUIDE.md
   ```

2. **对优先级2文件使用 docs/ 组织**
   ```
   docs/reference/API_REFERENCE.md
   docs/deployment/DEPLOYMENT_GUIDE.md
   ```

3. **使用一致的命名约定**
   ```
   ✓ ANALYSIS_REPORT.md (清晰的优先级指示)
   ✓ PROJECT_SUMMARY.md
   ✓ IMPLEMENTATION_GUIDE.md
   ```

4. **在版本控制中提交这些文件**
   ```
   git add ANALYSIS_REPORT.md PROJECT_SUMMARY.md
   git commit -m "docs: add analysis and summary"
   ```

### DON'T ❌

1. **不要将优先级1文件放入 docs/**
   ```
   ✗ docs/guides/analysis.md
   ✗ docs/reference/summary.md
   ```

2. **不要使用模糊的命名**
   ```
   ✗ report.md (不清楚是什么报告)
   ✓ PERFORMANCE_ANALYSIS_REPORT.md
   ```

3. **不要忽视文件输出规则**
   ```
   ✗ 按照 docs/ 规范放置所有文件
   ✓ 遵循优先级系统
   ```

---

## 相关文件

- `.claude/config.json` - 主配置文件（包含系统提示）
- `.claude/output-rules.json` - 详细规则定义
- `.claude/hooks/file-output-rule-hook` - 规则执行 hook

