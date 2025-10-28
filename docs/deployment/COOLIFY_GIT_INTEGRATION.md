# Coolify 与 Git 仓库集成指南

本指南介绍如何使用 Coolify CLI 和 Coolify Web 面板来集成 Git 仓库，实现自动化部署。

---

## 📋 目录

1. [概览](#概览)
2. [架构说明](#架构说明)
3. [前置准备](#前置准备)
4. [Coolify Web UI 配置](#coolify-web-ui-配置)
5. [Coolify CLI 配置](#coolify-cli-配置)
6. [Git 仓库配置](#git-仓库配置)
7. [部署流程](#部署流程)
8. [常用命令](#常用命令)
9. [故障排除](#故障排除)

---

## 概览

### 什么是 Coolify Git 集成？

Coolify 支持将应用程序与 Git 仓库关联，实现：
- **自动部署**: 代码推送到仓库时自动部署
- **多分支部署**: 不同分支部署到不同环境
- **Pull Request 预览**: 为每个 PR 创建临时部署
- **版本控制**: 完整的部署历史和回滚能力

### 支持的 Git 平台

| 平台 | 支持 | 说明 |
|------|------|------|
| **GitHub** | ✅ | 官方支持，推荐使用 |
| **GitLab** | ✅ | 支持公开和私有仓库 |
| **Gitea** | ✅ | 自托管 Git 服务 |
| **Bitbucket** | ✅ | 支持公开仓库 |

---

## 架构说明

### Coolify Git 集成工作流

```
┌─────────────────────────────────────────────────────────┐
│                    您的 Git 仓库                          │
│                  (GitHub/GitLab/Gitea)                   │
└─────────────────────────────────────────────────────────┘
                           ↓
                    (Push to repository)
                           ↓
┌─────────────────────────────────────────────────────────┐
│                 Coolify Web UI / CLI                      │
│          (配置 Git 连接和应用部署规则)                    │
└─────────────────────────────────────────────────────────┘
                           ↓
                   (Webhook 触发 / 手动部署)
                           ↓
┌─────────────────────────────────────────────────────────┐
│              Coolify 服务器                              │
│        (Clone 仓库 → Build → Deploy)                    │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│          云服务器上的应用 (Docker 容器)                   │
└─────────────────────────────────────────────────────────┘
```

### 三个关键组件

1. **GitHub App** (或其他 Git 平台应用)
   - 在 Git 平台创建应用，授权 Coolify 访问
   - 生成必要的凭证和密钥

2. **Coolify GitHub 集成**
   - 在 Coolify 中配置 Git 平台连接
   - 存储和管理 Git 平台凭证

3. **应用配置**
   - 在 Coolify 中创建应用，关联 Git 仓库
   - 配置构建和部署规则

---

## 前置准备

### 1. 项目 Git 仓库

- ✅ Git 仓库已初始化
- ✅ 项目包含 Dockerfile（如需要）或自动检测的项目类型
- ✅ `.gitignore` 已配置（已完成）

### 2. Coolify 服务器

- ✅ Coolify 已部署到云服务器
- ✅ Coolify CLI 已配置（已完成）
- ✅ 至少有一个项目和服务器资源

### 3. Git 平台帐户

以 GitHub 为例，需要：
- ✅ GitHub 帐户（https://github.com）
- ✅ 访问令牌或应用权限
- ✅ 仓库读写权限

---

## Coolify Web UI 配置

### 步骤 1: 创建 GitHub App (GitHub 平台)

首先在 GitHub 创建一个 OAuth App 或 GitHub App：

#### 方式 A: GitHub App（推荐）

1. 访问 GitHub 设置：https://github.com/settings/apps

2. 点击 **New GitHub App**

3. 填写应用信息：
   ```
   App name: Coolify Deployment
   Homepage URL: https://coolify.jackcwf.com
   Authorization callback URL: https://coolify.jackcwf.com/integrations/github/callback
   ```

4. 选择权限：
   - Repository permissions:
     - Contents: Read & write
     - Workflows: Read & write
     - Checks: Read & write
   - Organization permissions:
     - Members: Read-only

5. 选择事件：
   - Push
   - Pull request
   - Release

6. 点击 **Create GitHub App**

7. 获取必要信息：
   - App ID (从应用页面)
   - Client ID (从 General 标签)
   - Client Secret (生成新的)
   - Installation ID (安装应用后)
   - Private Key (生成 PEM 格式)

#### 方式 B: OAuth App

1. 访问 GitHub 设置：https://github.com/settings/developers

2. 点击 **New OAuth App**

3. 填写信息：
   ```
   Application name: Coolify
   Homepage URL: https://coolify.jackcwf.com
   Authorization callback URL: https://coolify.jackcwf.com/integrations/github/callback
   ```

4. 获取 Client ID 和 Client Secret

### 步骤 2: 在 Coolify Web UI 中配置 GitHub

1. 访问 Coolify Web UI: https://coolpanel.jackcwf.com

2. 进入 **Settings** → **Git** （或搜索 GitHub 集成）

3. 点击 **Add GitHub Integration**

4. 填写信息：
   ```
   Name: GitHub Account (或自定义名称)
   API URL: https://api.github.com
   HTML URL: https://github.com
   App ID: [从 GitHub 获取]
   Installation ID: [从 GitHub 获取]
   Client ID: [从 GitHub 获取]
   Client Secret: [从 GitHub 获取]
   Private Key: [PEM 格式密钥]
   ```

5. 点击 **Save**

6. Coolify 会验证连接

### 步骤 3: 创建应用和配置 Git

1. 进入 **Projects** → 选择项目

2. 点击 **Create Application**

3. 选择应用类型：**Docker** 或 **Node.js** 等

4. 在 **Deployment** 选项卡中：
   - **Source**: 选择 **Git**
   - **Git Repository**: 选择已配置的 GitHub 集成
   - **Repository**: 选择你的仓库 (例如 `yourname/working`)
   - **Branch**: 选择分支 (例如 `main` 或 `dev`)
   - **Base Directory**: 仓库根目录 (通常为 `.`)

5. 配置构建规则：
   - **Dockerfile**: 自动检测或自定义路径
   - **Install Command**: `uv sync`
   - **Build Command**: `uv run reflex build` (如需要)
   - **Start Command**: `uv run reflex run` 或自定义

6. 配置端口和域名

7. 点击 **Deploy**

---

## Coolify CLI 配置

### 步骤 1: 创建 GitHub 集成 (CLI)

使用 CLI 创建 GitHub 集成：

```bash
# 首先生成或获取 Private Key
# 查看已有的私钥
coolify private-key list

# 或创建新的私钥
coolify private-key create --name "github-key"

# 记下返回的 UUID，将在下面使用
```

**获取 Private Key UUID 后，创建 GitHub 集成：**

```bash
coolify github create \
  --name "My GitHub" \
  --api-url "https://api.github.com" \
  --html-url "https://github.com" \
  --app-id 123456 \
  --installation-id 789012 \
  --client-id "Iv1.abc123..." \
  --client-secret "gho_xxxxx..." \
  --private-key-uuid "abc-def-123-456"
```

### 步骤 2: 验证 GitHub 集成

```bash
# 列出所有 GitHub 集成
coolify github list

# 获取特定集成的详情
coolify github get <uuid>

# 列出该集成可访问的仓库
coolify github repos <uuid>

# 列出仓库的分支
coolify github branches <uuid> --repository "yourname/working"
```

### 步骤 3: 配置应用 Git 源

使用 CLI 配置应用的 Git 源：

```bash
# 更新应用配置，设置 Git 仓库
coolify app update <app-uuid> \
  --git-repository "https://github.com/yourname/working.git" \
  --git-branch "main" \
  --base-directory "."

# 或使用应用名称
coolify app update <app-uuid> \
  --name "My Reflex App" \
  --start-command "uv run reflex run" \
  --build-command "uv sync"
```

### 步骤 4: 部署应用

```bash
# 通过应用名称部署
coolify deploy name "My Reflex App"

# 通过 UUID 部署
coolify deploy uuid <app-uuid>

# 部署多个应用
coolify deploy batch "App1" "App2" "App3"

# 查看部署状态
coolify deploy list

# 获取特定部署的详情
coolify deploy get <deployment-uuid>
```

---

## Git 仓库配置

### 步骤 1: 初始化 Git 仓库

```bash
# 如果还未初始化
git init
git remote add origin https://github.com/yourname/working.git
```

### 步骤 2: 提交代码

```bash
# 添加所有文件（遵守 .gitignore）
git add .

# 提交
git commit -m "Initial commit: project setup and configuration"

# 推送到远程仓库
git push -u origin main
```

### 步骤 3: 配置 Webhook (可选，自动部署)

在 GitHub 中配置 Webhook，使推送时自动触发部署：

1. 进入仓库设置：https://github.com/yourname/working/settings/hooks

2. 点击 **Add webhook**

3. 填写 Payload URL：
   ```
   https://coolify.jackcwf.com/api/webhooks/github
   ```

4. 选择事件：**Push events** 和 **Pull request events**

5. 点击 **Add webhook**

---

## 部署流程

### 手动部署流程

```bash
# 1. 本地开发
git commit -m "Feature: add new feature"

# 2. 推送代码
git push origin main

# 3. 通过 CLI 触发部署
coolify deploy name "My Reflex App"

# 4. 查看部署日志
coolify app logs <app-uuid>

# 5. 验证部署结果
# 访问应用 URL 或检查应用状态
coolify app get <app-uuid>
```

### 自动部署流程（使用 Webhook）

```
1. 本地推送代码
   git push origin main
   ↓
2. GitHub 触发 Webhook
   ↓
3. Coolify 接收 Webhook 通知
   ↓
4. Coolify 自动部署应用
   ↓
5. 应用更新完成
```

---

## 常用命令

### GitHub 集成管理

```bash
# 列出所有 GitHub 集成
coolify github list

# 创建新的 GitHub 集成
coolify github create \
  --name "GitHub Account" \
  --api-url "https://api.github.com" \
  --html-url "https://github.com" \
  --app-id 123456 \
  --installation-id 789012 \
  --client-id "..." \
  --client-secret "..." \
  --private-key-uuid "..."

# 获取集成详情
coolify github get <uuid>

# 更新集成
coolify github update <uuid> --name "New Name"

# 删除集成
coolify github delete <uuid>

# 列出集成可访问的仓库
coolify github repos <uuid>

# 列出仓库的分支
coolify github branches <uuid> --repository "owner/repo"
```

### 应用管理

```bash
# 列出所有应用
coolify app list

# 获取应用详情
coolify app get <app-uuid>

# 创建应用
coolify app create --name "My App" --project <project-uuid> --server <server-uuid>

# 更新应用配置
coolify app update <app-uuid> \
  --git-repository "https://github.com/..." \
  --git-branch "main" \
  --start-command "uv run reflex run"

# 获取应用日志
coolify app logs <app-uuid>

# 重启应用
coolify app restart <app-uuid>

# 停止应用
coolify app stop <app-uuid>

# 启动应用
coolify app start <app-uuid>

# 删除应用
coolify app delete <app-uuid>
```

### 部署管理

```bash
# 列出所有部署
coolify deploy list

# 获取部署详情
coolify deploy get <deployment-uuid>

# 通过应用名称部署
coolify deploy name "App Name"

# 通过 UUID 部署
coolify deploy uuid <app-uuid>

# 部署多个应用
coolify deploy batch "App1" "App2" "App3"

# 查看部署日志
coolify deploy list | grep <app-name>

# 取消部署
coolify deploy cancel <deployment-uuid>
```

### 私钥管理

```bash
# 列出所有私钥
coolify private-key list

# 创建新私钥
coolify private-key create --name "github-key"

# 获取私钥详情
coolify private-key get <uuid>

# 删除私钥
coolify private-key delete <uuid>
```

---

## 故障排除

### 问题 1: GitHub 连接失败

**症状**: "Authentication failed" 或 "Invalid credentials"

**解决方案**:
1. 验证 GitHub App ID 和 Client Secret 是否正确
2. 检查 Private Key 是否是有效的 PEM 格式
3. 验证 Installation ID 是否正确
4. 重新生成 Client Secret 和 Private Key

```bash
# 测试连接
coolify github get <uuid>
```

### 问题 2: 仓库无法访问

**症状**: "Repository not found" 或 "Access denied"

**解决方案**:
1. 检查仓库 URL 是否正确
2. 验证 GitHub App 是否已安装到仓库
3. 检查 GitHub App 权限是否足够

```bash
# 列出可访问的仓库
coolify github repos <github-uuid>

# 列出仓库分支
coolify github branches <github-uuid> --repository "owner/repo"
```

### 问题 3: 部署失败

**症状**: 部署开始但未完成，应用无法启动

**解决方案**:
1. 检查应用日志以查找具体错误
2. 验证构建命令是否正确
3. 检查启动命令和依赖项

```bash
# 查看应用日志
coolify app logs <app-uuid>

# 查看部署日志
coolify deploy get <deployment-uuid>

# 重启应用
coolify app restart <app-uuid>
```

### 问题 4: Webhook 不工作

**症状**: 推送代码但没有自动部署

**解决方案**:
1. 验证 Webhook URL 是否正确
2. 检查 GitHub Webhook 日志：Repository → Settings → Webhooks
3. 验证 Coolify 服务器是否可从 GitHub 访问
4. 检查防火墙规则

```bash
# 手动触发部署
coolify deploy name "App Name"
```

### 问题 5: 应用启动失败

**症状**: 部署成功但应用无法启动或立即崩溃

**解决方案**:
1. 检查应用日志
2. 验证启动命令和依赖项
3. 检查端口配置
4. 验证环境变量是否正确

```bash
# 检查应用配置
coolify app get <app-uuid>

# 查看详细日志
coolify app logs <app-uuid>

# 更新启动命令
coolify app update <app-uuid> --start-command "uv run reflex run"
```

---

## 完整工作流示例

### 场景: 部署 Reflex 应用

**第一次部署**:

```bash
# 1. 创建 GitHub 集成
coolify github create \
  --name "GitHub Account" \
  --api-url "https://api.github.com" \
  --html-url "https://github.com" \
  --app-id 123456 \
  --installation-id 789012 \
  --client-id "Iv1.abc123..." \
  --client-secret "gho_xxxxx..." \
  --private-key-uuid "abc-def-123-456"

# 2. 验证连接
coolify github repos <github-uuid>

# 3. 创建应用
coolify app create \
  --name "Reflex App" \
  --project <project-uuid> \
  --server <server-uuid>

# 4. 配置 Git
coolify app update <app-uuid> \
  --git-repository "https://github.com/yourname/working.git" \
  --git-branch "main" \
  --base-directory "."

# 5. 配置构建和启动
coolify app update <app-uuid> \
  --install-command "uv sync" \
  --start-command "uv run reflex run"

# 6. 部署应用
coolify deploy uuid <app-uuid>

# 7. 查看日志
coolify app logs <app-uuid>
```

**后续更新**:

```bash
# 在本地开发
git commit -m "Feature: add new page"
git push origin main

# 通过 CLI 部署
coolify deploy name "Reflex App"

# 查看部署状态
coolify deploy list

# 查看应用日志
coolify app logs <app-uuid>
```

---

## 最佳实践

### 1. 版本管理

- ✅ 为每个部署阶段创建不同分支（main、dev、staging）
- ✅ 使用 Git 标签标记版本
- ✅ 在 .gitignore 中排除本地文件（已完成）

### 2. 部署策略

- ✅ 先在 staging 分支测试
- ✅ 使用 GitHub Actions 进行 CI/CD（可选）
- ✅ 保留部署日志供审计

### 3. 安全性

- ✅ 定期轮换 GitHub App Secret
- ✅ 限制 GitHub App 权限
- ✅ 使用环境变量存储敏感信息
- ✅ 定期检查部署日志

### 4. 性能

- ✅ 优化 Dockerfile 以加快构建
- ✅ 使用 Docker 缓存层
- ✅ 监控部署时间和资源使用

---

## 相关资源

- [Coolify 官方文档](https://coolify.io/docs)
- [GitHub 应用开发](https://docs.github.com/en/developers/apps)
- [Coolify CLI 文档](https://github.com/coollabsio/coolify-cli)
- [项目指导 - CLAUDE.md](../../CLAUDE.md)
- [Coolify CLI 管理规则](../../CLAUDE.md#coolify-cli-管理规则)

---

**最后更新**: 2025-10-28
**版本**: 1.0.0
**维护者**: 项目团队
