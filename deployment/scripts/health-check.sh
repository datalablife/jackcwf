#!/bin/bash
# Health Check Script for HA Deployment
# Monitors all replicas and reports their health status
#
# Usage:
#   ./deployment/scripts/health-check.sh [OPTIONS]
#
# Options:
#   --platform TYPE    Platform: docker-compose|kubernetes|swarm (default: docker-compose)
#   --continuous       Run continuous monitoring (every 30s)
#   --alert            Send alerts on failures
#   --verbose          Verbose output

set -e

# ============================================
# Configuration
# ============================================

PLATFORM=${PLATFORM:-docker-compose}
CONTINUOUS=false
ALERT=false
VERBOSE=false

# ============================================
# Colors
# ============================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
    echo -e "${RED}[ERROR]${NC} $1"
}

# ============================================
# Parse Arguments
# ============================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --platform)
            PLATFORM="$2"
            shift 2
            ;;
        --continuous)
            CONTINUOUS=true
            shift
            ;;
        --alert)
            ALERT=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# ============================================
# Health Check Functions
# ============================================

check_docker_compose() {
    log_info "Checking Docker Compose deployment health..."

    COMPOSE_FILE="deployment/docker-compose.ha.yml"

    # Get all web service containers
    CONTAINERS=$(docker-compose -f $COMPOSE_FILE ps -q web 2>/dev/null)

    if [ -z "$CONTAINERS" ]; then
        log_error "No web containers found"
        return 1
    fi

    TOTAL=0
    HEALTHY=0
    UNHEALTHY=0

    for CONTAINER in $CONTAINERS; do
        TOTAL=$((TOTAL + 1))
        CONTAINER_NAME=$(docker inspect --format='{{.Name}}' $CONTAINER | sed 's/\///')
        HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' $CONTAINER 2>/dev/null || echo "unknown")

        if [ "$HEALTH_STATUS" = "healthy" ]; then
            HEALTHY=$((HEALTHY + 1))
            log_success "Container $CONTAINER_NAME: HEALTHY"
        else
            UNHEALTHY=$((UNHEALTHY + 1))
            log_error "Container $CONTAINER_NAME: $HEALTH_STATUS"

            if [ "$VERBOSE" = true ]; then
                log_info "Last 10 log lines:"
                docker logs --tail 10 $CONTAINER
            fi
        fi
    done

    echo ""
    echo "Summary:"
    echo "  Total:     $TOTAL"
    echo "  Healthy:   $HEALTHY"
    echo "  Unhealthy: $UNHEALTHY"
    echo ""

    # Check Traefik
    log_info "Checking Traefik load balancer..."
    TRAEFIK_STATUS=$(docker inspect --format='{{.State.Status}}' jackcwf-traefik 2>/dev/null || echo "not_found")

    if [ "$TRAEFIK_STATUS" = "running" ]; then
        log_success "Traefik: RUNNING"
    else
        log_error "Traefik: $TRAEFIK_STATUS"
    fi

    if [ $UNHEALTHY -eq 0 ] && [ "$TRAEFIK_STATUS" = "running" ]; then
        return 0
    else
        return 1
    fi
}

check_kubernetes() {
    log_info "Checking Kubernetes deployment health..."

    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl not found"
        return 1
    fi

    # Get deployment status
    DEPLOYMENT_STATUS=$(kubectl get deployment jackcwf-backend -n jackcwf -o jsonpath='{.status.conditions[?(@.type=="Available")].status}' 2>/dev/null || echo "Unknown")

    if [ "$DEPLOYMENT_STATUS" = "True" ]; then
        log_success "Deployment: AVAILABLE"
    else
        log_error "Deployment: NOT AVAILABLE"
    fi

    # Get pod status
    TOTAL=$(kubectl get pods -n jackcwf -l app=jackcwf-backend --no-headers 2>/dev/null | wc -l)
    RUNNING=$(kubectl get pods -n jackcwf -l app=jackcwf-backend --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
    READY=$(kubectl get pods -n jackcwf -l app=jackcwf-backend -o jsonpath='{range .items[*]}{.status.conditions[?(@.type=="Ready")].status}{"\n"}{end}' 2>/dev/null | grep -c "True" || echo 0)

    echo ""
    echo "Pod Summary:"
    echo "  Total:   $TOTAL"
    echo "  Running: $RUNNING"
    echo "  Ready:   $READY"
    echo ""

    if [ "$VERBOSE" = true ]; then
        log_info "Pod details:"
        kubectl get pods -n jackcwf -l app=jackcwf-backend
    fi

    # Check HPA
    log_info "Checking Horizontal Pod Autoscaler..."
    kubectl get hpa jackcwf-backend-hpa -n jackcwf 2>/dev/null || log_warning "HPA not found"

    echo ""

    if [ "$DEPLOYMENT_STATUS" = "True" ] && [ $READY -eq $TOTAL ]; then
        return 0
    else
        return 1
    fi
}

check_swarm() {
    log_info "Checking Docker Swarm service health..."

    if ! docker info | grep -q "Swarm: active"; then
        log_error "Docker Swarm is not active"
        return 1
    fi

    SERVICE_NAME="jackcwf_web"

    REPLICAS=$(docker service ls --filter name=$SERVICE_NAME --format "{{.Replicas}}" 2>/dev/null)

    if [ -z "$REPLICAS" ]; then
        log_error "Service $SERVICE_NAME not found"
        return 1
    fi

    RUNNING=$(echo $REPLICAS | cut -d'/' -f1)
    DESIRED=$(echo $REPLICAS | cut -d'/' -f2)

    echo ""
    echo "Service Summary:"
    echo "  Running: $RUNNING"
    echo "  Desired: $DESIRED"
    echo ""

    if [ "$VERBOSE" = true ]; then
        log_info "Service details:"
        docker service ps $SERVICE_NAME
    fi

    if [ "$RUNNING" = "$DESIRED" ]; then
        log_success "All replicas are running"
        return 0
    else
        log_error "Not all replicas are running ($RUNNING/$DESIRED)"
        return 1
    fi
}

# ============================================
# Main Health Check
# ============================================

run_health_check() {
    echo "========================================"
    echo "Health Check - $(date)"
    echo "Platform: $PLATFORM"
    echo "========================================"
    echo ""

    case $PLATFORM in
        docker-compose)
            check_docker_compose
            ;;
        kubernetes)
            check_kubernetes
            ;;
        swarm)
            check_swarm
            ;;
        *)
            log_error "Invalid platform: $PLATFORM"
            exit 1
            ;;
    esac

    RESULT=$?

    echo ""
    if [ $RESULT -eq 0 ]; then
        log_success "All health checks passed"
    else
        log_error "Some health checks failed"

        if [ "$ALERT" = true ]; then
            # Send alert (integrate with your alerting system)
            log_warning "Sending alert..."
            # Example: curl -X POST https://alerts.example.com/webhook -d '{"status":"unhealthy"}'
        fi
    fi

    return $RESULT
}

# ============================================
# Continuous Monitoring
# ============================================

if [ "$CONTINUOUS" = true ]; then
    log_info "Starting continuous monitoring (press Ctrl+C to stop)..."

    while true; do
        run_health_check
        echo ""
        echo "Next check in 30 seconds..."
        echo ""
        sleep 30
    done
else
    run_health_check
    exit $?
fi
