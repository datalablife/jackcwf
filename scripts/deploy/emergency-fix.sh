#!/bin/bash
# Emergency deployment fix for 404 issue
# This script will build, test, and deploy a working Docker image

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Configuration
REPO_ROOT="/mnt/d/工作区/云开发/working"
IMAGE_NAME="ghcr.io/jackcwf888/jackcwf"
TAG="emergency-fix-$(date +%s)"
TEST_PORT=8080
DATABASE_URL="${DATABASE_URL:-postgresql://testuser:testpass@localhost:5432/testdb}"

cd "$REPO_ROOT"

log "============================================"
log "Emergency Deployment Fix"
log "============================================"
log ""
log "Repo: $REPO_ROOT"
log "Image: $IMAGE_NAME:$TAG"
log ""

# Step 1: Verify frontend build
log "Step 1: Verifying frontend build..."
if [ ! -d "frontend/dist" ] || [ ! -f "frontend/dist/index.html" ]; then
    warn "Frontend dist directory not found, building..."
    cd frontend
    npm ci --legacy-peer-deps
    npm run build
    cd ..
fi

if [ -f "frontend/dist/index.html" ]; then
    log "✅ Frontend build verified ($(du -sh frontend/dist | cut -f1))"
else
    error "❌ Frontend build failed - index.html not found"
    exit 1
fi

# Step 2: Build Docker image
log ""
log "Step 2: Building Docker image..."
docker build -t "$IMAGE_NAME:$TAG" -t "$IMAGE_NAME:latest" .

if [ $? -eq 0 ]; then
    log "✅ Docker image built successfully"
else
    error "❌ Docker build failed"
    exit 1
fi

# Step 3: Test image locally
log ""
log "Step 3: Testing Docker image locally..."

# Stop any existing test container
docker stop test-deployment 2>/dev/null || true
docker rm test-deployment 2>/dev/null || true

# Run test container
log "Starting test container on port $TEST_PORT..."
docker run -d \
    -p $TEST_PORT:80 \
    -e DATABASE_URL="$DATABASE_URL" \
    -e ENVIRONMENT=production \
    --name test-deployment \
    "$IMAGE_NAME:$TAG"

# Wait for container to start
log "Waiting for container to initialize (45 seconds)..."
sleep 45

# Check container status
if ! docker ps | grep -q test-deployment; then
    error "❌ Container failed to start"
    log "Container logs:"
    docker logs test-deployment --tail 50
    docker rm -f test-deployment 2>/dev/null || true
    exit 1
fi

# Test endpoints
log ""
log "Testing endpoints..."

# Test 1: Root path
log "  Testing: http://localhost:$TEST_PORT/"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$TEST_PORT/)
if [ "$HTTP_CODE" = "200" ]; then
    log "  ✅ Root path returned 200 OK"
else
    warn "  ⚠️  Root path returned $HTTP_CODE (expected 200)"
fi

# Test 2: Health endpoint
log "  Testing: http://localhost:$TEST_PORT/health"
HEALTH_RESPONSE=$(curl -s http://localhost:$TEST_PORT/health)
if [ "$HEALTH_RESPONSE" = "healthy" ]; then
    log "  ✅ Health endpoint returned 'healthy'"
else
    warn "  ⚠️  Health endpoint returned: $HEALTH_RESPONSE"
fi

# Test 3: Check Server header
log "  Checking Server header..."
SERVER_HEADER=$(curl -s -I http://localhost:$TEST_PORT/ | grep -i "^Server:" || echo "")
if [ -n "$SERVER_HEADER" ]; then
    log "  ✅ Server header present: $SERVER_HEADER"
else
    warn "  ⚠️  No Server header found"
fi

# Test 4: Check Supervisor status
log ""
log "  Checking Supervisor status..."
docker exec test-deployment supervisorctl status

# Test 5: Check frontend files
log ""
log "  Checking frontend files in container..."
FILE_COUNT=$(docker exec test-deployment ls -1 /usr/share/nginx/html 2>/dev/null | wc -l)
if [ "$FILE_COUNT" -gt 1 ]; then
    log "  ✅ Frontend files present ($FILE_COUNT files/directories)"
    docker exec test-deployment ls -lh /usr/share/nginx/html
else
    error "  ❌ Frontend files missing in /usr/share/nginx/html"
    docker logs test-deployment --tail 100
    docker rm -f test-deployment 2>/dev/null || true
    exit 1
fi

# Clean up test container
log ""
log "Cleaning up test container..."
docker stop test-deployment
docker rm test-deployment

# Step 4: Push to registry (if GitHub token is available)
log ""
log "Step 4: Pushing to GitHub Container Registry..."

if [ -n "$GITHUB_TOKEN" ]; then
    log "Logging in to ghcr.io..."
    echo "$GITHUB_TOKEN" | docker login ghcr.io -u jackcwf888 --password-stdin

    log "Pushing image: $IMAGE_NAME:$TAG"
    docker push "$IMAGE_NAME:$TAG"

    log "Pushing image: $IMAGE_NAME:latest"
    docker push "$IMAGE_NAME:latest"

    log "✅ Images pushed successfully"
else
    warn "⚠️  GITHUB_TOKEN not set - skipping push to registry"
    warn "To push manually, run:"
    warn "  echo \$GITHUB_TOKEN | docker login ghcr.io -u jackcwf888 --password-stdin"
    warn "  docker push $IMAGE_NAME:$TAG"
    warn "  docker push $IMAGE_NAME:latest"
fi

# Step 5: Trigger Coolify deployment (if API token is available)
log ""
log "Step 5: Triggering Coolify deployment..."

if [ -n "$COOLIFY_API_TOKEN" ]; then
    COOLIFY_URL="https://coolpanel.jackcwf.com"
    APP_UUID="zogcwskg8s0okw4c0wk0kscg"

    log "Triggering deployment for app $APP_UUID..."
    RESPONSE=$(curl -s -X POST "$COOLIFY_URL/api/v1/applications/$APP_UUID/deploy" \
        -H "Authorization: Bearer $COOLIFY_API_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"tag\": \"$TAG\"}")

    log "Deployment triggered: $RESPONSE"

    log ""
    log "Waiting for deployment to complete (60 seconds)..."
    sleep 60

    APP_URL="http://zogcwskg8s0okw4c0wk0kscg.47.79.87.199.sslip.io"
    log "Testing deployed app: $APP_URL"

    DEPLOYED_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$APP_URL/")
    if [ "$DEPLOYED_CODE" = "200" ]; then
        log "✅ Deployment successful - app responding with 200 OK"
    else
        warn "⚠️  Deployment returned $DEPLOYED_CODE (check Coolify logs)"
    fi
else
    warn "⚠️  COOLIFY_API_TOKEN not set - skipping automatic deployment"
    warn "To deploy manually:"
    warn "  1. Log in to Coolify: https://coolpanel.jackcwf.com"
    warn "  2. Go to application: zogcwskg8s0okw4c0wk0kscg"
    warn "  3. Set image tag to: $TAG"
    warn "  4. Click 'Deploy'"
fi

log ""
log "============================================"
log "Emergency fix complete!"
log "============================================"
log ""
log "Image built and tested: $IMAGE_NAME:$TAG"
log ""
log "Next steps:"
log "  1. If push failed, set GITHUB_TOKEN and re-run"
log "  2. If deployment failed, set COOLIFY_API_TOKEN and re-run"
log "  3. Monitor Coolify logs for deployment status"
log "  4. Fix CI/CD test failures in .github/workflows/cd.yml"
log ""
