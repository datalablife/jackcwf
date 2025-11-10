#!/bin/bash

# 后端启动脚本
# 用于开发和测试环境的快速启动

set -e

echo "🚀 启动后端服务..."

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python 3"
    exit 1
fi

echo "✅ Python 版本: $(python3 --version)"

# 检查 Poetry
if ! command -v poetry &> /dev/null; then
    echo "⚠️  警告: 未找到 Poetry，尝试使用 pip 安装依赖"
    pip install -r requirements.txt
else
    echo "✅ 安装 Python 依赖..."
    poetry install
fi

# 创建虚拟环境
if [ ! -d ".venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv .venv
fi

# 激活虚拟环境
source .venv/bin/activate

# 设置环境变量
echo "⚙️  设置环境变量..."
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# 检查数据库
echo "🗄️  检查数据库..."
if [ -f ".env" ]; then
    source .env
else
    echo "❌ 错误: 未找到 .env 文件"
    echo "提示: 请复制 .env.example 为 .env 并配置"
    exit 1
fi

# 运行数据库迁移
echo "🔄 运行数据库迁移..."
alembic upgrade head || echo "⚠️  迁移可能已经是最新版本"

# 启动后端服务
echo ""
echo "════════════════════════════════════════"
echo "🚀 后端服务已启动！"
echo "════════════════════════════════════════"
echo "API 地址: http://localhost:8000"
echo "API 文档: http://localhost:8000/docs"
echo "日志: 查看上方输出"
echo "════════════════════════════════════════"
echo ""

# 使用 uvicorn 启动 (开发)
if [ "$1" == "dev" ]; then
    echo "📝 开发模式: 启用自动重载..."
    uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
else
    # 使用 gunicorn 启动 (生产)
    echo "⚡ 生产模式: 使用 gunicorn..."
    gunicorn -w 4 -b 0.0.0.0:8000 --access-logfile - "src.main:app"
fi
