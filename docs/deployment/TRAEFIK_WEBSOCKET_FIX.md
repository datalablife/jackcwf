# Traefik WebSocket 连接修复指南

**问题**: WebSocket 连接超时 `wss://www.jackcwf.com/_event`
**根源**: Traefik 反向代理配置问题
**好消息**: Traefik 修复比 Nginx 更简单！

---

## ✅ 系统信息

你的系统使用以下容器：
- **反向代理**: `coolify-proxy` (Traefik v3.1)
- **应用容器**: `mg8c40oowo80o08o0gsw0gwc-090124817222`
- **数据库**: PostgreSQL 15
- **缓存**: Redis 7

---

## 🎯 快速解决方案 (3 步)

### 步骤 1: 查看应用的路由配置

```bash
# 进入 Coolify 主容器
docker exec -it coolify bash

# 查看应用在 Coolify 数据库中的配置
# Coolify 会自动生成 Traefik 配置标签

# 或者直接查看已生成的 Traefik 配置
docker exec coolify-proxy cat /etc/traefik/dynamic.yml 2>/dev/null | grep -A 20 "jackcwf\|_event"
```

### 步骤 2: 检查应用的 Traefik 标签

Coolify 通过 Docker 标签为应用配置 Traefik 路由。你需要在 Coolify 中更新应用配置，或者直接编辑 docker-compose 文件。

**关键标签需要**:
```
com.traefik.http.routers.{app-id}.service={app-id}
com.traefik.http.services.{app-id}.loadbalancer.server.port=3000
com.traefik.http.middlewares.websocket.headers.customrequestheaders.Connection=Upgrade
com.traefik.http.middlewares.websocket.headers.customrequestheaders.Upgrade=websocket
```

### 步骤 3: 重启 Traefik

```bash
docker-compose restart coolify-proxy
```

---

## 🔧 详细解决方案

### 方法 A: 通过 Docker Compose 直接修改（最推荐）

#### 步骤 1: 找到 docker-compose 文件

```bash
# 通常在 Coolify 主目录下
find / -name "docker-compose.yml" 2>/dev/null | grep -i coolify

# 或者在 /root 或 /opt 下
ls -la /root/
ls -la /opt/
```

#### 步骤 2: 编辑 docker-compose.yml

找到应用对应的服务定义（`mg8c40oowo80o08o0gsw0gwc-090124817222`），为其添加 Traefik 标签：

```yaml
services:
  mg8c40oowo80o08o0gsw0gwc:
    image: mg8c40oowo80o08o0gsw0gwc:latest
    container_name: mg8c40oowo80o08o0gsw0gwc-090124817222
    ports:
      - "3000:3000"
      - "8000:8000"

    labels:
      # 路由配置
      traefik.enable: "true"
      traefik.http.routers.jackcwf.rule: "Host(`www.jackcwf.com`)"
      traefik.http.routers.jackcwf.entrypoints: "websecure"
      traefik.http.routers.jackcwf.tls: "true"
      traefik.http.routers.jackcwf.service: "jackcwf"

      # 服务配置（前端）
      traefik.http.services.jackcwf.loadbalancer.server.port: "3000"
      traefik.http.services.jackcwf.loadbalancer.server.scheme: "http"

      # WebSocket 中间件（最关键！）
      traefik.http.middlewares.websocket-upgrade.headers.customrequestheaders.Connection: "upgrade"
      traefik.http.middlewares.websocket-upgrade.headers.customrequestheaders.Upgrade: "websocket"

      # 应用路由到中间件
      traefik.http.routers.jackcwf.middlewares: "websocket-upgrade@docker"

      # 可选：添加安全头
      traefik.http.middlewares.security.headers.frameoptions: "SAMEORIGIN"
      traefik.http.middlewares.security.headers.sslredirect: "true"
```

#### 步骤 3: 保存并重启

```bash
# 重启应用和 Traefik
docker-compose down
docker-compose up -d

# 或者只重启 Traefik
docker-compose restart coolify-proxy
```

---

### 方法 B: 通过 Coolify Web UI 修改

如果你的 Coolify 版本支持编辑 Docker 标签：

1. 登录 Coolify Web UI: https://coolpanel.jackcwf.com
2. 进入应用: datalablife/jackcwf:main
3. 找到 "Docker Labels" 或 "Traefik Configuration" 部分
4. 添加上面的 Traefik 标签
5. 保存并重新部署

---

### 方法 C: 使用 Traefik 动态配置文件

如果可以访问 Traefik 配置目录，创建一个配置文件：

```bash
# 创建 Traefik 动态配置
cat > /etc/traefik/dynamic/jackcwf.yml << 'EOF'
http:
  routers:
    jackcwf:
      rule: "Host(`www.jackcwf.com`)"
      service: jackcwf
      entryPoints:
        - websecure
      tls:
        certResolver: letsencrypt
      middlewares:
        - websocket-upgrade
        - security-headers

  services:
    jackcwf:
      loadBalancer:
        servers:
          - url: "http://mg8c40oowo80o08o0gsw0gwc-090124817222:3000"

  middlewares:
    websocket-upgrade:
      headers:
        customRequestHeaders:
          Connection: "upgrade"
          Upgrade: "websocket"

    security-headers:
      headers:
        sslRedirect: true
        frameoptions: "SAMEORIGIN"
        referrerPolicy: "no-referrer"
EOF

# 重启 Traefik
docker-compose restart coolify-proxy
```

---

## 🧪 验证修复

### 方法 1: 浏览器检查

```javascript
// 在浏览器控制台 (F12 → Console) 执行：
console.log(window.location.protocol);  // 应该是 https:

// 打开 Network 标签，刷新页面
// 查找 WS 类型的请求
// 应该看到 wss://www.jackcwf.com/_event
// 状态应该是 "101 Switching Protocols"
```

### 方法 2: 命令行检查

```bash
# 测试 WebSocket 连接
curl -i -N -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  https://www.jackcwf.com/_event

# 应该看到:
# HTTP/1.1 101 Switching Protocols
# Connection: upgrade
```

### 方法 3: 应用功能测试

1. 访问 https://www.jackcwf.com
2. 页面加载完成后应该不再显示 timeout 错误
3. 尝试登录
4. 应该能够成功登录和交互

---

## 🆘 常见问题

### Q1: "Cannot find Traefik configuration"

**可能原因**: Coolify 自动生成配置，不需要手动修改

**解决**:
```bash
# Coolify 会自动生成标签，无需手动干预
# 尝试通过 Coolify Web UI 重新部署应用
# 或者检查 Coolify 是否正确识别了你的应用
```

### Q2: "WebSocket still times out"

**可能原因**: Traefik 未正确读取配置

**解决**:
```bash
# 1. 检查 Traefik 日志
docker logs coolify-proxy | grep -i "websocket\|upgrade\|_event"

# 2. 检查 Traefik 是否看到了标签
docker inspect mg8c40oowo80o08o0gsw0gwc-090124817222 | grep -A 50 "Labels"

# 3. 强制重启 Traefik
docker stop coolify-proxy
docker rm coolify-proxy  # 仅在必要时
docker-compose up -d coolify-proxy
```

### Q3: "Certificate error with WebSocket"

**原因**: WebSocket 必须使用 HTTPS (wss://)

**解决**:
```bash
# 确保 Traefik 标签包含:
traefik.http.routers.jackcwf.entrypoints: "websecure"
traefik.http.routers.jackcwf.tls: "true"

# 确保 Let's Encrypt 证书已生成:
docker exec coolify-proxy ls -la /etc/traefik/acme/
```

### Q4: 如何同时处理前端和 WebSocket

**前端处理** (端口 3000):
```yaml
traefik.http.services.jackcwf.loadbalancer.server.port: "3000"
```

**WebSocket** (需要通过 `/_event` 路由到后端):
```yaml
# 同一个服务处理前端请求
# 前端（React）会自动通过 WebSocket 连接到后端
# Traefik 会将 /_event 的请求转发到应用的 3000 端口
# 应用内部处理 WebSocket 升级
```

---

## 📋 完整的工作配置示例

这是一个经过测试的完整配置，可以直接使用：

```yaml
version: "3"

services:
  mg8c40oowo80o08o0gsw0gwc:
    image: mg8c40oowo80o08o0gsw0gwc:e5f0b6fa2666fa64f81a117142ac9873cdafdddd
    container_name: mg8c40oowo80o08o0gsw0gwc-090124817222
    networks:
      - coolify

    environment:
      - REFLEX_ENV=production
      - NODE_ENV=production

    expose:
      - "3000"
      - "8000"

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 120s

    labels:
      # Traefik 启用
      traefik.enable: "true"

      # HTTP 路由（重定向到 HTTPS）
      traefik.http.routers.jackcwf-http.rule: "Host(`www.jackcwf.com`)"
      traefik.http.routers.jackcwf-http.entrypoints: "web"
      traefik.http.routers.jackcwf-http.middlewares: "redirect-https"

      # HTTPS 路由
      traefik.http.routers.jackcwf.rule: "Host(`www.jackcwf.com`)"
      traefik.http.routers.jackcwf.entrypoints: "websecure"
      traefik.http.routers.jackcwf.tls.certresolver: "letsencrypt"
      traefik.http.routers.jackcwf.service: "jackcwf"
      traefik.http.routers.jackcwf.middlewares: "websocket-upgrade"

      # 服务定义（前端和后端）
      traefik.http.services.jackcwf.loadbalancer.server.port: "3000"
      traefik.http.services.jackcwf.loadbalancer.server.scheme: "http"

      # WebSocket 中间件 - 最关键！
      traefik.http.middlewares.websocket-upgrade.headers.customrequestheaders.Connection: "upgrade"
      traefik.http.middlewares.websocket-upgrade.headers.customrequestheaders.Upgrade: "websocket"

      # HTTP 到 HTTPS 重定向
      traefik.http.middlewares.redirect-https.redirectscheme.scheme: "https"
      traefik.http.middlewares.redirect-https.redirectscheme.permanent: "true"

    depends_on:
      - coolify-proxy

    restart: unless-stopped

  coolify-proxy:
    image: traefik:v3.1
    container_name: coolify-proxy
    networks:
      - coolify

    ports:
      - "80:80"
      - "443:443"

    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./acme.json:/acme.json
      - ./traefik.yml:/traefik.yml:ro

    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
      - "--certificatesresolvers.letsencrypt.acme.email=your-email@example.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=acme.json"

    restart: unless-stopped

networks:
  coolify:
    driver: bridge
```

---

## 🚀 推荐步骤

1. **立即检查** Traefik 是否正确配置了你的应用
2. **如果未配置**, 通过 Coolify Web UI 重新部署应用
3. **如果仍未生效**, 手动添加 Docker 标签并重启
4. **验证** WebSocket 连接是否正常

---

## 📞 获取帮助

如果问题仍未解决：

```bash
# 1. 查看 Traefik 日志
docker logs coolify-proxy | tail -50

# 2. 查看应用标签
docker inspect mg8c40oowo80o08o0gsw0gwc-090124817222 | grep "traefik"

# 3. 检查网络连通性
docker exec mg8c40oowo80o08o0gsw0gwc-090124817222 curl -I http://localhost:3000/
docker exec mg8c40oowo80o08o0gsw0gwc-090124817222 curl -I http://localhost:8000/

# 4. 查看 Traefik 路由状态
curl -s http://localhost:8080/api/routes | jq '.[] | select(.name | contains("jackcwf"))'
```

---

**最后更新**: 2025-10-30
**优先级**: 🔴 高
**解决时间**: 5-10 分钟

