# 脚本中心

本目录包含项目开发、测试、部署和维护的各类脚本。

## 📂 脚本分类

### 🛠️ 开发脚本 (`dev/`)
用于本地开发的辅助脚本

| 脚本 | 用途 | 用法 |
|------|------|------|
| `setup-env.sh` | 初始化开发环境 | `./dev/setup-env.sh` |
| `run-app.sh` | 启动应用 | `./dev/run-app.sh` |
| `format-code.sh` | 代码格式化 | `./dev/format-code.sh` |
| `lint-code.sh` | 代码检查 | `./dev/lint-code.sh` |
| `update-deps.sh` | 更新依赖 | `./dev/update-deps.sh` |
| `create-directory-structure.sh` | 创建目录结构 | `./dev/create-directory-structure.sh` |

### ✅ 测试脚本 (`test/`)
用于运行测试套件的脚本

| 脚本 | 用途 | 用法 |
|------|------|------|
| `run-all-tests.sh` | 运行全部测试 | `./test/run-all-tests.sh` |
| `run-unit-tests.sh` | 运行单元测试 | `./test/run-unit-tests.sh` |
| `run-integration-tests.sh` | 运行集成测试 | `./test/run-integration-tests.sh` |
| `run-e2e-tests.sh` | 运行端到端测试 | `./test/run-e2e-tests.sh` |
| `coverage-report.sh` | 生成覆盖率报告 | `./test/coverage-report.sh` |

### 🚀 部署脚本 (`deploy/`)
用于各种环境部署的脚本

| 脚本 | 用途 | 用法 |
|------|------|------|
| `deploy-dev.sh` | 部署到开发环境 | `./deploy/deploy-dev.sh` |
| `deploy-staging.sh` | 部署到测试环境 | `./deploy/deploy-staging.sh` |
| `deploy-production.sh` | 部署到生产环境 | `./deploy/deploy-production.sh` |
| `rollback.sh` | 回滚部署 | `./deploy/rollback.sh [版本]` |
| `health-check.sh` | 健康检查 | `./deploy/health-check.sh [环境]` |

### 🔧 维护脚本 (`maintenance/`)
用于系统维护的脚本

| 脚本 | 用途 | 用法 |
|------|------|------|
| `backup-database.sh` | 数据库备份 | `./maintenance/backup-database.sh` |
| `cleanup-logs.sh` | 清理日志 | `./maintenance/cleanup-logs.sh [天数]` |
| `migrate-database.sh` | 数据库迁移 | `./maintenance/migrate-database.sh [版本]` |
| `sync-config.sh` | 配置同步 | `./maintenance/sync-config.sh` |

### 🛠️ 工具脚本 (`tools/`)
通用的工具脚本

| 脚本 | 用途 | 用法 |
|------|------|------|
| `file-organizer.sh` | 文件组织工具 | `./tools/file-organizer.sh [目录]` |
| `report-generator.sh` | 报告生成 | `./tools/report-generator.sh [类型]` |
| `data-processor.sh` | 数据处理 | `./tools/data-processor.sh [文件]` |
| `batch-operations.sh` | 批量操作 | `./tools/batch-operations.sh [操作]` |
| `coolify_postgres_manage.sh` | Coolify PostgreSQL 管理 | `./tools/coolify_postgres_manage.sh` |

### 🗄️ 数据库脚本 (`database/`)
数据库管理脚本

| 脚本 | 用途 | 用法 |
|------|------|------|
| `init-db.sh` | 初始化数据库 | `./database/init-db.sh` |
| `seed-data.sh` | 导入测试数据 | `./database/seed-data.sh` |
| `export-data.sh` | 导出数据 | `./database/export-data.sh [表名]` |
| `validate-schema.sh` | 验证数据库模式 | `./database/validate-schema.sh` |
| `test_postgres_connection.py` | 测试 PostgreSQL 连接 | `./database/test_postgres_connection.py` |

### ⚙️ CI/CD 脚本 (`ci/`)
持续集成和持续部署脚本

| 脚本 | 用途 | 用法 |
|------|------|------|
| `pre-commit.sh` | 提交前检查 | 自动执行（Git Hook） |
| `run-ci.sh` | CI 流程 | `./ci/run-ci.sh` |
| `run-cd.sh` | CD 流程 | `./ci/run-cd.sh` |
| `notify-status.sh` | 通知脚本 | `./ci/notify-status.sh [状态]` |

### 📚 工具函数库 (`utils/`)
脚本中的公共函数库

| 文件 | 用途 | 说明 |
|------|------|------|
| `logger.sh` | 日志工具 | 提供 log_info, log_error 等函数 |
| `validators.sh` | 验证工具 | 提供数据验证函数 |
| `common.sh` | 通用函数 | 常用的辅助函数 |
| `config-parser.sh` | 配置解析 | 解析配置文件 |

---

## 🚀 快速开始

### 1. 初始化环境

```bash
# 进入 scripts 目录
cd scripts

# 设置所有脚本的执行权限
chmod +x **/*.sh

# 初始化开发环境
./dev/setup-env.sh
```

### 2. 运行应用

```bash
# 启动应用
./dev/run-app.sh

# 应用将运行在 http://localhost:3000
```

### 3. 运行测试

```bash
# 运行全部测试
./test/run-all-tests.sh

# 或运行特定测试
./test/run-unit-tests.sh
./test/run-integration-tests.sh
./test/run-e2e-tests.sh

# 生成覆盖率报告
./test/coverage-report.sh
```

### 4. 部署应用

```bash
# 部署到开发环境
./deploy/deploy-dev.sh

# 部署到测试环境
./deploy/deploy-staging.sh

# 部署到生产环境
./deploy/deploy-production.sh

# 执行健康检查
./deploy/health-check.sh production
```

---

## 📋 脚本命名规范

所有脚本遵循以下规范：

### 文件名格式
- 小写字母和连字符: `run-app.sh` ✓，不要用 `RunApp.sh` ✗
- 动词开头: `run-app.sh` ✓，不要用 `app-run.sh` ✗
- 脚本加 `.sh` 后缀
- 避免缩写: `setup-env.sh` ✓，不要用 `setup-e.sh` ✗

### 脚本头部格式

```bash
#!/bin/bash
# 脚本简要说明
#
# 详细说明（可选）
#
# 用法: ./script-name.sh [参数]
# 示例: ./script-name.sh arg1 arg2
#
# 参数说明（如有）:
#   arg1 - 参数1的说明
#   arg2 - 参数2的说明

set -euo pipefail

# 导入通用函数
source "$(dirname "$0")/../utils/logger.sh"
source "$(dirname "$0")/../utils/common.sh"

# 主函数
main() {
    log_info "开始执行脚本..."
    # 脚本逻辑
    log_info "执行完成"
}

# 错误处理
trap 'log_error "脚本执行失败"' ERR

main "$@"
```

---

## 📝 脚本编写指南

### 基本结构

```bash
#!/bin/bash
# 脚本说明

set -euo pipefail  # 严格模式

# 导入工具函数
source "$(dirname "$0")/../utils/logger.sh"

# 定义常量
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 定义函数
function setup() {
    log_info "设置..."
}

function cleanup() {
    log_info "清理..."
}

# 主函数
function main() {
    log_info "开始执行"
    setup
    # 主逻辑
    cleanup
}

# 错误处理
trap cleanup EXIT
trap 'log_error "脚本失败"; exit 1' ERR

# 执行
main "$@"
```

### 使用日志工具

```bash
source "$(dirname "$0")/../utils/logger.sh"

log_info "信息消息"      # 蓝色
log_success "成功消息"    # 绿色
log_warning "警告消息"    # 黄色
log_error "错误消息"      # 红色
log_debug "调试消息"      # 灰色
```

### 使用验证工具

```bash
source "$(dirname "$0")/../utils/validators.sh"

# 检查文件是否存在
if ! file_exists "/path/to/file"; then
    log_error "文件不存在"
    exit 1
fi

# 检查目录是否存在
if ! dir_exists "/path/to/dir"; then
    log_error "目录不存在"
    exit 1
fi

# 检查命令是否存在
if ! command_exists "docker"; then
    log_error "Docker 未安装"
    exit 1
fi
```

---

## 🔍 调试脚本

### 启用调试模式

```bash
# 运行脚本时启用调试
bash -x scripts/dev/run-app.sh

# 或在脚本中添加
set -x  # 启用调试
set +x  # 禁用调试
```

### 常见问题

#### 权限被拒绝
```bash
# 解决方案：设置执行权限
chmod +x scripts/dev/run-app.sh
```

#### 命令未找到
```bash
# 检查脚本中的 source 路径
# 确保路径相对于脚本位置正确
source "$(dirname "$0")/../utils/logger.sh"
```

#### 变量未定义
```bash
# 在脚本头部添加严格模式
set -u  # 禁止使用未定义的变量

# 检查 source 的文件中是否定义了该变量
```

---

## 📦 输出文件管理

脚本生成的输出文件存放在 `output/` 目录：

```
scripts/
├── output/
│   ├── coverage-reports/  # 测试覆盖率报告
│   ├── build-logs/        # 构建日志
│   ├── deployment-logs/   # 部署日志
│   └── data-exports/      # 数据导出
```

**重要**: `output/` 目录中的文件不应提交到 Git，已添加到 `.gitignore`

---

## 🤝 脚本贡献规范

创建新脚本时：

1. ✓ 遵循命名规范
2. ✓ 添加详细的头部说明
3. ✓ 使用工具函数库中的函数
4. ✓ 包含错误处理
5. ✓ 添加日志记录
6. ✓ 测试脚本的所有路径
7. ✓ 更新本文档
8. ✓ 设置执行权限

---

## 📚 相关文档

- [开发指南](../docs/guides/developer/)
- [部署指南](../docs/deployment/)
- [贡献指南](../docs/guides/developer/contributing.md)

---

**最后更新**: 2025-10-27
**版本**: 1.0.0
**维护者**: 项目团队
