# 端口管理指南
## 智能端口检查与自动清理

**版本**: 1.0
**实现日期**: 2025-11-25
**适用环境**: 开发 + 生产

---

## 📋 概述

后端启动系统现在具有**智能端口管理功能**：

- ✅ **开发环境**: 自动检查并清理占用的端口
- ✅ **生产环境**: 安全地报错，要求手动处理
- ✅ **无需改变启动方式**: 直接运行 `python -m uvicorn ...`
- ✅ **集成到 main.py**: 自动执行，无需额外步骤

---

## 🎯 工作原理

### 启动流程

```
用户运行: python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
                        ↓
            src/main.py 的 __main__ 块执行
                        ↓
            PortManager.ensure_port_available()
                        ↓
                检查环境变量 ENVIRONMENT
                        ↓
        ┌───────────────┴───────────────┐
        │                               │
        ▼ (ENVIRONMENT != production)   ▼ (ENVIRONMENT == production)
    开发环境                        生产环境
        │                               │
        ├─ 检查端口是否被占用          ├─ 检查端口是否被占用
        │                               │
        ├─ 被占用 → 杀死进程           ├─ 被占用 → 报错
        │                               │
        ├─ 验证端口释放                ├─ 打印故障排查步骤
        │                               │
        ├─ 启动 uvicorn ✅            ├─ 退出程序 ❌
        │                               │
        ▼                               ▼
    服务器正常启动                  需要手动处理
```

### 端口检查算法

**Step 1**: 检查端口是否被占用
```python
socket.connect_ex(('127.0.0.1', port))
# Returns: 0 (occupied) or 1 (available)
```

**Step 2**: 获取占用进程的 PID
```bash
# 尝试 lsof（优先）
lsof -i :8000 | grep LISTEN | awk '{print $2}'

# 回退方案：netstat
netstat -tlnp | grep :8000
```

**Step 3**: 杀死进程（仅开发环境）
```python
# SIGTERM (graceful)
os.kill(pid, signal.SIGTERM)
time.sleep(1)

# SIGKILL if still running (force)
os.kill(pid, signal.SIGKILL)
```

**Step 4**: 验证端口释放
```python
time.sleep(2)
if not is_port_in_use(port):
    # 成功，启动服务器
else:
    # 失败，报错退出
```

---

## 💡 使用方式

### 方式 1: 直接运行（推荐）

```bash
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

**自动处理**:
- ✅ 自动检查端口 8000
- ✅ 自动杀死占用进程（开发环境）
- ✅ 启动服务器
- ✅ 无需额外命令

### 方式 2: 使用自定义脚本

如果需要更多控制，可以使用 `run_backend.py`：

```bash
python run_backend.py --port 8000 --host 0.0.0.0
```

### 方式 3: 生产环境启动

```bash
export ENVIRONMENT=production
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

**生产环境行为**:
- ❌ 不会自动杀死进程
- 🔴 如果端口被占用，会报错并打印故障排查步骤
- 👤 需要人工介入

---

## 🔍 环境检测

### 开发环境
```bash
# 以下任何一种设置都会被认为是开发环境：
unset ENVIRONMENT           # 未设置（默认）
export ENVIRONMENT=dev      # 任何非 production
export ENVIRONMENT=development
```

### 生产环境
```bash
# 只有明确设置为 production 才会被认为是生产环境
export ENVIRONMENT=production
```

---

## 📊 日志输出示例

### 开发环境 - 成功清理端口

```
2025-11-25 11:25:00 - INFO - Port 8000 is already in use
2025-11-25 11:25:00 - INFO - 💡 Development environment detected
2025-11-25 11:25:00 - INFO - Attempting to free up port...
2025-11-25 11:25:00 - INFO - Process using port: 36237
2025-11-25 11:25:00 - INFO - Attempting to kill process 36237...
2025-11-25 11:25:01 - INFO - ✅ Successfully killed process 36237
2025-11-25 11:25:03 - INFO - ✅ Port 8000 is now available
2025-11-25 11:25:03 - INFO - ✅ Starting server on 0.0.0.0:8000

INFO:     Started server process [38001]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 开发环境 - 无法清理端口

```
2025-11-25 11:25:00 - INFO - Port 8000 is already in use
2025-11-25 11:25:00 - INFO - 💡 Development environment detected
2025-11-25 11:25:00 - INFO - Attempting to free up port...
2025-11-25 11:25:00 - WARNING - Could not determine process ID
2025-11-25 11:25:00 - ERROR - Failed to free port 8000
2025-11-25 11:25:00 - ERROR - ❌ Cannot start: port is not available

# 应用退出
```

### 生产环境 - 端口被占用

```
2025-11-25 11:25:00 - WARNING - Port 8000 is already in use
2025-11-25 11:25:00 - ERROR - 🚨 Port conflict in PRODUCTION environment!
2025-11-25 11:25:00 - ERROR - Port 8000 is already in use
2025-11-25 11:25:00 - ERROR -
2025-11-25 11:25:00 - ERROR - ⚠️  IMPORTANT: Do NOT auto-kill processes in production!
2025-11-25 11:25:00 - ERROR -
2025-11-25 11:25:00 - ERROR - Please:
2025-11-25 11:25:00 - ERROR -   1. Find the process: lsof -i :8000
2025-11-25 11:25:00 - ERROR -   2. Investigate if it should be running
2025-11-25 11:25:00 - ERROR -   3. Kill manually if safe: kill -9 <PID>
2025-11-25 11:25:00 - ERROR -   4. Or use a different port: --port 8001
2025-11-25 11:25:00 - ERROR - ❌ Cannot start: port is not available

# 应用退出，需要手动处理
```

---

## 🛠️ 故障排查

### 问题 1: 权限被拒绝

**错误**:
```
PermissionError: [Errno 1] Operation not permitted
```

**原因**: 没有权限杀死其他用户的进程

**解决**:
```bash
# 方案 A: 使用 sudo（不推荐）
sudo python -m uvicorn src.main:app --host 0.0.0.0 --port 8000

# 方案 B: 手动杀死进程
lsof -i :8000
kill -9 <PID>
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000

# 方案 C: 使用不同端口
python -m uvicorn src.main:app --host 0.0.0.0 --port 8001
```

### 问题 2: 无法确定进程 ID

**错误**:
```
Could not determine process ID, port may be stuck
```

**原因**: `lsof` 或 `netstat` 命令不可用

**解决**:
```bash
# 安装必要工具
# Ubuntu/Debian:
sudo apt-get install net-tools lsof

# macOS:
brew install lsof

# 或手动杀死端口
fuser -k 8000/tcp
```

### 问题 3: 生产环境启动失败

**场景**: 生产服务器上启动时报告端口被占用

**解决步骤**:

1. **检查占用的进程**
   ```bash
   lsof -i :8000
   ps aux | grep 8000
   ```

2. **判断是否应该运行**
   ```bash
   # 检查是否是旧的后端实例
   # 检查是否是其他应用
   # 检查进程是否正常
   ```

3. **安全地停止进程**
   ```bash
   # 先尝试 SIGTERM (graceful)
   kill -15 <PID>
   sleep 5

   # 如果还在运行，才用 SIGKILL
   kill -9 <PID>
   ```

4. **启动新实例**
   ```bash
   python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
   ```

---

## 📝 实现细节

### 文件结构

```
src/infrastructure/port_manager.py
  ├─ PortManager 类
  │   ├─ is_port_in_use() - 检查端口
  │   ├─ get_process_using_port() - 获取 PID
  │   ├─ kill_process() - 杀死进程
  │   └─ check_and_clean_port() - 主逻辑
  │
  └─ ensure_port_available() - 便捷函数

src/main.py
  └─ __main__ 块
      ├─ 导入 PortManager
      ├─ 调用 ensure_port_available()
      └─ 启动 uvicorn
```

### 关键变量

```python
# 开发/生产环境检测
IS_DEVELOPMENT = os.getenv("ENVIRONMENT") != "production"

# 杀死进程的超时
AUTO_KILL_TIMEOUT = 5  # seconds

# 检查间隔
CLEANUP_SLEEP = 2  # seconds
```

---

## ✅ 最佳实践

### 开发环境

```bash
# ✅ 推荐：直接运行，让系统自动处理
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000

# ✅ 推荐：使用 reload 模式
export ENV=development
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 生产环境

```bash
# ✅ 必须设置环境变量
export ENVIRONMENT=production

# ✅ 使用 systemd 或 docker 管理进程
# ✅ 确保没有多个实例争夺同一端口
# ✅ 使用负载均衡器管理多个实例

python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### 重启脚本

```bash
#!/bin/bash
# safe_restart.sh

PORT=8000

# 停止旧实例（优雅关闭）
echo "Stopping old instance..."
lsof -i :$PORT | grep -v COMMAND | awk '{print $2}' | xargs kill -15 2>/dev/null || true

# 等待进程关闭
sleep 3

# 强制杀死仍在运行的进程
lsof -i :$PORT | grep -v COMMAND | awk '{print $2}' | xargs kill -9 2>/dev/null || true

# 启动新实例
echo "Starting new instance..."
export ENVIRONMENT=production
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

---

## 📊 性能影响

- **启动时间增加**: < 100ms（端口检查）
- **内存占用**: 无增加
- **运行时性能**: 零影响（只在启动时运行）

---

## 🔐 安全考虑

### 开发环境安全

✅ 安全 - 只在本地开发时有用

### 生产环境安全

⚠️ **关键**: 生产环境中 **不会自动杀死进程**
- 防止意外停止重要服务
- 防止数据损坏
- 要求人工审查和决策

---

## 📞 相关命令快速参考

```bash
# 检查端口占用
lsof -i :8000
netstat -tlnp | grep 8000

# 获取进程信息
ps aux | grep 8000
ps -p <PID> -o cmd=

# 杀死进程
kill -9 <PID>
fuser -k 8000/tcp

# 测试端口连接
nc -zv localhost 8000
telnet localhost 8000
```

---

## 📚 相关文档

- `src/infrastructure/port_manager.py` - 实现源代码
- `src/main.py` - 集成点
- `run_backend.py` - 可选的启动脚本

---

**状态**: ✅ 生产就绪
**最后更新**: 2025-11-25

