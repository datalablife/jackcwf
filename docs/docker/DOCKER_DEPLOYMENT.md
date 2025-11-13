# Docker + Coolify 部署架构文档

## 目录

- [架构概览](#架构概览)
- [设计决策](#设计决策)
- [文件结构](#文件结构)
- [容器化策略](#容器化策略)
- [启动流程](#启动流程)
- [开发工作流](#开发工作流)
- [生产部署](#生产部署)
- [监控和日志](#监控和日志)
- [故障排除](#故障排除)
- [最佳实践](#最佳实践)

---

## 架构概览

### 部署架构图

```
┌─────────────────────────────────────────────────────────┐
│                    Coolify 平台                          │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │           Traefik 反向代理                     │    │
│  │  - HTTPS/SSL (Let's Encrypt)                   │    │
│  │  - 路径路由 (/ 和 /_event)                     │    │
│  │  - WebSocket 支持                              │    │
│  │  - 压缩和缓存                                   │    │
│  └──────────┬───────────────────┬──────────────────┘    │
│             │                   │                        │
│     / (前端 3000)        /_event (后端 8000)            │
│             │                   │                        │
│  ┌──────────┴───────────────────┴──────────────────┐   │
│  │                                                  │   │
│  │         Docker 容器 (单容器架构)                 │   │
│  │                                                  │   │
│  │  ┌──────────────┐      ┌───────────────────┐  │   │
│  │  │              │      │                   │  │   │
│  │  │   Next.js    │◄────►│   FastAPI        │  │   │
│  │  │   前端服务    │      │   后端 API       │  │   │
│  │  │   :3000      │      │   :8000          │  │   │
│  │  │              │      │                   │  │   │
│  │  └──────────────┘      └────────┬──────────┘  │   │
│  │                                  │              │   │
│  │         Reflex Framework         │              │   │
│  │         (统一启动和管理)          │              │   │
│  │                                  │              │   │
│  │  ┌───────────────────────────────┴────────┐   │   │
│  │  │        entrypoint.sh                   │   │   │
│  │  │  - 环境验证                             │   │   │
│  │  │  - 数据库连接检查                        │   │   │
│  │  │  - 健康检查                             │   │   │
│  │  │  - 优雅关闭                             │   │   │
│  │  └────────────────────────────────────────┘   │   │
│  │                                                │   │
│  └────────────────────┬───────────────────────────┘   │
│                       │                               │
└───────────────────────┼───────────────────────────────┘
                        │
                        │ PostgreSQL 连接
                        │
            ┌───────────┴──────────────┐
            │                          │
            │  PostgreSQL (云托管)      │
            │  pgvctor.jackcwf.com     │
            │                          │
            └──────────────────────────┘
```

### 关键组件

1. **Coolify 平台**
   - 容器编排和管理
   - 自动化 CI/CD
   - 监控和日志聚合
   - 自动重启和故障恢复

2. **Traefik 反向代理**
   - 自动 HTTPS (Let's Encrypt)
   - 路径路由规则
   - WebSocket 支持
   - 压缩和优化

3. **Docker 容器**
   - 单容器运行前后端
   - Reflex 框架统一管理
   - 优雅启动和关闭
   - 健康检查集成

4. **PostgreSQL 数据库**
   - 云托管 (独立于容器)
   - 持久化数据存储
   - 连接池管理

---

## 设计决策

### 为什么选择单容器架构？

**决策：前后端在同一容器内运行**

✅ **优势：**
- Reflex 框架本身设计为单进程启动
- 前后端通过内部 WebSocket 紧密耦合
- 简化部署和网络配置
- 减少容器编排复杂性
- 内部通信无网络延迟
- 状态同步更可靠
- 资源利用更高效

❌ **劣势：**
- 无法独立扩展前后端
- 故障隔离性较差
- 升级需要整体重启

**结论：** 对于 Reflex 应用，单容器是最佳选择，因为框架本身就是为此设计的。

### 多阶段构建 vs 单阶段构建

**决策：采用多阶段构建**

```dockerfile
# 阶段 1: base - 系统依赖
FROM python:3.12-slim AS base

# 阶段 2: dependencies - Python 包安装
FROM base AS dependencies

# 阶段 3: application - 最终镜像
FROM base AS application
```

**优势：**
- 减小最终镜像大小
- 分离构建依赖和运行依赖
- 更好的缓存利用
- 提高构建速度

### Entrypoint vs CMD

**决策：使用 ENTRYPOINT + 自定义脚本**

```dockerfile
ENTRYPOINT ["/app/entrypoint.sh"]
```

**原因：**
- 需要在容器启动时执行初始化任务
- 环境验证
- 数据库连接检查
- 优雅的信号处理 (SIGTERM)
- 更灵活的启动逻辑

### 日志策略

**决策：所有日志输出到 stdout/stderr**

```python
ENV PYTHONUNBUFFERED=1
```

**原因：**
- Docker 的标准日志实践
- Coolify 自动收集容器日志
- 无需管理日志文件
- 便于日志聚合和分析

---

## 文件结构

```
/mnt/d/工作区/云开发/working/
├── Dockerfile                    # 生产环境 Dockerfile
├── docker-compose.yml            # Coolify 使用的配置
├── docker-compose.dev.yml        # 本地开发测试配置
├── entrypoint.sh                 # 容器启动脚本
├── .dockerignore                 # Docker 构建忽略文件
├── rxconfig.py                   # Reflex 配置
├── pyproject.toml                # Python 依赖
├── uv.lock                       # 依赖锁定文件
│
├── scripts/
│   ├── dev.sh                    # 本地开发启动脚本
│   ├── test-docker.sh            # 本地测试 Docker 容器
│   └── build.sh                  # 构建 Docker 镜像
│
├── working/
│   ├── working.py                # 主应用
│   └── health.py                 # 健康检查端点
│
└── .web/                         # Reflex 编译的前端 (运行时生成)
```

---

## 容器化策略

### Dockerfile 详解

#### 1. 构建参数

```dockerfile
ARG PYTHON_VERSION=3.12
ARG NODE_VERSION=20
```

- 可在构建时覆盖
- 便于版本管理

#### 2. 基础镜像 (base)

```dockerfile
FROM python:${PYTHON_VERSION}-slim AS base

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \    # C/C++ 编译器
    libpq-dev \          # PostgreSQL 客户端库
    curl \               # 健康检查
    git \                # 某些包需要
    && rm -rf /var/lib/apt/lists/*

# 安装 Node.js (Reflex 前端需要)
RUN curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash - && \
    apt-get install -y nodejs
```

#### 3. 依赖安装 (dependencies)

```dockerfile
FROM base AS dependencies

# 安装 uv 包管理器
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# 安装 Python 依赖
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --locked
```

**关键点：**
- `--no-dev`: 不安装开发依赖
- `--locked`: 使用锁定的版本
- 创建 `.venv` 虚拟环境

#### 4. 应用镜像 (application)

```dockerfile
FROM base AS application

# 复制虚拟环境
COPY --from=dependencies /app/.venv /app/.venv

# 设置环境变量
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PYTHONPATH=/app:$PYTHONPATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 复制应用代码
COPY . .

# 预编译前端
RUN python -m reflex init --loglevel warning && \
    python -m reflex export --frontend-only --loglevel info
```

**预编译的重要性：**
- 大幅减少容器启动时间 (从 2 分钟到 10 秒)
- 前端资源在构建时生成
- 生产环境只需启动服务

---

## 启动流程

### entrypoint.sh 详解

```bash
#!/bin/bash
set -e  # 遇到错误立即退出

# 信号处理器 (优雅关闭)
trap shutdown_handler SIGTERM SIGINT

# 1. 环境变量验证
# 2. 数据库连接检查
# 3. 数据库迁移 (可选)
# 4. 预检查
# 5. 启动应用
# 6. 等待进程并处理信号
```

#### 1. 环境变量验证

```bash
REQUIRED_VARS=(
    "REFLEX_ENV"
    "FRONTEND_PORT"
    "BACKEND_PORT"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        log_error "Required environment variable $var is not set"
        exit 1
    fi
done
```

#### 2. 数据库连接检查

```bash
if [ -n "$DATABASE_URL" ]; then
    # 最多重试 30 次 (30 秒)
    python -c "
from sqlalchemy import create_engine
engine = create_engine('$DATABASE_URL')
with engine.connect() as conn:
    conn.execute('SELECT 1')
"
fi
```

#### 3. 启动应用

```bash
python -m reflex run \
    --env production \
    --loglevel info \
    --backend-host 0.0.0.0 \
    --backend-port "${BACKEND_PORT}" \
    --frontend-host 0.0.0.0 \
    --frontend-port "${FRONTEND_PORT}" &

# 保存 PID 用于优雅关闭
REFLEX_PID=$!
echo $REFLEX_PID > /tmp/reflex.pid

# 等待进程
wait $REFLEX_PID
```

#### 4. 优雅关闭

```bash
shutdown_handler() {
    log_info "Received shutdown signal..."

    # 发送 SIGTERM 到 Reflex 进程
    kill -TERM "$PID"

    # 等待最多 30 秒
    for i in {1..30}; do
        if ! kill -0 "$PID" 2>/dev/null; then
            break
        fi
        sleep 1
    done

    # 强制结束 (如果需要)
    kill -KILL "$PID" 2>/dev/null || true
}
```

---

## 开发工作流

### 本地开发 (推荐)

```bash
# 使用开发脚本
chmod +x scripts/dev.sh
./scripts/dev.sh

# 或直接使用 uv
uv run reflex run
```

**特点：**
- 热重载
- 详细日志
- 即时反馈
- 无需构建镜像

### 本地测试容器

```bash
# 构建和测试生产容器
chmod +x scripts/test-docker.sh
./scripts/test-docker.sh

# 或使用 docker-compose
docker-compose -f docker-compose.dev.yml up --build
```

**用途：**
- 验证容器配置
- 测试生产环境行为
- 调试容器问题

### 工作流程

```
开发 → 本地测试 → 容器测试 → 推送到 Git → Coolify 自动部署
  ↓        ↓          ↓            ↓              ↓
dev.sh   reflex   test-docker   git push    Auto-rebuild
         run      .sh
```

---

## 生产部署

### Coolify 自动部署流程

1. **代码推送**
   ```bash
   git add .
   git commit -m "Your changes"
   git push origin main
   ```

2. **Coolify 自动检测**
   - 监听 Git 仓库变更
   - 触发构建流程

3. **Docker 镜像构建**
   - 使用 Dockerfile 构建镜像
   - 应用 docker-compose.yml 配置
   - 添加 Traefik 标签

4. **容器部署**
   - 启动新容器
   - 健康检查 (120 秒启动期)
   - 切换流量
   - 停止旧容器

5. **验证部署**
   - 访问应用 URL
   - 检查健康状态: `https://www.jackcwf.com/health`
   - 查看日志

### 环境变量配置 (Coolify)

在 Coolify 面板中配置：

```bash
# 应用配置
APP_NAME=working
ENVIRONMENT=production
DEBUG=false
REFLEX_ENV=production

# 端口配置
FRONTEND_PORT=3000
BACKEND_PORT=8000

# 数据库
DATABASE_URL=postgresql://user:pass@pgvctor.jackcwf.com:5432/working

# Coolify 配置
COOLIFY_URL=https://coolpanel.jackcwf.com
COOLIFY_FQDN=jackcwf.coolify.io
```

### docker-compose.yml 详解

```yaml
services:
  app:
    # Coolify 生成的镜像名
    image: mg8c40oowo80o08o0gsw0gwc:3692de12e493ff0bb343810c872bac002c86f956

    # 网络配置
    networks:
      - coolify

    # 重启策略
    restart: unless-stopped

    # 健康检查
    healthcheck:
      test: ['CMD', 'curl', '-f', 'http://localhost:3000/']
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 120s  # 重要：给 Reflex 足够的启动时间

    # 暴露端口 (内部)
    expose:
      - 3000
      - 8000

    # Traefik 标签
    labels:
      # 前端路由 (/ -> 3000)
      - traefik.http.routers.https-0.rule=Host(`www.jackcwf.com`) && PathPrefix(`/`)
      - traefik.http.services.https-0.loadbalancer.server.port=3000

      # 后端 WebSocket 路由 (/_event -> 8000)
      - traefik.http.routers.https-websocket.rule=Host(`www.jackcwf.com`) && PathPrefix(`/_event`)
      - traefik.http.services.https-websocket.loadbalancer.server.port=8000
      - traefik.http.routers.https-websocket.priority=20  # 高优先级
```

---

## 监控和日志

### 健康检查端点

访问 `/health` 查看应用状态：

```json
{
  "status": "healthy",
  "timestamp": "2025-11-12T10:30:00",
  "service": "working",
  "environment": "production",
  "database": "connected",
  "git_commit": "3692de12"
}
```

**健康检查逻辑：**
```python
# working/health.py
def get_health_status():
    - 检查数据库连接
    - 返回应用状态
    - 包含版本信息
```

### Docker 健康检查

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=5 \
    CMD curl -f http://localhost:3000/ || exit 1
```

**参数说明：**
- `interval`: 每 30 秒检查一次
- `timeout`: 10 秒超时
- `start-period`: 120 秒启动期 (考虑 Reflex 编译时间)
- `retries`: 5 次失败后标记为不健康

### 日志管理

#### 查看容器日志

```bash
# 在 Coolify 面板
应用 → Logs → 实时查看

# 或使用 Docker 命令 (如果有 SSH 访问权限)
docker logs -f <container_name>
```

#### 日志级别

```bash
# 开发环境
--loglevel debug

# 生产环境
--loglevel info
```

#### 日志格式

```python
# entrypoint.sh 中的日志
[INFO] Starting Reflex application...
[WARN] Database connection attempt 1/30 failed, retrying...
[ERROR] Database connection failed after 30 attempts
```

---

## 故障排除

### 常见问题和解决方案

#### 1. 容器启动失败

**症状：** 容器不断重启

**排查步骤：**
```bash
# 1. 查看容器日志
docker logs <container_name>

# 2. 检查健康检查状态
docker inspect <container_name> | grep -A 10 Health

# 3. 进入容器调试
docker exec -it <container_name> /bin/bash
```

**常见原因：**
- 数据库连接失败 → 检查 `DATABASE_URL`
- 环境变量缺失 → 检查 Coolify 配置
- 端口冲突 → 检查端口映射
- 内存不足 → 增加容器资源限制

#### 2. 健康检查失败

**症状：** `Health: unhealthy`

**排查步骤：**
```bash
# 1. 测试健康端点
curl http://localhost:3000/

# 2. 检查进程是否运行
ps aux | grep reflex

# 3. 检查端口监听
netstat -tuln | grep 3000
```

**解决方案：**
- 增加 `start_period` (给更多启动时间)
- 检查应用是否真正启动
- 验证健康检查 URL

#### 3. WebSocket 连接失败

**症状：** 前端无法连接后端

**排查步骤：**
```bash
# 1. 检查 Traefik 路由配置
# 确保 /_event 路由到 8000 端口

# 2. 检查后端是否监听 WebSocket
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  http://localhost:8000/_event
```

**解决方案：**
- 检查 `docker-compose.yml` 中的 Traefik 标签
- 确保 WebSocket 路由优先级更高 (`priority: 20`)
- 验证 `rxconfig.py` 中的 `api_url` 配置

#### 4. 数据库连接问题

**症状：** 应用无法连接数据库

**排查步骤：**
```bash
# 1. 测试数据库连接
docker exec -it <container_name> python -c "
from sqlalchemy import create_engine
import os
engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as conn:
    print('Connected successfully')
"

# 2. 检查 DNS 解析
docker exec -it <container_name> nslookup pgvctor.jackcwf.com

# 3. 检查网络连接
docker exec -it <container_name> telnet pgvctor.jackcwf.com 5432
```

**解决方案：**
- 验证 `DATABASE_URL` 格式
- 检查数据库服务器防火墙
- 确认数据库用户权限

#### 5. 镜像构建失败

**症状：** Docker build 失败

**常见错误：**

```bash
# 错误 1: uv sync 失败
解决：检查 pyproject.toml 和 uv.lock 是否存在

# 错误 2: Node.js 安装失败
解决：检查网络连接和 apt 源

# 错误 3: reflex export 失败
解决：确保所有 Python 依赖已安装
```

#### 6. 应用性能问题

**症状：** 响应缓慢

**优化建议：**

```yaml
# 1. 增加容器资源
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G

# 2. 调整 worker 数量 (如果使用多进程)
# 3. 启用数据库连接池
# 4. 添加缓存层 (Redis)
```

---

## 最佳实践

### 1. 安全性

```bash
# 不要在镜像中硬编码敏感信息
❌ ENV DATABASE_URL=postgresql://user:pass@host/db

# 使用环境变量
✅ ENV DATABASE_URL=${DATABASE_URL}

# 在 Coolify 中配置环境变量
```

### 2. 镜像优化

```dockerfile
# 使用 .dockerignore 排除不必要的文件
.git
.github
tests/
*.md
.env
```

```bash
# 查看镜像大小
docker images working

# 优化建议
- 使用 slim 基础镜像
- 多阶段构建
- 清理 apt 缓存
- 合并 RUN 命令
```

### 3. 配置管理

```bash
# 使用不同的配置文件
.env.development
.env.production
.env.test

# 在 rxconfig.py 中根据环境加载
reflex_env = os.getenv("REFLEX_ENV", "dev")
is_production = reflex_env in ("prod", "production")
```

### 4. 数据库迁移

```bash
# 在 entrypoint.sh 中运行迁移 (可选)
# 注释掉这段代码，等需要时启用
# log_info "Running database migrations..."
# alembic upgrade head
```

**推荐方式：**
- 开发环境：手动运行迁移
- 生产环境：
  - 方案 1: 在 entrypoint.sh 中自动运行
  - 方案 2: 部署前手动运行
  - 方案 3: 使用单独的 migration job

### 5. 监控和告警

```bash
# 设置健康检查告警
- Coolify 内置监控
- 外部 uptime 监控 (UptimeRobot, Pingdom)
- 自定义告警 (webhook)
```

### 6. 备份和恢复

```bash
# 数据库备份 (PostgreSQL)
pg_dump -h pgvctor.jackcwf.com -U user -d working > backup.sql

# 恢复
psql -h pgvctor.jackcwf.com -U user -d working < backup.sql
```

### 7. 版本管理

```bash
# 使用 Git 标签管理版本
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# 在 Dockerfile 中记录构建信息
ARG BUILD_DATE
ARG VERSION
ARG GIT_COMMIT
```

### 8. 测试策略

```bash
# 本地测试
./scripts/dev.sh

# 容器测试
./scripts/test-docker.sh

# 生产环境测试
# 使用 staging 环境 (如果有)
```

---

## 快速参考

### 常用命令

```bash
# 本地开发
./scripts/dev.sh

# 测试容器
./scripts/test-docker.sh

# 构建镜像
./scripts/build.sh

# 查看日志
docker logs -f <container_name>

# 进入容器
docker exec -it <container_name> /bin/bash

# 重启容器 (Coolify)
Coolify 面板 → Restart

# 查看健康状态
curl https://www.jackcwf.com/health
```

### 关键文件

| 文件 | 用途 | 环境 |
|------|------|------|
| `Dockerfile` | 生产镜像构建 | 生产 |
| `docker-compose.yml` | Coolify 配置 | 生产 |
| `docker-compose.dev.yml` | 本地测试 | 开发 |
| `entrypoint.sh` | 容器启动脚本 | 生产 |
| `scripts/dev.sh` | 本地开发 | 开发 |
| `scripts/test-docker.sh` | 容器测试 | 开发 |
| `working/health.py` | 健康检查 | 生产/开发 |

### 环境变量

| 变量 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `REFLEX_ENV` | 是 | dev | 运行环境 |
| `FRONTEND_PORT` | 是 | 3000 | 前端端口 |
| `BACKEND_PORT` | 是 | 8000 | 后端端口 |
| `DATABASE_URL` | 否 | - | 数据库连接 |
| `DEBUG` | 否 | false | 调试模式 |

---

## 总结

这个 Docker + Coolify 架构提供了：

✅ **简单部署** - 单容器，一键部署
✅ **自动化 CI/CD** - Git 推送自动部署
✅ **健康监控** - 内置健康检查和监控
✅ **优雅重启** - 零停机部署
✅ **灵活扩展** - 可根据需求调整资源
✅ **开发友好** - 本地和容器开发并行
✅ **生产就绪** - 完整的错误处理和日志

**下一步行动：**
1. 本地测试：`./scripts/test-docker.sh`
2. 推送代码：`git push origin main`
3. 监控部署：Coolify 面板
4. 验证应用：访问 `https://www.jackcwf.com/health`

---

**文档版本:** 1.0.0
**最后更新:** 2025-11-12
**维护者:** 开发团队
