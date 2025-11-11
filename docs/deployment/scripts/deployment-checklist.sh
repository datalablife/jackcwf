#!/bin/bash

# Interactive Deployment Execution Checklist
# Purpose: Guide through production deployment with interactive checklist
# Usage: bash deployment-checklist.sh
# Last Updated: 2025-11-12

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
COMPLETED=0
TOTAL=0
SKIPPED=0

# Function to display section header
section_header() {
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo ""
}

# Function to ask yes/no question
ask_yes_no() {
    local prompt="$1"
    local answer=""

    while true; do
        read -p "$prompt (y/n): " answer
        case $answer in
            [Yy]*)
                return 0
                ;;
            [Nn]*)
                return 1
                ;;
            *)
                echo "请输入 y 或 n"
                ;;
        esac
    done
}

# Function to mark task complete
mark_complete() {
    echo -e "${GREEN}✅ 完成${NC}: $1"
    ((COMPLETED++))
    ((TOTAL++))
}

# Function to mark task skipped
mark_skip() {
    echo -e "${YELLOW}⊘ 跳过${NC}: $1"
    ((SKIPPED++))
    ((TOTAL++))
}

# Function to show error and exit
show_error() {
    echo -e "${RED}❌ 错误${NC}: $1"
    echo ""
    exit 1
}

# ========================================
# Start
# ========================================

clear
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║  🚀 Data Management System 生产部署交互式清单                 ║"
echo "║     Production Deployment Interactive Checklist                ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "本清单将指导您完成生产部署的所有步骤。"
echo "每个步骤需要手动验证或执行。"
echo ""

# ========================================
# Phase 1: 部署前准备
# ========================================

section_header "[Phase 1] 部署前准备 (Pre-Deployment)"

echo "本阶段需要完成的检查:"
echo "  1. 验证环境和依赖"
echo "  2. 检查配置文件"
echo "  3. 验证数据库连接"
echo "  4. 检查磁盘空间"
echo ""

# Check 1: Environment
echo -e "${BLUE}检查 1/4: 验证环境${NC}"
echo ""

if ask_yes_no "已经安装 Python 3.9+ 吗?"; then
    PYTHON_VERSION=$(python --version 2>&1)
    echo "  Python: $PYTHON_VERSION"
    mark_complete "Python 版本验证"
else
    echo "  ❌ 请先安装 Python 3.9 或更高版本"
    show_error "Python 环境未满足要求"
fi

if ask_yes_no "已经安装 Node.js 18+ 吗?"; then
    NODE_VERSION=$(node --version)
    echo "  Node.js: $NODE_VERSION"
    mark_complete "Node.js 版本验证"
else
    echo "  ❌ 请先安装 Node.js 18 或更高版本"
    show_error "Node.js 环境未满足要求"
fi

if ask_yes_no "已经安装 Poetry 吗?"; then
    POETRY_VERSION=$(poetry --version 2>&1 | head -1)
    echo "  Poetry: $POETRY_VERSION"
    mark_complete "Poetry 工具验证"
else
    echo "  ❌ 请先安装 Poetry"
    show_error "Poetry 工具缺失"
fi

# Check 2: Configuration Files
echo ""
echo -e "${BLUE}检查 2/4: 配置文件${NC}"
echo ""

if [ -f "backend/.env.production" ]; then
    echo "  ✅ backend/.env.production 存在"
    if grep -q "DATABASE_URL=postgresql+asyncpg://" backend/.env.production; then
        echo "  ✅ 数据库连接配置正确"
        mark_complete "后端生产配置"
    else
        show_error "数据库连接字符串格式不正确"
    fi
else
    show_error "backend/.env.production 文件不存在"
fi

if [ -f "frontend/.env.production" ]; then
    echo "  ✅ frontend/.env.production 存在"
    mark_complete "前端生产配置"
else
    show_error "frontend/.env.production 文件不存在"
fi

# Check 3: Database
echo ""
echo -e "${BLUE}检查 3/4: 数据库连接${NC}"
echo ""

if ask_yes_no "已经创建生产数据库 (data_management_prod) 吗?"; then
    if ask_yes_no "可以从命令行连接到数据库吗? (测试: psql postgresql://...)"; then
        mark_complete "数据库连接验证"
    else
        show_error "无法连接到数据库"
    fi
else
    show_error "生产数据库尚未创建"
fi

# Check 4: Disk Space
echo ""
echo -e "${BLUE}检查 4/4: 磁盘空间${NC}"
echo ""

DISK_USAGE=$(df / | awk 'NR==2{print $5}' | sed 's/%//')
echo "  当前磁盘使用率: ${DISK_USAGE}%"

if [ "$DISK_USAGE" -lt 80 ]; then
    echo "  ✅ 磁盘空间充足"
    mark_complete "磁盘空间检查"
else
    show_error "磁盘空间不足 (> 80%)"
fi

echo ""
echo -e "${GREEN}✅ Phase 1 完成: 所有前置检查通过${NC}"
echo ""

# ========================================
# Phase 2: 部署前脚本验证
# ========================================

section_header "[Phase 2] 部署脚本验证"

echo "本阶段将运行部署前验证脚本。"
echo ""

if ask_yes_no "现在运行部署前验证脚本? (bash verify-prod-deployment.sh)"; then
    if bash verify-prod-deployment.sh; then
        mark_complete "部署前验证"
        echo ""
        echo -e "${GREEN}✅ 所有验证通过${NC}"
    else
        show_error "部署前验证失败"
    fi
else
    mark_skip "部署前验证"
fi

echo ""

# ========================================
# Phase 3: 启动服务
# ========================================

section_header "[Phase 3] 启动生产服务"

echo "本阶段将启动后端和前端服务。"
echo ""

# Start Backend
echo -e "${BLUE}启动后端服务${NC}"
echo ""

if ask_yes_no "现在启动后端服务? (bash start-prod-env.sh)"; then
    echo ""
    echo "启动后端服务..."
    bash start-prod-env.sh &
    BACKEND_PID=$!

    echo ""
    echo "等待后端服务启动 (30 秒)..."
    sleep 5

    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        echo -e "${GREEN}✅ 后端服务已启动并健康${NC}"
        mark_complete "后端服务启动"
    else
        show_error "后端服务未能正常启动"
    fi
else
    mark_skip "后端服务启动"
fi

echo ""

# Start Frontend
echo -e "${BLUE}启动前端应用${NC}"
echo ""

if ask_yes_no "现在构建并启动前端应用?"; then
    echo ""
    echo "构建前端..."
    cd frontend
    npm run build

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 前端构建成功${NC}"
        mark_complete "前端构建"

        echo ""
        echo "启动前端服务..."
        npm install -g serve 2>/dev/null
        serve -s dist -l 3000 > /tmp/frontend.log 2>&1 &

        sleep 3

        if curl -s http://localhost:3000 | grep -q "<!DOCTYPE"; then
            echo -e "${GREEN}✅ 前端应用已启动${NC}"
            mark_complete "前端应用启动"
        else
            show_error "前端应用未能正常启动"
        fi
    else
        show_error "前端构建失败"
    fi

    cd ..
else
    mark_skip "前端应用启动"
fi

echo ""

# ========================================
# Phase 4: 服务验证
# ========================================

section_header "[Phase 4] 服务验证"

echo "本阶段验证所有服务是否正常运行。"
echo ""

# API Health Check
echo -e "${BLUE}验证 API 健康状态${NC}"
if curl -s http://localhost:8000/health | jq . > /dev/null 2>&1; then
    curl -s http://localhost:8000/health | jq .
    mark_complete "后端 API 健康检查"
else
    show_error "后端 API 未响应"
fi

echo ""

# Frontend Check
echo -e "${BLUE}验证前端应用${NC}"
if curl -s http://localhost:3000 | grep -q "<!DOCTYPE"; then
    echo "✅ 前端应用响应正常"
    mark_complete "前端应用验证"
else
    show_error "前端应用未响应"
fi

echo ""

# Database Check
echo -e "${BLUE}验证数据库连接${NC}"
if curl -s http://localhost:8000/health/db | jq . > /dev/null 2>&1; then
    curl -s http://localhost:8000/health/db | jq .
    mark_complete "数据库连接验证"
else
    show_error "数据库连接异常"
fi

echo ""

# ========================================
# Phase 5: 监控系统初始化
# ========================================

section_header "[Phase 5] 监控系统初始化"

echo "本阶段初始化监控、日志和告警系统。"
echo ""

if ask_yes_no "现在初始化监控系统? (bash setup-monitoring.sh)"; then
    bash setup-monitoring.sh
    mark_complete "监控系统初始化"
else
    mark_skip "监控系统初始化"
fi

echo ""

# ========================================
# Phase 6: 完整系统验证
# ========================================

section_header "[Phase 6] 完整系统验证"

echo "本阶段运行部署后的完整系统验证。"
echo ""

if ask_yes_no "现在运行完整系统验证脚本? (bash verify-prod-system.sh)"; then
    bash verify-prod-system.sh
    mark_complete "完整系统验证"
else
    mark_skip "完整系统验证"
fi

echo ""

# ========================================
# Summary
# ========================================

section_header "部署总结"

echo "已完成的步骤: $COMPLETED"
echo "已跳过的步骤: $SKIPPED"
echo "总步骤数: $TOTAL"
echo ""

if [ "$COMPLETED" -eq "$TOTAL" ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✅ 部署完成！                                                 ║${NC}"
    echo -e "${GREEN}║     系统已准备好接收生产流量                                   ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "后续步骤:"
    echo "  1. 监控系统运行 (首 24 小时)"
    echo "  2. 查看日志确认没有错误"
    echo "  3. 进行烟雾测试验证主要功能"
    echo "  4. 通知相关团队和用户"
    echo ""
    echo "常用命令:"
    echo "  查看日志: tail -f /var/log/data-management-prod/app.log"
    echo "  后端 API: http://localhost:8000/health"
    echo "  前端应用: http://localhost:3000"
    echo "  Prometheus: http://localhost:9090"
    echo ""
else
    echo -e "${YELLOW}⚠️  部署过程未完全完成${NC}"
    echo ""
    echo "请完成以下未完成的步骤:"
    echo "  - 查看上面的错误信息"
    echo "  - 参考 PRODUCTION_LAUNCH_GUIDE.md 的故障排除部分"
    echo "  - 检查相关的日志文件"
fi

echo ""
echo "部署检查清单完成！"
echo ""
