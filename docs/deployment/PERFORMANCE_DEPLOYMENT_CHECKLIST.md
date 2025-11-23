# Performance Optimization Deployment Checklist

Use this checklist to ensure successful deployment of caching and performance optimizations.

---

## Pre-Deployment Checklist

### Environment Verification

- [ ] Docker and Docker Compose installed (20.10+)
- [ ] Python 3.12+ available
- [ ] PostgreSQL 15+ with pgvector extension
- [ ] At least 1GB RAM available (512MB for Redis + overhead)
- [ ] Port 6379 available for Redis
- [ ] Port 8000 available for FastAPI
- [ ] Port 9090 available for Prometheus (optional)
- [ ] Port 3001 available for Grafana (optional)

### Backup and Safety

- [ ] Database backup created: `pg_dump postgres > backup_$(date +%Y%m%d).sql`
- [ ] Application code committed to git
- [ ] Current .env file backed up: `cp .env .env.backup`
- [ ] Rollback plan documented

---

## Deployment Checklist

### Phase 1: Redis Setup (10 minutes)

- [ ] Create Redis configuration directory: `mkdir -p config/redis`
- [ ] Redis config file created: `config/redis/redis.conf`
- [ ] Docker compose file updated with Redis service
- [ ] Start Redis container: `docker-compose up -d redis`
- [ ] Redis health check passes: `docker-compose exec redis redis-cli ping`
- [ ] Redis memory limit set: `docker-compose exec redis redis-cli CONFIG GET maxmemory` returns `512mb`
- [ ] Redis persistence enabled: `docker-compose exec redis redis-cli CONFIG GET appendonly` returns `yes`

**Verification Commands:**
```bash
# All should pass
docker-compose ps redis | grep "Up"
docker-compose exec redis redis-cli INFO server | grep redis_version
docker-compose logs redis | grep -i error  # Should be empty
```

---

### Phase 2: Database Optimization (15 minutes)

- [ ] Migration script exists: `src/db/migrations/performance_optimization.py`
- [ ] Database connection verified: `psql -h 47.79.87.199 -U jackcwf888 -d postgres -c "SELECT 1"`
- [ ] Run migration: `python -m src.db.migrations.performance_optimization apply`
- [ ] Migration recorded: Check `schema_migrations` table
- [ ] Indexes created: Run `\di` in psql to list indexes
- [ ] Tables analyzed: Check for "ANALYZE" in migration output

**Verification Commands:**
```bash
# Check indexes created
python -m src.db.migrations.performance_optimization analyze

# Expected output: 10+ new indexes listed
```

---

### Phase 3: Application Configuration (10 minutes)

- [ ] .env file updated with Redis configuration:
  - [ ] `REDIS_HOST=redis`
  - [ ] `REDIS_PORT=6379`
  - [ ] `REDIS_DB=0`
  - [ ] `REDIS_MAX_CONNECTIONS=50`
  - [ ] `CACHE_ENABLED=true`
  - [ ] `CACHE_TTL_SECONDS=3600`
  - [ ] `DB_POOL_SIZE=20`
  - [ ] `DB_MAX_OVERFLOW=10`

- [ ] Dependencies installed:
  - [ ] `redis` package installed
  - [ ] `prometheus-client` package installed

- [ ] Integration files created:
  - [ ] `src/infrastructure/redis_cache.py`
  - [ ] `src/middleware/cache_middleware.py`
  - [ ] `src/middleware/performance_middleware.py`
  - [ ] `src/integrations/fastapi_redis_integration.py`

**Verification Commands:**
```bash
# Check environment variables
docker-compose exec backend env | grep REDIS

# Check dependencies
docker-compose exec backend python -c "import redis; print(redis.__version__)"
```

---

### Phase 4: Application Deployment (10 minutes)

- [ ] Backend container rebuilt: `docker-compose build backend`
- [ ] Backend container restarted: `docker-compose up -d backend`
- [ ] Backend logs show no errors: `docker-compose logs backend`
- [ ] Redis cache initialization logged: `docker-compose logs backend | grep "Redis cache initialized"`
- [ ] Cache warmup completed: `docker-compose logs backend | grep "Cache warmup complete"`
- [ ] Health check passes: `curl http://localhost:8000/health`

**Verification Commands:**
```bash
# Check all services running
docker-compose ps

# Check backend logs for errors
docker-compose logs backend | grep -i error

# Test API endpoint
curl http://localhost:8000/api/conversations
```

---

### Phase 5: Performance Testing (15 minutes)

- [ ] Performance test suite exists: `tests/test_performance_optimization.py`
- [ ] Run cache performance tests: `pytest tests/test_performance_optimization.py::TestRedisCachePerformance -v`
- [ ] All cache tests pass
- [ ] Run database performance tests: `pytest tests/test_performance_optimization.py::TestDatabaseQueryPerformance -v`
- [ ] All database tests pass
- [ ] Run integration tests: `pytest tests/test_performance_optimization.py::TestIntegrationPerformance -v`
- [ ] All integration tests pass

**Performance Targets:**
- [ ] Cache write latency: <5ms average
- [ ] Cache read latency: <5ms average
- [ ] Cache hit rate: >60%
- [ ] N+1 queries: 0 detected
- [ ] API response time: <200ms p95

---

### Phase 6: Monitoring Setup (10 minutes)

- [ ] Prometheus config created: `config/prometheus/prometheus.yml`
- [ ] Prometheus service started: `docker-compose up -d prometheus`
- [ ] Prometheus accessible: `curl http://localhost:9090/-/healthy`
- [ ] Grafana service started: `docker-compose up -d grafana` (optional)
- [ ] Grafana accessible: `curl http://localhost:3001/api/health`
- [ ] Metrics endpoint working: `curl http://localhost:8000/metrics`
- [ ] Cache metrics visible: `curl http://localhost:8000/metrics | grep cache_hits`

**Verification Commands:**
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq

# Check metrics are being collected
curl http://localhost:8000/metrics | grep http_request_duration_seconds
```

---

## Post-Deployment Verification

### Immediate Checks (within 5 minutes)

- [ ] All containers running: `docker-compose ps` shows all "Up"
- [ ] No error logs: `docker-compose logs | grep -i error` is empty
- [ ] API responds: `curl http://localhost:8000/health` returns 200
- [ ] Cache is working: Make 2 identical API calls, second should be faster
- [ ] Metrics available: `curl http://localhost:8000/metrics` returns data

### Short-term Monitoring (within 1 hour)

- [ ] Cache hit rate >60%: `curl http://localhost:8000/metrics | grep cache_hits`
- [ ] No slow queries: `docker-compose logs backend | grep "SLOW QUERY"` is empty
- [ ] API p95 latency <200ms: Check Prometheus metrics
- [ ] Redis memory <512MB: `docker-compose exec redis redis-cli INFO memory`
- [ ] No connection pool exhaustion: `docker-compose logs backend | grep "pool"`

### Long-term Validation (within 24 hours)

- [ ] Cache hit rate stabilized >70%
- [ ] Zero production errors
- [ ] API latency improved by >60%
- [ ] Database load reduced by >50%
- [ ] Memory usage stable
- [ ] No cache evictions: `docker-compose exec redis redis-cli INFO stats | grep evicted`

---

## Performance Benchmarks

Record baseline and post-deployment metrics:

### Before Deployment

```
API Response Time:
  p50: _____ ms
  p95: _____ ms
  p99: _____ ms

Database Queries:
  Average: _____ queries per request
  N+1 detected: Yes / No

Cache:
  Enabled: No
```

### After Deployment

```
API Response Time:
  p50: _____ ms (improvement: ___%)
  p95: _____ ms (improvement: ___%)
  p99: _____ ms (improvement: ___%)

Database Queries:
  Average: _____ queries per request (improvement: ___%)
  N+1 detected: No

Cache:
  Enabled: Yes
  Hit Rate: _____%
  Average Latency: _____ ms
```

---

## Rollback Procedure

If issues occur, follow these steps:

### Immediate Rollback (< 5 minutes)

1. Disable cache:
   ```bash
   # Edit .env
   CACHE_ENABLED=false

   # Restart backend
   docker-compose restart backend
   ```

2. Stop Redis:
   ```bash
   docker-compose stop redis
   ```

3. Verify application works without cache:
   ```bash
   curl http://localhost:8000/health
   ```

### Full Rollback (< 15 minutes)

1. Stop all new services:
   ```bash
   docker-compose stop redis prometheus grafana
   ```

2. Restore previous .env:
   ```bash
   cp .env.backup .env
   ```

3. Rollback database migration (DEVELOPMENT ONLY):
   ```bash
   python -m src.db.migrations.performance_optimization rollback
   ```

4. Restart with previous version:
   ```bash
   git checkout <previous-commit>
   docker-compose up -d --build backend
   ```

---

## Troubleshooting Guide

### Issue: Redis won't start

**Symptoms:**
- `docker-compose ps redis` shows "Exit 1"
- Logs show "Address already in use"

**Solutions:**
1. Check port 6379: `lsof -i :6379`
2. Change port in docker-compose.yml
3. Check Redis logs: `docker-compose logs redis`

---

### Issue: Cache not initializing

**Symptoms:**
- Backend logs show "Redis cache initialization failed"
- No cache metrics available

**Solutions:**
1. Check Redis is reachable: `docker-compose exec backend ping redis`
2. Check REDIS_HOST in .env
3. Check Redis logs for errors
4. Restart both services: `docker-compose restart redis backend`

---

### Issue: Slow queries still detected

**Symptoms:**
- Logs show "SLOW QUERY" warnings
- API latency still high

**Solutions:**
1. Check indexes created: `python -m src.db.migrations.performance_optimization analyze`
2. Check index usage: Run EXPLAIN ANALYZE on slow queries
3. Review query patterns in code
4. Increase cache TTL for hot data

---

### Issue: High cache miss rate

**Symptoms:**
- Cache hit rate <60%
- Little performance improvement

**Solutions:**
1. Increase cache TTL values
2. Implement cache warmup for hot data
3. Review cache key generation
4. Check cache eviction rate: `docker-compose exec redis redis-cli INFO stats`

---

## Success Criteria

Deployment is successful when ALL criteria are met:

**Infrastructure:**
- [ ] All containers healthy
- [ ] No error logs
- [ ] Monitoring operational

**Performance:**
- [ ] Cache hit rate >60%
- [ ] API latency reduced >60%
- [ ] Database queries reduced >50%
- [ ] No N+1 queries

**Stability:**
- [ ] Zero production errors
- [ ] Memory usage stable
- [ ] Response times consistent

**Monitoring:**
- [ ] Metrics collected
- [ ] Alerts configured
- [ ] Dashboards available

---

## Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Developer | | | |
| DevOps | | | |
| QA | | | |
| Product Owner | | | |

---

## Next Steps After Deployment

1. **Day 1-7**: Monitor closely
   - Check metrics hourly
   - Review error logs
   - Validate performance improvements

2. **Week 2**: Optimize
   - Tune cache TTL based on hit rates
   - Adjust database pool size
   - Identify new optimization opportunities

3. **Week 3-4**: Scale
   - Add Redis replicas if needed
   - Configure PostgreSQL read replicas
   - Implement Redis Cluster for >10GB data

4. **Ongoing**: Maintain
   - Weekly performance reviews
   - Monthly index analysis
   - Quarterly optimization sprints
