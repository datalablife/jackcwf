# WebSocket 连接修复 - 逐步执行指南

**问题**: 应用部署在 Coolify 生产环境，用户无法登录，显示: "Cannot connect to server: timeout. Check if server is reachable at wss://www.jackcwf.com/_event"

**根本原因**: Traefik 反向代理未正确转发 WebSocket 连接所需的 HTTP upgrade 请求

---

## 🚀 第一步：最快的解决方案（推荐）

### 通过 Coolify Web UI 重新部署应用

**为什么有效**: Coolify 在重新部署时会自动为应用生成正确的 Traefik 标签（包含 WebSocket 支持）

**步骤**:

1. **打开浏览器访问 Coolify 管理面板**:
   ```
   https://coolpanel.jackcwf.com
   ```

2. **登录到 Coolify**（使用你的 Coolify 凭证）

3. **找到你的应用**:
   - 看应用列表，找到 `datalablife/jackcwf:main` 或类似的应用名称
   - 点击进入应用详情

4. **重新部署应用**:
   - 在应用详情页面，找到 **"Actions"** 或 **"Options"** 菜单
   - 选择 **"Restart"** 或 **"Redeploy"** 按钮
   - 点击确认

5. **等待重新部署完成**:
   - 观察应用状态，应该会从 `restarting` → `running:healthy`
   - 耗时通常 1-3 分钟

6. **测试修复**:
   - 在浏览器中访问: https://www.jackcwf.com
   - 打开开发者工具: `F12` → 切换到 **"Network"** 标签
   - 刷新页面 (`F5`)
   - 在 Network 标签中查找包含 `_event` 的请求（应该显示为 `WS` 类型）
   - **成功标志**: 该请求的状态码应该是 **"101 Switching Protocols"**
   - 尝试用用户名和密码登录，应该能成功

**预期耗时**: 5-10 分钟

---

## 🔧 第二步：如果 Web UI 重新部署不行

### 在服务器上执行命令重启应用

**为什么有效**: 重启 Traefik 和应用容器，强制重新读取配置

**命令**（在服务器 shell 中执行，即 `root@s32615:~#` 提示符）:

```bash
# 命令 1: 重启应用容器
docker restart mg8c40oowo80o08o0gsw0gwc-090124817222

# 等待 10 秒钟让应用启动

# 命令 2: 重启 Traefik 反向代理
docker restart coolify-proxy

# 等待 5 秒钟让 Traefik 重新加载配置
```

**验证命令**（执行这个看是否修复成功）:

```bash
# 检查应用是否正常运行
docker ps | grep mg8c40oowo80o08o0gsw0gwc

# 输出应该显示: 应用容器状态为 Up
# 例如: mg8c40oowo80o08o0gsw0gwc-090124817222   datalablife/jackcwf:main ... Up ...
```

**然后测试**:
- 访问 https://www.jackcwf.com
- 打开开发者工具 (F12) → Network
- 刷新页面，查找 WebSocket 连接（`wss://www.jackcwf.com/_event`）
- 检查状态是否为 "101 Switching Protocols"

**预期耗时**: 2-3 分钟

---

## 🐛 第三步：如果上述都不行，执行诊断命令

### 运行诊断命令找出具体问题

**在服务器上执行这些命令，并记录输出**:

```bash
# ========== 诊断 1: 检查应用日志 ==========
echo "=== 应用日志 (最后 50 行) ==="
docker logs -n 50 mg8c40oowo80o08o0gsw0gwc-090124817222

echo ""
echo "=== Traefik 日志 (包含 WebSocket/应用相关) ==="
docker logs -n 100 coolify-proxy | grep -i "websocket\|jackcwf\|_event\|upgrade\|error"

# ========== 诊断 2: 检查应用的 Docker 标签 ==========
echo ""
echo "=== 应用的 Docker 标签（Traefik 配置）==="
docker inspect mg8c40oowo80o08o0gsw0gwc-090124817222 | grep -A 150 '"Labels"'

# ========== 诊断 3: 检查 Traefik 是否看到该应用 ==========
echo ""
echo "=== Traefik 路由配置 ==="
docker exec coolify-proxy curl -s http://localhost:8080/api/routes 2>/dev/null | grep -i jackcwf

# ========== 诊断 4: 检查应用内部网络连接 ==========
echo ""
echo "=== 应用内部连接测试 ==="
docker exec mg8c40oowo80o08o0gsw0gwc-090124817222 curl -I http://localhost:3000/ 2>/dev/null
```

### 根据诊断输出分析问题

#### 如果看到以下输出，说明问题在 Traefik 标签配置

**问题迹象**:
```
docker inspect 输出中没有看到:
  traefik.http.middlewares.websocket-upgrade.headers.customrequestheaders.Upgrade: "websocket"
  traefik.http.middlewares.websocket-upgrade.headers.customrequestheaders.Connection: "upgrade"
```

**解决办法**: 执行第四步

#### 如果看到 Traefik 日志有错误

**例如**:
```
level=error msg="Service not found" service=...
```

**解决办法**: 应用端口配置有问题，需要手动编辑配置

---

## 🔨 第四步：手动添加 Traefik WebSocket 配置（高级）

### 如果诊断发现 Traefik 标签缺失，手动添加

**重要**: 这一步只在诊断发现标签缺失时执行

```bash
# 创建 Traefik 动态配置文件
mkdir -p /data/coolify/traefik/config

cat > /data/coolify/traefik/config/websocket.yml << 'EOF'
http:
  middlewares:
    websocket-upgrade:
      headers:
        customRequestHeaders:
          Upgrade: "websocket"
          Connection: "upgrade"

  routers:
    jackcwf-websocket:
      rule: "Host(`www.jackcwf.com`) && Path(`/_event`)"
      service: app-service
      middlewares:
        - websocket-upgrade

  services:
    app-service:
      loadBalancer:
        servers:
          - url: "http://mg8c40oowo80o08o0gsw0gwc-090124817222:3000"
EOF

# 重启 Traefik 让配置生效
docker restart coolify-proxy

# 等待 10 秒
sleep 10

# 验证配置已加载
docker logs -n 20 coolify-proxy | grep -i "websocket\|_event"
```

---

## ✅ 验证修复成功

执行完上述步骤之一后，验证 WebSocket 连接已恢复：

### 方法 1: 浏览器验证（最直观）

1. 访问 https://www.jackcwf.com
2. 打开开发者工具: `F12`
3. 切换到 **Network** 标签
4. 刷新页面 (`F5` 或 `Ctrl+R`)
5. 在 Network 列表中查找 WebSocket 连接:
   - **URL**: `wss://www.jackcwf.com/_event`
   - **Type**: `WS` (WebSocket)
   - **Status**: `101 Switching Protocols` ✅
6. 尝试用用户名和密码登录

**成功标志**:
- ✅ Network 中能看到 WebSocket 连接
- ✅ 状态码为 101
- ✅ 能输入用户名和密码
- ✅ 能成功登录

### 方法 2: 命令行验证

```bash
# 测试 WebSocket 连接
curl -v -N \
  -H "Upgrade: websocket" \
  -H "Connection: upgrade" \
  https://www.jackcwf.com/_event

# 成功的输出应该包含:
# < HTTP/1.1 101 Switching Protocols
# < Upgrade: websocket
# < Connection: upgrade
```

### 方法 3: 查看应用日志

```bash
# 如果看到应用正在处理 WebSocket 连接，说明修复成功
docker logs -n 50 mg8c40oowo80o08o0gsw0gwc-090124817222 | grep -i "websocket\|event\|connection"
```

---

## 📋 执行流程表

| 步骤 | 方法 | 命令/操作 | 耗时 | 成功率 |
|------|------|---------|------|--------|
| 1️⃣ | Web UI 重新部署 | 在 Coolify 面板点击 Redeploy | 5-10 min | 85% |
| 2️⃣ | Docker 重启 | `docker restart` 两个命令 | 2-3 min | 80% |
| 3️⃣ | 诊断分析 | 执行诊断命令，看输出 | 5 min | 100% |
| 4️⃣ | 手动配置 | 创建 Traefik 配置文件 | 3-5 min | 95% |
| ✅ | 验证 | 浏览器测试或命令行验证 | 2 min | - |

---

## 🆘 常见问题排查

### Q1: 重启后仍然显示 WebSocket 超时

**可能原因**:
1. Coolify 版本过旧，WebSocket 配置未自动生成
2. Traefik 标签格式不正确
3. 应用绑定的端口不是 3000

**解决**:
- 执行诊断命令检查标签
- 手动执行第四步添加 Traefik 配置

### Q2: docker logs 命令显示 "permission denied"

**可能原因**: 没有 root 权限执行 docker 命令

**解决**:
```bash
# 在命令前加 sudo
sudo docker logs mg8c40oowo80o08o0gsw0gwc-090124817222

# 或使用当前用户（如果已添加到 docker 组）
# 检查权限
groups $(whoami)

# 如果输出中没有 docker，需要添加:
sudo usermod -aG docker $(whoami)
newgrp docker
```

### Q3: 显示 "Cannot connect to Docker daemon"

**可能原因**: Docker 服务未运行

**解决**:
```bash
# 启动 Docker 服务
sudo systemctl start docker

# 检查状态
sudo systemctl status docker

# 验证可以执行 docker 命令
docker ps
```

### Q4: WebSocket 连接仍然超时

**排查步骤**:

1. 检查应用是否真的在运行:
   ```bash
   docker ps | grep mg8c40oowo80o08o0gsw0gwc
   ```

2. 检查应用日志有没有错误:
   ```bash
   docker logs mg8c40oowo80o08o0gsw0gwc-090124817222 | tail -50
   ```

3. 检查 Traefik 日志有没有路由错误:
   ```bash
   docker logs coolify-proxy | grep -i "error\|jackcwf" | tail -20
   ```

4. 检查 DNS 是否正确指向服务器:
   ```bash
   nslookup www.jackcwf.com
   # 应该显示你的服务器 IP
   ```

---

## 📞 需要更多帮助？

如果上述步骤都尝试过仍未解决，请收集以下信息：

1. **应用日志**:
   ```bash
   docker logs mg8c40oowo80o08o0gsw0gwc-090124817222 > /tmp/app_logs.txt
   ```

2. **Traefik 日志**:
   ```bash
   docker logs coolify-proxy > /tmp/traefik_logs.txt
   ```

3. **Docker 标签**:
   ```bash
   docker inspect mg8c40oowo80o08o0gsw0gwc-090124817222 > /tmp/docker_labels.txt
   ```

4. **系统信息**:
   ```bash
   docker version
   docker ps --all
   ```

然后查看完整的详细文档: **docs/deployment/TRAEFIK_WEBSOCKET_FIX.md**
