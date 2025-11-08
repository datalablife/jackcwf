#!/bin/bash

# Claude Code 文件整理脚本 - 手动版
# 功能：查找并整理所有优先级1的文件到根目录
# 使用方法：./cleanup-claude-files.sh

set -e

PROJECT_ROOT="$(pwd)"
CLAUDE_DIR="$PROJECT_ROOT/.claude"

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  Claude Code 文件输出规则 - 文件整理工具                ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# 检查是否在项目根目录
if [ ! -d ".git" ]; then
    echo "❌ 错误：请在项目根目录运行此脚本"
    exit 1
fi

# 检查是否存在 docs/ 目录
if [ ! -d "docs" ]; then
    echo "ℹ️  没有找到 docs/ 目录，跳过整理"
    exit 0
fi

# 运行脚本
bash "$CLAUDE_DIR/reorganize-files.sh"

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  文件整理完成！                                         ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "📝 下一步："
echo "   1. git add . (添加所有更改)"
echo "   2. git commit -m 'docs: reorganize files per output rules'"
echo "   3. git push (推送到远程仓库)"
echo ""
