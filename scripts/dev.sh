#!/bin/bash
# Development startup script for AI Data Analyzer
# Starts both frontend (React + Vite) and backend (FastAPI) services
# This script manages both services and provides unified logging

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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

log_service() {
    echo -e "${CYAN}[$1]${NC} $2"
}

# =============================================================================
# Banner
# =============================================================================

cat << "EOF"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           AI Data Analyzer Development Server                ║
║                                                              ║
║  Full-stack development environment with hot reload          ║
║  - Frontend: React 19 + Vite + TypeScript                    ║
║  - Backend: FastAPI + Python + SQLAlchemy                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF

echo ""

# =============================================================================
# 1. Check Prerequisites
# =============================================================================

log_step "Checking prerequisites..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    log_error "Node.js is not installed. Install from: https://nodejs.org/"
    exit 1
fi
log_info "Node.js $(node --version) is installed"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    log_error "npm is not installed"
    exit 1
fi
log_info "npm $(npm --version) is installed"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    log_error "uv is not installed. Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi
log_info "uv is installed"

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
# 3. Backend Setup
# =============================================================================

log_step "Setting up backend..."

# Check if virtual environment exists and is up to date
if [ ! -d ".venv" ]; then
    log_info "Virtual environment not found, creating..."
    uv sync
else
    log_info "Virtual environment found, checking for updates..."
    uv sync
fi

log_info "Backend dependencies installed successfully"

# =============================================================================
# 4. Frontend Setup
# =============================================================================

log_step "Setting up frontend..."

if [ ! -d "frontend/node_modules" ]; then
    log_info "Frontend dependencies not found, installing..."
    npm install --prefix frontend
else
    log_info "Frontend dependencies found"
    # Ensure latest dependencies
    npm ci --prefix frontend
fi

log_info "Frontend dependencies installed successfully"

# =============================================================================
# 5. Database Setup
# =============================================================================

log_step "Database setup..."

if [ -z "$DATABASE_URL" ]; then
    log_warn "DATABASE_URL not set, skipping database checks"
else
    log_info "DATABASE_URL is configured (will be checked on first API call)"
    log_info "To test database connection manually: uv run python -c \"import asyncpg; print('asyncpg OK')\""
fi

# =============================================================================
# 6. Cleanup Handler
# =============================================================================

# Store PIDs of background processes
FRONTEND_PID=""
BACKEND_PID=""

# Cleanup function to kill all child processes
cleanup() {
    log_warn "Shutting down services..."

    if [ -n "$FRONTEND_PID" ]; then
        log_service "FRONTEND" "Stopping (PID: $FRONTEND_PID)"
        kill $FRONTEND_PID 2>/dev/null || true
    fi

    if [ -n "$BACKEND_PID" ]; then
        log_service "BACKEND" "Stopping (PID: $BACKEND_PID)"
        kill $BACKEND_PID 2>/dev/null || true
    fi

    # Wait for processes to terminate gracefully
    sleep 1

    # Force kill if still running
    pkill -P $$ 2>/dev/null || true

    log_info "All services stopped"
    exit 0
}

# Register cleanup function to be called on script exit
trap cleanup SIGTERM SIGINT EXIT

# =============================================================================
# 7. Start Services
# =============================================================================

log_step "Starting development services..."

echo ""
log_info "Application will be available at:"
log_info "  Frontend: ${CYAN}http://localhost:3000${NC}"
log_info "  Backend:  ${CYAN}http://localhost:8000${NC}"
log_info "  Docs:     ${CYAN}http://localhost:8000/docs${NC}"
echo ""
log_warn "Press ${YELLOW}Ctrl+C${NC} to stop all services"
echo ""

# Start backend in background
log_service "BACKEND" "Starting FastAPI server on port 8000..."
uv run python -m uvicorn backend.src.main:app \
    --reload \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level info &
BACKEND_PID=$!
log_service "BACKEND" "Started (PID: $BACKEND_PID)"

# Give backend a moment to start
sleep 2

# Start frontend in background
log_service "FRONTEND" "Starting Vite dev server on port 3000..."
npm run dev --prefix frontend &
FRONTEND_PID=$!
log_service "FRONTEND" "Started (PID: $FRONTEND_PID)"

echo ""
log_info "✅ Both services are running!"
echo ""

# Keep the script running and monitor processes
wait
