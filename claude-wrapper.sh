#!/bin/bash

# Claude Code Wrapper - 自动启用 Thinking 显示
# 这个脚本确保Claude Code总是显示思考过程，无需按ctrl+O

# 获取脚本所在的项目目录
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 合并thinking配置到config.json（如果存在）
CONFIG_FILE="$PROJECT_DIR/.claude/config.json"
THINKING_SETTINGS="$PROJECT_DIR/.claude/thinking-settings.json"

# 确保config.json存在
if [ ! -f "$CONFIG_FILE" ]; then
    echo "{}" > "$CONFIG_FILE"
fi

# 如果thinking-settings.json存在，将其配置合并到config.json
if [ -f "$THINKING_SETTINGS" ]; then
    # 使用jq或其他工具合并（如果可用）
    if command -v jq &> /dev/null; then
        # 使用jq合并配置
        MERGED=$(jq -s '.[0] * .[1]' "$CONFIG_FILE" "$THINKING_SETTINGS")
        echo "$MERGED" > "$CONFIG_FILE"
    fi
fi

# 添加thinking显示相关的环境变量
export CLAUDE_SHOW_THINKING=true
export CLAUDE_EXPAND_THINKING=true

# 调用真实的claude命令，传递所有参数
exec claude "$@"
