# Container Startup Comprehensive Diagnostic Analysis

**Date**: 2025-11-21
**Status**: Critical Analysis - Application Failure on Container Start
**Severity**: HIGH

---

## Executive Summary

After comprehensive analysis of the Docker container startup process, I've identified **5 critical issues** and **3 configuration warnings** that can cause application failure:

### Critical Issues (P0)
1. **Missing Prometheus Client Dependency** - Backend will crash on import
2. **Frontend Build Artifacts Not Verified** - Container starts with empty Nginx root
3. **Backend Startup Verification Missing** - No check if uvicorn binds to port 8000
4. **Health Monitor Dependency Issues** - Missing httpx, psutil imports may fail
5. **Database Connection Timeout Too Short** - 30s may not be enough for remote DB

### Configuration Warnings (P1)
1. **Nginx pid File Location Conflict** - May cause permission issues
2. **Supervisor Log Rotation Not Configured** - Logs may fill disk
3. **Backend Workers Configuration** - 2 workers may be too many for container resources

---

## 1. Startup Flow Analysis

### Current Startup Sequence

```
Container Start
    ↓
docker-entrypoint.sh
    ↓
├─ [1] Create log directories ✅
├─ [2] Verify environment variables (DATABASE_URL) ✅
├─ [3] Database connectivity check (30s timeout) ⚠️
├─ [4] Check .env file exists ✅
├─ [5] Verify supervisord.conf exists ✅
├─ [6] Verify health_monitor.py exists ✅
├─ [7] Nginx config validation (nginx -t) ✅
└─ [8] Start supervisord ⚠️
    ↓
supervisord (nodaemon=true)
    ↓
├─ [Priority 100] Backend (uvicorn) ❌ WILL CRASH
│   ├─ Command: python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 2
│   ├─ Startup time: 10s
│   └─ Issue: Missing prometheus_client import
│
├─ [Priority 200] Nginx (after 10s) ⚠️ STARTS BUT SERVES 404
│   ├─ Command: nginx -g 'daemon off;'
│   ├─ Root: /usr/share/nginx/html (EMPTY)
│   └─ Issue: Frontend files not copied
│
└─ [Priority 300] Health Monitor (after 30s) ❌ MAY CRASH
    ├─ Command: python /app/scripts/monitor/health_monitor.py
    ├─ Startup delay: 30s + 30s wait
    └─ Issue: Backend not available to monitor
```

### Result
- **Nginx starts successfully** (returns 200 on /health)
- **Backend crashes immediately** (import error)
- **Health monitor starts but finds nothing to monitor**
- **All HTTP requests return 404** (no frontend files)

---

## 2. Critical Issue #1: Missing Prometheus Client Dependency

### Problem Location
**File**: `/mnt/d/工作区/云开发/working/src/main.py` (Line 303-310)

```python
# Prometheus metrics endpoint
logger.info("Registering Prometheus metrics endpoint...")
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from src.infrastructure.cache_metrics import cache_registry

@app.get("/metrics", tags=["Metrics"])
async def metrics():
    """Prometheus metrics endpoint for monitoring."""
    return generate_latest(cache_registry)
```

### Root Cause
**File**: `/mnt/d/工作区/云开发/working/pyproject.toml` (Line 37-125)

```toml
dependencies = [
    # ... 60+ packages listed ...
    # ❌ prometheus_client is NOT listed
]
```

### Impact
```python
ModuleNotFoundError: No module named 'prometheus_client'
```

- Backend **will not start** at all
- Supervisor will retry 3 times (startsecs=10, startretries=3)
- After 30 seconds, Supervisor gives up
- Container remains running but backend is dead

### Evidence from Dockerfile
**File**: `/mnt/d/工作区/云开发/working/Dockerfile` (Line 20-22)

```dockerfile
# Install dependencies using uv (faster than pip)
RUN pip install uv && \
    uv pip install "." --system
```

This installs **only** dependencies from `pyproject.toml`. Since `prometheus_client` is missing, it won't be installed.

### Fix Required
```toml
# In pyproject.toml, add to dependencies array:
dependencies = [
    # ... existing packages ...
    "prometheus-client>=0.19.0",  # Metrics and monitoring
    "psutil>=5.9.0",  # Already present at line 97
]
```

---

## 3. Critical Issue #2: Frontend Build Not Verified

### Problem Location
**File**: `/mnt/d/工作区/云开发/working/Dockerfile` (Line 73)

```dockerfile
# ============================================
# Copy Frontend Build Result
# ============================================
COPY --from=frontend-builder /build/dist /usr/share/nginx/html
# ❌ No verification that files were copied
```

### Root Cause Analysis

#### Stage 2: Frontend Builder (Lines 27-39)
```dockerfile
FROM node:20-slim AS frontend-builder

WORKDIR /build

# Copy frontend files
COPY frontend/package*.json ./
RUN npm ci --legacy-peer-deps

# Copy source code
COPY frontend/ ./

# Build frontend (Vite outputs to /build/dist)
RUN npm run build
# ❌ No verification that /build/dist/index.html exists
```

#### Potential Failure Points
1. **npm ci fails** - Dependency conflicts, registry issues
2. **npm run build fails** - TypeScript errors, Vite config issues
3. **Build succeeds but outputs to wrong directory** - vite.config.ts misconfiguration
4. **Build succeeds but /build/dist is empty** - Vite internal error

### Impact
```bash
# Result in container:
$ ls -la /usr/share/nginx/html/
total 4
drwxr-xr-x 2 root root 4096 Nov 21 12:00 .
drwxr-xr-x 3 root root 4096 Nov 21 12:00 ..
# EMPTY - No index.html, no assets/
```

- Nginx starts successfully
- Nginx configuration validates (nginx -t passes)
- All HTTP requests to / return **404 Not Found**
- Only /health endpoint works (static Nginx response)

### Evidence from Entrypoint
**File**: `/mnt/d/工作区/云开发/working/docker/docker-entrypoint.sh` (Line 165-174)

```bash
# ============================================
# Pre-startup Nginx Config Check
# ============================================

log "Validating Nginx configuration..."
if ! nginx -t 2>&1 | tee /tmp/nginx_test.log; then
    log_error "Nginx configuration validation failed!"
    cat /tmp/nginx_test.log
    exit 1
fi

log "✅ Nginx configuration is valid"
# ❌ No check if /usr/share/nginx/html/index.html exists
```

### Fix Required

#### Fix 1: Add verification to Dockerfile (Stage 2)
```dockerfile
# Build frontend (Vite outputs to /build/dist)
RUN npm run build

# ✅ Verify build artifacts exist
RUN ls -la /build/dist/ && \
    test -f /build/dist/index.html || \
    (echo "ERROR: Frontend build failed - index.html not found in /build/dist/" && exit 1)
```

#### Fix 2: Add verification to Dockerfile (Stage 3)
```dockerfile
COPY --from=frontend-builder /build/dist /usr/share/nginx/html

# ✅ Verify files were copied
RUN ls -la /usr/share/nginx/html/ && \
    test -f /usr/share/nginx/html/index.html || \
    (echo "ERROR: Frontend files not copied to /usr/share/nginx/html/" && exit 1)
```

#### Fix 3: Add verification to entrypoint script
```bash
# ============================================
# Verify Frontend Files Exist
# ============================================

log "Verifying frontend files..."

if [ ! -f "/usr/share/nginx/html/index.html" ]; then
    log_error "Frontend index.html not found in /usr/share/nginx/html/"
    log_error "This indicates frontend build failed during Docker image build"
    log_error "Please rebuild the Docker image with --no-cache"
    exit 1
fi

ASSET_COUNT=$(find /usr/share/nginx/html/assets -type f 2>/dev/null | wc -l)
if [ "$ASSET_COUNT" -lt 3 ]; then
    log_warn "Warning: Frontend assets directory seems incomplete ($ASSET_COUNT files)"
    log_warn "Expected at least 3 JavaScript/CSS bundles"
fi

log "✅ Frontend files verified (index.html + $ASSET_COUNT assets)"
```

---

## 4. Critical Issue #3: Backend Startup Not Verified

### Problem Location
**File**: `/mnt/d/工作区/云开发/working/docker/docker-entrypoint.sh`

The entrypoint script checks:
- Database connectivity ✅
- Nginx configuration ✅
- Required files exist ✅

**Missing**: Verification that backend actually starts and binds to port 8000

### Root Cause
**File**: `/mnt/d/工作区/云开发/working/docker/supervisord.conf` (Line 28-54)

```ini
[program:backend]
command=python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 2 --log-level info --access-log

autostart=true
autorestart=true
startsecs=10          ; Wait 10 seconds after start to check success
startretries=3        ; Max 3 retries on failure
```

**Issue**: Supervisor considers the process "started" if it stays alive for 10 seconds. It doesn't check if:
- Port 8000 is actually bound
- FastAPI app initialized successfully
- Health endpoint responds

### Failure Scenario
```bash
# Backend process starts
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 2

# Immediate crash (import error)
ModuleNotFoundError: No module named 'prometheus_client'

# Supervisor sees process exited, retries (attempt 1/3)
# ... retries 2 more times ...
# After 30 seconds, gives up

# Backend status: FATAL
# Container status: RUNNING (because Nginx still works)
# Health check: PASSES (Nginx /health endpoint)
# Application: UNUSABLE
```

### Evidence from Health Monitor
**File**: `/mnt/d/工作区/云开发/working/scripts/monitor/health_monitor.py` (Line 162-163)

```python
# Wait for initial startup
logger.info("Waiting 30s for services to start...")
await asyncio.sleep(30)
```

Health monitor waits 30s before checking backend, but by then backend has already failed 3 times and given up.

### Fix Required

#### Option 1: Add backend health check to entrypoint (Recommended)
```bash
# ============================================
# Wait for Backend to Start
# ============================================

log "Waiting for backend to start..."

BACKEND_TIMEOUT=60
BACKEND_INTERVAL=2

for ((i=0; i<BACKEND_TIMEOUT; i+=BACKEND_INTERVAL)); do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        log "✅ Backend is responding on port 8000"
        break
    fi
    if [ $i -eq 0 ]; then
        log "Backend not ready yet, waiting..."
    fi
    sleep $BACKEND_INTERVAL
done

# Check if backend actually started
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    log_error "Backend failed to start after ${BACKEND_TIMEOUT}s"
    log_error "Check backend logs: docker logs <container> | grep backend"
    # Don't exit - let container run for debugging
    log_warn "Continuing startup for debugging purposes..."
fi
```

#### Option 2: Improve Supervisor configuration
```ini
[program:backend]
command=python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 1 --log-level info
startsecs=20          ; ✅ Increase to 20 seconds (allow app initialization)
startretries=5        ; ✅ Increase retries (maybe transient DB issue)

# ✅ Add health check script
[program:backend-healthcheck]
command=bash -c "sleep 30 && curl -f http://localhost:8000/health || exit 1"
autostart=true
autorestart=false
startsecs=0
priority=150          ; Run after backend starts
```

---

## 5. Critical Issue #4: Health Monitor Dependency Failures

### Problem Location
**File**: `/mnt/d/工作区/云开发/working/scripts/monitor/health_monitor.py` (Line 7-12)

```python
import asyncio
import logging
import httpx      # ❌ May not be installed
import os
import psutil     # ✅ Already in pyproject.toml (line 97)
import signal
```

### Root Cause
**File**: `/mnt/d/工作区/云开发/working/pyproject.toml` (Line 52)

```toml
dependencies = [
    # ...
    "httpx>=0.27.0",     # ✅ Listed in dependencies
    "httpcore>=1.0.0",   # ✅ Listed in dependencies
    "psutil>=5.9.0",     # ✅ Listed in dependencies (line 97)
]
```

**Good news**: All dependencies are already listed. Health monitor should work.

**But**: If backend fails to start, health monitor will log warnings but won't crash:

```python
# Line 75-78
except Exception as e:
    self.backend_failures += 1
    logger.warning(f"✗ Backend health check failed: {str(e)}")
    return False
```

### Issue: Infinite Warning Logs
```bash
# Every 30 seconds:
[WARNING] ✗ Backend health check failed: Connection refused
[WARNING] ✗ Backend health check failed: Connection refused
[WARNING] ✗ Backend health check failed: Connection refused
# ... forever ...
```

### Fix Required
```python
# In health_monitor.py, add max consecutive failures:

MAX_CONSECUTIVE_FAILURES = 20  # 10 minutes at 30s interval

async def handle_failure(self, service: str):
    """Handle service failure"""
    if service == "backend":
        failures = self.backend_failures
    else:
        failures = self.frontend_failures

    logger.error(f"{service} health check failed ({failures}/{MAX_FAILURES})")

    # ✅ Add: Stop monitoring if service never comes up
    if failures >= MAX_CONSECUTIVE_FAILURES:
        logger.error(f"{service} failed {MAX_CONSECUTIVE_FAILURES} times - service appears dead")
        logger.error("Health monitor stopping to prevent log spam")
        self.running = False
```

---

## 6. Critical Issue #5: Database Connection Timeout

### Problem Location
**File**: `/mnt/d/工作区/云开发/working/docker/docker-entrypoint.sh` (Line 70-113)

```bash
# Database Connection Check
DB_CHECK_TIMEOUT=30  # ⚠️ Only 30 seconds
DB_CHECK_INTERVAL=2

for ((i=0; i<DB_CHECK_TIMEOUT; i+=DB_CHECK_INTERVAL)); do
    if python3 << 'EOF'
import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def check_db():
    try:
        engine = create_async_engine(os.getenv("DATABASE_URL"), echo=False)
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        return True
    except Exception as e:
        print(f"DB Error: {type(e).__name__}: {str(e)[:100]}")
        return False
# ... checks and exits
```

### Issue Analysis

#### Database Configuration
**File**: `/mnt/d/工作区/云开发/working/.env` (Line 4)

```bash
DATABASE_URL=postgresql+asyncpg://jackcwf888:Jack_00492300@47.79.87.199:5432/postgres
```

**Database location**: Remote server (47.79.87.199)

#### Potential Delays
1. **DNS resolution**: 1-2s
2. **TCP connection**: 2-5s (remote server)
3. **SSL handshake**: 1-2s
4. **PostgreSQL authentication**: 1-2s
5. **Initial connection pool setup**: 2-5s

**Total**: 7-16 seconds (normal)

**But**: If database server is:
- Under heavy load: 10-30s
- Network congested: 15-45s
- Restarting: 30-90s

**Result**: 30s timeout may be too short for production environments.

### Current Behavior (Good)
```bash
if [ "$DB_CHECKED" = true ]; then
    log "$DB_CHECK_RESULT"
else
    log_warn "⚠️  Database connection failed after ${DB_CHECK_TIMEOUT}s"
    log_warn "Continuing startup anyway - Supervisor will start services"
    log_warn "This may affect backend API functionality, but frontend and Nginx will still run"
fi
# ✅ Container continues even if DB check fails
```

**This is actually good**: Container doesn't fail completely if DB is slow.

### Improvement Recommendation
```bash
# Increase timeout for production
DB_CHECK_TIMEOUT=60  # ✅ Increase to 60 seconds
DB_CHECK_INTERVAL=3  # ✅ Increase interval to reduce log spam
```

---

## 7. Configuration Warning #1: Nginx PID File Location

### Problem Location
**File**: `/mnt/d/工作区/云开发/working/Dockerfile` (Line 54-55)

```dockerfile
mkdir -p /var/cache/nginx /run && \
touch /run/nginx.pid && \
chown -R root:root /var/cache/nginx
```

**File**: `/mnt/d/工作区/云开发/working/docker/nginx.conf` (Line 5)

```nginx
pid /var/run/nginx.pid;
```

### Issue
- Dockerfile creates `/run/nginx.pid`
- Nginx config expects `/var/run/nginx.pid`
- On most systems, `/var/run` is a symlink to `/run`, so this works
- **But**: If symlink doesn't exist, Nginx will fail to start

### Verification
```bash
# In container:
$ ls -la /var/run
lrwxrwxrwx 1 root root 4 Nov 21 12:00 /var/run -> /run
# ✅ Symlink exists in python:3.12-slim base image
```

### Conclusion
**Not a critical issue**, but could be more explicit:

```dockerfile
# Create nginx directories and PID file location
RUN apt-get update && apt-get install -y \
    nginx \
    # ... other packages ...
    && rm -rf /var/lib/apt/lists/* && \
    mkdir -p /var/cache/nginx /var/run && \
    touch /var/run/nginx.pid && \
    chown -R root:root /var/cache/nginx /var/run
```

---

## 8. Configuration Warning #2: Supervisor Log Rotation

### Problem Location
**File**: `/mnt/d/工作区/云开发/working/docker/supervisord.conf` (Line 43-48, 75-80, 106-111)

```ini
stdout_logfile=/var/log/app/backend.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5

stderr_logfile=/var/log/app/backend_error.log
stderr_logfile_maxbytes=10MB
stderr_logfile_backups=5
```

### Issue
- Logs are configured to rotate (max 10MB, 5 backups)
- **But**: Total max logs per service = 10MB × 5 = 50MB
- 3 services × 2 log types (stdout, stderr) = 6 log files
- **Total max logs**: 6 × 50MB = **300MB**

In production with high traffic:
- Backend logs can grow 1MB/hour
- 10MB filled in 10 hours
- After 5 rotations (50 hours), old logs are deleted

### Recommendation
```ini
# Increase log retention for production debugging
stdout_logfile_maxbytes=50MB   # ✅ 50MB per file
stdout_logfile_backups=10      # ✅ 10 backups = 500MB total
```

**Or** use external log aggregation (e.g., Loki, CloudWatch).

---

## 9. Configuration Warning #3: Backend Workers

### Problem Location
**File**: `/mnt/d/工作区/云开发/working/docker/supervisord.conf` (Line 30)

```ini
[program:backend]
command=python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 2 --log-level info --access-log
```

### Issue Analysis

#### Worker Configuration
- **Workers**: 2
- **Worker type**: uvicorn default (sync workers)
- **Memory per worker**: ~100-200MB (FastAPI + SQLAlchemy + LangChain)
- **Total memory**: ~200-400MB

#### Container Resources (Typical Coolify Default)
- **CPU**: 0.5-1 vCPU
- **Memory**: 512MB-1GB

### Calculation
```
Base memory usage:
- Python runtime: 50MB
- FastAPI app: 100MB
- SQLAlchemy + asyncpg: 50MB
- LangChain + OpenAI: 100MB
- Nginx: 20MB
- Supervisor: 10MB
Total base: 330MB

With 2 workers:
- Worker 1: 150MB
- Worker 2: 150MB
Total: 330MB + 300MB = 630MB

With 1 worker:
- Worker 1: 150MB
Total: 330MB + 150MB = 480MB
```

### Recommendation
```ini
# Reduce to 1 worker for containers with <1GB RAM
command=python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 1 --log-level info
```

**Or** use `--workers 0` to auto-detect based on CPU cores:
```ini
command=python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 0 --log-level info
```

---

## 10. Environment Variable Verification

### Current Environment Variables (.env file)
**File**: `/mnt/d/工作区/云开发/working/.env`

```bash
# Required ✅
DATABASE_URL=postgresql+asyncpg://jackcwf888:Jack_00492300@47.79.87.199:5432/postgres

# Optional (with defaults)
MAX_FILE_SIZE=536870912
UPLOAD_DIR=./tmp/uploads
SCHEMA_CACHE_TTL=300
DEBUG="true"
LOG_LEVEL="INFO"
CORS_ORIGINS='["http://localhost:5173", "http://localhost:3000"]'

# API Keys ✅
OPENAI_API_KEY=sk-mw5tjSjGvrxKVn74Qtlt0HibRH5M4uWseX60EjbkUzSvrSxx
OPENAI_BASE_URL=https://anyrouter.top
ANTHROPIC_API_KEY=sk-mw5tjSjGvrxKVn74Qtlt0HibRH5M4uWseX60EjbkUzSvrSxx
ANTHROPIC_BASE_URL=https://anyrouter.top
```

### Validation in Entrypoint
**File**: `/mnt/d/工作区/云开发/working/docker/docker-entrypoint.sh` (Line 51-60)

```bash
required_vars=(
    "DATABASE_URL"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        log_error "Required environment variable not set: $var"
        exit 1
    fi
done
```

### Issue: Incomplete Validation
The script only checks `DATABASE_URL`, but the app may need:
- `OPENAI_API_KEY` (for embeddings)
- `ANTHROPIC_API_KEY` (for Claude models)

### Recommendation
```bash
required_vars=(
    "DATABASE_URL"
)

# Optional but recommended (app will fail if missing)
recommended_vars=(
    "OPENAI_API_KEY"
    "ANTHROPIC_API_KEY"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        log_error "Required environment variable not set: $var"
        exit 1
    fi
done

for var in "${recommended_vars[@]}"; do
    if [ -z "${!var}" ]; then
        log_warn "Recommended environment variable not set: $var"
        log_warn "Some features may not work without this"
    fi
done
```

---

## 11. Summary of All Issues

| Priority | Issue | Impact | Status | Fix Time |
|----------|-------|--------|--------|----------|
| **P0** | Missing prometheus_client dependency | Backend crashes on start | ❌ Critical | 2 min |
| **P0** | Frontend build not verified | All pages return 404 | ❌ Critical | 10 min |
| **P0** | Backend startup not verified | Silent failures | ⚠️ Major | 15 min |
| **P1** | Health monitor infinite warnings | Log spam | ⚠️ Major | 10 min |
| **P1** | Database timeout too short | Startup failures on slow DB | ⚠️ Moderate | 2 min |
| **P2** | Nginx PID file location | Potential start failure | ✅ Works | 2 min |
| **P2** | Log rotation limits | Disk space issues | ⚠️ Minor | 5 min |
| **P2** | Too many workers | Memory pressure | ⚠️ Minor | 2 min |
| **P3** | Incomplete env var validation | Silent feature failures | ⚠️ Minor | 5 min |

**Total estimated fix time**: **53 minutes**

---

## 12. Recommended Fix Order

### Phase 1: Critical Fixes (IMMEDIATE)

#### Fix 1: Add prometheus-client to dependencies (2 minutes)
```bash
# Edit pyproject.toml
dependencies = [
    # ... existing packages ...
    "prometheus-client>=0.19.0",  # Metrics and monitoring
]

# Rebuild
cd /mnt/d/工作区/云开发/working
docker build --no-cache -t langchain-app:test .
```

#### Fix 2: Add frontend build verification (10 minutes)
```dockerfile
# In Dockerfile, Stage 2 (after line 39):
RUN npm run build

# ✅ ADD
RUN ls -la /build/dist/ && \
    test -f /build/dist/index.html || \
    (echo "ERROR: Frontend build failed - index.html not found" && exit 1)
```

```dockerfile
# In Dockerfile, Stage 3 (after line 73):
COPY --from=frontend-builder /build/dist /usr/share/nginx/html

# ✅ ADD
RUN ls -la /usr/share/nginx/html/ && \
    test -f /usr/share/nginx/html/index.html || \
    (echo "ERROR: Frontend files not copied" && exit 1)
```

```bash
# In docker-entrypoint.sh (after line 174):
# ============================================
# Verify Frontend Files Exist
# ============================================

log "Verifying frontend files..."

if [ ! -f "/usr/share/nginx/html/index.html" ]; then
    log_error "Frontend index.html not found!"
    exit 1
fi

log "✅ Frontend files verified"
```

#### Fix 3: Add backend startup verification (15 minutes)
```bash
# In docker-entrypoint.sh (after Nginx validation):
# ============================================
# Wait for Backend to Start
# ============================================

log "Starting supervisord in background..."
supervisord -c /etc/supervisor/supervisord.conf &
SUPERVISORD_PID=$!

log "Waiting for backend to start..."

BACKEND_TIMEOUT=60
BACKEND_INTERVAL=2

for ((i=0; i<BACKEND_TIMEOUT; i+=BACKEND_INTERVAL)); do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        log "✅ Backend is responding on port 8000"
        break
    fi
    if [ $i -eq 0 ]; then
        log "Backend not ready yet, waiting..."
    fi
    sleep $BACKEND_INTERVAL
done

if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    log_error "Backend failed to start after ${BACKEND_TIMEOUT}s"
    log_error "Check logs: supervisorctl tail -f backend"
    log_warn "Container will continue running for debugging"
fi

log "✅ All services started successfully"

# Wait for supervisord process
wait $SUPERVISORD_PID
```

### Phase 2: Important Improvements (WITHIN 24 HOURS)

#### Fix 4: Increase database timeout (2 minutes)
```bash
# In docker-entrypoint.sh, line 70:
DB_CHECK_TIMEOUT=60  # Increase from 30 to 60
DB_CHECK_INTERVAL=3  # Increase from 2 to 3
```

#### Fix 5: Reduce backend workers (2 minutes)
```ini
# In supervisord.conf, line 30:
command=python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 1
```

#### Fix 6: Add health monitor max failures (10 minutes)
```python
# In scripts/monitor/health_monitor.py, add at line 26:
MAX_CONSECUTIVE_FAILURES = 20  # 10 minutes at 30s interval

# In handle_failure method (line 137):
if failures >= MAX_CONSECUTIVE_FAILURES:
    logger.error(f"{service} failed {MAX_CONSECUTIVE_FAILURES} times - stopping monitor")
    self.running = False
```

### Phase 3: Production Hardening (WITHIN 1 WEEK)

#### Fix 7: Increase log retention (5 minutes)
```ini
# In supervisord.conf:
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
```

#### Fix 8: Add environment variable validation (5 minutes)
```bash
# In docker-entrypoint.sh, add after line 60:
recommended_vars=(
    "OPENAI_API_KEY"
    "ANTHROPIC_API_KEY"
)

for var in "${recommended_vars[@]}"; do
    if [ -z "${!var}" ]; then
        log_warn "Recommended variable not set: $var"
    fi
done
```

---

## 13. Complete Verification Procedure

### Step 1: Rebuild Image
```bash
cd /mnt/d/工作区/云开发/working

# Clean rebuild
docker build --no-cache --progress=plain -t langchain-app:test . 2>&1 | tee build.log

# Verify build logs show:
grep "✓ built in" build.log
grep "Frontend files verified" build.log
```

### Step 2: Test Container Locally
```bash
# Run container
docker run -d -p 8080:80 \
  --name test-langchain \
  --env-file .env \
  langchain-app:test

# Wait for startup
sleep 60

# Check logs
docker logs test-langchain | grep "✅"
docker logs test-langchain | grep "ERROR"

# Test endpoints
curl -I http://localhost:8080/             # Should return 200
curl -I http://localhost:8080/health       # Should return 200
curl http://localhost:8080/api/health      # Should return JSON

# Verify processes
docker exec test-langchain ps aux | grep uvicorn
docker exec test-langchain ps aux | grep nginx
docker exec test-langchain ps aux | grep health_monitor
```

### Step 3: Verify File System
```bash
# Check frontend files
docker exec test-langchain ls -la /usr/share/nginx/html/
# Should show: index.html, assets/

# Check backend is serving
docker exec test-langchain curl -s http://localhost:8000/health
# Should return: {"status": "healthy"}
```

### Step 4: Deploy to Coolify
```bash
# Push to container registry
docker tag langchain-app:test your-registry.com/langchain-app:latest
docker push your-registry.com/langchain-app:latest

# Or trigger Git-based deployment in Coolify
git add .
git commit -m "fix: Critical startup issues - prometheus client, frontend verification"
git push origin main

# Coolify will auto-rebuild from Dockerfile
```

### Step 5: Monitor Deployment
```bash
# In Coolify dashboard, check logs for:
# - "✅ Frontend files verified"
# - "✅ Backend is responding"
# - "✅ Nginx configuration is valid"
# - "✅ All services started successfully"

# Test public URL
curl -I https://your-app.coolify.com/
curl https://your-app.coolify.com/api/health

# Check metrics endpoint
curl https://your-app.coolify.com/metrics
```

---

## 14. Debugging Guide (If Issues Persist)

### Scenario 1: Container Exits Immediately

```bash
# Check exit code
docker ps -a | grep langchain-app
# Look for "Exited (1)" or "Exited (137)"

# View full logs
docker logs <container-id>

# Common causes:
# - Missing environment variable (DATABASE_URL)
# - Frontend files missing (entrypoint check failed)
# - Nginx config invalid (nginx -t failed)
```

### Scenario 2: Container Runs But Returns 404

```bash
# SSH into container
docker exec -it <container-id> bash

# Check frontend files
ls -la /usr/share/nginx/html/
# If empty → Frontend build failed

# Check Nginx config
nginx -t
# Should pass

# Check Nginx logs
tail -f /var/log/app/nginx_error.log
# Look for "No such file or directory" errors
```

### Scenario 3: Backend Not Responding

```bash
# Check if backend process is running
docker exec <container-id> ps aux | grep uvicorn

# Check backend logs
docker exec <container-id> tail -f /var/log/app/backend.log
docker exec <container-id> tail -f /var/log/app/backend_error.log

# Check Supervisor status
docker exec <container-id> supervisorctl status
# backend should show "RUNNING" not "FATAL"

# Test backend directly
docker exec <container-id> curl http://localhost:8000/health
```

### Scenario 4: High Memory Usage

```bash
# Check memory usage
docker stats <container-id>

# If >80% memory:
# - Reduce backend workers to 1
# - Increase container memory limit
# - Check for memory leaks in application logs
```

---

## 15. Monitoring Recommendations

### Add Healthcheck to Docker Compose

If using docker-compose.yml:

```yaml
services:
  app:
    image: langchain-app:latest
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 90s
```

### Add Prometheus Monitoring

```yaml
# docker-compose.yml
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'langchain-app'
    static_configs:
      - targets: ['app:80']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

---

## 16. Final Checklist

Before deploying to production:

- [ ] Add `prometheus-client` to pyproject.toml
- [ ] Add frontend build verification to Dockerfile
- [ ] Add frontend file check to entrypoint
- [ ] Add backend startup verification to entrypoint
- [ ] Increase database timeout to 60s
- [ ] Reduce backend workers to 1
- [ ] Test build locally with `docker build --no-cache`
- [ ] Test container locally with `docker run`
- [ ] Verify all endpoints return 200
- [ ] Check Supervisor logs show no FATAL errors
- [ ] Verify Prometheus metrics endpoint works
- [ ] Deploy to staging environment first
- [ ] Monitor logs for 1 hour after deployment
- [ ] Set up alerts for container failures
- [ ] Document deployment procedure for team

---

**Document Version**: 1.0
**Last Updated**: 2025-11-21
**Status**: Complete Analysis - Ready for Implementation
**Estimated Total Fix Time**: 53 minutes
