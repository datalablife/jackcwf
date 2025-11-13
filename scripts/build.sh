#!/bin/bash
# Build Docker image for production deployment
# This script builds and optionally pushes the Docker image to a registry

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
║                   Docker Image Builder                       ║
║                                                              ║
║  Build production-ready Docker images                        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF

echo ""

# =============================================================================
# Configuration
# =============================================================================

# Get version from git tag or use 'latest'
VERSION="${VERSION:-$(git describe --tags --always 2>/dev/null || echo 'latest')}"

# Image configuration
IMAGE_NAME="${IMAGE_NAME:-working}"
REGISTRY="${DOCKER_REGISTRY:-}"  # e.g., docker.io/username or ghcr.io/username

# Build full image name
if [ -n "$REGISTRY" ]; then
    FULL_IMAGE_NAME="$REGISTRY/$IMAGE_NAME"
else
    FULL_IMAGE_NAME="$IMAGE_NAME"
fi

# Parse command line arguments
PUSH=false
PLATFORM=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --push)
            PUSH=true
            shift
            ;;
        --platform)
            PLATFORM="$2"
            shift 2
            ;;
        --version)
            VERSION="$2"
            shift 2
            ;;
        --registry)
            REGISTRY="$2"
            FULL_IMAGE_NAME="$REGISTRY/$IMAGE_NAME"
            shift 2
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Usage: $0 [--push] [--platform PLATFORM] [--version VERSION] [--registry REGISTRY]"
            exit 1
            ;;
    esac
done

# =============================================================================
# Display Configuration
# =============================================================================

log_info "Build configuration:"
log_info "  Image name: $FULL_IMAGE_NAME"
log_info "  Version: $VERSION"
log_info "  Platform: ${PLATFORM:-auto}"
log_info "  Push: $PUSH"
echo ""

# =============================================================================
# Pre-build Checks
# =============================================================================

log_step "Running pre-build checks..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed"
    exit 1
fi
log_info "Docker is installed"

# Check if Dockerfile exists
if [ ! -f "Dockerfile" ]; then
    log_error "Dockerfile not found in $PROJECT_ROOT"
    exit 1
fi
log_info "Dockerfile found"

# Check if required files exist
REQUIRED_FILES=("pyproject.toml" "uv.lock" "rxconfig.py")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        log_error "Required file not found: $file"
        exit 1
    fi
done
log_info "All required files present"

# =============================================================================
# Build Docker Image
# =============================================================================

log_step "Building Docker image..."

BUILD_ARGS=(
    -t "$FULL_IMAGE_NAME:$VERSION"
    -t "$FULL_IMAGE_NAME:latest"
)

# Add platform if specified
if [ -n "$PLATFORM" ]; then
    BUILD_ARGS+=(--platform "$PLATFORM")
fi

# Add build metadata
BUILD_ARGS+=(
    --build-arg "BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    --build-arg "VERSION=$VERSION"
    --build-arg "GIT_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo 'unknown')"
)

log_info "Running docker build..."
echo ""

if docker build "${BUILD_ARGS[@]}" .; then
    log_info "Docker image built successfully"
else
    log_error "Docker build failed"
    exit 1
fi

# =============================================================================
# Display Image Information
# =============================================================================

log_step "Image information:"

docker images "$FULL_IMAGE_NAME" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

echo ""

# =============================================================================
# Push to Registry (if requested)
# =============================================================================

if [ "$PUSH" = true ]; then
    log_step "Pushing image to registry..."

    if [ -z "$REGISTRY" ]; then
        log_error "Cannot push: No registry specified (use --registry or set DOCKER_REGISTRY)"
        exit 1
    fi

    log_info "Pushing $FULL_IMAGE_NAME:$VERSION..."
    if docker push "$FULL_IMAGE_NAME:$VERSION"; then
        log_info "Pushed $FULL_IMAGE_NAME:$VERSION"
    else
        log_error "Failed to push $FULL_IMAGE_NAME:$VERSION"
        exit 1
    fi

    log_info "Pushing $FULL_IMAGE_NAME:latest..."
    if docker push "$FULL_IMAGE_NAME:latest"; then
        log_info "Pushed $FULL_IMAGE_NAME:latest"
    else
        log_error "Failed to push $FULL_IMAGE_NAME:latest"
        exit 1
    fi

    log_info "All images pushed successfully"
fi

# =============================================================================
# Summary
# =============================================================================

log_step "Build complete!"

echo ""
log_info "Built images:"
log_info "  $FULL_IMAGE_NAME:$VERSION"
log_info "  $FULL_IMAGE_NAME:latest"

if [ "$PUSH" = true ]; then
    echo ""
    log_info "Images have been pushed to registry: $REGISTRY"
fi

echo ""
log_info "Next steps:"
log_info "  1. Test locally: ./scripts/test-docker.sh $VERSION"
log_info "  2. Deploy to Coolify (it will auto-build on push)"

if [ "$PUSH" = false ]; then
    log_info "  3. To push to registry: $0 --push --registry YOUR_REGISTRY"
fi

echo ""
