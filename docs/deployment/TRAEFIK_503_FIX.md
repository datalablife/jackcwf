# Traefik 503 "No Available Server" 修复指南

## 问题描述

**症状：**
- Coolify 显示应用状态：`running:healthy` ✅
- 应用日志显示：`App running at http://0.0.0.0:3000/` ✅
- 但访问 `https://www.jackcwf.com` 返回：HTTP 503 "no available server" ❌

**根本原因：**

Traefik 无法将流量路由到容器，因为：
1. Nixpacks 生成的容器可能没有正确声明 `EXPOSE 3000` 指令
2. Coolify 的 Port Exposes 配置可能缺失或不正确
3. 应用虽然在 0.0.0.0:3000 监听，但 Traefik 不知道应该连接到哪个端口

---

## 诊断步骤

运行诊断脚本：

```bash
./scripts/dev/diagnose-coolify-503.sh mg8c40oowo80o08o0gsw0gwc
```

**检查清单：**

- [x] rxconfig.py 配置正确（frontend_host="0.0.0.0", frontend_port=3000）
- [x] nixpacks.toml 环境变量正确（FRONTEND_PORT=3000）
- [x] 应用日志显示正确启动
- [x] 健康检查通过（localhost:3000 可访问）
- [ ] **PORT 环境变量设置为 3000**（新增）
- [ ] Traefik 路由配置正确

---

## 修复方案

### 方案 A：修改 Nixpacks 配置（已实施）

**修改内容：**

在 `nixpacks.toml` 的 `[variables]` 部分添加 `PORT` 环境变量：

```toml
[variables]
PYTHONUNBUFFERED = "1"
PYTHONDONTWRITEBYTECODE = "1"
REFLEX_ENV = "production"
FRONTEND_PORT = "3000"
BACKEND_PORT = "8000"
# PORT is used by Nixpacks to determine which port to expose
# For Reflex, the frontend port is the primary entry point
PORT = "3000"  # ← 关键修改
VIRTUAL_ENV = "/app/.venv"
PATH = "/app/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
```

**为什么这能解决问题：**

- Nixpacks 使用 `PORT` 环境变量来确定应该在生成的 Dockerfile 中添加 `EXPOSE <PORT>` 指令
- Traefik 依赖容器的 EXPOSE 声明来确定应该连接到哪个端口
- 设置 `PORT=3000` 确保 Nixpacks 生成的容器正确暴露端口 3000

**部署步骤：**

1. 提交更改到 Git：
   ```bash
   git add nixpacks.toml
   git commit -m "fix: add PORT variable to nixpacks.toml for Traefik routing"
   git push
   ```

2. 在 Coolify 中重新部署：
   ```bash
   coolify deploy <project_id> mg8c40oowo80o08o0gsw0gwc
   ```

3. 等待部署完成（约 3-5 分钟）

4. 验证修复：
   ```bash
   curl -I https://www.jackcwf.com
   # 应该返回 HTTP/2 200 而不是 503
   ```

---

### 方案 B：Coolify Web 面板配置（备选）

如果方案 A 不起作用，在 Coolify Web 面板中手动配置：

**步骤：**

1. 访问：https://coolpanel.jackcwf.com/project/<project_id>/application/mg8c40oowo80o08o0gsw0gwc

2. 导航到 **Configuration** 标签页

3. 找到 **Port Exposes** 或 **Ports** 部分

4. 添加端口映射：
   ```
   3000:3000
   ```
   或者只是：
   ```
   3000
   ```

5. 保存并重新部署

**注意：**
- Port Exposes 配置可能在不同版本的 Coolify 中有不同的 UI
- 有些版本可能叫 "Ports"、"Expose Ports" 或 "Port Mappings"

---

### 方案 C：切换到 Dockerfile 构建（高级）

如果 Nixpacks 持续出现问题，切换到直接使用 Dockerfile：

**优点：**
- 完全控制构建过程
- Dockerfile 已经正确声明 `EXPOSE 3000 8000`
- 更容易调试和维护

**步骤：**

1. 在 Coolify 应用设置中：
   - 将构建方式从 "Nixpacks" 改为 "Dockerfile"
   - 确保 Dockerfile 路径设置为：`./Dockerfile`

2. 重新部署

**缺点：**
- 构建时间可能更长（需要编译所有依赖）
- 失去 Nixpacks 的自动优化

---

## 验证修复

### 1. 检查应用状态

```bash
coolify app get mg8c40oowo80o08o0gsw0gwc
# 应该显示：status: "running:healthy"
```

### 2. 测试 HTTPS 访问

```bash
curl -I https://www.jackcwf.com
# 应该返回：HTTP/2 200
```

### 3. 测试完整响应

```bash
curl https://www.jackcwf.com
# 应该返回 Reflex 应用的 HTML 内容，而不是 "no available server"
```

### 4. 检查应用日志

```bash
coolify app logs mg8c40oowo80o08o0gsw0gwc | tail -20
# 应该看到：
# App running at: http://0.0.0.0:3000/
# Backend running at: http://0.0.0.0:8000
```

### 5. 浏览器访问

打开浏览器访问：https://www.jackcwf.com

应该能看到 Reflex 应用的前端界面。

---

## 技术细节

### Reflex 应用的端口结构

Reflex 应用有两个独立的服务：

```
┌─────────────────────────────────────────────┐
│  Reflex Application Container               │
│                                             │
│  ┌─────────────────────┐  ┌──────────────┐ │
│  │  Frontend (React)   │  │   Backend    │ │
│  │  Port: 3000         │  │   (FastAPI)  │ │
│  │  Serves: HTML/JS/CSS│  │   Port: 8000 │ │
│  └─────────────────────┘  └──────────────┘ │
│           ▲                        ▲        │
│           │                        │        │
└───────────┼────────────────────────┼────────┘
            │                        │
            │ EXPOSE 3000            │ EXPOSE 8000
            │                        │
┌───────────▼────────────────────────▼────────┐
│         Traefik Reverse Proxy               │
│         (Routes: www.jackcwf.com → 3000)    │
└─────────────────────────────────────────────┘
            │
            │ HTTPS (443)
            │
┌───────────▼─────────────────────────────────┐
│         Internet Users                      │
│         (https://www.jackcwf.com)           │
└─────────────────────────────────────────────┘
```

### Traefik 路由机制

1. **Traefik 通过 Docker 标签发现服务**：
   ```yaml
   labels:
     - "traefik.enable=true"
     - "traefik.http.routers.app.rule=Host(`www.jackcwf.com`)"
     - "traefik.http.services.app.loadbalancer.server.port=3000"
   ```

2. **端口必须被 EXPOSE**：
   - 如果容器没有 `EXPOSE 3000`，Traefik 无法知道应该连接到哪个端口
   - 健康检查可以通过（使用 localhost:3000），但外部路由会失败

3. **Nixpacks 的 PORT 变量**：
   - Nixpacks 读取 `PORT` 环境变量来确定应该 EXPOSE 哪个端口
   - 如果没有设置 `PORT`，Nixpacks 可能不会添加 EXPOSE 指令

---

## 常见问题

### Q: 为什么健康检查通过但 Traefik 返回 503？

**A:** 健康检查在容器内部运行（使用 localhost），可以直接访问 127.0.0.1:3000。但 Traefik 从外部通过 Docker 网络访问容器，需要容器声明 EXPOSE 端口。

### Q: rxconfig.py 中的 frontend_host="0.0.0.0" 不够吗？

**A:** 这确保应用监听所有网络接口，但不会告诉 Docker/Traefik 应该暴露哪个端口。需要同时设置：
- 应用层：`frontend_host="0.0.0.0"` （应用监听地址）
- 容器层：`EXPOSE 3000` （Docker 端口声明）
- Nixpacks：`PORT=3000` （告诉 Nixpacks 添加 EXPOSE）

### Q: 可以使用端口 80 代替 3000 吗？

**A:** 技术上可以，但不推荐：
- Reflex 默认使用 3000（前端）和 8000（后端）
- Traefik 已经在监听 80/443 端口
- 在容器内使用标准端口，让 Traefik 处理外部访问

### Q: 如何确认 EXPOSE 指令已添加？

**A:** 部署后检查容器：
```bash
# 获取容器 ID
docker ps | grep working

# 检查容器配置
docker inspect <container_id> | grep -A 10 "ExposedPorts"
```

应该看到：
```json
"ExposedPorts": {
    "3000/tcp": {},
    "8000/tcp": {}
}
```

---

## 下一步行动

**立即执行：**

1. ✅ 修改 `nixpacks.toml` 添加 `PORT=3000`（已完成）
2. 提交并推送到 Git
3. 在 Coolify 触发重新部署
4. 验证修复生效
5. 更新文档记录解决方案

**监控：**

- 部署后观察应用日志 5 分钟
- 运行完整的健康检查测试
- 确认 Traefik 正确路由流量

**如果仍然失败：**

1. 尝试方案 B（Coolify Web 面板配置）
2. 检查 Coolify 服务器的 Traefik 配置
3. 联系 Coolify 支持或查看 Coolify GitHub Issues

---

## 参考资源

- **Reflex 部署文档**: https://reflex.dev/docs/hosting/self-hosting/
- **Nixpacks 配置**: https://nixpacks.com/docs/configuration/file
- **Traefik Docker 集成**: https://doc.traefik.io/traefik/providers/docker/
- **Coolify 文档**: https://coolify.io/docs

---

## 变更历史

- **2025-11-03**: 诊断 503 错误，添加 PORT 变量到 nixpacks.toml
- **预期修复时间**: 重新部署后 3-5 分钟
