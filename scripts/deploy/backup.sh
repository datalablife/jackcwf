#!/bin/bash
# Backup Script
# Usage: ./backup.sh <environment>

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKUP_ROOT="${PROJECT_ROOT}/backups"

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
    log_error "Usage: $0 <environment>"
    log_info "Example: $0 production"
    exit 1
fi

ENVIRONMENT=$1
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="${BACKUP_ROOT}/${ENVIRONMENT}/${TIMESTAMP}"

log_info "Creating backup for ${ENVIRONMENT} environment"

# Validate environment
case $ENVIRONMENT in
    development|staging|production)
        log_info "Valid environment: ${ENVIRONMENT}"
        ;;
    *)
        log_error "Invalid environment: ${ENVIRONMENT}"
        exit 1
        ;;
esac

# Create backup directory
mkdir -p "$BACKUP_DIR"
log_info "Backup directory: ${BACKUP_DIR}"

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
    curl -s -H "Authorization: Bearer ${COOLIFY_TOKEN}" "${COOLIFY_API}${endpoint}"
}

# Backup application configuration
log_info "Backing up application configuration..."
APP_CONFIG=$(call_coolify_api "/applications/${COOLIFY_APP_UUID}")
echo "$APP_CONFIG" | jq '.' > "${BACKUP_DIR}/app-config.json"
log_info "✓ Application config saved"

# Backup environment variables
log_info "Backing up environment variables..."
ENV_VARS=$(call_coolify_api "/applications/${COOLIFY_APP_UUID}/envs")
echo "$ENV_VARS" | jq '.' > "${BACKUP_DIR}/env-vars.json"
log_info "✓ Environment variables saved"

# Backup deployment history
log_info "Backing up deployment history..."
DEPLOYMENTS=$(call_coolify_api "/applications/${COOLIFY_APP_UUID}/deployments")
echo "$DEPLOYMENTS" | jq '.' > "${BACKUP_DIR}/deployment-history.json"
log_info "✓ Deployment history saved"

# Get current version
CURRENT_VERSION=$(echo "$ENV_VARS" | jq -r '.VERSION // "unknown"')
log_info "Current version: ${CURRENT_VERSION}"

# Create backup metadata
log_info "Creating backup metadata..."
cat > "${BACKUP_DIR}/metadata.json" <<EOF
{
    "environment": "${ENVIRONMENT}",
    "timestamp": "${TIMESTAMP}",
    "datetime": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "version": "${CURRENT_VERSION}",
    "app_uuid": "${COOLIFY_APP_UUID}",
    "backup_dir": "${BACKUP_DIR}"
}
EOF
log_info "✓ Metadata created"

# Create restore instructions
log_info "Creating restore instructions..."
cat > "${BACKUP_DIR}/RESTORE.md" <<EOF
# Restore Instructions

## Backup Information
- **Environment**: ${ENVIRONMENT}
- **Timestamp**: ${TIMESTAMP}
- **Version**: ${CURRENT_VERSION}
- **App UUID**: ${COOLIFY_APP_UUID}

## Files in this backup
- \`app-config.json\`: Application configuration
- \`env-vars.json\`: Environment variables
- \`deployment-history.json\`: Deployment history
- \`metadata.json\`: Backup metadata

## How to restore

### Option 1: Using rollback script
\`\`\`bash
cd ${PROJECT_ROOT}
./scripts/deploy/rollback.sh ${ENVIRONMENT} ${CURRENT_VERSION}
\`\`\`

### Option 2: Manual restore
1. Review the backup files
2. Update environment variables via Coolify UI or API
3. Trigger a new deployment with the backed-up version

### Option 3: Using Coolify API
\`\`\`bash
# Restore environment variables
curl -X PATCH \\
  -H "Authorization: Bearer \$COOLIFY_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d @env-vars.json \\
  "${COOLIFY_API}/applications/${COOLIFY_APP_UUID}/envs"

# Trigger deployment
curl -X POST \\
  -H "Authorization: Bearer \$COOLIFY_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"force": true, "commit": "${CURRENT_VERSION}"}' \\
  "${COOLIFY_API}/applications/${COOLIFY_APP_UUID}/deploy"
\`\`\`

## Verification
After restore, verify the application is working:
\`\`\`bash
./scripts/deploy/health-check.sh <app-url>
\`\`\`

## Support
If you encounter issues, check:
- Coolify deployment logs
- Application health endpoints
- Backup files in this directory
EOF
log_info "✓ Restore instructions created"

# Compress backup (optional)
if command -v tar &> /dev/null; then
    log_info "Compressing backup..."
    cd "$BACKUP_ROOT/${ENVIRONMENT}"
    tar -czf "${TIMESTAMP}.tar.gz" "${TIMESTAMP}/"
    log_info "✓ Backup compressed: ${TIMESTAMP}.tar.gz"
fi

# Cleanup old backups (keep last 10)
log_info "Cleaning up old backups..."
cd "$BACKUP_ROOT/${ENVIRONMENT}"
ls -t | grep -E '^[0-9]{8}-[0-9]{6}$' | tail -n +11 | xargs -r rm -rf
log_info "✓ Old backups cleaned up (keeping last 10)"

# Summary
log_info "================================================"
log_info "Backup Summary"
log_info "================================================"
log_info "Environment:    ${ENVIRONMENT}"
log_info "Version:        ${CURRENT_VERSION}"
log_info "Timestamp:      ${TIMESTAMP}"
log_info "Backup Dir:     ${BACKUP_DIR}"
log_info "================================================"

log_info "✅ Backup completed successfully"
echo "${BACKUP_DIR}"
exit 0
