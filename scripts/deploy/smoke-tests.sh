#!/bin/bash
# Smoke Tests Script
# Usage: ./smoke-tests.sh <url>

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

log_info "Running smoke tests for: ${BASE_URL}"

# Counters
PASSED=0
FAILED=0

# Function to run test
run_test() {
    local test_name=$1
    local url=$2
    local expected_code=${3:-200}
    local method=${4:-GET}
    local data=${5:-}

    log_info "Test: ${test_name}"

    if [ -n "$data" ]; then
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            --max-time 10 "$url" || echo "000")
    else
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" \
            --max-time 10 "$url" || echo "000")
    fi

    if [ "$HTTP_CODE" == "$expected_code" ]; then
        log_info "✓ PASSED: ${test_name} (HTTP ${HTTP_CODE})"
        PASSED=$((PASSED + 1))
        return 0
    else
        log_error "✗ FAILED: ${test_name} (Expected HTTP ${expected_code}, got ${HTTP_CODE})"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Function to test JSON response
test_json_response() {
    local test_name=$1
    local url=$2
    local jq_filter=$3
    local expected_value=$4

    log_info "Test: ${test_name}"

    RESPONSE=$(curl -s --max-time 10 "$url" || echo "{}")

    if echo "$RESPONSE" | jq -e "$jq_filter" > /dev/null 2>&1; then
        ACTUAL_VALUE=$(echo "$RESPONSE" | jq -r "$jq_filter")

        if [ "$ACTUAL_VALUE" == "$expected_value" ]; then
            log_info "✓ PASSED: ${test_name} (${ACTUAL_VALUE})"
            PASSED=$((PASSED + 1))
            return 0
        else
            log_error "✗ FAILED: ${test_name} (Expected '${expected_value}', got '${ACTUAL_VALUE}')"
            FAILED=$((FAILED + 1))
            return 1
        fi
    else
        log_error "✗ FAILED: ${test_name} (Could not parse JSON or field not found)"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

log_info "================================================"
log_info "Smoke Test Suite"
log_info "================================================"
log_info "Target: ${BASE_URL}"
log_info "Timestamp: $(date -u +%Y-%m-%d\ %H:%M:%S\ UTC)"
log_info "================================================"

# Test 1: Frontend is accessible
run_test "Frontend Homepage" "$BASE_URL" "200"

# Test 2: Backend API is accessible
run_test "Backend API Root" "${BASE_URL}/api" "200"

# Test 3: Health endpoint
run_test "Health Endpoint" "${BASE_URL}/api/health" "200"

# Test 4: Health endpoint returns correct status
test_json_response "Health Status Field" "${BASE_URL}/api/health" ".status" "healthy" || \
test_json_response "Health Status Field (alt)" "${BASE_URL}/api/health" ".status" "ok" || \
test_json_response "Health Status Field (alt2)" "${BASE_URL}/api/health" ".status" "up"

# Test 5: API documentation (if available)
run_test "API Documentation" "${BASE_URL}/api/docs" "200" || log_warn "API docs not available"

# Test 6: Static assets
run_test "Favicon" "${BASE_URL}/favicon.ico" "200" || log_warn "Favicon not found"

# Test 7: 404 handling
run_test "404 Error Handling" "${BASE_URL}/this-page-does-not-exist-12345" "404"

# Test 8: CORS headers (if applicable)
log_info "Test: CORS Headers"
CORS_HEADERS=$(curl -s -I -H "Origin: https://example.com" "${BASE_URL}/api/health" | grep -i "access-control" || echo "")
if [ -n "$CORS_HEADERS" ]; then
    log_info "✓ PASSED: CORS headers present"
    echo "$CORS_HEADERS"
    PASSED=$((PASSED + 1))
else
    log_warn "CORS headers not found (may be expected)"
fi

# Test 9: Response headers
log_info "Test: Security Headers"
HEADERS=$(curl -s -I "$BASE_URL" || echo "")

# Check for security headers
HAS_SECURITY_HEADERS=0

if echo "$HEADERS" | grep -qi "x-frame-options"; then
    log_info "✓ X-Frame-Options header present"
    HAS_SECURITY_HEADERS=1
fi

if echo "$HEADERS" | grep -qi "x-content-type-options"; then
    log_info "✓ X-Content-Type-Options header present"
    HAS_SECURITY_HEADERS=1
fi

if echo "$HEADERS" | grep -qi "strict-transport-security"; then
    log_info "✓ Strict-Transport-Security header present"
    HAS_SECURITY_HEADERS=1
fi

if [ $HAS_SECURITY_HEADERS -eq 1 ]; then
    PASSED=$((PASSED + 1))
else
    log_warn "No security headers detected"
fi

# Test 10: WebSocket endpoint (if applicable)
log_info "Test: WebSocket Endpoint"
WS_URL=$(echo "$BASE_URL" | sed 's/^http/ws/')
if curl -s --max-time 5 -i -N \
    -H "Connection: Upgrade" \
    -H "Upgrade: websocket" \
    -H "Sec-WebSocket-Version: 13" \
    -H "Sec-WebSocket-Key: x3JJHMbDL1EzLkh9GBhXDw==" \
    "${WS_URL}/ws" 2>&1 | grep -qi "switching protocols"; then
    log_info "✓ PASSED: WebSocket endpoint available"
    PASSED=$((PASSED + 1))
else
    log_warn "WebSocket endpoint not available (may be expected)"
fi

# Summary
log_info "================================================"
log_info "Smoke Test Results"
log_info "================================================"
log_info "Passed: ${PASSED}"
log_info "Failed: ${FAILED}"
log_info "Total:  $((PASSED + FAILED))"
log_info "================================================"

if [ $FAILED -eq 0 ]; then
    log_info "✅ All smoke tests passed"
    exit 0
else
    log_error "❌ ${FAILED} smoke test(s) failed"
    exit 1
fi
