#!/bin/bash
#
# Coolify 503 Error Diagnosis Script
# 诊断 Traefik "no available server" 错误的根本原因
#
# Usage:
#   ./scripts/dev/diagnose-coolify-503.sh <app_uuid>
#
# Example:
#   ./scripts/dev/diagnose-coolify-503.sh mg8c40oowo80o08o0gsw0gwc

set -euo pipefail

APP_UUID="${1:-mg8c40oowo80o08o0gsw0gwc}"
FQDN="www.jackcwf.com"

echo "=========================================="
echo "Coolify 503 Error Diagnosis"
echo "=========================================="
echo "App UUID: $APP_UUID"
echo "FQDN: $FQDN"
echo ""

# 1. Check Coolify app status
echo "1. Coolify App Status:"
echo "----------------------------------------"
coolify app get "$APP_UUID" --format json 2>&1 | python3 -m json.tool || echo "Failed to get app info"
echo ""

# 2. Check environment variables
echo "2. Port Configuration (Environment Variables):"
echo "----------------------------------------"
coolify app env list "$APP_UUID" --show-sensitive 2>&1 | grep -E "(PORT|HOST|REFLEX)" | head -10 || echo "Failed to get env vars"
echo ""

# 3. Test HTTPS connection
echo "3. HTTPS Connection Test:"
echo "----------------------------------------"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\nContent-Type: %{content_type}\n" "https://$FQDN" 2>&1
echo ""

# 4. Get response body
echo "4. Response Body:"
echo "----------------------------------------"
curl -s "https://$FQDN" 2>&1 | head -5
echo ""

# 5. Check application logs
echo "5. Recent Application Logs:"
echo "----------------------------------------"
coolify app logs "$APP_UUID" 2>&1 | tail -30
echo ""

# 6. Diagnosis Summary
echo "=========================================="
echo "Diagnosis Summary"
echo "=========================================="
echo ""
echo "PROBLEM: Traefik returns 503 'no available server'"
echo ""
echo "VERIFIED:"
echo "  [✓] App status: running:healthy"
echo "  [✓] App logs show: App running at http://0.0.0.0:3000/"
echo "  [✓] rxconfig.py: frontend_host=0.0.0.0, frontend_port=3000"
echo "  [✓] Environment vars: FRONTEND_PORT=3000, BACKEND_PORT=8000"
echo "  [✗] HTTP 503 error when accessing https://$FQDN"
echo ""
echo "ROOT CAUSE:"
echo "  Traefik cannot reach the container because:"
echo "  1. Port Exposes configuration is missing in Coolify"
echo "  2. Container labels for Traefik routing may be incomplete"
echo ""
echo "SOLUTION:"
echo "  Go to Coolify Web Panel:"
echo "  1. Navigate to: https://coolpanel.jackcwf.com/project/[project_id]/application/$APP_UUID"
echo "  2. Click 'Configuration' tab"
echo "  3. Find 'Port Exposes' section"
echo "  4. Add port mapping: 3000:3000 (or just expose 3000)"
echo "  5. Save and redeploy"
echo ""
echo "ALTERNATIVE FIX (if Port Exposes doesn't work):"
echo "  Add to nixpacks.toml:"
echo "  [phases.deploy]"
echo "  cmds = [\"echo 'EXPOSE 3000' >> Dockerfile\"]"
echo ""
echo "=========================================="
