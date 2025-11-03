# 文件归档系统实施清单

## 概述

本清单提供分步指导，帮助您实施完整的项目文件归档系统。

**预计总时间**: 10-12 小时
**推荐方式**: 分多个会话完成，每次 2-3 小时

---

## 实施计划

### 第 1 步: 创建目录结构（30 分钟）

```bash
# 创建 docs 目录结构
mkdir -p docs/{api/{endpoints,schemas,errors},architecture/{diagrams,decisions},guides/{user,developer,operations},deployment,integrations,reference,changelog/versions,archived}

# 创建 scripts 目录结构
mkdir -p scripts/{dev,test,deploy,maintenance,tools,database,ci,utils}

# 创建其他必要目录
mkdir -p tests/{unit,integration,e2e}
mkdir -p .temp

echo "✓ 目录结构创建完成"
```

**验证**:
```bash
tree -L 2 docs/
tree -L 2 scripts/
```

---

### 第 2 步: 创建 README 索引文件（30 分钟）

#### docs/README.md
```bash
cat > docs/README.md << 'EOF'
# 项目文档

欢迎查阅项目文档。本文档系统按功能和受众组织，方便快速找到所需信息。

## 快速导航

### 🚀 快速开始
- [用户快速开始](guides/user/getting-started.md)
- [开发环境搭建](guides/developer/setup.md)

### 📚 主要文档类别

#### API 文档
- [API 概览](api/README.md)
- [端点文档](api/endpoints/)
- [数据模型](api/schemas/)

#### 架构设计
- [系统架构](architecture/system-overview.md)
- [数据库设计](architecture/database-schema.md)
- [架构决策](architecture/decisions/)

#### 使用指南
- [用户指南](guides/user/)
- [开发者指南](guides/developer/)
- [运维指南](guides/operations/)

#### 部署
- [部署指南](deployment/)
- [环境配置](deployment/production.md)

#### 集成
- [PostgreSQL](integrations/postgresql.md)
- [ChromeDevTools MCP](integrations/chrome-devtools.md)
- [CrewAI 代码审查](integrations/crewai.md)

### 📖 参考资料
- [配置参考](reference/configuration.md)
- [环境变量](reference/environment-variables.md)
- [CLI 命令](reference/cli-commands.md)

### 📝 变更记录
- [CHANGELOG](changelog/CHANGELOG.md)

## 文档贡献

请参阅 [贡献指南](guides/developer/contributing.md)

## 文档规范

本文档遵循以下规范：
- 文件命名：小写，连字符分隔
- 格式：Markdown
- 版本控制：通过 Git 管理
- 更新频率：随代码变更同步更新
EOF
```

#### scripts/README.md
```bash
cat > scripts/README.md << 'EOF'
# 项目脚本

本目录包含项目开发、测试、部署和维护所需的所有自动化脚本。

## 目录结构

```
scripts/
├── dev/           # 开发辅助脚本
├── test/          # 测试相关脚本
├── deploy/        # 部署脚本
├── maintenance/   # 维护脚本
├── tools/         # 工具脚本
├── database/      # 数据库管理
├── ci/            # CI/CD 脚本
└── utils/         # 通用工具函数
```

## 快速使用

### 开发环境

```bash
# 初始化开发环境
./scripts/dev/setup-env.sh

# 清理缓存
./scripts/dev/clean-cache.sh

# 重置数据库
./scripts/dev/reset-db.sh
```

### 测试

```bash
# 运行所有测试
./scripts/test/run-all-tests.sh

# 运行单元测试
./scripts/test/run-unit-tests.sh

# 生成覆盖率报告
./scripts/test/test-coverage.sh
```

### 部署

```bash
# 部署到测试环境
./scripts/deploy/deploy-staging.sh

# 部署到生产环境
./scripts/deploy/deploy-production.sh

# 回滚
./scripts/deploy/rollback.sh
```

### 数据库

```bash
# 创建迁移
./scripts/database/create-migration.sh "description"

# 应用迁移
./scripts/database/migrate.sh

# PostgreSQL 管理
./scripts/database/postgres-manage.sh
```

### 工具

```bash
# 代码格式化
./scripts/tools/format-code.sh

# 代码检查
./scripts/tools/lint-check.sh

# 代码审查
./scripts/tools/code-review.sh <file>

# 检查文件组织
./scripts/tools/check-file-organization.sh
```

## 脚本规范

所有脚本遵循以下规范：

1. **Shebang**: `#!/usr/bin/env bash` 或 `#!/usr/bin/env python3`
2. **权限**: 可执行脚本设置 `chmod +x`
3. **错误处理**: 使用 `set -euo pipefail`
4. **日志**: 提供清晰的输出和错误信息
5. **文档**: 脚本头部包含用法说明

## 添加新脚本

1. 确定脚本类别，放入对应子目录
2. 使用描述性命名（动词开头）
3. 添加脚本头部注释
4. 设置执行权限
5. 测试脚本功能
6. 更新本 README

## 故障排除

如脚本执行失败：

1. 检查权限：`ls -l scripts/path/to/script.sh`
2. 查看日志输出
3. 验证环境变量
4. 检查依赖工具是否安装

## 联系方式

如有问题或建议，请提交 Issue 或联系维护者。
EOF
```

---

### 第 3 步: 迁移现有文件（1 小时）

创建迁移脚本：

```bash
cat > migrate-files.sh << 'EOF'
#!/usr/bin/env bash
#
# 脚本名称: migrate-files.sh
# 描述: 迁移现有文件到新的目录结构
#

set -euo pipefail

ROOT_DIR="/mnt/d/工作区/云开发/working"
cd "$ROOT_DIR"

echo "开始文件迁移..."

# 创建备份
BACKUP_DIR=".migration-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# 迁移文档
if [ -f "POSTGRESQL_CONNECTION.md" ]; then
    cp "POSTGRESQL_CONNECTION.md" "$BACKUP_DIR/"
    mv "POSTGRESQL_CONNECTION.md" "docs/integrations/postgresql-connection.md"
    echo "✓ 迁移 POSTGRESQL_CONNECTION.md"
fi

if [ -f "POSTGRESQL_QUICK_START.md" ]; then
    cp "POSTGRESQL_QUICK_START.md" "$BACKUP_DIR/"
    mv "POSTGRESQL_QUICK_START.md" "docs/integrations/postgresql-quickstart.md"
    echo "✓ 迁移 POSTGRESQL_QUICK_START.md"
fi

if [ -f "REFLEX_WITH_UV.md" ]; then
    cp "REFLEX_WITH_UV.md" "$BACKUP_DIR/"
    mv "REFLEX_WITH_UV.md" "docs/guides/developer/reflex-with-uv.md"
    echo "✓ 迁移 REFLEX_WITH_UV.md"
fi

if [ -f "UV_GUIDE.md" ]; then
    cp "UV_GUIDE.md" "$BACKUP_DIR/"
    mv "UV_GUIDE.md" "docs/reference/uv-guide.md"
    echo "✓ 迁移 UV_GUIDE.md"
fi

# 迁移脚本
if [ -f "coolify_postgres_manage.sh" ]; then
    cp "coolify_postgres_manage.sh" "$BACKUP_DIR/"
    mv "coolify_postgres_manage.sh" "scripts/database/postgres-manage.sh"
    chmod +x "scripts/database/postgres-manage.sh"
    echo "✓ 迁移 coolify_postgres_manage.sh"
fi

if [ -f "test_postgres_connection.py" ]; then
    cp "test_postgres_connection.py" "$BACKUP_DIR/"
    mv "test_postgres_connection.py" "scripts/test/test-connection.py"
    chmod +x "scripts/test/test-connection.py"
    echo "✓ 迁移 test_postgres_connection.py"
fi

# 处理临时文件
if [ -f "progress.md" ]; then
    cp "progress.md" "$BACKUP_DIR/"
    mv "progress.md" ".temp/progress.md"
    echo "✓ 移动 progress.md 到临时目录"
fi

if [ -f "progress.archive.md" ]; then
    cp "progress.archive.md" "$BACKUP_DIR/"
    mv "progress.archive.md" ".temp/progress.archive.md"
    echo "✓ 移动 progress.archive.md 到临时目录"
fi

echo ""
echo "文件迁移完成！"
echo "备份保存在: $BACKUP_DIR"
echo ""
echo "下一步："
echo "1. 验证迁移的文件"
echo "2. 更新 CLAUDE.md 中的文件路径引用"
echo "3. 运行 git status 查看变更"
EOF

chmod +x migrate-files.sh
echo "✓ 迁移脚本已创建"
```

**执行迁移**:
```bash
./migrate-files.sh
```

---

### 第 4 步: 更新 .gitignore（15 分钟）

```bash
cat >> .gitignore << 'EOF'

# === 文件归档系统配置 ===

# 临时文件目录
.temp/
*.tmp
*.bak
*.backup

# 测试输出
.pytest_cache/
.coverage
htmlcov/
coverage.xml
.tox/

# 日志文件
*.log
logs/

# 脚本生成的输出
.migration-backup-*/

# 编辑器临时文件
*~
.*.swp
.*.swo

# OS 文件
.DS_Store
Thumbs.db
EOF

echo "✓ .gitignore 已更新"
```

---

### 第 5 步: 创建工具脚本（2 小时）

#### 5.1 文件组织检查脚本

```bash
cat > scripts/tools/check-file-organization.sh << 'EOF'
#!/usr/bin/env bash
#
# 脚本名称: check-file-organization.sh
# 描述: 检查项目文件是否正确归档
# 用法: ./check-file-organization.sh
#

set -euo pipefail

ROOT_DIR="/mnt/d/工作区/云开发/working"
ERRORS=0

echo "检查项目文件组织..."
echo ""

# 允许的根目录文件
ALLOWED_ROOT_FILES=(
    "README.md"
    "CLAUDE.md"
    "LICENSE"
    "LICENSE.md"
    ".gitignore"
    "pyproject.toml"
    "uv.lock"
    "rxconfig.py"
    "requirements.txt"
    ".env.example"
    "Dockerfile"
    "docker-compose.yml"
    ".editorconfig"
)

# 检查根目录的 .md 文件
echo "1. 检查根目录文档文件..."
cd "$ROOT_DIR"
for file in *.md; do
    [ -f "$file" ] || continue

    is_allowed=false
    for allowed in "${ALLOWED_ROOT_FILES[@]}"; do
        if [ "$file" = "$allowed" ]; then
            is_allowed=true
            break
        fi
    done

    if [ "$is_allowed" = false ]; then
        echo "  ❌ 发现不应在根目录的文档: $file"
        echo "     建议: 移动到 docs/ 目录"
        ((ERRORS++))
    fi
done

# 检查根目录的 .sh 文件
echo "2. 检查根目录脚本文件..."
for file in *.sh; do
    [ -f "$file" ] || continue
    echo "  ❌ 发现不应在根目录的脚本: $file"
    echo "     建议: 移动到 scripts/ 目录"
    ((ERRORS++))
done

# 检查根目录的 .py 测试文件
echo "3. 检查根目录测试文件..."
for file in test_*.py *_test.py; do
    [ -f "$file" ] || continue
    echo "  ❌ 发现不应在根目录的测试文件: $file"
    echo "     建议: 移动到 scripts/test/ 或 tests/ 目录"
    ((ERRORS++))
done

# 检查临时文件
echo "4. 检查临时文件..."
for pattern in "*.tmp" "*.bak" "progress*.md"; do
    for file in $pattern; do
        [ -f "$file" ] || continue
        echo "  ⚠️  发现临时文件: $file"
        echo "     建议: 移动到 .temp/ 目录或删除"
        ((ERRORS++))
    done
done

# 检查脚本权限
echo "5. 检查脚本执行权限..."
if [ -d "scripts" ]; then
    while IFS= read -r -d '' script; do
        if [ ! -x "$script" ]; then
            echo "  ⚠️  脚本缺少执行权限: $script"
            echo "     修复: chmod +x $script"
        fi
    done < <(find scripts -type f \( -name "*.sh" -o -name "*.py" \) -print0)
fi

echo ""
if [ $ERRORS -eq 0 ]; then
    echo "✅ 文件组织检查通过！"
    exit 0
else
    echo "❌ 发现 $ERRORS 个问题需要处理"
    exit 1
fi
EOF

chmod +x scripts/tools/check-file-organization.sh
echo "✓ 创建 check-file-organization.sh"
```

#### 5.2 自动归档脚本

```bash
cat > scripts/tools/organize-files.sh << 'EOF'
#!/usr/bin/env bash
#
# 脚本名称: organize-files.sh
# 描述: 自动整理项目文件到正确位置
# 用法: ./organize-files.sh [--dry-run]
#

set -euo pipefail

ROOT_DIR="/mnt/d/工作区/云开发/working"
DRY_RUN=false

# 解析参数
if [ "${1:-}" = "--dry-run" ]; then
    DRY_RUN=true
    echo "DRY RUN 模式 - 仅显示将要执行的操作"
    echo ""
fi

cd "$ROOT_DIR"

# 允许的根目录文件
ALLOWED_FILES="README.md|CLAUDE.md|LICENSE|LICENSE.md|.gitignore|pyproject.toml|uv.lock|rxconfig.py|requirements.txt|.env.example|Dockerfile|docker-compose.yml|.editorconfig"

echo "开始整理文件..."
echo ""

# 整理文档
echo "1. 整理文档文件..."
for file in *.md; do
    [ -f "$file" ] || continue

    if ! echo "$file" | grep -qE "^($ALLOWED_FILES)$"; then
        target="docs/archived/$file"
        if [ "$DRY_RUN" = true ]; then
            echo "  将移动: $file → $target"
        else
            mv "$file" "$target"
            echo "  ✓ 移动: $file → $target"
        fi
    fi
done

# 整理脚本
echo "2. 整理脚本文件..."
for file in *.sh; do
    [ -f "$file" ] || continue

    target="scripts/tools/$file"
    if [ "$DRY_RUN" = true ]; then
        echo "  将移动: $file → $target"
    else
        mv "$file" "$target"
        chmod +x "$target"
        echo "  ✓ 移动: $file → $target"
    fi
done

# 整理测试文件
echo "3. 整理测试文件..."
for file in test_*.py *_test.py; do
    [ -f "$file" ] || continue

    target="scripts/test/$file"
    if [ "$DRY_RUN" = true ]; then
        echo "  将移动: $file → $target"
    else
        mv "$file" "$target"
        chmod +x "$target"
        echo "  ✓ 移动: $file → $target"
    fi
done

# 清理临时文件
echo "4. 清理临时文件..."
for pattern in "*.tmp" "*.bak" "progress*.md"; do
    for file in $pattern; do
        [ -f "$file" ] || continue

        target=".temp/$file"
        if [ "$DRY_RUN" = true ]; then
            echo "  将移动: $file → $target"
        else
            mv "$file" "$target"
            echo "  ✓ 移动: $file → $target"
        fi
    done
done

echo ""
if [ "$DRY_RUN" = true ]; then
    echo "DRY RUN 完成 - 没有实际修改文件"
    echo "运行 ./scripts/tools/organize-files.sh 执行实际整理"
else
    echo "✅ 文件整理完成！"
fi
EOF

chmod +x scripts/tools/organize-files.sh
echo "✓ 创建 organize-files.sh"
```

#### 5.3 代码审查快捷脚本

```bash
cat > scripts/tools/code-review.sh << 'EOF'
#!/usr/bin/env bash
#
# 脚本名称: code-review.sh
# 描述: 使用 CrewAI 运行代码审查
# 用法: ./code-review.sh <file_path>
#

set -euo pipefail

if [ $# -eq 0 ]; then
    echo "用法: $0 <file_path>"
    echo "示例: $0 working/pages/dashboard.py"
    exit 1
fi

FILE_PATH="$1"
CREW_DIR="/mnt/d/工作区/云开发/working/code_review_crew"

if [ ! -f "$FILE_PATH" ]; then
    echo "错误: 文件不存在: $FILE_PATH"
    exit 1
fi

echo "运行代码审查: $FILE_PATH"
echo ""

cd "$CREW_DIR"
poetry run python src/code_review_crew/main.py "$FILE_PATH"

echo ""
echo "代码审查完成！"
echo "报告位置: $CREW_DIR/output/code_review_report.md"
EOF

chmod +x scripts/tools/code-review.sh
echo "✓ 创建 code-review.sh"
```

---

### 第 6 步: 创建开发脚本（1 小时）

#### 6.1 环境初始化脚本

```bash
cat > scripts/dev/setup-env.sh << 'EOF'
#!/usr/bin/env bash
#
# 脚本名称: setup-env.sh
# 描述: 初始化开发环境
# 用法: ./setup-env.sh
#

set -euo pipefail

ROOT_DIR="/mnt/d/工作区/云开发/working"
cd "$ROOT_DIR"

echo "初始化开发环境..."
echo ""

# 检查 uv
if ! command -v uv &> /dev/null; then
    echo "错误: uv 未安装"
    echo "安装: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi
echo "✓ uv 已安装"

# 同步依赖
echo "同步 Python 依赖..."
uv sync
echo "✓ 依赖同步完成"

# 创建 .env 文件
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp ".env.example" ".env"
        echo "✓ 创建 .env 文件（从 .env.example）"
        echo "  请编辑 .env 文件配置环境变量"
    else
        echo "⚠️  未找到 .env.example，请手动创建 .env"
    fi
else
    echo "✓ .env 文件已存在"
fi

# 安装 Git 钩子
if [ -f "scripts/ci/pre-commit.sh" ]; then
    ln -sf "../../scripts/ci/pre-commit.sh" ".git/hooks/pre-commit"
    chmod +x ".git/hooks/pre-commit"
    echo "✓ 安装 Git pre-commit 钩子"
fi

# 创建必要目录
mkdir -p .temp
mkdir -p logs
echo "✓ 创建必要目录"

echo ""
echo "✅ 开发环境初始化完成！"
echo ""
echo "下一步:"
echo "1. 编辑 .env 文件配置环境变量"
echo "2. 运行 uv run reflex run 启动应用"
echo "3. 访问 http://localhost:3000"
EOF

chmod +x scripts/dev/setup-env.sh
echo "✓ 创建 setup-env.sh"
```

#### 6.2 清理缓存脚本

```bash
cat > scripts/dev/clean-cache.sh << 'EOF'
#!/usr/bin/env bash
#
# 脚本名称: clean-cache.sh
# 描述: 清理项目缓存文件
# 用法: ./clean-cache.sh
#

set -euo pipefail

ROOT_DIR="/mnt/d/工作区/云开发/working"
cd "$ROOT_DIR"

echo "清理缓存文件..."
echo ""

# Python 缓存
echo "清理 Python 缓存..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
echo "✓ Python 缓存已清理"

# Reflex 缓存
if [ -d ".web" ]; then
    echo "清理 Reflex 前端缓存..."
    rm -rf .web/node_modules/.cache
    rm -rf .web/.cache
    echo "✓ Reflex 缓存已清理"
fi

# 测试缓存
if [ -d ".pytest_cache" ]; then
    echo "清理测试缓存..."
    rm -rf .pytest_cache
    rm -rf .tox
    rm -f .coverage
    rm -rf htmlcov
    echo "✓ 测试缓存已清理"
fi

# 临时文件
if [ -d ".temp" ]; then
    echo "清理临时文件..."
    find .temp -type f -mtime +7 -delete 2>/dev/null || true
    echo "✓ 临时文件已清理（保留 7 天内的文件）"
fi

echo ""
echo "✅ 缓存清理完成！"
EOF

chmod +x scripts/dev/clean-cache.sh
echo "✓ 创建 clean-cache.sh"
```

---

### 第 7 步: 创建测试脚本（1 小时）

```bash
cat > scripts/test/run-all-tests.sh << 'EOF'
#!/usr/bin/env bash
#
# 脚本名称: run-all-tests.sh
# 描述: 运行所有测试
# 用法: ./run-all-tests.sh [--verbose] [--coverage]
#

set -euo pipefail

ROOT_DIR="/mnt/d/工作区/云开发/working"
cd "$ROOT_DIR"

VERBOSE=false
COVERAGE=false

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        *)
            echo "未知参数: $1"
            exit 1
            ;;
    esac
done

echo "运行所有测试..."
echo ""

# 构建 pytest 命令
PYTEST_CMD="uv run pytest tests/"

if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=working --cov-report=html --cov-report=term"
fi

# 运行测试
eval $PYTEST_CMD

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ 所有测试通过！"

    if [ "$COVERAGE" = true ]; then
        echo "覆盖率报告: htmlcov/index.html"
    fi
else
    echo ""
    echo "❌ 测试失败！"
fi

exit $EXIT_CODE
EOF

chmod +x scripts/test/run-all-tests.sh
echo "✓ 创建 run-all-tests.sh"
```

---

### 第 8 步: 创建 CI 脚本（30 分钟）

```bash
cat > scripts/ci/pre-commit.sh << 'EOF'
#!/usr/bin/env bash
#
# 脚本名称: pre-commit.sh
# 描述: Git pre-commit 钩子
# 用法: 自动通过 Git 调用
#

set -euo pipefail

echo "运行 pre-commit 检查..."
echo ""

# 检查文件组织
echo "1. 检查文件组织..."
if ! ./scripts/tools/check-file-organization.sh; then
    echo ""
    echo "❌ 文件组织检查失败"
    echo "运行 ./scripts/tools/organize-files.sh 自动整理"
    exit 1
fi

# 代码格式检查
echo "2. 检查代码格式..."
if command -v ruff &> /dev/null; then
    uv run ruff check . || {
        echo "❌ 代码格式检查失败"
        echo "运行 uv run ruff check --fix . 自动修复"
        exit 1
    }
fi

echo ""
echo "✅ Pre-commit 检查通过！"
EOF

chmod +x scripts/ci/pre-commit.sh
echo "✓ 创建 pre-commit.sh"
```

---

### 第 9 步: 更新 README（30 分钟）

在 README.md 的合适位置添加：

```markdown
## 项目结构

本项目遵循标准化的文件组织结构：

```
working/
├── docs/              # 📄 所有文档
├── scripts/           # 📜 自动化脚本
├── tests/             # 🧪 测试代码
├── working/           # 💻 Reflex 应用代码
└── ...
```

- **文档**: 查看 [docs/README.md](docs/README.md)
- **脚本**: 查看 [scripts/README.md](scripts/README.md)
- **完整指南**: 查看 [FILE_ORGANIZATION_SYSTEM.md](FILE_ORGANIZATION_SYSTEM.md)
```

---

### 第 10 步: 更新 CLAUDE.md（30 分钟）

更新文件路径引用：

```markdown
## 文档参考

- **MCP 服务器文档**: `docs/integrations/chrome-devtools.md`
- **代码审查系统**: `docs/integrations/crewai.md`
- **PostgreSQL 连接**: `docs/integrations/postgresql-connection.md`
- **PostgreSQL 快速开始**: `docs/integrations/postgresql-quickstart.md`
- **Reflex + uv 指南**: `docs/guides/developer/reflex-with-uv.md`
- **uv 使用指南**: `docs/reference/uv-guide.md`
```

---

## 验证清单

完成实施后，运行以下验证：

```bash
# 1. 检查目录结构
tree -L 2 docs/
tree -L 2 scripts/

# 2. 检查文件组织
./scripts/tools/check-file-organization.sh

# 3. 测试脚本
./scripts/dev/setup-env.sh --help || true
./scripts/test/run-all-tests.sh --help || true

# 4. 检查权限
find scripts -name "*.sh" -type f ! -executable

# 5. 验证 Git
git status
```

---

## 常见问题

### Q: 实施过程中遇到错误怎么办？
A: 所有脚本都有备份功能。查看 `.migration-backup-*` 目录恢复文件。

### Q: 是否需要一次性完成所有步骤？
A: 不需要。可以分阶段完成，建议优先完成第 1-3 步。

### Q: 如何撤销更改？
A: 使用 Git 撤销：`git checkout -- <file>` 或 `git reset --hard`

### Q: 脚本在 WSL 中无法执行？
A: 检查行尾符：`dos2unix scripts/**/*.sh`

---

## 下一步

完成实施后：

1. ✅ 提交更改到 Git
2. ✅ 运行代码审查：`./scripts/tools/code-review.sh <file>`
3. ✅ 更新团队文档
4. ✅ 培训团队成员

---

**文档版本**: 1.0.0
**最后更新**: 2025-10-27
