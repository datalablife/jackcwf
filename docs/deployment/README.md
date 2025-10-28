# 部署指南

欢迎来到部署指南！本目录包含所有与应用部署相关的文档。

## 📚 指南导航

### 🔄 CI/CD 自动化部署

- **[Quick Start Guide (English)](./QUICK_START.md)** - 10分钟快速启动指南
- **[Complete CI/CD Guide (English)](./ci-cd.md)** - 完整的CI/CD文档
  - GitHub Actions 工作流
  - 多环境部署策略
  - 安全扫描和监控
  - 故障排除和最佳实践

### 🌐 Coolify 部署

- [Coolify Git 集成指南](./COOLIFY_GIT_INTEGRATION.md) - 使用 Coolify CLI 进行 Git 仓库管理和自动部署
  - GitHub App 配置
  - Coolify Web UI 设置
  - Coolify CLI 命令
  - 自动部署工作流
  - 故障排除指南

### 📦 Docker 部署

- [Docker 部署指南](./docker-deployment.md) - Docker 容器化和部署（编写中）

### 🔧 环境配置

- [生产环境配置](./production-config.md) - 生产环境配置和最佳实践（编写中）

---

## 🎯 按任务查找指南

### 我想...

#### CI/CD 自动化
- **快速设置 CI/CD** → [Quick Start (10 min)](./QUICK_START.md)
- **详细了解 CI/CD 系统** → [Complete Guide](./ci-cd.md)
- **配置 GitHub Actions** → [CI/CD Setup](./ci-cd.md#setup-instructions)
- **部署到生产环境** → [Deployment Process](./ci-cd.md#deployment-process)
- **排查 CI/CD 问题** → [Troubleshooting](./ci-cd.md#troubleshooting)

#### Coolify 部署
- **部署到 Coolify 服务器** → [Coolify Git 集成指南](./COOLIFY_GIT_INTEGRATION.md)
- **学习 Git 与部署集成** → [Coolify Git 集成指南](./COOLIFY_GIT_INTEGRATION.md#概览)
- **配置自动部署** → [Coolify Git 集成指南](./COOLIFY_GIT_INTEGRATION.md#部署流程)
- **使用 Coolify CLI** → [Coolify Git 集成指南](./COOLIFY_GIT_INTEGRATION.md#coolify-cli-配置)
- **设置 GitHub App** → [Coolify Git 集成指南](./COOLIFY_GIT_INTEGRATION.md#coolify-web-ui-配置)
- **排查部署问题** → [Coolify Git 集成指南](./COOLIFY_GIT_INTEGRATION.md#故障排除)

---

## 📖 快速参考

### CI/CD Pipeline - 快速开始

```bash
# 1. 配置 GitHub Secrets
./scripts/ci/setup-secrets.sh

# 2. 推送代码触发 CI
git push origin main

# 3. 查看工作流
# GitHub → Actions 标签

# 4. 手动部署到生产环境
# GitHub → Actions → CD workflow → Run workflow
```

### Coolify Git 集成 - 3 步快速开始

```bash
# 1. 创建 GitHub 集成
coolify github create \
  --name "My GitHub" \
  --api-url "https://api.github.com" \
  --html-url "https://github.com" \
  --app-id <APP_ID> \
  --installation-id <INSTALLATION_ID> \
  --client-id <CLIENT_ID> \
  --client-secret <CLIENT_SECRET> \
  --private-key-uuid <KEY_UUID>

# 2. 配置应用 Git 源
coolify app update <APP_UUID> \
  --git-repository "https://github.com/yourname/working.git" \
  --git-branch "main"

# 3. 部署应用
coolify deploy uuid <APP_UUID>
```

### 常用命令速查

#### CI/CD 命令
```bash
# 健康检查
./scripts/deploy/health-check.sh https://jackcwf.com

# 烟雾测试
./scripts/deploy/smoke-tests.sh https://jackcwf.com

# 回滚部署
./scripts/deploy/rollback.sh production

# 创建备份
./scripts/deploy/backup.sh production

# 监控指标
./scripts/deploy/monitor-metrics.sh https://jackcwf.com
```

#### Coolify 命令
```bash
# 列出所有应用
coolify app list

# 部署应用
coolify deploy name "App Name"

# 查看应用日志
coolify app logs <app-uuid>

# 查看部署状态
coolify deploy list
```

---

## 🚀 完整部署流程

### 方案 1: CI/CD 自动化部署 (推荐)

#### 第一次设置 (10分钟)

1. **准备 Coolify 凭证**
   - 获取 API Token 和应用 UUIDs
   - 参考: [Quick Start](./QUICK_START.md#step-1-get-coolify-credentials-2-min)

2. **配置 GitHub**
   - 设置 Repository Secrets
   - 创建 Environments (dev, staging, prod)
   - 参考: [Quick Start](./QUICK_START.md#step-2-configure-github-secrets-3-min)

3. **启用 GitHub Actions**
   - 配置工作流权限
   - 设置分支保护
   - 参考: [Quick Start](./QUICK_START.md#step-3-enable-github-actions-1-min)

4. **测试流水线**
   ```bash
   git push origin main
   # 自动触发 CI/CD
   ```

#### 日常开发流程

```bash
# 1. 创建功能分支
git checkout -b feature/my-feature

# 2. 开发和提交
git add .
git commit -m "feat: add new feature"
git push origin feature/my-feature

# 3. 创建 Pull Request
# → Pre-commit checks 自动运行

# 4. 合并到 develop
# → 自动部署到 Development 环境

# 5. 合并到 main
# → 自动部署到 Staging 环境
# → 手动批准后部署到 Production
```

### 方案 2: 传统 Coolify 部署

#### 第一次部署

1. **准备工作** (在本地完成)
   - ✅ Git 仓库已初始化
   - ✅ 代码已提交到 GitHub
   - ✅ Coolify 服务器已部署

2. **配置 GitHub** (在 GitHub 平台)
   - 创建 GitHub App 或 OAuth App
   - 获取必要的凭证

3. **配置 Coolify** (在 Coolify Web UI 或 CLI)
   - 添加 GitHub 集成
   - 创建应用并配置 Git 源
   - 配置构建和启动命令

4. **部署应用** (通过 CLI 或 Web UI)
   - 触发初次部署
   - 查看日志和确认部署成功

5. **验证部署**
   - 访问应用 URL
   - 检查日志和监控

#### 后续更新

1. 本地开发和提交
   ```bash
   git commit -m "Feature: ..."
   git push origin main
   ```

2. 触发部署
   ```bash
   coolify deploy name "App Name"
   ```

3. 验证更新
   ```bash
   coolify app logs <app-uuid>
   ```

---

## 📊 部署架构

### CI/CD 架构

```
开发者本地
    ↓
GitHub 仓库
    ↓
GitHub Actions (CI/CD)
    ├─→ CI Pipeline (测试、构建、质量检查)
    └─→ CD Pipeline (部署)
        ├─→ Development (自动)
        ├─→ Staging (自动)
        └─→ Production (手动批准)
            ↓
        Coolify 服务器
            ↓
        Docker 容器
            ↓
        云服务器上的应用
```

### 传统 Coolify 架构

```
GitHub 仓库
    ↓
Coolify GitHub 集成
    ↓
Coolify 服务器
    ↓
Docker 容器
    ↓
云服务器上的应用
```

---

## ⚙️ 关键配置项

### CI/CD 环境

| 环境 | URL | 部署方式 | 用途 |
|-----|-----|---------|------|
| **Development** | https://dev.jackcwf.com | 自动 | 开发测试 |
| **Staging** | https://staging.jackcwf.com | 自动 | 预生产验证 |
| **Production** | https://jackcwf.com | 手动批准 | 生产环境 |

### 应用配置

| 配置项 | 说明 | 示例 |
|-------|------|------|
| **Git Repository** | 仓库 URL | `https://github.com/datalablife/jackcwf.git` |
| **Git Branch** | 部署分支 | `main`, `develop`, `staging` |
| **Base Directory** | 项目根目录 | `.` |
| **Install Command** | 依赖安装 | `uv sync` |
| **Build Command** | 构建命令 | `uv run reflex build` |
| **Start Command** | 启动命令 | `uv run reflex run` |

### 环境变量

```bash
# 在 Coolify Web UI 或 GitHub Secrets 中设置
REFLEX_ENV_MODE=prod
DATABASE_URL=postgresql://...
API_KEY=...
COOLIFY_API_TOKEN=...
```

---

## 🔒 安全最佳实践

### CI/CD 安全
- ✅ 使用 GitHub Secrets 存储敏感信息
- ✅ 启用分支保护和代码审查
- ✅ 运行安全扫描 (Dependabot, CodeQL, Trivy)
- ✅ 启用生产环境部署审批
- ✅ 定期审查和轮换凭证

### Coolify 安全
- ✅ 使用强 Secret Key
- ✅ 定期轮换凭证
- ✅ 限制 GitHub App 权限
- ✅ 使用环境变量存储敏感信息
- ✅ 启用二次验证
- ✅ 监控部署日志

---

## 🆘 需要帮助？

### CI/CD 问题
1. **设置问题** → 查看 [Quick Start](./QUICK_START.md)
2. **工作流失败** → 查看 [Troubleshooting](./ci-cd.md#troubleshooting)
3. **部署失败** → 检查 GitHub Actions 日志
4. **回滚需求** → 运行 `./scripts/deploy/rollback.sh production`

### Coolify 问题
1. **连接问题** → 查看 [Coolify Git 集成 - 故障排除](./COOLIFY_GIT_INTEGRATION.md#故障排除)
2. **部署失败** → 查看应用日志 `coolify app logs <uuid>`
3. **配置问题** → 查看 [Coolify CLI 管理规则](../../CLAUDE.md#coolify-cli-管理规则)
4. **其他问题** → 查看 [Coolify 官方文档](https://coolify.io/docs)

---

## 📚 相关文档

### CI/CD 文档
- [Quick Start Guide](./QUICK_START.md) - 10分钟快速启动
- [Complete CI/CD Guide](./ci-cd.md) - 完整的CI/CD指南
- [GitHub Actions 文档](https://docs.github.com/en/actions)

### Coolify 文档
- [Coolify Git 集成指南](./COOLIFY_GIT_INTEGRATION.md) - 详细指南
- [Coolify CLI 规则](../../CLAUDE.md#coolify-cli-管理规则) - CLI 使用
- [Coolify 官方文档](https://coolify.io/docs)

### 项目文档
- [项目指导 - CLAUDE.md](../../CLAUDE.md) - 项目配置
- [项目指导 - Reflex](../../CLAUDE.md#reflex-全栈应用开发规则) - Reflex 开发
- [开发者指南](../guides/developer/) - 本地开发指南

---

## 🎓 学习资源

### 外部资源
- [Reflex Documentation](https://reflex.dev/docs)
- [uv Documentation](https://docs.astral.sh/uv/)
- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

**最后更新**: 2025-10-28
**版本**: 2.0.0
**维护者**: DevOps 团队

有问题或建议？请在 GitHub 上创建 Issue 或联系维护团队。
