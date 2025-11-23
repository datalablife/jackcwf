#!/bin/bash
#
# Quick Start Script: 4GB Optimization Performance Benchmark
#
# This script runs the complete performance benchmark suite and generates reports.
#
# Prerequisites:
# - PostgreSQL running with test database
# - Redis running on localhost:6379
# - Python 3.12+ with dependencies installed
#
# Usage:
#   ./run_benchmark.sh [--db-url DB_URL] [--redis-url REDIS_URL]
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
DB_URL="${DATABASE_URL:-postgresql://jackcwf888@pgvctor.jackcwf.com:5432/postgres}"
REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
BENCHMARK_DIR="/mnt/d/工作区/云开发/working/tests/benchmarks"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}4GB Optimization Performance Benchmark${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --db-url)
            DB_URL="$2"
            shift 2
            ;;
        --redis-url)
            REDIS_URL="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --db-url DB_URL       PostgreSQL connection string"
            echo "  --redis-url REDIS_URL Redis connection string"
            echo "  --help                Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  DATABASE_URL          PostgreSQL connection string (default)"
            echo "  REDIS_URL             Redis connection string (default)"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Step 1: Check prerequisites
echo -e "${YELLOW}Step 1: Checking prerequisites...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.12+${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python found: $(python3 --version)${NC}"

# Check if in virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}⚠️  Not in virtual environment. Activating...${NC}"
    if [[ -f "/mnt/d/工作区/云开发/working/.venv/bin/activate" ]]; then
        source "/mnt/d/工作区/云开发/working/.venv/bin/activate"
        echo -e "${GREEN}✅ Virtual environment activated${NC}"
    else
        echo -e "${RED}❌ Virtual environment not found at /mnt/d/工作区/云开发/working/.venv${NC}"
        echo -e "${YELLOW}   Create it with: python3 -m venv .venv${NC}"
        exit 1
    fi
fi

# Check required Python packages
echo -e "${YELLOW}Checking Python packages...${NC}"
required_packages=("pytest" "asyncpg" "redis" "psutil")
missing_packages=()

for package in "${required_packages[@]}"; do
    if ! python3 -c "import $package" 2>/dev/null; then
        missing_packages+=("$package")
    fi
done

if [ ${#missing_packages[@]} -gt 0 ]; then
    echo -e "${RED}❌ Missing packages: ${missing_packages[*]}${NC}"
    echo -e "${YELLOW}   Install with: uv pip install ${missing_packages[*]}${NC}"
    exit 1
fi
echo -e "${GREEN}✅ All required packages installed${NC}"

# Check PostgreSQL connection
echo -e "${YELLOW}Checking PostgreSQL connection...${NC}"
if python3 -c "import asyncio, asyncpg; asyncio.run(asyncpg.connect('$DB_URL'))" 2>/dev/null; then
    echo -e "${GREEN}✅ PostgreSQL connection successful${NC}"
else
    echo -e "${RED}❌ PostgreSQL connection failed${NC}"
    echo -e "${YELLOW}   DB URL: $DB_URL${NC}"
    echo -e "${YELLOW}   Check your DATABASE_URL environment variable or --db-url argument${NC}"
    exit 1
fi

# Check Redis connection
echo -e "${YELLOW}Checking Redis connection...${NC}"
if python3 -c "import asyncio, redis.asyncio as aioredis; asyncio.run(aioredis.from_url('$REDIS_URL').ping())" 2>/dev/null; then
    echo -e "${GREEN}✅ Redis connection successful${NC}"
else
    echo -e "${YELLOW}⚠️  Redis connection failed (optional for some tests)${NC}"
    echo -e "${YELLOW}   Redis URL: $REDIS_URL${NC}"
    echo -e "${YELLOW}   Some benchmarks may be skipped${NC}"
fi

echo ""

# Step 2: Run benchmark suite
echo -e "${YELLOW}Step 2: Running benchmark suite...${NC}"
echo -e "${BLUE}This may take 5-10 minutes depending on your system${NC}"
echo ""

export DATABASE_URL="$DB_URL"
export REDIS_URL="$REDIS_URL"

cd "$BENCHMARK_DIR"

# Run the benchmark
if python3 test_4gb_optimization_benchmark.py; then
    echo -e "${GREEN}✅ Benchmark completed successfully${NC}"
else
    echo -e "${RED}❌ Benchmark failed${NC}"
    exit 1
fi

echo ""

# Step 3: Generate reports
echo -e "${YELLOW}Step 3: Generating performance reports...${NC}"

if python3 generate_performance_report.py; then
    echo -e "${GREEN}✅ Reports generated successfully${NC}"
else
    echo -e "${RED}❌ Report generation failed${NC}"
    exit 1
fi

echo ""

# Step 4: Display summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Benchmark Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Find latest report files
LATEST_JSON="$BENCHMARK_DIR/benchmark_results_latest.json"
LATEST_MD="$BENCHMARK_DIR/performance_report_latest.md"
LATEST_HTML="$BENCHMARK_DIR/performance_report_latest.html"

echo -e "${GREEN}📊 Reports Generated:${NC}"
echo -e "   JSON Results:  $LATEST_JSON"
echo -e "   Markdown:      $LATEST_MD"
echo -e "   HTML:          $LATEST_HTML"
echo ""

# Parse and display key metrics from JSON
if [ -f "$LATEST_JSON" ]; then
    echo -e "${GREEN}🎯 Key Performance Metrics:${NC}"

    # Extract metrics using Python
    python3 << EOF
import json

with open("$LATEST_JSON", "r") as f:
    results = json.load(f)

cache = results.get("cache_performance", {})
api = results.get("api_performance", {})
capacity = results.get("concurrent_capacity", {})

print(f"   Cache Hit Rate:     {cache.get('hit_rate', 0):.1%} {'✅' if cache.get('hit_rate', 0) >= 0.5 else '❌'} (Target: 50-70%)")
print(f"   API P50 Latency:    {api.get('p50_latency_ms', 0):.2f}ms {'✅' if api.get('p50_latency_ms', 1000) < 100 else '❌'} (Target: <100ms)")
print(f"   API P95 Latency:    {api.get('p95_latency_ms', 0):.2f}ms {'✅' if api.get('p95_latency_ms', 1000) < 300 else '❌'} (Target: <300ms)")
print(f"   Max Concurrent:     {capacity.get('max_concurrent_connections', 0):,} {'✅' if capacity.get('max_concurrent_connections', 0) >= 500 else '❌'} (Target: 500+)")
print(f"   Memory @ 90%:       {capacity.get('memory_usage_90pct_mb', 0):.1f}MB / 4096MB")
EOF

    echo ""
fi

echo -e "${YELLOW}📖 Next Steps:${NC}"
echo -e "   1. Review the HTML report in a browser: file://$LATEST_HTML"
echo -e "   2. Share the Markdown report with your team: $LATEST_MD"
echo -e "   3. Analyze detailed JSON results: $LATEST_JSON"
echo ""

echo -e "${GREEN}✅ All done!${NC}"
