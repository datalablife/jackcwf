# 文件归档系统快速参考

## 📁 我的文件应该放在哪里？

### 文档类文件 (.md, .txt, .pdf)

| 文件类型 | 目录 | 示例 |
|---------|------|------|
| API 文档 | `docs/api/` | `docs/api/endpoints/users.md` |
| 架构设计 | `docs/architecture/` | `docs/architecture/system-overview.md` |
| 用户指南 | `docs/guides/user/` | `docs/guides/user/getting-started.md` |
| 开发指南 | `docs/guides/developer/` | `docs/guides/developer/setup.md` |
| 部署文档 | `docs/deployment/` | `docs/deployment/production.md` |
| 集成文档 | `docs/integrations/` | `docs/integrations/postgresql.md` |
| 配置参考 | `docs/reference/` | `docs/reference/configuration.md` |
| 变更日志 | `docs/changelog/` | `docs/changelog/CHANGELOG.md` |

### 脚本文件 (.sh, .py)

| 脚本类型 | 目录 | 示例 |
|---------|------|------|
| 开发工具 | `scripts/dev/` | `scripts/dev/setup-env.sh` |
| 测试脚本 | `scripts/test/` | `scripts/test/run-all-tests.sh` |
| 部署脚本 | `scripts/deploy/` | `scripts/deploy/deploy-production.sh` |
| 维护脚本 | `scripts/maintenance/` | `scripts/maintenance/backup-db.sh` |
| 通用工具 | `scripts/tools/` | `scripts/tools/format-code.sh` |
| 数据库管理 | `scripts/database/` | `scripts/database/migrate.sh` |
| CI/CD | `scripts/ci/` | `scripts/ci/pre-commit.sh` |

### 代码文件

| 代码类型 | 目录 | 示例 |
|---------|------|------|
| Reflex 页面 | `working/pages/` | `working/pages/dashboard.py` |
| Reflex 组件 | `working/components/` | `working/components/sidebar.py` |
| Reflex 状态 | `working/states/` | `working/states/user_state.py` |
| 工具函数 | `working/utils/` | `working/utils/helpers.py` |
| 单元测试 | `tests/unit/` | `tests/unit/test_user_state.py` |
| 集成测试 | `tests/integration/` | `tests/integration/test_api.py` |
| E2E 测试 | `tests/e2e/` | `tests/e2e/test_login_flow.py` |

### 临时文件

| 文件类型 | 目录 | 说明 |
|---------|------|------|
| 临时测试 | `.temp/` | 不提交到 Git |
| 开发草稿 | `.temp/` | 定期清理 |
| 日志文件 | `logs/` | 在 .gitignore 中 |

---

## 🚀 常用命令

### 开发环境

```bash
# 初始化环境
./scripts/dev/setup-env.sh

# 清理缓存
./scripts/dev/clean-cache.sh

# 启动应用
uv run reflex run
```

### 测试

```bash
# 运行所有测试
./scripts/test/run-all-tests.sh

# 运行测试并生成覆盖率
./scripts/test/run-all-tests.sh --coverage

# 测试数据库连接
./scripts/test/test-connection.py
```

### 代码质量

```bash
# 代码审查
./scripts/tools/code-review.sh <file_path>

# 检查文件组织
./scripts/tools/check-file-organization.sh

# 自动整理文件
./scripts/tools/organize-files.sh
```

### 数据库

```bash
# PostgreSQL 管理
./scripts/database/postgres-manage.sh

# 创建迁移
./scripts/database/create-migration.sh "description"

# 应用迁移
./scripts/database/migrate.sh
```

---

## 📝 命名规范

### 文档文件

- **格式**: 小写，连字符分隔
- **示例**: `user-authentication.md`
- **禁止**: `UserAuthentication.md`, `user_authentication.md`

### 脚本文件

- **格式**: 动词开头，小写，连字符分隔
- **示例**: `run-tests.sh`, `deploy-app.sh`
- **禁止**: `test.sh`（太模糊）, `run_tests.sh`（下划线）

### ADR（架构决策记录）

- **格式**: 三位数序号 + 描述
- **示例**: `001-choose-reflex.md`, `002-state-pattern.md`

### 版本文件

- **格式**: `v` + 语义化版本号
- **示例**: `v1.0.0.md`, `v1.2.3.md`

---

## ✅ 根目录允许的文件

### 必须存在

- `README.md` - 项目介绍
- `CLAUDE.md` - Claude 指导文件
- `pyproject.toml` - Python 配置
- `uv.lock` - 依赖锁定
- `rxconfig.py` - Reflex 配置
- `.gitignore` - Git 忽略规则

### 可选

- `LICENSE` - 开源许可证
- `.env.example` - 环境变量示例
- `Dockerfile` - Docker 配置
- `docker-compose.yml` - Docker Compose
- `.editorconfig` - 编辑器配置
- `requirements.txt` - Python 依赖（uv 时代可选）

### ❌ 不应存在

- 其他 `.md` 文档 → 移到 `docs/`
- `.sh` 脚本 → 移到 `scripts/`
- `test_*.py` 测试文件 → 移到 `scripts/test/` 或 `tests/`
- 临时文件 → 移到 `.temp/`

---

## 🔍 决策树

```
新文件放在哪？
│
├─ 是文档？ → docs/[分类]/
│
├─ 是脚本？ → scripts/[分类]/
│
├─ 是测试？ → tests/[分类]/
│
├─ 是 Reflex 代码？ → working/[分类]/
│
├─ 是配置文件？ → 根目录
│
└─ 是临时文件？ → .temp/
```

---

## 🛠 工具脚本

| 脚本 | 功能 | 用法 |
|------|------|------|
| `check-file-organization.sh` | 检查文件组织 | `./scripts/tools/check-file-organization.sh` |
| `organize-files.sh` | 自动整理文件 | `./scripts/tools/organize-files.sh` |
| `code-review.sh` | 代码审查 | `./scripts/tools/code-review.sh <file>` |
| `setup-env.sh` | 初始化环境 | `./scripts/dev/setup-env.sh` |
| `clean-cache.sh` | 清理缓存 | `./scripts/dev/clean-cache.sh` |
| `run-all-tests.sh` | 运行测试 | `./scripts/test/run-all-tests.sh` |

---

## 📋 快速检查清单

### 提交代码前

- [ ] 代码放在正确的目录
- [ ] 相关文档已更新
- [ ] 运行 `./scripts/tools/check-file-organization.sh`
- [ ] 运行 `./scripts/tools/code-review.sh <file>`
- [ ] 运行测试确保通过
- [ ] 更新 CHANGELOG（如需要）

### 新增功能

- [ ] 创建功能代码
- [ ] 编写单元测试
- [ ] 更新 API 文档（如有 API）
- [ ] 更新用户指南
- [ ] 运行代码审查
- [ ] 提交 PR

### 发布前

- [ ] 所有测试通过
- [ ] 文档完整更新
- [ ] CHANGELOG 已更新
- [ ] 版本号已更新
- [ ] 文件组织检查通过

---

## 🚨 常见错误

### ❌ 错误做法

```bash
# 在根目录创建文档
touch postgresql-guide.md

# 在根目录创建脚本
touch deploy.sh

# 在根目录创建测试
touch test_api.py
```

### ✅ 正确做法

```bash
# 文档放到对应目录
touch docs/integrations/postgresql.md

# 脚本放到对应目录
touch scripts/deploy/deploy-production.sh
chmod +x scripts/deploy/deploy-production.sh

# 测试放到对应目录
touch tests/integration/test_api.py
```

---

## 📞 获取帮助

### 查看完整文档

```bash
# 文件组织系统
cat FILE_ORGANIZATION_SYSTEM.md

# 实施清单
cat IMPLEMENTATION_CHECKLIST.md

# 文档索引
cat docs/README.md

# 脚本指南
cat scripts/README.md
```

### 自动化工具

```bash
# 不确定文件放哪？运行检查工具
./scripts/tools/check-file-organization.sh

# 自动整理（先预览）
./scripts/tools/organize-files.sh --dry-run

# 真正执行
./scripts/tools/organize-files.sh
```

---

## 🎯 关键原则

1. **文档集中**: 所有文档在 `docs/`
2. **脚本分类**: 所有脚本在 `scripts/[分类]/`
3. **根目录简洁**: 仅保留必要配置文件
4. **命名统一**: 小写 + 连字符
5. **自动化优先**: 使用工具脚本管理

---

**打印此页面**: 贴在墙上作为快速参考！

**文档版本**: 1.0.0
**最后更新**: 2025-10-27
