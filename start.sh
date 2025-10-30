#!/bin/bash
# Reflex application startup script for Coolify deployment
# This script ensures proper initialization and provides detailed logging

set -e  # Exit on error

echo "=================================================="
echo "Starting Reflex 0.8.16 Application"
echo "=================================================="

# Display environment info
echo ""
echo "Environment Information:"
echo "  Python version: $(python --version)"
echo "  Node version: $(node --version)"
echo "  Working directory: $(pwd)"
echo "  User: $(whoami)"

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
export PATH="/app/.venv/bin:$PATH"

# Verify Reflex installation
echo ""
echo "Verifying Reflex installation..."
REFLEX_VERSION=$(python -m reflex --version 2>&1 || echo "FAILED")
if [ "$REFLEX_VERSION" = "FAILED" ]; then
    echo "ERROR: Reflex is not properly installed!"
    exit 1
fi
echo "  Reflex version: $REFLEX_VERSION"

# Check for compiled frontend
echo ""
echo "Checking frontend compilation..."
if [ ! -d ".web" ]; then
    echo "WARNING: .web directory not found!"
    echo "Running frontend export..."
    python -m reflex export --frontend-only --loglevel info
else
    echo "  ✓ Frontend compiled (.web directory exists)"
fi

# Display configuration
echo ""
echo "Application Configuration:"
echo "  REFLEX_ENV: ${REFLEX_ENV:-production}"
echo "  FRONTEND_PORT: ${FRONTEND_PORT:-3000}"
echo "  BACKEND_PORT: ${BACKEND_PORT:-8000}"
echo "  PYTHONUNBUFFERED: ${PYTHONUNBUFFERED:-1}"

# Start Reflex application
echo ""
echo "=================================================="
echo "Starting Reflex in production mode..."
echo "=================================================="
echo ""

exec python -m reflex run --env production --loglevel info
