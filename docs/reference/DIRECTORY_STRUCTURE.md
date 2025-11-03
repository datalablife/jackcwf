# 文件归档系统 - 完整目录结构设计

## 项目概述

本文档定义了整个项目的文件组织规范，包括 `docs/`、`scripts/` 和 `tests/` 三个核心目录的结构和使用规则。

---

## 1. docs/ 目录结构

**用途**: 集中存储所有类型的文档

```
docs/
├── README.md                          # 文档导航和快速索引
├── api/                               # API 文档
│   ├── endpoints.md                   # API 端点列表
│   ├── schemas.md                     # 数据模式定义
│   ├── authentication.md              # 认证和授权
│   └── errors.md                      # 错误代码参考
├── architecture/                      # 架构设计文档
│   ├── overview.md                    # 系统架构概览
│   ├── diagrams/                      # 架构图
│   │   ├── system-architecture.svg
│   │   ├── data-flow.svg
│   │   └── deployment-architecture.svg
│   └── decisions/                     # 架构决策记录 (ADR)
│       ├── 0001-use-reflex.md
│       ├── 0002-chromeptools-mcp.md
│       └── README.md
├── guides/                            # 开发和使用指南
│   ├── user/                          # 用户指南
│   │   ├── getting-started.md
│   │   ├── features.md
│   │   └── faq.md
│   ├── developer/                     # 开发者指南
│   │   ├── setup.md                   # 开发环境设置
│   │   ├── contributing.md            # 贡献指南
│   │   ├── code-style.md              # 代码风格规范
│   │   ├── testing.md                 # 测试指南
│   │   └── debugging.md               # 调试指南
│   └── operations/                    # 运维指南
│       ├── deployment.md
│       ├── monitoring.md
│       ├── backup.md
│       └── troubleshooting.md
├── deployment/                        # 部署相关文档
│   ├── docker.md                      # Docker 部署
│   ├── kubernetes.md                  # Kubernetes 部署
│   ├── coolify.md                     # Coolify 部署
│   ├── ci-cd.md                       # CI/CD 流程
│   └── scaling.md                     # 扩展策略
├── integrations/                      # 第三方集成文档
│   ├── postgresql.md
│   ├── redis.md
│   ├── external-apis.md
│   └── webhooks.md
├── reference/                         # 参考文档
│   ├── glossary.md                    # 术语表
│   ├── dependencies.md                # 依赖列表
│   ├── configuration.md               # 配置参考
│   └── commands.md                    # 常用命令参考
├── changelog/                         # 变更日志
│   ├── CHANGELOG.md                   # 主变更日志
│   ├── releases/                      # 版本发布说明
│   │   ├── v1.0.0.md
│   │   ├── v1.1.0.md
│   │   └── README.md
│   └── migrations/                    # 数据库迁移记录
│       └── README.md
└── archived/                          # 归档文档
    ├── old-architecture.md
    └── README.md
```

### docs/ 目录使用规则

| 目录 | 文件类型 | 保留周期 | 说明 |
|------|---------|--------|------|
| api/ | Markdown | 长期 | API 端点和数据模式文档 |
| architecture/ | Markdown, SVG | 长期 | 系统设计和决策记录 |
| guides/ | Markdown | 长期 | 各类用户和开发者指南 |
| deployment/ | Markdown | 长期 | 部署和基础设施文档 |
| integrations/ | Markdown | 长期 | 集成和第三方工具文档 |
| reference/ | Markdown | 长期 | 快速参考文档 |
| changelog/ | Markdown | 长期 | 版本历史和迁移记录 |
| archived/ | Markdown | 归档 | 过期但需要保留的文档 |

---

## 2. scripts/ 目录结构

**用途**: 存储开发过程中的脚本和工具

```
scripts/
├── README.md                          # 脚本使用指南
├── dev/                               # 开发辅助脚本
│   ├── setup-env.sh                   # 环境设置脚本
│   ├── run-app.sh                     # 启动应用
│   ├── format-code.sh                 # 代码格式化
│   ├── lint-code.sh                   # 代码检查
│   └── update-deps.sh                 # 更新依赖
├── test/                              # 测试脚本
│   ├── run-all-tests.sh               # 运行全部测试
│   ├── run-unit-tests.sh              # 单元测试
│   ├── run-integration-tests.sh        # 集成测试
│   ├── run-e2e-tests.sh               # 端到端测试
│   └── coverage-report.sh             # 覆盖率报告
├── deploy/                            # 部署脚本
│   ├── deploy-dev.sh                  # 开发环境部署
│   ├── deploy-staging.sh              # 测试环境部署
│   ├── deploy-production.sh           # 生产环境部署
│   ├── rollback.sh                    # 回滚脚本
│   └── health-check.sh                # 健康检查
├── maintenance/                       # 维护脚本
│   ├── backup-database.sh             # 数据库备份
│   ├── cleanup-logs.sh                # 清理日志
│   ├── migrate-database.sh            # 数据库迁移
│   └── sync-config.sh                 # 配置同步
├── tools/                             # 工具脚本
│   ├── file-organizer.sh              # 文件组织工具
│   ├── report-generator.sh            # 报告生成工具
│   ├── data-processor.sh              # 数据处理工具
│   └── batch-operations.sh            # 批量操作工具
├── database/                          # 数据库管理脚本
│   ├── init-db.sh                     # 初始化数据库
│   ├── seed-data.sh                   # 导入测试数据
│   ├── export-data.sh                 # 导出数据
│   └── validate-schema.sh             # 验证数据库模式
├── ci/                                # CI/CD 脚本
│   ├── pre-commit.sh                  # 提交前检查
│   ├── run-ci.sh                      # CI 流程
│   ├── run-cd.sh                      # CD 流程
│   └── notify-status.sh               # 通知脚本
└── utils/                             # 通用工具函数库
    ├── logger.sh                      # 日志工具
    ├── validators.sh                  # 验证工具
    ├── common.sh                      # 通用函数
    └── config-parser.sh               # 配置解析
```

### scripts/ 目录使用规则

| 目录 | 脚本类型 | 执行权限 | 说明 |
|------|---------|--------|------|
| dev/ | Bash/Shell | 可执行 | 本地开发辅助 |
| test/ | Bash/Shell | 可执行 | 测试自动化 |
| deploy/ | Bash/Shell | 可执行 | 环境部署 |
| maintenance/ | Bash/Shell | 可执行 | 系统维护 |
| tools/ | Bash/Shell | 可执行 | 工具脚本 |
| database/ | Bash/SQL | 可执行 | 数据库操作 |
| ci/ | Bash/YAML | 可执行 | CI/CD 自动化 |
| utils/ | Bash | 可执行 | 共享函数库 |

**脚本命名规范**:
- 使用小写字母和连字符: `setup-env.sh`，不要用 `SetupEnv.sh`
- 动词开头: `run-app.sh`，不要用 `app-run.sh`
- 脚本加 `.sh` 后缀
- 使用 `#!/bin/bash` 作为 shebang

---

## 3. tests/ 目录结构

**用途**: 存储项目测试

```
tests/
├── README.md                          # 测试指南
├── unit/                              # 单元测试
│   ├── backend/
│   │   ├── test_models.py
│   │   ├── test_services.py
│   │   ├── test_utils.py
│   │   └── __init__.py
│   └── frontend/
│       ├── test_components.tsx
│       ├── test_hooks.ts
│       └── __init__.ts
├── integration/                       # 集成测试
│   ├── test_api_endpoints.py
│   ├── test_database_integration.py
│   ├── test_external_services.py
│   └── __init__.py
├── e2e/                               # 端到端测试
│   ├── test_user_workflows.py
│   ├── test_critical_paths.py
│   └── __init__.py
├── fixtures/                          # 测试数据和 fixtures
│   ├── data/
│   │   ├── users.json
│   │   ├── products.json
│   │   └── sample-data.sql
│   ├── mocks/
│   │   ├── mock-api.py
│   │   └── mock-database.py
│   └── __init__.py
└── conftest.py                        # pytest 配置
```

### tests/ 目录使用规则

| 目录 | 文件类型 | 覆盖范围 | 说明 |
|------|---------|--------|------|
| unit/ | .py, .ts | 单个函数/组件 | 快速、隔离的测试 |
| integration/ | .py | 多模块交互 | 依赖集成测试 |
| e2e/ | .py | 完整用户流 | 功能完整性测试 |
| fixtures/ | .json, .py, .sql | 测试数据 | 模拟数据和对象 |

---

## 4. 项目根目录整洁规则

### ✓ 允许在根目录的文件

```
working/
├── CLAUDE.md                          # 项目指导 (必须)
├── README.md                          # 项目说明 (必须)
├── pyproject.toml                     # Python 项目配置 (必须)
├── uv.lock                            # 依赖锁定 (必须)
├── rxconfig.py                        # Reflex 配置 (必须)
├── package.json                       # Node.js 配置 (如需)
├── .gitignore                         # Git 忽略规则 (必须)
├── .env.example                       # 环境变量模板 (必须)
├── Dockerfile                         # Docker 配置 (如需)
└── .github/                           # GitHub 配置 (如需)
```

### ✗ 不允许在根目录的文件

| 文件类型 | 归档目录 | 说明 |
|---------|--------|------|
| Markdown 文档 | docs/ | 除了 README.md 和 CLAUDE.md |
| 脚本文件 (.sh, .py) | scripts/ | 开发和部署脚本 |
| 测试文件 (.test.py, .spec.ts) | tests/ | 所有测试文件 |
| 数据文件 (.json, .csv, .sql) | scripts/fixtures/ 或 docs/data/ | 测试和示例数据 |
| 临时文件 (.tmp, .log) | 不提交 | 添加到 .gitignore |
| 生成的文件 | scripts/output/ 或 .gitignore | 构建和生成的文件 |

### 例外处理

某些特殊文件可以在根目录：
- **配置文件**: `.env`, `.env.local` (但不提交), `.editorconfig`
- **构建文件**: `Dockerfile`, `docker-compose.yml`
- **CI/CD**: `.github/workflows/`, `.gitlab-ci.yml`
- **通知文件**: `CHANGELOG.md`, `CONTRIBUTING.md`, `LICENSE`

---

## 5. 开发工作流规范

### 5.1 代码生成时的规则

**新功能开发**:
```
1. 编写代码 → 源代码目录 (src/, components/ 等)
2. 编写测试 → tests/unit/ 或 tests/integration/
3. 编写文档 → docs/guides/developer/ 或 docs/api/
4. 记录决策 → docs/architecture/decisions/
```

**脚本生成**:
```
1. 编写脚本 → scripts/ 对应的子目录
2. 添加使用说明 → scripts/README.md
3. 添加执行权限 → chmod +x scripts/xxx.sh
4. 记录变更 → docs/changelog/CHANGELOG.md
```

**文档生成**:
```
1. 生成文档 → docs/ 对应的子目录
2. 更新索引 → docs/README.md
3. 记录版本 → docs/changelog/CHANGELOG.md
4. 过期文档 → 移至 docs/archived/
```

### 5.2 临时文件处理

**开发过程中产生的临时文件**:
- 日志文件: `.log` → 不提交，添加 `.gitignore`
- 缓存: `__pycache__/`, `.pytest_cache/` → 不提交
- 输出: 脚本输出 → `scripts/output/` → 不提交
- 临时数据: `.tmp`, `.temp` → 不提交

**.gitignore 配置**:
```bash
# 临时文件
*.log
*.tmp
*.temp
*.swp
.DS_Store

# Python
__pycache__/
.pytest_cache/
.venv/
dist/
build/

# Node.js
node_modules/
.node_modules/

# 编辑器
.vscode/local
.idea/local

# 脚本输出
scripts/output/
```

### 5.3 代码审查检查清单

提交代码前检查:

- [ ] 新文件在正确的目录中
- [ ] 文件名遵循命名规范
- [ ] 没有临时文件或调试代码
- [ ] 文档已更新 (如有 API 变更)
- [ ] 脚本有执行权限和注释
- [ ] 测试已添加并通过
- [ ] 没有敏感信息 (密钥、密码等)

---

## 6. 文件迁移指南

### 6.1 现有文件迁移

**当前根目录文件**:
```bash
# 文档迁移
POSTGRESQL_CONNECTION.md → docs/reference/postgresql.md
POSTGRESQL_QUICK_START.md → docs/guides/operations/postgresql-quick-start.md
REFLEX_WITH_UV.md → docs/guides/developer/reflex-with-uv.md
UV_GUIDE.md → docs/guides/developer/uv-guide.md
README.md → 保留在根目录（项目总览）

# 脚本迁移
test_postgres_connection.py → scripts/database/test-postgres-connection.py
coolify_postgres_manage.sh → scripts/tools/coolify-postgres-manage.sh

# 代码审查脚本
code_review_crew/ → 保留在根目录（大型工具）
```

### 6.2 迁移命令

```bash
#!/bin/bash
# 迁移文档
mkdir -p docs/{api,architecture,guides/{user,developer,operations},deployment,integrations,reference,changelog,archived}
mkdir -p docs/architecture/diagrams docs/architecture/decisions docs/changelog/releases docs/changelog/migrations
mkdir -p scripts/{dev,test,deploy,maintenance,tools,database,ci,utils} scripts/output tests/{unit,integration,e2e,fixtures}

# 迁移文档文件
mv POSTGRESQL_CONNECTION.md docs/reference/
mv POSTGRESQL_QUICK_START.md docs/guides/operations/
mv REFLEX_WITH_UV.md docs/guides/developer/
mv UV_GUIDE.md docs/guides/developer/

# 迁移脚本
mv test_postgres_connection.py scripts/database/
chmod +x scripts/database/*.py

# 迁移代码审查工具
# code_review_crew/ 保留在根目录

# 设置权限
chmod +x scripts/dev/*.sh
chmod +x scripts/test/*.sh
chmod +x scripts/deploy/*.sh
chmod +x scripts/maintenance/*.sh
```

---

## 7. 日常操作规范

### 7.1 创建新文档

```bash
# 确定文档类型
# API 文档 → docs/api/
# 开发指南 → docs/guides/developer/
# 用户指南 → docs/guides/user/
# 参考文档 → docs/reference/
# 架构文档 → docs/architecture/

# 创建文件
touch docs/guides/developer/new-guide.md

# 添加头部
cat > docs/guides/developer/new-guide.md << 'EOF'
# 标题

描述...

## 目录
- [第一部分](#第一部分)
- [第二部分](#第二部分)

## 第一部分

内容...

## 第二部分

内容...

## 相关链接
- [相关文档](../other-doc.md)
EOF

# 更新 docs/README.md 中的索引
```

### 7.2 创建新脚本

```bash
# 确定脚本类型
# 开发脚本 → scripts/dev/
# 测试脚本 → scripts/test/
# 部署脚本 → scripts/deploy/
# 工具脚本 → scripts/tools/

# 创建文件
touch scripts/dev/new-script.sh

# 添加头部
cat > scripts/dev/new-script.sh << 'EOF'
#!/bin/bash
# 脚本说明
# 用法: ./new-script.sh [参数]
# 示例: ./new-script.sh arg1 arg2

set -euo pipefail

# 日志记录
source "$(dirname "$0")/../utils/logger.sh"

# 主函数
main() {
    log_info "开始执行..."
    # 脚本逻辑
    log_info "执行完成"
}

# 错误处理
trap 'log_error "执行失败"' ERR

main "$@"
EOF

# 设置执行权限
chmod +x scripts/dev/new-script.sh

# 更新 scripts/README.md
```

### 7.3 添加新测试

```bash
# 单元测试 → tests/unit/
# 集成测试 → tests/integration/
# 端到端测试 → tests/e2e/

# 创建文件
touch tests/unit/test_new_feature.py

# 添加测试代码
cat > tests/unit/test_new_feature.py << 'EOF'
"""新功能的单元测试"""

import pytest
from src.module import new_feature


def test_new_feature_basic():
    """测试基本功能"""
    result = new_feature()
    assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
EOF

# 运行测试
pytest tests/unit/test_new_feature.py
```

---

## 8. 检查清单

### 月度审查 (每月第一周)

- [ ] 检查归档文档是否完整
- [ ] 验证脚本是否有执行权限
- [ ] 清理 scripts/output/ 目录
- [ ] 更新 CHANGELOG.md
- [ ] 审查过期文档并移至归档

### 季度审查 (每季末)

- [ ] 完整的结构审计
- [ ] 更新依赖和工具版本
- [ ] 性能和存储评估
- [ ] 安全性审查
- [ ] 流程改进建议

---

## 9. 常见问题

**Q: 生成的测试覆盖率报告放在哪？**
A: `scripts/output/coverage-report/` (临时，不提交)

**Q: 如何组织多个相关的脚本？**
A: 创建子目录，如 `scripts/deploy/kubernetes/` 存放 K8s 相关脚本

**Q: 可以在 scripts/ 下创建 Python 脚本吗？**
A: 可以，但要确保有 shebang (`#!/usr/bin/env python3`) 并设置执行权限

**Q: 应该提交 scripts/output/ 吗？**
A: 不应该，添加到 .gitignore

**Q: 如何处理大型文档？**
A: 分解成多个小文件，使用目录索引 (README.md) 组织

---

## 10. 参考资源

- [Markdown 风格指南](../reference/markdown-style.md)
- [Shell 脚本最佳实践](../reference/shell-best-practices.md)
- [Python 代码风格](../guides/developer/code-style.md)
- [API 文档模板](../api/template.md)
- [变更日志格式](../changelog/format.md)

---

**最后更新**: 2025-10-27
**版本**: 1.0.0
**维护者**: 项目团队
