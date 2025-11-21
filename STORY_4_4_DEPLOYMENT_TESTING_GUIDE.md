# Story 4.4 Day 2-3: CI/CD 部署测试和环境配置指南

**日期**: 2025-11-21
**状态**: 🔄 **配置中 - Day 2-3**
**目标**: 完整的 GitHub → Coolify CI/CD 流程配置和测试

---

## 📋 工作流程概览

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub → Coolify 部署流程                │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
    ┌──────────────────────────────────────────────┐
    │  Step 1: 配置 GitHub Secrets (Day 2)         │
    │  - COOLIFY_API_TOKEN                          │
    │  - COOLIFY_DEV_APP_UUID                       │
    │  - COOLIFY_STAGING_APP_UUID                   │
    │  - COOLIFY_PROD_APP_UUID                      │
    └──────────────┬───────────────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────────────┐
    │  Step 2: 验证 Secrets (Day 2)                │
    │  运行验证脚本确保所有配置正确                  │
    └──────────────┬───────────────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────────────┐
    │  Step 3: 测试部署流程 (Day 2-3)              │
    │  - 手动触发开发环境部署                        │
    │  - 验证 Docker 镜像构建                       │
    │  - 验证应用启动                               │
    │  - 运行健康检查                               │
    └──────────────┬───────────────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────────────┐
    │  Step 4: 环境保护和回滚 (Day 3)              │
    │  - 配置环境保护规则                           │
    │  - 设置生产环保护 (需要审批)                   │
    │  - 测试回滚机制                               │
    └──────────────────────────────────────────────┘
```

---

## 🔐 Day 2: 配置和验证阶段

### 2.1 准备工作清单

在开始配置前，需要准备以下信息：

- [ ] **Coolify 访问权限**
  - Coolify Dashboard URL: https://coolpanel.jackcwf.com
  - 登录凭证: (您的用户名/密码)

- [ ] **现有应用信息**
  - 应用名称: `datalablife/jackcwf:main-t8ksc8so4o88c084ow4koog8`
  - 应用 UUID: _________________________ (需要获取)
  - 当前环境: [ ] Dev [ ] Staging [ ] Prod

- [ ] **GitHub 访问权限**
  - Repository: https://github.com/datalablife/jackcwf
  - 权限: Admin 或有写入 Secrets 的权限

### 2.2 获取 Coolify 配置信息

#### 2.2.1 获取 API Token

**步骤**:

1. 登录 Coolify Dashboard (https://coolpanel.jackcwf.com)
2. 进入设置/API 部分
3. 复制或生成 API Token
4. **保存到安全地方** (仅显示一次)

**示例 API Token 格式**:
```
Token: cl_1234567890abcdef1234567890abcdef
```

#### 2.2.2 获取现有应用 UUID

**步骤**:

1. 在 Coolify Dashboard 中找到现有应用
2. 应用详情页面查看 UUID 或 Application ID
3. **记录三个环境的 UUID**（可能需要创建新应用）

**应用 UUID 表格**:

| 环境 | 应用名称 | UUID | 状态 |
|------|---------|------|------|
| Development | datalablife/jackcwf:main-... | | [ ] 已创建 |
| Staging | datalablife/jackcwf:staging-... | | [ ] 需要创建 |
| Production | datalablife/jackcwf:prod-... | | [ ] 需要创建 |

### 2.3 在 GitHub 配置 Secrets

#### 2.3.1 访问 Repository Secrets 设置

```
URL: https://github.com/datalablife/jackcwf/settings/secrets/actions
```

**或**:
1. 打开 GitHub 仓库主页
2. Settings → Secrets and variables → Actions
3. 点击 "New repository secret"

#### 2.3.2 添加所需的 Secrets

**按顺序添加以下 Secrets** (每个 Secret 点击 "New repository secret"):

**Secret #1: COOLIFY_API_TOKEN**
```
Name: COOLIFY_API_TOKEN
Value: <从 Coolify 复制的 API Token>

例如: cl_1234567890abcdef1234567890abcdef
```

**Secret #2: COOLIFY_DEV_APP_UUID**
```
Name: COOLIFY_DEV_APP_UUID
Value: <开发环境应用的 UUID>

例如: ok0s0cgw8ck0w8kgs8kk4kk8
```

**Secret #3: COOLIFY_STAGING_APP_UUID**
```
Name: COOLIFY_STAGING_APP_UUID
Value: <预发布环境应用的 UUID>

例如: xk1s1dhx9dl1x9lhs9ll5ll9
```

**Secret #4: COOLIFY_PROD_APP_UUID**
```
Name: COOLIFY_PROD_APP_UUID
Value: <生产环境应用的 UUID>

例如: ym2t2eiy0em2y0mity0mm6mm0
```

#### 2.3.3 验证 Secrets 已保存

在 GitHub Secrets 设置页面应该看到:

```
✓ COOLIFY_API_TOKEN
✓ COOLIFY_DEV_APP_UUID
✓ COOLIFY_STAGING_APP_UUID
✓ COOLIFY_PROD_APP_UUID
```

**注意**: 保存后无法再查看 Secret 值，仅能重新编辑或删除。

### 2.4 验证配置正确性

#### 方式 1: 运行验证脚本 (在 GitHub Actions 中)

创建临时工作流验证 Secrets:

**文件**: `.github/workflows/verify-secrets.yml`

```yaml
name: Verify Secrets

on:
  workflow_dispatch:

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run verification script
        env:
          COOLIFY_TOKEN: ${{ secrets.COOLIFY_API_TOKEN }}
          COOLIFY_DEV_APP_UUID: ${{ secrets.COOLIFY_DEV_APP_UUID }}
          COOLIFY_STAGING_APP_UUID: ${{ secrets.COOLIFY_STAGING_APP_UUID }}
          COOLIFY_PROD_APP_UUID: ${{ secrets.COOLIFY_PROD_APP_UUID }}
        run: |
          chmod +x scripts/verify-secrets.sh
          ./scripts/verify-secrets.sh
```

#### 方式 2: 手动测试

```bash
# 本地测试 (需要设置环境变量)
export COOLIFY_TOKEN="your_token"
export COOLIFY_DEV_APP_UUID="your_dev_uuid"
export COOLIFY_STAGING_APP_UUID="your_staging_uuid"
export COOLIFY_PROD_APP_UUID="your_prod_uuid"

chmod +x scripts/verify-secrets.sh
./scripts/verify-secrets.sh
```

---

## 🚀 Day 2-3: 部署测试阶段

### 3.1 首次部署测试 (Development 环境)

#### 3.1.1 手动触发工作流

**步骤**:

1. **进入 GitHub Actions**
   - URL: https://github.com/datalablife/jackcwf/actions
   - 选择 "CD - Continuous Deployment" 工作流

2. **手动触发**
   - 点击 "Run workflow" 按钮
   - 在弹出菜单中:
     - **Select a branch**: `main`
     - **Deployment environment**: `development`
     - **Skip tests**: `false` (首次部署应运行测试)
   - 点击绿色 "Run workflow" 按钮

3. **监控执行**
   - 实时查看每个 Job 的进度
   - 查看日志以诊断问题

#### 3.1.2 监控工作流执行

**预期执行流程**:

```
✓ pre-deploy
  ├─ Checkout code
  ├─ Determine deployment environment → development
  ├─ Generate version tag → YYYYMMDD-HHMMSS-<sha7>
  └─ Validate branch → main

✓ test (可选)
  ├─ Setup PostgreSQL service
  ├─ Install Python/Node.js
  ├─ Run unit tests
  └─ Run integration tests

✓ build-image
  ├─ Setup Docker Buildx
  ├─ Login to GHCR
  ├─ Build Docker image
  └─ Push to ghcr.io

✓ deploy-development
  ├─ Deploy to Coolify (Development)
  ├─ Run health checks
  └─ Notify status

✓ post-deploy (可选)
  ├─ Monitor application health
  ├─ Generate deployment report
  └─ Log summary
```

#### 3.1.3 验证部署成功

**部署成功的标志**:

- [ ] GitHub Actions 工作流全部 PASS (绿色 ✓)
- [ ] Docker 镜像成功推送到 GHCR
- [ ] Coolify 应用状态变为 "running"
- [ ] 应用可通过 URL 访问: https://dev.jackcwf.com
- [ ] 健康检查返回 200 OK

**验证命令**:

```bash
# 检查应用是否在线
curl -I https://dev.jackcwf.com

# 应该返回:
# HTTP/1.1 200 OK
# ...

# 检查应用日志
# 通过 Coolify Dashboard 查看应用日志
```

#### 3.1.4 故障排查

**常见问题及解决方案**:

| 错误 | 原因 | 解决方案 |
|-----|------|---------|
| `COOLIFY_TOKEN not set` | Secret 未配置 | 检查 GitHub Secrets 设置 |
| `Authentication failed` | Token 无效或过期 | 更新 Coolify API Token |
| `Application not found` | UUID 不存在 | 验证 UUID 是否正确 |
| `Deployment timeout` | 部署耗时过长 | 检查 Coolify 应用资源 |
| `Health check failed` | 应用未启动 | 查看 Coolify 应用日志 |

### 3.2 完整工作流测试 (Staging 和 Production)

#### 3.2.1 测试 Staging 部署

**触发条件**:
- 从 `main` 分支推送或合并代码 → 自动部署到 Staging

**测试步骤**:

1. 创建并推送一个简单的变更到 `main` 分支:
   ```bash
   git checkout main
   git pull origin main
   echo "# Deployment test" >> README.md
   git add README.md
   git commit -m "test: trigger staging deployment"
   git push origin main
   ```

2. 监控 GitHub Actions 工作流执行
3. 验证应用部署到 Staging 环境
4. 验证应用可访问: https://staging.jackcwf.com

#### 3.2.2 测试 Production 部署 (手动)

**触发条件**:
- 需要在 GitHub Actions 中手动选择 `production` 环境

**测试步骤**:

1. **手动触发 Production 部署**
   - GitHub Actions → CD 工作流 → Run workflow
   - **Deployment environment**: `production`
   - 点击 "Run workflow"

2. **生产环境特殊处理**
   - 包含备份步骤
   - 失败时自动回滚
   - 包含监控和告警

3. **验证部署**
   - 主应用 URL: https://jackcwf.com
   - 检查应用状态和日志

---

## 🔒 Day 3: 环境保护和安全配置

### 4.1 配置环境保护规则

#### 4.1.1 创建 Deployment Environment

**步骤**:

1. 进入 GitHub Repository Settings
   - URL: https://github.com/datalablife/jackcwf/settings/environments

2. **为生产环境创建保护规则**
   - 点击 "New environment"
   - Name: `production`
   - 配置保护规则:

#### 4.1.2 生产环境保护规则

**推荐配置**:

```
Environment: production

Rules:
├─ Required reviewers
│  ├─ Require at least 1 reviewer
│  ├─ Reviewers: (team leads or admins)
│  └─ Dismiss stale reviews: ✓
│
├─ Deployment branches
│  ├─ Allow deployments only from: main
│  └─ Allow deployments from specific branches: ✓
│
└─ Wait timer
   ├─ Wait 30 minutes before deploying
   └─ (可选，增加额外审查时间)
```

### 4.2 配置回滚机制

#### 4.2.1 理解回滚流程

回滚由 `.github/workflows/cd.yml` 的 `deploy-production` job 自动处理:

```yaml
- name: Rollback on failure
  if: failure()
  run: |
    ./scripts/deploy/rollback.sh production
```

#### 4.2.2 测试回滚机制

**测试步骤**:

1. **查看部署历史**
   - Coolify Dashboard → 应用 → Deployments
   - 记录最新版本的部署 ID

2. **触发失败的部署** (可选测试)
   - 模拟部署失败场景
   - 观察自动回滚

3. **验证回滚成功**
   - 应用恢复到上一个稳定版本
   - 查看 Coolify 日志验证回滚过程

### 4.3 配置监控和通知

#### 4.3.1 Slack 通知 (可选)

创建工作流通知 Slack:

**文件**: `.github/workflows/notify-deployment.yml`

```yaml
name: Deployment Notification

on:
  workflow_run:
    workflows: ["CD - Continuous Deployment"]
    types: [completed]

jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      - name: Notify Slack
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "Deployment ${{ github.event.workflow_run.conclusion }}",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Deployment Status*\nWorkflow: ${{ github.event.workflow_run.name }}\nStatus: ${{ github.event.workflow_run.conclusion }}"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

---

## 📊 Day 2-3: 测试检查清单

### 配置阶段

- [ ] **Coolify 配置**
  - [ ] 获取 API Token
  - [ ] 获取开发应用 UUID
  - [ ] 创建或获取 Staging UUID
  - [ ] 创建或获取 Production UUID

- [ ] **GitHub Secrets**
  - [ ] 添加 COOLIFY_API_TOKEN
  - [ ] 添加 COOLIFY_DEV_APP_UUID
  - [ ] 添加 COOLIFY_STAGING_APP_UUID
  - [ ] 添加 COOLIFY_PROD_APP_UUID
  - [ ] 验证所有 Secrets 已保存

### 部署测试阶段

- [ ] **Development 环境**
  - [ ] 手动触发部署
  - [ ] 工作流全部通过 (绿色 ✓)
  - [ ] Docker 镜像成功构建和推送
  - [ ] 应用在 Coolify 中运行
  - [ ] 应用可通过 https://dev.jackcwf.com 访问
  - [ ] 健康检查通过

- [ ] **Staging 环境**
  - [ ] 推送代码到 main 分支
  - [ ] 工作流自动触发
  - [ ] 部署成功完成
  - [ ] 应用可通过 https://staging.jackcwf.com 访问

- [ ] **Production 环境**
  - [ ] 手动触发生产部署
  - [ ] 部署完成所有安全检查
  - [ ] 应用可通过 https://jackcwf.com 访问
  - [ ] 健康检查和烟测通过

### 安全和回滚阶段

- [ ] **环境保护**
  - [ ] 配置 Production 环境保护规则
  - [ ] 设置必需审查者
  - [ ] 限制部署分支为 main
  - [ ] 设置等待时间 (可选)

- [ ] **回滚机制**
  - [ ] 验证回滚脚本可用
  - [ ] 测试失败时的自动回滚
  - [ ] 验证应用恢复到上一版本

---

## 🔗 关键文件和 URL

| 文件/URL | 说明 |
|---------|------|
| `.github/workflows/cd.yml` | 主 CI/CD 工作流定义 |
| `scripts/deploy/deploy-coolify.sh` | Coolify 部署脚本 |
| `scripts/deploy/health-check.sh` | 健康检查脚本 |
| `scripts/verify-secrets.sh` | Secrets 验证脚本 |
| https://coolpanel.jackcwf.com | Coolify Dashboard |
| https://github.com/datalablife/jackcwf/actions | GitHub Actions 工作流 |
| https://github.com/datalablife/jackcwf/settings/secrets/actions | GitHub Secrets 设置 |

---

## 📖 相关文档

- `STORY_4_4_GITHUB_SECRETS_SETUP.md` - Secrets 配置详细指南
- `scripts/deploy/deploy-coolify.sh` - 部署脚本源码和文档
- `.github/workflows/cd.yml` - 完整 CI/CD 工作流定义

---

## ✅ 完成标准

Story 4.4 Day 2-3 完成标准:

1. **配置完成** ✓
   - 所有 GitHub Secrets 已配置
   - Coolify 应用 UUIDs 已确定

2. **测试通过** ✓
   - Development 部署成功
   - Staging 部署成功
   - Production 部署成功

3. **安全配置** ✓
   - Production 环境保护规则已设置
   - 回滚机制已验证

4. **文档完整** ✓
   - 部署过程文档化
   - 故障排查指南完成
   - 操作手册已准备

---

**预计完成时间**: 2025-11-22 (Day 2-3)
**负责人**: DevOps Team / Cloud Infrastructure
**验证**: GitHub Actions 工作流和 Coolify 应用状态

