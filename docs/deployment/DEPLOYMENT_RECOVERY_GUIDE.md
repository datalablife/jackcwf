# 🔍 诊断和恢复步骤

## 现状分析

容器仍在 `Restarting (2)` 状态，镜像 hash 是 `f0852b9`（**旧镜像**）。

新提交 `a342503` 的修复应该产生不同的镜像 hash。这意味着：
- ⏳ GitHub Actions 可能还在构建
- ⏳ Coolify 可能还没有拉取最新镜像
- ⏳ 或镜像构建中

---

## 📋 立即行动项

### 步骤 1: 查看容器日志找出具体错误

在你的云服务器上运行：

```bash
# 方法1: 使用诊断脚本
bash /path/to/check-container-logs.sh

# 方法2: 手动查看日志
docker logs $(docker ps -aqf "name=zogcwskg8s0okw4c0wk0kscg") 2>&1 | tail -150
```

**查找以下错误迹象：**
- `ModuleNotFoundError: No module named 'prometheus_client'` → 说明旧镜像没有我们的修复
- `Cannot GET /` → Nginx 问题
- `Connection refused` → 后端未启动
- 其他 Python 导入错误

### 步骤 2: 检查 GitHub Actions 构建状态

访问: https://github.com/datalablife/jackcwf/actions

查找最新的 workflow run (应该是 commit `a342503`)
- 🟡 Yellow = 正在运行
- 🟢 Green = 成功
- 🔴 Red = 失败

如果构建失败，查看构建日志看是什么错误。

### 步骤 3: 检查 Coolify 部署状态

访问: https://coolpanel.jackcwf.com (你的 Coolify 面板)

1. 找到应用 `jackcwf-fastapi` 或 UUID `zogcwskg8s0okw4c0wk0kscg`
2. 查看 "Deployment" 或 "History" 标签
3. 确认最新部署是否使用了新镜像

---

## 🚨 如果还是失败怎么办？

### 可能的原因 1: Prometheus-client 仍未安装

**症状**: 日志包含 `ModuleNotFoundError: No module named 'prometheus_client'`

**原因**: 旧镜像还在运行

**解决**:
```bash
# 1. 等待 GitHub Actions 完成（观察 15-20 分钟）

# 2. 在 Coolify 中手动触发重新部署：
# 进入 Coolify 仪表板 → 应用 → 部署 → "Deploy" 按钮
# 或使用 Coolify CLI:
coolify app restart zogcwskg8s0okw4c0wk0kscg --deployment-pull-request latest

# 3. 或手动重建镜像并推送：
docker build --no-cache -t ghcr.io/datalablife/jackcwf:main-debug .
docker push ghcr.io/datalablife/jackcwf:main-debug
# 然后在 Coolify 中改为手动镜像 URL
```

### 可能的原因 2: 前端 API URL 仍未修复

**症状**: 浏览器加载但所有 API 请求都是 404，Network 标签显示请求到 `https://api.yourdomain.com`

**原因**: 前端是用旧 `.env.production` 编译的

**解决**:
```bash
# 验证 .env.production 在本地已修改
cat frontend/.env.production | grep VITE_API_BASE_URL
# 应该输出: VITE_API_BASE_URL=/api/v1

# 查看 git diff
git diff HEAD~1 frontend/.env.production

# 如果文件被 .gitignore 忽略，强制添加
git add -f frontend/.env.production
git commit --amend --no-edit
git push origin main --force-with-lease
```

### 可能的原因 3: GitHub Actions 工作流失败

**症状**: GitHub Actions dashboard 显示 Red ❌

**调查**:
1. 点击最新的 workflow run
2. 查看 "Logs" 标签
3. 找出哪个 step 失败（Docker build, Push to GHCR, etc.)

**常见错误**:
- `docker build` 失败 → 查看 Dockerfile 语法
- `docker push` 失败 → 检查 GitHub Secrets 中的 `GHCR_TOKEN`
- 测试失败 → 查看测试日志

---

## 📊 完整诊断决策树

```
┌─ 容器状态: Restarting (2)
├─ 查看日志
│  ├─ 包含 prometheus_client 错误
│  │  └─ 原因: 旧镜像还在运行
│  │     └─ 解决: 等待 GitHub Actions 完成 → Coolify 自动部署新镜像
│  │
│  ├─ 包含其他 Python 导入错误
│  │  └─ 原因: 依赖缺失或代码有问题
│  │     └─ 解决: 查看完整日志 → 定位具体错误 → 修复代码 → 提交
│  │
│  ├─ 包含 Nginx 错误 (nginx: ...)
│  │  └─ 原因: Nginx 配置问题
│  │     └─ 解决: 检查 docker/nginx.conf → 运行 nginx -t 验证
│  │
│  └─ 日志空白或没有有用信息
│     └─ 原因: 容器启动极快就崩溃
│        └─ 解决: 进入容器手动运行启动脚本调试
│
└─ 检查 GitHub Actions
   ├─ 🟢 Green (成功)
   │  └─ 等待 Coolify 拉取新镜像 (通常 2-5 分钟)
   │
   └─ 🟡 Yellow (运行中) 或 🔴 Red (失败)
      └─ 查看构建日志 → 修复问题 → 提交新 commit
```

---

## ⏱️ 预期时间表

| 时间 | 事件 | 你需要做什么 |
|------|------|-----------|
| Now | 新 commit 推送完成 | ✅ 完成 |
| +2-3 min | GitHub Actions 开始构建 | 观察 |
| +10-15 min | Docker 镜像构建完成 | 等待 |
| +15-20 min | 镜像推送到 GHCR | 等待 |
| +20-25 min | Coolify 检测到新镜像 | 等待 |
| +25-30 min | 新容器启动 | 监控状态 |
| +30-35 min | Health check 通过 | 应该是 "Running (healthy)" |

---

## 🔗 重要链接

- GitHub Repo: https://github.com/datalablife/jackcwf
- GitHub Actions: https://github.com/datalablife/jackcwf/actions
- GHCR: https://ghcr.io/datalablife/jackcwf
- Coolify Panel: https://coolpanel.jackcwf.com
- Application: https://zogcwskg8s0okw4c0wk0kscg.47.79.87.199.sslip.io

---

## 📝 如果需要立即修复

如果你无法等待 GitHub Actions，可以在服务器上手动处理：

```bash
# 1. 进入项目目录
cd /path/to/jackcwf

# 2. 本地构建新镜像（包含所有修复）
docker build --no-cache -t ghcr.io/datalablife/jackcwf:main-fix-latest .

# 3. 在 Coolify 中改为这个镜像
# 或使用 docker run 测试
docker run -it --env-file .env -p 8080:80 ghcr.io/datalablife/jackcwf:main-fix-latest

# 4. 测试
curl http://localhost:8080/
curl http://localhost:8080/api/v1/health
```

---

**下一步**:
1. ✅ 运行诊断脚本获取容器日志
2. ✅ 检查 GitHub Actions 构建状态
3. ✅ 根据日志内容采取相应行动
