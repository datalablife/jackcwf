# Granian "FileNotFoundError" 修复指南

## 问题描述

在 Coolify 部署 Reflex 应用时，应用启动后立即崩溃，错误信息：

```
FileNotFoundError: [Errno 2] No such file or directory: 'granian'
```

## 根本原因

1. **虚拟环境 PATH 问题**：虽然使用 `.venv/bin/python` 启动 Reflex，但 Reflex 使用 `subprocess.Popen()` 启动 granian 时，子进程没有继承虚拟环境的 PATH
2. **Granian 位置**：granian 安装在 `/app/.venv/bin/granian`，但系统 PATH 中没有这个目录
3. **Subprocess 行为**：Python subprocess 默认继承当前进程的环境变量，但如果 PATH 没有正确设置，就找不到可执行文件

## 解决方案

### 方案 1：修改环境变量（推荐）

**修改内容**：`nixpacks.toml`

```toml
# Start command - Use wrapper script to ensure PATH includes virtual environment
[start]
cmd = "bash -c 'export PATH=/app/.venv/bin:$PATH && python -m reflex run --env prod --loglevel info'"

# Environment variables for production
[variables]
PYTHONUNBUFFERED = "1"
PYTHONDONTWRITEBYTECODE = "1"
REFLEX_ENV = "production"
FRONTEND_PORT = "3000"
BACKEND_PORT = "8000"
# Add virtual environment to PATH so granian can be found
PATH = "/app/.venv/bin:$PATH"
```

**原理**：
- 在启动命令中显式设置 PATH 环境变量
- 在 Nixpacks variables 中添加 PATH 配置
- 这样所有子进程（包括 granian）都能找到虚拟环境中的可执行文件

**优点**：
- 最简单直接
- 不需要额外文件
- 适用于所有 Python 工具（不只是 granian）

### 方案 2：使用启动脚本（备选）

**新建文件**：`start.sh`

```bash
#!/bin/bash
set -e

cd /app
source .venv/bin/activate

# Verify granian is available
if ! command -v granian &> /dev/null; then
    echo "ERROR: granian not found in PATH"
    exit 1
fi

echo "Starting Reflex application..."
echo "Python: $(which python)"
echo "Granian: $(which granian)"

exec python -m reflex run --env prod --loglevel info
```

**修改**：`nixpacks.toml`

```toml
[phases.build]
cmds = [
    "...",
    "chmod +x start.sh"
]

[start]
cmd = "./start.sh"
```

**优点**：
- 更好的调试信息
- 可以添加更多启动前检查
- 更灵活的环境控制

## 验证步骤

部署后检查日志，应该看到：

**方案 1 成功标志**：
```
App running at: http://0.0.0.0:3000/
Backend running at: http://0.0.0.0:8000/
[应用保持运行，不崩溃]
```

**方案 2 成功标志**：
```
Starting Reflex application...
Python: /app/.venv/bin/python
Granian: /app/.venv/bin/granian
App running at: http://0.0.0.0:3000/
Backend running at: http://0.0.0.0:8000/
```

## 如果仍然失败

1. **检查 granian 是否安装**：
   ```bash
   # 在容器中执行
   ls -la /app/.venv/bin/granian
   /app/.venv/bin/pip list | grep granian
   ```

2. **检查 PATH 环境变量**：
   ```bash
   echo $PATH
   ```

3. **手动测试 granian**：
   ```bash
   /app/.venv/bin/granian --help
   ```

4. **降级到 uvicorn**（临时方案）：
   修改 `rxconfig.py`：
   ```python
   config = rx.Config(
       app_name="working",
       backend_host="0.0.0.0",
       backend_port=8000,
       frontend_host="0.0.0.0",
       frontend_port=3000,
       backend_backend="uvicorn",  # 强制使用 uvicorn 而非 granian
   )
   ```

## 技术背景

- **Reflex 0.6.0+** 默认使用 granian 作为生产 ASGI 服务器
- **Granian** 比 uvicorn 更快，但对环境配置要求更严格
- **虚拟环境激活** 使用 `source .venv/bin/activate` 会自动设置 PATH，但直接使用 `.venv/bin/python` 不会
- **Docker 环境** 中默认 PATH 是最小化的，不包括用户安装的工具

## 参考

- Reflex Backend Config: https://reflex.dev/docs/api-reference/config/#backend
- Granian Documentation: https://github.com/emmett-framework/granian
- Python subprocess PATH: https://docs.python.org/3/library/subprocess.html#subprocess.Popen
