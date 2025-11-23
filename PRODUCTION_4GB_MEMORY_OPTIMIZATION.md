# 4GB内存生产环境优化策略调整

## 📊 内存占用分析

### 完整优化栈的内存占用（我之前推荐的）

| 组件 | 内存占用 | 备注 |
|------|---------|------|
| FastAPI 后端 | 200-300MB | 必需 |
| PostgreSQL | 500MB-1GB | 必需 |
| Redis (512MB配置) | 512MB | 可选，但推荐 |
| Elasticsearch | 1-2GB | **问题：太大** |
| Logstash | 256-512MB | **问题：太大** |
| Kibana | 256-512MB | **问题：太大** |
| Prometheus | 256-512MB | **问题：太大** |
| Grafana | 128-256MB | **问题：太大** |
| AlertManager | 64MB | OK |
| **总计** | **3.8-6.5GB** | **❌ 不适合4GB服务器** |

---

## ⚠️ 4GB内存的风险

### 当前完整栈的问题

1. **OOM Kill（内存溢出）**
   - 系统会自动杀死内存占用最大的进程
   - 通常是Elasticsearch或后端服务被杀死
   - 导致服务间歇性崩溃

2. **Swap磁盘交换（致命）**
   - 内存溢出时使用磁盘（极慢）
   - 导致响应时间从毫秒级变成秒级
   - 整个应用陷入"假死"状态

3. **无法突发处理**
   - 没有缓冲空间
   - 任何流量峰值都会导致崩溃

---

## ✅ 推荐方案：分层优化（4GB内存）

### 方案选择矩阵

| 优先级 | 功能 | 内存 | 必需性 | 推荐 |
|--------|------|------|--------|------|
| P1 | FastAPI 后端 | 200-300MB | ✅ 必需 | **部署** |
| P1 | PostgreSQL | 500MB-1GB | ✅ 必需 | **部署** |
| P2 | Redis 缓存 | 256MB | ✅ 高推荐 | **部署（缩小）** |
| P3 | Prometheus | 100-200MB | ⭐ 重要 | **部署（轻量版）** |
| P4 | Grafana | 100-150MB | ⭐ 推荐 | **部署（可选）** |
| P5 | Elasticsearch | 1-2GB | ⚠️ 可选 | **跳过/外部服务** |
| P5 | Logstash | 256-512MB | ⚠️ 可选 | **跳过/替代品** |
| P5 | Kibana | 256-512MB | ⚠️ 可选 | **跳过** |

---

## 🎯 推荐部署方案（4GB内存）

### 方案：轻量级监控 + Redis缓存 + 数据库优化

**总内存占用：2.5-3.2GB** ✅

```
┌─────────────────────────────────────────┐
│         4GB 内存分配方案                 │
├─────────────────────────────────────────┤
│ 系统保留（Linux kernel） .... 300MB     │
│ FastAPI 后端 ............... 250MB     │
│ PostgreSQL ................. 800MB     │
│ Redis 缓存 ................. 256MB     │
│ Prometheus ................. 150MB     │
│ Grafana (可选) ............. 100MB     │
│ 文件系统缓存 ............... 500MB     │
│ 应急缓冲 ................... 544MB     │
├─────────────────────────────────────────┤
│ 总计 .................. ~3.2GB         │
└─────────────────────────────────────────┘
```

---

## 📋 分阶段部署指南

### PHASE 1: 核心组件（Week 1）- 必需 ✅

#### Step 1: 调整 PostgreSQL 内存配置

编辑 PostgreSQL 配置（或通过 Coolify 环境变量）：

```ini
# 针对 4GB 内存的优化
shared_buffers = 256MB        # 25% of total RAM
effective_cache_size = 1GB    # 25% of total RAM
work_mem = 8MB                # shared_buffers / max_connections
maintenance_work_mem = 64MB   # 1/6 of available RAM
```

**为什么这样配置**：
- 不会争夺其他服务的内存
- PostgreSQL 会自动利用操作系统缓存
- 足以处理大多数查询

#### Step 2: 部署 Redis 缓存（缩小配置）

```bash
docker run -d \
  --name redis-cache \
  --restart unless-stopped \
  -p 6379:6379 \
  -v redis-data:/data \
  redis:7-alpine \
  redis-server \
    --appendonly yes \
    --maxmemory 256mb \
    --maxmemory-policy allkeys-lru \
    --save 900 1 \
    --save 300 10 \
    --save 60 10000
```

**4GB 专用配置**：
```env
# .env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_MAX_MEMORY=256      # MB

# 缓存策略（针对4GB）
CACHE_TTL_CONVERSATION=1800        # 30分钟（默认1小时）
CACHE_TTL_USER=3600                # 1小时
CACHE_TTL_DOCUMENT=43200           # 12小时（默认24小时）
```

**预期性能**：
- Cache Hit Rate: 50-70%（仍然很好）
- Latency improvement: 60%↓
- Memory usage: **仅256MB**

#### Step 3: 启用 Redis 缓存集成

参考之前的 "PHASE 2: Redis Caching Integration" 步骤（完全相同）

```python
# src/main.py - 在 lifespan 中添加 Redis 初始化
redis_cache = RedisCache(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 0)),
    password=os.getenv("REDIS_PASSWORD"),
    ssl=os.getenv("REDIS_SSL", "false").lower() == "true"
)
await redis_cache.initialize()
app.state.redis_cache = redis_cache
```

#### Step 4: 数据库查询优化（无内存成本）

这些优化**完全不占用额外内存**，反而能减少内存使用：

```python
# 优化 1: 使用 eager loading（减少数据库连接）
from sqlalchemy.orm import selectinload

stmt = select(Conversation).options(
    selectinload(Conversation.messages),
    selectinload(Conversation.user)
)

# 优化 2: 实现 cursor 分页（比 OFFSET 节省 90% 内存）
if cursor:
    query = query.where(Message.id > cursor).limit(50)

# 优化 3: 添加数据库索引（无内存开销）
# 创建 migration...
```

**预期性能**：
- 数据库查询速度: 10-100x↑
- 数据库连接数: 减少 60%
- Memory usage: **-50MB**

---

### PHASE 2: 轻量级监控（Week 2）- 强烈推荐 ⭐

#### Option A: Prometheus 只 + Grafana（推荐）

**总内存**: 250MB

```bash
# Prometheus 配置（轻量级）
docker run -d \
  --name prometheus \
  --restart unless-stopped \
  -p 9090:9090 \
  -v prometheus-data:/prometheus \
  prom/prometheus:latest \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/prometheus \
  --storage.tsdb.retention.time=7d \        # 仅保留 7 天（默认 30 天）
  --query.max-samples=10000000
```

**4GB 专用 Prometheus 配置**：

```yaml
# monitoring/prometheus/prometheus.yml
global:
  scrape_interval: 30s          # 改为 30s（默认 15s）
  evaluation_interval: 30s      # 改为 30s
  external_labels:
    monitor: 'langchain-ai'

# 减少 alert 规则数量
rule_files:
  - 'alerts-4gb.yml'            # 只加载关键告警

scrape_configs:
  - job_name: 'fastapi'
    static_configs:
      - targets: ['localhost:8000']
    scrape_interval: 60s         # FastAPI 改为 60s
    metrics_path: '/metrics'
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
```

**创建精简告警规则** `monitoring/prometheus/alerts-4gb.yml`：

```yaml
groups:
  - name: critical-4gb
    rules:
      # 仅保留关键告警（从 47 个减少到 10 个）

      - alert: ServiceDown
        expr: up{job="fastapi"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Service is down"

      - alert: HighMemoryUsage
        expr: process_resident_memory_bytes / 1024 / 1024 / 1024 > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Memory usage > 800MB"

      - alert: HighAPILatency
        expr: histogram_quantile(0.95, api_request_duration_seconds) > 3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API P95 latency > 3s"

      # ... 其他 7 个关键告警
```

**Grafana 配置**（轻量级）：

```bash
docker run -d \
  --name grafana \
  --restart unless-stopped \
  -p 3001:3000 \
  -v grafana-data:/var/lib/grafana \
  -e GF_SECURITY_ADMIN_PASSWORD=<password> \
  -e GF_USERS_ALLOW_SIGN_UP=false \
  grafana/grafana:latest
```

**预期成本**：
- Prometheus: 100-150MB
- Grafana: 80-100MB
- **总计: 180-250MB** ✅

---

#### Option B: 使用云服务日志收集（最小化内存）

如果不想部署 ELK，使用云服务：

```bash
# 选项 1: Coolify 内置日志（推荐）
# 在 Coolify 中启用日志收集，无需额外部署

# 选项 2: Datadog/New Relic（付费，但无内存占用）
# 应用端发送日志到外部服务

# 选项 3: Cloudflare Logpush（免费日志推送）
# 配置推送到 S3 或其他存储
```

---

### PHASE 3: 不推荐部署（4GB服务器）❌

#### ❌ 完全跳过 ELK 栈

**原因**：
- Elasticsearch 最小 1GB
- Logstash 256-512MB
- Kibana 256-512MB
- **总计: 1.5-2.5GB** （占总内存的 37-62%！）

**替代方案**：
1. **使用 Coolify 内置日志**（最简单）
2. **流式日志到外部服务**（如 CloudWatch、Datadog）
3. **本地文件日志 + 定期轮转**（最轻量）

---

## 📈 4GB 内存的性能目标调整

### 与完整部署对比

| 指标 | 完整部署（8GB+） | 4GB 轻量部署 | 差异 |
|------|-----------------|-------------|------|
| Cache Hit Rate | 70-80% | 50-70% | -10-20% |
| Average Latency | 40ms | 60ms | +50% |
| Max Throughput | 500 req/s | 300 req/s | -40% |
| 99th Percentile | <500ms | <1s | +100% |
| Memory Available | 2GB+ | 800MB | -60% |

**仍然可接受的性能**：
- 大多数用户不会感觉到差异
- 足以支持中等流量
- 成本大幅降低

---

## 🚀 4GB 生产环境最终方案

### 推荐配置

```
┌─────────────────────────────────────────────┐
│         最优方案：轻量级监控 + Redis        │
├─────────────────────────────────────────────┤
│ 优先级 | 组件 | 状态 | 内存 | 说明         │
├─────────────────────────────────────────────┤
│ P1 ✅  | 后端 + DB | 部署 | 1.1GB | 核心  │
│ P2 ⭐  | Redis | 部署 | 256MB | 缓存  │
│ P3 📊  | Prometheus | 部署 | 150MB | 监控  │
│ P4 📈  | Grafana | 部署 | 100MB | 仪表板 │
│ P5 ❌  | ELK | 跳过 | 0MB | 用云服务 │
├─────────────────────────────────────────────┤
│ 总计 | - | 3.2GB | - | ✅ 安全    │
└─────────────────────────────────────────────┘
```

### 部署步骤（Week 1-2）

**Week 1（3-4 天）**：
1. ✅ 优化 PostgreSQL 内存配置
2. ✅ 部署 Redis（256MB）
3. ✅ 集成 Redis 到应用
4. ✅ 应用数据库查询优化

**Week 2（2-3 天）**：
5. ✅ 部署 Prometheus（轻量级）
6. ✅ 部署 Grafana
7. ✅ 配置告警规则（10个关键告警）
8. ✅ 性能测试验证

---

## 💰 成本影响

### 与完整部署对比

| 方案 | 服务器内存 | 成本/月 | 性能 | 推荐 |
|------|-----------|--------|------|------|
| 完整（8GB） | 8GB | ¥800 | 最高 | ❌ 过度配置 |
| **轻量（4GB）** | **4GB** | **¥400** | **良好** | **✅ 推荐** |
| 最小（2GB） | 2GB | ¥200 | 差 | ⚠️ 经常崩溃 |

**成本节省**: **50%** ✅

---

## ⚡ 性能优化优先级（对于4GB）

### 最高性价比的优化

| 优化 | 内存成本 | 性能提升 | 优先级 |
|------|---------|---------|--------|
| Redis 缓存 | +256MB | 60%↓ latency | **P1** |
| 数据库优化 | -50MB | 10-100x 查询 | **P1** |
| Prometheus 监控 | +150MB | 可观测性 | **P2** |
| Grafana 仪表板 | +100MB | 可视化 | **P2** |
| 数据库索引 | 0MB | 5-20x 查询 | **P1** |

---

## ⚠️ 关键监控点（4GB）

在没有完整 ELK 的情况下监控什么：

```python
# 关键指标 - 在 /metrics 端点暴露这些
cache_hits_total          # Redis 命中数
cache_misses_total        # Redis 未命中数
db_query_duration_seconds # 数据库查询时间
api_request_duration      # API 响应时间
process_resident_memory_bytes  # 内存占用
postgresql_database_size  # 数据库大小

# 配置告警（简化版）
IF cache_hit_rate < 40% FOR 10min -> ALERT
IF api_latency_p95 > 2s FOR 5min -> ALERT
IF memory > 3.2GB FOR 5min -> ALERT
IF db_connections > 80 FOR 5min -> ALERT
```

---

## 总结

### ✅ 推荐方案（4GB 内存）

**部署以下组件**：
1. ✅ FastAPI + PostgreSQL（必需）
2. ✅ Redis 256MB（强烈推荐 - 60% 性能提升）
3. ✅ Prometheus 轻量版（监控）
4. ✅ Grafana（可视化）
5. ❌ 不部署 ELK（用云服务替代）

**预期结果**：
- 内存占用: 3.2GB（安全范围）
- 性能提升: 60%（通过缓存）
- 告警可用性: 10个关键告警
- 月成本: 节省 50%

### ❌ 不推荐

- 部署完整的 ELK（会导致 OOM）
- 超过 3 个监控组件
- 任何额外的消息队列

**结论**：4GB 内存完全可以运行，只需要**跳过 ELK，优先部署 Redis + Prometheus + Grafana**即可。

