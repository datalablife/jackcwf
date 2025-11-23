# 4GB Infrastructure Testing - Complete Execution Guide

**Date:** 2025-11-22
**Purpose:** Step-by-step guide to validate 4GB memory optimized deployment
**Expected Duration:** 2-3 hours (including monitoring)

---

## Prerequisites

### Required Tools
```bash
# Check if tools are installed
docker --version          # Required: Docker 20.10+
docker-compose --version  # Required: Docker Compose 2.0+
python3 --version         # Required: Python 3.10+
curl --version           # Required: curl
bc --version             # Optional: for calculations
```

### Required Python Dependencies
```bash
# Install stress test dependencies
pip install aiohttp asyncio
```

### System Requirements
- 4GB RAM minimum
- 20GB free disk space
- Network access to Docker Hub

---

## Phase 1: Pre-Deployment Validation (15 minutes)

### Step 1.1: Backup Current State
```bash
# Backup existing database (if upgrading)
docker exec postgres pg_dump -U langchain langchain_db > backup_$(date +%Y%m%d).sql

# Export current container state
docker ps -a > current_containers.txt
docker stats --no-stream > current_stats.txt
```

### Step 1.2: Validate Configuration Files
```bash
cd /mnt/d/工作区/云开发/working

# Check Docker Compose syntax
docker-compose -f docker-compose-4gb.yml config

# Validate Prometheus config
docker run --rm -v $(pwd)/monitoring/prometheus:/etc/prometheus \
  prom/prometheus:latest \
  promtool check config /etc/prometheus/prometheus-4gb.yml

# Validate Alert rules
docker run --rm -v $(pwd)/monitoring/prometheus:/etc/prometheus \
  prom/prometheus:latest \
  promtool check rules /etc/prometheus/alerts-4gb.yml
```

Expected output:
```
SUCCESS: 0 rule groups found
  - alerts-4gb.yml: 2 groups, 10 rules
```

### Step 1.3: Resource Check
```bash
# Check available memory
free -h

# Check disk space
df -h

# Check CPU
nproc
```

Minimum requirements:
- Available memory: > 4GB
- Free disk space: > 20GB
- CPU cores: >= 2

---

## Phase 2: Deployment (10 minutes)

### Step 2.1: Stop Existing Containers
```bash
# Stop old stack (if exists)
docker-compose down

# Optional: Clean up unused resources
docker system prune -f
```

### Step 2.2: Deploy 4GB Optimized Stack
```bash
# Pull latest images
docker-compose -f docker-compose-4gb.yml pull

# Start services
docker-compose -f docker-compose-4gb.yml up -d

# Watch startup logs
docker-compose -f docker-compose-4gb.yml logs -f
```

Wait for all services to show:
```
fastapi-backend | INFO:     Application startup complete.
postgres        | database system is ready to accept connections
redis-cache     | Ready to accept connections
prometheus      | Server is ready to receive web requests.
grafana         | HTTP Server Listen
```

Press Ctrl+C to stop watching logs.

### Step 2.3: Verify Service Health
```bash
# Check container status
docker ps

# Verify FastAPI health
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# Verify PostgreSQL
docker exec postgres psql -U langchain -d langchain_db -c "SELECT version();"

# Verify Redis
docker exec redis-cache redis-cli ping
# Expected: PONG

# Verify Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job, health}'

# Verify Grafana
curl http://localhost:3001/api/health
```

All services should respond successfully.

---

## Phase 3: Memory Baseline Testing (10 minutes)

### Step 3.1: Collect Memory Baseline
```bash
# Create results directory
mkdir -p /tmp/4gb-test-results

# Capture system memory
free -h > /tmp/4gb-test-results/01-memory-baseline.txt

# Capture container memory
docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.CPUPerc}}" \
  >> /tmp/4gb-test-results/01-memory-baseline.txt

# Calculate total Docker memory
docker stats --no-stream --format "{{.MemUsage}}" | \
  awk '{print $1}' | \
  sed 's/MiB//g' | \
  awk '{s+=$1} END {print "Total Docker Memory:", s, "MB"}' \
  >> /tmp/4gb-test-results/01-memory-baseline.txt
```

### Step 3.2: Validate Memory Limits
```bash
# Check each container against limits
echo "=== Memory Limit Validation ===" > /tmp/4gb-test-results/02-memory-validation.txt

# FastAPI (limit: 500MB)
FASTAPI_MEM=$(docker stats --no-stream --format "{{.MemUsage}}" fastapi-backend | awk '{print $1}' | sed 's/MiB//g')
echo "FastAPI: ${FASTAPI_MEM}MB / 500MB (Limit)" >> /tmp/4gb-test-results/02-memory-validation.txt

# PostgreSQL (limit: 800MB)
POSTGRES_MEM=$(docker stats --no-stream --format "{{.MemUsage}}" postgres | awk '{print $1}' | sed 's/MiB//g')
echo "PostgreSQL: ${POSTGRES_MEM}MB / 800MB (Limit)" >> /tmp/4gb-test-results/02-memory-validation.txt

# Redis (limit: 300MB)
REDIS_MEM=$(docker stats --no-stream --format "{{.MemUsage}}" redis-cache | awk '{print $1}' | sed 's/MiB//g')
echo "Redis: ${REDIS_MEM}MB / 300MB (Limit)" >> /tmp/4gb-test-results/02-memory-validation.txt

# Prometheus (limit: 200MB)
PROM_MEM=$(docker stats --no-stream --format "{{.MemUsage}}" prometheus | awk '{print $1}' | sed 's/MiB//g')
echo "Prometheus: ${PROM_MEM}MB / 200MB (Limit)" >> /tmp/4gb-test-results/02-memory-validation.txt

# Grafana (limit: 150MB)
GRAFANA_MEM=$(docker stats --no-stream --format "{{.MemUsage}}" grafana | awk '{print $1}' | sed 's/MiB//g')
echo "Grafana: ${GRAFANA_MEM}MB / 150MB (Limit)" >> /tmp/4gb-test-results/02-memory-validation.txt

# Display results
cat /tmp/4gb-test-results/02-memory-validation.txt
```

Expected ranges:
- FastAPI: 250-400MB
- PostgreSQL: 500-700MB
- Redis: 100-256MB
- Prometheus: 80-120MB
- Grafana: 100-130MB

---

## Phase 4: Configuration Validation (15 minutes)

### Step 4.1: Prometheus Configuration
```bash
echo "=== Prometheus Configuration Validation ===" > /tmp/4gb-test-results/03-prometheus-validation.txt

# Check scrape interval
SCRAPE_INTERVAL=$(docker exec prometheus cat /etc/prometheus/prometheus.yml | grep "scrape_interval:" | head -1 | awk '{print $2}')
echo "Global Scrape Interval: $SCRAPE_INTERVAL (Expected: 30s)" >> /tmp/4gb-test-results/03-prometheus-validation.txt

# Check retention
RETENTION=$(docker inspect prometheus --format='{{.Args}}' | grep -o 'storage.tsdb.retention.time=[^ ]*' | cut -d= -f2)
echo "Retention Time: $RETENTION (Expected: 7d)" >> /tmp/4gb-test-results/03-prometheus-validation.txt

# Count alert rules
ALERT_COUNT=$(docker exec prometheus cat /etc/prometheus/alerts.yml | grep -c "alert:" || echo 0)
echo "Alert Rules Count: $ALERT_COUNT (Expected: 10)" >> /tmp/4gb-test-results/03-prometheus-validation.txt

# Validate scrape targets
curl -s http://localhost:9090/api/v1/targets | \
  jq -r '.data.activeTargets[] | "\(.job): \(.health)"' \
  >> /tmp/4gb-test-results/03-prometheus-validation.txt

cat /tmp/4gb-test-results/03-prometheus-validation.txt
```

### Step 4.2: PostgreSQL Configuration
```bash
echo "=== PostgreSQL Configuration Validation ===" > /tmp/4gb-test-results/04-postgresql-validation.txt

# Check shared_buffers
SHARED_BUFFERS=$(docker exec postgres psql -U langchain -d langchain_db -t -c "SHOW shared_buffers;" | xargs)
echo "shared_buffers: $SHARED_BUFFERS (Expected: 256MB)" >> /tmp/4gb-test-results/04-postgresql-validation.txt

# Check max_connections
MAX_CONN=$(docker exec postgres psql -U langchain -d langchain_db -t -c "SHOW max_connections;" | xargs)
echo "max_connections: $MAX_CONN (Expected: 50)" >> /tmp/4gb-test-results/04-postgresql-validation.txt

# Check active connections
ACTIVE_CONN=$(docker exec postgres psql -U langchain -d langchain_db -t -c "SELECT count(*) FROM pg_stat_activity;" | xargs)
echo "Active connections: $ACTIVE_CONN" >> /tmp/4gb-test-results/04-postgresql-validation.txt

# Check database size
DB_SIZE=$(docker exec postgres psql -U langchain -d langchain_db -t -c "SELECT pg_size_pretty(pg_database_size('langchain_db'));" | xargs)
echo "Database size: $DB_SIZE" >> /tmp/4gb-test-results/04-postgresql-validation.txt

cat /tmp/4gb-test-results/04-postgresql-validation.txt
```

### Step 4.3: Redis Configuration
```bash
echo "=== Redis Configuration Validation ===" > /tmp/4gb-test-results/05-redis-validation.txt

# Check maxmemory
MAXMEMORY=$(docker exec redis-cache redis-cli CONFIG GET maxmemory | tail -1)
MAXMEMORY_MB=$((MAXMEMORY / 1024 / 1024))
echo "maxmemory: ${MAXMEMORY_MB}MB (Expected: 256MB)" >> /tmp/4gb-test-results/05-redis-validation.txt

# Check maxmemory-policy
POLICY=$(docker exec redis-cache redis-cli CONFIG GET maxmemory-policy | tail -1)
echo "maxmemory-policy: $POLICY (Expected: allkeys-lru)" >> /tmp/4gb-test-results/05-redis-validation.txt

# Check used memory
USED_MEMORY=$(docker exec redis-cache redis-cli INFO memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
echo "Used memory: $USED_MEMORY" >> /tmp/4gb-test-results/05-redis-validation.txt

# Check persistence
AOF=$(docker exec redis-cache redis-cli CONFIG GET appendonly | tail -1)
echo "AOF persistence: $AOF (Expected: yes)" >> /tmp/4gb-test-results/05-redis-validation.txt

cat /tmp/4gb-test-results/05-redis-validation.txt
```

---

## Phase 5: Performance Stress Testing (60 minutes)

### Step 5.1: Run Automated Stress Test
```bash
# Make stress test executable
chmod +x /mnt/d/工作区/云开发/working/scripts/infrastructure/stress-test-4gb.py

# Run stress test (will take ~10-15 minutes)
python3 /mnt/d/工作区/云开发/working/scripts/infrastructure/stress-test-4gb.py \
  --url http://localhost:8000 \
  --output /tmp/4gb-test-results
```

This will run 4 scenarios:
1. Normal Load: 100 req/s for 60s
2. Peak Load: 200 req/s for 60s
3. Spike Load: 500 req/s for 30s
4. Sustained Load: 150 req/s for 300s

Expected output:
```
4GB Deployment Stress Test Suite
==================================================
Target: http://localhost:8000
Start Time: 2025-11-22 14:30:00
==================================================

[1/4] Running Normal Load Test (100 req/s for 60s)...
  ✓ Completed: 6000 requests, P95: 180.5ms, Errors: 0.0%

[2/4] Running Peak Load Test (200 req/s for 60s)...
  ✓ Completed: 12000 requests, P95: 350.2ms, Errors: 0.1%

[3/4] Running Spike Load Test (500 req/s for 30s)...
  ✓ Completed: 15000 requests, P95: 850.8ms, Errors: 2.5%

[4/4] Running Sustained Load Test (150 req/s for 300s)...
  ✓ Completed: 45000 requests, P95: 280.3ms, Errors: 0.2%

STRESS TEST RESULTS SUMMARY
==================================================
...
Results saved to: /tmp/4gb-test-results/stress_test_results_20251122_143000.json
```

### Step 5.2: Monitor Memory During Test
```bash
# In a separate terminal, run continuous monitoring
watch -n 5 'docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}\t{{.CPUPerc}}"'
```

### Step 5.3: Check for OOM Kills
```bash
# After stress test completes, check for any OOM kills
dmesg | grep -i oom > /tmp/4gb-test-results/06-oom-check.txt

# If file is empty, no OOM kills occurred (good!)
if [ ! -s /tmp/4gb-test-results/06-oom-check.txt ]; then
    echo "✓ No OOM kills detected" > /tmp/4gb-test-results/06-oom-check.txt
fi

cat /tmp/4gb-test-results/06-oom-check.txt
```

---

## Phase 6: Alert Rules Validation (10 minutes)

### Step 6.1: Verify All Alerts Loaded
```bash
# Check Prometheus alerts page
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[].rules[] | {alert: .name, state: .state}'

# Expected: 10 alerts in "inactive" state (no active alerts is good)
```

### Step 6.2: Test Sample Alert (Optional)
```bash
# Trigger high memory alert by filling Redis
docker exec redis-cache redis-cli DEBUG POPULATE 100000 key 1000

# Wait 5 minutes for alert to fire
sleep 300

# Check if alert fired
curl -s http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | {alert: .labels.alertname, state: .state}'

# Clean up
docker exec redis-cache redis-cli FLUSHDB
```

---

## Phase 7: Final Validation & Reporting (15 minutes)

### Step 7.1: Run Full Test Script
```bash
# Make test script executable
chmod +x /mnt/d/工作区/云开发/working/scripts/infrastructure/test-4gb-deployment.sh

# Run comprehensive test suite
cd /mnt/d/工作区/云开发/working
./scripts/infrastructure/test-4gb-deployment.sh
```

This will generate a full report in `/tmp/4gb-test-results-TIMESTAMP/`

### Step 7.2: Review Test Results
```bash
# Find latest test results directory
LATEST_RESULTS=$(ls -td /tmp/4gb-test-results-* | head -1)

# View final report
cat $LATEST_RESULTS/FINAL_INFRASTRUCTURE_TEST_REPORT.md

# View individual test results
ls -lh $LATEST_RESULTS/
```

### Step 7.3: Generate Summary
```bash
# Create summary report
echo "4GB Deployment Test Summary" > /tmp/4gb-final-summary.txt
echo "Date: $(date)" >> /tmp/4gb-final-summary.txt
echo "" >> /tmp/4gb-final-summary.txt

# Memory usage
echo "=== Memory Usage ===" >> /tmp/4gb-final-summary.txt
docker stats --no-stream --format "{{.Container}}: {{.MemUsage}}" >> /tmp/4gb-final-summary.txt
echo "" >> /tmp/4gb-final-summary.txt

# Configuration validation
echo "=== Configuration ===" >> /tmp/4gb-final-summary.txt
echo "Prometheus Scrape Interval: $(docker exec prometheus cat /etc/prometheus/prometheus.yml | grep scrape_interval | head -1 | awk '{print $2}')" >> /tmp/4gb-final-summary.txt
echo "Alert Rules Count: $(docker exec prometheus cat /etc/prometheus/alerts.yml | grep -c 'alert:')" >> /tmp/4gb-final-summary.txt
echo "Redis MaxMemory: $(docker exec redis-cache redis-cli CONFIG GET maxmemory | tail -1 | awk '{print $1/1024/1024 "MB"}')" >> /tmp/4gb-final-summary.txt
echo "PostgreSQL Max Connections: $(docker exec postgres psql -U langchain -d langchain_db -t -c 'SHOW max_connections;' | xargs)" >> /tmp/4gb-final-summary.txt
echo "" >> /tmp/4gb-final-summary.txt

# Service health
echo "=== Service Health ===" >> /tmp/4gb-final-summary.txt
curl -s http://localhost:8000/health | jq . >> /tmp/4gb-final-summary.txt
echo "Prometheus Targets: $(curl -s http://localhost:9090/api/v1/targets | jq -r '.data.activeTargets[] | select(.health=="up") | .job' | wc -l) up" >> /tmp/4gb-final-summary.txt
echo "" >> /tmp/4gb-final-summary.txt

# Display summary
cat /tmp/4gb-final-summary.txt
```

---

## Phase 8: Continuous Monitoring (24 hours)

### Step 8.1: Set Up Monitoring Dashboard
```bash
# Access Grafana
open http://localhost:3001  # macOS
# OR
xdg-open http://localhost:3001  # Linux
# OR browse to http://localhost:3001 manually

# Login: admin / admin
# Navigate to pre-provisioned dashboards
```

### Step 8.2: Monitor Key Metrics
Monitor these metrics for 24 hours:

**Memory:**
- System memory available > 500MB (12%)
- Container memory within limits
- No OOM kills

**Performance:**
- API P95 latency < 500ms
- Database connections < 45 (90%)
- Cache hit rate > 70%

**Alerts:**
- No critical alerts firing
- Warning alerts resolved within 10 minutes

### Step 8.3: Create Monitoring Checklist
```bash
cat > /tmp/24h-monitoring-checklist.txt <<EOF
4GB Deployment - 24 Hour Monitoring Checklist
=============================================

Every 2 hours, check:
[ ] docker stats (memory usage)
[ ] http://localhost:9090/alerts (active alerts)
[ ] http://localhost:3001 (Grafana dashboards)
[ ] dmesg | grep -i oom (OOM kills)

Log any issues in: /tmp/4gb-issues.log

After 24 hours:
[ ] Review memory trend (stable or growing?)
[ ] Review error logs
[ ] Fine-tune alert thresholds if needed
[ ] Document lessons learned
[ ] Approve for production or request changes
EOF

cat /tmp/24h-monitoring-checklist.txt
```

---

## Success Criteria

### Deployment is SUCCESSFUL if:

- [ ] All 5 containers running and healthy
- [ ] Total memory usage < 3.5GB (87.5% of 4GB)
- [ ] No OOM kills during stress test
- [ ] API P95 latency < 500ms under normal load
- [ ] Cache hit rate > 70% (after warmup)
- [ ] Database connections < 45 (90% of max 50)
- [ ] All 10 alert rules loaded and functional
- [ ] No unresolved critical alerts
- [ ] Stress test passes all 4 scenarios
- [ ] System recovers after spike load within 15 minutes

### Deployment NEEDS TUNING if:

- Memory usage > 3.5GB
- OOM kills detected
- API P95 latency > 1s under normal load
- Error rate > 5% during peak load
- Database connection exhaustion (>45)
- Critical alerts firing continuously

### Deployment is NOT READY if:

- Any service fails to start
- OOM kills during normal load
- Memory usage > 3.8GB (95%)
- API completely unresponsive
- Data corruption or loss detected

---

## Rollback Procedure

If deployment fails:

```bash
# 1. Stop 4GB deployment
docker-compose -f docker-compose-4gb.yml down

# 2. Restore original deployment
docker-compose -f docker-compose.yml up -d

# 3. Restore database (if needed)
docker exec -i postgres psql -U langchain langchain_db < backup_YYYYMMDD.sql

# 4. Verify services
curl http://localhost:8000/health

# 5. Document failure reason
echo "Rollback reason: [DESCRIBE ISSUE]" >> /tmp/rollback-log.txt
```

---

## Next Steps After Successful Testing

### Week 1:
- [ ] Deploy to production with 48-hour close monitoring
- [ ] Set up AlertManager for Slack/email notifications
- [ ] Document any production-specific tuning

### Week 2:
- [ ] Implement semantic caching (30-50% DB load reduction)
- [ ] Add pgBouncer connection pooling (300MB memory savings)
- [ ] Fine-tune alert thresholds based on actual usage

### Month 2:
- [ ] Analyze 30-day trend data
- [ ] Plan capacity upgrade path (8GB at 10K users)
- [ ] Implement automated scaling policies
- [ ] Document lessons learned and best practices

---

## Resources

**Test Scripts:**
- Full test suite: `/mnt/d/工作区/云开发/working/scripts/infrastructure/test-4gb-deployment.sh`
- Stress test: `/mnt/d/工作区/云开发/working/scripts/infrastructure/stress-test-4gb.py`

**Configuration Files:**
- Docker Compose: `/mnt/d/工作区/云开发/working/docker-compose-4gb.yml`
- Prometheus: `/mnt/d/工作区/云开发/working/monitoring/prometheus/prometheus-4gb.yml`
- Alerts: `/mnt/d/工作区/云开发/working/monitoring/prometheus/alerts-4gb.yml`
- DB/Redis Config: `/mnt/d/工作区/云开发/working/config/REDIS_POSTGRESQL_4GB_CONFIG.md`

**Reports:**
- Full test report: `/mnt/d/工作区/云开发/working/docs/infrastructure/4GB_INFRASTRUCTURE_TEST_REPORT.md`
- Executive summary: `/mnt/d/工作区/云开发/working/docs/infrastructure/4GB_DEPLOYMENT_EXECUTIVE_SUMMARY.md`

**Support:**
- Prometheus: https://prometheus.io/docs/
- Docker Stats: https://docs.docker.com/engine/reference/commandline/stats/
- PostgreSQL Memory: https://wiki.postgresql.org/wiki/Tuning_Your_PostgreSQL_Server

---

**Document Version:** 1.0
**Last Updated:** 2025-11-22
**Author:** Infrastructure Team
**Status:** Ready for Execution
