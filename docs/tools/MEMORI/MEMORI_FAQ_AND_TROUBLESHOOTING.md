# Memori集成FAQ和故障排查指南

**版本**: 1.0.0
**最后更新**: 2025-11-11
**适用范围**: Text2SQL项目Memori集成

---

## 目录

1. [常见问题 (FAQ)](#常见问题-faq)
2. [故障排查指南](#故障排查指南)
3. [性能问题诊断](#性能问题诊断)
4. [成本相关问题](#成本相关问题)
5. [安全和隐私](#安全和隐私)
6. [调试技巧](#调试技巧)

---

## 常见问题 (FAQ)

### Q1: Memori是否支持离线使用？

**A**: 不支持。Memori依赖Anthropic Claude API，需要网络连接。但您可以：
- 实施请求缓存来减少API调用
- 在本地存储常见查询的结果
- 使用本地模型作为降级方案（需要额外开发）

### Q2: 如何选择合适的Claude模型？

**A**: 根据场景选择：

| 场景 | 推荐模型 | 理由 |
|------|----------|------|
| 复杂SQL（多表JOIN） | Sonnet 4.5 | 最强推理能力 |
| 一般查询 | Sonnet 3.5 | 平衡性能和成本 |
| 简单查询/Schema查询 | Haiku 3 | 快速且经济 |
| 高并发场景 | Haiku 3 | 更高的速率限制 |

**动态选择示例**:
```python
def select_model(query: str, user_tier: str) -> str:
    if "JOIN" in query.upper() or "complex" in query.lower():
        return "claude-sonnet-4-5-20250929"
    elif user_tier == "free":
        return "claude-3-haiku-20240307"
    else:
        return "claude-3-5-sonnet-20241022"
```

### Q3: 记忆会在多个会话间共享吗？

**A**: 默认不会。每个会话有独立的记忆空间。但您可以：

**实现跨会话共享**:
```python
# 使用命名空间实现跨会话共享
# 例如：用户级别的偏好设置
await memori_service.add_conscious_memory(
    user_id="user_123",
    session_id="global",  # 特殊的全局会话
    content="用户偏好: 使用MySQL语法",
    namespace="user_preferences",
    importance=0.9
)

# 在任何会话中都可以检索
memories = await memori_service.search_memories(
    user_id="user_123",
    session_id="any_session",
    query="偏好",
    namespace="user_preferences"
)
```

### Q4: Token限制如何影响记忆数量？

**A**: Claude有上下文窗口限制（如8K tokens）。记忆越多，可用于实际对话的空间越少。

**最佳实践**:
```python
# 监控记忆大小
stats = await memori_service.get_memory_stats(user_id, session_id)
if stats["memory_tokens"] > 6000:  # 留2K给对话
    # 策略1: 清理低重要性记忆
    await cleanup_low_importance_memories(user_id, session_id)

    # 策略2: 归档旧记忆
    await archive_old_memories(user_id, session_id)

    # 策略3: 压缩记忆
    await consolidate_similar_memories(user_id, session_id)
```

### Q5: 如何实现实时流式响应？

**A**: 使用Claude的streaming API：

```python
from anthropic import AsyncAnthropic

client = AsyncAnthropic(api_key="...")

async def stream_response(user_id, session_id, messages):
    async with client.messages.stream(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            yield text  # 逐块返回给前端

# 在FastAPI中使用
from fastapi.responses import StreamingResponse

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    return StreamingResponse(
        stream_response(request.user_id, request.session_id, request.messages),
        media_type="text/event-stream"
    )
```

### Q6: Memori的记忆存储在哪里？

**A**: Memori默认使用内置的向量存储。您可以配置使用外部向量数据库：

**配置选项**:
1. **Memori内置** (默认): 简单，适合中小规模
2. **PostgreSQL pgvector**: 利用现有数据库，成本低
3. **Pinecone**: 专用向量DB，性能最优但成本较高
4. **Weaviate**: 开源向量DB，平衡选择

**切换到pgvector示例**:
```python
# 在未来版本中可能支持
memori = Memori(
    vector_store="pgvector",
    connection_string="postgresql://..."
)
```

### Q7: 如何处理敏感信息？

**A**: 实施多层保护：

```python
import re

class SensitiveDataFilter:
    """敏感数据过滤器"""

    PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone": r'\b\d{3}-\d{3}-\d{4}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "credit_card": r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'
    }

    @classmethod
    def mask(cls, text: str) -> str:
        """遮蔽敏感信息"""
        masked = text
        for name, pattern in cls.PATTERNS.items():
            masked = re.sub(pattern, f"[REDACTED_{name.upper()}]", masked)
        return masked

# 在保存记忆前使用
content = SensitiveDataFilter.mask(original_content)
await memori_service.add_conscious_memory(
    content=content,
    ...
)
```

### Q8: 记忆会自动过期吗？

**A**: Memori本身不自动过期记忆。您需要实施生命周期管理：

```python
from datetime import datetime, timedelta

async def cleanup_expired_memories(
    user_id: str,
    session_id: str,
    max_age_days: int = 30
):
    """清理过期记忆"""
    cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)

    # 获取所有记忆
    all_memories = await memori_service.search_memories(
        user_id=user_id,
        session_id=session_id,
        query="",  # 空查询获取所有
        limit=1000
    )

    # 删除过期记忆
    for memory in all_memories:
        if memory["timestamp"] < cutoff_date:
            await memori_service.delete_memory(
                user_id=user_id,
                session_id=session_id,
                memory_id=memory["id"]
            )

# 定期运行（如每天凌晨）
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()
scheduler.add_job(
    cleanup_expired_memories,
    'cron',
    hour=2,  # 凌晨2点
    args=["user_id", "session_id"]
)
scheduler.start()
```

### Q9: 如何测试Memori集成？

**A**: 分层测试策略：

**单元测试**:
```python
@pytest.mark.asyncio
async def test_add_memory():
    service = MemoriService()
    await service.add_conscious_memory(
        user_id="test",
        session_id="test",
        content="Test memory"
    )

    memories = await service.search_memories(
        user_id="test",
        session_id="test",
        query="test"
    )

    assert len(memories) > 0
```

**集成测试**:
```python
@pytest.mark.integration
async def test_end_to_end_text2sql():
    # 1. 添加schema记忆
    await add_schema_memory(datasource_id=1)

    # 2. 生成SQL
    response = await generate_sql(
        user_id="test",
        session_id="test",
        query="查询所有用户"
    )

    # 3. 验证结果
    assert "SELECT" in response["sql"]
    assert "users" in response["sql"].lower()
```

**性能测试**:
```python
import asyncio
import time

@pytest.mark.performance
async def test_concurrent_requests():
    start = time.time()

    tasks = [
        generate_sql("user_1", "session_1", "query")
        for _ in range(100)
    ]

    await asyncio.gather(*tasks)

    elapsed = time.time() - start
    avg_latency = elapsed / 100

    assert avg_latency < 2.0  # 平均延迟<2秒
```

### Q10: 生产环境部署需要注意什么？

**A**: 关键检查清单：

**1. 安全配置**
```bash
# 使用环境变量管理密钥
export MEMORI_ANTHROPIC_API_KEY=$(vault read secret/api_key)

# 启用HTTPS
uvicorn src.main:app --ssl-keyfile=key.pem --ssl-certfile=cert.pem

# 限制CORS
CORS_ORIGINS='["https://yourdomain.com"]'
```

**2. 性能优化**
```python
# 使用多worker
uvicorn src.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker

# 启用连接池
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
```

**3. 监控告警**
```yaml
# Prometheus metrics
- job_name: 'memori_service'
  static_configs:
    - targets: ['localhost:8000']

# Alert rules
- alert: HighErrorRate
  expr: rate(http_requests_total{status="500"}[5m]) > 0.1
  for: 5m
  annotations:
    summary: "High error rate detected"
```

**4. 备份策略**
```bash
# 每日备份记忆数据
0 2 * * * pg_dump -t memories > /backup/memories_$(date +\%Y\%m\%d).sql

# 保留30天备份
find /backup -name "memories_*.sql" -mtime +30 -delete
```

---

## 故障排查指南

### 问题类型1: API连接失败

**症状**:
```
Error: Could not connect to Anthropic API
Connection timeout
```

**诊断步骤**:

1. **检查API密钥**
```bash
# 验证环境变量
echo $MEMORI_ANTHROPIC_API_KEY

# 测试API密钥
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $MEMORI_ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-haiku-20240307","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'
```

2. **检查网络连接**
```bash
# 测试DNS解析
nslookup api.anthropic.com

# 测试连接
ping api.anthropic.com

# 检查防火墙
telnet api.anthropic.com 443
```

3. **检查代理设置**
```python
# 如果使用代理
import os
os.environ['HTTP_PROXY'] = 'http://proxy.company.com:8080'
os.environ['HTTPS_PROXY'] = 'http://proxy.company.com:8080'
```

**解决方案**:
- 确保API密钥正确且有效
- 检查网络防火墙规则
- 配置正确的代理设置
- 实施重试机制

### 问题类型2: 记忆隔离失败

**症状**:
```
User A can see User B's memories
Session mixing occurs
```

**诊断步骤**:

1. **验证session key生成**
```python
# 添加调试日志
def get_session_key(user_id, session_id, namespace):
    key = f"{user_id}:{session_id}:{namespace}"
    logger.debug(f"Generated session key: {key}")
    return key
```

2. **检查实例缓存**
```python
# 打印实例映射
logger.info(f"Active instances: {list(_memori_instances.keys())}")
```

3. **测试隔离性**
```python
async def test_isolation():
    # 添加User A的记忆
    await add_memory("userA", "session1", "A's memory")

    # 添加User B的记忆
    await add_memory("userB", "session1", "B's memory")

    # 搜索User A
    a_memories = await search("userA", "session1", "memory")
    assert all("A's" in m["content"] for m in a_memories)

    # 搜索User B
    b_memories = await search("userB", "session1", "memory")
    assert all("B's" in m["content"] for m in b_memories)
```

**解决方案**:
- 确保session key包含所有必要的隔离维度
- 使用强类型确保不会混淆参数
- 添加单元测试验证隔离性
- 在生产环境启用审计日志

### 问题类型3: Token限制错误

**症状**:
```
Error: This model's maximum context length is 8192 tokens
You requested 10000 tokens
```

**诊断步骤**:

1. **计算实际token使用**
```python
from src.services.token_manager import get_token_manager

token_manager = get_token_manager()

# 计算消息token
msg_tokens = token_manager.count_messages_tokens(messages)
logger.info(f"Messages tokens: {msg_tokens}")

# 计算记忆token
memory_tokens = sum(
    token_manager.count_tokens(m["content"])
    for m in memories
)
logger.info(f"Memory tokens: {memory_tokens}")

# 总计
total = msg_tokens + memory_tokens
logger.info(f"Total tokens: {total}")
```

2. **分析token分布**
```python
def analyze_token_distribution(messages, memories):
    breakdown = {
        "system": token_manager.count_tokens(system_prompt),
        "messages": token_manager.count_messages_tokens(messages),
        "memories": sum(token_manager.count_tokens(m["content"]) for m in memories),
        "max_tokens": max_tokens_param
    }

    total = sum(breakdown.values())
    logger.info(f"Token breakdown: {breakdown}")
    logger.info(f"Total: {total}")

    return breakdown
```

**解决方案**:

**方案1: 减少上下文**
```python
from src.services.optimization_strategies import CostOptimizer, OptimizationStrategy

optimizer = CostOptimizer(strategy=OptimizationStrategy.AGGRESSIVE)

# 修剪消息历史
optimized_messages = optimizer.optimize_context(
    messages=messages,
    max_tokens=4000  # 为记忆留出空间
)
```

**方案2: 减少记忆检索**
```python
# 减少检索数量
memories = await memori_service.search_memories(
    user_id=user_id,
    session_id=session_id,
    query=query,
    limit=5  # 从10减少到5
)
```

**方案3: 使用更大的模型**
```python
# Opus有更大的上下文窗口
model = "claude-3-opus-20240229"  # 200K context
```

### 问题类型4: 高延迟

**症状**:
```
Response time > 10 seconds
User experience degraded
```

**诊断步骤**:

1. **分解延迟**
```python
import time

async def diagnose_latency(user_id, session_id, query):
    timings = {}

    # 1. 数据库查询
    start = time.time()
    schema = await get_schema(datasource_id)
    timings["db_query"] = (time.time() - start) * 1000

    # 2. 记忆检索
    start = time.time()
    memories = await search_memories(user_id, session_id, query)
    timings["memory_retrieval"] = (time.time() - start) * 1000

    # 3. 上下文构建
    start = time.time()
    context = build_context(schema, memories, query)
    timings["context_build"] = (time.time() - start) * 1000

    # 4. Claude API调用
    start = time.time()
    response = await claude_api_call(context, query)
    timings["claude_api"] = (time.time() - start) * 1000

    logger.info(f"Latency breakdown: {timings}")
    return timings
```

2. **识别瓶颈**
```python
def identify_bottleneck(timings):
    bottleneck = max(timings.items(), key=lambda x: x[1])
    logger.warning(f"Bottleneck: {bottleneck[0]} ({bottleneck[1]:.2f}ms)")
    return bottleneck[0]
```

**解决方案**:

**针对数据库查询慢**:
```python
# 添加缓存
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_schema(datasource_id):
    return fetch_schema(datasource_id)

# 或使用Redis
import redis
cache = redis.Redis(host='localhost', port=6379, db=0)

def get_schema_with_cache(datasource_id):
    cached = cache.get(f"schema:{datasource_id}")
    if cached:
        return json.loads(cached)

    schema = fetch_schema(datasource_id)
    cache.setex(f"schema:{datasource_id}", 3600, json.dumps(schema))
    return schema
```

**针对记忆检索慢**:
```python
# 1. 减少检索数量
limit = 5  # 从10减少

# 2. 添加索引
# 如果使用PostgreSQL存储记忆
CREATE INDEX idx_memories_user_session ON memories(user_id, session_id);
CREATE INDEX idx_memories_embedding ON memories USING ivfflat (embedding);

# 3. 预过滤
# 先用简单条件过滤再做向量搜索
memories = await search_memories(
    user_id=user_id,
    session_id=session_id,
    query=query,
    filters={"type": "schema", "datasource_id": datasource_id}
)
```

**针对Claude API慢**:
```python
# 1. 使用更快的模型
model = "claude-3-haiku-20240307"  # 比Sonnet快3-5倍

# 2. 减少max_tokens
max_tokens = 1024  # 从4096减少

# 3. 实施超时
async with asyncio.timeout(5.0):  # 5秒超时
    response = await claude_api_call(...)
```

### 问题类型5: 成本超支

**症状**:
```
Monthly API cost exceeds budget
Unexpected charges
```

**诊断步骤**:

1. **分析成本分布**
```python
from src.services.monitoring import get_monitoring_service

monitoring = get_monitoring_service()

# 获取成本统计
stats = await monitoring.get_hourly_stats(hours=24)
print(f"24h total cost: ${stats['total_cost']:.2f}")
print(f"Avg cost per request: ${stats['avg_cost_per_request']:.4f}")

# 按用户分析
top_users = await get_top_users_by_cost(limit=10)
for user in top_users:
    print(f"User {user['id']}: ${user['cost']:.2f}")
```

2. **识别异常**
```python
# 查找异常高成本请求
expensive_requests = [
    r for r in recent_requests
    if r.estimated_cost > 0.10  # 超过$0.10的请求
]

for req in expensive_requests:
    logger.warning(
        f"Expensive request: user={req.user_id}, "
        f"tokens={req.total_tokens}, cost=${req.estimated_cost:.4f}"
    )
```

**解决方案**:

**1. 实施严格预算控制**
```python
class StrictBudgetManager:
    def __init__(self):
        self.daily_limits = {
            "free_tier": 10000,      # 10K tokens
            "basic_tier": 100000,    # 100K tokens
            "premium_tier": 1000000  # 1M tokens
        }

    async def check_budget(self, user_id, user_tier, estimated_tokens):
        # 获取今日使用量
        today_usage = await get_daily_usage(user_id)

        # 检查限额
        limit = self.daily_limits[user_tier]
        if today_usage + estimated_tokens > limit:
            raise HTTPException(
                status_code=429,
                detail=f"Daily limit reached ({limit} tokens)"
            )
```

**2. 自动成本优化**
```python
class AutoCostOptimizer:
    async def optimize_request(self, request):
        # 1. 检查缓存
        cached = await check_cache(request.query)
        if cached:
            return cached  # 成本=$0

        # 2. 选择合适的模型
        if request.complexity == "simple":
            model = "claude-3-haiku-20240307"  # $0.00025/1K
        else:
            model = "claude-sonnet-4-5-20250929"  # $0.003/1K

        # 3. 优化上下文
        optimized_context = trim_context(
            request.context,
            max_tokens=3000
        )

        return await call_claude(model, optimized_context)
```

**3. 实施告警**
```python
# 成本告警
async def check_cost_alerts():
    stats = await get_daily_stats()

    if stats["total_cost"] > DAILY_BUDGET * 0.8:
        await send_alert(
            "Cost Alert",
            f"Daily cost at {stats['total_cost']/DAILY_BUDGET:.1%} of budget"
        )

    if stats["total_cost"] > DAILY_BUDGET:
        await send_alert(
            "CRITICAL: Budget Exceeded",
            f"Daily cost ${stats['total_cost']:.2f} exceeds budget ${DAILY_BUDGET:.2f}"
        )

        # 自动限流
        await enable_rate_limiting()
```

---

## 性能问题诊断

### 性能基线

**建立基线**:
```python
# 记录正常情况下的性能指标
BASELINE_METRICS = {
    "api_latency_p50": 1500,  # ms
    "api_latency_p95": 3000,
    "api_latency_p99": 5000,
    "db_query_time": 50,
    "memory_retrieval_time": 200,
    "error_rate": 0.01,  # 1%
    "tokens_per_request": 3000,
    "cost_per_request": 0.05,  # USD
}
```

### 性能回归检测

```python
class PerformanceMonitor:
    def __init__(self, baseline):
        self.baseline = baseline

    async def check_regression(self, current_metrics):
        """检测性能回归"""
        regressions = []

        for metric, baseline_value in self.baseline.items():
            current_value = current_metrics.get(metric)

            if current_value is None:
                continue

            # 检查是否超过基线20%
            threshold = baseline_value * 1.2
            if current_value > threshold:
                regressions.append({
                    "metric": metric,
                    "baseline": baseline_value,
                    "current": current_value,
                    "regression": (current_value / baseline_value - 1) * 100
                })

        if regressions:
            logger.warning(f"Performance regressions detected: {regressions}")
            await send_alert("Performance Regression", regressions)

        return regressions
```

### 性能优化工具

```python
import cProfile
import pstats
from io import StringIO

def profile_function(func):
    """性能分析装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()

        result = await func(*args, **kwargs)

        pr.disable()
        s = StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats()

        logger.debug(f"Profile for {func.__name__}:\n{s.getvalue()}")

        return result
    return wrapper

# 使用
@profile_function
async def generate_sql(...):
    ...
```

---

## 成本相关问题

### 成本分析工具

```python
class CostAnalyzer:
    """成本分析工具"""

    @staticmethod
    async def analyze_cost_trends(days=30):
        """分析成本趋势"""
        # 获取历史数据
        daily_costs = await get_daily_costs(days=days)

        # 计算趋势
        avg_cost = sum(daily_costs) / len(daily_costs)
        trend = (daily_costs[-1] - daily_costs[0]) / daily_costs[0]

        # 预测
        projected_monthly = avg_cost * 30

        return {
            "avg_daily_cost": avg_cost,
            "trend_percent": trend * 100,
            "projected_monthly": projected_monthly,
            "daily_breakdown": daily_costs
        }

    @staticmethod
    async def find_cost_optimization_opportunities():
        """查找优化机会"""
        opportunities = []

        # 1. 检查缓存命中率
        cache_stats = await get_cache_stats()
        if cache_stats["hit_rate"] < 0.5:
            opportunities.append({
                "type": "cache",
                "current": cache_stats["hit_rate"],
                "potential_savings": "30-50%",
                "action": "Improve caching strategy"
            })

        # 2. 检查模型使用
        model_stats = await get_model_usage_stats()
        if model_stats["sonnet_ratio"] > 0.8:
            opportunities.append({
                "type": "model_selection",
                "current": f"{model_stats['sonnet_ratio']:.1%} Sonnet usage",
                "potential_savings": "40-60%",
                "action": "Use Haiku for simple queries"
            })

        # 3. 检查token使用
        token_stats = await get_token_stats()
        if token_stats["avg_tokens"] > 5000:
            opportunities.append({
                "type": "token_optimization",
                "current": f"{token_stats['avg_tokens']} avg tokens",
                "potential_savings": "20-40%",
                "action": "Implement context trimming"
            })

        return opportunities
```

### 成本优化建议生成器

```python
class CostOptimizationAdvisor:
    """成本优化建议生成器"""

    @staticmethod
    async def generate_recommendations():
        """生成优化建议"""
        recommendations = []

        # 分析当前状态
        cost_analysis = await CostAnalyzer.analyze_cost_trends()
        opportunities = await CostAnalyzer.find_cost_optimization_opportunities()

        # 生成建议
        for opp in opportunities:
            rec = {
                "priority": "high" if float(opp["potential_savings"].split("-")[0].strip("%")) > 40 else "medium",
                "title": f"Optimize {opp['type']}",
                "current_state": opp["current"],
                "expected_savings": opp["potential_savings"],
                "action_items": [opp["action"]],
                "estimated_effort": "medium"
            }
            recommendations.append(rec)

        # 按优先级排序
        recommendations.sort(
            key=lambda x: {"high": 0, "medium": 1, "low": 2}[x["priority"]]
        )

        return recommendations
```

---

## 安全和隐私

### 数据安全检查清单

```python
class SecurityAuditor:
    """安全审计工具"""

    CHECKS = [
        "api_key_exposure",
        "sensitive_data_in_logs",
        "unencrypted_storage",
        "weak_session_tokens",
        "missing_rate_limiting",
        "cors_misconfiguration"
    ]

    async def run_security_audit(self):
        """运行安全审计"""
        results = {}

        for check in self.CHECKS:
            method = getattr(self, f"check_{check}")
            results[check] = await method()

        # 生成报告
        report = self.generate_report(results)
        return report

    async def check_api_key_exposure(self):
        """检查API密钥暴露"""
        issues = []

        # 检查环境变量
        if "ANTHROPIC_API_KEY" in os.environ:
            issues.append("API key in environment variable")

        # 检查代码
        # (这里应该扫描代码文件)

        return {
            "status": "pass" if not issues else "fail",
            "issues": issues
        }

    async def check_sensitive_data_in_logs(self):
        """检查日志中的敏感数据"""
        # 扫描日志文件
        # 查找PII、密钥等
        return {"status": "pass", "issues": []}

    # 其他检查方法...
```

### 隐私保护实践

```python
class PrivacyProtector:
    """隐私保护工具"""

    @staticmethod
    def anonymize_user_data(data: dict) -> dict:
        """匿名化用户数据"""
        import hashlib

        anonymized = data.copy()

        # 哈希用户ID
        if "user_id" in anonymized:
            anonymized["user_id"] = hashlib.sha256(
                anonymized["user_id"].encode()
            ).hexdigest()[:16]

        # 移除PII
        pii_fields = ["email", "phone", "name", "address"]
        for field in pii_fields:
            if field in anonymized:
                anonymized[field] = "[REDACTED]"

        return anonymized

    @staticmethod
    def apply_data_retention_policy(days=90):
        """应用数据保留策略"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # 删除旧记忆
        deleted_count = await delete_memories_before(cutoff_date)

        logger.info(f"Deleted {deleted_count} memories older than {days} days")

        return deleted_count
```

---

## 调试技巧

### 启用详细日志

```python
import logging

# 为特定模块启用DEBUG日志
logging.getLogger('src.services.memori_service').setLevel(logging.DEBUG)
logging.getLogger('anthropic').setLevel(logging.DEBUG)

# 日志格式化
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/memori_debug.log'),
        logging.StreamHandler()
    ]
)
```

### 请求追踪

```python
import uuid
from contextvars import ContextVar

# 请求ID上下文
request_id_var: ContextVar[str] = ContextVar('request_id', default='')

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """添加请求ID中间件"""
    request_id = str(uuid.uuid4())
    request_id_var.set(request_id)

    # 添加到请求和响应头
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response

# 在日志中使用
logger.info(f"[{request_id_var.get()}] Processing request...")
```

### 性能追踪

```python
import time
from contextlib import asynccontextmanager

@asynccontextmanager
async def trace_operation(operation_name: str):
    """操作追踪上下文管理器"""
    start_time = time.time()
    request_id = request_id_var.get()

    logger.info(f"[{request_id}] Starting {operation_name}")

    try:
        yield
    except Exception as e:
        logger.error(
            f"[{request_id}] {operation_name} failed: {e}",
            exc_info=True
        )
        raise
    finally:
        elapsed = (time.time() - start_time) * 1000
        logger.info(
            f"[{request_id}] {operation_name} completed in {elapsed:.2f}ms"
        )

# 使用
async with trace_operation("generate_sql"):
    result = await generate_sql(...)
```

### 内存调试

```python
import tracemalloc

def debug_memory():
    """调试内存使用"""
    tracemalloc.start()

    # 执行操作...

    # 获取内存快照
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')

    print("[ Top 10 memory consumers ]")
    for stat in top_stats[:10]:
        print(stat)

    tracemalloc.stop()
```

---

## 联系支持

### 获取帮助的步骤

1. **查看文档**
   - 集成指南: `MEMORI_CLAUDE_INTEGRATION_GUIDE.md`
   - 快速开始: `MEMORI_QUICK_START.md`
   - 架构文档: `MEMORI_ARCHITECTURE_AND_DECISIONS.md`

2. **检查日志**
   - 应用日志: `/tmp/backend.log`
   - 调试日志: `/tmp/memori_debug.log`
   - 系统日志: `journalctl -u memori-service`

3. **运行诊断**
   ```bash
   # 健康检查
   curl http://localhost:8000/health

   # 性能统计
   curl http://localhost:8000/api/monitoring/stats/hourly

   # 系统信息
   curl http://localhost:8000/api/system/info
   ```

4. **收集信息**
   - 错误消息和堆栈跟踪
   - 请求ID
   - 时间戳
   - 环境配置

5. **提交Issue**
   - GitHub Issues: [项目仓库]
   - 邮件: support@example.com
   - Slack: #memori-support

---

**文档维护者**: AI Integration Team
**最后更新**: 2025-11-11
**版本**: 1.0.0
