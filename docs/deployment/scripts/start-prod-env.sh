#!/bin/bash

# Production Environment Startup Script
# Usage: bash start-prod-env.sh
# Purpose: Start backend and frontend services in production configuration

set -e

echo "╔════════════════════════════════════════╗"
echo "║  🚀 启动生产环境                       ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Color definitions
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
BACKEND_DIR="/mnt/d/工作区/云开发/working/backend"
FRONTEND_DIR="/mnt/d/工作区/云开发/working/frontend"
BACKEND_PORT=8000
BACKEND_HOST=0.0.0.0
LOG_DIR="/var/log/data-management-prod"

# Create log directory if it doesn't exist
if [ ! -d "$LOG_DIR" ]; then
    mkdir -p "$LOG_DIR" 2>/dev/null || LOG_DIR="/tmp/prod-logs"
    mkdir -p "$LOG_DIR"
fi

# Set environment variables
export DATABASE_URL='postgresql+asyncpg://jackcwf888:Jack_00492300@pgvctor.jackcwf.com:5432/data_management_prod'
export ENVIRONMENT=production
export WORKERS=0  # Auto-detect CPU cores

echo -e "${BLUE}ℹ️  配置生产环境...${NC}"
echo "  数据库: data_management_prod"
echo "  API: http://localhost:8000"
echo "  日志目录: $LOG_DIR"
echo ""

# Check Python availability
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 错误: 未找到 Python 3${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python 版本: $(python3 --version)${NC}"
echo ""

# ========================================
# Backend Startup
# ========================================
echo -e "${BLUE}🚀 启动后端服务 (生产配置)...${NC}"
cd "$BACKEND_DIR"

# Verify environment file exists
if [ ! -f ".env.production" ]; then
    echo -e "${RED}❌ 错误: .env.production 文件不存在${NC}"
    echo "请参考 DATABASE_SETUP_GUIDE.md 创建生产环境配置文件"
    exit 1
fi

echo "✅ .env.production 文件已验证"
echo ""

# Create virtual environment if needed
if [ ! -d ".venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv .venv
fi

# Ensure dependencies are installed
echo "📦 验证依赖..."
poetry install --no-root 2>&1 | tail -3

# Start backend with production settings
echo "🔄 启动 Uvicorn 服务器..."
DATABASE_URL="${DATABASE_URL}" \
ENVIRONMENT=production \
poetry run uvicorn src.main:app \
    --host $BACKEND_HOST \
    --port $BACKEND_PORT \
    --workers 4 \
    --log-level warning \
    --access-log \
    --use-colors \
    > "$LOG_DIR/backend.log" 2>&1 &

BACKEND_PID=$!
echo -e "${GREEN}✅ 后端进程已启动 (PID: $BACKEND_PID)${NC}"

# Wait for backend to start
echo "⏳ 等待后端启动..."
sleep 4

# Verify backend is responding
if curl -s http://localhost:$BACKEND_PORT/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 后端服务已就绪${NC}"
else
    echo -e "${RED}❌ 后端服务启动失败${NC}"
    echo "错误日志:"
    tail -20 "$LOG_DIR/backend.log"
    exit 1
fi

echo ""

# ========================================
# Display Service Information
# ========================================
echo "╔════════════════════════════════════════╗"
echo "║  ✅ 生产环境已启动                     ║"
echo "╚════════════════════════════════════════╝"
echo ""

echo -e "${GREEN}📡 可用服务:${NC}"
echo "  后端 API: http://localhost:$BACKEND_PORT"
echo "  API 文档: http://localhost:$BACKEND_PORT/docs (已禁用)"
echo "  Redoc: http://localhost:$BACKEND_PORT/redoc (已禁用)"
echo ""

echo -e "${GREEN}📝 日志文件:${NC}"
echo "  后端日志: $LOG_DIR/backend.log"
echo "  实时监控: tail -f $LOG_DIR/backend.log"
echo ""

echo -e "${YELLOW}⚠️  生产环境注意事项:${NC}"
echo "  - API 文档已禁用 (出于安全考虑)"
echo "  - DEBUG 模式已禁用"
echo "  - 日志级别设置为 WARNING"
echo "  - 请更新 CORS_ORIGINS 配置为实际的生产域名"
echo "  - 请生成真正的生产加密密钥"
echo ""

echo -e "${GREEN}数据库信息:${NC}"
echo "  主机: pgvctor.jackcwf.com"
echo "  数据库: data_management_prod"
echo "  用户: jackcwf888"
echo ""

echo -e "${BLUE}常用命令:${NC}"
echo "  - 停止后端: pkill -f 'uvicorn src.main:app'"
echo "  - 查看日志: tail -f $LOG_DIR/backend.log"
echo "  - 查看进程: ps aux | grep uvicorn"
echo "  - 测试健康检查: curl http://localhost:$BACKEND_PORT/health"
echo ""

# Keep script running
echo "按 Ctrl+C 停止后端服务"
echo ""

wait $BACKEND_PID
