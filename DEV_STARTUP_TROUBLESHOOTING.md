# 🔧 Dev Startup Troubleshooting Guide

**执行时间**: 2025-11-15
**执行命令**: `bash scripts/dev.sh`
**最终状态**: ✅ 已识别问题，提供解决方案

---

## 📋 执行日志分析

### 问题 1（已修复）：Shell 语法错误 ❌→✅

**错误信息：**
```
scripts/dev.sh: line 102: export: `http://localhost:3000]': not a valid identifier
```

**根本原因：**
- `.env` 文件第 26 行包含特殊字符（方括号）
- `export $(grep...|xargs)` 方法无法正确处理

**修复方案：**
- ✅ 改用 `set -a && source .env && set +a` 方法
- ✅ 修复 `.env` 文件中的引号问题

**验证状态：** ✅ 已解决

---

### 问题 2（已修复）：.env 引号错误 ❌→✅

**错误信息：**
```
.env: line 20: Data: command not found
```

**根本原因：**
- `.env` 中 `APP_NAME=AI Data Analyzer` 包含空格但未被引号包围
- `source .env` 试图执行这一行，shell 将其解析为命令

**修复方案：**
- ✅ 添加引号：`APP_NAME="AI Data Analyzer"`
- ✅ 修复所有包含空格的值

**验证状态：** ✅ 已解决

---

### 问题 3（待解决）：交互式提示阻塞 ❌

**错误信息：**
```
Database connection failed: No module named 'asyncpg'
[WARN] Database connection failed. Continue anyway? (y/n)
```

**根本原因：**
- 脚本检查数据库连接时失败
- 脚本停在交互式提示处，等待用户输入 `y` 或 `n`
- 无法自动化进行

**现象：**
- 脚本运行中断，卡在提示符处
- 无法继续启动后端和前端
- 自动化启动不可行

---

## ✅ 完整修复步骤

### 步骤 1：修复 scripts/dev.sh（已完成）

✅ **修改**：第 100-106 行
```bash
# 旧方式
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# 新方式
if [ -f ".env" ]; then
    log_info "Loading environment variables from .env..."
    set -a
    source .env
    set +a
fi
```

### 步骤 2：修复 .env 文件（已完成）

✅ **修改**：第 19-26 行
```env
# 旧方式
APP_NAME=AI Data Analyzer
APP_VERSION=0.1.0
DEBUG=true
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]

# 新方式
APP_NAME="AI Data Analyzer"
APP_VERSION="0.1.0"
DEBUG="true"
LOG_LEVEL="INFO"
CORS_ORIGINS='["http://localhost:5173", "http://localhost:3000"]'
```

### 步骤 3：修复数据库检查（需要做）

**问题：** 脚本在数据库连接失败时要求用户确认

**当前代码位置：** `scripts/dev.sh` 中的数据库检查函数

**解决方案：**
改为非交互模式，在开发环境中跳过数据库检查或使用 SQLite

**建议修改：**
```bash
# 在 scripts/dev.sh 中找到数据库检查部分
# 改为：
if [ "$ENVIRONMENT" = "development" ]; then
    log_info "Skipping database check in development mode"
else
    # 生产环境需要检查
    check_database_connection || exit 1
fi
```

---

## 🎯 当前启动状态

### 已解决的问题 ✅

1. ✅ Shell 语法错误（第 102 行）
2. ✅ 环境变量引号错误（.env 文件）

### 待解决的问题 ⚠️

1. ⚠️ 数据库检查交互式提示（阻塞启动）
2. ⚠️ asyncpg 模块缺失错误

---

## 🔍 问题分析：为什么会有 asyncpg 错误？

### 可能原因 1：虚拟环境未更新
```bash
# 症状：`No module named 'asyncpg'`
# 原因：uv sync 没有正确安装依赖
# 解决：
uv sync --force-reinstall
```

### 可能原因 2：虚拟环境隔离问题
```bash
# 症状：模块安装了但在 source .env 时找不到
# 原因：虚拟环境未激活
# 解决：
source .venv/bin/activate
python -m pip install asyncpg
```

### 可能原因 3：Python 路径不一致
```bash
# 检查当前 Python
which python
python --version

# 检查虚拟环境
ls -la .venv/bin/python*

# 激活虚拟环境后检查
source .venv/bin/activate
which python
python -m pip list | grep asyncpg
```

---

## 📝 推荐的完整修复流程

### Phase 1：清理和重建环境

```bash
# 1. 停止所有正在运行的进程
pkill -f "uvicorn\|npm" || true

# 2. 清除旧的虚拟环境
rm -rf .venv

# 3. 重新同步依赖
uv sync --force-reinstall

# 4. 验证 asyncpg 已安装
uv run python -m pip list | grep asyncpg
```

### Phase 2：修改脚本使其非交互

```bash
# 编辑 scripts/dev.sh，找到数据库检查部分
# 改为跳过检查或使用非交互模式
```

### Phase 3：再次尝试启动

```bash
bash scripts/dev.sh
```

---

## 🚨 快速诊断命令

```bash
# 1. 检查虚拟环境
echo "Virtual environment path:"
ls -la .venv/bin/python

# 2. 检查 asyncpg 安装
echo "Checking asyncpg:"
.venv/bin/python -m pip list | grep asyncpg

# 3. 验证导入
echo "Testing import:"
.venv/bin/python -c "import asyncpg; print('asyncpg OK')"

# 4. 检查 .env 文件语法
echo "Checking .env syntax:"
bash -n <(cat .env | grep -v '^#' | grep -v '^$')

# 5. 模拟 source .env
echo "Testing source .env:"
(set -a; source .env; set +a; echo "CORS_ORIGINS=$CORS_ORIGINS")
```

---

## 💡 建议的启动方式变更

### 当前方式（有交互提示）
```bash
bash scripts/dev.sh  # 会卡在数据库检查处
```

### 推荐方式（非交互，开发友好）

**方案 A：跳过数据库检查**
```bash
# 创建环境变量跳过检查
SKIP_DB_CHECK=true bash scripts/dev.sh
```

**方案 B：手动启动服务**
```bash
# 终端 1：后端
uv run python -m uvicorn backend.src.main:app --reload --port 8000

# 终端 2：前端
npm run dev --prefix frontend
```

**方案 C：修改脚本配置**
编辑 `scripts/dev.sh`，在 ENVIRONMENT 变量中设置：
```bash
SKIP_DB_CHECK_IN_DEV=true
```

---

## 📊 总结表

| 问题 | 状态 | 修复方案 | 优先级 |
|------|------|---------|--------|
| Shell 语法错误 | ✅ 已修复 | 改用 source .env | 高 |
| .env 引号错误 | ✅ 已修复 | 添加引号 | 高 |
| 交互式提示阻塞 | ⚠️ 待修复 | 跳过或非交互 | 高 |
| asyncpg 模块缺失 | ⚠️ 调查中 | 重新安装依赖 | 中 |

---

## 🎯 下一步推荐行动

### 立即执行（5 分钟）
1. ✅ 查看修复后的 `scripts/dev.sh` 和 `.env` 文件
2. ✅ 运行诊断命令验证环境

### 短期执行（15 分钟）
1. 修改 scripts/dev.sh 中的数据库检查部分（非交互）
2. 重新运行 `bash scripts/dev.sh`
3. 验证前后端启动成功

### 如果仍然失败
1. 使用方案 B（手动启动各服务）
2. 收集日志进行进一步调试

---

**文档生成时间**: 2025-11-15
**修复状态**: 2/3 问题已解决（67%）
**预计完成时间**: < 15 分钟

