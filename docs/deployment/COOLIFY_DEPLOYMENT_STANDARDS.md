# Coolify 生产环境部署标准流程（CI/CD 代理指导）

**文档版本**: 1.0
**最后更新**: 2025-10-30
**应用框架**: Reflex 0.8.16+
**目标平台**: Coolify Self-Hosted
**文档用途**: 为 CI/CD 专家级 agents 提供标准化部署流程

---

## 概述

本文档规范了如何通过 Coolify CLI 和 GitHub 自动化部署 Reflex 应用到生产环境。遵循本标准可确保：

1. ✅ **一致性** - 每次部署行为相同
2. ✅ **可靠性** - 自动故障恢复
3. ✅ **可追溯性** - 清晰的部署历史
4. ✅ **性能** - 优化的构建和启动时间
5. ✅ **安全性** - 生产环境最佳实践

---

## 部分 A：前置条件和验证

### A1. 系统要求

**开发环境**:
- Python 3.12+
- Node.js 20+
- uv 包管理器 (>= 0.9.0)
- Git 客户端

**Coolify 环境**:
- Coolify 版本 4.0.0-beta.434+
- Coolify CLI 1.0.3+
- API Token 已配置
- 网络连接到目标服务器

**应用要求**:
- Reflex 0.8.16+
- pyproject.toml 和 uv.lock 已同步
- GitHub 仓库已配置
- SSH key（如需要）或 GitHub token

### A2. 环境验证清单

**Coolify CLI 验证**:
```bash
# 检查 CLI 版本
coolify version
# 期望: coolify-cli 1.0.3+

# 列出已配置的上下文
coolify context list
# 期望: 至少一个上下文（如 "myapp"）标记为 default

# 验证默认上下文连接
coolify context verify
# 期望: ✓ Connected successfully
```

**GitHub 仓库验证**:
```bash
# 确保本地 main 分支是最新的
git checkout main
git pull origin main

# 检查 Reflex 应用结构
ls -la | grep -E "pyproject.toml|rxconfig.py|working"
# 期望: 看到这些文件存在

# 验证关键文件
test -f pyproject.toml && echo "✓ pyproject.toml found"
test -f uv.lock && echo "✓ uv.lock found"
test -f rxconfig.py && echo "✓ rxconfig.py found"
test -f Dockerfile && echo "✓ Dockerfile found"
test -f nixpacks.toml && echo "✓ nixpacks.toml found"
test -f working/__main__.py && echo "✓ __main__.py found"
```

**应用配置验证**:
```bash
# 检查 rxconfig.py 中的端口配置
grep -E "frontend_port|backend_port" rxconfig.py
# 期望:
#   frontend_port=3000
#   backend_port=8000

# 检查 __main__.py 格式
cat working/__main__.py | grep -E "^from working|pass"
# 期望: 包含 "from working.working import app" 和 pass 语句

# 检查 Dockerfile env 参数
grep -E "reflex run" Dockerfile | grep -E "\-\-env (prod|production)"
# 期望: --env prod (不是 --env production)

# 检查 nixpacks.toml 系统包
grep -A5 "phases.setup" nixpacks.toml | grep unzip
# 期望: unzip 在系统包列表中
```

---

## 部分 B：GitHub 到 Coolify 同步流程

### B1. GitHub 仓库配置

**GitHub Secrets（如需密钥认证）**:

如果 Coolify 应用使用 SSH key 访问 GitHub 私有仓库：

```bash
# 1. 在 Coolify 面板中生成或导入 SSH key
# 2. 在 GitHub Settings > Deploy keys 中添加公钥

# 3. 验证连接
ssh -T git@github.com
# 期望: Hi <username>! You've successfully authenticated.
```

**Branch Protection Rules**:

推荐在 GitHub 中配置 main 分支保护：
- 需要 PR 审查
- 需要 CI 检查通过
- 禁止强制推送

### B2. Coolify 应用配置

**应用基本信息**:

| 项目 | 值 | 说明 |
|------|-----|------|
| **应用名称** | datalablife/jackcwf | GitHub repo 格式 |
| **仓库 URL** | https://github.com/datalablife/jackcwf | 全 HTTPS |
| **分支** | main | 生产分支 |
| **部署触发** | GitHub push | 自动部署 |

**Coolify 应用创建命令**:

```bash
# 获取项目 ID
PROJECT_ID=$(coolify project list --format json | jq -r '.[] | select(.name | contains("Your Project")) | .uuid')

# 创建应用（示例，实际命令可能不同）
# 建议通过 Coolify Web UI 创建，然后通过 CLI 管理

# 获取已创建的应用 ID
coolify app list --format json | jq '.[] | select(.name | contains("jackcwf"))'
```

### B3. Coolify 应用连接 GitHub

**Web UI 操作**:
1. 登录 Coolify (https://coolpanel.jackcwf.com)
2. 找到应用 "datalablife/jackcwf"
3. 点击"Settings"标签
4. 在"Repository"部分：
   - Git URL: `https://github.com/datalablife/jackcwf.git`
   - Branch: `main`
   - Auto-deploy: ✓ 启用

**验证连接**:
```bash
# 查看应用的 Git 信息
coolify app get <app-id> --show-sensitive | grep -E "git|repository|branch"
```

---

## 部分 C：环境变量配置

### C1. 必须的环境变量

**应用必须设置这些环境变量**:

```bash
# 部署前，在 Coolify Web UI 设置：
# Settings > Environment Variables > Add

PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
REFLEX_ENV=production
FRONTEND_PORT=3000
BACKEND_PORT=8000
```

**CLI 设置环境变量** (如果支持):

```bash
# 注意: Coolify CLI 可能不支持直接设置环境变量
# 推荐通过 Web UI 操作

# 验证已设置的环境变量
coolify app env list <app-id> --show-sensitive
# 期望: 看到上面列出的所有 5 个变量
```

### C2. 可选的环境变量

根据应用需要，可考虑添加：

```bash
# 数据库连接
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# API 密钥
API_KEY=your-api-key

# 日志级别（仅用于调试）
LOG_LEVEL=info
```

---

## 部分 D：健康检查配置（关键）

### D1. 健康检查参数

**这是最常见的部署失败原因。必须正确配置。**

**Web UI 配置步骤**:

1. 在 Coolify 应用页面，点击"Health Check"标签
2. 设置以下参数：

| 参数 | 值 | 说明 |
|------|-----|------|
| **Enabled** | ✓ | 启用健康检查 |
| **Path** | / | 根路径 |
| **Port** | 3000 | 前端端口 |
| **Initial Delay** | 120 | ⭐ **关键** (秒) |
| **Interval** | 30 | 检查间隔 (秒) |
| **Timeout** | 10 | 单次超时 (秒) |
| **Retries** | 5 | 失败重试次数 |

**为什么 Initial Delay = 120 秒？**

Reflex 应用启动时序列：
```
0-5s    : 虚拟环境初始化
5-25s   : Reflex init (创建 .web 目录)
25-65s  : React 编译 (TypeScript → JavaScript)
65-85s  : Bun 依赖安装
85-95s  : FastAPI 启动
95+s    : 应用就绪，接受请求
```

120 秒提供 25-35 秒的安全缓冲。

### D2. 健康检查验证

**部署后验证**:

```bash
# 查看应用状态
coolify app get <app-id>

# 期望输出中包含：
# Status: running:healthy
# Health: last_check_passed: true

# 查看最近的健康检查日志
coolify app logs <app-id> | grep -i health

# 期望: 看到多个 "Health check passed" 消息
```

**测试健康检查端点**:

```bash
# 如果应用可外网访问，直接测试
curl -I http://your-domain:3000/
# 期望: HTTP 200

# 或使用 Coolify 内部测试
curl -I http://localhost:3000/
# 期望: HTTP 200
```

---

## 部分 E：部署流程

### E1. 手动部署流程

**触发部署**:

```bash
# 1. 确保代码已推送到 GitHub main
git add -A
git commit -m "deployment: prepare for production release"
git push origin main

# 2. 触发 Coolify 部署
coolify deploy <project-id> <app-id>

# 3. 监控部署进度
coolify app logs <app-id> --follow

# 4. 验证部署结果
coolify app get <app-id> | grep -i status
# 期望: status = "running:healthy"
```

**完整的 Bash 部署脚本**:

```bash
#!/bin/bash
set -e

APP_ID="<your-app-id>"
PROJECT_ID="<your-project-id>"

echo "🚀 开始 Coolify 部署..."

# 步骤 1: 验证本地代码
echo "✓ 验证本地代码..."
git status --porcelain && echo "❌ 有未提交的修改，请先提交" && exit 1

# 步骤 2: 推送到 GitHub
echo "✓ 推送代码到 GitHub..."
git push origin main

# 步骤 3: 等待 GitHub Actions 完成
echo "⏳ 等待 GitHub Actions 完成测试..."
sleep 30  # 给 GitHub Actions 时间启动

# 步骤 4: 触发 Coolify 部署
echo "✓ 触发 Coolify 部署..."
coolify deploy $PROJECT_ID $APP_ID

# 步骤 5: 等待初始化
echo "⏳ 等待应用初始化 (120s)..."
sleep 120

# 步骤 6: 检查部署状态
echo "🔍 检查部署状态..."
STATUS=$(coolify app get $APP_ID --format json | jq -r '.status')

if [[ $STATUS == "running:healthy" ]]; then
    echo "✅ 部署成功！应用状态: $STATUS"
    exit 0
else
    echo "❌ 部署失败！应用状态: $STATUS"
    echo "📋 查看日志..."
    coolify app logs $APP_ID
    exit 1
fi
```

### E2. 自动部署流程（推荐）

**配置自动部署**:

1. **GitHub Webhook**
   - Coolify 自动监听 GitHub push 事件
   - main 分支更新时自动触发部署

2. **启用自动部署**
   - 在 Coolify Web UI: Settings > Auto-deploy: ✓

3. **验证自动部署**
   ```bash
   # 当 GitHub main 有新 push 时，检查 Coolify 是否自动部署
   coolify app get <app-id> | grep -i status
   # 应该自动更新到最新版本
   ```

---

## 部分 F：监控和日志

### F1. 实时日志监控

**查看应用日志**:

```bash
# 实时跟踪日志
coolify app logs <app-id> --follow

# 指定行数查看
coolify app logs <app-id> --tail 50

# 查看部署日志
coolify app logs <app-id> | grep -i "deploy\|build\|start"
```

**日志关键字查找**:

```bash
# 查找错误
coolify app logs <app-id> | grep -i "error\|exception\|failed"

# 查找成功消息
coolify app logs <app-id> | grep -i "started\|running\|successful"

# 查找健康检查
coolify app logs <app-id> | grep -i "health"
```

### F2. 状态监控

**定期检查应用状态**:

```bash
# 创建监控脚本
#!/bin/bash

APP_ID="<your-app-id>"
INTERVAL=300  # 5 分钟

while true; do
    STATUS=$(coolify app get $APP_ID --format json | jq -r '.status')
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    if [[ $STATUS == "running:healthy" ]]; then
        echo "[$TIMESTAMP] ✅ Status: $STATUS"
    else
        echo "[$TIMESTAMP] ⚠️  Status: $STATUS"
        # 发送告警（邮件、Slack 等）
    fi

    sleep $INTERVAL
done
```

### F3. 性能监控

**查看应用资源使用**:

```bash
# 获取应用详细信息
coolify app get <app-id> --format json | jq '.resource | {memory_usage, cpu_usage}'

# 根据需要设置资源限制
# (通常在 Coolify Web UI 中配置)
```

---

## 部分 G：常见故障排除

### G1. 故障诊断决策树

```
应用部署失败？
├─ 构建阶段失败？
│  ├─ "unzip: command not found"
│  │  → 检查 nixpacks.toml 是否包含 "unzip" in nixPkgs
│  │
│  ├─ "uv: command not found"
│  │  → 检查 install 阶段是否设置了 PATH
│  │
│  └─ 其他编译错误
│     → 查看 build logs，搜索关键错误信息
│
├─ 健康检查失败？
│  ├─ "Health check timeout"
│  │  → 增加 start_period 到 120s
│  │
│  ├─ "Connection refused"
│  │  → 确认应用确实在监听 3000 端口
│  │
│  └─ "HTTP 5xx"
│     → 检查应用日志，修复业务逻辑错误
│
└─ 应用运行但功能异常？
   ├─ 前端 (port 3000) 无响应
   │  → 检查 React 编译是否完成
   │
   ├─ 后端 (port 8000) 无响应
   │  → 检查 FastAPI 启动日志
   │
   └─ 数据库连接失败
      → 验证 DATABASE_URL 环境变量
```

### G2. 特定错误修复

**错误: "Invalid value for '--env': 'production' is not one of 'dev', 'prod'"**

```bash
# 问题: 使用了 --env production（全词）
# 修复: 改为 --env prod

# 在 nixpacks.toml 中：
# [start]
# cmd = "python -m reflex run --env prod --loglevel info"

# 在 Dockerfile 中：
# CMD ["python", "-m", "reflex", "run", "--env", "prod"]

# 验证
grep "env prod" nixpacks.toml Dockerfile
```

**错误: "System package 'unzip' is missing"**

```bash
# 问题: nixpacks.toml 缺少 unzip
# 修复: 添加到系统包列表

# 编辑 nixpacks.toml：
# [phases.setup]
# nixPkgs = ["python312", "nodejs_20", "curl", "git", "unzip"]

# 验证
grep "unzip" nixpacks.toml
```

**错误: "no module named 'working.__main__'"**

```bash
# 问题: 缺少 working/__main__.py 文件
# 修复: 创建该文件

cat > working/__main__.py << 'EOF'
"""Entrypoint for running the Reflex application."""

from working.working import app

if __name__ == "__main__":
    pass  # App is automatically run by Reflex framework
EOF

# 验证
test -f working/__main__.py && echo "✓ File created"
```

---

## 部分 H：回滚和恢复

### H1. 部署回滚

**识别部署历史**:

```bash
# 查看应用所有部署版本
coolify app get <app-id> --format json | jq '.deployments[]'

# 获取特定部署 UUID
DEPLOYMENT_UUID="<from-above>"
```

**执行回滚**:

```bash
# 使用 Coolify Web UI 回滚（推荐）：
# 1. 在应用页面找到历史部署
# 2. 点击要回滚到的版本的"回滚"按钮

# 或通过 CLI（如支持）：
coolify app rollback <app-id> --to <deployment-uuid>

# 验证回滚
coolify app get <app-id> | grep -i "deployment\|status"
```

### H2. 紧急停止

**如果应用出现严重问题**:

```bash
# 停止应用
coolify app stop <app-id>

# 等待
sleep 30

# 重新启动
coolify app start <app-id>

# 监控启动过程
coolify app logs <app-id> --follow
```

---

## 部分 I：集成检查清单

### I1. 部署前检查清单

- [ ] 所有代码更改已提交到 GitHub main
- [ ] `pyproject.toml` 和 `uv.lock` 已同步
- [ ] `Dockerfile` 中 `--env` 使用 `prod` 而非 `production`
- [ ] `nixpacks.toml` 包含 `unzip` 系统包
- [ ] `working/__main__.py` 存在且正确
- [ ] `rxconfig.py` 端口配置正确 (3000 和 8000)
- [ ] GitHub Actions 测试通过
- [ ] Coolify 应用已连接到 GitHub 仓库

### I2. 部署中检查清单

- [ ] 代码成功推送到 GitHub
- [ ] Coolify 检测到新推送，自动启动部署
- [ ] Docker 镜像构建成功 (2-3 分钟)
- [ ] 应用容器启动 (5-10 秒)
- [ ] 等待健康检查启动期 (120 秒)

### I3. 部署后检查清单

- [ ] 应用状态是 `running:healthy`
- [ ] 应用日志无错误
- [ ] 前端可访问 (http://domain:3000)
- [ ] 后端 API 文档可访问 (http://domain:8000/docs)
- [ ] 业务功能正常工作
- [ ] 性能指标在预期范围内

---

## 部分 J：CI/CD 代理任务模板

### J1. 标准部署任务

**任务名称**: 生产环境部署 - Reflex 应用到 Coolify

**任务描述**:
使用 Coolify CLI 和 GitHub 自动化工作流将 Reflex 应用部署到生产环境。

**前置条件**:
1. 代码已提交到 GitHub main 分支
2. 所有单元测试和集成测试通过
3. Coolify 应用已配置并连接到 GitHub

**任务步骤**:

```markdown
## 步骤 1: 验证代码质量
- [ ] 运行 pytest 单元测试
- [ ] 运行代码审查 (CrewAI)
- [ ] 检查 GitHub Actions 状态

## 步骤 2: 验证配置文件
- [ ] 检查 nixpacks.toml (包含 unzip)
- [ ] 检查 Dockerfile (--env prod)
- [ ] 检查 working/__main__.py (格式正确)
- [ ] 检查 rxconfig.py (端口 3000/8000)

## 步骤 3: 推送代码
- [ ] 执行 git push origin main
- [ ] 等待 GitHub Actions 完成

## 步骤 4: 触发 Coolify 部署
- [ ] 使用 coolify deploy 触发部署
- [ ] 等待初始化 (120s)

## 步骤 5: 验证部署
- [ ] 检查应用状态是否 running:healthy
- [ ] 验证前端可访问 (port 3000)
- [ ] 验证后端可访问 (port 8000/docs)
- [ ] 运行端到端测试

## 步骤 6: 监控和告警
- [ ] 设置性能监控
- [ ] 配置错误告警
- [ ] 记录部署历史
```

### J2. 故障恢复任务

**任务名称**: Coolify 部署故障恢复

**任务描述**:
当 Coolify 部署失败时，诊断根本原因并执行修复。

**诊断流程**:

```markdown
## 第 1 步: 收集诊断信息
- [ ] 获取应用状态: `coolify app get <app-id>`
- [ ] 收集构建日志: `coolify app logs <app-id>`
- [ ] 搜索错误关键字: "error", "failed", "exception"

## 第 2 步: 识别错误类型
- [ ] 构建阶段错误？ → 查看错误诊断表
- [ ] 启动阶段错误？ → 检查 start-period
- [ ] 健康检查错误？ → 验证健康检查配置
- [ ] 应用错误？ → 检查业务日志

## 第 3 步: 执行修复
- [ ] 按照故障排除指南修复问题
- [ ] 提交修复代码到 GitHub
- [ ] 触发新的部署

## 第 4 步: 验证修复
- [ ] 检查应用状态
- [ ] 验证功能正常
- [ ] 确认没有回归问题
```

---

## 部分 K：自动化部署脚本

### K1. Bash 自动化脚本

**完整的部署自动化脚本** (`scripts/deploy/coolify-deploy.sh`):

```bash
#!/bin/bash

# Coolify 生产部署脚本
# 使用方法: ./coolify-deploy.sh [--force]

set -e  # 任何错误立即退出

# 配置
PROJECT_ID="${COOLIFY_PROJECT_ID:-}"
APP_ID="${COOLIFY_APP_ID:-}"
BRANCH="main"
INITIAL_DELAY=120
DEPLOY_TIMEOUT=300

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 函数
log_info() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC}  $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

check_prerequisites() {
    log_info "检查前置条件..."

    # 检查 CLI 工具
    command -v coolify >/dev/null 2>&1 || {
        log_error "coolify CLI 未安装"
        exit 1
    }

    command -v git >/dev/null 2>&1 || {
        log_error "git 未安装"
        exit 1
    }

    # 检查 APP_ID 和 PROJECT_ID
    if [[ -z $APP_ID ]] || [[ -z $PROJECT_ID ]]; then
        log_error "未设置 COOLIFY_APP_ID 或 COOLIFY_PROJECT_ID"
        echo "使用方法: COOLIFY_PROJECT_ID=xxx COOLIFY_APP_ID=yyy $0"
        exit 1
    }

    log_info "前置条件检查完成"
}

verify_code_quality() {
    log_info "验证代码质量..."

    # 检查本地修改
    if [[ -n $(git status -s) ]]; then
        log_error "本地有未提交的修改"
        git status --short
        exit 1
    fi

    # 检查关键文件
    for file in pyproject.toml uv.lock Dockerfile nixpacks.toml working/__main__.py; do
        if [[ ! -f $file ]]; then
            log_error "缺少关键文件: $file"
            exit 1
        fi
    done

    log_info "代码质量验证完成"
}

push_to_github() {
    log_info "推送代码到 GitHub..."

    git push origin $BRANCH || {
        log_error "推送到 GitHub 失败"
        exit 1
    }

    log_info "代码已推送"
    sleep 10  # 等待 GitHub 处理
}

deploy_with_coolify() {
    log_info "触发 Coolify 部署..."

    coolify deploy $PROJECT_ID $APP_ID || {
        log_error "Coolify 部署命令失败"
        exit 1
    }

    log_info "部署已触发，等待初始化..."
    sleep $INITIAL_DELAY
}

verify_deployment() {
    log_info "验证部署结果..."

    local start_time=$(date +%s)

    while true; do
        STATUS=$(coolify app get $APP_ID --format json 2>/dev/null | jq -r '.status // "unknown"')

        case $STATUS in
            "running:healthy")
                log_info "应用状态正常: $STATUS"
                return 0
                ;;
            "running:unhealthy")
                log_warn "应用运行但不健康: $STATUS"
                return 1
                ;;
            "exited:unhealthy")
                log_error "应用已退出: $STATUS"
                return 1
                ;;
            "starting")
                log_info "应用启动中... (已等待 $(( $(date +%s) - start_time )) 秒)"
                ;;
            *)
                log_warn "未知状态: $STATUS"
                ;;
        esac

        # 超时检查
        if (( $(date +%s) - start_time > DEPLOY_TIMEOUT )); then
            log_error "部署超时 (> ${DEPLOY_TIMEOUT}s)"
            return 1
        fi

        sleep 10
    done
}

main() {
    echo "🚀 Coolify 生产部署开始"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    check_prerequisites
    verify_code_quality
    push_to_github
    deploy_with_coolify

    if verify_deployment; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        log_info "✅ 部署成功完成！"
        exit 0
    else
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        log_error "❌ 部署失败，请查看上面的错误信息"

        # 收集日志用于调试
        echo ""
        log_warn "收集诊断信息..."
        echo "应用日志："
        coolify app logs $APP_ID --tail 20 | head -20

        exit 1
    fi
}

main "$@"
```

**使用方法**:

```bash
# 设置环境变量
export COOLIFY_PROJECT_ID="your-project-id"
export COOLIFY_APP_ID="your-app-id"

# 运行部署脚本
chmod +x scripts/deploy/coolify-deploy.sh
./scripts/deploy/coolify-deploy.sh
```

---

## 部分 L：文档参考

### 相关文档

- **`COOLIFY_FIX_REPORT.md`** - 完整的错误修复报告和根本原因分析
- **`REFLEX_COOLIFY_BEST_PRACTICES.md`** - Reflex + Coolify 最佳实践指南
- **`CLAUDE.md`** - 项目通用指导和规范

### 外部资源

- [Coolify 官方文档](https://coolify.io/docs)
- [Coolify CLI GitHub](https://github.com/coollabsio/coolify-cli)
- [Reflex 官方文档](https://reflex.dev/docs)
- [Nixpacks 文档](https://nixpacks.com/docs)

---

**文档版本历史**:

| 版本 | 日期 | 更新内容 |
|------|------|--------|
| 1.0 | 2025-10-30 | 首次发布，包含完整部署标准 |

**维护者**: Claude Code AI Assistant
**最后验证**: 2025-10-30 (部署 6 - 成功)
