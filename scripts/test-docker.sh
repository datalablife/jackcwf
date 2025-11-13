#!/bin/bash
# Test Docker container locally before deploying to Coolify
# This script builds and runs the production Docker image locally

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "\n${BLUE}==>${NC} $1\n"
}

# =============================================================================
# Banner
# =============================================================================

cat << "EOF"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║              Docker Container Local Testing                  ║
║                                                              ║
║  Test production container before deploying to Coolify       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF

echo ""

# =============================================================================
# Configuration
# =============================================================================

IMAGE_NAME="working"
IMAGE_TAG="${1:-local}"
CONTAINER_NAME="working-test"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
BACKEND_PORT="${BACKEND_PORT:-8000}"

# =============================================================================
# 1. Cleanup Previous Container
# =============================================================================

log_step "Cleaning up previous test container..."

if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    log_info "Stopping and removing existing container..."
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
else
    log_info "No existing container found"
fi

# =============================================================================
# 2. Build Docker Image
# =============================================================================

log_step "Building Docker image..."

log_info "Building ${IMAGE_NAME}:${IMAGE_TAG}..."

if docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .; then
    log_info "Docker image built successfully"

    # Display image size
    IMAGE_SIZE=$(docker images "${IMAGE_NAME}:${IMAGE_TAG}" --format "{{.Size}}")
    log_info "Image size: $IMAGE_SIZE"
else
    log_error "Docker build failed"
    exit 1
fi

# =============================================================================
# 3. Load Environment Variables
# =============================================================================

log_step "Preparing environment variables..."

# Load .env file if it exists
ENV_ARGS=""
if [ -f ".env" ]; then
    log_info "Loading environment variables from .env..."
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ "$key" =~ ^#.*$ ]] && continue
        [[ -z "$key" ]] && continue

        # Remove quotes from value
        value=$(echo "$value" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")

        ENV_ARGS="$ENV_ARGS -e $key=$value"
    done < .env
else
    log_warn ".env file not found, using default environment"
fi

# Override with production settings
ENV_ARGS="$ENV_ARGS -e REFLEX_ENV=production"
ENV_ARGS="$ENV_ARGS -e FRONTEND_PORT=$FRONTEND_PORT"
ENV_ARGS="$ENV_ARGS -e BACKEND_PORT=$BACKEND_PORT"

# =============================================================================
# 4. Run Container
# =============================================================================

log_step "Starting container..."

log_info "Container name: $CONTAINER_NAME"
log_info "Frontend port: $FRONTEND_PORT"
log_info "Backend port: $BACKEND_PORT"
echo ""

# Run container
docker run -d \
    --name "$CONTAINER_NAME" \
    -p "${FRONTEND_PORT}:3000" \
    -p "${BACKEND_PORT}:8000" \
    $ENV_ARGS \
    "${IMAGE_NAME}:${IMAGE_TAG}"

log_info "Container started successfully"

# =============================================================================
# 5. Monitor Container Startup
# =============================================================================

log_step "Monitoring container startup..."

log_info "Waiting for application to be ready (this may take up to 2 minutes)..."
echo ""

# Follow logs for 30 seconds
timeout 30 docker logs -f "$CONTAINER_NAME" 2>&1 || true

echo ""

# =============================================================================
# 6. Health Check
# =============================================================================

log_step "Performing health checks..."

MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f -s "http://localhost:$FRONTEND_PORT/" > /dev/null 2>&1; then
        log_info "Health check passed!"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
        echo -n "."
        sleep 2
    fi
done

echo ""

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    log_error "Health check failed after $MAX_RETRIES attempts"
    log_info "Container logs:"
    docker logs "$CONTAINER_NAME"
    exit 1
fi

# =============================================================================
# 7. Display Information
# =============================================================================

log_step "Container is running!"

echo ""
log_info "Application URLs:"
log_info "  Frontend: http://localhost:$FRONTEND_PORT"
log_info "  Backend:  http://localhost:$BACKEND_PORT"
echo ""
log_info "Useful commands:"
log_info "  View logs:        docker logs -f $CONTAINER_NAME"
log_info "  Stop container:   docker stop $CONTAINER_NAME"
log_info "  Remove container: docker rm $CONTAINER_NAME"
log_info "  Enter container:  docker exec -it $CONTAINER_NAME /bin/bash"
echo ""
log_info "Container details:"
docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
log_warn "Press Ctrl+C to stop following logs, or run: docker logs -f $CONTAINER_NAME"
echo ""

# Follow logs
docker logs -f "$CONTAINER_NAME"
