#!/bin/bash
# Reflex production startup script for Coolify deployment
# Ensures virtual environment is properly activated with all paths

set -e  # Exit on error

# Set working directory
cd /app

# Activate virtual environment - this sets PATH correctly
source .venv/bin/activate

# Verify granian is available
if ! command -v granian &> /dev/null; then
    echo "ERROR: granian not found in PATH"
    echo "Current PATH: $PATH"
    echo "Python location: $(which python)"
    echo "Installed packages:"
    pip list | grep -i granian
    exit 1
fi

echo "Starting Reflex application..."
echo "Python: $(which python)"
echo "Granian: $(which granian)"
echo "PATH: $PATH"

# Start Reflex with production settings
exec python -m reflex run --env prod --loglevel info
