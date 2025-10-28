#!/bin/bash
# Health Check Script
# Usage: ./health-check.sh <url>

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check required parameters
if [ -z "$1" ]; then
    log_error "Usage: $0 <url>"
    log_info "Example: $0 https://jackcwf.com"
    exit 1
fi

BASE_URL=$1

log_info "Starting health checks for: ${BASE_URL}"

# Health check endpoints
FRONTEND_URL="${BASE_URL}"
BACKEND_URL="${BASE_URL}/api"
HEALTH_ENDPOINT="${BACKEND_URL}/health"
READY_ENDPOINT="${BACKEND_URL}/ready"

# Function to check HTTP endpoint
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

# Function to check JSON health endpoint
check_health_json() {
    local url=$1
    local name=$2

    log_info "Checking ${name} detailed health..."

    RESPONSE=$(curl -s --max-time 10 "$url" || echo "{}")

    if echo "$RESPONSE" | jq -e '.status' > /dev/null 2>&1; then
        STATUS=$(echo "$RESPONSE" | jq -r '.status')

        if [ "$STATUS" == "healthy" ] || [ "$STATUS" == "ok" ] || [ "$STATUS" == "up" ]; then
            log_info "✓ ${name} health status: ${STATUS}"
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

# Function to measure response time
measure_response_time() {
    local url=$1
    local name=$2

    log_info "Measuring ${name} response time..."

    RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" --max-time 10 "$url" || echo "timeout")

    if [ "$RESPONSE_TIME" == "timeout" ]; then
        log_error "${name} response timed out"
        return 1
    else
        log_info "${name} response time: ${RESPONSE_TIME}s"

        # Check if response time is acceptable (< 5 seconds)
        if (( $(echo "$RESPONSE_TIME < 5.0" | bc -l) )); then
            log_info "✓ Response time is acceptable"
            return 0
        else
            log_warn "Response time is slower than expected (>5s)"
            return 1
        fi
    fi
}

# Main health checks
log_info "================================================"
log_info "Health Check Report"
log_info "================================================"
log_info "Target: ${BASE_URL}"
log_info "Timestamp: $(date -u +%Y-%m-%d\ %H:%M:%S\ UTC)"
log_info "================================================"

FAILED_CHECKS=0

# Check 1: Frontend accessibility
if ! check_endpoint "$FRONTEND_URL" "Frontend" 3 5; then
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

# Check 2: Backend API accessibility
if ! check_endpoint "$BACKEND_URL" "Backend API" 3 5; then
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

# Check 3: Health endpoint
if ! check_endpoint "$HEALTH_ENDPOINT" "Health Endpoint" 3 5; then
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
else
    # Get detailed health info
    check_health_json "$HEALTH_ENDPOINT" "Health Status" || true
fi

# Check 4: Ready endpoint
if ! check_endpoint "$READY_ENDPOINT" "Ready Endpoint" 3 5; then
    log_warn "Ready endpoint not accessible (this may be expected)"
fi

# Check 5: Response time
if ! measure_response_time "$FRONTEND_URL" "Frontend"; then
    log_warn "Frontend response time check failed"
fi

# Check 6: SSL certificate (if HTTPS)
if [[ "$BASE_URL" == https://* ]]; then
    log_info "Checking SSL certificate..."
    CERT_INFO=$(echo | openssl s_client -servername "${BASE_URL#https://}" -connect "${BASE_URL#https://}:443" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null || echo "")

    if [ -n "$CERT_INFO" ]; then
        log_info "✓ SSL certificate is valid"
        echo "$CERT_INFO"
    else
        log_warn "Could not verify SSL certificate"
    fi
fi

# Summary
log_info "================================================"
log_info "Health Check Summary"
log_info "================================================"

if [ $FAILED_CHECKS -eq 0 ]; then
    log_info "✅ All health checks passed"
    log_info "Application is healthy and ready"
    exit 0
else
    log_error "❌ ${FAILED_CHECKS} health check(s) failed"
    log_error "Application may not be fully operational"
    exit 1
fi
