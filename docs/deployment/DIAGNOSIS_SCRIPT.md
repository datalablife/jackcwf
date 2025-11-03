# 🔍 WebSocket 连接失败 - 诊断脚本

**现象**: F12 Network 标签中看不到 `_event` 请求，说明 WebSocket 连接完全没有建立

**原因**: Traefik 反向代理没有正确转发 WebSocket upgrade 请求

---

## 📝 如何运行诊断

你需要在你的服务器上运行一个简单的脚本。

### 方式 1: 通过 SSH 连接到服务器

```bash
# 在你的电脑上打开终端/命令行，连接到服务器
ssh root@你的服务器地址

# 例如（如果这是之前用过的地址）
ssh root@s32615

# 然后输入密码
```

### 方式 2: 如果你已经在服务器上

直接继续下面的步骤。

---

## 🚀 运行诊断脚本

在服务器的命令行中，复制以下整个代码块，粘贴到终端，按 Enter：

```bash
#!/bin/bash

echo "======================================"
echo "WebSocket 诊断 - 开始"
echo "======================================"

echo ""
echo "【第 1 步】检查应用容器状态"
echo "======================================="
docker ps | grep mg8c40oowo80o08o0gsw0gwc || echo "❌ 应用容器未找到！"

echo ""
echo "【第 2 步】检查应用是否在运行"
echo "======================================="
if docker ps | grep -q mg8c40oowo80o08o0gsw0gwc; then
    echo "✅ 应用容器在运行"
else
    echo "❌ 应用容器未运行"
fi

echo ""
echo "【第 3 步】查看应用最近的 10 行日志"
echo "======================================="
docker logs -n 10 mg8c40oowo80o08o0gsw0gwc-090124817222 2>/dev/null || echo "❌ 无法读取日志"

echo ""
echo "【第 4 步】检查 Traefik 日志中的错误"
echo "======================================="
echo "查找 WebSocket/jackcwf 相关错误..."
docker logs -n 100 coolify-proxy 2>/dev/null | grep -i "websocket\|jackcwf\|_event\|upgrade\|error" | tail -20 || echo "未找到相关日志"

echo ""
echo "【第 5 步】检查 Traefik 配置中的标签"
echo "======================================="
echo "查找应用的 Docker 标签（Traefik 配置）..."
docker inspect mg8c40oowo80o08o0gsw0gwc-090124817222 2>/dev/null | grep -A 200 '"Labels"' | grep -i "traefik\|websocket" | head -50 || echo "❌ 无法读取标签"

echo ""
echo "【第 6 步】检查 Traefik 是否识别该应用"
echo "======================================="
echo "查询 Traefik 路由..."
docker exec coolify-proxy curl -s http://localhost:8080/api/routes 2>/dev/null | grep -o '"host":"[^"]*jackcwf[^"]*"' || echo "❌ Traefik 未找到该域名的路由"

echo ""
echo "【第 7 步】检查应用是否在 3000 端口监听"
echo "======================================="
docker exec mg8c40oowo80o08o0gsw0gwc-090124817222 curl -I http://localhost:3000/ 2>/dev/null | head -5 || echo "❌ 无法连接到应用的 3000 端口"

echo ""
echo "======================================"
echo "诊断完成"
echo "======================================"
echo ""
echo "根据上面的输出，下面是可能的问题：
echo ""
echo "1️⃣ 如果第 4 步看到很多错误 → Traefik 配置有问题"
echo "2️⃣ 如果第 5 步没有 WebSocket 标签 → Traefik 标签未生成"
echo "3️⃣ 如果第 6 步未找到路由 → 应用未注册到 Traefik"
echo "4️⃣ 如果第 7 步连接失败 → 应用本身有问题"
echo ""
```

---

## 📋 如何粘贴这个脚本

### 如果你在 Windows 上

1. **选中上面的整个代码块**（从 `#!/bin/bash` 到最后的 `fi`）
2. **按 Ctrl+C 复制**
3. **右键点击终端窗口，选择"粘贴"**或按 **Shift+Insert**
4. **按 Enter 运行**

### 如果你在 Mac/Linux 上

1. **选中代码块**
2. **按 Cmd+C（Mac）或 Ctrl+C（Linux）复制**
3. **在终端中按 Cmd+V（Mac）或 Ctrl+Shift+V（Linux）粘贴**
4. **按 Enter 运行**

---

## 📊 诊断输出示例和解释

运行脚本后，根据输出来判断问题：

### ✅ 好的迹象

```
【第 1 步】检查应用容器状态
mg8c40oowo80o08o0gsw0gwc-090124817222   datalablife/jackcwf:main ... Up ...

【第 2 步】检查应用是否在运行
✅ 应用容器在运行

【第 3 步】查看应用最近的日志
[app logs showing normal operation]

【第 5 步】检查标签
traefik.http.routers.jackcwf.rule=Host(`www.jackcwf.com`)
traefik.http.middlewares.websocket-upgrade.headers.customrequestheaders.Upgrade=websocket
traefik.http.middlewares.websocket-upgrade.headers.customrequestheaders.Connection=upgrade

【第 6 步】Traefik 路由
"host":"www.jackcwf.com"
```

### ❌ 坏的迹象

**如果第 5 步中看不到 `websocket` 相关的标签**：
```
❌ traefik.http.middlewares.websocket-upgrade 标签不存在
```
→ **说明 Traefik 没有正确配置 WebSocket 支持**

**如果第 4 步看到错误**：
```
ERROR: Service not found
ERROR: websocket upgrade failed
```
→ **说明 Traefik 无法正确路由请求**

**如果第 6 步未找到路由**：
```
❌ Traefik 未找到该域名的路由
```
→ **说明应用未注册到 Traefik，可能是标签配置错误**

---

## 🔧 根据诊断结果的修复方案

### 情况 A: 标签中没有 WebSocket 配置

**问题**: Traefik 标签中缺少 WebSocket upgrade 相关的配置

**原因**: Coolify 在生成 Traefik 配置时没有包含 WebSocket 支持

**修复方法**:

1. **进入 Coolify Web UI**
2. **找到应用 → Settings（设置）**
3. **查看 "Expose Ports"（暴露端口）部分**
4. **确保正确配置了以下内容**:
   - Port: `3000`
   - Protocol: `HTTP` (或 `HTTPS`)
5. **保存设置**
6. **点击 "Redeploy"（重新部署）**

---

### 情况 B: Traefik 日志中有大量错误

**问题**: Traefik 反向代理出现了错误

**修复方法**:

1. **查看完整的 Traefik 日志**:
   ```bash
   docker logs -n 200 coolify-proxy | grep -i "error\|warning" | tail -50
   ```

2. **重启 Traefik**:
   ```bash
   docker restart coolify-proxy
   ```

3. **等待 10 秒，再测试**

---

### 情况 C: 应用本身有问题

**问题**: 应用容器崩溃或没有正确启动

**修复方法**:

1. **查看完整应用日志**:
   ```bash
   docker logs mg8c40oowo80o08o0gsw0gwc-090124817222
   ```

2. **查找错误信息**（通常会显示为 `ERROR`, `Exception`, `Failed`）

3. **重启应用**:
   ```bash
   docker restart mg8c40oowo80o08o0gsw0gwc-090124817222
   ```

---

## 📝 收集诊断信息

运行完脚本后，**请告诉我**:

1. **第 4 步的输出** - Traefik 日志中有什么错误？
2. **第 5 步的输出** - 能看到哪些 Traefik 标签？特别是有没有 `websocket` 相关的？
3. **第 6 步的输出** - Traefik 能否找到路由？
4. **第 7 步的输出** - 应用能否响应？

根据这些信息，我可以给你更准确的解决方案。

---

## 🎯 下一步

1. **运行上面的诊断脚本**
2. **告诉我输出中看到的关键错误或信息**
3. **我会根据诊断结果给你具体的修复步骤**

不需要完整的输出，只需要告诉我：
- ✅ 应用容器在运行吗？
- ✅ Traefik 日志中有错误吗？（什么错误？）
- ✅ 能看到 WebSocket 标签吗？
- ✅ 应用能响应吗？

---

## 💡 如果不想运行脚本，快速检查方式

如果你觉得脚本太复杂，试试这个最简单的：

```bash
# 1. 检查应用日志
docker logs mg8c40oowo80o08o0gsw0gwc-090124817222

# 2. 重启应用
docker restart mg8c40oowo80o08o0gsw0gwc-090124817222

# 3. 重启 Traefik
docker restart coolify-proxy

# 4. 等待 10 秒
sleep 10

# 5. 再次测试访问 https://www.jackcwf.com
```

运行这三个重启命令后，再访问网站测试一次。

---

## 📞 卡住了？

如果你在任何步骤卡住：

1. **"我找不到终端/命令行"** → 在 Windows 上搜索 "cmd"，在 Mac 上搜索 "Terminal"
2. **"怎样连接到服务器？"** → 你之前用过什么工具连接（Putty、SSH、其他？）
3. **"脚本运行出错"** → 告诉我出错的具体信息

别紧张，慢慢来，我会帮你！
