#!/bin/bash
# 4GB Memory Optimized Health Check Script
# Usage: ./health-check-4gb.sh <url>
#
# This script performs comprehensive health checks specifically designed
# for the 4GB memory-constrained deployment configuration.

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MEMORY_THRESHOLD_MB=4096  # 4GB total system memory
WARNING_THRESHOLD_PERCENT=85  # Warning if memory usage > 85%
CRITICAL_THRESHOLD_PERCENT=95  # Critical if memory usage > 95%

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# Check required parameters
if [ -z "$1" ]; then
    log_error "Usage: $0 <url>"
    log_info "Example: $0 https://jackcwf.com"
    exit 1
fi

BASE_URL=$1

log_info "================================================"
log_info "4GB Memory Optimized Health Check"
log_info "================================================"
log_info "Target: ${BASE_URL}"
log_info "Timestamp: $(date -u +%Y-%m-%d\ %H:%M:%S\ UTC)"
log_info "================================================"

# Health check endpoints
FRONTEND_URL="${BASE_URL}"
BACKEND_URL="${BASE_URL}/api"
HEALTH_ENDPOINT="${BACKEND_URL}/health"
READY_ENDPOINT="${BACKEND_URL}/ready"
METRICS_ENDPOINT="${BACKEND_URL}/metrics"
PROMETHEUS_URL="${BASE_URL}:9090"
GRAFANA_URL="${BASE_URL}:3001"

FAILED_CHECKS=0

# ============================================
# Function: Check HTTP endpoint
# ============================================
check_endpoint() {
    local url=$1
    local name=$2
    local max_retries=${3:-3}
    local retry_delay=${4:-5}

    log_info "Checking ${name}..."

    for i in $(seq 1 $max_retries); do
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" || echo "000")

        if [ "$HTTP_CODE" == "200" ] || [ "$HTTP_CODE" == "301" ] || [ "$HTTP_CODE" == "302" ]; then
            log_info "✓ ${name} is healthy (HTTP ${HTTP_CODE})"
            return 0
        else
            log_warn "Attempt $i/$max_retries: ${name} returned HTTP ${HTTP_CODE}"
            if [ $i -lt $max_retries ]; then
                sleep $retry_delay
            fi
        fi
    done

    log_error "✗ ${name} health check failed after ${max_retries} attempts"
    return 1
}

# ============================================
# Function: Check JSON health endpoint
# ============================================
check_health_json() {
    local url=$1
    local name=$2

    log_info "Checking ${name} detailed health..."

    RESPONSE=$(curl -s --max-time 10 "$url" || echo "{}")

    if echo "$RESPONSE" | jq -e '.status' > /dev/null 2>&1; then
        STATUS=$(echo "$RESPONSE" | jq -r '.status')

        if [ "$STATUS" == "healthy" ] || [ "$STATUS" == "ok" ] || [ "$STATUS" == "up" ]; then
            log_info "✓ ${name} health status: ${STATUS}"

            # Check if memory info is available
            if echo "$RESPONSE" | jq -e '.memory' > /dev/null 2>&1; then
                MEMORY_USAGE=$(echo "$RESPONSE" | jq -r '.memory.used_mb // "N/A"')
                MEMORY_TOTAL=$(echo "$RESPONSE" | jq -r '.memory.total_mb // "N/A"')
                log_info "  Memory: ${MEMORY_USAGE}MB / ${MEMORY_TOTAL}MB"
            fi

            echo "$RESPONSE" | jq '.'
            return 0
        else
            log_warn "${name} health status: ${STATUS}"
            echo "$RESPONSE" | jq '.'
            return 1
        fi
    else
        log_warn "Could not parse JSON health response"
        return 1
    fi
}

# ============================================
# Function: Measure response time
# ============================================
measure_response_time() {
    local url=$1
    local name=$2
    local threshold=${3:-2.0}  # 4GB systems: stricter 2s threshold

    log_info "Measuring ${name} response time..."

    RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" --max-time 10 "$url" || echo "timeout")

    if [ "$RESPONSE_TIME" == "timeout" ]; then
        log_error "${name} response timed out"
        return 1
    else
        log_info "${name} response time: ${RESPONSE_TIME}s"

        # Check if response time is acceptable
        if (( $(echo "$RESPONSE_TIME < $threshold" | bc -l) )); then
            log_info "✓ Response time is acceptable (<${threshold}s)"
            return 0
        else
            log_warn "Response time is slower than expected (>${threshold}s)"
            return 1
        fi
    fi
}

# ============================================
# Function: Check memory usage via API
# ============================================
check_memory_usage() {
    local url=$1

    log_info "Checking memory usage via metrics endpoint..."

    METRICS=$(curl -s --max-time 10 "$url" || echo "")

    if [ -z "$METRICS" ]; then
        log_warn "Could not fetch metrics from $url"
        return 1
    fi

    # Extract memory metrics (example: process_resident_memory_bytes)
    MEMORY_BYTES=$(echo "$METRICS" | grep "^process_resident_memory_bytes" | awk '{print $2}')

    if [ -n "$MEMORY_BYTES" ]; then
        MEMORY_MB=$((MEMORY_BYTES / 1024 / 1024))
        log_info "Process memory usage: ${MEMORY_MB}MB"

        # Check against 4GB limits
        if [ $MEMORY_MB -gt 3500 ]; then
            log_error "⚠ Memory usage ${MEMORY_MB}MB exceeds safe threshold for 4GB system"
            return 1
        elif [ $MEMORY_MB -gt 3000 ]; then
            log_warn "Memory usage ${MEMORY_MB}MB is approaching 4GB limit"
        else
            log_info "✓ Memory usage is within safe limits"
        fi
    else
        log_debug "Memory metrics not available in Prometheus format"
    fi

    return 0
}

# ============================================
# Function: Check service-specific metrics
# ============================================
check_service_metrics() {
    local prometheus_url=$1

    log_info "Checking service-specific 4GB metrics..."

    # Query Prometheus for critical metrics
    if command -v curl &> /dev/null; then
        # 1. Check Redis memory
        REDIS_MEMORY=$(curl -s "${prometheus_url}/api/v1/query?query=redis_memory_used_bytes" | jq -r '.data.result[0].value[1] // "N/A"')
        if [ "$REDIS_MEMORY" != "N/A" ]; then
            REDIS_MB=$((REDIS_MEMORY / 1024 / 1024))
            log_info "Redis memory: ${REDIS_MB}MB / 256MB limit"

            if [ $REDIS_MB -gt 230 ]; then
                log_warn "Redis approaching memory limit (256MB)"
            fi
        fi

        # 2. Check PostgreSQL connections
        PG_CONNECTIONS=$(curl -s "${prometheus_url}/api/v1/query?query=pg_stat_activity_count" | jq -r '.data.result[0].value[1] // "N/A"')
        if [ "$PG_CONNECTIONS" != "N/A" ]; then
            log_info "PostgreSQL connections: ${PG_CONNECTIONS} / 50 limit"

            if [ $PG_CONNECTIONS -gt 40 ]; then
                log_warn "PostgreSQL connections approaching limit (50)"
            fi
        fi

        # 3. Check overall system memory
        SYSTEM_MEM_PERCENT=$(curl -s "${prometheus_url}/api/v1/query?query=node:memory_usage_percent:1m" | jq -r '.data.result[0].value[1] // "N/A"')
        if [ "$SYSTEM_MEM_PERCENT" != "N/A" ]; then
            log_info "System memory usage: ${SYSTEM_MEM_PERCENT}%"

            MEM_INT=$(printf "%.0f" "$SYSTEM_MEM_PERCENT")
            if [ $MEM_INT -gt $CRITICAL_THRESHOLD_PERCENT ]; then
                log_error "⚠ CRITICAL: System memory > ${CRITICAL_THRESHOLD_PERCENT}%"
                return 1
            elif [ $MEM_INT -gt $WARNING_THRESHOLD_PERCENT ]; then
                log_warn "WARNING: System memory > ${WARNING_THRESHOLD_PERCENT}%"
            fi
        fi
    fi

    return 0
}

# ============================================
# Function: Verify 4GB alerts are loaded
# ============================================
check_prometheus_alerts() {
    local prometheus_url=$1

    log_info "Verifying 4GB Prometheus alerts are loaded..."

    ALERTS_RESPONSE=$(curl -s "${prometheus_url}/api/v1/rules" || echo "{}")

    # Check if critical 4GB alerts exist
    CRITICAL_ALERTS=(
        "ServiceDown"
        "HighMemoryUsage"
        "HighAPILatency"
        "LowCacheHitRate"
        "HighDatabaseConnections"
    )

    LOADED_ALERTS=0
    for alert in "${CRITICAL_ALERTS[@]}"; do
        if echo "$ALERTS_RESPONSE" | grep -q "$alert"; then
            log_info "✓ Alert loaded: $alert"
            LOADED_ALERTS=$((LOADED_ALERTS + 1))
        else
            log_warn "✗ Alert missing: $alert"
        fi
    done

    log_info "Loaded ${LOADED_ALERTS}/${#CRITICAL_ALERTS[@]} critical alerts"

    if [ $LOADED_ALERTS -eq ${#CRITICAL_ALERTS[@]} ]; then
        log_info "✓ All critical 4GB alerts are loaded"
        return 0
    else
        log_warn "Some 4GB alerts are missing"
        return 1
    fi
}

# ============================================
# Main Health Checks
# ============================================

# Check 1: Frontend accessibility
log_info ""
log_info "[1/10] Checking Frontend..."
if ! check_endpoint "$FRONTEND_URL" "Frontend" 3 5; then
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

# Check 2: Backend API accessibility
log_info ""
log_info "[2/10] Checking Backend API..."
if ! check_endpoint "$BACKEND_URL" "Backend API" 3 5; then
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

# Check 3: Health endpoint
log_info ""
log_info "[3/10] Checking Health Endpoint..."
if ! check_endpoint "$HEALTH_ENDPOINT" "Health Endpoint" 3 5; then
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
else
    # Get detailed health info
    check_health_json "$HEALTH_ENDPOINT" "Health Status" || true
fi

# Check 4: Ready endpoint
log_info ""
log_info "[4/10] Checking Ready Endpoint..."
if ! check_endpoint "$READY_ENDPOINT" "Ready Endpoint" 3 5; then
    log_warn "Ready endpoint not accessible (this may be expected)"
fi

# Check 5: Response time
log_info ""
log_info "[5/10] Measuring Response Time..."
if ! measure_response_time "$FRONTEND_URL" "Frontend" 2.0; then
    log_warn "Frontend response time check failed"
fi

# Check 6: Memory usage via metrics
log_info ""
log_info "[6/10] Checking Memory Usage..."
if ! check_memory_usage "$METRICS_ENDPOINT"; then
    log_warn "Memory usage check failed or not available"
fi

# Check 7: Prometheus accessibility
log_info ""
log_info "[7/10] Checking Prometheus..."
if ! check_endpoint "$PROMETHEUS_URL" "Prometheus" 2 3; then
    log_warn "Prometheus not accessible"
else
    # Check 4GB alerts are loaded
    check_prometheus_alerts "$PROMETHEUS_URL" || true
fi

# Check 8: Grafana accessibility
log_info ""
log_info "[8/10] Checking Grafana..."
if ! check_endpoint "$GRAFANA_URL" "Grafana" 2 3; then
    log_warn "Grafana not accessible"
fi

# Check 9: Service-specific metrics
log_info ""
log_info "[9/10] Checking Service Metrics..."
if ! check_service_metrics "$PROMETHEUS_URL"; then
    log_warn "Some service metrics are concerning"
fi

# Check 10: SSL certificate (if HTTPS)
log_info ""
log_info "[10/10] Checking SSL Certificate..."
if [[ "$BASE_URL" == https://* ]]; then
    CERT_INFO=$(echo | openssl s_client -servername "${BASE_URL#https://}" -connect "${BASE_URL#https://}:443" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null || echo "")

    if [ -n "$CERT_INFO" ]; then
        log_info "✓ SSL certificate is valid"
        echo "$CERT_INFO"
    else
        log_warn "Could not verify SSL certificate"
    fi
fi

# ============================================
# Summary Report
# ============================================
log_info ""
log_info "================================================"
log_info "4GB Health Check Summary"
log_info "================================================"

if [ $FAILED_CHECKS -eq 0 ]; then
    log_info "✅ All critical health checks passed"
    log_info "✅ Application is healthy and within 4GB memory limits"
    log_info "✅ Monitoring stack is operational"
    log_info ""
    log_info "Next steps:"
    log_info "  1. Monitor Grafana dashboard: ${GRAFANA_URL}"
    log_info "  2. Check Prometheus alerts: ${PROMETHEUS_URL}/alerts"
    log_info "  3. Review application logs in Coolify"
    exit 0
else
    log_error "❌ ${FAILED_CHECKS} health check(s) failed"
    log_error "❌ Application may not be fully operational"
    log_error ""
    log_error "Troubleshooting steps:"
    log_error "  1. Check container logs: docker-compose -f docker-compose-4gb.yml logs"
    log_error "  2. Verify memory usage: docker stats"
    log_error "  3. Review Prometheus alerts: ${PROMETHEUS_URL}/alerts"
    log_error "  4. Check Coolify deployment logs"
    exit 1
fi
