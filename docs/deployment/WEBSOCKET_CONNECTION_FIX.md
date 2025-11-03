# WebSocket 连接失败诊断和修复

**问题**: 生产环境访问 https://www.jackcwf.com 时出现错误：
```
Cannot connect to server: timeout
Check if server is reachable at wss://www.jackcwf.com/_event
```

**应用信息**:
- 应用ID: mg8c40oowo80o08o0gsw0gwc
- 应用名: datalablife/jackcwf:main
- 应用状态: running:healthy
- 后端日志: 正常，应用在 http://0.0.0.0:8000 运行

---

## 🔍 问题分析

Reflex 框架需要通过 **WebSocket** (`wss://`) 与后端通信，用于实时交互和状态同步。

**问题原因**:
Coolify 的反向代理（Nginx）没有正确配置 WebSocket 支持，导致：
- HTTP 请求 ✅ 可以正常转发
- WebSocket 升级请求 ❌ 被拒绝

---

## 🛠️ 解决方案

### 方案 A: 通过 Coolify CLI 更新（推荐）

Coolify 应该在部署时自动配置 WebSocket 支持，但有时需要手动修复。

#### 步骤 1: 检查 Coolify Nginx 配置

```bash
# 进入 Coolify 容器
docker exec -it coolify-docker /bin/bash

# 查看应用的 Nginx 配置
cat /etc/nginx/sites-enabled/default
# 或查找包含你域名的配置
grep -r "www.jackcwf.com" /etc/nginx/
```

#### 步骤 2: 更新 Nginx 配置以支持 WebSocket

编辑 Nginx 配置文件（通常在 `/etc/nginx/sites-available/default` 或 `/etc/nginx/conf.d/`）：

```nginx
upstream backend {
    server 127.0.0.1:8000;  # Reflex 后端地址
}

server {
    listen 80;
    server_name www.jackcwf.com;

    # HTTP → HTTPS 重定向
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name www.jackcwf.com;

    # SSL 证书配置
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    # WebSocket 支持的关键配置
    proxy_read_timeout 86400;
    proxy_send_timeout 86400;

    location / {
        # 反向代理到 Reflex 前端 (3000)
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /_event {
        # WebSocket 反向代理到后端 (8000)
        proxy_pass http://127.0.0.1:8000;

        # WebSocket 协议升级配置 (最关键!)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # WebSocket 超时配置
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;

        # 代理头配置
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 关键：禁用缓冲（WebSocket 需要）
        proxy_buffering off;
        proxy_request_buffering off;
    }

    location ~ ^/(\.well-known|/_next) {
        # 静态文件和 Next.js 资源
        proxy_pass http://127.0.0.1:3000;
    }
}
```

#### 步骤 3: 验证并重启 Nginx

```bash
# 检查 Nginx 配置语法
nginx -t

# 重启 Nginx
systemctl restart nginx
# 或
docker restart coolify-docker  # 如果在容器中
```

---

### 方案 B: 通过 Coolify Web UI 修复（如支持）

1. 登录 Coolify: https://coolpanel.jackcwf.com
2. 进入应用详情: datalablife/jackcwf:main
3. 查找 "Reverse Proxy" 或 "Nginx" 配置部分
4. 确保启用了 WebSocket 支持选项
5. 保存配置并重新部署

---

### 方案 C: 在应用层解决（备选）

如果无法修改 Nginx 配置，在 Reflex 应用中配置：

#### 编辑 `rxconfig.py`

```python
import reflex as rx

config = rx.Config(
    app_name="working",

    # WebSocket 配置
    ws_protocol="wss",  # 使用 WebSocket Secure

    # 前端配置
    frontend_packages=[],

    # 其他配置...
)
```

#### 编辑 `working/working.py` 中的 State 类

```python
import reflex as rx

class State(rx.State):
    """状态管理类"""

    # 配置 WebSocket 连接参数
    # Reflex 会自动使用 wss:// 而不是 ws://
    pass
```

---

## ✅ 验证修复

修复后，用以下方法验证 WebSocket 连接是否正常：

### 1. 浏览器控制台检查

1. 打开 https://www.jackcwf.com
2. 打开浏览器开发者工具 (F12)
3. 进入 "Network" 标签
4. 查找 "WS" 类型的请求

**正常情况**:
- ✅ 请求 URL: `wss://www.jackcwf.com/_event`
- ✅ 状态: "101 Switching Protocols"
- ✅ 显示 "websocket" 连接

**异常情况**:
- ❌ 显示 timeout 或 connection refused
- ❌ HTTP 状态码 4xx 或 5xx

### 2. 命令行验证

```bash
# 测试 HTTP 连接
curl -I https://www.jackcwf.com
# 应该返回 HTTP/2 200

# 测试 WebSocket 连接（需要 wscat 工具）
npm install -g wscat
wscat -c wss://www.jackcwf.com/_event
# 应该显示 "Connected"
```

### 3. 应用级验证

1. 访问 https://www.jackcwf.com
2. 页面应该加载正常
3. 登录表单应该可以交互
4. 输入用户名和密码
5. 点击登录按钮
6. 应该能成功登录（不再显示 timeout 错误）

---

## 🔧 常见问题

### Q1: 修改 Nginx 配置后仍然无法连接

**可能原因**:
- 配置文件没有被正确应用
- Nginx 进程没有重启
- Coolify 自动覆盖了配置

**解决步骤**:
```bash
# 1. 查看 Nginx 进程状态
ps aux | grep nginx

# 2. 强制重启 Nginx
systemctl restart nginx

# 3. 如果在 Docker 中，重启容器
docker-compose restart nginx
# 或
docker restart coolify-docker

# 4. 检查配置是否被应用
curl -I https://www.jackcwf.com/_event
```

### Q2: Coolify 自动恢复原配置

如果 Coolify 在部署时自动恢复 Nginx 配置，需要：

1. 检查 Coolify 的部署配置
2. 确保启用 "WebSocket Support" 或类似选项
3. 或者在 Coolify 的"自定义 Nginx 配置"部分添加 WebSocket 支持

### Q3: 域名 HTTPS 正常，但 WebSocket 连接失败

这是最常见的问题。原因是 HTTP/HTTPS 和 WebSocket 走不同的代理路径。

**解决**:
- 确保 `/_event` 路由被正确代理到后端
- 确保 Nginx 中有 `Upgrade` 和 `Connection` 头设置
- 确保禁用了缓冲 (`proxy_buffering off`)

---

## 📊 完整的 Nginx 配置示例

以下是一个完整、可直接使用的配置：

```nginx
# /etc/nginx/sites-available/jackcwf

upstream reflex_frontend {
    server 127.0.0.1:3000;
}

upstream reflex_backend {
    server 127.0.0.1:8000;
}

# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name www.jackcwf.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS 服务器配置
server {
    listen 443 ssl http2;
    server_name www.jackcwf.com;

    # SSL 证书（Let's Encrypt）
    ssl_certificate /path/to/live/www.jackcwf.com/fullchain.pem;
    ssl_certificate_key /path/to/live/www.jackcwf.com/privkey.pem;

    # SSL 最佳实践
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 安全头
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # 日志
    access_log /var/log/nginx/jackcwf_access.log;
    error_log /var/log/nginx/jackcwf_error.log;

    # 静态文件缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        proxy_pass http://reflex_frontend;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # WebSocket 连接 - 最关键的部分！
    location /_event {
        proxy_pass http://reflex_backend;

        # 协议升级到 WebSocket
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 超时配置（WebSocket 需要长连接）
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
        proxy_connect_timeout 7d;

        # 代理头
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;

        # 禁用缓冲（WebSocket 必需）
        proxy_buffering off;
        proxy_request_buffering off;
    }

    # API 和其他后端路由
    location ~ ^/api {
        proxy_pass http://reflex_backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 前端应用
    location / {
        proxy_pass http://reflex_frontend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 🚀 下一步

1. **立即检查** Coolify Nginx 配置是否包含 WebSocket 支持
2. **如果没有**, 按方案 A 或 B 添加配置
3. **验证修复** - 刷新浏览器，检查 WebSocket 连接
4. **测试登录** - 尝试用用户名密码登录

---

## 📞 获取更多帮助

如果问题仍未解决：

1. **检查应用日志**
   ```bash
   coolify app logs mg8c40oowo80o08o0gsw0gwc
   ```

2. **检查 Nginx 错误日志**
   ```bash
   tail -f /var/log/nginx/error.log
   ```

3. **在浏览器控制台查看具体错误**
   - F12 → Console 标签
   - 查找 WebSocket 相关的错误信息

4. **参考 Reflex 官方文档**
   - https://reflex.dev/docs/deployment/
   - https://reflex.dev/docs/advanced/custom-backend/

---

**最后更新**: 2025-10-30
**应用状态**: running:healthy
**优先级**: 🔴 高 - 阻止用户登录

