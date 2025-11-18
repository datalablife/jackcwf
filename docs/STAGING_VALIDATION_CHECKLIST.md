# Staging Validation Checklist: Phase 1 AI Optimization

**Objective**: Validate that Phase 1 delivers 53% latency improvement (850ms → 400ms average) with 40-60% cache hit rate.

**Timeline**: 2-3 hours for complete validation
**Date**: [To be completed]
**Validated By**: [Your name]

---

## Pre-Deployment Setup (30 minutes)

### Database Preparation
- [ ] PostgreSQL 15+ running and accessible
- [ ] Lantern extension installed: `SELECT extname FROM pg_extension WHERE extname = 'lantern';`
- [ ] Database migration applied: Check for `llm_response_cache` table
- [ ] Verify table structure: `\d llm_response_cache` in psql
- [ ] Verify indexes: Check for Lantern HNSW index `idx_cache_embedding`
- [ ] Verify views: Check for `cache_analytics` view

### Application Setup
- [ ] Environment variables configured (.env)
  - [ ] DATABASE_URL set correctly
  - [ ] OPENAI_API_KEY configured
  - [ ] ANTHROPIC_API_KEY configured
  - [ ] ENABLE_MONITORING=true
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] asyncpg package installed: `pip show asyncpg`
- [ ] prometheus-client installed: `pip show prometheus-client`
- [ ] locust installed: `pip show locust`

### Monitoring Setup
- [ ] Prometheus installed and configured
- [ ] prometheus.yml created with correct scrape config
  - [ ] Target: localhost:8000
  - [ ] Metrics path: /metrics
  - [ ] Scrape interval: 10s
- [ ] Grafana installed and running
- [ ] Grafana data source configured (Prometheus)
- [ ] Grafana dashboard imported from `docs/monitoring/cache_dashboard.json`

---

## Deployment Steps (15 minutes)

### Step 1: Start Services
```bash
# Terminal 1: FastAPI Application
cd /path/to/project
python -m uvicorn src.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --log-level info
```
- [ ] App started successfully
- [ ] See "✅ Semantic cache initialized successfully" in logs
- [ ] See "✅ Cache stats updater started" in logs
- [ ] No errors about database connection

```bash
# Terminal 2: Prometheus
prometheus --config.file=prometheus.yml
```
- [ ] Prometheus started on http://localhost:9090
- [ ] Status page accessible

```bash
# Terminal 3: Grafana (if using Docker)
docker run -d \
  --name grafana \
  -p 3000:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  grafana/grafana
```
- [ ] Grafana running on http://localhost:3000

### Step 2: Verify Endpoints
```bash
# Check metrics endpoint
curl http://localhost:8000/metrics | head -30
```
- [ ] /metrics endpoint returns 200
- [ ] Prometheus format text output
- [ ] Sees `llm_cache_hits_total` metric
- [ ] Sees `llm_cache_misses_total` metric

```bash
# Check health endpoint
curl http://localhost:8000/health
```
- [ ] Health check returns 200
- [ ] Shows "healthy" status

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets
```
- [ ] Sees FastAPI target in ACTIVE state
- [ ] Scrape URL shows `/metrics`
- [ ] Last scrape time is recent (< 1 minute)

### Step 3: Verify Grafana Dashboard
- [ ] Log into Grafana: http://localhost:3000 (admin/admin)
- [ ] Navigate to "Cache Monitoring" dashboard
- [ ] See dashboard loading without errors
- [ ] Panels exist but may show "No data" initially (normal)

---

## Load Testing Phase (45 minutes)

### Prepare Test Data
```bash
# Option 1: Create test queries in database directly
psql $DATABASE_URL << 'EOF'
INSERT INTO llm_response_cache
  (model_name, query_text, query_embedding, response_text, created_at, expires_at, hit_count)
VALUES
  ('claude-3-5-sonnet-20241022', 'What is RAG?', '{0,0,0...}', 'RAG is...', NOW(), NOW() + INTERVAL '24 hours', 0);
EOF
```

### Run Load Test
```bash
# Install Locust if needed
pip install locust

# Start Locust
locust -f tests/load_test_cache.py \
  --host=http://localhost:8000 \
  --users=50 \
  --spawn-rate=5 \
  --run-time=10m
```

- [ ] Locust web interface opens: http://localhost:8089
- [ ] Shows connection to FastAPI
- [ ] Requests are being sent
- [ ] Error rate is 0% (or < 1%)
- [ ] Response times displayed in real-time

### Monitor During Load Test
In separate terminal, watch Prometheus:
```bash
# Query cache hit rate
curl 'http://localhost:9090/api/v1/query?query=llm_cache_hit_rate'

# Query cache size
curl 'http://localhost:9090/api/v1/query?query=llm_cache_size_entries'
```

- [ ] Metrics updating in real-time
- [ ] Cache size increasing with queries
- [ ] Hit rate gradually increasing

### Watch Grafana Dashboard
- [ ] Dashboard panels updating in real-time
- [ ] "Cache Hit Rate" gauge changing
- [ ] "Query Latency Comparison" showing two lines
- [ ] "Cache Hits vs Misses" pie chart updating

---

## Performance Validation (30 minutes)

### After Load Test Completes, Review Results

#### Locust Report (from web interface or terminal)
Check the final statistics displayed:

```
CACHE PERFORMANCE TEST RESULTS
================================================================================
Total Queries: [should be 500+]
Cache Hits: [should be 200-300]
Cache Misses: [should be 200-300]
Hit Rate: [should be 40-60%]
Target Hit Rate: 40-60%
Target Status: ✅ PASS [or ❌ FAIL]

CACHE HIT LATENCIES (ms):
  avg: [should be ~300ms]
  p95: [should be < 320ms]
  Target: 300ms
  Status: ✅ PASS [or ❌ FAIL]

CACHE MISS LATENCIES (ms):
  avg: [should be ~850ms]
  p95: [should be < 880ms]
  Target: 850ms
  Status: ✅ PASS [or ❌ FAIL]

LATENCY IMPROVEMENT:
  Improvement: [should be 50-70%]
  Target: 53% improvement
  Status: ✅ PASS [or ❌ FAIL]
================================================================================
```

### Validation Checklist - Performance Metrics

**Cache Hit Rate**
- [ ] Hit rate between 40% and 60%
  - If < 40%: Check if cache is initializing properly
  - If > 60%: Normal variation, verify database growth
- [ ] Total queries >= 500
- [ ] Hit count and miss count both > 0

**Cache Hit Latency**
- [ ] Average hit latency < 350ms
- [ ] p95 hit latency < 320ms
- [ ] Minimum hit latency > 250ms (sanity check)

**Cache Miss Latency**
- [ ] Average miss latency < 900ms
- [ ] p95 miss latency < 880ms
- [ ] Minimum miss latency > 600ms (sanity check)

**Overall Improvement**
- [ ] Improvement >= 50%
  - Expected: 53% (±5%)
  - Formula: ((miss_avg - hit_avg) / miss_avg) * 100

### Validation Checklist - Database Metrics

```bash
# Check cache statistics
psql $DATABASE_URL -c \
  "SELECT * FROM cache_analytics;"
```

- [ ] `total_entries` > 50 (at least 50 unique queries cached)
- [ ] `total_hits` >= 100 (at least 100 cache hits)
- [ ] `hit_percentage` >= 40%
- [ ] `table_size` < 100MB (reasonable for test load)

### Validation Checklist - Prometheus Metrics

Query each metric in Prometheus (http://localhost:9090/graph):

```prometheus
# Counter metrics
rate(llm_cache_hits_total[5m])           # Should show increasing counter
rate(llm_cache_misses_total[5m])         # Should show increasing counter

# Gauge metrics
llm_cache_size_entries                   # Should show current count
llm_cache_hit_rate                       # Should show hit rate percentage

# Histogram metrics (percentiles)
histogram_quantile(0.95, llm_cache_hit_latency_ms)    # Should be ~310ms
histogram_quantile(0.95, llm_cache_miss_latency_ms)   # Should be ~870ms
```

- [ ] All metrics are present and updating
- [ ] No "No data" or null values
- [ ] Metric values are reasonable
- [ ] Timestamps are recent

### Validation Checklist - Grafana Dashboards

Open each dashboard panel and verify:

1. **Cache Hit Rate (Gauge)**
   - [ ] Showing value between 40-60%
   - [ ] Green color (healthy)

2. **Cache Size (Stat)**
   - [ ] Shows number > 50
   - [ ] No errors

3. **Cache Table Size (Stat)**
   - [ ] Shows size in bytes
   - [ ] Less than 100MB for test

4. **Cache Hits vs Misses (Pie Chart)**
   - [ ] Shows both hit and miss portions
   - [ ] Hit portion is 40-60% of total

5. **Query Latency Comparison (Time Series)**
   - [ ] Shows two lines: "Hit" and "Miss"
   - [ ] Hit line consistently below miss line
   - [ ] Hit line around 300ms
   - [ ] Miss line around 850ms

6. **Hit/Miss Latency Distributions (Histograms)**
   - [ ] Both showing bucket distributions
   - [ ] Hit distribution concentrated around 300ms
   - [ ] Miss distribution concentrated around 850ms

---

## Error Handling

### Common Issues & Solutions

#### Issue: "Cache service not initialized"
**Check**:
- [ ] Database connection string correct
- [ ] PostgreSQL running and accessible
- [ ] Lantern extension installed
- [ ] Migration applied
- [ ] Check logs for specific error message

**Fix**:
```bash
# Verify database
psql $DATABASE_URL -c "SELECT version();"

# Check Lantern
psql $DATABASE_URL -c "SELECT extname FROM pg_extension WHERE extname = 'lantern';"

# Check tables
psql $DATABASE_URL -c "\dt llm_response_cache;"
```

#### Issue: "No metrics showing in Prometheus"
**Check**:
- [ ] /metrics endpoint accessible: `curl http://localhost:8000/metrics`
- [ ] Prometheus target shows ACTIVE
- [ ] Check target last scrape status
- [ ] No scrape errors in Prometheus logs

**Fix**:
```bash
# Manually check endpoint format
curl http://localhost:8000/metrics | grep llm_cache

# Verify Prometheus config
cat prometheus.yml | grep -A5 "langchain-cache"
```

#### Issue: "Cache hits showing 0"
**Check**:
- [ ] Load test is running (check Locust status)
- [ ] Queries are being sent to correct endpoint (/api/conversations/v1/chat)
- [ ] enable_cache=true in requests
- [ ] Database growing (check table size)

**Fix**:
- [ ] Review FastAPI logs for request processing
- [ ] Check that cache_service.initialize() succeeded
- [ ] Verify query embedding is being calculated
- [ ] Run simple test query manually:
```bash
curl -X POST http://localhost:8000/api/conversations/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is RAG?", "enable_cache": true}'
```

#### Issue: "High error rate in Locust"
**Check**:
- [ ] Application logs for 500 errors
- [ ] Database connection issues
- [ ] LLM API key validity
- [ ] OpenAI API rate limiting

**Fix**:
- [ ] Check FastAPI logs: `tail -f app.log`
- [ ] Reduce Locust user count and retry
- [ ] Verify API keys are correct
- [ ] Check OpenAI/Anthropic account status

---

## Final Validation Summary

After completing all checks above, fill in this summary:

### Deployment Status
- [ ] Pre-deployment setup: ✅ Complete
- [ ] Services running: ✅ Complete
- [ ] Endpoints verified: ✅ Complete
- [ ] Load test completed: ✅ Complete

### Performance Results
- [ ] Cache hit rate: **[___]%** (Target: 40-60%)
- [ ] Hit latency p95: **[___]ms** (Target: <320ms)
- [ ] Miss latency p95: **[___]ms** (Target: <880ms)
- [ ] Latency improvement: **[___]%** (Target: >50%)

### Monitoring Status
- [ ] Prometheus collecting metrics: ✅ / ❌
- [ ] Grafana dashboards visible: ✅ / ❌
- [ ] All metrics present: ✅ / ❌
- [ ] No data collection errors: ✅ / ❌

### Pass/Fail Decision

```
┌─────────────────────────────────────────┐
│  Phase 1 Validation Result              │
├─────────────────────────────────────────┤
│                                         │
│  Overall Status: [ PASS ] [ FAIL ]      │
│                                         │
│  Validated By: ________________________  │
│  Date: _______________________________   │
│  Notes: _______________________________  │
│         _______________________________  │
│                                         │
│  Next Step: Deploy to Production?       │
│             [ Yes ] [ No - Fix Issues ] │
│                                         │
└─────────────────────────────────────────┘
```

---

## Post-Validation Steps

### If PASS ✅
1. [ ] Document results
2. [ ] Prepare production deployment plan
3. [ ] Schedule production rollout
4. [ ] Proceed to Phase 2 planning

### If FAIL ❌
1. [ ] Document failures
2. [ ] Identify root causes
3. [ ] Create fix plan
4. [ ] Re-run validation after fixes
5. [ ] Only deploy to production after PASS

---

## Sign-Off

**Validation Date**: ___________________
**Validated By**: ___________________
**Sign-Off**: ___________________
**Status**: [ PASS ] [ FAIL ]

---

**Document Version**: 1.0
**Last Updated**: 2025-11-18
