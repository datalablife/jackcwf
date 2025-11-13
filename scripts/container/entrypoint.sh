#!/bin/bash

################################################################################
# Container Entrypoint Script
# 容器入口点脚本 - 生产环境专用
#
# 用途: Docker 容器启动时的入口点
# 特点:
#   - PID 1 进程处理（Docker 容器中的主进程）
#   - 优雅关闭 (SIGTERM 信号处理)
#   - 数据库迁移自动执行
#   - JSON 日志输出（用于日志聚合）
#   - 健康检查支持
#   - 最优 Worker 数计算
################################################################################

set -o pipefail

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_ROOT="$(dirname "$SCRIPT_DIR")"
APP_ROOT="$(dirname "$SCRIPTS_ROOT")"

# 导入共享库
source "$SCRIPTS_ROOT/lib/ui.sh" 2>/dev/null || true
source "$SCRIPTS_ROOT/lib/utils.sh" 2>/dev/null || true
source "$SCRIPTS_ROOT/lib/logging.sh" 2>/dev/null || true
source "$SCRIPTS_ROOT/lib/signals.sh" 2>/dev/null || true

# ============================================================================
# 容器特定配置
# ============================================================================

# 环境配置
ENV_FILE="${SCRIPTS_ROOT}/config/prod.env"
ENV_NAME="production"

# 容器日志设置（仅 stdout/stderr，没有文件日志）
setup_container_logging

# 设置信号处理（SIGTERM 用于优雅关闭）
setup_signal_handlers

# ============================================================================
# 日志函数（容器模式下用简单输出）
# ============================================================================

# 简单的日志输出（容器中避免过多格式化）
echo_info() {
    echo "[INFO] $@"
}

echo_warn() {
    echo "[WARN] $@" >&2
}

echo_error() {
    echo "[ERROR] $@" >&2
}

echo_success() {
    echo "[SUCCESS] $@"
}

# ============================================================================
# 配置加载和验证
# ============================================================================

# 加载生产环境配置
load_container_env() {
    if [[ -f "$ENV_FILE" ]]; then
        set -a
        source "$ENV_FILE"
        set +a
        echo_info "Production environment variables loaded"
    else
        echo_warn "Environment file not found: $ENV_FILE, using defaults"
    fi

    # 验证关键环境变量
    required_vars=(
        "DATABASE_URL"
        "ENVIRONMENT"
    )

    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            echo_error "Required environment variable not set: $var"
            exit 1
        fi
    done

    # 显示容器配置
    echo_info "Container Configuration:"
    echo_info "  Environment: ${ENVIRONMENT}"
    echo_info "  Database: ${DATABASE_URL:0:50}..."
    echo_info "  Python Workers: ${BACKEND_WORKERS:-auto}"
}

# ============================================================================
# 前置条件检查
# ============================================================================

# 检查 Python 环境
check_python_env() {
    echo_info "Checking Python environment..."

    if [[ ! -d "$APP_ROOT/.venv" ]]; then
        echo_error "Virtual environment not found at $APP_ROOT/.venv"
        exit 1
    fi

    # 激活虚拟环境
    source "$APP_ROOT/.venv/bin/activate" || {
        echo_error "Failed to activate virtual environment"
        exit 1
    }

    # 验证 Python 版本
    local python_version=$(python --version 2>&1)
    echo_info "Python: $python_version"

    # 检查关键依赖
    python -c "import fastapi; import uvicorn; import sqlalchemy" 2>/dev/null || {
        echo_error "Critical Python dependencies missing"
        exit 1
    }

    echo_success "Python environment ready"
}

# 检查数据库连接
check_database() {
    echo_info "Checking database connection..."

    if [[ -z "$DATABASE_URL" ]]; then
        echo_error "DATABASE_URL environment variable not set"
        exit 1
    fi

    # 尝试连接到数据库
    local max_attempts=10
    local attempt=1
    local timeout=30

    while [[ $attempt -le $max_attempts ]]; do
        # 尝试使用 psql 连接
        if command_exists psql; then
            if timeout 5 psql "$DATABASE_URL" -c "SELECT 1" >/dev/null 2>&1; then
                echo_success "Database connection successful"
                return 0
            fi
        else
            # 如果 psql 不可用，尝试通过 Python 连接
            python -c "
import sqlalchemy
from sqlalchemy import create_engine
try:
    engine = create_engine('$DATABASE_URL')
    with engine.connect() as conn:
        conn.exec_driver_sql('SELECT 1')
    print('Database connection successful')
    exit(0)
except Exception as e:
    print(f'Connection failed: {e}')
    exit(1)
" 2>/dev/null && return 0
        fi

        echo_warn "Database connection attempt $attempt/$max_attempts failed, retrying..."
        sleep $((attempt * 2))  # 指数退避
        attempt=$((attempt + 1))
    done

    echo_error "Failed to connect to database after $max_attempts attempts"
    exit 1
}

# ============================================================================
# 数据库迁移
# ============================================================================

# 执行数据库迁移
run_database_migrations() {
    echo_info "Running database migrations..."

    cd "$APP_ROOT/backend" || {
        echo_error "Cannot change to backend directory"
        exit 1
    }

    # 检查 alembic.ini
    if [[ ! -f "alembic.ini" ]]; then
        echo_warn "alembic.ini not found, skipping migrations"
        return 0
    fi

    # 运行迁移
    alembic upgrade head 2>&1 | while read -r line; do
        echo_info "  Migration: $line"
    done

    if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
        echo_error "Database migrations failed"
        exit 1
    fi

    echo_success "Database migrations completed"
    cd "$APP_ROOT" || exit 1
}

# ============================================================================
# Worker 配置
# ============================================================================

# 计算最优 Worker 数量
calculate_workers() {
    local workers="${BACKEND_WORKERS}"

    # 如果未设置或设为 "auto"，根据 CPU 核数计算
    if [[ -z "$workers" ]] || [[ "$workers" == "auto" ]]; then
        local cpu_cores=$(get_cpu_cores)
        # 公式: workers = (cpu_cores * 2) + 1
        workers=$(( (cpu_cores * 2) + 1 ))

        # 限制范围: 最少 2, 最多 8
        if [[ $workers -lt 2 ]]; then
            workers=2
        elif [[ $workers -gt 8 ]]; then
            workers=8
        fi
    fi

    echo "$workers"
}

# ============================================================================
# 服务启动
# ============================================================================

# 启动 FastAPI 后端
start_backend() {
    echo_info "Starting FastAPI backend service..."

    cd "$APP_ROOT/backend" || {
        echo_error "Cannot change to backend directory"
        exit 1
    }

    # 计算 Worker 数
    local workers=$(calculate_workers)
    local host="${BACKEND_HOST:-0.0.0.0}"
    local port="${BACKEND_PORT:-8000}"

    echo_info "Backend Configuration:"
    echo_info "  Host: $host"
    echo_info "  Port: $port"
    echo_info "  Workers: $workers"
    echo_info "  Max Connections: ${DB_POOL_SIZE:-20}"

    # 启动 Uvicorn（作为 PID 1 进程）
    # 这个命令不会返回，它替代 shell 成为 PID 1 进程
    exec uvicorn src.main:app \
        --host "$host" \
        --port "$port" \
        --workers "$workers" \
        --access-log \
        --log-level "${LOG_LEVEL:-warning}" \
        --timeout-keep-alive 75 \
        --timeout-notify 30
}

# 健康检查端点
health_check() {
    echo_info "Health check requested"

    local port="${BACKEND_PORT:-8000}"
    local max_attempts=3
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        if timeout 5 curl -f "http://localhost:$port/health" >/dev/null 2>&1; then
            echo "OK"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done

    echo "FAILED"
    return 1
}

# ============================================================================
# 命令处理
# ============================================================================

# 处理命令参数
handle_command() {
    local cmd="${1:-start}"

    case "$cmd" in
        start)
            # 标准启动流程
            load_container_env
            echo ""
            check_python_env
            echo ""
            check_database
            echo ""
            run_database_migrations
            echo ""
            notify_container_ready
            echo ""
            echo_info "════════════════════════════════════════"
            echo_info "🚀 Container is ready, starting services..."
            echo_info "════════════════════════════════════════"
            echo ""
            start_backend
            ;;

        health)
            # 健康检查命令
            health_check
            ;;

        migrate)
            # 仅运行迁移命令
            load_container_env
            check_python_env
            check_database
            run_database_migrations
            echo_success "Migration completed"
            ;;

        shell)
            # 进入 shell 用于调试
            echo_info "Starting shell session..."
            /bin/bash
            ;;

        *)
            echo_error "Unknown command: $cmd"
            echo "Usage: $0 {start|health|migrate|shell}"
            exit 1
            ;;
    esac
}

# ============================================================================
# 主入口点
# ============================================================================

# 捕获错误
trap 'echo_error "Script error on line $LINENO"; exit 1' ERR

# 处理命令
handle_command "$@"
