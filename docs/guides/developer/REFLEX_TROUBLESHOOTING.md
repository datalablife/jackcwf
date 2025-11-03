# Reflex 开发服务器故障排除指南

## 概述

本文档记录在使用 Reflex 0.8.16 + uv 虚拟环境配置下遇到的常见问题及解决方案。

---

## 问题 1: Worker 重启循环 ("Killing worker-0")

### 症状
- 服务器初始启动正常，编译完成
- 启动后 5-10 分钟内，出现警告：`[WARNING] Killing worker-0 after it refused to gracefully stop`
- 之后陷入无限循环：自动重新编译 → Worker 崩溃 → 再次编译
- 循环持续数小时直至进程 killed

### 根本原因分析
1. **文件监听触发**: `.web/` 目录生成的编译产物被文件监听系统检测到，触发再次编译
2. **Worker 进程崩溃**: Worker 在处理热重载时可能遇到资源竞争或内存问题
3. **级联效应**: 编译 → 生成文件 → 触发监听 → 编译 → 循环

### 解决方案

#### 方案 A: 清理缓存后重启 ✅ 推荐

```bash
# 1. 停止服务器（如果还在运行）
pkill -f "reflex run" -9

# 2. 清理编译缓存
rm -rf .web .reflex

# 3. 重新启动
uv run reflex run
```

**预期结果**: 服务器应该稳定启动，不再有worker重启警告。

#### 方案 B: 升级 Reflex 版本

```bash
# 检查当前版本
uv pip show reflex

# 升级到最新版本 (0.8.17+)
uv add reflex --upgrade

# 重启服务器
uv run reflex run
```

**优势**: 最新版本可能已修复 worker 管理问题

#### 方案 C: 隔离前后端启动

如果上述方案不生效，可以分别启动前后端：

```bash
# 终端 1: 启动后端
uv run reflex run --backend-only

# 终端 2: 启动前端
uv run reflex run --frontend-only
```

**优势**: 便于隔离问题，哪个端出现问题可以单独诊断

### 预防措施

1. **定期清理缓存**: 每次启动前删除 `.web` 目录
2. **使用 git 忽略**: 确保 `.web` 和 `.reflex` 在 `.gitignore` 中
3. **避免编辑 .web 内容**: 不要手动修改 `.web` 目录下的文件

---

## 问题 2: 前后端通信延迟

### 症状
- 前端加载缓慢
- 控制台出现网络超时
- 状态更新响应慢

### 解决方案

#### 增加超时时间 (开发环境)

编辑 `rxconfig.py`:

```python
config = rx.Config(
    app_name="working",
    frontend_host="0.0.0.0",
    frontend_port=3000,
    backend_host="0.0.0.0",
    backend_port=8000,
    # 增加超时时间
    timeout=30,  # 默认 10 秒
)
```

#### 禁用热重载 (调试用)

```bash
# 禁用文件监听的热重载
uv run reflex run --no-watch
```

---

## 问题 3: 端口占用

### 症状
```
ERROR: Address already in use
Address [::]:3000 is already in use
```

### 解决方案

#### 查找占用进程
```bash
# 查看哪些进程占用了 3000 和 8000 端口
lsof -i :3000
lsof -i :8000

# 或使用 netstat
ss -tulpn | grep -E ":(3000|8000)"
```

#### 杀死占用进程
```bash
# 根据 PID 杀死进程（替换 <PID> 为实际进程号）
kill -9 <PID>

# 或直接杀死所有 reflex 相关进程
pkill -f "reflex run" -9
pkill -f "uv run" -9
```

#### 使用不同端口
```bash
# 如果 3000/8000 被占用，可以使用其他端口
uv run reflex run --frontend-port 3001 --backend-port 8001
```

⚠️ **注意**: CLAUDE.md 规定项目必须运行在 **3000/8000**，不允许自动转移到其他端口。必须先清理占用的进程。

---

## 问题 4: 编译失败

### 症状
```
[ERROR] Compilation failed: ...
Failed to compile components
```

### 常见原因和解决方案

#### 原因 1: 缺少依赖

```bash
# 重新同步虚拟环境
uv sync --refresh

# 清除缓存并重装
uv sync --clear-cache
```

#### 原因 2: Python 版本不兼容

```bash
# 检查 Python 版本
python --version

# 应该是 3.12+
# 如果版本过低，重新创建虚拟环境
uv python install 3.12
uv sync
```

#### 原因 3: Reflex 版本冲突

```bash
# 列出当前安装的包
uv pip show reflex

# 如果版本过旧，升级
uv add reflex --upgrade

# 清理并重建
rm -rf .web .reflex
uv run reflex build
```

---

## 问题 5: 数据库连接失败

### 症状
```
Failed to connect to PostgreSQL
psycopg2.OperationalError: could not connect to server
```

### 解决方案

#### 检查数据库状态
```bash
# 加载数据库配置
source .postgres_config

# 测试连接
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME
```

#### 检查连接字符串
确保 `pyproject.toml` 或环境变量中的数据库 URL 正确：

```python
DATABASE_URL = "postgresql://jackcwf888:Jack_00492300@host.docker.internal:5432/postgres"
```

#### 常见错误排查
- **host.docker.internal 无法解析**: WSL 中可能需要使用实际 IP 地址，或在 Windows 中需要使用 WSL IP
- **端口 5432 无法访问**: 检查防火墙规则或容器端口映射
- **认证失败**: 确认用户名和密码正确

详见 `POSTGRESQL_CONNECTION.md`

---

## 完整启动工作流

当遇到多个问题时，按以下步骤系统地启动：

```bash
# 1. 清理所有旧进程
pkill -f "reflex run" -9 || true
pkill -f "uv run" -9 || true
sleep 2

# 2. 清理缓存
rm -rf .web .reflex __pycache__ .pytest_cache
rm -rf .venv (可选，仅在严重问题时)

# 3. 重新同步环境
uv sync --refresh

# 4. 验证数据库连接
source .postgres_config
python test_postgres_connection.py

# 5. 启动开发服务器
uv run reflex run

# 6. 测试连接
# 浏览器访问: http://localhost:3000
# API 文档: http://localhost:8000/docs
```

---

## 性能优化建议

### 生产环境考虑

对于生产部署，避免使用 `reflex run` (用于开发)，而是：

```bash
# 构建生产版本
uv run reflex build

# 使用 gunicorn 或类似生产服务器
uv run gunicorn -w 4 .web.api:app
```

### 开发环境优化

```bash
# 禁用不必要的功能以加速开发
uv run reflex run --no-telemetry --loglevel info
```

---

## 日志分析

### 查看详细日志

```bash
# 获取 DEBUG 级别日志
uv run reflex run --loglevel debug 2>&1 | tee reflex.log

# 只查看错误
uv run reflex run 2>&1 | grep -i error
```

### 常见日志模式

| 日志 | 含义 | 处理方案 |
|------|------|---------|
| `Killing worker-0` | Worker 进程崩溃 | 见"问题1" |
| `Address already in use` | 端口被占用 | 见"问题3" |
| `Failed to compile` | 代码编译失败 | 见"问题4" |
| `Connection refused` | 无法连接后端 | 检查后端是否启动 |

---

## 快速参考

### 最常用命令

```bash
# 标准启动
uv run reflex run

# 清理缓存后启动
rm -rf .web && uv run reflex run

# 前后端分离启动
uv run reflex run --backend-only  # 终端1
uv run reflex run --frontend-only  # 终端2

# 测试后端
curl http://localhost:8000/docs

# 测试数据库
python test_postgres_connection.py
```

### 应急命令

```bash
# 杀死所有相关进程
pkill -f reflex -9; pkill -f uv -9

# 完全重置
rm -rf .web .reflex __pycache__
uv sync --clear-cache
uv run reflex run
```

---

## 获取帮助

1. **查看 Reflex 文档**: https://reflex.dev/docs
2. **检查日志文件**: 查看详细的错误堆栈跟踪
3. **隔离问题**: 分别启动前后端确定问题在哪一端
4. **清理重装**: 最后的手段，删除 `.venv` 重新创建

---

最后更新: 2025-10-27
Reflex 版本: 0.8.16+ (建议升级到 0.8.17+)
uv 版本: 0.9.2+
Python: 3.12+
