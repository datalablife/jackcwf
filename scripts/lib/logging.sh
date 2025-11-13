#!/bin/bash

################################################################################
# Logging Module - Comprehensive Logging System
# 支持文件和 stdout 两种日志模式
################################################################################

# 日志级别定义
LOG_LEVEL_DEBUG=0
LOG_LEVEL_INFO=1
LOG_LEVEL_WARNING=2
LOG_LEVEL_ERROR=3
LOG_LEVEL_CRITICAL=4

# 当前日志级别（可通过环境变量覆盖）
CURRENT_LOG_LEVEL="${LOG_LEVEL:-$LOG_LEVEL_INFO}"

# 日志文件配置
LOG_DIR="${LOG_DIR:-.}"
LOG_FILE="${LOG_FILE:-}"
LOG_TO_FILE="${LOG_TO_FILE:-false}"
LOG_TO_STDOUT="${LOG_TO_STDOUT:-true}"

# ============================================================================
# 初始化日志系统
# ============================================================================

# 设置本地开发日志（文件 + stdout）
setup_local_logging() {
    local env="${1:-development}"
    local log_base_dir="${2:-logs}"

    # 创建日志目录
    LOG_DIR="$log_base_dir/$env"
    ensure_dir "$LOG_DIR" || return 1

    # 设置日志文件
    LOG_FILE="$LOG_DIR/launcher-$(get_date).log"

    # 启用日志到文件和 stdout
    LOG_TO_FILE=true
    LOG_TO_STDOUT=true

    # 创建日志文件
    touch "$LOG_FILE" || {
        print_error "Failed to create log file: $LOG_FILE"
        return 1
    }

    log_info "launcher" "Local logging initialized: $LOG_FILE"
    return 0
}

# 设置容器日志（仅 stdout/stderr）
setup_container_logging() {
    # 容器环境：只输出到 stdout/stderr
    LOG_TO_FILE=false
    LOG_TO_STDOUT=true

    # 设置日志级别（容器通常使用 WARNING 或 ERROR）
    CURRENT_LOG_LEVEL="${LOG_LEVEL:-$LOG_LEVEL_WARNING}"

    # 禁用缓冲以确保日志立即输出
    export PYTHONUNBUFFERED=1
    export NODE_ENV=production
}

# ============================================================================
# 日志输出函数
# ============================================================================

# 核心日志函数
log_message() {
    local level="$1"
    local component="$2"
    local message="$3"
    local level_num="${4:-$LOG_LEVEL_INFO}"

    # 检查日志级别
    if [[ $level_num -lt $CURRENT_LOG_LEVEL ]]; then
        return 0
    fi

    # 生成时间戳
    local timestamp=$(get_datetime)

    # 格式化日志消息
    local log_entry="[$timestamp] [$level] [$component] $message"

    # 写入文件
    if [[ "$LOG_TO_FILE" == "true" ]] && [[ -n "$LOG_FILE" ]]; then
        echo "$log_entry" >> "$LOG_FILE" 2>/dev/null
    fi

    # 输出到 stdout/stderr
    if [[ "$LOG_TO_STDOUT" == "true" ]]; then
        case "$level" in
            DEBUG)
                echo -e "${GRAY}$log_entry${RESET}" >&1
                ;;
            INFO)
                echo -e "${BLUE}[INFO]${RESET} $message" >&1
                ;;
            WARNING)
                echo -e "${YELLOW}[WARN]${RESET} $message" >&1
                ;;
            ERROR)
                echo -e "${RED}[ERROR]${RESET} $message" >&2
                ;;
            CRITICAL)
                echo -e "${BRIGHT_RED}${BOLD}[CRITICAL]${RESET} $message" >&2
                ;;
        esac
    fi
}

# DEBUG 日志
log_debug() {
    local component="$1"
    local message="$2"
    log_message "DEBUG" "$component" "$message" $LOG_LEVEL_DEBUG
}

# INFO 日志
log_info() {
    local component="$1"
    local message="$2"
    log_message "INFO" "$component" "$message" $LOG_LEVEL_INFO
}

# WARNING 日志
log_warning() {
    local component="$1"
    local message="$2"
    log_message "WARNING" "$component" "$message" $LOG_LEVEL_WARNING
}

# ERROR 日志
log_error() {
    local component="$1"
    local message="$2"
    log_message "ERROR" "$component" "$message" $LOG_LEVEL_ERROR
}

# CRITICAL 日志
log_critical() {
    local component="$1"
    local message="$2"
    log_message "CRITICAL" "$component" "$message" $LOG_LEVEL_CRITICAL
}

# ============================================================================
# 结构化日志（JSON 格式，用于日志聚合）
# ============================================================================

# 输出结构化日志（JSON）
log_json() {
    local level="$1"
    local component="$2"
    local message="$3"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local hostname=$(hostname 2>/dev/null || echo "unknown")

    # 生成 JSON
    local json=$(cat <<EOF
{"timestamp":"$timestamp","level":"$level","component":"$component","message":"$message","environment":"${ENVIRONMENT:-unknown}","hostname":"$hostname","pid":$$}
EOF
)

    # 写入文件
    if [[ "$LOG_TO_FILE" == "true" ]] && [[ -n "$LOG_FILE" ]]; then
        echo "$json" >> "$LOG_FILE" 2>/dev/null
    fi

    # 输出到 stdout
    if [[ "$LOG_TO_STDOUT" == "true" ]]; then
        echo "$json" >&1
    fi
}

# ============================================================================
# 进度日志
# ============================================================================

# 日志进度
log_progress() {
    local component="$1"
    local message="$2"
    local current="$3"
    local total="$4"

    if [[ -n "$current" ]] && [[ -n "$total" ]]; then
        local percentage=$((current * 100 / total))
        log_info "$component" "$message ($current/$total - $percentage%)"
    else
        log_info "$component" "$message"
    fi
}

# ============================================================================
# 日志轮转
# ============================================================================

# 轮转日志文件
rotate_logs() {
    local log_dir="$1"
    local max_age_days="${2:-30}"

    if [[ ! -d "$log_dir" ]]; then
        return 0
    fi

    log_debug "logger" "Rotating logs in $log_dir (max age: ${max_age_days}d)"

    # 压缩昨天及以前的日志
    find "$log_dir" -name "*.log" -mtime +1 -type f | while read -r file; do
        if [[ ! "$file" =~ .gz$ ]]; then
            gzip "$file" 2>/dev/null && log_debug "logger" "Compressed: $file"
        fi
    done

    # 删除过期的压缩日志
    find "$log_dir" -name "*.log.gz" -mtime +$max_age_days -type f -delete

    # 创建归档目录并移动压缩日志
    local archive_dir="$log_dir/archive"
    if [[ ! -d "$archive_dir" ]]; then
        mkdir -p "$archive_dir"
    fi

    find "$log_dir" -maxdepth 1 -name "*.log.gz" -type f | while read -r file; do
        mv "$file" "$archive_dir/" 2>/dev/null && log_debug "logger" "Archived: $(basename $file)"
    done
}

# ============================================================================
# 日志查看和分析
# ============================================================================

# 显示最近的日志
show_recent_logs() {
    local log_file="$1"
    local lines="${2:-50}"

    if [[ ! -f "$log_file" ]]; then
        print_warning "Log file not found: $log_file"
        return 1
    fi

    print_subtitle "Recent logs (last $lines lines):"
    echo ""
    tail -n "$lines" "$log_file"
}

# 搜索日志
search_logs() {
    local pattern="$1"
    local log_dir="${2:-.}"

    print_info "Searching for: $pattern"
    grep -r "$pattern" "$log_dir" --include="*.log" --include="*.log.gz" | head -50
}

# 显示错误日志
show_error_logs() {
    local log_dir="${1:-.}"

    print_subtitle "Error logs:"
    grep -r "ERROR\|CRITICAL" "$log_dir" --include="*.log" --include="*.log.gz" | tail -50
}

# 统计日志
summarize_logs() {
    local log_file="$1"

    if [[ ! -f "$log_file" ]]; then
        print_warning "Log file not found: $log_file"
        return 1
    fi

    echo ""
    print_subtitle "Log Summary:"
    echo "Total lines: $(wc -l < "$log_file")"
    echo "DEBUG:    $(grep -c "\[DEBUG\]" "$log_file" || echo 0)"
    echo "INFO:     $(grep -c "\[INFO\]" "$log_file" || echo 0)"
    echo "WARNING:  $(grep -c "\[WARNING\]" "$log_file" || echo 0)"
    echo "ERROR:    $(grep -c "\[ERROR\]" "$log_file" || echo 0)"
    echo "CRITICAL: $(grep -c "\[CRITICAL\]" "$log_file" || echo 0)"
}

# ============================================================================
# 实时日志跟踪
# ============================================================================

# 跟踪日志文件
tail_logs() {
    local log_file="$1"
    local lines="${2:-50}"

    if [[ ! -f "$log_file" ]]; then
        print_error "Log file not found: $log_file"
        return 1
    fi

    print_info "Following log file: $log_file"
    echo "(Press Ctrl+C to stop)"
    echo ""

    tail -f -n "$lines" "$log_file"
}

# ============================================================================
# 导出函数
# ============================================================================

export -f setup_local_logging setup_container_logging
export -f log_message log_debug log_info log_warning log_error log_critical
export -f log_json
export -f log_progress
export -f rotate_logs
export -f show_recent_logs search_logs show_error_logs summarize_logs
export -f tail_logs
