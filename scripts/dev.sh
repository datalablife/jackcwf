#!/bin/bash
# Local development startup script
# This script sets up and runs the application in development mode

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

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

log_step() {
    echo -e "\n${BLUE}==>${NC} $1\n"
}

# =============================================================================
# Banner
# =============================================================================

cat << "EOF"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║                   Reflex Development Server                  ║
║                                                              ║
║  Local development environment with hot reload               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF

echo ""

# =============================================================================
# 1. Check Prerequisites
# =============================================================================

log_step "Checking prerequisites..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    log_error "uv is not installed. Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi
log_info "uv is installed"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    log_error "Node.js is not installed. Install from: https://nodejs.org/"
    exit 1
fi
log_info "Node.js $(node --version) is installed"

# Check if Python is available
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    log_error "Python is not installed"
    exit 1
fi
log_info "Python is installed"

# =============================================================================
# 2. Environment Setup
# =============================================================================

log_step "Setting up environment..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    log_warn ".env file not found"
    if [ -f ".env.example" ]; then
        log_info "Creating .env from .env.example..."
        cp .env.example .env
        log_warn "Please update .env with your actual configuration"
    else
        log_warn "No .env.example found. You may need to create .env manually"
    fi
else
    log_info ".env file found"
fi

# Load environment variables (safe method - handles special characters)
if [ -f ".env" ]; then
    log_info "Loading environment variables from .env..."
    set -a
    source .env
    set +a
fi

# =============================================================================
# 3. Install Dependencies
# =============================================================================

log_step "Installing dependencies..."

# Check if virtual environment exists and is up to date
if [ ! -d ".venv" ]; then
    log_info "Virtual environment not found, creating..."
    uv sync
else
    log_info "Virtual environment found, checking for updates..."
    uv sync
fi

log_info "Dependencies installed successfully"

# =============================================================================
# 4. Database Setup (if needed)
# =============================================================================

# Skip database checks in development mode (non-interactive startup)
# In production, use proper health checks and migration management
log_step "Database setup..."

if [ -z "$DATABASE_URL" ]; then
    log_warn "DATABASE_URL not set, skipping database checks"
else
    log_info "DATABASE_URL is configured (will be checked on first API call)"
    log_info "To test database connection manually: uv run python -c \"import asyncpg; print('asyncpg OK')\""
fi

# =============================================================================
# 5. Clean Previous Build (optional)
# =============================================================================

if [ "$1" == "--clean" ]; then
    log_step "Cleaning previous build..."
    rm -rf .web
    log_info "Build cache cleaned"
fi

# =============================================================================
# 6. Start Development Server
# =============================================================================

log_step "Starting development server..."

log_info "Application will be available at:"
log_info "  Frontend: http://localhost:3000"
log_info "  Backend:  http://localhost:8000"
echo ""
log_info "Press Ctrl+C to stop the server"
echo ""

# Start Reflex in development mode
# This enables hot reload and verbose logging
uv run reflex run \
    --env dev \
    --loglevel info \
    --backend-host 0.0.0.0 \
    --backend-port 8000 \
    --frontend-host 0.0.0.0 \
    --frontend-port 3000
