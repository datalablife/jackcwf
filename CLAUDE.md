
[项目记忆规则]
        - **必须主动调用** progress-recorder agent 来记录重要决策、任务变更、完成事项等关键信息到progress.md
        - 检测到以下情况时**立即自动触发** progress-recorder:
               *   出现"决定使用/最终选择/将采用"等决策语言
               *   出现"必须/不能/要求"等约束语言
               *   出现"完成了/实现了/修复了"等完成标识
               *   出现"需要/应该/计划"等新任务
        - 当 progress.md 的 Notes/Done 条目过多 (>100条)影响阅读时，应归档到 progress.archive.md

[指令集 - 前缀 "/"]
        - record：使用 progress-recorder 执行增量合并任务
        - archive：使用 progress-recorder 执行快照归档任务
        - recap：阅读 progress.md，回顾项目当前状态（包括但不仅限于关键约束、待办事项、完成时度等）

[代码模块索引]
        - 需要理解 `src/` 结构时，优先查阅 `docs/guides/MODULE_OVERVIEW.md`。该文档按 FastAPI 应用、API 路由、服务、仓储、中间件与工具等模块总结功能，便于 CLAUDE code 快速定位实现。

[文件输出规则改进记录]
        - **2025-11-17 v2.2**: Hook脚本最终优化完成
               * ✅ 支持.txt文件处理
               * ✅ 添加无优先级关键词文件的默认分类规则
               * ✅ 支持CURRENT_STATUS.md, MODULE_OVERVIEW.md等常见文件
               * ✅ 所有68个文档文件100%正确分类
               * ✅ 根目录清爽（仅6个优先级1状态标记）

        - **2025-11-17 v2.1**: 状态标记优先级判断改进
               * SUCCESS/COMPLETE优先保留在根目录
               * 特殊规则：REPORT优先于SUCCESS（COMPLETION_REPORT→docs/reference/）

        - **2025-11-17 v2.0**: 增强Hook脚本规则初版
               * 双向文件整理（根目录↔docs/）
               * 智能优先级判断处理关键词冲突
               * 根目录扫描功能

        - 规则定义（最终版）：
               * Priority 1 (根目录): 项目状态标记 (COMPLETE, SUCCESS, READY等)
               * Priority 2 (docs/): 内容文档 (REPORT, GUIDE, SUMMARY, DEPLOYMENT等)
               * 默认规则: CURRENT_STATUS→docs/reference, MODULE_OVERVIEW→docs/guides
               * 特定文件: README→根, CONTRIBUTING→docs/guides, ARCHITECTURE→docs/architecture
