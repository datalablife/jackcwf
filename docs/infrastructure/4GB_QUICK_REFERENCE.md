# 4GB Deployment - Quick Reference Card

## Deployment Commands

```bash
# Deploy 4GB stack
docker-compose -f docker-compose-4gb.yml up -d

# Check status
docker ps

# View logs
docker-compose -f docker-compose-4gb.yml logs -f

# Stop stack
docker-compose -f docker-compose-4gb.yml down

# Restart single service
docker-compose restart fastapi-backend
```

## Health Check URLs

| Service | URL | Expected Response |
|---------|-----|-------------------|
| FastAPI | http://localhost:8000/health | `{"status":"healthy"}` |
| Prometheus | http://localhost:9090/targets | All targets "UP" |
| Grafana | http://localhost:3001 | Login page (admin/admin) |

## Quick Diagnostics

### Memory Check
```bash
# Container memory
docker stats --no-stream

# System memory
free -h

# Total Docker memory
docker stats --no-stream --format "{{.MemUsage}}" | awk '{print $1}' | sed 's/MiB//g' | awk '{s+=$1} END {print s "MB"}'
```

### Service Health
```bash
# FastAPI
curl http://localhost:8000/health

# PostgreSQL
docker exec postgres psql -U langchain -d langchain_db -c "SELECT count(*) FROM pg_stat_activity;"

# Redis
docker exec redis-cache redis-cli ping
docker exec redis-cache redis-cli INFO memory | grep used_memory_human
```

### Performance Metrics
```bash
# Database connections (max 50)
docker exec postgres psql -U langchain -d langchain_db -t -c "SELECT count(*) FROM pg_stat_activity;" | xargs

# Cache hit rate
docker exec redis-cache redis-cli INFO stats | grep keyspace_hits

# Prometheus targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job, health}'
```

## Expected Memory Usage

| Service | Limit | Normal | Peak |
|---------|-------|--------|------|
| FastAPI | 500M | 300-400M | 450-500M |
| PostgreSQL | 800M | 500-650M | 700-800M |
| Redis | 300M | 200-256M | 256M (capped) |
| Prometheus | 200M | 100-130M | 150-200M |
| Grafana | 150M | 110-130M | 130-150M |
| **TOTAL** | **1.95G** | **1.7-2.2G** | **2.3-2.9G** |

## Alert Thresholds

| Alert | Threshold | Action |
|-------|-----------|--------|
| HighMemoryUsage | <15% available | Clear cache, restart services |
| HighAPILatency | P95 >2s | Check slow queries |
| HighDatabaseConnections | >80 | Add connection pooling |
| RedisMemoryHigh | >90% of 256MB | LRU eviction active (normal) |
| ContainerOOMKills | Any kills | Increase memory or optimize |

## Emergency Actions

### High Memory (>3.5GB)
```bash
# 1. Clear Redis cache
docker exec redis-cache redis-cli FLUSHDB

# 2. Restart heaviest service
docker-compose restart postgres

# 3. Check for memory leaks
docker logs fastapi-backend | grep -i "memory"
```

### Service Down
```bash
# 1. Check container status
docker ps -a | grep fastapi

# 2. View last 50 log lines
docker logs fastapi-backend --tail 50

# 3. Restart container
docker-compose restart fastapi-backend
```

### Database Connection Exhaustion (>45)
```bash
# 1. Check connections
docker exec postgres psql -U langchain -d langchain_db -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# 2. Kill idle connections
docker exec postgres psql -U langchain -d langchain_db -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND state_change < now() - interval '10 minutes';"

# 3. Restart FastAPI
docker-compose restart fastapi-backend
```

### OOM Detected
```bash
# 1. Check OOM logs
dmesg | grep -i oom

# 2. Identify killed container
docker ps -a

# 3. Reduce memory pressure
docker exec redis-cache redis-cli FLUSHDB
docker-compose restart <killed-container>
```

## Configuration Validation

### Prometheus
```bash
# Scrape interval (expected: 30s)
docker exec prometheus cat /etc/prometheus/prometheus.yml | grep scrape_interval | head -1

# Retention (expected: 7d)
docker inspect prometheus --format='{{.Args}}' | grep retention

# Alert count (expected: 10)
docker exec prometheus cat /etc/prometheus/alerts.yml | grep -c "alert:"
```

### Redis
```bash
# Max memory (expected: 256MB = 268435456 bytes)
docker exec redis-cache redis-cli CONFIG GET maxmemory

# Eviction policy (expected: allkeys-lru)
docker exec redis-cache redis-cli CONFIG GET maxmemory-policy

# Current usage
docker exec redis-cache redis-cli INFO memory | grep used_memory_human
```

### PostgreSQL
```bash
# Shared buffers (expected: 256MB)
docker exec postgres psql -U langchain -d langchain_db -t -c "SHOW shared_buffers;" | xargs

# Max connections (expected: 50)
docker exec postgres psql -U langchain -d langchain_db -t -c "SHOW max_connections;" | xargs

# Active connections
docker exec postgres psql -U langchain -d langchain_db -t -c "SELECT count(*) FROM pg_stat_activity;" | xargs
```

## Testing Commands

### Run Stress Test
```bash
# Full stress test (15 min)
python3 scripts/infrastructure/stress-test-4gb.py --url http://localhost:8000 --output results/

# Quick health test (1 min)
for i in {1..60}; do curl -s http://localhost:8000/health > /dev/null && echo "OK" || echo "FAIL"; sleep 1; done
```

### Run Full Test Suite
```bash
# Comprehensive test (generates full report)
./scripts/infrastructure/test-4gb-deployment.sh
```

### Monitor During Test
```bash
# Continuous memory monitoring (Ctrl+C to stop)
watch -n 5 'docker stats --no-stream'

# Check for OOM kills
watch -n 10 'dmesg | tail -20 | grep -i oom'
```

## Success Indicators

### Good Signs
- Total memory < 3.5GB
- All containers within limits
- API P95 latency < 500ms
- Cache hit rate > 70%
- No OOM kills
- DB connections < 45
- No critical alerts

### Warning Signs
- Total memory > 3.5GB
- API P95 latency > 500ms
- Cache hit rate < 50%
- DB connections > 40
- Warning alerts firing

### Critical Issues
- Total memory > 3.8GB
- OOM kills detected
- API P95 latency > 2s
- DB connection exhaustion (>45)
- Critical alerts firing
- Service crashes

## Rollback

```bash
# Quick rollback to original stack
docker-compose -f docker-compose-4gb.yml down
docker-compose -f docker-compose.yml up -d
curl http://localhost:8000/health
```

## Optimization Quick Wins

### Add Semantic Caching (2 hours)
```python
# src/services/semantic_cache.py
# Expected: 30-50% DB load reduction
```

### Add pgBouncer (1 hour)
```yaml
# docker-compose-4gb.yml
# Expected: 300MB memory savings
```

### Enable Gzip Compression (5 min)
```python
# src/main.py
app.add_middleware(GZipMiddleware, minimum_size=1000)
# Expected: 60-80% response size reduction
```

## Support Contacts

**Documentation:**
- Full Report: `docs/infrastructure/4GB_INFRASTRUCTURE_TEST_REPORT.md`
- Executive Summary: `docs/infrastructure/4GB_DEPLOYMENT_EXECUTIVE_SUMMARY.md`
- Testing Guide: `docs/infrastructure/4GB_TESTING_EXECUTION_GUIDE.md`

**Resources:**
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin)
- FastAPI Docs: http://localhost:8000/docs

---

**Last Updated:** 2025-11-22
**Version:** 1.0
**Status:** Ready for Testing

---

Print this card or keep it open during testing for quick reference!
