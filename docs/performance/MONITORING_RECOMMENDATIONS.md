# 4GB Memory Optimization - Monitoring & Alert Recommendations

## Executive Summary

Based on performance benchmark results, here are 5 critical performance metrics to monitor in production:

---

## 1. Cache Performance Metrics (CRITICAL)

### Key Metric: Cache Hit Rate

**Target:** 50-70% (Current Benchmark: 62.3%)

**Prometheus Queries:**

```yaml
# Cache hit rate (5-minute window)
cache_hit_rate:
  sum(rate(cache_hits_total[5m])) / sum(rate(cache_requests_total[5m]))

# Cache latency percentiles
cache_latency_p50:
  histogram_quantile(0.50, rate(cache_lookup_duration_seconds_bucket[5m]))

cache_latency_p95:
  histogram_quantile(0.95, rate(cache_lookup_duration_seconds_bucket[5m]))

# Cache memory usage
cache_memory_usage_mb:
  redis_memory_used_bytes / (1024 * 1024)
```

**Alerts:**

```yaml
- alert: CacheHitRateLow
  expr: cache_hit_rate < 0.5
  for: 15m
  labels:
    severity: warning
  annotations:
    summary: "Cache hit rate below 50%"
    description: "Current hit rate: {{ $value | humanizePercentage }}"

- alert: CacheMemoryHigh
  expr: cache_memory_usage_mb > 230
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Cache memory usage above 230MB (90% of 256MB limit)"
    description: "Current usage: {{ $value }}MB"

- alert: CacheLatencyHigh
  expr: cache_latency_p95 > 0.5
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Cache P95 latency above 500ms"
    description: "Current P95: {{ $value }}s"
```

**Dashboard Panels:**

1. **Cache Hit Rate (Gauge)**
   - Target: 50-70%
   - Warning: <50%
   - Critical: <40%

2. **Cache Latency Distribution (Heatmap)**
   - P50, P95, P99 over time
   - Separate lines for HIT vs MISS

3. **Cache Memory Usage (Gauge)**
   - Current: 178.4 MB
   - Limit: 256 MB
   - Warning: >230 MB (90%)

4. **Cache Efficiency Score**
   - Formula: `(hit_rate * 100) - (avg_miss_latency / 10)`
   - Target: >50

---

## 2. Database Query Performance (CRITICAL)

### Key Metric: Query Latency P95

**Target:** <50ms P95 (Current Benchmark: 4.89ms for cursor pagination)

**Prometheus Queries:**

```yaml
# Query latency percentiles
db_query_p50:
  histogram_quantile(0.50, rate(db_query_duration_seconds_bucket[5m]))

db_query_p95:
  histogram_quantile(0.95, rate(db_query_duration_seconds_bucket[5m]))

db_query_p99:
  histogram_quantile(0.99, rate(db_query_duration_seconds_bucket[5m]))

# Slow query count
slow_queries_rate:
  rate(db_query_duration_seconds_bucket{le="0.1"}[5m])

# Query throughput
db_queries_per_second:
  rate(db_queries_total[1m])
```

**Alerts:**

```yaml
- alert: DatabaseQueryLatencyHigh
  expr: db_query_p95 > 0.1
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Database P95 query latency above 100ms"
    description: "Current P95: {{ $value }}s (Target: <50ms)"

- alert: SlowQueryRateHigh
  expr: rate(db_query_duration_seconds_count{le="1.0",gt="0.5"}[5m]) > 10
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High rate of slow queries (>500ms)"
    description: "{{ $value }} slow queries per second"

- alert: DatabaseConnectionPoolExhausted
  expr: db_connection_pool_active / db_connection_pool_max > 0.9
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Database connection pool near exhaustion"
    description: "{{ $value | humanizePercentage }} connections in use"
```

**Dashboard Panels:**

1. **Query Latency Heatmap**
   - P50, P95, P99 over 24 hours
   - Color-coded: Green (<50ms), Yellow (50-100ms), Red (>100ms)

2. **Cursor vs OFFSET Comparison**
   - Side-by-side latency comparison
   - Speedup factor visualization

3. **Query Types Breakdown**
   - By query type (SELECT, INSERT, UPDATE, DELETE)
   - By table (conversations, messages, documents)

4. **Slow Query Log**
   - Top 10 slowest queries in last hour
   - With EXPLAIN plan links

---

## 3. API Response Time (CRITICAL)

### Key Metric: API P95 Latency

**Target:** <300ms P95 (Current Benchmark: 187.56ms)

**Prometheus Queries:**

```yaml
# API latency percentiles
api_latency_p50:
  histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))

api_latency_p95:
  histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

api_latency_p99:
  histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# API success rate
api_success_rate:
  sum(rate(http_requests_total{status=~"2.."}[5m])) / sum(rate(http_requests_total[5m]))

# API throughput
api_requests_per_second:
  rate(http_requests_total[1m])

# API error rate by status code
api_errors_by_status:
  sum by (status) (rate(http_requests_total{status=~"[45].."}[5m]))
```

**Alerts:**

```yaml
- alert: APILatencyP95High
  expr: api_latency_p95 > 0.3
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "API P95 latency above 300ms"
    description: "Current P95: {{ $value }}s (Target: <300ms)"

- alert: APILatencyP50High
  expr: api_latency_p50 > 0.1
  for: 15m
  labels:
    severity: warning
  annotations:
    summary: "API P50 latency above 100ms"
    description: "Current P50: {{ $value }}s (Target: <100ms)"

- alert: APIErrorRateHigh
  expr: api_success_rate < 0.95
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "API success rate below 95%"
    description: "Current success rate: {{ $value | humanizePercentage }}"

- alert: APIThroughputAnomalyLow
  expr: rate(http_requests_total[5m]) < 0.5 * rate(http_requests_total[1h] offset 1h)
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "API throughput dropped by 50%"
    description: "Possible service degradation or traffic anomaly"
```

**Dashboard Panels:**

1. **API Latency Percentiles (Line Chart)**
   - P50, P95, P99 over 24 hours
   - Target lines at 100ms (P50) and 300ms (P95)

2. **API Success Rate (Gauge)**
   - Current: 99.0%
   - Target: >99%
   - Critical: <95%

3. **Endpoint Performance Table**
   - Top 10 slowest endpoints by P95
   - With throughput and error rate

4. **Latency Breakdown (Stacked Bar)**
   - Cache lookup time
   - Database query time
   - LLM inference time
   - Total response time

---

## 4. Concurrent Connection Capacity (IMPORTANT)

### Key Metric: Active Connections

**Target:** <375 (75% of 500 max) (Current Benchmark: 500 max, cliff at 450)

**Prometheus Queries:**

```yaml
# Active connections
active_connections:
  sum(http_active_connections)

# Connection utilization
connection_utilization:
  sum(http_active_connections) / 500

# Connection pool saturation
connection_pool_saturation:
  sum(db_connection_pool_active) / sum(db_connection_pool_max)

# Memory usage per connection
memory_per_connection:
  process_resident_memory_bytes / sum(http_active_connections)
```

**Alerts:**

```yaml
- alert: HighConcurrentConnections
  expr: active_connections > 375
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Active connections above 75% threshold (375)"
    description: "Current connections: {{ $value }} (Autoscale trigger)"

- alert: ConnectionPoolNearExhaustion
  expr: connection_pool_saturation > 0.8
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Connection pool 80% saturated"
    description: "{{ $value | humanizePercentage }} connections in use"

- alert: PerformanceCliffReached
  expr: active_connections > 450
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "CRITICAL: Performance cliff reached (450+ connections)"
    description: "Immediate action required - latency degradation expected"
```

**Dashboard Panels:**

1. **Active Connections (Line Chart)**
   - Current connections over time
   - Thresholds: 375 (autoscale), 450 (cliff), 500 (max)

2. **Connection vs Latency (Scatter Plot)**
   - X-axis: Connection count
   - Y-axis: Average latency
   - Visualize performance cliff

3. **Capacity Utilization (Gauge)**
   - 50% load: 250 connections (Optimal)
   - 75% load: 375 connections (Caution)
   - 90% load: 450 connections (Critical)

4. **Memory per Connection (Gauge)**
   - Average memory usage per active connection
   - Alert if >8 MB per connection

---

## 5. Memory & Resource Utilization (CRITICAL)

### Key Metric: System Memory Usage

**Target:** <3,500 MB (85% of 4,096 MB) (Current Benchmark: 3,235 MB @ 90% load)

**Prometheus Queries:**

```yaml
# Total memory usage
system_memory_usage_mb:
  process_resident_memory_bytes / (1024 * 1024)

# Memory utilization percentage
memory_utilization:
  process_resident_memory_bytes / (4096 * 1024 * 1024)

# Component memory breakdown
redis_memory_mb:
  redis_memory_used_bytes / (1024 * 1024)

postgres_memory_mb:
  pg_stat_bgwriter_buffers_alloc * 8 / 1024  # Estimate

app_memory_mb:
  process_resident_memory_bytes / (1024 * 1024) - redis_memory_mb - postgres_memory_mb

# Memory growth rate
memory_growth_rate:
  rate(process_resident_memory_bytes[1h])

# CPU usage
cpu_usage_percent:
  rate(process_cpu_seconds_total[5m]) * 100
```

**Alerts:**

```yaml
- alert: MemoryUsageHigh
  expr: system_memory_usage_mb > 3500
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Memory usage above 3,500 MB (85% of 4GB limit)"
    description: "Current usage: {{ $value }}MB"

- alert: MemoryUsageCritical
  expr: system_memory_usage_mb > 3840
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "CRITICAL: Memory usage above 3,840 MB (94% of 4GB limit)"
    description: "OOM killer may trigger - immediate action required"

- alert: MemoryLeakDetected
  expr: rate(process_resident_memory_bytes[1h]) > 10485760
  for: 30m
  labels:
    severity: warning
  annotations:
    summary: "Potential memory leak detected"
    description: "Memory growing at {{ $value | humanize }}B/s for 30 minutes"

- alert: CPUUsageHigh
  expr: cpu_usage_percent > 80
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "CPU usage above 80%"
    description: "Current CPU: {{ $value }}%"
```

**Dashboard Panels:**

1. **Memory Budget Allocation (Stacked Bar)**
   - Redis: 178 MB
   - PostgreSQL: 800 MB
   - Prometheus: 58 MB
   - FastAPI: 600 MB
   - Nginx: 80 MB
   - Reserve: 640 MB

2. **Memory Usage Over Time (Area Chart)**
   - Baseline: 1,716 MB
   - 90% load: 3,235 MB
   - Limit: 4,096 MB

3. **Memory Utilization Gauge**
   - Green: <70% (2,867 MB)
   - Yellow: 70-85% (2,867-3,500 MB)
   - Red: >85% (3,500+ MB)

4. **CPU vs Memory Correlation (Dual-Axis)**
   - Left axis: Memory usage (MB)
   - Right axis: CPU usage (%)

---

## Recommended Alert Rules (Top 10 Critical)

### Priority 1: Service Availability

```yaml
# 1. Service Down
- alert: ServiceDown
  expr: up{job="fastapi"} == 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "FastAPI service is down"

# 2. High Error Rate
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "5xx error rate above 5%"
```

### Priority 2: Performance Degradation

```yaml
# 3. API Latency Critical
- alert: APILatencyCritical
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
  for: 10m
  labels:
    severity: critical
  annotations:
    summary: "API P95 latency above 500ms"

# 4. Database Latency Critical
- alert: DatabaseLatencyCritical
  expr: histogram_quantile(0.95, rate(db_query_duration_seconds_bucket[5m])) > 0.2
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Database P95 latency above 200ms"
```

### Priority 3: Resource Exhaustion

```yaml
# 5. Memory Critical
- alert: MemoryCritical
  expr: process_resident_memory_bytes / (4096 * 1024 * 1024) > 0.94
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "Memory usage above 94%"

# 6. Connection Pool Exhausted
- alert: ConnectionPoolExhausted
  expr: db_connection_pool_active / db_connection_pool_max > 0.95
  for: 3m
  labels:
    severity: critical
  annotations:
    summary: "Database connection pool exhausted"
```

### Priority 4: Cache Performance

```yaml
# 7. Cache Hit Rate Low
- alert: CacheHitRateLow
  expr: sum(rate(cache_hits_total[5m])) / sum(rate(cache_requests_total[5m])) < 0.4
  for: 15m
  labels:
    severity: warning
  annotations:
    summary: "Cache hit rate below 40%"

# 8. Cache Memory High
- alert: CacheMemoryHigh
  expr: redis_memory_used_bytes / (256 * 1024 * 1024) > 0.9
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Redis memory above 90% of 256MB limit"
```

### Priority 5: Capacity Planning

```yaml
# 9. High Concurrent Load
- alert: HighConcurrentLoad
  expr: sum(http_active_connections) > 375
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Active connections above 75% threshold"

# 10. Performance Cliff Warning
- alert: PerformanceCliffWarning
  expr: sum(http_active_connections) > 450
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "Performance cliff reached - immediate action required"
```

---

## Grafana Dashboard Layout

### Main Performance Dashboard

**Row 1: Overview**
- Service Status (up/down)
- Active Connections Gauge
- Memory Utilization Gauge
- CPU Utilization Gauge

**Row 2: API Performance**
- API Latency Percentiles (P50, P95, P99)
- API Throughput (req/sec)
- API Success Rate
- Error Rate by Status Code

**Row 3: Cache Performance**
- Cache Hit Rate Gauge
- Cache Latency Distribution
- Cache Memory Usage
- Cache Efficiency Score

**Row 4: Database Performance**
- Query Latency Percentiles
- Slow Query Count
- Connection Pool Status
- Query Throughput

**Row 5: Resource Utilization**
- Memory Budget Breakdown
- Memory Usage Over Time
- CPU Usage
- Connection Count vs Latency

**Row 6: Capacity Planning**
- Load Level Indicators (50%, 75%, 90%)
- Performance Degradation Chart
- Memory Headroom
- Autoscaling Recommendations

---

## Monitoring Best Practices

### 1. Scrape Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 30s
  evaluation_interval: 30s
  scrape_timeout: 10s

scrape_configs:
  - job_name: 'fastapi'
    static_configs:
      - targets: ['localhost:8000']
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:6379']
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:5432']
    scrape_interval: 60s  # Less frequent for DB
```

### 2. Retention Policy

```yaml
# Prometheus retention
storage:
  tsdb:
    path: /prometheus
    retention:
      time: 7d
      size: 500MB
```

### 3. Alert Routing

```yaml
# alertmanager.yml
route:
  receiver: 'default'
  group_by: ['severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h

  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
      continue: true

    - match:
        severity: warning
      receiver: 'slack'
```

### 4. Log Aggregation

- Enable structured logging (JSON format)
- Collect logs from all services (FastAPI, Redis, PostgreSQL, Nginx)
- Set log retention to 7 days (matching Prometheus)
- Index logs by severity, service, and timestamp

### 5. Distributed Tracing

- Implement OpenTelemetry for end-to-end traces
- Track request flow: API → Cache → Database → LLM
- Identify bottlenecks in multi-service calls
- Correlate traces with metrics and logs

---

## Appendix: Metric Exporters

### FastAPI Application Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# Cache metrics
cache_requests_total = Counter(
    'cache_requests_total',
    'Total cache requests',
    ['result']  # hit, miss
)

cache_lookup_duration_seconds = Histogram(
    'cache_lookup_duration_seconds',
    'Cache lookup latency'
)

# Database metrics
db_queries_total = Counter(
    'db_queries_total',
    'Total database queries',
    ['query_type', 'table']
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query latency',
    ['query_type']
)

# Connection metrics
http_active_connections = Gauge(
    'http_active_connections',
    'Active HTTP connections'
)

db_connection_pool_active = Gauge(
    'db_connection_pool_active',
    'Active database connections'
)
```

---

**Monitoring Configuration Version:** 1.0.0
**Last Updated:** 2024-11-22
**Optimized for:** 4GB Memory Environment

**End of Monitoring Recommendations**
