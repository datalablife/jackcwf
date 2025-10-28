#!/bin/bash
# Coolify Deployment Script
# Usage: ./deploy-coolify.sh <environment> <version>

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

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
if [ -z "$1" ] || [ -z "$2" ]; then
    log_error "Usage: $0 <environment> <version>"
    log_info "Example: $0 development 20231028-123456-abc1234"
    exit 1
fi

ENVIRONMENT=$1
VERSION=$2

log_info "Starting deployment to ${ENVIRONMENT} environment"
log_info "Version: ${VERSION}"

# Validate environment
case $ENVIRONMENT in
    development|staging|production)
        log_info "Valid environment: ${ENVIRONMENT}"
        ;;
    *)
        log_error "Invalid environment: ${ENVIRONMENT}"
        log_error "Must be one of: development, staging, production"
        exit 1
        ;;
esac

# Check required environment variables
if [ -z "$COOLIFY_TOKEN" ]; then
    log_error "COOLIFY_TOKEN environment variable is not set"
    exit 1
fi

if [ -z "$COOLIFY_APP_UUID" ]; then
    log_error "COOLIFY_APP_UUID environment variable is not set"
    exit 1
fi

# Set Coolify API URL
COOLIFY_API="${COOLIFY_URL:-https://coolpanel.jackcwf.com}/api/v1"

log_info "Coolify API: ${COOLIFY_API}"
log_info "App UUID: ${COOLIFY_APP_UUID}"

# Function to call Coolify API
call_coolify_api() {
    local endpoint=$1
    local method=${2:-GET}
    local data=${3:-}

    if [ -n "$data" ]; then
        curl -s -X "$method" \
            -H "Authorization: Bearer ${COOLIFY_TOKEN}" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "${COOLIFY_API}${endpoint}"
    else
        curl -s -X "$method" \
            -H "Authorization: Bearer ${COOLIFY_TOKEN}" \
            "${COOLIFY_API}${endpoint}"
    fi
}

# Check Coolify connection
log_info "Verifying Coolify connection..."
if ! call_coolify_api "/health" | grep -q "ok"; then
    log_error "Failed to connect to Coolify API"
    exit 1
fi
log_info "✓ Coolify connection verified"

# Get current application status
log_info "Fetching current application status..."
APP_STATUS=$(call_coolify_api "/applications/${COOLIFY_APP_UUID}")
echo "$APP_STATUS" | jq '.' || log_warn "Could not parse app status"

# Update environment variables
log_info "Updating environment variables..."
ENV_VARS=$(cat <<EOF
{
    "VERSION": "${VERSION}",
    "ENVIRONMENT": "${ENVIRONMENT}",
    "DEPLOYED_AT": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
)

call_coolify_api "/applications/${COOLIFY_APP_UUID}/envs" "PATCH" "$ENV_VARS" > /dev/null
log_info "✓ Environment variables updated"

# Trigger deployment
log_info "Triggering deployment..."
DEPLOY_RESPONSE=$(call_coolify_api "/applications/${COOLIFY_APP_UUID}/deploy" "POST" '{"force": true}')
DEPLOYMENT_ID=$(echo "$DEPLOY_RESPONSE" | jq -r '.deployment_uuid // empty')

if [ -z "$DEPLOYMENT_ID" ]; then
    log_error "Failed to trigger deployment"
    echo "$DEPLOY_RESPONSE" | jq '.'
    exit 1
fi

log_info "✓ Deployment triggered: ${DEPLOYMENT_ID}"

# Monitor deployment status
log_info "Monitoring deployment progress..."
MAX_WAIT=600  # 10 minutes
ELAPSED=0
CHECK_INTERVAL=10

while [ $ELAPSED -lt $MAX_WAIT ]; do
    DEPLOY_STATUS=$(call_coolify_api "/deployments/${DEPLOYMENT_ID}")
    STATUS=$(echo "$DEPLOY_STATUS" | jq -r '.status // "unknown"')

    log_info "Deployment status: ${STATUS} (${ELAPSED}s elapsed)"

    case $STATUS in
        success|completed)
            log_info "✓ Deployment completed successfully"
            break
            ;;
        failed|error)
            log_error "Deployment failed"
            echo "$DEPLOY_STATUS" | jq '.'
            exit 1
            ;;
        cancelled)
            log_error "Deployment was cancelled"
            exit 1
            ;;
        *)
            sleep $CHECK_INTERVAL
            ELAPSED=$((ELAPSED + CHECK_INTERVAL))
            ;;
    esac
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    log_error "Deployment timeout after ${MAX_WAIT}s"
    exit 1
fi

# Get deployment logs
log_info "Fetching deployment logs..."
LOGS=$(call_coolify_api "/deployments/${DEPLOYMENT_ID}/logs")
echo "$LOGS" | tail -50

# Verify deployment
log_info "Verifying deployment..."
NEW_APP_STATUS=$(call_coolify_api "/applications/${COOLIFY_APP_UUID}")
NEW_STATUS=$(echo "$NEW_APP_STATUS" | jq -r '.status // "unknown"')

if [ "$NEW_STATUS" != "running" ]; then
    log_warn "Application status is not 'running': ${NEW_STATUS}"
fi

log_info "✓ Deployment verification complete"

# Summary
log_info "================================================"
log_info "Deployment Summary"
log_info "================================================"
log_info "Environment:    ${ENVIRONMENT}"
log_info "Version:        ${VERSION}"
log_info "Deployment ID:  ${DEPLOYMENT_ID}"
log_info "Status:         ${NEW_STATUS}"
log_info "Completed at:   $(date -u +%Y-%m-%d\ %H:%M:%S\ UTC)"
log_info "================================================"

log_info "✅ Deployment to ${ENVIRONMENT} completed successfully"
exit 0
