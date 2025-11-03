# Traefik 503 错误修复指南

## 问题描述

Coolify 部署的 Reflex 应用遇到 Traefik 反向代理 503 错误：
- HTTP 工作（302 重定向到 HTTPS）
- HTTPS TLS 握手成功
- HTTPS 请求被卡住，返回 `503 no available server`

## 根本原因

**LoadBalancer 服务器列表为空** - Traefik 找到了路由配置，但无法找到或连接到健康的后端服务器。

可能的原因：
1. Docker 标签缺少 `loadbalancer.server.port` 配置
2. 端口配置与实际监听端口不一致
3. 容器启动命令不完整（只启动了后端，未启动前端）
4. 健康检查失败导致服务器被标记为不可用

## 解决方案

### 步骤 1: 验证容器端口监听

```bash
# 在 Coolify 服务器上执行
docker exec mg8c40oowo80o08o0gsw0gwc-185136275970 netstat -tulpn | grep -E ":(3000|8000)"
# 或
docker exec mg8c40oowo80o08o0gsw0gwc-185136275970 ss -tulpn | grep -E ":(3000|8000)"
```

**预期结果**：
```
tcp  0  0  0.0.0.0:3000  0.0.0.0:*  LISTEN  -
tcp  0  0  0.0.0.0:8000  0.0.0.0:*  LISTEN  -
```

**如果 3000 端口未监听**：说明前端未启动，继续步骤 2。

**如果 3000 和 8000 都在监听**：说明是 Traefik 标签配置问题，继续步骤 3。

### 步骤 2: 修复容器启动命令

Reflex 应用需要同时启动前端和后端。修改 Coolify 应用配置：

#### 方法 A: 使用 Reflex 官方命令（推荐）

在 Coolify 应用设置中，将启动命令改为：

```bash
reflex run --env prod --backend-host 0.0.0.0 --backend-port 8000 --frontend-host 0.0.0.0 --frontend-port 3000
```

#### 方法 B: 使用 uv（如果项目使用 uv）

```bash
uv run reflex run --env prod --backend-host 0.0.0.0 --backend-port 8000 --frontend-host 0.0.0.0 --frontend-port 3000
```

#### 方法 C: 分别启动前后端（不推荐，除非必要）

如果需要分开启动，使用 `supervisord` 或创建一个启动脚本：

```bash
#!/bin/bash
# start.sh

# 启动后端
python -m uvicorn working.webserver:app --host 0.0.0.0 --port 8000 &

# 启动前端
cd .web && npm run start &

# 等待所有进程
wait
```

**重要**：确保 Dockerfile 中 `EXPOSE 3000 8000` 声明了两个端口。

### 步骤 3: 验证和修复 Docker 标签

检查应用容器的标签配置是否完整：

```bash
docker inspect mg8c40oowo80o08o0gsw0gwc-185136275970 --format='{{range $key, $value := .Config.Labels}}{{$key}}={{$value}}{{"\n"}}{{end}}' | grep traefik
```

**必需的标签配置**：

```yaml
# 启用 Traefik
traefik.enable=true

# HTTP 路由（重定向到 HTTPS）
traefik.http.routers.http-0-mg8c40oowo80o08o0gsw0gwc.entryPoints=http
traefik.http.routers.http-0-mg8c40oowo80o08o0gsw0gwc.rule=Host(`www.jackcwf.com`)
traefik.http.routers.http-0-mg8c40oowo80o08o0gsw0gwc.middlewares=redirect-to-https

# HTTPS 主路由（前端）
traefik.http.routers.https-0-mg8c40oowo80o08o0gsw0gwc.entryPoints=https
traefik.http.routers.https-0-mg8c40oowo80o08o0gsw0gwc.rule=Host(`www.jackcwf.com`)
traefik.http.routers.https-0-mg8c40oowo80o08o0gsw0gwc.tls=true
traefik.http.routers.https-0-mg8c40oowo80o08o0gsw0gwc.tls.certresolver=letsencrypt
traefik.http.routers.https-0-mg8c40oowo80o08o0gsw0gwc.service=mg8c40oowo80o08o0gsw0gwc

# HTTPS WebSocket 路由（后端 API）
traefik.http.routers.https-websocket-mg8c40oowo80o08o0gsw0gwc.entryPoints=https
traefik.http.routers.https-websocket-mg8c40oowo80o08o0gsw0gwc.rule=Host(`www.jackcwf.com`) && PathPrefix(`/api`, `/_event`)
traefik.http.routers.https-websocket-mg8c40oowo80o08o0gsw0gwc.tls=true
traefik.http.routers.https-websocket-mg8c40oowo80o08o0gsw0gwc.tls.certresolver=letsencrypt
traefik.http.routers.https-websocket-mg8c40oowo80o08o0gsw0gwc.middlewares=gzip,websocket-upgrade
traefik.http.routers.https-websocket-mg8c40oowo80o08o0gsw0gwc.service=mg8c40oowo80o08o0gsw0gwc-backend

# 关键：LoadBalancer 服务配置（前端）
traefik.http.services.mg8c40oowo80o08o0gsw0gwc.loadbalancer.server.port=3000
traefik.http.services.mg8c40oowo80o08o0gsw0gwc.loadbalancer.server.scheme=http
traefik.http.services.mg8c40oowo80o08o0gsw0gwc.loadbalancer.healthcheck.path=/
traefik.http.services.mg8c40oowo80o08o0gsw0gwc.loadbalancer.healthcheck.interval=10s

# 关键：LoadBalancer 服务配置（后端）
traefik.http.services.mg8c40oowo80o08o0gsw0gwc-backend.loadbalancer.server.port=8000
traefik.http.services.mg8c40oowo80o08o0gsw0gwc-backend.loadbalancer.server.scheme=http
traefik.http.services.mg8c40oowo80o08o0gsw0gwc-backend.loadbalancer.healthcheck.path=/api/_health
traefik.http.services.mg8c40oowo80o08o0gsw0gwc-backend.loadbalancer.healthcheck.interval=10s

# 中间件
traefik.http.middlewares.redirect-to-https.redirectscheme.scheme=https
traefik.http.middlewares.redirect-to-https.redirectscheme.permanent=true
traefik.http.middlewares.gzip.compress=true
traefik.http.middlewares.websocket-upgrade.headers.customrequestheaders.Connection=Upgrade
traefik.http.middlewares.websocket-upgrade.headers.customrequestheaders.Upgrade=websocket
```

**关键缺失项检查**：

如果以下标签缺失，必须添加：

```bash
traefik.http.services.mg8c40oowo80o08o0gsw0gwc.loadbalancer.server.port=3000
traefik.http.services.mg8c40oowo80o08o0gsw0gwc-backend.loadbalancer.server.port=8000
```

### 步骤 4: 在 Coolify 中重新部署应用

**方法 A: 通过 Coolify UI**

1. 登录 Coolify 面板：https://coolpanel.jackcwf.com
2. 导航到应用：`mg8c40oowo80o08o0gsw0gwc`
3. 点击 **Settings** → **General**
4. 修改 **Start Command** 为：
   ```bash
   reflex run --env prod --backend-host 0.0.0.0 --backend-port 8000 --frontend-host 0.0.0.0 --frontend-port 3000
   ```
5. 滚动到 **Labels** 部分，确保所有必需标签都存在（参考步骤 3）
6. 点击 **Save**
7. 点击 **Deploy** → **Force Deploy**

**方法 B: 通过 Coolify CLI**

```bash
# 更新应用启动命令
coolify app update mg8c40oowo80o08o0gsw0gwc --start-command "reflex run --env prod --backend-host 0.0.0.0 --backend-port 8000 --frontend-host 0.0.0.0 --frontend-port 3000"

# 重新部署
coolify deploy mg8c40oowo80o08o0gsw0gwc --force
```

**方法 C: 手动重启容器（临时测试）**

```bash
# 停止容器
docker stop mg8c40oowo80o08o0gsw0gwc-185136275970

# 使用正确命令启动（仅用于测试）
docker run -d --name test-reflex \
  --network coolify \
  -l "traefik.enable=true" \
  -l "traefik.http.routers.test.rule=Host(\`www.jackcwf.com\`)" \
  -l "traefik.http.routers.test.entrypoints=https" \
  -l "traefik.http.routers.test.tls=true" \
  -l "traefik.http.services.test.loadbalancer.server.port=3000" \
  datalablife/jackcwf:main \
  reflex run --env prod --backend-host 0.0.0.0 --backend-port 8000 --frontend-host 0.0.0.0 --frontend-port 3000
```

### 步骤 5: 验证修复

#### 5.1 验证容器状态

```bash
# 检查容器是否运行
docker ps | grep mg8c40oowo80o08o0gsw0gwc

# 检查容器日志
docker logs mg8c40oowo80o08o0gsw0gwc-185136275970 --tail 50

# 验证端口监听
docker exec mg8c40oowo80o08o0gsw0gwc-185136275970 netstat -tulpn | grep -E ":(3000|8000)"
```

**预期输出**：
```
tcp  0  0  0.0.0.0:3000  0.0.0.0:*  LISTEN
tcp  0  0  0.0.0.0:8000  0.0.0.0:*  LISTEN
```

#### 5.2 验证 Traefik 服务发现

```bash
# 检查 Traefik 是否发现服务
docker logs traefik --tail 100 | grep mg8c40oowo80o08o0gsw0gwc

# 检查 Traefik API（如果启用）
curl http://localhost:8080/api/http/services | jq '.[] | select(.name | contains("mg8c40oowo80o08o0gsw0gwc"))'
```

**预期输出**：应该看到两个服务：
- `mg8c40oowo80o08o0gsw0gwc@docker` (前端，端口 3000)
- `mg8c40oowo80o08o0gsw0gwc-backend@docker` (后端，端口 8000)

#### 5.3 测试 HTTPS 访问

```bash
# 测试前端
curl -I https://www.jackcwf.com/

# 测试后端 API
curl -I https://www.jackcwf.com/api/_health

# 详细诊断
curl -v https://www.jackcwf.com/ 2>&1 | grep -E "(HTTP|< |> )"
```

**预期结果**：
```
HTTP/2 200
content-type: text/html; charset=utf-8
```

#### 5.4 测试 WebSocket 连接

```bash
# 使用 wscat（如果已安装）
wscat -c wss://www.jackcwf.com/_event

# 或使用 curl（HTTP/1.1 升级测试）
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" https://www.jackcwf.com/_event
```

### 步骤 6: 持久化配置（可选）

如果需要更细粒度的控制，可以创建 Traefik 动态配置文件：

```yaml
# /traefik/dynamic/reflex-app.yml
http:
  routers:
    reflex-frontend:
      rule: "Host(`www.jackcwf.com`)"
      entryPoints:
        - https
      tls:
        certResolver: letsencrypt
      service: reflex-frontend-service

    reflex-backend:
      rule: "Host(`www.jackcwf.com`) && PathPrefix(`/api`, `/_event`)"
      entryPoints:
        - https
      middlewares:
        - websocket-upgrade
        - gzip
      tls:
        certResolver: letsencrypt
      service: reflex-backend-service

  services:
    reflex-frontend-service:
      loadBalancer:
        servers:
          - url: "http://10.0.1.8:3000"
        healthCheck:
          path: /
          interval: 10s

    reflex-backend-service:
      loadBalancer:
        servers:
          - url: "http://10.0.1.8:8000"
        healthCheck:
          path: /api/_health
          interval: 10s

  middlewares:
    websocket-upgrade:
      headers:
        customRequestHeaders:
          Connection: "Upgrade"
          Upgrade: "websocket"

    gzip:
      compress: true
```

然后重启 Traefik：
```bash
docker restart traefik
```

## 预防措施

### 1. 监控和告警

在 Coolify 中配置健康检查：

```yaml
# Healthcheck 配置
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:3000/"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### 2. 日志监控

定期检查 Traefik 日志：

```bash
# 设置日志告警
docker logs traefik -f | grep -i "error\|503\|no available server"
```

### 3. 自动重启策略

确保容器重启策略正确：

```bash
docker update --restart=unless-stopped mg8c40oowo80o08o0gsw0gwc-185136275970
```

### 4. 文档化配置

将所有 Docker 标签和启动命令记录在项目文档中：

- 标签配置：`docs/deployment/traefik-labels.yml`
- 启动命令：`docs/deployment/start-command.sh`
- 健康检查：`docs/deployment/healthcheck.md`

### 5. 使用 Coolify 环境变量

将配置参数化：

```bash
# 在 Coolify 应用环境变量中
FRONTEND_PORT=3000
BACKEND_PORT=8000
FRONTEND_HOST=0.0.0.0
BACKEND_HOST=0.0.0.0
REFLEX_ENV=prod
```

启动命令使用变量：
```bash
reflex run --env ${REFLEX_ENV} --backend-host ${BACKEND_HOST} --backend-port ${BACKEND_PORT} --frontend-host ${FRONTEND_HOST} --frontend-port ${FRONTEND_PORT}
```

## 故障排查清单

如果问题仍未解决，按顺序检查：

- [ ] 容器是否运行且健康？`docker ps | grep mg8c40oowo80o08o0gsw0gwc`
- [ ] 前端端口 3000 是否监听？`docker exec <container> netstat -tulpn | grep 3000`
- [ ] 后端端口 8000 是否监听？`docker exec <container> netstat -tulpn | grep 8000`
- [ ] 容器内部访问正常？`docker exec <container> curl http://localhost:3000/`
- [ ] Docker 标签完整？`docker inspect <container> | grep traefik`
- [ ] Traefik 发现了服务？`docker logs traefik | grep mg8c40oowo80o08o0gsw0gwc`
- [ ] Traefik 日志有错误？`docker logs traefik --tail 100 | grep -i error`
- [ ] 网络连接正常？`docker exec traefik curl http://10.0.1.8:3000/`
- [ ] 证书有效？`curl -v https://www.jackcwf.com/ 2>&1 | grep "SSL certificate"`
- [ ] DNS 解析正确？`nslookup www.jackcwf.com`

## 相关文件

- **Coolify CLI 使用**: `/mnt/d/工作区/云开发/working/CLAUDE.md` - Coolify 管理规则
- **Reflex 部署指南**: `/mnt/d/工作区/云开发/working/docs/guides/developer/reflex-with-uv.md`
- **Docker 标签参考**: https://doc.traefik.io/traefik/providers/docker/
- **Traefik 健康检查**: https://doc.traefik.io/traefik/routing/services/#health-check

## 紧急回滚方案

如果修复失败导致服务完全不可用：

```bash
# 1. 回滚到上一个工作版本
coolify deploy mg8c40oowo80o08o0gsw0gwc --rollback

# 2. 或使用备份镜像
docker pull datalablife/jackcwf:backup
docker tag datalablife/jackcwf:backup datalablife/jackcwf:main
coolify deploy mg8c40oowo80o08o0gsw0gwc --force

# 3. 临时使用直接端口访问
# 在 Coolify 中启用端口映射 3000:3000
# 用户可临时访问 http://www.jackcwf.com:3000
```

---

**生成日期**: 2025-11-03
**适用版本**: Coolify 4.0.0-beta.434, Traefik v3.1
**作者**: Claude Code Assistant
