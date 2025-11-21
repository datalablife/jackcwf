# Story 4.4 - Coolify 部署实施指南

**日期**: 2025-11-21
**状态**: ✅ **准备部署**

---

## 📋 部署概览

使用 **Coolify CLI** + **GitHub Actions** 的云端部署方案：

```
GitHub (代码推送)
    ↓
GitHub Actions (自动构建)
    ↓
GHCR (镜像仓库)
    ↓
Coolify CLI (应用部署)
    ↓
Coolify (生产环境运行)
```

---

## 🔧 前置条件

✅ **Coolify CLI** - 已安装在本地 WSL
✅ **Coolify 上下文** - 已配置 (myapp)
✅ **现有应用** - UUID: `mg8c40oowo80o08o0gsw0gwc`
✅ **GitHub 仓库** - feature/epic4-hybrid-frontend 分支已推送

---

## 📝 Step 1: 配置 GitHub Secrets

在 GitHub 仓库设置中添加以下 Secrets:

### 1.1 获取 Coolify API Token

1. 访问: https://coolpanel.jackcwf.com
2. 登录账号
3. 导航到: **Account Settings** → **API Tokens**
4. 创建新 Token，复制内容

### 1.2 添加 GitHub Secrets

进入 GitHub 仓库 → **Settings** → **Secrets and variables** → **Actions**

添加以下 Secrets:

| Secret 名称 | 值 | 说明 |
|-----------|-----|------|
| `COOLIFY_API_TOKEN` | (从 Coolify 获取) | API 认证 Token |
| `COOLIFY_FQDN` | `https://coolpanel.jackcwf.com` | Coolify 面板地址 |
| `COOLIFY_APP_UUID` | `mg8c40oowo80o08o0gsw0gwc` | 应用 UUID |

### 1.3 验证 Secrets

```bash
# 在 GitHub Actions 中会自动读取这些 Secrets
# 不需要本地验证
```

---

## 🚀 Step 2: 部署流程

### 方案 A: 通过 GitHub Actions 自动部署 (推荐)

**触发条件**:
- 推送到 `main` 分支
- 推送到 `feature/epic4-hybrid-frontend` 分支
- 手动触发 (workflow_dispatch)

**工作流步骤**:
1. 检出代码
2. 设置 Docker Buildx
3. 登录 GHCR
4. 构建并推送镜像到 GHCR
5. 调用 Coolify API 触发部署

**执行方式**:
```bash
# 推送代码到 main 分支触发自动部署
git push origin main

# 或手动触发 (在 GitHub Actions 页面)
```

### 方案 B: 使用 Coolify CLI 手动部署

**如果需要立即部署到现有应用**:

```bash
# 1. 获取最新的 Git commit SHA
COMMIT_SHA=$(git rev-parse --short HEAD)

# 2. 更新应用镜像
coolify app update mg8c40oowo80o08o0gsw0gwc \
  --context myapp \
  --image ghcr.io/datalablife/jackcwf:main-$COMMIT_SHA \
  --git-branch main

# 3. 查看应用状态
coolify app status mg8c40oowo80o08o0gsw0gwc --context myapp

# 4. 查看应用日志
coolify app logs mg8c40oowo80o08o0gsw0gwc --context myapp --follow
```

---

## 📊 Step 3: 镜像构建说明

### 镜像结构 (Dockerfile)

```dockerfile
Stage 1: backend-builder
  └─ Python 3.12 + 依赖编译

Stage 2: frontend-builder
  └─ Node.js 20 + React 构建

Stage 3: production
  └─ Python 3.12 + Supervisor
     ├─ Backend (FastAPI, 8000)
     ├─ Frontend (Nginx, 3000)
     └─ HealthMonitor (Python)
```

### 镜像信息

| 属性 | 值 |
|------|-----|
| **Registry** | ghcr.io (GitHub Container Registry) |
| **Repository** | datalablife/jackcwf |
| **Tag** | main-{commit_sha} / latest |
| **Build Context** | . (项目根目录) |
| **Dockerfile** | ./Dockerfile |

---

## ✅ Step 4: 部署验证

### 4.1 检查镜像推送

```bash
# 验证镜像已推送到 GHCR
curl -H "Authorization: token $(gh auth token)" \
  https://ghcr.io/v2/datalablife/jackcwf/tags/list
```

### 4.2 检查应用部署

```bash
# 查看应用状态
coolify app status mg8c40oowo80o08o0gsw0gwc --context myapp

# 查看应用日志 (实时)
coolify app logs mg8c40oowo80o08o0gsw0gwc --context myapp --follow

# 查看环境变量
coolify app env list mg8c40oowo80o08o0gsw0gwc --context myapp
```

### 4.3 HTTP 验证

```bash
# 检查后端健康状态
curl http://mg8c40oowo80o08o0gsw0gwc.47.79.87.199.sslip.io/health

# 检查前端可访问性
curl http://mg8c40oowo80o08o0gsw0gwc.47.79.87.199.sslip.io

# 检查 API 响应
curl http://mg8c40oowo80o08o0gsw0gwc.47.79.87.199.sslip.io/api/conversations
```

---

## 🔄 Step 5: 部署后的配置

### 5.1 环境变量配置

在 Coolify 应用中配置以下环境变量:

```bash
# 数据库
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...

# Webhook (可选)
ALERT_WEBHOOK_URL=https://hooks.slack.com/...
```

**配置方式**:
```bash
coolify app env set mg8c40oowo80o08o0gsw0gwc \
  --context myapp \
  --key DATABASE_URL \
  --value "postgresql://..."
```

### 5.2 健康检查配置

Coolify 自动配置的健康检查:
- **端点**: `http://localhost:8000/health`
- **间隔**: 30 秒
- **超时**: 10 秒
- **启动延迟**: 60 秒
- **重试次数**: 3 次

### 5.3 重启策略

- **策略**: unless-stopped
- **自动重启**: 启用
- **最大尝试**: 3 次

---

## 🆘 故障排查

### 问题 1: 镜像推送失败

```bash
# 检查 GHCR 认证
docker login ghcr.io

# 使用 GitHub Token
echo $CR_PAT | docker login ghcr.io -u USERNAME --password-stdin

# 查看 GitHub Actions 日志
gh run list --limit 5
gh run view <run-id>
```

### 问题 2: 应用部署失败

```bash
# 查看 Coolify 应用日志
coolify app logs mg8c40oowo80o08o0gsw0gwc --context myapp --follow

# 检查应用配置
coolify app get mg8c40oowo80o08o0gsw0gwc --context myapp

# 重启应用
coolify app restart mg8c40oowo80o08o0gsw0gwc --context myapp
```

### 问题 3: 服务无法连接

```bash
# 进入容器调试
coolify app exec mg8c40oowo80o08o0gsw0gwc --context myapp bash

# 容器内验证
curl localhost:8000/health
curl localhost:3000

# 查看 Supervisor 状态
supervisorctl status
```

---

## 📈 监控和维护

### 实时监控

```bash
# 持续查看日志 (30 秒更新一次)
watch -n 30 'coolify app logs mg8c40oowo80o08o0gsw0gwc --context myapp --tail 20'

# 监控应用状态
watch -n 10 'coolify app status mg8c40oowo80o08o0gsw0gwc --context myapp'
```

### 自动化扩展

如果需要多副本部署:
```bash
coolify app update mg8c40oowo80o08o0gsw0gwc \
  --context myapp \
  --replicas 2
```

---

## 📋 部署检查清单

### 前置检查
- [ ] Coolify CLI 已安装并配置
- [ ] GitHub Secrets 已配置
- [ ] 代码已推送到 GitHub
- [ ] Dockerfile 已验证

### 部署步骤
- [ ] GitHub Actions 工作流已运行
- [ ] 镜像已成功推送到 GHCR
- [ ] Coolify 应用已收到部署请求
- [ ] 容器已启动并通过健康检查

### 验证步骤
- [ ] 应用健康端点 (`/health`) 返回 200
- [ ] 前端可访问 (响应 200)
- [ ] 监控脚本运行正常
- [ ] 日志输出正常

### 后续配置
- [ ] 环境变量已配置
- [ ] 告警 Webhook 已配置 (可选)
- [ ] 数据库连接已验证
- [ ] API Keys 已添加

---

## 🎯 下一步

1. **配置 GitHub Secrets** (5 分钟)
   ```bash
   # 在 GitHub UI 中进行
   ```

2. **触发首次部署** (2-3 分钟)
   ```bash
   git push origin main
   ```

3. **监控部署过程** (进行中)
   ```bash
   coolify app logs mg8c40oowo80o08o0gsw0gwc --context myapp --follow
   ```

4. **验证应用** (5 分钟)
   ```bash
   curl http://mg8c40oowo80o08o0gsw0gwc.47.79.87.199.sslip.io/health
   ```

---

## 📞 技术支持

| 组件 | 命令 | 说明 |
|------|------|------|
| Coolify CLI | `coolify --help` | 通用帮助 |
| 应用列表 | `coolify app list --context myapp` | 查看所有应用 |
| 应用日志 | `coolify app logs <uuid> --context myapp` | 实时日志 |
| 应用重启 | `coolify app restart <uuid> --context myapp` | 重启应用 |
| 应用停止 | `coolify app stop <uuid> --context myapp` | 停止应用 |
| 应用启动 | `coolify app start <uuid> --context myapp` | 启动应用 |

---

**准备完成日期**: 2025-11-21
**预计部署时间**: 5-10 分钟
**状态**: 🟢 **就绪，等待执行**
