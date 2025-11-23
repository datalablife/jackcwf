#!/bin/bash

# Production Optimization Verification & Deployment Script
# This script verifies all production optimization implementations are in place
# and ready for deployment.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="$PROJECT_ROOT/OPTIMIZATION_VERIFICATION_${TIMESTAMP}.md"

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNING=0

# Helper functions
log_success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((CHECKS_PASSED++))
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
    ((CHECKS_FAILED++))
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((CHECKS_WARNING++))
}

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

header() {
    echo -e "\n${BLUE}=====================================\n$1\n=====================================${NC}\n"
}

# Start verification report
start_report() {
    cat > "$REPORT_FILE" << 'EOF'
# Production Optimization Verification Report

EOF
}

# Append to report
append_report() {
    echo "$1" >> "$REPORT_FILE"
}

# Final report summary
finish_report() {
    {
        echo ""
        echo "## Summary"
        echo ""
        echo "- ✅ Checks Passed: $CHECKS_PASSED"
        echo "- ❌ Checks Failed: $CHECKS_FAILED"
        echo "- ⚠️  Warnings: $CHECKS_WARNING"
        echo ""
        echo "**Generated**: $(date)"
    } >> "$REPORT_FILE"
}

# ==========================================
# Main Verification
# ==========================================

header "Production Optimization Verification"

start_report

# 1. Check Monitoring Stack
echo "Checking monitoring stack components..."
{
    echo "## 1. Monitoring Stack"
    echo ""
} >> "$REPORT_FILE"

if [[ -f "$PROJECT_ROOT/monitoring/prometheus/prometheus.yml" ]]; then
    log_success "Prometheus configuration found"
    echo "- Prometheus configuration: ✅" >> "$REPORT_FILE"
else
    log_error "Prometheus configuration missing"
    echo "- Prometheus configuration: ❌" >> "$REPORT_FILE"
fi

if [[ -f "$PROJECT_ROOT/monitoring/prometheus/alerts.yml" ]]; then
    log_success "Alert rules found"
    ALERT_COUNT=$(grep -c "alert:" "$PROJECT_ROOT/monitoring/prometheus/alerts.yml" || true)
    log_info "Found $ALERT_COUNT alert rules"
    echo "- Alert rules: ✅ ($ALERT_COUNT rules)" >> "$REPORT_FILE"
else
    log_error "Alert rules missing"
    echo "- Alert rules: ❌" >> "$REPORT_FILE"
fi

if [[ -f "$PROJECT_ROOT/docker-compose.monitoring.yml" ]]; then
    log_success "Monitoring stack compose file found"
    SERVICES=$(grep -E '^\s+\w+:$' "$PROJECT_ROOT/docker-compose.monitoring.yml" | wc -l)
    log_info "Contains $SERVICES monitoring services"
    echo "- Docker Compose: ✅ ($SERVICES services)" >> "$REPORT_FILE"
else
    log_error "Monitoring compose file missing"
    echo "- Docker Compose: ❌" >> "$REPORT_FILE"
fi

# 2. Check Redis Cache Implementation
echo ""
echo "Checking Redis cache implementation..."
{
    echo "## 2. Redis Cache Layer"
    echo ""
} >> "$REPORT_FILE"

if [[ -f "$PROJECT_ROOT/src/infrastructure/redis_cache.py" ]]; then
    log_success "Redis cache module found"
    LINES=$(wc -l < "$PROJECT_ROOT/src/infrastructure/redis_cache.py")
    log_info "Module size: $LINES lines"
    echo "- Redis cache module: ✅ ($LINES lines)" >> "$REPORT_FILE"
else
    log_error "Redis cache module missing"
    echo "- Redis cache module: ❌" >> "$REPORT_FILE"
fi

if grep -q "RedisCache" "$PROJECT_ROOT/src/main.py" 2>/dev/null; then
    log_success "Redis integrated in main.py"
    echo "- Redis initialization: ✅" >> "$REPORT_FILE"
else
    log_warning "Redis not initialized in main.py (manual integration needed)"
    echo "- Redis initialization: ⚠️ (manual integration needed)" >> "$REPORT_FILE"
fi

# 3. Check Database Optimization
echo ""
echo "Checking database optimization..."
{
    echo "## 3. Database Query Optimization"
    echo ""
} >> "$REPORT_FILE"

if [[ -f "$PROJECT_ROOT/src/infrastructure/query_optimization.py" ]]; then
    log_success "Query optimization patterns found"
    LINES=$(wc -l < "$PROJECT_ROOT/src/infrastructure/query_optimization.py")
    log_info "Pattern library: $LINES lines"
    echo "- Query optimization: ✅ ($LINES lines)" >> "$REPORT_FILE"
else
    log_error "Query optimization patterns missing"
    echo "- Query optimization: ❌" >> "$REPORT_FILE"
fi

# 4. Check Metrics Endpoint
echo ""
echo "Checking Prometheus metrics endpoint..."
{
    echo "## 4. Prometheus Metrics Endpoint"
    echo ""
} >> "$REPORT_FILE"

if grep -q '/metrics' "$PROJECT_ROOT/src/main.py" 2>/dev/null; then
    log_success "Metrics endpoint registered"
    echo "- Metrics endpoint: ✅" >> "$REPORT_FILE"
else
    log_error "Metrics endpoint not found in main.py"
    echo "- Metrics endpoint: ❌" >> "$REPORT_FILE"
fi

# 5. Check HA Configuration
echo ""
echo "Checking high availability configuration..."
{
    echo "## 5. High Availability Deployment"
    echo ""
} >> "$REPORT_FILE"

if [[ -f "$PROJECT_ROOT/deployment/docker-compose.ha.yml" ]]; then
    log_success "HA compose configuration found"
    REPLICAS=$(grep -c "backend_" "$PROJECT_ROOT/deployment/docker-compose.ha.yml" || true)
    echo "- HA Docker Compose: ✅ ($REPLICAS replicas)" >> "$REPORT_FILE"
else
    log_error "HA compose configuration missing"
    echo "- HA Docker Compose: ❌" >> "$REPORT_FILE"
fi

if [[ -d "$PROJECT_ROOT/deployment/kubernetes" ]]; then
    log_success "Kubernetes manifests found"
    K8S_FILES=$(find "$PROJECT_ROOT/deployment/kubernetes" -name "*.yml" 2>/dev/null | wc -l)
    echo "- Kubernetes manifests: ✅ ($K8S_FILES files)" >> "$REPORT_FILE"
else
    log_error "Kubernetes manifests missing"
    echo "- Kubernetes manifests: ❌" >> "$REPORT_FILE"
fi

# 6. Check Deployment Scripts
echo ""
echo "Checking deployment automation scripts..."
{
    echo "## 6. Deployment Automation"
    echo ""
} >> "$REPORT_FILE"

SCRIPTS_FOUND=0
if [[ -f "$PROJECT_ROOT/scripts/monitoring/deploy-monitoring.sh" ]]; then
    log_success "Monitoring deployment script found"
    ((SCRIPTS_FOUND++))
    echo "- Monitoring deployment: ✅" >> "$REPORT_FILE"
fi

if [[ -f "$PROJECT_ROOT/deployment/scripts/deploy-ha.sh" ]]; then
    log_success "HA deployment script found"
    ((SCRIPTS_FOUND++))
    echo "- HA deployment: ✅" >> "$REPORT_FILE"
fi

if [[ -f "$PROJECT_ROOT/deployment/quick-start.sh" ]]; then
    log_success "Quick start script found"
    ((SCRIPTS_FOUND++))
    echo "- Quick start: ✅" >> "$REPORT_FILE"
fi

echo "- Found $SCRIPTS_FOUND deployment scripts" >> "$REPORT_FILE"

# 7. Check Dependencies
echo ""
echo "Checking dependencies..."
{
    echo "## 7. Dependencies"
    echo ""
} >> "$REPORT_FILE"

if grep -q "prometheus-client" "$PROJECT_ROOT/pyproject.toml" 2>/dev/null; then
    log_success "prometheus-client dependency added"
    echo "- prometheus-client: ✅" >> "$REPORT_FILE"
else
    log_warning "prometheus-client not in pyproject.toml"
    echo "- prometheus-client: ⚠️" >> "$REPORT_FILE"
fi

if grep -q "redis" "$PROJECT_ROOT/pyproject.toml" 2>/dev/null; then
    log_success "redis dependency added"
    echo "- redis: ✅" >> "$REPORT_FILE"
else
    log_warning "redis not in pyproject.toml"
    echo "- redis: ⚠️" >> "$REPORT_FILE"
fi

# 8. Check Documentation
echo ""
echo "Checking documentation..."
{
    echo "## 8. Documentation"
    echo ""
} >> "$REPORT_FILE"

DOCS_FOUND=0
if [[ -f "$PROJECT_ROOT/PRODUCTION_OPTIMIZATION_DEPLOYMENT_GUIDE.md" ]]; then
    log_success "Deployment guide found"
    ((DOCS_FOUND++))
    echo "- Deployment guide: ✅" >> "$REPORT_FILE"
fi

if [[ -f "$PROJECT_ROOT/deployment/README.md" ]]; then
    log_success "HA deployment README found"
    ((DOCS_FOUND++))
    echo "- HA README: ✅" >> "$REPORT_FILE"
fi

if [[ -f "$PROJECT_ROOT/monitoring/README.md" ]]; then
    log_success "Monitoring README found"
    ((DOCS_FOUND++))
    echo "- Monitoring README: ✅" >> "$REPORT_FILE"
fi

echo "- Found $DOCS_FOUND documentation files" >> "$REPORT_FILE"

# ==========================================
# Summary & Next Steps
# ==========================================

echo ""
header "Verification Complete"

echo "Summary:"
echo "  ✅ Passed: $CHECKS_PASSED"
echo "  ❌ Failed: $CHECKS_FAILED"
echo "  ⚠️  Warnings: $CHECKS_WARNING"
echo ""

finish_report

echo "Full report saved to: $REPORT_FILE"
echo ""

# Recommendations
echo "Next Steps:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1️⃣  Phase 1: Deploy Monitoring Stack"
echo "   cd $PROJECT_ROOT"
echo "   docker-compose -f docker-compose.monitoring.yml up -d"
echo "   ./scripts/monitoring/deploy-monitoring.sh verify"
echo ""
echo "2️⃣  Phase 2: Integrate Redis Cache"
echo "   - Deploy Redis instance"
echo "   - Update .env with REDIS_HOST and REDIS_PORT"
echo "   - Uncomment Redis initialization in src/main.py"
echo "   - Enable cache middleware"
echo ""
echo "3️⃣  Phase 3: Deploy to Production"
echo "   - Monitoring stack to Coolify"
echo "   - Redis to Coolify"
echo "   - Backend with cache integration"
echo "   - HA configuration with load balancing"
echo ""
echo "4️⃣  Phase 4: Verify Metrics & Performance"
echo "   - Access Grafana: http://localhost:3001"
echo "   - Check metrics: http://localhost:8000/metrics"
echo "   - Monitor cache hit rate and latency"
echo "   - Verify alert notifications"
echo ""
echo "For detailed instructions, see:"
echo "  📖 $PROJECT_ROOT/PRODUCTION_OPTIMIZATION_DEPLOYMENT_GUIDE.md"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Exit with appropriate code
if [[ $CHECKS_FAILED -gt 0 ]]; then
    exit 1
else
    exit 0
fi
