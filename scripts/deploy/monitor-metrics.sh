#!/bin/bash
# Monitor Metrics Script
# Usage: ./monitor-metrics.sh <url>

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

log_info "Monitoring metrics for: ${BASE_URL}"
log_info "Duration: 3 minutes with 30-second intervals"

# Metrics endpoints
METRICS_ENDPOINT="${BASE_URL}/api/metrics"
HEALTH_ENDPOINT="${BASE_URL}/api/health"

# Initialize metrics arrays
declare -a RESPONSE_TIMES
declare -a MEMORY_USAGE
declare -a CPU_USAGE

# Function to measure response time
measure_response_time() {
    local url=$1
    curl -s -o /dev/null -w "%{time_total}" --max-time 10 "$url" 2>/dev/null || echo "0"
}

# Function to get metrics from endpoint
get_metrics() {
    local url=$1
    curl -s --max-time 5 "$url" 2>/dev/null || echo "{}"
}

log_info "================================================"
log_info "Metrics Collection Started"
log_info "================================================"

# Collect metrics over 3 minutes (6 samples at 30-second intervals)
for i in {1..6}; do
    log_info "Sample ${i}/6 at $(date +%H:%M:%S)"

    # Measure response time
    RESPONSE_TIME=$(measure_response_time "$BASE_URL")
    RESPONSE_TIMES+=("$RESPONSE_TIME")
    log_info "  Response time: ${RESPONSE_TIME}s"

    # Get application metrics
    METRICS=$(get_metrics "$METRICS_ENDPOINT")

    if [ "$METRICS" != "{}" ]; then
        # Try to extract memory and CPU if available
        MEM=$(echo "$METRICS" | jq -r '.memory.used_mb // empty' 2>/dev/null)
        CPU=$(echo "$METRICS" | jq -r '.cpu.usage_percent // empty' 2>/dev/null)

        if [ -n "$MEM" ]; then
            MEMORY_USAGE+=("$MEM")
            log_info "  Memory: ${MEM} MB"
        fi

        if [ -n "$CPU" ]; then
            CPU_USAGE+=("$CPU")
            log_info "  CPU: ${CPU}%"
        fi
    fi

    # Check health status
    HEALTH=$(get_metrics "$HEALTH_ENDPOINT")
    STATUS=$(echo "$HEALTH" | jq -r '.status // "unknown"' 2>/dev/null)
    log_info "  Health: ${STATUS}"

    # Sleep before next sample (except for last iteration)
    if [ $i -lt 6 ]; then
        sleep 30
    fi
done

log_info "================================================"
log_info "Metrics Analysis"
log_info "================================================"

# Calculate response time statistics
if [ ${#RESPONSE_TIMES[@]} -gt 0 ]; then
    AVG_RESPONSE=$(echo "${RESPONSE_TIMES[@]}" | tr ' ' '\n' | awk '{sum+=$1} END {print sum/NR}')
    MAX_RESPONSE=$(echo "${RESPONSE_TIMES[@]}" | tr ' ' '\n' | sort -n | tail -1)
    MIN_RESPONSE=$(echo "${RESPONSE_TIMES[@]}" | tr ' ' '\n' | sort -n | head -1)

    log_info "Response Times:"
    log_info "  Average: ${AVG_RESPONSE}s"
    log_info "  Min: ${MIN_RESPONSE}s"
    log_info "  Max: ${MAX_RESPONSE}s"

    # Check if response times are acceptable
    if (( $(echo "$AVG_RESPONSE > 5.0" | bc -l) )); then
        log_warn "  ⚠️ Average response time exceeds 5 seconds"
    else
        log_info "  ✓ Response times are acceptable"
    fi
fi

# Calculate memory statistics
if [ ${#MEMORY_USAGE[@]} -gt 0 ]; then
    AVG_MEMORY=$(echo "${MEMORY_USAGE[@]}" | tr ' ' '\n' | awk '{sum+=$1} END {print sum/NR}')
    MAX_MEMORY=$(echo "${MEMORY_USAGE[@]}" | tr ' ' '\n' | sort -n | tail -1)

    log_info "Memory Usage:"
    log_info "  Average: ${AVG_MEMORY} MB"
    log_info "  Max: ${MAX_MEMORY} MB"
fi

# Calculate CPU statistics
if [ ${#CPU_USAGE[@]} -gt 0 ]; then
    AVG_CPU=$(echo "${CPU_USAGE[@]}" | tr ' ' '\n' | awk '{sum+=$1} END {print sum/NR}')
    MAX_CPU=$(echo "${CPU_USAGE[@]}" | tr ' ' '\n' | sort -n | tail -1)

    log_info "CPU Usage:"
    log_info "  Average: ${AVG_CPU}%"
    log_info "  Max: ${MAX_CPU}%"

    # Check if CPU usage is high
    if (( $(echo "$AVG_CPU > 80.0" | bc -l) )); then
        log_warn "  ⚠️ High CPU usage detected"
    fi
fi

# Stability check
log_info "================================================"
log_info "Stability Assessment"
log_info "================================================"

# Check for response time variance
if [ ${#RESPONSE_TIMES[@]} -gt 0 ]; then
    VARIANCE=$(echo "${RESPONSE_TIMES[@]}" | tr ' ' '\n' | awk -v avg="$AVG_RESPONSE" '{sum+=($1-avg)^2} END {print sum/NR}')
    STDDEV=$(echo "$VARIANCE" | awk '{print sqrt($1)}')

    if (( $(echo "$STDDEV > 1.0" | bc -l) )); then
        log_warn "High response time variance detected (σ=${STDDEV}s)"
        log_warn "Application performance may be unstable"
    else
        log_info "✓ Response times are stable (σ=${STDDEV}s)"
    fi
fi

log_info "================================================"
log_info "Monitoring completed at $(date +%Y-%m-%d\ %H:%M:%S)"
log_info "================================================"

exit 0
