# Reflex Coolify 部署 - 快速修复指南

## TL;DR - 立即执行这些步骤

如果你只想快速解决问题，按照以下步骤操作：

### 1. 更新配置文件（已完成 ✓）

这些文件已经为你准备好：

- ✓ `nixpacks.toml` - 修复了构建配置
- ✓ `start.sh` - 增强的启动脚本
- ✓ `Dockerfile` - 备用方案

### 2. 提交代码

```bash
cd /mnt/d/工作区/云开发/working

# 添加修改的文件
git add nixpacks.toml start.sh Dockerfile

# 提交
git commit -m "fix: update Nixpacks config for Coolify deployment

- Fix nixpacks.toml build phases
- Add enhanced startup script with logging
- Configure proper health check timing
- Set correct environment variables"

# 推送到远程
git push origin main
```

### 3. 在 Coolify 面板配置（5 分钟）

访问：https://coolpanel.jackcwf.com

#### 3.1 环境变量

进入应用设置 → Environment Variables → 添加：

```
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
REFLEX_ENV=production
FRONTEND_PORT=3000
BACKEND_PORT=8000
```

#### 3.2 健康检查（关键！）

进入应用设置 → Health Check → 配置：

| 设置 | 值 |
|------|-----|
| Enabled | ✓ |
| Path | `/` |
| Port | `3000` |
| **Initial Delay** | **60** 秒 ⭐ |
| Interval | 30 秒 |
| Timeout | 10 秒 |
| Retries | 5 |

⚠️ **Initial Delay 60 秒是解决问题的关键！**

#### 3.3 资源限制

进入应用设置 → Resources：

- Memory: 1024 MB
- CPU: 1.0 core

### 4. 重新部署

在 Coolify 点击 "Deploy" 按钮，或者：

```bash
coolify deploy uuid mg8c40oowo80o08o0gsw0gwc
```

### 5. 验证部署

等待 2-3 分钟，然后检查：

1. **状态**: 应显示 `running:healthy`（不再是 `exited:unhealthy`）
2. **日志**: 应看到 "App running at" 消息
3. **访问**: 浏览器打开应用 URL

---

## 问题根本原因（简述）

1. **Nixpacks 配置错误** → 修复了构建阶段
2. **健康检查太早** → 延迟到 60 秒
3. **日志输出被缓冲** → 设置 `PYTHONUNBUFFERED=1`
4. **前端未编译** → 添加 `reflex export` 步骤

---

## 本地测试（可选）

在推送到 Coolify 之前，可以本地测试：

### 测试 Dockerfile

```bash
./scripts/test/test-docker-build.sh
```

### 测试 Nixpacks

```bash
# 需要先安装 Nixpacks
curl -sSL https://nixpacks.com/install.sh | bash

# 运行测试
./scripts/test/test-nixpacks-build.sh
```

---

## 故障排除

### 问题：容器还是立即退出

**检查**:
```bash
coolify app logs mg8c40oowo80o08o0gsw0gwc
```

**可能原因**:
- uv sync 失败 → 检查 pyproject.toml
- Python 模块导入错误 → 检查依赖版本
- 内存不足 → 增加到 1GB

### 问题：健康检查还是失败

**检查**:
- Initial Delay 确实设置为 60 秒吗？
- 端口 3000 是否正确映射？
- 应用日志显示 "App running" 吗？

**解决**:
1. 进入 Coolify → Health Check
2. 禁用健康检查（临时）
3. 检查应用是否能启动
4. 重新启用，增加延迟到 90 秒

### 问题：前端 404

**检查**:
```bash
# 查看构建日志
# 确认看到 "Exporting frontend" 消息
```

**解决**:
- 确认 build 阶段有 `reflex export`
- 检查 `.web` 目录是否生成

---

## 如果还是不行

1. **查看完整诊断**:
   - 阅读 `DEPLOYMENT_DIAGNOSIS.md`

2. **检查 Coolify 配置**:
   - 阅读 `COOLIFY_CONFIG.md`

3. **本地复现问题**:
   - 运行测试脚本
   - 查看详细错误

4. **收集信息**:
   ```bash
   # 应用详情
   coolify app get mg8c40oowo80o08o0gsw0gwc --format json

   # 部署历史
   coolify deploy list --format json

   # 完整日志
   coolify app logs mg8c40oowo80o08o0gsw0gwc
   ```

---

## 检查清单

部署前确认：

- [ ] `nixpacks.toml` 已更新
- [ ] 代码已提交并推送到 Git
- [ ] Coolify 环境变量已配置
- [ ] 健康检查 Initial Delay = 60 秒
- [ ] 资源限制 ≥ 1GB 内存
- [ ] 端口映射 3000 和 8000
- [ ] Auto Deploy 已启用（可选）

部署后验证：

- [ ] 状态 = `running:healthy`
- [ ] 日志显示 "App running at"
- [ ] 前端可访问（http://yourapp.jackcwf.com）
- [ ] 后端可访问（http://yourapp.jackcwf.com/api）
- [ ] 没有错误日志

---

## 成功标志

当你看到以下内容时，说明部署成功了：

### Coolify 面板
```
Status: ● running:healthy
Health Check: ✓ Passing
Uptime: > 2 minutes
```

### 应用日志
```
==================================================
Starting Reflex 0.8.16 Application
==================================================

Environment Information:
  Python version: 3.12.x
  Node version: 20.x.x

Reflex version: 0.8.16
✓ Frontend compiled (.web directory exists)

==================================================
Starting Reflex in production mode...
==================================================

Compiling: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
App running at:
  ├─ http://0.0.0.0:8000 (backend)
  └─ http://0.0.0.0:3000 (frontend)
```

### 浏览器
- 打开 URL → 看到登录页面
- 输入 admin/password → 登录成功
- 控制台无 WebSocket 错误

---

## 文档索引

| 文档 | 用途 |
|------|------|
| `QUICK_FIX_GUIDE.md` | 快速修复（本文档） |
| `DEPLOYMENT_DIAGNOSIS.md` | 完整的问题诊断和分析 |
| `COOLIFY_CONFIG.md` | 详细的 Coolify 配置步骤 |
| `nixpacks.toml` | Nixpacks 构建配置 |
| `start.sh` | 应用启动脚本 |
| `scripts/test/test-docker-build.sh` | 本地 Docker 测试 |
| `scripts/test/test-nixpacks-build.sh` | 本地 Nixpacks 测试 |

---

**准备好了吗？开始部署！**

1. 提交代码 ✓
2. 配置 Coolify ✓
3. 点击 Deploy ✓
4. 等待 2-3 分钟 ✓
5. 验证成功 ✓

祝你好运！
