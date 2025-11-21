#!/bin/bash
# GitHub Secrets Configuration Verification Script
# 验证 GitHub Secrets 和 Coolify 连接
#
# 使用方式:
# chmod +x scripts/verify-secrets.sh
# ./scripts/verify-secrets.sh
#

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

echo -e "${BLUE}════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}GitHub Secrets & Coolify Configuration Verification${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════${NC}"
echo ""

# Step 1: Check if running in GitHub Actions or locally
log_info "Checking environment..."

if [ -z "$GITHUB_ACTIONS" ]; then
    log_warn "Not running in GitHub Actions environment"
    log_info "This script should be run in GitHub Actions CI/CD pipeline"
    echo ""
    log_info "To test locally, set environment variables:"
    echo ""
    echo "  export COOLIFY_API_TOKEN='your_token'"
    echo "  export COOLIFY_DEV_APP_UUID='your_dev_uuid'"
    echo ""
else
    log_success "Running in GitHub Actions"
fi

# Step 2: Check required environment variables
echo ""
log_info "Verifying environment variables..."
MISSING_VARS=0

check_env_var() {
    local var_name=$1
    local var_value=${!var_name}

    if [ -z "$var_value" ]; then
        log_error "Missing: $var_name"
        MISSING_VARS=$((MISSING_VARS + 1))
    else
        # 只显示前几个字符用于验证
        local masked="${var_value:0:5}...${var_value: -5}"
        log_success "Found: $var_name = $masked"
    fi
}

check_env_var "COOLIFY_TOKEN"
check_env_var "COOLIFY_DEV_APP_UUID"
check_env_var "COOLIFY_STAGING_APP_UUID"
check_env_var "COOLIFY_PROD_APP_UUID"

if [ $MISSING_VARS -gt 0 ]; then
    log_error "Missing $MISSING_VARS required environment variables"
    log_info "Please configure them in GitHub Secrets"
    exit 1
fi

log_success "All required environment variables are present"

# Step 3: Test Coolify API connection
echo ""
log_info "Testing Coolify API connection..."

COOLIFY_API="${COOLIFY_URL:-https://coolpanel.jackcwf.com}/api/v1"

# Test health endpoint
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET \
    -H "Authorization: Bearer ${COOLIFY_TOKEN}" \
    "${COOLIFY_API}/health")

HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n 1)
BODY=$(echo "$HEALTH_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" == "200" ]; then
    log_success "Coolify API health check passed (HTTP 200)"
else
    log_error "Coolify API health check failed (HTTP $HTTP_CODE)"
    echo "Response: $BODY"
    exit 1
fi

# Step 4: Verify app UUIDs
echo ""
log_info "Verifying application UUIDs..."

verify_app_uuid() {
    local env_name=$1
    local uuid=$2

    log_info "Checking $env_name application ($uuid)..."

    APP_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET \
        -H "Authorization: Bearer ${COOLIFY_TOKEN}" \
        "${COOLIFY_API}/applications/${uuid}")

    HTTP_CODE=$(echo "$APP_RESPONSE" | tail -n 1)
    BODY=$(echo "$APP_RESPONSE" | head -n -1)

    if [ "$HTTP_CODE" == "200" ]; then
        STATUS=$(echo "$BODY" | jq -r '.status // "unknown"' 2>/dev/null || echo "unknown")
        log_success "$env_name app found (Status: $STATUS)"
        return 0
    else
        log_error "$env_name app not found (HTTP $HTTP_CODE)"
        return 1
    fi
}

verify_app_uuid "Development" "$COOLIFY_DEV_APP_UUID"
verify_app_uuid "Staging" "$COOLIFY_STAGING_APP_UUID"
verify_app_uuid "Production" "$COOLIFY_PROD_APP_UUID"

# Step 5: Summary
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════${NC}"
log_success "Verification complete!"
echo -e "${BLUE}════════════════════════════════════════════════════${NC}"
echo ""
log_info "Configuration Status:"
echo "  ✓ All environment variables configured"
echo "  ✓ Coolify API connectivity verified"
echo "  ✓ Application UUIDs accessible"
echo ""
log_info "Next steps:"
echo "  1. Push changes to GitHub main branch"
echo "  2. Monitor GitHub Actions for deployment"
echo "  3. Verify application health at deployment URL"
echo ""
