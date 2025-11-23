#!/bin/bash

#######################################################################
# 前端代码强制同步到GitHub脚本
# 用途: 快速同步本地前端代码到GitHub并触发工作流
# 用法: ./scripts/sync-frontend-to-github.sh
#######################################################################

set -e

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║            前端代码强制同步到GitHub - FORCE SYNC SCRIPT                   ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# 色彩定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 步骤1: 验证git仓库
echo -e "${BLUE}【步骤1】验证Git仓库...${NC}"
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}✗ 错误: 不是一个Git仓库${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Git仓库验证成功${NC}"
echo ""

# 步骤2: 检查当前分支
echo -e "${BLUE}【步骤2】检查当前分支...${NC}"
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "当前分支: $CURRENT_BRANCH"

if [ "$CURRENT_BRANCH" != "main" ]; then
    echo -e "${YELLOW}⚠ 警告: 不在main分支上${NC}"
    read -p "是否切换到main分支? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git checkout main
    else
        echo -e "${RED}✗ 已取消${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✓ 分支验证完成${NC}"
echo ""

# 步骤3: 检查本地修改
echo -e "${BLUE}【步骤3】检查本地修改...${NC}"
if [ -z "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠ 提示: 没有检测到本地修改${NC}"
    echo "当前本地代码与远程一致"
else
    echo -e "${YELLOW}✓ 检测到本地修改:${NC}"
    git status --short | head -20
fi
echo ""

# 步骤4: 添加所有改动
echo -e "${BLUE}【步骤4】添加所有改动到暂存区...${NC}"
git add -A
echo -e "${GREEN}✓ 已暂存所有改动${NC}"
echo ""

# 步骤5: 检查将要提交的内容
echo -e "${BLUE}【步骤5】检查将要提交的内容...${NC}"
STAGED_FILES=$(git diff --cached --name-only | wc -l)
if [ "$STAGED_FILES" -eq 0 ]; then
    echo -e "${YELLOW}⚠ 没有文件需要提交${NC}"
    echo "本地与远程保持一致"
    echo ""
    echo "如果您在IDE中修改了文件但没有保存，请:"
    echo "  1. 保存IDE中的文件 (Ctrl+S)"
    echo "  2. 重新运行此脚本"
    exit 0
else
    echo -e "${GREEN}✓ 将提交 $STAGED_FILES 个文件${NC}"
    git diff --cached --stat | head -20
fi
echo ""

# 步骤6: 提交修改
echo -e "${BLUE}【步骤6】提交修改...${NC}"
COMMIT_MESSAGE="feat: Force sync frontend code to latest version - $(date +%Y-%m-%d\ %H:%M:%S)"
git commit -m "$COMMIT_MESSAGE"
COMMIT_HASH=$(git rev-parse --short HEAD)
echo -e "${GREEN}✓ 提交成功: $COMMIT_HASH${NC}"
echo ""

# 步骤7: 推送到GitHub
echo -e "${BLUE}【步骤7】推送到GitHub...${NC}"
git push origin main
echo -e "${GREEN}✓ 推送成功${NC}"
echo ""

# 步骤8: 验证工作流触发
echo -e "${BLUE}【步骤8】验证工作流触发...${NC}"
sleep 3
echo "检查工作流状态..."
LATEST_RUN=$(gh run list --workflow build-and-deploy.yml --limit 1 --json status,conclusion,displayTitle,createdAt 2>/dev/null)

if [ -n "$LATEST_RUN" ]; then
    echo -e "${GREEN}✓ 工作流已触发${NC}"
    echo "$LATEST_RUN" | jq '.[0] | {status, displayTitle, createdAt}'
else
    echo -e "${YELLOW}⚠ 无法获取工作流状态，请手动检查:${NC}"
    echo "  https://github.com/datalablife/jackcwf/actions"
fi
echo ""

# 步骤9: 显示部署时间线
echo -e "${BLUE}【部署时间线】${NC}"
echo ""
echo "⏱ 时间线预计:"
echo "  • GitHub Actions 运行: ~1分钟"
echo "  • Docker 镜像构建: ~2分钟"
echo "  • 推送到GHCR: ~30秒"
echo "  • Coolify webhook触发: 自动"
echo "  • 容器重启: ~5分钟"
echo "  • 应用启动: ~1分钟"
echo ""
echo "总计: 约 10-15 分钟内，新前端代码将在Coolify上线"
echo ""

# 步骤10: 验证步骤
echo -e "${BLUE}【验证步骤】${NC}"
echo ""
echo "推送后，请按以下步骤验证:"
echo ""
echo "1️⃣  检查GitHub工作流状态:"
echo "    gh run list --workflow build-and-deploy.yml --limit 1"
echo ""
echo "2️⃣  访问应用地址:"
echo "    https://chat.jackcwf.com"
echo ""
echo "3️⃣  清除浏览器缓存:"
echo "    • 按 Ctrl+Shift+Delete (或 Cmd+Shift+Delete)"
echo "    • 选择'所有时间'"
echo "    • 清除缓存"
echo ""
echo "4️⃣  硬刷新浏览器:"
echo "    • 按 Ctrl+Shift+R (或 Cmd+Shift+R)"
echo "    • 或在DevTools中禁用缓存后重新加载"
echo ""
echo "5️⃣  验证前端代码:"
echo "    • 查看页面源代码"
echo "    • 检查最后修改时间是否为最新"
echo ""

echo -e "${GREEN}✓ 前端代码强制同步完成！${NC}"
echo ""
echo "📝 摘要:"
echo "  提交: $COMMIT_HASH"
echo "  提交信息: $COMMIT_MESSAGE"
echo "  分支: main"
echo "  推送状态: 成功"
echo ""
