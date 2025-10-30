# Reflex 0.8.16 Coolify 部署失败诊断报告

## 执行摘要

**问题**: Reflex 应用在 Coolify 上部署后容器立即退出，健康检查失败，且容器日志为空。

**根本原因**: 多个配置问题导致应用无法启动，主要包括：
1. Nixpacks 配置格式不正确
2. Reflex 应用缺少必要的导出步骤
3. 健康检查时机不当
4. 缺少必要的环境变量

**状态**: 应用 UUID `mg8c40oowo80o08o0gsw0gwc` 显示 `exited:unhealthy`

---

## 关键问题分析

### 1. 为什么容器日志为空？

**分析**:
- 容器日志完全为空意味着应用在启动时立即崩溃
- 可能的原因：
  - Python 模块导入失败
  - Reflex 初始化失败
  - 缺少必要的编译产物（`.web/` 目录）
  - 环境变量配置错误

**证据**:
```bash
# 从 coolify app get 返回
"status":"exited:unhealthy"

# 从 coolify app logs 返回
"Application is not running"
```

### 2. Coolify 为什么忽略健康检查配置？

**分析**:
- Coolify 使用 Nixpacks 自动生成 Dockerfile
- 你的 `Dockerfile` 被 Coolify 忽略了
- `nixpacks.toml` 的健康检查配置格式不正确

**当前 nixpacks.toml 的问题**:
```toml
# ❌ 错误：Nixpacks 不支持 [health] 部分
[health]
enabled = true
cmd = "curl -f http://localhost:3000/ || exit 1"
start_period = 120
```

**正确的格式**:
Nixpacks 不直接支持健康检查配置。健康检查由 Coolify 在生成的 Dockerfile 中管理。

### 3. Reflex 在容器中需要什么才能正常启动？

**关键要求**:

1. **前端编译产物**: Reflex 需要 `.web/` 目录中的编译前端
2. **初始化步骤**: 必须运行 `reflex init` 和 `reflex export --frontend-only`
3. **环境变量**:
   ```bash
   PYTHONUNBUFFERED=1          # 实时日志输出
   REFLEX_ENV=production       # 生产模式
   FRONTEND_PORT=3000          # 前端端口
   BACKEND_PORT=8000           # 后端端口
   ```

4. **启动命令**: `reflex run --env production --loglevel info`

---

## 具体问题清单

### 问题 1: nixpacks.toml 配置不完整

**当前配置问题**:
```toml
[build]
install = "uv sync"  # ❌ 不足：缺少 --no-dev 标志
build = "python -m reflex init --loglevel warning && python -m reflex export --frontend-only --loglevel info"
start = "python -m reflex run --env production --loglevel info"
```

**缺失的关键部分**:
- 没有指定 Python 版本
- 没有指定 Nixpacks provider
- 健康检查配置格式错误

### 问题 2: 应用启动时机

**问题**:
- Reflex 应用启动需要时间（编译、初始化）
- Coolify 默认只等待 5 秒
- 健康检查在应用准备好之前就开始

**Reflex 启动流程**:
```
1. Python 导入 (2-5 秒)
2. Reflex 框架初始化 (5-10 秒)
3. 前端编译/启动 (15-30 秒)
4. 后端 API 启动 (5-10 秒)
5. WebSocket 连接建立 (2-5 秒)
────────────────────────────────
总计: 29-60 秒
```

### 问题 3: 前端编译产物缺失

**分析**:
- `.web/` 目录在 `.gitignore` 中被忽略（正确）
- 但是构建时需要重新生成
- `reflex export --frontend-only` 必须在构建阶段完成

**当前 .gitignore**:
```
.web        # ✓ 正确：不提交编译产物
.states     # ✓ 正确：不提交状态文件
```

### 问题 4: 端口配置

**rxconfig.py 配置**:
```python
frontend_host="0.0.0.0",  # ✓ 正确
frontend_port=3000,       # ✓ 正确
backend_host="0.0.0.0",   # ✓ 正确
backend_port=8000,        # ✓ 正确
```

**注意**: Coolify 需要知道监听的端口，必须在 Nixpacks 配置中声明。

---

## 解决方案

### 方案 1: 修复 nixpacks.toml（推荐）

创建新的 `nixpacks.toml`：

```toml
# Nixpacks configuration for Reflex 0.8.16 application
# Optimized for Coolify deployment

# 指定 providers
[phases.setup]
nixPkgs = ["python312", "nodejs_20", "curl"]

# 安装阶段
[phases.install]
cmds = [
    "curl -LsSf https://astral.sh/uv/install.sh | sh",
    "export PATH=\"$HOME/.cargo/bin:$PATH\"",
    "uv sync --no-dev"
]

# 构建阶段 - 关键：生成前端
[phases.build]
cmds = [
    "export PATH=\".venv/bin:$PATH\"",
    "python -m reflex init --loglevel warning",
    "python -m reflex export --frontend-only --loglevel info"
]

# 启动命令
[start]
cmd = "python -m reflex run --env production --loglevel info"

# 环境变量
[variables]
PYTHONUNBUFFERED = "1"
PYTHONDONTWRITEBYTECODE = "1"
REFLEX_ENV = "production"
FRONTEND_PORT = "3000"
BACKEND_PORT = "8000"
```

### 方案 2: 使用自定义 Dockerfile（备选）

如果 Nixpacks 继续有问题，可以强制 Coolify 使用你的 Dockerfile：

在 Coolify 应用设置中：
1. 进入应用设置
2. 找到 "Build Pack" 设置
3. 选择 "Dockerfile"（而非 Nixpacks）
4. 指定 Dockerfile 路径

然后修改你的 Dockerfile：

```dockerfile
ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 安装 Node.js 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# 安装 uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# 复制依赖文件
COPY pyproject.toml uv.lock ./

# 安装 Python 依赖（生产环境）
RUN uv sync --no-dev

# 复制应用代码
COPY . .

# 初始化 Reflex 和构建前端
ENV PATH="/app/.venv/bin:$PATH"
RUN python -m reflex init --loglevel warning && \
    python -m reflex export --frontend-only --loglevel info

# 环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    REFLEX_ENV=production \
    FRONTEND_PORT=3000 \
    BACKEND_PORT=8000

# 暴露端口
EXPOSE 3000 8000

# 启动应用（不设置健康检查，由 Coolify 管理）
CMD ["python", "-m", "reflex", "run", "--env", "production", "--loglevel", "info"]
```

### 方案 3: 添加启动脚本（增强稳定性）

创建 `/mnt/d/工作区/云开发/working/start.sh`:

```bash
#!/bin/bash
set -e

echo "Starting Reflex application..."
echo "Python version: $(python --version)"
echo "Node version: $(node --version)"
echo "Working directory: $(pwd)"

# 激活虚拟环境
export PATH="/app/.venv/bin:$PATH"

# 验证 Reflex 安装
echo "Reflex version: $(python -m reflex --version)"

# 检查前端编译产物
if [ ! -d ".web" ]; then
    echo "WARNING: .web directory not found, running export..."
    python -m reflex export --frontend-only --loglevel info
fi

# 启动应用
echo "Starting Reflex in production mode..."
exec python -m reflex run --env production --loglevel info
```

然后在 `nixpacks.toml` 或 `Dockerfile` 中使用：
```toml
[start]
cmd = "bash start.sh"
```

---

## Coolify 特定配置

在 Coolify 应用设置中配置：

### 1. 环境变量
```
PYTHONUNBUFFERED=1
REFLEX_ENV=production
FRONTEND_PORT=3000
BACKEND_PORT=8000
```

### 2. 端口映射
- Frontend: 3000
- Backend: 8000

### 3. 健康检查（在 Coolify UI 中配置）
- **URL**: `http://localhost:3000/`
- **Initial Delay**: 60 秒
- **Interval**: 30 秒
- **Timeout**: 10 秒
- **Retries**: 5

### 4. 资源限制（推荐）
- **Memory**: 至少 512MB（推荐 1GB）
- **CPU**: 至少 0.5 core

---

## 调试步骤

### 步骤 1: 本地验证 Docker 构建

```bash
cd /mnt/d/工作区/云开发/working

# 使用你的 Dockerfile 构建
docker build -t reflex-test .

# 运行容器
docker run -p 3000:3000 -p 8000:8000 reflex-test

# 检查日志
docker logs -f <container_id>
```

### 步骤 2: 模拟 Nixpacks 构建

```bash
# 安装 Nixpacks
curl -sSL https://nixpacks.com/install.sh | bash

# 使用 Nixpacks 构建
nixpacks build . --name reflex-nixpacks

# 运行
docker run -p 3000:3000 -p 8000:8000 reflex-nixpacks
```

### 步骤 3: 检查容器内部

```bash
# 启动容器但不运行应用
docker run -it --entrypoint /bin/bash reflex-test

# 在容器内手动运行
cd /app
source .venv/bin/activate
python -m reflex run --env production --loglevel debug
```

### 步骤 4: 查看 Coolify 构建日志

在 Coolify 面板：
1. 进入应用详情
2. 点击 "Deployments"
3. 查看最新的部署日志
4. 查找构建错误和启动错误

---

## 预期日志输出

**正常启动应该看到**:

```
Starting Reflex application...
Python version: 3.12.x
Node version: 20.x.x
Reflex version: 0.8.16

Initializing app...
Compiling: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
Compiling finished in X.XX s
App running at:
  ├─ http://0.0.0.0:8000 (backend)
  └─ http://0.0.0.0:3000 (frontend)
```

**异常情况**:

1. **模块导入错误**:
   ```
   ModuleNotFoundError: No module named 'reflex'
   ```
   → 解决：检查 `uv sync` 是否成功

2. **编译错误**:
   ```
   Error: .web directory not found
   ```
   → 解决：确保 build 阶段运行 `reflex export`

3. **端口占用**:
   ```
   OSError: [Errno 98] Address already in use
   ```
   → 解决：检查 Coolify 端口映射

---

## 推荐行动计划

### 立即执行（优先级 1）

1. **更新 nixpacks.toml**（使用方案 1）
2. **在 Coolify UI 中配置健康检查**（60 秒初始延迟）
3. **添加环境变量**到 Coolify 应用设置
4. **重新部署**应用

### 短期优化（优先级 2）

1. **添加启动脚本**（start.sh）以增强日志和错误处理
2. **本地测试 Docker 构建**确保可重现性
3. **监控资源使用**调整内存/CPU 限制

### 长期改进（优先级 3）

1. **设置 CI/CD 管道**自动化测试和部署
2. **添加应用级日志**使用 Python logging
3. **实现优雅关闭**处理 SIGTERM 信号
4. **添加监控和告警**

---

## 常见错误和解决方案

| 错误 | 原因 | 解决方案 |
|------|------|---------|
| 容器立即退出 | Python 导入失败 | 检查 `uv sync --no-dev` 日志 |
| 日志为空 | stdout 被缓冲 | 设置 `PYTHONUNBUFFERED=1` |
| 健康检查失败 | 启动时间过长 | 增加 `start_period` 到 120 秒 |
| 前端 404 | `.web/` 未生成 | 确保 build 阶段运行 `reflex export` |
| 端口无法访问 | 绑定到 127.0.0.1 | 使用 `0.0.0.0` 在 rxconfig.py |

---

## 下一步

1. **立即执行**: 使用方案 1 更新 `nixpacks.toml`
2. **提交变更**: `git add nixpacks.toml && git commit -m "fix: update nixpacks config for Coolify"`
3. **重新部署**: 在 Coolify 面板触发部署
4. **监控日志**: 实时查看部署和启动日志
5. **报告结果**: 如果问题持续，提供完整的构建和运行日志

---

## 联系和支持

如果问题持续：
1. 导出 Coolify 部署日志
2. 运行本地 Docker 构建测试
3. 检查 Reflex 官方文档：https://reflex.dev/docs/hosting/self-hosting/
4. 查看 Coolify 文档：https://coolify.io/docs/knowledge-base/nixpacks

---

**报告生成时间**: 2025-10-30
**分析者**: Claude Code
**应用 UUID**: mg8c40oowo80o08o0gsw0gwc
**Reflex 版本**: 0.8.16
