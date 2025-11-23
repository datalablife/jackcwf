#!/bin/bash
# CDN Deployment Verification Script
#
# This script verifies that:
# 1. Frontend is built correctly
# 2. Assets are properly hashed
# 3. Compression is enabled
# 4. CDN is serving content
# 5. Cache headers are correct

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

SUCCESS="${GREEN}✓${NC}"
WARNING="${YELLOW}⚠${NC}"
ERROR="${RED}✗${NC}"

DOMAIN="${1:-https://pgvctor.jackcwf.com}"

echo "=================================================="
echo "CDN Deployment Verification"
echo "Domain: $DOMAIN"
echo "=================================================="

# Function to check HTTP header
check_header() {
    local url=$1
    local header=$2
    local expected=$3

    local actual=$(curl -s -I "$url" | grep -i "^$header:" | cut -d' ' -f2- | tr -d '\r')

    if [[ "$actual" == *"$expected"* ]]; then
        echo -e "$SUCCESS $header: $actual"
        return 0
    else
        echo -e "$ERROR $header: Expected '$expected', got '$actual'"
        return 1
    fi
}

# 1. Check frontend build exists
echo ""
echo "1. Checking frontend build..."
if [ -f "frontend/dist/index.html" ]; then
    echo -e "$SUCCESS Frontend build exists"

    # Check bundle sizes
    echo "Bundle sizes:"
    du -h frontend/dist/assets/*.js 2>/dev/null | sort -h | tail -5
else
    echo -e "$ERROR Frontend build not found. Run: cd frontend && npm run build"
    exit 1
fi

# 2. Check asset hashing
echo ""
echo "2. Checking asset hashing..."
hashed_files=$(find frontend/dist/assets -name "*-[a-f0-9]*.js" -o -name "*-[a-f0-9]*.css" | wc -l)
if [ "$hashed_files" -gt 0 ]; then
    echo -e "$SUCCESS Found $hashed_files hashed assets (cache busting enabled)"
else
    echo -e "$WARNING No hashed assets found (cache busting may not work)"
fi

# 3. Check compression
echo ""
echo "3. Checking compression..."
if [ -f "frontend/dist/assets/index-*.js.gz" ]; then
    echo -e "$SUCCESS Gzip compression enabled"

    # Compare sizes
    original=$(find frontend/dist/assets -name "index-*.js" -not -name "*.gz" -not -name "*.br" -exec du -b {} + | head -1 | cut -f1)
    gzipped=$(find frontend/dist/assets -name "index-*.js.gz" -exec du -b {} + | head -1 | cut -f1)
    ratio=$(echo "scale=1; 100 - ($gzipped * 100 / $original)" | bc)
    echo "  Compression ratio: ${ratio}% reduction"
else
    echo -e "$WARNING Gzip files not found. Consider enabling vite-plugin-compression"
fi

if [ -f "frontend/dist/assets/index-*.js.br" ]; then
    echo -e "$SUCCESS Brotli compression enabled"
else
    echo -e "$WARNING Brotli files not found. Consider enabling vite-plugin-compression with brotli"
fi

# 4. Check if domain is accessible
echo ""
echo "4. Checking domain accessibility..."
if curl -s -o /dev/null -w "%{http_code}" "$DOMAIN" | grep -q "200"; then
    echo -e "$SUCCESS Domain is accessible"
else
    echo -e "$ERROR Domain is not accessible or returned non-200 status"
    exit 1
fi

# 5. Check CDN headers
echo ""
echo "5. Checking CDN headers..."

# Check for Cloudflare
cf_ray=$(curl -s -I "$DOMAIN" | grep -i "cf-ray" | cut -d' ' -f2-)
if [ -n "$cf_ray" ]; then
    echo -e "$SUCCESS Cloudflare CDN detected (CF-Ray: ${cf_ray:0:30}...)"
else
    echo -e "$WARNING No Cloudflare headers detected. CDN may not be enabled."
fi

# 6. Check cache headers for static assets
echo ""
echo "6. Checking cache headers..."

# Get a JS file URL
js_file=$(curl -s "$DOMAIN" | grep -o '/assets/[^"]*\.js' | head -1)
if [ -n "$js_file" ]; then
    js_url="$DOMAIN$js_file"
    echo "Testing: $js_url"

    # Check Cache-Control header
    cache_control=$(curl -s -I "$js_url" | grep -i "cache-control:" | cut -d' ' -f2- | tr -d '\r')
    if [[ "$cache_control" == *"public"* ]] && [[ "$cache_control" == *"immutable"* ]]; then
        echo -e "$SUCCESS Cache-Control: $cache_control"
    else
        echo -e "$WARNING Cache-Control: $cache_control (expected 'public, immutable')"
    fi

    # Check if gzip is accepted
    content_encoding=$(curl -s -I -H "Accept-Encoding: gzip, deflate" "$js_url" | grep -i "content-encoding:" | cut -d' ' -f2- | tr -d '\r')
    if [[ "$content_encoding" == *"gzip"* ]] || [[ "$content_encoding" == *"br"* ]]; then
        echo -e "$SUCCESS Content-Encoding: $content_encoding"
    else
        echo -e "$WARNING Content-Encoding: $content_encoding (compression may not be enabled)"
    fi
else
    echo -e "$WARNING Could not find JS file to test"
fi

# 7. Check API cache bypass
echo ""
echo "7. Checking API cache bypass..."
api_cache=$(curl -s -I "$DOMAIN/api/health" | grep -i "cache-control:" | cut -d' ' -f2- | tr -d '\r')
if [[ "$api_cache" == *"no-cache"* ]] || [[ "$api_cache" == *"no-store"* ]]; then
    echo -e "$SUCCESS API cache disabled: $api_cache"
else
    echo -e "$WARNING API cache: $api_cache (should be 'no-cache, no-store')"
fi

# 8. Check security headers
echo ""
echo "8. Checking security headers..."

check_header "$DOMAIN" "X-Content-Type-Options" "nosniff" || true
check_header "$DOMAIN" "X-Frame-Options" "SAMEORIGIN" || true
check_header "$DOMAIN" "X-XSS-Protection" "1" || true

# 9. Test cache hit rate
echo ""
echo "9. Testing cache hit rate..."
echo "Making 3 requests to test CDN cache..."

for i in {1..3}; do
    cache_status=$(curl -s -I "$js_url" 2>/dev/null | grep -i "cf-cache-status:" | cut -d' ' -f2- | tr -d '\r')
    age=$(curl -s -I "$js_url" 2>/dev/null | grep -i "age:" | cut -d' ' -f2- | tr -d '\r')

    if [ -n "$cache_status" ]; then
        if [ "$cache_status" = "HIT" ]; then
            echo -e "$SUCCESS Request $i: CF-Cache-Status: $cache_status (Age: ${age}s)"
        elif [ "$cache_status" = "MISS" ]; then
            echo -e "$WARNING Request $i: CF-Cache-Status: $cache_status (first request)"
        else
            echo -e "$WARNING Request $i: CF-Cache-Status: $cache_status"
        fi
    else
        echo -e "  Request $i: No cache status header (CDN may not be enabled)"
    fi

    sleep 1
done

# 10. Performance check
echo ""
echo "10. Performance check (TTFB)..."
ttfb=$(curl -o /dev/null -s -w '%{time_starttransfer}\n' "$DOMAIN")
ttfb_ms=$(echo "$ttfb * 1000" | bc)
ttfb_int=${ttfb_ms%.*}

if [ "$ttfb_int" -lt 800 ]; then
    echo -e "$SUCCESS Time to First Byte: ${ttfb_ms}ms (good)"
elif [ "$ttfb_int" -lt 1800 ]; then
    echo -e "$WARNING Time to First Byte: ${ttfb_ms}ms (needs improvement)"
else
    echo -e "$ERROR Time to First Byte: ${ttfb_ms}ms (poor)"
fi

echo ""
echo "=================================================="
echo "Verification complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Run Lighthouse audit: lighthouse $DOMAIN"
echo "2. Test from multiple locations: https://www.webpagetest.org"
echo "3. Monitor performance: $DOMAIN/api/analytics/performance/summary"
echo "4. Check CDN dashboard: https://dash.cloudflare.com"
