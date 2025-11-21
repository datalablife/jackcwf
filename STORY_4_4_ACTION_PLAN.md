# Story 4.4 Day 2-3: 部署与发布 - 完整行动计划

**日期**: 2025-11-21
**周期**: Week 2 Day 2-3 (2 天)
**状态**: 🔄 **配置阶段 - 已准备就绪**

---

## 📊 Story 4.4 概览

### 目标
建立完整的 GitHub → Docker → Coolify 自动化部署流程，支持开发、预发布、生产三层环境，具备健康检查、自动回滚、监控告警等生产级特性。

### 核心决策
✅ **已决定**: 使用 **Option B（在现有 Coolify 应用基础上重新部署）**
- 理由: 数据安全、配置复用、最小化停机时间、符合行业最佳实践
- 现有应用: `datalablife/jackcwf:main-t8ksc8so4o88c084ow4koog8`

---

## 🎯 Day 2: GitHub Secrets 配置和验证

### 2.1 已完成的准备工作 ✓

| 任务 | 状态 | 说明 |
|------|------|------|
| 调查现有基础设施 | ✅ 完成 | `.github/workflows/cd.yml` 和 `scripts/deploy/` 已存在 |
| 识别必需的 Secrets | ✅ 完成 | 4 个 Secrets + 1 个 API Token |
| 创建配置指南 | ✅ 完成 | `STORY_4_4_GITHUB_SECRETS_SETUP.md` |
| 创建验证脚本 | ✅ 完成 | `scripts/verify-secrets.sh` |
| 制定部署测试计划 | ✅ 完成 | `STORY_4_4_DEPLOYMENT_TESTING_GUIDE.md` |

### 2.2 需要您执行的步骤

#### 步骤 1️⃣: 在 Coolify 中收集应用信息 (15-20 分钟)

**任务**:
```
☐ 登录 Coolify Dashboard (https://coolpanel.jackcwf.com)
☐ 获取 Coolify API Token
☐ 找到现有应用 datalablife/jackcwf:main-t8ksc8so4o88c084ow4koog8
☐ 记录应用 UUID (24 个字符)
☐ 确定该应用是哪个环境 (dev/staging/prod)
☐ 如需要，创建 Staging 和 Production 应用
```

**预期结果**:
```
COOLIFY_API_TOKEN = cl_xxxxxxxxxxxxx
COOLIFY_DEV_APP_UUID = ok0s0cgw8ck0w8kgs8kk4kk8
COOLIFY_STAGING_APP_UUID = xk1s1dhx9dl1x9lhs9ll5ll9 (或需要创建)
COOLIFY_PROD_APP_UUID = ym2t2eiy0em2y0mity0mm6mm0 (或需要创建)
```

#### 步骤 2️⃣: 在 GitHub 配置 Secrets (10-15 分钟)

**任务**:
```
☐ 进入 GitHub Secrets 设置:
  https://github.com/datalablife/jackcwf/settings/secrets/actions

☐ 创建 4 个 Repository Secrets:
  ☐ COOLIFY_API_TOKEN = <从 Coolify 复制>
  ☐ COOLIFY_DEV_APP_UUID = <开发环境 UUID>
  ☐ COOLIFY_STAGING_APP_UUID = <预发布环境 UUID>
  ☐ COOLIFY_PROD_APP_UUID = <生产环境 UUID>

☐ 验证所有 Secrets 已保存 (显示为 ✓ XXXXXX)
```

**预期结果**:
```
GitHub Secrets 列表:
✓ COOLIFY_API_TOKEN
✓ COOLIFY_DEV_APP_UUID
✓ COOLIFY_STAGING_APP_UUID
✓ COOLIFY_PROD_APP_UUID
```

#### 步骤 3️⃣: 验证配置 (10 分钟)

**任务** - 选项 A（推荐 - 在 GitHub Actions 中）:
```bash
# 1. 在仓库根目录创建临时验证工作流
# .github/workflows/verify-config.yml

# 2. 在 GitHub Actions 中手动运行此工作流
# 3. 观察输出结果，确保所有验证通过
```

**任务** - 选项 B（本地验证）:
```bash
# 设置本地环境变量
export COOLIFY_TOKEN="your_api_token"
export COOLIFY_DEV_APP_UUID="your_dev_uuid"
export COOLIFY_STAGING_APP_UUID="your_staging_uuid"
export COOLIFY_PROD_APP_UUID="your_prod_uuid"

# 运行验证脚本
chmod +x scripts/verify-secrets.sh
./scripts/verify-secrets.sh
```

**预期结果**:
```
✓ All environment variables configured
✓ Coolify API connectivity verified
✓ Application UUIDs accessible
```

---

## 🚀 Day 2-3: 部署测试阶段

### 3.1 开发环境部署测试 (30-45 分钟)

#### 测试 1: 手动触发部署

```
1. 进入 GitHub Actions
   https://github.com/datalablife/jackcwf/actions

2. 选择 "CD - Continuous Deployment" 工作流

3. 点击 "Run workflow" 按钮

4. 配置:
   - Branch: main
   - Environment: development
   - Skip tests: false (首次应运行测试)

5. 点击绿色 "Run workflow" 按钮
```

#### 测试 2: 监控工作流执行

**预期执行流程** (约 10-15 分钟):
```
✓ pre-deploy (1-2 分钟)
  └─ 确定环境: development
  └─ 生成版本号: 20251121-HHMMSS-<sha7>

✓ test (3-5 分钟)
  └─ 运行 Python/Node.js 测试
  └─ 连接到临时 PostgreSQL

✓ build-image (3-5 分钟)
  └─ 构建 Docker 镜像
  └─ 推送到 GHCR

✓ deploy-development (2-3 分钟)
  └─ 调用 Coolify API
  └─ 更新应用镜像
  └─ 启动容器

✓ post-deploy (1-2 分钟)
  └─ 运行 5 分钟监控
  └─ 生成部署报告
```

#### 测试 3: 验证部署成功

```
☐ 所有 GitHub Actions Jobs 都是绿色 ✓ (PASSED)
☐ 在 Coolify Dashboard 中，应用状态为 "running"
☐ Docker 镜像成功推送到 GHCR
☐ 应用可访问: https://dev.jackcwf.com
☐ 健康检查端点返回 200 OK

验证命令:
$ curl -I https://dev.jackcwf.com
HTTP/1.1 200 OK
```

### 3.2 预发布环境部署测试 (15-20 分钟)

#### 自动触发方式

```
1. 推送代码变更到 main 分支:

   $ git checkout main
   $ git pull origin main
   $ echo "# Deployment test" >> README.md
   $ git add README.md
   $ git commit -m "test: trigger staging deployment"
   $ git push origin main

2. GitHub Actions 自动触发工作流

3. 监控执行，验证部署到 Staging 环境

4. 验证应用: https://staging.jackcwf.com
```

### 3.3 生产环境部署测试 (手动，可选)

#### 手动触发方式

```
1. GitHub Actions → "Run workflow" → production
2. 包含备份、监控、失败回滚等特性
3. 验证应用: https://jackcwf.com
```

---

## 🔒 Day 3: 环境保护和安全配置

### 4.1 配置 Production 环境保护

#### 步骤 1: 创建 Deployment Environment

```
GitHub Repository Settings → Environments → New environment

Name: production
```

#### 步骤 2: 设置保护规则

```
Environment protection rules:

✓ Required reviewers
  - Require at least 1 reviewer
  - Reviewers: (指定 Team Leads 或 Admins)
  - Dismiss stale reviews: ✓

✓ Deployment branches
  - Allow deployments only from: main

✓ Wait timer (可选)
  - Wait 30 minutes before deploying
```

### 4.2 验证回滚机制

```
☐ 理解回滚流程 (.github/workflows/cd.yml 中的 rollback.sh)
☐ 检查 scripts/deploy/rollback.sh 脚本
☐ (可选) 模拟部署失败并验证自动回滚
```

---

## 📚 提供的文档和脚本

| 文件 | 说明 | 用途 |
|------|------|------|
| `STORY_4_4_GITHUB_SECRETS_SETUP.md` | GitHub Secrets 配置详细指南 | 参考配置步骤 |
| `STORY_4_4_DEPLOYMENT_TESTING_GUIDE.md` | 完整部署测试和环境保护指南 | 参考测试步骤 |
| `scripts/verify-secrets.sh` | 验证脚本 | 验证配置正确性 |
| `.github/workflows/cd.yml` | CI/CD 工作流定义 | 理解自动化流程 |
| `scripts/deploy/deploy-coolify.sh` | Coolify 部署脚本 | 执行实际部署 |
| `scripts/deploy/health-check.sh` | 健康检查脚本 | 验证应用状态 |
| `scripts/deploy/rollback.sh` | 回滚脚本 | 失败时恢复 |

---

## ⏱️ 时间估算

| 阶段 | 任务 | 估计时间 | 实际时间 |
|------|------|---------|---------|
| **Day 2** | | | |
| | 1. 收集 Coolify 信息 | 20 min | |
| | 2. 配置 GitHub Secrets | 15 min | |
| | 3. 验证配置 | 10 min | |
| | **小计** | **45 min** | |
| **Day 2-3** | | | |
| | 4. 开发环境部署 | 45 min | |
| | 5. 预发布环境部署 | 20 min | |
| | 6. 生产环境配置 | 30 min | |
| | **小计** | **1.5 hours** | |
| **Day 3** | | | |
| | 7. 环境保护规则 | 15 min | |
| | 8. 回滚机制验证 | 15 min | |
| | 9. 文档和交接 | 30 min | |
| | **小计** | **1 hour** | |
| | **总计** | **~3.5 小时** | |

---

## 🎯 成功标准

### Day 2: 配置完成标准

- [x] 已识别所有应用 UUID
- [x] GitHub Secrets 已配置
- [x] 配置已验证无误

### Day 2-3: 部署测试标准

- [ ] Development 部署成功 (所有 Jobs PASS)
- [ ] Staging 部署成功 (自动触发)
- [ ] Production 部署测试完成
- [ ] 健康检查全部通过
- [ ] 应用在所有环境可访问

### Day 3: 安全配置标准

- [ ] Production 环境保护规则已设置
- [ ] 回滚机制已验证
- [ ] 部署日志和文档完整
- [ ] 团队已了解部署流程

---

## 🔗 重要 URL 和资源

| 资源 | URL |
|------|-----|
| Coolify Dashboard | https://coolpanel.jackcwf.com |
| GitHub Repository | https://github.com/datalablife/jackcwf |
| GitHub Actions | https://github.com/datalablife/jackcwf/actions |
| GitHub Secrets Settings | https://github.com/datalablife/jackcwf/settings/secrets/actions |
| GitHub Environments | https://github.com/datalablife/jackcwf/settings/environments |
| Development App | https://dev.jackcwf.com |
| Staging App | https://staging.jackcwf.com |
| Production App | https://jackcwf.com |

---

## 💡 关键提示

### 配置阶段
- ✅ **API Token 只显示一次** - 保存到安全地方
- ✅ **UUID 格式** - 通常是 24 个字符的字母数字组合
- ✅ **Secret 值无法查看** - 只能编辑或删除

### 部署阶段
- ✅ **首次部署可能较慢** - Docker 镜像构建 (3-5 分钟)
- ✅ **健康检查等待时间** - 应用启动可能需要 30-60 秒
- ✅ **监控输出** - 每个 Job 的日志可帮助诊断问题

### 生产阶段
- ✅ **Production 环境需要审批** - 设置后每次部署都需要审查
- ✅ **自动回滚** - 如果部署失败，自动恢复到上一版本
- ✅ **版本追踪** - 每个部署都有唯一的版本号便于追踪

---

## 📋 下一步行动项

**即刻**:
1. [ ] 打开 `STORY_4_4_GITHUB_SECRETS_SETUP.md`
2. [ ] 按照步骤收集 Coolify 应用信息
3. [ ] 在 GitHub 配置 Secrets

**Day 2-3**:
4. [ ] 打开 `STORY_4_4_DEPLOYMENT_TESTING_GUIDE.md`
5. [ ] 执行开发环境部署测试
6. [ ] 执行预发布环境部署测试
7. [ ] 执行生产环境配置

**Day 3**:
8. [ ] 配置 Production 环境保护规则
9. [ ] 验证回滚机制
10. [ ] 更新部署文档

---

## 📞 支持和故障排查

如遇到问题，参考:
- **常见错误** → `STORY_4_4_GITHUB_SECRETS_SETUP.md` 的故障排查表
- **工作流问题** → `STORY_4_4_DEPLOYMENT_TESTING_GUIDE.md` 的常见问题
- **Coolify 相关** → Coolify Dashboard 的应用日志
- **GitHub Actions** → GitHub Actions 工作流执行日志

---

## ✅ 完成标准

Story 4.4 (部署与发布) 完成时应满足:

```
☐ GitHub → Docker → Coolify CI/CD 流程正常运作
☐ 支持 3 个环境: Development, Staging, Production
☐ 每个环境都能自动或手动部署
☐ 部署成功后应用可访问并通过健康检查
☐ Production 环境配置了保护规则和审批流程
☐ 失败部署自动回滚到上一版本
☐ 完整的日志和监控记录
☐ 团队成员了解部署流程
```

---

**文档准备日期**: 2025-11-21
**预计完成日期**: 2025-11-22 (Day 2-3)
**最后更新**: 2025-11-21

