#!/bin/bash

# 测试环境启动脚本
# 用于启动完整的测试环境（后端 + 前端 + 测试数据库）

set -e

echo "╔════════════════════════════════════════╗"
echo "║  🧪 启动测试环境                       ║"
echo "╚════════════════════════════════════════╝"
echo ""

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 设置环境变量
export DATABASE_URL='postgresql+asyncpg://jackcwf888:Jack_00492300@pgvctor.jackcwf.com:5432/data_management_test'
export ENVIRONMENT=test

echo -e "${BLUE}ℹ️  配置测试环境...${NC}"
echo "  数据库: data_management_test"
echo "  API: http://localhost:8000"
echo "  前端: http://localhost:5173"
echo ""

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python 3"
    exit 1
fi

echo -e "${GREEN}✅ Python 版本: $(python3 --version)${NC}"
echo ""

# 启动后端服务
echo -e "${BLUE}🚀 启动后端服务...${NC}"
cd /mnt/d/工作区/云开发/working/backend

if [ ! -d ".venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv .venv
fi

# 确保依赖已安装
echo "📦 安装/更新依赖..."
poetry install --no-root 2>&1 | tail -5

# 启动后端
DATABASE_URL="${DATABASE_URL}" poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 > /tmp/test-backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✅ 后端进程已启动 (PID: $BACKEND_PID)${NC}"

# 等待后端启动
echo "⏳ 等待后端启动..."
sleep 3

# 检查后端是否响应
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 后端服务已就绪${NC}"
else
    echo "❌ 后端服务启动失败"
    tail -20 /tmp/test-backend.log
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════╗"
echo "║  ✅ 测试环境已启动                     ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}可用服务:${NC}"
echo "  📡 后端 API: http://localhost:8000"
echo "  📖 API 文档: http://localhost:8000/docs"
echo "  🔍 API Redoc: http://localhost:8000/redoc"
echo ""
echo -e "${GREEN}日志文件:${NC}"
echo "  📝 后端日志: /tmp/test-backend.log"
echo ""
echo -e "${BLUE}提示:${NC}"
echo "  - 运行测试: cd backend && poetry run pytest"
echo "  - 查看日志: tail -f /tmp/test-backend.log"
echo "  - 停止环境: pkill -f uvicorn"
echo ""
echo -e "${GREEN}数据库信息:${NC}"
echo "  主机: pgvctor.jackcwf.com"
echo "  数据库: data_management_test"
echo "  用户: jackcwf888"
echo ""
echo "按 Ctrl+C 停止后端服务"
echo ""

# 保持脚本运行
wait $BACKEND_PID
