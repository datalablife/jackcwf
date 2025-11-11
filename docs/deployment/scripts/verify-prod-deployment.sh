#!/bin/bash

# Production Environment Verification Script
# Purpose: Verify production environment configuration before deployment
# Usage: bash verify-prod-deployment.sh

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  🔍 生产环境部署验证                                           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Color definitions
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

# Helper functions
check_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

check_error() {
    echo -e "${RED}❌ $1${NC}"
    ((ERRORS++))
}

check_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

# ========================================
# 1. Check Environment Files
# ========================================
echo -e "${BLUE}[1/7] 检查环境配置文件...${NC}"
echo ""

if [ -f "backend/.env.production" ]; then
    check_success "后端生产环境文件存在: backend/.env.production"
else
    check_error "后端生产环境文件不存在: backend/.env.production"
fi

if [ -f "frontend/.env.production" ]; then
    check_success "前端生产环境文件存在: frontend/.env.production"
else
    check_error "前端生产环境文件不存在: frontend/.env.production"
fi

echo ""

# ========================================
# 2. Check Database Configuration
# ========================================
echo -e "${BLUE}[2/7] 检查数据库配置...${NC}"
echo ""

# Extract DATABASE_URL from backend config
if grep -q "DATABASE_URL=postgresql" backend/.env.production; then
    check_success "数据库连接字符串已配置"
    DB_URL=$(grep "^DATABASE_URL=" backend/.env.production | cut -d'=' -f2)
    if [[ $DB_URL == *"data_management_prod"* ]]; then
        check_success "正在使用生产数据库: data_management_prod"
    else
        check_warning "未使用生产数据库，当前数据库: $DB_URL"
    fi
else
    check_error "未找到数据库连接字符串"
fi

# Test database connection
echo "⏳ 测试数据库连接..."
if PGPASSWORD=Jack_00492300 psql postgresql://jackcwf888@pgvctor.jackcwf.com:5432/data_management_prod -c "SELECT 1" > /dev/null 2>&1; then
    check_success "数据库连接成功"
else
    check_error "无法连接到生产数据库"
fi

echo ""

# ========================================
# 3. Check Security Configuration
# ========================================
echo -e "${BLUE}[3/7] 检查安全配置...${NC}"
echo ""

# Check encryption key
if grep -q "your-production-encryption-key" backend/.env.production; then
    check_warning "使用的是占位符加密密钥，需要生成真正的生产密钥"
else
    check_success "已配置加密密钥"
fi

# Check DEBUG mode
if grep -q "^DEBUG=false" backend/.env.production; then
    check_success "DEBUG 模式已禁用"
else
    check_warning "DEBUG 模式未禁用，建议禁用以提高安全性"
fi

# Check CORS configuration
if grep -q "your-domain.com" frontend/.env.production; then
    check_warning "CORS 配置使用了占位符，需要更新为实际的生产域名"
else
    check_success "CORS 配置已更新"
fi

echo ""

# ========================================
# 4. Check API Documentation Security
# ========================================
echo -e "${BLUE}[4/7] 检查 API 文档安全...${NC}"
echo ""

if grep -q "ENABLE_API_DOCS=false" backend/.env.production; then
    check_success "API 文档已在生产环境中禁用"
else
    check_warning "API 文档在生产环境中仍未禁用，建议禁用"
fi

echo ""

# ========================================
# 5. Check Startup Scripts
# ========================================
echo -e "${BLUE}[5/7] 检查启动脚本...${NC}"
echo ""

if [ -f "start-prod-env.sh" ] && [ -x "start-prod-env.sh" ]; then
    check_success "生产环境启动脚本存在且可执行: start-prod-env.sh"
else
    check_error "生产环境启动脚本不存在或不可执行"
fi

if [ -f "start-test-env.sh" ] && [ -x "start-test-env.sh" ]; then
    check_success "测试环境启动脚本存在且可执行: start-test-env.sh"
else
    check_warning "测试环境启动脚本不存在或不可执行"
fi

echo ""

# ========================================
# 6. Check Database Schema
# ========================================
echo -e "${BLUE}[6/7] 检查数据库架构...${NC}"
echo ""

# Count tables
TABLE_COUNT=$(PGPASSWORD=Jack_00492300 psql postgresql://jackcwf888@pgvctor.jackcwf.com:5432/data_management_prod -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null || echo "0")

if [ "$TABLE_COUNT" -ge 3 ]; then
    check_success "数据库架构已初始化 ($TABLE_COUNT 个表)"
else
    check_warning "数据库表较少，可能未完全初始化"
fi

# Check specific tables
TABLES=("data_sources" "file_uploads" "file_metadata")
for table in "${TABLES[@]}"; do
    if PGPASSWORD=Jack_00492300 psql postgresql://jackcwf888@pgvctor.jackcwf.com:5432/data_management_prod -t -c "\d $table" > /dev/null 2>&1; then
        check_success "表 '$table' 存在"
    else
        check_warning "表 '$table' 不存在"
    fi
done

echo ""

# ========================================
# 7. Check Dependencies
# ========================================
echo -e "${BLUE}[7/7] 检查依赖和环境...${NC}"
echo ""

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    check_success "Python 已安装: $PYTHON_VERSION"
else
    check_error "Python 3 未安装"
fi

# Check Poetry
if command -v poetry &> /dev/null; then
    check_success "Poetry 已安装"
else
    check_error "Poetry 未安装"
fi

# Check curl
if command -v curl &> /dev/null; then
    check_success "curl 已安装"
else
    check_warning "curl 未安装（用于 API 测试）"
fi

# Check psql
if command -v psql &> /dev/null; then
    check_success "psql 已安装"
else
    check_warning "psql 未安装（用于数据库管理）"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"

# Summary
if [ $ERRORS -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        echo "║  ✅ 验证完成 - 系统准备就绪                                  ║"
    else
        echo "║  ⚠️  验证完成 - 有 $WARNINGS 个警告需要注意                        ║"
    fi
else
    echo "║  ❌ 验证失败 - 有 $ERRORS 个错误需要修复                      ║"
fi

echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Print summary statistics
echo -e "${GREEN}总计: ✅ 成功  ${YELLOW}⚠️ 警告数: $WARNINGS  ${RED}❌ 错误数: $ERRORS${NC}"
echo ""

# Exit with appropriate code
if [ $ERRORS -gt 0 ]; then
    exit 1
else
    exit 0
fi
