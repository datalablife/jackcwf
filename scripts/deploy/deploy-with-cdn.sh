#!/bin/bash
# Quick CDN Deployment Script
#
# This script automates the CDN deployment process:
# 1. Builds frontend with optimizations
# 2. Tests build output
# 3. Updates Nginx configuration
# 4. Rebuilds Docker image
# 5. Provides next steps for CDN setup

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================="
echo "CDN Deployment Automation Script"
echo "==================================================${NC}"

# Check if we're in the project root
if [ ! -f "pyproject.toml" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory${NC}"
    exit 1
fi

# Step 1: Build frontend
echo ""
echo -e "${BLUE}Step 1: Building frontend with optimizations...${NC}"
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm ci --legacy-peer-deps
fi

# Build frontend
echo "Building production bundle..."
npm run build

# Verify build
if [ ! -f "dist/index.html" ]; then
    echo -e "${RED}Error: Frontend build failed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Frontend build successful${NC}"

# Show bundle sizes
echo ""
echo "Bundle sizes:"
du -h dist/assets/*.js 2>/dev/null | sort -h | tail -5

cd ..

# Step 2: Test build output
echo ""
echo -e "${BLUE}Step 2: Testing build output...${NC}"

# Check asset hashing
hashed_files=$(find frontend/dist/assets -name "*-[a-f0-9]*.js" -o -name "*-[a-f0-9]*.css" | wc -l)
if [ "$hashed_files" -gt 0 ]; then
    echo -e "${GREEN}✓ Asset hashing enabled ($hashed_files hashed files)${NC}"
else
    echo -e "${YELLOW}⚠ No hashed assets found${NC}"
fi

# Check compression
if [ -f "frontend/dist/assets/index-*.js.gz" ]; then
    echo -e "${GREEN}✓ Gzip compression enabled${NC}"
else
    echo -e "${YELLOW}⚠ Gzip compression not found (install vite-plugin-compression)${NC}"
fi

# Step 3: Update Nginx configuration
echo ""
echo -e "${BLUE}Step 3: Updating Nginx configuration...${NC}"

if [ -f "docker/nginx.optimized.conf" ]; then
    # Backup current config
    if [ -f "docker/nginx.conf" ]; then
        cp docker/nginx.conf docker/nginx.conf.backup.$(date +%Y%m%d_%H%M%S)
        echo -e "${GREEN}✓ Current config backed up${NC}"
    fi

    # Copy optimized config
    cp docker/nginx.optimized.conf docker/nginx.conf
    echo -e "${GREEN}✓ Nginx config updated with optimizations${NC}"
else
    echo -e "${YELLOW}⚠ Optimized Nginx config not found, using existing config${NC}"
fi

# Step 4: Update Vite configuration (optional)
echo ""
read -p "Update Vite config with optimizations? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "frontend/vite.config.optimized.ts" ]; then
        cp frontend/vite.config.ts frontend/vite.config.backup.ts
        cp frontend/vite.config.optimized.ts frontend/vite.config.ts
        echo -e "${GREEN}✓ Vite config updated${NC}"
        echo -e "${YELLOW}⚠ Rebuild frontend to apply changes: cd frontend && npm run build${NC}"
    else
        echo -e "${YELLOW}⚠ Optimized Vite config not found${NC}"
    fi
fi

# Step 5: Update main.py to include analytics router
echo ""
echo -e "${BLUE}Step 4: Checking analytics router...${NC}"

if grep -q "analytics_routes" src/main.py; then
    echo -e "${GREEN}✓ Analytics router already registered${NC}"
else
    echo -e "${YELLOW}⚠ Analytics router not registered${NC}"
    echo "Please add the following to src/main.py:"
    echo ""
    echo "from src.api.analytics_routes import router as analytics_router"
    echo "app.include_router(analytics_router)"
    echo ""
    read -p "Press Enter to continue..."
fi

# Step 6: Rebuild Docker image
echo ""
echo -e "${BLUE}Step 5: Rebuilding Docker image...${NC}"

read -p "Rebuild Docker image? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    IMAGE_NAME="langchain-ai-chat:cdn-optimized"
    echo "Building Docker image: $IMAGE_NAME"

    docker build -t $IMAGE_NAME .

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Docker image built successfully${NC}"

        # Ask if user wants to test locally
        echo ""
        read -p "Test Docker image locally? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Starting container on port 8080..."
            docker run --rm -d \
                -p 8080:80 \
                -e DATABASE_URL="$DATABASE_URL" \
                -e OPENAI_API_KEY="$OPENAI_API_KEY" \
                -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
                --name langchain-test \
                $IMAGE_NAME

            echo ""
            echo "Container started. Test with:"
            echo "  curl http://localhost:8080/health"
            echo ""
            echo "To view logs:"
            echo "  docker logs -f langchain-test"
            echo ""
            echo "To stop:"
            echo "  docker stop langchain-test"
        fi
    else
        echo -e "${RED}Error: Docker build failed${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠ Skipping Docker build${NC}"
fi

# Step 7: Next steps
echo ""
echo -e "${BLUE}=================================================="
echo "Deployment preparation complete!"
echo "==================================================${NC}"
echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo ""
echo "1. Configure Cloudflare CDN:"
echo "   - Add domain to Cloudflare: https://dash.cloudflare.com"
echo "   - Update nameservers at registrar"
echo "   - Configure SSL/TLS (Full strict)"
echo "   - Set up Page Rules for caching"
echo ""
echo "2. Deploy to production:"
echo "   - Push Docker image to registry"
echo "   - OR commit and push to trigger Coolify deployment"
echo ""
echo "3. Verify deployment:"
echo "   - Run: bash scripts/deploy/verify-cdn-deployment.sh https://pgvctor.jackcwf.com"
echo "   - Test performance with Lighthouse"
echo "   - Check CDN cache hit rate"
echo ""
echo "4. Monitor performance:"
echo "   - Cloudflare dashboard: https://dash.cloudflare.com"
echo "   - Analytics endpoint: https://pgvctor.jackcwf.com/api/analytics/performance/summary"
echo ""
echo "For detailed instructions, see:"
echo "  - docs/deployment/CDN_INTEGRATION_GUIDE.md"
echo "  - docs/deployment/CDN_DEPLOYMENT_CHECKLIST.md"
echo ""
