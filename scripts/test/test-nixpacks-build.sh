#!/bin/bash
# Test script to validate Nixpacks build before Coolify deployment
# This simulates exactly how Coolify will build the application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=================================================="
echo "Nixpacks Build Test for Reflex Application"
echo "=================================================="
echo ""

# Configuration
IMAGE_NAME="reflex-nixpacks-test"
CONTAINER_NAME="reflex-nixpacks-container"
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

echo "Project root: $PROJECT_ROOT"
echo ""

# Step 1: Check if Nixpacks is installed
echo -e "${YELLOW}Step 1: Checking Nixpacks installation...${NC}"
if ! command -v nixpacks &> /dev/null; then
    echo -e "${RED}✗ Nixpacks not found${NC}"
    echo ""
    echo "To install Nixpacks:"
    echo "  curl -sSL https://nixpacks.com/install.sh | bash"
    echo ""
    exit 1
fi

NIXPACKS_VERSION=$(nixpacks --version)
echo -e "${GREEN}✓ Nixpacks installed: $NIXPACKS_VERSION${NC}"
echo ""

# Step 2: Clean up previous test
echo -e "${YELLOW}Step 2: Cleaning up previous test containers...${NC}"
docker rm -f $CONTAINER_NAME 2>/dev/null || true
docker rmi $IMAGE_NAME 2>/dev/null || true
echo -e "${GREEN}✓ Cleanup complete${NC}"
echo ""

# Step 3: Build with Nixpacks
echo -e "${YELLOW}Step 3: Building with Nixpacks...${NC}"
cd "$PROJECT_ROOT"

echo "Using nixpacks.toml configuration:"
echo "=================================================="
cat nixpacks.toml
echo "=================================================="
echo ""

if nixpacks build . --name $IMAGE_NAME; then
    echo -e "${GREEN}✓ Nixpacks build successful${NC}"
else
    echo -e "${RED}✗ Nixpacks build failed${NC}"
    echo ""
    echo "This means your nixpacks.toml has issues."
    echo "Fix the configuration and try again."
    exit 1
fi
echo ""

# Step 4: Inspect the generated plan
echo -e "${YELLOW}Step 4: Nixpacks build plan:${NC}"
echo "=================================================="
nixpacks plan .
echo "=================================================="
echo ""

# Step 5: Run container
echo -e "${YELLOW}Step 5: Starting container...${NC}"
docker run -d \
    --name $CONTAINER_NAME \
    -p 3002:3000 \
    -p 8002:8000 \
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

# Step 6: Monitor container startup
echo -e "${YELLOW}Step 6: Monitoring container startup...${NC}"
echo "Waiting for application to start (showing logs):"
echo "=================================================="

# Show logs in real-time for 60 seconds
timeout 60 docker logs -f $CONTAINER_NAME &
LOGS_PID=$!

# Wait and check if container is still running
sleep 60
kill $LOGS_PID 2>/dev/null || true

echo "=================================================="
echo ""

if ! docker ps | grep -q $CONTAINER_NAME; then
    echo -e "${RED}✗ Container exited unexpectedly${NC}"
    echo ""
    echo "Full container logs:"
    echo "=================================================="
    docker logs $CONTAINER_NAME
    echo "=================================================="
    exit 1
fi

echo -e "${GREEN}✓ Container still running after 60 seconds${NC}"
echo ""

# Step 7: Test endpoints
echo -e "${YELLOW}Step 7: Testing endpoints...${NC}"

# Test frontend
echo -n "Testing frontend (http://localhost:3002)... "
if curl -f -s http://localhost:3002/ > /dev/null; then
    echo -e "${GREEN}✓ Frontend responding${NC}"
else
    echo -e "${RED}✗ Frontend not responding${NC}"
    FRONTEND_FAILED=1
fi

# Test backend
echo -n "Testing backend (http://localhost:8002)... "
if curl -f -s http://localhost:8002/ > /dev/null; then
    echo -e "${GREEN}✓ Backend responding${NC}"
else
    echo -e "${RED}✗ Backend not responding${NC}"
    BACKEND_FAILED=1
fi

echo ""

# Step 8: Image size comparison
echo -e "${YELLOW}Step 8: Image information:${NC}"
docker images $IMAGE_NAME --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
echo ""

# Step 9: Container inspection
echo -e "${YELLOW}Step 9: Container details:${NC}"
echo "Health status: $(docker inspect --format='{{.State.Health.Status}}' $CONTAINER_NAME 2>/dev/null || echo 'No health check')"
echo "Started at: $(docker inspect --format='{{.State.StartedAt}}' $CONTAINER_NAME)"
echo ""

# Step 10: Resource usage
echo -e "${YELLOW}Step 10: Container resource usage:${NC}"
docker stats $CONTAINER_NAME --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
echo ""

# Step 11: Summary
echo "=================================================="
echo "Test Summary"
echo "=================================================="

if [ -z "$FRONTEND_FAILED" ] && [ -z "$BACKEND_FAILED" ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "Your Nixpacks configuration is working correctly."
    echo "This is exactly how Coolify will build and run your app."
    echo ""
    echo "Access URLs (while running):"
    echo "  - Frontend: http://localhost:3002"
    echo "  - Backend: http://localhost:8002"
    echo "  - API Docs: http://localhost:8002/docs"
    echo ""
    echo "Next steps:"
    echo "  1. Commit and push nixpacks.toml to Git"
    echo "  2. Configure Coolify as per COOLIFY_CONFIG.md"
    echo "  3. Deploy to Coolify"
    echo ""
    echo "To stop the test container:"
    echo "  docker stop $CONTAINER_NAME"
    echo "  docker rm $CONTAINER_NAME"
    EXIT_CODE=0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    echo ""
    echo "Issues detected with Nixpacks build."
    echo "Please fix nixpacks.toml before deploying to Coolify."
    echo ""
    echo "Check the logs above for specific errors."
    EXIT_CODE=1
fi

echo ""
echo "=================================================="

exit $EXIT_CODE
