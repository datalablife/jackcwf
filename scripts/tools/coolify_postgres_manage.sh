#!/bin/bash

# Coolify PostgreSQL 管理脚本
# 用于快速管理 Coolify 中部署的 PostgreSQL 实例

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# PostgreSQL 应用信息
APP_UUID="ok0s0cgw8ck0w8kgs8kk4kk8"
APP_NAME="docker-image-ok0s0cgw8ck0w8kgs8kk4kk8"

# 打印信息函数
print_info() {
    echo -e "${BLUE}ℹ ${1}${NC}"
}

print_success() {
    echo -e "${GREEN}✓ ${1}${NC}"
}

print_error() {
    echo -e "${RED}✗ ${1}${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ ${1}${NC}"
}

# 命令菜单
show_menu() {
    echo ""
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}Coolify PostgreSQL 管理工具${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
    echo "应用信息:"
    echo "  UUID: $APP_UUID"
    echo "  名称: $APP_NAME"
    echo ""
    echo "可用命令:"
    echo "  1) status      - 查看应用状态"
    echo "  2) logs        - 查看应用日志"
    echo "  3) envs        - 查看环境变量"
    echo "  4) restart     - 重启应用"
    echo "  5) stop        - 停止应用"
    echo "  6) start       - 启动应用"
    echo "  7) test        - 测试数据库连接"
    echo "  8) psql        - 启动 psql 交互式客户端"
    echo "  9) info        - 显示连接信息"
    echo "  0) exit        - 退出"
    echo ""
}

# 查看状态
cmd_status() {
    print_info "获取应用状态..."
    coolify app get $APP_UUID
}

# 查看日志
cmd_logs() {
    print_info "显示最近的应用日志..."
    echo ""
    coolify app logs $APP_UUID | tail -30
    echo ""
    print_info "提示: 使用 'coolify app logs $APP_UUID' 查看全部日志"
}

# 查看环境变量
cmd_envs() {
    print_info "获取应用环境变量..."
    echo ""
    coolify app env list $APP_UUID --show-sensitive
    echo ""
}

# 重启应用
cmd_restart() {
    print_warning "正在重启应用..."
    coolify app restart $APP_UUID
    print_success "应用已重启"
}

# 停止应用
cmd_stop() {
    print_warning "正在停止应用..."
    coolify app stop $APP_UUID
    print_success "应用已停止"
}

# 启动应用
cmd_start() {
    print_info "正在启动应用..."
    coolify app start $APP_UUID
    print_success "应用已启动"
}

# 测试连接
cmd_test() {
    print_info "测试数据库连接..."
    echo ""

    if ! command -v psql &> /dev/null; then
        print_error "psql 未安装"
        return 1
    fi

    psql -h host.docker.internal -p 5432 -U jackcwf888 -d postgres -c "SELECT version();" 2>&1 && \
        print_success "数据库连接成功" || \
        print_error "数据库连接失败"
}

# 启动 psql 客户端
cmd_psql() {
    print_info "启动 psql 交互式客户端..."
    print_info "连接信息:"
    echo "  主机: host.docker.internal"
    echo "  端口: 5432"
    echo "  数据库: postgres"
    echo "  用户: jackcwf888"
    echo ""

    export PGPASSWORD="Jack_00492300"
    psql -h host.docker.internal -p 5432 -U jackcwf888 -d postgres
    unset PGPASSWORD
}

# 显示连接信息
cmd_info() {
    echo ""
    echo -e "${BLUE}========== PostgreSQL 连接信息 ==========${NC}"
    echo ""
    echo "主机: host.docker.internal"
    echo "端口: 5432"
    echo "数据库: postgres"
    echo "用户: jackcwf888"
    echo "密码: Jack_00492300"
    echo ""
    echo -e "${BLUE}========== 连接字符串 ==========${NC}"
    echo ""
    echo "psql:"
    echo "  psql -h host.docker.internal -p 5432 -U jackcwf888 -d postgres"
    echo ""
    echo "Python (psycopg2):"
    echo "  postgresql://jackcwf888:Jack_00492300@host.docker.internal:5432/postgres"
    echo ""
    echo "Node.js (pg):"
    echo '  {host: "host.docker.internal", port: 5432, user: "jackcwf888", password: "Jack_00492300"}'
    echo ""
    echo -e "${BLUE}========== Coolify 应用信息 ==========${NC}"
    echo ""
    echo "UUID: $APP_UUID"
    echo "名称: $APP_NAME"
    echo "FQDN: https://pgvctor.jackcwf.com"
    echo "镜像: lanterndata/lantern-suite:pg15-latest"
    echo ""
}

# 主循环
main() {
    while true; do
        show_menu
        read -p "请选择命令 [0-9]: " choice

        case $choice in
            1) cmd_status ;;
            2) cmd_logs ;;
            3) cmd_envs ;;
            4) cmd_restart ;;
            5) cmd_stop ;;
            6) cmd_start ;;
            7) cmd_test ;;
            8) cmd_psql ;;
            9) cmd_info ;;
            0)
                print_success "退出"
                exit 0
                ;;
            *)
                print_error "无效选择，请重试"
                ;;
        esac

        read -p "按 Enter 继续..."
    done
}

# 如果有参数，直接执行对应命令
if [ $# -gt 0 ]; then
    case $1 in
        status) cmd_status ;;
        logs) cmd_logs ;;
        envs) cmd_envs ;;
        restart) cmd_restart ;;
        stop) cmd_stop ;;
        start) cmd_start ;;
        test) cmd_test ;;
        psql) cmd_psql ;;
        info) cmd_info ;;
        *)
            print_error "未知命令: $1"
            print_info "可用命令: status, logs, envs, restart, stop, start, test, psql, info"
            exit 1
            ;;
    esac
else
    # 进入交互式菜单
    main
fi
