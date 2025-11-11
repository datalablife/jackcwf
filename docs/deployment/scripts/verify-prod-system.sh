#!/bin/bash

# Post-Deployment System Verification Script
# Purpose: Comprehensive system verification after production deployment
# Usage: bash verify-prod-system.sh
# Last Updated: 2025-11-12

set -e

# Color definitions
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNING=0

# Functions
check_pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((CHECKS_PASSED++))
}

check_fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((CHECKS_FAILED++))
}

check_warning() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
    ((CHECKS_WARNING++))
}

divider() {
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo "$1"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
}

# ========================================
# Main Verification
# ========================================

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  🔍 生产环境系统验证                                           ║"
echo "║     Post-Deployment System Verification                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# ========================================
# 1. Environment Variables
# ========================================
divider "[1/10] 环境变量检查"

if [ -f "backend/.env.production" ]; then
    check_pass "后端生产配置文件存在"

    if grep -q "DATABASE_URL=postgresql+asyncpg://" backend/.env.production; then
        check_pass "数据库连接字符串使用正确的驱动程序"
    else
        check_fail "数据库连接字符串驱动程序不正确"
    fi

    if grep -q "DEBUG=false" backend/.env.production; then
        check_pass "DEBUG 模式已禁用"
    else
        check_fail "DEBUG 模式未禁用 - 存在安全风险"
    fi

    if grep -q "LOG_LEVEL=WARNING" backend/.env.production; then
        check_pass "日志级别正确 (WARNING)"
    else
        check_warning "日志级别可能不是 WARNING"
    fi
else
    check_fail "后端生产配置文件不存在"
fi

if [ -f "frontend/.env.production" ]; then
    check_pass "前端生产配置文件存在"
    if grep -q "VITE_API_URL=" frontend/.env.production; then
        check_pass "前端 API 端点已配置"
    else
        check_fail "前端 API 端点未配置"
    fi
else
    check_fail "前端生产配置文件不存在"
fi

# ========================================
# 2. Service Status
# ========================================
divider "[2/10] 服务状态检查"

# Check backend
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    HEALTH=$(curl -s http://localhost:8000/health | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    if [ "$HEALTH" = "healthy" ]; then
        check_pass "后端服务运行且健康状态正常"
    else
        check_warning "后端服务运行但健康状态为: $HEALTH"
    fi
else
    check_fail "后端服务未响应 (http://localhost:8000)"
fi

# Check frontend
if curl -s http://localhost:3000 | grep -q "<!DOCTYPE"; then
    check_pass "前端应用正在运行"
else
    check_fail "前端应用未响应 (http://localhost:3000)"
fi

# Check process status
if pgrep -f "uvicorn" > /dev/null; then
    check_pass "Uvicorn 后端进程运行中"
else
    check_fail "Uvicorn 后端进程未运行"
fi

# ========================================
# 3. Database Connectivity
# ========================================
divider "[3/10] 数据库连接检查"

DB_HOST="pgvctor.jackcwf.com"
DB_USER="jackcwf888"
DB_NAME="data_management_prod"

# Extract from env file
if [ -f "backend/.env.production" ]; then
    DB_URL=$(grep DATABASE_URL backend/.env.production | cut -d'=' -f2)

    # Test connection with simple query
    if PGPASSWORD=$(grep -o 'pgvctor.jackcwf.com://[^@]*' backend/.env.production | cut -d':' -f2) && \
       psql "postgresql://$DB_USER:$PGPASSWORD@$DB_HOST:5432/$DB_NAME" -c "SELECT 1" > /dev/null 2>&1; then
        check_pass "数据库连接成功"

        # Check tables exist
        if psql "postgresql://$DB_USER:$PGPASSWORD@$DB_HOST:5432/$DB_NAME" -c "\dt" | grep -q "file_uploads"; then
            check_pass "数据库表结构完整"
        else
            check_fail "数据库表结构不完整"
        fi

        # Check connection pool
        CONN_COUNT=$(psql "postgresql://$DB_USER:$PGPASSWORD@$DB_HOST:5432/$DB_NAME" -t -c \
            "SELECT count(*) FROM pg_stat_activity WHERE datname='$DB_NAME';" | xargs)
        if [ "$CONN_COUNT" -le 20 ]; then
            check_pass "数据库连接池状态正常 ($CONN_COUNT 个活跃连接)"
        else
            check_warning "数据库连接池可能过高 ($CONN_COUNT 个活跃连接)"
        fi
    else
        check_fail "数据库连接失败"
    fi
else
    check_warning "无法读取数据库配置文件"
fi

# ========================================
# 4. API Endpoints
# ========================================
divider "[4/10] API 端点检查"

ENDPOINTS=(
    "/health"
    "/health/db"
    "/api/file-uploads"
    "/api/datasources"
    "/metrics"
)

for endpoint in "${ENDPOINTS[@]}"; do
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000$endpoint | grep -qE "200|401|403"; then
        check_pass "API 端点 $endpoint 可访问"
    else
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000$endpoint)
        if [ "$HTTP_CODE" = "404" ]; then
            check_warning "API 端点 $endpoint 返回 404 (可能在生产中禁用)"
        else
            check_fail "API 端点 $endpoint 错误 (HTTP $HTTP_CODE)"
        fi
    fi
done

# ========================================
# 5. API Documentation (should be disabled)
# ========================================
divider "[5/10] API 文档安全检查"

if curl -s http://localhost:8000/docs | grep -q "<!DOCTYPE"; then
    check_fail "API 文档在生产中仍然可访问 - 安全风险"
else
    check_pass "API 文档在生产中已禁用"
fi

# ========================================
# 6. System Resources
# ========================================
divider "[6/10] 系统资源检查"

# Memory
TOTAL_MEM=$(free -m | awk 'NR==2{print $2}')
USED_MEM=$(free -m | awk 'NR==2{print $3}')
MEM_PERCENT=$((USED_MEM * 100 / TOTAL_MEM))

if [ "$MEM_PERCENT" -lt 80 ]; then
    check_pass "内存使用率正常 ($MEM_PERCENT%)"
else
    check_warning "内存使用率较高 ($MEM_PERCENT%)"
fi

# Disk
USED_DISK=$(df / | awk 'NR==2{print $5}' | sed 's/%//')

if [ "$USED_DISK" -lt 80 ]; then
    check_pass "磁盘使用率正常 ($USED_DISK%)"
else
    check_warning "磁盘使用率较高 ($USED_DISK%)"
fi

# Check specific directories
if [ -d "/var/log/data-management-prod" ]; then
    LOG_SIZE=$(du -sh /var/log/data-management-prod | awk '{print $1}')
    check_pass "日志目录存在 (大小: $LOG_SIZE)"
else
    check_warning "日志目录不存在"
fi

# ========================================
# 7. Log Files
# ========================================
divider "[7/10] 日志文件检查"

if [ -f "/var/log/data-management-prod/app.log" ]; then
    check_pass "应用日志文件存在"

    LAST_MODIFIED=$(stat -c %Y /var/log/data-management-prod/app.log)
    NOW=$(date +%s)
    TIME_DIFF=$((NOW - LAST_MODIFIED))

    if [ "$TIME_DIFF" -lt 3600 ]; then
        check_pass "应用日志文件最近更新过"
    else
        check_warning "应用日志文件未最近更新 ($(($TIME_DIFF / 60)) 分钟前)"
    fi

    # Check for errors
    ERROR_COUNT=$(grep -c "ERROR" /var/log/data-management-prod/app.log || echo "0")
    if [ "$ERROR_COUNT" -eq 0 ]; then
        check_pass "应用日志中无错误"
    else
        check_warning "应用日志中有 $ERROR_COUNT 条错误信息"
    fi
else
    check_fail "应用日志文件不存在"
fi

if [ -f "/var/log/data-management-prod/errors/error.log" ]; then
    check_pass "错误日志文件存在"
else
    check_warning "错误日志文件不存在"
fi

# ========================================
# 8. Monitoring Configuration
# ========================================
divider "[8/10] 监控配置检查"

if [ -f "/etc/data-management-prod/monitoring-config.yml" ]; then
    check_pass "监控配置文件已部署"
else
    check_warning "监控配置文件未找到"
fi

if [ -f "/etc/data-management-prod/alerts/alert-rules.json" ]; then
    check_pass "告警规则已部署"

    ALERT_COUNT=$(grep -o '"alert_name"' /etc/data-management-prod/alerts/alert-rules.json | wc -l)
    check_pass "告警规则数量: $ALERT_COUNT"
else
    check_warning "告警规则文件未找到"
fi

if [ -f "/etc/logrotate.d/data-management-prod" ]; then
    check_pass "日志轮转配置已安装"
else
    check_warning "日志轮转配置未安装"
fi

# ========================================
# 9. Security
# ========================================
divider "[9/10] 安全性检查"

# Check file permissions
if [ -f "backend/.env.production" ]; then
    PERMS=$(ls -l backend/.env.production | awk '{print $1}')
    if [[ "$PERMS" == *"640"* ]] || [[ "$PERMS" == *"600"* ]] || [[ "$PERMS" == *"rw-"* ]]; then
        check_pass ".env.production 权限配置安全"
    else
        check_warning ".env.production 权限可能过开放: $PERMS"
    fi
fi

# Check if .env files are in .gitignore
if grep -q ".env" .gitignore 2>/dev/null; then
    check_pass ".env 文件已添加到 .gitignore"
else
    check_warning ".env 文件可能未添加到 .gitignore"
fi

# Check CORS configuration
if curl -s -H "Origin: http://malicious.com" http://localhost:8000/health | grep -q "access-control-allow-origin"; then
    CORS_ORIGIN=$(curl -s -H "Origin: http://malicious.com" http://localhost:8000/health | grep -i "access-control-allow-origin")
    if [[ "$CORS_ORIGIN" == *"malicious"* ]]; then
        check_fail "CORS 配置过于宽松 - 安全风险"
    else
        check_pass "CORS 配置受限"
    fi
fi

# ========================================
# 10. Backup Configuration
# ========================================
divider "[10/10] 备份配置检查"

if [ -d "/var/backups/data-management-prod" ]; then
    check_pass "备份目录已创建"

    BACKUP_COUNT=$(ls /var/backups/data-management-prod/*.sql 2>/dev/null | wc -l)
    if [ "$BACKUP_COUNT" -gt 0 ]; then
        check_pass "数据库备份存在 ($BACKUP_COUNT 个)"
        LATEST_BACKUP=$(ls -t /var/backups/data-management-prod/*.sql 2>/dev/null | head -1)
        check_pass "最新备份: $(basename $LATEST_BACKUP)"
    else
        check_warning "数据库备份目录为空"
    fi
else
    check_warning "备份目录未创建"
fi

# ========================================
# Summary Report
# ========================================
divider "验证结果总结"

TOTAL_CHECKS=$((CHECKS_PASSED + CHECKS_FAILED + CHECKS_WARNING))

echo -e "${GREEN}✅ 通过${NC}: $CHECKS_PASSED/$TOTAL_CHECKS"
echo -e "${YELLOW}⚠️  警告${NC}: $CHECKS_WARNING/$TOTAL_CHECKS"
echo -e "${RED}❌ 失败${NC}: $CHECKS_FAILED/$TOTAL_CHECKS"
echo ""

if [ "$CHECKS_FAILED" -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✅ 系统验证完成 - 生产环境就绪                               ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "系统状态: 🟢 READY FOR PRODUCTION"
    echo ""
    exit 0
elif [ "$CHECKS_WARNING" -gt 0 ] && [ "$CHECKS_FAILED" -eq 0 ]; then
    echo -e "${YELLOW}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║  ⚠️  系统验证完成 - 有警告需要注意                            ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "系统状态: 🟡 READY WITH WARNINGS"
    echo ""
    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ❌ 系统验证失败 - 需要修复问题                              ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "系统状态: 🔴 NOT READY - ISSUES DETECTED"
    echo ""
    exit 1
fi
