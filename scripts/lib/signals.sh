#!/bin/bash

################################################################################
# Signals Module - Graceful Shutdown and Signal Handling
# 处理信号、优雅关闭和资源清理
# 这是容器生产环境的关键！
################################################################################

# 全局变量存储进程 PID
BACKEND_PID=""
FRONTEND_PID=""
BACKGROUND_PIDS=()

# 标志位
SHUTDOWN_IN_PROGRESS=false
SHUTDOWN_TIMEOUT=30

# ============================================================================
# 信号处理设置
# ============================================================================

# 设置信号处理器
setup_signal_handlers() {
    # SIGTERM: 从容器运行时或操作系统发出的优雅关闭信号
    # 这是容器关闭时首先发送的信号
    trap 'handle_sigterm' SIGTERM

    # SIGINT: 来自用户的中断（Ctrl+C）
    trap 'handle_sigint' INT

    # SIGHUP: 终端断开连接
    trap 'handle_sighup' SIGHUP

    # EXIT: 脚本正常或异常退出
    trap 'handle_exit' EXIT

    log_debug "signals" "Signal handlers initialized"
}

# ============================================================================
# 信号处理函数
# ============================================================================

# 处理 SIGTERM（容器优雅关闭）
handle_sigterm() {
    log_warning "signals" "Received SIGTERM - initiating graceful shutdown"
    graceful_shutdown
    exit 0
}

# 处理 SIGINT（用户中断 Ctrl+C）
handle_sigint() {
    log_warning "signals" "Received SIGINT (Ctrl+C) - shutting down"
    graceful_shutdown
    exit 130  # 标准的 Ctrl+C 退出码
}

# 处理 SIGHUP（终端断开）
handle_sighup() {
    log_info "signals" "Received SIGHUP - continuing in background"
    # 通常不需要退出，继续运行
}

# 处理 EXIT（最后的清理）
handle_exit() {
    if [[ "$SHUTDOWN_IN_PROGRESS" != "true" ]]; then
        log_debug "signals" "Script exiting, cleaning up..."
        cleanup_all_resources
    fi
}

# ============================================================================
# 优雅关闭实现
# ============================================================================

graceful_shutdown() {
    # 防止重复关闭
    if [[ "$SHUTDOWN_IN_PROGRESS" == "true" ]]; then
        return 0
    fi

    SHUTDOWN_IN_PROGRESS=true

    log_info "signals" "Starting graceful shutdown sequence..."
    log_info "signals" "Timeout: ${SHUTDOWN_TIMEOUT}s"
    echo ""

    local shutdown_start=$(get_timestamp)

    # 关闭后端
    if [[ -n "$BACKEND_PID" ]]; then
        shutdown_backend "$BACKEND_PID"
    fi

    # 关闭前端
    if [[ -n "$FRONTEND_PID" ]]; then
        shutdown_frontend "$FRONTEND_PID"
    fi

    # 关闭所有后台进程
    shutdown_background_processes

    # 清理资源
    cleanup_all_resources

    local shutdown_end=$(get_timestamp)
    local shutdown_duration=$((shutdown_end - shutdown_start))

    log_success "signals" "Graceful shutdown completed in ${shutdown_duration}s"
}

# ============================================================================
# 服务关闭函数
# ============================================================================

# 关闭后端服务
shutdown_backend() {
    local pid="$1"

    if ! is_process_running "$pid"; then
        log_debug "signals" "Backend process (PID: $pid) is not running"
        return 0
    fi

    log_info "signals" "Shutting down backend (PID: $pid)..."

    # 发送 SIGTERM 给后端
    kill -TERM "$pid" 2>/dev/null || {
        log_warning "signals" "Failed to send SIGTERM to backend"
        return 1
    }

    # 等待后端优雅关闭
    local elapsed=0
    local wait_step=1

    while is_process_running "$pid" && [[ $elapsed -lt $SHUTDOWN_TIMEOUT ]]; do
        # 显示等待进度
        if [[ $((elapsed % 5)) -eq 0 ]]; then
            local remaining=$((SHUTDOWN_TIMEOUT - elapsed))
            log_debug "signals" "Waiting for backend to shutdown... (${remaining}s remaining)"
        fi

        sleep $wait_step
        elapsed=$((elapsed + wait_step))
    done

    # 检查后端是否已关闭
    if is_process_running "$pid"; then
        log_warning "signals" "Backend did not shutdown gracefully, forcing termination (kill -9)..."
        kill -9 "$pid" 2>/dev/null || {
            log_error "signals" "Failed to force kill backend"
        }

        # 再等待一下，确保进程已关闭
        sleep 1
    fi

    if ! is_process_running "$pid"; then
        log_success "signals" "Backend shut down successfully"
        return 0
    else
        log_error "signals" "Failed to shutdown backend"
        return 1
    fi
}

# 关闭前端服务
shutdown_frontend() {
    local pid="$1"

    if ! is_process_running "$pid"; then
        log_debug "signals" "Frontend process (PID: $pid) is not running"
        return 0
    fi

    log_info "signals" "Shutting down frontend (PID: $pid)..."

    # 发送 SIGTERM 给前端
    kill -TERM "$pid" 2>/dev/null || {
        log_warning "signals" "Failed to send SIGTERM to frontend"
        return 1
    }

    # 等待前端关闭（前端通常更快）
    local elapsed=0
    while is_process_running "$pid" && [[ $elapsed -lt 10 ]]; do
        sleep 1
        elapsed=$((elapsed + 1))
    done

    # 强制杀死（如果还在运行）
    if is_process_running "$pid"; then
        log_warning "signals" "Frontend did not shutdown, forcing termination..."
        kill -9 "$pid" 2>/dev/null
        sleep 1
    fi

    if ! is_process_running "$pid"; then
        log_success "signals" "Frontend shut down successfully"
        return 0
    else
        log_error "signals" "Failed to shutdown frontend"
        return 1
    fi
}

# 关闭所有后台进程
shutdown_background_processes() {
    if [[ ${#BACKGROUND_PIDS[@]} -eq 0 ]]; then
        return 0
    fi

    log_info "signals" "Shutting down ${#BACKGROUND_PIDS[@]} background process(es)..."

    for pid in "${BACKGROUND_PIDS[@]}"; do
        if is_process_running "$pid"; then
            log_debug "signals" "Terminating background process (PID: $pid)"
            kill -TERM "$pid" 2>/dev/null

            # 等待最多 5 秒
            local elapsed=0
            while is_process_running "$pid" && [[ $elapsed -lt 5 ]]; do
                sleep 1
                elapsed=$((elapsed + 1))
            done

            # 强制杀死
            if is_process_running "$pid"; then
                kill -9 "$pid" 2>/dev/null
            fi
        fi
    done

    log_success "signals" "Background processes shut down"
}

# ============================================================================
# 资源清理
# ============================================================================

cleanup_all_resources() {
    log_debug "signals" "Cleaning up resources..."

    # 清理临时文件
    cleanup_temp_files

    # 清理 PID 文件
    cleanup_pid_files

    # 清理端口（可选，可能需要 root）
    # cleanup_ports

    log_debug "signals" "Resource cleanup completed"
}

# 清理临时文件
cleanup_temp_files() {
    local temp_pattern="/tmp/launcher-*.tmp"

    if ls $temp_pattern 1>/dev/null 2>&1; then
        rm -f $temp_pattern 2>/dev/null || true
        log_debug "signals" "Temporary files cleaned up"
    fi
}

# 清理 PID 文件
cleanup_pid_files() {
    local pid_dir="${PID_DIR:-.}"

    if [[ -d "$pid_dir" ]] && ls "$pid_dir"/*.pid 1>/dev/null 2>&1; then
        rm -f "$pid_dir"/*.pid 2>/dev/null || true
        log_debug "signals" "PID files cleaned up"
    fi
}

# ============================================================================
# 进程管理辅助函数
# ============================================================================

# 注册后端 PID
register_backend_pid() {
    local pid="$1"
    BACKEND_PID="$pid"
    log_debug "signals" "Backend PID registered: $pid"
}

# 注册前端 PID
register_frontend_pid() {
    local pid="$1"
    FRONTEND_PID="$pid"
    log_debug "signals" "Frontend PID registered: $pid"
}

# 注册后台进程 PID
register_background_pid() {
    local pid="$1"
    BACKGROUND_PIDS+=("$pid")
    log_debug "signals" "Background PID registered: $pid"
}

# 等待所有进程
wait_for_all_processes() {
    local pids=("$@")

    if [[ ${#pids[@]} -eq 0 ]]; then
        return 0
    fi

    log_debug "signals" "Waiting for ${#pids[@]} process(es)..."

    # 等待任何进程退出
    wait -n "${pids[@]}" 2>/dev/null
    local exit_status=$?

    log_debug "signals" "One of the processes exited with status: $exit_status"
    return $exit_status
}

# ============================================================================
# 异常处理
# ============================================================================

# 处理启动失败
on_startup_failure() {
    local component="$1"
    local message="$2"

    log_critical "signals" "Startup failure in $component: $message"

    # 立即触发关闭
    graceful_shutdown

    exit 1
}

# 处理运行时错误
on_runtime_error() {
    local component="$1"
    local message="$2"
    local exit_code="${3:-1}"

    log_error "signals" "Runtime error in $component: $message"

    # 记录堆栈信息（如果可用）
    if [[ ${#BASH_SOURCE[@]} -gt 1 ]]; then
        log_debug "signals" "Call stack:"
        for ((i = ${#BASH_SOURCE[@]} - 1; i >= 1; i--)); do
            log_debug "signals" "  ${BASH_SOURCE[$i]}:${BASH_LINENO[$((i - 1))]}: ${FUNCNAME[$i]}"
        done
    fi

    return "$exit_code"
}

# ============================================================================
# 容器特定的处理
# ============================================================================

# 通知容器运行时准备就绪
notify_container_ready() {
    log_info "signals" "Container is ready and healthy"

    # 如果有特殊的准备就绪通知方式，在这里实现
    # 例如：写入特殊文件、发送 HTTP 响应等
}

# ============================================================================
# 导出函数
# ============================================================================

export -f setup_signal_handlers
export -f handle_sigterm handle_sigint handle_sighup handle_exit
export -f graceful_shutdown
export -f shutdown_backend shutdown_frontend shutdown_background_processes
export -f cleanup_all_resources cleanup_temp_files cleanup_pid_files
export -f register_backend_pid register_frontend_pid register_background_pid
export -f wait_for_all_processes
export -f on_startup_failure on_runtime_error
export -f notify_container_ready
