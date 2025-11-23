# 🚀 Story 4.4 - 快速部署指南

**完成日期**: 2025-11-21
**状态**: ✅ **已准备，可执行**

---

## 📋 部署概览 (5 分钟)

```
你的代码变更
    ↓
推送到 GitHub main 分支
    ↓
GitHub Actions 自动触发
    ↓
构建 Docker 镜像
    ↓
推送到 GHCR (镜像仓库)
    ↓
Coolify 自动拉取新镜像
    ↓
应用自动更新并启动
    ↓
✅ 完成！
```

---

## 🎯 部署步骤

### Step 1️⃣: 在 GitHub 配置 Secrets (3 分钟)

**位置**: GitHub 仓库 → Settings → Secrets and variables → Actions

**添加以下 3 个 Secrets**:

| 名称 | 值 |
|------|-----|
| `COOLIFY_API_TOKEN` | 从 Coolify 获取 |
| `COOLIFY_FQDN` | `https://coolpanel.jackcwf.com` |
| `COOLIFY_APP_UUID` | `mg8c40oowo80o08o0gsw0gwc` |

**如何获取 Coolify API Token**:
1. 访问: https://coolpanel.jackcwf.com
2. 登录 → Account Settings → API Tokens
3. 创建新 Token 并复制

---

### Step 2️⃣: 推送代码触发部署 (自动)

```bash
# 推送到 main 分支（自动触发部署）
git push origin main

# 或者推送到 feature 分支（也会触发）
git push origin feature/epic4-hybrid-frontend
```

**GitHub Actions 会自动**:
✅ 检出代码
✅ 构建 Docker 镜像
✅ 推送到 GHCR
✅ 通知 Coolify 更新

---

### Step 3️⃣: 监控部署过程 (实时)

```bash
# 查看应用日志 (实时更新)
coolify app logs mg8c40oowo80o08o0gsw0gwc --context myapp --follow

# 或者检查应用状态
coolify app status mg8c40oowo80o08o0gsw0gwc --context myapp
```

---

### Step 4️⃣: 验证应用 (完成后)

```bash
# 检查后端健康状态 ✅
curl http://mg8c40oowo80o08o0gsw0gwc.47.79.87.199.sslip.io/health

# 检查前端可访问性 ✅
curl http://mg8c40oowo80o08o0gsw0gwc.47.79.87.199.sslip.io

# 检查 API ✅
curl http://mg8c40oowo80o08o0gsw0gwc.47.79.87.199.sslip.io/api/conversations
```

---

## ⚡ 常用命令参考

### 查看应用信息

```bash
# 列出所有应用
coolify app list --context myapp

# 查看应用详情
coolify app get mg8c40oowo80o08o0gsw0gwc --context myapp

# 查看应用状态
coolify app status mg8c40oowo80o08o0gsw0gwc --context myapp
```

### 查看日志

```bash
# 实时日志 (最后 100 行)
coolify app logs mg8c40oowo80o08o0gsw0gwc --context myapp --follow

# 历史日志 (最后 50 行)
coolify app logs mg8c40oowo80o08o0gsw0gwc --context myapp --tail 50

# 重定向到文件保存
coolify app logs mg8c40oowo80o08o0gsw0gwc --context myapp > app.log
```

### 应用控制

```bash
# 重启应用
coolify app restart mg8c40oowo80o08o0gsw0gwc --context myapp

# 停止应用
coolify app stop mg8c40oowo80o08o0gsw0gwc --context myapp

# 启动应用
coolify app start mg8c40oowo80o08o0gsw0gwc --context myapp
```

### 环境变量管理

```bash
# 列出所有环境变量
coolify app env list mg8c40oowo80o08o0gsw0gwc --context myapp

# 设置环境变量
coolify app env set mg8c40oowo80o08o0gsw0gwc \
  --context myapp \
  --key DATABASE_URL \
  --value "postgresql://user:pass@host:5432/db"

# 删除环境变量
coolify app env delete mg8c40oowo80o08o0gsw0gwc \
  --context myapp \
  --key ENV_VAR_NAME
```

---

## 📊 部署时间预期

| 步骤 | 预期时间 |
|------|---------|
| 配置 Secrets | 3 分钟 |
| 代码推送 | <1 分钟 |
| GitHub Actions 构建 | 3-5 分钟 |
| 镜像推送到 GHCR | 1-2 分钟 |
| Coolify 拉取和启动 | 2-3 分钟 |
| **总计** | **~10-15 分钟** |

---

## ✅ 部署检查清单

部署后请逐项验证:

- [ ] **Secrets 已配置** - GitHub Settings 中可见 3 个 Secrets
- [ ] **GitHub Actions 已运行** - Actions 选项卡显示成功
- [ ] **镜像已推送** - ghcr.io 中可见新镜像
- [ ] **应用已启动** - `coolify app status` 显示 running
- [ ] **健康检查通过** - `/health` 端点返回 200
- [ ] **前端可访问** - 浏览器能打开应用
- [ ] **日志正常** - `coolify app logs` 显示正常启动

---

## 🆘 遇到问题？

### 1️⃣ Secrets 未生效

```bash
# 重新检查 Secrets 是否正确设置
# GitHub Settings → Secrets → 验证值
# 常见错误：多余空格、错误的 Token
```

### 2️⃣ GitHub Actions 失败

```bash
# 查看 Actions 日志
# GitHub → Actions → 最近的运行 → 查看详细日志

# 常见问题:
# - Docker 构建失败：检查 Dockerfile 语法
# - 镜像推送失败：检查 GHCR 认证
# - Secrets 缺失：添加缺失的 Secrets
```

### 3️⃣ 应用启动失败

```bash
# 查看应用日志
coolify app logs mg8c40oowo80o08o0gsw0gwc --context myapp --follow

# 重启应用
coolify app restart mg8c40oowo80o08o0gsw0gwc --context myapp

# 检查环境变量
coolify app env list mg8c40oowo80o08o0gsw0gwc --context myapp
```

### 4️⃣ 服务无法连接

```bash
# 检查容器是否运行
coolify app status mg8c40oowo80o08o0gsw0gwc --context myapp

# 进入容器调试
coolify app exec mg8c40oowo80o08o0gsw0gwc --context myapp bash

# 容器内检查
curl localhost:8000/health  # 后端
curl localhost:3000         # 前端
supervisorctl status        # Supervisor
```

---

## 🔗 相关文档

| 文档 | 用途 |
|------|------|
| [COOLIFY_DEPLOYMENT_GUIDE.md](./COOLIFY_DEPLOYMENT_GUIDE.md) | 完整部署指南 |
| [STORY_4_4_INTEGRATED_SERVICE_ARCHITECTURE.md](../reference/STORY_4_4_INTEGRATED_SERVICE_ARCHITECTURE.md) | 架构设计 |
| [STORY_4_4_DEPLOYMENT_GUIDE.md](./STORY_4_4_DEPLOYMENT_GUIDE.md) | Docker 部署 |

---

## 📞 快速查询

```bash
# 忘记应用 UUID？
coolify app list --context myapp

# 需要获取日志？
coolify app logs mg8c40oowo80o08o0gsw0gwc --context myapp --tail 50

# 需要重启？
coolify app restart mg8c40oowo80o08o0gsw0gwc --context myapp

# 所有命令帮助
coolify app --help
```

---

## 🎉 就绪！

所有部署配置已完成！

**现在您可以**:

1. ✅ 在 GitHub 配置 3 个 Secrets
2. ✅ 推送代码到 main 分支
3. ✅ 自动构建、推送、部署
4. ✅ 监控应用日志和状态

**预期结果**: 应用在 10-15 分钟内自动更新和启动 🚀

---

**部署准备完成时间**: 2025-11-21 15:50 UTC
**状态**: 🟢 **完全就绪，可立即执行**
