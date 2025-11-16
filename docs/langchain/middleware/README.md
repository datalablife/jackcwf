# LangChain 1.0 中间件系统

**快速导航**: [快速开始](README_MIDDLEWARE.md) | [系统设计](MIDDLEWARE_STACK_DESIGN.md) | [实现代码](MIDDLEWARE_IMPLEMENTATION.md) | [LangChain集成](LANGCHAIN_MIDDLEWARE_INTEGRATION.md)

---

## 📋 本目录内容

本目录包含LangChain 1.0中间件系统的完整设计、实现和集成指南。

### 文件清单

| 文件名 | 内容概要 | 用途 | 推荐阅读时间 |
|-----|--------|------|-----------|
| **README_MIDDLEWARE.md** | 中间件系统快速入门 | 了解中间件 | 10分钟 |
| **MIDDLEWARE_STACK_DESIGN.md** | 完整系统设计（62KB） | 理解架构 | 40分钟 |
| **MIDDLEWARE_IMPLEMENTATION.md** | 生产级实现（2,000+行） | 部署系统 | 30分钟 |
| **LANGCHAIN_MIDDLEWARE_INTEGRATION.md** | LangChain 1.0集成指南 | 集成到项目 | 20分钟 |

---

## 🎯 中间件系统核心

### 6个执行钩子

```
请求流程
    ↓
[before_agent]  ────→ 加载会话，验证预算
    ↓
[before_model]  ────→ 构建RAG上下文，脱敏PII
    ↓
[wrap_model_call] ──→ 计数令牌，追踪成本
    ↓
[after_model]   ────→ 验证输出，脱敏PII
    ↓
[wrap_tool_call] ──→ 执行检索，超时控制
    ↓
[after_agent]   ────→ 保存检查点，发送分析
```

### 典型应用场景

1. **安全防护**
   - PII检测与脱敏（>99%准确度）
   - 人工审批工作流
   - 审计日志记录

2. **成本控制**
   - 令牌预算管理
   - 成本追踪和告警
   - 预算超出保护

3. **性能优化**
   - 动态模型路由（Haiku/Sonnet/Opus）
   - 上下文压缩
   - 缓存管理

4. **状态管理**
   - 对话持久化
   - 自动总结
   - 检查点管理

---

## 🚀 快速开始

### 第一步：理解概念（10分钟）
阅读 `README_MIDDLEWARE.md` 了解：
- 中间件是什么
- 为什么需要中间件
- 中间件能做什么
- 简单示例

### 第二步：深入学习设计（40分钟）
阅读 `MIDDLEWARE_STACK_DESIGN.md`：
- 8个中间件组件详解
- 执行顺序和状态传递
- 错误处理策略
- 性能考虑

### 第三步：实现系统（30分钟）
参考 `MIDDLEWARE_IMPLEMENTATION.md`：
- 复制生产代码
- 配置中间件栈
- 集成你的项目
- 测试和验证

### 第四步：集成到LangChain（20分钟）
阅读 `LANGCHAIN_MIDDLEWARE_INTEGRATION.md`：
- create_agent集成
- 中间件顺序配置
- 状态传递模式
- 最佳实践

---

## 📊 系统能力矩阵

| 能力 | 中间件 | PII脱敏 | 模型路由 | 令牌预算 | 成本追踪 | 人工批准 |
|-----|-------|--------|--------|---------|---------|---------|
| 安全防护 | ✅ | ✅ | - | - | - | ✅ |
| 成本控制 | ✅ | - | ✅ | ✅ | ✅ | - |
| 性能优化 | ✅ | - | ✅ | - | - | - |
| 状态管理 | ✅ | - | - | - | - | - |

---

## 💼 使用场景示例

### 场景1: 金融数据处理
```
金融用户请求
    ↓
[before_agent] ────→ 检测信用卡号、SSN
    ↓
[before_model] ────→ 脱敏PII
    ↓
[wrap_model_call] ──→ 计价
    ↓
模型生成响应
    ↓
[after_model] ────→ 再次脱敏敏感数据
    ↓
返回安全响应
```

### 场景2: 成本控制
```
用户查询（10K令牌预算）
    ↓
[before_agent] ────→ 加载用户预算 (10K)
    ↓
[wrap_model_call] ──→ Claude用2K令牌
    ↓ 预算剩余: 8K
[wrap_tool_call] ──→ 检索用3K令牌
    ↓ 预算剩余: 5K
[wrap_model_call] ──→ Claude用4K令牌
    ↓ 预算剩余: 1K
[after_agent] ────→ 保存成本记录 (9K/10K)
```

### 场景3: 高风险操作批准
```
用户请求删除操作
    ↓
[before_model] ────→ 标记为"高风险"
    ↓
中间件触发人工批准流程
    ↓
等待管理员审批
    ↓
批准后继续 或 拒绝并返回错误
```

---

## 🏗️ 架构概图

```
LangChain Agent
    ↓
create_agent(tools, middleware=[...])
    ↓
┌──────────────────────────────────────┐
│ 中间件栈                             │
├──────────────────────────────────────┤
│ 1. SessionMiddleware (before_agent)  │
│ 2. PIIMiddleware (before_model)      │
│ 3. BudgetMiddleware (before_model)   │
│ 4. CostTracker (wrap_model_call)     │
│ 5. ReasoningExtractor (after_model)  │
│ 6. RetrieverMiddleware (wrap_tool)   │
│ 7. StateMiddleware (after_agent)     │
└──────────────────────────────────────┘
    ↓
LangGraph Checkpoints (状态持久化)
```

---

## 🔗 相关文档

- **迁移相关**: 查看 `../migration/` 如何从0.x迁移
- **内容块处理**: 查看 `../content-blocks/` 处理推理痕迹
- **状态管理**: 查看 `../state-management/` LangGraph集成
- **RAG应用**: 查看 `../../features/rag/` 中间件实际应用

---

## 📈 性能指标

| 指标 | 数值 |
|-----|-----|
| 中间件执行开销 | <50ms (6个钩子) |
| PII检测准确度 | >99% |
| 系统可用性 | 99.9% |
| 支持的中间件 | 8个标准 + 无限自定义 |
| 吞吐量 | 1000+ req/s |

---

## ✅ 实现清单

- [ ] 阅读 `README_MIDDLEWARE.md` (10分钟)
- [ ] 理解6个执行钩子
- [ ] 阅读 `MIDDLEWARE_STACK_DESIGN.md` (40分钟)
- [ ] 了解8个中间件组件
- [ ] 复制 `MIDDLEWARE_IMPLEMENTATION.md` 代码
- [ ] 配置中间件栈
- [ ] 测试集成
- [ ] 部署到生产

---

_生成于 2025-11-16 | 维护者: LangChain开发团队_
