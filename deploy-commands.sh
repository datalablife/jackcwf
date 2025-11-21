#!/bin/bash
# 部署命令参考

APP_UUID="mg8c40oowo80o08o0gsw0gwc"
CONTEXT="myapp"
IMAGE="ghcr.io/datalablife/jackcwf:main-$(git rev-parse --short HEAD)"

# 1. 更新应用镜像
echo "1️⃣  更新应用镜像..."
coolify app update "$APP_UUID" \
  --context "$CONTEXT" \
  --image "$IMAGE" \
  --git-branch main

echo "✅ 应用已更新"

# 2. 触发部署
echo ""
echo "2️⃣  触发部署..."
coolify deploy trigger "$APP_UUID" --context "$CONTEXT"

echo "✅ 部署已触发"

# 3. 检查部署状态
echo ""
echo "3️⃣  检查部署状态..."
sleep 5
coolify app status "$APP_UUID" --context "$CONTEXT"

echo ""
echo "✅ 部署完成！"
