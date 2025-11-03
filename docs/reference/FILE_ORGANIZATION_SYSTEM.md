# 项目文件归档系统设计

## 目录

1. [docs 目录结构](#docs-目录结构)
2. [scripts 目录结构](#scripts-目录结构)
3. [项目根目录规则](#项目根目录规则)
4. [开发工作流](#开发工作流)
5. [实施清单](#实施清单)

---

## docs 目录结构

### 完整目录树

```
docs/
├── README.md                          # 文档导航索引
├── api/                               # API 文档
│   ├── README.md                      # API 文档总览
│   ├── endpoints/                     # API 端点文档
│   │   ├── authentication.md          # 认证相关 API
│   │   ├── users.md                   # 用户管理 API
│   │   └── resources.md               # 资源管理 API
│   ├── schemas/                       # 数据模型文档
│   │   ├── request-schemas.md         # 请求数据结构
│   │   └── response-schemas.md        # 响应数据结构
│   └── errors/                        # 错误码文档
│       └── error-codes.md             # 错误码列表和说明
├── architecture/                      # 架构设计文档
│   ├── README.md                      # 架构概览
│   ├── system-overview.md             # 系统总体架构
│   ├── database-schema.md             # 数据库设计
│   ├── component-design.md            # 组件设计
│   ├── state-management.md            # 状态管理架构
│   ├── diagrams/                      # 架构图表
│   │   ├── system-flow.png            # 系统流程图
│   │   ├── database-erd.png           # 数据库 ERD
│   │   └── component-hierarchy.png    # 组件层级图
│   └── decisions/                     # 架构决策记录 (ADR)
│       ├── 001-choose-reflex.md       # ADR: 选择 Reflex 框架
│       ├── 002-state-pattern.md       # ADR: 状态管理模式
│       └── template.md                # ADR 模板
├── guides/                            # 用户和开发指南
│   ├── README.md                      # 指南索引
│   ├── user/                          # 用户指南
│   │   ├── getting-started.md         # 快速开始
│   │   ├── features.md                # 功能说明
│   │   └── faq.md                     # 常见问题
│   ├── developer/                     # 开发者指南
│   │   ├── setup.md                   # 开发环境搭建
│   │   ├── coding-standards.md        # 编码规范
│   │   ├── testing.md                 # 测试指南
│   │   ├── debugging.md               # 调试技巧
│   │   └── contributing.md            # 贡献指南
│   └── operations/                    # 运维指南
│       ├── monitoring.md              # 监控和告警
│       ├── backup-recovery.md         # 备份和恢复
│       └── troubleshooting.md         # 故障排除
├── deployment/                        # 部署文档
│   ├── README.md                      # 部署总览
│   ├── local.md                       # 本地部署
│   ├── staging.md                     # 测试环境部署
│   ├── production.md                  # 生产环境部署
│   ├── docker.md                      # Docker 部署
│   ├── coolify.md                     # Coolify 部署指南
│   ├── ci-cd.md                       # CI/CD 流程
│   └── rollback.md                    # 回滚策略
├── integrations/                      # 集成文档
│   ├── README.md                      # 集成概览
│   ├── postgresql.md                  # PostgreSQL 集成
│   ├── chrome-devtools.md             # ChromeDevTools MCP
│   ├── crewai.md                      # CrewAI 代码审查
│   ├── third-party-apis.md            # 第三方 API 集成
│   └── authentication-providers.md    # 认证提供商集成
├── reference/                         # 参考文档
│   ├── README.md                      # 参考索引
│   ├── configuration.md               # 配置参考
│   ├── environment-variables.md       # 环境变量
│   ├── cli-commands.md                # CLI 命令参考
│   └── dependencies.md                # 依赖清单
├── changelog/                         # 变更日志
│   ├── CHANGELOG.md                   # 主变更日志
│   └── versions/                      # 版本归档
│       ├── v0.1.0.md                  # 0.1.0 版本变更
│       └── v0.2.0.md                  # 0.2.0 版本变更
└── archived/                          # 归档文档
    ├── README.md                      # 归档说明
    ├── deprecated-features.md         # 已废弃功能
    └── old-architecture.md            # 旧架构文档
```

### 目录说明

#### 1. `docs/api/` - API 文档
**用途**: 存储所有 REST API、GraphQL 或 WebSocket 接口文档

**存储规则**:
- 按功能模块划分子目录（endpoints、schemas、errors）
- 使用 OpenAPI/Swagger 规范作为补充
- 包含请求/响应示例
- 标注认证要求和权限

**命名约定**:
- 文件名使用小写，单词用连字符分隔：`user-profile.md`
- 端点文档以资源名称命名：`users.md`、`posts.md`
- Schema 文档分为请求和响应：`request-schemas.md`、`response-schemas.md`

#### 2. `docs/architecture/` - 架构设计文档
**用途**: 存储系统架构、设计决策和技术选型文档

**存储规则**:
- 包含系统设计图表（使用 Mermaid、PlantUML 或图片）
- 记录架构决策记录（ADR - Architecture Decision Records）
- 数据库设计和 ER 图
- 组件交互和状态管理

**命名约定**:
- ADR 使用序号前缀：`001-choose-reflex.md`
- 图表文件使用描述性名称：`system-flow.png`
- 设计文档使用功能域命名：`state-management.md`

#### 3. `docs/guides/` - 用户和开发指南
**用途**: 分类存储不同受众的操作指南

**子目录**:
- `user/` - 面向最终用户的功能使用指南
- `developer/` - 面向开发者的编码和开发指南
- `operations/` - 面向运维人员的系统管理指南

**存储规则**:
- 使用循序渐进的教程风格
- 包含代码示例和截图
- 提供故障排除和常见问题解答

#### 4. `docs/deployment/` - 部署文档
**用途**: 存储所有环境的部署指南和配置

**存储规则**:
- 分别记录开发、测试、生产环境
- 包含环境变量配置示例
- 记录部署步骤和回滚流程
- 包含 Docker、Kubernetes、Coolify 等平台的具体指南

#### 5. `docs/integrations/` - 集成文档
**用途**: 记录与外部系统、服务和工具的集成

**存储规则**:
- 每个集成一个独立文档
- 包含配置步骤、API 密钥管理
- 记录集成测试方法
- 提供故障排除指南

#### 6. `docs/reference/` - 参考文档
**用途**: 快速查询的参考资料

**存储规则**:
- 配置选项完整列表
- 环境变量说明
- CLI 命令手册
- 依赖库版本和兼容性

#### 7. `docs/changelog/` - 变更日志
**用途**: 记录项目历史和版本变更

**存储规则**:
- 遵循 [Keep a Changelog](https://keepachangelog.com/) 格式
- 主文件 `CHANGELOG.md` 记录最近版本
- 旧版本归档到 `versions/` 子目录
- 使用语义化版本号：`v1.2.3`

#### 8. `docs/archived/` - 归档文档
**用途**: 存储过期但保留参考价值的文档

**存储规则**:
- 不再维护但保留历史
- 包含已废弃功能的文档
- 旧架构设计参考

### 文档命名约定

**规则**:
1. **全部小写** - 使用小写字母
2. **连字符分隔** - 单词之间用 `-` 分隔（不用下划线或空格）
3. **描述性命名** - 名称应清晰表达内容
4. **避免缩写** - 除非是广泛认可的缩写（API、REST、HTTP）
5. **版本号前缀** - 版本相关文档使用 `v` 前缀：`v1.0.0.md`
6. **序号前缀** - ADR 和教程使用三位数序号：`001-title.md`

**示例**:
- ✅ `user-authentication.md`
- ✅ `api-rate-limiting.md`
- ✅ `001-choose-database.md`
- ❌ `UserAuthentication.md`
- ❌ `api_rate_limiting.md`
- ❌ `1-choose-db.md`

### 文档版本管理策略

#### 主版本控制
- 所有文档提交到 Git 仓库
- 使用语义化版本标签：`v1.0.0`、`v1.1.0`
- 每个重大版本创建分支：`release/v1.0`

#### 文档版本策略
1. **当前版本** - 保存在主分支的 `docs/`
2. **历史版本** - 通过 Git 标签访问
3. **多版本支持** - 如需同时维护多个版本，在 `docs/versions/` 下创建子目录

#### 更新流程
```
1. 修改文档
2. 更新 CHANGELOG.md
3. 提交 Git
4. 代码审查（使用 CrewAI）
5. 合并主分支
6. 发布时打标签
```

---

## scripts 目录结构

### 完整目录树

```
scripts/
├── README.md                          # 脚本使用说明
├── dev/                               # 开发辅助脚本
│   ├── setup-env.sh                   # 开发环境初始化
│   ├── clean-cache.sh                 # 清理缓存文件
│   ├── reset-db.sh                    # 重置数据库
│   ├── seed-data.sh                   # 生成测试数据
│   ├── generate-mocks.py              # 生成 Mock 数据
│   └── reflex-helpers.sh              # Reflex 常用操作快捷脚本
├── test/                              # 测试相关脚本
│   ├── run-all-tests.sh               # 运行所有测试
│   ├── run-unit-tests.sh              # 运行单元测试
│   ├── run-integration-tests.sh       # 运行集成测试
│   ├── test-coverage.sh               # 生成测试覆盖率报告
│   ├── test-connection.py             # 测试数据库连接
│   └── benchmark.py                   # 性能基准测试
├── deploy/                            # 部署脚本
│   ├── build-docker.sh                # 构建 Docker 镜像
│   ├── deploy-staging.sh              # 部署到测试环境
│   ├── deploy-production.sh           # 部署到生产环境
│   ├── rollback.sh                    # 回滚脚本
│   ├── health-check.sh                # 健康检查
│   └── coolify-deploy.sh              # Coolify 部署脚本
├── maintenance/                       # 维护脚本
│   ├── backup-db.sh                   # 数据库备份
│   ├── restore-db.sh                  # 数据库恢复
│   ├── clean-logs.sh                  # 清理日志文件
│   ├── rotate-secrets.sh              # 轮换密钥
│   └── check-dependencies.py          # 检查依赖更新
├── tools/                             # 工具脚本
│   ├── analyze-bundle-size.sh         # 分析前端打包大小
│   ├── format-code.sh                 # 代码格式化
│   ├── lint-check.sh                  # 代码检查
│   ├── generate-docs.py               # 自动生成文档
│   ├── code-review.sh                 # 运行 CrewAI 代码审查
│   └── check-ports.sh                 # 检查端口占用
├── database/                          # 数据库管理脚本
│   ├── migrate.sh                     # 数据库迁移
│   ├── create-migration.sh            # 创建迁移文件
│   ├── rollback-migration.sh          # 回滚迁移
│   ├── export-schema.sh               # 导出数据库模式
│   └── postgres-manage.sh             # PostgreSQL 管理（现有的）
├── ci/                                # CI/CD 脚本
│   ├── pre-commit.sh                  # Git pre-commit 钩子
│   ├── pre-push.sh                    # Git pre-push 钩子
│   ├── validate-pr.sh                 # PR 验证
│   └── release.sh                     # 发布脚本
└── utils/                             # 通用工具函数
    ├── common.sh                      # Shell 脚本公共函数
    ├── colors.sh                      # 终端颜色输出
    ├── logging.sh                     # 日志工具函数
    └── validation.py                  # Python 验证工具
```

### 目录说明

#### 1. `scripts/dev/` - 开发辅助脚本
**用途**: 开发过程中频繁使用的辅助工具

**脚本类型**:
- 环境设置和初始化
- 缓存和临时文件清理
- 数据库重置和种子数据生成
- Mock 数据生成

**使用场景**:
- 新成员入职时运行 `setup-env.sh`
- 遇到缓存问题时运行 `clean-cache.sh`
- 需要重置开发环境时运行 `reset-db.sh`

#### 2. `scripts/test/` - 测试相关脚本
**用途**: 自动化测试执行和报告

**脚本类型**:
- 单元测试、集成测试、E2E 测试
- 测试覆盖率报告生成
- 性能基准测试
- 连接和健康检查测试

**使用场景**:
- 本地开发时运行 `run-unit-tests.sh`
- CI/CD 中运行 `run-all-tests.sh`
- 评估性能时运行 `benchmark.py`

#### 3. `scripts/deploy/` - 部署脚本
**用途**: 自动化部署流程

**脚本类型**:
- Docker 镜像构建
- 不同环境的部署脚本
- 回滚和健康检查
- 平台特定部署（Coolify、K8s 等）

**使用场景**:
- 部署到测试环境：`./deploy-staging.sh`
- 生产发布：`./deploy-production.sh`
- 紧急回滚：`./rollback.sh`

#### 4. `scripts/maintenance/` - 维护脚本
**用途**: 系统维护和管理任务

**脚本类型**:
- 数据库备份和恢复
- 日志清理和轮换
- 密钥和证书更新
- 依赖检查和更新

**使用场景**:
- 定期备份：`cron` 定时运行 `backup-db.sh`
- 日志清理：每周运行 `clean-logs.sh`
- 安全审计后运行 `rotate-secrets.sh`

#### 5. `scripts/tools/` - 工具脚本
**用途**: 开发工具和质量保证

**脚本类型**:
- 代码格式化和 Lint
- 文档生成
- 代码审查（CrewAI 集成）
- 打包分析

**使用场景**:
- 提交前运行 `format-code.sh` 和 `lint-check.sh`
- 功能完成后运行 `code-review.sh`
- 优化性能时运行 `analyze-bundle-size.sh`

#### 6. `scripts/database/` - 数据库管理脚本
**用途**: 数据库迁移和管理

**脚本类型**:
- 数据库迁移（使用 Alembic）
- Schema 导出和版本控制
- PostgreSQL 特定管理

**使用场景**:
- 修改数据库结构：`./create-migration.sh "add_user_table"`
- 应用迁移：`./migrate.sh`
- 回滚错误迁移：`./rollback-migration.sh`

#### 7. `scripts/ci/` - CI/CD 脚本
**用途**: 持续集成和持续部署

**脚本类型**:
- Git 钩子脚本
- PR 验证和自动化检查
- 自动发布流程

**使用场景**:
- 自动安装 Git 钩子
- GitHub Actions 中调用验证脚本
- 发布新版本时运行 `release.sh`

#### 8. `scripts/utils/` - 通用工具函数
**用途**: 可复用的脚本工具库

**脚本类型**:
- Shell 公共函数（日志、错误处理）
- 终端颜色输出
- 通用验证函数

**使用场景**:
- 其他脚本中 source 引用：`source utils/common.sh`

### 脚本命名约定

**规则**:
1. **全部小写** - 使用小写字母
2. **连字符分隔** - 单词之间用 `-` 分隔
3. **动词开头** - 使用动词表达操作：`run-tests.sh`、`deploy-app.sh`
4. **扩展名明确** - Shell 脚本用 `.sh`，Python 脚本用 `.py`
5. **描述性命名** - 清晰表达脚本功能

**示例**:
- ✅ `run-all-tests.sh`
- ✅ `backup-database.sh`
- ✅ `generate-mocks.py`
- ❌ `test.sh`（太模糊）
- ❌ `run_tests.sh`（使用下划线）
- ❌ `RunTests.sh`（大写）

### 脚本权限和执行规则

#### 文件权限
```bash
# 所有可执行脚本应设置执行权限
chmod +x scripts/**/*.sh
chmod +x scripts/**/*.py

# 工具函数库不需要执行权限
chmod 644 scripts/utils/*.sh
```

#### Shebang 规范
```bash
# Shell 脚本
#!/usr/bin/env bash

# Python 脚本
#!/usr/bin/env python3
```

#### 脚本头部模板
```bash
#!/usr/bin/env bash
#
# 脚本名称: run-all-tests.sh
# 描述: 运行项目的所有自动化测试
# 作者: Jack
# 日期: 2025-10-27
# 用法: ./run-all-tests.sh [--verbose] [--coverage]
#

set -euo pipefail  # 严格模式

# 加载公共函数
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../utils/common.sh"

# 脚本主逻辑...
```

#### 错误处理规范
```bash
# 使用 set 选项
set -e  # 遇到错误立即退出
set -u  # 使用未定义变量时报错
set -o pipefail  # 管道命令中任何失败都返回失败

# 提供有意义的错误消息
function handle_error() {
    echo "错误: $1" >&2
    exit 1
}

# 验证参数
[[ -z "${DATABASE_URL:-}" ]] && handle_error "DATABASE_URL 未设置"
```

#### 日志输出规范
```bash
# 使用不同级别的日志
function log_info() {
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $*"
}

function log_error() {
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $*" >&2
}

function log_success() {
    echo "[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $*"
}
```

---

## 项目根目录规则

### 允许在根目录的文件

#### 1. 项目元文件（必须）
```
README.md                   # 项目介绍和快速开始
CLAUDE.md                   # Claude Code 指导文件
LICENSE                     # 开源许可证
.gitignore                  # Git 忽略规则
```

#### 2. 配置文件（必须）
```
pyproject.toml              # Python 项目配置
uv.lock                     # uv 依赖锁定文件
rxconfig.py                 # Reflex 配置文件
requirements.txt            # Python 依赖（可选，uv 已替代）
.env.example                # 环境变量示例
```

#### 3. CI/CD 配置（必须）
```
.github/                    # GitHub Actions 配置
.gitlab-ci.yml              # GitLab CI 配置
Dockerfile                  # Docker 镜像构建文件
docker-compose.yml          # Docker Compose 配置
```

#### 4. 编辑器配置（可选）
```
.vscode/                    # VS Code 配置
.editorconfig               # 编辑器通用配置
*.code-workspace            # VS Code 工作区文件
```

### 必须归档的文件

#### 1. 文档类文件
```
❌ 根目录
POSTGRESQL_CONNECTION.md
POSTGRESQL_QUICK_START.md
REFLEX_WITH_UV.md
UV_GUIDE.md

✅ 正确位置
docs/integrations/postgresql.md
docs/guides/developer/setup.md
docs/reference/uv-guide.md
```

#### 2. 脚本类文件
```
❌ 根目录
coolify_postgres_manage.sh
test_postgres_connection.py

✅ 正确位置
scripts/database/postgres-manage.sh
scripts/test/test-connection.py
```

#### 3. 临时文件
```
❌ 根目录
progress.md
progress.archive.md
test_output.txt

✅ 正确位置
.temp/                      # 临时文件目录（加入 .gitignore）
.temp/progress.md
.temp/test_output.txt
```

### 根目录最终结构

```
working/
├── .claude/                        # Claude Code 配置
├── .github/                        # GitHub Actions
├── .venv/                          # Python 虚拟环境（忽略）
├── .web/                           # Reflex 前端生成文件（忽略）
├── assets/                         # 应用资源文件
├── code_review_crew/               # CrewAI 代码审查系统
├── docs/                           # 📄 所有文档
├── scripts/                        # 📜 所有脚本
├── working/                        # Reflex 应用代码
│   ├── components/                 # Reflex 组件
│   ├── pages/                      # 页面
│   ├── states/                     # 状态管理
│   └── __init__.py
├── tests/                          # 测试代码
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── .gitignore                      # Git 忽略规则
├── .env.example                    # 环境变量示例
├── CLAUDE.md                       # Claude 指导文件
├── README.md                       # 项目介绍
├── LICENSE                         # 开源许可证
├── pyproject.toml                  # Python 项目配置
├── uv.lock                         # 依赖锁定文件
└── rxconfig.py                     # Reflex 配置
```

### 特殊情况处理

#### 快速开始文档
- **原则**: 重要的快速开始信息应保留在根目录 `README.md`
- **详细文档**: 归档到 `docs/guides/user/getting-started.md`
- **示例**:
  ```markdown
  # README.md（简洁版）
  快速开始指南...详见 [完整文档](docs/guides/user/getting-started.md)
  ```

#### 多语言文档
- **位置**: `docs/i18n/`
- **结构**:
  ```
  docs/i18n/
  ├── en/                   # 英文文档
  ├── zh-CN/                # 简体中文文档
  └── zh-TW/                # 繁体中文文档
  ```

#### 临时实验文件
- **位置**: `.temp/`（加入 .gitignore）
- **用途**: 开发过程中的临时测试、草稿、实验代码
- **规则**: 不提交到 Git，定期清理

---

## 开发工作流

### 1. 代码生成时的文件放置规则

#### Reflex 应用代码
```python
# 新页面
working/pages/dashboard.py

# 新组件
working/components/sidebar.py

# 新状态
working/states/user_state.py

# 新工具函数
working/utils/helpers.py
```

#### 配置和脚本
```bash
# 新的数据库迁移脚本
scripts/database/migrations/001_create_users_table.py

# 新的测试
tests/unit/test_user_state.py
tests/integration/test_api.py

# 新的工具脚本
scripts/tools/new-tool.sh
```

### 2. 测试生成的临时文件处理

#### 测试输出文件
```bash
# 不要放在根目录！
❌ test_output.txt
❌ coverage.xml
❌ pytest_cache/

# 正确位置
✅ .temp/test_output.txt
✅ .temp/coverage/
✅ .pytest_cache/（已在 .gitignore）
```

#### .gitignore 配置
```gitignore
# 临时文件
.temp/
*.tmp
*.log

# 测试输出
.pytest_cache/
.coverage
htmlcov/
coverage.xml

# Reflex 生成文件
.web/
.states/

# Python
__pycache__/
*.pyc
.venv/

# 编辑器
.vscode/
.idea/
*.swp
```

### 3. 开发过程中的文档更新规范

#### 何时更新文档

**立即更新**:
- 新增 API 端点 → 更新 `docs/api/endpoints/`
- 修改配置选项 → 更新 `docs/reference/configuration.md`
- 修改数据库结构 → 更新 `docs/architecture/database-schema.md`

**定期更新**:
- 新增功能 → 更新 `docs/guides/user/features.md`
- Bug 修复 → 更新 `docs/changelog/CHANGELOG.md`
- 架构变更 → 更新 `docs/architecture/` 相关文档

**发布前更新**:
- 部署流程变更 → 更新 `docs/deployment/`
- 版本发布 → 更新 `CHANGELOG.md`

#### 文档更新工作流

```bash
# 1. 开发新功能
git checkout -b feature/new-dashboard

# 2. 编写代码
vim working/pages/dashboard.py

# 3. 编写测试
vim tests/unit/test_dashboard.py

# 4. 更新 API 文档（如有）
vim docs/api/endpoints/dashboard.md

# 5. 更新用户指南
vim docs/guides/user/features.md

# 6. 运行代码审查
./scripts/tools/code-review.sh working/pages/dashboard.py

# 7. 提交更改
git add .
git commit -m "feat: add new dashboard page

- Add dashboard page with data visualization
- Update API documentation
- Update user guide

Refs: #123"

# 8. 发起 PR
git push origin feature/new-dashboard
```

### 4. 文件归档检查清单

#### 每周检查
```bash
# 运行归档检查脚本
./scripts/tools/check-file-organization.sh

# 检查内容：
# 1. 根目录是否有不该存在的文档
# 2. 脚本是否正确归类
# 3. 临时文件是否清理
# 4. 文档是否更新
```

#### 发布前检查
```bash
# 1. 检查根目录整洁度
ls -la | grep -E "\.(md|txt|sh|py)$" | grep -v "README\|CLAUDE\|LICENSE"

# 2. 检查文档完整性
./scripts/tools/validate-docs.sh

# 3. 检查 CHANGELOG
./scripts/tools/check-changelog.sh

# 4. 生成文档站点（如需要）
./scripts/tools/generate-docs.py
```

### 5. 自动化归档工具

#### 创建归档脚本
```bash
# scripts/tools/organize-files.sh
#!/usr/bin/env bash
#
# 自动整理项目文件
#

set -euo pipefail

ROOT_DIR="/mnt/d/工作区/云开发/working"

# 移动文档到 docs/
find "$ROOT_DIR" -maxdepth 1 -type f -name "*.md" \
    ! -name "README.md" \
    ! -name "CLAUDE.md" \
    ! -name "LICENSE.md" \
    -exec echo "需要归档: {}" \;

# 移动脚本到 scripts/
find "$ROOT_DIR" -maxdepth 1 -type f -name "*.sh" \
    -exec echo "需要归档: {}" \;

# 清理临时文件
find "$ROOT_DIR" -maxdepth 1 -type f \
    -name "*.tmp" -o \
    -name "*.log" -o \
    -name "progress*.md" \
    -exec echo "需要清理: {}" \;
```

---

## 实施清单

### 阶段 1: 创建目录结构（1 小时）

- [ ] 创建 `docs/` 主目录和所有子目录
- [ ] 创建 `scripts/` 主目录和所有子目录
- [ ] 创建 `tests/` 目录结构
- [ ] 创建 `.temp/` 临时文件目录
- [ ] 为每个子目录创建 `README.md` 说明文件

**脚本**:
```bash
./scripts/tools/create-directory-structure.sh
```

### 阶段 2: 文件迁移（2 小时）

#### 文档迁移
- [ ] 移动 `POSTGRESQL_CONNECTION.md` → `docs/integrations/postgresql.md`
- [ ] 移动 `POSTGRESQL_QUICK_START.md` → `docs/guides/developer/setup.md`（合并）
- [ ] 移动 `REFLEX_WITH_UV.md` → `docs/guides/developer/reflex-with-uv.md`
- [ ] 移动 `UV_GUIDE.md` → `docs/reference/uv-guide.md`
- [ ] 提取 `CLAUDE.md` 中的内容到对应的 `docs/` 子目录

#### 脚本迁移
- [ ] 移动 `coolify_postgres_manage.sh` → `scripts/database/postgres-manage.sh`
- [ ] 移动 `test_postgres_connection.py` → `scripts/test/test-connection.py`
- [ ] 移动 `.postgres_config` → `docs/integrations/` 或 `.env.example`

#### 临时文件处理
- [ ] 移动 `progress.md` 和 `progress.archive.md` → `.temp/`（或删除）

### 阶段 3: 创建模板和示例（1 小时）

- [ ] 创建 ADR 模板: `docs/architecture/decisions/template.md`
- [ ] 创建脚本模板: `scripts/templates/script-template.sh`
- [ ] 创建文档模板: `docs/templates/doc-template.md`
- [ ] 为每个脚本子目录创建示例脚本

### 阶段 4: 更新配置文件（30 分钟）

- [ ] 更新 `.gitignore` 添加 `.temp/` 和其他忽略规则
- [ ] 更新 `README.md` 添加文档和脚本导航链接
- [ ] 更新 `CLAUDE.md` 更新文件位置引用
- [ ] 创建 `docs/README.md` 作为文档导航索引
- [ ] 创建 `scripts/README.md` 作为脚本使用指南

### 阶段 5: 创建自动化工具（2 小时）

#### 创建脚本
- [ ] `scripts/tools/check-file-organization.sh` - 检查文件组织
- [ ] `scripts/tools/organize-files.sh` - 自动归档文件
- [ ] `scripts/tools/validate-docs.sh` - 验证文档完整性
- [ ] `scripts/tools/check-changelog.sh` - 检查 CHANGELOG 更新
- [ ] `scripts/dev/setup-env.sh` - 开发环境初始化
- [ ] `scripts/test/run-all-tests.sh` - 运行所有测试
- [ ] `scripts/ci/pre-commit.sh` - Git pre-commit 钩子

#### 安装 Git 钩子
- [ ] 安装 pre-commit 钩子检查文件组织
- [ ] 安装 pre-push 钩子运行测试

### 阶段 6: 文档编写（3 小时）

#### 核心文档
- [ ] 编写 `docs/README.md` - 文档导航
- [ ] 编写 `scripts/README.md` - 脚本使用指南
- [ ] 编写 `docs/guides/developer/setup.md` - 开发环境搭建
- [ ] 编写 `docs/guides/developer/contributing.md` - 贡献指南
- [ ] 编写 `docs/reference/configuration.md` - 配置参考

#### 架构文档
- [ ] 编写 `docs/architecture/system-overview.md` - 系统架构
- [ ] 编写 `docs/architecture/database-schema.md` - 数据库设计
- [ ] 编写 `docs/architecture/decisions/001-choose-reflex.md` - 第一个 ADR

### 阶段 7: 测试和验证（1 小时）

- [ ] 运行 `check-file-organization.sh` 验证文件组织
- [ ] 测试所有迁移的脚本是否正常工作
- [ ] 验证文档链接是否正确
- [ ] 检查 `.gitignore` 是否正确忽略文件
- [ ] 运行代码审查确保质量

### 阶段 8: 团队培训和文档化（1 小时）

- [ ] 编写团队培训文档
- [ ] 更新 `README.md` 添加文件组织说明
- [ ] 创建 Quick Reference 卡片
- [ ] 在团队会议上演示新系统

---

## 维护和持续改进

### 每周任务
- 运行 `check-file-organization.sh` 检查文件组织
- 清理 `.temp/` 目录
- 审查新增文件是否正确归档

### 每月任务
- 审查和更新文档
- 检查脚本是否需要优化
- 更新 CHANGELOG
- 清理归档文档

### 每季度任务
- 评估目录结构是否仍然合适
- 重构和优化工具脚本
- 更新团队培训材料
- 审查自动化流程效率

---

## 快速参考

### 常见问题

**Q: 我创建了一个新的测试脚本，应该放在哪里？**
A: 放在 `scripts/test/` 目录下，使用描述性命名，如 `test-api-endpoints.sh`

**Q: 我需要写一个新的部署文档，应该放在哪里？**
A: 放在 `docs/deployment/` 目录下，如 `docs/deployment/aws-ecs.md`

**Q: 临时测试文件应该放在哪里？**
A: 放在 `.temp/` 目录下，这个目录会被 Git 忽略，定期清理

**Q: 如何找到某个功能的文档？**
A: 查看 `docs/README.md`，这是文档导航索引

**Q: 脚本应该使用什么权限？**
A: 可执行脚本使用 `chmod +x`（755），工具函数库使用 644

### 文件归档决策树

```
新文件 →
    是文档？
        → YES → docs/[子目录]/
        → NO ↓
    是脚本？
        → YES → scripts/[子目录]/
        → NO ↓
    是测试？
        → YES → tests/[子目录]/
        → NO ↓
    是配置？
        → YES → 根目录（如 pyproject.toml）
        → NO ↓
    是临时文件？
        → YES → .temp/
        → NO ↓
    是应用代码？
        → YES → working/[子目录]/
        → NO → 询问团队
```

---

## 附录

### A. 相关资源

- [Keep a Changelog](https://keepachangelog.com/)
- [Semantic Versioning](https://semver.org/)
- [Architecture Decision Records](https://adr.github.io/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)

### B. 工具推荐

- **文档生成**: MkDocs, Sphinx, Docusaurus
- **脚本测试**: ShellCheck, pytest
- **文档验证**: markdownlint, vale
- **图表工具**: Mermaid, PlantUML, Draw.io

### C. 联系方式

如有问题或建议，请联系：
- GitHub Issues: [项目仓库]/issues
- 团队讨论: [讨论平台]
- 维护者: Jack

---

**文档版本**: 1.0.0
**最后更新**: 2025-10-27
**维护者**: Jack
