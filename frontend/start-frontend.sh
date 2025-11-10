#!/bin/bash

# 前端启动脚本
# 用于开发和测试环境的快速启动

set -e

echo "🚀 启动前端应用..."

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 未找到 Node.js"
    echo "提示: 请访问 https://nodejs.org 下载安装"
    exit 1
fi

echo "✅ Node.js 版本: $(node --version)"
echo "✅ npm 版本: $(npm --version)"

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装 npm 依赖..."
    npm install
fi

# 设置环境变量
echo "⚙️  设置环境变量..."
if [ ! -f ".env.local" ]; then
    echo "VITE_API_URL=http://localhost:8000" > .env.local
    echo "✅ 创建 .env.local 文件"
fi

# 代码检查
echo "🔍 运行代码检查..."
npm run lint || echo "⚠️  存在 linting 警告"

# 启动前端
echo ""
echo "════════════════════════════════════════"
echo "🚀 前端应用已启动！"
echo "════════════════════════════════════════"
echo "应用地址: http://localhost:5173"
echo "API 地址: http://localhost:8000"
echo "════════════════════════════════════════"
echo ""

if [ "$1" == "build" ]; then
    echo "🏗️  构建生产版本..."
    npm run build
    echo "✅ 构建完成！输出目录: dist/"
elif [ "$1" == "test" ]; then
    echo "🧪 运行测试..."
    npm test
else
    echo "👀 开发模式: 启用热重载..."
    npm run dev
fi
