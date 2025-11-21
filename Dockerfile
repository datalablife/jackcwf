# 多阶段构建 Docker 镜像
# 支持 Supervisor 进程管理，整合前后端服务

# ============================================
# 阶段 1: 构建后端依赖
# ============================================
FROM python:3.12-slim AS backend-builder

WORKDIR /build

# 安装构建工具
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY pyproject.toml pyproject.toml

# 使用 uv 快速安装
RUN pip install uv && \
    uv pip install -e "." --system

# ============================================
# 阶段 2: 构建前端
# ============================================
FROM node:20-slim AS frontend-builder

WORKDIR /build

# 复制前端文件
COPY frontend/package*.json ./
RUN npm ci

# 复制源码
COPY frontend/ ./

# 构建前端
RUN npm run build

# ============================================
# 阶段 3: 最终生产镜像
# ============================================
FROM python:3.12-slim

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    nodejs npm \
    supervisor \
    nginx \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ============================================
# 复制后端依赖和代码
# ============================================
COPY --from=backend-builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# 复制后端源码
COPY src/ ./src/
COPY pyproject.toml .

# ============================================
# 复制前端构建结果
# ============================================
COPY --from=frontend-builder /build/dist /usr/share/nginx/html
COPY frontend/package*.json frontend/

# 安装 serve (用于生产环境前端)
RUN npm install -g serve

# ============================================
# 配置 Supervisor
# ============================================
RUN mkdir -p /etc/supervisor/conf.d /var/log/supervisor /var/log/app

COPY docker/supervisord.conf /etc/supervisor/supervisord.conf

# ============================================
# 配置 Nginx (前端反向代理)
# ============================================
COPY docker/nginx.conf /etc/nginx/nginx.conf

# ============================================
# 健康监控脚本
# ============================================
RUN mkdir -p /app/scripts/monitor
COPY scripts/monitor/ /app/scripts/monitor/

RUN chmod +x /app/scripts/monitor/*.py \
    && chmod +x /app/scripts/monitor/*.sh

# ============================================
# 启动脚本
# ============================================
COPY docker/docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# ============================================
# 日志目录和权限
# ============================================
RUN mkdir -p /var/log/app /var/log/supervisor /app/logs && \
    chmod 777 /var/log/app /var/log/supervisor /app/logs

# ============================================
# 环境变量配置
# ============================================
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    ENVIRONMENT=production \
    LOG_LEVEL=info

# ============================================
# 健康检查配置
# ============================================
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health && \
        curl -f http://localhost:3000 || exit 1

# ============================================
# 暴露端口
# ============================================
EXPOSE 3000 8000

# ============================================
# 启动
# ============================================
ENTRYPOINT ["/entrypoint.sh"]
CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]
