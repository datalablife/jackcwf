# Tasks Template

## 项目宪法检查
- 所有任务是否按原则 #6 (语义代码组织) 分组? ✅
- 任务是否包含类型安全需求 (原则 #4)? ✅
- 任务是否包含异步实现需求 (原则 #5)? ✅
- 任务是否包含向量存储验收标准 (原则 #3)? ✅
- 任务是否包含中间件要求 (原则 #2)? ✅
- 任务是否包含测试和监控 (原则 #7, #8)? ✅

---

## 任务清单

### Epic: [FEATURE_NAME] 实现

**Epic 描述**: [高层功能描述]
**优先级**: P[0-3]
**预估工作量**: [X 周]
**相关原则**: [列出所有适用的原则]

---

## Story 1: [功能模块] 后端架构

**Story 点数**: [5-8]
**优先级**: P1
**涉及的原则**:
- AI-First 架构 (原则 #1)
- 类型安全 (原则 #4)
- 异步优先 (原则 #5)
- 语义组织 (原则 #6)

### 任务分解

#### Task 1.1: 数据模型设计
**类别**: Design
**完成标准**:
- [ ] 创建 Pydantic v2 数据模型 (`models/dto.py`)
- [ ] 所有字段包含类型注解和描述文档
- [ ] 模型通过 `mypy --strict` 检查
- [ ] 生成 OpenAPI 文档

**技术约束**:
```python
# 示例模型
from pydantic import BaseModel, Field

class ChatMessageDTO(BaseModel):
    id: str = Field(..., description="Unique message ID")
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    tokens_used: int = Field(default=0)
```

#### Task 1.2: 向量存储库实现
**类别**: Implementation
**完成标准**:
- [ ] 实现 `VectorRepository` 类，支持异步操作
- [ ] 实现 `embed_document()` - 文档向量化 (维度=1536)
- [ ] 实现 `search()` - 相似性搜索 (≤ 200ms P99)
- [ ] 实现 `batch_insert()` - 批量插入向量
- [ ] 为所有方法编写单元测试 (≥ 80% 覆盖)

**技术约束**:
```python
# 向量搜索示例
async def search(
    self,
    query_vector: List[float],
    limit: int = 5,
    threshold: float = 0.7
) -> List[dict]:
    """
    使用 HNSW 索引的余弦相似性搜索
    超时: ≤ 200ms P99
    """
    pass
```

**性能目标**:
- 单次查询延迟: ≤ 200ms P99
- 批量插入: ≤ 100ms per 1000 vectors
- 索引大小: < 100GB (with HNSW)

#### Task 1.3: Agent 服务集成
**类别**: Implementation
**完成标准**:
- [ ] 集成 LangChain v1.0 `create_agent()` API
- [ ] 实现 Agent 工具定义 (RAG、数据库查询等)
- [ ] 实现中间件系统 (认证、记忆注入、审核)
- [ ] 支持 LangGraph 持久化对话
- [ ] 单元测试覆盖率 ≥ 80%

**技术约束**:
```python
# Agent 创建示例
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o")
tools = [
    rag_tool,          # RAG 工具
    database_tool,     # 数据库查询
    web_search_tool    # Web 搜索
]
middleware = [
    AuthMiddleware(),
    MemoryInjectionMiddleware(),
    ContentModerationMiddleware()
]

agent = create_agent(
    llm=llm,
    tools=tools,
    middleware=middleware
)
```

---

## Story 2: [功能模块] 中间件和监控

**Story 点数**: [5]
**优先级**: P1
**涉及的原则**:
- 模块化中间件框架 (原则 #2)
- 可观测性 (原则 #8)
- 生产就绪 (原则 #7)

### 任务分解

#### Task 2.1: 中间件实现
**类别**: Implementation
**完成标准**:
- [ ] 实现 5 个核心中间件
  1. 认证中间件
  2. 记忆注入中间件
  3. 内容审核中间件
  4. 响应结构化中间件
  5. 审计日志中间件
- [ ] 所有中间件异步实现
- [ ] 异常处理和错误传播
- [ ] 中间件测试覆盖率 ≥ 90%

**技术约束**:
```python
# 中间件模板
class CustomMiddleware:
    async def __call__(self, request: Request, call_next: Callable) -> Any:
        # 请求处理 (入站)
        # ...

        response = await call_next(request)

        # 响应处理 (出站)
        # ...

        return response
```

#### Task 2.2: 监控和日志
**类别**: Implementation
**完成标准**:
- [ ] 配置结构化日志 (JSON 格式)
- [ ] 实现请求追踪 (X-Request-ID)
- [ ] 集成 OpenTelemetry
- [ ] 收集关键指标 (响应时间、错误率、吞吐量)
- [ ] 配置告警规则 (Prometheus)

**关键指标**:
| 指标 | 告警阈值 | 日志级别 |
|------|---------|---------|
| 响应时间 P99 | > 1000ms | WARNING |
| 错误率 | > 1% | CRITICAL |
| 向量搜索超时 | > 5% | WARNING |
| 数据库连接池满 | 100% | CRITICAL |

---

## Story 3: [功能模块] 前端集成

**Story 点数**: [8]
**优先级**: P1
**涉及的原则**:
- 类型安全 (原则 #4)
- 异步优先 (原则 #5)
- 语义组织 (原则 #6)

### 任务分解

#### Task 3.1: Tailark UI 集成
**类别**: Implementation
**完成标准**:
- [ ] 安装 Tailark 组件库
- [ ] 实现 Hero 组件 (登陆页面)
- [ ] 实现 Navigation 组件 (顶部导航)
- [ ] 实现 Form 组件 (文档上传)
- [ ] 响应式设计验证 (移动、平板、桌面)

**技术约束**:
```typescript
// 使用 Tailark 组件
import { HeroSection, NavigationBar, FileUploadForm } from "@tailark/ui"

export const Layout: React.FC = () => {
  return (
    <>
      <NavigationBar />
      <HeroSection title="AI Chat" subtitle="Ask your documents" />
      <FileUploadForm />
    </>
  )
}
```

#### Task 3.2: 实时通信 (WebSocket)
**类别**: Implementation
**完成标准**:
- [ ] 实现 WebSocket 连接 (Socket.IO)
- [ ] 支持流式响应
- [ ] 处理连接重连和心跳
- [ ] 错误处理和降级
- [ ] 集成测试覆盖率 ≥ 60%

**性能目标**:
- 连接建立时间: ≤ 500ms
- 消息延迟: ≤ 100ms
- 支持 100+ 并发连接

---

## Story 4: [功能模块] 测试和部署

**Story 点数**: [5-8]
**优先级**: P1
**涉及的原则**:
- 生产就绪 (原则 #7)
- 可观测性 (原则 #8)

### 任务分解

#### Task 4.1: 自动化测试
**类别**: Testing
**完成标准**:
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 集成测试覆盖率 ≥ 60%
- [ ] E2E 测试覆盖关键用户流程
- [ ] 所有测试在 CI/CD 中自动运行

**测试矩阵**:
| 层级 | 框架 | 覆盖率 | 示例 |
|------|------|--------|------|
| 单元 | pytest | ≥ 80% | 服务、存储库 |
| 集成 | pytest-asyncio | ≥ 60% | API 端点 |
| E2E | Playwright | 关键路径 | 用户对话流 |

#### Task 4.2: 部署和监控
**类别**: DevOps
**完成标准**:
- [ ] Dockerfile 已创建 (python:3.14-slim)
- [ ] GitHub Actions CI/CD 配置完成
- [ ] 蓝绿部署脚本已验证
- [ ] 健康检查端点 ≤ 500ms
- [ ] Grafana 仪表板已配置
- [ ] 告警规则已启用

**部署检查清单**:
- [ ] 所有环境变量已配置
- [ ] 数据库迁移已应用
- [ ] 向量索引已创建
- [ ] 备份和恢复流程已验证

---

## 按优先级排序的任务

### P0 (阻塞) - 必须完成才能发布

1. **Task 1.1**: 数据模型设计 (前置)
2. **Task 1.2**: 向量存储库实现
3. **Task 1.3**: Agent 服务集成
4. **Task 2.1**: 中间件实现

### P1 (高) - 应在第一个发布版本中完成

5. **Task 2.2**: 监控和日志
6. **Task 3.1**: Tailark UI 集成
7. **Task 3.2**: 实时通信

### P2 (中) - 后续迭代可完成

8. **Task 4.1**: 自动化测试
9. **Task 4.2**: 部署和监控

---

## 依赖关系图

```
Task 1.1 (数据模型)
  │
  ├─▶ Task 1.2 (向量存储)
  │      │
  │      └─▶ Task 1.3 (Agent)
  │
  ├─▶ Task 3.1 (UI)
  │
  └─▶ Task 2.1 (中间件)
       │
       └─▶ Task 2.2 (监控)
            │
            └─▶ Task 4.2 (部署)

Task 1.3 (Agent)
  │
  └─▶ Task 3.2 (WebSocket)
       │
       └─▶ Task 4.1 (测试)
```

---

## 完成标准 (Definition of Done)

每个 Task 完成必须满足:

- [ ] 代码已实现并提交到 GitHub
- [ ] 所有单元测试通过 (≥ 80% 覆盖率)
- [ ] mypy --strict 类型检查通过
- [ ] 代码审查已通过 (至少 1 个 maintainer)
- [ ] 文档已更新
- [ ] 相关监控指标已配置
- [ ] 性能目标已验证
- [ ] 没有新的安全漏洞

---

## 时间估算

| Story | Story Points | 预估工作量 (人天) | 预估完成时间 |
|-------|--------------|------------------|------------|
| Story 1 | 6-8 | 8-10 | 2 周 |
| Story 2 | 5 | 6-8 | 1.5 周 |
| Story 3 | 8 | 10-12 | 2 周 |
| Story 4 | 5-8 | 8-10 | 2 周 |
| **总计** | **24-29** | **32-40** | **7.5 周** |

---

## Notes

- 所有时间估算包括代码审查、测试和文档
- 如果遇到阻塞，立即升报
- 每日站会更新进度
- 参考资源: [constitution.md](../memory/constitution.md)
