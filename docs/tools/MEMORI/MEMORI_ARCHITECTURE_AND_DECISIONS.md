# Memori集成架构和决策分析

**文档版本**: 1.0.0
**创建日期**: 2025-11-11
**项目**: Text2SQL数据管理系统

---

## 架构概览

### 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Frontend (React/Vue)                              │
│                     用户界面 - 自然语言查询输入                               │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │ HTTPS/REST API
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FastAPI Application Layer                           │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        API Endpoints                                  │   │
│  │  /api/text2sql/generate  |  /api/ai/chat  |  /api/monitoring        │   │
│  └────────────┬──────────────────────────┬──────────────────┬───────────┘   │
│               │                          │                  │               │
│  ┌────────────▼───────────┐  ┌──────────▼─────────┐  ┌─────▼────────────┐  │
│  │   Session Manager      │  │  Token Manager     │  │  Monitoring      │  │
│  │  - Session validation  │  │  - Budget control  │  │  - Metrics       │  │
│  │  - Isolation control   │  │  - Cost tracking   │  │  - Analytics     │  │
│  └────────────┬───────────┘  └──────────┬─────────┘  └──────────────────┘  │
│               │                          │                                  │
│  ┌────────────▼──────────────────────────▼─────────────────────────────┐   │
│  │                      Memori Service Layer                            │   │
│  │  ┌──────────────────────────────────────────────────────────────┐   │   │
│  │  │              MemoriService (Singleton)                       │   │   │
│  │  │  - Session management (user:session:namespace)              │   │   │
│  │  │  - Memory CRUD operations                                   │   │   │
│  │  │  - Context injection                                        │   │   │
│  │  └─────────────┬──────────────────────────────┬─────────────────┘   │   │
│  │                │                              │                     │   │
│  │  ┌─────────────▼──────────┐    ┌─────────────▼──────────────────┐  │   │
│  │  │   Memori Instance      │    │   Claude Client (Async)        │  │   │
│  │  │   (per session)        │◄───┤   - Anthropic SDK              │  │   │
│  │  │                        │    │   - Memori.enable() wrapper    │  │   │
│  │  └─────────────┬──────────┘    └─────────────┬──────────────────┘  │   │
│  └────────────────┼───────────────────────────────┼─────────────────────┘   │
│                   │                               │                         │
└───────────────────┼───────────────────────────────┼─────────────────────────┘
                    │                               │
       ┌────────────▼────────────┐     ┌───────────▼────────────────┐
       │   Vector Database       │     │   Anthropic Claude API     │
       │   (Memori Storage)      │     │   - claude-sonnet-4-5      │
       │   - Embeddings          │     │   - Messages API           │
       │   - Semantic search     │     │   - Streaming support      │
       └─────────────────────────┘     └────────────────────────────┘
                    │
       ┌────────────▼────────────┐
       │   PostgreSQL Database   │
       │   - User sessions       │
       │   - Data sources        │
       │   - Query history       │
       └─────────────────────────┘
```

---

## 核心组件设计

### 1. MemoriService - 记忆管理核心

**职责**:
- 管理Memori实例生命周期
- 提供会话隔离
- 处理记忆的CRUD操作
- 集成Claude API调用

**设计模式**: Singleton + Factory

**关键方法**:
```python
class MemoriService:
    - get_memori_instance(user_id, session_id, namespace) -> Memori
    - get_claude_client(user_id, session_id, namespace) -> AsyncAnthropic
    - create_message(...) -> Dict[str, Any]
    - add_conscious_memory(...)
    - search_memories(...) -> List[Dict]
    - clear_session_memory(...)
    - get_memory_stats(...) -> Dict
```

**会话隔离策略**:
```
Session Key格式: {user_id}:{session_id}:{namespace}

示例:
- user_123:session_456:schema:1
- user_123:session_456:query
- user_456:session_789:schema:2
```

### 2. TokenManager - Token预算管理

**职责**:
- Token计数和估算
- 预算控制（每日、每请求）
- 成本追踪
- 使用统计

**预算控制流程**:
```
Request → Estimate Tokens → Check Budget → Allow/Deny
                                    ↓
                              Record Usage
                                    ↓
                              Update Stats
                                    ↓
                           Check Alert Threshold
```

**成本计算**:
```python
# Claude Sonnet 4.5 (2025年1月)
Input:  $0.003 per 1K tokens
Output: $0.015 per 1K tokens

Total Cost = (input_tokens / 1000 * 0.003) + (output_tokens / 1000 * 0.015)
```

### 3. SessionManager - 会话生命周期

**职责**:
- 会话创建和验证
- 超时管理
- 会话元数据管理

**会话状态机**:
```
[Created] → [Active] → [Inactive/Expired]
              ↓
         [Ended] (手动结束)
```

**超时策略**:
- 默认超时: 60分钟
- 每次请求刷新最后活动时间
- 后台任务定期清理过期会话

### 4. ContextBuilder - 智能上下文构建

**职责**:
- 根据查询构建相关上下文
- Schema信息注入
- 记忆检索和排序
- SQL示例选择

**上下文构建流程**:
```
User Query
    ↓
Schema Retrieval (from Memori namespace:schema:{id})
    ↓
Memory Search (semantic search in Memori)
    ↓
Example Selection (based on query type)
    ↓
Context Assembly
    ↓
Token Optimization
    ↓
Final Context String
```

---

## 关键决策点分析

### 决策1: 使用直接Anthropic SDK vs LiteLLM

| 因素 | Anthropic SDK | LiteLLM | 决策 |
|------|---------------|---------|------|
| Memori支持 | 原生支持 | 需要适配 | ✅ Anthropic SDK |
| 性能 | 最优 | 有额外开销 | ✅ Anthropic SDK |
| 多模型支持 | 仅Anthropic | 多提供商 | - |
| 类型提示 | 完整 | 一般 | ✅ Anthropic SDK |
| 维护成本 | 官方维护 | 社区依赖 | ✅ Anthropic SDK |

**最终决策**: 使用直接Anthropic SDK

**理由**:
1. Memori官方文档推荐使用Anthropic SDK
2. 更好的性能和类型支持
3. 当前项目只需要Claude，不需要多模型支持
4. 如果未来需要多模型，在服务层抽象即可

### 决策2: Memori实例管理 - 全局 vs 按会话

| 方案 | 优点 | 缺点 | 决策 |
|------|------|------|------|
| 全局单例 | 简单、资源高效 | 隔离复杂、风险高 | ❌ |
| 按用户创建 | 用户隔离 | 会话混淆风险 | ❌ |
| 按会话创建 | 完全隔离、清晰 | 资源开销较大 | ✅ |

**最终决策**: 按会话创建Memori实例

**实现方式**:
```python
# 使用字典缓存实例，key为 user:session:namespace
_memori_instances: Dict[str, Memori] = {}

def get_instance(user_id, session_id, namespace):
    key = f"{user_id}:{session_id}:{namespace}"
    if key not in _memori_instances:
        _memori_instances[key] = Memori(user_id=key)
    return _memori_instances[key]
```

**清理策略**:
- 会话结束时清理
- 后台任务定期清理过期实例
- 实施LRU淘汰（保留最近N个活跃会话）

### 决策3: Memory Mode - Conscious vs Auto

| 场景 | Conscious | Auto | 推荐 |
|------|-----------|------|------|
| Schema信息 | ✅ | ❌ | Conscious (高优先级) |
| 用户配置 | ✅ | ❌ | Conscious (持久化) |
| 对话历史 | ❌ | ✅ | Auto (自动管理) |
| SQL查询结果 | ✅ | ❌ | Conscious (重要查询) |
| 临时提示 | ❌ | ✅ | Auto (短期记忆) |

**决策原则**:
1. **高价值、长期信息**: 使用Conscious Mode
2. **对话流、临时信息**: 使用Auto Mode
3. **重要性≥0.8**: 使用Conscious Mode
4. **需要精确控制**: 使用Conscious Mode

### 决策4: Token预算控制策略

| 策略 | 描述 | 适用场景 |
|------|------|----------|
| 激进 (Aggressive) | 严格限制，快速拒绝 | 成本敏感、高流量 |
| 平衡 (Balanced) | 适度控制，用户友好 | 一般生产环境 ✅ |
| 宽松 (Loose) | 最小限制，最大灵活性 | 内部工具、测试 |

**最终决策**: 平衡策略

**配置**:
```python
# 平衡策略配置
DAILY_TOKEN_LIMIT = 1,000,000  # 每日100万token
PER_REQUEST_LIMIT = 8,000      # 单次8K token
ALERT_THRESHOLD = 0.8          # 80%告警
```

**动态调整**:
- 高峰时段自动降级（使用Haiku模型）
- VIP用户提高限额
- 批量任务独立配额

### 决策5: 并发控制模型

| 模型 | 复杂度 | 公平性 | 性能 | 决策 |
|------|--------|--------|------|------|
| 全局信号量 | 低 | 低 | 高 | ❌ |
| 用户级信号量 | 中 | 中 | 中 | ✅ |
| 优先级队列 | 高 | 高 | 低 | ❌ |

**最终决策**: 全局+用户级双层信号量

**实现**:
```python
global_semaphore = asyncio.Semaphore(10)  # 全局10并发
user_semaphores = {
    user_id: asyncio.Semaphore(3)  # 每用户3并发
}
```

**优势**:
- 防止单用户占满所有资源
- 保证系统整体稳定性
- 实现简单，性能好

### 决策6: 记忆存储架构

| 方案 | 优点 | 缺点 | 决策 |
|------|------|------|------|
| Memori内置存储 | 简单、集成好 | 扩展性有限 | ✅ (初期) |
| PostgreSQL pgvector | 已有DB、成本低 | 性能一般 | 候选 |
| 专用向量DB (Pinecone) | 性能最优 | 成本高、复杂 | ❌ (当前) |

**最终决策**: 使用Memori内置存储，预留扩展接口

**扩展计划**:
```python
class MemoryStorage(ABC):
    @abstractmethod
    async def store(self, memory): pass

    @abstractmethod
    async def search(self, query): pass

# 当前实现
class MemoriStorage(MemoryStorage):
    # 使用Memori内置存储

# 未来可扩展
class PgVectorStorage(MemoryStorage):
    # 使用PostgreSQL pgvector

class PineconeStorage(MemoryStorage):
    # 使用Pinecone
```

---

## 性能优化策略

### 1. Token优化

**策略矩阵**:

| 场景 | 优化方法 | 预期节省 |
|------|----------|----------|
| 重复查询 | 语义缓存 | 70-90% |
| 长对话历史 | 上下文修剪 | 30-50% |
| 大Schema | 智能选择相关表 | 40-60% |
| 示例冗余 | 动态选择最相关示例 | 20-30% |

**实现优先级**:
1. 语义缓存（最高ROI）
2. 上下文修剪
3. Schema智能选择
4. 示例优化

### 2. 延迟优化

**延迟分解**:
```
Total Latency = DB Query + Memory Retrieval + Claude API + Post-processing

目标:
- DB Query: < 50ms
- Memory Retrieval: < 200ms
- Claude API: 1000-3000ms (不可控)
- Post-processing: < 50ms

Total Target: < 3300ms
```

**优化措施**:
```python
# 1. 并行化
async def optimized_generate_sql():
    # 并行执行数据库查询和记忆检索
    schema, memories = await asyncio.gather(
        get_schema(datasource_id),
        search_memories(query)
    )

# 2. 预取
# 在用户输入时预加载schema
await prefetch_schema(datasource_id)

# 3. 流式响应
# 使用Claude streaming API
async for chunk in client.messages.stream(...):
    yield chunk
```

### 3. 成本优化

**成本控制矩阵**:

| 方法 | 实施难度 | 节省潜力 | 优先级 |
|------|----------|----------|--------|
| 语义缓存 | 中 | 高 (70%) | P0 |
| 模型选择 | 低 | 中 (50%) | P0 |
| Token修剪 | 中 | 中 (40%) | P1 |
| 批处理 | 高 | 低 (20%) | P2 |

**成本优化决策树**:
```
Query Received
    ↓
Is cached? → Yes → Return cached (Cost: $0)
    ↓ No
Is simple query? → Yes → Use Haiku ($)
    ↓ No
Is complex query? → Yes → Use Sonnet ($$)
    ↓
Token > 5000? → Yes → Trim context
    ↓
Execute with optimization
```

---

## 监控和告警策略

### 监控指标层级

**L1 - 系统健康指标** (实时监控):
- API可用性 (target: 99.9%)
- 错误率 (target: < 1%)
- 平均延迟 (target: < 3s)
- P95延迟 (target: < 5s)

**L2 - 业务指标** (小时级):
- 总请求数
- Token使用量
- 成本消耗
- 活跃用户数
- 会话数量

**L3 - 记忆指标** (天级):
- 记忆总量
- 平均记忆大小
- 记忆增长率
- 检索命中率

**L4 - 成本指标** (周级):
- 总成本趋势
- 每用户成本
- ROI分析

### 告警规则

**P0 - 紧急** (立即响应):
```yaml
- name: API完全不可用
  condition: error_rate > 50% for 5m
  action: 立即通知、自动降级

- name: 成本异常
  condition: hourly_cost > threshold * 3
  action: 限流、通知管理员
```

**P1 - 严重** (15分钟内响应):
```yaml
- name: 高错误率
  condition: error_rate > 10% for 10m
  action: 通知on-call

- name: 高延迟
  condition: p95_latency > 10s for 15m
  action: 检查瓶颈
```

**P2 - 警告** (1小时内处理):
```yaml
- name: Token使用接近限额
  condition: daily_usage > limit * 0.8
  action: 通知、准备降级

- name: 记忆大小异常
  condition: memory_size > threshold
  action: 触发清理任务
```

---

## 扩展性和未来演进

### 短期优化 (1-3个月)

1. **实施语义缓存**
   - 使用Redis存储查询-结果映射
   - 基于embedding相似度匹配
   - 预期节省70%成本

2. **优化记忆检索**
   - 实施索引优化
   - 引入预过滤
   - 减少检索延迟

3. **完善监控**
   - 集成APM工具
   - 实施分布式追踪
   - 建立性能基线

### 中期演进 (3-6个月)

1. **多模型支持**
   - 抽象模型接口
   - 支持GPT-4、Gemini等
   - 实施模型路由

2. **高级记忆管理**
   - 记忆重要性自动评分
   - 记忆生命周期管理
   - 记忆压缩和归档

3. **智能优化**
   - 基于历史的自动调优
   - 预测性扩容
   - 成本优化建议

### 长期规划 (6-12个月)

1. **分布式架构**
   - 微服务拆分
   - 独立的记忆服务
   - 跨区域部署

2. **AI增强**
   - 使用AI优化记忆管理
   - 自动上下文构建
   - 智能成本控制

3. **企业级特性**
   - 多租户支持
   - 细粒度权限控制
   - 审计和合规

---

## 风险评估和缓解

### 技术风险

| 风险 | 影响 | 可能性 | 缓解措施 |
|------|------|--------|----------|
| Claude API限流 | 高 | 中 | 实施重试、队列、降级 |
| 记忆数据膨胀 | 中 | 高 | 生命周期管理、定期清理 |
| 会话隔离失败 | 高 | 低 | 严格测试、代码审查 |
| Token成本失控 | 中 | 中 | 多层预算控制、告警 |

### 运营风险

| 风险 | 影响 | 可能性 | 缓解措施 |
|------|------|--------|----------|
| API密钥泄露 | 高 | 低 | 密钥管理服务、定期轮换 |
| 服务过载 | 中 | 中 | 并发控制、自动扩容 |
| 数据丢失 | 高 | 低 | 定期备份、冗余存储 |
| 合规问题 | 中 | 低 | 数据加密、访问日志 |

### 业务风险

| 风险 | 影响 | 可能性 | 缓解措施 |
|------|------|--------|----------|
| 用户体验差 | 高 | 中 | 性能优化、降级策略 |
| 成本超预算 | 中 | 中 | 严格预算控制、优化 |
| 竞争对手超越 | 中 | 中 | 持续创新、快速迭代 |

---

## 总结

### 核心优势

1. **完整的会话隔离**: 确保多用户、多会话安全
2. **智能成本控制**: 多层预算管理，避免失控
3. **高性能架构**: 异步处理，并发优化
4. **可扩展设计**: 模块化，易于演进

### 技术债务

1. **记忆存储**: 当前依赖Memori内置，未来需要迁移到专用向量DB
2. **缓存层**: 缺少Redis缓存层，需要尽快实施
3. **监控**: 监控工具集成不完整，需要加强

### 下一步行动

**立即行动** (本周):
1. 部署基础Memori集成
2. 实施Token预算控制
3. 建立基础监控

**近期计划** (本月):
1. 完善会话管理
2. 优化上下文构建
3. 实施语义缓存

**持续优化** (持续):
1. 监控性能指标
2. 收集用户反馈
3. 迭代优化策略

---

**文档维护者**: AI Integration Team
**最后更新**: 2025-11-11
**版本**: 1.0.0
