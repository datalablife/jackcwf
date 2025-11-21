# Story 4.4: GitHub Secrets 与 Coolify CI/CD 集成配置

**日期**: 2025-11-21
**状态**: 🔄 **配置中 - Day 2**
**目标**: 配置 GitHub Secrets 和 Coolify 部署工作流

---

## 📋 配置概览

本文档指导如何为 GitHub → Coolify CI/CD 流程配置所需的密钥和环境变量。

### 已有基础设施
- ✅ `.github/workflows/cd.yml` - 完整的 CI/CD 工作流
- ✅ `scripts/deploy/` - 部署脚本集合
- ✅ 现有 Coolify 应用: `datalablife/jackcwf:main-t8ksc8so4o88c084ow4koog8`

### 需要配置的内容
1. ✅ **Identify Coolify App UUIDs** - 确定应用 UUID
2. ⏳ **GitHub Secrets** - 配置 GitHub 密钥
3. ⏳ **Coolify Webhook** - 配置自动触发
4. ⏳ **Environment Protection** - 环境保护规则

---

## 🔍 Step 1: 识别和获取 Coolify 应用 UUID

### 需要的信息
根据 CI/CD 工作流 (`.github/workflows/cd.yml:175-277`)，我们需要三个环境的应用 UUID：

| 环境 | 说明 | 用途 | 所需 Secret |
|------|------|------|-----------|
| **Development** | 开发/测试环境 | 每次 push 自动部署 | `COOLIFY_DEV_APP_UUID` |
| **Staging** | 预发布环境 | 从 main 分支部署 | `COOLIFY_STAGING_APP_UUID` |
| **Production** | 生产环境 | 手动触发部署 | `COOLIFY_PROD_APP_UUID` |

### 获取 Coolify App UUID

#### 方法 1: 通过 Coolify Web UI（推荐）

**步骤**:

1. **登录 Coolify Dashboard**
   ```
   URL: https://coolpanel.jackcwf.com
   用户名: (您的凭证)
   ```

2. **找到应用详情**
   - 导航至 "Applications" 或 "Projects"
   - 找到现有应用: `datalablife/jackcwf:main-t8ksc8so4o88c084ow4koog8`
   - 点击应用查看详细信息

3. **复制应用 UUID**
   - 在应用详情页面查找 "UUID" 或 "Application ID"
   - 格式通常是: `xxxxxxxxxxxxxxxxxxxxxxx` (24 个字符)
   - 示例: `ok0s0cgw8ck0w8kgs8kk4kk8`

4. **确定环境分类**
   - 如果现有应用是开发环境，记录为 `COOLIFY_DEV_APP_UUID`
   - 如果需要创建 Staging 和 Production，请参考下一步

#### 方法 2: 通过 Coolify API

```bash
# 设置环境变量
COOLIFY_TOKEN="your_api_token"  # 从 Coolify 获取
COOLIFY_URL="https://coolpanel.jackcwf.com"

# 列出所有应用
curl -s -X GET \
  -H "Authorization: Bearer ${COOLIFY_TOKEN}" \
  "${COOLIFY_URL}/api/v1/applications" | jq '.data[] | {uuid, name, status}'
```

#### 方法 3: 从 Coolify CLI

```bash
# 如果您有 Coolify CLI 配置
coolify app list --format json | jq '.[] | {uuid, name, environment}'
```

### UUID 信息填写表

请获取并填写以下信息（用于下一步配置 GitHub Secrets）：

```
现有应用分类:
应用名称: datalablife/jackcwf:main-t8ksc8so4o88c084ow4koog8
应用 UUID: _________________________ (24 字符)
当前环境: [ ] Development [ ] Staging [ ] Production

如果现有应用是开发环境，则:
COOLIFY_DEV_APP_UUID = _________________________

需要创建新应用的环境（如适用）:
[ ] 需要创建 Staging 环境
[ ] 需要创建 Production 环境
```

---

## 🔐 Step 2: 在 GitHub 中配置 Secrets

### 2.1 获取 Coolify API Token

首先，需要从 Coolify 获取 API Token 用于认证。

**步骤**:

1. **登录 Coolify Dashboard**: https://coolpanel.jackcwf.com
2. **进入设置/API 部分**
   - 找到 "Settings" 或 "Admin"
   - 查找 "API Tokens" 或 "API Keys"
3. **创建或复制 API Token**
   - 点击 "Generate New Token" 或复制现有 token
   - Token 格式: 通常以 `cl_` 或 `token_` 开头
4. **保存 Token** 安全地保存（仅显示一次）

### 2.2 配置 GitHub Repository Secrets

**步骤**:

1. **进入 GitHub Repository Settings**
   - URL: `https://github.com/your-org/your-repo/settings/secrets/actions`
   - 或在仓库首页: Settings → Secrets and variables → Actions

2. **添加以下 Secrets**（点击 "New repository secret"）

#### Secret 1: COOLIFY_API_TOKEN

```
名称: COOLIFY_API_TOKEN
值: <从 Coolify 获取的 API Token>
```

#### Secret 2: COOLIFY_DEV_APP_UUID

```
名称: COOLIFY_DEV_APP_UUID
值: <开发环境应用 UUID>
示例: ok0s0cgw8ck0w8kgs8kk4kk8
```

#### Secret 3: COOLIFY_STAGING_APP_UUID

```
名称: COOLIFY_STAGING_APP_UUID
值: <预发布环境应用 UUID>
注: 如果还没有 Staging 应用，需要先在 Coolify 中创建
```

#### Secret 4: COOLIFY_PROD_APP_UUID

```
名称: COOLIFY_PROD_APP_UUID
值: <生产环境应用 UUID>
注: 如果还没有 Production 应用，需要先在 Coolify 中创建
```

#### Secret 5: DOCKER_REGISTRY_PASSWORD (可选)

```
名称: DOCKER_REGISTRY_PASSWORD
值: ${{ secrets.GITHUB_TOKEN }}  (已自动可用)
```

### 2.3 验证 Secrets 配置

在 GitHub 中验证配置：

```bash
# 查看已配置的 secrets 列表
# URL: https://github.com/your-org/your-repo/settings/secrets/actions

# 应该看到：
✓ COOLIFY_API_TOKEN
✓ COOLIFY_DEV_APP_UUID
✓ COOLIFY_STAGING_APP_UUID
✓ COOLIFY_PROD_APP_UUID
```

---

## 🚀 Step 3: 测试 CI/CD 工作流

### 3.1 手动触发工作流（首次测试）

**步骤**:

1. **进入 GitHub Actions**
   - URL: `https://github.com/your-org/your-repo/actions`
   - 选择 "CD - Continuous Deployment" 工作流

2. **手动触发部署**
   - 点击 "Run workflow"
   - 选择环境: `development` （首次测试）
   - 点击 "Run workflow" 按钮

3. **监控执行进度**
   - 观察各个 Job 的执行状态
   - 查看日志以诊断任何问题

### 3.2 测试工作流步骤

#### 测试 1: Pre-deployment Checks ✓
- 确保环境确定正确
- 确保版本号生成成功
- 预期: PASS

#### 测试 2: Run Tests (可选跳过)
- 运行 Python 和 Node.js 测试
- 需要 PostgreSQL 连接
- 预期: PASS

#### 测试 3: Build Docker Image ✓
- 构建 Docker 镜像
- 推送到 GHCR
- 预期: PASS

#### 测试 4: Deploy to Development ✓
- 调用 `deploy-coolify.sh` 脚本
- 使用 `COOLIFY_API_TOKEN` 和 `COOLIFY_DEV_APP_UUID` 身份验证
- 触发 Coolify 部署
- 预期: PASS

#### 测试 5: Health Checks ✓
- 运行健康检查脚本
- 验证应用可访问
- 预期: PASS

### 3.3 故障排查

**常见问题**:

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| `COOLIFY_TOKEN environment variable is not set` | Secret 未正确配置 | 验证 GitHub Secret 名称和值 |
| `Failed to connect to Coolify API` | Coolify 连接失败 | 检查 Token 有效性和网络连接 |
| `Invalid environment: <env>` | 环境名称错误 | 确保使用 `development`, `staging`, 或 `production` |
| `App UUID not found` | UUID 不存在 | 验证 UUID 是否正确 |
| `Deployment timeout after 600s` | 部署超时 | 检查 Coolify 应用状态和资源 |

---

## 📋 配置检查清单

### Coolify 配置

- [ ] 获取现有应用的 UUID
- [ ] 确定现有应用属于哪个环境
- [ ] 如需要，在 Coolify 中创建 Staging 应用
- [ ] 如需要，在 Coolify 中创建 Production 应用
- [ ] 获取 Coolify API Token
- [ ] 测试 Coolify API 连接

### GitHub 配置

- [ ] 添加 `COOLIFY_API_TOKEN` Secret
- [ ] 添加 `COOLIFY_DEV_APP_UUID` Secret
- [ ] 添加 `COOLIFY_STAGING_APP_UUID` Secret
- [ ] 添加 `COOLIFY_PROD_APP_UUID` Secret
- [ ] 验证所有 Secret 已正确保存
- [ ] 手动触发工作流进行测试

### 工作流验证

- [ ] Pre-deployment checks 通过
- [ ] Docker 镜像构建成功
- [ ] Development 部署成功
- [ ] Health checks 通过
- [ ] 应用在 Coolify 中运行

---

## 🔐 安全最佳实践

1. **保护 API Token**
   - 不要在代码中硬编码 Token
   - 定期轮换 Token
   - 使用 GitHub Secrets 管理

2. **环境隔离**
   - 开发、预发布、生产使用不同的 UUID
   - 不同环境不同的权限级别

3. **审计日志**
   - 监控 Coolify API 日志
   - 追踪谁部署了什么内容
   - 记录部署时间和版本

4. **版本管理**
   - 每次部署生成唯一版本号
   - 保留部署历史用于回滚

---

## 📖 相关文档

- `.github/workflows/cd.yml` - CI/CD 工作流定义
- `scripts/deploy/deploy-coolify.sh` - Coolify 部署脚本
- `scripts/deploy/health-check.sh` - 健康检查脚本
- `scripts/deploy/backup.sh` - 备份脚本
- `scripts/deploy/rollback.sh` - 回滚脚本

---

## 🔗 Coolify 资源

- **Coolify Panel**: https://coolpanel.jackcwf.com
- **Coolify API Documentation**: 通常在 Coolify 面板中
- **示例应用**: `datalablife/jackcwf:main-t8ksc8so4o88c084ow4koog8`

---

## ✅ 下一步

完成本步骤后，继续：

1. **Step 2**: 配置 Coolify Webhook 自动触发
2. **Step 3**: 部署测试和验证
3. **Day 3**: 环境保护和回滚机制

---

**状态**: 等待 Coolify UUID 信息收集和 GitHub Secret 配置

