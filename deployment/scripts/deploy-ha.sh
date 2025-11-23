#!/bin/bash
# High-Availability Deployment Script
# Deploys the application with multiple replicas and load balancing
#
# Usage:
#   ./deployment/scripts/deploy-ha.sh [OPTIONS]
#
# Options:
#   --replicas N      Number of replicas (default: 3)
#   --platform TYPE   Deployment platform: docker-compose|kubernetes|swarm (default: docker-compose)
#   --build           Build Docker image before deployment
#   --no-cache        Build without cache
#   --health-check    Wait for health checks to pass
#   --rollback        Rollback to previous version
#   --dry-run         Show what would be deployed without actually deploying

set -e

# ============================================
# Configuration
# ============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DEPLOYMENT_DIR="$PROJECT_ROOT/deployment"

REPLICAS=${REPLICAS:-3}
PLATFORM=${PLATFORM:-docker-compose}
BUILD=false
NO_CACHE=false
HEALTH_CHECK=true
ROLLBACK=false
DRY_RUN=false

IMAGE_NAME="jackcwf-backend"
IMAGE_TAG="${IMAGE_TAG:-latest}"
CONTAINER_REGISTRY="${CONTAINER_REGISTRY:-}"

# ============================================
# Colors
# ============================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================
# Logging Functions
# ============================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# ============================================
# Parse Arguments
# ============================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --replicas)
            REPLICAS="$2"
            shift 2
            ;;
        --platform)
            PLATFORM="$2"
            shift 2
            ;;
        --build)
            BUILD=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --health-check)
            HEALTH_CHECK=true
            shift
            ;;
        --rollback)
            ROLLBACK=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            cat << EOF
High-Availability Deployment Script

Usage:
  ./deployment/scripts/deploy-ha.sh [OPTIONS]

Options:
  --replicas N      Number of replicas (default: 3)
  --platform TYPE   Deployment platform: docker-compose|kubernetes|swarm (default: docker-compose)
  --build           Build Docker image before deployment
  --no-cache        Build without cache
  --health-check    Wait for health checks to pass
  --rollback        Rollback to previous version
  --dry-run         Show what would be deployed without actually deploying
  --help            Show this help message

Examples:
  # Deploy with Docker Compose (3 replicas)
  ./deployment/scripts/deploy-ha.sh --replicas 3 --platform docker-compose

  # Deploy with Kubernetes (auto-scaling enabled)
  ./deployment/scripts/deploy-ha.sh --platform kubernetes --build

  # Dry run
  ./deployment/scripts/deploy-ha.sh --dry-run
EOF
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# ============================================
# Validation
# ============================================

log_info "Validating deployment configuration..."

# Check required files
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    log_error ".env file not found. Please create one based on .env.example"
    exit 1
fi

if [ ! -f "$PROJECT_ROOT/Dockerfile" ]; then
    log_error "Dockerfile not found"
    exit 1
fi

# Validate platform
if [[ ! "$PLATFORM" =~ ^(docker-compose|kubernetes|swarm)$ ]]; then
    log_error "Invalid platform: $PLATFORM. Must be: docker-compose, kubernetes, or swarm"
    exit 1
fi

# Validate replicas
if ! [[ "$REPLICAS" =~ ^[0-9]+$ ]] || [ "$REPLICAS" -lt 1 ]; then
    log_error "Invalid replicas count: $REPLICAS. Must be a positive integer"
    exit 1
fi

log_success "Validation passed"

# ============================================
# Build Docker Image (if requested)
# ============================================

if [ "$BUILD" = true ]; then
    log_info "Building Docker image: ${IMAGE_NAME}:${IMAGE_TAG}"

    BUILD_ARGS=""
    if [ "$NO_CACHE" = true ]; then
        BUILD_ARGS="--no-cache"
    fi

    if [ "$DRY_RUN" = false ]; then
        docker build $BUILD_ARGS -t "${IMAGE_NAME}:${IMAGE_TAG}" "$PROJECT_ROOT"
        log_success "Docker image built successfully"

        # Tag and push if registry is specified
        if [ -n "$CONTAINER_REGISTRY" ]; then
            log_info "Pushing to container registry: $CONTAINER_REGISTRY"
            docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${CONTAINER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
            docker push "${CONTAINER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
            log_success "Image pushed to registry"
        fi
    else
        log_info "[DRY RUN] Would build Docker image with: docker build $BUILD_ARGS -t ${IMAGE_NAME}:${IMAGE_TAG}"
    fi
fi

# ============================================
# Deploy Based on Platform
# ============================================

deploy_docker_compose() {
    log_info "Deploying with Docker Compose (${REPLICAS} replicas)..."

    cd "$PROJECT_ROOT"

    if [ "$DRY_RUN" = false ]; then
        # Stop existing containers
        docker-compose -f deployment/docker-compose.ha.yml down

        # Start with specified replicas
        docker-compose -f deployment/docker-compose.ha.yml up -d --scale web=$REPLICAS

        log_success "Docker Compose deployment completed"
    else
        log_info "[DRY RUN] Would run: docker-compose -f deployment/docker-compose.ha.yml up -d --scale web=$REPLICAS"
    fi
}

deploy_kubernetes() {
    log_info "Deploying to Kubernetes..."

    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl not found. Please install kubectl first."
        exit 1
    fi

    if [ "$DRY_RUN" = false ]; then
        # Update replica count in deployment
        sed -i.bak "s/replicas: [0-9]*/replicas: $REPLICAS/" "$DEPLOYMENT_DIR/kubernetes/all-in-one.yml"

        # Apply Kubernetes manifests
        kubectl apply -f "$DEPLOYMENT_DIR/kubernetes/all-in-one.yml"

        # Wait for rollout
        kubectl rollout status deployment/jackcwf-backend -n jackcwf --timeout=5m

        # Restore original file
        mv "$DEPLOYMENT_DIR/kubernetes/all-in-one.yml.bak" "$DEPLOYMENT_DIR/kubernetes/all-in-one.yml"

        log_success "Kubernetes deployment completed"
    else
        log_info "[DRY RUN] Would apply Kubernetes manifests with $REPLICAS replicas"
    fi
}

deploy_swarm() {
    log_info "Deploying to Docker Swarm (${REPLICAS} replicas)..."

    if [ "$DRY_RUN" = false ]; then
        # Initialize swarm if not already initialized
        if ! docker info | grep -q "Swarm: active"; then
            log_info "Initializing Docker Swarm..."
            docker swarm init
        fi

        # Deploy stack
        docker stack deploy -c "$DEPLOYMENT_DIR/docker-compose.ha.yml" jackcwf

        # Scale service
        docker service scale jackcwf_web=$REPLICAS

        log_success "Docker Swarm deployment completed"
    else
        log_info "[DRY RUN] Would deploy to Docker Swarm with $REPLICAS replicas"
    fi
}

# Execute deployment
case $PLATFORM in
    docker-compose)
        deploy_docker_compose
        ;;
    kubernetes)
        deploy_kubernetes
        ;;
    swarm)
        deploy_swarm
        ;;
esac

# ============================================
# Health Check
# ============================================

if [ "$HEALTH_CHECK" = true ] && [ "$DRY_RUN" = false ]; then
    log_info "Running health checks..."

    sleep 10  # Wait for containers to start

    HEALTH_URL="http://localhost/health"
    MAX_RETRIES=30
    RETRY_INTERVAL=5

    for ((i=1; i<=MAX_RETRIES; i++)); do
        if curl -f -s "$HEALTH_URL" > /dev/null 2>&1; then
            log_success "Health check passed (${i}/${MAX_RETRIES})"
            break
        else
            if [ $i -eq $MAX_RETRIES ]; then
                log_error "Health check failed after ${MAX_RETRIES} attempts"
                exit 1
            fi
            log_warning "Health check attempt ${i}/${MAX_RETRIES} failed, retrying in ${RETRY_INTERVAL}s..."
            sleep $RETRY_INTERVAL
        fi
    done
fi

# ============================================
# Summary
# ============================================

log_success "Deployment completed successfully!"
echo ""
echo "Deployment Summary:"
echo "  Platform:  $PLATFORM"
echo "  Replicas:  $REPLICAS"
echo "  Image:     ${IMAGE_NAME}:${IMAGE_TAG}"
echo ""

case $PLATFORM in
    docker-compose)
        echo "View containers:"
        echo "  docker-compose -f deployment/docker-compose.ha.yml ps"
        echo ""
        echo "View logs:"
        echo "  docker-compose -f deployment/docker-compose.ha.yml logs -f"
        echo ""
        echo "Scale replicas:"
        echo "  docker-compose -f deployment/docker-compose.ha.yml up -d --scale web=5"
        ;;
    kubernetes)
        echo "View pods:"
        echo "  kubectl get pods -n jackcwf"
        echo ""
        echo "View logs:"
        echo "  kubectl logs -f -l app=jackcwf-backend -n jackcwf"
        echo ""
        echo "Scale replicas:"
        echo "  kubectl scale deployment/jackcwf-backend --replicas=5 -n jackcwf"
        ;;
    swarm)
        echo "View services:"
        echo "  docker service ls"
        echo ""
        echo "View logs:"
        echo "  docker service logs -f jackcwf_web"
        echo ""
        echo "Scale replicas:"
        echo "  docker service scale jackcwf_web=5"
        ;;
esac

echo ""
echo "Access application:"
echo "  http://localhost"
echo ""
echo "Access Traefik dashboard (Docker Compose):"
echo "  http://localhost:8080"
