#!/bin/bash
# Docker Container Startup Script
# Initializes environment and starts Supervisor

set -e

# ============================================
# Configuration
# ============================================

LOG_DIR="/var/log/app"
APP_LOG_DIR="/app/logs"
SUPERVISOR_LOG_DIR="/var/log/supervisor"

# ============================================
# Logging Functions
# ============================================

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $1"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $1" >&2
}

log_warn() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARN] $1"
}

# ============================================
# Initialization
# ============================================

log "=========================================="
log "Docker Container Startup"
log "=========================================="

# Create log directories
mkdir -p "$LOG_DIR" "$APP_LOG_DIR" "$SUPERVISOR_LOG_DIR"
chmod 777 "$LOG_DIR" "$APP_LOG_DIR" "$SUPERVISOR_LOG_DIR"

log "Log directories created"

# ============================================
# Environment Variable Verification
# ============================================

log "Verifying environment variables..."

required_vars=(
    "DATABASE_URL"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        log_error "Required environment variable not set: $var"
        exit 1
    fi
done

log "Required environment variables verified"

# ============================================
# Database Connection Check
# ============================================

log "Checking database connectivity..."

DB_CHECK_TIMEOUT=30
DB_CHECK_INTERVAL=2
DB_CHECKED=false
DB_CHECK_RESULT=""

for ((i=0; i<DB_CHECK_TIMEOUT; i+=DB_CHECK_INTERVAL)); do
    if python3 << 'EOF'
import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def check_db():
    try:
        engine = create_async_engine(os.getenv("DATABASE_URL"), echo=False)
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        return True
    except Exception as e:
        print(f"DB Error: {type(e).__name__}: {str(e)[:100]}")
        return False

if asyncio.run(check_db()):
    exit(0)
else:
    exit(1)
EOF
    then
        DB_CHECKED=true
        DB_CHECK_RESULT="✅ Database connection successful"
        break
    fi
    log "Database not ready yet, retrying in ${DB_CHECK_INTERVAL}s... (${i}/${DB_CHECK_TIMEOUT}s)"
    sleep $DB_CHECK_INTERVAL
done

if [ "$DB_CHECKED" = true ]; then
    log "$DB_CHECK_RESULT"
else
    log_warn "⚠️  Database connection failed after ${DB_CHECK_TIMEOUT}s"
    log_warn "Continuing startup anyway - Supervisor will start services"
    log_warn "This may affect backend API functionality, but frontend and Nginx will still run"
fi

# ============================================
# Environment Initialization
# ============================================

log "Initializing application environment..."

# Ensure .env file exists
if [ ! -f "/app/.env" ]; then
    log_warn ".env file not found, using .env.example as template"
    if [ -f "/app/.env.example" ]; then
        cp /app/.env.example /app/.env
    fi
fi

# Set permissions
chmod 644 /app/.env 2>/dev/null || true

log "Environment initialized"

# ============================================
# Pre-startup Checks
# ============================================

log "Pre-startup checks..."

# Check required files (use correct supervisor config path)
files_to_check=(
    "/etc/supervisor/supervisord.conf"
    "/app/scripts/monitor/health_monitor.py"
)

for file in "${files_to_check[@]}"; do
    if [ ! -f "$file" ]; then
        log_error "Required file not found: $file"
        exit 1
    fi
done

log "All required files present"

# ============================================
# Startup Logging
# ============================================

log "=========================================="
log "Starting Supervisor..."
log "=========================================="

# ============================================
# Start Supervisor (use correct config path)
# Note: Do NOT pass "$@" here as Dockerfile CMD already contains the full supervisord command
# ============================================

exec supervisord -c /etc/supervisor/supervisord.conf
