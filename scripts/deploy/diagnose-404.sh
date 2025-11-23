#!/bin/bash
# Diagnostic script for 404 page not found issue in Coolify deployment

set -e

APP_URL="${1:-http://zogcwskg8s0okw4c0wk0kscg.47.79.87.199.sslip.io}"

echo "============================================"
echo "Coolify Deployment 404 Diagnostic Tool"
echo "============================================"
echo ""
echo "App URL: $APP_URL"
echo ""

# 1. Check HTTP response
echo "1. Checking HTTP Response Headers..."
curl -s -I "$APP_URL/" | head -10
echo ""

# 2. Check health endpoint
echo "2. Checking Health Endpoint..."
curl -s -I "$APP_URL/health"
echo ""

# 3. Check API endpoint
echo "3. Checking API Endpoint..."
curl -s -I "$APP_URL/api/conversations"
echo ""

# 4. Check if it's returning HTML or plain text
echo "4. Checking Root Path Response Content..."
curl -s "$APP_URL/" | head -20
echo ""

# 5. Check if Nginx is responding
echo "5. Checking Server Header..."
curl -s -I "$APP_URL/" | grep -i "server:"
echo ""

# 6. Common issues checklist
echo "============================================"
echo "Common Issues Checklist:"
echo "============================================"
echo ""
echo "Issue 1: Frontend build directory not copied to /usr/share/nginx/html"
echo "  - Check Dockerfile stage 3: COPY --from=frontend-builder /build/dist /usr/share/nginx/html"
echo ""
echo "Issue 2: Frontend build failed (npm run build)"
echo "  - Check GitHub Actions build logs for frontend-builder stage"
echo ""
echo "Issue 3: Nginx root directory misconfigured"
echo "  - Check nginx.conf: root /usr/share/nginx/html;"
echo ""
echo "Issue 4: /usr/share/nginx/html is empty"
echo "  - Docker build didn't copy frontend files"
echo "  - Frontend dist directory was empty"
echo ""
echo "Issue 5: Coolify serving wrong container/image"
echo "  - Check Coolify deployment logs"
echo "  - Verify correct image tag is deployed"
echo ""
echo "Issue 6: Nginx not started or crashed"
echo "  - Check Supervisor logs in container"
echo "  - Verify Nginx process is running"
echo ""

# 7. Recommended debugging commands
echo "============================================"
echo "Recommended Next Steps:"
echo "============================================"
echo ""
echo "1. SSH into Coolify server and check container logs:"
echo "   docker ps | grep zogcwskg8s0okw4c0wk0kscg"
echo "   docker logs <container-id>"
echo ""
echo "2. Check if /usr/share/nginx/html has files:"
echo "   docker exec <container-id> ls -la /usr/share/nginx/html"
echo ""
echo "3. Check Supervisor status:"
echo "   docker exec <container-id> supervisorctl status"
echo ""
echo "4. Check Nginx error logs:"
echo "   docker exec <container-id> cat /var/log/app/nginx_error.log"
echo ""
echo "5. Rebuild Docker image locally to verify build:"
echo "   docker build -t test-build ."
echo "   docker run -p 8080:80 -e DATABASE_URL=postgresql://... test-build"
echo "   curl http://localhost:8080/"
echo ""
