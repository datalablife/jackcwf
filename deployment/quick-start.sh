#!/bin/bash
# Quick Start Guide - High-Availability Deployment
# This script guides you through the deployment process

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   High-Availability Deployment - Quick Start             ║
║   Jackcwf AI Conversation Platform                       ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo ""
echo "This guide will help you deploy the application with:"
echo "  - 3 backend replicas (load balanced)"
echo "  - Automatic failover"
echo "  - Health monitoring"
echo "  - Zero-downtime updates"
echo ""

# Check prerequisites
echo -e "${BLUE}[1/6] Checking prerequisites...${NC}"
echo ""

MISSING=false

if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}[WARNING]${NC} Docker not found. Please install Docker first."
    MISSING=true
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}[WARNING]${NC} Docker Compose not found. Please install Docker Compose first."
    MISSING=true
fi

if [ "$MISSING" = true ]; then
    echo ""
    echo "Please install the missing tools and run this script again."
    exit 1
fi

echo -e "${GREEN}✓${NC} Docker installed"
echo -e "${GREEN}✓${NC} Docker Compose installed"
echo ""

# Check .env file
echo -e "${BLUE}[2/6] Checking environment configuration...${NC}"
echo ""

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}[WARNING]${NC} .env file not found."
    echo ""
    echo "Creating .env from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓${NC} .env file created"
        echo ""
        echo -e "${YELLOW}IMPORTANT:${NC} Please edit .env and configure:"
        echo "  - DATABASE_URL"
        echo "  - OPENAI_API_KEY"
        echo "  - ANTHROPIC_API_KEY"
        echo ""
        echo "Press Enter when you've updated .env..."
        read
    else
        echo -e "${YELLOW}ERROR:${NC} .env.example not found. Please create .env manually."
        exit 1
    fi
fi

echo -e "${GREEN}✓${NC} .env file exists"
echo ""

# Build Docker image
echo -e "${BLUE}[3/6] Building Docker image...${NC}"
echo ""
echo "This may take 5-10 minutes on the first run."
echo ""

docker build -t jackcwf-backend:latest . || {
    echo -e "${YELLOW}ERROR:${NC} Docker build failed"
    exit 1
}

echo ""
echo -e "${GREEN}✓${NC} Docker image built successfully"
echo ""

# Choose deployment mode
echo -e "${BLUE}[4/6] Choose deployment mode:${NC}"
echo ""
echo "1) Development (2 replicas, local setup)"
echo "2) Production (3 replicas, recommended)"
echo "3) High-traffic (5 replicas)"
echo ""
read -p "Enter choice [1-3] (default: 2): " CHOICE
CHOICE=${CHOICE:-2}

case $CHOICE in
    1)
        REPLICAS=2
        MODE="development"
        ;;
    2)
        REPLICAS=3
        MODE="production"
        ;;
    3)
        REPLICAS=5
        MODE="high-traffic"
        ;;
    *)
        echo "Invalid choice. Using default (3 replicas)."
        REPLICAS=3
        MODE="production"
        ;;
esac

echo ""
echo "Selected: $MODE mode with $REPLICAS replicas"
echo ""

# Deploy
echo -e "${BLUE}[5/6] Deploying application...${NC}"
echo ""

./deployment/scripts/deploy-ha.sh \
    --platform docker-compose \
    --replicas $REPLICAS \
    --health-check || {
    echo -e "${YELLOW}ERROR:${NC} Deployment failed"
    exit 1
}

echo ""
echo -e "${GREEN}✓${NC} Deployment completed"
echo ""

# Verify
echo -e "${BLUE}[6/6] Verifying deployment...${NC}"
echo ""

sleep 5

./deployment/scripts/health-check.sh --platform docker-compose || {
    echo -e "${YELLOW}WARNING:${NC} Some health checks failed. Review logs above."
}

# Success
echo ""
echo -e "${GREEN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   ✓ Deployment Successful!                               ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo ""
echo "Your application is now running with $REPLICAS replicas!"
echo ""
echo "Access Points:"
echo "  Application:     http://localhost"
echo "  Health Check:    http://localhost/health"
echo "  API Docs:        http://localhost/api/docs"
echo "  Traefik Dashboard: http://localhost:8080"
echo ""
echo "Useful Commands:"
echo "  View logs:       docker-compose -f deployment/docker-compose.ha.yml logs -f"
echo "  Check status:    docker-compose -f deployment/docker-compose.ha.yml ps"
echo "  Scale replicas:  docker-compose -f deployment/docker-compose.ha.yml up -d --scale web=5"
echo "  Stop all:        docker-compose -f deployment/docker-compose.ha.yml down"
echo ""
echo "Monitoring (Optional):"
echo "  Deploy monitoring: docker-compose -f deployment/monitoring/docker-compose.monitoring.yml up -d"
echo "  Prometheus:        http://localhost:9090"
echo "  Grafana:           http://localhost:3001 (admin/admin)"
echo ""
echo "Documentation:"
echo "  Quick Guide:     deployment/README.md"
echo "  Full Guide:      docs/deployment/HA_DEPLOYMENT_GUIDE.md"
echo "  Architecture:    docs/deployment/HA_ARCHITECTURE_DIAGRAMS.md"
echo ""
echo -e "${GREEN}Happy deploying!${NC}"
