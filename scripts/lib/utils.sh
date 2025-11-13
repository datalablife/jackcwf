#!/bin/bash

################################################################################
# Utils Module - General Purpose Utilities
# 提供通用工具函数
################################################################################

# ============================================================================
# 命令检查函数
# ============================================================================

# 检查命令是否存在
command_exists() {
    command -v "$1" > /dev/null 2>&1
}

# 检查命令并输出结果
check_command() {
    local cmd="$1"
    local display_name="${2:-$cmd}"

    if command_exists "$cmd"; then
        local version=$($cmd --version 2>/dev/null | head -1)
        print_success "$display_name - OK ${GRAY}($version)${RESET}"
        return 0
    else
        print_error "$display_name - NOT FOUND"
        return 1
    fi
}

# ============================================================================
# 文件和目录函数
# ============================================================================

# 检查文件是否存在
file_exists() {
    [[ -f "$1" ]]
}

# 检查目录是否存在
dir_exists() {
    [[ -d "$1" ]]
}

# 检查路径是否可读
is_readable() {
    [[ -r "$1" ]]
}

# 检查路径是否可写
is_writable() {
    [[ -w "$1" ]]
}

# 检查路径是否可执行
is_executable() {
    [[ -x "$1" ]]
}

# 获取绝对路径
get_absolute_path() {
    cd "$1" 2>/dev/null && pwd || echo "$1"
}

# 确保目录存在
ensure_dir() {
    local dir="$1"
    if [[ ! -d "$dir" ]]; then
        mkdir -p "$dir" || {
            print_error "Failed to create directory: $dir"
            return 1
        }
    fi
}

# 获取文件大小（字节）
get_file_size() {
    stat -f%z "$1" 2>/dev/null || stat -c%s "$1" 2>/dev/null || echo "0"
}

# ============================================================================
# 系统信息函数
# ============================================================================

# 获取操作系统
get_os() {
    case "$(uname -s)" in
        Linux*)     echo "Linux" ;;
        Darwin*)    echo "MacOS" ;;
        CYGWIN*)    echo "Windows" ;;
        MINGW*)     echo "Windows" ;;
        MSYS*)      echo "Windows" ;;
        *)          echo "Unknown" ;;
    esac
}

# 检测是否在 Docker 容器内
is_in_container() {
    [[ -f "/.dockerenv" ]] || grep -q "docker" /proc/1/cgroup 2>/dev/null
}

# 获取 CPU 核心数
get_cpu_cores() {
    if [[ "$(get_os)" == "MacOS" ]]; then
        sysctl -n hw.ncpu 2>/dev/null || echo "1"
    else
        nproc 2>/dev/null || echo "1"
    fi
}

# 获取可用内存（MB）
get_available_memory() {
    if [[ "$(get_os)" == "MacOS" ]]; then
        vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/.//' | awk '{printf "%.0f", $1 * 4 / 1024}'
    else
        free -m | awk 'NR==2 {print $7}'
    fi
}

# 获取磁盘可用空间（GB）
get_available_disk_space() {
    local path="${1:-.}"
    if [[ "$(get_os)" == "MacOS" ]]; then
        df -h "$path" | awk 'NR==2 {print $4}' | sed 's/G//'
    else
        df -BG "$path" | awk 'NR==2 {print $4}' | sed 's/G//'
    fi
}

# ============================================================================
# 环境和配置函数
# ============================================================================

# 加载环境文件
load_env_file() {
    local env_file="$1"

    if [[ ! -f "$env_file" ]]; then
        print_warning "Environment file not found: $env_file"
        return 1
    fi

    # 导出所有变量
    set -a
    source "$env_file"
    set +a

    return 0
}

# 验证环境变量
validate_env_var() {
    local var_name="$1"
    local var_value="${!var_name}"

    if [[ -z "$var_value" ]]; then
        print_error "Required environment variable not set: $var_name"
        return 1
    fi

    return 0
}

# 验证多个环境变量
validate_env_vars() {
    local required_vars=("$@")
    local missing_vars=()

    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done

    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        print_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            print_error "  - $var"
        done
        return 1
    fi

    return 0
}

# ============================================================================
# 进程管理函数
# ============================================================================

# 检查进程是否运行
is_process_running() {
    local pid="$1"
    kill -0 "$pid" 2>/dev/null
}

# 获取进程使用的端口
get_process_port() {
    local pid="$1"
    lsof -i -P -n 2>/dev/null | grep "$pid" | awk '{print $9}' | cut -d: -f2 | sort -u
}

# 检查端口是否被占用
is_port_in_use() {
    local port="$1"
    netstat -tuln 2>/dev/null | grep -q ":$port " || lsof -i ":$port" >/dev/null 2>&1
}

# 获取占用端口的进程信息
get_process_using_port() {
    local port="$1"
    lsof -i :$port 2>/dev/null | tail -1 | awk '{print $1, $2}'
}

# 优雅地杀死进程
kill_process_gracefully() {
    local pid="$1"
    local timeout="${2:-10}"
    local elapsed=0

    if ! is_process_running "$pid"; then
        return 0
    fi

    # 发送 SIGTERM
    kill -TERM "$pid" 2>/dev/null || return 1

    # 等待进程退出
    while is_process_running "$pid" && [[ $elapsed -lt $timeout ]]; do
        sleep 1
        elapsed=$((elapsed + 1))
    done

    # 如果还在运行，强制杀死
    if is_process_running "$pid"; then
        kill -9 "$pid" 2>/dev/null || return 1
    fi

    return 0
}

# ============================================================================
# 时间和日期函数
# ============================================================================

# 获取当前时间戳
get_timestamp() {
    date +%s
}

# 获取当前日期时间（格式化）
get_datetime() {
    date '+%Y-%m-%d %H:%M:%S'
}

# 获取当前日期（短格式）
get_date() {
    date '+%Y-%m-%d'
}

# 计算耗时（秒）
calculate_elapsed_time() {
    local start_time="$1"
    local end_time="${2:-$(get_timestamp)}"
    echo $((end_time - start_time))
}

# 格式化秒数为可读格式
format_duration() {
    local seconds="$1"
    local hours=$((seconds / 3600))
    local minutes=$(((seconds % 3600) / 60))
    local secs=$((seconds % 60))

    if [[ $hours -gt 0 ]]; then
        printf "%dh %dm %ds\n" $hours $minutes $secs
    elif [[ $minutes -gt 0 ]]; then
        printf "%dm %ds\n" $minutes $secs
    else
        printf "%ds\n" $secs
    fi
}

# ============================================================================
# 字符串函数
# ============================================================================

# 去除前后空格
trim() {
    local var="$1"
    var="${var#"${var%%[![:space:]]*}"}"
    var="${var%"${var##*[![:space:]]}"}"
    echo -n "$var"
}

# 检查字符串是否为空
is_empty() {
    [[ -z "$1" ]]
}

# 检查字符串是否相等（忽略大小写）
string_equals_ignore_case() {
    [[ "${1,,}" == "${2,,}" ]]
}

# 字符串包含子串
string_contains() {
    [[ "$1" == *"$2"* ]]
}

# ============================================================================
# 数据验证函数
# ============================================================================

# 检查是否为有效的 URL
is_valid_url() {
    local url="$1"
    local regex='^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
    [[ $url =~ $regex ]]
}

# 检查是否为有效的 IP 地址
is_valid_ip() {
    local ip="$1"
    local regex='^([0-9]{1,3}\.){3}[0-9]{1,3}$'
    if [[ $ip =~ $regex ]]; then
        # 检查每个八位组是否 <= 255
        local IFS=.
        local -a parts=($ip)
        [[ ${parts[0]} -le 255 && ${parts[1]} -le 255 &&
           ${parts[2]} -le 255 && ${parts[3]} -le 255 ]]
    else
        return 1
    fi
}

# 检查是否为有效的端口
is_valid_port() {
    local port="$1"
    [[ $port =~ ^[0-9]+$ ]] && [[ $port -ge 1 ]] && [[ $port -le 65535 ]]
}

# ============================================================================
# 网络函数
# ============================================================================

# 测试网络连接
test_network_connection() {
    local host="$1"
    local port="${2:-80}"
    local timeout="${3:-5}"

    timeout "$timeout" bash -c "cat < /dev/null > /dev/tcp/$host/$port" 2>/dev/null
}

# 等待服务可用（TCP）
wait_for_port() {
    local host="$1"
    local port="$2"
    local timeout="${3:-30}"
    local elapsed=0

    print_info "Waiting for $host:$port to be available..."

    while [[ $elapsed -lt $timeout ]]; do
        if test_network_connection "$host" "$port" 1; then
            print_success "Port $port is available"
            return 0
        fi

        sleep 1
        elapsed=$((elapsed + 1))
        progress_bar $elapsed $timeout
    done

    echo ""
    print_error "Timeout waiting for $host:$port"
    return 1
}

# 等待 HTTP 端点响应
wait_for_http() {
    local url="$1"
    local timeout="${2:-30}"
    local elapsed=0

    print_info "Waiting for $url to be available..."

    while [[ $elapsed -lt $timeout ]]; do
        if curl -sf "$url" >/dev/null 2>&1; then
            print_success "Endpoint $url is responding"
            return 0
        fi

        sleep 1
        elapsed=$((elapsed + 1))
        progress_bar $elapsed $timeout
    done

    echo ""
    print_error "Timeout waiting for $url"
    return 1
}

# ============================================================================
# 导出所有函数
# ============================================================================

export -f command_exists check_command
export -f file_exists dir_exists is_readable is_writable is_executable
export -f get_absolute_path ensure_dir get_file_size
export -f get_os is_in_container get_cpu_cores get_available_memory get_available_disk_space
export -f load_env_file validate_env_var validate_env_vars
export -f is_process_running get_process_port is_port_in_use get_process_using_port kill_process_gracefully
export -f get_timestamp get_datetime get_date calculate_elapsed_time format_duration
export -f trim is_empty string_equals_ignore_case string_contains
export -f is_valid_url is_valid_ip is_valid_port
export -f test_network_connection wait_for_port wait_for_http
