#!/bin/bash

################################################################################
# UI Module - Color, Icons and Formatting
# 提供彩色输出、图标和格式化工具
################################################################################

# ============================================================================
# 颜色定义（ANSI 转义码）
# ============================================================================

# 基础颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[0;37m'
GRAY='\033[0;90m'

# 明亮颜色
BRIGHT_RED='\033[0;91m'
BRIGHT_GREEN='\033[0;92m'
BRIGHT_YELLOW='\033[0;93m'
BRIGHT_BLUE='\033[0;94m'

# 背景颜色
BG_RED='\033[41m'
BG_GREEN='\033[42m'
BG_YELLOW='\033[43m'
BG_BLUE='\033[44m'

# 文本样式
BOLD='\033[1m'
DIM='\033[2m'
ITALIC='\033[3m'
UNDERLINE='\033[4m'
BLINK='\033[5m'
INVERT='\033[7m'

# 重置
RESET='\033[0m'
NC='\033[0m'

# ============================================================================
# 图标定义
# ============================================================================

# 检查是否支持 Unicode
if [[ "$LANG" =~ UTF-8 ]] || [[ "$LC_ALL" =~ UTF-8 ]]; then
    ICON_SUCCESS="✅"
    ICON_ERROR="❌"
    ICON_WARNING="⚠️ "
    ICON_INFO="ℹ️ "
    ICON_ARROW="➜"
    ICON_BULLET="•"
    ICON_CHECK="✓"
    ICON_CROSS="✗"
    ICON_CLOCK="⏱️ "
    ICON_ROCKET="🚀"
    ICON_GEAR="⚙️ "
    ICON_FOLDER="📁"
    ICON_FILE="📄"
    ICON_LINK="🔗"
    ICON_SHIELD="🛡️ "
    ICON_WAIT="⏳"
    ICON_LOADING="⌛"
else
    # 降级到 ASCII 符号
    ICON_SUCCESS="[OK]"
    ICON_ERROR="[ERR]"
    ICON_WARNING="[WARN]"
    ICON_INFO="[INFO]"
    ICON_ARROW=">"
    ICON_BULLET="*"
    ICON_CHECK="+"
    ICON_CROSS="-"
    ICON_CLOCK="[T]"
    ICON_ROCKET="[ROCKET]"
    ICON_GEAR="[GEAR]"
    ICON_FOLDER="[DIR]"
    ICON_FILE="[FILE]"
    ICON_LINK="[LINK]"
    ICON_SHIELD="[SHIELD]"
    ICON_WAIT="[WAIT]"
    ICON_LOADING="[...]"
fi

# ============================================================================
# 是否禁用颜色输出（用于 CI/CD）
# ============================================================================

if [[ "${CI}" == "true" ]] || [[ "${CI_ENVIRONMENT}" == "true" ]] || [[ ! -t 1 ]]; then
    # 在 CI 环境或非 TTY 中禁用颜色
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    MAGENTA=''
    CYAN=''
    WHITE=''
    GRAY=''
    BRIGHT_RED=''
    BRIGHT_GREEN=''
    BRIGHT_YELLOW=''
    BRIGHT_BLUE=''
    BOLD=''
    DIM=''
    ITALIC=''
    UNDERLINE=''
    RESET=''
    NC=''
fi

# ============================================================================
# 输出函数
# ============================================================================

# 成功消息
print_success() {
    echo -e "${GREEN}${BOLD}${ICON_SUCCESS} $*${RESET}"
}

# 错误消息
print_error() {
    echo -e "${RED}${BOLD}${ICON_ERROR} $*${RESET}" >&2
}

# 警告消息
print_warning() {
    echo -e "${YELLOW}${BOLD}${ICON_WARNING} $*${RESET}"
}

# 信息消息
print_info() {
    echo -e "${BLUE}${BOLD}${ICON_INFO} $*${RESET}"
}

# 调试消息
print_debug() {
    if [[ "${DEBUG}" == "true" ]] || [[ "${VERBOSE}" == "true" ]]; then
        echo -e "${GRAY}${ICON_INFO} [DEBUG] $*${RESET}"
    fi
}

# 消息（无图标）
print_message() {
    echo -e "$*"
}

# 标题
print_title() {
    local title="$1"
    local width=${2:-50}

    echo ""
    echo -e "${BOLD}${BLUE}╔$(printf '═%.0s' $(seq 1 $((width - 2))))╗${RESET}"
    printf "${BOLD}${BLUE}║${RESET}  %-$((width - 4))s  ${BOLD}${BLUE}║${RESET}\n" "$title"
    echo -e "${BOLD}${BLUE}╚$(printf '═%.0s' $(seq 1 $((width - 2))))╝${RESET}"
    echo ""
}

# 小标题
print_subtitle() {
    echo -e "${BOLD}${CYAN}$*${RESET}"
}

# 分隔线
print_separator() {
    echo -e "${GRAY}$(printf '─%.0s' $(seq 1 80))${RESET}"
}

# ============================================================================
# 进度条函数
# ============================================================================

# 简单进度条
progress_bar() {
    local current=$1
    local total=$2
    local width=40
    local percentage=$((current * 100 / total))
    local filled=$((current * width / total))

    printf "\r${BLUE}["
    printf "$(printf '█%.0s' $(seq 1 $filled))"
    printf "$(printf '░%.0s' $(seq 1 $((width - filled))))"
    printf "]${RESET} ${percentage}%%"
}

# 完成进度条
progress_bar_complete() {
    printf "\r${GREEN}[$(printf '█%.0s' $(seq 1 40))${RESET}] 100%%\n"
}

# ============================================================================
# 列表函数
# ============================================================================

# 项目列表
list_item() {
    local item="$1"
    echo -e "  ${ICON_BULLET} $item"
}

# 编号列表
numbered_list_item() {
    local num="$1"
    local item="$2"
    printf "  ${CYAN}%2d)${RESET} %s\n" "$num" "$item"
}

# ============================================================================
# 状态指示器
# ============================================================================

# 打印状态
print_status() {
    local status="$1"
    local message="$2"

    case "$status" in
        ok|success)
            print_success "$message"
            ;;
        error|fail)
            print_error "$message"
            ;;
        warning|warn)
            print_warning "$message"
            ;;
        info)
            print_info "$message"
            ;;
        *)
            print_message "$message"
            ;;
    esac
}

# 打印步骤
print_step() {
    local num="$1"
    local message="$2"
    echo -e "${BOLD}${CYAN}Step $num:${RESET} $message"
}

# ============================================================================
# 框式输出
# ============================================================================

# 简单框
print_box() {
    local message="$1"
    local width=${2:-60}

    echo -e "${BOLD}${BLUE}┌$(printf '─%.0s' $(seq 1 $((width - 2))))┐${RESET}"
    printf "${BOLD}${BLUE}│${RESET} %-$((width - 4))s${BOLD}${BLUE}│${RESET}\n" "$message"
    echo -e "${BOLD}${BLUE}└$(printf '─%.0s' $(seq 1 $((width - 2))))┘${RESET}"
}

# ============================================================================
# 问题和确认
# ============================================================================

# 确认对话框
confirm() {
    local prompt="$1"
    local response

    while true; do
        read -p "$(echo -e ${YELLOW}$prompt${RESET}) (y/n): " response
        case "$response" in
            [yY][eE][sS]|[yY])
                return 0
                ;;
            [nN][oO]|[nN])
                return 1
                ;;
            *)
                echo "Please answer yes or no."
                ;;
        esac
    done
}

# 选择菜单
select_option() {
    local options=("$@")
    local ps3="$(echo -e ${CYAN}Select an option:${RESET}) "

    select opt in "${options[@]}"; do
        if [[ -n "$opt" ]]; then
            echo "$opt"
            break
        fi
    done
}

# ============================================================================
# 导出所有函数（用于 source）
# ============================================================================

export -f print_success print_error print_warning print_info print_debug
export -f print_message print_title print_subtitle print_separator
export -f progress_bar progress_bar_complete
export -f list_item numbered_list_item
export -f print_status print_step print_box
export -f confirm select_option
