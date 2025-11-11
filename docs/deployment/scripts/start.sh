#!/bin/bash
# Reflex production startup script
# Ensures proper virtual environment activation for Coolify deployment

set -e

echo "========================================="
echo "Starting Reflex Application"
echo "========================================="

# Set working directory
cd /app

# Activate virtual environment
echo "Activating virtual environment at /app/.venv"
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "Virtual environment activated successfully"
else
    echo "ERROR: Virtual environment not found at /app/.venv"
    exit 1
fi

# Display environment information
echo ""
echo "Environment Information:"
echo "----------------------------------------"
echo "Python: $(which python)"
echo "Python version: $(python --version)"
echo "Reflex: $(which reflex)"
echo "Granian: $(which granian 2>/dev/null || echo 'NOT FOUND')"
echo "VIRTUAL_ENV: $VIRTUAL_ENV"
echo "PATH: $PATH"
echo "----------------------------------------"
echo ""

# Verify granian is available
if ! command -v granian &> /dev/null; then
    echo "ERROR: granian not found in PATH"
    echo ""
    echo "Checking installed packages:"
    pip list | grep -i granian || echo "granian package not found"
    echo ""
    echo "Checking .venv/bin directory:"
    ls -la .venv/bin/ | grep granian || echo "granian binary not found in .venv/bin"
    exit 1
fi

echo "All checks passed. Starting Reflex server..."
echo "========================================="
echo ""

# Start Reflex with production settings
# Use exec to replace shell process with Reflex
exec reflex run --env prod --loglevel info
