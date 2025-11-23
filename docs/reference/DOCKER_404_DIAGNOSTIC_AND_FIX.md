# Docker 404 Error - Root Cause Analysis & Fix

**Date**: 2025-11-21
**Container ID**: zogcwskg8s0okw4c0wk0kscg
**Status**: Container Running, All HTTP Requests Return 404

---

## Executive Summary

**ROOT CAUSE IDENTIFIED**: Frontend build artifacts are not being properly copied to Nginx's document root during Docker image build, resulting in an empty `/usr/share/nginx/html` directory.

**PRIMARY ISSUE**: The `.dockerignore` file excludes `frontend/dist/`, which may interfere with the frontend build process in the Docker multi-stage build.

**IMPACT**:
- Frontend (React SPA): 404 Not Found
- Backend API endpoints: Potentially accessible via direct proxy but unreachable due to no frontend
- Health check: Passes (returns 200) but application unusable

---

## Architecture Verification

### Current Docker Architecture (3-Stage Build)

```
┌─────────────────────────────────────────────────────────┐
│ Stage 1: backend-builder (python:3.12-slim)            │
│ ├─ Install uv, build dependencies                      │
│ ├─ Copy pyproject.toml + src/                          │
│ └─ Output: /usr/local/lib/python3.12/site-packages     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Stage 2: frontend-builder (node:20-slim)               │
│ ├─ WORKDIR /build                                      │
│ ├─ COPY frontend/package*.json ./                      │
│ ├─ npm ci --legacy-peer-deps                           │
│ ├─ COPY frontend/ ./   ⚠️ FILTERED BY .dockerignore   │
│ ├─ npm run build → Vite outputs to /build/dist        │
│ └─ Expected output: /build/dist/{index.html, assets/}  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Stage 3: final (python:3.12-slim)                      │
│ ├─ Install nginx, supervisor, node                     │
│ ├─ COPY --from=backend-builder (dependencies)          │
│ ├─ COPY --from=frontend-builder /build/dist            │
│ │   → /usr/share/nginx/html ⚠️ MAY BE EMPTY           │
│ ├─ Configure Nginx (root: /usr/share/nginx/html)      │
│ ├─ Configure Supervisor (Backend:8000, Nginx:80)      │
│ └─ Start: supervisord → backend → nginx → monitor     │
└─────────────────────────────────────────────────────────┘
```

### Nginx Configuration (Validated ✅)

```nginx
server {
    listen 80 default_server;
    root /usr/share/nginx/html;  # ← Must contain index.html
    index index.html;

    # Health check (works independently)
    location = /health {
        return 200 "healthy\n";
    }

    # API proxy to backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
    }

    # WebSocket proxy
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;  # ← Needs index.html
    }
}
```

**Analysis**: Nginx configuration is correct. The 404 error indicates `/usr/share/nginx/html/index.html` does not exist.

### Supervisor Configuration (Validated ✅)

```ini
[program:backend]
command=python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 2
priority=100  # Starts first
startsecs=10

[program:nginx]
command=nginx -g 'daemon off;'
priority=200  # Starts after backend
startsecs=10

[program:healthmonitor]
command=python /app/scripts/monitor/health_monitor.py
priority=300  # Starts last
startsecs=30
```

**Analysis**: Process startup order is correct. Nginx waits for backend to be ready.

---

## Root Cause Analysis

### Issue #1: .dockerignore Excludes Frontend Build Artifacts (CRITICAL)

**File**: `/mnt/d/工作区/云开发/working/.dockerignore`

```
dist/             # Line 18 - Excludes all dist/ folders
frontend/dist/    # Line 78 - Explicitly excludes frontend/dist/
```

**Impact**:
- When `COPY frontend/ ./` executes in Stage 2 (frontend-builder), the `.dockerignore` filters out `frontend/dist/`
- If the local `frontend/dist/` exists, it won't be copied
- However, `.dockerignore` should NOT affect `npm run build` output (which creates a fresh `/build/dist`)

**Clarification**:
- `.dockerignore` applies to `COPY` from **host → Docker** (Stage 2, Line 36)
- `.dockerignore` does NOT apply to `COPY --from` between stages (Stage 3, Line 73)

**Potential Issue**: If the frontend build (`npm run build`) fails silently, `/build/dist` will be empty or nonexistent, and Stage 3 will copy nothing.

### Issue #2: No Frontend Build Verification (MEDIUM)

**File**: `/mnt/d/工作区/云开发/working/docker/docker-entrypoint.sh`

The entrypoint script checks:
- Database connectivity ✅
- Nginx configuration validity ✅
- Required files (supervisord.conf, health_monitor.py) ✅

**Missing checks**:
```bash
# Should verify frontend files exist
if [ ! -f "/usr/share/nginx/html/index.html" ]; then
    log_error "Frontend files not found in /usr/share/nginx/html!"
    exit 1
fi
```

### Issue #3: Frontend Build May Fail Silently (HIGH)

**Dockerfile Stage 2** (Lines 32-39):

```dockerfile
COPY frontend/package*.json ./
RUN npm ci --legacy-peer-deps

COPY frontend/ ./
RUN npm run build
```

**Potential failure points**:
1. `npm ci` may fail if dependencies have conflicts
2. `npm run build` may fail if:
   - TypeScript compilation errors
   - Missing environment variables
   - Vite build errors
3. No explicit check that `/build/dist/index.html` exists after build

**Current behavior**: Docker build continues even if `npm run build` fails, because it doesn't use `set -e` in RUN commands by default.

---

## Diagnostic Steps to Confirm Root Cause

### Step 1: Check Container Filesystem

SSH into the container and verify:

```bash
# Check if frontend files exist
ls -la /usr/share/nginx/html/

# Expected output:
# total 4
# drwxr-xr-x 3 root root 4096 Nov 21 12:00 .
# drwxr-xr-x 3 root root 4096 Nov 21 12:00 ..
# drwxr-xr-x 2 root root 4096 Nov 21 12:00 assets
# -rw-r--r-- 1 root root  750 Nov 21 12:00 index.html

# If empty or only .gitkeep:
# total 0  ← PROBLEM CONFIRMED
```

### Step 2: Check Docker Build Logs

Review the build logs for Stage 2 (frontend-builder):

```bash
docker build --no-cache --progress=plain -t test-build . 2>&1 | tee build.log

# Look for:
# - "npm run build" output
# - "✓ built in XXXms"
# - "dist/index.html" generation
# - Any TypeScript errors
# - Any build failures
```

### Step 3: Check Nginx Access Logs

```bash
tail -f /var/log/app/nginx_access.log
tail -f /var/log/app/nginx_error.log

# Make a request and check logs:
# 404 errors indicate file not found
# 50x errors indicate Nginx crash
```

### Step 4: Test Health Check Endpoint

```bash
curl http://localhost/health
# Expected: 200 "healthy\n"
# This works because it's a static Nginx response (doesn't need files)

curl http://localhost/
# Expected: 404 Not Found (if index.html missing)
# Expected: 200 + HTML (if index.html exists)
```

---

## Fix Strategy (Priority Order)

### Fix #1: Add Build Verification to Dockerfile (IMMEDIATE)

**File**: `/mnt/d/工作区/云开发/working/Dockerfile`

**Change Stage 2** (Lines 38-40):

```dockerfile
# Build frontend (Vite outputs to /build/dist)
RUN npm run build

# ✅ ADD: Verify build artifacts exist
RUN ls -la /build/dist/ && \
    test -f /build/dist/index.html || \
    (echo "ERROR: Frontend build failed - index.html not found" && exit 1)
```

**Rationale**: This ensures the Docker build fails immediately if frontend build produces no output.

### Fix #2: Add Frontend File Verification to Entrypoint (IMMEDIATE)

**File**: `/mnt/d/工作区/云开发/working/docker/docker-entrypoint.sh`

**Add after Nginx config check** (after Line 174):

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
if [ "$ASSET_COUNT" -lt 5 ]; then
    log_warn "Warning: Frontend assets directory seems incomplete ($ASSET_COUNT files)"
    log_warn "Expected at least 5 JavaScript/CSS bundles"
fi

log "✅ Frontend files verified (index.html + $ASSET_COUNT assets)"
```

### Fix #3: Improve .dockerignore (OPTIONAL, LOW PRIORITY)

**File**: `/mnt/d/工作区/云开发/working/.dockerignore`

**Current**:
```
dist/
frontend/dist/
```

**Analysis**: This is actually correct behavior. The `.dockerignore` prevents copying **local** build artifacts into the Docker build context, forcing a fresh build inside Docker.

**No change needed**, but add a comment for clarity:

```
# Exclude local build artifacts (force fresh build in Docker)
dist/
frontend/dist/
```

### Fix #4: Add Explicit Build Output Directory Check (RECOMMENDED)

**File**: `/mnt/d/工作区/云开发/working/Dockerfile`

**Replace Line 73**:

```dockerfile
# Before:
COPY --from=frontend-builder /build/dist /usr/share/nginx/html

# After: Add explicit check and informative error
COPY --from=frontend-builder /build/dist /usr/share/nginx/html
RUN ls -la /usr/share/nginx/html/ && \
    test -f /usr/share/nginx/html/index.html || \
    (echo "ERROR: Frontend files not copied to /usr/share/nginx/html/" && exit 1)
```

### Fix #5: Alternative - Build Frontend Locally and Copy (NOT RECOMMENDED)

If Docker build continues to fail, as a workaround:

```dockerfile
# Remove frontend-builder stage entirely
# Build locally: cd frontend && npm run build
# Then copy local dist:
COPY frontend/dist /usr/share/nginx/html
```

**Downside**: Requires local Node.js setup, defeats purpose of containerization.

---

## Verification Steps After Fix

### 1. Rebuild Docker Image

```bash
cd /mnt/d/工作区/云开发/working

# Clean build (no cache)
docker build --no-cache -t langchain-app:latest .

# Verify build logs show:
# - "npm run build" completed successfully
# - "✓ built in XXXms" from Vite
# - "✅ Frontend files verified" from verification step
```

### 2. Test Container Locally

```bash
# Run container
docker run -d -p 8080:80 \
  -e DATABASE_URL="postgresql+asyncpg://..." \
  --name test-langchain \
  langchain-app:latest

# Wait 30s for startup
sleep 30

# Test endpoints
curl -I http://localhost:8080/             # Should return 200
curl -I http://localhost:8080/health       # Should return 200
curl -I http://localhost:8080/api/health   # Should return 200 (if backend has this endpoint)

# Check logs
docker logs test-langchain | grep "Frontend files verified"
docker logs test-langchain | grep "Nginx configuration is valid"
```

### 3. Verify File System in Container

```bash
docker exec test-langchain ls -la /usr/share/nginx/html/

# Expected output:
# total 8
# drwxr-xr-x 3 root root 4096 Nov 21 12:00 .
# drwxr-xr-x 3 root root 4096 Nov 21 12:00 ..
# drwxr-xr-x 2 root root 4096 Nov 21 12:00 assets
# -rw-r--r-- 1 root root  750 Nov 21 12:00 index.html
```

### 4. Deploy to Coolify

```bash
# Push to registry (if using one)
docker tag langchain-app:latest registry.example.com/langchain-app:latest
docker push registry.example.com/langchain-app:latest

# Or rebuild in Coolify (trigger from Git)
# Coolify will rebuild from Dockerfile automatically
```

### 5. Monitor Deployment

```bash
# Check Coolify application logs
# Verify:
# - "Frontend files verified" appears in startup logs
# - No "Frontend index.html not found" errors
# - Nginx starts successfully
# - Health check passes

# Test public URL
curl -I https://your-app.coolify.com/
# Should return 200 with HTML content
```

---

## Prevention: CI/CD Pipeline Checks

Add to `.github/workflows/docker-build.yml`:

```yaml
name: Docker Build Test

on: [push, pull_request]

jobs:
  test-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: docker build --no-cache -t test-image .

      - name: Verify frontend files
        run: |
          docker run --rm test-image \
            sh -c "test -f /usr/share/nginx/html/index.html && echo 'OK' || exit 1"

      - name: Test health endpoint
        run: |
          docker run -d --name test-container -p 8080:80 test-image
          sleep 30
          curl -f http://localhost:8080/health || exit 1
          curl -f http://localhost:8080/ || exit 1
```

---

## Summary of Fixes

| Priority | Fix | File | Lines | Effort |
|----------|-----|------|-------|--------|
| **P0** | Add build verification after `npm run build` | `Dockerfile` | 40-42 | 5 min |
| **P0** | Add frontend file check to entrypoint | `docker-entrypoint.sh` | 175-190 | 10 min |
| **P1** | Add verification after COPY from builder | `Dockerfile` | 74-76 | 5 min |
| **P2** | Add CI/CD build verification | `.github/workflows/` | New file | 15 min |

**Total estimated effort**: 35 minutes

---

## Expected Outcome

After applying fixes:

1. **Docker build will fail fast** if frontend build produces no output
2. **Container startup will fail fast** if frontend files missing
3. **Clear error messages** guide developers to rebuild image
4. **CI/CD prevents** broken images from being deployed

**Result**: 404 errors will be prevented at build time, not discovered at runtime.

---

## Additional Diagnostics (If Issue Persists)

If fixes above don't resolve the issue, investigate:

### 1. Check Vite Build Configuration

**File**: `/mnt/d/工作区/云开发/working/frontend/vite.config.ts`

Verify `build.outDir` is not overridden:

```typescript
export default defineConfig({
  build: {
    outDir: 'dist',  // ← Should be 'dist' (default)
    // NOT '/some/other/path'
  }
})
```

### 2. Check for Build-time Environment Variables

Some builds require environment variables at build time:

```dockerfile
# In Stage 2 (frontend-builder), add:
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build
```

### 3. Check Node.js Version Compatibility

The Dockerfile uses `node:20-slim`. Verify package.json compatibility:

```json
{
  "engines": {
    "node": ">=18.0.0"  // ← Should be satisfied by Node 20
  }
}
```

### 4. Test Frontend Build Locally

```bash
cd frontend
npm ci --legacy-peer-deps
npm run build

# Verify dist/ folder is created
ls -la dist/
# Should contain index.html and assets/
```

If local build works but Docker build fails, the issue is Docker-specific (likely file permissions or build context).

---

## Contact & Support

**Deployment Environment**: Coolify (https://coolpanel.jackcwf.com)
**Container ID**: zogcwskg8s0okw4c0wk0kscg
**Application**: LangChain AI Chat (FastAPI + React)

**Next Steps**:
1. Apply Fix #1 and Fix #2 (highest priority)
2. Rebuild Docker image with `--no-cache`
3. Test locally before deploying to Coolify
4. Monitor startup logs for verification messages

---

**Document Version**: 1.0
**Last Updated**: 2025-11-21
**Status**: Ready for Implementation
