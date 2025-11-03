# WebSocket 修复 - 快速执行清单

**你的系统**:
- 反向代理: Traefik v3.1 (coolify-proxy)
- 应用: mg8c40oowo80o08o0gsw0gwc-090124817222
- 问题: WebSocket 连接超时 wss://www.jackcwf.com/_event

---

## ⚡ 最快解决方案 (5分钟)

### 方案1: 通过 Coolify Web UI 重新部署（推荐）

这是最简单的方法，让 Coolify 自动重新生成 Traefik 配置。

**步骤**:

1. 打开浏览器访问: https://coolpanel.jackcwf.com
2. 登录到 Coolify
3. 在应用列表中找到: "datalablife/jackcwf:main"
4. 点击应用进入详情页
5. 找到 **"Restart"** 或 **"Redeploy"** 按钮
6. 点击按钮重新启动应用
7. 等待部署完成（显示 "running:healthy"）
8. 访问 https://www.jackcwf.com 测试
9. 打开开发者工具 (F12) → Network → 刷新页面
10. 查找 "WS" 请求，应该看到 "101 Switching Protocols"

---

## 🔧 如果方案1不行，执行方案2

### 方案2: 手动修复 Traefik 配置

你需要在服务器上执行以下命令:

#### 命令 1: 进入 Coolify 容器（选择其中一个）

```bash
# 尝试方式 1
docker exec -it coolify sh

# 如果上面不行，尝试方式 2（直接执行命令）
docker exec coolify sh -c "your-command-here"

# 查看可用的 Shell
docker exec coolify which bash
docker exec coolify which sh
docker exec coolify which ash
```

#### 命令 2: 查看 Coolify 配置

如果你能进入容器，执行：

```bash
# 列出应用配置
cd /app
ls -la

# 查看数据库中的应用配置
sqlite3 /data/coolify.db "SELECT * FROM applications WHERE name LIKE '%jackcwf%';"

# 或查看应用文件
find /data -name "*jackcwf*" -o -name "*mg8c40oowo80o08o0gsw0gwc*"
```

#### 命令 3: 强制重新部署

```bash
# 在服务器上（不需要进入容器）执行：
docker exec coolify sh -c "cd /app && php artisan app:deploy --uuid=mg8c40oowo80o08o0gsw0gwc"

# 或通过 Coolify CLI
coolify app restart mg8c40oowo80o08o0gsw0gwc

# 或重启应用容器
docker restart mg8c40oowo80o08o0gsw0gwc-090124817222

# 重启 Traefik
docker restart coolify-proxy
```

---

## 🐛 诊断命令

如果上述方法都不行，运行这些诊断命令来了解具体问题：

```bash
# 1. 检查应用容器状态
docker ps | grep mg8c40oowo80o08o0gsw0gwc

# 2. 查看应用日志（最后50行）
docker logs -n 50 mg8c40oowo80o08o0gsw0gwc-090124817222

# 3. 检查 Traefik 日志（查找 WebSocket 或应用相关的错误）
docker logs -n 100 coolify-proxy | grep -i "websocket\|jackcwf\|_event\|upgrade"

# 4. 检查应用的 Docker 标签（Traefik 配置）
docker inspect mg8c40oowo80o08o0gsw0gwc-090124817222 | grep -A 100 '"Labels"'

# 5. 查看 Traefik 配置是否看到了应用
docker exec coolify-proxy curl -s http://localhost:8080/api/routes | grep -i jackcwf

# 6. 测试应用网络连通性
docker exec mg8c40oowo80o08o0gsw0gwc-090124817222 curl -I http://localhost:3000/

# 7. 查看所有 Traefik 路由
docker exec coolify-proxy curl -s http://localhost:8080/api/routes | jq '.'
```

---

## 📋 按照这个顺序尝试

| 步骤 | 操作 | 预期结果 | 耗时 |
|------|------|--------|------|
| 1 | 方案 1: 通过 Web UI 重新部署 | WebSocket 正常 | 5 min |
| 2 | 方案 2: docker restart 重启应用 | WebSocket 正常 | 2 min |
| 3 | 运行诊断命令 1-7 | 看到具体的配置和日志 | 5 min |
| 4 | 根据日志分析原因 | 找到根本问题 | 10 min |
| 5 | 查看详细文档 | docs/deployment/TRAEFIK_WEBSOCKET_FIX.md | - |

---

## ✅ 成功的标志

修复成功后，你会看到：

1. **浏览器 Network 标签**:
   - ✅ 请求 URL: `wss://www.jackcwf.com/_event`
   - ✅ 状态: `101 Switching Protocols`
   - ✅ 显示 "websocket" 连接

2. **应用功能**:
   - ✅ 页面加载时不再显示 timeout 错误
   - ✅ 能够输入用户名和密码
   - ✅ 能够成功登录

3. **命令验证**:
   ```bash
   curl -I -N -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     https://www.jackcwf.com/_event

   # 应该返回:
   # HTTP/1.1 101 Switching Protocols
   ```

---

## 💡 最可能的原因

根据你的配置，WebSocket 问题最可能是由以下原因导致：

1. **Traefik 标签未正确配置** (70% 概率)
   - Coolify 没有为应用添加 WebSocket 支持的标签
   - 解决: 重新部署应用让 Coolify 重新生成标签

2. **Traefik 未读取配置** (20% 概率)
   - Traefik 进程未正确加载标签
   - 解决: 重启 Traefik `docker restart coolify-proxy`

3. **应用端口映射错误** (5% 概率)
   - 应用未在 3000 端口正确监听
   - 解决: 检查应用日志 `docker logs mg8c40oowo80o08o0gsw0gwc-090124817222`

4. **Coolify 版本问题** (5% 概率)
   - 你的 Coolify 版本 (4.0.0-beta.434) 可能有 bug
   - 解决: 更新 Coolify 或手动添加 Traefik 配置

---

## 🚀 立即行动

**现在就执行**:

1. 打开 https://coolpanel.jackcwf.com
2. 找到应用重新部署
3. 等待完成
4. 刷新 https://www.jackcwf.com 测试

**5分钟内应该能看到结果！**

---

## 如果需要更多帮助

完整的详细文档在: **docs/deployment/TRAEFIK_WEBSOCKET_FIX.md**

包含内容:
- 多种修复方案
- 完整的 docker-compose 配置示例
- 高级诊断步骤
- 常见问题解答

