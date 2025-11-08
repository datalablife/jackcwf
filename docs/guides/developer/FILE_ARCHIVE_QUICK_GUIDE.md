# 文件归档快速参考指南

这是一份快速查阅指南，适合日常开发使用。详细规范请参考 `CLAUDE.md` 和 `DIRECTORY_STRUCTURE.md`。

---

## 📍 我应该把文件放在哪里？

### 🎯 快速判断树

```
我要创建一个文件...

┌─ 是否是 Markdown 文档？
│  ├─ YES → docs/ 对应子目录
│  └─ NO → 继续
│
├─ 是否是脚本（.sh / .py）？
│  ├─ YES → scripts/ 对应子目录
│  └─ NO → 继续
│
├─ 是否是测试文件？
│  ├─ YES → tests/ 对应子目录
│  └─ NO → 继续
│
├─ 是否是源代码？
│  ├─ YES → src/ 或 components/ (项目结构)
│  └─ NO → 继续
│
└─ 是否是配置文件（.env / Dockerfile）？
   ├─ YES → 根目录（仅配置文件）
   └─ NO → ⚠️ 重新检查！
```

---

## 📁 三大目录详解

### 📚 docs/ - 文档

| 子目录 | 放什么 | 例子 |
|--------|--------|------|
| `api/` | API 文档 | endpoints.md, schemas.md |
| `architecture/` | 系统设计 | overview.md, decisions/ |
| `guides/user/` | 用户指南 | getting-started.md |
| `guides/developer/` | 开发指南 | setup.md, testing.md |
| `guides/operations/` | 运维指南 | deployment.md, monitoring.md |
| `deployment/` | 部署文档 | docker.md, kubernetes.md |
| `integrations/` | 集成文档 | postgresql.md, redis.md |
| `reference/` | 参考文档 | commands.md, glossary.md |
| `changelog/` | 变更记录 | CHANGELOG.md, releases/ |
| `archived/` | 过期文档 | old-architecture.md |

**规则**:
- 文件名: 小写 + 连字符 (`setup-guide.md`)
- 索引: 更新 `docs/README.md`
- 过期: 移至 `archived/`，不要删除

---

### 🔧 scripts/ - 脚本

| 子目录 | 放什么 | 例子 | 权限 |
|--------|--------|------|------|
| `dev/` | 开发脚本 | setup-env.sh, run-app.sh | 可执行 |
| `test/` | 测试脚本 | run-tests.sh, coverage.sh | 可执行 |
| `deploy/` | 部署脚本 | deploy-prod.sh, rollback.sh | 可执行 |
| `maintenance/` | 维护脚本 | backup-db.sh, cleanup.sh | 可执行 |
| `tools/` | 工具脚本 | report-gen.sh, batch-ops.sh | 可执行 |
| `database/` | 数据库脚本 | init-db.sh, seed-data.sh | 可执行 |
| `ci/` | CI/CD 脚本 | pre-commit.sh, run-ci.sh | 可执行 |
| `utils/` | 工具函数库 | logger.sh, validators.sh | 可执行 |
| `output/` | 脚本输出 | 报告、日志（不提交） | - |

**规则**:
- 文件名: 动词开头 + 小写 + 连字符 (`setup-env.sh`)
- Shebang: `#!/bin/bash` 或 `#!/usr/bin/env python3`
- 权限: `chmod +x scripts/xxx.sh`
- 头部: 必须有说明和使用示例
- 输出: 生成到 `scripts/output/`（不提交）

**脚本模板**:
```bash
#!/bin/bash
# 脚本简要说明
#
# 详细说明（可选）
#
# 用法: ./script-name.sh [参数]
# 示例: ./script-name.sh arg1 arg2

set -euo pipefail

source "$(dirname "$0")/../utils/logger.sh"

main() {
    log_info "开始执行..."
    # 脚本逻辑
    log_info "执行完成"
}

trap 'log_error "执行失败"' ERR
main "$@"
```

---

### 🧪 tests/ - 测试

| 子目录 | 放什么 | 例子 |
|--------|--------|------|
| `unit/backend/` | 后端单元测试 | test_models.py, test_services.py |
| `unit/frontend/` | 前端单元测试 | test_components.tsx, test_hooks.ts |
| `integration/` | 集成测试 | test_api_endpoints.py |
| `e2e/` | 端到端测试 | test_user_workflows.py |
| `fixtures/data/` | 测试数据 | users.json, sample-data.sql |
| `fixtures/mocks/` | Mock 对象 | mock-api.py, mock-database.py |

**规则**:
- 文件名: `test_*.py` 或 `*.test.ts`
- 配置: `conftest.py`（pytest 配置）
- 数据: 放在 `fixtures/`
- Mock: 放在 `fixtures/mocks/`

---

## ✅ 常见操作速查

### 创建新 API 文档

```bash
# 创建文件
touch docs/api/new-endpoint.md

# 编辑并保存
# 使用 docs/api/template.md 作为模板

# 更新索引
# 编辑 docs/README.md 和 docs/api/README.md
```

### 创建新开发脚本

```bash
# 创建脚本
touch scripts/dev/new-script.sh

# 添加内容（使用上面的模板）

# 设置权限
chmod +x scripts/dev/new-script.sh

# 更新文档
# 编辑 scripts/README.md
```

### 创建新测试

```bash
# 单元测试
touch tests/unit/backend/test_new_feature.py

# 集成测试
touch tests/integration/test_new_api.py

# 编写测试代码

# 运行测试
pytest tests/unit/backend/test_new_feature.py
```

### 创建新文档

```bash
# 创建文件
touch docs/guides/developer/new-guide.md

# 添加头部和内容

# 更新导航
# 编辑 docs/README.md
```

---

## 🚫 绝对不要做的事

| ❌ 错误 | ✓ 正确做法 |
|-------|----------|
| 在根目录放脚本 | 放在 `scripts/` |
| 在根目录放文档 | 放在 `docs/` |
| 在根目录放测试 | 放在 `tests/` |
| 在根目录放临时文件 | 放在 `scripts/output/` 或 `.gitignore` |
| 文件名大写 | 用小写 + 连字符 |
| 脚本没有权限 | `chmod +x scripts/xxx.sh` |
| 脚本没有说明 | 添加头部注释和使用示例 |
| 删除过期文档 | 移至 `docs/archived/` |
| 在 scripts/ 放测试数据 | 放在 `tests/fixtures/` |
| 提交临时文件 | 添加到 `.gitignore` |

---

## 📊 文件位置总览

```
working/
├── CLAUDE.md                              ✓ 根目录
├── README.md                              ✓ 根目录
├── pyproject.toml                         ✓ 根目录
├── uv.lock                                ✓ 根目录
├── rxconfig.py                            ✓ 根目录
├── .gitignore                             ✓ 根目录
├── .env.example                           ✓ 根目录
│
├── docs/                                  📚 所有文档
│   ├── README.md                          ✓
│   ├── api/                               ✓
│   ├── architecture/                      ✓
│   ├── guides/                            ✓
│   ├── deployment/                        ✓
│   ├── integrations/                      ✓
│   ├── reference/                         ✓
│   ├── changelog/                         ✓
│   └── archived/                          ✓
│
├── scripts/                               🔧 所有脚本
│   ├── README.md                          ✓
│   ├── dev/                               ✓
│   ├── test/                              ✓
│   ├── deploy/                            ✓
│   ├── maintenance/                       ✓
│   ├── tools/                             ✓
│   ├── database/                          ✓
│   ├── ci/                                ✓
│   ├── utils/                             ✓
│   └── output/                            ✗ 不提交
│
├── tests/                                 🧪 所有测试
│   ├── README.md                          ✓
│   ├── conftest.py                        ✓
│   ├── unit/                              ✓
│   ├── integration/                       ✓
│   ├── e2e/                               ✓
│   └── fixtures/                          ✓
│
├── DIRECTORY_STRUCTURE.md                 ✓ 参考文档
├── FILE_ARCHIVE_QUICK_GUIDE.md           ✓ 本文件
│
└── src/                                   💻 源代码
    ├── ...                                ✓ 项目结构
```

---

## 🎯 提交前检查清单

每次提交前，检查:

```
□ 新文件在正确的目录（不在根目录）
□ 文件名遵循规范（小写 + 连字符）
□ 没有临时文件或调试代码
□ 文档已更新（新功能/API）
□ 脚本有执行权限和注释
□ 测试已添加并通过
□ 没有敏感信息（密钥、密码）
□ 根目录保持整洁
```

---

## 💡 快速命令参考

```bash
# 查看目录结构
tree -L 2 docs/
tree -L 2 scripts/
tree -L 2 tests/

# 设置脚本权限
chmod +x scripts/dev/*.sh
chmod +x scripts/test/*.sh

# 运行测试
pytest tests/unit/
pytest tests/integration/

# 检查目录完整性
ls -la docs/
ls -la scripts/
ls -la tests/

# 更新索引（编辑后）
# docs/README.md
# scripts/README.md
# tests/README.md
```

---

## 📞 需要帮助？

1. **查看完整规范**: `CLAUDE.md` → "文件归档规范"
2. **详细目录设计**: `DIRECTORY_STRUCTURE.md`
3. **文档导航**: `docs/README.md`
4. **脚本指南**: `scripts/README.md`
5. **测试指南**: `tests/README.md`

---

**最后更新**: 2025-10-27
**版本**: 1.0.0
**用途**: 日常开发速查表
