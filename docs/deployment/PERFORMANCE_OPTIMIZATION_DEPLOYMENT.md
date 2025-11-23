# Performance Optimization Deployment Guide

## Overview

This guide covers deploying Redis cache and database optimizations to improve performance by 60-80% across key metrics.

## Performance Targets

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Cache Hit Latency | 50-200ms | 5ms | 95% faster |
| API p95 Response | 500ms | 150ms | 70% faster |
| DB Query Count | N+1 queries | 2 queries | 50-100x fewer |
| Memory Usage | High | Optimized | -40% |

---

## Prerequisites

- Docker and Docker Compose installed
- PostgreSQL 15+ with pgvector
- Python 3.12+
- 512MB+ RAM for Redis

---

## Step 1: Deploy Redis with Docker Compose

### 1.1 Start Redis Container

```bash
# Navigate to project root
cd /mnt/d/工作区/云开发/working

# Start Redis service
docker-compose up -d redis

# Verify Redis is running
docker-compose ps redis
docker-compose logs redis
```

### 1.2 Test Redis Connection

```bash
# Connect to Redis CLI
docker-compose exec redis redis-cli

# Test connection
> PING
PONG

> INFO server
# Should show Redis 7.2.x

> EXIT
```

### 1.3 Verify Redis Configuration

```bash
# Check Redis configuration
docker-compose exec redis redis-cli CONFIG GET maxmemory
# Should show: 512mb

docker-compose exec redis redis-cli CONFIG GET maxmemory-policy
# Should show: allkeys-lru
```

---

## Step 2: Apply Database Optimizations

### 2.1 Run Performance Migration

```bash
# Apply database indexes
python -m src.db.migrations.performance_optimization apply

# Expected output:
# - 10+ new indexes created
# - Tables analyzed
# - Migration recorded
```

### 2.2 Verify Indexes Created

```bash
# Check created indexes
python -m src.db.migrations.performance_optimization analyze

# Expected output:
# - List of all indexes
# - Table sizes
# - Index usage statistics
```

### 2.3 Monitor Index Usage

After deploying, monitor index usage:

```sql
-- Connect to PostgreSQL
psql -h 47.79.87.199 -U jackcwf888 -d postgres

-- Check index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as scans,
    idx_tup_read as tuples_read
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- Look for indexes with 0 scans (may need to be removed)
```

---

## Step 3: Update Environment Variables

### 3.1 Add Redis Configuration to .env

```bash
# Edit .env file
nano .env

# Add these lines:
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_TIMEOUT=5

# Cache Configuration
CACHE_ENABLED=true
CACHE_TTL_SECONDS=3600
CACHE_CONVERSATION_TTL=7200
CACHE_DOCUMENT_TTL=86400
CACHE_USER_DATA_TTL=1800

# Database Pool Configuration
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

---

## Step 4: Update FastAPI Application

### 4.1 Integrate Redis in main.py

Edit `/mnt/d/工作区/云开发/working/src/main.py`:

```python
from src.integrations.fastapi_redis_integration import (
    lifespan_with_cache,
    setup_performance_optimizations
)

# Replace existing lifespan with cache-enabled version
app = FastAPI(
    title="AI Data Analyzer",
    version="0.1.0",
    lifespan=lifespan_with_cache  # Use cache-enabled lifespan
)

# Apply performance optimizations
setup_performance_optimizations(app)
```

### 4.2 Update Dependencies

```bash
# Ensure redis is installed
uv pip install redis

# Or with poetry:
poetry add redis
```

---

## Step 5: Deploy and Test

### 5.1 Restart Application

```bash
# Stop existing containers
docker-compose down

# Rebuild and start all services
docker-compose up -d --build

# Check logs
docker-compose logs -f backend
```

### 5.2 Verify Cache is Working

```bash
# Check application logs for cache initialization
docker-compose logs backend | grep -i "redis"

# Expected output:
# Redis cache initialized: localhost:6379 (db=0, pool_size=50)
# Cache warmup complete: {'users': 0, 'conversations': 100}
```

### 5.3 Test Cache Performance

```bash
# Run performance tests
docker-compose exec backend pytest tests/test_performance_optimization.py -v

# Expected output:
# - Cache write latency: <5ms
# - Cache read latency: <5ms
# - Cache hit rate: >90%
# - All tests PASSED
```

---

## Step 6: Monitor Performance

### 6.1 Start Prometheus and Grafana (Optional)

```bash
# Start monitoring services
docker-compose up -d prometheus grafana

# Access Grafana
open http://localhost:3001
# Login: admin / admin (change password)
```

### 6.2 Check Cache Metrics

Access cache metrics endpoint:

```bash
curl http://localhost:8000/metrics | grep cache

# Expected metrics:
# cache_hits_total{cache_type="redis"} 1234
# cache_misses_total{cache_type="redis"} 56
# cache_hit_rate 0.956
```

### 6.3 Monitor API Response Times

```bash
# Check response time headers
curl -I http://localhost:8000/api/conversations

# Should include:
# X-Response-Time: 45.23ms
```

---

## Step 7: Verify Optimizations

### 7.1 Performance Checklist

- [ ] Redis container is running
- [ ] Database indexes created
- [ ] Cache initialization in logs
- [ ] Cache hit rate >60%
- [ ] API response time <200ms p95
- [ ] No N+1 queries in logs
- [ ] Prometheus metrics available

### 7.2 Run Full Test Suite

```bash
# Run all tests including performance
docker-compose exec backend pytest tests/ -v --cov=src

# Expected:
# - All tests pass
# - Coverage >85%
# - Performance tests show improvements
```

---

## Troubleshooting

### Redis Connection Issues

```bash
# Check Redis is accessible
docker-compose exec backend ping redis -c 3

# Check Redis logs
docker-compose logs redis --tail=50

# Test Redis from Python
docker-compose exec backend python -c "
import redis
r = redis.Redis(host='redis', port=6379, db=0)
print(r.ping())
"
```

### Cache Not Working

```bash
# Verify environment variables
docker-compose exec backend env | grep REDIS

# Check application logs
docker-compose logs backend | grep -i "cache"

# Test cache manually
docker-compose exec backend python -c "
from src.infrastructure.redis_cache import RedisCache
import asyncio

async def test():
    cache = RedisCache(host='redis', port=6379)
    await cache.initialize()
    health = await cache.health_check()
    print(f'Cache status: {health}')
    await cache.close()

asyncio.run(test())
"
```

### Slow Queries

```bash
# Enable slow query logging
docker-compose exec backend python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
"

# Check for N+1 queries
docker-compose logs backend | grep "SLOW QUERY"

# Analyze with EXPLAIN
# In PostgreSQL:
EXPLAIN ANALYZE SELECT * FROM conversations WHERE user_id = 'test';
```

---

## Performance Benchmarks

Run benchmarks to verify improvements:

```bash
# Benchmark cache performance
docker-compose exec backend python -m pytest \
  tests/test_performance_optimization.py::TestRedisCachePerformance -v

# Benchmark database performance
docker-compose exec backend python -m pytest \
  tests/test_performance_optimization.py::TestDatabaseQueryPerformance -v

# Full integration benchmark
docker-compose exec backend python -m pytest \
  tests/test_performance_optimization.py::TestIntegrationPerformance -v
```

---

## Rollback Procedure

If you need to rollback:

### Disable Cache

```bash
# Edit .env
CACHE_ENABLED=false

# Restart backend
docker-compose restart backend
```

### Remove Database Indexes

```bash
# Rollback migration (development only!)
python -m src.db.migrations.performance_optimization rollback
```

### Stop Redis

```bash
docker-compose stop redis
```

---

## Production Recommendations

1. **Redis Persistence**
   - Enable AOF: `appendonly yes`
   - Daily backups of Redis dump.rdb

2. **Cache Warmup**
   - Pre-load top 1000 conversations on startup
   - Warm up user data for active users

3. **Monitoring**
   - Set up alerts for cache hit rate <60%
   - Monitor Redis memory usage
   - Track slow queries (>100ms)

4. **Scaling**
   - Use Redis Sentinel for high availability
   - Consider Redis Cluster for >10GB data
   - Add read replicas for PostgreSQL

5. **Security**
   - Set Redis password in production
   - Use SSL/TLS for Redis connections
   - Restrict Redis network access

---

## Success Metrics

After deployment, you should see:

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Cache Hit Rate | >60% | Prometheus metrics |
| API p95 Latency | <200ms | Response time headers |
| DB Query Count | -50% | Application logs |
| Memory Usage | <600MB | Docker stats |
| Error Rate | <0.1% | Error logs |

---

## Next Steps

1. **Week 1**: Deploy to staging, monitor metrics
2. **Week 2**: Tune cache TTL based on hit rates
3. **Week 3**: Deploy to production with canary release
4. **Week 4**: Optimize based on production metrics

---

## Support

If you encounter issues:

1. Check logs: `docker-compose logs -f`
2. Review this guide
3. Run diagnostics: `python -m src.db.migrations.performance_optimization analyze`
4. Check Redis: `docker-compose exec redis redis-cli INFO`
