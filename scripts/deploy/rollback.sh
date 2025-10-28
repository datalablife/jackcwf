#!/bin/bash
# Rollback Script
# Usage: ./rollback.sh <environment> [version]

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
if [ -z "$1" ]; then
    log_error "Usage: $0 <environment> [version]"
    log_info "Example: $0 production"
    log_info "Example: $0 production 20231027-154532-def4567"
    exit 1
fi

ENVIRONMENT=$1
ROLLBACK_VERSION=${2:-}

log_info "Starting rollback for ${ENVIRONMENT} environment"

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

# Get deployment history
log_info "Fetching deployment history..."
DEPLOYMENTS=$(call_coolify_api "/applications/${COOLIFY_APP_UUID}/deployments")

if [ -z "$ROLLBACK_VERSION" ]; then
    # Find the last successful deployment
    log_info "Looking for last successful deployment..."

    LAST_SUCCESSFUL=$(echo "$DEPLOYMENTS" | jq -r '
        .deployments[]
        | select(.status == "success" or .status == "completed")
        | select(.current != true)
        | .version
        | select(. != null)
    ' | head -1)

    if [ -z "$LAST_SUCCESSFUL" ]; then
        log_error "No previous successful deployment found"
        exit 1
    fi

    ROLLBACK_VERSION="$LAST_SUCCESSFUL"
    log_info "Found last successful version: ${ROLLBACK_VERSION}"
else
    log_info "Using specified version: ${ROLLBACK_VERSION}"
fi

# Confirm rollback
log_warn "================================================"
log_warn "ROLLBACK CONFIRMATION"
log_warn "================================================"
log_warn "Environment:     ${ENVIRONMENT}"
log_warn "Rollback to:     ${ROLLBACK_VERSION}"
log_warn "Application:     ${COOLIFY_APP_UUID}"
log_warn "================================================"

# In CI environment, skip confirmation
if [ "${CI:-false}" != "true" ]; then
    read -p "Continue with rollback? (yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        log_info "Rollback cancelled"
        exit 0
    fi
fi

# Create backup of current state
log_info "Creating backup of current state..."
BACKUP_DIR="${PROJECT_ROOT}/backups/${ENVIRONMENT}"
mkdir -p "$BACKUP_DIR"

CURRENT_STATE=$(call_coolify_api "/applications/${COOLIFY_APP_UUID}")
echo "$CURRENT_STATE" > "${BACKUP_DIR}/pre-rollback-$(date +%Y%m%d-%H%M%S).json"
log_info "✓ Backup created"

# Update environment to rollback version
log_info "Updating environment to rollback version..."
ROLLBACK_ENV=$(cat <<EOF
{
    "VERSION": "${ROLLBACK_VERSION}",
    "ROLLBACK": "true",
    "ROLLBACK_AT": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
)

call_coolify_api "/applications/${COOLIFY_APP_UUID}/envs" "PATCH" "$ROLLBACK_ENV" > /dev/null
log_info "✓ Environment updated"

# Trigger rollback deployment
log_info "Triggering rollback deployment..."
DEPLOY_DATA=$(cat <<EOF
{
    "force": true,
    "commit": "${ROLLBACK_VERSION}",
    "comment": "Rollback to ${ROLLBACK_VERSION}"
}
EOF
)

DEPLOY_RESPONSE=$(call_coolify_api "/applications/${COOLIFY_APP_UUID}/deploy" "POST" "$DEPLOY_DATA")
DEPLOYMENT_ID=$(echo "$DEPLOY_RESPONSE" | jq -r '.deployment_uuid // empty')

if [ -z "$DEPLOYMENT_ID" ]; then
    log_error "Failed to trigger rollback deployment"
    echo "$DEPLOY_RESPONSE" | jq '.'
    exit 1
fi

log_info "✓ Rollback deployment triggered: ${DEPLOYMENT_ID}"

# Monitor rollback deployment
log_info "Monitoring rollback progress..."
MAX_WAIT=600  # 10 minutes
ELAPSED=0
CHECK_INTERVAL=10

while [ $ELAPSED -lt $MAX_WAIT ]; do
    DEPLOY_STATUS=$(call_coolify_api "/deployments/${DEPLOYMENT_ID}")
    STATUS=$(echo "$DEPLOY_STATUS" | jq -r '.status // "unknown"')

    log_info "Rollback status: ${STATUS} (${ELAPSED}s elapsed)"

    case $STATUS in
        success|completed)
            log_info "✓ Rollback completed successfully"
            break
            ;;
        failed|error)
            log_error "Rollback failed"
            echo "$DEPLOY_STATUS" | jq '.'
            exit 1
            ;;
        cancelled)
            log_error "Rollback was cancelled"
            exit 1
            ;;
        *)
            sleep $CHECK_INTERVAL
            ELAPSED=$((ELAPSED + CHECK_INTERVAL))
            ;;
    esac
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    log_error "Rollback timeout after ${MAX_WAIT}s"
    exit 1
fi

# Wait for application to stabilize
log_info "Waiting for application to stabilize..."
sleep 30

# Run health checks
log_info "Running health checks..."

case $ENVIRONMENT in
    production)
        APP_URL="https://jackcwf.com"
        ;;
    staging)
        APP_URL="https://staging.jackcwf.com"
        ;;
    development)
        APP_URL="https://dev.jackcwf.com"
        ;;
esac

if [ -x "${SCRIPT_DIR}/health-check.sh" ]; then
    if "${SCRIPT_DIR}/health-check.sh" "$APP_URL"; then
        log_info "✓ Health checks passed"
    else
        log_error "Health checks failed after rollback"
        log_error "Manual intervention may be required"
        exit 1
    fi
else
    log_warn "Health check script not found, skipping validation"
fi

# Summary
log_info "================================================"
log_info "Rollback Summary"
log_info "================================================"
log_info "Environment:      ${ENVIRONMENT}"
log_info "Rolled back to:   ${ROLLBACK_VERSION}"
log_info "Deployment ID:    ${DEPLOYMENT_ID}"
log_info "Application URL:  ${APP_URL}"
log_info "Completed at:     $(date -u +%Y-%m-%d\ %H:%M:%S\ UTC)"
log_info "================================================"

log_info "✅ Rollback to ${ENVIRONMENT} completed successfully"
exit 0
