#!/bin/bash
# Container entrypoint script for Reflex application
# This script runs inside the Docker container and handles:
# - Environment validation
# - Database migrations (if needed)
# - Graceful startup and shutdown

set -e  # Exit on error

# Color output for better visibility in logs
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

# Graceful shutdown handler
shutdown_handler() {
    log_info "Received shutdown signal, gracefully stopping..."

    # If we have a PID file, send SIGTERM to the process
    if [ -f /tmp/reflex.pid ]; then
        PID=$(cat /tmp/reflex.pid)
        log_info "Sending SIGTERM to process $PID..."
        kill -TERM "$PID" 2>/dev/null || true

        # Wait for process to exit (max 30 seconds)
        for i in {1..30}; do
            if ! kill -0 "$PID" 2>/dev/null; then
                log_info "Process exited gracefully"
                break
            fi
            sleep 1
        done

        # Force kill if still running
        if kill -0 "$PID" 2>/dev/null; then
            log_warn "Process did not exit, forcing shutdown..."
            kill -KILL "$PID" 2>/dev/null || true
        fi

        rm -f /tmp/reflex.pid
    fi

    exit 0
}

# Register signal handlers
trap shutdown_handler SIGTERM SIGINT

# =============================================================================
# 1. Environment Validation
# =============================================================================

log_info "Starting Reflex application in production mode..."
log_info "Environment: ${REFLEX_ENV:-production}"

# Check required environment variables
REQUIRED_VARS=(
    "REFLEX_ENV"
    "FRONTEND_PORT"
    "BACKEND_PORT"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        log_error "Required environment variable $var is not set"
        exit 1
    fi
done

log_info "Environment validation passed"

# =============================================================================
# 2. Database Connection Check (if DATABASE_URL is set)
# =============================================================================

if [ -n "$DATABASE_URL" ]; then
    log_info "Database URL detected, checking connection..."

    # Wait for database to be ready (max 30 seconds)
    MAX_RETRIES=30
    RETRY_COUNT=0

    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if python -c "
import sys
try:
    from sqlalchemy import create_engine
    engine = create_engine('$DATABASE_URL')
    with engine.connect() as conn:
        conn.execute('SELECT 1')
    print('Database connection successful')
    sys.exit(0)
except Exception as e:
    print(f'Database connection failed: {e}')
    sys.exit(1)
" 2>/dev/null; then
            log_info "Database connection successful"
            break
        fi

        RETRY_COUNT=$((RETRY_COUNT + 1))
        log_warn "Database connection attempt $RETRY_COUNT/$MAX_RETRIES failed, retrying..."
        sleep 1
    done

    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        log_error "Database connection failed after $MAX_RETRIES attempts"
        exit 1
    fi

    # =============================================================================
    # 3. Database Migrations (optional)
    # =============================================================================

    # Uncomment this section when you have Alembic migrations
    # log_info "Running database migrations..."
    # if alembic upgrade head; then
    #     log_info "Database migrations completed successfully"
    # else
    #     log_error "Database migrations failed"
    #     exit 1
    # fi
else
    log_warn "DATABASE_URL not set, skipping database checks"
fi

# =============================================================================
# 4. Pre-flight Checks
# =============================================================================

log_info "Running pre-flight checks..."

# Check if Python packages are installed
if ! python -c "import reflex" 2>/dev/null; then
    log_error "Reflex package not found. Did you run 'uv sync'?"
    exit 1
fi

# Check if .web directory exists (frontend build)
if [ ! -d ".web" ]; then
    log_warn ".web directory not found, Reflex will initialize it on first run"
fi

log_info "Pre-flight checks passed"

# =============================================================================
# 5. Start Application
# =============================================================================

log_info "Starting Reflex application..."
log_info "Frontend: http://0.0.0.0:${FRONTEND_PORT}"
log_info "Backend: http://0.0.0.0:${BACKEND_PORT}"

# Start Reflex in production mode
# The --env flag ensures production optimizations
# The --loglevel controls output verbosity
python -m reflex run \
    --env production \
    --loglevel info \
    --backend-host 0.0.0.0 \
    --backend-port "${BACKEND_PORT}" \
    --frontend-host 0.0.0.0 \
    --frontend-port "${FRONTEND_PORT}" &

# Store the PID for graceful shutdown
REFLEX_PID=$!
echo $REFLEX_PID > /tmp/reflex.pid

log_info "Reflex started with PID $REFLEX_PID"

# Wait for the process to exit
wait $REFLEX_PID
EXIT_CODE=$?

# Clean up PID file
rm -f /tmp/reflex.pid

log_info "Reflex process exited with code $EXIT_CODE"
exit $EXIT_CODE
