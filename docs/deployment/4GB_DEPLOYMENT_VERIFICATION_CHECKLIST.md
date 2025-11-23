# 4GB Deployment Verification Checklist

**Project:** SaaS Control Deck
**Configuration:** 4GB Memory Optimized
**Last Updated:** 2025-11-22
**Checklist Version:** 1.0

---

## Phase 1: Pre-Deployment Validation (BEFORE Deployment)

### 1.1 Configuration Files Validation

- [ ] **Docker Compose Syntax Check**
  ```bash
  docker-compose -f docker-compose-4gb.yml config > /dev/null
  echo "Exit code: $?"  # Should be 0
  ```

- [ ] **Prometheus Configuration Validation**
  ```bash
  docker run --rm -v $PWD/monitoring/prometheus:/etc/prometheus \
    prom/prometheus:latest \
    promtool check config /etc/prometheus/prometheus-4gb.yml
  ```
  Expected output: `SUCCESS: 0 rule files found`

- [ ] **Alert Rules Validation**
  ```bash
  docker run --rm -v $PWD/monitoring/prometheus:/etc/prometheus \
    prom/prometheus:latest \
    promtool check rules /etc/prometheus/alerts-4gb.yml
  ```
  Expected: 10 alert rules found, 0 errors

- [ ] **Grafana Dashboard JSON Validation**
  ```bash
  jq empty monitoring/grafana/dashboards/application-overview-4gb.json
  echo $?  # Should be 0
  ```

- [ ] **Memory Limits Verification**
  ```bash
  # Sum of all container memory limits should be < 3.5GB
  grep -A 5 "resources:" docker-compose-4gb.yml | grep "memory:" | awk '{sum+=$2} END {print sum}'
  ```
  Expected: Total < 3500MB

### 1.2 GitHub Configuration

- [ ] **GitHub Secrets Configured**
  - `COOLIFY_API_TOKEN` exists and valid
  - `COOLIFY_FQDN` = https://coolpanel.jackcwf.com
  - `COOLIFY_STAGING_APP_UUID` configured
  - `COOLIFY_PRODUCTION_APP_UUID` configured
  - `SLACK_WEBHOOK` configured (optional)

- [ ] **GitHub Actions Workflow File**
  - File exists: `.github/workflows/build-and-deploy-4gb.yml`
  - Workflow syntax valid (GitHub validates automatically)

- [ ] **Branch Protection Rules**
  - Main branch requires pull request reviews
  - Status checks required before merge
  - Deployment approval configured for production

### 1.3 Environment Variables

- [ ] **Production .env File Created**
  - Copy from `.env.example`
  - Update all `your-*` placeholders
  - Database credentials verified
  - Redis configuration set (256MB limit)

- [ ] **Coolify Environment Variables Set**
  Log into Coolify and verify:
  - `DATABASE_URL`
  - `REDIS_HOST`, `REDIS_PORT`
  - `REDIS_MAX_MEMORY=256`
  - `CACHE_TTL_CONVERSATION=1800`
  - `CACHE_TTL_USER=3600`
  - `CACHE_TTL_DOCUMENT=43200`
  - `LOG_LEVEL=INFO`

### 1.4 Backup Verification

- [ ] **Latest Backup Exists**
  ```bash
  ./scripts/deploy/backup.sh production --verify
  ```

- [ ] **Backup Location Accessible**
  - Verify backup is stored in secure location
  - Test restore procedure (if first deployment)

- [ ] **Database Backup Size Reasonable**
  - Check backup file is not corrupt
  - Verify size matches expected database size

### 1.5 Infrastructure Readiness

- [ ] **Server Resources Available**
  - RAM: 4GB total (verified in Coolify)
  - Disk: 40GB minimum free
  - CPU: 2 cores minimum

- [ ] **Network Configuration**
  - Ports exposed: 80 (Nginx), 3001 (Grafana), 9090 (Prometheus)
  - Firewall rules configured
  - DNS records pointing to correct IP

- [ ] **SSL Certificate Valid**
  ```bash
  echo | openssl s_client -servername jackcwf.com -connect jackcwf.com:443 2>/dev/null | openssl x509 -noout -dates
  ```
  Expected: `notAfter` date in future

---

## Phase 2: Deployment Execution (DURING Deployment)

### 2.1 GitHub Actions Workflow Monitoring

- [ ] **Workflow Triggered Successfully**
  - Check GitHub Actions tab
  - Verify workflow is running

- [ ] **Configuration Validation Job Passed**
  - Docker Compose validation ✓
  - Prometheus config validation ✓
  - Alert rules validation ✓
  - Memory limits verification ✓

- [ ] **Build and Push Job Passed**
  - Docker image built successfully
  - Image pushed to GHCR
  - Vulnerability scan completed (Trivy)
  - No critical vulnerabilities found

- [ ] **Deploy to Staging Job Passed**
  - Coolify deployment triggered
  - Health checks passed
  - Memory constraints verified

- [ ] **Production Approval Granted**
  - Manual approval completed
  - Backup created before deployment

- [ ] **Deploy to Production Job Running**
  - Monitor deployment logs in real-time
  - Check Coolify dashboard for progress

### 2.2 Coolify Deployment Monitoring

- [ ] **Deployment Started in Coolify**
  - Navigate to Coolify dashboard
  - Verify deployment is in "Building" state

- [ ] **Image Pull Successful**
  - Check logs show: "Pulling image..."
  - No authentication errors

- [ ] **Containers Starting**
  - Monitor container logs in Coolify
  - Verify all 5 services starting:
    - fastapi-backend
    - postgres
    - redis-cache
    - prometheus
    - grafana

- [ ] **No Container Crashes**
  - Monitor logs for errors
  - Check for OOM kills (exit code 137)
  - Verify all containers reach "Running" state

### 2.3 Real-Time Health Monitoring

- [ ] **Initial Health Check (30 seconds after start)**
  ```bash
  curl -f http://jackcwf.com/health || echo "FAILED"
  ```
  Expected: HTTP 200

- [ ] **Container Memory Usage Check**
  ```bash
  docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}"
  ```
  Expected: All containers within limits

- [ ] **Application Logs Clean**
  ```bash
  docker-compose -f docker-compose-4gb.yml logs --tail=50
  ```
  Expected: No ERROR or CRITICAL messages

---

## Phase 3: Post-Deployment Validation (AFTER Deployment)

### 3.1 Automated Health Checks

- [ ] **Run 4GB Health Check Script**
  ```bash
  ./scripts/deploy/health-check-4gb.sh https://jackcwf.com
  ```
  Expected: All 10 checks pass

  **10 Critical Checks:**
  1. ✅ Frontend accessibility
  2. ✅ Backend API accessibility
  3. ✅ Health endpoint (`/api/health`)
  4. ✅ Ready endpoint (`/api/ready`)
  5. ✅ Response time (< 2s)
  6. ✅ Memory usage (< 3.5GB)
  7. ✅ Prometheus accessibility
  8. ✅ Grafana accessibility
  9. ✅ Service metrics (Redis, PostgreSQL)
  10. ✅ SSL certificate validity

- [ ] **Run Smoke Tests**
  ```bash
  ./scripts/deploy/smoke-tests.sh https://jackcwf.com
  ```
  Expected: All functional tests pass

### 3.2 Service Availability Verification

- [ ] **Frontend Loads**
  - Navigate to https://jackcwf.com
  - Page loads without errors
  - Assets loading correctly (CSS, JS)

- [ ] **API Documentation Accessible**
  - Navigate to https://jackcwf.com/docs
  - Swagger UI loads
  - All endpoints listed

- [ ] **Health Endpoint Responds**
  ```bash
  curl https://jackcwf.com/api/health | jq '.'
  ```
  Expected:
  ```json
  {
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2025-11-22T10:00:00Z"
  }
  ```

- [ ] **Metrics Endpoint Responds**
  ```bash
  curl https://jackcwf.com/api/metrics
  ```
  Expected: Prometheus format metrics

### 3.3 Database Health Verification

- [ ] **PostgreSQL Accessible**
  ```bash
  docker exec -it postgres psql -U langchain -d langchain_db -c "SELECT version();"
  ```

- [ ] **Connection Count Within Limits**
  ```bash
  docker exec postgres psql -U langchain -d langchain_db \
    -c "SELECT count(*) FROM pg_stat_activity;"
  ```
  Expected: < 50 connections

- [ ] **Database Tables Exist**
  ```bash
  docker exec postgres psql -U langchain -d langchain_db \
    -c "\dt"
  ```
  Expected: All tables listed (conversations, messages, documents, etc.)

- [ ] **No Long-Running Queries**
  ```bash
  docker exec postgres psql -U langchain -d langchain_db \
    -c "SELECT pid, query, state FROM pg_stat_activity WHERE state != 'idle' AND query_start < now() - interval '1 minute';"
  ```
  Expected: Empty result

### 3.4 Redis Cache Health Verification

- [ ] **Redis Accessible**
  ```bash
  docker exec redis-cache redis-cli PING
  ```
  Expected: `PONG`

- [ ] **Memory Usage Within Limit**
  ```bash
  docker exec redis-cache redis-cli INFO memory | grep "used_memory_human"
  ```
  Expected: < 256MB

- [ ] **Max Memory Policy Correct**
  ```bash
  docker exec redis-cache redis-cli CONFIG GET maxmemory-policy
  ```
  Expected: `allkeys-lru`

- [ ] **Keys Exist (if applicable)**
  ```bash
  docker exec redis-cache redis-cli DBSIZE
  ```
  Expected: > 0 (if application has run)

- [ ] **Cache Hit Rate Reasonable**
  ```bash
  docker exec redis-cache redis-cli INFO stats | grep "keyspace_hits"
  ```
  Expected: Hit rate > 40% after warmup

### 3.5 Monitoring Stack Verification

- [ ] **Prometheus Accessible**
  - Navigate to https://jackcwf.com:9090
  - UI loads successfully
  - Targets page shows all services "UP"

- [ ] **10 Critical Alerts Loaded**
  - Navigate to https://jackcwf.com:9090/alerts
  - Verify all 10 alerts present:
    1. ServiceDown
    2. HighMemoryUsage
    3. HighAPILatency
    4. LowCacheHitRate
    5. HighDatabaseConnections
    6. RedisMemoryHigh
    7. LowDiskSpace
    8. SlowDatabaseQueries
    9. ContainerOOMKills
    10. HighNetworkIO

- [ ] **No Critical Alerts Firing**
  - Check alerts page
  - All should be "green" (inactive)

- [ ] **Prometheus Metrics Being Collected**
  ```bash
  curl -s http://jackcwf.com:9090/api/v1/query?query=up | jq '.data.result[] | {job: .metric.job, status: .value[1]}'
  ```
  Expected: All jobs show `"1"` (up)

- [ ] **Grafana Accessible**
  - Navigate to https://jackcwf.com:3001
  - Login: admin/admin
  - Prompted to change password

- [ ] **Grafana Data Source Configured**
  - Go to Configuration → Data Sources
  - Prometheus data source exists
  - Test connection successful

- [ ] **4GB Dashboard Imported**
  - Navigate to Dashboards
  - "Application Overview (4GB)" exists
  - Dashboard loads with data

- [ ] **Dashboard Metrics Populating**
  - CPU usage graph shows data
  - Memory usage graph shows data
  - API latency graph shows data
  - Cache hit rate graph shows data

### 3.6 Performance Verification

- [ ] **API Response Time Acceptable**
  ```bash
  time curl -s https://jackcwf.com/api/health > /dev/null
  ```
  Expected: < 2s

- [ ] **Frontend Load Time Acceptable**
  - Use browser DevTools
  - Network tab shows load time < 3s

- [ ] **Database Query Performance**
  ```bash
  docker exec postgres psql -U langchain -d langchain_db \
    -c "EXPLAIN ANALYZE SELECT * FROM conversations LIMIT 10;"
  ```
  Expected: Execution time < 500ms

- [ ] **Memory Usage Stable**
  - Wait 5 minutes
  - Re-check `docker stats`
  - Memory usage should be stable (not increasing)

### 3.7 Functional Testing

- [ ] **User Authentication Works** (if applicable)
  - Create test user
  - Login successful
  - JWT token generated

- [ ] **API CRUD Operations Work**
  - Create: POST /api/conversations
  - Read: GET /api/conversations/{id}
  - Update: PUT /api/conversations/{id}
  - Delete: DELETE /api/conversations/{id}

- [ ] **Database Persistence Works**
  - Create resource via API
  - Restart backend container
  - Verify resource still exists

- [ ] **Cache Works**
  - Make API request
  - Check Redis for cached response
  - Second request should be faster (cache hit)

### 3.8 Logging and Monitoring

- [ ] **Application Logs Available**
  ```bash
  docker-compose -f docker-compose-4gb.yml logs -f fastapi-backend
  ```
  Expected: Logs streaming, no errors

- [ ] **Log Level Correct**
  - Check logs show `INFO` level messages
  - No `DEBUG` messages (unless debugging)

- [ ] **Log Rotation Configured**
  - Check docker-compose.yml has logging config
  - `max-size: "50m"`, `max-file: "3"`

- [ ] **Prometheus Metrics Exported**
  ```bash
  curl https://jackcwf.com/api/metrics | grep "api_request_duration_seconds"
  ```
  Expected: Histogram metrics present

### 3.9 Security Verification

- [ ] **HTTPS Working**
  - Navigate to https://jackcwf.com
  - No SSL warnings in browser

- [ ] **HTTP Redirects to HTTPS**
  ```bash
  curl -I http://jackcwf.com
  ```
  Expected: HTTP 301 redirect to HTTPS

- [ ] **API Documentation Secured** (if applicable)
  - Verify /docs requires authentication
  - Or is publicly accessible as intended

- [ ] **No Sensitive Data in Logs**
  - Review logs for API keys, passwords
  - Ensure secrets are redacted

### 3.10 Rollback Readiness

- [ ] **Rollback Script Tested**
  ```bash
  ./scripts/deploy/rollback.sh production --dry-run
  ```
  Expected: Shows rollback plan

- [ ] **Previous Version Documented**
  - Note down previous Docker image tag
  - Save in deployment log

- [ ] **Rollback Procedure Documented**
  - Team knows how to rollback
  - Emergency contacts available

---

## Phase 4: Long-Term Validation (1 hour after deployment)

### 4.1 Memory Stability Check

- [ ] **Memory Usage Stable Over 1 Hour**
  ```bash
  # Run every 15 minutes
  docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}"
  ```
  Expected: No significant increase (< 10%)

- [ ] **No OOM Kills**
  ```bash
  dmesg | grep -i "out of memory"
  ```
  Expected: No new OOM kills

- [ ] **Swap Usage Minimal**
  ```bash
  free -h
  ```
  Expected: Swap used < 500MB

### 4.2 Performance Baseline Established

- [ ] **API P95 Latency Recorded**
  - Check Grafana dashboard
  - Document baseline P95 latency

- [ ] **Cache Hit Rate Stabilized**
  - Check Grafana or Prometheus
  - Expected: > 40% after 1 hour

- [ ] **Database Connection Pool Stable**
  - Check PostgreSQL connections
  - Expected: Stable count (not constantly maxing out)

### 4.3 Alert Testing

- [ ] **Test Alert Firing** (optional, in staging)
  - Trigger HighMemoryUsage alert intentionally
  - Verify alert fires in Prometheus
  - Verify notification sent (if configured)

- [ ] **Alert Recovery**
  - Resolve condition
  - Verify alert auto-resolves

---

## Phase 5: Final Sign-Off

### 5.1 Deployment Summary

- [ ] **Deployment Version Documented**
  - Docker image tag: `________________`
  - Git commit SHA: `________________`
  - Deployment timestamp: `________________`

- [ ] **All Checks Passed**
  - Total checks passed: `_____ / 100+`
  - Critical failures: `_____ (should be 0)`

- [ ] **Deployment Notes Recorded**
  - Any issues encountered: `________________`
  - Workarounds applied: `________________`
  - Follow-up actions needed: `________________`

### 5.2 Stakeholder Notification

- [ ] **Development Team Notified**
  - Slack message sent
  - Email notification sent

- [ ] **Monitoring Team Notified**
  - On-call team aware
  - Escalation path documented

- [ ] **Deployment Summary Created**
  - GitHub Actions generated summary
  - Uploaded to deployment artifacts

### 5.3 Post-Deployment Actions

- [ ] **Update Deployment Log**
  - Record in deployment history
  - Note any deviations from plan

- [ ] **Schedule Post-Mortem** (if issues occurred)
  - Book meeting within 48 hours
  - Invite relevant stakeholders

- [ ] **Monitor for 24 Hours**
  - Assign on-call rotation
  - Watch for memory trends
  - Review alerts daily

---

## Rollback Triggers

**Immediate Rollback Required If:**

- [ ] Critical services down for > 5 minutes
- [ ] Memory usage > 95% for > 2 minutes
- [ ] OOM kills occurring
- [ ] Database connection failures
- [ ] API error rate > 10%
- [ ] Data corruption detected

**Rollback Procedure:**

```bash
# Immediate rollback
./scripts/deploy/rollback.sh production

# Verify rollback
./scripts/deploy/health-check-4gb.sh https://jackcwf.com
```

---

## Checklist Completion Summary

**Total Checkpoints:** 100+
**Passed:** _____
**Failed:** _____
**Skipped:** _____

**Overall Deployment Status:**
- [ ] ✅ **PASS** - Deployment successful, all checks passed
- [ ] ⚠️ **PASS WITH WARNINGS** - Deployment successful, minor issues noted
- [ ] ❌ **FAIL** - Deployment failed, rollback initiated

**Approved By:**
- Deployment Engineer: `________________`
- Technical Lead: `________________`
- Date: `________________`

---

**Checklist Version:** 1.0
**Last Updated:** 2025-11-22
**Next Review:** After first production deployment

**Notes:**
- This checklist should be followed for every 4GB deployment
- Update checklist based on lessons learned
- Archive completed checklists for audit trail
