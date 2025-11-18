# Semantic Cache Monitoring Setup Guide

This guide covers the complete Prometheus and Grafana monitoring setup for the LangChain semantic cache system.

## Overview

The monitoring system provides real-time insights into cache performance:
- **Cache Hit Rate**: Percentage of queries served from cache
- **Latency Metrics**: Query latency breakdown by cache hit/miss
- **Cache Statistics**: Cache size, entry count, and table size
- **Semantic Similarity**: Cache distance metrics for hit quality

## Architecture

```
┌─────────────────┐
│  FastAPI App    │
│  - Metrics      │
│  - /metrics     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Prometheus    │
│   (Scraper)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Grafana      │
│  (Dashboard)    │
└─────────────────┘
```

## Component 1: Prometheus Metrics

### Location
- **File**: `src/infrastructure/cache_metrics.py`
- **Endpoint**: `GET /metrics`

### Available Metrics

#### Cache Hit/Miss Counters
```prometheus
llm_cache_hits_total{model="claude-3-5-sonnet-20241022", cache_type="semantic"}
llm_cache_misses_total{model="claude-3-5-sonnet-20241022", cache_type="semantic"}
```

#### Latency Histograms (in milliseconds)
```prometheus
llm_cache_hit_latency_ms{model="claude-3-5-sonnet-20241022"}
llm_cache_miss_latency_ms{model="claude-3-5-sonnet-20241022"}
llm_query_latency_ms{model="claude-3-5-sonnet-20241022", cached="true|false"}
```

#### Component Latencies
```prometheus
llm_embedding_latency_ms{model="claude-3-5-sonnet-20241022"}      # Embedding generation
llm_vector_search_latency_ms{model="claude-3-5-sonnet-20241022"} # Vector similarity search
llm_generation_latency_ms{model="claude-3-5-sonnet-20241022"}    # LLM response generation
```

#### Cache Gauges
```prometheus
llm_cache_size_entries{model="claude-3-5-sonnet-20241022"}        # Number of cached entries
llm_cache_hit_rate{model="claude-3-5-sonnet-20241022"}            # Hit rate (0-100)
llm_cache_table_size_bytes{model="claude-3-5-sonnet-20241022"}    # Table size in bytes
```

#### Semantic Similarity
```prometheus
llm_cache_distance{model="claude-3-5-sonnet-20241022"}            # Semantic similarity distance
llm_cached_responses_served{model="claude-3-5-sonnet-20241022"}   # Total responses from cache
```

### Recording Metrics

Metrics are automatically recorded in:
- **Cache Hits**: `src/services/cached_rag.py:129-133`
- **Cache Misses**: `src/services/cached_rag.py:183-189`
- **Stats Updates**: `src/infrastructure/cache_stats_updater.py` (30s interval)

## Component 2: Cache Stats Updater

### Location
- **File**: `src/infrastructure/cache_stats_updater.py`
- **Class**: `CacheStatsUpdater`

### Functionality
Periodically updates cache statistics from the database:
- Query frequency: Every 30 seconds (configurable)
- Updates gauge metrics with current cache state
- Runs in background during application lifespan

### Configuration
```python
# In src/main.py lifespan
await start_cache_stats_updater(interval_seconds=30)  # Update every 30 seconds
```

## Component 3: Grafana Dashboard

### Location
- **File**: `docs/monitoring/cache_dashboard.json`

### Setup Instructions

#### Step 1: Install Prometheus

```bash
# Using Docker
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v /path/to/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

# Or install locally
# Visit: https://prometheus.io/download/
```

#### Step 2: Configure Prometheus

Create `prometheus.yml`:
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'langchain-cache'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

#### Step 3: Install Grafana

```bash
# Using Docker
docker run -d \
  --name grafana \
  -p 3000:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  grafana/grafana

# Or install locally
# Visit: https://grafana.com/grafana/download
```

#### Step 4: Add Prometheus Data Source

1. Open Grafana: http://localhost:3000
2. Go to Configuration > Data Sources
3. Add new Prometheus data source:
   - Name: `Prometheus`
   - URL: `http://localhost:9090`
   - Click "Save & Test"

#### Step 5: Import Dashboard

1. In Grafana, go to: + > Import
2. Upload JSON file: `docs/monitoring/cache_dashboard.json`
3. Select Prometheus as data source
4. Click "Import"

## Performance Targets

### Cache Hit Rate
- **Target**: 40-60%
- **Status Check**: `(hits / (hits + misses)) * 100`

### Cache Hit Latency
- **Target**: ~300ms (p95)
- **Includes**: Embedding + search + cache lookup (no LLM generation)

### Cache Miss Latency
- **Target**: ~850ms (p95)
- **Includes**: Embedding + search + LLM generation + caching

### Overall Latency Improvement
- **Target**: 53% improvement
- **Formula**: `((miss_latency - hit_latency) / miss_latency) * 100`
- **Expected**: 850ms → 400ms average

### Semantic Similarity (Cache Distance)
- **Target**: < 0.05 L2 distance for cache hits
- **Meaning**: 95%+ semantic similarity between cached and current query

## Load Testing

### Using Locust

#### Step 1: Install Locust
```bash
pip install locust
```

#### Step 2: Run Load Test
```bash
# Start FastAPI application
python -m uvicorn src.main:app --reload

# In another terminal, run load test
locust -f tests/load_test_cache.py \
  --host=http://localhost:8000 \
  -u 50 \
  -r 5 \
  -t 10m
```

#### Step 3: Monitor Results
- Open Locust UI: http://localhost:8089
- Watch real-time request stats
- Check FastAPI metrics endpoint: http://localhost:8000/metrics
- Monitor Grafana dashboard: http://localhost:3000

### Expected Results

After running load test:
```
CACHE PERFORMANCE TEST RESULTS
================================================================================
Total Queries: 500
Cache Hits: 250
Cache Misses: 250
Hit Rate: 50.0%
Target Hit Rate: 40-60%
Target Status: ✅ PASS

CACHE HIT LATENCIES (ms):
  min: 280.5ms
  max: 320.1ms
  avg: 298.3ms
  median: 295.0ms
  p95: 310.5ms
  p99: 318.2ms
  Target: 300ms
  Status: ✅ PASS

CACHE MISS LATENCIES (ms):
  min: 800.2ms
  max: 920.5ms
  avg: 852.7ms
  median: 848.0ms
  p95: 895.3ms
  p99: 912.1ms
  Target: 850ms
  Status: ✅ PASS

LATENCY IMPROVEMENT:
  Improvement: 65.0% (852.7ms → 298.3ms)
  Target: 53% improvement
  Status: ✅ PASS
================================================================================
```

## Monitoring Checklist

### Daily Monitoring
- [ ] Check cache hit rate (target: 40-60%)
- [ ] Review p95 latencies (hit: <300ms, miss: <850ms)
- [ ] Verify cache table size growth
- [ ] Check for any errors in application logs

### Weekly Review
- [ ] Analyze hit rate trends
- [ ] Review cache efficiency metrics
- [ ] Check semantic similarity distribution
- [ ] Verify cost savings from cache hits

### Monthly Analysis
- [ ] Full performance report
- [ ] Compare against baseline (no cache)
- [ ] Identify optimization opportunities
- [ ] Plan cache TTL adjustments if needed

## Troubleshooting

### Metrics Not Showing
1. Verify `/metrics` endpoint is accessible: `curl http://localhost:8000/metrics`
2. Check Prometheus scrape targets: http://localhost:9090/targets
3. Verify data source in Grafana
4. Check application logs for errors

### Low Cache Hit Rate
1. Check if cache is being properly initialized
2. Verify database connectivity
3. Check cache TTL setting (24 hours default)
4. Review query patterns - may need more test data

### High Latency for Cache Hits
1. Check semantic cache lookup performance
2. Verify database indexes are created
3. Check network latency to database
4. Review Lantern HNSW index configuration

### Dashboard Not Updating
1. Check Prometheus is scraping metrics
2. Verify scrape interval (default: 10s)
3. Check Grafana refresh rate (default: 30s)
4. Restart Grafana if needed

## Advanced Configuration

### Custom Scrape Interval
```yaml
# In prometheus.yml
scrape_configs:
  - job_name: 'langchain-cache'
    scrape_interval: 5s  # More frequent updates
    metrics_path: '/metrics'
```

### Custom Cache Stats Update Interval
```python
# In src/main.py
await start_cache_stats_updater(interval_seconds=15)  # Update every 15s
```

### Custom Prometheus Retention
```yaml
# In prometheus.yml
global:
  external_labels:
    replica: '1'

# Command line
prometheus --storage.tsdb.retention.time=30d
```

## Integration with Alerting

### Prometheus Alert Rules
Create `alerts.yml`:
```yaml
groups:
  - name: cache
    rules:
      - alert: LowCacheHitRate
        expr: llm_cache_hit_rate < 30
        for: 5m
        annotations:
          summary: "Cache hit rate below 30%"

      - alert: HighMissLatency
        expr: histogram_quantile(0.95, llm_cache_miss_latency_ms) > 1000
        for: 5m
        annotations:
          summary: "Cache miss latency above 1 second"
```

### Grafana Alerting
1. Edit dashboard panels
2. Add alert rules
3. Configure notification channels
4. Set alert conditions

## Performance Optimization Tips

1. **Increase Cache TTL**: Change from 24h to 48h for more hit opportunities
2. **Query Normalization**: Normalize similar queries before embedding
3. **Batch Processing**: Group similar queries for better cache utilization
4. **Model Selection**: Use smaller embedding models for faster similarity search
5. **Index Optimization**: Fine-tune Lantern HNSW parameters

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Locust Documentation](https://locust.io/docs/)
- [prometheus-client Python](https://github.com/prometheus/client_python)
