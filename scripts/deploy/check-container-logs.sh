#!/bin/bash

# Container diagnostics script for Coolify deployment troubleshooting
# Run this on the server: bash check-container-logs.sh

set -e

CONTAINER_ID=$(docker ps -a | grep "zogcwskg8s0okw4c0wk0kscg" | head -1 | awk '{print $1}')

if [ -z "$CONTAINER_ID" ]; then
    echo "❌ Could not find container"
    echo "Available containers:"
    docker ps -a | grep -E "zogcwskg8s0okw4c0wk0kscg|jackcwf"
    exit 1
fi

echo "📋 Container ID: $CONTAINER_ID"
echo ""

echo "═══════════════════════════════════════════"
echo "🔴 CONTAINER STATUS"
echo "═══════════════════════════════════════════"
docker ps -a --filter "id=$CONTAINER_ID" --format "table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Names}}"
echo ""

echo "═══════════════════════════════════════════"
echo "📜 RECENT LOGS (Last 100 lines)"
echo "═══════════════════════════════════════════"
docker logs "$CONTAINER_ID" 2>&1 | tail -100
echo ""

echo "═══════════════════════════════════════════"
echo "🔍 GREP FOR ERRORS"
echo "═══════════════════════════════════════════"
docker logs "$CONTAINER_ID" 2>&1 | grep -E "ERROR|Traceback|ModuleNotFoundError|ImportError|Failed|Error:" || echo "No error lines found"
echo ""

echo "═══════════════════════════════════════════"
echo "📊 IMAGE INFORMATION"
echo "═══════════════════════════════════════════"
IMAGE=$(docker ps -a --filter "id=$CONTAINER_ID" --format "{{.Image}}")
echo "Image: $IMAGE"
docker images --filter "reference=$IMAGE" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.Created}}"
echo ""

echo "═══════════════════════════════════════════"
echo "⚠️  RESTART COUNT"
echo "═══════════════════════════════════════════"
docker inspect "$CONTAINER_ID" --format='{{.RestartCount}} restarts'
echo ""

echo "═══════════════════════════════════════════"
echo "🕐 CONTAINER CREATION TIME"
echo "═══════════════════════════════════════════"
docker inspect "$CONTAINER_ID" --format='Created: {{.Created}}'
docker inspect "$CONTAINER_ID" --format='Started: {{.State.StartedAt}}'
echo ""

echo "✅ Diagnostics complete"
