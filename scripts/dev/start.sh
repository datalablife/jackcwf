#!/bin/bash

################################################################################
# Development Environment Startup Script
# 开发环境启动脚本 - 启动前后端服务
#
# 用途: 在开发环境中快速启动前后端服务
# 特点:
#   - 自动热重载 (backend: uvicorn --reload, frontend: Vite dev server)
#   - 彩色输出和进度信息
#   - 文件和 stdout 双重日志
#   - 优雅关闭 (Ctrl+C)
#   - 环境检查和依赖验证
################################################################################

set -o pipefail  # 管道失败时返回错误

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_ROOT="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$SCRIPTS_ROOT")"

# 导入共享库
source "$SCRIPTS_ROOT/lib/ui.sh" || { echo "Failed to source ui.sh"; exit 1; }
source "$SCRIPTS_ROOT/lib/utils.sh" || { echo "Failed to source utils.sh"; exit 1; }
source "$SCRIPTS_ROOT/lib/logging.sh" || { echo "Failed to source logging.sh"; exit 1; }
source "$SCRIPTS_ROOT/lib/signals.sh" || { echo "Failed to source signals.sh"; exit 1; }

# ============================================================================
# 配置常量
# ============================================================================

# 环境配置
ENV_FILE="$SCRIPTS_ROOT/config/dev.env"
ENV_NAME="development"

# 服务配置
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# 默认环境变量
DEFAULT_BACKEND_HOST="127.0.0.1"
DEFAULT_BACKEND_PORT="8000"
DEFAULT_FRONTEND_PORT="5173"

# ============================================================================
# 初始化
# ============================================================================

# 初始化日志系统（开发模式：文件 + stdout）
setup_local_logging "$ENV_NAME" "$PROJECT_ROOT/logs" || {
    print_error "Failed to setup logging"
    exit 1
}

log_info "launcher" "Starting development environment..."
log_debug "launcher" "Script directory: $SCRIPT_DIR"
log_debug "launcher" "Project root: $PROJECT_ROOT"

# 设置信号处理器（优雅关闭）
setup_signal_handlers

# ============================================================================
# 辅助函数
# ============================================================================

# 加载环境配置
load_dev_env() {
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error "launcher" "Environment file not found: $ENV_FILE"
        on_startup_failure "launcher" "Missing environment configuration"
        exit 1
    fi

    load_env_file "$ENV_FILE" || {
        log_error "launcher" "Failed to load environment file"
        on_startup_failure "launcher" "Failed to load environment configuration"
        exit 1
    }

    log_info "launcher" "Environment variables loaded from $ENV_FILE"
    log_debug "launcher" "ENVIRONMENT=$ENVIRONMENT"
    log_debug "launcher" "BACKEND_PORT=${BACKEND_PORT:-$DEFAULT_BACKEND_PORT}"
    log_debug "launcher" "FRONTEND_PORT=${FRONTEND_PORT:-$DEFAULT_FRONTEND_PORT}"
}

# 检查必要的命令
check_commands() {
    local commands=("node" "npm" "python3" "poetry")
    local missing_commands=()

    print_subtitle "🔍 检查必要命令..."

    for cmd in "${commands[@]}"; do
        if command_exists "$cmd"; then
            log_info "launcher" "✓ Found $cmd: $(check_command "$cmd")"
        else
            log_warning "launcher" "✗ Missing command: $cmd"
            missing_commands+=("$cmd")
        fi
    done

    if [[ ${#missing_commands[@]} -gt 0 ]]; then
        log_error "launcher" "Missing required commands: ${missing_commands[*]}"
        on_startup_failure "launcher" "Missing required commands: ${missing_commands[*]}"
        exit 1
    fi

    echo ""
}

# 检查目录结构
check_directories() {
    print_subtitle "📁 检查项目目录..."

    local dirs=("$BACKEND_DIR" "$FRONTEND_DIR")

    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            log_error "launcher" "Directory not found: $dir"
            on_startup_failure "launcher" "Missing directory: $dir"
            exit 1
        fi
        log_debug "launcher" "✓ Directory exists: $dir"
    done

    echo ""
}

# 检查并安装后端依赖
setup_backend_dependencies() {
    print_subtitle "🐍 检查后端依赖..."

    cd "$BACKEND_DIR" || {
        log_error "launcher" "Failed to change to backend directory"
        on_startup_failure "backend" "Cannot access backend directory"
        exit 1
    }

    # 检查 Python 环境
    if [[ ! -d ".venv" ]]; then
        log_info "launcher" "Creating Python virtual environment..."
        python3 -m venv .venv || {
            log_error "launcher" "Failed to create virtual environment"
            on_startup_failure "backend" "Failed to create Python virtual environment"
            exit 1
        }
    fi

    # 使用 Poetry 安装依赖
    if command_exists poetry; then
        log_info "launcher" "Installing Python dependencies with Poetry..."
        poetry install --no-interaction 2>&1 | while read -r line; do
            log_debug "backend-setup" "$line"
        done

        if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
            log_error "launcher" "Failed to install Poetry dependencies"
            on_startup_failure "backend" "Poetry dependency installation failed"
            exit 1
        fi
    else
        log_warning "launcher" "Poetry not found, attempting pip install..."
        source .venv/bin/activate
        pip install -r requirements.txt 2>&1 | while read -r line; do
            log_debug "backend-setup" "$line"
        done
    fi

    log_success "launcher" "Backend dependencies ready"
    echo ""

    cd "$PROJECT_ROOT" || exit 1
}

# 检查并安装前端依赖
setup_frontend_dependencies() {
    print_subtitle "📦 检查前端依赖..."

    cd "$FRONTEND_DIR" || {
        log_error "launcher" "Failed to change to frontend directory"
        on_startup_failure "frontend" "Cannot access frontend directory"
        exit 1
    }

    if [[ ! -d "node_modules" ]]; then
        log_info "launcher" "Installing npm dependencies..."
        npm install 2>&1 | while read -r line; do
            log_debug "frontend-setup" "$line"
        done

        if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
            log_error "launcher" "Failed to install npm dependencies"
            on_startup_failure "frontend" "npm dependency installation failed"
            exit 1
        fi
    else
        log_debug "launcher" "node_modules directory exists, skipping npm install"
    fi

    log_success "launcher" "Frontend dependencies ready"
    echo ""

    cd "$PROJECT_ROOT" || exit 1
}

# 检查数据库连接
check_database_connection() {
    print_subtitle "🗄️  检查数据库连接..."

    if [[ -z "$DATABASE_URL" ]]; then
        log_warning "launcher" "DATABASE_URL not set, skipping database check"
        echo ""
        return 0
    fi

    # 提取主机和端口
    local db_host=$(echo "$DATABASE_URL" | grep -oP 'postgresql[^\s]*/[^@]*@\K[^:]+')
    local db_port=$(echo "$DATABASE_URL" | grep -oP ':\K[0-9]+(?=/)')
    local db_port="${db_port:-5432}"

    if [[ -n "$db_host" ]]; then
        if wait_for_port "$db_host" "$db_port" 5; then
            log_success "launcher" "Database connection successful"
        else
            log_warning "launcher" "Could not connect to database at $db_host:$db_port"
            log_warning "launcher" "This may cause issues when the backend starts"
            confirm "Continue anyway?" || {
                log_error "launcher" "Startup cancelled by user"
                exit 1
            }
        fi
    fi

    echo ""
}

# 启动后端服务
start_backend() {
    local port="${BACKEND_PORT:-$DEFAULT_BACKEND_PORT}"
    local host="${BACKEND_HOST:-$DEFAULT_BACKEND_HOST}"

    print_subtitle "🚀 启动后端服务..."

    cd "$BACKEND_DIR" || {
        on_startup_failure "backend" "Cannot access backend directory"
        exit 1
    }

    # 设置 Python 环境变量
    export PYTHONUNBUFFERED=1
    export PYTHONDONTWRITEBYTECODE=1

    # 激活虚拟环境
    if [[ -f ".venv/bin/activate" ]]; then
        source .venv/bin/activate
    fi

    # 运行数据库迁移
    log_info "launcher" "Running database migrations..."
    alembic upgrade head 2>&1 | while read -r line; do
        log_debug "backend" "$line"
    done || log_warning "launcher" "Database migration may have failed"

    # 启动 Uvicorn
    log_info "launcher" "Starting Uvicorn development server..."

    # 在后台启动后端
    uvicorn src.main:app \
        --reload \
        --host "$host" \
        --port "$port" \
        --log-level info \
        >> "$LOG_FILE" 2>&1 &

    local backend_pid=$!
    register_backend_pid "$backend_pid"

    log_debug "launcher" "Backend PID: $backend_pid"

    # 等待后端启动
    if wait_for_http "http://localhost:$port/health" 30; then
        log_success "launcher" "Backend started successfully"
        echo ""
    else
        log_error "launcher" "Backend failed to start"
        # 尝试获取错误日志
        log_error "launcher" "Last 20 lines of backend log:"
        tail -n 20 "$LOG_FILE" 2>/dev/null | while read -r line; do
            log_error "launcher" "  $line"
        done
        on_startup_failure "backend" "Failed to start backend service"
        exit 1
    fi

    cd "$PROJECT_ROOT" || exit 1
}

# 启动前端服务
start_frontend() {
    local port="${FRONTEND_PORT:-$DEFAULT_FRONTEND_PORT}"

    print_subtitle "🎨 启动前端服务..."

    cd "$FRONTEND_DIR" || {
        on_startup_failure "frontend" "Cannot access frontend directory"
        exit 1
    }

    log_info "launcher" "Starting Vite development server..."

    # 在后台启动前端
    npm run dev \
        -- --port "$port" \
        >> "$LOG_FILE" 2>&1 &

    local frontend_pid=$!
    register_frontend_pid "$frontend_pid"

    log_debug "launcher" "Frontend PID: $frontend_pid"

    # 等待前端启动
    if wait_for_http "http://localhost:$port" 30; then
        log_success "launcher" "Frontend started successfully"
        echo ""
    else
        log_error "launcher" "Frontend failed to start"
        log_error "launcher" "Last 20 lines of frontend log:"
        tail -n 20 "$LOG_FILE" 2>/dev/null | while read -r line; do
            log_error "launcher" "  $line"
        done
        on_startup_failure "frontend" "Failed to start frontend service"
        exit 1
    fi

    cd "$PROJECT_ROOT" || exit 1
}

# 显示启动摘要
show_startup_summary() {
    local backend_port="${BACKEND_PORT:-$DEFAULT_BACKEND_PORT}"
    local frontend_port="${FRONTEND_PORT:-$DEFAULT_FRONTEND_PORT}"
    local backend_host="${BACKEND_HOST:-$DEFAULT_BACKEND_HOST}"

    echo ""
    print_box "✨ 开发环境启动完成！" "success"
    echo ""
    echo "📋 服务信息:"
    echo ""
    echo "  后端 (FastAPI + Uvicorn):"
    echo "    🔗 API:       http://localhost:$backend_port"
    echo "    📚 文档:      http://localhost:$backend_port/docs"
    echo "    🔍 ReDoc:     http://localhost:$backend_port/redoc"
    echo "    🌐 Host:      $backend_host"
    echo ""
    echo "  前端 (React + Vite):"
    echo "    🔗 应用:      http://localhost:$frontend_port"
    echo "    📂 项目:      $FRONTEND_DIR"
    echo ""
    echo "📝 日志:"
    echo "    📄 文件:      $LOG_FILE"
    echo "    👀 实时查看:  tail -f $LOG_FILE"
    echo ""
    echo "🔄 热重载:"
    echo "    后端: 修改 backend/src 中的文件会自动重载"
    echo "    前端: 修改 frontend/src 中的文件会自动刷新"
    echo ""
    echo "⏹️  停止: 按 Ctrl+C 优雅关闭所有服务"
    echo "════════════════════════════════════════"
    echo ""

    log_success "launcher" "All services started successfully"
}

# ============================================================================
# 主程序流程
# ============================================================================

main() {
    print_banner "🚀 Development Environment Launcher" "blue"
    echo ""

    # 第一步: 加载环境配置
    log_info "launcher" "Step 1/6: Loading environment configuration..."
    load_dev_env

    # 第二步: 检查命令
    log_info "launcher" "Step 2/6: Checking required commands..."
    check_commands

    # 第三步: 检查目录
    log_info "launcher" "Step 3/6: Checking project directories..."
    check_directories

    # 第四步: 检查和安装后端依赖
    log_info "launcher" "Step 4/6: Setting up backend dependencies..."
    setup_backend_dependencies

    # 第五步: 检查和安装前端依赖
    log_info "launcher" "Step 5/6: Setting up frontend dependencies..."
    setup_frontend_dependencies

    # 第六步: 检查数据库
    log_info "launcher" "Step 6/6: Checking database connection..."
    check_database_connection

    # 启动服务
    log_info "launcher" "Starting services..."
    echo ""

    start_backend
    start_frontend

    # 显示摘要
    show_startup_summary

    # 等待子进程
    log_info "launcher" "Waiting for services... (Press Ctrl+C to stop)"
    wait -n
    local exit_status=$?

    log_warning "launcher" "One of the processes exited with status: $exit_status"
    graceful_shutdown
}

# 捕获异常
trap 'on_runtime_error "launcher" "Unexpected error" 1' ERR

# 运行主程序
main "$@"
