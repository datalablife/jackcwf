# Granian PATH 问题修复指南

## 问题描述

在 Coolify 部署 Reflex 应用时遇到以下错误：

```
FileNotFoundError: [Errno 2] No such file or directory: 'granian'
```

### 错误堆栈

```python
File "/app/.venv/lib/python3.12/site-packages/reflex/utils/exec.py", line 681, in run_granian_backend_prod
    processes.new_process(
...
File "/root/.nix-profile/lib/python3.12/subprocess.py", line 1026, in __init__
    self._execute_child(args, executable, preexec_fn, close_fds,
FileNotFoundError: [Errno 2] No such file or directory: 'granian'
```

## 根本原因

1. **Python subprocess 无法找到 granian 命令**
   - Reflex 启动 granian 作为子进程
   - 子进程在 PATH 环境变量中查找 `granian`
   - 虽然 granian 安装在 `.venv/bin/`，但 PATH 没有正确设置

2. **虚拟环境未正确激活**
   - 使用 `python -m reflex run` 可以找到 reflex 模块
   - 但子进程不继承虚拟环境的完整环境变量
   - 特别是 PATH 和 VIRTUAL_ENV 没有正确传递

3. **Nixpacks 环境变量限制**
   - 在 `nixpacks.toml` 的 `[variables]` 中设置 PATH 可能被覆盖
   - 容器启动时的默认环境可能优先级更高

## 解决方案

### 方案 1: 在 nixpacks.toml 中正确激活虚拟环境（推荐）

修改 `nixpacks.toml` 的 `[start]` 命令：

```toml
[start]
cmd = ". /app/.venv/bin/activate && exec reflex run --env prod --loglevel info"

[variables]
PYTHONUNBUFFERED = "1"
PYTHONDONTWRITEBYTECODE = "1"
REFLEX_ENV = "production"
FRONTEND_PORT = "3000"
BACKEND_PORT = "8000"
# Ensure virtual environment binaries are in PATH
VIRTUAL_ENV = "/app/.venv"
PATH = "/app/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
```

**关键点**：
- 使用 `. /app/.venv/bin/activate` 激活虚拟环境
- `activate` 脚本会正确设置所有环境变量
- 使用 `exec` 替换当前进程，避免额外的进程层级
- 激活后直接使用 `reflex run` 而不是 `python -m reflex run`

### 方案 2: 使用启动脚本（最可靠）

如果方案 1 仍然失败，使用 `start.sh` 启动脚本：

1. **脚本位置**: `/app/start.sh` (项目根目录)

2. **脚本内容**:
   ```bash
   #!/bin/bash
   set -e

   cd /app
   source .venv/bin/activate

   # 验证 granian 可用
   if ! command -v granian &> /dev/null; then
       echo "ERROR: granian not found"
       exit 1
   fi

   exec reflex run --env prod --loglevel info
   ```

3. **修改 nixpacks.toml**:
   ```toml
   [start]
   cmd = "bash /app/start.sh"
   ```

4. **确保脚本可执行**:
   ```bash
   chmod +x start.sh
   ```

## 验证步骤

部署后检查日志：

### 成功的日志应该显示：

```
=========================================
Starting Reflex Application
=========================================
Activating virtual environment at /app/.venv
Virtual environment activated successfully

Environment Information:
----------------------------------------
Python: /app/.venv/bin/python
Python version: Python 3.12.x
Reflex: /app/.venv/bin/reflex
Granian: /app/.venv/bin/granian
VIRTUAL_ENV: /app/.venv
PATH: /app/.venv/bin:...
----------------------------------------

All checks passed. Starting Reflex server...
=========================================

App running at: http://0.0.0.0:3000/
Backend running at: http://0.0.0.0:8000
Serving app at: http://0.0.0.0:8000
```

### 失败的日志会显示：

```
ERROR: granian not found in PATH
Current PATH: /usr/local/bin:/usr/bin:/bin
Python location: /root/.nix-profile/bin/python
```

## 工作原理

### 虚拟环境激活做了什么

当执行 `. .venv/bin/activate` 时：

1. **修改 PATH** - 将 `.venv/bin` 添加到 PATH 开头
   ```bash
   PATH="/app/.venv/bin:$PATH"
   ```

2. **设置 VIRTUAL_ENV** - 标识当前激活的虚拟环境
   ```bash
   VIRTUAL_ENV="/app/.venv"
   ```

3. **修改 PS1** - 改变命令提示符（可选）
   ```bash
   PS1="(.venv) $PS1"
   ```

4. **deactivate 函数** - 提供退出虚拟环境的方法

### 子进程继承

- Python 的 `subprocess.Popen()` 会继承父进程的完整环境
- 包括 PATH、VIRTUAL_ENV 等所有环境变量
- 当 Reflex 启动 granian 时，granian 能在继承的 PATH 中被找到

## 故障排除

### 如果仍然失败

1. **检查 granian 是否安装**:
   ```bash
   # 进入 Coolify 容器
   docker exec -it <container-id> bash

   # 激活虚拟环境
   source /app/.venv/bin/activate

   # 检查 granian
   which granian
   pip list | grep granian
   ```

2. **手动测试启动**:
   ```bash
   # 在容器中
   cd /app
   source .venv/bin/activate
   reflex run --env prod
   ```

3. **检查环境变量**:
   ```bash
   echo $PATH
   echo $VIRTUAL_ENV
   ```

### 常见错误

| 错误 | 原因 | 解决方案 |
|------|------|---------|
| `granian not found` | PATH 没有包含 .venv/bin | 确保正确激活虚拟环境 |
| `No module named 'granian'` | granian 未安装 | 检查 install 阶段是否成功 |
| `Permission denied` | start.sh 没有执行权限 | 运行 `chmod +x start.sh` |
| `activate: No such file` | 虚拟环境未创建 | 检查 install 阶段日志 |

## 相关文件

- **`/mnt/d/工作区/云开发/working/nixpacks.toml`** - Nixpacks 构建配置
- **`/mnt/d/工作区/云开发/working/start.sh`** - 启动脚本
- **`/mnt/d/工作区/云开发/working/rxconfig.py`** - Reflex 应用配置

## 参考资源

- **Reflex 部署文档**: https://reflex.dev/docs/hosting/self-hosting/
- **Granian 文档**: https://github.com/emmett-framework/granian
- **Python venv 文档**: https://docs.python.org/3/library/venv.html
- **Nixpacks 文档**: https://nixpacks.com/docs
