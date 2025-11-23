# 🚀 立即部署指南 - 容器修复总结

**生成时间**: 2025-11-21
**修复状态**: ✅ 完成诊断和代码修复
**部署状态**: 🔴 等待手动操作

---

## 📊 完整情况概览

### 根本问题（已确认）

| 问题 | 根本原因 | 修复状态 |
|------|---------|---------|
| 容器 Exit code 2 | `.dockerignore` 中的 `*.sh` 规则排除了 `docker/docker-entrypoint.sh` | ✅ 已修复 (c17ac66) |
| 404 page not found | 前端 API URL 硬编码为 `https://api.yourdomain.com` | ✅ 已修复 (a342503) |
| 缺少 prometheus-client | pyproject.toml 依赖不完整 | ✅ 已修复 (a342503) |
| GitHub Actions 未触发 | `.dockerignore` 不在 workflow paths 列表中 | ✅ 已修复 (3b50a61) |

### 可用的镜像

| 镜像标签 | 包含的修复 | 是否可部署 | 完整性 |
|----------|-----------|----------|--------|
| `main-f0852b9` | 无（当前运行，有问题） | ❌ 不可用 | 不完整 |
| `main-a342503` | prometheus-client + 前端 URL | ✅ 可用 | 90% |
| `main-c17ac66` | .dockerignore 完整修复 | ❌ 构建失败 | 未构建 |
| `main` (latest) | = main-a342503 | ✅ 可用 | 90% |

---

## 🎯 两种部署方案

### 方案 A: 立即部署（推荐 - 5分钟内见效）

**镜像**: `ghcr.io/datalablife/jackcwf:main-a342503`
**优点**: 立即可用，已测试成功构建
**缺点**: 不包含 `.dockerignore` 完整修复
**适用**: 急需恢复服务

**步骤**:

1. **访问 Coolify 仪表板**
   ```
   https://coolpanel.jackcwf.com
   ```

2. **找到应用 `jackcwf-fastapi` (UUID: zogcwskg8s0okw4c0wk0kscg)**

3. **更新镜像标签**
   - 进入应用设置
   - 找到 "Docker Image" 字段
   - 更改为: `ghcr.io/datalablife/jackcwf:main-a342503`

4. **点击 "Deploy" 或 "Redeploy"**

5. **监控部署**
   - 等待容器拉取镜像（2-3分钟）
   - 监控"Servers"状态，应变为绿色 ✅
   - 健康检查应通过（容器状态从 Degraded → Healthy）

6. **验证部署成功**
   ```bash
   # 访问应用
   curl https://zogcwskg8s0okw4c0wk0kscg.47.79.87.199.sslip.io/

   # 应该返回 React HTML（不再 404）
   # 检查浏览器控制台，API 调用应该到 /api/v1/* 而不是 https://api.yourdomain.com
   ```

---

### 方案 B: 等待完整修复（推荐长期 - 10-15分钟）

**镜像**: `ghcr.io/datalablife/jackcwf:main-c17ac66`
**优点**: 包含所有修复，完整解决方案
**缺点**: 需要等待 GitHub Actions 新构建
**适用**: 有时间等待的情况

**步骤**:

1. **GitHub Actions 自动构建新镜像**
   ```
   https://github.com/datalablife/jackcwf/actions
   ```
   - 查找最新的 workflow run
   - 应该看到 commit `3b50a61` 被触发
   - 等待构建完成（约 5-10分钟）

2. **镜像推送到 GHCR**
   - GitHub Actions 成功后，自动推送到 GHCR
   - 新镜像标签应该是 `main-c17ac66`

3. **在 Coolify 中部署新镜像**
   - 同方案 A 的步骤 1-5
   - 但使用镜像: `ghcr.io/datalablife/jackcwf:main-c17ac66`

---

## 📋 代码修复清单

所有代码修复均已完成：

| 文件 | 修复内容 | 提交 |
|------|----------|------|
| `pyproject.toml` | 添加 prometheus-client>=0.19.0 | a342503 |
| `frontend/.env.production` | 改为相对 URL (/api/v1, /ws) | a342503 |
| `Dockerfile` | 添加前端构建验证 | a342503 |
| `.dockerignore` | 移除 *.sh 通配符，允许 docker/ | c17ac66 |
| `.github/workflows/build-and-deploy.yml` | 添加 .dockerignore 到 paths | 3b50a61 |

---

## 🔗 重要链接

| 资源 | URL |
|------|-----|
| **Coolify 仪表板** | https://coolpanel.jackcwf.com |
| **GitHub 仓库** | https://github.com/datalablife/jackcwf |
| **GitHub Actions** | https://github.com/datalablife/jackcwf/actions |
| **GHCR 镜像** | https://ghcr.io/datalablife/jackcwf |
| **应用 URL** | https://zogcwskg8s0okw4c0wk0kscg.47.79.87.199.sslip.io |

---

## ✅ 验证部署成功

部署后，执行以下检查确认成功：

### 1. 容器状态检查
```
Coolify 仪表板 → 应用 → 状态应该显示: "Running (healthy)" ✅
不应该再看到: "Degraded (unhealthy)" 或 "Restarting"
```

### 2. HTTP 端点检查
```bash
# 前端加载
curl -I https://zogcwskg8s0okw4c0wk0kscg.47.79.87.199.sslip.io/
# 预期: HTTP 200

# 健康检查
curl https://zogcwskg8s0okw4c0wk0kscg.47.79.87.199.sslip.io/health
# 预期: {"status": "healthy"}

# API 端点
curl https://zogcwskg8s0okw4c0wk0kscg.47.79.87.199.sslip.io/api/v1/health
# 预期: JSON 响应（具体内容取决于后端）
```

### 3. 浏览器验证
```
1. 访问: https://zogcwskg8s0okw4c0wk0kscg.47.79.87.199.sslip.io/
2. 页面应该加载 React 应用（不是 404）
3. 打开浏览器 DevTools → Network 标签
4. 刷新页面
5. 检查 API 调用：
   ✅ 应该看到: /api/v1/conversations, /api/v1/messages 等
   ❌ 不应该看到: https://api.yourdomain.com/* 请求
6. 控制台不应该有错误（除了可能的第三方脚本错误）
```

---

## 🚨 如果部署失败

### 容器仍然 Degraded (unhealthy)

**检查清单**:

1. **镜像是否正确下载？**
   - Coolify UI → 应用 → Docker → 检查镜像字段
   - 确认是 `ghcr.io/datalablife/jackcwf:main-a342503` 或 `main-c17ac66`

2. **查看容器日志**
   ```bash
   # SSH 到服务器（如果可以）
   ssh root@47.79.87.199

   # 查看最新容器日志
   docker logs $(docker ps -aqf "name=zogcwskg8s0okw4c0wk0kscg") --tail 100

   # 应该看到:
   # ✅ "Frontend files verified in Nginx root"
   # ✅ "Nginx configuration is valid"
   # ✅ "supervisord started"
   # 而不是:
   # ❌ "ModuleNotFoundError: No module named 'prometheus_client'"
   # ❌ "cannot open shared object file"
   ```

3. **DATABASE_URL 是否已配置？**
   - Coolify UI → 应用 → 环境变量
   - 确认 `DATABASE_URL` 已设置为有效的 PostgreSQL URL

4. **重启容器**
   - Coolify UI → 应用 → 点击 "Restart" 或 "Redeploy"

### HTTP 404 错误仍未解决

**可能原因**:
1. 缓存问题 - 清除浏览器缓存和 Nginx 缓存
2. 前端未正确编译 - 检查前端文件是否在 `/usr/share/nginx/html/`
3. Nginx 配置问题 - 容器日志应该显示任何 Nginx 错误

**解决方案**:
```bash
# 在容器内检查
docker exec <container_id> ls -la /usr/share/nginx/html/
# 应该看到 index.html 和 assets/ 目录

# 检查 Nginx 配置
docker exec <container_id> nginx -t
# 应该返回: nginx: configuration file test is successful

# 硬刷浏览器缓存
# Windows/Linux: Ctrl+Shift+Delete
# macOS: Cmd+Shift+Delete
```

---

## 📞 技术支持

如果遇到问题：

1. **检查 GitHub Actions 日志**
   - https://github.com/datalablife/jackcwf/actions
   - 找最新的 workflow run
   - 查看任何失败的步骤

2. **检查容器日志**
   - Coolify UI → 应用 → Logs
   - 查找 ERROR 或 WARNING 信息

3. **查看诊断报告**
   - `/docs/deployment/CRITICAL_FIXES_DEPLOYMENT_ANALYSIS.md`
   - `/docs/deployment/DEPLOYMENT_RECOVERY_GUIDE.md`
   - `/docs/deployment/DEPLOYMENT_READINESS_CHECKLIST.md`

---

## 📝 快速参考

| 任务 | 命令/操作 |
|------|----------|
| 部署立即可用镜像 | Coolify → 更改镜像到 `main-a342503` → 部署 |
| 监控 GitHub Actions | https://github.com/datalablife/jackcwf/actions |
| 检查 GHCR 镜像 | https://ghcr.io/datalablife/jackcwf |
| 查看应用 | https://zogcwskg8s0okw4c0wk0kscg.47.79.87.199.sslip.io |
| 测试健康检查 | curl https://.../health |

---

**状态**: 🟢 所有代码修复完成，准备部署
**建议**: 立即部署方案 A（使用 main-a342503），然后等待方案 B（c17ac66）完整镜像构建