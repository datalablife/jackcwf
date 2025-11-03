#!/bin/bash
# Test script to validate Docker build before Coolify deployment
# This helps catch issues locally before pushing to production

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=================================================="
echo "Docker Build Test for Reflex Application"
echo "=================================================="
echo ""

# Configuration
IMAGE_NAME="reflex-test"
CONTAINER_NAME="reflex-test-container"
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

echo "Project root: $PROJECT_ROOT"
echo ""

# Step 1: Clean up previous test
echo -e "${YELLOW}Step 1: Cleaning up previous test containers...${NC}"
docker rm -f $CONTAINER_NAME 2>/dev/null || true
docker rmi $IMAGE_NAME 2>/dev/null || true
echo -e "${GREEN}✓ Cleanup complete${NC}"
echo ""

# Step 2: Build Docker image
echo -e "${YELLOW}Step 2: Building Docker image...${NC}"
cd "$PROJECT_ROOT"
if docker build -t $IMAGE_NAME .; then
    echo -e "${GREEN}✓ Docker build successful${NC}"
else
    echo -e "${RED}✗ Docker build failed${NC}"
    exit 1
fi
echo ""

# Step 3: Run container
echo -e "${YELLOW}Step 3: Starting container...${NC}"
docker run -d \
    --name $CONTAINER_NAME \
    -p 3001:3000 \
    -p 8001:8000 \
    -e PYTHONUNBUFFERED=1 \
    -e REFLEX_ENV=production \
    -e FRONTEND_PORT=3000 \
    -e BACKEND_PORT=8000 \
    $IMAGE_NAME

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Container started${NC}"
else
    echo -e "${RED}✗ Container failed to start${NC}"
    exit 1
fi
echo ""

# Step 4: Wait for application to start
echo -e "${YELLOW}Step 4: Waiting for application to start (60 seconds)...${NC}"
for i in {1..60}; do
    echo -n "."
    sleep 1

    # Check if container is still running
    if ! docker ps | grep -q $CONTAINER_NAME; then
        echo ""
        echo -e "${RED}✗ Container exited unexpectedly${NC}"
        echo ""
        echo "Container logs:"
        docker logs $CONTAINER_NAME
        exit 1
    fi
done
echo ""
echo -e "${GREEN}✓ Container still running after 60 seconds${NC}"
echo ""

# Step 5: Show container logs
echo -e "${YELLOW}Step 5: Container logs:${NC}"
echo "=================================================="
docker logs $CONTAINER_NAME
echo "=================================================="
echo ""

# Step 6: Test health checks
echo -e "${YELLOW}Step 6: Testing endpoints...${NC}"

# Test frontend
echo -n "Testing frontend (http://localhost:3001)... "
if curl -f -s http://localhost:3001/ > /dev/null; then
    echo -e "${GREEN}✓ Frontend responding${NC}"
else
    echo -e "${RED}✗ Frontend not responding${NC}"
    FRONTEND_FAILED=1
fi

# Test backend
echo -n "Testing backend (http://localhost:8001)... "
if curl -f -s http://localhost:8001/ > /dev/null; then
    echo -e "${GREEN}✓ Backend responding${NC}"
else
    echo -e "${RED}✗ Backend not responding${NC}"
    BACKEND_FAILED=1
fi

# Test backend docs
echo -n "Testing API docs (http://localhost:8001/docs)... "
if curl -f -s http://localhost:8001/docs > /dev/null; then
    echo -e "${GREEN}✓ API docs responding${NC}"
else
    echo -e "${YELLOW}⚠ API docs not responding (may be expected)${NC}"
fi

echo ""

# Step 7: Container stats
echo -e "${YELLOW}Step 7: Container resource usage:${NC}"
docker stats $CONTAINER_NAME --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
echo ""

# Step 8: Summary
echo "=================================================="
echo "Test Summary"
echo "=================================================="

if [ -z "$FRONTEND_FAILED" ] && [ -z "$BACKEND_FAILED" ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "Your application is ready for Coolify deployment."
    echo ""
    echo "Access URLs (while running):"
    echo "  - Frontend: http://localhost:3001"
    echo "  - Backend: http://localhost:8001"
    echo "  - API Docs: http://localhost:8001/docs"
    echo ""
    echo "To stop the test container:"
    echo "  docker stop $CONTAINER_NAME"
    echo "  docker rm $CONTAINER_NAME"
    EXIT_CODE=0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    echo ""
    echo "Please check the logs above and fix issues before deploying."
    EXIT_CODE=1
fi

echo ""
echo "=================================================="

exit $EXIT_CODE
