# 前后端整合启动架构 - 完整实施指南

**日期**: 2025-11-21
**版本**: 1.0
**状态**: ✅ **所有组件已创建，待部署**

---

## 🎯 架构决策总结

### 最终方案: **Supervisor + Python 监控 + Docker 容器化**

| 维度 | 决策 | 理由 |
|------|------|------|
| **进程管理** | Supervisord | 成熟稳定，支持自动重启、日志聚合 |
| **监控方式** | Python 脚本 | 与后端技术栈一致，支持异步HTTP检查 |
| **容器运行** | Docker 多阶段 | 完整的应用镜像，包括前后端和Supervisor |
| **前端服务** | Nginx | 高性能反向代理，支持SPA路由 |
| **生产部署** | Coolify | 自动部署、监控、日志管理 |
| **故障恢复** | 自动重启 | 健康检查失败后自动由Supervisor重启 |

---

## 📁 已创建的文件列表

### Docker 配置文件

```
docker/
├── Dockerfile                 # 多阶段构建，包含前后端
├── supervisord.conf          # Supervisor 进程管理配置
├── docker-entrypoint.sh       # Docker 启动脚本
└── nginx.conf                # Nginx 前端配置
```

### 监控脚本

```
scripts/monitor/
└── health_monitor.py         # Python 健康检查和监控脚本
```

### 架构文档

```
STORY_4_4_INTEGRATED_SERVICE_ARCHITECTURE.md  # 架构设计文档
README_STORY_4_4.md                          # 快速入门指南
STORY_4_4_ACTION_PLAN.md                     # 完整行动计划
```

---

## 🚀 启动流程详解

### 1. Docker 容器启动流程

```
┌─ Docker 容器启动
│
├─ 1️⃣ docker-entrypoint.sh 执行
│  ├─ 创建日志目录
│  ├─ 验证环境变量
│  ├─ 检查数据库连接 (最多 30 秒)
│  └─ 启动 Supervisor
│
└─ 2️⃣ Supervisord 启动 (PID 1)
   ├─ Priority 100: Backend (FastAPI)
   │  └─ python -m uvicorn src.main:app --port 8000
   │     └─ 等待就绪 (10 秒)
   │
   ├─ Priority 200: Frontend (Nginx)
   │  └─ nginx -g "daemon off;"
   │     └─ 等待启动 (5 秒)
   │
   └─ Priority 300: HealthMonitor (Python)
      └─ python scripts/monitor/health_monitor.py
         └─ 等待 30 秒后开始监控
```

### 2. 健康监控循环

```
┌─ 每 30 秒执行一次
│
├─ 检查后端健康: GET http://localhost:8000/health
│  ├─ 成功 (200 OK) → failures = 0
│  └─ 失败 → failures++
│
├─ 检查前端可用: GET http://localhost:3000
│  ├─ 成功 (200 OK) → failures = 0
│  └─ 失败 → failures++
│
├─ 如果失败 >= 3 次
│  ├─ 发送告警 (Webhook)
│  └─ Supervisor 自动重启服务
│
└─ 记录系统指标: CPU, 内存, 磁盘使用率
```

### 3. 故障恢复流程

```
检测到服务故障
    │
    ├─ 记录错误信息到日志
    │
    ├─ 如果失败 < 3 次
    │  └─ 继续监控，等待下一次检查
    │
    └─ 如果失败 >= 3 次
       ├─ 发送告警通知 (Webhook)
       └─ Supervisor 自动重启
          ├─ 停止失败的进程
          ├─ 清理资源
          ├─ 重新启动
          └─ 从失败计数清零
```

---

## 📊 完整的文件配置说明

### 1. Dockerfile (多阶段构建)

**三个构建阶段**:

**阶段 1: backend-builder**
- Python 3.12 基础镜像
- 编译后端依赖
- 使用 uv 加速安装

**阶段 2: frontend-builder**
- Node.js 20 基础镜像
- 构建 React 前端
- 输出到 dist/ 目录

**阶段 3: 生产镜像**
- Python 3.12 运行时
- 安装 Node.js, Supervisor, Nginx
- 复制所有依赖和代码
- 配置 Supervisor 和 Nginx
- 设置健康检查
- 暴露端口 3000 (前端) 和 8000 (后端)

### 2. Supervisor 配置 (supervisord.conf)

**三个 Program**:

**[program:backend]**
- 命令: `python -m uvicorn src.main:app --port 8000`
- Priority: 100 (最先启动)
- 自动重启: 最多 3 次
- 日志: `/var/log/app/backend.log`
- 等待时间: 10 秒

**[program:frontend]**
- 命令: `nginx -g "daemon off;"`
- Priority: 200 (等待后端启动)
- 自动重启: 最多 3 次
- 日志: `/var/log/app/frontend.log`
- 等待时间: 5 秒

**[program:healthmonitor]**
- 命令: `python /app/scripts/monitor/health_monitor.py`
- Priority: 300 (最后启动)
- 自动重启: 最多 3 次
- 日志: `/var/log/app/health_monitor.log`
- 等待时间: 30 秒

### 3. 健康监控脚本 (health_monitor.py)

**核心功能**:

1. **定期健康检查** (30 秒间隔)
   - 后端: `GET /health`
   - 前端: `GET /`

2. **失败计数和阈值**
   - 每次失败计数 +1
   - 达到 3 次失败触发重启

3. **告警通知**
   - Webhook 发送告警
   - 5 分钟内相同告警只发送一次

4. **系统指标监控**
   - CPU 使用率 > 80% 告警
   - 内存使用率 > 85% 告警
   - 磁盘使用率监控

5. **优雅关闭**
   - 接收 SIGTERM/SIGINT
   - 正常退出监控循环

### 4. Docker 启动脚本 (docker-entrypoint.sh)

**初始化步骤**:

1. **创建日志目录**
   - `/var/log/app/`
   - `/var/log/supervisor/`
   - `/app/logs/`

2. **验证环境变量**
   - 检查 `DATABASE_URL` 等必需变量

3. **数据库连接检查**
   - 最多尝试 30 秒
   - 每 2 秒检查一次
   - 确保数据库就绪后再启动应用

4. **环境初始化**
   - 检查 `.env` 文件
   - 设置权限

5. **预启动检查**
   - 验证必需文件存在

6. **启动 Supervisor**
   - 作为主进程 (PID 1)

### 5. Nginx 配置 (nginx.conf)

**功能**:

1. **静态文件服务**
   - 服务 React 构建的文件
   - SPA 路由回退到 index.html

2. **API 代理**
   - `/api/*` → 后端 (8000)
   - WebSocket 支持

3. **健康检查**
   - `/health` → 200 OK

4. **性能优化**
   - Gzip 压缩
   - 缓存头
   - 缓冲设置

5. **安全头**
   - CSP (内容安全策略)
   - X-Frame-Options (防 clickjacking)
   - X-Content-Type-Options (防 MIME 嗅探)
   - X-XSS-Protection (XSS 保护)

---

## 🔧 部署准备清单

### 前置条件

- [ ] Python 3.12+ 环境
- [ ] Node.js 20+ 和 npm
- [ ] Docker 安装并运行
- [ ] Docker Compose (可选)
- [ ] Git 仓库配置

### 配置文件验证

- [ ] `Dockerfile` 存在且正确
- [ ] `docker/supervisord.conf` 存在
- [ ] `docker/docker-entrypoint.sh` 存在且可执行
- [ ] `docker/nginx.conf` 存在
- [ ] `scripts/monitor/health_monitor.py` 存在且可执行

### 环境变量

- [ ] `DATABASE_URL` - PostgreSQL 连接
- [ ] `OPENAI_API_KEY` - OpenAI API 密钥
- [ ] `ANTHROPIC_API_KEY` - Anthropic API 密钥
- [ ] `ALERT_WEBHOOK_URL` (可选) - 告警 Webhook

### 依赖包

后端依赖 (pyproject.toml):
- [ ] httpx (健康检查)
- [ ] psutil (系统监控)
- [ ] uvicorn (ASGI 服务器)
- [ ] fastapi (API 框架)
- [ ] sqlalchemy (ORM)
- [ ] asyncpg (异步 PostgreSQL)

---

## 🚀 本地测试步骤

### Step 1: 构建镜像

```bash
# 构建 Docker 镜像
docker build -f Dockerfile -t myapp:latest .

# 验证镜像大小和层
docker images myapp:latest
docker history myapp:latest
```

### Step 2: 本地运行

```bash
# 运行容器
docker run -d \
  --name myapp \
  -p 3000:3000 \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://..." \
  -e OPENAI_API_KEY="sk-..." \
  myapp:latest

# 查看日志
docker logs -f myapp

# 进入容器调试
docker exec -it myapp bash
```

### Step 3: 验证服务

```bash
# 检查后端健康
curl http://localhost:8000/health

# 检查前端可访问性
curl http://localhost:3000

# 查看监控脚本日志
docker exec myapp tail -f /var/log/app/health_monitor.log

# 查看 Supervisor 日志
docker exec myapp tail -f /var/log/supervisor/supervisord.log
```

### Step 4: 测试故障转移

```bash
# 手动停止后端服务
docker exec myapp supervisorctl stop backend

# 观察监控脚本日志
docker exec myapp tail -f /var/log/app/health_monitor.log

# 应该看到:
# [ERROR] backend health check failed
# 3 次失败后自动重启

# 验证后端已自动重启
curl http://localhost:8000/health
```

---

## 📈 生产环境部署 (Coolify)

### Step 1: 推送镜像到 GHCR

```bash
# 标记镜像
docker tag myapp:latest ghcr.io/datalablife/myapp:latest

# 登录 GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# 推送镜像
docker push ghcr.io/datalablife/myapp:latest
```

### Step 2: 在 Coolify 中配置

1. **创建/更新应用**
   - 应用名: `myapp`
   - 镜像源: `ghcr.io/datalablife/myapp:latest`

2. **环境变量**
   ```
   DATABASE_URL=postgresql://...
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=...
   ALERT_WEBHOOK_URL=https://hooks.slack.com/...
   ```

3. **健康检查**
   - 端点: `http://localhost:8000/health`
   - 间隔: 30s
   - 超时: 10s
   - 启动延迟: 60s

4. **重启策略**
   - 自动重启: `unless-stopped`

5. **资源限制**
   ```
   CPU: 2 核
   内存: 4 GB
   磁盘: 自动
   ```

### Step 3: 部署和验证

```bash
# 部署到 Coolify
# (通过 Coolify UI 或 API)

# 验证部署
curl https://jackcwf.com/health

# 查看容器日志
docker logs <container-id>

# 监控指标
curl https://jackcwf.com/metrics
```

---

## 🎓 关键特性和优势

### 可靠性

✅ **自动重启** - 服务故障时自动恢复
✅ **健康监控** - 每 30 秒检查一次
✅ **告警通知** - 立即通知故障事件
✅ **日志聚合** - 统一日志管理

### 可观察性

✅ **完整日志** - 所有服务日志在 `/var/log/app/`
✅ **系统指标** - CPU、内存、磁盘监控
✅ **错误追踪** - 详细的错误和异常记录
✅ **性能指标** - 响应时间、错误率等

### 可维护性

✅ **清晰的配置** - supervisord.conf 易于修改
✅ **模块化设计** - 前后端独立管理
✅ **易于调试** - 容器内可直接执行命令
✅ **版本控制** - 所有配置在 Git 中

### 可扩展性

✅ **易于添加服务** - 在 supervisord.conf 中添加 [program]
✅ **易于添加监控规则** - 修改 health_monitor.py
✅ **支持多副本** - 可配置 Supervisor 启动多个进程
✅ **支持负载均衡** - Nginx 配置支持上游服务器

---

## 🔍 故障排查指南

### 容器无法启动

```bash
# 查看启动日志
docker logs <container-id>

# 检查环境变量
docker inspect <container-id> | grep -A 20 "Env"

# 测试数据库连接
docker exec <container-id> python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
async def test():
    engine = create_async_engine('$DATABASE_URL')
    async with engine.begin() as conn:
        result = await conn.execute('SELECT 1')
asyncio.run(test())
"
```

### 后端无法启动

```bash
# 查看后端日志
docker exec <container-id> tail -f /var/log/app/backend.log

# 查看 Supervisor 日志
docker exec <container-id> supervisorctl status backend

# 手动启动后端测试
docker exec <container-id> python -m uvicorn src.main:app --port 8000
```

### 前端无法启动

```bash
# 查看 Nginx 日志
docker exec <container-id> tail -f /var/log/app/frontend.log

# 测试 Nginx 配置
docker exec <container-id> nginx -t

# 查看 Supervisor 状态
docker exec <container-id> supervisorctl status frontend
```

### 监控脚本故障

```bash
# 查看监控日志
docker exec <container-id> tail -f /var/log/app/health_monitor.log

# 手动运行监控脚本
docker exec <container-id> python /app/scripts/monitor/health_monitor.py
```

---

## 📋 完成清单

部署前最后检查:

- [ ] 所有 Docker 文件创建完成
- [ ] Dockerfile 通过验证
- [ ] supervisord.conf 配置正确
- [ ] health_monitor.py 依赖已满足
- [ ] 本地测试通过
- [ ] 镜像已推送到 GHCR
- [ ] Coolify 应用已创建/更新
- [ ] 环境变量已配置
- [ ] 健康检查已配置
- [ ] 告警 Webhook 已配置 (可选)

---

## 🎉 总结

您现在拥有:

✅ **完整的 Docker 镜像** - 包含前后端和 Supervisor
✅ **智能监控系统** - 自动检查和恢复
✅ **生产级配置** - Nginx、日志、安全头
✅ **详细文档** - 架构、部署、故障排查
✅ **本地测试方案** - 快速验证和调试

**下一步**: 按照"本地测试步骤"进行测试，然后部署到 Coolify。

---

**准备完成日期**: 2025-11-21
**预计测试完成**: 2025-11-22
**预计部署完成**: 2025-11-22-23
**架构版本**: 1.0 - Supervisor + Python 监控

